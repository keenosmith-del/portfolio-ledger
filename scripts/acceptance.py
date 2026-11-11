"""Isolated real-PostgreSQL acceptance journey and 10,000-event benchmark.

Run from repository root: .venv/bin/python scripts/acceptance.py
The unique temporary schema is dropped in finally; existing demo data is untouched.
"""

import json
import platform
import subprocess
import time
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import app.db.session as sessions
import app.workers.runner as worker
from alembic import command
from alembic.config import Config
from app.core.auth import hasher
from app.core.config import settings
from app.db.models import Access, ImportJob, LedgerEntry, Portfolio, Pricing, User, now
from app.integrations.synthetic import atlas_feed, meridian_feed
from app.main import app
from app.services.ingestion import enqueue
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

root = Path(__file__).resolve().parents[1]
schema = "acceptance_" + uuid4().hex
admin_engine = create_engine(settings.database_url)
engine = create_engine(
    settings.database_url, connect_args={"options": f"-csearch_path={schema}"}
)
factory = sessionmaker(engine, expire_on_commit=False)
original_factory, original_worker = sessions.SessionLocal, worker.SessionLocal
started = time.monotonic()
try:
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    cfg = Config(str(root / "backend" / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "backend" / "alembic"))
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")
    sessions.SessionLocal = factory
    worker.SessionLocal = factory
    with factory.begin() as db:
        actor = User(
            email="acceptance@portfolioledger.test",
            password_hash=hasher.hash("Acceptance-only-passphrase"),
            role="admin",
        )
        cedar = Portfolio(name="Acceptance Cedar", adapter="atlaspm")
        harbour = Portfolio(name="Acceptance Harbour", adapter="meridianrent")
        db.add_all([actor, cedar, harbour])
        db.flush()
        for portfolio in (cedar, harbour):
            db.add(Access(user_id=actor.id, portfolio_id=portfolio.id))
            db.add(
                Pricing(
                    portfolio_id=portfolio.id,
                    version=1,
                    monthly_fee=Decimal("85.00"),
                    effective_from=date(2024, 1, 1),
                )
            )
    with TestClient(app) as client:
        login = client.post(
            "/api/auth/login",
            json={"email": actor.email, "password": "Acceptance-only-passphrase"},
        )
        assert login.status_code == 200, login.text
        client.headers["X-CSRF-Token"] = login.json()["csrf"]
        assert len(client.get("/api/portfolios").json()) == 2
        for portfolio, content, filename, mime in [
            (cedar, atlas_feed(), "snapshot.csv", "text/csv"),
            (harbour, meridian_feed(), "events.json", "application/json"),
        ]:
            response = client.post(
                f"/api/portfolios/{portfolio.id}/imports",
                data={"adapter": portfolio.adapter, "source_key": "demo"},
                files={"file": (filename, content, mime)},
                headers={"Idempotency-Key": "journey"},
            )
            assert response.status_code == 202, response.text
            assert worker.tick()
        base = f"/api/portfolios/{cedar.id}"
        assert client.get(base + "/leases").json()["total"] == 2
        assert client.get(base + "/ledger").json()["total"] == 5
        run = client.post(
            base + "/reconciliations",
            json={"month": "2026-11", "cutoff": now().isoformat()},
        )
        assert run.status_code == 200, run.text
        exceptions = client.get(base + "/exceptions").json()["items"]
        assert len(exceptions) == 4
        review = client.post(
            base + "/exceptions/" + exceptions[0]["id"] + "/resolve",
            json={
                "status": "resolved",
                "rationale": "Acceptance reviewed persisted source evidence",
            },
        )
        assert review.status_code == 200
        request = {"month": "2026-11", "cutoff": now().isoformat()}
        first = client.post(base + "/billing-previews", json=request)
        again = client.post(base + "/billing-previews", json=request)
        assert first.status_code == 200 and first.json()["id"] == again.json()["id"]
        assert first.json()["total"] == "170.00"
        csv = client.get(
            base + "/billing-previews/" + first.json()["id"] + "/export.csv"
        )
        assert csv.status_code == 200 and "170.00" in csv.text
        assert client.get(base + "/audit").json()["total"] >= 5
        assert client.get("/ready").status_code == 200
    content = atlas_feed(10000, True)
    assert content == atlas_feed(10000, True), "generator must be deterministic"
    timings = []
    receipts = []
    for key in ("load-initial", "load-replay"):
        begin = time.monotonic()
        with factory.begin() as db:
            job, _ = enqueue(
                db,
                cedar.id,
                "atlaspm",
                "benchmark",
                key,
                "load.csv",
                content,
                actor.id,
                key,
            )
            job_id = job.id
        assert worker.tick()
        timings.append(round(time.monotonic() - begin, 3))
        with factory() as db:
            job = db.get(ImportJob, job_id)
            assert job and job.status == "partially_completed"
            receipts.append(
                {
                    "accepted": job.accepted,
                    "duplicates": job.duplicates,
                    "quarantined": job.quarantined,
                }
            )
    with factory() as db:
        count, total = db.execute(
            select(func.count(), func.sum(LedgerEntry.amount)).where(
                LedgerEntry.source_key == "benchmark"
            )
        ).one()
    assert receipts == [
        {"accepted": 10002, "duplicates": 0, "quarantined": 2},
        {"accepted": 0, "duplicates": 10002, "quarantined": 2},
    ], receipts
    assert count == 10000 and total == Decimal("18750000.00"), (count, total)
    output = {
        "status": "passed",
        "timestamp_utc": now().isoformat(),
        "python": platform.python_version(),
        "platform": platform.system() + " " + platform.machine(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=root, text=True
        ).strip(),
        "working_tree": "see git status; benchmark includes uncommitted acceptance script",
        "financial_events": 10000,
        "artifact_bytes": len(content),
        "receipts": receipts,
        "first_import_seconds": timings[0],
        "replay_seconds": timings[1],
        "ledger_entries_after_replay": count,
        "ledger_total_zar": str(total),
        "full_journey_seconds": round(time.monotonic() - started, 3),
        "isolation": "temporary PostgreSQL schema; migrated from blank; removed on exit",
    }
    print(json.dumps(output, indent=2))
finally:
    sessions.SessionLocal, worker.SessionLocal = original_factory, original_worker
    engine.dispose()
    with admin_engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    admin_engine.dispose()
