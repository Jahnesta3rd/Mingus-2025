# MINGUS Article Library - Testing Guide

## Overview

This guide covers comprehensive testing strategies for the MINGUS Article Library functionality, including unit tests, integration tests, API tests, and end-to-end testing.

## Table of Contents

1. [Test Structure](#test-structure)
2. [Running Tests](#running-tests)
3. [Test Categories](#test-categories)
4. [Test Fixtures](#test-fixtures)
5. [Mocking and Stubbing](#mocking-and-stubbing)
6. [Coverage and Reporting](#coverage-and-reporting)
7. [Continuous Integration](#continuous-integration)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Test Structure

### Directory Organization

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_integration.py         # Integration tests
├── test_api.py                 # API endpoint tests
├── test_models.py              # Database model tests
├── test_services.py            # Service layer tests
├── test_utils.py               # Utility function tests
├── test_frontend.py            # Frontend component tests
├── fixtures/                   # Test data fixtures
│   ├── articles.json
│   ├── users.json
│   └── assessments.json
└── reports/                    # Test reports (generated)
    ├── test_report.html
    └── coverage_report.html
```

### Test File Naming Convention

- `test_*.py` - Test files
- `conftest.py` - Pytest configuration
- `*_test.py` - Alternative naming (not recommended)

## Running Tests

### Quick Start

```bash
# Run all tests
./run_tests.sh all

# Run integration tests only
./run_tests.sh integration

# Run with coverage
./run_tests.sh coverage

# Run in Docker
./run_tests.sh docker
```

### Test Runner Commands

```bash
# Basic test commands
./run_tests.sh all              # Run all tests
./run_tests.sh integration      # Integration tests
./run_tests.sh api              # API tests
./run_tests.sh database         # Database tests

# Coverage and reporting
./run_tests.sh coverage         # With coverage report
./run_tests.sh html             # With HTML report
./run_tests.sh show-coverage    # Show coverage
./run_tests.sh open-coverage    # Open coverage in browser

# Performance and parallelization
./run_tests.sh parallel         # Run in parallel
./run_tests.sh fast             # Fast tests only
./run_tests.sh slow             # Slow tests only

# Maintenance
./run_tests.sh clean            # Clean test artifacts
./run_tests.sh stats            # Show test statistics
./run_tests.sh file <filename>  # Run specific test file
```

### Direct Pytest Commands

```bash
# Run specific test file
pytest tests/test_integration.py -v

# Run specific test function
pytest tests/test_integration.py::test_article_library_integration -v

# Run tests with markers
pytest -m integration -v
pytest -m "not slow" -v

# Run with coverage
pytest --cov=backend --cov-report=html tests/

# Run in parallel
pytest -n auto tests/
```

## Test Categories

### 1. Integration Tests

Integration tests verify that different components work together correctly.

**File**: `tests/test_integration.py`

**Key Test Areas**:
- Complete article library workflow
- Assessment-based access control
- Article progress tracking
- Folder and bookmark management
- Analytics and insights
- Cultural personalization
- Advanced search features
- Export/import functionality

**Example**:
```python
def test_article_library_integration(client, auth_headers, sample_articles):
    """Test complete article library workflow"""
    
    # Test assessment creation
    response = client.post('/api/user/assessment', 
                          json={'be_score': 75, 'do_score': 65, 'have_score': 45},
                          headers=auth_headers)
    assert response.status_code == 200
    
    # Test article access based on assessment
    response = client.get('/api/articles?phase=BE&difficulty=Intermediate',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'articles' in data
```

### 2. API Tests

API tests verify that endpoints return correct responses and handle errors properly.

**Key Test Areas**:
- HTTP status codes
- Response format validation
- Error handling
- Authentication and authorization
- Rate limiting
- Input validation

**Example**:
```python
def test_article_search_api(client, auth_headers):
    """Test article search API endpoint"""
    
    # Valid search
    response = client.post('/api/articles/search',
                          json={'query': 'career advancement'},
                          headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'articles' in data
    
    # Invalid search (empty query)
    response = client.post('/api/articles/search',
                          json={'query': ''},
                          headers=auth_headers)
    assert response.status_code == 400
```

### 3. Database Tests

Database tests verify that models work correctly and data integrity is maintained.

**Key Test Areas**:
- Model creation and validation
- Relationships between models
- Database constraints
- Query performance
- Migration testing

**Example**:
```python
def test_article_model(app):
    """Test Article model functionality"""
    
    with app.app_context():
        article = Article(
            title='Test Article',
            content='Test content',
            url='https://example.com',
            source='example.com'
        )
        db.session.add(article)
        db.session.commit()
        
        assert article.id is not None
        assert article.title == 'Test Article'
```

### 4. Service Tests

Service tests verify business logic in the service layer.

**Key Test Areas**:
- AI classification service
- Recommendation engine
- Search service
- Analytics service
- Cache service

**Example**:
```python
def test_ai_classifier_service(mock_openai):
    """Test AI classification service"""
    
    service = AIClassifierService()
    result = service.classify_article({
        'title': 'Test Article',
        'content': 'Test content'
    })
    
    assert 'phase' in result
    assert 'difficulty' in result
    assert 'cultural_relevance_score' in result
```

## Test Fixtures

### Common Fixtures

Fixtures are defined in `tests/conftest.py` and provide reusable test data and setup.

```python
@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """Create a test user"""
    user = User(email='test@example.com', username='testuser')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def auth_headers(test_user, client):
    """Get authentication headers"""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}
```

### Sample Data Fixtures

```python
@pytest.fixture
def sample_articles(app):
    """Create sample articles for testing"""
    articles = []
    article_data = [
        {
            'title': 'Career Advancement Strategies',
            'content': 'This article discusses...',
            'phase': 'BE',
            'difficulty': 'Intermediate',
            'cultural_relevance_score': 8.5
        }
    ]
    
    for data in article_data:
        article = Article(**data)
        db.session.add(article)
        articles.append(article)
    
    db.session.commit()
    return articles
```

## Mocking and Stubbing

### External Service Mocking

```python
@pytest.fixture
def mock_openai():
    """Mock OpenAI API responses"""
    with patch('backend.services.ai_classifier.openai.ChatCompletion.create') as mock:
        mock.return_value = Mock(
            choices=[
                Mock(
                    message=Mock(
                        content=json.dumps({
                            'phase': 'BE',
                            'difficulty': 'Intermediate',
                            'cultural_relevance_score': 8.5
                        })
                    )
                )
            ]
        )
        yield mock

@pytest.fixture
def mock_celery():
    """Mock Celery task execution"""
    with patch('backend.celery_app.celery.delay') as mock:
        mock.return_value = Mock(id='test-task-id')
        yield mock
```

### Database Mocking

```python
@pytest.fixture
def mock_database():
    """Mock database operations"""
    with patch('backend.models.db.session') as mock_session:
        mock_session.query.return_value.filter.return_value.first.return_value = None
        yield mock_session
```

## Coverage and Reporting

### Coverage Configuration

Create `.coveragerc` file:

```ini
[run]
source = backend
omit = 
    */tests/*
    */migrations/*
    */__init__.py
    */config.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod
```

### Running Coverage

```bash
# Run tests with coverage
pytest --cov=backend --cov-report=html --cov-report=term-missing tests/

# Show coverage report
coverage report

# Generate HTML report
coverage html
```

### Coverage Targets

- **Overall Coverage**: > 90%
- **Critical Paths**: > 95%
- **API Endpoints**: > 95%
- **Service Layer**: > 90%
- **Models**: > 85%

## Continuous Integration

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-article-library-dev.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:password@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        pytest --cov=backend --cov-report=xml --cov-report=html tests/
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Best Practices

### 1. Test Organization

- **Arrange-Act-Assert**: Structure tests with clear sections
- **Descriptive Names**: Use descriptive test function names
- **Single Responsibility**: Each test should test one thing
- **Independent Tests**: Tests should not depend on each other

### 2. Test Data Management

- **Fixtures**: Use fixtures for reusable test data
- **Factory Pattern**: Use factories for complex object creation
- **Cleanup**: Always clean up test data
- **Isolation**: Each test should have its own data

### 3. Mocking Strategy

- **External Services**: Mock external API calls
- **Database**: Use test database or mock for unit tests
- **Time**: Mock time-dependent operations
- **Random**: Mock random number generation

### 4. Performance Testing

```python
def test_article_search_performance(client, auth_headers, sample_articles):
    """Test search performance"""
    
    import time
    start_time = time.time()
    
    response = client.post('/api/articles/search',
                          json={'query': 'career'},
                          headers=auth_headers)
    
    end_time = time.time()
    response_time = end_time - start_time
    
    assert response.status_code == 200
    assert response_time < 1.0  # Should complete within 1 second
```

### 5. Error Testing

```python
def test_error_handling(client, auth_headers):
    """Test error handling"""
    
    # Test invalid input
    response = client.post('/api/user/assessment', 
                          json={'be_score': 150},  # Invalid score
                          headers=auth_headers)
    assert response.status_code == 400
    
    # Test missing authentication
    response = client.get('/api/articles')
    assert response.status_code == 401
    
    # Test resource not found
    response = client.get('/api/articles/999999', headers=auth_headers)
    assert response.status_code == 404
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check database configuration
export DATABASE_URL="postgresql://user:password@localhost:5432/test_db"

# Reset test database
pytest --reuse-db tests/
```

#### 2. Import Errors

```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install in development mode
pip install -e .
```

#### 3. Mock Issues

```python
# Ensure proper import path for mocking
from unittest.mock import patch

# Mock the correct import path
@patch('backend.services.ai_classifier.openai.ChatCompletion.create')
def test_ai_classifier(mock_openai):
    # Test implementation
    pass
```

#### 4. Slow Tests

```bash
# Run only fast tests
pytest -m "not slow" tests/

# Run tests in parallel
pytest -n auto tests/

# Profile slow tests
pytest --durations=10 tests/
```

### Debugging Tests

```python
# Add debugging to tests
def test_debug_example(client, auth_headers):
    response = client.get('/api/articles', headers=auth_headers)
    
    # Debug response
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.get_json()}")
    
    # Use pdb for interactive debugging
    import pdb; pdb.set_trace()
    
    assert response.status_code == 200
```

### Test Logging

```python
# Enable test logging
import logging

def test_with_logging(client, auth_headers):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    logger.debug("Starting test")
    response = client.get('/api/articles', headers=auth_headers)
    logger.debug(f"Response: {response.status_code}")
    
    assert response.status_code == 200
```

## Next Steps

1. **Add More Tests**: Expand test coverage for edge cases
2. **Performance Tests**: Add load testing for critical endpoints
3. **Security Tests**: Add security vulnerability testing
4. **End-to-End Tests**: Add browser automation tests
5. **Mutation Testing**: Add mutation testing for better test quality
6. **Test Documentation**: Document test scenarios and expected outcomes
