# Mingus Assessment Components

A comprehensive React component library for the Mingus financial wellness assessment system. These components provide a complete user experience from assessment discovery to results and conversion.

## 🎯 Overview

The assessment system consists of five main components that work together to provide a seamless assessment experience:

1. **AssessmentLanding** - Landing page with available assessments
2. **AssessmentFlow** - Multi-step assessment form with progress tracking
3. **AssessmentQuestion** - Reusable question component for all input types
4. **AssessmentResults** - Results display with insights and recommendations
5. **ConversionModal** - Subscription conversion with payment integration

## 🚀 Features

### AssessmentLanding
- **Responsive Grid Layout**: 4 assessments on desktop, 2x2 on tablet, 1 column on mobile
- **Real-time Statistics**: Completion rates, average scores, and user counts from API
- **Trending Badges**: Dynamic badges based on actual usage data
- **Value Propositions**: Clear outcomes for each assessment type
- **Social Proof**: User statistics and completion metrics
- **Estimated Times**: Real completion times from user data

### AssessmentFlow
- **Multi-step Form**: Visual progress tracking with percentage completion
- **Auto-save**: Progress saved to localStorage with recovery on page reload
- **Real-time Validation**: Immediate feedback on form errors
- **Skip Logic**: Conditional questions based on previous answers
- **Mobile Optimized**: 44px minimum touch targets
- **Smooth Transitions**: Animated progress between steps
- **Back/Next Navigation**: Full form navigation with validation

### AssessmentQuestion
- **Multiple Input Types**: Text, email, number, select, radio, multi-select
- **Accessibility**: WCAG 2.1 AA compliant with proper ARIA labels
- **Validation**: Real-time validation with helpful error messages
- **Keyboard Navigation**: Full keyboard support for all input types
- **Screen Reader Support**: Proper semantic HTML and ARIA attributes
- **Mobile Touch Targets**: Minimum 44px touch areas

### AssessmentResults
- **Risk Level Display**: Color-coded indicators (red/yellow/green)
- **Score Visualization**: Animated progress bars and charts
- **Personalized Insights**: Specific recommendations from exact calculations
- **Cost Projections**: Dollar amounts with time frames
- **Social Comparison**: Percentile rankings vs other users
- **PDF Download**: Complete results export functionality
- **Social Sharing**: Native sharing with fallback to clipboard

### ConversionModal
- **Subscription Tiers**: Integration with $10, $20, $50 pricing
- **Countdown Timer**: 60-minute server-validated timer
- **Stripe Integration**: Payment processing with existing components
- **User Testimonials**: Real testimonials from database
- **Exit Intent Detection**: Emergency $19 offer on mouse leave
- **Mobile Checkout**: Optimized for mobile payment flow

## 🎨 Design System

### Colors
- **Primary Purple**: `#8A31FF` - Main brand color
- **Primary Green**: `#10b981` - Success/positive actions
- **Background**: `#f5f5f7` - Light gray background
- **Surface**: `#ffffff` - White cards and surfaces
- **Text**: `#333333` - Primary text color

### Typography
- **Primary Font**: Inter (400, 500, 600, 700, 900)
- **Secondary Font**: Open Sans (400, 600, 700)
- **Body Font**: System fonts with Inter fallback

### Spacing
- **Base Unit**: 8px
- **Small Gap**: 8px
- **Medium Gap**: 16px
- **Large Gap**: 24px
- **Extra Large Gap**: 32px

### Responsive Breakpoints
- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px - 1920px+
- **Large Desktop**: 1920px+

## 📦 Installation & Usage

### Prerequisites
- React 18+
- React Router 6+
- TypeScript 4.5+
- Tailwind CSS 3.0+

### Basic Usage

```jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AssessmentRoutes from './routes/assessmentRoutes';

function App() {
  return (
    <Router>
      <Routes>
        {/* Other routes */}
        <Route path="/assessments/*" element={<AssessmentRoutes />} />
      </Routes>
    </Router>
  );
}
```

### Individual Component Usage

```jsx
import AssessmentLanding from './components/assessments/AssessmentLanding';
import AssessmentFlow from './components/assessments/AssessmentFlow';
import AssessmentResults from './components/assessments/AssessmentResults';

// Landing page
<AssessmentLanding />

// Assessment flow (with routing)
<AssessmentFlow />

// Results page (with routing)
<AssessmentResults assessmentId="optional-id" />
```

## 🔌 API Integration

### Required Endpoints

#### GET /api/assessments/available
Returns list of available assessments with statistics.

```json
{
  "success": true,
  "assessments": [
    {
      "id": "uuid",
      "type": "ai_job_risk",
      "title": "AI Job Risk Assessment",
      "description": "Assess your job's vulnerability to AI automation",
      "estimated_duration_minutes": 10,
      "stats": {
        "total_attempts": 150,
        "completed_attempts": 120,
        "completion_rate": 80.0,
        "average_score": 65.5,
        "average_time_minutes": 8.2
      },
      "user_completed": false,
      "attempts_remaining": 3
    }
  ]
}
```

#### GET /api/assessments/{type}/questions
Returns assessment questions and configuration.

```json
{
  "id": "uuid",
  "type": "ai_job_risk",
  "title": "AI Job Risk Assessment",
  "description": "Assess your job's vulnerability to AI automation",
  "questions": [
    {
      "id": "job_title",
      "type": "text",
      "text": "What is your current job title?",
      "required": true,
      "validation": {
        "min": 2,
        "max": 100
      }
    }
  ],
  "estimated_duration_minutes": 10,
  "version": "1.0"
}
```

#### POST /api/assessments/{type}/submit
Submits assessment responses and returns results.

```json
{
  "responses": {
    "job_title": "Software Engineer",
    "industry": "Technology"
  },
  "time_spent_seconds": 480
}
```

#### GET /api/assessments/{id}/results
Returns detailed assessment results.

```json
{
  "id": "uuid",
  "assessment_type": "ai_job_risk",
  "score": 75,
  "risk_level": "medium",
  "insights": ["Your role has moderate AI automation risk"],
  "recommendations": ["Consider upskilling in AI-resistant skills"],
  "cost_projection": {
    "amount": 5000,
    "timeframe": "1 year",
    "currency": "USD"
  },
  "social_comparison": {
    "percentile": 65,
    "total_users": 1000,
    "message": "You scored higher than 65% of users"
  }
}
```

#### POST /api/assessments/convert
Handles subscription conversion.

```json
{
  "assessment_id": "uuid",
  "subscription_tier": "premium",
  "lead_id": "lead-uuid"
}
```

## 🧪 Testing

### Running Tests
```bash
npm test -- --testPathPattern=assessments
```

### Test Coverage
- **Unit Tests**: Individual component functionality
- **Integration Tests**: Complete assessment flow
- **Accessibility Tests**: WCAG 2.1 AA compliance
- **Mobile Tests**: Touch target validation
- **Error Handling**: Network failures and edge cases

### Test Structure
```
__tests__/
├── AssessmentComponents.test.js    # Main test suite
├── AssessmentLanding.test.js       # Landing page tests
├── AssessmentFlow.test.js          # Flow tests
├── AssessmentQuestion.test.js      # Question component tests
├── AssessmentResults.test.js       # Results tests
└── ConversionModal.test.js         # Modal tests
```

## ♿ Accessibility

### WCAG 2.1 AA Compliance
- **Color Contrast**: Minimum 4.5:1 ratio for normal text
- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: Proper ARIA labels and semantic HTML
- **Focus Management**: Visible focus indicators
- **Error Handling**: Clear error messages and recovery

### Accessibility Features
- **ARIA Labels**: Proper labeling for all interactive elements
- **Semantic HTML**: Correct heading hierarchy and landmarks
- **Focus Indicators**: Visible focus states for keyboard users
- **Error Announcements**: Screen reader announcements for errors
- **Reduced Motion**: Respects user motion preferences

## 📱 Mobile Optimization

### Touch Targets
- **Minimum Size**: 44px x 44px for all interactive elements
- **Spacing**: Adequate spacing between touch targets
- **Visual Feedback**: Clear touch feedback and states

### Responsive Design
- **Fluid Layouts**: Responsive grids and flexbox layouts
- **Touch-Friendly**: Large buttons and form controls
- **Performance**: Optimized for mobile network conditions
- **Orientation**: Supports both portrait and landscape

## 🔧 Configuration

### Environment Variables
```env
REACT_APP_API_BASE_URL=http://localhost:5000
REACT_APP_STRIPE_PUBLIC_KEY=pk_test_...
REACT_APP_ASSESSMENT_TIMEOUT=30000
```

### Feature Flags
```javascript
const FEATURE_FLAGS = {
  ASSESSMENT_AUTO_SAVE: true,
  ASSESSMENT_PDF_EXPORT: true,
  ASSESSMENT_SOCIAL_SHARING: true,
  ASSESSMENT_CONVERSION_MODAL: true,
};
```

## 🚀 Performance

### Optimization Features
- **Code Splitting**: Lazy loading of assessment components
- **Memoization**: React.memo for expensive components
- **Debouncing**: Input validation debouncing
- **Caching**: API response caching
- **Bundle Optimization**: Tree shaking and minification

### Performance Metrics
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

## 🔒 Security

### Security Features
- **Input Validation**: Client and server-side validation
- **XSS Prevention**: Proper content sanitization
- **CSRF Protection**: Token-based CSRF protection
- **Rate Limiting**: API rate limiting for assessments
- **Data Encryption**: Sensitive data encryption

### Privacy
- **Data Minimization**: Only collect necessary data
- **User Consent**: Clear consent for data collection
- **Data Retention**: Automatic data cleanup
- **GDPR Compliance**: Right to be forgotten

## 🐛 Troubleshooting

### Common Issues

#### Assessment Not Loading
```javascript
// Check API endpoint
console.log('API URL:', process.env.REACT_APP_API_BASE_URL);

// Check network tab for errors
// Verify authentication status
```

#### Progress Not Saving
```javascript
// Check localStorage permissions
console.log('localStorage available:', !!window.localStorage);

// Check storage quota
// Verify auto-save timing
```

#### Payment Integration Issues
```javascript
// Check Stripe configuration
console.log('Stripe key:', process.env.REACT_APP_STRIPE_PUBLIC_KEY);

// Verify webhook endpoints
// Check payment method validation
```

### Debug Mode
```javascript
// Enable debug logging
localStorage.setItem('assessment_debug', 'true');

// View debug information
console.log('Assessment Debug:', window.assessmentDebug);
```

## 📚 Additional Resources

### Documentation
- [API Documentation](./API.md)
- [Design System](./DESIGN_SYSTEM.md)
- [Accessibility Guide](./ACCESSIBILITY.md)
- [Performance Guide](./PERFORMANCE.md)

### Examples
- [Basic Implementation](./examples/basic.md)
- [Advanced Features](./examples/advanced.md)
- [Custom Styling](./examples/styling.md)
- [Integration Patterns](./examples/integration.md)

### Support
- [GitHub Issues](https://github.com/mingus/assessments/issues)
- [Discord Community](https://discord.gg/mingus)
- [Email Support](mailto:support@mingus.com)

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.

## 🤝 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

---

**Built with ❤️ by the Mingus Team**
