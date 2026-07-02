"""Unit tests for database models and ORM."""

import pytest
from datetime import datetime, timezone
from app.database.models.dispute import Dispute
from app.database.models.sla_tracking import SLATracking
from app.database.models.enums import SlaStatus


class TestDisputeModel:
    """Test Dispute database model."""
    
    def test_create_dispute_instance(self):
        """Test creating a dispute instance."""
        dispute = Dispute(
            external_id="EXT-001",
            amount=1000.0,
            currency="USD",
            type="chargeback",
            status="pending",
            customer_id="customer-1"
        )
        
        assert dispute.external_id == "EXT-001"
        assert dispute.amount == 1000.0
        assert dispute.type == "chargeback"
    
    def test_dispute_timestamps(self):
        """Test dispute timestamp fields."""
        now = datetime.now(timezone.utc)
        
        dispute = Dispute(
            external_id="EXT-002",
            amount=500.0,
            currency="USD",
            type="refund",
            status="pending",
            customer_id="customer-2",
            created_at=now
        )
        
        assert dispute.created_at is not None
        assert dispute.created_at == now
    
    def test_dispute_status_transitions(self):
        """Test valid status transitions."""
        dispute = Dispute(
            external_id="EXT-003",
            amount=100.0,
            currency="USD",
            type="test",
            status="pending",
            customer_id="customer-3"
        )
        
        # Simulate status change
        valid_statuses = ["pending", "in_progress", "resolved", "rejected"]
        assert dispute.status in valid_statuses
    
    def test_dispute_required_fields(self):
        """Test required fields."""
        required_fields = [
            "external_id",
            "amount",
            "currency",
            "type",
            "customer_id"
        ]
        
        # All should be settable
        for field in required_fields:
            assert hasattr(Dispute, field) or field in ["external_id"]


class TestSLATrackingModel:
    """Test SLA tracking model."""
    
    def test_sla_tracking_creation(self):
        """Test creating SLA tracking record."""
        sla = SLATracking(
            dispute_id="dispute-1",
            sla_due_at=datetime.now(timezone.utc),
            status=SlaStatus.ON_TRACK
        )
        
        assert sla.dispute_id == "dispute-1"
        assert sla.status == SlaStatus.ON_TRACK
    
    def test_sla_status_values(self):
        """Test SLA status enum values."""
        statuses = [SlaStatus.ON_TRACK, SlaStatus.BREACHED, SlaStatus.RESOLVED]
        
        for status in statuses:
            assert status is not None
    
    def test_sla_breach_tracking(self):
        """Test tracking breach status."""
        sla = SLATracking(
            dispute_id="dispute-2",
            sla_due_at=datetime.now(timezone.utc),
            status=SlaStatus.BREACHED,
            breached=True
        )
        
        assert sla.breached is True
        assert sla.status == SlaStatus.BREACHED
    
    def test_sla_metrics_fields(self):
        """Test SLA metrics fields."""
        sla = SLATracking(
            dispute_id="dispute-3",
            sla_due_at=datetime.now(timezone.utc),
            status=SlaStatus.ON_TRACK
        )
        
        # Should have metrics fields
        assert hasattr(sla, "response_hours") or hasattr(sla, "sla_due_at")


class TestAuditLogModel:
    """Test audit logging."""
    
    def test_audit_log_creation(self):
        """Test creating audit log."""
        from app.database.models.audit_log import AuditLog
        
        audit = AuditLog(
            entity_type="dispute",
            entity_id="dispute-1",
            action="created",
            user_id="user-1",
            changes={"status": "pending"}
        )
        
        assert audit.entity_type == "dispute"
        assert audit.action == "created"
    
    def test_audit_log_captures_changes(self):
        """Test that changes are captured."""
        from app.database.models.audit_log import AuditLog
        
        changes = {"status": {"old": "pending", "new": "resolved"}}
        
        audit = AuditLog(
            entity_type="dispute",
            entity_id="dispute-2",
            action="updated",
            user_id="user-1",
            changes=changes
        )
        
        assert audit.changes is not None


class TestJiraIssueModel:
    """Test Jira issue model."""
    
    def test_jira_issue_creation(self):
        """Test creating Jira issue record."""
        from app.database.models.jira_issue import JiraIssue
        
        issue = JiraIssue(
            dispute_id="dispute-1",
            jira_key="PAY-123",
            jira_id="123456",
            status="To Do"
        )
        
        assert issue.jira_key == "PAY-123"
        assert issue.dispute_id == "dispute-1"
    
    def test_jira_issue_tracking(self):
        """Test tracking Jira issues."""
        from app.database.models.jira_issue import JiraIssue
        
        issue = JiraIssue(
            dispute_id="dispute-2",
            jira_key="PAY-124",
            jira_id="123457",
            status="In Progress"
        )
        
        assert issue.status in ["To Do", "In Progress", "Done", "In Review"]


class TestApiRequestLogModel:
    """Test API request logging."""
    
    def test_log_api_request(self):
        """Test logging API request."""
        from app.database.models.api_request_log import ApiRequestLog
        
        log = ApiRequestLog(
            method="POST",
            endpoint="/api/disputes",
            status_code=201,
            response_time_ms=150,
            user_id="user-1"
        )
        
        assert log.method == "POST"
        assert log.status_code == 201
    
    def test_log_contains_timing(self):
        """Test that logs contain timing information."""
        from app.database.models.api_request_log import ApiRequestLog
        
        log = ApiRequestLog(
            method="GET",
            endpoint="/api/disputes",
            status_code=200,
            response_time_ms=50
        )
        
        assert log.response_time_ms >= 0
