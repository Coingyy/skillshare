#!/usr/bin/env python3
"""Security scanner for submitted skill repos.

Runs in CI on every PR that changes skills.json:
  1. Finds new/changed entries compared to the base branch.
  2. Shallow-clones each new repo and scans all text files
     for known red flags.
  3. Writes a Markdown report (posted as PR comment) and exits
     with code 1 if any HIGH findings exist.

Usage:
  python scripts/security_scan.py --base-ref origin/main --report report.md
  python scripts/security_scan.py --repo https://github.com/foo/bar --report report.md
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_FILE_BYTES = 512 * 1024
TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".sh", ".bash", ".zsh",
    ".ps1", ".psm1", ".bat", ".cmd", ".py", ".js", ".mjs", ".cjs", ".ts",
    ".rb", ".pl", ".php", ".lua", ".html", ".css", ".xml", ".ini", ".cfg", "",
}

# (severity, description, regex) — HIGH fails the build, WARN is a heads-up.
PATTERNS = [
    ("HIGH", "Download piped directly into a shell (curl|sh)",
     re.compile(r"(curl|wget|iwr|invoke-webrequest)[^\n|;&]{0,200}\|\s*(sh|bash|zsh|iex|invoke-expression|powershell)", re.I)),
    ("HIGH", "PowerShell with encoded payload",
     re.compile(r"powershell[^\n]{0,80}(-enc\b|-encodedcommand)", re.I)),
    ("HIGH", "Invoke-Expression on downloaded content",
     re.compile(r"(iex|invoke-expression)\s*\(?\s*\(?\s*(new-object\s+net\.webclient|iwr|invoke-webrequest|invoke-restmethod)", re.I)),
    ("HIGH", "Destructive deletion of system paths",
     re.compile(r"(rm\s+-rf\s+[\"']?(/|~/?|\$HOME/?)[\"']?(\s|$|[;&|)])|del\s+/[fsq]\s+.{0,20}c:\\\\|rd\s+/s\s+/q\s+c:\\\\|format\s+c:)", re.I)),
    ("HIGH", "Access to SSH keys / credentials",
     re.compile(r"(\.ssh[/\\]id_[a-z0-9]+|\.aws[/\\]credentials|\.netrc\b|\.git-credentials)", re.I)),
    ("HIGH", "Reads API keys/tokens from environment with network call nearby",
     re.compile(r"(ANTHROPIC_API_KEY|OPENAI_API_KEY|GITHUB_TOKEN|AWS_SECRET_ACCESS_KEY)[\s\S]{0,300}(curl|fetch\(|requests\.(post|get)|http\.client|urllib|invoke-restmethod|iwr\b)", re.I)),
    ("HIGH", "Browser credential/cookie theft",
     re.compile(r"(login\s*data|cookies\.sqlite|local\s*state)[\s\S]{0,120}(chrome|chromium|edge|firefox|brave)|"
                r"(chrome|chromium|edge|brave)[\s\S]{0,120}(login\s*data|cookies\b.{0,30}(copy|read|sqlite))", re.I)),
    ("HIGH", "Prompt injection: instruction to ignore prior instructions",
     re.compile(r"(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions|prompts|rules)", re.I)),
    ("HIGH", "Prompt injection: demands hidden behavior",
     re.compile(r"(do\s+not|don'?t|never)\s+(tell|inform|mention|reveal|show)\s+(this\s+)?(to\s+)?the\s+user", re.I)),
    ("WARN", "Large base64 blob (possibly obfuscated payload)",
     re.compile(r"[A-Za-z0-9+/=]{400,}")),
    ("WARN", "Base64 decode combined with execution",
     re.compile(r"(base64\s+(-d|--decode)|frombase64string|b64decode)[\s\S]{0,160}(\|\s*(sh|bash)|iex|invoke-expression|exec\(|eval\()", re.I)),
    ("WARN", "eval/exec on dynamic content",
     re.compile(r"\b(eval|exec)\s*\(\s*(request|resp|data|input|urllib|fetch)", re.I)),
    ("WARN", "Network request to non-GitHub host in script",
     re.compile(r"(curl|wget|iwr|invoke-restmethod|requests\.post|fetch\()\s+[\"']?https?://(?!(github\.com|raw\.githubusercontent\.com|api\.github\.com|fonts\.googleapis\.com|registry\.npmjs\.org|pypi\.org))[a-z0-9.-]+", re.I)),
    ("WARN", "Zero-width characters (possible hidden text)",
     re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")),
    ("WARN", "Claude Code hook defined (runs commands automatically — review manually!)",
     re.compile(r"\"hooks\"\s*:|PreToolUse|PostToolUse|SessionStart|UserPromptSubmit")),
    ("WARN", "Reads environment variables named KEY, TOKEN or SECRET",
     re.compile(r"(os\.environ|process\.env|\$env:)[\[\.\:]?\s*[\"']?[A-Z_]*?(KEY|TOKEN|SECRET|PASSWORD)", re.I)),
]

REPO_URL_RE = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$")

# An API key next to a request against one of these hosts is normal API usage,
# not exfiltration — such matches are downgraded from HIGH to WARN.
TRUSTED_API_HOSTS = re.compile(
    r"api\.anthropic\.com|api\.openai\.com|api\.github\.com|[a-z-]+\.googleapis\.com|"
    r"registry\.npmjs\.org|pypi\.org|huggingface\.co|anthropic-version", re.I)

# Official installers that many legit dev repos pipe into a shell.
TRUSTED_INSTALLERS = re.compile(
    r"https://(claude\.ai/install\.(sh|ps1)|bun\.sh/install|sh\.rustup\.rs|get\.docker\.com)", re.I)

# Findings inside test code don't run on an installer's machine — keep them
# visible, but as WARN instead of HIGH.
TEST_PATH_RE = re.compile(r"(^|[/\\])(tests?|__tests__|e2e|spec|fixtures)([/\\]|$)|\.(test|spec)\.[a-z]+$", re.I)

# CI config of the scanned repo runs in that repo's own CI, never on the
# machine of someone installing the skill.
CI_PATH_RE = re.compile(r"^(\.github[/\\]|action\.ya?ml$)", re.I)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def changed_repos(base_ref: str) -> list[dict]:
    """New/changed entries in skills.json compared to base_ref."""
    current = json.loads(Path("skills.json").read_text(encoding="utf-8"))
    old_raw = run(["git", "show", f"{base_ref}:skills.json"])
    old_entries = {}
    if old_raw.returncode == 0:
        try:
            old = json.loads(old_raw.stdout)
            old_entries = {e["id"]: e for e in old.get("skills", [])}
        except json.JSONDecodeError:
            pass
    changed = []
    for entry in current.get("skills", []):
        prev = old_entries.get(entry.get("id"))
        if prev is None or prev.get("repo") != entry.get("repo"):
            changed.append(entry)
    return changed


def scan_repo(url: str) -> list[tuple[str, str, str, str]]:
    """Shallow-clones url and returns findings: (severity, file, desc, snippet)."""
    findings = []
    if not REPO_URL_RE.match(url):
        return [("HIGH", "-", "Repo URL is not a valid GitHub URL", url)]
    with tempfile.TemporaryDirectory() as tmp:
        clone = run(["git", "clone", "--depth", "1", "--no-tags", url, tmp], timeout=120)
        if clone.returncode != 0:
            return [("HIGH", "-", "Repo could not be cloned (private/deleted?)",
                     clone.stderr.strip()[:200])]
        root = Path(tmp)
        for f in root.rglob("*"):
            if not f.is_file() or ".git" in f.parts:
                continue
            if f.suffix.lower() not in TEXT_EXTENSIONS or f.stat().st_size > MAX_FILE_BYTES:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = str(f.relative_to(root))
            for sev, desc, rx in PATTERNS:
                m = rx.search(text)
                if m:
                    line = text.count("\n", 0, m.start()) + 1
                    full = m.group(0)
                    severity = sev
                    context = text[max(0, m.start() - 100):m.end() + 300]
                    if severity == "HIGH" and "API keys" in desc and TRUSTED_API_HOSTS.search(context):
                        severity = "WARN"
                    if severity == "HIGH" and "piped" in desc and TRUSTED_INSTALLERS.search(context):
                        severity = "WARN"
                    if severity == "HIGH" and TEST_PATH_RE.search(rel):
                        severity = "WARN"
                        desc = desc + " (in test code)"
                    elif severity == "HIGH" and CI_PATH_RE.search(rel):
                        severity = "WARN"
                        desc = desc + " (in CI config — runs in the repo's own CI, not on your machine)"
                    snippet = full[:120].replace("\n", " ")
                    findings.append((severity, f"{rel}:{line}", desc, snippet))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-ref", help="Base ref to diff skills.json against, e.g. origin/main")
    ap.add_argument("--repo", action="append", default=[], help="Scan a repo URL directly")
    ap.add_argument("--report", default="security-report.md")
    args = ap.parse_args()

    targets = list(args.repo)
    if args.base_ref:
        entries = changed_repos(args.base_ref)
        targets += [e["repo"] for e in entries]
    targets = sorted(set(targets))

    lines = ["# Security Scan\n"]
    exit_code = 0
    if not targets:
        lines.append("No new or changed repos in `skills.json` — nothing to scan.")
    for url in targets:
        print(f"::group::Scanning {url}")
        findings = scan_repo(url)
        print(f"{len(findings)} finding(s)")
        print("::endgroup::")
        lines.append(f"\n## {url}\n")
        if not findings:
            lines.append("No red flags found. (Automated scanning is no substitute for a human look — still skim hooks and shell scripts yourself.)")
            continue
        highs = [f for f in findings if f[0] == "HIGH"]
        if highs:
            exit_code = 1
        lines.append("| Severity | File | Issue | Match |")
        lines.append("|---|---|---|---|")
        for sev, loc, desc, snippet in sorted(findings, key=lambda x: x[0] != "HIGH"):
            icon = "🔴 HIGH" if sev == "HIGH" else "🟡 WARN"
            safe = snippet.replace("|", "\\|").replace("`", "'")
            lines.append(f"| {icon} | `{loc}` | {desc} | `{safe}` |")
        if highs:
            lines.append("\n**Result: REJECTED** — HIGH findings must be resolved before merging.")
        else:
            lines.append("\n**Result: review the warnings**, then this can be merged.")

    Path(args.report).write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {args.report}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
