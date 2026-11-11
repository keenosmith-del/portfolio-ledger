# Iteration 002 — Import, authorization and finance API

Starting state: foundation commit `52ecd33`; migrated PostgreSQL schema and seven passing domain tests. Objective: exercise real database invariants and HTTP journey before interface work.

Changes: real FastAPI endpoints; persisted cookie sessions and CSRF; grants; bounded upload and login/write throttling; deterministic fixtures and seed; per-test isolated PostgreSQL schemas created through Alembic; concurrency, crash/recovery, IDOR and immutability tests. Added typed portfolio-entity base after mypy found six attribute/type errors in generic pagination. Strict mypy then passed 15 source files.

First integration run: `cd backend && ../.venv/bin/pytest -q` — **2 failed, 15 passed in 14.40s**. Both failing tests concern billing preview persistence: `test_reconcile_and_concurrent_preview` and `test_http_journey`. The service flushed a zero-total header and later updated its total; the database correctly rejected this under the immutable-evidence trigger. The HTTP handler could return 200 before transaction teardown failure, leaving a subsequent export returning 404. This is a real failed test result, retained in a red checkpoint commit, not a finished milestone.

Correction plan: calculate all lines and total before first header insertion; commit dependency transactions before returning success; serialize publication with financial snapshot reads; constrain cutoff queries to completed imports. Do not weaken immutability. Rerun affected tests, then suite.

Passing behaviors in this first run: identical replay, payload conflict, concurrent ingestion, out-of-order corrections, deterministic crash rollback and lease recovery, database immutability/composite scope constraints, portfolio IDOR, reviewer denial, upload rejection and bounded attempts.

Final verification: pending correction.

Correction and verification: calculate immutable header total before INSERT; use function-scoped FastAPI dependencies to finish transactions before returning HTTP success. Added portfolio-wide financial publication lock and completed-import cutoff filtering, plus audit-based exception state reconstruction. Full rerun: **17 passed, 1 warning in 13.70s**; strict mypy passed 15 files. The warning is upstream Starlette's httpx TestClient deprecation, not a failed test. The concurrency and HTTP regression tests both pass without weakening the database trigger. Import/API increment accepted for the tested scope. Historical cutoff regressions and performance remain next verification scope.
