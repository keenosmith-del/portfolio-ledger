import secrets
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.core.auth import hasher
from app.core.config import settings
from app.db.models import Access, IntegrationSource, Portfolio, Preview, Pricing, User, now
from app.db.session import SessionLocal
from app.integrations.synthetic import atlas_feed, meridian_feed
from app.services.common import audit, lock
from app.services.ingestion import enqueue, process
from app.workers.runner import tick


def seed() -> None:
    if not settings.seed_synthetic_demo:
        raise SystemExit("Explicit SEED_SYNTHETIC_DEMO=true is required")
    if len(settings.demo_password) < 12:
        raise SystemExit(
            "Set DEMO_PASSWORD (at least 12 characters) in your private .env before seeding"
        )
    with SessionLocal.begin() as db:
        lock(db, "seed")
        users: list[User] = []
        for email, role in [
            ("admin@portfolioledger.test", "admin"),
            ("analyst@portfolioledger.test", "analyst"),
            ("reviewer@portfolioledger.test", "reviewer"),
            ("public-review@portfolioledger.test", "reviewer"),
        ]:
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(
                    email=email,
                    role=role,
                    password_hash=hasher.hash(
                        secrets.token_urlsafe(32)
                        if email.startswith("public-review@")
                        else settings.demo_password
                    ),
                )
                db.add(user)
                db.flush()
            users.append(user)
        for name, adapter, content in [
            ("Cedarstone Living", "atlaspm", atlas_feed()),
            ("Harbourlight Estates", "meridianrent", meridian_feed()),
        ]:
            portfolio = db.scalar(select(Portfolio).where(Portfolio.name == name))
            if portfolio is None:
                portfolio = Portfolio(name=name, adapter=adapter)
                db.add(portfolio)
                db.flush()
                db.add(
                    Pricing(
                        portfolio_id=portfolio.id,
                        version=1,
                        monthly_fee=Decimal("85.00"),
                        effective_from=date(2026, 1, 1),
                    )
                )
            portfolio.synthetic_demo = True
            source_key = adapter + "-demo"
            source = db.get(IntegrationSource, (portfolio.id, source_key))
            if source is None:
                db.add(
                    IntegrationSource(
                        portfolio_id=portfolio.id,
                        source_key=source_key,
                        adapter=adapter,
                        upstream_account=source_key,
                    )
                )
            else:
                source.enabled = True
            db.flush()
            for user in users:
                if user.role == "analyst" and adapter != "atlaspm":
                    continue
                if db.get(Access, (user.id, portfolio.id)) is None:
                    db.add(Access(user_id=user.id, portfolio_id=portfolio.id))
            enqueue(
                db,
                portfolio.id,
                adapter,
                adapter + "-demo",
                "seed-v1",
                "snapshot.csv" if adapter == "atlaspm" else "events.json",
                content,
                users[0].id,
                "seed-v1",
            )
    while tick():
        pass
    # Persist a real rolled-back attempt and recovery for reviewer diagnostics.
    with SessionLocal.begin() as db:
        cedar = db.scalar(select(Portfolio).where(Portfolio.adapter == "atlaspm"))
        admin = db.scalar(select(User).where(User.email == "admin@portfolioledger.test"))
        assert cedar and admin
        recovery, _ = enqueue(
            db,
            cedar.id,
            "atlaspm",
            "atlaspm-demo",
            "seed-recovery-v1",
            "recovery.csv",
            atlas_feed(),
            admin.id,
            "seed-recovery-v1",
        )
        should_fail = recovery.attempts == 0 and recovery.status == "queued"
        if should_fail:
            recovery.status = "processing"
            recovery.attempts = 1
            recovery.lease_until = now()
        recovery_id = recovery.id
    if should_fail:
        try:
            with SessionLocal.begin() as db:
                process(db, recovery_id, fail_after=4)
        except RuntimeError as exc:
            if str(exc) != "deterministic_crash":
                raise
            with SessionLocal.begin() as db:
                audit(
                    db,
                    cedar.id,
                    admin.id,
                    "import.recovery_demonstrated",
                    recovery_id,
                    "seed-recovery-v1",
                    {"injected_failure_after_row": 4, "attempt_rolled_back": True},
                )
    while tick():
        pass
    from app.services.finance import preview, reconcile

    with SessionLocal.begin() as db:
        for portfolio in db.scalars(select(Portfolio).where(Portfolio.synthetic_demo.is_(True))):
            if db.scalar(select(Preview.id).where(Preview.portfolio_id == portfolio.id).limit(1)):
                continue
            cutoff = now()
            reconcile(db, portfolio.id, "2026-11", cutoff, admin.id, "seed-reviewer")
            preview(db, portfolio.id, "2026-11", cutoff, admin.id, "seed-reviewer")
    print(
        "Seed complete. Synthetic identities: admin / analyst / reviewer @portfolioledger.test. Password is your private DEMO_PASSWORD. Seed does not rotate existing passwords."
    )


if __name__ == "__main__":
    seed()
