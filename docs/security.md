# Security and demo boundaries

This local synthetic demonstration is **not approved for unrestricted public writable hosting**. Compose binds to loopback only. No customer records, real provider APIs, payment instructions, actual invoices or insurance decisions exist. The project has no affiliation with LeaseSurance, Octoco, MRI, Xero, Guardrisk or any real property-management provider.

Implemented: Argon2id password hashing; random opaque server sessions stored hashed; HttpOnly/SameSite Strict cookies; eight-hour expiry and logout revocation; server-issued CSRF token and explicit origin enforcement; portfolio access grants for every scoped route; composite lineage foreign keys; immutable evidence triggers; bounded uploads and paged results; allowlisted raw payload retention; escaped CSV cells; login/write rate windows; safe errors/correlation IDs; frontend no token persistence in localStorage. Tests exercise forged portfolio IDs, read-only role, CSRF/origin failures, invalid credentials, upload abuse and rate limits.

Demo identities: admin accesses both portfolios, analyst only Cedarstone, reviewer reads both. Password is supplied via private DEMO_PASSWORD, generated locally with `scripts/init_env.py`; seed never prints it or rotates existing hashes. Existing users persist across restarts. No password/account enrollment API is exposed.

## Threat model and open hardening work

- Malicious/accidental replay: checksum/idempotency conflict plus source/revision uniqueness and transactional locks. Stable source keys are a user responsibility in this demo; production should restrict them to integration configuration rather than arbitrary new namespaces.
- Guessed identifiers: scope all resource lookup and authorize portfolio before service invocation. Database ownership constraints are an additional barrier, not a replacement for auth.
- Uploads: 8 MiB read cap plus Content-Length guard, 20k rows, strict schema, no execution. Production ingress must enforce body limits for chunked multipart uploads too; local proxy is capped at 9 MiB. Arbitrarily nested JSON/untrusted multipart resource behavior deserves production fuzzing.
- SQL owner privileges: local development uses schema owner; production must separate migration owner from least-privilege runtime user. Owner can disable triggers, so the demo is not a tamper-proof external accounting record.
- Brute force: DB-backed fixed windows (10 login requests/minute/IP and 60 primary operation writes/minute/user). These are modest demo controls, not perimeter DDoS protection. Review actions are authenticated and bounded but not separately throttled. Add session-count/expiry cleanup and rate-window retention before sustained public use.
- XSS/exports: React escapes display, no HTML payload rendering, source shown as text, safe CSV prefixes. Nginx CSP/no-sniff/frame-ancestors; HTTPS/secure cookies required in production.
- Public demo isolation/reset: not implemented. Provision per-reviewer databases/schemas or isolated deployments with expiry, quotas and controlled reset before enabling public writes. Do not publish the current shared mutable database.
- Hosting: TLS, proxy trust, backup/restore drill, secret manager, monitoring/alerts and incident retention are operator tasks not verified in this local build. No claims of production-grade security or compliance.

Browser traces/error contexts can capture typed credentials. They are gitignored and remain local. Only sanitized benchmark JSON and authenticated screenshots without secret fields may enter evidence. Never commit `.env`, database dumps, tokens or raw runtime logs.
