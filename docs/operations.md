# Local operation and recovery

Use README quick start. Run API and worker as separate processes or `docker compose up --build -d`. Named volume `ledger_data` preserves PostgreSQL across `docker compose down`/up. Do not use `down -v` unless intentionally discarding this synthetic database. Re-running seed uses stable receipt keys and does not inflate ledger totals or reset existing passwords.

Liveness `/health`; readiness `/ready` checks DB, applied schema revision and secure cookie configuration in production. Structured JSON request logs include correlation ID, method/path/status/duration, never request bodies/passwords. Worker emits job ID and duration. Audit events retain actor, operation, resource, correlation and state-change detail. The operations UI derives counts/timeline from database rows. Readiness is checked on demand, not represented as permanent green health.

## Worker lifecycle

1. Poll durable import_jobs. Select queued or expired-processing job with FOR UPDATE SKIP LOCKED.
2. Claim in a short committed transaction; increment attempts and set five-minute processing lease.
3. Process under job row lock plus portfolio/source advisory locks. Other portfolios can run concurrently.
4. Commit all effects, row outcomes and audit at once. Expected row errors are quarantined via savepoints. Programming/database failure rolls back attempt.
5. Expired claim can be reclaimed after process death; held row lock prevents another live worker taking the same in-flight transaction even if its lease expires. Maximum three attempts, then failed. Failed jobs may be explicitly replayed into new receipts with audit; original remains evidence.
6. SIGTERM/SIGINT requests graceful shutdown after current bounded attempt. A hard stop rolls back via connection termination; worker recovers after lease expiry.

`test_crash_recovery` injects RuntimeError after row four, verifies zero partial raw/ledger persistence, expires the claim, reprocesses and asserts no duplicate effects. `test_failed_worker_attempts_recover_and_stop` tests three real rolled-back attempts and terminal failure. Seed also creates `recovery.csv`: an intentional attempt rollback followed by successful attempt two, discoverable in worker diagnostics and audit, without additional financial effects.

## Operational limits

Per file: 8 MiB, 20,000 rows; bounded three-attempt processing; fixed-window mutation budgets. Full source imports per portfolio serialize. Reconciliation reads the portfolio's cutoff records in memory; leases use application paging after version selection. This suits bounded demonstrations, not very large multi-million-row portfolios. No scheduler, object storage, external integrations, email, telemetry collector or distributed queue is configured.

The measured 10k baseline is ~100.59s initial and 80.81s replay. Do not infer an SLA from one workstation run. Next performance step is profile round trips, stage/bulk insert validated rows and prefetch source mappings, then repeat the exact isolated acceptance benchmark with invariant suite. Do not remove uniqueness/triggers to make a benchmark look faster.

Back up PostgreSQL with tested provider snapshots/pg_dump in deployment; restore into isolated database and verify migrations before production adoption. This repository does not claim an executed backup/restore drill.
