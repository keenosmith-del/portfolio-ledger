# Engineering journal

Entries are recorded during work. This is an account of observed activity, not a reconstructed commit history. Times are UTC; reviewer-facing calendar context is Africa/Johannesburg (UTC+02).

## 2026-11-11 — Initial reconnaissance and foundation (recorded 07:02 UTC)

Starting state: commit `346d1dd` on `main`, clean working tree, one 19-byte README. Remote: `https://github.com/keenosmith-del/portfolio-ledger.git`. No applicable AGENTS.md found. Read the entire supplied master build prompt. Python default was 3.15.1; selected installed Python 3.12 for compatibility. Node 24.21.0, npm 11.19.0, Docker CLI 29.8.2. Checked environment variable names only; no secret values printed.

Objective: establish a PostgreSQL-first, explicitly transactional foundation and durable ingestion primitives before adding UI.

Changes: Python package, typed ORM models, adapter validation, financial helpers, authentication dependencies, source-scoped ingestion serialization, queue worker, finance services, Compose, Dockerfile, environment example. These are implementation in progress, not accepted product behavior.

Observed failures and corrections:
- First dependency installation failed because restricted execution could not resolve pypi.org. Re-ran with approved network access; installation succeeded.
- Docker engine initially stopped. `open -a Docker` failed to locate the application; explicit `/Applications/Docker.app` launched with approved access.
- First Compose invocation failed before creating resources because DEMO_PASSWORD was required. Generated a private local `.env` with a random password and mode 0600; no password committed or printed. Local PostgreSQL container then started.
- First Ruff pass fixed four import/unused-import issues; formatted ten files. Strict mypy passed for 12 source files. These are static checks only; no database tests had run at this entry.

Design decisions: ADR-001 and ADR-002. Initial migration generation started against actual PostgreSQL. Documentation requirement was added by the owner during this increment; this is the first journal entry and explicitly includes work preceding that instruction. No earlier journal entries or commits are invented.

Verification status: static typing passes. Migration, database behavior, browser workflow and performance remain pending. See iteration 001 and the evidence index.

### Foundation verification and first saved increment

Generated initial Alembic revision against the empty local PostgreSQL database; added a separate immutability-trigger revision. Applied both with exit 0. Seven financial boundary/CSV-safety tests passed in 0.04s. Ruff and strict mypy passed. Saving this verified infrastructure increment; import, HTTP, concurrency and full UI verification remain outstanding. No failed-to-passing application test exists yet, so none is claimed.
