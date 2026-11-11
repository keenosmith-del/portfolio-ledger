import json
import logging
import re
import secrets
import time
from datetime import timedelta
from typing import Any
from uuid import uuid4

from argon2.exceptions import VerificationError
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.auth import (
    DUMMY_HASH,
    authenticate,
    authorized,
    hasher,
    rate_limit,
    token_hash,
    writable,
)
from app.core.config import settings
from app.db.models import (
    Access,
    AuditEvent,
    AuthSession,
    Base,
    ExceptionRecord,
    ImportJob,
    LedgerEntry,
    Portfolio,
    PortfolioEntity,
    Preview,
    PreviewLine,
    Pricing,
    RawRecord,
    Reconciliation,
    User,
    now,
)
from app.db.session import get_db
from app.integrations.adapters import MAX_BYTES, FeedError
from app.schemas.api import Login, ReviewRequest, RunRequest
from app.services.common import audit, lock
from app.services.finance import export_preview, lease_versions, preview, reconcile
from app.services.ingestion import enqueue

app = FastAPI(
    title="PortfolioLedger",
    version="0.1.0",
    description="Synthetic property-finance operations. No real invoicing, payments or insurance integration.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key", "X-Request-ID"],
)
logger = logging.getLogger("portfolioledger.api")
logging.basicConfig(level=logging.INFO, format="%(message)s")


def obj(value: Base, exclude: set[str] | None = None) -> dict[str, Any]:
    hidden = exclude or set()
    return {
        column.key: getattr(value, column.key)
        for column in inspect(type(value)).columns
        if column.key not in hidden
    }


def paged(
    db: Session, model: type[PortfolioEntity], portfolio: str, offset: int, limit: int
) -> dict[str, Any]:
    statement = select(model).where(model.portfolio_id == portfolio)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.scalars(
        statement.order_by(model.created_at.desc(), model.id).offset(offset).limit(limit)
    )
    return {
        "items": [obj(row, {"payload"}) for row in rows],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


def scoped(db: Session, model: type[PortfolioEntity], portfolio: str, resource_id: str) -> Any:
    value = db.scalar(select(model).where(model.portfolio_id == portfolio, model.id == resource_id))
    if value is None:
        raise HTTPException(404, "resource_not_found")
    return value


def corr(request: Request) -> str:
    return str(request.state.correlation_id)


@app.middleware("http")
async def request_context(request: Request, call_next: Any) -> Response:
    supplied = request.headers.get("x-request-id", "")
    request.state.correlation_id = (
        supplied if re.fullmatch(r"[A-Za-z0-9_-]{1,80}", supplied) else str(uuid4())
    )
    started = time.monotonic()
    try:
        if int(request.headers.get("content-length", "0")) > MAX_BYTES + 65536:
            return JSONResponse(
                {"error": {"code": "request_too_large", "request_id": corr(request)}},
                status_code=413,
            )
    except ValueError:
        return JSONResponse({"error": {"code": "invalid_content_length"}}, status_code=400)
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = corr(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "same-origin"
    logger.info(
        json.dumps(
            {
                "event": "http_request",
                "request_id": corr(request),
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.monotonic() - started) * 1000),
            }
        )
    )
    return response


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        {"error": {"code": exc.detail, "request_id": corr(request)}},
        status_code=exc.status_code,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        {
            "error": {
                "code": "schema_validation_failed",
                "fields": [".".join(str(x) for x in error["loc"]) for error in exc.errors()],
                "request_id": corr(request),
            }
        },
        status_code=422,
    )


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error(
        json.dumps(
            {"event": "database_error", "request_id": corr(request), "type": type(exc).__name__}
        )
    )
    return JSONResponse(
        {"error": {"code": "database_operation_failed", "request_id": corr(request)}},
        status_code=503,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    version = db.scalar(text("SELECT version_num FROM alembic_version"))
    if version != "b001" or (settings.app_env == "production" and not settings.cookie_secure):
        raise HTTPException(503, "configuration_or_migration_not_ready")
    return {"status": "ready", "schema": str(version)}


@app.post("/api/auth/login")
def login(
    data: Login, request: Request, response: Response, db: Session = Depends(get_db)
) -> dict[str, Any]:
    origin = request.headers.get("origin")
    if origin and origin not in [*settings.allowed_origins, str(request.base_url).rstrip("/")]:
        raise HTTPException(403, "origin_not_allowed")
    address = request.client.host if request.client else "unknown"
    rate_limit(db, "login:" + token_hash(address), 10, 60)
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    try:
        hasher.verify(user.password_hash if user else DUMMY_HASH, data.password)
    except VerificationError as exc:
        raise HTTPException(401, "invalid_credentials") from exc
    if user is None:
        raise HTTPException(401, "invalid_credentials")
    old = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == token_hash(request.cookies.get("ledger_session", ""))
        )
    )
    if old:
        db.delete(old)
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.add(
        AuthSession(
            token_hash=token_hash(token),
            csrf=csrf,
            user_id=user.id,
            expires_at=now() + timedelta(hours=8),
        )
    )
    response.set_cookie(
        "ledger_session",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=28800,
        path="/",
    )
    return {"email": user.email, "role": user.role, "csrf": csrf}


@app.get("/api/auth/me")
def me(request: Request, user: User = Depends(authenticate)) -> dict[str, str]:
    return {"email": user.email, "role": user.role, "csrf": request.state.auth_session.csrf}


@app.post("/api/auth/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    user: User = Depends(authenticate),
    db: Session = Depends(get_db),
) -> None:
    db.delete(request.state.auth_session)
    response.delete_cookie("ledger_session", path="/")


@app.get("/api/portfolios")
def portfolios(
    user: User = Depends(authenticate), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    return [
        obj(row)
        for row in db.scalars(
            select(Portfolio)
            .join(Access, Access.portfolio_id == Portfolio.id)
            .where(Access.user_id == user.id)
            .order_by(Portfolio.name)
        )
    ]


@app.get("/api/portfolios/{portfolio_id}/overview")
def overview(
    portfolio_id: str, user: User = Depends(authorized), db: Session = Depends(get_db)
) -> dict[str, Any]:
    jobs = list(db.scalars(select(ImportJob).where(ImportJob.portfolio_id == portfolio_id)))
    versions = lease_versions(db, portfolio_id, now())
    last_sync = max(
        (
            job.completed_at
            for job in jobs
            if job.completed_at and job.status in {"completed", "partially_completed"}
        ),
        default=None,
    )
    return {
        "leases": len(versions),
        "active_leases": sum(v.status == "active" for _, v in versions),
        "balance": str(
            db.scalar(
                select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
                    LedgerEntry.portfolio_id == portfolio_id
                )
            )
        ),
        "open_exceptions": db.scalar(
            select(func.count())
            .select_from(ExceptionRecord)
            .where(
                ExceptionRecord.portfolio_id == portfolio_id,
                ExceptionRecord.status.in_(["open", "investigating"]),
            )
        ),
        "pending_jobs": sum(job.status in {"queued", "processing"} for job in jobs),
        "failed_jobs": sum(job.status == "failed" for job in jobs),
        "processed_rows": sum(job.accepted for job in jobs),
        "quarantined_rows": sum(job.quarantined for job in jobs),
        "last_sync": last_sync,
        "source_stale": last_sync is None or last_sync < now() - timedelta(hours=24),
        "recent_jobs": [
            obj(job, {"payload"})
            for job in sorted(jobs, key=lambda j: j.created_at, reverse=True)[:5]
        ],
        "latest_preview": (
            obj(value)
            if (
                value := db.scalar(
                    select(Preview)
                    .where(Preview.portfolio_id == portfolio_id)
                    .order_by(Preview.created_at.desc())
                    .limit(1)
                )
            )
            else None
        ),
    }


@app.get("/api/portfolios/{portfolio_id}/leases")
def leases(
    portfolio_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    q: str = Query("", max_length=100),
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = [
        {
            **obj(lease),
            **{
                key: value for key, value in obj(version).items() if key not in {"id", "created_at"}
            },
            "version_id": version.id,
        }
        for lease, version in lease_versions(db, portfolio_id, now())
        if q.lower() in lease.external_id.lower()
    ]
    return {
        "items": rows[offset : offset + limit],
        "total": len(rows),
        "offset": offset,
        "limit": limit,
    }


@app.get("/api/portfolios/{portfolio_id}/ledger")
def ledger(
    portfolio_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return paged(db, LedgerEntry, portfolio_id, offset, limit)


@app.get("/api/portfolios/{portfolio_id}/sources/{raw_id}")
def source(
    portfolio_id: str, raw_id: str, user: User = Depends(authorized), db: Session = Depends(get_db)
) -> dict[str, Any]:
    return obj(scoped(db, RawRecord, portfolio_id, raw_id))


@app.post("/api/portfolios/{portfolio_id}/imports", status_code=202)
async def import_file(
    portfolio_id: str,
    request: Request,
    file: UploadFile = File(),
    adapter: str = Form(max_length=30),
    source_key: str = Form(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$"),
    idempotency_key: str = Header(min_length=1, max_length=120),
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    writable(user)
    rate_limit(db, "write:" + user.id, 60)
    portfolio = db.get(Portfolio, portfolio_id)
    if portfolio is None or adapter != portfolio.adapter:
        raise HTTPException(422, "adapter_not_configured_for_portfolio")
    if file.content_type not in {
        "text/csv",
        "application/json",
        "application/octet-stream",
        "application/vnd.ms-excel",
    }:
        raise HTTPException(422, "unsupported_mime_type")
    content = await file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "file_too_large")
    try:
        job, duplicate = enqueue(
            db,
            portfolio_id,
            adapter,
            source_key,
            idempotency_key,
            (file.filename or "")[:150],
            content,
            user.id,
            corr(request),
        )
    except FeedError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {**obj(job, {"payload"}), "duplicate_request": duplicate}


@app.get("/api/portfolios/{portfolio_id}/imports")
def imports(
    portfolio_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return paged(db, ImportJob, portfolio_id, offset, limit)


@app.get("/api/portfolios/{portfolio_id}/imports/{job_id}")
def import_detail(
    portfolio_id: str,
    job_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    job = scoped(db, ImportJob, portfolio_id, job_id)
    rows = list(
        db.scalars(
            select(RawRecord)
            .where(RawRecord.portfolio_id == portfolio_id, RawRecord.job_id == job_id)
            .order_by(RawRecord.row_number)
            .offset(offset)
            .limit(limit)
        )
    )
    return {
        "job": obj(job, {"payload"}),
        "rows": [obj(row) for row in rows],
        "offset": offset,
        "limit": limit,
    }


@app.post("/api/portfolios/{portfolio_id}/imports/{job_id}/replay", status_code=202)
def replay(
    portfolio_id: str,
    job_id: str,
    request: Request,
    idempotency_key: str = Header(min_length=1, max_length=120),
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    writable(user)
    rate_limit(db, "write:" + user.id, 60)
    source_job = scoped(db, ImportJob, portfolio_id, job_id)
    lock(db, "enqueue:" + portfolio_id + ":" + idempotency_key)
    old = db.scalar(
        select(ImportJob).where(
            ImportJob.portfolio_id == portfolio_id, ImportJob.idempotency_key == idempotency_key
        )
    )
    if old:
        if (
            old.checksum != source_job.checksum
            or old.source_key != source_job.source_key
            or old.adapter != source_job.adapter
        ):
            raise HTTPException(409, "idempotency_payload_conflict")
        return obj(old, {"payload"})
    job = ImportJob(
        portfolio_id=portfolio_id,
        adapter=source_job.adapter,
        source_key=source_job.source_key,
        idempotency_key=idempotency_key,
        checksum=source_job.checksum,
        filename=source_job.filename,
        payload=source_job.payload,
        actor_id=user.id,
        correlation_id=corr(request),
    )
    db.add(job)
    db.flush()
    audit(
        db,
        portfolio_id,
        user.id,
        "import.replayed",
        job.id,
        corr(request),
        {"original_job": job_id},
    )
    return obj(job, {"payload"})


@app.post("/api/portfolios/{portfolio_id}/reconciliations")
def run_reconciliation(
    portfolio_id: str,
    data: RunRequest,
    request: Request,
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    writable(user)
    rate_limit(db, "write:" + user.id, 60)
    return obj(reconcile(db, portfolio_id, data.month, data.cutoff, user.id, corr(request)))


@app.get("/api/portfolios/{portfolio_id}/reconciliations/{run_id}")
def reconciliation(
    portfolio_id: str, run_id: str, user: User = Depends(authorized), db: Session = Depends(get_db)
) -> dict[str, Any]:
    return obj(scoped(db, Reconciliation, portfolio_id, run_id))


@app.get("/api/portfolios/{portfolio_id}/exceptions")
def exceptions(
    portfolio_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    status: str | None = None,
    severity: str | None = None,
    reason: str | None = None,
    month: str | None = None,
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    statement = select(ExceptionRecord).where(ExceptionRecord.portfolio_id == portfolio_id)
    if status:
        statement = statement.where(ExceptionRecord.status == status)
    if severity:
        statement = statement.where(ExceptionRecord.severity == severity)
    if reason:
        statement = statement.where(ExceptionRecord.reason == reason)
    if month:
        statement = statement.join(
            Reconciliation, Reconciliation.id == ExceptionRecord.run_id
        ).where(Reconciliation.month == month)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    return {
        "items": [
            obj(row)
            for row in db.scalars(
                statement.order_by(ExceptionRecord.created_at.desc(), ExceptionRecord.id)
                .offset(offset)
                .limit(limit)
            )
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@app.post("/api/portfolios/{portfolio_id}/exceptions/{exception_id}/resolve")
def resolve(
    portfolio_id: str,
    exception_id: str,
    data: ReviewRequest,
    request: Request,
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    writable(user)
    record = db.scalar(
        select(ExceptionRecord)
        .where(ExceptionRecord.portfolio_id == portfolio_id, ExceptionRecord.id == exception_id)
        .with_for_update()
    )
    if record is None:
        raise HTTPException(404, "resource_not_found")
    if record.status in {"resolved", "dismissed"}:
        raise HTTPException(409, "exception_already_closed")
    old = record.status
    record.status = data.status
    audit(
        db,
        portfolio_id,
        user.id,
        "exception." + data.status,
        record.id,
        corr(request),
        {
            "prior_status": old,
            "new_status": data.status,
            "rationale": data.rationale,
            "run_id": record.run_id,
        },
    )
    return obj(record)


@app.get("/api/portfolios/{portfolio_id}/pricing")
def pricing(
    portfolio_id: str, user: User = Depends(authorized), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    return [
        obj(row)
        for row in db.scalars(
            select(Pricing)
            .where(Pricing.portfolio_id == portfolio_id)
            .order_by(Pricing.version.desc())
        )
    ]


@app.post("/api/portfolios/{portfolio_id}/billing-previews")
def create_preview(
    portfolio_id: str,
    data: RunRequest,
    request: Request,
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    writable(user)
    rate_limit(db, "write:" + user.id, 60)
    return obj(preview(db, portfolio_id, data.month, data.cutoff, user.id, corr(request)))


@app.get("/api/portfolios/{portfolio_id}/billing-previews")
def previews(
    portfolio_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return paged(db, Preview, portfolio_id, offset, limit)


@app.get("/api/portfolios/{portfolio_id}/billing-previews/{preview_id}")
def preview_detail(
    portfolio_id: str,
    preview_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    result = scoped(db, Preview, portfolio_id, preview_id)
    statement = select(PreviewLine).where(
        PreviewLine.portfolio_id == portfolio_id, PreviewLine.preview_id == preview_id
    )
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    return {
        "preview": obj(result),
        "lines": [
            obj(row)
            for row in db.scalars(
                statement.order_by(PreviewLine.external_id).offset(offset).limit(limit)
            )
        ],
        "total": total,
    }


@app.get("/api/portfolios/{portfolio_id}/billing-previews/{preview_id}/export.csv")
def export(
    portfolio_id: str,
    preview_id: str,
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> Response:
    result = scoped(db, Preview, portfolio_id, preview_id)
    lines = list(
        db.scalars(
            select(PreviewLine)
            .where(PreviewLine.portfolio_id == portfolio_id, PreviewLine.preview_id == preview_id)
            .order_by(PreviewLine.external_id)
        )
    )
    return Response(
        export_preview(result, lines),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="portfolioledger-{result.month}.csv"'
        },
    )


@app.get("/api/portfolios/{portfolio_id}/audit")
def audit_events(
    portfolio_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    user: User = Depends(authorized),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return paged(db, AuditEvent, portfolio_id, offset, limit)
