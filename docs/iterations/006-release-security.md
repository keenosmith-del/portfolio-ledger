# Iteration 006 — Release security

Status: implementation and local acceptance complete; public release remains NO-GO pending hosted gates. Base 3a605a0, dirty inherited changes preserved.

Five actual failing tests captured before changes (5 failed / 1.39s): arbitrary source accepted, no dynamic head helper, early error headers missing, unsafe production config accepted, no public reviewer.

Registry migration b003 retains existing source keys and evidence; historical identities default disabled, with only explicitly seeded fictional accounts re-enabled. Registry mutation is an operator/migration responsibility, never an upload side effect. Unique upstream account prevents duplicate registrations of one configured feed. Public demo creates only a scoped read-only session, with a global business-write kill switch in production public mode. Same-origin session routing remains mandatory. Verification pending.

## Verified implementation checkpoint

39 backend tests pass (34.13s, 85% statement coverage, one upstream warning). Original invariants remain green. New coverage includes historical b002 receipt retained unchanged under b003, alias rejection/no financial inflation, unique upstream identities, legitimately independent accounts, disabled source replay and cross-portfolio registry. Public reviewer/session routes enforce grants and reject non-synthetic scopes; global public mode denies even admin business writes. Streamed oversize bodies and forged Host fail. Configuration rejects local/default production values and validates a representative TLS/runtime contract.

Separate API/worker roles are exercised by actual authenticated upload -> worker processing -> ledger -> reconciliation -> preview -> CSV, including production readiness. Neither role can disable evidence triggers, truncate, modify/delete posted ledger or mint registry entries. Worker cannot read user/session/rate/grant tables. Sessions expire, clean up and enforce active-count caps; public sessions are one hour, private eight hours. API migration ownership is rejected at production readiness.

Non-root restricted runtime containers built and started successfully. Explicit migration/seed release service upgrades existing populated volume; API no longer migrates on ordinary boot. Standalone production Compose has no local database fallback; operator HTTPS ingress/TLS DB/secrets are still required. Local backup/restore passed after a genuine target-schema conflict correction; see backup-restore.json. Dependency scans report no known vulnerabilities at verification time. Public-browser, restart and final candidate verification continue in journal; hosted CI/release unverified until explicitly performed.

Final acceptance: 41 backend tests pass (35.88s, 85%); a genuine schema-owner privilege reproducer failed before database/schema ownership guards were added. Separate-role financial journey remains green and rejects temporary runtime schema ownership at production readiness. Public browser denies all five mutation APIs and leaves business records unchanged; private/public Chrome total seven cases passed. Local restore and full stop/start verified; source/worker/money schema unchanged since successful 10k run. No hosted CI/public deployment claim.

Latest final checks include corrected Nginx readiness Host forwarding (D025): six private cases pass in 33.1s, public case in 9.9s, real browser readiness 200 and dialog asserts ready/b003. Private stack restored and healthy.
