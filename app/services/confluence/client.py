from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings


class ConfluenceClient:
    """Confluence REST client using Basic Authentication for Atlassian Cloud."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        space_key: Optional[str] = None,
        parent_page_id: Optional[str] = None,
        timeout: int = 15,
    ) -> None:
        self.base_url = (base_url or os.getenv("CONFLUENCE_BASE_URL", settings.CONFLUENCE_BASE_URL)).rstrip("/")
        self.email = email or os.getenv("CONFLUENCE_EMAIL", settings.CONFLUENCE_EMAIL)
        self.api_token = api_token or os.getenv("CONFLUENCE_API_TOKEN", settings.CONFLUENCE_API_TOKEN)
        self.space_key = space_key or os.getenv("CONFLUENCE_SPACE_KEY", settings.CONFLUENCE_SPACE_KEY)
        self.parent_page_id = parent_page_id or os.getenv(
            "CONFLUENCE_PARENT_PAGE_ID",
            settings.CONFLUENCE_PARENT_PAGE_ID,
        )
        self.timeout = timeout

        if not self.base_url:
            raise ValueError("CONFLUENCE_BASE_URL is not configured.")
        if not self.email:
            raise ValueError("CONFLUENCE_EMAIL is not configured.")
        if not self.api_token:
            raise ValueError("CONFLUENCE_API_TOKEN is not configured.")
        if not self.space_key:
            raise ValueError("CONFLUENCE_SPACE_KEY is not configured.")

    def _request(self, method: str, path: str, *, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
        return response.json()

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