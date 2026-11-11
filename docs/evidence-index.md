# Reviewer evidence index

All results below were actually observed on 2026-11-11. Failed checkpoints remain in Git; no development history was reconstructed.

| Evidence | Artifact / command | Observed status |
|---|---|---|
| Starting repository and chronological increments | [Engineering journal](engineering-journal.md) | Empty initial repository → functioning local stack |
| Foundation | [Iteration 001](iterations/001-foundation.md), `52ecd33` | Migrated PostgreSQL; seven boundary tests |
| Genuine first red checkpoint | [Iteration 002](iterations/002-ingestion-api.md), `5f191c5` | Two failed / 15 passed |
| Immutable preview and transaction correction | `81fd5e6`, [D005](defects.md) | 17 passed |
| Connected frontend + cutoff refinement | [Iteration 003](iterations/003-frontend-and-cutoffs.md), `c89820a` | Browser journey/mobile green |
| DB-boundary hardening and recovery | [Iteration 004](iterations/004-reliability-release.md), `d741c76` | 26 PostgreSQL tests passed; 85% coverage; final container/browser/restart evidence below |
| Architectural evolution | [ADR-001](adr/001-postgresql-transactions.md), [002](adr/002-ingestion-publication.md), [003](adr/003-reproducible-cutoffs.md), [004](adr/004-database-boundary-hardening.md) | Explicit decisions/consequences, real regression basis |
| Actual defect corrections | [Defect log](defects.md) | Infrastructure, application and test defects distinguished |
| Test/build/container/browser commands | [Validation](validation.md) | Real commands, elapsed times and warnings |
| First 10k load/replay | [Baseline JSON](evidence/acceptance-baseline.json) | 100.590s import / 80.810s replay; count/total correct |
| Hardened-schema 10k repeat | [Repeat JSON](evidence/acceptance-hardened.json) | 100.555s / 63.949s; same count/total; no causal speedup claim |
| Authenticated rendered UI | [Desktop](evidence/overview-desktop.png), [mobile](evidence/overview-mobile.png) | Actual DB state; no password fields |
| Verification reproduction | [Verification guide](verification.md), [README](../README.md) | Commands and demo access process |
| Scope and release limitations | [Security](security.md), [deployment](deployment.md), [tradeoffs](tradeoffs.md) | Local synthetic demo; no public/hosted CI claim |
| Reviewer narration | [Walkthrough](reviewer-walkthrough.md), [application description](project-description.md) | Uses completed functionality only |

Full database/container stop/start persistence comparison passed: [sanitized JSON](evidence/persistence-restart.json), reproducible with `scripts/persistence_smoke.py`. Browser traces and raw runtime logs are intentionally untracked; do not upload credential-bearing traces as evidence. The screenshots show state after repeated real review actions, so exception/job counts legitimately differ between captures and a fresh seed.

Final post-restart browser journey/mobile: **2 passed in 6.9s**. Final static/type/build checks pass. No push, hosted Actions run or public frontend/API deployment is claimed.
