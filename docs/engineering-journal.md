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

## 2026-11-11 — Historical publication refinement

A first cutoff test without pre-existing leases passed but did not exercise ledger effects; strengthened the case with previously published leases and a later financial import. Targeted regression then failed: expected two missing charges before later batch publication, observed one (1 failed in 0.56s). Found the ledger query joined ImportJob but lacked its completed-at predicate; lease/raw queries already had it. Corrected ledger predicate; rerun pending. This distinguishes a weak initial test from the later reproducer rather than claiming the first test proved the invariant.

Frontend `npm run build` from frontend completed: strict TypeScript and Vite succeeded, 1,580 modules; 265.29 kB JS (80.80 kB gzip), 20.69 kB CSS, build 11.68s. Live API seeded, local Vite/API/worker started. Chrome journey/mobile tests written and launched. A repeated root-directory npm invocation failed ENOENT; commands will be centralized in Makefile to prevent this operator error.

### Browser correction sequence

After the origin fix, mobile viewport test passed. Journey first exposed stale feedback timing: success notice was rendered before refreshed import history, so the old batch could be inspected (1 failed / 1 passed, 11.5s). Moved notice emission after data reload. Next run advanced through replay/source/reconciliation/review to billing, where the test incorrectly assumed decimal-point formatting; browser's en-ZA uses comma. Corrected only the display assertion to accept locale separators, preserving exact Decimal API and CSV assertions (1 failed / 1 passed, 13.4s). Added Escape handling, focus containment/restoration for dialogs, removed externally fetched fonts and formatted frontend for reviewability. Running next verification before acceptance.

The 10k acceptance run has completed its first import: worker observed **100,429 ms** processing time. Replay is still running; no final benchmark result yet. This is a baseline, not a claimed performance improvement.

## 2026-11-11 07:25:42 UTC — Acceptance and first load baseline

Full isolated acceptance completed successfully: both provider HTTP imports, source-backed leases/ledger, reconciliation, audit review, idempotent preview and CSV, then deterministic 10k financial events and replay. Imported 10,002 accepted source rows (two leases included), quarantined two; replay produced 10,002 duplicates and two quarantines, zero accepted. Exactly 10,000 ledger entries remained, total ZAR 18,750,000.00. Initial import 100.590s, replay 80.810s, full run 182.079s. Checked in sanitized machine output; no credential traces included. This is an intentionally honest performance baseline, with no before/after improvement asserted.

Browser rerun then revealed navigation accessible-name instability after accumulated exception counts. Added stable aria-label, keeping visible counts. Mobile continued to pass. Journey remains unaccepted until rerun passes.

## 2026-11-11 — Browser milestone green, container build

Chrome reviewer journey and mobile viewport now **2 passed in 7.3s**. The last test correction selected Ledger explicitly after reload; backend persistence was intact and only local UI mode reset. Expanded worker/error/revision suite **24 passed in 8.03s**, 85% coverage (larger seed-code denominator). Container builds succeeded for all three app images. Recording milestone before release/container persistence work. No hosted CI or public deployment result is inferred from these local checks.

## 2026-11-11 — Final database-boundary audit

Added direct-DB tests beyond the already passing API authorization/source service tests. Both failed (2 failed in 0.74s): pricing FK linked only global pricing ID, and ledger's type-inclusive unique constraint permitted a second posting of another kind with same event/revision. These were blocked by current service logic but not database boundary. Add migration `b002` with composite pricing scope and partial uniqueness across non-reversal types; keep reversal coexistence. This is explicit schema evolution after initial applied migrations, not rewriting history. Also adding positive revision and row/job validity checks.

## 2026-11-11 — Database hardening green and release checkpoint

Added b002 as a new migration, enforcing pricing portfolio ownership and type-independent non-reversal event identity. Both failing direct-DB tests now pass; complete suite **26 passed / one upstream warning in 9.23s**, 85% coverage. Strict mypy passes. Added durable recovery fixture to seed (real injected rollback then second attempt), CI and operational documentation. Container runtime verification next; no cloud resources created. Removed accidentally tracked tsconfig.tsbuildinfo and ignored generated build-state files. No claimed bulk-performance improvement; repeat acceptance planned because schema invariants changed.
