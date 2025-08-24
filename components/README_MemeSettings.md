# MemeSettings Component

A comprehensive React component for managing user meme splash page preferences in the MINGUS application.

## Features

### ✅ Core Functionality
- **Toggle Enable/Disable**: Complete control over daily memes
- **Category Selection**: Choose from 6 content categories with visual icons
- **Frequency Settings**: Every login, once per day, or weekly options
- **Preview Functionality**: See sample content before saving
- **Reset Options**: Quick reset to default preferences
- **Analytics Display**: View engagement metrics and statistics

### ✅ User Experience
- **Optimistic Updates**: Immediate UI feedback with error handling
- **Loading States**: Skeleton loading and progress indicators
- **Error Handling**: Comprehensive error states with user feedback
- **Success Feedback**: Visual confirmation of saved changes
- **Responsive Design**: Mobile-first approach with Tailwind CSS

### ✅ Accessibility
- **ARIA Labels**: Proper labeling for screen readers
- **Keyboard Navigation**: Full keyboard support
- **Focus Management**: Clear focus indicators
- **Screen Reader Support**: Semantic HTML structure

## Installation & Usage

### Basic Usage

```tsx
import MemeSettings from '../components/MemeSettings';

function SettingsPage() {
  const userId = '123'; // Get from auth context or props
  
  return (
    <MemeSettings
      userId={userId}
      onClose={() => console.log('Settings closed')}
      className="w-full max-w-2xl"
    />
  );
}
```

### With Modal Integration

```tsx
import React, { useState } from 'react';
import MemeSettings from '../components/MemeSettings';

function SettingsModal() {
  const [showSettings, setShowSettings] = useState(false);
  const userId = '123';

  return (
    <>
      <button onClick={() => setShowSettings(true)}>
        Open Meme Settings
      </button>
      
      {showSettings && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <MemeSettings
            userId={userId}
            onClose={() => setShowSettings(false)}
            className="w-full max-w-4xl"
          />
        </div>
      )}
    </>
  );
}
```

## API Integration

The component integrates with existing MINGUS API endpoints:

### GET `/api/user-meme-preferences/{user_id}`
Fetches current user preferences and analytics.

**Response:**
```json
{
  "success": true,
  "preferences": {
    "memes_enabled": true,
    "preferred_categories": ["faith", "work_life", "friendships"],
    "frequency_setting": "daily",
    "custom_frequency_days": 1,
    "last_meme_shown_at": "2025-01-15T10:30:00Z",
    "opt_out_reason": null,
    "opt_out_date": null
  },
  "analytics": {
    "total_interactions": 45,
    "interactions_by_type": {
      "view": 30,
      "like": 10,
      "skip": 5
    },
    "favorite_categories": ["faith", "work_life"],
    "skip_rate": 11.11,
    "engagement_rate": 33.33,
    "last_updated": "2025-01-15T10:30:00Z"
  }
}
```

### PUT `/api/user-meme-preferences/{user_id}`
Updates user preferences.

**Request:**
```json
{
  "memes_enabled": true,
  "preferred_categories": ["faith", "work_life", "children"],
  "frequency_setting": "weekly",
  "custom_frequency_days": 7
}
```

### GET `/api/user-meme`
Fetches a sample meme for preview functionality.

## Component Props

```tsx
interface MemeSettingsProps {
  userId: string;           // Required: User ID for API calls
  onClose?: () => void;     // Optional: Callback when settings are closed
  className?: string;       // Optional: Additional CSS classes
}
```

## Data Models

### MemePreferences Interface
```tsx
interface MemePreferences {
  memes_enabled: boolean;
  preferred_categories: string[];
  frequency_setting: 'every_login' | 'once_per_day' | 'weekly';
  custom_frequency_days?: number;
  last_meme_shown_at?: string;
  opt_out_reason?: string;
  opt_out_date?: string;
}
```

### MemeAnalytics Interface
```tsx
interface MemeAnalytics {
  total_interactions: number;
  interactions_by_type: Record<string, number>;
  favorite_categories: string[];
  skip_rate: number;
  engagement_rate: number;
  last_updated: string;
}
```

## Content Categories

The component supports 6 predefined categories:

| Category ID | Label | Description | Icon |
|-------------|-------|-------------|------|
| `faith` | Faith & Spirituality | Inspirational content related to faith, spirituality, and personal growth | 🙏 |
| `work_life` | Work & Career | Motivational content about professional development and work-life balance | 💼 |
| `friendships` | Friendships | Content about building and maintaining meaningful friendships | 👥 |
| `children` | Parenting & Children | Family-focused content about parenting and raising children | 👶 |
| `relationships` | Relationships | Content about romantic relationships and partnership | ❤️ |
| `going_out` | Social Life | Content about social activities, entertainment, and leisure | 🎉 |

## Frequency Options

| Value | Label | Description |
|-------|-------|-------------|
| `every_login` | Every Login | See a meme every time you log into MINGUS |
| `once_per_day` | Once Per Day | See one meme per day, even with multiple logins |
| `weekly` | Weekly | See one meme per week |

## State Management

The component uses React hooks for state management:

- **useState**: Local component state
- **useCallback**: Memoized functions for performance
- **useEffect**: Side effects and API calls

### Key State Variables
```tsx
const [preferences, setPreferences] = useState<MemePreferences>({...});
const [analytics, setAnalytics] = useState<MemeAnalytics | null>(null);
const [loading, setLoading] = useState(true);
const [saving, setSaving] = useState(false);
const [error, setError] = useState<string | null>(null);
const [success, setSuccess] = useState<string | null>(null);
```

## Error Handling

The component includes comprehensive error handling:

1. **API Errors**: Network failures, server errors, validation errors
2. **User Feedback**: Clear error messages with retry options
3. **Fallback States**: Graceful degradation when features are unavailable
4. **Loading States**: Skeleton loading during API calls

## Accessibility Features

### ARIA Labels
- Proper labeling for all interactive elements
- Screen reader announcements for state changes
- Descriptive text for complex UI elements

### Keyboard Navigation
- Tab order follows logical flow
- Enter/Space for button activation
- Escape key for modal dismissal
- Arrow keys for radio button selection

### Focus Management
- Clear focus indicators
- Focus trapping in modals
- Focus restoration after state changes

## Styling

The component uses Tailwind CSS with:

- **Responsive Design**: Mobile-first approach
- **Dark Mode Support**: Compatible with dark themes
- **Custom Classes**: Extensible styling system
- **Consistent Spacing**: Design system compliance

### Key CSS Classes
```css
/* Container */
.bg-white.rounded-lg.shadow-lg.overflow-hidden

/* Header */
.bg-gradient-to-r.from-blue-600.to-purple-600

/* Form Elements */
.border-2.cursor-pointer.transition-all

/* States */
.border-blue-500.bg-blue-50  /* Selected */
.border-gray-200.hover:border-gray-300  /* Default */

/* Buttons */
.bg-blue-600.hover:bg-blue-700.disabled:bg-gray-400
```

## Performance Optimizations

1. **Memoized Functions**: useCallback for expensive operations
2. **Optimistic Updates**: Immediate UI feedback
3. **Debounced API Calls**: Prevents excessive requests
4. **Lazy Loading**: Images loaded on demand
5. **Error Boundaries**: Graceful error handling

## Testing

### Unit Tests
```tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MemeSettings from '../MemeSettings';

test('renders meme settings with user preferences', async () => {
  render(<MemeSettings userId="123" />);
  
  await waitFor(() => {
    expect(screen.getByText('Meme Settings')).toBeInTheDocument();
  });
});

test('toggles meme categories', async () => {
  render(<MemeSettings userId="123" />);
  
  const faithCheckbox = screen.getByLabelText(/Faith & Spirituality/);
  fireEvent.click(faithCheckbox);
  
  expect(faithCheckbox).toBeChecked();
});
```

### Integration Tests
```tsx
test('saves preferences to API', async () => {
  const mockFetch = jest.fn();
  global.fetch = mockFetch;
  
  render(<MemeSettings userId="123" />);
  
  // Toggle a setting
  const toggle = screen.getByRole('checkbox');
  fireEvent.click(toggle);
  
  await waitFor(() => {
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/user-meme-preferences/123',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify(expect.objectContaining({
          memes_enabled: false
        }))
      })
    );
  });
});
```

## Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile**: iOS Safari 14+, Chrome Mobile 90+
- **Accessibility**: Screen readers, keyboard navigation, high contrast

## Dependencies

- **React**: 17.0.0 or higher
- **TypeScript**: 4.5.0 or higher
- **Tailwind CSS**: 2.0.0 or higher

## Future Enhancements

1. **Custom Frequency**: Allow users to set custom intervals
2. **Time-based Preferences**: Schedule memes for specific times
3. **Advanced Analytics**: More detailed engagement metrics
4. **Bulk Operations**: Select/deselect all categories
5. **Import/Export**: Save and restore preference configurations

## Contributing

When contributing to this component:

1. Follow the existing code style and patterns
2. Add comprehensive TypeScript types
3. Include accessibility considerations
4. Write unit tests for new features
5. Update documentation for API changes

## License

This component is part of the MINGUS application and follows the project's licensing terms.
