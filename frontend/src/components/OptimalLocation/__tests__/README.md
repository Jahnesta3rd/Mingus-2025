# OptimalLocationRouter Testing Guide

## Overview
This directory contains comprehensive tests for the OptimalLocationRouter component, including unit tests, integration tests, and manual testing tools.

## Test Files

### 1. OptimalLocationRouter.test.tsx
**Comprehensive unit tests** covering:
- Authentication and authorization
- Component rendering and structure
- View navigation and state management
- Form interactions and API calls
- Error handling and loading states
- Accessibility features
- Mobile responsiveness
- Tier-based feature restrictions

### 2. OptimalLocationRouter.simple.test.tsx
**Basic smoke tests** for:
- Component import and basic rendering
- TypeScript type checking
- Basic functionality without complex mocking

## Manual Testing

### 1. Interactive Test Page
**File**: `../../pages/OptimalLocationTestPage.tsx`
- Live component testing with real-time controls
- Tier switching to test different user levels
- Responsive design testing
- Mock data loading for realistic testing

### 2. HTML Test Page
**File**: `../../../test/OptimalLocationTest.html`
- Standalone HTML page for manual testing
- No build process required
- Interactive tier switching
- Responsive breakpoint testing
- Real-time component state display

## Running Tests

### Unit Tests
```bash
# Run all tests
npm test

# Run specific test file
npm test -- --testPathPatterns=OptimalLocationRouter.test.tsx

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### Manual Testing
1. **Interactive Test Page**:
   - Start the dev server: `npm run dev`
   - Navigate to `/optimal-location-test`
   - Use the test controls to switch tiers and test features

2. **HTML Test Page**:
   - Open `src/test/OptimalLocationTest.html` in a browser
   - Use the tier selector to test different user levels
   - Resize the browser to test responsiveness

## Test Coverage

### Authentication & Authorization
- ✅ Unauthenticated user redirect
- ✅ Loading states during auth check
- ✅ User tier fetching and display
- ✅ Tier-based feature restrictions

### Component Rendering
- ✅ Main component structure
- ✅ Navigation tabs
- ✅ User tier badge display
- ✅ View switching

### Form Interactions
- ✅ Housing search form rendering
- ✅ Form submission handling
- ✅ Input validation
- ✅ Error display

### Error Handling
- ✅ API failure handling
- ✅ Error message display
- ✅ Retry functionality
- ✅ Graceful degradation

### Accessibility
- ✅ ARIA attributes
- ✅ Keyboard navigation
- ✅ Screen reader support
- ✅ Focus management

### Mobile Responsiveness
- ✅ Responsive breakpoints
- ✅ Touch-friendly interfaces
- ✅ Mobile navigation
- ✅ Adaptive layouts

### Tier-based Features
- ✅ Budget tier restrictions
- ✅ Mid-tier features
- ✅ Professional tier features
- ✅ Upgrade prompts

## Mock Data

The tests use comprehensive mock data including:
- **User Tiers**: All four subscription levels
- **Scenarios**: Sample location scenarios
- **Search Results**: Mock housing search results
- **API Responses**: Realistic API response mocking

## Test Utilities

### Mock Hooks
- `useAuth`: Mock authentication state
- `useAnalytics`: Mock analytics tracking
- `useNavigate`: Mock React Router navigation

### Mock APIs
- User tier fetching
- Scenario management
- Housing search
- Analytics tracking

### Test Helpers
- `TestWrapper`: React Router wrapper for tests
- `mockFetch`: Global fetch mocking
- `mockLocalStorage`: Storage mocking

## Best Practices

### Test Organization
- Group related tests in describe blocks
- Use descriptive test names
- Test one behavior per test
- Clean up after each test

### Mocking Strategy
- Mock external dependencies
- Use realistic mock data
- Test error conditions
- Verify mock calls

### Accessibility Testing
- Test keyboard navigation
- Verify ARIA attributes
- Check focus management
- Test screen reader compatibility

### Responsive Testing
- Test all breakpoints
- Verify mobile interactions
- Check touch targets
- Test adaptive layouts

## Troubleshooting

### Common Issues
1. **Jest Configuration**: Ensure proper Jest setup with jsdom environment
2. **Module Mocking**: Check that all external dependencies are properly mocked
3. **TypeScript**: Ensure proper TypeScript configuration for tests
4. **React Router**: Mock navigation hooks properly

### Debug Tips
- Use `console.log` in tests for debugging
- Check Jest configuration for proper module resolution
- Verify mock implementations match expected interfaces
- Test individual components in isolation

## Future Enhancements

### Planned Tests
- E2E tests with Playwright
- Visual regression tests
- Performance tests
- Cross-browser compatibility tests

### Test Improvements
- Better error boundary testing
- More comprehensive accessibility tests
- Integration with real API endpoints
- Automated visual testing
