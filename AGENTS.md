# PortfolioLedger contributor instructions

Read README.md, docs/domain-rules.md and the current engineering journal before changes. This is a PostgreSQL-first synthetic finance demo. Never add real personal/customer data, live financial actions, provider affiliations or unverified deployment claims.

## Mandatory engineering evidence

For each meaningful increment, record starting state, objective, decisions, code changes, actual tests/commands, observed results, defects/corrections and final verification **during work**, not only at delivery. Maintain:
- docs/engineering-journal.md (chronological; actual timestamps only)
- docs/iterations/ (milestone records)
- docs/adr/ (material architectural decisions)
- docs/defects.md, CHANGELOG.md, docs/validation.md and docs/evidence-index.md

An increment is incomplete until its implementation, appropriate verification and documentation are complete. Commit meaningful increments when authorized. Preserve genuine failed-to-passing test history and measured before/after evidence. Never fabricate elapsed times, test output, commits or development history; record dirty-tree/base-commit context for measurements. Keep runtime credentials, .env, raw logs and browser traces out of Git. Only sanitized aggregate evidence or authenticated screenshots without secret fields belong in docs/evidence.

## Invariants and checks

Use Decimal/NUMERIC for money and explicit transactions. Do not weaken database immutability/uniqueness/scope constraints to make tests pass. Changes to schema require a new Alembic migration, never rewriting applied revisions or create_all. All queries and mutations must respect portfolio grants and source lineage. Snapshot absence never deletes history; revision corrections reverse then replace. Worker processing must stay durable and recoverable.

Run `make check`, relevant PostgreSQL tests (`make test`) and full acceptance/browser verification when financial, transaction, schema or end-to-end changes justify it. Test schemas are isolated and migrated from blank; no SQLite substitution. Browser tests need running API/worker/web and private demo password. Document local vs hosted verification separately. No paid infrastructure, public writable demo or push/deployment claim without actual authorization and verification.
