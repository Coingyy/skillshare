# Submit an offering

Use [the website form](https://coingyy.github.io/skillshare/#submit): paste a public GitHub repository URL and optionally add a note, platform suggestions, offering type and provider setup link. No GitHub account or API key is required for the form. Alternatively, use the repository's **Submit a skill** issue template.

Suggestions are evidence to investigate, not proof of compatibility. The automation resolves the repository, scans an exact commit, asks OpenAI to assess documentation and findings, and validates the metadata. HIGH findings always block acceptance. Every warning needs an acceptable assessment. Missing or failed AI review cannot be bypassed.

**Received**, **scanning**, **AI review**, **merged**, and **published** are different states. Follow the GitHub issue linked by the form. Publication is confirmed only after checking the live catalog. Failure leaves the issue open; it does not promise an automatic addition later.

## Compatibility and evidence

An entry has a topic category, one offering type, and separate records for `claude-code`, `codex` and `chatgpt`. Types are `skill`, `plugin`, `mcp`, `tool`, `collection`, `reference` and `workflow`. See [the schema](schema/skills.schema.json).

- `documented` requires a provider source supporting the named program and setup.
- `tested` requires a dated functional test, tester, notes and sources. A maintainer must assess new test claims; AI cannot invent them.
- `unverified` means insufficient evidence. Claude Desktop is not Claude Code; Claude.ai is not ChatGPT. Local skills, plugins and remotely hosted MCP apps have distinct setup requirements.
- Security, AI review, compatibility and popularity are separate records.

## Direct pull requests

Prefer the issue route for new repositories: it enriches metadata and attaches actual scanner/AI evidence. Direct PRs must validate against schema version 2 and change at most one entry for automatic review. IDs and canonical repositories must remain unique.

For a new manually authored entry, use `security.status: "unverified"`, `aiReview.status: "not-reviewed"` and `status: "pending"`. Supply the required platform, source and repository review fields. An existing entry is a structural reference, not evidence to copy. Do not reuse another entry's scans, dates or tests. The PR workflow reviews data but does not invent attestations inside your commit.

Older issue formats still work. Old-format direct PRs receive a conservative `normalized-catalog.json` artifact to help the author migrate; it proves neither compatibility nor approval. Fork workflows cannot access the owner's API secret: submit the repository URL through an issue. Maintainers handle bulk migrations and functional-test claims separately.

## Maintainer recovery

Inspect the failed workflow artifact and issue state. Correct missing API credentials, access, quota, branch rules or publishing setup, then start **Process submission → Run workflow** with the existing issue number. Do not fabricate green statuses, remove HIGH rules or accept incomplete AI output. Retry dispatches count toward the daily limit; timeouts are never retried automatically.

See [activation and stuck submissions](research/ACTIVATION.md) for this migration's rollout.
