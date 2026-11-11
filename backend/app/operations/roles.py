"""Explicit owner-run release step. Runtime processes never execute this module."""

import os

import psycopg
from psycopg import sql

API_INSERT = (
    "sessions",
    "rate_windows",
    "import_jobs",
    "reconciliations",
    "exceptions",
    "billing_previews",
    "billing_preview_lines",
    "audit_events",
)
API_UPDATE = ("sessions", "rate_windows", "exceptions")
WORKER_INSERT = (
    "raw_records",
    "units",
    "tenants",
    "leases",
    "lease_versions",
    "ledger_entries",
    "audit_events",
)
WORKER_UPDATE = ("raw_records", "import_jobs")


def grant_runtime(
    connection: psycopg.Connection[tuple[object, ...]], schema: str, api_role: str, worker_role: str
) -> None:
    """Grant known operations; roles and owner must already be distinct."""
    if api_role == worker_role:
        raise ValueError("API and worker roles must differ")
    for role in (api_role, worker_role):
        row = connection.execute(
            "SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls FROM pg_roles WHERE rolname=%s",
            (role,),
        ).fetchone()
        if row is None or any(row):
            raise ValueError("runtime role missing or privileged")
        membership = connection.execute(
            "SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member WHERE r.rolname=%s",
            (role,),
        ).fetchone()
        if membership and membership[0] != 0:
            raise ValueError("runtime roles must not inherit other roles")
        owners = connection.execute(
            "SELECT count(*) FROM pg_tables WHERE schemaname=%s AND tableowner=%s", (schema, role)
        ).fetchone()
        if owners and owners[0] != 0:
            raise ValueError("runtime roles must not own tables")
        r, s = sql.Identifier(role), sql.Identifier(schema)
        connection.execute(sql.SQL("REVOKE ALL ON SCHEMA {} FROM {}").format(s, r))
        connection.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(s, r))
        connection.execute(sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA {} FROM {}").format(s, r))
        connection.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}").format(s, r))
        if role == worker_role:
            connection.execute(
                sql.SQL(
                    "REVOKE SELECT ON {}.users, {}.sessions, {}.rate_windows, {}.portfolio_access FROM {}"
                ).format(s, s, s, s, r)
            )
        for action, tables in [
            ("INSERT", API_INSERT if role == api_role else WORKER_INSERT),
            ("UPDATE", API_UPDATE if role == api_role else WORKER_UPDATE),
            ("DELETE", ("sessions", "rate_windows") if role == api_role else ()),
        ]:
            for table in tables:
                connection.execute(
                    sql.SQL("GRANT {} ON {}.{} TO {}").format(
                        sql.SQL(action), s, sql.Identifier(table), r
                    )
                )


def main() -> None:
    # Owner DSN and passwords come only from private environment, never CLI arguments.
    dsn = os.environ["MIGRATION_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    schema = os.environ.get("DATABASE_SCHEMA", "public")
    api_role, worker_role = os.environ["API_DB_ROLE"], os.environ["WORKER_DB_ROLE"]
    with psycopg.connect(dsn) as connection:
        for role, key in [(api_role, "API_DB_PASSWORD"), (worker_role, "WORKER_DB_PASSWORD")]:
            password = os.environ[key]
            if len(password) < 20:
                raise ValueError("runtime passwords require at least 20 characters")
            exists = connection.execute(
                "SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)
            ).fetchone()
            if not exists:
                connection.execute(
                    sql.SQL(
                        "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS PASSWORD {}"
                    ).format(sql.Identifier(role), sql.Literal(password))
                )
        connection.execute(
            sql.SQL("REVOKE CREATE ON SCHEMA {} FROM PUBLIC").format(sql.Identifier(schema))
        )
        grant_runtime(connection, schema, api_role, worker_role)
    print("Runtime grants applied; existing role passwords unchanged.")


if __name__ == "__main__":
    main()
