# Meme Splash Page Component

A comprehensive React component for displaying daily memes in a mobile finance app with full-screen overlay, analytics tracking, and accessibility features.

## Features

### ✅ Core Requirements Met
- **Full-screen overlay** that appears before dashboard
- **Meme image with caption** display
- **Prominent "Continue to Dashboard" button** with hover effects
- **Easy-to-find "Turn off daily memes" link** in header and footer
- **"Not today" option** for temporary skip
- **Loading state** with skeleton animation
- **Error fallback** if meme fails to load
- **Smooth animations/transitions** with CSS transforms
- **Mobile-first responsive design** using Tailwind CSS
- **Accessibility features** (alt text, keyboard navigation, ARIA labels)

### 🚀 Additional Features
- **Auto-advance countdown** (10 seconds default)
- **Analytics tracking** for all user interactions
- **Error boundary** for graceful error handling
- **Image loading states** with fallback for broken images
- **Keyboard shortcuts** (Enter/Space to continue, Escape to skip, O for opt-out)
- **Time spent tracking** for engagement analytics
- **Confirmation modal** for opt-out action
- **Production-ready** with proper error handling and loading states

## Installation

The component is already included in your project at `components/MemeSplashPage.tsx`.

## Usage

### Basic Usage

```tsx
import MemeSplashPage from '../components/MemeSplashPage';

function App() {
  return (
    <MemeSplashPage />
  );
}
```

### Advanced Usage with Custom Handlers

```tsx
import MemeSplashPage from '../components/MemeSplashPage';

function App() {
  const handleContinue = () => {
    // Custom logic before going to dashboard
    console.log('User continued to dashboard');
    router.push('/dashboard');
  };

  const handleOptOut = () => {
    // Custom logic for opt-out
    console.log('User opted out of daily memes');
    router.push('/dashboard');
  };

  const handleSkip = () => {
    // Custom logic for skip
    console.log('User skipped today');
    router.push('/dashboard');
  };

  return (
    <MemeSplashPage
      onContinue={handleContinue}
      onOptOut={handleOptOut}
      onSkip={handleSkip}
      autoAdvanceSeconds={15}
      showOptOutModal={true}
    />
  );
}
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onContinue` | `() => void` | `undefined` | Callback when user clicks "Continue to Dashboard" |
| `onOptOut` | `() => void` | `undefined` | Callback when user opts out of daily memes |
| `onSkip` | `() => void` | `undefined` | Callback when user clicks "Not today" |
| `autoAdvanceSeconds` | `number` | `10` | Seconds before auto-advancing to dashboard (0 to disable) |
| `showOptOutModal` | `boolean` | `true` | Whether to show confirmation modal for opt-out |

## API Integration

The component integrates with the following API endpoints:

### Fetch Meme
- **Endpoint**: `GET /api/user-meme`
- **Authentication**: Required (uses session cookies)
- **Response**: `MemeApiResponse`

### Track Analytics
- **Endpoint**: `POST /api/meme-analytics`
- **Authentication**: Required
- **Body**: `MemeAnalytics`
- **Response**: `MemeAnalyticsResponse`

### Update Preferences
- **Endpoint**: `PUT /api/user-meme-preferences`
- **Authentication**: Required
- **Body**: `MemePreferences`
- **Response**: `MemePreferencesResponse`

## Data Types

### Meme Interface
```typescript
interface Meme {
  id: string;
  image_url: string;
  caption: string;
  category: string;
  alt_text: string;
  tags?: string[];
  source_attribution?: string;
  created_at?: string;
  updated_at?: string;
}
```

### Analytics Interface
```typescript
interface MemeAnalytics {
  meme_id: string;
  interaction_type: 'viewed' | 'skipped' | 'continued' | 'liked' | 'shared' | 'reported';
  time_spent_seconds?: number;
  source_page?: string;
  device_type?: string;
  user_agent?: string;
  ip_address?: string;
  session_id?: string;
}
```

## User Interactions Tracked

1. **Viewed** - When meme is successfully loaded and displayed
2. **Continued** - When user clicks "Continue to Dashboard"
3. **Skipped** - When user clicks "Not today" or opts out
4. **Liked** - Future feature for like functionality
5. **Shared** - Future feature for share functionality
6. **Reported** - Future feature for report functionality

## Accessibility Features

- **Keyboard Navigation**:
  - `Enter` or `Space`: Continue to dashboard
  - `Escape`: Skip for today
  - `O`: Open opt-out modal
- **Screen Reader Support**:
  - Proper ARIA labels on all interactive elements
  - Alt text for meme images
  - Descriptive button text
- **Focus Management**:
  - Visible focus indicators
  - Logical tab order
  - Focus trapping in modal

## Error Handling

The component includes comprehensive error handling:

1. **Network Errors**: Retry button with user-friendly message
2. **API Errors**: Graceful fallback with error details
3. **Image Loading Errors**: Fallback placeholder with emoji
4. **Component Errors**: Error boundary with reload option

## Loading States

1. **Initial Loading**: Skeleton animation with placeholder content
2. **Image Loading**: Loading indicator while image loads
3. **Opt-out Loading**: Spinner with "Turning off..." text
4. **Auto-advance**: Countdown timer in top-right corner

## Styling

The component uses Tailwind CSS classes for styling:

- **Colors**: Black background with white content cards
- **Typography**: Clear hierarchy with proper contrast
- **Spacing**: Consistent padding and margins
- **Animations**: Smooth transitions and hover effects
- **Responsive**: Mobile-first design that scales to larger screens

## Performance Optimizations

- **Image Loading**: Eager loading for immediate display
- **Analytics**: Non-blocking API calls
- **State Management**: Efficient use of React hooks
- **Memory Management**: Proper cleanup of intervals and event listeners
- **Bundle Size**: Minimal dependencies, only React and Next.js router

## Browser Support

- **Modern Browsers**: Chrome, Firefox, Safari, Edge (latest versions)
- **Mobile Browsers**: iOS Safari, Chrome Mobile, Samsung Internet
- **Progressive Enhancement**: Graceful degradation for older browsers

## Testing

The component is designed to be easily testable:

```tsx
// Example test structure
describe('MemeSplashPage', () => {
  it('should render loading state initially', () => {
    // Test loading skeleton
  });

  it('should display meme when loaded', () => {
    // Test meme display
  });

  it('should handle continue button click', () => {
    // Test continue functionality
  });

  it('should handle opt-out flow', () => {
    // Test opt-out functionality
  });

  it('should auto-advance after countdown', () => {
    // Test auto-advance functionality
  });
});
```

## Customization

### Styling Customization
You can customize the appearance by modifying the Tailwind classes or adding custom CSS:

```css
/* Custom styles for meme splash page */
.meme-splash-custom {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.meme-card-custom {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}
```

### API Endpoint Customization
You can customize API endpoints by modifying the fetch calls in the component or by extending the component with custom endpoint props.

## Troubleshooting

### Common Issues

1. **Meme not loading**: Check API endpoint and authentication
2. **Analytics not tracking**: Verify API endpoint and network connectivity
3. **Auto-advance not working**: Check if `autoAdvanceSeconds` is set correctly
4. **Image not displaying**: Check image URL and CORS settings

### Debug Mode
Enable debug logging by setting `localStorage.debug = 'meme-splash'` in browser console.

## Contributing

When contributing to this component:

1. Follow the existing code style and patterns
2. Add proper TypeScript types for new features
3. Include accessibility considerations
4. Test on multiple devices and browsers
5. Update this documentation for any new features

## License

This component is part of the Mingus Application and follows the same license terms.
