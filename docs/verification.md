# Verification guide

Run commands from repository root after setup and PostgreSQL startup:

```sh
make check
make test
make acceptance
# API, frontend and worker must be running for this:
make e2e
```

`make test` creates isolated PostgreSQL schemas, applies the actual Alembic chain and drops each schema in teardown. It never replaces PostgreSQL with SQLite. Configured database user requires CREATE SCHEMA for tests; use a dedicated test database in shared environments.

`make acceptance` creates its own temporary schema, migrates from blank, exercises both feeds and HTTP journey, then ingests 10k financial events twice and asserts receipts/ledger count/Decimal total. Prints machine-readable JSON after assertions; logs go stderr. A finally block removes its own schema only. Run with output redirected to private temporary paths if preserving runtime logs; copy only sanitized aggregate JSON to docs/evidence.

`make e2e` uses installed Chrome (`channel: chrome`) against local 5173/8000 and a separate worker. Tests read DEMO_PASSWORD from environment or private .env. It deliberately persists reviewer actions in the synthetic demo so reload survival is real. Browser traces can include typed credentials and remain gitignored. No trace-upload action is enabled in CI. Mobile test checks 390px viewport and absence of horizontal document overflow; table panels retain independent horizontal scrolling.

Actual results and failed-to-passing history: [validation](validation.md), [journal](engineering-journal.md), [defects](defects.md), [evidence index](evidence-index.md). Do not treat this command list as proof that a command was executed; only the dated result entries establish that.
