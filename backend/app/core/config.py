from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env", extra="ignore"
    )
    database_url: str = "postgresql+psycopg://ledger:ledger_local@localhost:5438/ledger"
    app_env: str = "development"
    cookie_secure: bool = False
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    demo_password: str = ""


settings = Settings()
