# Domain rules and mappings

All examples are invented. No insurance premium or liability calculation exists.

Money: Decimal, ROUND_HALF_UP to 0.01 ZAR; stored NUMERIC(18,2). Charge >= 0, payment/credit <= 0, signed adjustment explicit, zero permitted. Reversal negates the prior amount at the prior effective date; replacement carries new amount/date and its own higher revision. Posted evidence cannot be updated/deleted through SQL due to triggers. A review never creates a posting. Corrections are ingested explicitly from provider revisions or adjustment events, not fabricated by resolving an exception.

## Calendar and eligibility

Effective dates are date values. UTC timestamps define recorded/published cutoffs; Africa/Johannesburg defines calendar interpretation and UI display (SAST). `local_month` requires aware timestamps and is boundary-tested. Monthly administration fee v1 is ZAR 85.00 per lease active **on the month's first calendar date**. Start date <= first; end date inclusive >= first or null; source status active. No proration. A lease starting on February 29 is eligible March 1 if active. A lease ending January 31 is excluded February 1. Fee configuration effective date <= month start and created timestamp <= cutoff; latest effective date/version wins. Zero-price versions are valid. Historical versions remain intact.

Reconciliation compares active-on-month-start lease rent to net source charges/reversals in `[month start, next month start)`. Payments reduce balance but not expected rent. Negative cumulative balance flags unallocated credit. Partial receipts leave a positive receivable, not automatically an error. Each quarantine produces source evidence. Exceptions store source IDs, expected/actual values and cutoff; resolution status transitions are audited. Fresh runs use distinct cutoffs; repeated identical run coordinates return their stored result. Cutoff is explicit and must be aware/not in future.

## Provider differences

| Meaning | AtlasPM CSV | MeridianRent JSON |
|---|---|---|
| schema | exact 12-column header | `schema: meridian.v1`, events array |
| stable source event | record_id | eventId |
| lease reference | lease_ref | contractId |
| revision | revision | version |
| signed ZAR amount | amount_zar decimal string | value decimal string |
| event type | record_type: lease/charge/payment/credit/adjustment | event: contract/rent/receipt/credit/correction |
| effective date | effective_date | effectiveOn |
| unit/tenant | unit_ref / tenant_ref | occupancy.space / resident |
| lease dates | lease_start / lease_end | occupancy.from / until |

Atlas snapshots include lease and financial row types. Missing rows never delete financial history or infer termination: send an explicit higher lease revision with ended status. Source freshness is shown and considered stale after 24 hours. Meridian corrections use higher revisions; late lower revisions quarantine as stale_revision. Same revision/same hash deduplicates; changed content without revision advancement quarantines as revision_conflict. Stable external IDs contain safe alphanumeric punctuation and no formula prefix.

## Ingestion policy

Reject malformed container/schema, wrong extension/MIME, UTF-8/NUL errors, >8 MiB, >20,000 rows. Otherwise each malformed/unmatched/stale row is quarantined while valid rows are accepted. Unexpected infrastructure errors abort the entire attempt. Raw payloads retain only schema-allowlisted sanitized fields; original upload checksum remains in receipt, row content hash describes sanitized provider row. Never use original input as executable content. A changed payload with an existing idempotency key returns 409. Replays use distinct receipts, stable provider identity avoids duplicate effects.

Fixture dates are deliberately anchored to November 2026 so the reviewer can reproduce results independently of today's date. Select **2026-11** in the UI. Atlas includes five financial events plus two bad rows; Meridian includes correction and late revision. Source refs are fictional resident identifiers, no names/addresses/contact details.

## Canonical source identity (b003)

Financial namespaces must be authorized before uploading. Each portfolio/provider source registry entry has one unique upstream-account identity; callers select an enabled source rather than create keys. Multiple independently authorized upstream accounts are legitimate; a second alias for the same account is not. Upload, replay and worker processing validate the registry, with composite job/source ownership enforced by PostgreSQL. Historical identities migrate disabled until operator review; explicit synthetic seed enables only the two known fictional demo identities. No existing posting/evidence is merged or rewritten to introduce the registry.
