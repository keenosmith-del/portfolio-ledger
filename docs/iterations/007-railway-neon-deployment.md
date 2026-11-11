# Iteration 007 — Railway and Neon deployment

Status: in progress. Clean base 22ce9b4, deployment branch codex/railway-neon-deployment. No hosted application URL verified.

Existing single Railway service failed during Railpack detection at repo root; existing Neon portfolioledger Free project found. Preserve financial model/schema/history and existing tests/10k evidence. Adapt existing Dockerfiles with explicit service roots/start commands. Only web receives a public domain; API/worker remain private. Owner migration/seed/grants run as an explicit one-off, never API startup. Runtime roles require direct verified TLS and no owner membership.

## Local increment

44 PostgreSQL tests passed (16.78s, one warning), make check passed; both deployment Docker images built. Actual generated Nginx starts UID 101, serves canonical Host 200 and rejects unknown Host 444. Backend UID 10001 and trusted CA bundle present. Financial/worker algorithms and b003 unchanged; preserved accepted 10k evidence.

Railway CLI authorized and linked to existing deployment project. Neon CLI broad temporary OAuth blocked by automatic review; Console project-scoped key form prepared for owner storage. No cloud migration or successful deployment claimed.

Railway rejected new legacy TOML opt-in. Replaced with current `.railway/railway.ts`; official SDK 3.16.0 is isolated from app dependencies. Actual plan succeeded with safe web updates and api/worker creation, zero destruction, variables unmanaged. Existing service renamed web; private DNS update succeeded. Hosted apply/rebuild pending.

## Applied infrastructure and corrected gates

Current IaC apply succeeded for web/api/worker, with private api/worker DNS and only web's generated domain (`web-production-6a3f45e7.up.railway.app`). No successful runtime/HTTPS app claim yet. Non-secret production/read-only flags set without owner credentials. Initial cloud API health 400/worker crash preceded database configuration.

First CI 43069924214 failed in new test fixture, 43 passed/1 failed. Corrected fixture supplies public read-only flags explicitly. Full local follow-up 45 passed/20.07s/one warning, make check passed. Neon actual client TLS/verify-full preflight passed; pg_stat_ssl proxy-side false/null kept separate. Owner release initiated explicitly, result pending.

Owner release completed to b003; both actual runtime connections passed all ownership/privilege/membership and verified-client-TLS gates. Isolated hosted backup/restore passed exact hashes/IDs/total with source unchanged; first public-schema conflict and TOC correction retained in journal. Web homepage HTTPS 200; API readiness still pending. Corrected CI 43071397070 on db1b599 passed full financial/10k and private/public browser gates.

## Hosted application accepted; final operational gates pending

Public URL: https://web-production-6a3f45e7.up.railway.app . Public /ready 200/b003, HTTPS/HSTS/secure cookie flags verified. Actual public browser journey passed 21.7s, security follow-up 6.5s. Five business writes denied, persisted synthetic evidence/CSV/audit inspected. Exact rollout persistence: 9 postings / ZAR 19,500.00, unchanged business IDs. Owner failure/crash Email & In-App notifications verified enabled and actual in-app failures observed. Final logging classification correction passes static checks and 46 local tests/22.94s; rollout, explicit full restart and default-branch scheduled monitoring pending.
