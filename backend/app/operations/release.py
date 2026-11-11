"""Explicit one-off owner release. Never configured as an API/worker pre-deploy hook."""

import os
from pathlib import Path

from alembic.config import Config

from alembic import command
from app.operations.neon_check import direct_neon_dsn, inspect_connection


def main() -> None:
    owner = os.environ["MIGRATION_DATABASE_URL"]
    direct_neon_dsn(owner)
    # This standalone owner operation validates direct verified TLS above. It is
    # intentionally separate from production runtime-role configuration.
    os.environ["DATABASE_URL"] = owner.replace("postgresql://", "postgresql+psycopg://", 1)
    os.environ["APP_ENV"] = "development"
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    command.upgrade(config, "head")
    if os.environ.get("SEED_SYNTHETIC_DEMO", "").lower() == "true":
        from app.seed import seed

        seed()
    from app.operations.roles import main as configure_roles

    configure_roles()
    inspect_connection(owner, runtime=False)
    print(
        "Owner release complete: migrations, explicit synthetic seed (if enabled), runtime grants and verified TLS. No credentials printed."
    )


if __name__ == "__main__":
    main()
