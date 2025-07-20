# Comprehensive Testing Guide for Ratchet Money Questionnaire

## Overview

This testing suite provides comprehensive coverage for the Ratchet Money questionnaire application, including unit tests, integration tests, user experience testing, and A/B testing framework.

## Test Structure

```
src/tests/
├── utils/
│   └── testUtils.ts          # Testing utilities and mock data generators
├── unit/
│   └── scoring.test.ts       # Unit tests for scoring algorithm and validation
├── integration/
│   └── questionnaireFlow.test.tsx  # Complete questionnaire flow tests
├── ux/
│   └── userExperience.test.tsx     # UX, accessibility, and performance tests
├── ab/
│   └── abTesting.test.tsx          # A/B testing framework tests
├── setup.ts                  # Test environment setup
├── globalSetup.ts            # Global test setup
├── globalTeardown.ts         # Global test cleanup
└── env.ts                    # Environment variables for tests
```

## Quick Start

### Installation

```bash
# Install dependencies
npm install

# Run all tests
npm test

# Run specific test types
npm run test:unit
npm run test:integration
npm run test:ux
npm run test:ab

# Run with coverage
npm run test:coverage
```

### Test Commands

| Command | Description |
|---------|-------------|
| `npm test` | Run all tests |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:coverage` | Run tests with coverage report |
| `npm run test:unit` | Run only unit tests |
| `npm run test:integration` | Run only integration tests |
| `npm run test:ux` | Run only UX tests |
| `npm run test:ab` | Run only A/B testing tests |
| `npm run test:ci` | Run tests for CI/CD |
| `npm run test:debug` | Run tests with debug info |
| `npm run test:report` | Generate and open coverage report |

## Test Categories

### 1. Unit Tests (`src/tests/unit/`)

Unit tests focus on individual functions and components in isolation.

#### Scoring Algorithm Tests
- **Purpose**: Verify scoring algorithm accuracy and edge cases
- **Coverage**: Score calculation, segment assignment, weight application
- **Key Tests**:
  - Correct score calculation for positive/negative responses
  - Weight application for different question types
  - Edge cases (empty responses, invalid weights)
  - Segment assignment based on score ranges

#### Form Validation Tests
- **Purpose**: Ensure form validation works correctly
- **Coverage**: Email validation, field validation, error handling
- **Key Tests**:
  - Email format validation
  - Required field validation
  - Age and income range validation
  - Phone number format validation

#### Local Storage Tests
- **Purpose**: Verify progress saving and recovery
- **Coverage**: Save/load functionality, data persistence
- **Key Tests**:
  - Progress saving during questionnaire
  - Progress recovery on return
  - Data expiration handling
  - Error handling for corrupted data

### 2. Integration Tests (`src/tests/integration/`)

Integration tests verify the complete user flow and component interactions.

#### Complete Questionnaire Flow
- **Purpose**: Test end-to-end questionnaire completion
- **Coverage**: Landing page → Questionnaire → Email collection → Results
- **Key Tests**:
  - Navigation from landing page to questionnaire
  - Complete question answering flow
  - Email submission and validation
  - Results display and accuracy

#### Email Submission Process
- **Purpose**: Verify email collection and processing
- **Coverage**: Form submission, API calls, error handling
- **Key Tests**:
  - Email form validation
  - API integration with email services
  - Error handling for network issues
  - Success flow and redirects

#### Analytics Integration
- **Purpose**: Ensure analytics events are properly tracked
- **Coverage**: Event firing, data accuracy, funnel tracking
- **Key Tests**:
  - Questionnaire start tracking
  - Question completion tracking
  - Email submission tracking
  - Results view tracking

### 3. User Experience Tests (`src/tests/ux/`)

UX tests focus on user experience, accessibility, and performance.

#### Cross-Browser Compatibility
- **Purpose**: Ensure consistent behavior across browsers
- **Coverage**: Chrome, Firefox, Safari, Edge
- **Key Tests**:
  - Rendering consistency
  - Functionality across browsers
  - CSS compatibility
  - JavaScript compatibility

#### Mobile Device Testing
- **Purpose**: Verify mobile responsiveness and touch interactions
- **Coverage**: iOS, Android, various screen sizes
- **Key Tests**:
  - Touch-friendly button sizes
  - Responsive design
  - Orientation handling
  - iOS Safari quirks

#### Accessibility Compliance (WCAG 2.1)
- **Purpose**: Ensure accessibility standards are met
- **Coverage**: Screen readers, keyboard navigation, color contrast
- **Key Tests**:
  - WCAG 2.1 AA compliance
  - Proper heading structure
  - Form labels and ARIA attributes
  - Keyboard navigation
  - Color contrast ratios

#### Performance Testing
- **Purpose**: Verify application performance
- **Coverage**: Load times, memory usage, bundle size
- **Key Tests**:
  - Component render times
  - Memory usage optimization
  - Bundle size analysis
  - Core Web Vitals

### 4. A/B Testing Framework (`src/tests/ab/`)

A/B testing framework for optimizing conversion rates.

#### Headline Variations
- **Purpose**: Test different headline effectiveness
- **Coverage**: Landing page headlines, results page headlines
- **Key Tests**:
  - Random variant assignment
  - Consistent user assignment
  - Conversion tracking
  - Statistical significance

#### Question Phrasing
- **Purpose**: Optimize question wording for better responses
- **Coverage**: Question text, answer options
- **Key Tests**:
  - Different question phrasings
  - Completion rate tracking
  - Time spent analysis
  - Response quality

#### Results Presentation
- **Purpose**: Test different results page layouts
- **Coverage**: Layout variations, emphasis placement
- **Key Tests**:
  - Different layout styles
  - Engagement tracking
  - Scroll depth analysis
  - CTA effectiveness

#### CTA Optimization
- **Purpose**: Optimize call-to-action buttons
- **Coverage**: Button text, placement, colors
- **Key Tests**:
  - Different CTA wordings
  - Placement variations
  - Color scheme testing
  - Click-through rates

## Testing Utilities

### Mock Data Generators

```typescript
import { 
  generateMockQuestions, 
  generateMockResponses, 
  generateMockResults,
  generateMockUser 
} from '../utils/testUtils'

// Generate test questions
const questions = generateMockQuestions(10)

// Generate test responses
const responses = generateMockResponses(questions)

// Generate test results
const results = generateMockResults({ score: 75, segment: 'stress-free' })

// Generate test user
const user = generateMockUser({ email: 'test@example.com' })
```

### Test Environment Setup

```typescript
import { setupTestEnvironment, cleanupTestEnvironment } from '../utils/testUtils'

beforeEach(() => {
  setupTestEnvironment()
})

afterEach(() => {
  cleanupTestEnvironment()
})
```

### Accessibility Testing

```typescript
import { axe, toHaveNoViolations } from 'jest-axe'

it('should meet accessibility standards', async () => {
  const { container } = render(<MyComponent />)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})
```

### Performance Testing

```typescript
import { performanceTestHelpers } from '../utils/testUtils'

it('should render quickly', async () => {
  const renderTime = await performanceTestHelpers.measureRenderTime(<MyComponent />)
  expect(renderTime).toBeLessThan(100)
})
```

## Best Practices

### Writing Unit Tests

1. **Test One Thing**: Each test should verify one specific behavior
2. **Use Descriptive Names**: Test names should clearly describe what's being tested
3. **Arrange-Act-Assert**: Structure tests with clear sections
4. **Mock External Dependencies**: Don't test external services in unit tests
5. **Test Edge Cases**: Include tests for error conditions and boundary values

```typescript
describe('calculateScore', () => {
  it('should return 0 for empty responses', () => {
    // Arrange
    const questions = generateMockQuestions()
    const responses = []
    
    // Act
    const score = calculateScore(questions, responses)
    
    // Assert
    expect(score).toBe(0)
  })
})
```

### Writing Integration Tests

1. **Test Complete Flows**: Focus on user journeys rather than individual components
2. **Use Realistic Data**: Use mock data that resembles real user data
3. **Test Error Scenarios**: Include tests for network errors and edge cases
4. **Verify Side Effects**: Check that analytics events and API calls are made
5. **Clean Up**: Ensure tests don't leave side effects

```typescript
it('should complete full questionnaire flow', async () => {
  // Complete questionnaire
  for (let i = 0; i < questions.length; i++) {
    const answerOption = screen.getByText(questions[i].options[2])
    await userEvent.click(answerOption)
  }
  
  // Submit email
  const emailInput = screen.getByLabelText(/Email/i)
  await userEvent.type(emailInput, 'test@example.com')
  await userEvent.click(screen.getByText(/Get Your Results/i))
  
  // Verify results
  await waitFor(() => {
    expect(screen.getByText(/Your Results/i)).toBeInTheDocument()
  })
})
```

### Writing UX Tests

1. **Test Real User Scenarios**: Focus on actual user interactions
2. **Verify Accessibility**: Use axe-core for accessibility testing
3. **Test Performance**: Measure render times and memory usage
4. **Cross-Browser Testing**: Test in multiple browsers
5. **Mobile Testing**: Verify mobile responsiveness

```typescript
it('should be keyboard navigable', async () => {
  render(<Questionnaire questions={questions} />)
  
  // Test keyboard navigation
  const answerOptions = screen.getAllByRole('button')
  answerOptions[0].focus()
  
  fireEvent.keyDown(answerOptions[0], { key: 'ArrowRight' })
  expect(document.activeElement).toBe(answerOptions[1])
})
```

### Writing A/B Tests

1. **Random Assignment**: Ensure users are randomly assigned to variants
2. **Consistent Assignment**: Same user should see same variant
3. **Track Conversions**: Monitor key conversion events
4. **Statistical Significance**: Use proper statistical methods
5. **Test Duration**: Run tests long enough for statistical significance

```typescript
it('should randomly assign users to variants', () => {
  const variants = new Set()
  
  for (let i = 0; i < 100; i++) {
    const { variant } = useABTest('test_id', ['A', 'B', 'C'])
    variants.add(variant)
  }
  
  expect(variants.size).toBeGreaterThan(1)
})
```

## Coverage Requirements

### Minimum Coverage Thresholds

- **Branches**: 80%
- **Functions**: 80%
- **Lines**: 80%
- **Statements**: 80%

### Coverage Reports

```bash
# Generate coverage report
npm run test:coverage

# Open coverage report in browser
npm run test:report
```

Coverage reports are generated in:
- `coverage/lcov-report/index.html` - HTML report
- `coverage/lcov.info` - LCOV format
- `coverage/coverage-final.json` - JSON format

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test:ci
      - run: npm run test:coverage
      - uses: codecov/codecov-action@v2
```

### Pre-commit Hooks

```json
{
  "husky": {
    "hooks": {
      "pre-commit": "npm run test:quick && npm run test:lint",
      "pre-push": "npm run test:all"
    }
  }
}
```

## Troubleshooting

### Common Issues

#### Tests Failing Due to Async Operations

```typescript
// Use waitFor for async operations
await waitFor(() => {
  expect(screen.getByText(/Results/i)).toBeInTheDocument()
})
```

#### Memory Leaks in Tests

```typescript
// Clean up after each test
afterEach(() => {
  cleanupTestEnvironment()
  jest.clearAllMocks()
})
```

#### Mock Not Working

```typescript
// Ensure mocks are set up before tests
beforeEach(() => {
  setupTestEnvironment()
  jest.clearAllMocks()
})
```

#### Accessibility Tests Failing

```typescript
// Check for common accessibility issues
- Missing alt attributes on images
- Missing form labels
- Improper heading structure
- Insufficient color contrast
```

### Debug Mode

```bash
# Run tests in debug mode
npm run test:debug

# Run specific test with verbose output
npm run test:verbose -- --testNamePattern="should calculate score"
```

### Performance Issues

```bash
# Run tests sequentially
npm run test:sequential

# Run tests with increased timeout
npm run test:timeout

# Clear Jest cache
npm run test:clear-cache
```

## Advanced Testing

### Visual Regression Testing

```bash
# Install visual testing tools
npm install --save-dev @percy/cli

# Run visual tests
npx percy exec -- npm run test:visual
```

### Load Testing

```bash
# Install load testing tools
npm install --save-dev artillery

# Run load tests
npm run test:load
```

### Security Testing

```bash
# Install security testing tools
npm install --save-dev snyk

# Run security tests
npm run test:security
```

## Test Data Management

### Mock Data Strategy

1. **Realistic Data**: Use data that resembles real user data
2. **Consistent Data**: Use the same test data across related tests
3. **Edge Case Data**: Include boundary values and error conditions
4. **Randomized Data**: Use randomization for A/B testing scenarios

### Database Testing

```typescript
// Use test database for integration tests
beforeAll(async () => {
  await setupTestDatabase()
})

afterAll(async () => {
  await teardownTestDatabase()
})
```

## Performance Testing

### Core Web Vitals

```typescript
// Test Core Web Vitals
it('should meet Core Web Vitals requirements', async () => {
  const metrics = await measureCoreWebVitals()
  expect(metrics.LCP).toBeLessThan(2.5)
  expect(metrics.FID).toBeLessThan(100)
  expect(metrics.CLS).toBeLessThan(0.1)
})
```

### Bundle Size Testing

```typescript
// Test bundle size
it('should maintain reasonable bundle size', () => {
  const bundleSize = getBundleSize()
  expect(bundleSize).toBeLessThan(250 * 1024) // 250KB
})
```

## Conclusion

This comprehensive testing suite ensures the Ratchet Money questionnaire application is robust, accessible, performant, and optimized for conversion. Regular testing helps maintain code quality and catch issues early in the development process.

For questions or issues with the testing suite, please refer to the troubleshooting section or create an issue in the project repository. 