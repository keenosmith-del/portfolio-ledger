import json
from datetime import timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import ImportJob, Lease, LeaseVersion, LedgerEntry, RawRecord, Tenant, Unit, now
from app.integrations.adapters import Record, digest, load_rows, normalize, row_reason, sanitized
from app.services.common import audit, lock

MAX_ATTEMPTS = 3


def enqueue(
    db: Session,
    portfolio_id: str,
    adapter: str,
    source_key: str,
    key: str,
    filename: str,
    content: bytes,
    actor: str,
    correlation: str,
) -> tuple[ImportJob, bool]:
    rows = load_rows(adapter, filename, content)
    # Store a canonical sanitized artifact. Unknown schema fields are refused by normalization;
    # only allowlisted source fields are retained in persistent storage.
    safe_rows = [sanitized(row) for row in rows]
    checksum = digest(content.decode("utf-8-sig"))
    lock(db, "enqueue:" + portfolio_id + ":" + key)
    old = db.scalar(
        select(ImportJob).where(
            ImportJob.portfolio_id == portfolio_id, ImportJob.idempotency_key == key
        )
    )
    if old:
        if old.checksum != checksum or old.adapter != adapter or old.source_key != source_key:
            raise HTTPException(409, "idempotency_payload_conflict")
        return old, True
    # Retain row validation outcomes even for unknown fields removed by sanitization.
    for original, safe in zip(rows, safe_rows, strict=True):
        try:
            normalize(adapter, original)
        except ValueError as exc:
            safe["_validation_error"] = row_reason(exc)
    job = ImportJob(
        portfolio_id=portfolio_id,
        adapter=adapter,
        source_key=source_key,
        idempotency_key=key,
        filename=filename,
        checksum=checksum,
        payload=json.dumps(safe_rows, sort_keys=True),
        actor_id=actor,
        correlation_id=correlation,
    )
    db.add(job)
    db.flush()
    audit(
        db,
        portfolio_id,
        actor,
        "import.queued",
        job.id,
        correlation,
        {"rows": len(rows), "checksum": checksum},
    )
    return job, False


def claim(db: Session) -> str | None:
    job = db.scalar(
        select(ImportJob)
        .where(
            or_(
                ImportJob.status == "queued",
                (ImportJob.status == "processing") & (ImportJob.lease_until < now()),
            )
        )
        .order_by(ImportJob.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if not job:
        return None
    if job.attempts >= MAX_ATTEMPTS:
        job.status = "failed"
        job.error = "attempt_limit_exceeded"
        job.completed_at = now()
        return None
    job.status = "processing"
    job.attempts += 1
    job.lease_until = now() + timedelta(minutes=5)
    job.error = None
    return job.id


def current_lease(db: Session, portfolio: str, source: str, external: str) -> Lease | None:
    return db.scalar(
        select(Lease).where(
            Lease.portfolio_id == portfolio,
            Lease.source_key == source,
            Lease.external_id == external,
        )
    )


def apply_record(db: Session, job: ImportJob, raw: RawRecord, record: Record) -> str:
    lease = current_lease(db, job.portfolio_id, job.source_key, record.lease_id)
    if record.type == "lease":
        if lease is None:
            lease = Lease(
                portfolio_id=job.portfolio_id,
                source_key=job.source_key,
                external_id=record.lease_id,
            )
            db.add(lease)
            db.flush()
        previous = db.scalar(
            select(LeaseVersion)
            .where(LeaseVersion.lease_id == lease.id)
            .order_by(LeaseVersion.revision.desc())
            .limit(1)
        )
        if previous and record.revision <= previous.revision:
            old_raw = db.get(RawRecord, previous.raw_id)
            if (
                record.revision == previous.revision
                and old_raw
                and old_raw.content_hash == raw.content_hash
            ):
                return "duplicate"
            raise ValueError(
                "stale_revision" if record.revision < previous.revision else "revision_conflict"
            )
        unit = db.scalar(
            select(Unit).where(
                Unit.portfolio_id == job.portfolio_id, Unit.external_id == record.unit
            )
        )
        tenant = db.scalar(
            select(Tenant).where(
                Tenant.portfolio_id == job.portfolio_id, Tenant.external_id == record.tenant
            )
        )
        if unit is None:
            unit = Unit(portfolio_id=job.portfolio_id, external_id=record.unit)
            db.add(unit)
        if tenant is None:
            tenant = Tenant(portfolio_id=job.portfolio_id, external_id=record.tenant)
            db.add(tenant)
        db.flush()
        assert record.start_date is not None
        db.add(
            LeaseVersion(
                portfolio_id=job.portfolio_id,
                lease_id=lease.id,
                raw_id=raw.id,
                unit_id=unit.id,
                tenant_id=tenant.id,
                revision=record.revision,
                start_date=record.start_date,
                end_date=record.end_date,
                status=record.status,
                rent=record.amount,
            )
        )
    else:
        if lease is None:
            raise ValueError("unmatched_lease")
        previous_entry = db.scalar(
            select(LedgerEntry)
            .where(
                LedgerEntry.portfolio_id == job.portfolio_id,
                LedgerEntry.source_key == job.source_key,
                LedgerEntry.external_id == record.external_id,
                LedgerEntry.kind != "reversal",
            )
            .order_by(LedgerEntry.revision.desc())
            .limit(1)
        )
        if previous_entry:
            if previous_entry.lease_id != lease.id:
                raise ValueError("event_lease_conflict")
            old_raw = db.get(RawRecord, previous_entry.raw_id)
            if record.revision <= previous_entry.revision:
                if (
                    record.revision == previous_entry.revision
                    and old_raw
                    and old_raw.content_hash == raw.content_hash
                ):
                    return "duplicate"
                raise ValueError(
                    "stale_revision"
                    if record.revision < previous_entry.revision
                    else "revision_conflict"
                )
            db.add(
                LedgerEntry(
                    portfolio_id=job.portfolio_id,
                    lease_id=lease.id,
                    raw_id=raw.id,
                    source_key=job.source_key,
                    external_id=record.external_id,
                    revision=record.revision,
                    kind="reversal",
                    amount=-previous_entry.amount,
                    effective_date=previous_entry.effective_date,
                    reverses_id=previous_entry.id,
                    reason="reversal: " + record.reason[:180],
                )
            )
        db.add(
            LedgerEntry(
                portfolio_id=job.portfolio_id,
                lease_id=lease.id,
                raw_id=raw.id,
                source_key=job.source_key,
                external_id=record.external_id,
                revision=record.revision,
                kind=record.type,
                amount=record.amount,
                effective_date=record.effective_date,
                reason=record.reason,
            )
        )
    return "accepted"


def process(db: Session, job_id: str, fail_after: int | None = None) -> None:
    job = db.scalar(select(ImportJob).where(ImportJob.id == job_id).with_for_update())
    if job is None or job.status != "processing":
        return
    lock(db, "finance:" + job.portfolio_id)
    # Serialize all imports for one source; concurrent workers may process other sources.
    lock(db, "source:" + job.portfolio_id + ":" + job.source_key)
    rows: list[dict[str, Any]] = json.loads(job.payload)
    for i, row in enumerate(rows, 1):
        payload = {key: value for key, value in row.items() if key != "_validation_error"}
        raw = RawRecord(
            portfolio_id=job.portfolio_id,
            job_id=job.id,
            row_number=i,
            content_hash=digest(json.dumps(payload, sort_keys=True)),
            payload=payload,
            status="pending",
        )
        db.add(raw)
        db.flush()
        try:
            with db.begin_nested():
                if "_validation_error" in row:
                    raise ValueError(row["_validation_error"])
                record = normalize(job.adapter, payload)
                raw.external_id = record.external_id
                raw.status = apply_record(db, job, raw, record)
                db.flush()
        except ValueError as exc:
            raw.status = "quarantined"
            raw.reason = row_reason(exc)
        if raw.status == "accepted":
            job.accepted += 1
        elif raw.status == "duplicate":
            job.duplicates += 1
        else:
            job.quarantined += 1
        if fail_after == i:
            raise RuntimeError("deterministic_crash")
    job.status = "partially_completed" if job.quarantined else "completed"
    job.completed_at = now()
    job.lease_until = None
    audit(
        db,
        job.portfolio_id,
        job.actor_id,
        "import." + job.status,
        job.id,
        job.correlation_id,
        {
            "accepted": job.accepted,
            "duplicates": job.duplicates,
            "quarantined": job.quarantined,
            "attempt": job.attempts,
        },
    )
