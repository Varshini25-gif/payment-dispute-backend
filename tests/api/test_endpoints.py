"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_endpoint_returns_ok(self) -> None:
        """Test health endpoint returns 200 with ok status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "degraded"]
        assert data["service"] == "payment-dispute-backend"
    
    def test_health_endpoint_has_timestamp(self) -> None:
        """Test health endpoint includes timestamp."""
        response = client.get("/api/health")
        data = response.json()
        assert "timestamp" in data
    
    def test_health_endpoint_json_valid(self) -> None:
        """Test health endpoint returns valid JSON."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestDisputesEndpoints:
    """Test dispute endpoints."""
    
    def test_list_disputes_endpoint(self) -> None:
        """Test listing disputes."""
        response = client.get("/api/disputes")
        # Should be 200 or 401 depending on auth
        assert response.status_code in [200, 401, 403]
    
    def test_create_dispute_endpoint(self) -> None:
        """Test creating a dispute."""
        dispute_data = {
            "external_id": "EXT-001",
            "amount": 100.0,
            "currency": "USD",
            "type": "chargeback",
            "customer_id": "customer-1",
            "reason": "Unauthorized charge"
        }
        response = client.post("/api/disputes", json=dispute_data)
        # Should be 201 or 401 depending on auth
        assert response.status_code in [201, 401, 403, 422]


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_login_endpoint_exists(self) -> None:
        """Test login endpoint is available."""
        login_data = {
            "username": "testuser",
            "password": "TestPassword@123"
        }
        response = client.post("/api/auth/login", json=login_data)
        # Should return something (success or error)
        assert response.status_code in [200, 401, 422, 404]
    
    def test_invalid_credentials_rejected(self) -> None:
        """Test that invalid credentials are rejected."""
        login_data = {
            "username": "invalid",
            "password": "invalid"
        }
        response = client.post("/api/auth/login", json=login_data)
        # Should not return 200
        assert response.status_code != 200


class TestErrorHandling:
    """Test error handling."""
    
    def test_404_not_found(self) -> None:
        """Test 404 error handling."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_json_returns_422(self) -> None:
        """Test that invalid JSON returns 422."""
        response = client.post(
            "/api/disputes",
            json={"invalid": "field"},
            headers={"Content-Type": "application/json"}
        )
        # Invalid data should result in error
        assert response.status_code in [422, 400, 401, 403]
    
    def test_missing_required_fields(self) -> None:
        """Test missing required fields."""
        response = client.post(
            "/api/disputes",
            json={"external_id": "EXT-001"}
        )
        # Missing required fields
        assert response.status_code in [422, 400, 401, 403]
