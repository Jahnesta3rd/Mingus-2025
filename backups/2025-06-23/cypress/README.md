# Mingus Application - Cypress E2E Tests

This directory contains comprehensive end-to-end tests for the Mingus application, focusing on the complete user onboarding workflow.

## Test Files

### 1. `onboarding-workflow.cy.js`
**Main onboarding workflow test** - Tests the complete user journey from registration through health onboarding to dashboard access.

**Test Scenarios:**
- Complete user onboarding workflow
- Skip onboarding option
- Onboarding navigation (forward/back)
- Minimal data onboarding
- Progress tracking verification

### 2. `complete-onboarding-workflow.cy.js`
**Comprehensive onboarding test** - Extended test covering additional scenarios and edge cases.

**Test Scenarios:**
- Full user onboarding with all questionnaires
- Validation error handling
- Dashboard feature testing
- Session persistence and logout
- Career and financial questionnaires (if available)

### 3. `job-security-workflow.cy.js`
**Job security feature tests** - Tests job security monitoring and insights features.

## Prerequisites

1. **Flask Backend Running**: Ensure the Flask application is running on `http://localhost:5002`
2. **Node.js**: Version 16 or higher
3. **Cypress**: Installed as a dev dependency

## Installation

```bash
# Navigate to the cypress directory
cd cypress

# Install dependencies
npm install
```

## Running Tests

### Quick Start
```bash
# Run the main onboarding workflow test
npm run test:onboarding

# Run with browser visible (headed mode)
npm run test:onboarding:headed
```

### All Test Commands
```bash
# Open Cypress Test Runner (interactive)
npm run cypress:open

# Run all tests
npm run test:all

# Run specific test suites
npm run test:onboarding
npm run test:complete-onboarding
npm run test:job-security

# Run tests with browser visible
npm run test:headed
```

## Test Data

Test data is stored in `fixtures/onboarding-data.json` and includes:
- Sample user registration data
- Health profile information
- Financial profile data
- Career profile information

## Test Workflow

### Main Onboarding Test Flow:
1. **User Registration** - Register a new user with valid credentials
2. **Health Onboarding** - Complete the 4-step health onboarding process:
   - Step 1: Introduction and feature overview
   - Step 2: Health check-in questionnaire
   - Step 3: Timeline and reminder setup
   - Step 4: Wellness goals selection
3. **Dashboard Access** - Verify successful access to the main dashboard

### Test Features:
- **Progress Tracking** - Verifies progress bar updates correctly
- **Navigation** - Tests forward/back navigation between steps
- **Skip Functionality** - Tests the skip onboarding option
- **Minimal Data** - Tests onboarding with minimal required data
- **Error Handling** - Tests validation and error scenarios

## Configuration

The tests are configured in `cypress.config.js` with:
- Base URL: `http://localhost:5002`
- Viewport: 1280x720
- Timeouts: 10-30 seconds for various operations
- Video recording and screenshots on failure

## Troubleshooting

### Common Issues:

1. **Flask App Not Running**
   ```bash
   # Start the Flask application first
   python app.py
   ```

2. **Port Already in Use**
   ```bash
   # Kill processes on port 5002
   pkill -f "python app.py"
   ```

3. **Database Issues**
   ```bash
   # Reset database if needed
   python scripts/init_db.py
   ```

4. **Cypress Installation Issues**
   ```bash
   # Clear npm cache and reinstall
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   ```

### Debug Mode:
```bash
# Run with debug logging
DEBUG=cypress:* npm run test:onboarding
```

## Test Results

Test results are saved in:
- **Videos**: `cypress/videos/`
- **Screenshots**: `cypress/screenshots/`
- **Reports**: Generated in the terminal output

## Continuous Integration

These tests can be integrated into CI/CD pipelines. Example GitHub Actions workflow:

```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '16'
      - run: cd cypress && npm install
      - run: cd cypress && npm run test:onboarding
```

## Contributing

When adding new tests:
1. Follow the existing naming convention
2. Include comprehensive test scenarios
3. Add appropriate error handling
4. Update this README with new test descriptions
5. Ensure tests are independent and can run in any order 