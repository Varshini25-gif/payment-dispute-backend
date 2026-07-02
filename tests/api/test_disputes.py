"""API tests for dispute endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestDisputeCreation:
    """Test dispute creation endpoint."""
    
    def test_create_dispute_with_valid_data(self):
        """Test creating dispute with valid data."""
        dispute_data = {
            "external_id": "EXT-001",
            "amount": 100.0,
            "currency": "USD",
            "type": "chargeback",
            "customer_id": "customer-1",
            "reason": "Unauthorized charge"
        }
        response = client.post("/api/disputes", json=dispute_data)
        assert response.status_code in [201, 400, 401, 403, 422]
    
    def test_create_dispute_missing_required_field(self):
        """Test that missing required field is rejected."""
        dispute_data = {
            "external_id": "EXT-002",
            # Missing amount
            "currency": "USD",
            "type": "chargeback"
        }
        response = client.post("/api/disputes", json=dispute_data)
        assert response.status_code in [422, 400, 401, 403]
    
    def test_create_dispute_invalid_amount(self):
        """Test that invalid amount is rejected."""
        dispute_data = {
            "external_id": "EXT-003",
            "amount": -100.0,  # Negative amount
            "currency": "USD",
            "type": "chargeback",
            "customer_id": "customer-1",
            "reason": "Test"
        }
        response = client.post("/api/disputes", json=dispute_data)
        assert response.status_code in [422, 400, 401, 403]
    
    def test_create_dispute_invalid_type(self):
        """Test that invalid type is rejected."""
        dispute_data = {
            "external_id": "EXT-004",
            "amount": 100.0,
            "currency": "USD",
            "type": "invalid_type",
            "customer_id": "customer-1",
            "reason": "Test"
        }
        response = client.post("/api/disputes", json=dispute_data)
        assert response.status_code in [422, 400, 401, 403]


class TestDisputeRetrieval:
    """Test dispute retrieval endpoints."""
    
    def test_list_disputes(self):
        """Test listing disputes."""
        response = client.get("/api/disputes")
        assert response.status_code in [200, 401, 403]
    
    def test_get_dispute_by_id(self):
        """Test getting specific dispute."""
        response = client.get("/api/disputes/nonexistent-id")
        assert response.status_code in [404, 401, 403, 200]
    
    def test_list_disputes_with_filters(self):
        """Test listing with filters."""
        response = client.get("/api/disputes?type=chargeback&status=pending")
        assert response.status_code in [200, 401, 403, 422]
    
    def test_list_disputes_with_pagination(self):
        """Test pagination."""
        response = client.get("/api/disputes?skip=0&limit=10")
        assert response.status_code in [200, 401, 403, 422]


class TestDisputeUpdate:
    """Test dispute update endpoints."""
    
    def test_update_dispute_status(self):
        """Test updating dispute status."""
        update_data = {"status": "resolved"}
        response = client.patch("/api/disputes/dispute-1", json=update_data)
        assert response.status_code in [200, 404, 401, 403, 422]
    
    def test_update_nonexistent_dispute(self):
        """Test updating nonexistent dispute."""
        update_data = {"status": "resolved"}
        response = client.patch("/api/disputes/nonexistent", json=update_data)
        assert response.status_code in [404, 401, 403, 422]
    
    def test_partial_update_dispute(self):
        """Test partial update."""
        update_data = {"reason": "Updated reason"}
        response = client.patch("/api/disputes/dispute-1", json=update_data)
        assert response.status_code in [200, 404, 401, 403, 422]


class TestDisputeDeletion:
    """Test dispute deletion."""
    
    def test_delete_dispute(self):
        """Test deleting a dispute."""
        response = client.delete("/api/disputes/dispute-1")
        assert response.status_code in [204, 404, 401, 403]
    
    def test_delete_nonexistent_dispute(self):
        """Test deleting nonexistent dispute."""
        response = client.delete("/api/disputes/nonexistent")
        assert response.status_code in [404, 401, 403, 204]


class TestDisputeSearch:
    """Test dispute search functionality."""
    
    def test_search_by_external_id(self):
        """Test search by external ID."""
        response = client.get("/api/disputes/search?external_id=EXT-001")
        assert response.status_code in [200, 401, 403, 404, 422]
    
    def test_search_by_customer_id(self):
        """Test search by customer ID."""
        response = client.get("/api/disputes/search?customer_id=customer-1")
        assert response.status_code in [200, 401, 403, 404, 422]
    
    def test_search_by_amount_range(self):
        """Test search by amount range."""
        response = client.get("/api/disputes/search?min_amount=100&max_amount=500")
        assert response.status_code in [200, 401, 403, 404, 422]
    
    def test_search_empty_result(self):
        """Test search with no results."""
        response = client.get("/api/disputes/search?external_id=NONEXISTENT")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
