from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass
class IntegrationServiceError(Exception):
    """Base error used for external service integrations."""

    message: str
    service_name: str
    status_code: int = 502
    error_code: str = "integration_error"
    retryable: bool = False
    details: Optional[dict[str, Any]] = None

    def __str__(self) -> str:
        return self.message

    def to_response(self, correlation_id: Optional[str] = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "detail": self.message,
            "error_code": self.error_code,
            "service": self.service_name,
            "retryable": self.retryable,
            "correlation_id": correlation_id,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class ServiceTimeoutError(IntegrationServiceError):
    def __init__(self, service_name: str, message: str = "External service timed out.") -> None:
        super().__init__(
            message=message,
            service_name=service_name,
            status_code=504,
            error_code="service_timeout",
            retryable=True,
        )


class ServiceUnavailableError(IntegrationServiceError):
    def __init__(self, service_name: str, message: str = "External service is unavailable.") -> None:
        super().__init__(
            message=message,
            service_name=service_name,
            status_code=503,
            error_code="service_unavailable",
            retryable=True,
        )


class ServiceRecoveryError(IntegrationServiceError):
    def __init__(self, service_name: str) -> None:
        super().__init__(
            message=(
                f"{service_name.title()} service is in recovery mode after consecutive failures. "
                "Please retry shortly."
            ),
            service_name=service_name,
            status_code=503,
            error_code="service_recovery",
            retryable=True,
        )


def map_httpx_exception(service_name: str, exc: Exception) -> IntegrationServiceError:
    """Normalize low-level HTTP client errors into API-friendly integration errors."""

    if isinstance(exc, IntegrationServiceError):
        return exc

    if isinstance(exc, httpx.TimeoutException):
        return ServiceTimeoutError(service_name, message=f"{service_name.title()} request timed out.")

    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code in {429, 500, 502, 503, 504}:
            return ServiceUnavailableError(
                service_name,
                message=f"{service_name.title()} service responded with a transient error.",
            )
        return IntegrationServiceError(
            message=f"{service_name.title()} request failed.",
            service_name=service_name,
            status_code=502,
            error_code="service_request_failed",
            retryable=False,
            details={"upstream_status_code": status_code},
        )

    if isinstance(exc, httpx.RequestError):
        return ServiceUnavailableError(
            service_name,
            message=f"Could not reach {service_name.title()} service.",
        )

    return IntegrationServiceError(
        message=f"Unexpected error while contacting {service_name.title()} service.",
        service_name=service_name,
    )
