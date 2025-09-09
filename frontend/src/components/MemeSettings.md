# MemeSettings Component

A comprehensive React component for managing user meme splash page preferences in the Mingus personal finance application.

## Features

- ✅ **Toggle Control**: Enable/disable daily memes completely
- ✅ **Category Selection**: Checkboxes for each meme category (faith, work_life, friendships, children, relationships, going_out)
- ✅ **Frequency Settings**: Choose between every login, once per day, or weekly
- ✅ **Preview Functionality**: "Preview memes" button to see sample content
- ✅ **Reset Preferences**: Button to restore default settings
- ✅ **Optimistic Updates**: Immediate UI updates with background saving
- ✅ **Loading States**: Visual feedback during API calls
- ✅ **Error Handling**: Comprehensive error handling with user-friendly messages
- ✅ **Form Validation**: Client-side and server-side validation
- ✅ **Accessibility**: Proper labels, keyboard navigation, and ARIA attributes
- ✅ **Responsive Design**: Mobile-first design with Tailwind CSS
- ✅ **TypeScript Support**: Full type definitions and type safety

## API Endpoints Required

The component expects these API endpoints to be available:

### GET /api/user-meme-preferences/{user_id}
Returns meme preferences for the specified user.

**Response:**
```json
{
  "success": true,
  "preferences": {
    "enabled": true,
    "categories": {
      "faith": true,
      "work_life": true,
      "friendships": false,
      "children": true,
      "relationships": true,
      "going_out": false
    },
    "frequency": "once_per_day"
  }
}
```

### PUT /api/user-meme-preferences/{user_id}
Saves meme preferences for the specified user.

**Request Body:**
```json
{
  "preferences": {
    "enabled": true,
    "categories": {
      "faith": true,
      "work_life": true,
      "friendships": false,
      "children": true,
      "relationships": true,
      "going_out": false
    },
    "frequency": "once_per_day"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Preferences saved successfully",
  "preferences": { ... }
}
```

### DELETE /api/user-meme-preferences/{user_id}
Deletes user preferences (resets to defaults).

**Response:**
```json
{
  "success": true,
  "message": "Preferences deleted successfully"
}
```

## Usage

### Basic Usage

```tsx
import MemeSettings from './components/MemeSettings';

function SettingsPage() {
  const [userId] = useState('user123');

  const handlePreferencesChange = (preferences) => {
    console.log('Preferences updated:', preferences);
  };

  return (
    <MemeSettings
      userId={userId}
      onPreferencesChange={handlePreferencesChange}
    />
  );
}
```

### With Full Settings Page

```tsx
import SettingsPage from './pages/SettingsPage';

function App() {
  return (
    <SettingsPage userId="user123" />
  );
}
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `userId` | `string` | Optional | User ID for API calls |
| `onPreferencesChange` | `(preferences: MemePreferences) => void` | Optional | Callback when preferences change |
| `className` | `string` | `''` | Additional CSS classes |

## Types

### MemePreferences

```typescript
interface MemePreferences {
  enabled: boolean;
  categories: {
    faith: boolean;
    work_life: boolean;
    friendships: boolean;
    children: boolean;
    relationships: boolean;
    going_out: boolean;
  };
  frequency: 'every_login' | 'once_per_day' | 'weekly';
}
```

### MemeSettingsProps

```typescript
interface MemeSettingsProps {
  userId?: string;
  onPreferencesChange?: (preferences: MemePreferences) => void;
  className?: string;
}
```

## Categories

The component supports six meme categories:

1. **Faith & Spirituality** - Religious and spiritual financial struggles
2. **Work & Career** - Work-related financial challenges and career expenses
3. **Friendships** - Social spending and friend-related expenses
4. **Children & Family** - Parenting and child-related financial stress
5. **Relationships** - Dating, marriage, and relationship financial dynamics
6. **Going Out** - Entertainment, dining out, and social activities

## Frequency Options

- **Every Login**: Show a meme every time the user logs in
- **Once Per Day**: Show one meme per day maximum
- **Weekly**: Show one meme per week maximum

## Accessibility Features

- **Keyboard Navigation**: All controls are keyboard accessible
- **Screen Reader Support**: Proper ARIA labels and descriptions
- **Focus Management**: Clear focus indicators and logical tab order
- **High Contrast**: Meets WCAG contrast requirements
- **Semantic HTML**: Uses proper form elements and labels

## Error Handling

The component includes comprehensive error handling:

1. **Network Errors**: Shows retry options with clear error messages
2. **Validation Errors**: Client-side and server-side validation
3. **API Failures**: Graceful fallback with user-friendly messages
4. **Loading States**: Visual feedback during all async operations

## Styling

The component uses Tailwind CSS classes and follows these design principles:

- **Mobile-first**: Optimized for mobile devices
- **Consistent**: Matches existing Mingus app styling
- **Accessible**: High contrast, proper focus states
- **Responsive**: Adapts to different screen sizes

## Dependencies

- React 16.8+ (for hooks)
- TypeScript (for type safety)
- Tailwind CSS (for styling)

## Browser Support

- Modern browsers with ES6+ support
- Mobile browsers (iOS Safari, Chrome Mobile, etc.)
- Requires fetch API support

## Performance Considerations

- **Optimistic Updates**: UI updates immediately, saves in background
- **Debounced Saving**: Prevents excessive API calls
- **Efficient Re-renders**: Uses useCallback and useMemo where appropriate
- **Lazy Loading**: Preview memes are loaded on demand

## Security

- Uses `credentials: 'include'` for authenticated requests
- Validates all user input
- Sanitizes API responses
- Includes CSRF protection via cookies

## Testing

The component includes comprehensive error handling and can be tested with:

1. **Unit Tests**: Test individual functions and state changes
2. **Integration Tests**: Test API interactions
3. **Accessibility Tests**: Verify keyboard navigation and screen reader support
4. **Visual Tests**: Ensure consistent styling across devices

## Example Integration

See `MemeSettingsExample.tsx` for a complete example of how to integrate the component into your application.

## Database Schema

The component requires a `user_meme_preferences` table:

```sql
CREATE TABLE user_meme_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    preferences TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## Future Enhancements

Potential future improvements:

- **Advanced Scheduling**: More granular frequency options
- **Category Weights**: Prioritize certain categories
- **Time-based Settings**: Different preferences for different times
- **Analytics Integration**: Track preference changes
- **Bulk Operations**: Import/export preferences
