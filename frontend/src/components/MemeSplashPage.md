# MemeSplashPage Component

A full-screen React component for displaying memes in a mobile finance app before users access the dashboard.

## Features

- ✅ Full-screen overlay with smooth animations
- ✅ Meme image display with caption
- ✅ "Continue to Dashboard" and "Skip this feature" buttons
- ✅ Loading state with skeleton animation
- ✅ Error handling with retry functionality
- ✅ Auto-advance after 10 seconds (configurable)
- ✅ Mobile-first responsive design
- ✅ Accessibility features (keyboard navigation, alt text, ARIA labels)
- ✅ Analytics tracking for user interactions
- ✅ TypeScript support with full type definitions
- ✅ Error boundary for graceful failure handling

## API Endpoints Required

The component expects these API endpoints to be available:

### GET /api/user-meme
Returns a random meme for the current user.

**Response:**
```json
{
  "id": 1,
  "image_url": "/uploads/meme_123.jpg",
  "category": "work_life",
  "caption": "When you check your bank account on Monday morning",
  "alt_text": "Meme showing shocked face with bank account balance",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### POST /api/meme-analytics
Tracks user interactions with memes.

**Request Body:**
```json
{
  "meme_id": 1,
  "action": "view|continue|skip|auto_advance",
  "timestamp": "2024-01-15T10:30:00Z",
  "user_id": "user123",
  "session_id": "session456"
}
```

## Usage

```tsx
import MemeSplashPage from './components/MemeSplashPage';

function App() {
  const [showMeme, setShowMeme] = useState(true);

  const handleContinue = () => {
    setShowMeme(false);
    // Navigate to dashboard
  };

  const handleSkip = () => {
    setShowMeme(false);
    // Skip meme feature
  };

  if (showMeme) {
    return (
      <MemeSplashPage
        onContinue={handleContinue}
        onSkip={handleSkip}
        userId="user123"
        sessionId="session456"
        autoAdvanceDelay={10000}
      />
    );
  }

  return <Dashboard />;
}
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onContinue` | `() => void` | Required | Callback when user clicks "Continue to Dashboard" |
| `onSkip` | `() => void` | Required | Callback when user clicks "Skip this feature" |
| `userId` | `string` | Optional | User ID for analytics tracking |
| `sessionId` | `string` | Optional | Session ID for analytics tracking |
| `autoAdvanceDelay` | `number` | `10000` | Auto-advance delay in milliseconds |
| `className` | `string` | `''` | Additional CSS classes |

## Keyboard Navigation

- **Enter** or **Space**: Continue to dashboard
- **Escape**: Skip this feature

## Analytics Events

The component automatically tracks these events:

- `view`: When meme is successfully loaded and displayed
- `continue`: When user clicks "Continue to Dashboard"
- `skip`: When user clicks "Skip this feature"
- `auto_advance`: When component auto-advances after timeout

## Error Handling

The component includes comprehensive error handling:

1. **Network errors**: Shows retry button with error message
2. **Image load failures**: Displays error state with retry option
3. **API failures**: Graceful fallback with user-friendly messages
4. **Component errors**: Error boundary catches and displays fallback UI

## Styling

The component uses Tailwind CSS classes and is designed to be:

- **Mobile-first**: Optimized for mobile devices
- **Dark theme**: Uses gray-900 background with white text
- **Responsive**: Adapts to different screen sizes
- **Accessible**: High contrast, proper focus states

## Dependencies

- React 16.8+ (for hooks)
- TypeScript (for type safety)
- Tailwind CSS (for styling)

## Browser Support

- Modern browsers with ES6+ support
- Mobile browsers (iOS Safari, Chrome Mobile, etc.)
- Requires fetch API support

## Performance Considerations

- Images are lazy-loaded
- Analytics calls are non-blocking
- Timers are properly cleaned up
- Component unmounts cleanly

## Security

- Uses `credentials: 'include'` for authenticated requests
- Validates API responses
- Sanitizes user input
- Includes CSRF protection via cookies
