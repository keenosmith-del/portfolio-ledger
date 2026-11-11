import json
import logging
import signal
import threading
import time

from sqlalchemy import select

from app.db.models import ImportJob, now
from app.db.session import SessionLocal
from app.services.ingestion import MAX_ATTEMPTS, claim, process

stop = threading.Event()
logger = logging.getLogger("portfolioledger.worker")


def tick() -> bool:
    with SessionLocal.begin() as db:
        job_id = claim(db)
    if job_id is None:
        return False
    started = time.monotonic()
    try:
        with SessionLocal.begin() as db:
            process(db, job_id)
        logger.info(
            json.dumps(
                {
                    "event": "import_processed",
                    "job_id": job_id,
                    "duration_ms": round((time.monotonic() - started) * 1000),
                }
            )
        )
    except Exception:
        logger.error(json.dumps({"event": "import_attempt_failed", "job_id": job_id}))
        with SessionLocal.begin() as db:
            job = db.scalar(select(ImportJob).where(ImportJob.id == job_id).with_for_update())
            if job:
                job.error = "processing_error_retryable"
                job.lease_until = now()
                if job.attempts >= MAX_ATTEMPTS:
                    job.status = "failed"
                    job.completed_at = now()
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    while not stop.is_set():
        if not tick():
            stop.wait(1)


if __name__ == "__main__":
    main()
