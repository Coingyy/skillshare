# skillshare_

Kuratierte, sicherheitsgeprüfte Sammlung von Claude Code Skills und Repos — von Freunden, für Freunde.

**Website:** wird nach dem ersten Push unter GitHub Pages verfügbar (`https://<username>.github.io/skillshare/`)

## Wie es funktioniert

1. Alle Skills stehen in [`skills.json`](skills.json) — die Website liest daraus.
2. Neue Skills kommen per **Pull Request** rein (siehe [CONTRIBUTING.md](CONTRIBUTING.md)).
3. Bei jedem PR läuft automatisch ein **Security-Scan** ([`scripts/security_scan.py`](scripts/security_scan.py)):
   das eingereichte Repo wird geklont und auf Rotflaggen gescannt — Shell-Pipes (`curl | sh`),
   Credential-Zugriff, Prompt-Injection, obfuskierte Payloads, destruktive Befehle.
   Der Report landet als Kommentar im PR.
4. HIGH-Findings blockieren den Merge. Nach grünem Check + kurzem menschlichen Review
   wird gemergt und der Skill erscheint auf der Website.

## Wichtig

Der automatische Scan fängt plumpe Malware, ist aber **kein Ersatz für den eigenen Blick**.
Vor der Installation eines Skills: Hooks, Shell-Skripte und `SKILL.md` selbst kurz anschauen.

## Lokal testen

```bash
# Website lokal ansehen (Python-Webserver, weil fetch() file:// nicht mag)
python -m http.server 8080
# → http://localhost:8080

# Scanner manuell gegen ein Repo laufen lassen
python scripts/security_scan.py --repo https://github.com/user/skill-repo --report report.md
```
