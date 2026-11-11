from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import now
from app.integrations.synthetic import atlas_feed


def test_arbitrary_source_cannot_inflate(client: TestClient, demo: dict[str, Any]) -> None:
    response = client.post(
        f"/api/portfolios/{demo['a']}/imports",
        data={"adapter": "atlaspm", "source_key": "new-financial-namespace"},
        files={"file": ("snapshot.csv", atlas_feed(), "text/csv")},
        headers={"Idempotency-Key": "arbitrary-source"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "source_not_configured"


def test_ready_tracks_head(client: TestClient, factory: sessionmaker[Session]) -> None:
    from app.db.readiness import migration_heads

    response = client.get("/ready")
    assert response.status_code == 200
    assert set(response.json()["schema"].split(",")) == migration_heads()
    with factory.begin() as db:
        db.execute(text("UPDATE alembic_version SET version_num = 'b001'"))
    assert client.get("/ready").status_code == 503


def test_error_headers(client: TestClient) -> None:
    response = client.post("/api/auth/login", headers={"Content-Length": "invalid"})
    assert response.status_code == 400
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Request-ID"]


def test_production_fails_closed() -> None:
    import pytest
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="production")


def test_public_review_is_read_only(
    client: TestClient, demo: dict[str, Any], monkeypatch: Any
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "public_review_enabled", True)
    response = client.post("/api/auth/public-review")
    assert response.status_code == 200
    assert response.json()["role"] == "reviewer"
    client.headers["X-CSRF-Token"] = response.json()["csrf"]
    path = f"/api/portfolios/{demo['a']}"
    assert client.get(path + "/overview").status_code == 200
    for suffix in ["/reconciliations", "/billing-previews"]:
        assert (
            client.post(
                path + suffix, json={"month": "2026-11", "cutoff": now().isoformat()}
            ).status_code
            == 403
        )
    assert (
        client.post(
            path + "/imports",
            data={"adapter": "atlaspm", "source_key": "source"},
            files={"file": ("snapshot.csv", atlas_feed(), "text/csv")},
            headers={"Idempotency-Key": "public-write"},
        ).status_code
        == 403
    )


def test_registry_scope_replay_and_multiple_accounts(
    client: TestClient, demo: dict[str, Any], factory: sessionmaker[Session]
) -> None:
    import pytest
    from sqlalchemy import func, select
    from sqlalchemy.exc import IntegrityError

    from app.db.models import IntegrationSource, LedgerEntry
    from app.workers.runner import tick

    path = f"/api/portfolios/{demo['a']}"

    def upload(source: str, key: str) -> Any:
        return client.post(
            path + "/imports",
            data={"adapter": "atlaspm", "source_key": source},
            files={"file": ("snapshot.csv", atlas_feed(), "text/csv")},
            headers={"Idempotency-Key": key},
        )

    first = upload("source", "first")
    assert first.status_code == 202
    assert tick()
    assert upload("same-feed-alias", "alias").status_code == 422
    replay = client.post(
        path + "/imports/" + first.json()["id"] + "/replay", headers={"Idempotency-Key": "replay"}
    )
    assert replay.status_code == 202
    assert tick()
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(LedgerEntry)) == 5
    with pytest.raises(IntegrityError), factory.begin() as db:
        db.add(
            IntegrationSource(
                portfolio_id=demo["a"],
                adapter="atlaspm",
                source_key="alias",
                upstream_account="test-primary",
            )
        )
        db.flush()
    with factory.begin() as db:
        db.add(
            IntegrationSource(
                portfolio_id=demo["a"],
                adapter="atlaspm",
                source_key="second-account",
                upstream_account="independent-invented-provider-account",
            )
        )
        db.add(
            IntegrationSource(
                portfolio_id=demo["b"],
                adapter="meridianrent",
                source_key="harbour-only",
                upstream_account="harbour",
            )
        )
    assert upload("harbour-only", "cross").status_code == 422
    assert upload("second-account", "second").status_code == 202
    assert tick()
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(LedgerEntry)) == 10
    with factory.begin() as db:
        source = db.get(IntegrationSource, (demo["a"], "source"))
        assert source
        source.enabled = False
    assert (
        client.post(
            path + "/imports/" + first.json()["id"] + "/replay",
            headers={"Idempotency-Key": "disabled"},
        ).status_code
        == 422
    )


def test_public_mode_denies_admin_writes_and_non_demo_grants(
    client: TestClient, demo: dict[str, Any], factory: sessionmaker[Session], monkeypatch: Any
) -> None:
    from sqlalchemy import select

    from app.core.config import settings
    from app.db.models import Access, User

    monkeypatch.setattr(settings, "public_demo_read_only", True)
    path = f"/api/portfolios/{demo['a']}"
    assert (
        client.post(
            path + "/reconciliations", json={"month": "2026-11", "cutoff": now().isoformat()}
        ).status_code
        == 403
    )
    monkeypatch.setattr(settings, "public_review_enabled", True)
    with factory.begin() as db:
        user = db.scalar(select(User).where(User.email == "public-review@portfolioledger.test"))
        assert user
        db.add(Access(user_id=user.id, portfolio_id=demo["b"]))
    assert client.post("/api/auth/public-review").status_code == 503


def test_streamed_upload_and_host_protection(client: TestClient) -> None:
    from app.integrations.adapters import MAX_BYTES

    response = client.post("/api/auth/login", content=iter([b"x" * (MAX_BYTES + 65537)]))
    assert response.status_code == 413
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert client.get("/health", headers={"host": "evil.invalid"}).status_code == 400


def test_runtime_roles_cannot_own_or_bypass_evidence(
    factory: sessionmaker[Session], demo: dict[str, Any]
) -> None:
    from uuid import uuid4

    import pytest
    from sqlalchemy.exc import DBAPIError

    from app.operations.roles import grant_runtime

    api_role, worker_role = "test_api_" + uuid4().hex, "test_worker_" + uuid4().hex
    engine = factory.kw["bind"]
    with engine.begin() as connection:
        schema = connection.scalar(text("SELECT current_schema()"))
        for role in (api_role, worker_role):
            connection.execute(
                text(
                    f'CREATE ROLE "{role}" NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS'
                )
            )
        grant_runtime(connection.connection.driver_connection, schema, api_role, worker_role)
    try:
        for role in (api_role, worker_role):
            with engine.begin() as connection:
                connection.execute(text(f'SET LOCAL ROLE "{role}"'))
                assert connection.scalar(text("SELECT count(*) FROM ledger_entries")) == 0
            for statement in [
                "ALTER TABLE ledger_entries DISABLE TRIGGER ALL",
                "TRUNCATE ledger_entries",
                "UPDATE ledger_entries SET amount=0",
                "DELETE FROM ledger_entries",
                "INSERT INTO integration_sources (portfolio_id, source_key, adapter, upstream_account) VALUES ('x','x','x','x')",
            ]:
                with pytest.raises(DBAPIError), engine.begin() as connection:
                    connection.execute(text(f'SET LOCAL ROLE "{role}"'))
                    connection.execute(text(statement))
        with engine.begin() as connection:
            connection.execute(text(f'SET LOCAL ROLE "{api_role}"'))
            connection.execute(
                text(
                    "INSERT INTO rate_windows (key, count, started_at) VALUES ('role-probe', 1, CURRENT_TIMESTAMP)"
                )
            )
        with engine.begin() as connection:
            connection.execute(text(f'SET LOCAL ROLE "{worker_role}"'))
            connection.execute(
                text("UPDATE raw_records SET status='accepted' WHERE status='pending'")
            )
    finally:
        with engine.begin() as connection:
            for role in (api_role, worker_role):
                connection.execute(text(f'DROP OWNED BY "{role}"'))
                connection.execute(text(f'DROP ROLE "{role}"'))


def test_production_configuration_and_owner_readiness(client: TestClient, monkeypatch: Any) -> None:
    import pytest
    from pydantic import ValidationError

    from app.core.config import Settings, settings

    valid = dict(
        app_env="production",
        cookie_secure=True,
        database_url="postgresql+psycopg://api_runtime:synthetic-test-password-only@db.example.invalid/ledger?sslmode=verify-full",
        allowed_origins=["https://demo.example.invalid"],
        allowed_hosts=["demo.example.invalid"],
        trusted_proxy_ips=["10.0.0.2/32"],
        public_review_enabled=True,
        public_demo_read_only=True,
    )
    assert Settings(_env_file=None, **valid).cookie_secure
    for change in [
        dict(cookie_secure=False),
        dict(allowed_origins=["http://demo.example.invalid"]),
        dict(allowed_hosts=["*"]),
        dict(trusted_proxy_ips=["0.0.0.0/0"]),
        dict(public_demo_read_only=False),
        dict(database_url="postgresql://ledger:weak@localhost/ledger"),
    ]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **(valid | change))
    monkeypatch.setattr(settings, "app_env", "production")
    assert client.get("/ready").status_code == 503
    assert client.get("/ready").json()["error"]["code"] == "runtime_role_is_privileged"


def test_cleanup_and_private_session_cap(
    client: TestClient, demo: dict[str, Any], factory: sessionmaker[Session]
) -> None:
    from datetime import timedelta

    from app.core.auth import rate_limit
    from app.db.models import AuthSession, RateWindow

    with factory.begin() as db:
        db.add(
            AuthSession(
                user_id=demo["admin"],
                token_hash="expired",
                csrf="expired",
                expires_at=now() - timedelta(hours=1),
            )
        )
        db.add(RateWindow(key="expired-window", count=1, started_at=now() - timedelta(days=2)))
        for n in range(19):
            db.add(
                AuthSession(
                    user_id=demo["admin"],
                    token_hash=f"cap-{n}",
                    csrf="cap",
                    expires_at=now() + timedelta(hours=1),
                )
            )
    with factory() as db:
        rate_limit(db, "cleanup-probe", 10)
    with factory() as db:
        from sqlalchemy import select

        assert db.scalar(select(AuthSession).where(AuthSession.token_hash == "expired")) is None
        assert db.get(RateWindow, "expired-window") is None
    # A separate browser with no prior session cannot create the 21st active session.
    client.cookies.clear()
    assert (
        client.post(
            "/api/auth/login", json={"email": "admin@test.invalid", "password": "TestPassword123!"}
        ).status_code
        == 429
    )


def test_separate_runtime_roles_complete_financial_journey(
    factory: sessionmaker[Session], demo: dict[str, Any], monkeypatch: Any
) -> None:
    from uuid import uuid4

    from sqlalchemy import create_engine

    import app.db.session as sessions
    import app.workers.runner as worker
    from app.core.config import settings
    from app.main import app
    from app.operations.roles import grant_runtime

    api_role, worker_role = "test_api_" + uuid4().hex, "test_worker_" + uuid4().hex
    owner = factory.kw["bind"]
    with owner.begin() as connection:
        schema = connection.scalar(text("SELECT current_schema()"))
        for role in (api_role, worker_role):
            connection.execute(
                text(
                    f'CREATE ROLE "{role}" NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS'
                )
            )
        grant_runtime(connection.connection.driver_connection, schema, api_role, worker_role)
    engines = [
        create_engine(
            settings.database_url, connect_args={"options": f"-csearch_path={schema} -crole={role}"}
        )
        for role in (api_role, worker_role)
    ]
    try:
        monkeypatch.setattr(
            sessions, "SessionLocal", sessionmaker(engines[0], expire_on_commit=False)
        )
        monkeypatch.setattr(
            worker, "SessionLocal", sessionmaker(engines[1], expire_on_commit=False)
        )
        with TestClient(app) as client:
            login = client.post(
                "/api/auth/login",
                json={"email": "admin@test.invalid", "password": "TestPassword123!"},
            )
            assert login.status_code == 200, login.text
            client.headers["X-CSRF-Token"] = login.json()["csrf"]
            path = f"/api/portfolios/{demo['a']}"
            response = client.post(
                path + "/imports",
                data={"adapter": "atlaspm", "source_key": "source"},
                files={"file": ("snapshot.csv", atlas_feed(), "text/csv")},
                headers={"Idempotency-Key": "roles"},
            )
            assert response.status_code == 202, response.text
            assert worker.tick()
            assert client.get(path + "/ledger").json()["total"] == 5
            payload = {"month": "2026-11", "cutoff": now().isoformat()}
            assert client.post(path + "/reconciliations", json=payload).status_code == 200
            preview = client.post(path + "/billing-previews", json=payload)
            assert preview.status_code == 200, preview.text
            assert preview.json()["total"] == "170.00"
            assert (
                client.get(
                    path + "/billing-previews/" + preview.json()["id"] + "/export.csv"
                ).status_code
                == 200
            )
            monkeypatch.setattr(settings, "app_env", "production")
            assert client.get("/ready").status_code == 200
    finally:
        for engine in engines:
            engine.dispose()
        with owner.begin() as connection:
            for role in (api_role, worker_role):
                connection.execute(text(f'DROP OWNED BY "{role}"'))
                connection.execute(text(f'DROP ROLE "{role}"'))


def test_public_scope_rechecked_after_session(
    client: TestClient, demo: dict[str, Any], factory: sessionmaker[Session], monkeypatch: Any
) -> None:
    from app.core.config import settings
    from app.db.models import Portfolio

    monkeypatch.setattr(settings, "public_review_enabled", True)
    assert client.post("/api/auth/public-review").status_code == 200
    assert client.get("/api/portfolios").json()[0]["id"] == demo["a"]
    with factory.begin() as db:
        portfolio = db.get(Portfolio, demo["a"])
        assert portfolio
        portfolio.synthetic_demo = False
    assert client.get("/api/portfolios").json() == []
    assert client.get(f"/api/portfolios/{demo['a']}/overview").status_code == 404
