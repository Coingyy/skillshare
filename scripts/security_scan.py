#!/usr/bin/env python3
"""Security-Scanner fuer eingereichte Skill-Repos.

Wird in CI bei jedem PR ausgefuehrt, der skills.json aendert:
  1. Findet neue/geaenderte Eintraege gegenueber dem Basis-Branch.
  2. Validiert die Eintraege gegen das Schema (Basis-Checks).
  3. Klont jedes neue Repo (shallow) und scannt alle Textdateien
     auf bekannte Rotflaggen.
  4. Schreibt einen Markdown-Report (fuer den PR-Kommentar) und
     bricht mit Exit-Code 1 ab, wenn HIGH-Findings existieren.

Nutzung:
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

# (Severity, Beschreibung, Regex) — Severity: HIGH bricht den Build ab, WARN ist Hinweis.
PATTERNS = [
    ("HIGH", "Download wird direkt in Shell gepiped (curl|sh)",
     re.compile(r"(curl|wget|iwr|invoke-webrequest)[^\n|;&]{0,200}\|\s*(sh|bash|zsh|iex|invoke-expression|powershell)", re.I)),
    ("HIGH", "PowerShell mit encodetem Payload",
     re.compile(r"powershell[^\n]{0,80}(-enc\b|-encodedcommand)", re.I)),
    ("HIGH", "Invoke-Expression auf heruntergeladenen Inhalt",
     re.compile(r"(iex|invoke-expression)\s*\(?\s*\(?\s*(new-object\s+net\.webclient|iwr|invoke-webrequest|invoke-restmethod)", re.I)),
    ("HIGH", "Destruktives Loeschen von Systempfaden",
     re.compile(r"(rm\s+-rf\s+[\"']?(/|~|\$HOME)[\s\"'/]|del\s+/[fsq]\s+.{0,20}c:\\\\|rd\s+/s\s+/q\s+c:\\\\|format\s+c:)", re.I)),
    ("HIGH", "Zugriff auf SSH-Keys / Credentials",
     re.compile(r"(\.ssh[/\\]id_[a-z0-9]+|\.aws[/\\]credentials|\.netrc\b|\.git-credentials)", re.I)),
    ("HIGH", "Auslesen von API-Keys/Tokens aus Umgebung mit Netzwerkversand in Naehe",
     re.compile(r"(ANTHROPIC_API_KEY|OPENAI_API_KEY|GITHUB_TOKEN|AWS_SECRET_ACCESS_KEY)[\s\S]{0,300}(curl|fetch\(|requests\.(post|get)|http\.client|urllib|invoke-restmethod|iwr\b)", re.I)),
    ("HIGH", "Browser-Credential-/Cookie-Diebstahl",
     re.compile(r"(login\s*data|cookies\.sqlite|local\s*state)[\s\S]{0,120}(chrome|chromium|edge|firefox|brave)|"
                r"(chrome|chromium|edge|brave)[\s\S]{0,120}(login\s*data|cookies\b.{0,30}(copy|read|sqlite))", re.I)),
    ("HIGH", "Prompt-Injection: Anweisung, Instruktionen zu ignorieren",
     re.compile(r"(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions|prompts|rules)", re.I)),
    ("HIGH", "Prompt-Injection: heimliches Verhalten gefordert",
     re.compile(r"(do\s+not|don'?t|never)\s+(tell|inform|mention|reveal|show)\s+(this\s+)?(to\s+)?the\s+user", re.I)),
    ("WARN", "Grosser Base64-Blob (moeglich verschleierter Payload)",
     re.compile(r"[A-Za-z0-9+/=]{400,}")),
    ("WARN", "Base64-Decode kombiniert mit Ausfuehrung",
     re.compile(r"(base64\s+(-d|--decode)|frombase64string|b64decode)[\s\S]{0,160}(\|\s*(sh|bash)|iex|invoke-expression|exec\(|eval\()", re.I)),
    ("WARN", "eval/exec auf dynamischen Inhalt",
     re.compile(r"\b(eval|exec)\s*\(\s*(request|resp|data|input|urllib|fetch)", re.I)),
    ("WARN", "Netzwerk-Request an Nicht-GitHub-Host in Skript",
     re.compile(r"(curl|wget|iwr|invoke-restmethod|requests\.post|fetch\()\s+[\"']?https?://(?!(github\.com|raw\.githubusercontent\.com|api\.github\.com|fonts\.googleapis\.com|registry\.npmjs\.org|pypi\.org))[a-z0-9.-]+", re.I)),
    ("WARN", "Zero-Width-Zeichen (versteckter Text moeglich)",
     re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")),
    ("WARN", "Claude-Code-Hook definiert (fuehrt automatisch Befehle aus — manuell pruefen!)",
     re.compile(r"\"hooks\"\s*:|PreToolUse|PostToolUse|SessionStart|UserPromptSubmit")),
    ("WARN", "Zugriff auf Umgebungsvariablen mit 'KEY', 'TOKEN' oder 'SECRET'",
     re.compile(r"(os\.environ|process\.env|\$env:)[\[\.\:]?\s*[\"']?[A-Z_]*?(KEY|TOKEN|SECRET|PASSWORD)", re.I)),
]

REPO_URL_RE = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$")

# API-Key + Request an einen dieser Hosts ist normale API-Nutzung, kein Exfil —
# solche Treffer werden von HIGH auf WARN heruntergestuft.
TRUSTED_API_HOSTS = re.compile(
    r"api\.anthropic\.com|api\.openai\.com|api\.github\.com|[a-z-]+\.googleapis\.com|"
    r"registry\.npmjs\.org|pypi\.org|huggingface\.co|anthropic-version", re.I)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def changed_repos(base_ref: str) -> list[dict]:
    """Neue/geaenderte Eintraege in skills.json gegenueber base_ref."""
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
    """Klont url shallow und liefert Findings: (severity, file, desc, snippet)."""
    findings = []
    if not REPO_URL_RE.match(url):
        return [("HIGH", "-", "Repo-URL ist keine gueltige GitHub-URL", url)]
    with tempfile.TemporaryDirectory() as tmp:
        clone = run(["git", "clone", "--depth", "1", "--no-tags", url, tmp], timeout=120)
        if clone.returncode != 0:
            return [("HIGH", "-", "Repo konnte nicht geklont werden (privat/geloescht?)",
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
                    if severity == "HIGH" and "API-Keys" in desc and TRUSTED_API_HOSTS.search(context):
                        severity = "WARN"
                    snippet = full[:120].replace("\n", " ")
                    findings.append((severity, f"{rel}:{line}", desc, snippet))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-ref", help="Basis-Ref fuer skills.json-Diff, z.B. origin/main")
    ap.add_argument("--repo", action="append", default=[], help="Repo-URL direkt scannen")
    ap.add_argument("--report", default="security-report.md")
    args = ap.parse_args()

    targets = list(args.repo)
    if args.base_ref:
        entries = changed_repos(args.base_ref)
        targets += [e["repo"] for e in entries]
    targets = sorted(set(targets))

    lines = ["# Security-Scan\n"]
    exit_code = 0
    if not targets:
        lines.append("Keine neuen oder geaenderten Repos in `skills.json` — nichts zu scannen.")
    for url in targets:
        print(f"::group::Scanne {url}")
        findings = scan_repo(url)
        print(f"{len(findings)} Finding(s)")
        print("::endgroup::")
        lines.append(f"\n## {url}\n")
        if not findings:
            lines.append("Keine Rotflaggen gefunden. (Automatischer Scan ersetzt keinen manuellen Blick — besonders Hooks und Shell-Skripte kurz selbst anschauen.)")
            continue
        highs = [f for f in findings if f[0] == "HIGH"]
        if highs:
            exit_code = 1
        lines.append("| Severity | Datei | Problem | Fundstelle |")
        lines.append("|---|---|---|---|")
        for sev, loc, desc, snippet in sorted(findings, key=lambda x: x[0] != "HIGH"):
            icon = "🔴 HIGH" if sev == "HIGH" else "🟡 WARN"
            safe = snippet.replace("|", "\\|").replace("`", "'")
            lines.append(f"| {icon} | `{loc}` | {desc} | `{safe}` |")
        if highs:
            lines.append("\n**Ergebnis: ABGELEHNT** — HIGH-Findings muessen geklaert werden, bevor gemergt wird.")
        else:
            lines.append("\n**Ergebnis: Warnungen pruefen**, dann kann gemergt werden.")

    Path(args.report).write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {args.report}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
