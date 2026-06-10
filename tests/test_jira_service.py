from types import SimpleNamespace

import httpx

from app.services.jira.client import JiraClient
from app.services.jira.issue_service import JiraIssueService


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=None, response=None)

    def json(self) -> dict:
        return self._payload


class FakeTransport:
    def __init__(self, payload: dict):
        self.payload = payload
        self.calls = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        return httpx.Response(200, request=request, json=self.payload)


def test_jira_client_uses_basic_auth_and_posts_issue(monkeypatch) -> None:
    seen = {}

    def fake_request(method, url, *, auth=None, json=None, timeout=None):
        seen["method"] = method
        seen["url"] = url
        seen["auth"] = auth
        seen["json"] = json
        seen["timeout"] = timeout
        return FakeResponse({"key": "PAY-123"})

    monkeypatch.setattr(httpx, "request", fake_request)

    client = JiraClient(base_url="https://jira.example.com", email="tester@example.com", api_token="secret")
    issue = client.create_issue({"project": {"key": "PAY"}, "summary": "Test issue"})

    assert issue == {"key": "PAY-123"}
    assert seen["method"] == "POST"
    assert seen["url"] == "https://jira.example.com/rest/api/3/issue"
    assert seen["auth"] == ("tester@example.com", "secret")
    assert seen["json"] == {"fields": {"project": {"key": "PAY"}, "summary": "Test issue"}}


def test_issue_service_builds_issue_payload_for_dispute() -> None:
    created = {}

    class FakeClient:
        def create_issue(self, fields):
            created["fields"] = fields
            return {"key": "PAY-1"}

    service = JiraIssueService(client=FakeClient())
    dispute = SimpleNamespace(
        external_id="EXT-1",
        amount=1250,
        currency="USD",
        type="chargeback",
        reason="Fraud case",
        customer_id="customer-42",
    )

    result = service.create_issue(dispute, project_key="PAY")

    assert result == {"key": "PAY-1"}
    assert created["fields"]["project"] == {"key": "PAY"}
    assert created["fields"]["summary"] == "Dispute EXT-1 - chargeback"
    assert created["fields"]["priority"] == {"name": "High"}
