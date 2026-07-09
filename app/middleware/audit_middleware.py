import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database.connection import get_engine
from app.database.models.api_request_log import APIRequestLog
from app.database.session import SessionLocal

logger = logging.getLogger("app.middleware.audit")


def _should_capture_request_body(path: str, method: str) -> bool:
    if method not in {"POST", "PUT", "PATCH"}:
        return False

    # Avoid persisting credentials or tokens from auth and token endpoints.
    sensitive_path_tokens = ("/auth", "/login", "/token", "/password")
    return not any(token in path.lower() for token in sensitive_path_tokens)


class AuditMiddleware(BaseHTTPMiddleware):
    """Persist API request traces to the database for auditing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        started = time.perf_counter()
        raw_request_body = (await request.body()).decode("utf-8", errors="replace")

        response = await call_next(request)

        duration_ms = int((time.perf_counter() - started) * 1000)
        correlation_id = getattr(request.state, "correlation_id", None) or str(uuid.uuid4())
        request_id = getattr(request.state, "request_id", None)
        actor = request.headers.get("X-Actor") or request.headers.get("X-User-ID") or "anonymous"
        client_ip = request.client.host if request.client else None

        metadata = {
            "path_params": dict(request.path_params),
            "query_params": dict(request.query_params),
        }

        entry = APIRequestLog(
            correlation_id=correlation_id,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_string=request.url.query,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
            user_agent=request.headers.get("User-Agent"),
            actor=actor,
            request_body=(
                raw_request_body[:4000]
                if raw_request_body and _should_capture_request_body(request.url.path, request.method)
                else None
            ),
            error_detail=getattr(request.state, "error_detail", None),
            metadata_json=json.dumps(metadata, default=str),
        )

        session = None
        try:
            session = SessionLocal(bind=get_engine())
            session.add(entry)
            session.commit()
        except Exception:
            if session is not None:
                session.rollback()
            logger.exception("Failed to persist API request audit log")
        finally:
            if session is not None:
                session.close()

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            logger.info(
                "Audit trace recorded",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "correlation_id": correlation_id,
                },
            )

        return response
