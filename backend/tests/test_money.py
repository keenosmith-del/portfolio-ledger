from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.domain.money import eligible, local_month, money, month_bounds, safe_cell


def test_money_rounding_and_invalid() -> None:
    assert money("1.005") == Decimal("1.01")
    assert money("-1.005") == Decimal("-1.01")
    assert money("0") == Decimal("0.00")
    for value in ("NaN", "Infinity", "-Infinity", "10000000000000000", "nope"):
        with pytest.raises(ValueError):
            money(value)


def test_calendar_boundaries() -> None:
    assert month_bounds("2024-02") == (date(2024, 2, 1), date(2024, 3, 1))
    assert month_bounds("2024-12")[1] == date(2025, 1, 1)
    assert eligible(date(2024, 1, 1), date(2024, 2, 1), "active", "2024-02")
    assert not eligible(date(2024, 2, 2), None, "active", "2024-02")
    assert not eligible(date(2024, 1, 1), date(2024, 1, 31), "active", "2024-02")
    assert eligible(date(2024, 2, 29), None, "active", "2024-03")
    assert not eligible(date(2024, 1, 1), None, "ended", "2024-02")
    assert local_month(datetime(2024, 2, 29, 22, tzinfo=UTC)) == "2024-03"
    with pytest.raises(ValueError):
        local_month(datetime(2024, 2, 1))
    with pytest.raises(ValueError):
        month_bounds("2024-13")


@pytest.mark.parametrize("value", ["=cmd()", "+SUM(1)", "-1", "@run", " \t=evil"])
def test_csv_injection(value: str) -> None:
    assert safe_cell(value).startswith("'")
