import csv
import io
import json
from typing import Any

from app.integrations.adapters import ATLAS_COLUMNS


def atlas_feed(events: int = 5, invalid: bool = True) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(ATLAS_COLUMNS)
    writer.writerow(
        [
            "lease",
            "ATL-L001",
            "ATL-L001",
            1,
            "2026-01-01",
            "7500.00",
            "ATL-U001",
            "RESIDENT-001",
            "2026-01-01",
            "",
            "active",
            "synthetic lease",
        ]
    )
    writer.writerow(
        [
            "lease",
            "ATL-L002",
            "ATL-L002",
            1,
            "2026-01-01",
            "8200.00",
            "ATL-U002",
            "RESIDENT-002",
            "2026-01-01",
            "",
            "active",
            "synthetic lease",
        ]
    )
    for i in range(events):
        writer.writerow(
            [
                "charge" if i % 2 == 0 else "payment",
                f"ATL-E{i:06}",
                "ATL-L001",
                1,
                "2026-11-01",
                "7500.00" if i % 2 == 0 else "-3750.00",
                "",
                "",
                "",
                "",
                "",
                "synthetic rent" if i % 2 == 0 else "partial receipt",
            ]
        )
    if invalid:
        writer.writerow(
            [
                "payment",
                "ATL-BAD001",
                "ATL-UNKNOWN",
                1,
                "2026-11-01",
                "-100.00",
                "",
                "",
                "",
                "",
                "",
                "deliberate unmatched lease",
            ]
        )
        writer.writerow(
            [
                "charge",
                "ATL-BAD002",
                "ATL-L001",
                1,
                "2026-11-01",
                "not-money",
                "",
                "",
                "",
                "",
                "",
                "deliberate malformed amount",
            ]
        )
    return output.getvalue().encode()


def meridian_feed() -> bytes:
    events: list[dict[str, Any]] = [
        {
            "event": "contract",
            "eventId": "MER-C001",
            "contractId": "MER-C001",
            "version": 1,
            "effectiveOn": "2026-01-01",
            "value": "9000.00",
            "occupancy": {
                "space": "MER-U001",
                "resident": "RESIDENT-M001",
                "from": "2026-01-01",
                "until": None,
                "state": "active",
            },
        },
        {
            "event": "rent",
            "eventId": "MER-E001",
            "contractId": "MER-C001",
            "version": 1,
            "effectiveOn": "2026-11-01",
            "value": "8900.00",
        },
        {
            "event": "receipt",
            "eventId": "MER-E002",
            "contractId": "MER-C001",
            "version": 1,
            "effectiveOn": "2026-11-02",
            "value": "-4500.00",
        },
        {
            "event": "rent",
            "eventId": "MER-E001",
            "contractId": "MER-C001",
            "version": 2,
            "effectiveOn": "2026-11-01",
            "value": "9000.00",
            "memo": "correct rent via reversal and replacement",
        },
        {
            "event": "rent",
            "eventId": "MER-E001",
            "contractId": "MER-C001",
            "version": 1,
            "effectiveOn": "2026-11-01",
            "value": "8900.00",
            "memo": "deliberate late old revision",
        },
    ]
    return json.dumps({"schema": "meridian.v1", "events": events}, indent=2).encode()
