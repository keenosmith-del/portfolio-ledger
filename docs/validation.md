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
