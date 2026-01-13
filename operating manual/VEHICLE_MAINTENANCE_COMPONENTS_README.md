# Vehicle Maintenance Prediction Components

## Overview

This document describes the React components created for vehicle maintenance predictions in the Mingus app. These components provide a comprehensive solution for predictive vehicle maintenance, financial planning, and mobile-optimized user experience.

## Components Created

### 1. MaintenanceForecast Component
**File:** `MaintenanceForecast.tsx`

A comprehensive timeline component showing upcoming vehicle maintenance services with filtering, sorting, and priority management.

#### Features:
- **Timeline Format**: Chronological display of upcoming services
- **Priority Color Coding**: Visual indicators for routine, recommended, and urgent services
- **Filtering & Sorting**: Multiple filter options (priority, timeframe) and sort options (date, cost, priority)
- **Confidence Indicators**: Progress bars showing prediction confidence levels
- **Service Metadata**: Mileage, dates, costs, and service history
- **Interactive Elements**: Clickable service items with hover effects

#### Props:
```typescript
interface MaintenanceForecastProps {
  vehicleId?: string;
  className?: string;
  onServiceClick?: (service: MaintenanceItem) => void;
}
```

### 2. ServiceCard Component
**File:** `ServiceCard.tsx`

Detailed individual service cards with cost estimates, service provider recommendations, and booking functionality.

#### Features:
- **Service Details**: Complete service information with descriptions
- **Cost Breakdown**: Estimated costs with confidence indicators
- **Service Providers**: Recommended providers with ratings, distances, and pricing
- **Booking Integration**: Direct booking and quote request functionality
- **Expandable Content**: Collapsible provider listings
- **Priority Indicators**: Visual priority and urgency indicators

#### Props:
```typescript
interface ServiceCardProps {
  service: MaintenanceItem;
  className?: string;
  onBookService?: (serviceId: string, providerId: string) => void;
  onGetQuote?: (serviceId: string) => void;
  onScheduleReminder?: (serviceId: string) => void;
}
```

### 3. EmergencyFundRecommendations Component
**File:** `EmergencyFundRecommendations.tsx`

Financial planning component for emergency fund recommendations based on potential major repairs.

#### Features:
- **Fund Analysis**: Current vs recommended emergency fund amounts
- **Major Repair Predictions**: Analysis of potential high-cost repairs
- **Monthly Goals**: Calculated monthly contribution recommendations
- **Priority Actions**: Step-by-step action items for fund building
- **Risk Assessment**: Risk level indicators based on repair predictions
- **Progress Tracking**: Visual progress indicators for fund goals

#### Props:
```typescript
interface EmergencyFundRecommendationsProps {
  vehicleId?: string;
  className?: string;
  onSetGoal?: (goal: EmergencyFundRecommendation) => void;
}
```

### 4. MaintenanceCashFlowIntegration Component
**File:** `MaintenanceCashFlowIntegration.tsx`

Integration component that displays maintenance costs within the existing cash flow forecast system.

#### Features:
- **Monthly Breakdown**: Month-by-month maintenance cost projections
- **Cost Categorization**: Routine vs major repair cost separation
- **Chart & List Views**: Multiple visualization options
- **Summary Statistics**: Total costs, averages, and peak months
- **Service Details**: Individual service listings per month
- **Integration Notes**: Clear connection to main cash flow system

#### Props:
```typescript
interface CashFlowIntegrationProps {
  vehicleId?: string;
  className?: string;
  onViewDetails?: (month: string) => void;
}
```

### 5. MobileMaintenanceCards Component
**File:** `MobileMaintenanceCards.tsx`

Mobile-optimized swipeable card interface for maintenance services.

#### Features:
- **Swipe Navigation**: Touch-based card swiping
- **Card Indicators**: Progress dots and navigation controls
- **Mobile Layout**: Optimized for mobile screens
- **Touch Interactions**: Tap to view details, swipe to navigate
- **Service Providers**: Mobile-friendly provider information
- **Quick Actions**: Book service and get quote buttons

#### Props:
```typescript
interface MobileMaintenanceCardsProps {
  cards: MaintenanceCard[];
  className?: string;
  onCardSwipe?: (direction: 'left' | 'right', cardId: string) => void;
  onCardTap?: (card: MaintenanceCard) => void;
  onBookService?: (cardId: string) => void;
  onGetQuote?: (cardId: string) => void;
}
```

### 6. VehicleMaintenanceDashboard Component
**File:** `VehicleMaintenanceDashboard.tsx`

Main dashboard component that orchestrates all maintenance-related components.

#### Features:
- **Unified Interface**: Single entry point for all maintenance features
- **View Switching**: Tabbed interface for different views
- **Mobile Detection**: Automatic mobile/desktop layout switching
- **Quick Stats**: Summary statistics and alerts
- **Navigation**: Easy switching between forecast, services, emergency fund, and cash flow
- **Error Handling**: Comprehensive error states and loading indicators

#### Props:
```typescript
interface VehicleMaintenanceDashboardProps {
  vehicleId?: string;
  className?: string;
  isMobile?: boolean;
}
```

## Design Patterns

### Mingus Brand Integration
All components follow the established Mingus design system:

- **Color Scheme**: Violet/purple gradients (`from-violet-600 to-purple-600`)
- **Background**: Dark theme with `bg-slate-800/50` and backdrop blur effects
- **Borders**: `border-slate-700/50` with transparency effects
- **Typography**: White text with gray variants for secondary information
- **Interactive Elements**: Violet hover states and focus rings

### Priority Color Coding
Consistent color coding across all components:

- **Routine**: Green (`text-green-400`, `bg-green-400/10`)
- **Recommended**: Yellow (`text-yellow-400`, `bg-yellow-400/10`)
- **Urgent**: Red (`text-red-400`, `bg-red-400/10`)

### Mobile Optimization
- **Touch Targets**: Minimum 44px touch targets for mobile
- **Swipe Gestures**: Native touch support for card navigation
- **Responsive Layout**: Grid systems that adapt to screen size
- **Mobile Navigation**: Bottom navigation for mobile users

## Data Types

### MaintenanceItem Interface
```typescript
interface MaintenanceItem {
  id: string;
  service: string;
  description: string;
  predictedDate: string;
  estimatedCost: number;
  priority: 'routine' | 'recommended' | 'urgent';
  category: 'oil_change' | 'brake_service' | 'tire_rotation' | 'engine_service' | 'transmission' | 'other';
  confidence: number;
  mileage: number;
  isOverdue: boolean;
  lastServiceDate?: string;
  nextServiceMileage?: number;
  provider?: ServiceProvider;
}
```

### ServiceProvider Interface
```typescript
interface ServiceProvider {
  id: string;
  name: string;
  rating: number;
  distance: number;
  price: number;
  phone: string;
  address: string;
  isRecommended: boolean;
  specialties: string[];
}
```

## Usage Examples

### Basic Dashboard Usage
```tsx
import VehicleMaintenanceDashboard from './components/VehicleMaintenanceDashboard';

function App() {
  return (
    <VehicleMaintenanceDashboard 
      vehicleId="123"
      isMobile={window.innerWidth < 768}
    />
  );
}
```

### Individual Component Usage
```tsx
import MaintenanceForecast from './components/MaintenanceForecast';
import ServiceCard from './components/ServiceCard';

function MaintenancePage() {
  const handleServiceClick = (service) => {
    console.log('Service clicked:', service);
  };

  return (
    <div>
      <MaintenanceForecast 
        vehicleId="123"
        onServiceClick={handleServiceClick}
      />
      <ServiceCard 
        service={selectedService}
        onBookService={(id, providerId) => console.log('Booking:', id, providerId)}
      />
    </div>
  );
}
```

### Mobile Cards Usage
```tsx
import MobileMaintenanceCards from './components/MobileMaintenanceCards';

function MobileMaintenancePage() {
  return (
    <MobileMaintenanceCards
      cards={maintenanceData}
      onCardSwipe={(direction, cardId) => console.log('Swiped:', direction, cardId)}
      onBookService={(cardId) => console.log('Booking:', cardId)}
    />
  );
}
```

## Integration Points

### API Integration
Components are designed to integrate with the existing Mingus backend:

- **Maintenance Prediction Engine**: `/api/vehicles/{id}/maintenance-predictions`
- **Cash Flow Forecast**: `/api/vehicles/{id}/maintenance-cash-flow`
- **Service Providers**: `/api/service-providers`
- **Emergency Fund**: `/api/financial/emergency-fund-recommendations`

### State Management
Components use React hooks for local state management:

- `useState` for component state
- `useEffect` for data fetching
- `useRef` for DOM references (mobile cards)
- Custom event handlers for user interactions

### Error Handling
Comprehensive error handling throughout:

- Loading states with spinners
- Error messages with retry options
- Graceful degradation for missing data
- Network error handling

## Accessibility Features

### WCAG 2.1 AA Compliance
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Support**: ARIA labels and semantic HTML
- **Color Contrast**: Sufficient contrast ratios
- **Focus Management**: Clear focus indicators
- **Alternative Text**: Descriptive text for icons and images

### Mobile Accessibility
- **Touch Targets**: Minimum 44px touch targets
- **Gesture Support**: Native touch gestures
- **Voice Over**: iOS VoiceOver support
- **TalkBack**: Android TalkBack support

## Performance Considerations

### Optimization Strategies
- **Lazy Loading**: Components load data on demand
- **Memoization**: React.memo for expensive components
- **Virtual Scrolling**: For large lists of services
- **Image Optimization**: Lazy loading for service provider images
- **Bundle Splitting**: Code splitting for mobile components

### Data Fetching
- **Caching**: Intelligent caching of maintenance data
- **Background Updates**: Periodic data refresh
- **Offline Support**: Graceful offline degradation
- **Error Recovery**: Automatic retry mechanisms

## Testing Strategy

### Unit Tests
- Component rendering tests
- Props validation tests
- Event handler tests
- State management tests

### Integration Tests
- API integration tests
- User interaction tests
- Mobile gesture tests
- Cross-browser compatibility

### Accessibility Tests
- Screen reader testing
- Keyboard navigation testing
- Color contrast testing
- Mobile accessibility testing

## Future Enhancements

### Planned Features
- **Push Notifications**: Service reminders
- **Calendar Integration**: Service scheduling
- **Payment Integration**: Direct payment processing
- **Service History**: Complete maintenance history
- **Predictive Analytics**: Advanced ML predictions

### Scalability Considerations
- **Multi-Vehicle Support**: Support for multiple vehicles
- **Fleet Management**: Commercial fleet features
- **API Rate Limiting**: Backend optimization
- **Caching Strategy**: Advanced caching mechanisms

## Conclusion

The vehicle maintenance prediction components provide a comprehensive solution for predictive vehicle maintenance within the Mingus app. The components are designed with mobile-first principles, follow Mingus design patterns, and integrate seamlessly with the existing cash flow forecast system.

The modular architecture allows for easy customization and extension, while the comprehensive error handling and accessibility features ensure a robust user experience across all devices and user abilities.
