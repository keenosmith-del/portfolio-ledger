"""Database-level append-only financial evidence.

Revision ID: b001
aacf7692e44e -> b001
"""

from alembic import op

revision = "b001"
down_revision = "aacf7692e44e"
branch_labels = None
depends_on = None

IMMUTABLE = (
    "ledger_entries",
    "lease_versions",
    "pricing_versions",
    "billing_previews",
    "billing_preview_lines",
    "audit_events",
    "raw_records",
)


def upgrade() -> None:
    op.execute("""CREATE FUNCTION reject_evidence_mutation() RETURNS trigger AS $$
    BEGIN RAISE EXCEPTION 'immutable financial evidence: %', TG_TABLE_NAME;
    END; $$ LANGUAGE plpgsql""")
    # Raw rows are inserted pending and finalized in the same transaction, so only
    # protect finalized rows; the worker finalizes pending -> accepted/quarantined.
    for table in IMMUTABLE:
        if table == "raw_records":
            op.execute(
                f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW WHEN (OLD.status != 'pending') EXECUTE FUNCTION reject_evidence_mutation()"
            )
        else:
            op.execute(
                f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation()"
            )


def downgrade() -> None:
    for table in reversed(IMMUTABLE):
        op.execute(f"DROP TRIGGER immutable_{table} ON {table}")
    op.execute("DROP FUNCTION reject_evidence_mutation()")
