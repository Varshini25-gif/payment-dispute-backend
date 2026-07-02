"""Mock objects and fixtures for testing."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock


class FakeSession:
    """Fake database session for testing."""
    
    def __init__(self):
        self.added: List[Any] = []
        self.committed = False
        self.refreshed: List[Any] = []
        self.deleted: List[Any] = []
        self.queries: List[str] = []
    
    def add(self, obj: Any) -> None:
        self.added.append(obj)
    
    def delete(self, obj: Any) -> None:
        self.deleted.append(obj)
    
    def commit(self) -> None:
        self.committed = True
    
    def refresh(self, obj: Any) -> None:
        self.refreshed.append(obj)
    
    def rollback(self) -> None:
        self.added.clear()
        self.deleted.clear()
        self.committed = False
    
    def close(self) -> None:
        pass
    
    def query(self, model):
        """Mock query method."""
        self.queries.append(str(model))
        return MagicMock()


class FakeResponse:
    """Fake HTTP response for testing."""
    
    def __init__(self, payload: Dict[str, Any], status_code: int = 200, headers: Optional[Dict] = None):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}
        self.text = str(payload)
    
    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")
    
    def json(self) -> Dict[str, Any]:
        return self._payload


class FakeJiraClient:
    """Fake Jira client for testing."""
    
    def __init__(self, default_response: Optional[Dict] = None):
        self.calls: List[Dict[str, Any]] = []
        self.default_response = default_response or {"key": "TEST-1"}
    
    def create_issue(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append({"method": "create_issue", "fields": fields})
        return self.default_response
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        self.calls.append({"method": "get_issue", "key": issue_key})
        return self.default_response
    
    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append({"method": "update_issue", "key": issue_key, "fields": fields})
        return {"key": issue_key}
    
    def transition_issue(self, issue_key: str, transition_id: str, fields: Optional[Dict] = None) -> None:
        self.calls.append({"method": "transition_issue", "key": issue_key, "transition_id": transition_id})


class FakeConfluenceClient:
    """Fake Confluence client for testing."""
    
    def __init__(self, default_response: Optional[Dict] = None):
        self.calls: List[Dict[str, Any]] = []
        self.default_response = default_response or {"id": "confluence-1", "type": "page"}
    
    def create_page(self, space: str, title: str, body: str) -> Dict[str, Any]:
        self.calls.append({"method": "create_page", "space": space, "title": title})
        return self.default_response
    
    def update_page(self, page_id: str, title: str, body: str, version: int) -> Dict[str, Any]:
        self.calls.append({"method": "update_page", "page_id": page_id, "version": version})
        return self.default_response
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        self.calls.append({"method": "get_page", "page_id": page_id})
        return self.default_response


class FakeDispute:
    """Fake dispute object for testing."""
    
    def __init__(
        self,
        id: str = "dispute-123",
        external_id: str = "EXT-001",
        amount: float = 100.0,
        currency: str = "USD",
        type: str = "chargeback",
        status: str = "pending",
        customer_id: str = "customer-1",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.external_id = external_id
        self.amount = amount
        self.currency = currency
        self.type = type
        self.status = status
        self.customer_id = customer_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.description = f"Test dispute: {type}"
        self.reason = "Test reason"


class FakeJiraIssue:
    """Fake Jira issue object."""
    
    def __init__(
        self,
        key: str = "TEST-1",
        summary: str = "Test Issue",
        status: str = "To Do",
        created: Optional[datetime] = None,
    ):
        self.key = key
        self.id = key
        self.fields = {
            "summary": summary,
            "status": {"name": status},
            "created": created or datetime.now(timezone.utc).isoformat(),
            "updated": datetime.now(timezone.utc).isoformat(),
        }


class FakeSLATracking:
    """Fake SLA tracking object."""
    
    def __init__(
        self,
        id: str = "sla-1",
        dispute_id: str = "dispute-1",
        sla_due_at: Optional[datetime] = None,
        breached: bool = False,
        escalated: bool = False,
    ):
        self.id = id
        self.dispute_id = dispute_id
        self.sla_due_at = sla_due_at or (datetime.now(timezone.utc) + timedelta(hours=4))
        self.breached = breached
        self.escalated = escalated
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class FakeAuth:
    """Fake authentication context."""
    
    def __init__(self, user_id: str = "user-1", username: str = "testuser", roles: Optional[List[str]] = None):
        self.user_id = user_id
        self.username = username
        self.roles = roles or ["user"]
        self.is_authenticated = True
