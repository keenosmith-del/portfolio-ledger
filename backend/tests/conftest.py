from collections.abc import Generator
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

import app.db.session as sessions
import app.workers.runner as worker
from alembic import command
from app.core.config import settings
from app.db.models import Access, Portfolio, Pricing, User
from app.main import app


@pytest.fixture()
def factory(monkeypatch: pytest.MonkeyPatch) -> Generator[sessionmaker[Session], None, None]:
    schema = "test_" + uuid4().hex
    admin = create_engine(settings.database_url)
    with admin.begin() as db:
        db.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        settings.database_url, connect_args={"options": f"-csearch_path={schema}"}, pool_size=10
    )
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    factory = sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(sessions, "SessionLocal", factory)
    monkeypatch.setattr(worker, "SessionLocal", factory)
    yield factory
    engine.dispose()
    with admin.begin() as db:
        db.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    admin.dispose()


@pytest.fixture()
def demo(factory: sessionmaker[Session]) -> dict[str, Any]:
    from datetime import date
    from decimal import Decimal

    from app.core.auth import hasher

    with factory.begin() as db:
        admin = User(
            email="admin@test.invalid", role="admin", password_hash=hasher.hash("TestPassword123!")
        )
        analyst = User(
            email="analyst@test.invalid", role="analyst", password_hash=admin.password_hash
        )
        reader = User(
            email="reader@test.invalid", role="reviewer", password_hash=admin.password_hash
        )
        a, b = (
            Portfolio(name="Test Cedar", adapter="atlaspm"),
            Portfolio(name="Test Harbour", adapter="meridianrent"),
        )
        db.add_all([admin, analyst, reader, a, b])
        db.flush()
        for user, portfolio in [(admin, a), (admin, b), (analyst, a), (reader, a)]:
            db.add(Access(user_id=user.id, portfolio_id=portfolio.id))
        db.add_all(
            [
                Pricing(
                    portfolio_id=p.id,
                    version=1,
                    monthly_fee=Decimal("85.00"),
                    effective_from=date(2024, 1, 1),
                )
                for p in (a, b)
            ]
        )
    return {"admin": admin.id, "analyst": analyst.id, "a": a.id, "b": b.id}


@pytest.fixture()
def client(demo: dict[str, Any]) -> Generator[TestClient, None, None]:
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/auth/login", json={"email": "admin@test.invalid", "password": "TestPassword123!"}
        )
        assert response.status_code == 200, response.text
        client.headers["X-CSRF-Token"] = response.json()["csrf"]
        yield client
