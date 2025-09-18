# Location Intelligence Map Setup Guide

## Environment Configuration

Create a `.env` file in the frontend directory with the following variables:

```bash
# Google Maps API Key
REACT_APP_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# API Base URL
REACT_APP_API_BASE_URL=http://localhost:5000

# Environment
NODE_ENV=development
```

## Google Maps API Setup

### 1. Get API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Maps JavaScript API
   - Directions API
   - Geocoding API
   - Places API (optional)
4. Create credentials (API Key)
5. Restrict the API key to your domains

### 2. API Key Restrictions
For production, restrict your API key to:
- **HTTP referrers**: Your production domain
- **IP addresses**: Your server IPs (if applicable)

### 3. Billing Setup
- Google Maps requires billing to be enabled
- Set up usage quotas and alerts
- Monitor usage in the Cloud Console

## Backend API Endpoints

The Location Intelligence Map requires the following backend endpoints:

### 1. Jobs in Radius
```typescript
POST /api/risk/jobs-in-radius
Content-Type: application/json

{
  "user_location": {
    "lat": 37.7749,
    "lng": -122.4194
  },
  "radius_miles": 10,
  "include_commute_data": true
}

Response:
{
  "jobs": [
    {
      "id": "job_123",
      "title": "Software Engineer",
      "company": "Tech Corp",
      "latitude": 37.7849,
      "longitude": -122.4094,
      "distance_miles": 2.5,
      "salary_range": "$80k - $120k",
      "tier": "optimal",
      "commute_options": {
        "driving": {
          "time_minutes": 15,
          "cost_monthly": 200
        },
        "transit": {
          "time_minutes": 25,
          "cost_monthly": 80
        },
        "walking": {
          "time_minutes": 45,
          "cost_monthly": 0
        }
      }
    }
  ],
  "total_count": 1,
  "radius_miles": 10
}
```

### 2. Location Geocoding
```typescript
POST /api/location/geocode
Content-Type: application/json

{
  "zipcode": "94102"
}

Response:
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "formatted_address": "San Francisco, CA 94102, USA"
}
```

### 3. Analytics Tracking
```typescript
POST /api/analytics/user-behavior/track-interaction
Content-Type: application/json

{
  "event_type": "location_map_jobs_loaded",
  "user_id": "user_123",
  "session_id": "session_456",
  "page_url": "/location-map-test",
  "interaction_data": {
    "radius": 10,
    "jobs_found": 5,
    "user_location_type": "coordinates"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Testing the Component

### 1. Start the Development Server
```bash
cd frontend
npm run dev
```

### 2. Navigate to Test Page
Visit: `http://localhost:5173/location-map-test`

### 3. Test Features
- **Location Detection**: Allow location access when prompted
- **Radius Controls**: Test different radius values
- **Job Markers**: Click on markers to see job details
- **Commute Modes**: Switch between driving, transit, and walking
- **Responsive Design**: Test on different screen sizes

## Troubleshooting

### Common Issues

1. **Map Not Loading**
   - Check if Google Maps API key is set
   - Verify API key has correct permissions
   - Check browser console for errors

2. **Geolocation Not Working**
   - Ensure HTTPS connection (required for geolocation)
   - Check browser permissions
   - Test fallback zipcode functionality

3. **Jobs Not Displaying**
   - Check if backend API is running
   - Verify API endpoint responses
   - Check network requests in browser dev tools

4. **CORS Errors**
   - Configure CORS on backend to allow frontend domain
   - Check API headers and preflight requests

### Debug Mode

Enable debug logging:
```javascript
// In browser console
localStorage.setItem('debug_location_map', 'true');
```

## Production Deployment

### 1. Environment Variables
Set production environment variables:
```bash
REACT_APP_GOOGLE_MAPS_API_KEY=prod_api_key_here
REACT_APP_API_BASE_URL=https://your-api-domain.com
NODE_ENV=production
```

### 2. API Key Security
- Never commit API keys to version control
- Use environment variables or secure key management
- Restrict API keys to production domains
- Monitor API usage and costs

### 3. Performance Optimization
- Enable gzip compression
- Use CDN for static assets
- Implement proper caching headers
- Monitor bundle size

### 4. Monitoring
- Set up error tracking (Sentry, etc.)
- Monitor API response times
- Track user interactions and errors
- Set up alerts for API failures

## Security Considerations

1. **API Key Protection**
   - Restrict API keys to specific domains
   - Use server-side proxy for sensitive operations
   - Monitor and rotate keys regularly

2. **Input Validation**
   - Validate all user inputs
   - Sanitize location data
   - Implement rate limiting

3. **Data Privacy**
   - Comply with GDPR/CCPA requirements
   - Anonymize user location data
   - Implement proper data retention policies

## Cost Optimization

1. **API Usage**
   - Implement caching for repeated requests
   - Use batch requests when possible
   - Monitor usage quotas and alerts

2. **Map Optimization**
   - Use appropriate zoom levels
   - Implement marker clustering for large datasets
   - Optimize map styling and features

3. **Data Management**
   - Cache job data appropriately
   - Implement efficient data structures
   - Use pagination for large datasets
