# Commute Cost Calculator Integration Guide

## Quick Start

### 1. Add to Existing Career Pages

```typescript
import CareerCommuteIntegration from '../components/CareerCommuteIntegration';

// In your career page component
const CareerPage = () => {
  const [jobRecommendations, setJobRecommendations] = useState([]);
  const [vehicles, setVehicles] = useState([]);

  return (
    <div>
      {/* Your existing career content */}
      
      <CareerCommuteIntegration
        jobRecommendations={jobRecommendations}
        vehicles={vehicles}
        onSaveScenario={(scenario) => console.log('Saved:', scenario)}
        onLoadScenario={(id) => console.log('Loaded:', id)}
      />
    </div>
  );
};
```

### 2. Standalone Commute Calculator

```typescript
import CommuteCostCalculator from '../components/CommuteCostCalculator';

const CommutePage = () => {
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

  return (
    <CommuteCostCalculator
      vehicles={vehicles}
      onSaveScenario={(scenario) => saveScenario(scenario)}
      onLoadScenario={(id) => loadScenario(id)}
    />
  );
};
```

## API Integration

### 1. Register API Blueprints

Add to your Flask app initialization:

```python
from backend.api.commute_endpoints import commute_bp
from backend.api.geocoding_endpoints import geocoding_bp

app.register_blueprint(commute_bp)
app.register_blueprint(geocoding_bp)
```

### 2. Environment Variables

Add to your `.env` file:

```bash
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### 3. Database Initialization

The system automatically creates the required database tables on first run.

## Component Props

### CommuteCostCalculator Props

```typescript
interface CommuteCostCalculatorProps {
  jobOffer?: {
    id: string;
    title: string;
    company: string;
    location: string;
    salary: {
      min: number;
      max: number;
      median: number;
    };
    benefits: string[];
    remoteFriendly: boolean;
  };
  vehicles: Vehicle[];
  onSaveScenario: (scenario: CommuteScenario) => void;
  onLoadScenario: (scenarioId: string) => void;
  className?: string;
}
```

### CareerCommuteIntegration Props

```typescript
interface CareerCommuteIntegrationProps {
  jobRecommendations: JobRecommendation[];
  vehicles: Vehicle[];
  onSaveScenario: (scenario: CommuteScenario) => void;
  onLoadScenario: (scenarioId: string) => void;
  className?: string;
}
```

## Data Types

### Vehicle Type

```typescript
interface Vehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  mpg: number;
  fuelType: 'gasoline' | 'electric' | 'hybrid';
  currentMileage: number;
  monthlyMiles: number;
}
```

### CommuteScenario Type

```typescript
interface CommuteScenario {
  id: string;
  name: string;
  jobLocation: {
    address: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
  };
  homeLocation: {
    address: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
  };
  vehicle: {
    id: string;
    make: string;
    model: string;
    year: number;
    mpg: number;
    fuelType: 'gasoline' | 'electric' | 'hybrid';
  };
  commuteDetails: {
    distance: number;
    duration: number;
    frequency: 'daily' | 'weekly' | 'monthly';
    daysPerWeek: number;
  };
  costs: {
    fuel: number;
    maintenance: number;
    depreciation: number;
    insurance: number;
    parking: number;
    tolls: number;
    total: number;
  };
  createdAt: string;
  updatedAt: string;
}
```

## Styling Integration

The components use Tailwind CSS classes that match the existing Mingus design system:

- **Primary Colors**: `violet-600`, `purple-600`
- **Background**: `gray-900`, `gray-800`
- **Text**: `white`, `gray-400`
- **Accents**: `violet-400`, `green-400`, `orange-400`

## Error Handling

### Component Level

```typescript
const [error, setError] = useState<string | null>(null);

// Handle API errors
const handleApiError = (err: Error) => {
  setError(err.message);
  // Log to analytics
  trackError(err, { context: 'commute_calculation' });
};
```

### API Level

```python
try:
    # API logic
    return jsonify({'success': True, 'data': result})
except Exception as e:
    logger.error(f"API error: {e}")
    return jsonify({'success': False, 'error': str(e)}), 500
```

## Performance Optimization

### 1. Debounced API Calls

```typescript
const debouncedSearch = useCallback(
  debounce((query: string) => {
    searchAddresses(query);
  }, 500),
  []
);
```

### 2. Caching

```typescript
const [cache, setCache] = useState(new Map());

const getCachedResult = (key: string) => {
  return cache.get(key);
};

const setCachedResult = (key: string, value: any) => {
  setCache(prev => new Map(prev).set(key, value));
};
```

### 3. Lazy Loading

```typescript
const CommuteCalculator = lazy(() => import('./CommuteCostCalculator'));

// Use with Suspense
<Suspense fallback={<LoadingSpinner />}>
  <CommuteCalculator />
</Suspense>
```

## Testing

### Unit Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import CommuteCostCalculator from './CommuteCostCalculator';

test('renders commute calculator', () => {
  render(<CommuteCostCalculator vehicles={[]} onSaveScenario={jest.fn()} onLoadScenario={jest.fn()} />);
  expect(screen.getByText('Commute Cost Calculator')).toBeInTheDocument();
});
```

### Integration Tests

```typescript
test('calculates commute costs', async () => {
  const mockVehicles = [{
    id: '1',
    make: 'Honda',
    model: 'Civic',
    year: 2020,
    mpg: 32,
    fuelType: 'gasoline',
    currentMileage: 25000,
    monthlyMiles: 1200
  }];

  render(<CommuteCostCalculator vehicles={mockVehicles} onSaveScenario={jest.fn()} onLoadScenario={jest.fn()} />);
  
  // Test form interactions
  fireEvent.change(screen.getByLabelText('Job Location'), { target: { value: '123 Main St' } });
  fireEvent.change(screen.getByLabelText('Home Location'), { target: { value: '456 Home Ave' } });
  
  // Test calculation
  expect(screen.getByText('Weekly Commute Costs')).toBeInTheDocument();
});
```

## Deployment

### 1. Environment Setup

```bash
# Install dependencies
npm install

# Set environment variables
export GOOGLE_MAPS_API_KEY=your_key_here

# Run database migrations
python -c "from backend.api.commute_endpoints import init_commute_database; init_commute_database()"
```

### 2. Production Configuration

```python
# In your production config
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///mingus_commute.db')
```

### 3. Monitoring

```python
# Add to your monitoring setup
import logging

logger = logging.getLogger('commute_calculator')
logger.info('Commute calculator initialized')
```

## Troubleshooting

### Common Issues

1. **Google Maps API Key Missing**
   - Error: "Address autocomplete failed"
   - Solution: Set `GOOGLE_MAPS_API_KEY` environment variable

2. **Database Connection Issues**
   - Error: "Failed to save scenario"
   - Solution: Check database permissions and path

3. **CORS Issues**
   - Error: "Cross-origin request blocked"
   - Solution: Ensure `@cross_origin()` decorator is applied

### Debug Mode

```typescript
// Enable debug logging
const DEBUG = process.env.NODE_ENV === 'development';

if (DEBUG) {
  console.log('Commute calculation:', calculation);
}
```

## Support

For additional support or questions:

1. Check the comprehensive README: `COMMUTE_COST_CALCULATOR_README.md`
2. Review the API documentation in the endpoint files
3. Check the component prop types for integration guidance
4. Test with the provided example components

The commute cost calculator is designed to integrate seamlessly with the existing Mingus career planning system while providing powerful new capabilities for transportation cost analysis.
