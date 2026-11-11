import hashlib
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.models import AuditEvent


def lock(db: Session, key: str) -> None:
    number = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big", signed=True)
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": number})


def audit(
    db: Session,
    portfolio_id: str,
    actor: str,
    action: str,
    resource: str,
    correlation: str,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditEvent(
            portfolio_id=portfolio_id,
            actor_id=actor,
            action=action,
            resource_id=resource,
            correlation_id=correlation,
            details=details or {},
        )
    )
