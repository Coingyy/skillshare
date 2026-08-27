# Submitting a skill

## Easiest path (via the website)

1. Open [the catalog](https://coingyy.github.io/skillshare/) and scroll to **Submit a skill**.
2. Paste the repo link, roughly say what it does, hit submit — a prefilled GitHub issue opens; confirm it with "Submit new issue".
3. Everything else is automatic: the security scan checks the repo, Claude writes the catalog entry (description, category, tags) and opens a pull request in your name.
4. A maintainer merges → skill shows up on the site.

## Manual path (directly on GitHub)

1. Open [`skills.json`](skills.json) and click the pencil (Edit).
2. Add your entry to the end of the `skills` array:

```json
{
  "id": "my-skill",
  "name": "My Skill",
  "repo": "https://github.com/username/my-skill",
  "description": "What the skill does, in 1-2 sentences.",
  "category": "workflow",
  "tags": ["example", "tag"],
  "submittedBy": "your-github-name",
  "addedAt": "2026-08-27",
  "status": "pending"
}
```

3. "Propose changes" → open a pull request.
4. Wait: the security scan comments on the PR automatically.
5. On a green check, a maintainer merges and sets `status` to `verified`.

## Rules

- `id`: kebab-case, unique.
- `category`: one of `ui-design`, `3d`, `game-dev`, `web`, `audio`, `automation`, `code-quality`, `docs`, `integrations`, `subagents`, `prompting`, `llm-tooling`, `official`, `other`.
- `status`: always `pending` when submitting — only maintainers set `verified`.
- Public GitHub repos only.
- Look at the repo yourself before submitting. Your name vouches for it.

## What the scan rejects (HIGH)

- Downloads piped straight into a shell (`curl ... | sh`, `iwr ... | iex`)
- Access to SSH keys, AWS credentials, browser cookies
- Reading API keys combined with sending them over the network
- Destructive commands (`rm -rf /`, `format c:`)
- Prompt injection ("ignore previous instructions", "don't tell the user")

Warnings (WARN) don't block, but they get looked at in review — e.g. hooks,
base64 blobs, or requests to unknown hosts.
