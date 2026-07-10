from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.utils.error_responses import ServiceRecoveryError, map_httpx_exception
from app.utils.fallback_handler import FallbackHandler, ServiceRecoveryManager
from app.utils.retry_handler import execute_with_retry


class ConfluenceClient:
    """Confluence REST client using Basic Authentication for Atlassian Cloud."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
        api_token: Optional[str] = None,
        space_key: Optional[str] = None,
        parent_page_id: Optional[str] = None,
        timeout: Optional[int] = None,
        fallback_handler: Optional[FallbackHandler] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("CONFLUENCE_BASE_URL", settings.CONFLUENCE_BASE_URL)).rstrip("/")
        self.email = email or username or os.getenv("CONFLUENCE_EMAIL", settings.CONFLUENCE_EMAIL)
        self.api_token = api_token or os.getenv("CONFLUENCE_API_TOKEN", settings.CONFLUENCE_API_TOKEN)
        self.space_key = space_key or os.getenv("CONFLUENCE_SPACE_KEY", settings.CONFLUENCE_SPACE_KEY) or "TEST"
        self.parent_page_id = parent_page_id or os.getenv(
            "CONFLUENCE_PARENT_PAGE_ID",
            settings.CONFLUENCE_PARENT_PAGE_ID,
        )
        self.timeout = timeout or settings.CONFLUENCE_TIMEOUT_SECONDS
        self.fallback_handler = fallback_handler or FallbackHandler(
            ServiceRecoveryManager(
                failure_threshold=settings.INTEGRATION_FAILURE_THRESHOLD,
                recovery_window_seconds=settings.INTEGRATION_RECOVERY_WINDOW_SECONDS,
            )
        )

        if not self.base_url:
            raise ValueError("CONFLUENCE_BASE_URL is not configured.")
        if not self.email:
            raise ValueError("CONFLUENCE_EMAIL is not configured.")
        if not self.api_token:
            raise ValueError("CONFLUENCE_API_TOKEN is not configured.")
        if not self.space_key:
            raise ValueError("CONFLUENCE_SPACE_KEY is not configured.")

    @staticmethod
    def _is_retryable_exception(exc: Exception) -> bool:
        if isinstance(exc, (httpx.TimeoutException, httpx.RequestError)):
            return True
        if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
            return exc.response.status_code in {429, 500, 502, 503, 504}
        return False

    def _request(self, method: str, path: str, *, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        service_name = "confluence"

        def _operation() -> Dict[str, Any]:
            url = f"{self.base_url}{path}"
            response = httpx.request(
                method=method,
                url=url,
                auth=(self.email, self.api_token),
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                json=json_body,
                timeout=self.timeout,
            )
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return {}

        def _with_retry() -> Dict[str, Any]:
            return execute_with_retry(
                _operation,
                max_attempts=settings.INTEGRATION_RETRY_ATTEMPTS,
                base_delay_seconds=settings.INTEGRATION_RETRY_BASE_DELAY_SECONDS,
                max_delay_seconds=settings.INTEGRATION_RETRY_MAX_DELAY_SECONDS,
                should_retry=self._is_retryable_exception,
            )

        def _fallback(exc: Exception | None) -> Dict[str, Any]:
            if exc is None:
                raise ServiceRecoveryError(service_name)
            raise map_httpx_exception(service_name, exc)

        return self.fallback_handler.execute(
            service_name=service_name,
            primary_operation=_with_retry,
            fallback_operation=_fallback,
        )

    def create_page(self, title: str, body_html: str, *, parent_page_id: Optional[str] = None) -> Dict[str, Any]:
        ancestor_id = parent_page_id or self.parent_page_id
        payload: Dict[str, Any] = {
            "type": "page",
            "title": title,
            "space": {"key": self.space_key},
            "body": {"storage": {"value": body_html, "representation": "storage"}},
        }
        if ancestor_id:
            payload["ancestors"] = [{"id": ancestor_id}]

        page = self._request("POST", "/wiki/rest/api/content", json_body=payload)
        links = page.get("_links", {})
        webui = links.get("webui", "")
        base = links.get("base", self.base_url)
        page["resolved_url"] = f"{base}{webui}" if webui else None
        return page