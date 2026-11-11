from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.core.auth import hasher
from app.core.config import settings
from app.db.models import Access, Portfolio, Pricing, User
from app.db.session import SessionLocal
from app.integrations.synthetic import atlas_feed, meridian_feed
from app.services.common import lock
from app.services.ingestion import enqueue
from app.workers.runner import tick


def seed() -> None:
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
        ]:
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(
                    email=email, role=role, password_hash=hasher.hash(settings.demo_password)
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
    print(
        "Seed complete. Synthetic identities: admin / analyst / reviewer @portfolioledger.test. Password is your private DEMO_PASSWORD. Seed does not rotate existing passwords."
    )


if __name__ == "__main__":
    seed()
