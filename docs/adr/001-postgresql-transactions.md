# ADR-001: PostgreSQL and synchronous explicit transactions

Date: 2026-11-11. Status: accepted for implementation.

Context: imports, correction chains and preview generation must survive retries and concurrency. SQLite would not exercise PostgreSQL locks, numeric behavior or schema constraints.

Decision: Python 3.12, synchronous SQLAlchemy sessions, psycopg 3 and PostgreSQL 16. FastAPI dependencies open explicit transactions. Alembic revisions define tables. Composite foreign keys enforce portfolio ownership for financial lineage. Transaction advisory locks serialize competing operations; database unique constraints remain the last line of defense.

Consequences: worker/API require PostgreSQL. A source's imports are serialized, favoring correctness over throughput. No in-memory substitute is accepted as integration evidence. Database append-only triggers will protect ledger and immutable snapshots against direct SQL updates/deletes.
