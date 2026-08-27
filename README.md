# skillshare_

Curated, security-checked collection of Claude Code skills and repos — by friends, for friends.

**Website:** available via GitHub Pages after the first push (`https://<username>.github.io/skillshare/`)

## How it works

1. All skills live in [`skills.json`](skills.json) — the website reads from it.
2. New skills come in via **pull request** (see [CONTRIBUTING.md](CONTRIBUTING.md)).
3. Every PR automatically runs a **security scan** ([`scripts/security_scan.py`](scripts/security_scan.py)):
   the submitted repo is cloned and scanned for red flags — shell pipes (`curl | sh`),
   credential access, prompt injection, obfuscated payloads, destructive commands.
   The report is posted as a comment on the PR.
4. HIGH findings block the merge. After a green check plus a quick human review,
   the PR is merged and the skill appears on the website.

## Important

The automated scan catches blunt malware, but it is **no substitute for your own eyes**.
Before installing a skill: skim its hooks, shell scripts, and `SKILL.md` yourself.

## Local testing

```bash
# View the website locally (fetch() doesn't work over file://)
python -m http.server 8080
# → http://localhost:8080

# Run the scanner manually against a repo
python scripts/security_scan.py --repo https://github.com/user/skill-repo --report report.md
```
