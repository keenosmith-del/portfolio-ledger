from typing import Any

import pytest

from app.core.config import Settings
from app.operations.neon_check import direct_neon_dsn


def test_direct_neon_requires_verified_tls_and_ca(tmp_path: Any, monkeypatch: Any) -> None:
    root = tmp_path / "ca.pem"
    root.write_text("fixture-only")
    monkeypatch.setenv("PGSSLROOTCERT", str(root))
    direct = "postgresql+psycopg://runtime:synthetic-password@ep-test.us-east-2.aws.neon.tech/db?sslmode=verify-full"
    assert direct_neon_dsn(direct).startswith("postgresql://")
    for bad in [
        direct.replace("verify-full", "require"),
        direct.replace("ep-test.", "ep-test-pooler."),
        direct.replace("aws.neon.tech", "example.invalid"),
    ]:
        with pytest.raises(ValueError):
            direct_neon_dsn(bad)
    monkeypatch.setenv("PGSSLROOTCERT", str(tmp_path / "missing"))
    with pytest.raises(ValueError):
        direct_neon_dsn(direct)


def test_proxy_dns_resolves_only_exact_addresses(monkeypatch: Any) -> None:
    from app.operations import serve

    monkeypatch.setattr(serve.settings, "trusted_proxy_ips", [])
    monkeypatch.setattr(serve.settings, "trusted_proxy_hosts", ["web.railway.internal"])
    monkeypatch.setattr(
        serve.socket,
        "getaddrinfo",
        lambda *a, **k: [(10, 1, 6, "", ("fd12:3456::2", 0, 0, 0)), (2, 1, 6, "", ("10.0.0.7", 0))],
    )
    assert serve.proxy_addresses() == ["10.0.0.7", "fd12:3456::2"]
    monkeypatch.setattr(serve.socket, "getaddrinfo", lambda *a, **k: [])
    monkeypatch.setattr(serve.settings, "app_env", "production")
    with pytest.raises(ValueError):
        serve.proxy_addresses()


def test_proxy_dns_configuration_and_dynamic_port() -> None:
    from pydantic import ValidationError

    valid = dict(
        app_env="production",
        cookie_secure=True,
        public_review_enabled=True,
        public_demo_read_only=True,
        database_url="postgresql+psycopg://api_runtime:synthetic-test-password-only@ep-test.aws.neon.tech/db?sslmode=verify-full",
        allowed_origins=["https://demo.example.invalid"],
        allowed_hosts=["demo.example.invalid", "healthcheck.railway.app"],
        trusted_proxy_ips=[],
        trusted_proxy_hosts=["web.railway.internal"],
        api_bind_host="::",
        port=8765,
    )
    assert Settings(_env_file=None, **valid).port == 8765
    for change in [
        dict(trusted_proxy_hosts=["*.railway.internal"]),
        dict(trusted_proxy_hosts=["evil.example.invalid"]),
        dict(port=0),
        dict(port=65536),
    ]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **(valid | change))


def test_client_tls_must_be_active_and_verified() -> None:
    from types import SimpleNamespace

    from app.operations.neon_check import verify_client_tls

    connection: Any = SimpleNamespace(
        pgconn=SimpleNamespace(ssl_in_use=True),
        info=SimpleNamespace(get_parameters=lambda: {"sslmode": "verify-full"}),
    )
    verify_client_tls(connection)
    connection.pgconn.ssl_in_use = False
    with pytest.raises(ValueError):
        verify_client_tls(connection)
    connection.pgconn.ssl_in_use = True
    connection.info.get_parameters = lambda: {"sslmode": "require"}
    with pytest.raises(ValueError):
        verify_client_tls(connection)
