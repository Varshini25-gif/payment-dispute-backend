"""Unit test configuration."""

import pytest


@pytest.fixture
def unit_test_marker():
    """Marker for unit tests."""
    return "unit"


def pytest_collection_modifyitems(items):
    """Add unit marker to unit tests."""
    for item in items:
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
