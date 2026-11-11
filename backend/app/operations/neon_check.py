"""Read-only Neon connection and runtime boundary verification. Never print a DSN."""

import json
import os
from pathlib import Path
from typing import Any

import psycopg
from sqlalchemy.engine import make_url

from app.db.readiness import migration_heads


def direct_neon_dsn(value: str) -> str:
    url = make_url(value)
    if (
        url.get_backend_name() != "postgresql"
        or not url.host
        or not url.host.endswith(".neon.tech")
        or "-pooler." in url.host
        or url.query.get("sslmode") != "verify-full"
    ):
        raise ValueError("A direct Neon PostgreSQL connection with sslmode=verify-full is required")
    root = os.environ.get("PGSSLROOTCERT", "")
    if not root or not Path(root).is_file():
        raise ValueError("PGSSLROOTCERT must identify a readable trusted CA bundle")
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


def inspect_connection(value: str, *, runtime: bool) -> dict[str, Any]:
    with psycopg.connect(direct_neon_dsn(value), connect_timeout=15) as db:
        ssl = db.execute(
            "SELECT ssl,version FROM pg_stat_ssl WHERE pid=pg_backend_pid()"
        ).fetchone()
        if ssl is None or not ssl[0]:
            raise ValueError("Database connection is not TLS encrypted")
        flags = db.execute(
            "SELECT rolsuper,rolcreaterole,rolcreatedb,rolbypassrls FROM pg_roles WHERE rolname=current_user"
        ).fetchone()
        ownership = db.execute(
            "SELECT pg_has_role(current_user,nspowner,'MEMBER') OR pg_has_role(current_user,datdba,'MEMBER') FROM pg_namespace CROSS JOIN pg_database WHERE nspname=current_schema() AND datname=current_database()"
        ).fetchone()
        table_owner = db.execute(
            "SELECT count(*) FROM pg_tables WHERE schemaname=current_schema() AND pg_has_role(current_user,tableowner,'MEMBER')"
        ).fetchone()
        membership = db.execute(
            "SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user)"
        ).fetchone()
        if runtime and (
            flags is None
            or any(flags)
            or not ownership
            or ownership[0]
            or not table_owner
            or table_owner[0]
            or not membership
            or membership[0]
        ):
            raise ValueError(
                "Runtime role is privileged, inherits another role, or owns database/schema/tables"
            )
        versions = {str(row[0]) for row in db.execute("SELECT version_num FROM alembic_version")}
        if versions != migration_heads():
            raise ValueError("Database migration head is not current")
        return {
            "tls": True,
            "tls_version": ssl[1],
            "certificate_mode": "verify-full",
            "direct_connection": True,
            "migration_heads": sorted(versions),
            "runtime_role_verified": runtime,
        }


def main() -> None:
    print(json.dumps(inspect_connection(os.environ["DATABASE_URL"], runtime=True), indent=2))


if __name__ == "__main__":
    main()
