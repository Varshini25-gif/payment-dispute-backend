# Test Suite Documentation

## Overview

This directory contains the comprehensive test suite for the payment-dispute-backend application. Tests are organized into several categories to ensure maintainability and clarity.

## Directory Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── core/               # Tests for core modules (auth, config, security)
│   ├── database/           # Tests for database models and ORM
│   ├── services/           # Tests for business logic services
│   └── conftest.py        # Unit test configuration
├── integration/            # Integration tests for workflows
│   └── conftest.py        # Integration test configuration
├── api/                    # API endpoint tests
│   ├── test_endpoints.py   # General endpoint tests
│   ├── test_auth.py        # Authentication endpoint tests
│   ├── test_disputes.py    # Dispute endpoint tests
│   └── conftest.py        # API test configuration
├── fixtures/               # Test fixtures and utilities
│   ├── mocks.py           # Mock objects (FakeSession, FakeClient, etc.)
│   ├── data/
│   │   └── builders.py    # Test data builders
│   └── conftest.py        # Fixture configuration
├── conftest.py            # Root test configuration and shared fixtures
└── pytest.ini             # Pytest configuration
```

## Test Categories

### Unit Tests (`tests/unit/`)

Unit tests focus on testing individual components in isolation.

#### Core Tests (`tests/unit/core/`)
- **test_auth_security.py**: Tests for authentication, password hashing, JWT tokens, and permissions

#### Database Tests (`tests/unit/database/`)
- **test_models.py**: Tests for database models, ORM functionality, and data persistence

#### Service Tests (`tests/unit/services/`)
- **test_rule_engine.py**: Rule engine parsing, validation, and matching
- **test_sla.py**: SLA calculation, breach detection, and tracking
- **test_jira_service.py**: Jira API client and issue service
- **test_confluence_service.py**: Confluence API client and publisher
- **test_routing_service.py**: Dispute routing logic and queue assignment
- **test_workers.py**: Background worker functionality

### API Tests (`tests/api/`)

API tests verify endpoint functionality and HTTP behavior.

- **test_endpoints.py**: General endpoint tests (health, error handling)
- **test_auth.py**: Authentication endpoints and permission enforcement
- **test_disputes.py**: Dispute CRUD operations and search functionality

### Integration Tests (`tests/integration/`)

Integration tests verify complete workflows across multiple components.

- **test_workflows.py**: End-to-end dispute workflows, SLA tracking, rule engine integration

## Test Fixtures

### Mock Objects (`tests/fixtures/mocks.py`)

Provides fake implementations of external services:
- `FakeSession`: Mock database session
- `FakeResponse`: Mock HTTP response
- `FakeJiraClient`: Mock Jira API client
- `FakeConfluenceClient`: Mock Confluence client
- `FakeDispute`: Mock dispute object
- `FakeAuth`: Mock authentication context

### Data Builders (`tests/fixtures/data/builders.py`)

Builder pattern implementations for test data:
- `DisputeDataBuilder`: Build test dispute data
- `JiraIssueDataBuilder`: Build test Jira issue data
- `SLADataBuilder`: Build test SLA data
- `AuthDataBuilder`: Build test auth data
- `RuleDataBuilder`: Build test rule engine data

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test category
```bash
# Unit tests only
pytest tests/unit/

# API tests only
pytest tests/api/

# Integration tests only
pytest tests/integration/
```

### Run tests by marker
```bash
# Unit tests
pytest -m unit

# Integration tests
pytest -m integration

# API tests
pytest -m api
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/unit/services/test_rule_engine.py
```

### Run specific test class
```bash
pytest tests/unit/services/test_rule_engine.py::TestRuleEngine
```

### Run specific test function
```bash
pytest tests/unit/services/test_rule_engine.py::TestRuleEngine::test_engine_matches_amount_range
```

### Run with verbose output
```bash
pytest -v
```

### Run and stop on first failure
```bash
pytest -x
```

### Run last failed tests
```bash
pytest --lf
```

## Configuration

### pytest.ini

Main pytest configuration file with settings for:
- Test discovery patterns
- Output formatting
- Test markers
- Coverage settings

### conftest.py Files

Each test directory has a `conftest.py` for:
- Shared fixtures
- Test configuration
- Marker application

## Best Practices

### 1. Isolation
- Unit tests should not depend on external services
- Use mock objects and fixtures
- Test one thing per test function

### 2. Naming
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Descriptive names that explain what's being tested

### 3. Organization
- Group related tests in classes
- Use docstrings to explain complex tests
- Keep test files focused on one module

### 4. Data Setup
- Use builders for complex test data
- Use fixtures for common setup
- Keep test data simple and readable

### 5. Assertions
- Use clear assertion messages
- One logical assertion per test
- Use pytest's assertion introspection

### 6. Fixtures
- Reuse common fixtures from conftest.py
- Create test-specific fixtures as needed
- Use appropriate fixture scope (function, class, module, session)

## Test Data

### Builders

Use builders to create test data:

```python
def test_example():
    dispute = DisputeDataBuilder()\
        .with_amount(500)\
        .with_type("chargeback")\
        .build()
    
    assert dispute["amount"] == 500
    assert dispute["type"] == "chargeback"
```

### Fixtures

Use fixtures for common objects:

```python
def test_example(fake_session, dispute_builder):
    dispute = dispute_builder.with_amount(1000).build()
    fake_session.add(dispute)
    fake_session.commit()
    
    assert fake_session.committed is True
```

## Markers

Custom markers for organizing tests:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.api`: API tests
- `@pytest.mark.slow`: Slow running tests

## Coverage Goals

- Unit tests: ≥85% coverage
- Integration tests: Key workflows
- API tests: All endpoints
- Overall: ≥75% coverage

## Continuous Integration

Tests are automatically run:
- On pull requests
- Before merging to main
- On commits to main
- Nightly full suite

## Troubleshooting

### Import Errors
Ensure the root directory is in PYTHONPATH. The conftest.py at the root handles this.

### Database Errors
Use FakeSession for tests that don't need a real database.

### Timeout Issues
Long-running tests should be marked with `@pytest.mark.slow` and can be skipped with `pytest -m "not slow"`.

### Flaky Tests
- Avoid sleep() calls
- Use deterministic test data
- Don't depend on external timing
- Use mocks for time-dependent logic

## Contributing

When adding new tests:

1. Place in appropriate directory (unit/api/integration)
2. Follow naming conventions
3. Use fixtures and builders
4. Add docstrings
5. Ensure tests are isolated
6. Verify tests pass locally
7. Update this README if adding new test categories

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [Unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
