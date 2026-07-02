"""Unit tests for SLA service."""

from datetime import datetime, timedelta, timezone

from app.database.models.enums import SlaStatus
from app.services.sla.calculators import calculate_elapsed_hours, calculate_sla_metrics
from app.services.sla.breach_detector import detect_sla_breach
from app.services.sla.tracker import SlaTracker
from tests.fixtures.mocks import FakeSession


class TestSLACalculators:
    """Test SLA calculation functions."""
    
    def test_calculate_elapsed_hours_returns_correct_duration(self):
        """Test elapsed hours calculation."""
        created_at = datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)
        updated_at = created_at + timedelta(hours=3)

        elapsed = calculate_elapsed_hours(created_at, updated_at)

        assert elapsed == 3.0

    def test_calculate_elapsed_hours_with_minutes(self):
        """Test elapsed hours with partial hours."""
        created_at = datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)
        updated_at = created_at + timedelta(hours=3, minutes=30)

        elapsed = calculate_elapsed_hours(created_at, updated_at)

        assert elapsed == 3.5

    def test_calculate_sla_metrics_on_track(self):
        """Test metrics calculation when SLA is on track."""
        created_at = datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)
        updated_at = created_at + timedelta(hours=1)
        sla_due_at = created_at + timedelta(hours=2)

        metrics = calculate_sla_metrics(created_at, updated_at, sla_due_at=sla_due_at)

        assert metrics["response_hours"] == 1.0
        assert metrics["resolution_hours"] == 1.0
        assert metrics["is_breached"] is False
        assert metrics["escalate"] is False

    def test_calculate_sla_metrics_breached(self):
        """Test metrics calculation when SLA is breached."""
        created_at = datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)
        updated_at = created_at + timedelta(hours=3)
        sla_due_at = created_at + timedelta(hours=2)

        metrics = calculate_sla_metrics(created_at, updated_at, sla_due_at=sla_due_at)

        assert metrics["response_hours"] == 3.0
        assert metrics["resolution_hours"] == 3.0
        assert metrics["is_breached"] is True
        assert metrics["escalate"] is True

    def test_calculate_sla_metrics_with_no_due_date(self):
        """Test metrics when no due date is set."""
        created_at = datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)
        updated_at = created_at + timedelta(hours=3)

        metrics = calculate_sla_metrics(created_at, updated_at, sla_due_at=None)

        assert metrics["response_hours"] == 3.0
        assert metrics["resolution_hours"] == 3.0
        assert metrics["is_breached"] is False


class TestSLABreachDetector:
    """Test SLA breach detection."""
    
    def test_detect_sla_breach_marks_status_when_breached(self):
        """Test breach detection marks status correctly."""
        now = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
        due_at = now - timedelta(hours=1)

        result = detect_sla_breach(due_at=due_at, status=SlaStatus.ON_TRACK, now=now)

        assert result["status"] == SlaStatus.BREACHED
        assert result["breached"] is True
        assert result["escalate"] is True

    def test_detect_sla_breach_keeps_status_when_on_track(self):
        """Test that status remains ON_TRACK when not breached."""
        now = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
        due_at = now + timedelta(hours=2)

        result = detect_sla_breach(due_at=due_at, status=SlaStatus.ON_TRACK, now=now)

        assert result["status"] == SlaStatus.ON_TRACK
        assert result["breached"] is False
        assert result["escalate"] is False

    def test_detect_sla_breach_with_already_breached_status(self):
        """Test detection when status is already breached."""
        now = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
        due_at = now - timedelta(hours=1)

        result = detect_sla_breach(due_at=due_at, status=SlaStatus.BREACHED, now=now)

        assert result["status"] == SlaStatus.BREACHED
        assert result["breached"] is True

    def test_detect_sla_breach_critical_when_very_late(self):
        """Test critical escalation when significantly breached."""
        now = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
        due_at = now - timedelta(hours=8)  # Way overdue

        result = detect_sla_breach(due_at=due_at, status=SlaStatus.ON_TRACK, now=now)

        assert result["status"] == SlaStatus.BREACHED
        assert result["escalate"] is True


class TestSLATracker:
    """Test SLA tracking."""
    
    def test_sla_tracker_persists_metrics(self) -> None:
        """Test that tracker persists metrics to database."""
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

    def test_sla_tracker_calculates_metrics(self) -> None:
        """Test metric calculations."""
        session = FakeSession()
        dispute = type("Dispute", (), {"id": "dispute-456"})()

        tracker = SlaTracker()
        result = tracker.track(
            dispute,
            created_at=datetime(2026, 6, 10, 8, 0, tzinfo=timezone.utc),
            resolved_at=datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc),
            sla_due_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
            db=session,
        )

        assert result["sla_hours_remaining"] is not None or result["sla_hours_exceeded"] is not None
        assert result["response_time_hours"] == 2.0

    def test_sla_tracker_handles_missing_resolved_at(self) -> None:
        """Test tracking when dispute not resolved."""
        session = FakeSession()
        dispute = type("Dispute", (), {"id": "dispute-789"})()

        tracker = SlaTracker()
        result = tracker.track(
            dispute,
            created_at=datetime(2026, 6, 10, 8, 0, tzinfo=timezone.utc),
            resolved_at=None,
            sla_due_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
            db=session,
        )

        assert result is not None
        assert session.committed is True
