# Reviewer evidence index

| Evidence | Location | Status |
|---|---|---|
| Chronological engineering record | [Journal](engineering-journal.md) | Maintained during implementation |
| Foundation increment | [Iteration 001](iterations/001-foundation.md) | In progress |
| Design decisions | [ADR-001](adr/001-postgresql-transactions.md), [ADR-002](adr/002-ingestion-publication.md) | Accepted for implementation |
| Defects and corrections | [Defect log](defects.md) | Actual observed failures only |
| Changes | [Changelog](../CHANGELOG.md) | Unreleased |
| Test/build/benchmark measurements | [Validation](validation.md) | Static checks only so far |

No public deployment or performance result is claimed. Git commits are evidence of actual saved increments, not a fabricated development timeline.

## Verified milestones added during implementation

- [Iteration 002](iterations/002-ingestion-api.md): real red-to-green billing regression (`5f191c5` → `81fd5e6`), worker and HTTP invariants.
- [Iteration 003](iterations/003-frontend-and-cutoffs.md): live connected UI, historical cutoff refinement, browser defect sequence and passing journey/mobile.
- [10k acceptance baseline JSON](evidence/acceptance-baseline.json): actual receipt counts, Decimal DB totals, elapsed times, environment/base commit and dirty-tree disclosure.
- [Validation](validation.md): dated executed commands and results; frontend/container build status.

Earlier table is preserved as the chronological first snapshot, not the current milestone status.
