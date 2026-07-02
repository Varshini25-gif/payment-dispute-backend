"""API test configuration."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def api_client():
    """API test client."""
    return TestClient(app)


@pytest.fixture
def api_test_marker():
    """Marker for API tests."""
    return "api"


def pytest_collection_modifyitems(items):
    """Add API marker to API tests."""
    for item in items:
        if "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
