# Email Verification System Test Suite

## Overview

This comprehensive test suite covers all aspects of the email verification system in Mingus, ensuring 94%+ code coverage and comprehensive testing of security, performance, and functionality.

## Test Categories

### 1. Unit Tests (`test_email_verification_comprehensive.py`)
- **Model Tests**: EmailVerification model functionality, properties, and methods
- **Service Tests**: EmailVerificationService business logic and operations
- **Task Tests**: Celery task functionality and error handling
- **Security Tests**: Token generation, validation, and attack prevention
- **Performance Tests**: Token generation speed, database operations, memory usage

### 2. Rate Limiting Tests (`test_email_verification_rate_limiting.py`)
- **Rate Limiting Mechanisms**: User-based, IP-based, and global rate limiting
- **Recovery Mechanisms**: Lockout expiration and cooldown periods
- **Configuration Tests**: Configurable limits and dynamic rate limiting
- **Monitoring Tests**: Metrics collection, alerting, and reporting
- **Integration Tests**: Rate limiting with authentication and audit systems

### 3. Email Template Tests (`test_email_verification_templates.py`)
- **Template Rendering**: Basic template functionality and variable substitution
- **Security Tests**: XSS prevention, template injection protection, HTML encoding
- **Content Validation**: Email structure, accessibility, and localization support
- **Integration Tests**: Template integration with services and error handling
- **Performance Tests**: Template rendering speed and memory usage

### 4. Database Migration Tests (`test_email_verification_migrations.py`)
- **Schema Creation**: Table structure, columns, constraints, and indexes
- **Migration Validation**: Upgrade paths, rollback simulation, and data consistency
- **Performance Tests**: Index performance, bulk operations, and concurrency
- **Backup & Recovery**: Schema backup, data recovery, and integrity verification

## Prerequisites

### Required Dependencies
```bash
pip install -r requirements-testing.txt
```

### Required Packages
- pytest >= 7.0.0
- pytest-cov
- pytest-html
- pytest-xdist (for parallel execution)
- sqlalchemy
- flask
- redis (for rate limiting tests)
- jinja2 (for template tests)

### Environment Variables
```bash
export FLASK_ENV=testing
export PYTHONPATH=backend:frontend
export EMAIL_VERIFICATION_SECRET=test-secret-key
export REDIS_URL=redis://localhost:6379/1
```

## Test Execution

### 1. Run All Tests
```bash
# From project root
python backend/tests/test_email_verification_runner.py

# Or using pytest directly
pytest backend/tests/ -v --tb=short
```

### 2. Run Specific Test Categories
```bash
# Unit tests only
pytest backend/tests/test_email_verification_comprehensive.py -v

# Rate limiting tests only
pytest backend/tests/test_email_verification_rate_limiting.py -v

# Template tests only
pytest backend/tests/test_email_verification_templates.py -v

# Migration tests only
pytest backend/tests/test_email_verification_migrations.py -v
```

### 3. Run Tests by Marker
```bash
# Security tests only
pytest -m security -v

# Performance tests only
pytest -m performance -v

# Integration tests only
pytest -m integration -v

# Unit tests only
pytest -m unit -v
```

### 4. Run Tests with Coverage
```bash
# Comprehensive coverage report
pytest backend/tests/test_email_verification_comprehensive.py \
    --cov=backend.services.email_verification_service \
    --cov=backend.models.email_verification \
    --cov=backend.tasks.email_verification_tasks \
    --cov-report=html:reports/coverage \
    --cov-report=term-missing \
    --cov-fail-under=94
```

### 5. Parallel Execution
```bash
# Run tests in parallel (requires pytest-xdist)
pytest backend/tests/ -n auto -v
```

## Test Configuration

### Pytest Configuration
The test suite uses the existing `pytest.ini` configuration with additional markers:

```ini
[tool:pytest]
markers =
    unit: marks tests as unit tests
    integration: marks tests as integration tests
    security: marks tests as security tests
    performance: marks tests as performance tests
    rate_limiting: marks tests as rate limiting tests
    templates: marks tests as template tests
    migrations: marks tests as migration tests
    slow: marks tests as slow running
```

### Test Fixtures
The test suite provides comprehensive fixtures in `conftest_email_verification.py`:

- **Database Fixtures**: In-memory SQLite database with proper setup/teardown
- **Mock Services**: Email service, Redis, metrics, audit, and notification mocks
- **Test Data**: Factory functions for generating test users and verifications
- **Security Fixtures**: Malicious input data and rate limiting scenarios
- **Template Fixtures**: Sample email templates for testing

## Test Data and Factories

### Test Data Generation
```python
@pytest.fixture
def test_data_factory():
    """Factory for generating test data"""
    def create_test_user(user_id, email, **kwargs):
        return User(
            id=user_id,
            email=email,
            first_name=f'Test{user_id}',
            last_name=f'User{user_id}',
            # ... other fields
        )
    
    def create_test_verification(user_id, email, **kwargs):
        return EmailVerification(
            user_id=user_id,
            email=email,
            verification_token_hash=f'hash_{user_id}',
            # ... other fields
        )
    
    return {
        'create_user': create_test_user,
        'create_verification': create_test_verification
    }
```

### Using Test Factories
```python
def test_bulk_operations(test_data_factory):
    # Create 1000 test users
    users = []
    for i in range(1000):
        user = test_data_factory['create_user'](
            i, f'user{i}@example.com',
            subscription_tier='premium'
        )
        users.append(user)
    
    # Create corresponding verifications
    verifications = []
    for user in users:
        verification = test_data_factory['create_verification'](
            user.id, user.email,
            verification_type='signup'
        )
        verifications.append(verification)
```

## Security Testing

### XSS Prevention Tests
```python
def test_xss_prevention_in_templates(email_templates):
    """Test XSS prevention in email templates"""
    template = Template(email_templates['verification'])
    
    # Malicious data that could cause XSS
    malicious_data = {
        'user': Mock(full_name='<script>alert("xss")</script>'),
        'verification_url': 'javascript:alert("xss")',
        'expiry_hours': 24
    }
    
    rendered = template.render(**malicious_data)
    
    # Script tags should be escaped
    assert '<script>' not in rendered
    assert 'javascript:' not in rendered
```

### SQL Injection Prevention Tests
```python
def test_sql_injection_prevention(test_db):
    """Test SQL injection prevention in queries"""
    malicious_email = "'; DROP TABLE users; --"
    
    # Should not cause SQL injection
    verification = EmailVerification(
        user_id=1,
        email=malicious_email,
        verification_token_hash='safe_hash',
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    # Should be able to save without issues
    test_db.add(verification)
    test_db.commit()
```

### Timing Attack Prevention Tests
```python
def test_timing_attack_prevention(test_db):
    """Test that token verification prevents timing attacks"""
    verification = EmailVerification(
        expires_at=datetime.utcnow() + timedelta(hours=1),
        verified_at=None
    )
    
    # Both valid and invalid tokens should take similar time
    start_time = time.time()
    verification.verify_token('valid_token')
    valid_time = time.time() - start_time
    
    start_time = time.time()
    verification.verify_token('invalid_token')
    invalid_time = time.time() - start_time
    
    # Times should be very similar (within 10ms)
    time_diff = abs(valid_time - invalid_time)
    assert time_diff < 0.01
```

## Performance Testing

### Token Generation Performance
```python
def test_token_generation_speed(test_db):
    """Test token generation performance"""
    start_time = time.time()
    
    # Generate 1000 tokens
    for _ in range(1000):
        EmailVerification.create_verification(1, 'test@example.com', 'signup')
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Should generate 1000 tokens in under 1 second
    assert total_time < 1.0
```

### Database Query Performance
```python
def test_database_query_performance(test_db, test_data_factory):
    """Test database query performance with large datasets"""
    # Create 1000 test users and verifications
    users = []
    verifications = []
    
    for i in range(1000):
        user = test_data_factory['create_user'](i, f'user{i}@example.com')
        users.append(user)
        
        verification = test_data_factory['create_verification'](i, f'user{i}@example.com')
        verifications.append(verification)
    
    test_db.add_all(users)
    test_db.add_all(verifications)
    test_db.commit()
    
    # Test query performance with index
    start_time = time.time()
    result = test_db.query(EmailVerification).filter_by(email='user500@example.com').first()
    query_time = time.time() - start_time
    
    assert result is not None
    assert query_time < 0.1  # Should be very fast with index
```

## Rate Limiting Testing

### Rate Limit Scenarios
```python
@pytest.fixture
def rate_limit_scenarios():
    """Rate limiting test scenarios"""
    return {
        'normal_user': {
            'requests_per_minute': 5,
            'burst_limit': 10,
            'expected_result': 'allowed'
        },
        'suspicious_user': {
            'requests_per_minute': 50,
            'burst_limit': 100,
            'expected_result': 'rate_limited'
        },
        'malicious_user': {
            'requests_per_minute': 500,
            'burst_limit': 1000,
            'expected_result': 'blocked'
        }
    }
```

### Testing Rate Limit Mechanisms
```python
def test_verification_creation_rate_limit(test_db, mock_redis):
    """Test rate limiting on verification creation"""
    service = EmailVerificationService()
    
    # Mock Redis rate limiting
    with patch('backend.services.email_verification_service.redis_client') as mock_redis_client:
        mock_redis_client.incr.return_value = 1
        mock_redis_client.get.return_value = None
        
        # First verification should succeed
        verification1, token1 = service.create_verification(
            1, 'test@example.com', 'signup'
        )
        assert verification1 is not None
        
        # Mock rate limit exceeded
        mock_redis_client.incr.return_value = 6  # Over limit
        
        # Should be rate limited
        with pytest.raises(Exception) as exc_info:
            service.create_verification(1, 'test@example.com', 'signup')
        
        assert 'rate limit' in str(exc_info.value).lower()
```

## Coverage Requirements

### Minimum Coverage Thresholds
- **Statements**: 94%
- **Branches**: 90%
- **Functions**: 94%
- **Lines**: 94%

### Coverage Commands
```bash
# Generate coverage report
pytest --cov=backend --cov-report=html:reports/coverage --cov-fail-under=94

# View coverage in terminal
pytest --cov=backend --cov-report=term-missing --cov-fail-under=94

# Generate coverage JSON for CI/CD
pytest --cov=backend --cov-report=json:reports/coverage.json --cov-fail-under=94
```

## Test Reports

### HTML Reports
The test suite generates comprehensive HTML reports:

- **Individual Test Reports**: One report per test file
- **Coverage Reports**: Detailed coverage analysis with line-by-line breakdown
- **Final Summary Report**: Overall test results with recommendations

### JSON Reports
```bash
# Generate JSON reports for CI/CD integration
pytest --junitxml=reports/junit.xml \
       --cov-report=json:reports/coverage.json \
       --html=reports/test_report.html
```

### Report Locations
```
reports/
├── coverage_html/           # Coverage HTML report
├── coverage.json           # Coverage JSON data
├── email_verification_test_report.html  # Final HTML report
├── email_verification_test_report.json  # Final JSON report
├── test_email_verification_comprehensive_report.html
├── test_email_verification_rate_limiting_report.html
├── test_email_verification_templates_report.html
└── test_email_verification_migrations_report.html
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Email Verification Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements-testing.txt
    
    - name: Run tests
      run: |
        python backend/tests/test_email_verification_runner.py --verbose
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v1
      with:
        file: reports/coverage.json
        flags: email-verification
        name: email-verification-coverage
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: email-verification-tests
        name: Email Verification Tests
        entry: python backend/tests/test_email_verification_runner.py
        language: system
        types: [python]
        stages: [commit]
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure PYTHONPATH is set correctly
export PYTHONPATH=backend:frontend

# Or run from project root
cd /path/to/mingus
python -m pytest backend/tests/
```

#### 2. Database Connection Issues
```bash
# Check database configuration
export SQLALCHEMY_DATABASE_URI=sqlite:///:memory:

# Ensure test database is created
pytest --setup-show backend/tests/
```

#### 3. Mock Service Issues
```bash
# Check mock configurations
pytest -s backend/tests/ -k "test_mock"

# Verify service imports
python -c "from backend.services.email_verification_service import EmailVerificationService"
```

#### 4. Coverage Issues
```bash
# Check coverage configuration
pytest --cov=backend --cov-report=term-missing --cov-fail-under=94

# Generate detailed coverage report
pytest --cov=backend --cov-report=html:reports/coverage --cov-fail-under=94
```

### Debug Mode
```bash
# Run tests with debug output
pytest -s -v --tb=long backend/tests/

# Run specific test with debug
pytest -s -v --tb=long backend/tests/test_email_verification_comprehensive.py::TestEmailVerificationModel::test_create_verification_success
```

## Best Practices

### 1. Test Organization
- Group related tests in test classes
- Use descriptive test method names
- Follow AAA pattern (Arrange, Act, Assert)

### 2. Mock Usage
- Mock external dependencies (email services, Redis, etc.)
- Use realistic mock responses
- Verify mock calls when appropriate

### 3. Test Data
- Use factories for generating test data
- Create realistic test scenarios
- Clean up test data after each test

### 4. Performance Testing
- Set realistic performance thresholds
- Test with realistic data volumes
- Monitor memory usage and cleanup

### 5. Security Testing
- Test all input validation
- Verify attack prevention mechanisms
- Test rate limiting and abuse prevention

## Contributing

### Adding New Tests
1. Follow existing test patterns and naming conventions
2. Add appropriate markers for test categorization
3. Ensure tests meet coverage requirements
4. Update this README if adding new test categories

### Test Review Process
1. All tests must pass locally
2. Coverage must meet minimum thresholds
3. Security tests must pass
4. Performance tests must meet thresholds
5. Tests must be properly documented

## Support

For questions or issues with the test suite:

1. Check this README for common solutions
2. Review test output and error messages
3. Check pytest documentation for general issues
4. Contact the development team for specific Mingus issues

## License

This test suite is part of the Mingus application and follows the same licensing terms.
