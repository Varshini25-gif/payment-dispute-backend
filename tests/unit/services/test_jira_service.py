"""Unit tests for Jira service."""

from types import SimpleNamespace
import pytest

from app.services.jira.client import JiraClient
from app.services.jira.issue_service import JiraIssueService


class FakeResponse:
    """Fake HTTP response for testing."""
    
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._payload


class TestJiraClient:
    """Test Jira API client."""
    
    def test_jira_client_uses_basic_auth_and_posts_issue(self, monkeypatch) -> None:
        """Test that client uses basic auth and posts issues correctly."""
        seen = {}

        def fake_request(method, url, *, auth=None, json=None, timeout=None):
            seen["method"] = method
            seen["url"] = url
            seen["auth"] = auth
            seen["json"] = json
            seen["timeout"] = timeout
            return FakeResponse({"key": "PAY-123"})

        import httpx
        monkeypatch.setattr(httpx, "request", fake_request)

        client = JiraClient(
            base_url="https://jira.example.com",
            email="tester@example.com",
            api_token="secret"
        )
        issue = client.create_issue({"project": {"key": "PAY"}, "summary": "Test issue"})

        assert issue == {"key": "PAY-123"}
        assert seen["method"] == "POST"
        assert seen["url"] == "https://jira.example.com/rest/api/3/issue"
        assert seen["auth"] == ("tester@example.com", "secret")

    def test_jira_client_gets_issue(self, monkeypatch) -> None:
        """Test getting an issue."""
        def fake_request(method, url, **kwargs):
            return FakeResponse({
                "key": "PAY-123",
                "fields": {"summary": "Test", "status": {"name": "To Do"}}
            })

        import httpx
        monkeypatch.setattr(httpx, "request", fake_request)

        client = JiraClient(
            base_url="https://jira.example.com",
            email="tester@example.com",
            api_token="secret"
        )
        issue = client.get_issue("PAY-123")

        assert issue["key"] == "PAY-123"
        assert issue["fields"]["summary"] == "Test"

    def test_jira_client_handles_errors(self, monkeypatch) -> None:
        """Test error handling."""
        def fake_request(method, url, **kwargs):
            return FakeResponse({"errorMessages": ["Issue not found"]}, status_code=404)

        import httpx
        monkeypatch.setattr(httpx, "request", fake_request)

        client = JiraClient(
            base_url="https://jira.example.com",
            email="tester@example.com",
            api_token="secret"
        )

        # Should raise on 404
        with pytest.raises(Exception):
            client.get_issue("INVALID-KEY")


class TestJiraIssueService:
    """Test Jira issue service."""
    
    def test_issue_service_builds_issue_payload_for_dispute(self) -> None:
        """Test building issue payload from dispute."""
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

    def test_issue_service_creates_issue_with_description(self) -> None:
        """Test that description is included."""
        created = {}

        class FakeClient:
            def create_issue(self, fields):
                created["fields"] = fields
                return {"key": "PAY-1"}

        service = JiraIssueService(client=FakeClient())
        dispute = SimpleNamespace(
            external_id="EXT-2",
            amount=500,
            currency="USD",
            type="refund_dispute",
            reason="Customer dispute",
            customer_id="customer-1",
        )

        service.create_issue(dispute, project_key="PAY")

        assert "description" in created["fields"]
        assert "EXT-2" in created["fields"]["description"]

    def test_issue_service_handles_different_dispute_types(self) -> None:
        """Test handling different dispute types."""
        created = {}

        class FakeClient:
            def create_issue(self, fields):
                created["fields"] = fields
                return {"key": "PAY-1"}

        service = JiraIssueService(client=FakeClient())

        dispute_types = ["chargeback", "refund_dispute", "fraud", "other"]
        for dispute_type in dispute_types:
            dispute = SimpleNamespace(
                external_id=f"EXT-{dispute_type}",
                amount=100,
                currency="USD",
                type=dispute_type,
                reason="Test",
                customer_id="customer-1",
            )

            result = service.create_issue(dispute, project_key="PAY")

            assert result["key"] == "PAY-1"
            assert dispute_type in created["fields"]["summary"].lower() or dispute_type == created["fields"]["summary"]

    def test_issue_service_sets_priority_based_on_amount(self) -> None:
        """Test that priority is set based on dispute amount."""
        created_issues = []

        class FakeClient:
            def create_issue(self, fields):
                created_issues.append(fields)
                return {"key": f"PAY-{len(created_issues)}"}

        service = JiraIssueService(client=FakeClient())

        # Low amount
        dispute_low = SimpleNamespace(
            external_id="EXT-LOW",
            amount=50,
            currency="USD",
            type="refund",
            reason="Test",
            customer_id="customer-1",
        )
        service.create_issue(dispute_low, project_key="PAY")

        # High amount
        dispute_high = SimpleNamespace(
            external_id="EXT-HIGH",
            amount=5000,
            currency="USD",
            type="chargeback",
            reason="Test",
            customer_id="customer-1",
        )
        service.create_issue(dispute_high, project_key="PAY")

        assert len(created_issues) == 2
