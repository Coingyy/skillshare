<div align="center">

# skillshare_

Curated, security-checked collection of Claude Code skills and repos — by friends, for friends.

<br>

## [&nbsp;🛡️&nbsp;&nbsp;**OPEN THE CATALOG →**&nbsp;&nbsp;](https://coingyy.github.io/skillshare/)

### **https://coingyy.github.io/skillshare/**

<br>

[![Website](https://img.shields.io/badge/website-live-22C55E?style=for-the-badge)](https://coingyy.github.io/skillshare/)
[![Submit a skill](https://img.shields.io/badge/submit-a_skill-0F172A?style=for-the-badge)](https://github.com/Coingyy/skillshare/edit/main/skills.json)

</div>

## How it works

1. All skills live in [`skills.json`](skills.json) — the website reads from it.
2. New skills come in via **pull request** (see [CONTRIBUTING.md](CONTRIBUTING.md)).
3. Every PR automatically runs a **security scan** ([`scripts/security_scan.py`](scripts/security_scan.py)):
   the submitted repo is cloned and scanned for red flags — shell pipes (`curl | sh`),
   credential access, prompt injection, obfuscated payloads, destructive commands.
   The report is posted as a comment on the PR.
4. HIGH findings reject the submission automatically. If the scan passes, a bot
   drafts the catalog entry, opens a PR, and merges it — the skill appears on
   the website with no human in the loop.

## Disclaimer

The automated scan catches blunt malware, but **no scan is perfect and "checked"
is not a safety guarantee**. These are third-party repos; we take no
responsibility for what they do. Installing is your own decision — skim a
skill's hooks, shell scripts, and `SKILL.md` yourself before installing it.

## Local testing

```bash
# View the website locally (fetch() doesn't work over file://)
python -m http.server 8080
# → http://localhost:8080

# Run the scanner manually against a repo
python scripts/security_scan.py --repo https://github.com/user/skill-repo --report report.md
```
