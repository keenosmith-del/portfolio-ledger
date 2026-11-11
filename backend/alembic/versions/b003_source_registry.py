"""Register historical source identities without rewriting financial evidence."""

import sqlalchemy as sa

from alembic import op

revision = "b003"
down_revision = "b002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "portfolios",
        sa.Column("synthetic_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "integration_sources",
        sa.Column("portfolio_id", sa.String(36), sa.ForeignKey("portfolios.id"), primary_key=True),
        sa.Column("source_key", sa.String(100), primary_key=True),
        sa.Column("adapter", sa.String(30), nullable=False),
        sa.Column("upstream_account", sa.String(120), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("portfolio_id", "source_key", "adapter", name="uq_source_identity"),
        sa.UniqueConstraint(
            "portfolio_id", "adapter", "upstream_account", name="uq_source_upstream"
        ),
    )
    # Retain every existing namespace, but require operator review before enabling it.
    # Explicit seeding enables only the known synthetic demo identities.
    op.execute("""INSERT INTO integration_sources (portfolio_id, source_key, adapter, upstream_account, enabled)
        SELECT DISTINCT portfolio_id, source_key, adapter, source_key, false FROM import_jobs""")
    op.create_foreign_key(
        "fk_import_source",
        "import_jobs",
        "integration_sources",
        ["portfolio_id", "source_key", "adapter"],
        ["portfolio_id", "source_key", "adapter"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_import_source", "import_jobs", type_="foreignkey")
    op.drop_table("integration_sources")
    op.drop_column("portfolios", "synthetic_demo")
