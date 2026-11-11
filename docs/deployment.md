# Release deployment contract

**Current verdict: NO-GO for public deployment.** No public URL or cloud infrastructure is claimed. Local full-stack verification is documented separately in validation. Operator-supplied HTTPS ingress, TLS PostgreSQL, role secrets, backup scheduling and alerting must be configured and verified, and latest branch checks must pass before release. Full code-candidate Actions has passed.

## Verified local workflow

```sh
python3 scripts/init_env.py
docker compose up --build -d
# release migrates and explicitly seeds; ordinary API startup never migrates
make check
make test
make acceptance
make e2e
.venv/bin/python scripts/backup_restore.py
```

Open http://localhost:5173. Use private DEMO_PASSWORD in `.env`, never paste it into source control. Admin and analyst are private interactive accounts; reviewer@portfolioledger.test is read only. Select November 2026. The standalone public reviewer has no published password.

To exercise the password-free reviewer locally, with all business APIs locked:

```sh
PUBLIC_REVIEW_ENABLED=true PUBLIC_DEMO_READ_ONLY=true docker compose up -d api
npm --prefix frontend run test:public
# Restore the private interactive local configuration:
docker compose up -d api
```

Click **Explore read-only demo** on sign-in. Inspect imports/evidence, ledger, existing exceptions, billing preview CSV and audit. Public mutations return 403. This is loopback testing, not public hosting.

## Production topology and explicit release

Supported shape: HTTPS ingress -> Nginx/React same origin -> private API, verified-TLS PostgreSQL, separate long-lived worker. Standalone `compose.production.yaml` has no development DB/password fallback and publishes only loopback Nginx port 8080. Operator must front it with HTTPS, keep API/DB private and restrict ingress/proxy network trust. `frontend/nginx.production.conf` asserts HTTPS only behind that ingress; do not expose it directly over public HTTP.

Supply secrets privately (never CLI literals or committed files):

| Variable | Required meaning |
|---|---|
| MIGRATION_DATABASE_URL | Owner PostgreSQL DSN, TLS verified by operator, one-off release/role job only |
| API_DATABASE_URL / WORKER_DATABASE_URL | Distinct non-owner runtime DSNs, private passwords >=20 chars, `sslmode=verify-full` and trusted CA material |
| PRODUCTION_ORIGINS | JSON list of exact HTTPS browser origins |
| PRODUCTION_HOSTS | JSON list of exact allowed hostnames matching origins |
| PRODUCTION_PROXY_IPS | JSON list of trusted Nginx IP addresses or bounded private CIDRs; no wildcard trust |
| API_DB_ROLE / WORKER_DB_ROLE | Distinct dedicated database role names |
| API_DB_PASSWORD / WORKER_DB_PASSWORD | Private initial role credentials, >=20 chars; owner job leaves existing passwords unchanged |
| DATABASE_SCHEMA | Target schema, default public, for owner-run runtime grants |

Never run the normal app with migration-owner credentials in production. `/ready` rejects owner membership and privileged roles. Provision production CA certificates as operator-managed read-only mounts if required by the DB provider. No TLS verification disabling is supported.

1. Review historical source inventory, ownership and existing PUBLIC grants. Back up before migration; never reset an existing database. Registry b003 preserves all keys disabled until explicitly reviewed. Provision/enable legitimate source accounts through owner-controlled release SQL; uploads cannot do it. The unique `(portfolio_id, adapter, upstream_account)` must identify an independently authorized upstream account, never a second alias for one feed.
2. Run migration as explicit release task:

   ```sh
   docker compose -f compose.production.yaml build
   docker compose -f compose.production.yaml run --rm release
   ```

3. In an explicitly synthetic environment only, seed through a private owner job with `SEED_SYNTHETIC_DEMO=true` and a private DEMO_PASSWORD. Do not seed arbitrary existing production/customer data. For the local owner-run executable the command is `make seed`; production operator must provide the target owner DSN privately. Seed prepares existing reconciliation/preview records for read-only browsing.
4. Apply runtime roles with migration owner DSN and role/password environment variables in an owner-controlled shell:

   ```sh
   APP_ENV=development .venv/bin/python -m app.operations.roles
   ```

   This requires MIGRATION_DATABASE_URL and role secrets, and rejects privileged/inheriting/table-owner roles. It revokes schema CREATE from PUBLIC and grants only application operations. Reapply grants after future table migrations. Verify database-level PUBLIC/default privileges and revoke unrelated role memberships before exposing the service.
5. Start runtime independently of release jobs:

   ```sh
   docker compose -f compose.production.yaml up -d api worker web
   ```

6. Verify actual HTTPS cookies, exact-origin/Host/proxy handling, current Alembic readiness, role isolation, denied direct public writes, source evidence and CSV from a real browser. Verify worker recovery and restart persistence. Schedule encrypted backups and perform a restore drill in the hosted environment. Configure error/availability alerts and retention. Only then consider public release GO.

Private interactive hosting requires a separately access-controlled environment with public reviewer disabled and `PUBLIC_DEMO_READ_ONLY=false`; the shipped public configuration deliberately offers no public business writes. Provider selection/provisioning and costs require owner authorization; no paid resources have been created.

## Git and CI gate

Release work is on `codex/portfolio-ledger-release-ui-v2`, starting at 3a605a0 with preserved dirty local changes. Prior build PR #1 is merged; remote main was inspected at 21275fa. Owner authorized publication; draft PR #2 is open at https://github.com/keenosmith-del/portfolio-ledger/pull/2. Initial run failed at bundled pip audit. Corrected code candidate 65fdea6 passed full Actions https://github.com/keenosmith-del/portfolio-ledger/actions/runs/43027530061; latest PR checks remain required. Counts/benchmark are in validation. A workflow file alone is not a passing hosted run. Do not merge or release with failed/unrun checks.

## Railway + Neon (implementation in progress)

Existing target Railway project ID `34e13a89-756c-4a34-8e29-845dedeaeb11` was created as `amiable-imagination`; now renamed `portfolioledger`. Neon project `portfolioledger` (`twilight-shadow-25760482`) is Free, PostgreSQL 18, Ohio, observed six-hour history retention. Railway trial showed $5/30 days remaining; no paid upgrade authorized. Trial expiry is an availability limit, not durable hosting assurance.

Railway does **not** run `compose.production.yaml`. Current services also cannot opt into legacy railway.toml (the live API rejected it). Use `.railway/railway.ts`, with the official SDK pinned separately in `.railway/package-lock.json` (`npm ci --prefix .railway`). Run `railway config plan` before `railway config apply --yes`; never add destructive confirmation without reviewing and authorizing destruction. Secrets remain unmanaged by IaC.

| Service | Source root | Container start | Public domain |
|---|---|---|---|
| web | `/frontend` | Nginx Railway startup script | Only this service |
| api | `/backend` | `python -m app.operations.serve` | None |
| worker | `/backend` | `python -m app.workers.runner` | None |

Use branch `codex/railway-neon-deployment` until reviewed/merged and wait for successful CI. Every service uses its existing Dockerfile. Keep worker persistent (sleep/serverless off), one replica. API listens on `[::]:8000`; web on 8080. Private DNS names must be `web.railway.internal` and `api.railway.internal`. Existing failed service was renamed web and its private endpoint renamed web.railway.internal. Plan verified safe updates to web plus creation of api/worker, zero destruction.

Set web `PUBLIC_HOST` to its exact generated HTTPS hostname, `API_UPSTREAM_HOST=api.railway.internal`, `API_UPSTREAM_PORT=8000`, `PORT=8080`. API/worker use:

| Variable | Value |
|---|---|
| APP_ENV | production |
| COOKIE_SECURE | true |
| PUBLIC_REVIEW_ENABLED | true |
| PUBLIC_DEMO_READ_ONLY | true |
| ALLOWED_ORIGINS | JSON array containing only the public HTTPS origin |
| ALLOWED_HOSTS | JSON array containing public hostname and healthcheck.railway.app |
| TRUSTED_PROXY_HOSTS | `["web.railway.internal"]` |
| API_BIND_HOST / PORT | `::` / `8000` |
| PGSSLROOTCERT | `/etc/ssl/certs/ca-certificates.crt` (image default) |
| DATABASE_URL | Private direct Neon DSN for the respective API or worker role; `sslmode=verify-full` |

Never set owner DSN, migration-owner password, API_DB_PASSWORD, WORKER_DB_PASSWORD or DEMO_PASSWORD on normal services. No wildcard Host/origin/proxy trust. Nginx strips supplied forwarding chains and fixes HTTPS; API resolves exact web addresses at startup. After web replacement, restart API to refresh those addresses and verify cookie/CSRF behavior. Shared edge rate-limit identity is conservative and requires hosted usability checks.

For the explicit one-off release, provide a private owner environment with MIGRATION_DATABASE_URL (direct endpoint, verify-full), PGSSLROOTCERT for the local/container OS, API_DB_ROLE/WORKER_DB_ROLE distinct names, strong independent API_DB_PASSWORD/WORKER_DB_PASSWORD, SEED_SYNTHETIC_DEMO=true and private DEMO_PASSWORD. From backend run `../.venv/bin/python -m app.operations.release`. It upgrades Alembic to head, seeds only bundled synthetic data, applies existing SQL role setup and checks TLS/current head. Failure must stop runtime rollout. Existing role passwords are not rotated by role setup. Never attach this operation as runtime/pre-deploy with owner variables.

Run `python -m app.operations.neon_check` separately with each runtime DATABASE_URL; sanitized output must report TLS, verify-full, direct connection, current head and runtime role verification. SQL-created roles must have no Neon superuser membership, database/schema/table ownership or privileged flags. Actual Neon permission compatibility remains unverified until this succeeds.

Neon CLI `profile create --mint --project-id` currently initiates broad temporary org OAuth. That flow was blocked, not approved. Use a Console-created **Project-scoped** API key limited to portfolioledger instead; feed through stdin to `neon profile create portfolioledger-deploy --api-key -`, then retain only a private credential store. Never put keys/DSNs in command arguments, Git, screenshots, raw logs or chat.

Hosted gates remain mandatory: HTTPS/secure cookie/CSRF/Host tests, readiness, password-free review/portfolio selection/source evidence/reconciliation/preview/CSV/audit, denied business writes, worker recovery, persistence across restarts, isolated restore drill, and continuous availability/error monitoring. Railway deployment healthchecks alone are startup checks. Preserve historical financial regression and 10k evidence without sending large loads to the public database. Public release is NO-GO until actual results are recorded.
