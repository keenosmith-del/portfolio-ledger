from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import ExceptionRecord, ImportJob, LedgerEntry, Preview, RawRecord, now
from app.integrations.synthetic import atlas_feed, meridian_feed
from app.services.finance import preview, reconcile
from app.services.ingestion import claim, enqueue, process
from app.workers.runner import tick


def queued(
    factory: sessionmaker[Session],
    demo: dict[str, Any],
    content: bytes | None = None,
    key: str = "first",
    portfolio: str = "a",
) -> str:
    with factory.begin() as db:
        job, _ = enqueue(
            db,
            demo[portfolio],
            "atlaspm" if portfolio == "a" else "meridianrent",
            "source",
            key,
            "snapshot.csv" if portfolio == "a" else "events.json",
            content if content is not None else atlas_feed(),
            demo["admin"],
            "test",
        )
        return job.id


def test_replay_and_conflict(factory: sessionmaker[Session], demo: dict[str, Any]) -> None:
    job_id = queued(factory, demo)
    assert tick()
    with factory.begin() as db:
        job = db.get(ImportJob, job_id)
        assert job and (job.accepted, job.duplicates, job.quarantined) == (7, 0, 2)
        count = db.scalar(select(func.count()).select_from(LedgerEntry))
        same, duplicate = enqueue(
            db,
            demo["a"],
            "atlaspm",
            "source",
            "first",
            "snapshot.csv",
            atlas_feed(),
            demo["admin"],
            "test",
        )
        assert duplicate and same.id == job_id
    queued(factory, demo, key="second")
    assert tick()
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(LedgerEntry)) == count
        replay = db.scalar(select(ImportJob).where(ImportJob.idempotency_key == "second"))
        assert replay and replay.duplicates == 7 and replay.quarantined == 2
    with pytest.raises(HTTPException) as conflict, factory.begin() as db:
        enqueue(
            db,
            demo["a"],
            "atlaspm",
            "source",
            "first",
            "snapshot.csv",
            atlas_feed(4),
            demo["admin"],
            "test",
        )
    assert conflict.value.status_code == 409


def test_concurrent_imports(factory: sessionmaker[Session], demo: dict[str, Any]) -> None:
    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(lambda _: queued(factory, demo, atlas_feed(4, False)), range(2)))
    assert ids[0] == ids[1]
    # Distinct requests of the same content converge at source-level posting deduplication.
    queued(factory, demo, atlas_feed(4, False), key="another")
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: tick(), range(2)))
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(LedgerEntry)) == 4
        assert db.scalar(select(func.sum(ImportJob.duplicates))) == 6


def test_corrections_and_out_of_order(factory: sessionmaker[Session], demo: dict[str, Any]) -> None:
    queued(factory, demo, meridian_feed(), portfolio="b")
    assert tick()
    with factory() as db:
        entries = list(db.scalars(select(LedgerEntry)))
        assert len(entries) == 4
        assert sum(e.amount for e in entries) == Decimal("4500.00")
        reversal = next(e for e in entries if e.kind == "reversal")
        assert reversal.reverses_id in {e.id for e in entries}
        assert reversal.amount == Decimal("-8900.00")
        assert (
            db.scalar(select(RawRecord.reason).where(RawRecord.status == "quarantined"))
            == "stale_revision"
        )


def test_crash_recovery(factory: sessionmaker[Session], demo: dict[str, Any]) -> None:
    job_id = queued(factory, demo)
    with factory.begin() as db:
        assert claim(db) == job_id
    with pytest.raises(RuntimeError, match="deterministic_crash"), factory.begin() as db:
        process(db, job_id, fail_after=4)
    with factory.begin() as db:
        assert db.scalar(select(func.count()).select_from(LedgerEntry)) == 0
        assert db.scalar(select(func.count()).select_from(RawRecord)) == 0
        job = db.get(ImportJob, job_id)
        assert job and job.status == "processing"
        job.lease_until = now() - timedelta(seconds=1)
    assert tick()
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(LedgerEntry)) == 5
        job = db.get(ImportJob, job_id)
        assert job and job.attempts == 2 and job.accepted == 7


def test_append_only_and_composite_fk(factory: sessionmaker[Session], demo: dict[str, Any]) -> None:
    queued(factory, demo)
    tick()
    with pytest.raises(DBAPIError, match="immutable financial evidence"), factory.begin() as db:
        db.execute(text("UPDATE ledger_entries SET amount=1"))
    with factory() as db:
        entry = db.scalar(select(LedgerEntry))
        assert entry
        values = {"lease_id": entry.lease_id, "raw_id": entry.raw_id}
    with pytest.raises(IntegrityError), factory.begin() as db:
        db.add(
            LedgerEntry(
                portfolio_id=demo["b"],
                source_key="bad",
                external_id="bad",
                revision=1,
                kind="charge",
                amount=Decimal("1"),
                effective_date=now().date(),
                reason="invalid scope",
                **values,
            )
        )


def test_reconcile_and_concurrent_preview(
    factory: sessionmaker[Session], demo: dict[str, Any]
) -> None:
    queued(factory, demo)
    tick()
    cutoff = now()
    with factory.begin() as db:
        run = reconcile(db, demo["a"], "2026-11", cutoff, demo["admin"], "test")
        run_id = run.id
    with factory() as db:
        evidence = list(db.scalars(select(ExceptionRecord).where(ExceptionRecord.run_id == run_id)))
        assert len(evidence) == 4
        assert all(e.evidence for e in evidence)

    def calculate(_: int) -> tuple[str, Decimal]:
        with factory.begin() as db:
            result = preview(db, demo["a"], "2026-11", cutoff, demo["admin"], "test")
            return result.id, result.total

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(calculate, range(2)))
    assert results[0] == results[1]
    assert results[0][1] == Decimal("170.00")
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Preview)) == 1


def test_http_journey(
    client: TestClient, demo: dict[str, Any], factory: sessionmaker[Session]
) -> None:
    path = f"/api/portfolios/{demo['a']}"
    response = client.post(
        path + "/imports",
        files={"file": ("snapshot.csv", atlas_feed(), "text/csv")},
        data={"adapter": "atlaspm", "source_key": "source"},
        headers={"Idempotency-Key": "http-first"},
    )
    assert response.status_code == 202, response.text
    job_id = response.json()["id"]
    assert tick()
    receipt = client.get(path + "/imports/" + job_id).json()
    assert receipt["job"]["quarantined"] == 2
    assert client.get(path + "/leases").json()["total"] == 2
    ledger = client.get(path + "/ledger").json()
    assert ledger["total"] == 5
    assert client.get(path + "/sources/" + ledger["items"][0]["raw_id"]).status_code == 200
    payload = {"month": "2026-11", "cutoff": now().isoformat()}
    assert client.post(path + "/reconciliations", json=payload).status_code == 200
    record = client.get(path + "/exceptions").json()["items"][0]
    assert (
        client.post(
            path + "/exceptions/" + record["id"] + "/resolve",
            json={
                "status": "resolved",
                "rationale": "Reviewed source evidence; no financial posting",
            },
        ).status_code
        == 200
    )
    result = client.post(path + "/billing-previews", json=payload)
    assert result.status_code == 200, result.text
    assert result.json()["total"] == "170.00"
    preview_id = result.json()["id"]
    assert "170.00" in client.get(path + "/billing-previews/" + preview_id + "/export.csv").text
    assert client.get(path + "/audit").json()["total"] >= 5
    assert client.get(path + "/overview").json()["active_leases"] == 2
    # HTTP payload conflict is a 409, not a duplicate success.
    conflict = client.post(
        path + "/imports",
        files={"file": ("snapshot.csv", atlas_feed(4), "text/csv")},
        data={"adapter": "atlaspm", "source_key": "source"},
        headers={"Idempotency-Key": "http-first"},
    )
    assert conflict.status_code == 409
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get(path + "/leases").status_code == 401


def test_idor_and_roles(
    client: TestClient, demo: dict[str, Any], factory: sessionmaker[Session]
) -> None:
    queued(factory, demo, meridian_feed(), portfolio="b")
    tick()
    with factory() as db:
        other_entry = db.scalar(select(LedgerEntry))
        assert other_entry
        raw_id = other_entry.raw_id
    response = client.post(
        "/api/auth/login", json={"email": "analyst@test.invalid", "password": "TestPassword123!"}
    )
    client.headers["X-CSRF-Token"] = response.json()["csrf"]
    assert len(client.get("/api/portfolios").json()) == 1
    a = f"/api/portfolios/{demo['a']}"
    b = f"/api/portfolios/{demo['b']}"
    assert client.get(b + "/ledger").status_code == 404
    assert client.get(a + "/sources/" + raw_id).status_code == 404
    assert (
        client.post(
            b + "/reconciliations", json={"month": "2026-11", "cutoff": now().isoformat()}
        ).status_code
        == 404
    )
    response = client.post(
        "/api/auth/login", json={"email": "reader@test.invalid", "password": "TestPassword123!"}
    )
    client.headers["X-CSRF-Token"] = response.json()["csrf"]
    assert (
        client.post(
            a + "/reconciliations", json={"month": "2026-11", "cutoff": now().isoformat()}
        ).status_code
        == 403
    )
    client.headers.pop("X-CSRF-Token")
    assert client.post("/api/auth/logout").status_code == 403


def test_upload_safety(client: TestClient, demo: dict[str, Any]) -> None:
    path = f"/api/portfolios/{demo['a']}/imports"

    def upload(name: str, content: bytes, mime: str = "text/csv") -> Any:
        return client.post(
            path,
            files={"file": (name, content, mime)},
            data={"adapter": "atlaspm", "source_key": "source"},
            headers={"Idempotency-Key": "unsafe"},
        )

    assert upload("malware.exe", b"hello").status_code == 422
    assert upload("bad.csv", b"bad,columns\n1,2").status_code == 422
    assert upload("bad.csv", b"\0").status_code == 422
    assert upload("big.csv", b"x" * (8 * 1024 * 1024 + 1)).status_code == 413
    assert upload("bad.csv", atlas_feed(), "text/html").status_code == 422
    response = client.post(
        "/api/auth/login", json={"email": "admin@test.invalid", "password": "wrong"}
    )
    assert response.status_code == 401
    assert "wrong" not in response.text


def test_retries_bounded(factory: sessionmaker[Session], demo: dict[str, Any]) -> None:
    job_id = queued(factory, demo)
    with factory.begin() as db:
        job = db.get(ImportJob, job_id)
        assert job
        job.attempts = 3
    assert tick() is False
    with factory() as db:
        job = db.get(ImportJob, job_id)
        assert job and job.status == "failed" and job.error == "attempt_limit_exceeded"
