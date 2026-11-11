# Tradeoffs and next engineering priorities

Verified capability is bounded synthetic finance operations, not a commercial property or insurance system.

1. **Correctness over bulk speed.** Row savepoints and explicit ORM queries make reasons/lineage clear. Measured 10k first import 100.59s and replay 80.81s; bulk staging and mapping prefetch are future optimizations requiring identical invariants and a measured comparison.
2. **Portfolio serialization.** Locks simplify correction/preview races. Different portfolios process concurrently. This is a deliberate modest-throughput design, not horizontal scaling evidence.
3. **Versioned source state.** Immutable lease terms and completed import cutoff avoid historical overwrite. Snapshots never infer deletions. Reconciliation v1 expects rent for leases active on month start; it does not calculate prorated rent, complex allocation waterfalls or claims.
4. **Manual typed API response contract.** TypeScript request/response interfaces are strict; OpenAPI request models are real. Explicit Pydantic response DTOs and generated client contract checks remain useful hardening work.
5. **Scope filters.** Server-side ledger/audit/job/exception/preview paging exists; lease latest-version selection and overview aggregation currently materialize bounded source data. Large-scale reporting needs SQL window selection and database aggregates.
6. **Local safe demo.** Three roles, explicit grants, CSRF, quotas and no live transactions. Per-reviewer public isolation/reset and real cloud deployment remain unimplemented. No AWS/S3, telemetry collector or scheduled imports are represented as configured.
7. **UUID storage.** IDs are random UUID strings in VARCHAR(36), easy for API portability. Native PostgreSQL UUID would reduce index size but requires an explicit migration if adopted.
8. **Source namespace configuration.** One adapter per portfolio; source key entered at import. Production should make source configuration an admin-managed durable entity with bounded stable keys.
9. **Append-only evidence.** DB triggers enforce application-level immutability; a superuser/owner is outside that protection. Migration and runtime roles must be separated for hosted use.
10. **CI is code, not a claimed green run.** Local checks/build/browser evidence exist; hosted Actions success only after push and actual run inspection. Upstream Starlette TestClient currently emits an httpx deprecation warning.

First follow-up: tighter generated API contracts; profile/stage import data, comprehensive malicious parser fuzzing, isolated reviewer lifecycle, then an approved TLS deployment and backup restore drill. No optional claims/AI features are added before these core operational concerns.
