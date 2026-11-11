from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from zoneinfo import ZoneInfo

CENT = Decimal("0.01")


def money(value: str | Decimal) -> Decimal:
    try:
        amount = Decimal(value)
        if not amount.is_finite() or abs(amount) >= Decimal("10000000000000000"):
            raise ValueError("amount_out_of_range")
        return amount.quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError("invalid_amount") from exc


def month_bounds(month: str) -> tuple[date, date]:
    try:
        start = date.fromisoformat(month + "-01")
        if len(month) != 7:
            raise ValueError
        end = (
            date(start.year + 1, 1, 1)
            if start.month == 12
            else date(start.year, start.month + 1, 1)
        )
        return start, end
    except ValueError as exc:
        raise ValueError("month must be YYYY-MM") from exc


def local_month(timestamp: datetime) -> str:
    if timestamp.tzinfo is None:
        raise ValueError("timezone_required")
    return timestamp.astimezone(ZoneInfo("Africa/Johannesburg")).strftime("%Y-%m")


def eligible(start: date, end: date | None, status: str, month: str) -> bool:
    first, _ = month_bounds(month)
    return status == "active" and start <= first and (end is None or end >= first)


def safe_cell(value: str) -> str:
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value
