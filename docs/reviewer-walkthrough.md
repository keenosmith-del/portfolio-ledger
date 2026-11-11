# 60–90-second reviewer walkthrough

Sign in locally as the demo administrator. Cedarstone and Harbourlight are invented landlords with different provider schemas. Start in Integrations: AtlasPM is a CSV snapshot, MeridianRent is revisioned JSON. Open a batch and replay it. The worker creates a persisted receipt; accepted records become duplicates and the ledger balance does not grow. Invalid rows retain explicit quarantine reasons.

In Leases & ledger, open a posting's source evidence. Switch to Harbourlight to see a corrected rent posting preserved as the original, its reversal and a replacement. An older revision is quarantined instead of overwriting current history.

Return to Cedarstone, choose November 2026 and run reconciliation. Open a discrepancy: expected and actual charges, source IDs and cutoff explain the finding. Resolve it with a rationale. The audit timeline records the actor and state transition without changing money.

Calculate a monthly administration-fee preview. It is separate from rent, uses versioned ZAR pricing and explicit eligibility dates, and repeats consistently at the same cutoff. Download the itemized CSV, then reload to confirm persistence. Finally, inspect recovery.csv's second attempt and the engineering journal's failed-to-passing tests. The evidence index links the measured 10k benchmark and known local-only deployment limits.
