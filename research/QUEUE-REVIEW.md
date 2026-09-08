# Queue security review — 2026-09-08

Interactive Codex AI review plus the unchanged static scanner. No submitted code, install commands, API integrations or deletion helpers were executed. No paid model API was called. This is a targeted source and catalog review, not a full audit, runtime test or security guarantee. Exact commits, times, scanner coverage and findings are in [scan reports](scans/); every warning has a numbered assessment in [queue-reviews.json](queue-reviews.json).

| Offering | Scan | Decision |
|---|---|---|
| Verify-First Skills | 35 text files, 2 skipped; 0 HIGH, 0 WARN | Approved with disclosed scope |
| Marketing Skills | 465 text files, 1 skipped; 0 HIGH, 66 WARN | Approved with service-access limitations |
| Anthropic Claude Cookbooks | 419 text files, 253 skipped; 0 HIGH, 39 WARN | Approved as an API reference, not a ready-to-run protected extension |
| Storage Cleanup | 9 text files, 0 skipped; 0 HIGH, 0 WARN | Not approved; removed from active catalog pending correction |

All four were already represented in the previously published catalog. This review adds evidence and withdraws one earlier approval; it does not add duplicates. The old anthropic-cookbook URL resolves to claude-cookbooks. The active catalog now has 55 entries; all 47 original IDs remain.

## Storage Cleanup: earlier approval withdrawn

The static scanner's zero findings do not establish safe deletion. At commit `435f8a9c634f32e1dd3010b3e992a6a213c4a579`, `scripts/staged-delete.ps1` has these source-level issues:

- Stage accepts an existing staging directory and writes a new `_manifest.json` after moving files. A second staging operation replaces the previous restore map. Destination numbering also restarts at zero.
- Purge checks only that a marker exists, then recursively deletes the entire staging directory, including unrelated pre-existing content. The marker does not prove that every item was staged by this tool.
- The restore map is written only after all moves. A mid-operation failure can leave moved files without a complete restore map. Restore uses forceful moves without a conflict confirmation.

Consequently the claim that staging is reliably reversible is unsupported. Required correction: dedicated fresh staging directory or validated append-only manifest, collision handling, durable recording of each move, purge limited to validated staged contents, and safe restore conflict handling. A new upstream revision must be scanned and reviewed before re-entry. The preserved [quarantined entry](quarantine/storage-cleanup.json) records `needs-review`; issue 28 and PR 27 remain open. No foreign deletion script was run to demonstrate these problems.

## Accepted offerings: limits that matter

Verify-First reads selected artifacts/audio and local Claude transcripts to calculate usage. Its lock check opens an existing artifact in append mode; its debugging helper invokes project tests. Do not describe the whole collection as incapable of running code. Claude Code setup is provider documented; Codex/ChatGPT support remains unverified.

Marketing's warnings concern 62 optional credential-using CLIs, three integration examples, and a defensive prompt-injection quotation. Credentials go to service endpoints; ActiveCampaign/Plausible endpoints are configurable, and some APIs use query credentials. These tools can send messages or change accounts. Use trusted configuration, narrowly scoped credentials and explicit approval for writes. No live integration was tested. The source claims Claude Code and Codex support and provides an installer; ChatGPT remains unverified.

Cookbooks are examples requiring their own dependencies, credentials and environment review. Installer scripts and container supply chains are not covered. The chief-of-staff example logs full commands locally, which can expose command-line secrets; its Edit hook also names a missing `report-tracker.py123`. Some Skills hooks merely warn and exit successfully. These are not security enforcement guarantees. The catalog presents the repository as a reference and does not claim platform installation support.

## Queue disposition

After verifying deployment, issues 21 (Marketing) and 24 (Cookbooks) and superseded PR 26 (Verify-First) can be closed without adding duplicate entries. PR 26 is not merged: its old schema and blanket read-only description are not adopted. Issue 28 and PR 27 stay open for correction. No external comments are sent by this review.
