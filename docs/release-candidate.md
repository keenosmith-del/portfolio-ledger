# Iteration 005/006 release candidate

Implementation, local acceptance and hosted code-candidate CI complete. **Public deployment NO-GO** pending actual HTTPS ingress, verified-TLS PostgreSQL runtime secrets, hosted backup/restore and alerting. No cloud resources or public app URL claimed.

Branch: `codex/portfolio-ledger-release-ui-v2`. Starting SHA `3a605a0b130a9ece50b9308cef198573b85383b8`, 14 inherited dirty files preserved. Implementation increment `7ed81c6`; final evidence/ownership correction is the subsequent commit (`git log -1`). Published with owner authorization; [draft PR #2](https://github.com/keenosmith-del/portfolio-ledger/pull/2) is open. Initial hosted run failed on bundled pip; corrected code candidate 65fdea6 passed full Actions https://github.com/keenosmith-del/portfolio-ledger/actions/runs/43027530061. Later evidence-only checks remain on the PR. Prior build PR #1 was already merged before this iteration.

Verified: neutral UI/login/shared primitives, source registry and historical migration, direct public mutation denial/synthetic scope, bounded secure sessions/CSRF/origins/Host/proxy controls, fail-closed production config, dynamic readiness with database/schema/table-owner rejection, explicit release migrations, non-root restricted containers, distinct runtime-role financial journey, local backup/restore and restart. Generated response DTOs, parser fuzz campaign, OS-image scans, isolated public writable review and hosted infrastructure remain deferred.

Evidence: [validation](validation.md), [design + all screenshots](iterations/005-design-system-and-navigation.md), [security](iterations/006-release-security.md), [10k JSON](evidence/acceptance-release-ui.json), [restore](evidence/backup-restore.json), [restart](evidence/persistence-release.json), [public review](evidence/public-review.json).

Actual verification: 41 backend tests / 35.88s / 85% / one upstream deprecation warning; six private Chrome cases / 33.1s and one public / 9.9s. Includes 36 screen/viewport combinations and selected WCAG A/AA/2.1 AA audits. Static/type/build/style guards pass. Dependency scanners find no known vulnerabilities (unpublished project package cannot be looked up on PyPI). Alembic metadata check clean. Production Compose rejects missing configuration and validates synthetic placeholders; actual hosted TLS is not tested.

10k import/replay: 190.983s / 82.724s, full 275.891s; 10,000 postings / ZAR 18,750,000.00 retained, two quarantines per receipt, no replay inflation. Dirty base 3a605a0 with concurrent work on Apple M5/16 GiB; no speedup claim. Full local restore matches 13 business table hashes and evidence triggers; restart preserves captured IDs and ZAR 19,500.00 local total.

Run `python3 scripts/init_env.py` then `docker compose up --build -d`, open http://localhost:5173, private DEMO_PASSWORD from `.env`, November 2026. Admin/analyst interactive; reviewer@portfolioledger.test read only. Password-free public testing and exact deployment/role commands are in [deployment](deployment.md). Final local stack is private mode.

Owner authorized branch publication and draft PR. Review visuals/checks in draft PR #2 before merge; do not deploy until hosted infrastructure gates pass.

Hosted code candidate: 41 backend / 22.74s, six private Chrome / 24.4s, one public / 3.4s; all checks passed. Linux 10k import/replay 87.758s / 55.098s, exact 10,000 postings / ZAR 18,750,000.00. See hosted-ci.json and acceptance-hosted.json. Public application hosting unverified.
