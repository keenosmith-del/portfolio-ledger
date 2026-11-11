# ADR-005 — Registered sources, public read-only sessions and same-origin release

Accepted for implementation 2026-11-11.

Financial identity is a configured portfolio/provider/upstream account. Upload callers select an enabled registry entry; they cannot mint a namespace. The registry is operator-owned and has a composite job FK plus unique upstream identity. Migration preserves prior evidence without silently interpreting historical aliases as independent legitimate feeds; old entries start disabled. Explicit synthetic seed enables only known demo entries. Distinct real upstream accounts may have distinct authorized identities.

Public review uses a dedicated reviewer identity granted only explicitly marked synthetic portfolios, short-lived HttpOnly session cookies and no password publication. Production public mode globally rejects all business writes, including private admin sessions. Interactive demo runs privately with public mode disabled. Registry edits have no HTTP endpoint.

Frontend and API share an origin through Nginx. Production requires verified database TLS, least-privilege runtime roles, HTTPS origins, secure cookies and explicit host/proxy trust. Migration/seed are explicit release jobs. Cloud readiness still requires verified operator infrastructure; local success alone does not authorize public deployment.
