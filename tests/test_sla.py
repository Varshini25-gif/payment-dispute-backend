from datetime import datetime, timedelta, timezone

from app.database.models.enums import SlaStatus
from app.services.sla.calculators import calculate_elapsed_hours, calculate_sla_metrics
from app.services.sla.breach_detector import detect_sla_breach
from app.services.sla.tracker import SlaTracker


class FakeSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.refreshed = []

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed.append(obj)


def test_calculate_elapsed_hours_and_metrics():
    created_at = datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)
    updated_at = created_at + timedelta(hours=3)

    assert calculate_elapsed_hours(created_at, updated_at) == 3.0

    metrics = calculate_sla_metrics(created_at, updated_at, sla_due_at=created_at + timedelta(hours=2))

    assert metrics["response_hours"] == 3.0
    assert metrics["resolution_hours"] == 3.0
    assert metrics["is_breached"] is True
    assert metrics["escalate"] is True


def test_detect_sla_breach_marks_status_and_escalation():
    now = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
    due_at = now - timedelta(hours=1)

    result = detect_sla_breach(due_at=due_at, status=SlaStatus.ON_TRACK, now=now)

    assert result["status"] == SlaStatus.BREACHED
    assert result["breached"] is True
    assert result["escalate"] is True


def test_sla_tracker_persists_metrics() -> None:
    session = FakeSession()
    dispute = type("Dispute", (), {"id": "dispute-123"})()

    tracker = SlaTracker()
    result = tracker.track(
        dispute,
        created_at=datetime(2026, 6, 10, 8, 0, tzinfo=timezone.utc),
        resolved_at=datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc),
        sla_due_at=datetime(2026, 6, 10, 9, 0, tzinfo=timezone.utc),
        db=session,
    )

    assert session.committed is True
    assert len(session.added) == 1
    assert result["sla_status"] == SlaStatus.BREACHED
    assert result["breach_detected"] is True
