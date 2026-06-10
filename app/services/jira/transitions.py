from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.jira.client import JiraClient
from app.services.jira.issue_service import JiraIssueService


class JiraTransitionService:
    """Handles Jira issue transitions and ticket creation workflows."""

    def __init__(self, client: Optional[JiraClient] = None) -> None:
        self.client = client or JiraClient()

    def auto_create_ticket(self, dispute: Any, project_key: str = "PAY") -> Dict[str, Any]:
        return JiraIssueService(client=self.client).create_issue(dispute, project_key=project_key)

    def update_issue_status(self, issue_key: str, status: str, comment: Optional[str] = None) -> Dict[str, Any]:
        transition_id = self._status_to_transition(status)
        return self.transition_issue(issue_key, transition_id, comment=comment)

    def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        fields: Optional[Dict[str, Any]] = None,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.client.transition_issue(issue_key, transition_id, fields=fields, comment=comment)

    @staticmethod
    def _status_to_transition(status: str) -> str:
        normalized = status.strip().lower().replace(" ", "_")
        mapping = {
            "todo": "1",
            "to_do": "1",
            "in_progress": "2",
            "in-progress": "2",
            "done": "3",
            "resolved": "3",
            "closed": "4",
        }
        return mapping.get(normalized, status)
