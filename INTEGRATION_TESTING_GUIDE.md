# Integration Testing Guide - MINGUS Application

## Overview

This guide provides comprehensive instructions for running integration tests that connect your frontend to backend APIs and validate all test cases. The testing framework ensures end-to-end functionality and data consistency across the entire application.

## 🧪 Test Structure

### Test Organization
```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Test configuration and fixtures
├── test_auth_integration.py    # Authentication integration tests
├── test_financial_integration.py # Financial API integration tests
├── test_communication_integration.py # Communication API tests
├── test_workflows.py           # End-to-end workflow tests
└── test_api_validation.py     # API validation tests
```

### Test Categories

1. **Authentication Integration Tests** - User registration, login, token management
2. **Financial Integration Tests** - Transactions, budgets, accounts, analytics
3. **Communication Integration Tests** - Messaging, preferences, consent
4. **Workflow Tests** - Complete user journeys and business processes
5. **API Validation Tests** - Input validation, error handling, security

## 🚀 Getting Started

### Prerequisites

1. **Install Dependencies**
   ```bash
   pip install pytest pytest-cov pytest-html redis flask-testing
   ```

2. **Setup Test Environment**
   ```bash
   # Create test environment file
   cp .env.example .env.test
   
   # Configure test environment variables
   export FLASK_ENV=testing
   export TESTING=True
   export SQLALCHEMY_DATABASE_URI=sqlite:///:memory:
   export JWT_SECRET_KEY=test-secret-key
   export REDIS_URL=redis://localhost:6379/1
   ```

3. **Start Redis (for rate limiting tests)**
   ```bash
   # Install Redis if not already installed
   brew install redis  # macOS
   sudo apt-get install redis-server  # Ubuntu
   
   # Start Redis server
   redis-server
   ```

### Running Tests

#### Run All Tests
```bash
# Run all integration tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=backend --cov-report=html --cov-report=term

# Run with detailed HTML report
pytest tests/ --html=reports/test_report.html --self-contained-html
```

#### Run Specific Test Categories
```bash
# Authentication tests only
pytest tests/test_auth_integration.py -v

# Financial tests only
pytest tests/test_financial_integration.py -v

# Workflow tests only
pytest tests/test_workflows.py -v

# Run tests with specific markers
pytest tests/ -m "auth" -v
pytest tests/ -m "financial" -v
pytest tests/ -m "workflow" -v
```

#### Run Tests in Parallel
```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/ -n 4 -v
```

## 📋 Test Fixtures

### Core Fixtures

#### Application Setup
```python
@pytest.fixture(scope="session")
def app():
    """Create and configure test Flask application"""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture(scope="session")
def client(app):
    """Create test client for Flask application"""
    return app.test_client()
```

#### User Fixtures
```python
@pytest.fixture
def test_user(app, db_session, test_user_data):
    """Create a test user"""
    auth_service = AuthService()
    user = auth_service.create_user(
        email=test_user_data['email'],
        password=test_user_data['password'],
        full_name=test_user_data['full_name']
    )
    return user

@pytest.fixture
def auth_headers(test_user, app):
    """Generate authentication headers for test user"""
    access_token = create_access_token(identity=test_user.id)
    return {'Authorization': f'Bearer {access_token}'}
```

#### Data Fixtures
```python
@pytest.fixture
def test_transactions(test_user, app, db_session):
    """Create test transactions"""
    financial_service = FinancialService()
    transactions = []
    for i in range(5):
        transaction = financial_service.create_transaction(
            user_id=test_user.id,
            amount=50.00 + (i * 25.00),
            description=f'Test transaction {i+1}',
            category='Food & Dining',
            transaction_type='expense'
        )
        transactions.append(transaction)
    return transactions
```

## 🔧 Test Configuration

### Pytest Configuration
Create `pytest.ini` in your project root:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    auth: Authentication related tests
    financial: Financial API tests
    communication: Communication API tests
    workflow: End-to-end workflow tests
    slow: Slow running tests
    integration: Integration tests
```

### Test Environment Variables
```bash
# .env.test
FLASK_ENV=testing
TESTING=True
SQLALCHEMY_DATABASE_URI=sqlite:///:memory:
JWT_SECRET_KEY=test-secret-key
REDIS_URL=redis://localhost:6379/1
CORS_ORIGINS=http://localhost:3000
```

## 🧪 Writing Tests

### Authentication Test Example
```python
def test_user_registration_success(self, client, test_validation_schemas):
    """Test successful user registration"""
    registration_data = test_validation_schemas['user_registration']
    
    response = client.post('/api/v1/auth/register', 
                         json=registration_data,
                         content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    
    # Verify response structure
    assert data['success'] == True
    assert data['message'] == 'User registered successfully'
    assert 'data' in data
    assert 'user' in data['data']
    assert 'tokens' in data['data']
    
    # Verify user data
    user_data = data['data']['user']
    assert user_data['email'] == registration_data['email']
    assert user_data['full_name'] == registration_data['full_name']
```

### Financial Test Example
```python
def test_create_transaction_success(self, client, auth_headers, test_validation_schemas):
    """Test successful transaction creation"""
    transaction_data = test_validation_schemas['transaction']
    
    response = client.post('/api/v1/financial/transactions',
                         json=transaction_data,
                         headers=auth_headers,
                         content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    
    assert data['success'] == True
    assert data['message'] == 'Transaction created successfully'
    assert 'data' in data
    assert 'transaction' in data['data']
    
    transaction = data['data']['transaction']
    assert transaction['amount'] == transaction_data['amount']
    assert transaction['description'] == transaction_data['description']
```

### Workflow Test Example
```python
def test_user_onboarding_workflow(self, client, test_workflow_data):
    """Test complete user onboarding workflow"""
    workflow_data = test_workflow_data['user_onboarding']
    
    # Step 1: User Registration
    registration_data = workflow_data['registration']
    response = client.post('/api/v1/auth/register',
                         json=registration_data,
                         content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] == True
    
    # Extract tokens for subsequent requests
    tokens = data['data']['tokens']
    auth_headers = {'Authorization': f"Bearer {tokens['access_token']}"}
    
    # Step 2: Profile Update
    profile_data = workflow_data['profile_update']
    response = client.put('/api/v1/auth/profile',
                        json=profile_data,
                        headers=auth_headers,
                        content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
```

## 🔍 Test Validation

### Response Structure Validation
```python
def assert_response_structure(response_data):
    """Assert that response follows standard API structure"""
    assert 'success' in response_data
    assert 'timestamp' in response_data
    if response_data['success']:
        assert 'message' in response_data
    else:
        assert 'error' in response_data

def assert_pagination_structure(response_data):
    """Assert that paginated response has correct structure"""
    assert 'data' in response_data
    assert 'items' in response_data['data']
    assert 'meta' in response_data
    assert 'pagination' in response_data['meta']
```

### Error Response Validation
```python
def assert_validation_errors(response_data, expected_errors):
    """Assert that validation errors match expected errors"""
    assert not response_data['success']
    assert response_data['error'] == 'ValidationError'
    assert 'validation_errors' in response_data['details']
    
    actual_errors = response_data['details']['validation_errors']
    assert len(actual_errors) == len(expected_errors)
    
    for expected_error in expected_errors:
        matching_errors = [e for e in actual_errors if e['field'] == expected_error['field']]
        assert len(matching_errors) > 0
        assert matching_errors[0]['message'] == expected_error['message']
```

## 🚨 Error Handling Tests

### Rate Limiting Tests
```python
def test_rate_limiting_on_registration(self, client):
    """Test rate limiting on registration endpoint"""
    registration_data = {
        'email': 'rate_limit_test@example.com',
        'password': 'SecurePass123!',
        'full_name': 'Rate Limit Test User'
    }
    
    # Make multiple registration attempts
    responses = []
    for i in range(6):  # Exceed the 5 requests per 5 minutes limit
        data = registration_data.copy()
        data['email'] = f'rate_limit_test_{i}@example.com'
        
        response = client.post('/api/v1/auth/register',
                             json=data,
                             content_type='application/json')
        responses.append(response)
    
    # The 6th request should be rate limited
    assert responses[-1].status_code == 429
    data = json.loads(responses[-1].data)
    
    assert data['success'] == False
    assert data['error'] == 'RateLimitError'
    assert 'Rate limit exceeded' in data['message']
```

### Validation Error Tests
```python
def test_user_registration_validation_errors(self, client):
    """Test user registration with validation errors"""
    invalid_data = {
        'email': 'invalid-email',
        'password': 'weak',
        'full_name': ''
    }
    
    response = client.post('/api/v1/auth/register',
                         json=invalid_data,
                         content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    
    assert data['success'] == False
    assert data['error'] == 'ValidationError'
    assert 'validation_errors' in data['details']
    
    # Check specific validation errors
    errors = data['details']['validation_errors']
    error_fields = [error['field'] for error in errors]
    assert 'email' in error_fields
    assert 'password' in error_fields
    assert 'full_name' in error_fields
```

## 📊 Test Reporting

### Coverage Reports
```bash
# Generate HTML coverage report
pytest tests/ --cov=backend --cov-report=html

# Generate coverage report in terminal
pytest tests/ --cov=backend --cov-report=term-missing

# Generate XML coverage report for CI/CD
pytest tests/ --cov=backend --cov-report=xml
```

### HTML Test Reports
```bash
# Generate detailed HTML report
pytest tests/ --html=reports/test_report.html --self-contained-html

# Generate JUnit XML report for CI/CD
pytest tests/ --junitxml=reports/junit.xml
```

### Test Metrics
```bash
# Show test duration
pytest tests/ --durations=10

# Show slowest tests
pytest tests/ --durations=0

# Show test summary
pytest tests/ --tb=short -q
```

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-html redis
    
    - name: Run integration tests
      env:
        FLASK_ENV: testing
        TESTING: true
        SQLALCHEMY_DATABASE_URI: sqlite:///:memory:
        JWT_SECRET_KEY: test-secret-key
        REDIS_URL: redis://localhost:6379/1
      run: |
        pytest tests/ -v --cov=backend --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

## 🐛 Debugging Tests

### Debug Mode
```bash
# Run tests in debug mode
pytest tests/ -s -v

# Run specific test with debug output
pytest tests/test_auth_integration.py::TestAuthIntegration::test_user_registration_success -s -v
```

### Test Isolation
```bash
# Run tests in isolation
pytest tests/ --dist=no

# Run single test file
pytest tests/test_auth_integration.py -v

# Run single test method
pytest tests/test_auth_integration.py::TestAuthIntegration::test_user_login_success -v
```

### Database Debugging
```python
# Add to test for database debugging
def test_with_db_debug(self, client, db_session):
    # Your test code here
    
    # Debug database state
    from backend.database import db
    users = db.session.query(User).all()
    print(f"Users in database: {len(users)}")
    for user in users:
        print(f"User: {user.email}")
```

## 📈 Performance Testing

### Load Testing
```python
import time
import concurrent.futures

def test_api_performance(self, client, auth_headers):
    """Test API performance under load"""
    start_time = time.time()
    
    # Make concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(
                client.get, 
                '/api/v1/financial/transactions',
                headers=auth_headers
            )
            for _ in range(100)
        ]
        
        responses = [future.result() for future in futures]
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Verify all requests succeeded
    assert all(r.status_code == 200 for r in responses)
    
    # Verify performance (should complete within 10 seconds)
    assert duration < 10.0
    
    print(f"Processed 100 requests in {duration:.2f} seconds")
```

## 🔒 Security Testing

### Authentication Security
```python
def test_authentication_security(self, client):
    """Test authentication security measures"""
    # Test without authentication
    response = client.get('/api/v1/financial/transactions')
    assert response.status_code == 401
    
    # Test with invalid token
    response = client.get('/api/v1/financial/transactions',
                        headers={'Authorization': 'Bearer invalid_token'})
    assert response.status_code == 401
    
    # Test with expired token
    expired_token = create_access_token(identity=1, expires_delta=timedelta(seconds=-1))
    response = client.get('/api/v1/financial/transactions',
                        headers={'Authorization': f'Bearer {expired_token}'})
    assert response.status_code == 401
```

### Input Validation Security
```python
def test_sql_injection_protection(self, client, auth_headers):
    """Test SQL injection protection"""
    malicious_data = {
        'amount': "100; DROP TABLE users; --",
        'description': "'; DELETE FROM transactions; --",
        'category': "'; UPDATE users SET is_admin=1; --",
        'transaction_type': 'expense'
    }
    
    response = client.post('/api/v1/financial/transactions',
                         json=malicious_data,
                         headers=auth_headers,
                         content_type='application/json')
    
    # Should be rejected by validation, not cause SQL injection
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'ValidationError'
```

## 📝 Best Practices

### Test Organization
1. **Group related tests** in test classes
2. **Use descriptive test names** that explain the scenario
3. **Keep tests independent** - each test should be able to run in isolation
4. **Use fixtures** for common setup and teardown
5. **Test both success and failure scenarios**

### Test Data Management
1. **Use factory patterns** for creating test data
2. **Clean up test data** after each test
3. **Use realistic test data** that matches production scenarios
4. **Parameterize tests** for multiple scenarios

### Performance Considerations
1. **Use in-memory databases** for fast test execution
2. **Mock external services** to avoid network calls
3. **Run tests in parallel** when possible
4. **Monitor test execution time** and optimize slow tests

### Maintenance
1. **Update tests** when API changes
2. **Review test coverage** regularly
3. **Refactor tests** to reduce duplication
4. **Document test scenarios** for future reference

## 🎯 Test Execution Commands

### Quick Commands
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth_integration.py

# Run specific test method
pytest tests/test_auth_integration.py::TestAuthIntegration::test_user_login_success

# Run tests matching pattern
pytest -k "login"

# Run tests with specific marker
pytest -m "auth"

# Run tests excluding slow tests
pytest -m "not slow"
```

### CI/CD Commands
```bash
# Run tests with coverage for CI
pytest tests/ --cov=backend --cov-report=xml --cov-report=term-missing

# Run tests with JUnit XML output
pytest tests/ --junitxml=test-results.xml

# Run tests with HTML report
pytest tests/ --html=test-report.html --self-contained-html
```

This comprehensive testing framework ensures your MINGUS application is thoroughly tested with proper integration between frontend and backend components, validating all test cases and maintaining high code quality. 