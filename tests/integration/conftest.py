"""Integration test configuration."""

import pytest


@pytest.fixture
def integration_test_marker():
    """Marker for integration tests."""
    return "integration"


def pytest_collection_modifyitems(items):
    """Add integration marker to integration tests."""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
