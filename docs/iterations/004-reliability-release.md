# Iteration 004 — Reliability, schema hardening and release

Starting state: connected frontend milestone `c89820a`; 24 backend tests, two passing browser tests, first 10k baseline. Objective: verify complete container startup/restart, close DB-boundary gaps, publish honest operational docs/CI.

Implementation: Makefile with unambiguous directories; GitHub Actions PostgreSQL/type/lint/build/test/acceptance/browser pipeline; Docker build contexts; safe init_env helper; real seeded recovery.csv failure/rollback then second-attempt recovery; source/publication/schema docs; threat model and deployment blockers; architecture ADR-004.

Final boundary audit added two direct DB tests. Both initially failed (2 in 0.74s); added new b002 migration for pricing ownership and one non-reversal event/revision regardless of kind. Added state/revision constraints without rewriting prior migration history. Full suite **26 passed, 1 upstream warning, 9.23s**, **85% coverage**; strict mypy and Ruff pass. Deleted accidentally tracked generated TypeScript build-state file and added ignore rule.

Container images built successfully. Switching from development processes to complete containers; final restart/browser/acceptance still pending. Existing GitHub account authentication verified; no hosting credentials/public deployment or hosted CI success claimed.
