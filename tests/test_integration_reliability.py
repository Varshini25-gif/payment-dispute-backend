from __future__ import annotations

import httpx
import pytest

from app.services.jira.client import JiraClient
from app.utils.error_responses import ServiceRecoveryError, ServiceTimeoutError
from app.utils.fallback_handler import FallbackHandler, ServiceRecoveryManager
from app.utils.retry_handler import execute_with_retry


def test_execute_with_retry_succeeds_after_transient_failure() -> None:
    calls = {"count": 0}

    def flaky_operation() -> str:
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.ConnectError("temporary", request=httpx.Request("GET", "https://example.com"))
        return "ok"

    result = execute_with_retry(
        flaky_operation,
        max_attempts=3,
        should_retry=lambda exc: isinstance(exc, httpx.RequestError),
        sleep_fn=lambda _delay: None,
    )

    assert result == "ok"
    assert calls["count"] == 2


def test_fallback_handler_enters_recovery_after_threshold() -> None:
    manager = ServiceRecoveryManager(failure_threshold=2, recovery_window_seconds=120, time_fn=lambda: 10.0)
    handler = FallbackHandler(manager)

    with pytest.raises(RuntimeError):
        handler.execute(service_name="jira", primary_operation=lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(RuntimeError):
        handler.execute(service_name="jira", primary_operation=lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(ServiceRecoveryError):
        handler.execute(service_name="jira", primary_operation=lambda: {"ok": True})


def test_jira_client_maps_timeout_to_service_timeout(monkeypatch) -> None:
    def fake_request(method, url, *, auth=None, json=None, timeout=None):
        request = httpx.Request(method, url)
        raise httpx.TimeoutException("timed out", request=request)

    monkeypatch.setattr(httpx, "request", fake_request)

    client = JiraClient(base_url="https://jira.example.com", email="tester@example.com", api_token="secret")

    with pytest.raises(ServiceTimeoutError):
        client.create_issue({"project": {"key": "PAY"}, "summary": "test"})
