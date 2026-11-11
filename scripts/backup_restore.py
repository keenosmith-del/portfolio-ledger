"""Local Compose backup/restore drill; restore only into a newly created disposable DB.

Private dump exists only in a mode-0700 temporary directory and is removed on exit.
No existing source database is deleted, reset or mutated.
"""

import hashlib
import json
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import DBAPIError

TABLES = (
    "portfolios",
    "integration_sources",
    "leases",
    "lease_versions",
    "ledger_entries",
    "raw_records",
    "import_jobs",
    "pricing_versions",
    "reconciliations",
    "exceptions",
    "billing_previews",
    "billing_preview_lines",
    "audit_events",
)


def snapshot(url: URL) -> dict[str, object]:
    engine = create_engine(url)
    try:
        with engine.connect() as db:
            result: dict[str, object] = {}
            for table in TABLES:
                rows = [
                    dict(row._mapping)
                    for row in db.execute(text(f"SELECT * FROM {table} ORDER BY 1,2"))
                ]
                canonical = json.dumps(
                    sorted(json.dumps(row, sort_keys=True, default=str) for row in rows)
                )
                result[table] = {
                    "count": len(rows),
                    "sha256": hashlib.sha256(canonical.encode()).hexdigest(),
                }
            result["ledger_total"] = str(
                db.scalar(text("SELECT coalesce(sum(amount),0) FROM ledger_entries"))
            )
            return result
    finally:
        engine.dispose()


def main() -> None:
    name = "restore_verify_" + uuid4().hex
    source = create_engine(settings.database_url)
    url = source.url.set(database=name)
    if source.url.database != "ledger" or source.url.host not in {
        "localhost",
        "127.0.0.1",
    }:
        raise SystemExit(
            "This drill is restricted to the loopback Compose ledger database"
        )
    before = snapshot(source.url)
    created = False
    try:
        with source.connect().execution_options(isolation_level="AUTOCOMMIT") as db:
            db.execute(text(f'CREATE DATABASE "{name}"'))
            created = True
        with tempfile.TemporaryDirectory(
            prefix="portfolioledger-private-backup-"
        ) as folder:
            dump = Path(folder) / "demo.dump"
            with dump.open("wb") as output:
                subprocess.run(
                    [
                        "docker",
                        "compose",
                        "exec",
                        "-T",
                        "db",
                        "pg_dump",
                        "-U",
                        "ledger",
                        "-d",
                        "ledger",
                        "--schema=public",
                        "-Fc",
                    ],
                    stdout=output,
                    check=True,
                )
            dump.chmod(0o600)
            with dump.open("rb") as data:
                subprocess.run(
                    [
                        "docker",
                        "compose",
                        "exec",
                        "-T",
                        "db",
                        "pg_restore",
                        "-U",
                        "ledger",
                        "-d",
                        name,
                        "--clean",
                        "--if-exists",
                        "--no-owner",
                        "--no-acl",
                        "--exit-on-error",
                    ],
                    stdin=data,
                    check=True,
                    capture_output=True,
                )
        restored = snapshot(url)
        assert before == restored, "Restored business data differs from source snapshot"
        target = create_engine(url)
        try:
            try:
                with target.begin() as db:
                    db.execute(text("UPDATE ledger_entries SET amount=0"))
            except DBAPIError:
                immutable = True
            else:
                raise AssertionError("Restored evidence trigger failed")
        finally:
            target.dispose()
        evidence = {
            "status": "passed",
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "scope": "local Compose PostgreSQL; new disposable restore database removed afterward",
            "source_unchanged": before == snapshot(source.url),
            "restored_business_records_equal": True,
            "restored_immutability_trigger": immutable,
            "tables": before,
        }
        Path("docs/evidence/backup-restore.json").write_text(
            json.dumps(evidence, indent=2) + "\n"
        )
        print(json.dumps(evidence, indent=2))
    finally:
        if created:
            with source.connect().execution_options(isolation_level="AUTOCOMMIT") as db:
                db.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        source.dispose()


if __name__ == "__main__":
    main()
