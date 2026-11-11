# Deployment preparation and actual status

**No public frontend/API deployment has been created or verified.** Local images and stack verification are tracked in validation evidence. GitHub repository exists and authenticated GitHub access was checked, but GitHub authentication does not supply PostgreSQL/worker hosting credentials.

No Render/Neon/Cloudflare/Vercel/AWS environment credentials were present in the inspected environment variable names. No new cloud accounts, paid resources or pretend live URLs were created. The available static-site hosting workflow would not provision the required PostgreSQL/API/durable worker; publishing only that frontend would fail the product's acceptance criteria. Public writable demo also needs reviewer isolation/expiry/quota controls (see security notes).

## Container deployment checklist

- Provision PostgreSQL 16+ with TLS, backups and separate migration/runtime roles.
- Supply DATABASE_URL through secret management, plus private DEMO_PASSWORD for initial seed only.
- Run `alembic upgrade head` from backend as a one-off release task; then seed only explicitly synthetic demo namespaces.
- Run `uvicorn app.main:app --host 0.0.0.0` API and `python -m app.workers.runner` as separate long-lived services. Use `/ready` readiness checks and SIGTERM grace period sufficient for a bounded import. No BackgroundTasks durability assumption.
- Build frontend image with Nginx same-origin `/api` proxy. Replace Docker-internal hostname with actual private API upstream, or deploy all services on the same container network. Static frontend hosted separately requires a reviewed auth/domain proxy design; SameSite Strict is intentionally not disabled for convenience.
- Set APP_ENV=production, COOKIE_SECURE=true, explicit HTTPS ALLOWED_ORIGINS. Configure trusted reverse proxy and TLS. Production container compose overrides are operator-specific; shipped compose is loopback local development.
- Configure ingress body/time limits, read/write quotas, per-reviewer expiry/reset, session cleanup, rate-window retention and alerting.
- Verify migration from blank, restart persistence, browser login/import/replay/review/preview/export and recovery at the actual deployed HTTPS URL. Run load acceptance against an isolated namespace, never an existing shared financial database.

## Git publishing

Actual implementation branch and commits: `git log --oneline codex/portfolio-ledger-build`. Remote: `https://github.com/keenosmith-del/portfolio-ledger.git`. Changes are local incremental commits until explicitly pushed; no CI run is claimed unless Actions was actually triggered and inspected.

When ready to publish the branch:

```sh
git push -u origin codex/portfolio-ledger-build
```

Then configure the CI workflow and choose a backend/worker/database provider whose current plan explicitly supports persistent worker processes without unexpected charges. Pricing/free-tier availability is intentionally not asserted in this document.
