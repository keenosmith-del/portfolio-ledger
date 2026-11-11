import csv
import hashlib
import io
import json
from datetime import date
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.domain.money import money

MAX_BYTES = 8 * 1024 * 1024
MAX_ROWS = 20000


class FeedError(ValueError):
    pass


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["lease", "charge", "payment", "credit", "adjustment"]
    external_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
    lease_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
    revision: int = Field(ge=1, le=1000000)
    effective_date: date
    amount: Decimal
    unit: str = Field(default="", max_length=120)
    tenant: str = Field(default="", max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    status: Literal["active", "ended"] = "active"
    reason: str = Field(default="source posting", max_length=200)

    @field_validator("amount", mode="before")
    @classmethod
    def parse_money(cls, value: Any) -> Decimal:
        if not isinstance(value, str | Decimal):
            raise ValueError("amount must be a decimal string")
        return money(value)

    @model_validator(mode="after")
    def validate_record(self) -> "Record":
        if self.type == "lease":
            if not self.start_date or not self.unit or not self.tenant or self.amount < 0:
                raise ValueError("lease_terms_required")
            if self.end_date and self.end_date < self.start_date:
                raise ValueError("invalid_lease_dates")
            if self.external_id != self.lease_id:
                raise ValueError("lease_identifier_mismatch")
        if self.type == "charge" and self.amount < 0:
            raise ValueError("charge_must_be_positive")
        if self.type in ("payment", "credit") and self.amount > 0:
            raise ValueError("payment_credit_must_be_negative")
        return self


ATLAS_COLUMNS = [
    "record_type",
    "record_id",
    "lease_ref",
    "revision",
    "effective_date",
    "amount_zar",
    "unit_ref",
    "tenant_ref",
    "lease_start",
    "lease_end",
    "status",
    "reason",
]


def digest(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()


def load_rows(adapter: str, filename: str, content: bytes) -> list[dict[str, Any]]:
    if len(content) > MAX_BYTES:
        raise FeedError("file_too_large")
    try:
        text = content.decode("utf-8-sig")
        if "\x00" in text:
            raise FeedError("unsafe_content")
        if adapter == "atlaspm" and filename.endswith(".csv"):
            reader = csv.DictReader(io.StringIO(text), strict=True)
            if reader.fieldnames != ATLAS_COLUMNS:
                raise FeedError("invalid_csv_columns")
            rows: list[dict[str, Any]] = []
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise FeedError("malformed_csv")
                rows.append(dict(row))
                if len(rows) > MAX_ROWS:
                    raise FeedError("row_limit_exceeded")
        elif adapter == "meridianrent" and filename.endswith(".json"):
            data = json.loads(text)
            if (
                not isinstance(data, dict)
                or set(data) != {"schema", "events"}
                or data["schema"] != "meridian.v1"
            ):
                raise FeedError("invalid_json_schema")
            rows = data["events"]
            if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                raise FeedError("invalid_events")
        else:
            raise FeedError("unknown_adapter_or_extension")
        if not rows or len(rows) > MAX_ROWS:
            raise FeedError("invalid_row_count")
        return rows
    except (UnicodeError, json.JSONDecodeError, csv.Error, RecursionError) as exc:
        raise FeedError("malformed_file") from exc


def normalize(adapter: str, row: dict[str, Any]) -> Record:
    if adapter == "atlaspm":
        return Record.model_validate(
            {
                "type": row.get("record_type"),
                "external_id": row.get("record_id"),
                "lease_id": row.get("lease_ref"),
                "revision": row.get("revision"),
                "effective_date": row.get("effective_date"),
                "amount": row.get("amount_zar"),
                "unit": row.get("unit_ref", ""),
                "tenant": row.get("tenant_ref", ""),
                "start_date": row.get("lease_start") or None,
                "end_date": row.get("lease_end") or None,
                "status": row.get("status") or "active",
                "reason": row.get("reason") or "source posting",
            }
        )
    if set(row) - {
        "event",
        "eventId",
        "contractId",
        "version",
        "effectiveOn",
        "value",
        "occupancy",
        "memo",
    }:
        raise ValueError("unknown_fields")
    occupancy = row.get("occupancy", {})
    if not isinstance(occupancy, dict):
        raise ValueError("invalid_occupancy")
    return Record.model_validate(
        {
            "type": {
                "contract": "lease",
                "rent": "charge",
                "receipt": "payment",
                "credit": "credit",
                "correction": "adjustment",
            }.get(row.get("event", ""), row.get("event")),
            "external_id": row.get("eventId"),
            "lease_id": row.get("contractId"),
            "revision": row.get("version"),
            "effective_date": row.get("effectiveOn"),
            "amount": row.get("value"),
            "unit": occupancy.get("space", ""),
            "tenant": occupancy.get("resident", ""),
            "start_date": occupancy.get("from"),
            "end_date": occupancy.get("until"),
            "status": occupancy.get("state", "active"),
            "reason": row.get("memo", "source posting"),
        }
    )


def sanitized(row: dict[str, Any]) -> dict[str, Any]:
    # Preserve only the documented synthetic schema, never arbitrary extra PII fields.
    allowed = set(ATLAS_COLUMNS) | {
        "event",
        "eventId",
        "contractId",
        "version",
        "effectiveOn",
        "value",
        "occupancy",
        "memo",
    }
    result: dict[str, Any] = {}
    for key, value in row.items():
        if key not in allowed:
            continue
        if key == "occupancy" and isinstance(value, dict):
            result[key] = {
                k: str(v)[:200] if v is not None else None
                for k, v in value.items()
                if k in {"space", "resident", "from", "until", "state"}
            }
        else:
            result[key] = str(value)[:300] if value is not None else None
    return result


def row_reason(exc: ValueError) -> str:
    if isinstance(exc, ValidationError):
        error = exc.errors()[0]
        return "schema_error:" + ".".join(str(p) for p in error["loc"]) + ":" + str(error["type"])
    return str(exc)[:120]
