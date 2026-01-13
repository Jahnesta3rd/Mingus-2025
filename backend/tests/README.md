# Backend Tests - Quick Reference

## Quick Start

```bash
# Run all tests
cd backend/tests
python run_all_tests.py

# Run with coverage
python run_all_tests.py --coverage

# Run specific test suite
python run_all_tests.py --unit-only
python run_all_tests.py --integration-only
python run_all_tests.py --security-only
python run_all_tests.py --validation-only
```

## Test Structure

- **Unit Tests**: Fast, isolated tests for validation logic
- **Integration Tests**: Tests that require API endpoints
- **Security Tests**: Tests for security vulnerabilities

## Running Individual Tests

```bash
# Run specific test file
pytest backend/tests/unit/test_validation.py

# Run specific test class
pytest backend/tests/unit/test_validation.py::TestEmailValidation

# Run specific test
pytest backend/tests/unit/test_validation.py::TestEmailValidation::test_valid_email

# Run with verbose output
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

## Test Results

- **Unit Tests**: 24 tests - All passing ✅
- **Integration Tests**: 37 tests - Ready for execution
- **Total Coverage**: Validation logic, API endpoints, security measures

## Fixtures Available

- `app`: Flask application
- `client`: Test client
- `auth_headers`: Authentication headers
- `sample_assessment_data`: Sample assessment data
- `sample_profile_data`: Sample profile data
- `sample_vehicle_data`: Sample vehicle data

## Writing New Tests

1. Place unit tests in `backend/tests/unit/`
2. Place integration tests in `backend/tests/integration/`
3. Use fixtures from `conftest.py`
4. Follow naming convention: `test_*.py` for files, `test_*` for functions

## Example Test

```python
def test_example(client, auth_headers):
    """Example test"""
    response = client.get('/api/endpoint', headers=auth_headers)
    assert response.status_code == 200
```
