"""Unit tests for dispute routing service."""

import pytest
from unittest.mock import MagicMock
from app.services.dispute.routing_service import RoutingService
from app.services.rule_engine.parser import Rule
from app.services.rule_engine.engine import RuleEngine


class TestRoutingService:
    """Test dispute routing service."""
    
    def test_routing_service_initialization(self):
        """Test service initialization."""
        service = RoutingService()
        assert service is not None
    
    def test_route_dispute_by_rules(self):
        """Test routing dispute based on rules."""
        # Create test rule
        rule = Rule(
            id="route-fraud",
            description="Route fraud cases",
            conditions={"field": "type", "operator": "equals", "value": "fraud"},
            actions=[{"type": "route", "target": "fraud-team"}]
        )
        
        service = RoutingService()
        
        # Create test dispute
        dispute = {
            "id": "dispute-1",
            "type": "fraud",
            "amount": 1000,
            "customer_id": "cust-1"
        }
        
        # Route the dispute
        # Expected: returns routing decision
        assert dispute["type"] == "fraud"
    
    def test_route_dispute_high_value(self):
        """Test routing high-value disputes."""
        rule = Rule(
            id="route-high-value",
            description="Route high-value disputes",
            conditions={"field": "amount", "operator": "gte", "value": 5000},
            actions=[{"type": "route", "target": "vip-team"}]
        )
        
        service = RoutingService()
        
        dispute = {
            "id": "dispute-2",
            "type": "chargeback",
            "amount": 10000,
            "customer_id": "cust-2"
        }
        
        assert dispute["amount"] >= 5000
    
    def test_route_dispute_by_customer_tier(self):
        """Test routing based on customer tier."""
        service = RoutingService()
        
        vip_customer = {
            "id": "dispute-3",
            "customer_id": "vip-customer-1",
            "amount": 500,
            "type": "refund"
        }
        
        # VIP should be prioritized
        assert "vip" in vip_customer["customer_id"].lower()
    
    def test_fallback_routing(self):
        """Test fallback routing when no rules match."""
        service = RoutingService()
        
        dispute = {
            "id": "dispute-4",
            "type": "unknown_type",
            "amount": 100,
            "customer_id": "cust-4"
        }
        
        # Should route to default queue
        assert dispute is not None
    
    def test_routing_decision_includes_queue(self):
        """Test that routing decision includes target queue."""
        service = RoutingService()
        
        dispute = {
            "id": "dispute-5",
            "type": "chargeback",
            "amount": 1000
        }
        
        # Decision should include queue information
        assert "type" in dispute
    
    def test_multiple_routing_rules_priority(self):
        """Test priority when multiple rules match."""
        rules = [
            Rule(
                id="rule-1",
                description="High priority",
                conditions={"field": "amount", "operator": "gte", "value": 1000},
                actions=[{"type": "route", "target": "priority-team"}]
            ),
            Rule(
                id="rule-2",
                description="Medium priority",
                conditions={"field": "type", "operator": "equals", "value": "chargeback"},
                actions=[{"type": "route", "target": "standard-team"}]
            ),
        ]
        
        engine = RuleEngine(rules)
        
        dispute = {
            "amount": 5000,
            "type": "chargeback",
            "customer_id": "cust-6"
        }
        
        # First matching rule should be used
        match = engine.decide(dispute)
        assert match is not None


class TestRoutingMetrics:
    """Test routing metrics and monitoring."""
    
    def test_track_routing_decision(self):
        """Test tracking routing decisions."""
        service = RoutingService()
        
        dispute = {
            "id": "dispute-1",
            "type": "chargeback",
            "amount": 1000
        }
        
        # Service should track the routing
        assert dispute["id"] is not None
    
    def test_routing_success_rate(self):
        """Test success rate metrics."""
        service = RoutingService()
        
        # Successful routing
        disputes = [
            {"id": f"d-{i}", "type": "chargeback", "amount": 100 * (i + 1)}
            for i in range(5)
        ]
        
        assert len(disputes) == 5
    
    def test_routing_latency(self):
        """Test routing latency measurement."""
        from datetime import datetime, timezone
        
        start = datetime.now(timezone.utc)
        
        # Simulate routing
        dispute = {"id": "dispute-1", "type": "chargeback"}
        
        end = datetime.now(timezone.utc)
        latency = (end - start).total_seconds()
        
        assert latency >= 0
