# Raimy Backend Tests

This directory contains unit and integration tests for the Raimy backend.

## Test Coverage

- **Integration Tests** (`test_meal_planner_routes.py`): 7 tests - ALL PASSING ✅
  - Tests API endpoints with mocked auth and database
  - Full coverage of CRUD operations
  - Tests authentication and authorization
  - Tests error handling (404, 403)

## Setup

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure PostgreSQL test database exists:
```bash
createdb raimy_test
# Or if using docker:
docker exec -it raimy-postgres-1 psql -U raimy -c "CREATE DATABASE raimy_test;"
```

## Running Tests

### Run all tests:
```bash
cd server
pytest
```

### Run with coverage:
```bash
pytest --cov=app --cov=mcp_service --cov-report=html
```

### Run specific test types:
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Specific test file
pytest tests/test_database_service.py

# Specific test function
pytest tests/test_database_service.py::TestDatabaseServiceMealPlanner::test_create_meal_planner_session
```

### Verbose output:
```bash
pytest -v
```

## Test Structure

- `conftest.py` - Test fixtures and configuration
- `test_database_service.py` - Unit tests for database operations
- `test_meal_planner_routes.py` - Integration tests for API endpoints

## Coverage

Tests aim for 70% code coverage minimum. View HTML coverage report:
```bash
pytest --cov-report=html
open htmlcov/index.html
```

## Notes

- Tests use a separate `raimy_test` database
- Database is recreated for each test function (isolated tests)
- Authentication is mocked in integration tests
- All async tests use `pytest-asyncio`
