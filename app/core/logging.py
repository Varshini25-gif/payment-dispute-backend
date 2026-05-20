import logging
import sys
from app.core.config import settings


def configure_logging() -> None:
    level = logging.getLevelName(settings.LOG_LEVEL.upper())
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # FastAPI / Uvicorn logger propagation
    logging.getLogger("uvicorn").handlers = [handler]
    logging.getLogger("uvicorn.error").handlers = [handler]
    logging.getLogger("uvicorn.access").handlers = [handler]
