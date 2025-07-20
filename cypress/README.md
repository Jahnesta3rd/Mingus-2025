# Mingus Application E2E Testing

This directory contains comprehensive end-to-end tests for the Mingus financial wellness application using Cypress.

## 🚀 Quick Start

### Prerequisites
- Node.js >= 16.0.0
- Application running on `http://localhost:5002`

### Installation
```bash
npm install
```

### Running Tests
```bash
# Open Cypress Test Runner
npm run cypress:open

# Run all tests headlessly
npm run cypress:run

# Run specific test suites
npm run test:onboarding
npm run test:complete-onboarding
npm run test:job-security
npm run test:complete-journey
```

## 📋 Test Structure

### Test Files

| File | Description | Coverage |
|------|-------------|----------|
| `onboarding-workflow.cy.js` | Basic onboarding flow | Registration → Health Onboarding → Dashboard |
| `complete-onboarding-workflow.cy.js` | Extended onboarding | Registration → Health → Financial → Career → Dashboard |
| `job-security-workflow.cy.js` | Job security features | Job security assessment, goals, notifications |
| `complete-user-journey.cy.js` | **Complete user experience** | **Full journey from registration to active usage** |

### Test Data Fixtures

| File | Description |
|------|-------------|
| `onboarding-data.json` | Basic onboarding test data |
| `comprehensive-test-data.json` | **Complete user journey test data** |
| `users.json` | User account test data |
| `profile.json` | Profile information test data |

## 🎯 Complete User Journey Testing

The `complete-user-journey.cy.js` file provides comprehensive testing of the entire user experience:

### **16-Step User Journey Test**

1. **Welcome & Registration** - User registration with validation
2. **Profile Setup** - Basic demographic and financial information
3. **Baseline Assessment** - Career and financial snapshot
4. **Personalization & Goal Setting** - Smart goal configuration
5. **Education & Consent** - Privacy and terms acceptance
6. **Initial Insights** - Personalized recommendations
7. **Premium Preview** - Feature comparison and upgrade prompts
8. **App Tour** - Guided feature introduction
9. **Onboarding Completion** - Congratulations and engagement setup
10. **Dashboard Access & Usage** - Main application interface
11. **Goal Management** - Goal tracking and progress updates
12. **Insights & Recommendations** - Personalized insights
13. **Next Steps Checklist** - Actionable task management
14. **Notifications & Reminders** - Preference configuration
15. **Profile & Settings** - Account management
16. **Logout & Session Management** - Authentication flow

### **Additional Test Scenarios**

- **Error Handling** - Validation errors, network failures
- **Mobile Responsiveness** - iPhone X viewport testing
- **Accessibility** - Keyboard navigation, screen reader support

## 🛠️ Custom Commands

### Existing Commands
- `cy.registerUser(userData)` - Register new user
- `cy.loginUser(email, password)` - Login via API
- `cy.completeHealthOnboarding(healthData)` - Complete health questionnaire
- `cy.completeFinancialQuestionnaire(financialData)` - Complete financial questionnaire
- `cy.completeCareerQuestionnaire(careerData)` - Complete career questionnaire

### **New Comprehensive Commands**
- `cy.completeProfileSetup(profileData)` - Complete profile setup step
- `cy.completeBaselineAssessment(careerData, financialData)` - Complete baseline assessment
- `cy.completeGoalSetting(goalsData)` - Complete goal setting step
- `cy.completeEducationConsent()` - Complete education and consent
- `cy.completeAppTour(tourData)` - Complete app tour
- `cy.completeOnboardingCompletion(notificationData)` - Complete onboarding
- `cy.verifyDashboard()` - Verify dashboard elements
- `cy.testGoalManagement(goalData)` - Test goal management
- `cy.testInsights(insightsData)` - Test insights and recommendations
- `cy.testChecklist(checklistData)` - Test next steps checklist
- `cy.testNotifications(notificationData)` - Test notifications
- `cy.testProfileSettings(userData, profileData)` - Test profile settings
- `cy.testLogoutSession(userData)` - Test logout and session
- `cy.testErrorScenarios(errorData)` - Test error scenarios
- `cy.testMobileResponsiveness(mobileData)` - Test mobile responsiveness
- `cy.testAccessibility(accessibilityData)` - Test accessibility
- `cy.completeFullOnboarding(testData)` - Complete entire onboarding flow
- `cy.testCompleteUserJourney(testData)` - Test complete user journey

## 📊 Test Scripts

### Basic Scripts
```bash
npm run test:onboarding          # Basic onboarding flow
npm run test:complete-onboarding # Extended onboarding
npm run test:job-security        # Job security features
npm run test:complete-journey    # Complete user journey
```

### **Advanced Scripts**
```bash
npm run test:smoke               # Smoke test (main journey only)
npm run test:regression          # Error scenario testing
npm run test:mobile              # Mobile responsiveness testing
npm run test:accessibility       # Accessibility testing
npm run test:headed              # Run with browser UI
npm run test:journey:headed      # Complete journey with UI
```

### CI/CD Scripts
```bash
npm run test:ci                  # Recorded test runs
npm run test:parallel            # Parallel test execution
```

## 🔧 Configuration

### Cypress Configuration
- **Base URL**: `http://localhost:5002`
- **Viewport**: 1280x720 (desktop), iPhone X (mobile)
- **Timeouts**: 10 seconds default
- **Retries**: 2 retries on failure

### Environment Variables
```bash
CYPRESS_RECORD_KEY=your_cypress_record_key  # For CI/CD recording
CYPRESS_BASE_URL=http://localhost:5002      # Application URL
```

## 📱 Mobile Testing

The comprehensive test suite includes mobile responsiveness testing:

```javascript
// Test mobile viewport
cy.viewport('iphone-x')
cy.get('.onboarding-container').should('be.visible')
cy.viewport(1280, 720) // Reset to desktop
```

## ♿ Accessibility Testing

Basic accessibility testing is included:

```javascript
// Test keyboard navigation
cy.get('body').tab()
cy.focused().should('have.attr', 'name', 'email')

// Test ARIA labels
cy.get('input[name="email"]').should('have.attr', 'aria-label')
```

## 🚨 Error Testing

Comprehensive error scenario testing:

```javascript
// Test validation errors
cy.get('input[name="email"]').type('invalid-email')
cy.get('.error-message').should('be.visible')

// Test network errors
cy.intercept('POST', '/api/auth/register', { statusCode: 500 })
cy.get('button[type="submit"]').click()
cy.get('.error-message').should('contain', 'Something went wrong')
```

## 📈 Test Reports

### Screenshots
- Failed test screenshots saved to `cypress/screenshots/`
- Automatic screenshots on test failure

### Videos
- Test execution videos saved to `cypress/videos/`
- Videos recorded for all test runs

### CI/CD Integration
- Cypress Dashboard integration for test recording
- Parallel test execution support
- Test analytics and reporting

## 🧪 Running Specific Tests

### By Test Name
```bash
# Run specific test by name
cypress run --spec "cypress/e2e/complete-user-journey.cy.js" --grep "should complete full user journey"
```

### By Test Suite
```bash
# Run only onboarding tests
npm run test:onboarding

# Run only complete journey tests
npm run test:complete-journey
```

### Interactive Mode
```bash
# Open Cypress Test Runner
npm run cypress:open

# Select specific test file
# Click on test to run
```

## 🔄 Continuous Integration

### GitHub Actions Example
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
      - run: npm install
      - run: npm run test:smoke
```

### Parallel Execution
```bash
# Run tests in parallel with recording
npm run test:parallel
```

## 📝 Best Practices

### Test Data Management
- Use fixtures for test data
- Keep test data realistic and comprehensive
- Avoid hardcoded values in tests

### Selector Strategy
- Use data-testid attributes when possible
- Prefer semantic selectors over CSS classes
- Avoid brittle selectors that change frequently

### Test Organization
- Group related tests in describe blocks
- Use descriptive test names
- Keep tests independent and isolated

### Error Handling
- Test both happy path and error scenarios
- Verify error messages and user feedback
- Test network failures and edge cases

## 🐛 Troubleshooting

### Common Issues

1. **Application not running**
   ```bash
   # Ensure application is running on localhost:5002
   curl http://localhost:5002
   ```

2. **Test timeouts**
   ```javascript
   // Increase timeout for specific commands
   cy.get('.slow-element', { timeout: 15000 })
   ```

3. **Element not found**
   ```javascript
   // Wait for element to be visible
   cy.get('.dynamic-element').should('be.visible')
   ```

### Debug Mode
```bash
# Run with browser UI for debugging
npm run test:journey:headed
```

## 📚 Additional Resources

- [Cypress Documentation](https://docs.cypress.io/)
- [Cypress Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [Cypress Custom Commands](https://docs.cypress.io/api/cypress-api/custom-commands)
- [Cypress CI/CD](https://docs.cypress.io/guides/continuous-integration/introduction) 