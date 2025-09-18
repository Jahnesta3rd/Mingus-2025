# RecommendationTiers Component

A comprehensive React component that displays job recommendations in three distinct tiers (Conservative, Optimal, Stretch) with interactive features, analytics tracking, and mobile optimization.

## Features

### 🎯 Three-Tier Structure
- **Conservative (Safe Growth)**: 15-20% salary increase, high success probability
- **Optimal (Strategic Advance)**: 25-30% salary increase, moderate stretch (Featured)
- **Stretch (Ambitious Leap)**: 35%+ salary increase, significant growth

### 🔄 Interactive Features
- **Tier Expansion**: Click to expand/collapse job lists
- **Comparison Mode**: Side-by-side tier comparison
- **Location Filtering**: Radius-based job filtering (5, 10, 30 miles, Nationwide)
- **Refresh Functionality**: Real-time data updates
- **Job Interactions**: View details and apply buttons

### 📱 Mobile Optimization
- **Responsive Design**: Mobile-first approach with adaptive layouts
- **Touch Interactions**: Optimized for touch devices
- **Flexible Grid**: Adapts to screen size
- **Truncated Text**: Prevents overflow on small screens

### ♿ Accessibility Features
- **ARIA Labels**: Comprehensive screen reader support
- **Keyboard Navigation**: Full keyboard accessibility
- **Focus Management**: Clear focus indicators
- **Semantic HTML**: Proper heading hierarchy and landmarks

### 📊 Analytics Integration
- **useAnalytics Hook**: Integrated analytics tracking
- **Event Tracking**: Tier interactions, job clicks, filter changes
- **Error Tracking**: Comprehensive error monitoring
- **User Behavior**: Detailed interaction analytics

## Props

```typescript
interface RecommendationTiersProps {
  className?: string;        // Additional CSS classes
  userId?: string;          // User ID for personalization
  locationRadius?: number;  // Default search radius in miles
}
```

## Data Structure

### JobRecommendation Interface
```typescript
interface JobRecommendation {
  job: {
    job_id: string;
    title: string;
    company: string;
    location: string;
    salary_min: number;
    salary_max: number;
    // ... additional job details
  };
  tier: 'conservative' | 'optimal' | 'stretch';
  success_probability: number;
  salary_increase_potential: number;
  // ... additional analysis data
}
```

### TierData Interface
```typescript
interface TierData {
  tier_name: string;
  tier_label: string;
  description: string;
  color_scheme: string;
  border_style: string;
  jobs: JobRecommendation[];
  average_salary_increase: number;
  average_success_rate: number;
  recommended_timeline: string;
  icon: React.ReactNode;
}
```

## API Integration

### Endpoint: `/api/risk/trigger-recommendations`
```typescript
// Request
{
  user_id: string;
  location_radius: number;
  include_tier_analysis: boolean;
  risk_data: {
    overall_risk: number;
    risk_breakdown: object;
    risk_triggers: array;
  };
  recommendation_tiers: string[];
  max_recommendations_per_tier: number;
}

// Response
{
  success: boolean;
  recommendations: {
    conservative: JobRecommendation[];
    optimal: JobRecommendation[];
    stretch: JobRecommendation[];
    total_count: number;
  };
}
```

## Usage Examples

### Basic Usage
```tsx
import RecommendationTiers from './components/RecommendationTiers';

function App() {
  return (
    <div>
      <RecommendationTiers />
    </div>
  );
}
```

### With Custom Props
```tsx
<RecommendationTiers
  userId="user123"
  locationRadius={30}
  className="my-custom-class"
/>
```

### In Test Environment
```tsx
import RecommendationTiersTestPage from './pages/RecommendationTiersTestPage';

// Navigate to /test-recommendation-tiers
```

## Styling

The component uses Tailwind CSS classes with a consistent design system:

- **Color Schemes**: Blue (Conservative), Purple (Optimal), Orange (Stretch)
- **Typography**: Responsive text sizing with proper hierarchy
- **Spacing**: Consistent padding and margins
- **Shadows**: Subtle hover effects and depth
- **Borders**: Tier-specific border styles

## State Management

### Local State
- `tiers`: Array of tier data
- `loading`: Loading state indicator
- `expandedTier`: Currently expanded tier
- `comparisonMode`: Comparison view toggle
- `selectedRadius`: Current search radius
- `error`: Error state message
- `lastUpdated`: Last data refresh timestamp
- `isRefreshing`: Refresh operation state

### Event Handlers
- `fetchRecommendations()`: Loads data from API
- `handleTierExpansion()`: Manages tier expand/collapse
- `handleJobInteraction()`: Handles job-related actions
- `handleRadiusChange()`: Updates search radius
- `handleComparisonToggle()`: Toggles comparison mode
- `handleRefresh()`: Refreshes data

## Analytics Events

### Tracked Events
- `recommendation_tiers_loaded`: Initial data load
- `recommendation_tier_expanded`: Tier expansion/collapse
- `job_recommendation_interaction`: Job-related actions
- `location_radius_changed`: Radius filter changes
- `comparison_mode_toggled`: Comparison mode toggle
- `recommendations_refreshed`: Data refresh

### Event Data
Each event includes relevant context:
- User ID and session ID
- Interaction details
- Component state
- Error information (for error events)

## Error Handling

### Error States
- **API Errors**: Network and server errors
- **Data Errors**: Invalid response format
- **Loading Errors**: Timeout and connection issues

### Error Recovery
- **Retry Button**: Manual retry functionality
- **Error Tracking**: Comprehensive error logging
- **User Feedback**: Clear error messages
- **Graceful Degradation**: Fallback UI states

## Performance Considerations

### Optimization Strategies
- **Lazy Loading**: Jobs loaded on demand
- **Memoization**: Prevent unnecessary re-renders
- **Debouncing**: Rate-limit API calls
- **Caching**: Local data caching

### Bundle Size
- **Tree Shaking**: Only import used icons
- **Code Splitting**: Lazy load heavy components
- **Minification**: Optimized production build

## Testing

### Test Coverage
- **Unit Tests**: Component logic and state
- **Integration Tests**: API interactions
- **Accessibility Tests**: Screen reader compatibility
- **Mobile Tests**: Responsive behavior

### Test Files
- `RecommendationTiersTest.tsx`: Main test suite
- `RecommendationTiersTestPage.tsx`: Interactive test page

## Browser Support

### Supported Browsers
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Mobile Support
- iOS Safari 14+
- Chrome Mobile 90+
- Samsung Internet 13+

## Dependencies

### Required
- React 18+
- TypeScript 4.5+
- Tailwind CSS 3.0+
- Lucide React (Icons)

### Optional
- @testing-library/react (Testing)
- @testing-library/jest-dom (Testing)

## Future Enhancements

### Planned Features
- **Real-time Updates**: WebSocket integration
- **Advanced Filtering**: Skills, salary, company size
- **Job Favorites**: Save interesting positions
- **Share Functionality**: Share recommendations
- **Export Options**: PDF/CSV export

### Performance Improvements
- **Virtual Scrolling**: Large job lists
- **Image Optimization**: Company logos
- **Progressive Loading**: Staged data loading
- **Service Worker**: Offline support

## Troubleshooting

### Common Issues

#### Component Not Loading
- Check API endpoint availability
- Verify user authentication
- Check browser console for errors

#### Styling Issues
- Ensure Tailwind CSS is properly configured
- Check for CSS conflicts
- Verify responsive breakpoints

#### Analytics Not Tracking
- Verify useAnalytics hook integration
- Check network requests to analytics endpoint
- Ensure proper event data structure

### Debug Mode
Enable debug logging by setting:
```typescript
localStorage.setItem('mingus_debug', 'true');
```

## Contributing

### Development Setup
1. Install dependencies: `npm install`
2. Start dev server: `npm run dev`
3. Run tests: `npm test`
4. Build for production: `npm run build`

### Code Style
- Use TypeScript strict mode
- Follow React best practices
- Maintain accessibility standards
- Write comprehensive tests

### Pull Request Process
1. Create feature branch
2. Write tests for new features
3. Update documentation
4. Submit pull request with description
5. Address review feedback

## License

This component is part of the Mingus Application and follows the project's licensing terms.