from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings


class JiraClient:
    """Small Jira REST client with Basic Authentication support."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        timeout: int = 10,
    ) -> None:
        self.base_url = (base_url or os.getenv("JIRA_BASE_URL", settings.JIRA_BASE_URL)).rstrip("/")
        self.email = email or os.getenv("JIRA_EMAIL", settings.JIRA_EMAIL) or os.getenv("JIRA_USERNAME")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN", settings.JIRA_API_TOKEN) or os.getenv("JIRA_TOKEN")
        self.timeout = timeout

        if not self.base_url:
            raise ValueError("JIRA_BASE_URL is not configured.")
        if not self.email:
            raise ValueError("JIRA_EMAIL or JIRA_USERNAME is not configured.")
        if not self.api_token:
            raise ValueError("JIRA_API_TOKEN or JIRA_TOKEN is not configured.")

    def _request(self, method: str, path: str, *, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = httpx.request(
            method=method,
            url=url,
            auth=(self.email, self.api_token),
            json=json_body,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def create_issue(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/rest/api/3/issue", json_body={"fields": fields})
