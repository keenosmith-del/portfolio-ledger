# API and authentication

Live local schema: `/openapi.json`; interactive API: `/docs`. All portfolio routes require an authenticated session **and** explicit portfolio access; inaccessible portfolios and guessed cross-portfolio resource UUIDs return scoped 404. Reviewer may read only. Admin has no grant bypass.

Login `POST /api/auth/login` with email/password; response returns role/email and CSRF token. Browser receives HttpOnly, SameSite=Strict session cookie, 8-hour expiry. No token in localStorage. `GET /api/auth/me` restores identity/CSRF after reload; `POST /api/auth/logout` revokes the server session. All authenticated mutations require `X-CSRF-Token`; browser origins must match the explicit allowlist or same-origin host. Production requires HTTPS and COOKIE_SECURE=true.

| Route suffix under `/api/portfolios/{portfolio_id}` | Method | Behavior |
|---|---|---|
| overview | GET | Database-derived metrics, freshness, latest preview |
| leases / ledger | GET | Page normalized/source-backed records |
| sources/{raw_id} | GET | Scoped sanitized source evidence |
| imports | POST | Multipart file, adapter, source_key; Idempotency-Key header; 202 receipt |
| imports | GET | Page durable job history |
| imports/{job_id} | GET | Receipt and paged per-row report |
| imports/{job_id}/replay | POST | New bounded queued attempt; Idempotency-Key required |
| reconciliations | POST | `{month: YYYY-MM, cutoff: aware UTC timestamp}` |
| reconciliations/{run_id} | GET | Immutable algorithm/cutoff/input batch metadata |
| exceptions | GET | Status/severity/reason/month filters and pagination |
| exceptions/{id}/resolve | POST | Status investigating/resolved/dismissed and required rationale |
| pricing | GET | Versioned effective-dated fee assumptions |
| billing-previews | POST | Explicit month/cutoff, idempotent snapshot coordinates |
| billing-previews | GET | Page saved snapshots |
| billing-previews/{id} | GET | Header, paged included/excluded lines |
| billing-previews/{id}/export.csv | GET | Safe-cell ZAR CSV with totals and config/cutoff |
| audit | GET | Page append-only business action evidence |

Pagination uses offset >=0 and limit 1–100 (default 25). Public `/health` is liveness; `/ready` checks database and schema/configuration. `GET /api/portfolios` lists only grants. Errors use `error.code` and `request_id`, validation errors list field paths but never rejected passwords/payload values. HTTP 401 auth, 403 reviewer/CSRF/origin, 404 scoped missing, 409 idempotency/lifecycle conflict, 413 size, 422 schema, 429 fixed-window limit, 503 database/unready.

Frontend's `src/api.ts` is the manually maintained typed response contract; automatic OpenAPI client generation is not claimed. API ORM response objects are column dictionaries and OpenAPI does not enumerate every response column. Request bodies are Pydantic v2 models; explicit typed response models are a future contract-hardening task.
