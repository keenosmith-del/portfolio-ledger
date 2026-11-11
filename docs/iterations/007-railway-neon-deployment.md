# Iteration 007 — Railway and Neon deployment

Status: in progress. Clean base 22ce9b4, deployment branch codex/railway-neon-deployment. No hosted application URL verified.

Existing single Railway service failed during Railpack detection at repo root; existing Neon portfolioledger Free project found. Preserve financial model/schema/history and existing tests/10k evidence. Adapt existing Dockerfiles with explicit service roots/start commands. Only web receives a public domain; API/worker remain private. Owner migration/seed/grants run as an explicit one-off, never API startup. Runtime roles require direct verified TLS and no owner membership.

## Local increment

44 PostgreSQL tests passed (16.78s, one warning), make check passed; both deployment Docker images built. Actual generated Nginx starts UID 101, serves canonical Host 200 and rejects unknown Host 444. Backend UID 10001 and trusted CA bundle present. Financial/worker algorithms and b003 unchanged; preserved accepted 10k evidence.

Railway CLI authorized and linked to existing deployment project. Neon CLI broad temporary OAuth blocked by automatic review; Console project-scoped key form prepared for owner storage. No cloud migration or successful deployment claimed.

Railway rejected new legacy TOML opt-in. Replaced with current `.railway/railway.ts`; official SDK 3.16.0 is isolated from app dependencies. Actual plan succeeded with safe web updates and api/worker creation, zero destruction, variables unmanaged. Existing service renamed web; private DNS update succeeded. Hosted apply/rebuild pending.
