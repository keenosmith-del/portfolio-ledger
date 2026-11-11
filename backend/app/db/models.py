from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now() -> datetime:
    return datetime.now(UTC)


def uid() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Entity(Base):
    __abstract__ = True
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class PortfolioEntity(Entity):
    __abstract__ = True
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))


class User(Entity):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(200), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20))
    __table_args__ = (CheckConstraint("role IN ('admin','analyst','reviewer')"),)


class Portfolio(Entity):
    __tablename__ = "portfolios"
    name: Mapped[str] = mapped_column(String(120), unique=True)
    adapter: Mapped[str] = mapped_column(String(30))
    synthetic_demo: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )


class IntegrationSource(Base):
    __tablename__ = "integration_sources"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), primary_key=True)
    source_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    adapter: Mapped[str] = mapped_column(String(30))
    upstream_account: Mapped[str] = mapped_column(String(120))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    __table_args__ = (
        UniqueConstraint("portfolio_id", "source_key", "adapter", name="uq_source_identity"),
        UniqueConstraint("portfolio_id", "adapter", "upstream_account", name="uq_source_upstream"),
    )


class Access(Base):
    __tablename__ = "portfolio_access"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), primary_key=True)


class AuthSession(Entity):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf: Mapped[str] = mapped_column(String(80))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RateWindow(Base):
    __tablename__ = "rate_windows"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    count: Mapped[int] = mapped_column(Integer, default=0)


class Pricing(PortfolioEntity):
    __tablename__ = "pricing_versions"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    monthly_fee: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    effective_from: Mapped[date] = mapped_column(Date)
    rule: Mapped[str] = mapped_column(String(40), default="active_on_month_start")
    __table_args__ = (
        UniqueConstraint("portfolio_id", "version"),
        UniqueConstraint("portfolio_id", "id", name="uq_pricing_portfolio_id"),
        CheckConstraint("version > 0", name="ck_pricing_version"),
        CheckConstraint("monthly_fee >= 0"),
        CheckConstraint("rule = 'active_on_month_start'"),
    )


class ImportJob(PortfolioEntity):
    __tablename__ = "import_jobs"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    adapter: Mapped[str] = mapped_column(String(30))
    source_key: Mapped[str] = mapped_column(String(100))
    idempotency_key: Mapped[str] = mapped_column(String(120))
    checksum: Mapped[str] = mapped_column(String(64))
    filename: Mapped[str] = mapped_column(String(150))
    payload: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    correlation_id: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted: Mapped[int] = mapped_column(Integer, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, default=0)
    quarantined: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(String(250))
    __table_args__ = (
        ForeignKeyConstraint(
            ["portfolio_id", "source_key", "adapter"],
            [
                "integration_sources.portfolio_id",
                "integration_sources.source_key",
                "integration_sources.adapter",
            ],
            name="fk_import_source",
        ),
        UniqueConstraint("portfolio_id", "idempotency_key"),
        UniqueConstraint("portfolio_id", "id"),
        CheckConstraint(
            "status IN ('queued','processing','completed','partially_completed','failed')"
        ),
        Index("ix_import_queue", "status", "lease_until"),
        CheckConstraint(
            "attempts >= 0 AND attempts <= 3 AND accepted >= 0 AND duplicates >= 0 AND quarantined >= 0",
            name="ck_import_counts",
        ),
    )


class RawRecord(PortfolioEntity):
    __tablename__ = "raw_records"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    job_id: Mapped[str] = mapped_column(String(36))
    row_number: Mapped[int] = mapped_column(Integer)
    external_id: Mapped[str | None] = mapped_column(String(120))
    content_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str | None] = mapped_column(String(120))
    __table_args__ = (
        ForeignKeyConstraint(
            ["portfolio_id", "job_id"], ["import_jobs.portfolio_id", "import_jobs.id"]
        ),
        UniqueConstraint("job_id", "row_number"),
        CheckConstraint(
            "status IN ('pending','accepted','duplicate','quarantined')",
            name="ck_raw_status",
        ),
        UniqueConstraint("portfolio_id", "id"),
        Index("ix_raw_portfolio_external", "portfolio_id", "external_id"),
    )


class Unit(PortfolioEntity):
    __tablename__ = "units"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    external_id: Mapped[str] = mapped_column(String(120))
    __table_args__ = (
        UniqueConstraint("portfolio_id", "external_id"),
        UniqueConstraint("portfolio_id", "id"),
    )


class Tenant(PortfolioEntity):
    __tablename__ = "tenants"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    external_id: Mapped[str] = mapped_column(String(120))
    __table_args__ = (
        UniqueConstraint("portfolio_id", "external_id"),
        UniqueConstraint("portfolio_id", "id"),
    )


class Lease(PortfolioEntity):
    __tablename__ = "leases"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    source_key: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(120))
    __table_args__ = (
        UniqueConstraint("portfolio_id", "source_key", "external_id"),
        UniqueConstraint("portfolio_id", "id"),
    )


class LeaseVersion(PortfolioEntity):
    __tablename__ = "lease_versions"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    lease_id: Mapped[str] = mapped_column(String(36))
    raw_id: Mapped[str] = mapped_column(String(36))
    unit_id: Mapped[str] = mapped_column(String(36))
    tenant_id: Mapped[str] = mapped_column(String(36))
    revision: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20))
    rent: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    __table_args__ = (
        ForeignKeyConstraint(["portfolio_id", "lease_id"], ["leases.portfolio_id", "leases.id"]),
        ForeignKeyConstraint(
            ["portfolio_id", "raw_id"], ["raw_records.portfolio_id", "raw_records.id"]
        ),
        ForeignKeyConstraint(["portfolio_id", "unit_id"], ["units.portfolio_id", "units.id"]),
        ForeignKeyConstraint(["portfolio_id", "tenant_id"], ["tenants.portfolio_id", "tenants.id"]),
        UniqueConstraint("lease_id", "revision"),
        CheckConstraint("revision > 0", name="ck_lease_revision"),
        CheckConstraint("rent >= 0"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date"),
        CheckConstraint("status IN ('active','ended')"),
        Index("ix_lease_version_cutoff", "portfolio_id", "created_at"),
    )


class LedgerEntry(PortfolioEntity):
    __tablename__ = "ledger_entries"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    lease_id: Mapped[str] = mapped_column(String(36))
    raw_id: Mapped[str] = mapped_column(String(36))
    source_key: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(120))
    revision: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(20))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    effective_date: Mapped[date] = mapped_column(Date)
    reverses_id: Mapped[str | None] = mapped_column(String(36))
    reason: Mapped[str] = mapped_column(String(200))
    __table_args__ = (
        ForeignKeyConstraint(["portfolio_id", "lease_id"], ["leases.portfolio_id", "leases.id"]),
        ForeignKeyConstraint(
            ["portfolio_id", "raw_id"], ["raw_records.portfolio_id", "raw_records.id"]
        ),
        ForeignKeyConstraint(
            ["portfolio_id", "reverses_id"],
            ["ledger_entries.portfolio_id", "ledger_entries.id"],
        ),
        UniqueConstraint("portfolio_id", "id"),
        UniqueConstraint("portfolio_id", "source_key", "external_id", "revision", "kind"),
        UniqueConstraint("reverses_id"),
        CheckConstraint("kind IN ('charge','payment','credit','adjustment','reversal')"),
        CheckConstraint(
            "(kind != 'charge' OR amount >= 0) AND (kind NOT IN ('payment','credit') OR amount <= 0)"
        ),
        CheckConstraint("(kind = 'reversal') = (reverses_id IS NOT NULL)"),
        Index("ix_ledger_portfolio_date", "portfolio_id", "effective_date", "created_at"),
        CheckConstraint("revision > 0", name="ck_ledger_revision"),
        Index(
            "uq_ledger_posting_revision",
            "portfolio_id",
            "source_key",
            "external_id",
            "revision",
            unique=True,
            postgresql_where=text("kind <> 'reversal'"),
        ),
    )


class Reconciliation(PortfolioEntity):
    __tablename__ = "reconciliations"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    month: Mapped[str] = mapped_column(String(7))
    cutoff: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    algorithm: Mapped[str] = mapped_column(String(40), default="rent-v1")
    input_jobs: Mapped[list[str]] = mapped_column(JSON)
    __table_args__ = (
        UniqueConstraint("portfolio_id", "id"),
        UniqueConstraint("portfolio_id", "month", "cutoff", "algorithm"),
    )


class ExceptionRecord(PortfolioEntity):
    __tablename__ = "exceptions"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    run_id: Mapped[str] = mapped_column(String(36))
    lease_id: Mapped[str | None] = mapped_column(String(36))
    reason: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="open")
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON)
    __table_args__ = (
        ForeignKeyConstraint(
            ["portfolio_id", "run_id"],
            ["reconciliations.portfolio_id", "reconciliations.id"],
        ),
        ForeignKeyConstraint(["portfolio_id", "lease_id"], ["leases.portfolio_id", "leases.id"]),
        UniqueConstraint("portfolio_id", "id"),
        CheckConstraint("status IN ('open','investigating','resolved','dismissed')"),
        Index("ix_exceptions_portfolio_status", "portfolio_id", "status"),
    )


class Preview(PortfolioEntity):
    __tablename__ = "billing_previews"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    month: Mapped[str] = mapped_column(String(7))
    cutoff: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    pricing_id: Mapped[str] = mapped_column(ForeignKey("pricing_versions.id"))
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    unresolved_exceptions: Mapped[list[str]] = mapped_column(JSON)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    __table_args__ = (
        UniqueConstraint("portfolio_id", "month", "cutoff", "pricing_id"),
        ForeignKeyConstraint(
            ["portfolio_id", "pricing_id"],
            ["pricing_versions.portfolio_id", "pricing_versions.id"],
            name="fk_preview_pricing_scope",
        ),
        UniqueConstraint("portfolio_id", "id"),
        CheckConstraint("total >= 0"),
    )


class PreviewLine(PortfolioEntity):
    __tablename__ = "billing_preview_lines"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    preview_id: Mapped[str] = mapped_column(String(36))
    lease_id: Mapped[str] = mapped_column(String(36))
    external_id: Mapped[str] = mapped_column(String(120))
    eligible: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    __table_args__ = (
        ForeignKeyConstraint(
            ["portfolio_id", "preview_id"],
            ["billing_previews.portfolio_id", "billing_previews.id"],
        ),
        ForeignKeyConstraint(["portfolio_id", "lease_id"], ["leases.portfolio_id", "leases.id"]),
        UniqueConstraint("preview_id", "lease_id"),
        CheckConstraint("amount >= 0"),
    )


class AuditEvent(PortfolioEntity):
    __tablename__ = "audit_events"
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(100))
    correlation_id: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict[str, Any]] = mapped_column(JSON)
