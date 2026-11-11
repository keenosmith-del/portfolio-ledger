"""Harden pricing ownership, posting identity and recorded state invariants."""

import sqlalchemy as sa

from alembic import op

revision = "b002"
down_revision = "b001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_pricing_portfolio_id", "pricing_versions", ["portfolio_id", "id"]
    )
    op.create_foreign_key(
        "fk_preview_pricing_scope",
        "billing_previews",
        "pricing_versions",
        ["portfolio_id", "pricing_id"],
        ["portfolio_id", "id"],
    )
    op.create_index(
        "uq_ledger_posting_revision",
        "ledger_entries",
        ["portfolio_id", "source_key", "external_id", "revision"],
        unique=True,
        postgresql_where=sa.text("kind <> 'reversal'"),
    )
    for table, name, condition in [
        ("pricing_versions", "ck_pricing_version", "version > 0"),
        ("lease_versions", "ck_lease_revision", "revision > 0"),
        ("ledger_entries", "ck_ledger_revision", "revision > 0"),
        (
            "raw_records",
            "ck_raw_status",
            "status IN ('pending','accepted','duplicate','quarantined')",
        ),
        (
            "import_jobs",
            "ck_import_counts",
            "attempts >= 0 AND attempts <= 3 AND accepted >= 0 AND duplicates >= 0 AND quarantined >= 0",
        ),
    ]:
        op.create_check_constraint(name, table, condition)


def downgrade() -> None:
    for table, name in [
        ("import_jobs", "ck_import_counts"),
        ("raw_records", "ck_raw_status"),
        ("ledger_entries", "ck_ledger_revision"),
        ("lease_versions", "ck_lease_revision"),
        ("pricing_versions", "ck_pricing_version"),
    ]:
        op.drop_constraint(name, table, type_="check")
    op.drop_index("uq_ledger_posting_revision", "ledger_entries")
    op.drop_constraint("fk_preview_pricing_scope", "billing_previews", type_="foreignkey")
    op.drop_constraint("uq_pricing_portfolio_id", "pricing_versions", type_="unique")
