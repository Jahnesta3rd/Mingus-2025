# Education Flow Components

This directory contains interactive educational components for the Mingus financial wellness app, designed to introduce users to the app's key features and benefits.

## Components

### EducationFlow
The main container component that orchestrates the entire education experience.

**Features:**
- 4-step educational flow with smooth transitions
- Progress indicators and step counter
- Navigation controls (Previous, Next, Skip)
- Mobile-first responsive design
- Accessibility features (keyboard navigation, screen reader support)

**Props:**
- `onComplete`: Callback when user completes the education flow
- `onSkip`: Callback when user skips the education flow

### EducationalCardJobSecurity
Interactive card explaining the career confidence score feature.

**Features:**
- Expandable details with smooth animations
- Animated progress bar (demo score: 78)
- Industry analysis preview with trending line graph
- "Try It" functionality with success feedback
- Rotating testimonials from beta users

### EducationalCardCashFlow
Interactive card explaining the smart money planning feature.

**Features:**
- Expandable details with smooth animations
- Animated progress bar (demo score: 85)
- Interactive calendar preview with important dates
- Cash flow trend visualization
- "Try It" functionality with success feedback
- Rotating testimonials from beta users

### EducationalCardWellness
Interactive card explaining the health-wealth connection.

**Features:**
- Expandable details with smooth animations
- Animated progress bar (demo score: 72)
- Interconnected circles visualization showing health metrics
- Health-spending correlation chart
- "Try It" functionality with success feedback
- Rotating testimonials from beta users

### PrivacyAssuranceCard
Interactive card explaining privacy and security measures.

**Features:**
- Expandable details with smooth animations
- Animated progress bar (demo score: 95)
- Shield visualization with security features
- Data privacy control preview
- "Try It" functionality with success feedback
- Rotating testimonials from beta users

## Micro-Animations

All components include:
- **Slide-in animations**: Cards slide in from the right on mount
- **Pulsing icons**: Icons gently pulse to draw attention
- **Smooth progress bars**: Progress bars fill smoothly when expanded
- **Bouncing success checkmarks**: Success feedback appears with bounce animation
- **Expandable content**: Smooth height transitions for detail sections

## Usage

### Basic Usage
```jsx
import { EducationFlow } from './components/education';

function App() {
  const handleComplete = () => {
    // Navigate to main app
    console.log('Education completed!');
  };

  const handleSkip = () => {
    // Skip education flow
    console.log('Education skipped!');
  };

  return (
    <EducationFlow 
      onComplete={handleComplete}
      onSkip={handleSkip}
    />
  );
}
```

### Individual Cards
```jsx
import { EducationalCardJobSecurity } from './components/education';

function MyComponent() {
  return (
    <EducationalCardJobSecurity 
      onSeeScore={() => alert('Navigate to job security dashboard')}
      testimonialIndex={0}
    />
  );
}
```

### Demo Component
```jsx
import { EducationFlowDemo } from './components/education';

function App() {
  return <EducationFlowDemo />;
}
```

## Styling

All components use the Mingus dark theme:
- Background: `bg-gray-950` (main), `bg-gray-900` (cards)
- Text: `text-white` (primary), `text-gray-300` (secondary), `text-gray-400` (tertiary)
- Accents: `text-blue-400` (primary), `text-green-400` (success), `text-red-400` (error)
- Interactive: `bg-blue-600` (buttons), `hover:bg-blue-700` (button hover)

## Accessibility

- **Keyboard Navigation**: Arrow keys for navigation, Enter for expansion
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **High Contrast**: Designed for high contrast mode compatibility
- **Focus Management**: Clear focus indicators and logical tab order
- **Reduced Motion**: Respects user's motion preferences

## Dependencies

- **React**: 18+ with hooks
- **Framer Motion**: For animations and transitions
- **Lucide React**: For icons
- **Tailwind CSS**: For styling

## Customization

### Adding New Cards
1. Create a new card component following the existing pattern
2. Add it to the `cards` array in `EducationFlow.tsx`
3. Update the navigation logic if needed

### Modifying Animations
All animations use Framer Motion and can be customized by modifying the `transition` props in each component.

### Changing Testimonials
Update the `testimonials` array in each card component to change the rotating quotes.

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Components are optimized for 60fps animations
- Images and SVGs are optimized for fast loading
- Lazy loading is implemented for better performance
- Minimal re-renders through proper React patterns 