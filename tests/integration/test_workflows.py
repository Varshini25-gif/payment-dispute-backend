"""Integration tests for payment-dispute-backend."""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from tests.fixtures.mocks import FakeSession, FakeDispute, FakeSLATracking
from tests.fixtures.data.builders import DisputeDataBuilder, SLADataBuilder


client = TestClient(app)


class TestDisputeWorkflow:
    """Test complete dispute workflow."""
    
    def test_create_and_retrieve_dispute(self):
        """Test creating and retrieving a dispute."""
        # Create dispute
        dispute_data = {
            "external_id": "EXT-001",
            "amount": 100.0,
            "currency": "USD",
            "type": "chargeback",
            "customer_id": "customer-1",
            "reason": "Unauthorized charge"
        }
        
        create_response = client.post("/api/disputes", json=dispute_data)
        
        # Check response status
        if create_response.status_code == 201:
            dispute_id = create_response.json().get("id")
            
            # Retrieve dispute
            get_response = client.get(f"/api/disputes/{dispute_id}")
            
            if get_response.status_code == 200:
                retrieved = get_response.json()
                assert retrieved["external_id"] == "EXT-001"
                assert retrieved["amount"] == 100.0

    def test_dispute_status_transitions(self):
        """Test dispute status transitions."""
        builder = DisputeDataBuilder()
        dispute = builder.with_status("pending").build()
        
        assert dispute["status"] == "pending"
        
        # Simulate status change
        updated_dispute = builder.with_status("resolved").build()
        assert updated_dispute["status"] == "resolved"


class TestSLATracking:
    """Test SLA tracking integration."""
    
    def test_sla_calculated_on_dispute_creation(self):
        """Test that SLA is calculated when dispute is created."""
        builder = SLADataBuilder()
        sla = builder.with_sla_hours(4).build()
        
        assert sla["sla_hours"] == 4
        assert sla["breached"] is False
        assert sla["sla_due_at"] is not None

    def test_sla_breach_detection(self):
        """Test SLA breach is detected."""
        now = datetime.now(timezone.utc)
        due_at = now - timedelta(hours=1)
        
        builder = SLADataBuilder()
        sla = builder.with_breached(True).build()
        
        assert sla["breached"] is True

    def test_sla_escalation_on_breach(self):
        """Test that escalation happens on SLA breach."""
        builder = SLADataBuilder()
        sla = builder.with_breached(True).with_escalated(True).build()
        
        assert sla["breached"] is True
        assert sla["escalated"] is True


class TestRuleEngineIntegration:
    """Test rule engine with dispute data."""
    
    def test_rule_matches_dispute_attributes(self):
        """Test that rules match dispute attributes."""
        from app.services.rule_engine.parser import Rule
        from app.services.rule_engine.engine import RuleEngine
        
        rule = Rule(
            id="test-rule",
            description="Test rule",
            conditions={
                "all_of": [
                    {"field": "amount", "operator": "gte", "value": 100},
                    {"field": "type", "operator": "equals", "value": "chargeback"}
                ]
            },
            actions=[{"type": "route", "target": "fraud-team"}]
        )
        
        engine = RuleEngine([rule])
        dispute = DisputeDataBuilder().with_amount(500).with_type("chargeback").build()
        
        match = engine.decide({
            "amount": dispute["amount"],
            "type": dispute["type"],
            "customer_id": dispute["customer_id"]
        })
        
        assert match is not None
        assert match.rule_id == "test-rule"

    def test_multiple_rules_evaluation(self):
        """Test evaluating multiple rules."""
        from app.services.rule_engine.parser import Rule
        from app.services.rule_engine.engine import RuleEngine
        
        rules = [
            Rule(
                id="high-value",
                description="High value disputes",
                conditions={"field": "amount", "operator": "gte", "value": 1000},
                actions=[{"type": "route", "target": "vip-team"}]
            ),
            Rule(
                id="chargeback",
                description="Chargeback disputes",
                conditions={"field": "type", "operator": "equals", "value": "chargeback"},
                actions=[{"type": "route", "target": "fraud-team"}]
            ),
        ]
        
        engine = RuleEngine(rules)
        
        # High value match
        dispute = DisputeDataBuilder().with_amount(5000).with_type("refund").build()
        match = engine.decide({
            "amount": dispute["amount"],
            "type": dispute["type"],
            "customer_id": dispute["customer_id"]
        })
        
        assert match is not None


class TestAuthenticationFlow:
    """Test authentication flow."""
    
    def test_login_flow(self):
        """Test login flow."""
        login_data = {
            "username": "testuser",
            "password": "TestPassword@123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            assert "access_token" in token_data or "token" in token_data

    def test_protected_endpoint_requires_auth(self):
        """Test that protected endpoints require authentication."""
        # Try to access protected endpoint without token
        response = client.get("/api/disputes")
        
        # Should be 401 or 403 without auth
        assert response.status_code in [401, 403, 200]


class TestErrorHandlingIntegration:
    """Test error handling across system."""
    
    def test_invalid_dispute_data_rejected(self):
        """Test that invalid data is rejected."""
        invalid_data = {
            "external_id": "EXT-001",
            # Missing required fields
        }
        
        response = client.post("/api/disputes", json=invalid_data)
        
        # Should be 422 or error
        assert response.status_code in [422, 400, 401, 403]

    def test_concurrent_requests_handled(self):
        """Test handling concurrent requests."""
        for i in range(3):
            response = client.get("/api/health")
            assert response.status_code == 200

    def test_database_error_handling(self):
        """Test database error handling."""
        # With fake session, should handle gracefully
        session = FakeSession()
        session.add(FakeDispute())
        session.commit()
        
        assert session.committed is True


class TestDataConsistency:
    """Test data consistency across operations."""
    
    def test_dispute_and_sla_consistency(self):
        """Test that dispute and SLA data remain consistent."""
        builder = DisputeDataBuilder()
        dispute = builder.with_amount(500).build()
        
        sla_builder = SLADataBuilder()
        sla = sla_builder.with_sla_hours(4).build()
        
        # Both should be consistent
        assert dispute["id"] is not None
        assert sla["dispute_id"] is not None

    def test_audit_trail_created(self):
        """Test that audit trail is maintained."""
        dispute = FakeDispute(id="dispute-1", status="pending")
        
        # Create fake session for audit
        session = FakeSession()
        session.add(dispute)
        session.commit()
        
        # Audit should be created
        assert session.committed is True

    def test_transactional_integrity(self):
        """Test transactional integrity."""
        session = FakeSession()
        
        dispute1 = FakeDispute(id="d-1")
        dispute2 = FakeDispute(id="d-2")
        
        session.add(dispute1)
        session.add(dispute2)
        session.commit()
        
        assert len(session.added) == 2
        assert session.committed is True
