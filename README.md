# skillshare_

A shared catalog for Claude Code, Codex and ChatGPT, with platform-specific setup evidence and separate security and AI reviews.

[Open the catalog](https://coingyy.github.io/skillshare/) · [Submit an offering](https://coingyy.github.io/skillshare/#submit) · [Contributing](CONTRIBUTING.md)

The website reads `skills.json`. Topic, AI program and offering type are independent filters. An offering can support multiple programs. The existing English interface and visual design are retained.

## Evidence labels

- **Provider documented:** the provider describes the named program and setup. This is not a functional test.
- **Self-tested:** a dated test record names the tester and result. No catalog entry currently claims this status.
- **Not yet verified:** evidence is missing or incomplete. A `SKILL.md` alone does not establish compatibility.
- **Scan: no findings / warnings reviewed:** dated static scan evidence names the scanned commit. Dependencies and runtime behavior are not tested.
- **Historical scan label:** an old Verified label without a dated report. It never becomes tested compatibility.
- **AI review:** separately records the model, date and evidence. AI approval is mandatory for automatic acceptance and cannot override HIGH scanner findings.

Star counts are dated GitHub snapshots, not safety or quality ratings. See [the research report](research/REVIEW.md), [individual decisions](research/ENTRY-REVIEW.md), and [repository observations](research/repositories.json).

## Submission and publication

1. The website sends an anonymous suggestion to the Cloudflare Worker. GitHub creates an issue; HTTP 202 means **received**, not published.
2. `process-submission.yml` resolves the public repository and scans an exact commit without running its code. HIGH findings stop processing.
3. OpenAI reviews bounded source excerpts, purpose, installation evidence and every warning. It has no tools or repository write access. Missing credentials, refusal, incomplete output or uncertain approval stop processing.
4. Trusted Python code validates the result, preserves all existing entries, appends one new entry, and creates a PR. It checks the exact commit and changed files before recording the completed scan/AI status and requesting a merge. Branch-protection failures require maintainer action.
5. `publish.yml` deploys the current main catalog through GitHub Pages. It then fetches the deployed `skills.json` and compares the entire deployment artifact. Only that successful comparison allows a published notification and issue closure.

Failures leave the issue open with an attention message and diagnostic artifacts. The site keeps the submission tracking link and checks its loaded catalog for the repository. Issue creation never implies publication.

Direct PRs execute trusted base-branch code and read the proposed catalog as data. Automatic review permits one changed entry per PR. New scan/AI attestations cannot be self-authored in a PR. The specifically named bot submission branches already receive both reviews before PR creation and do not cause a second paid call. Other bots are reviewed normally. Forks do not receive the API secret; use the website/issue route for trusted processing. Do not execute untrusted PR code with secrets.

## Live setup and costs

The September 2026 changes are local; see [activation and recovery](research/ACTIVATION.md). Add `OPENAI_API_KEY` as a repository Actions secret, publish the migration to main, set Pages source to **GitHub Actions**, and deploy the existing Worker project. Permit Actions to create PRs; retain branch rules and use maintainer merges if necessary. The Worker only receives its existing issue-only GitHub credential, never the OpenAI key. API usage is billed separately from ChatGPT subscriptions.

The model is `gpt-5.4-mini-2026-03-17`. Each job can make one request with at most 100,000 input bytes and 5,000 output tokens. There are no automatic API retries. At most ten workflow runs across submission and PR review are admitted per UTC day; rerun attempts beyond the first are blocked. Start a new dispatch to retry, which counts toward the daily limit. Non-billable failures also count. GitHub counters and concurrent triggers are not a financial ledger: these are processing limits, not a guaranteed currency spending cap. API account usage controls remain separate.

At the model's [listed price](https://developers.openai.com/api/docs/models/gpt-5.4-mini), 20,000 input tokens plus 3,000 output tokens cost approximately US$0.0285. Actual use varies with repository size and output; prices may change. Visitors need no API key or paid ChatGPT subscription to browse or submit. The owner pays for reviews; third-party offerings can have their own requirements and prices.

## Local validation

```sh
python -m pip install -r scripts/requirements.txt
python scripts/catalog.py
python -m unittest discover -s tests -v
node --test tests/worker.test.mjs
python -m http.server 8080
```

Open `http://localhost:8080`. Optional UI tests use Playwright: install it in your development environment, or set `PLAYWRIGHT_MODULE` to an existing module and `BROWSER_PATH` to Chrome, then run `node tests/browser.cjs`. All external requests and submissions are intercepted. Screenshots/results go to ignored `.test-output/`.

```sh
python scripts/security_scan.py --repo https://github.com/owner/repository --report security-report.md --json-report scan.json
```

The scanner retains its existing rules and contextual downgrades. It inspects supported text files up to 512 KiB and records skipped files. It is a pattern scanner, not a complete malware, dependency or runtime audit. Research never installs or executes third-party skills.
