"""Read-only persisted-ID/ledger-total comparison across a Compose stop/start.

Capture before: python scripts/persistence_smoke.py capture /tmp/ledger-snapshot.json
Verify after: python scripts/persistence_smoke.py verify /tmp/ledger-snapshot.json
Do not run financial mutations between capture and verify.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from app.db.session import SessionLocal
from sqlalchemy import text

TABLES = [
    "ledger_entries",
    "leases",
    "billing_previews",
    "billing_preview_lines",
    "audit_events",
    "exceptions",
    "import_jobs",
]


def snapshot() -> dict[str, Any]:
    with SessionLocal() as db:
        result: dict[str, Any] = {
            table: [
                list(row)
                for row in db.execute(text(f"SELECT id FROM {table} ORDER BY id"))
            ]
            for table in TABLES
        }
        result["ledger_total"] = str(
            db.scalar(text("SELECT SUM(amount) FROM ledger_entries"))
        )
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["capture", "verify"])
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    current = snapshot()
    if args.mode == "capture":
        args.file.write_text(json.dumps(current, sort_keys=True))
    else:
        assert json.loads(args.file.read_text()) == current, (
            "Persisted IDs or ledger total changed"
        )
    print(
        json.dumps(
            {
                "status": "captured" if args.mode == "capture" else "passed",
                "counts": {table: len(current[table]) for table in TABLES},
                "ledger_total_zar": current["ledger_total"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
