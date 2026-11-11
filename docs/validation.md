# Validation evidence

## 2026-11-11 — Foundation static checks

Environment: macOS arm64, Python 3.12, Node 24.21.0, Docker Desktop, PostgreSQL 16 container. Starting commit `346d1dd`; checks apply to uncommitted foundation increment.

Commands actually executed:
- `.venv/bin/ruff check backend --fix`: four findings fixed; no remaining findings.
- `.venv/bin/ruff format backend`: ten files formatted, three unchanged.
- `.venv/bin/mypy backend/app`: success, 12 source files.
- `docker compose up -d db`: local database container started, after private environment configuration.

Database migrations, integration tests, frontend, browser tests and benchmark: not yet executed at time of this entry. Results will be appended as work proceeds.

Foundation verification: `cd backend && ../.venv/bin/alembic upgrade head` exited 0 against fresh PostgreSQL. `../.venv/bin/pytest tests/test_money.py -q`: **7 passed in 0.04s** (rounding, month/leap-day/Johannesburg boundaries and CSV formula escaping). This does not establish ingestion or API correctness yet.

## First integration run (red checkpoint)

Starting foundation commit `52ecd33`, in-progress API/test changes. Command: `cd backend && ../.venv/bin/pytest -q`. Result: **2 failed, 15 passed, 11 warnings in 14.40s**. Failing: `test_reconcile_and_concurrent_preview` (immutable header UPDATE rejected) and `test_http_journey` (CSV 404 after rollback). Temporary isolated PostgreSQL schemas used, initial migration applied for every test. See D005 and iteration 002. No passing finance milestone claimed at this point.

## Integration correction (green)

Command: `cd backend && ../.venv/bin/pytest -q` after immutable-header and transaction-scope fixes: **17 passed, 1 warning in 13.70s**. `mypy backend/app`: success, 15 source files. The upstream Starlette TestClient httpx deprecation remains. Concurrent ingestion, preview uniqueness, deterministic crash recovery, append-only trigger, composite FK isolation, HTTP lifecycle/export, IDOR, read-only role, CSRF, bad upload and attempt limits now exercised successfully. This result precedes the frontend and larger acceptance benchmark.

## Historical cutoff and expanded suite

`pytest tests/test_operations.py::test_cutoff_excludes_late_financial_publication -q`: **1 failed in 0.56s**, initially. After adding the missing ledger publication predicate: `pytest -q --cov=app --cov-report=term-missing` — **22 passed, 1 warning in 8.04s**, **86% total statement coverage**. Tests apply Alembic migrations in fresh isolated PostgreSQL schemas; no SQLite.

Frontend initial production build: `cd frontend && npm run build` — strict TypeScript and Vite passed, 1,580 transformed modules, JS 265.29 kB / gzip 80.80 kB; CSS 20.69 kB / gzip 5.30 kB; Vite build 11.68s. First Chrome E2E run: **2 failed** during login, origin allowlist mismatch (127.0.0.1 vs localhost). Correction applied, rerun pending. Artifacts intentionally untracked.

## 10,000-event measured acceptance baseline

Executed `.venv/bin/python scripts/acceptance.py` against PostgreSQL 16, Darwin arm64/Python 3.12.15. Completed **2026-11-11 07:25:42 UTC**. Base commit `81fd5e6`, in-progress uncommitted frontend/cutoff/acceptance changes (not represented as a clean-commit benchmark). Machine output: [baseline JSON](evidence/acceptance-baseline.json).

Full HTTP journey, both adapters, evidence review, duplicate preview and CSV export passed in the temporary migrated schema. Deterministic artifact 715,499 bytes, **10,000 financial events + two lease rows + two deliberately invalid rows**. Initial receipt: 10,002 accepted / 0 duplicate / 2 quarantined. Replay: 0 accepted / 10,002 duplicate / 2 quarantined. DB after replay: **10,000 ledger entries; ZAR 18,750,000.00**. Initial enqueue+processing **100.590s**, replay **80.810s**, full acceptance **182.079s**. Worker processing-only logs: 100,429ms and 80,646ms. This is one local baseline, not a production throughput/load SLO or an improvement claim. Isolated schema removed in finally. 50,000-event stretch target not executed.

## Browser milestone and reliability regression expansion

`cd frontend && npm run test:e2e`: **2 passed in 7.3s**, real installed Chrome against local API/Vite/PostgreSQL/separate worker. Full reviewer journey + 390px mobile; no horizontal document overflow. Historical browser failures/corrections are recorded as D008–D012. Backend `pytest -q --cov=app --cov-report=term-missing`: **24 passed, 1 warning in 8.03s**, **85% coverage**. Added worker infrastructure-failure retry cap and unchanged-revision conflict tests. Coverage denominator increased with recovery seed code; earlier 86% is not claimed as a lasting final percentage.

`docker compose build`: API, worker and Nginx frontend images all built successfully. Full container startup/restart verification still pending at this entry.

## Final schema boundary verification

Added two direct-SQL tests: cross-portfolio pricing reference and duplicate event/revision under a different kind. Initial targeted result **2 failed in 0.74s** (both missing IntegrityError). New migration b002 enforces both below service layer. Full `pytest -q --cov=app --cov-report=term-missing`: **26 passed, one upstream warning in 9.23s**, **85% coverage**. Strict mypy passes (15 files). Actual failed-to-passing reason and migration documented in ADR-004.

## Complete container stack and final static checks

`docker compose up --build -d`: built and launched all services; API and PostgreSQL reported healthy, worker/web running. Existing populated database upgraded to **b002**. `cd backend && ../.venv/bin/alembic check`: **No new upgrade operations detected** (exit 0). Recovery seed persisted **attempts 2**, accepted 0, duplicate 7, quarantined 2. Demo ledger before final container browser run: **9 entries, ZAR 19,500.00**; preview count 3 at that observation (later user/browser actions may add previews).

`make check`: Ruff lint/format pass, 25 files formatted; strict mypy success 15 app files; frontend Prettier passes; strict TypeScript/Vite build passes (JS 266.11 kB / gzip 81.08 kB; CSS 20.56 kB / gzip 5.21 kB; Vite 1.77s). `make e2e` against built Nginx frontend + container API/worker: **2 passed in 7.5s**. Local browser artifact captures logged-in synthetic views only; credential-bearing traces remain ignored.

## Hardened-schema 10k acceptance repeat

Repeated `.venv/bin/python scripts/acceptance.py` after b002, base commit **d741c76**, docs working tree dirty (reported by script). Completed **2026-11-11 07:36:39 UTC**; [machine output](evidence/acceptance-hardened.json). **Passed** full HTTP journey and 10k replay invariants. Exact same 715,499-byte deterministic fixture and receipts/totals as baseline. Initial import **100.555s**, replay **63.949s**, full acceptance **165.238s**. Worker-only times 100,394ms and 63,775ms. Final: **10,000 financial ledger entries / ZAR 18,750,000.00**, no inflation. This is a second observation with a hardened schema and concurrent local container work; no controlled performance optimization or causal speedup is claimed. Temporary schema cleaned on exit.

## Full stop/start persistence verification

After the hardened acceptance schema was cleaned up, saved IDs for ledger, leases, previews/lines, audit, exceptions and jobs plus ledger total. Rotated generated local demo credential and revoked debug sessions (secret never committed). Executed **`docker compose down` then `docker compose up -d`** without removing named volume. API/DB healthy after restart. Command `.venv/bin/python scripts/persistence_smoke.py verify /tmp/portfolioledger-before-restart.json`: **passed** exact pre/post ID and total comparison. Counts at the comparison boundary: 9 ledger, 3 leases, 4 previews, 8 preview lines, 31 audits, 52 exceptions, 9 import jobs; ledger total **ZAR 19,500.00**. These are accumulated synthetic reviewer state, not benchmark schema counts. [Sanitized result](evidence/persistence-restart.json). Browser actions after comparison legitimately add review/history rows.

## Final local audit

Post-full-restart `make e2e`: **2 passed in 6.9s** (rotated credential login, reviewer journey, mobile). Final `make check`: Ruff lint and 26-file formatting pass; strict mypy 15 app files pass; frontend Prettier/strict TypeScript/build pass. `git diff --check` clean. Current generated credential scan over tracked content passed; `.env` is not tracked. Existing GitHub URL verified read-only with `gh repo view`; public repository default branch main. No push or hosted Actions run executed, no public frontend/API deployed, no paid cloud resource provisioned. These limits are deliberate and documented, not hidden verification successes.

## Iteration 005/006 — release/UI candidate (2026-11-11)

Starting SHA 3a605a0, branch codex/portfolio-ledger-release-ui-v2, 14 inherited dirty files preserved. Actual baseline: formatting failed on 11 files; database first unavailable (7 tests passed/19 infrastructure setup errors); approved local rerun **26 passed / 13.36s / 85%**; Chrome **2 passed / 9.6s**. Baseline screenshots captured before design edits.

New failing regression checkpoint: **5 failed / 1.39s** (source namespace acceptance, readiness helper missing, early-error headers, unsafe production defaults, public reviewer absent). First correction rerun **4 passed/1 failed / 2.83s** (headers), then **31 passed / 18.86s** after correction. Expanded registry/role suite **35 passed / 56.94s** during concurrent build. Added historical migration, strict production cases, session bounds and full API/worker journey under separate runtime roles: **39 passed / 34.13s / 85% coverage**, one upstream Starlette/httpx warning.

`make check`: Ruff lint/format, strict mypy (20 files), Prettier, strict TypeScript, production Vite build and token guard pass. `make e2e` against rebuilt non-root Nginx/API/worker/PostgreSQL: **6 passed / 56.5s**, original assertions retained. Includes 36 view/viewport combinations (six screens x six widths), >=40px inputs/buttons, no page overflow, internal table scrolling, search/empty, keyboard focus/Escape/restoration, private reviewer read-only and CSV, sessions, login + all screens automated axe WCAG A/AA/2.1 AA. Automated audits do not replace manual accessibility review.

Manual visual review: actual before overview/login and after login, overview, integrations, leases, source modal, reconciliation, billing, audit, mobile and tablet screenshots. Neutral colors, pill controls, readable labels and confined table scrolling checked; metric-note spacing corrected afterward. Screenshot directories [before](evidence/ui/before), [after](evidence/ui/after). Credentials absent; traces/raw logs excluded.

`pip-audit` with no advisory suppressions: no known vulnerabilities; unpublished local `portfolio-ledger` package cannot be checked on PyPI. `npm audit --audit-level=high`: zero vulnerabilities. CI includes these scans; image OS packages are not represented as scanned.

`docker compose up --build -d`: explicit release job migrated b003 on the existing volume, API healthy, separate worker and non-root Nginx running with read-only runtime filesystems/capability restrictions. Historical migration test also applies b003 over a real b002 receipt and verifies unchanged historical row plus disabled registered identity.

`make acceptance`: [sanitized output](evidence/acceptance-release-ui.json). **Passed**, initial **190.983s**, replay **82.724s**, full **275.891s**; 10,002 accepted rows / two quarantines, then zero accepted / 10,002 duplicates / two quarantines. **10,000 postings / ZAR 18,750,000.00**. Darwin arm64/Python 3.12.15, dirty base 3a605a0, concurrent verification. This is slower than historical runs; no controlled performance conclusion is supported.

`.venv/bin/python scripts/backup_restore.py`: first restore into new target failed on default public schema; corrected disposable-target restore flags. Repeat **passed**: source unchanged, 13 business table hashes/counts equal, ledger ZAR 19,500.00, restored immutability trigger rejected mutation. [Evidence](evidence/backup-restore.json). Private dump and disposable database removed. This verifies local recovery only, not hosted backups.

Hosted candidate CI, public HTTPS release and cloud restore remain unverified; public release is NO-GO pending those gates.

Final backend expansion: **40 passed / 18.34s / 85%**, including synthetic-scope revocation after public login. Public Chrome check initially exposed two dialog-test timing/focus assumptions and an existing heading locator typo; after corrections **1 passed / 4.2s**. All five business mutation APIs returned 403 and before/after business IDs/ledger total matched: [public review evidence](evidence/public-review.json). Nginx production syntax passed in actual non-root image; production Compose refuses missing values and validates with synthetic placeholders. Alembic check reports no pending upgrade operations. Runtime IDs verified 10001/10001/101.
