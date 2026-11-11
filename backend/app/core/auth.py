import hashlib
import secrets
from datetime import timedelta

from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Access, AuthSession, Portfolio, RateWindow, User, now
from app.db.session import get_db
from app.services.common import lock

hasher = PasswordHasher()
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def rate_limit(db: Session, key: str, maximum: int, seconds: int = 60) -> None:
    # Independent transaction deliberately preserves failed-login counters.
    from app.db.session import SessionLocal

    with SessionLocal.begin() as counter_db:
        counter_db.execute(
            delete(RateWindow).where(RateWindow.started_at < now() - timedelta(days=1))
        )
        counter_db.execute(delete(AuthSession).where(AuthSession.expires_at < now()))
        lock(counter_db, "rate:" + key)
        window = counter_db.get(RateWindow, key)
        if window is None:
            window = RateWindow(key=key, count=0, started_at=now())
            counter_db.add(window)
        if window.started_at + timedelta(seconds=seconds) < now():
            window.started_at = now()
            window.count = 0
        blocked = window.count >= maximum
        window.count += 1
    if blocked:
        raise HTTPException(429, "rate_limit_exceeded", headers={"Retry-After": str(seconds)})


def authenticate(request: Request, db: Session = Depends(get_db, scope="function")) -> User:
    token = request.cookies.get("ledger_session", "")
    session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == token_hash(token), AuthSession.expires_at > now()
        )
    )
    if session is None:
        raise HTTPException(401, "authentication_required")
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(401, "authentication_required")
    request.state.auth_session = session
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        same_origin = str(request.base_url).rstrip("/")
        if (
            origin
            and origin not in settings.allowed_origins
            and not (settings.app_env != "production" and origin == same_origin)
        ):
            raise HTTPException(403, "origin_not_allowed")
        if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), session.csrf):
            raise HTTPException(403, "csrf_token_required")
    return user


def authorized(
    portfolio_id: str,
    user: User = Depends(authenticate, scope="function"),
    db: Session = Depends(get_db, scope="function"),
) -> User:
    if user.email == "public-review@portfolioledger.test":
        portfolio = db.get(Portfolio, portfolio_id)
        if portfolio is None or not portfolio.synthetic_demo:
            raise HTTPException(404, "portfolio_not_found")
    if db.get(Access, (user.id, portfolio_id)) is None:
        raise HTTPException(404, "portfolio_not_found")
    return user


def writable(user: User) -> None:
    if settings.public_demo_read_only or user.role == "reviewer":
        raise HTTPException(403, "read_only_role")
