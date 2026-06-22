import logging
import sys
from contextvars import ContextVar
from typing import Any, Dict

from app.core.config import settings
from app.utils.log_formatter import JsonLogFormatter


_log_context: ContextVar[Dict[str, Any]] = ContextVar("log_context", default={})


class RequestContextFilter(logging.Filter):
    """Inject request-scoped context (correlation IDs, method, path) into logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        context = _log_context.get()
        for key, value in context.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        return True


def set_request_log_context(**kwargs: Any) -> None:
    current = dict(_log_context.get())
    current.update({k: v for k, v in kwargs.items() if v is not None})
    _log_context.set(current)


def clear_request_log_context() -> None:
    _log_context.set({})


def configure_logging() -> None:
    level = logging.getLevelName(settings.LOG_LEVEL.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestContextFilter())

    if settings.LOG_JSON:
        handler.setFormatter(JsonLogFormatter())
    else:
        fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        handler.setFormatter(logging.Formatter(fmt))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # FastAPI / Uvicorn logger propagation
    logging.getLogger("uvicorn").handlers = [handler]
    logging.getLogger("uvicorn.error").handlers = [handler]
    logging.getLogger("uvicorn.access").handlers = [handler]
