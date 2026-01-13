# Commute Cost Calculator for Mingus Career Section

## Overview

The Commute Cost Calculator is a comprehensive React component system designed to help users evaluate job opportunities with true compensation calculations that include transportation costs. This system integrates seamlessly with the existing Mingus career planning components and job evaluation system.

## Key Features

### 🚗 Real-Time Commute Cost Calculation
- **Address Autocomplete**: Google Places API integration for job and home location input
- **Distance Calculation**: Accurate route distance and duration using Google Maps API
- **Multi-Vehicle Support**: Calculate costs for different vehicles in user's fleet
- **Cost Breakdown**: Detailed analysis of fuel, maintenance, depreciation, insurance, parking, and tolls

### 💰 True Compensation Analysis
- **Salary vs. Transportation**: Calculate actual take-home compensation after commute costs
- **Annual Impact**: Show yearly financial impact of commute decisions
- **Time Value**: Convert commute time to monetary value
- **Percentage Analysis**: Show commute costs as percentage of salary

### 📊 Vehicle Comparison
- **Side-by-Side Analysis**: Compare costs across multiple vehicles
- **Cost Per Mile**: Detailed breakdown of transportation expenses
- **Fuel Efficiency Impact**: See how vehicle choice affects total costs
- **Scenario Planning**: Test different commute scenarios

### 💾 Scenario Management
- **Save Scenarios**: Store commute calculations for future reference
- **Load Scenarios**: Quickly access previously calculated commutes
- **Scenario Comparison**: Compare different job/commute combinations
- **Integration**: Seamlessly integrate with job recommendations

## Components

### 1. CommuteCostCalculator.tsx
Main component for commute cost calculations.

**Features:**
- Job location input with address autocomplete
- Home location input with address autocomplete
- Vehicle selection from user's fleet
- Real-time cost calculation
- True compensation display
- Save/load scenario functionality

**Props:**
```typescript
interface CommuteCostCalculatorProps {
  jobOffer?: JobOffer;
  vehicles: Vehicle[];
  onSaveScenario: (scenario: CommuteScenario) => void;
  onLoadScenario: (scenarioId: string) => void;
  className?: string;
}
```

### 2. CareerCommuteIntegration.tsx
Integration component that connects commute analysis with job recommendations.

**Features:**
- Job recommendation display with commute analysis buttons
- Modal integration for commute calculator
- Saved scenarios management
- Career planning integration

**Props:**
```typescript
interface CareerCommuteIntegrationProps {
  jobRecommendations: JobRecommendation[];
  vehicles: Vehicle[];
  onSaveScenario: (scenario: CommuteScenario) => void;
  onLoadScenario: (scenarioId: string) => void;
  className?: string;
}
```

## API Endpoints

### Commute Endpoints (`/api/commute/`)

#### GET `/scenarios`
Retrieve all saved commute scenarios for the user.

**Response:**
```json
{
  "success": true,
  "scenarios": [
    {
      "id": "scenario_123",
      "name": "Tech Job - Honda Civic",
      "job_location": {...},
      "home_location": {...},
      "vehicle": {...},
      "commute_details": {...},
      "costs": {...},
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST `/scenarios`
Save a new commute scenario.

**Request Body:**
```json
{
  "id": "scenario_123",
  "name": "Tech Job - Honda Civic",
  "job_location": {
    "address": "123 Tech Street, San Francisco, CA",
    "coordinates": {"lat": 37.7749, "lng": -122.4194}
  },
  "home_location": {
    "address": "456 Home Ave, Oakland, CA",
    "coordinates": {"lat": 37.8044, "lng": -122.2712}
  },
  "vehicle": {
    "id": "vehicle_1",
    "make": "Honda",
    "model": "Civic",
    "year": 2020,
    "mpg": 32,
    "fuel_type": "gasoline"
  },
  "commute_details": {
    "distance": 15.5,
    "duration": 25,
    "frequency": "daily",
    "days_per_week": 5
  },
  "costs": {
    "fuel": 45.50,
    "maintenance": 12.30,
    "depreciation": 8.75,
    "insurance": 15.00,
    "parking": 75.00,
    "tolls": 5.25,
    "total": 161.80
  }
}
```

#### DELETE `/scenarios/<scenario_id>`
Delete a specific commute scenario.

#### GET `/vehicles`
Retrieve user's vehicles for commute calculations.

#### POST `/calculate`
Calculate commute costs between two locations.

**Request Body:**
```json
{
  "origin": {"lat": 37.7749, "lng": -122.4194},
  "destination": {"lat": 37.8044, "lng": -122.2712},
  "vehicle": {
    "id": "vehicle_1",
    "make": "Honda",
    "model": "Civic",
    "year": 2020,
    "mpg": 32,
    "fuel_type": "gasoline"
  },
  "days_per_week": 5
}
```

### Geocoding Endpoints (`/api/geocoding/`)

#### POST `/autocomplete`
Get address autocomplete suggestions.

**Request Body:**
```json
{
  "query": "123 Main Street"
}
```

**Response:**
```json
{
  "success": true,
  "suggestions": [
    {
      "description": "123 Main Street, New York, NY, USA",
      "place_id": "ChIJ...",
      "formatted_address": "123 Main Street, New York, NY, USA"
    }
  ]
}
```

#### POST `/geocode`
Geocode an address to get coordinates.

**Request Body:**
```json
{
  "address": "123 Main Street, New York, NY"
}
```

**Response:**
```json
{
  "success": true,
  "coordinates": {"lat": 40.7128, "lng": -74.0060},
  "formatted_address": "123 Main Street, New York, NY, USA"
}
```

#### POST `/distance`
Calculate distance and duration between two points.

**Request Body:**
```json
{
  "origin": {"lat": 40.7128, "lng": -74.0060},
  "destination": {"lat": 40.7589, "lng": -73.9851}
}
```

**Response:**
```json
{
  "success": true,
  "distance": 5.2,
  "duration": 12
}
```

## Cost Calculation Logic

### Fuel Costs
```typescript
const fuelCostPerMile = fuelPrice / vehicle.mpg;
const fuelCost = weeklyDistance * fuelCostPerMile;
```

### Maintenance Costs
Based on vehicle age and mileage:
- **New vehicles (0-5 years)**: $0.08 per mile
- **Mid-age vehicles (5-10 years)**: $0.10 per mile
- **Older vehicles (10+ years)**: $0.15 per mile

### Depreciation
Based on vehicle age:
- **New vehicles (0-5 years)**: 12% per mile
- **Mid-age vehicles (5-10 years)**: 8% per mile
- **Older vehicles (10+ years)**: 5% per mile

### Additional Costs
- **Insurance**: $500/month prorated for commute days
- **Parking**: $15/day (configurable)
- **Tolls**: $0.05/mile (configurable)

## Integration with Existing Systems

### Job Recommendation System
The commute calculator integrates with the existing three-tier job recommendation system:

1. **Conservative Tier**: Lower commute costs, established locations
2. **Optimal Tier**: Balanced commute costs with growth potential
3. **Stretch Tier**: Higher commute costs for career advancement

### Vehicle Management
Integrates with the existing vehicle setup system:
- Uses vehicle data from `VehicleSetup.tsx`
- Leverages MSA-based pricing from location intelligence
- Incorporates vehicle maintenance predictions

### Career Planning
Seamlessly integrates with:
- Job recommendation tiers
- Skills gap analysis
- Application strategy planning
- Career advancement potential

## Usage Examples

### Basic Commute Calculation
```typescript
import CommuteCostCalculator from './components/CommuteCostCalculator';

const MyComponent = () => {
  const vehicles = [
    {
      id: 'vehicle_1',
      make: 'Honda',
      model: 'Civic',
      year: 2020,
      mpg: 32,
      fuelType: 'gasoline',
      currentMileage: 25000,
      monthlyMiles: 1200
    }
  ];

  const handleSaveScenario = (scenario) => {
    console.log('Saved scenario:', scenario);
  };

  return (
    <CommuteCostCalculator
      vehicles={vehicles}
      onSaveScenario={handleSaveScenario}
      onLoadScenario={(id) => console.log('Load scenario:', id)}
    />
  );
};
```

### Career Integration
```typescript
import CareerCommuteIntegration from './components/CareerCommuteIntegration';

const CareerPage = () => {
  const jobRecommendations = [
    // Job recommendation data
  ];

  return (
    <CareerCommuteIntegration
      jobRecommendations={jobRecommendations}
      vehicles={vehicles}
      onSaveScenario={handleSaveScenario}
      onLoadScenario={handleLoadScenario}
    />
  );
};
```

## Configuration

### Environment Variables
```bash
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### Database Setup
The system uses SQLite for scenario storage:
- `commute_scenarios` table for saved scenarios
- `user_vehicles` table for vehicle data
- Automatic database initialization on first run

## Performance Considerations

### Caching
- Address autocomplete results cached for 1 hour
- Distance calculations cached for 24 hours
- Vehicle cost calculations cached per session

### API Rate Limits
- Google Maps API: 1000 requests/day (free tier)
- Implemented debouncing for autocomplete (500ms delay)
- Batch processing for multiple calculations

### Mobile Optimization
- Responsive design for mobile devices
- Touch-friendly interface elements
- Optimized for mobile data usage

## Error Handling

### Graceful Degradation
- Fallback to mock data when APIs are unavailable
- Offline mode with cached calculations
- Clear error messages for user guidance

### Validation
- Address format validation
- Vehicle data validation
- Cost calculation bounds checking

## Future Enhancements

### Planned Features
- **Public Transit Integration**: Calculate costs for bus/train commutes
- **Rideshare Analysis**: Compare Uber/Lyft costs
- **Carbon Footprint**: Environmental impact calculations
- **Time Value Analysis**: Convert commute time to monetary value
- **Remote Work Impact**: Analyze hybrid work scenarios

### API Improvements
- **Batch Calculations**: Calculate multiple scenarios at once
- **Historical Data**: Track commute cost trends over time
- **Predictive Analytics**: Forecast future commute costs
- **Integration APIs**: Connect with other financial planning tools

## Support and Maintenance

### Monitoring
- API usage tracking
- Error rate monitoring
- Performance metrics
- User interaction analytics

### Updates
- Regular API key rotation
- Cost calculation algorithm updates
- New vehicle type support
- Enhanced address autocomplete

This comprehensive commute cost calculator system provides users with the tools they need to make informed career decisions by understanding the true financial impact of their commute choices.
