# Location Intelligence Map Component

## Overview

The `LocationIntelligenceMap` component provides an interactive geographic visualization of career opportunities with advanced location-based filtering, commute analysis, and real-time job data integration.

## Features

### 🗺️ Interactive Map Integration
- **Google Maps Integration**: Dynamic map loading with custom styling
- **Real-time Job Markers**: Color-coded markers based on job tiers (Conservative, Optimal, Stretch)
- **User Location Detection**: Automatic geolocation with fallback to zipcode-based location
- **Radius Visualization**: Dynamic circle overlay showing search radius

### 📍 Location-Based Job Filtering
- **Radius Controls**: 5, 10, 30 miles, or nationwide search
- **Real-time Updates**: Job count updates as radius changes
- **Tier-based Filtering**: Visual distinction between job risk levels
- **Distance Calculation**: Accurate distance measurements from user location

### 🚗 Commute Analysis
- **Multiple Transportation Modes**: Driving, Transit, Walking/Biking
- **Real-time Route Display**: Interactive directions on map
- **Cost Analysis**: Monthly commute cost calculations
- **Time Estimates**: Accurate travel time for each mode

### 📊 Analytics Integration
- **User Interaction Tracking**: Comprehensive analytics for all map interactions
- **Location Analytics**: Track radius changes, job selections, and commute mode switches
- **Error Tracking**: Detailed error logging for debugging and improvement
- **Performance Monitoring**: Track map load times and API response times

### ♿ Accessibility Features
- **Keyboard Navigation**: Full keyboard support for all controls
- **Screen Reader Support**: Proper ARIA labels and descriptions
- **High Contrast Mode**: Accessible color schemes
- **Focus Management**: Clear focus indicators and logical tab order

### 📱 Responsive Design
- **Mobile Optimization**: Touch-friendly controls and gestures
- **Adaptive Layout**: Responsive design for all screen sizes
- **Touch Interactions**: Optimized for mobile map interactions
- **Performance**: Optimized for mobile data usage

## Component Structure

```typescript
interface JobLocation {
  id: string;
  title: string;
  company: string;
  latitude: number;
  longitude: number;
  distance_miles: number;
  salary_range: string;
  tier: 'conservative' | 'optimal' | 'stretch';
  commute_options: {
    driving: { time_minutes: number; cost_monthly: number };
    transit: { time_minutes: number; cost_monthly: number };
    walking: { time_minutes: number; cost_monthly: number };
  };
}

interface MapState {
  userLocation: { lat: number; lng: number };
  selectedRadius: number;
  jobs: JobLocation[];
  selectedJob: JobLocation | null;
  commuteMode: 'driving' | 'transit' | 'walking';
  showSalaryHeatmap: boolean;
}
```

## API Integration

### Required Endpoints

#### 1. Jobs in Radius
```typescript
POST /api/risk/jobs-in-radius
{
  "user_location": { "lat": number, "lng": number },
  "radius_miles": number,
  "include_commute_data": boolean
}

Response:
{
  "jobs": JobLocation[],
  "total_count": number,
  "radius_miles": number
}
```

#### 2. Location Geocoding
```typescript
POST /api/location/geocode
{
  "zipcode": string
}

Response:
{
  "latitude": number,
  "longitude": number,
  "formatted_address": string
}
```

### Analytics Endpoints

#### Track User Interactions
```typescript
POST /api/analytics/user-behavior/track-interaction
{
  "event_type": string,
  "user_id": string,
  "session_id": string,
  "page_url": string,
  "interaction_data": object,
  "timestamp": string
}
```

## Environment Variables

```bash
# Google Maps API Key
REACT_APP_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

## Usage

```tsx
import LocationIntelligenceMap from './components/LocationIntelligenceMap';

function App() {
  return (
    <div className="container mx-auto p-4">
      <LocationIntelligenceMap className="mb-8" />
    </div>
  );
}
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes for styling |

## State Management

The component uses React hooks for state management:

- **`useState`**: Local component state for map data and UI state
- **`useRef`**: References to map instances and DOM elements
- **`useCallback`**: Optimized event handlers and functions
- **`useEffect`**: Side effects for map initialization and data fetching

## Error Handling

### Graceful Degradation
- **Map Load Failure**: Fallback to error message with retry option
- **Geolocation Failure**: Automatic fallback to zipcode-based location
- **API Errors**: User-friendly error messages with retry functionality
- **Network Issues**: Offline state handling and retry mechanisms

### Error Types
- **Map Initialization Errors**: Google Maps API failures
- **Geolocation Errors**: Permission denied or timeout
- **API Errors**: Network or server errors
- **Data Validation Errors**: Invalid job data or coordinates

## Performance Optimizations

### Map Performance
- **Lazy Loading**: Google Maps script loaded only when needed
- **Marker Clustering**: Efficient rendering of large job datasets
- **Viewport Culling**: Only render visible markers
- **Debounced Updates**: Prevent excessive API calls during radius changes

### Memory Management
- **Marker Cleanup**: Proper cleanup of map markers
- **Event Listener Cleanup**: Remove event listeners on unmount
- **Reference Management**: Proper cleanup of map references

## Testing

### Unit Tests
```bash
npm test LocationIntelligenceMap
```

### Integration Tests
```bash
npm run test:integration
```

### E2E Tests
```bash
npm run test:e2e
```

## Browser Support

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

## Dependencies

```json
{
  "react": "^18.2.0",
  "lucide-react": "^0.263.1"
}
```

## Development Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Set Environment Variables**
   ```bash
   cp .env.example .env
   # Add your Google Maps API key
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

## Deployment Considerations

### Google Maps API
- **API Key Security**: Use environment variables, never commit keys
- **Domain Restrictions**: Restrict API key to production domains
- **Usage Monitoring**: Monitor API usage and costs
- **Fallback Strategy**: Implement fallback for API failures

### Performance
- **CDN Integration**: Use CDN for static assets
- **Image Optimization**: Optimize map marker icons
- **Bundle Size**: Monitor bundle size impact

### Security
- **CORS Configuration**: Proper CORS setup for API calls
- **Input Validation**: Validate all user inputs
- **XSS Prevention**: Sanitize user-generated content

## Troubleshooting

### Common Issues

1. **Map Not Loading**
   - Check Google Maps API key
   - Verify network connectivity
   - Check browser console for errors

2. **Geolocation Not Working**
   - Check browser permissions
   - Verify HTTPS connection
   - Check fallback zipcode functionality

3. **Jobs Not Displaying**
   - Check API endpoint availability
   - Verify data format
   - Check network requests in dev tools

### Debug Mode

Enable debug mode by setting:
```javascript
localStorage.setItem('debug_location_map', 'true');
```

## Future Enhancements

- **Mapbox Integration**: Alternative mapping service support
- **Heatmap Visualization**: Salary and opportunity density heatmaps
- **Advanced Filtering**: Industry, company size, remote options
- **Route Optimization**: Multi-stop commute planning
- **Offline Support**: Cached map data for offline viewing
- **Real-time Updates**: WebSocket integration for live job updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This component is part of the Mingus Application and is proprietary software.
