# ADR 006 — Railway containers and Neon ownership boundary

Status: implementation accepted; hosted verification pending.

Railway does not execute Compose. Each service uses its existing Dockerfile with its own source root and service definition in .railway/railway.ts (the live API rejects new legacy TOML configuration). Only web gets a public domain. Unprivileged Nginx forwards /api and /ready to api.railway.internal, fixes canonical Host and HTTPS protocol and discards caller forwarding chains. API binds dual stack and trusts only exact addresses resolved from web.railway.internal, never a provider-wide network or wildcard. Restart API after web address changes to refresh trust; failures remain closed. Rate limiting initially sees Railway edge addresses, sharing the budget; verify public usability before release.

Neon uses direct PostgreSQL with verify-full and the trusted OS certificate bundle. SQL-created runtime roles use existing explicit grants, never Console-created neon_superuser members. Owner migrations/seed/grants execute once through app.operations.release with private owner environment. Ordinary services never receive owner DSNs. app.operations.neon_check rejects pooled endpoints, weak TLS, stale migration heads and privileged/owning/inheriting runtime identities.

The public reviewer is password-free and synthetic-only; PUBLIC_REVIEW_ENABLED and PUBLIC_DEMO_READ_ONLY are both true. Existing business write guards remain mandatory. No finance logic/schema redesign. Railway startup healthchecks do not replace continuous monitoring; backup/restore, role operations, hosted browser and operational verification remain release gates.
