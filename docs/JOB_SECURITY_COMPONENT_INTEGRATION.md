# Job Security Analysis Component Integration Guide

## Overview

The `JobSecurityAnalysis` component provides a comprehensive, responsive interface for displaying job security scores, risk factors, trends, and personalized recommendations. It integrates seamlessly with your existing Mingus health dashboard and supports drill-down functionality for detailed analysis.

## Features

- **Circular Progress Indicator**: Visual representation of overall job security score (0-100)
- **Component Breakdown**: Detailed view of user perception vs external data scores
- **Risk Factor Analysis**: Color-coded risk factors with severity levels
- **Positive Indicators**: Highlighting favorable conditions
- **Personalized Recommendations**: Actionable advice based on score analysis
- **Trend Analysis**: 12-week historical data with change indicators
- **Drill-Down Functionality**: Detailed analysis of individual components
- **Mobile-First Design**: Fully responsive across all device sizes
- **Accessibility**: WCAG compliant with proper ARIA labels

## Component Structure

### Main Component: `JobSecurityAnalysis.tsx`

```tsx
import JobSecurityAnalysis from './components/dashboard/JobSecurityAnalysis';

<JobSecurityAnalysis
  data={jobSecurityData}
  onDrillDown={(component) => handleDrillDown(component)}
  className="custom-styles"
/>
```

### Drill-Down Component: `JobSecurityDrillDown.tsx`

```tsx
import JobSecurityDrillDown from './components/dashboard/JobSecurityDrillDown';

<JobSecurityDrillDown
  data={drillDownData}
  onClose={() => setShowDrillDown(false)}
/>
```

## Data Structure

### JobSecurityData Interface

```typescript
interface JobSecurityData {
  overall_score: number;           // 0-100 overall job security score
  user_perception_score: number;   // 0-100 user perception component
  external_data_score: number;     // 0-100 external data component
  confidence_level: number;        // 0-100 confidence in analysis
  risk_factors: RiskFactor[];      // Array of identified risk factors
  positive_indicators: string[];   // Array of positive indicators
  recommendations: Recommendation[]; // Array of personalized recommendations
  trend_data: TrendPoint[];        // Historical score data
  last_updated: string;            // ISO timestamp of last update
  employer_name?: string;          // Optional employer name
  industry_sector?: string;        // Optional industry sector
  location?: string;               // Optional location
}
```

### Supporting Interfaces

```typescript
interface RiskFactor {
  category: string;           // Risk category (e.g., "Local Layoffs")
  severity: 'low' | 'medium' | 'high';
  description: string;        // Detailed description
  impact_score: number;       // 0-100 impact on overall score
}

interface Recommendation {
  priority: 'high' | 'medium' | 'low';
  category: string;           // Recommendation category
  title: string;              // Short title
  description: string;        // Detailed description
  action_items: string[];     // Specific action items
}

interface TrendPoint {
  date: string;               // ISO date string
  score: number;              // Score for that date
  change?: number;            // Change from previous period
}
```

## Integration with Existing Dashboard

### 1. Add to Dashboard Layout

```tsx
// In your main dashboard component
import JobSecurityAnalysis from './components/dashboard/JobSecurityAnalysis';

const Dashboard = () => {
  const [jobSecurityData, setJobSecurityData] = useState<JobSecurityData | null>(null);
  const [showDrillDown, setShowDrillDown] = useState(false);
  const [drillDownData, setDrillDownData] = useState<any>(null);

  // Fetch job security data
  useEffect(() => {
    const fetchJobSecurityData = async () => {
      try {
        const response = await fetch('/api/career-wellness-checkin/latest');
        const data = await response.json();
        setJobSecurityData(data);
      } catch (error) {
        console.error('Failed to fetch job security data:', error);
      }
    };

    fetchJobSecurityData();
  }, []);

  const handleDrillDown = async (component: string) => {
    try {
      const response = await fetch(`/api/job-security/drill-down/${component}`);
      const data = await response.json();
      setDrillDownData(data);
      setShowDrillDown(true);
    } catch (error) {
      console.error('Failed to fetch drill-down data:', error);
    }
  };

  return (
    <div className="dashboard-layout">
      {/* Existing health cards */}
      <HealthCard />
      <FinancialCard />
      
      {/* Job Security Analysis */}
      {jobSecurityData && (
        <JobSecurityAnalysis
          data={jobSecurityData}
          onDrillDown={handleDrillDown}
          className="col-span-full lg:col-span-2"
        />
      )}

      {/* Drill-down modal */}
      {showDrillDown && drillDownData && (
        <JobSecurityDrillDown
          data={drillDownData}
          onClose={() => setShowDrillDown(false)}
        />
      )}
    </div>
  );
};
```

### 2. API Integration

#### Backend Endpoints Required

```python
# Django views for job security data
@api_view(['GET'])
def get_latest_job_security(request):
    """Get latest job security analysis for user"""
    user_id = request.user.id
    data = career_wellness_service.get_latest_analysis(user_id)
    return Response(data)

@api_view(['GET'])
def get_job_security_drill_down(request, component):
    """Get detailed drill-down data for specific component"""
    user_id = request.user.id
    data = career_wellness_service.get_drill_down_data(user_id, component)
    return Response(data)
```

#### URL Configuration

```python
# urls.py
urlpatterns = [
    path('api/career-wellness-checkin/latest/', views.get_latest_job_security),
    path('api/job-security/drill-down/<str:component>/', views.get_job_security_drill_down),
]
```

## Styling and Theming

### Tailwind CSS Classes Used

The component uses Tailwind CSS classes that are consistent with your existing Mingus design system:

- **Colors**: Blue, green, yellow, red for different risk levels
- **Spacing**: Consistent padding and margins
- **Typography**: Standard font weights and sizes
- **Borders**: Rounded corners and subtle borders
- **Shadows**: Consistent shadow system

### Custom Styling

You can override styles by passing a `className` prop:

```tsx
<JobSecurityAnalysis
  data={data}
  className="custom-border custom-shadow"
/>
```

## Mobile Responsiveness

The component is designed with a mobile-first approach:

- **Grid Layout**: Responsive grid that adapts to screen size
- **Touch Targets**: Adequate size for mobile interaction
- **Typography**: Readable on all screen sizes
- **Modal**: Full-screen modal on mobile devices

## Accessibility Features

- **ARIA Labels**: Proper labeling for screen readers
- **Keyboard Navigation**: Full keyboard support
- **Color Contrast**: WCAG AA compliant color ratios
- **Focus Management**: Proper focus handling in modals
- **Semantic HTML**: Proper heading hierarchy and landmarks

## Performance Considerations

### Data Fetching

- **Caching**: Implement client-side caching for job security data
- **Lazy Loading**: Load drill-down data only when needed
- **Error Handling**: Graceful handling of API failures

### Rendering Optimization

- **Memoization**: Use React.memo for expensive calculations
- **Virtual Scrolling**: For large trend datasets
- **Image Optimization**: Optimize any icons or images

## Error States

The component handles various error states gracefully:

```tsx
// Error state example
{!jobSecurityData ? (
  <div className="bg-gray-50 rounded-lg p-6 text-center">
    <p className="text-gray-500">Loading job security analysis...</p>
  </div>
) : jobSecurityData.error ? (
  <div className="bg-red-50 rounded-lg p-6 text-center">
    <p className="text-red-600">Unable to load job security data</p>
  </div>
) : (
  <JobSecurityAnalysis data={jobSecurityData} />
)}
```

## Testing

### Unit Tests

```tsx
// Example test for JobSecurityAnalysis component
import { render, screen, fireEvent } from '@testing-library/react';
import JobSecurityAnalysis from './JobSecurityAnalysis';

test('renders job security score correctly', () => {
  const mockData = {
    overall_score: 75,
    // ... other required fields
  };
  
  render(<JobSecurityAnalysis data={mockData} />);
  expect(screen.getByText('75')).toBeInTheDocument();
});

test('handles drill-down click', () => {
  const mockDrillDown = jest.fn();
  render(<JobSecurityAnalysis data={mockData} onDrillDown={mockDrillDown} />);
  
  fireEvent.click(screen.getByText('User Perception'));
  expect(mockDrillDown).toHaveBeenCalledWith('user_perception');
});
```

### Integration Tests

Test the complete flow from data fetching to drill-down:

```tsx
test('complete job security analysis flow', async () => {
  // Mock API responses
  server.use(
    rest.get('/api/career-wellness-checkin/latest', (req, res, ctx) => {
      return res(ctx.json(mockJobSecurityData));
    })
  );
  
  render(<Dashboard />);
  
  // Wait for data to load
  await screen.findByText('Job Security Analysis');
  
  // Test drill-down functionality
  fireEvent.click(screen.getByText('User Perception'));
  await screen.findByText('User Perception Analysis');
});
```

## Deployment Checklist

- [ ] Component files added to the project
- [ ] API endpoints implemented and tested
- [ ] Database migrations for job security data
- [ ] Integration with existing dashboard layout
- [ ] Error handling and loading states implemented
- [ ] Mobile responsiveness tested
- [ ] Accessibility audit completed
- [ ] Performance testing completed
- [ ] Unit and integration tests written
- [ ] Documentation updated

## Support and Maintenance

### Regular Updates

- **Data Freshness**: Ensure job security data is updated weekly
- **Score Accuracy**: Monitor and adjust scoring algorithms
- **User Feedback**: Collect and incorporate user feedback
- **Performance**: Monitor component performance metrics

### Troubleshooting

Common issues and solutions:

1. **Data not loading**: Check API endpoints and authentication
2. **Score not updating**: Verify data pipeline and caching
3. **Mobile display issues**: Test responsive breakpoints
4. **Accessibility issues**: Run accessibility audit tools

## Conclusion

The JobSecurityAnalysis component provides a comprehensive, user-friendly interface for job security insights. It integrates seamlessly with your existing Mingus dashboard and provides valuable insights to help users understand and improve their job security situation.

For additional support or customization, refer to the component source code or contact the development team. 