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
