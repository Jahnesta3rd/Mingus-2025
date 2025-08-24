# Meme Splash Page Testing Suite

A comprehensive testing suite for the Meme Splash Page feature in the MINGUS application. This suite includes unit tests, integration tests, performance tests, and automated CI/CD pipelines.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Getting Started](#getting-started)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [CI/CD Pipeline](#cicd-pipeline)
- [Test Data](#test-data)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Meme Splash Page testing suite provides comprehensive coverage for:

- **Backend Services**: MemeService, API endpoints, database operations
- **Frontend Components**: React components, user interactions, accessibility
- **Integration**: End-to-end user flows, API integration
- **Performance**: Load testing, memory usage, response times
- **Security**: Vulnerability scanning, input validation
- **Accessibility**: Screen reader support, keyboard navigation

## 🏗️ Test Structure

```
tests/meme_splash_page/
├── __init__.py
├── conftest.py                    # Pytest fixtures and configuration
├── test_meme_service_unit.py      # Backend service unit tests
├── test_meme_api_endpoints.py     # API endpoint tests
├── test_meme_integration.py       # Integration tests
├── test_meme_performance.py       # Performance tests
├── run_tests.py                   # Test runner script
└── README.md                      # This documentation

components/__tests__/
└── MemeSplashPage.test.tsx        # Frontend component tests

.github/workflows/
└── meme-splash-page-tests.yml     # CI/CD pipeline
```

## 🚀 Getting Started

### Prerequisites

1. **Python Environment**
   ```bash
   python 3.8+
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Node.js Environment**
   ```bash
   node 16+
   npm install
   ```

3. **Database**
   ```bash
   # For local testing (SQLite)
   # No setup required - uses in-memory database
   
   # For integration testing (PostgreSQL)
   docker run -d --name test-postgres \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=test_db \
     -p 5432:5432 \
     postgres:13
   ```

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mingus-application
   ```

2. **Install dependencies**
   ```bash
   # Python dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   
   # Node.js dependencies
   npm install
   ```

3. **Setup test environment**
   ```bash
   export TESTING=true
   export FLASK_ENV=testing
   export DATABASE_URL=sqlite:///:memory:
   ```

## 🧪 Running Tests

### Quick Start

Run all tests with the test runner:
```bash
python tests/meme_splash_page/run_tests.py
```

### Individual Test Categories

#### Backend Tests
```bash
# Unit tests only
python tests/meme_splash_page/run_tests.py --backend

# Specific test file
pytest tests/meme_splash_page/test_meme_service_unit.py -v

# With coverage
pytest tests/meme_splash_page/test_meme_service_unit.py --cov=backend/services/meme_service --cov-report=html
```

#### Frontend Tests
```bash
# Frontend tests only
python tests/meme_splash_page/run_tests.py --frontend

# Direct npm command
npm test -- --testPathPattern="MemeSplashPage.test.tsx" --coverage --watchAll=false
```

#### Performance Tests
```bash
# Performance tests only
python tests/meme_splash_page/run_tests.py --performance

# Direct pytest command
pytest tests/meme_splash_page/test_meme_performance.py -v
```

#### Security Tests
```bash
# Security tests only
python tests/meme_splash_page/run_tests.py --security

# Manual security scan
bandit -r backend/routes/meme_routes.py backend/services/meme_service.py
safety check
```

### Advanced Options

```bash
# Verbose output
python tests/meme_splash_page/run_tests.py --verbose

# Quick tests (skip performance tests)
python tests/meme_splash_page/run_tests.py --quick

# Run specific test categories
python tests/meme_splash_page/run_tests.py --backend --frontend
```

## 📊 Test Categories

### 1. Backend Unit Tests (`test_meme_service_unit.py`)

Tests the core business logic of the MemeService class:

- **Meme Operations**: Create, read, update, delete memes
- **User Preferences**: Manage user meme preferences
- **Analytics**: Track user interactions and engagement
- **Caching**: Test caching behavior and performance
- **Error Handling**: Database errors, invalid inputs
- **Edge Cases**: Empty datasets, boundary conditions

**Example Test:**
```python
def test_select_best_meme_for_user_success(self, meme_service, sample_user, sample_user_preferences, sample_memes):
    """Test successful meme selection"""
    meme = meme_service.select_best_meme_for_user(sample_user.id)
    
    assert meme is not None
    assert 'id' in meme
    assert 'image' in meme
    assert 'caption' in meme
    assert 'category' in meme
```

### 2. API Endpoint Tests (`test_meme_api_endpoints.py`)

Tests the Flask API endpoints:

- **Authentication**: User authorization and session management
- **Request Validation**: Input validation and error handling
- **Response Format**: JSON response structure and status codes
- **Rate Limiting**: API rate limiting behavior
- **CORS**: Cross-origin resource sharing
- **Error Responses**: Proper error status codes and messages

**Example Test:**
```python
def test_get_user_meme_success(self, test_client, mock_flask_session, sample_meme_data):
    """Test successful GET /api/user-meme/<user_id>"""
    response = test_client.get('/api/user-meme/123')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'meme' in data
```

### 3. Integration Tests (`test_meme_integration.py`)

Tests complete user workflows:

- **User Flow**: Login → Meme Display → Interaction → Dashboard
- **Data Consistency**: Database state across operations
- **Concurrent Users**: Multiple users accessing simultaneously
- **Error Recovery**: System recovery after failures
- **Performance**: Response times under load

**Example Test:**
```python
def test_complete_user_flow_with_meme(self, test_client, db_session, sample_user, sample_memes):
    """Test complete user flow from login to dashboard with meme interaction"""
    # Step 1: User logs in and gets redirected to meme splash
    response = test_client.get('/api/user-meme/123')
    assert response.status_code == 200
    
    # Step 2: User views the meme (analytics tracked)
    # Step 3: User continues to dashboard
    # Step 4: Verify analytics were recorded
```

### 4. Performance Tests (`test_meme_performance.py`)

Tests system performance characteristics:

- **Response Times**: API response time under various loads
- **Memory Usage**: Memory consumption during operations
- **Database Performance**: Query execution times
- **Concurrent Users**: System behavior with multiple users
- **Caching Effectiveness**: Cache hit/miss ratios
- **Resource Usage**: CPU, disk I/O, network usage

**Example Test:**
```python
def test_meme_loading_speed(self, test_client, db_session, sample_user, sample_memes):
    """Test meme loading speed under normal conditions"""
    start_time = time.time()
    response = test_client.get('/api/user-meme/123')
    end_time = time.time()
    
    response_time = end_time - start_time
    assert response_time < 0.5, f"Meme loading took {response_time:.3f}s, expected < 0.5s"
```

### 5. Frontend Tests (`MemeSplashPage.test.tsx`)

Tests React component behavior:

- **Component Rendering**: Proper display of memes and UI elements
- **User Interactions**: Button clicks, keyboard navigation
- **State Management**: Loading, error, and success states
- **Accessibility**: ARIA labels, keyboard navigation, screen readers
- **Error Handling**: Network errors, invalid data
- **Analytics Tracking**: User interaction tracking

**Example Test:**
```typescript
it('should display meme when loaded successfully', async () => {
  render(<MemeSplashPage />);

  await waitFor(() => {
    expect(screen.getByText('Test meme caption')).toBeInTheDocument();
  });

  expect(screen.getByAltText('A funny meme about work life balance')).toBeInTheDocument();
});
```

## 🔄 CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/meme-splash-page-tests.yml`) provides:

### Automated Testing
- **Triggers**: Push to main/develop, pull requests, daily schedule
- **Matrix Testing**: Multiple Python versions and databases
- **Parallel Execution**: Tests run in parallel for faster feedback
- **Artifact Collection**: Test reports, coverage, and logs

### Test Jobs
1. **Backend Unit Tests**: Service layer testing
2. **Backend API Tests**: Endpoint testing
3. **Frontend Tests**: Component testing
4. **Integration Tests**: End-to-end workflows
5. **Performance Tests**: Load and stress testing
6. **Security Tests**: Vulnerability scanning
7. **Accessibility Tests**: A11y compliance
8. **E2E Tests**: Full application testing

### Deployment
- **Staging**: Automatic deployment to staging environment
- **Production**: Manual deployment after staging validation
- **Rollback**: Automatic rollback on test failures

## 📈 Test Data

### Sample Data Fixtures

The test suite includes comprehensive sample data:

```python
# Sample memes
sample_memes = [
    {
        'id': 'meme-1',
        'image_url': 'https://example.com/meme1.jpg',
        'category': 'monday_career',
        'caption_text': 'Monday motivation: Building wealth one paycheck at a time',
        'alt_text': 'A person in business attire flexing muscles',
        'priority': 9,
        'is_active': True,
        'engagement_score': 0.8
    },
    # ... more memes
]

# Sample user preferences
sample_user_preferences = {
    'memes_enabled': True,
    'preferred_categories': ['monday_career', 'tuesday_health'],
    'frequency_setting': 'daily',
    'custom_frequency_days': 1
}
```

### Test Categories
- **Valid Data**: Normal operation scenarios
- **Edge Cases**: Boundary conditions and limits
- **Invalid Data**: Error handling scenarios
- **Large Datasets**: Performance testing data
- **Security Test Data**: Injection attempts, malicious inputs

## 🎯 Best Practices

### Writing Tests

1. **Test Structure**
   ```python
   def test_feature_name(self, fixture1, fixture2):
       """Test description - what is being tested and expected outcome"""
       # Arrange - setup test data
       # Act - perform the action
       # Assert - verify the result
   ```

2. **Naming Conventions**
   - Test methods: `test_<feature>_<scenario>`
   - Fixtures: `sample_<entity>`
   - Variables: descriptive names

3. **Assertions**
   - Use specific assertions
   - Include meaningful error messages
   - Test both positive and negative cases

### Test Organization

1. **Group Related Tests**
   ```python
   class TestMemeService:
       def test_create_meme(self):
           pass
       
       def test_get_meme_by_id(self):
           pass
   ```

2. **Use Descriptive Test Names**
   ```python
   def test_select_best_meme_for_user_when_user_has_opted_out(self):
       pass
   ```

3. **Keep Tests Independent**
   - Each test should be self-contained
   - Use fixtures for shared data
   - Clean up after tests

### Performance Testing

1. **Baseline Measurements**
   - Establish performance baselines
   - Monitor for regressions
   - Set realistic thresholds

2. **Load Testing**
   - Test with realistic user loads
   - Monitor resource usage
   - Identify bottlenecks

3. **Continuous Monitoring**
   - Track performance over time
   - Alert on performance degradation
   - Maintain performance dashboards

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database URL
   echo $DATABASE_URL
   
   # Test database connection
   python -c "from backend.database import get_db_session; print('DB OK')"
   ```

2. **Import Errors**
   ```bash
   # Add project root to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   
   # Install missing dependencies
   pip install -r requirements-dev.txt
   ```

3. **Node.js Issues**
   ```bash
   # Clear npm cache
   npm cache clean --force
   
   # Reinstall dependencies
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Test Failures**
   ```bash
   # Run with verbose output
   pytest -v --tb=long
   
   # Run specific failing test
   pytest tests/meme_splash_page/test_meme_service_unit.py::TestMemeService::test_specific_method -v
   ```

### Debug Mode

Enable debug mode for detailed output:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python tests/meme_splash_page/run_tests.py --verbose
```

### Coverage Reports

Generate detailed coverage reports:
```bash
# HTML coverage report
pytest --cov=backend --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## 🤝 Contributing

When adding new tests:

1. Follow the existing test structure
2. Add appropriate fixtures in `conftest.py`
3. Update this documentation
4. Ensure CI/CD pipeline passes
5. Add test data for new scenarios

## 📞 Support

For questions or issues with the testing suite:

1. Check the troubleshooting section
2. Review existing test examples
3. Create an issue with detailed error information
4. Include test logs and environment details
