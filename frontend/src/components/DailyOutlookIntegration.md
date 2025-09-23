# DailyOutlook Integration Guide

This guide shows how to integrate the DailyOutlook component into your existing MINGUS application.

## Quick Integration

### 1. Basic Dashboard Integration

```tsx
import React from 'react';
import DailyOutlook from './components/DailyOutlook';
import { AuthProvider } from './hooks/useAuth';

function Dashboard() {
  return (
    <AuthProvider>
      <div className="container mx-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Daily Outlook - Takes up 1/3 of the width on large screens */}
          <div className="lg:col-span-1">
            <DailyOutlook />
          </div>
          
          {/* Other dashboard components */}
          <div className="lg:col-span-2">
            {/* Your existing dashboard content */}
          </div>
        </div>
      </div>
    </AuthProvider>
  );
}
```

### 2. Mobile-First Layout

```tsx
function MobileDashboard() {
  return (
    <div className="space-y-6 p-4">
      {/* Daily Outlook at the top for mobile */}
      <DailyOutlook />
      
      {/* Other components stack below */}
      <div className="space-y-4">
        {/* Additional dashboard components */}
      </div>
    </div>
  );
}
```

### 3. With Custom Styling

```tsx
function StyledDashboard() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto p-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
            {/* Daily Outlook with custom styling */}
            <div className="xl:col-span-1">
              <DailyOutlook className="sticky top-6 shadow-xl" />
            </div>
            
            {/* Main content area */}
            <div className="xl:col-span-3">
              {/* Your main dashboard content */}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

## API Setup

### Required Backend Endpoints

The DailyOutlook component expects these API endpoints to be available:

#### 1. Daily Outlook Data
```typescript
GET /api/daily-outlook
Authorization: Bearer <token>

Response:
{
  "user_name": "John Doe",
  "current_time": "9:30 AM",
  "balance_score": {
    "value": 85,
    "trend": "up",
    "change_percentage": 5.2,
    "previous_value": 81
  },
  "primary_insight": {
    "title": "Great Progress!",
    "message": "Your financial health is improving steadily. Keep up the great work!",
    "type": "positive",
    "icon": "sun"
  },
  "quick_actions": [
    {
      "id": "action_1",
      "title": "Review Budget",
      "description": "Check your monthly budget and make adjustments",
      "completed": false,
      "priority": "high",
      "estimated_time": "5 min"
    }
  ],
  "encouragement_message": {
    "text": "You're doing amazing! Every small step counts towards your financial goals.",
    "type": "motivational",
    "emoji": "🎉"
  },
  "streak_data": {
    "current_streak": 7,
    "longest_streak": 15,
    "milestone_reached": false,
    "next_milestone": 10,
    "progress_percentage": 70
  },
  "tomorrow_teaser": {
    "title": "New Investment Opportunity",
    "description": "We've found a potential investment that matches your risk profile.",
    "excitement_level": 4
  },
  "user_tier": "mid_tier"
}
```

#### 2. Action Completion
```typescript
POST /api/daily-outlook/actions
Authorization: Bearer <token>
Content-Type: application/json

{
  "action_id": "action_1",
  "completed": true
}
```

#### 3. Rating Submission
```typescript
POST /api/daily-outlook/rating
Authorization: Bearer <token>
Content-Type: application/json

{
  "rating": 4,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Styling Integration

### Using Existing Design System

The component follows the existing MINGUS design patterns:

```tsx
// The component automatically uses your existing Tailwind configuration
<DailyOutlook className="shadow-lg border border-gray-200" />
```

### Custom Theme Integration

```tsx
// You can override specific styles using Tailwind classes
<DailyOutlook className="bg-gradient-to-br from-blue-50 to-indigo-100" />
```

## State Management Integration

### With Zustand Store

```tsx
import { useDashboardStore } from '../stores/dashboardStore';

function DashboardWithStore() {
  const { userTier, updateUserTier } = useDashboardStore();
  
  return (
    <div>
      <DailyOutlook />
      {/* Component automatically uses auth context */}
    </div>
  );
}
```

### With Redux

```tsx
import { useSelector } from 'react-redux';

function DashboardWithRedux() {
  const user = useSelector(state => state.auth.user);
  
  return (
    <div>
      <DailyOutlook />
      {/* Component handles its own state management */}
    </div>
  );
}
```

## Error Handling

### Global Error Boundary

```tsx
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Dashboard />
      </AuthProvider>
    </ErrorBoundary>
  );
}
```

### Component-Level Error Handling

The DailyOutlook component includes built-in error handling:

- **Network Errors**: Automatic retry with user feedback
- **API Errors**: Graceful degradation with error messages
- **Loading States**: Skeleton animations during data fetching
- **User Feedback**: Clear error messages with retry options

## Analytics Integration

### Automatic Tracking

The component automatically tracks:

- Page views and component loads
- User interactions (clicks, ratings, shares)
- Error occurrences and stack traces
- Performance metrics and timing

### Custom Analytics

```tsx
import { useAnalytics } from '../hooks/useAnalytics';

function DashboardWithAnalytics() {
  const { trackInteraction } = useAnalytics();
  
  const handleCustomEvent = () => {
    trackInteraction('custom_dashboard_event', {
      component: 'daily_outlook',
      action: 'custom_action'
    });
  };
  
  return (
    <div>
      <DailyOutlook />
      <button onClick={handleCustomEvent}>
        Track Custom Event
      </button>
    </div>
  );
}
```

## Testing Integration

### Component Testing

```tsx
import { render, screen } from '@testing-library/react';
import { AuthProvider } from '../hooks/useAuth';
import DailyOutlook from '../components/DailyOutlook';

// Mock the auth context
const mockAuthContext = {
  user: { name: 'Test User', id: '123' },
  isAuthenticated: true,
  login: jest.fn(),
  logout: jest.fn(),
  loading: false
};

test('renders daily outlook with user data', () => {
  render(
    <AuthProvider value={mockAuthContext}>
      <DailyOutlook />
    </AuthProvider>
  );
  
  expect(screen.getByText(/Good morning, Test User/)).toBeInTheDocument();
});
```

### Integration Testing

```tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DailyOutlook from '../components/DailyOutlook';

test('handles action completion', async () => {
  // Mock API responses
  global.fetch = jest.fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => mockDailyOutlookData
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

  render(<DailyOutlook />);
  
  // Wait for component to load
  await waitFor(() => {
    expect(screen.getByText('Quick Actions')).toBeInTheDocument();
  });
  
  // Click on an action checkbox
  const checkbox = screen.getByRole('button', { name: /Mark as complete/ });
  fireEvent.click(checkbox);
  
  // Verify optimistic update
  expect(screen.getByRole('button', { name: /Mark as incomplete/ })).toBeInTheDocument();
});
```

## Performance Considerations

### Optimization Tips

1. **Lazy Loading**: Load the component only when needed
2. **Memoization**: Use React.memo for expensive computations
3. **Debouncing**: Debounce user interactions to prevent excessive API calls
4. **Caching**: Cache API responses to reduce network requests

### Bundle Size

The component adds approximately:
- **JavaScript**: ~15KB (gzipped)
- **CSS**: Uses existing Tailwind classes (no additional CSS)
- **Dependencies**: Only uses existing project dependencies

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure AuthProvider is in the component tree
2. **API Errors**: Check that backend endpoints are implemented
3. **Styling Issues**: Verify Tailwind CSS is properly configured
4. **TypeScript Errors**: Ensure all required types are imported

### Debug Mode

Enable debug logging:

```tsx
// Add to your environment variables
REACT_APP_DEBUG_DAILY_OUTLOOK=true
```

### Performance Monitoring

```tsx
// Monitor component performance
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(console.log);
getFID(console.log);
getFCP(console.log);
getLCP(console.log);
getTTFB(console.log);
```

## Migration Guide

### From Existing Components

If you're replacing an existing daily summary component:

1. **Data Migration**: Map your existing data structure to the new format
2. **API Updates**: Update your backend to provide the required endpoints
3. **Styling Updates**: Replace existing styles with the new component
4. **Testing Updates**: Update your tests to use the new component structure

### Backward Compatibility

The component is designed to be backward compatible:

- **Graceful Degradation**: Works without all features enabled
- **Progressive Enhancement**: Adds features as they become available
- **Fallback Support**: Provides fallbacks for unsupported browsers

## Support

For additional support:

1. **Documentation**: Check the component README
2. **Examples**: Review the test page implementation
3. **Issues**: Report issues through your project's issue tracker
4. **Community**: Join the MINGUS developer community
