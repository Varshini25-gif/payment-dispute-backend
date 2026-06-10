from app.services.jira.transitions import JiraTransitionService


class FakeJiraClient:
    def __init__(self):
        self.calls = []

    def transition_issue(self, issue_key: str, transition_id: str, fields=None, comment=None):
        self.calls.append({
            "issue_key": issue_key,
            "transition_id": transition_id,
            "fields": fields,
            "comment": comment,
        })
        return {"key": issue_key, "status": "In Progress"}


def test_transition_service_updates_status_and_comment() -> None:
    client = FakeJiraClient()
    service = JiraTransitionService(client=client)

    result = service.transition_issue("PAY-1", "in_progress", comment="Review started")

    assert result == {"key": "PAY-1", "status": "In Progress"}
    assert client.calls == [
        {
            "issue_key": "PAY-1",
            "transition_id": "in_progress",
            "fields": None,
            "comment": "Review started",
        }
    ]


def test_transition_service_maps_status_to_transition_id() -> None:
    client = FakeJiraClient()
    service = JiraTransitionService(client=client)

    service.transition_issue("PAY-2", "done")

    assert client.calls[0]["transition_id"] == "done"
