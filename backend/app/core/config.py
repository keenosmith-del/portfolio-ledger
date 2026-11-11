import ipaddress
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        extra="ignore",
        hide_input_in_errors=True,
    )
    database_url: str = Field(
        default="postgresql+psycopg://ledger:ledger_local@localhost:5438/ledger", repr=False
    )
    app_env: Literal["development", "test", "production"] = "development"
    cookie_secure: bool = False
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    trusted_proxy_ips: list[str] = []
    demo_password: str = Field(default="", repr=False)
    public_review_enabled: bool = False
    public_demo_read_only: bool = False
    seed_synthetic_demo: bool = False

    @model_validator(mode="after")
    def production_contract(self) -> Self:
        if self.app_env != "production":
            return self
        url = make_url(self.database_url)
        if not self.cookie_secure:
            raise ValueError("production requires secure cookies")
        if not self.allowed_origins or any(
            urlsplit(origin).scheme != "https"
            or not urlsplit(origin).hostname
            or urlsplit(origin).path not in {"", "/"}
            or urlsplit(origin).query
            or urlsplit(origin).fragment
            or urlsplit(origin).username
            for origin in self.allowed_origins
        ):
            raise ValueError("production requires explicit HTTPS origins")
        if not self.allowed_hosts or any(
            h in {"*", "localhost", "127.0.0.1", "testserver"} or h.startswith("*.")
            for h in self.allowed_hosts
        ):
            raise ValueError("production requires explicit trusted hosts")
        if any(urlsplit(o).hostname not in self.allowed_hosts for o in self.allowed_origins):
            raise ValueError("origin hosts must be trusted")
        if not self.trusted_proxy_ips:
            raise ValueError("production requires explicit proxy addresses")
        for address in self.trusted_proxy_ips:
            network = ipaddress.ip_network(address)
            if network.prefixlen == 0:
                raise ValueError("unbounded proxy trust forbidden")
        if (
            url.get_backend_name() != "postgresql"
            or not url.username
            or not url.host
            or not url.password
            or len(url.password) < 20
            or url.username in {"ledger", "postgres"}
            or url.query.get("sslmode") not in {"verify-full"}
        ):
            raise ValueError(
                "production requires a private runtime PostgreSQL role and verified TLS"
            )
        if self.public_review_enabled and not self.public_demo_read_only:
            raise ValueError("public reviewer requires globally read-only business APIs")
        return self


settings = Settings()
