> Update 2026-09-08: Website and Worker are deployed. The active catalog now contains 55 entries. Storage Cleanup approval was withdrawn after source review and the entry moved to quarantine. See [current queue decisions](QUEUE-REVIEW.md). The migration observations below describe the earlier state. Automated API review remains unavailable without a key.

# Live activation and recovery

Prepared 2026-09-08. Changes are local: no push, deployment, issue comment or paid OpenAI request has been performed.

## Observed failure

The [Process submission run 34072135893](https://github.com/Coingyy/skillshare/actions/runs/34072135893) for [issue 28](https://github.com/Coingyy/skillshare/issues/28) completed the Storage Cleanup scan, then failed in Claude processing. Its result had `is_error: true`, no model usage and no new catalog PR. The precise underlying credential/quota failure is not established by the log. Issue creation was not evidence of a catalog addition.

Read-only inspection found only `CLAUDE_CODE_OAUTH_TOKEN` in Actions secrets; `OPENAI_API_KEY` was absent. Pages used legacy main/root publishing. PRs [26](https://github.com/Coingyy/skillshare/pull/26) and [27](https://github.com/Coingyy/skillshare/pull/27) had Security-Check runs requiring approval; neither was changed. Issues 21/24 describe existing catalog entries and can be closed honestly after a verified deployment.

## Activation order

1. Add `OPENAI_API_KEY` in **Settings → Secrets and variables → Actions**. Use the owner's API project and usage controls. Do not put the key in code, catalog, Worker or conversation.
2. Review and publish the local migration to main. This is a catalog-wide maintainer change; the new one-entry PR rule is not its approval mechanism. The initial PR's trusted base also predates the new scripts/schema. Bootstrap using the recorded local validation and maintainer review, without claiming an API-reviewed PR.
3. Set **Settings → Pages → Source → GitHub Actions** and permit Actions PR creation. Retain branch protection; if it blocks a bot merge, the maintainer can review/merge its prepared PR.
4. Deploy the existing Cloudflare Worker from `worker/`, retaining its issue-only `GH_TOKEN`. The Worker does not receive the OpenAI key. Old minimal form payloads remain accepted.
5. Run **Publish catalog**. It stages public assets, deploys, fetches live skills.json, and compares the complete content before notifying/closing matching issues.
6. Confirm 56 live entries, including Storage Cleanup and Verify-First Skills. They are included in this locally reviewed migration; retries detect existing repositories before a paid review. Inspect PRs 26/27 and close superseded proposals manually after verifying that their content is represented.
7. For the first genuinely new suggestion, verify scan, AI evidence, exact PR diff, merge and Pages publication. This hosted end-to-end test remains outstanding because no API secret was available.

Visitors can submit while the owner PC is off. GitHub executes reviews/deployment. A processing limit or failed check leaves the suggestion pending instead of bypassing the safety gate.

## Recovery

- Missing key/model access/API credit: resolve setup, then start a new dispatch with the existing issue number. Keys and API response bodies are not logged.
- HIGH or uncertain AI result: inspect evidence and resolve the source issue; do not weaken rules.
- Merge blocked: inspect the PR and branch rules. Existing branches are never force-reset.
- Deploy/content mismatch: fix Pages and rerun Publish catalog. No published message precedes a successful comparison.
- Daily limit: dispatch pending issues on the next UTC day. No scheduler is configured to clear this queue automatically.

To pause intake, disable the Worker route or review workflow. For rollback, restore the prior catalog, schema, page and workflows together from version control, plus matching Pages settings. Keep issue history/reports. Rollback alone does not fix the old Claude workflow failure.
