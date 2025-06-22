# Mingus Application - Cypress Test Suite

This directory contains comprehensive end-to-end tests for the Mingus Flask application using Cypress.

## 🚀 Quick Start

### Prerequisites
- Node.js (v16 or higher)
- Flask application running on `http://127.0.0.1:5002`

### Installation
```bash
# Install dependencies
npm install

# Install Cypress (if not already installed)
npm install cypress --save-dev
```

### Running Tests

#### Run All Tests
```bash
# Using the test runner
node run-tests.js

# Or using Cypress directly
npx cypress run
```

#### Run Specific Test Suite
```bash
# Run only authentication tests
node run-tests.js auth

# Run only health check tests
node run-tests.js health

# Run only application health check
node run-tests.js application-health-check
```

#### Interactive Mode
```bash
# Open Cypress Test Runner
npx cypress open
```

## 📋 Test Suites

### 1. Application Health Check (`application-health-check.cy.js`)
**Purpose**: Basic connectivity and core functionality verification
- Server connectivity tests
- Authentication system validation
- API endpoint testing
- Database connectivity verification
- Frontend functionality checks
- Error handling validation
- Session management testing

### 2. Authentication Flow (`auth-flow-detailed.cy.js`)
**Purpose**: Comprehensive login/registration testing
- Login page functionality
- Registration page functionality
- Form validation testing
- API endpoint testing
- Session and cookie management
- Error scenario handling

### 3. Health & Onboarding Features (`health-onboarding-features.cy.js`)
**Purpose**: Health check-in and onboarding system validation
- Health check-in system testing
- Onboarding flow validation
- Dashboard functionality
- Health correlation features
- User management features
- Integration testing

### 4. Basic Auth Flow (Legacy) (`basic-auth-flow.cy.js`)
**Purpose**: Original basic authentication tests
- Basic login/register functionality
- Form element validation
- Navigation testing

## 🎯 What These Tests Verify

### ✅ Server & Infrastructure
- Flask server connectivity
- Database operations
- API endpoint availability
- Error handling

### ✅ Authentication System
- User registration
- User login/logout
- Session management
- Password validation
- Email validation
- Duplicate user handling

### ✅ Health & Wellness Features
- Health check-in forms
- Onboarding questionnaires
- Dashboard functionality
- Health insights generation
- Data correlation

### ✅ User Experience
- Form validation
- Navigation flows
- Responsive design
- Error messages
- Success states

### ✅ API Functionality
- RESTful endpoint testing
- Request/response validation
- Authentication requirements
- Data persistence

## 🔧 Configuration

### Base URL
The tests are configured to run against `http://127.0.0.1:5002`. To change this:

1. Update `cypress.config.js`:
```javascript
module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://your-server:port',
    // ...
  },
})
```

2. Update test files that use hardcoded URLs

### Test Data
Tests use unique email addresses to avoid conflicts:
- Format: `test{timestamp}@example.com`
- Each test generates unique identifiers
- No cleanup required (tests are independent)

## 📊 Test Results

### Success Indicators
- ✅ All API endpoints respond appropriately
- ✅ Forms submit without errors
- ✅ Navigation works correctly
- ✅ Authentication flows complete
- ✅ Database operations succeed

### Common Failure Points
- ❌ Flask server not running
- ❌ Database connection issues
- ❌ Missing form elements
- ❌ Authentication middleware problems
- ❌ CORS configuration issues

## 🐛 Debugging

### View Test Logs
```bash
# Run with verbose output
npx cypress run --spec "cypress/e2e/application-health-check.cy.js" --reporter spec
```

### Check Flask Application
```bash
# Ensure Flask app is running
python app.py

# Check logs
tail -f logs/app.log
```

### Database Issues
```bash
# Check database file
ls -la mingus.db

# Initialize database if needed
python scripts/init_db.py
```

## 📝 Adding New Tests

### Test Structure
```javascript
describe('Feature Name', () => {
  beforeEach(() => {
    // Setup
  });

  it('should do something specific', () => {
    // Test implementation
  });
});
```

### Best Practices
1. **Use unique test data** - Avoid conflicts between tests
2. **Handle failures gracefully** - Use `failOnStatusCode: false` for API tests
3. **Log responses** - Use `cy.log()` for debugging
4. **Test both success and failure cases**
5. **Keep tests independent** - Don't rely on other tests

### Example Test
```javascript
it('should handle API endpoint', () => {
  cy.request({
    method: 'POST',
    url: '/api/endpoint',
    body: { test: 'data' },
    failOnStatusCode: false
  }).then((response) => {
    cy.log(`Response status: ${response.status}`);
    expect(response.status).to.be.oneOf([200, 400, 401]);
  });
});
```

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
name: Cypress Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '16'
      - run: npm install
      - run: npm run test:cypress
```

## 📞 Support

If tests are failing:

1. **Check Flask server** - Ensure it's running on the correct port
2. **Verify database** - Check if tables exist and are accessible
3. **Review logs** - Check both Cypress and Flask application logs
4. **Test manually** - Try the same actions in a browser
5. **Update selectors** - If UI has changed, update element selectors

## 🎉 Success Criteria

Tests are considered successful when:
- ✅ All test suites pass
- ✅ No critical errors in logs
- ✅ API endpoints respond correctly
- ✅ User flows complete successfully
- ✅ Database operations work
- ✅ Authentication system functions

This test suite provides comprehensive coverage of the Mingus application's core functionality and helps ensure reliability as the application evolves. 