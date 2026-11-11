from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from alembic import command


@pytest.mark.parametrize("factory", ["b002"], indirect=True)
def test_registry_upgrade_retains_historical_receipt(factory: sessionmaker[Session]) -> None:
    ids = {name: str(uuid4()) for name in ("user", "portfolio", "job")}
    with factory.begin() as db:
        db.execute(
            text(
                "INSERT INTO users (id,created_at,email,password_hash,role) VALUES (:user,CURRENT_TIMESTAMP,'migration@test.invalid','synthetic-unused','admin')"
            ),
            ids,
        )
        db.execute(
            text(
                "INSERT INTO portfolios (id,created_at,name,adapter) VALUES (:portfolio,CURRENT_TIMESTAMP,'Migration synthetic','atlaspm')"
            ),
            ids,
        )
        db.execute(
            text(
                "INSERT INTO import_jobs (id,created_at,portfolio_id,adapter,source_key,idempotency_key,checksum,filename,payload,actor_id,correlation_id,status,attempts,accepted,duplicates,quarantined) VALUES (:job,CURRENT_TIMESTAMP,:portfolio,'atlaspm','historical-source','historical-key','checksum','snapshot.csv','[]',:user,'migration','completed',1,0,0,0)"
            ),
            ids,
        )
        before = dict(
            db.execute(text("SELECT * FROM import_jobs WHERE id=:job"), ids).one()._mapping
        )
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    with factory.kw["bind"].begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    with factory() as db:
        assert (
            dict(db.execute(text("SELECT * FROM import_jobs WHERE id=:job"), ids).one()._mapping)
            == before
        )
        registry = db.execute(
            text(
                "SELECT source_key,adapter,enabled FROM integration_sources WHERE portfolio_id=:portfolio"
            ),
            ids,
        ).one()
        assert tuple(registry) == ("historical-source", "atlaspm", False)
