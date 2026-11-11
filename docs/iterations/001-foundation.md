# Iteration 001 — Transactional foundation (in progress)

Starting state and objective: empty initialized repository; provide real database schema and typed infrastructure supporting safe financial ingestion.

Decisions: synchronous SQLAlchemy sessions; PostgreSQL is authoritative; Alembic alone manages schema; rows are individually quarantined while each successful worker attempt commits atomically. Worker claim is a separate transaction with lease and bounded attempts. Financial corrections are explicit reversal plus replacement. Source IDs are scoped by portfolio and stable source key. Financial snapshot/reconciliation work will serialize with imports to prevent concurrent publication inconsistencies.

Code: `backend/app/db`, `core`, `domain`, `integrations`, `services`, `workers`; Compose and package configuration.

Executed: Python 3.12 virtual environment creation; dependency installation (initial DNS failure, approved retry succeeded); `docker compose up -d db` (initial missing environment error, corrected and succeeded); `ruff check backend --fix`; `ruff format backend`; `mypy backend/app` (12 files, success).

Defects: D001–D003 in defect log. No database or HTTP tests were yet executed at entry creation. Increment is not marked accepted until migration and invariant tests pass.

Final verification: pending, to be updated with observed results rather than forecasts.

Verification update: generated initial revision `aacf7692e44e` against local PostgreSQL and applied `alembic upgrade head`, including `b001` database immutability triggers, exit 0. `pytest tests/test_money.py -q`: **7 passed in 0.04s**. Strict mypy: success, 12 files. Migration command's zero exit indicates applied successfully; database invariant tests remain iteration 002 scope. Foundation infrastructure verified; application journey is not yet accepted.
