import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.routes.confluence import router as confluence_router
from app.api.routes.disputes import router as disputes_router
from app.api.routes.sla import router as sla_router
from app.api.routes.auth import router as auth_router
from app.core.logging import configure_logging
from app.core.config import settings
from app.core.scheduler import shutdown_scheduler, start_scheduler
from app.middleware.audit_middleware import AuditMiddleware
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.request_logger import RequestLoggerMiddleware

configure_logging()
logger = logging.getLogger("app")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Payment dispute backend service",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)

app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(AuditMiddleware)
register_exception_handlers(app)

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(disputes_router, prefix="/api")
app.include_router(sla_router, prefix="/api")
app.include_router(confluence_router, prefix="/api")


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting %s", settings.APP_NAME)
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    shutdown_scheduler()
    logger.info("Shutting down %s", settings.APP_NAME)
