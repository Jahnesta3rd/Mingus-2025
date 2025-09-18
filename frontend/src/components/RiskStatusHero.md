# RiskStatusHero Component

A React component that displays real-time career risk status with dynamic UI states, integrating with the existing risk analytics API.

## Features

### Visual States
- **Secure** (Green) - Career on track, stay prepared
- **Watchful** (Amber) - Market changes detected, strategic positioning recommended  
- **Action Needed** (Orange) - Career risk identified, proactive steps recommended
- **Urgent** (Red) - High risk detected, immediate action required

### Key Components
- **Animated Circular Progress Ring** - Shows risk score with smooth animations
- **Primary Threat Preview** - Displays the most critical risk factor
- **Context-Aware CTA Buttons** - Different actions based on risk level
- **Emergency Indicators** - Visual alerts for urgent situations
- **Loading & Error States** - Proper UX patterns for all states

### Accessibility Features
- ARIA labels for screen readers
- Keyboard navigation support
- Focus management
- Semantic HTML structure
- WCAG 2.1 AA compliance

### Analytics Integration
- Risk hero viewed events
- CTA click tracking
- Risk level analytics
- User interaction metrics

## API Integration

### Endpoints Used
- `POST /api/risk/assess-and-track` - Fetches risk assessment data
- `POST /api/analytics/user-behavior/track-interaction` - Tracks user interactions

### Data Flow
1. Component mounts and calls risk assessment API
2. Displays appropriate visual state based on risk level
3. Tracks analytics events for user interactions
4. Handles navigation based on risk level and available features

## Usage

```tsx
import RiskStatusHero from './components/RiskStatusHero';

// Basic usage
<RiskStatusHero />

// With custom className
<RiskStatusHero className="mb-8" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| className | string | '' | Additional CSS classes |

## Dependencies

- React 18+
- TypeScript
- Tailwind CSS
- Lucide React (for icons)

## Mobile Responsiveness

The component is fully responsive with:
- Touch-friendly interactions
- Adaptive layouts for different screen sizes
- Optimized typography and spacing
- Mobile-first design approach

## Error Handling

- Graceful fallback for API failures
- Retry functionality for failed requests
- Loading states during data fetching
- User-friendly error messages

## Performance

- Optimized animations (60fps target)
- Efficient re-renders
- Lazy loading of heavy components
- Reduced motion support for accessibility
