# ADR-003: Completed-source cutoffs and immutable preview construction

Date: 2026-11-11. Status: accepted and regression-tested in increment 002, with additional historical tests planned.

Context: timestamps on individual rows alone could expose a subset of a long processing attempt when reconstructing historical state. Immutable header triggers also exposed the service's attempt to update a total after insertion (D005).

Decision: lock portfolio financial publication during import/reconciliation/preview. Source reads require the owning import to have completed by the requested UTC cutoff. Lease effective dates and calendar eligibility are date values; display/calendar context is Johannesburg. A snapshot header is assembled with its final total before INSERT. Request dependencies complete transactions before emitting success. Exception state at cutoff derives from immutable action audit, not present-day status. Preserve immutable result under portfolio/month/cutoff/pricing uniqueness.

Consequences: financial generation and imports for the same portfolio serialize. This intentionally trades peak throughput for explainability and correctness. New cutoff/config produces an explicit different snapshot rather than overwriting the old one.
