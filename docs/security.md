# Security and demo boundaries

Current release candidate is verified locally; **public deployment remains NO-GO until operator HTTPS/TLS, infrastructure, candidate CI and release checks pass**. No real customer records, provider APIs, payment instructions, actual invoices or insurance decisions exist. This independent project has no provider affiliation.

## Implemented controls

- Argon2id password hashes; random opaque sessions stored hashed; HttpOnly / SameSite Strict cookies; private expiry eight hours, public expiry one hour; logout revocation. Session caps: 20 private / 200 public concurrent sessions per identity. Expired sessions and rate windows older than one day are removed during rate checks.
- CSRF and explicit Origin checks; production only accepts configured HTTPS origins, exact trusted hosts and bounded explicit proxy trust. Every portfolio route checks grants. Authentication and business writes have independent DB-persisted rate windows; exception review is included. Failed requests do not roll back rate counts.
- **Canonical source registry:** uploads and replays require enabled portfolio/provider/source entries; worker rechecks on processing. Composite job-to-source FK and unique upstream account identity prevent callers minting namespaces or registering one upstream account twice. No HTTP registry-write endpoint; runtime database roles cannot edit registry. Additive b003 migrates historical identities **disabled**; explicit synthetic seed enables only atlaspm-demo / meridianrent-demo. Operators must review any other historical aliases before enabling them; historical ledger data is never merged, deleted or rewritten.
- Portfolio lineage FKs, immutable evidence triggers, NUMERIC/Decimal arithmetic, financial source publication cutoffs and durable worker retries remain enforced. Evidence can never be edited by runtime roles. Migration owner remains inherently privileged and must stay private.
- ASGI streaming-body cap before multipart/JSON parsing, 30-second receive timeout, 8 MiB file / 20,000-row bounds, recursion-safe JSON error handling, sanitized field allowlist and bounded pages. Nginx sets ingress body/read/connect/send limits. Text is escaped by React; downloadable CSV prefixes formula cells safely.
- Production configuration fails closed on insecure cookies, HTTP/wildcard/local origins or hosts, unbounded proxy trust, weak/default DB credentials and missing verify-full database TLS. `/ready` compares installed revisions to actual Alembic heads and rejects privileged/owner runtime roles in production.
- API/worker containers run UID 10001; Nginx UID 101 on port 8080. Read-only runtime filesystems, writable tmpfs, dropped capabilities and no-new-privileges. Explicit release container runs migrations separately from API boot. `app.operations.roles` applies separate API/worker grants as an owner-run release step; full financial regression is exercised under these separate roles.
- Uniform no-store/no-sniff/correlation/error headers, Nginx CSP and same-origin session routing. Dependency audit commands are included in CI; automated WCAG checks supplement manual visual and keyboard inspection.

## Public read-only review

`PUBLIC_REVIEW_ENABLED=true` exposes a bounded session-creation route, not a shared password. It requires an explicitly seeded dedicated `public-review@portfolioledger.test` reviewer, with grants exclusively to portfolios marked synthetic. The account has an unshared random password hash. Public browser can inspect source evidence, existing exceptions, previews, CSV and audit. Public reviewers cannot upload, replay, reconcile, resolve exceptions or calculate new previews, even by calling APIs directly.

Production public configuration requires `PUBLIC_DEMO_READ_ONLY=true`: **all** business mutations are blocked, including private admin sessions. Private interactive demonstrations run separately with private credentials and public mode disabled. No isolated writable public reviewer sessions are offered. Local development may exercise public reviewer behavior on loopback without being a public deployment.

## Remaining operator boundaries

Local Compose intentionally retains the private development database owner connection. Production uses the separate standalone Compose contract and externally provisioned verified-TLS PostgreSQL; never publish the development stack. Runtime grants must be reapplied after migrations adding tables; owner credentials must not be given to API/worker services. Grant installation is not a substitute for reviewing database PUBLIC privileges, role memberships and provider-specific defaults.

No cloud TLS endpoint, cloud backup schedule, incident alerting, secret manager, production perimeter/DDoS protection or externally hosted browser journey is claimed. The real backup/restore drill covers local PostgreSQL only. API response DTO generation and broader fuzz/load testing remain deferred. Dependencies and infrastructure require recurring maintenance; a point-in-time advisory scan is not a security guarantee.

Never commit `.env`, passwords, cookies, dumps, raw logs or browser traces. Screenshot evidence contains only credential-free login screens and authenticated synthetic records. Browser traces remain ignored and local.
