from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.scheduler import scheduler
from app.database.connection import get_engine

router = APIRouter()


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _check_database() -> tuple[str, str | None]:
    if not settings.HEALTH_DB_CHECK_ENABLED:
        return "skipped", None

    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok", None
    except Exception as exc:
        return "error", str(exc)


def _check_scheduler() -> dict[str, int | bool]:
    jobs = scheduler.get_jobs()
    return {
        "running": scheduler.running,
        "job_count": len(jobs),
    }


@router.get("/health", tags=["Health"], summary="Health check")
async def health_check() -> dict[str, object]:
    db_status, db_error = _check_database()
    scheduler_status = _check_scheduler()

    overall_status = "ok"
    if db_status == "error":
        overall_status = "degraded"

    response: dict[str, object] = {
        "status": overall_status,
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": _utc_timestamp(),
        "checks": {
            "database": {
                "status": db_status,
            },
            "scheduler": scheduler_status,
        },
    }

    if db_error:
        response["checks"]["database"]["error"] = db_error

    return response


@router.get("/health/live", tags=["Health"], summary="Liveness probe")
async def health_live() -> dict[str, object]:
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "timestamp": _utc_timestamp(),
    }


@router.get("/health/ready", tags=["Health"], summary="Readiness probe")
async def health_ready() -> dict[str, object]:
    db_status, db_error = _check_database()
    scheduler_status = _check_scheduler()

    ready = db_status in {"ok", "skipped"}

    return {
        "status": "ready" if ready else "not_ready",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": _utc_timestamp(),
        "checks": {
            "database": {
                "status": db_status,
            },
            "scheduler": scheduler_status,
        },
    }
