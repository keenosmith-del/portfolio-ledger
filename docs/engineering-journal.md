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

## 2026-11-11 — Import/API integration, first red checkpoint

Implemented API and synthetic seed/fixture generator. Strict mypy initially found six generic model errors; added a typed shared portfolio model base and reran successfully (15 files). The first actual PostgreSQL integration suite returned **2 failed, 15 passed in 14.40s**. D005: immutable billing snapshot header was flushed before its final total was calculated. Database guard rejected the later update. HTTP teardown permitted an apparent success before rollback, discovered by subsequent CSV export 404. Saving failing regression tests and the observed result before correction. This is an intentionally incomplete checkpoint, not an accepted phase.

## 2026-11-11 — Immutable preview correction, green verification

Corrected D005 by calculating preview lines/total before header insertion. Applied function-scoped FastAPI transaction dependencies so commit failures cannot be reported as successful responses. Refined cutoff design: financial reads serialize with source publication, completed imports bound source eligibility, and exception state reconstructs from audit records at the cutoff. Rerun: **17 passed, 1 upstream deprecation warning in 13.70s**, strict mypy passes 15 files, Ruff passes. This is the observed red-to-green transition from checkpoint `5f191c5`.

Frontend development began with React/TypeScript, live API contract, all six operational views, source/report dialogs and CSV download. npm install completed: 72 packages, zero reported vulnerabilities. First build was invoked from repository root and failed ENOENT; corrected invocation uses frontend directory. Build/browser verification not yet claimed.
