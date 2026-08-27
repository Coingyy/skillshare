# Skill einreichen

## Schnellweg (direkt auf GitHub)

1. Öffne [`skills.json`](skills.json) und klicke auf den Stift (Edit).
2. Füge deinen Eintrag ans Ende des `skills`-Arrays:

```json
{
  "id": "mein-skill",
  "name": "Mein Skill",
  "repo": "https://github.com/username/mein-skill",
  "description": "Was der Skill macht, in 1-2 Sätzen.",
  "category": "workflow",
  "tags": ["beispiel", "tag"],
  "submittedBy": "dein-github-name",
  "addedAt": "2026-08-27",
  "status": "pending"
}
```

3. "Propose changes" → Pull Request öffnen.
4. Warten: Der Security-Scan kommentiert automatisch im PR.
5. Bei grünem Check merged ein Maintainer und setzt `status` auf `verified`.

## Regeln

- `id`: kebab-case, eindeutig.
- `category`: eine aus `design`, `workflow`, `review`, `testing`, `mcp`, `official`, `other`.
- `status`: immer `pending` beim Einreichen — `verified` vergibt nur der Maintainer.
- Nur öffentliche GitHub-Repos.
- Schau dir das Repo vorher selbst an. Du bürgst mit deinem Namen dafür.

## Was der Scan ablehnt (HIGH)

- Downloads, die direkt in eine Shell gepiped werden (`curl ... | sh`, `iwr ... | iex`)
- Zugriff auf SSH-Keys, AWS-Credentials, Browser-Cookies
- Auslesen von API-Keys mit Netzwerkversand
- Destruktive Befehle (`rm -rf /`, `format c:`)
- Prompt-Injection ("ignore previous instructions", "don't tell the user")

Warnungen (WARN) blockieren nicht, werden aber im Review angeschaut — z.B. Hooks,
Base64-Blobs oder Requests an fremde Hosts.
