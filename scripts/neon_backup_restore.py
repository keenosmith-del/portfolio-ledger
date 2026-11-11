"""Restore a private Neon dump into a NEW database; never reset/delete the source.

Requires private MIGRATION_DATABASE_URL, PGSSLROOTCERT and APP_ENV=development.
Retains the uniquely named restore database for operator review (no DROP operation).
"""

import json
import os
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import psycopg
from app.operations.neon_check import direct_neon_dsn, verify_client_tls
from backup_restore import snapshot
from psycopg import sql
from sqlalchemy.engine import make_url


def main() -> None:
    owner = os.environ["MIGRATION_DATABASE_URL"]
    source = make_url(direct_neon_dsn(owner)).set(drivername="postgresql+psycopg")
    target_name = os.environ.get("RESTORE_DATABASE") or (
        "portfolioledger_restore_"
        + datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        + uuid4().hex[:6]
    )
    with psycopg.connect(direct_neon_dsn(owner)) as preflight:
        verify_client_tls(preflight)
        if preflight.execute(
            "SELECT count(*) FROM portfolios WHERE NOT synthetic_demo"
        ).fetchone()[0]:
            raise ValueError(
                "Restore drill is limited to explicitly synthetic portfolios"
            )
    before = snapshot(source)
    with psycopg.connect(direct_neon_dsn(owner), autocommit=True) as db:
        verify_client_tls(db)
        if not re.fullmatch(r"portfolioledger_restore_[0-9a-f]+", target_name):
            raise ValueError("Unsafe isolated restore database name")
        if os.environ.get("RESTORE_DATABASE"):
            target = source.set(database=target_name).render_as_string(
                hide_password=False
            )
            with psycopg.connect(direct_neon_dsn(target)) as check:
                if check.execute(
                    "SELECT count(*) FROM pg_tables WHERE schemaname='public'"
                ).fetchone()[0]:
                    raise ValueError(
                        "Resume requires an empty isolated restore database"
                    )
        else:
            db.execute(
                sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(
                    sql.Identifier(target_name)
                )
            )
    env = dict(os.environ)
    env.update(
        PGHOST=source.host or "",
        PGPORT=str(source.port or 5432),
        PGUSER=source.username or "",
        PGPASSWORD=source.password or "",
        PGDATABASE=source.database or "",
        PGSSLMODE="verify-full",
        PGSSLROOTCERT="/etc/ssl/certs/ca-certificates.crt",
    )
    docker = ["docker", "run", "--rm", "-i"]
    for key in (
        "PGHOST",
        "PGPORT",
        "PGUSER",
        "PGPASSWORD",
        "PGDATABASE",
        "PGSSLMODE",
        "PGSSLROOTCERT",
    ):
        docker += ["-e", key]
    docker += ["postgres:18-alpine"]
    with tempfile.TemporaryDirectory(
        prefix="portfolioledger-private-neon-restore-"
    ) as folder:
        dump = Path(folder) / "synthetic.dump"
        with dump.open("wb") as output:
            os.chmod(dump, 0o600)
            result = subprocess.run(
                docker
                + [
                    "pg_dump",
                    "--format=custom",
                    "--schema=public",
                    "--no-owner",
                    "--no-acl",
                ],
                check=False,
                env=env,
                stdout=output,
                stderr=subprocess.PIPE,
            )
        if result.returncode:
            raise RuntimeError(
                "Hosted backup failed; credential-bearing diagnostics suppressed"
            )
        # A fresh PostgreSQL database already owns its public schema. Exclude
        # just that archive entry; never clean/drop a schema to make restore pass.
        with dump.open("rb") as archive:
            listing = subprocess.run(
                docker + ["pg_restore", "--list"],
                env=env,
                stdin=archive,
                capture_output=True,
                check=True,
            ).stdout.decode()
        entries = listing.splitlines()
        if sum(" SCHEMA - public " in line for line in entries) != 1:
            raise ValueError("Expected exactly one public schema archive entry")
        restore_list = Path(folder) / "restore.list"
        restore_list.write_text(
            "\n".join(line for line in entries if " SCHEMA - public " not in line)
            + "\n"
        )
        os.chmod(restore_list, 0o600)
        env["PGDATABASE"] = target_name
        restore_docker = docker[:-1] + ["-v", folder + ":/backup:ro", docker[-1]]
        result = subprocess.run(
            restore_docker
            + [
                "pg_restore",
                "--exit-on-error",
                "--no-owner",
                "--no-acl",
                "--dbname=" + target_name,
                "--use-list=/backup/restore.list",
                "/backup/synthetic.dump",
            ],
            check=False,
            env=env,
            capture_output=True,
        )
        if result.returncode:
            raise RuntimeError(
                "Isolated restore failed: "
                + result.stderr.decode(errors="replace")
                .splitlines()[0]
                .replace(source.password or "__none__", "[REDACTED]")
            )
    after = snapshot(source.set(database=target_name))
    unchanged = snapshot(source)
    if before != after or before != unchanged:
        raise RuntimeError(
            "Restored or source business identity/hash comparison failed"
        )
    print(
        json.dumps(
            {
                "verified_at": datetime.now(UTC).isoformat(),
                "source_unchanged": True,
                "exact_business_hashes_restored": True,
                "restore_database": target_name,
                "restore_database_retained": True,
                "private_dump_removed": True,
                "tables": before,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
