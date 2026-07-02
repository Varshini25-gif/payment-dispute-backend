"""Test data builders for payment dispute backend."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional


class DisputeDataBuilder:
    """Builder for creating test dispute data."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {
            "id": "dispute-123",
            "external_id": "EXT-001",
            "amount": 100.0,
            "currency": "USD",
            "type": "chargeback",
            "status": "pending",
            "reason": "Unauthorized transaction",
            "customer_id": "customer-1",
            "description": "Test dispute",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    
    def with_amount(self, amount: float) -> "DisputeDataBuilder":
        self.data["amount"] = amount
        return self
    
    def with_type(self, dispute_type: str) -> "DisputeDataBuilder":
        self.data["type"] = dispute_type
        return self
    
    def with_status(self, status: str) -> "DisputeDataBuilder":
        self.data["status"] = status
        return self
    
    def with_customer_id(self, customer_id: str) -> "DisputeDataBuilder":
        self.data["customer_id"] = customer_id
        return self
    
    def with_currency(self, currency: str) -> "DisputeDataBuilder":
        self.data["currency"] = currency
        return self
    
    def with_reason(self, reason: str) -> "DisputeDataBuilder":
        self.data["reason"] = reason
        return self
    
    def build(self) -> Dict[str, Any]:
        return self.data.copy()


class JiraIssueDataBuilder:
    """Builder for creating test Jira issue data."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {
            "key": "TEST-1",
            "id": "1",
            "fields": {
                "summary": "Test Issue",
                "description": "This is a test issue",
                "project": {"key": "TEST"},
                "status": {"name": "To Do"},
                "priority": {"name": "Medium"},
                "issuetype": {"name": "Task"},
                "created": datetime.now(timezone.utc).isoformat(),
                "updated": datetime.now(timezone.utc).isoformat(),
            }
        }
    
    def with_key(self, key: str) -> "JiraIssueDataBuilder":
        self.data["key"] = key
        return self
    
    def with_summary(self, summary: str) -> "JiraIssueDataBuilder":
        self.data["fields"]["summary"] = summary
        return self
    
    def with_status(self, status: str) -> "JiraIssueDataBuilder":
        self.data["fields"]["status"]["name"] = status
        return self
    
    def with_priority(self, priority: str) -> "JiraIssueDataBuilder":
        self.data["fields"]["priority"]["name"] = priority
        return self
    
    def build(self) -> Dict[str, Any]:
        import copy
        return copy.deepcopy(self.data)


class SLADataBuilder:
    """Builder for creating test SLA data."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {
            "id": "sla-1",
            "dispute_id": "dispute-1",
            "sla_hours": 4,
            "sla_due_at": datetime.now(timezone.utc) + timedelta(hours=4),
            "breached": False,
            "escalated": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "response_hours": None,
            "resolution_hours": None,
        }
    
    def with_sla_hours(self, hours: int) -> "SLADataBuilder":
        self.data["sla_hours"] = hours
        self.data["sla_due_at"] = datetime.now(timezone.utc) + timedelta(hours=hours)
        return self
    
    def with_breached(self, breached: bool) -> "SLADataBuilder":
        self.data["breached"] = breached
        return self
    
    def with_escalated(self, escalated: bool) -> "SLADataBuilder":
        self.data["escalated"] = escalated
        return self
    
    def with_response_hours(self, hours: float) -> "SLADataBuilder":
        self.data["response_hours"] = hours
        return self
    
    def with_resolution_hours(self, hours: float) -> "SLADataBuilder":
        self.data["resolution_hours"] = hours
        return self
    
    def build(self) -> Dict[str, Any]:
        return self.data.copy()


class AuthDataBuilder:
    """Builder for creating test authentication data."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {
            "user_id": "user-1",
            "username": "testuser",
            "email": "testuser@example.com",
            "roles": ["user"],
            "permissions": ["read"],
            "is_active": True,
            "is_verified": True,
        }
    
    def with_username(self, username: str) -> "AuthDataBuilder":
        self.data["username"] = username
        return self
    
    def with_roles(self, roles: list) -> "AuthDataBuilder":
        self.data["roles"] = roles
        return self
    
    def with_permissions(self, permissions: list) -> "AuthDataBuilder":
        self.data["permissions"] = permissions
        return self
    
    def as_admin(self) -> "AuthDataBuilder":
        self.data["roles"] = ["admin"]
        self.data["permissions"] = ["read", "write", "delete", "admin"]
        return self
    
    def build(self) -> Dict[str, Any]:
        return self.data.copy()


class RuleDataBuilder:
    """Builder for creating test rule engine data."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {
            "id": "rule-1",
            "description": "Test rule",
            "conditions": {
                "field": "amount",
                "operator": "gte",
                "value": 100
            },
            "actions": [
                {
                    "type": "route",
                    "target": "default-queue"
                }
            ]
        }
    
    def with_id(self, rule_id: str) -> "RuleDataBuilder":
        self.data["id"] = rule_id
        return self
    
    def with_description(self, description: str) -> "RuleDataBuilder":
        self.data["description"] = description
        return self
    
    def with_conditions(self, conditions: dict) -> "RuleDataBuilder":
        self.data["conditions"] = conditions
        return self
    
    def with_actions(self, actions: list) -> "RuleDataBuilder":
        self.data["actions"] = actions
        return self
    
    def build(self) -> Dict[str, Any]:
        return self.data.copy()
