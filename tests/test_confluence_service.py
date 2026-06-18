from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import httpx

from app.services.confluence.client import ConfluenceClient
from app.services.confluence.html_builder import build_page_title, build_resolution_html
from app.services.confluence.publisher import ConfluencePublisher


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=None, response=None)

    def json(self) -> dict:
        return self._payload


class FakeSession:
    def __init__(self, existing=None):
        self.existing = existing
        self.added = []
        self.committed = False
        self.refreshed = []

    def scalar(self, _query):
        return self.existing

    def add(self, obj):
        self.added.append(obj)
        self.existing = obj

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed.append(obj)


def test_confluence_client_creates_page_with_basic_auth(monkeypatch) -> None:
    seen = {}

    def fake_request(method, url, *, auth=None, headers=None, json=None, timeout=None):
        seen["method"] = method
        seen["url"] = url
        seen["auth"] = auth
        seen["headers"] = headers
        seen["json"] = json
        seen["timeout"] = timeout
        return FakeResponse(
            {
                "id": "98765",
                "_links": {
                    "base": "https://acme.atlassian.net/wiki",
                    "webui": "/spaces/PAY/pages/98765",
                },
            }
        )

    monkeypatch.setattr(httpx, "request", fake_request)

    client = ConfluenceClient(
        base_url="https://acme.atlassian.net",
        email="tester@example.com",
        api_token="secret",
        space_key="PAY",
    )
    page = client.create_page("Dispute Summary", "<h1>Hello</h1>")

    assert seen["method"] == "POST"
    assert seen["url"] == "https://acme.atlassian.net/wiki/rest/api/content"
    assert seen["auth"] == ("tester@example.com", "secret")
    assert seen["json"]["space"] == {"key": "PAY"}
    assert seen["json"]["body"]["storage"]["representation"] == "storage"
    assert page["resolved_url"] == "https://acme.atlassian.net/wiki/spaces/PAY/pages/98765"


def test_html_builder_renders_dispute_fields() -> None:
    dispute = SimpleNamespace(
        external_id="EXT-123",
        status="new",
        type="chargeback",
        amount=250.50,
        currency="USD",
        customer_id="cust-77",
        reason="Card not present fraud.",
    )

    title = build_page_title(dispute)
    html = build_resolution_html(dispute, published_at=datetime(2026, 6, 18, tzinfo=timezone.utc))

    assert title == "Dispute Case Summary - EXT-123"
    assert "Payment Dispute Case Summary" in html
    assert "EXT-123" in html
    assert "cust-77" in html
    assert "Card not present fraud." in html


def test_confluence_publisher_tracks_success_status() -> None:
    class FakeClient:
        def create_page(self, title, body_html, *, parent_page_id=None):
            assert "Dispute Case Summary - EXT-555" in title
            assert "Payment Dispute Case Summary" in body_html
            assert parent_page_id == "10001"
            return {
                "id": "10002",
                "resolved_url": "https://acme.atlassian.net/wiki/spaces/PAY/pages/10002",
            }

    dispute = SimpleNamespace(
        id="e5f8cc29-53cb-4c58-b129-0c5fa1ca9c57",
        external_id="EXT-555",
        status="assigned",
        type="fraud",
        amount=1500,
        currency="USD",
        customer_id="cust-9",
        reason="Issuer confirmed fraud.",
    )
    db = FakeSession(existing=None)
    publisher = ConfluencePublisher(client=FakeClient())

    post = publisher.publish_dispute_summary(dispute, db=db, parent_page_id="10001")

    assert db.committed is True
    assert post.publish_status == "published"
    assert post.page_id == "10002"
    assert post.publish_attempts == 1
    assert post.failure_reason is None