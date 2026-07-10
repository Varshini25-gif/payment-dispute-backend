from __future__ import annotations

from typing import Any, Optional

from app.services.jira.client import JiraClient


class JiraIssueService:
    """Builds Jira issue payloads for disputes and creates them through the client."""

    def __init__(self, client: Optional[JiraClient] = None) -> None:
        self.client = client or JiraClient()

    def _priority_for(self, dispute: Any) -> str:
        amount = float(getattr(dispute, "amount", 0) or 0)
        return "High" if amount >= 1000 else "Medium"

    def create_issue(self, dispute: Any, project_key: str = "PAY") -> Any:
        amount = getattr(dispute, "amount", 0) or 0
        dispute_type = getattr(dispute, "type", "other") or "other"
        summary = f"Dispute {getattr(dispute, 'external_id', 'UNKNOWN')} - {dispute_type}"
        description = (
            f"External ID: {getattr(dispute, 'external_id', 'UNKNOWN')}\n"
            f"Customer: {getattr(dispute, 'customer_id', 'unknown')}\n"
            f"Amount: {amount}\n"
            f"Reason: {getattr(dispute, 'reason', 'No reason provided')}"
        )

        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Task"},
            "priority": {"name": self._priority_for(dispute)},
        }

        return self.client.create_issue(fields)
