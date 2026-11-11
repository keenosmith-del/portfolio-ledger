# ADR-004: Enforce ownership and event identity below service layer

Date: 2026-11-11. Status: accepted and tested.

Context: final direct-database tests found two gaps despite passing authorized API behavior: global pricing FK allowed a preview to reference a different portfolio's pricing; kind-inclusive ledger uniqueness allowed the same event/revision under another kind. Both tests failed before correction (2 failed in 0.74s).

Decision: add Alembic b002, preserving applied revisions. Composite `(portfolio_id, pricing_id)` FK references scoped pricing identity. Partial unique index enforces one non-reversal posting for each portfolio/source/event/revision, allowing exactly the explicit reversal/replacement pattern. Add positive revision/version and bounded job/row-state checks. Readiness expects the new head.

Consequences: stronger database guarantees independent of API/service correctness. Migration checks existing data for violations; no repair/deletion is silently performed. Full suite after migration from blank: 26 passed in 9.23s, 85% coverage. Local existing-data upgrade and container restart verification follow in iteration 004.
