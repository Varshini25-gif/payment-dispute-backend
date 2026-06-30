import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.error_responses import IntegrationServiceError

logger = logging.getLogger("app.middleware.exception_handler")


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for API consistency."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)
        request.state.error_detail = str(exc.detail)

        logger.warning(
            "HTTP exception encountered",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": exc.status_code,
                "correlation_id": correlation_id,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "correlation_id": correlation_id,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)
        request.state.error_detail = str(exc.errors())

        logger.warning(
            "Validation exception encountered",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": 422,
                "correlation_id": correlation_id,
            },
        )

        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.errors(),
                "correlation_id": correlation_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)

        if isinstance(exc, IntegrationServiceError):
            request.state.error_detail = str(exc)
            logger.warning(
                "Integration exception encountered",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": exc.status_code,
                    "service": exc.service_name,
                    "correlation_id": correlation_id,
                },
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_response(correlation_id=correlation_id),
            )

        request.state.error_detail = str(exc)

        logger.exception(
            "Unhandled exception encountered",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "correlation_id": correlation_id,
            },
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "correlation_id": correlation_id,
            },
        )
