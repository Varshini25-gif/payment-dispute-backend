"""Root test configuration and shared fixtures."""

from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app
from tests.fixtures.mocks import (
    FakeSession, FakeResponse, FakeJiraClient, 
    FakeConfluenceClient, FakeDispute, FakeAuth
)
from tests.fixtures.data.builders import (
    DisputeDataBuilder, JiraIssueDataBuilder,
    SLADataBuilder, AuthDataBuilder, RuleDataBuilder
)


# ==================== Fixtures ====================

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def fake_session():
    """Fake database session."""
    return FakeSession()


@pytest.fixture
def fake_dispute():
    """Fake dispute object."""
    return FakeDispute()


@pytest.fixture
def dispute_builder():
    """Dispute data builder."""
    return DisputeDataBuilder()


@pytest.fixture
def sla_builder():
    """SLA data builder."""
    return SLADataBuilder()


@pytest.fixture
def auth_builder():
    """Auth data builder."""
    return AuthDataBuilder()


@pytest.fixture
def rule_builder():
    """Rule data builder."""
    return RuleDataBuilder()


@pytest.fixture
def jira_issue_builder():
    """Jira issue builder."""
    return JiraIssueDataBuilder()


@pytest.fixture
def fake_jira_client():
    """Fake Jira client."""
    return FakeJiraClient()


@pytest.fixture
def fake_confluence_client():
    """Fake Confluence client."""
    return FakeConfluenceClient()


@pytest.fixture
def fake_auth():
    """Fake auth context."""
    return FakeAuth()


# ==================== Configuration ====================

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
