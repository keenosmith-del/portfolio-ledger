import csv
import io
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    ExceptionRecord,
    ImportJob,
    Lease,
    LeaseVersion,
    LedgerEntry,
    Preview,
    PreviewLine,
    Pricing,
    RawRecord,
    Reconciliation,
)
from app.domain.money import eligible, money, month_bounds, safe_cell
from app.services.common import audit, lock


def lease_versions(
    db: Session, portfolio: str, cutoff: datetime
) -> list[tuple[Lease, LeaseVersion]]:
    rows = db.execute(
        select(Lease, LeaseVersion)
        .join(LeaseVersion, Lease.id == LeaseVersion.lease_id)
        .where(Lease.portfolio_id == portfolio, LeaseVersion.created_at <= cutoff)
        .order_by(Lease.id, LeaseVersion.revision.desc())
    ).all()
    seen: set[str] = set()
    result: list[tuple[Lease, LeaseVersion]] = []
    for lease, version in rows:
        if lease.id not in seen:
            seen.add(lease.id)
            result.append((lease, version))
    return result


def reconcile(
    db: Session, portfolio: str, month: str, cutoff: datetime, actor: str, correlation: str
) -> Reconciliation:
    first, end = month_bounds(month)
    lock(db, "finance:" + portfolio)
    old = db.scalar(
        select(Reconciliation).where(
            Reconciliation.portfolio_id == portfolio,
            Reconciliation.month == month,
            Reconciliation.cutoff == cutoff,
        )
    )
    if old:
        return old
    jobs = list(
        db.scalars(
            select(ImportJob.id).where(
                ImportJob.portfolio_id == portfolio, ImportJob.completed_at <= cutoff
            )
        )
    )
    run = Reconciliation(portfolio_id=portfolio, month=month, cutoff=cutoff, input_jobs=jobs)
    db.add(run)
    db.flush()
    entries = list(
        db.scalars(
            select(LedgerEntry).where(
                LedgerEntry.portfolio_id == portfolio, LedgerEntry.created_at <= cutoff
            )
        )
    )
    by_lease: dict[str, list[LedgerEntry]] = {}
    by_id = {entry.id: entry for entry in entries}
    for entry in entries:
        by_lease.setdefault(entry.lease_id, []).append(entry)
    for lease, version in lease_versions(db, portfolio, cutoff):
        posted = by_lease.get(lease.id, [])
        charges = Decimal("0.00")
        monthly: list[str] = []
        balance = sum(
            (entry.amount for entry in posted if entry.effective_date < end), Decimal("0.00")
        )
        for entry in posted:
            if first <= entry.effective_date < end:
                monthly.append(entry.id)
                original = by_id.get(entry.reverses_id or "")
                if entry.kind == "charge" or (
                    entry.kind == "reversal" and original and original.kind == "charge"
                ):
                    charges += entry.amount
        if (
            eligible(version.start_date, version.end_date, version.status, month)
            and charges != version.rent
        ):
            db.add(
                ExceptionRecord(
                    portfolio_id=portfolio,
                    run_id=run.id,
                    lease_id=lease.id,
                    reason="missing_charge" if charges == 0 else "charge_mismatch",
                    severity="high",
                    evidence={
                        "expected": str(version.rent),
                        "actual": str(charges),
                        "lease_version_id": version.id,
                        "ledger_ids": monthly,
                        "cutoff": cutoff.isoformat(),
                    },
                )
            )
        if balance < 0:
            db.add(
                ExceptionRecord(
                    portfolio_id=portfolio,
                    run_id=run.id,
                    lease_id=lease.id,
                    reason="unallocated_credit",
                    severity="medium",
                    evidence={
                        "balance": str(balance),
                        "ledger_ids": [entry.id for entry in posted if entry.effective_date < end],
                    },
                )
            )
    for row in db.scalars(
        select(RawRecord).where(
            RawRecord.portfolio_id == portfolio,
            RawRecord.created_at <= cutoff,
            RawRecord.status == "quarantined",
        )
    ):
        db.add(
            ExceptionRecord(
                portfolio_id=portfolio,
                run_id=run.id,
                reason="source_quarantine",
                severity="high",
                evidence={"raw_id": row.id, "job_id": row.job_id, "reason": row.reason},
            )
        )
    audit(
        db,
        portfolio,
        actor,
        "reconciliation.created",
        run.id,
        correlation,
        {"month": month, "cutoff": cutoff.isoformat(), "algorithm": "rent-v1"},
    )
    return run


def preview(
    db: Session, portfolio: str, month: str, cutoff: datetime, actor: str, correlation: str
) -> Preview:
    first, _ = month_bounds(month)
    lock(db, "finance:" + portfolio)
    pricing = db.scalar(
        select(Pricing)
        .where(
            Pricing.portfolio_id == portfolio,
            Pricing.effective_from <= first,
            Pricing.created_at <= cutoff,
        )
        .order_by(Pricing.effective_from.desc(), Pricing.version.desc())
        .limit(1)
    )
    if pricing is None:
        raise HTTPException(422, "no_pricing_at_cutoff")
    old = db.scalar(
        select(Preview).where(
            Preview.portfolio_id == portfolio,
            Preview.month == month,
            Preview.cutoff == cutoff,
            Preview.pricing_id == pricing.id,
        )
    )
    if old:
        return old
    # Snapshot exception state at generation. Historical evidence remains immutable afterward.
    unresolved = list(
        db.scalars(
            select(ExceptionRecord.id).where(
                ExceptionRecord.portfolio_id == portfolio,
                ExceptionRecord.created_at <= cutoff,
                ExceptionRecord.status.in_(["open", "investigating"]),
            )
        )
    )
    result = Preview(
        portfolio_id=portfolio,
        month=month,
        cutoff=cutoff,
        pricing_id=pricing.id,
        total=Decimal("0.00"),
        config={
            "version": pricing.version,
            "monthly_fee": str(pricing.monthly_fee),
            "rule": pricing.rule,
            "currency": "ZAR",
            "proration": "none",
            "effective_from": pricing.effective_from.isoformat(),
        },
        unresolved_exceptions=unresolved,
    )
    db.add(result)
    db.flush()
    for lease, version in lease_versions(db, portfolio, cutoff):
        included = eligible(version.start_date, version.end_date, version.status, month)
        amount = money(pricing.monthly_fee) if included else Decimal("0.00")
        result.total += amount
        db.add(
            PreviewLine(
                portfolio_id=portfolio,
                preview_id=result.id,
                lease_id=lease.id,
                external_id=lease.external_id,
                eligible=included,
                reason="active_on_month_start" if included else "outside_eligibility_boundary",
                amount=amount,
            )
        )
    audit(
        db,
        portfolio,
        actor,
        "billing.preview_created",
        result.id,
        correlation,
        {
            "month": month,
            "cutoff": cutoff.isoformat(),
            "total": str(result.total),
            "pricing_version": pricing.version,
        },
    )
    return result


def export_preview(result: Preview, lines: list[PreviewLine]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "preview_id",
            "month",
            "currency",
            "cutoff_utc",
            "pricing_version",
            "lease",
            "eligible",
            "reason",
            "amount_zar",
        ]
    )
    for line in lines:
        values: list[Any] = [
            result.id,
            result.month,
            "ZAR",
            result.cutoff.isoformat(),
            result.config["version"],
            line.external_id,
            line.eligible,
            line.reason,
            str(line.amount),
        ]
        writer.writerow([safe_cell(str(value)) for value in values])
    writer.writerow(["TOTAL", result.month, "ZAR", "", "", "", "", "", str(result.total)])
    return output.getvalue()
