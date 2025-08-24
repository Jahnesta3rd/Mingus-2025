# MINGUS Landing Page JavaScript Guide

## Overview

This guide covers the comprehensive JavaScript functionality for the MINGUS landing page, including assessment modals, animations, analytics integration, and mobile interactions.

## Files Structure

```
static/
├── js/
│   └── landing-page.js          # Main JavaScript functionality
├── css/
│   └── landing-page.css         # Supporting styles
└── templates/
    └── landing_page_example.html # Example implementation
```

## Core Features

### 1. Assessment Modal System

#### **Modal Functions**

**`openAssessmentModal()`**
- Shows the assessment selection modal
- Prevents body scroll
- Tracks analytics event
- Manages focus for accessibility

```javascript
// Usage
window.mingusLandingPage.openAssessmentModal();
```

**`closeAssessmentModal()`**
- Hides the modal with smooth animation
- Restores body scroll
- Returns focus to trigger element

```javascript
// Usage
window.mingusLandingPage.closeAssessmentModal();
```

**`selectAssessment(assessmentType)`**
- Tracks assessment selection
- Routes to appropriate assessment page
- Closes modal after selection

```javascript
// Usage
window.mingusLandingPage.selectAssessment('income-comparison');
```

#### **Assessment Route Mapping**

```javascript
this.assessmentRoutes = {
    'income-comparison': '/assessment/income-comparison',
    'job-matching': '/assessment/job-matching',
    'relationship-money': '/assessment/relationship-money',
    'tax-impact': '/assessment/tax-impact'
};
```

### 2. Animation System

#### **Fade-in Animations**

Elements with the `fade-in` class automatically animate when they enter the viewport:

```html
<div class="fade-in">
    <!-- Content will animate in -->
</div>
```

#### **Progress Bar Animations**

```html
<div class="progress-bar-container">
    <div class="progress-bar" data-progress="85"></div>
</div>
```

**Features:**
- Staggered animation (200ms delay between bars)
- Smooth easing with cubic-bezier
- Automatic trigger on viewport entry

#### **User Count Animations**

```html
<span class="user-count" data-count="15420">15,420</span>
```

**Features:**
- Count-up animation with easing
- Staggered timing (300ms delay)
- Number formatting with commas
- 2-second duration

### 3. FAQ Toggle System

```html
<div class="faq-item">
    <button class="faq-toggle">
        Question text
        <span class="faq-icon">▼</span>
    </button>
    <div class="faq-content">
        <p>Answer content</p>
    </div>
</div>
```

**Features:**
- Smooth expand/collapse animation
- Auto-close other FAQ items
- Icon rotation animation
- Keyboard accessible

### 4. Scroll Effects

#### **Header Background**

The header automatically changes opacity and adds shadow when scrolling past 100px:

```css
.header-scrolled {
    background: rgba(26, 26, 46, 0.98);
    box-shadow: 0 2px 20px rgba(0, 0, 0, 0.3);
}
```

#### **Smooth Scrolling**

Anchor links automatically scroll smoothly to their targets:

```html
<a href="#features">Features</a>
```

### 5. Mobile Touch Interactions

#### **Swipe Gestures**

- **Swipe Up**: Closes modal (if open)
- **Swipe Down**: Opens modal (if closed)
- **Threshold**: 50px minimum swipe distance

#### **Touch Optimizations**

- Prevents zoom on double-tap
- Passive event listeners for performance
- Touch-friendly button sizes

### 6. Analytics Integration

#### **Google Analytics 4 Events**

```javascript
// Tracked events
{
    modalOpen: 'mingus_assessment_modal_open',
    assessmentSelect: 'mingus_assessment_selected',
    ctaClick: 'mingus_cta_click',
    scrollDepth: 'mingus_scroll_depth'
}
```

#### **Event Tracking**

```javascript
// Track custom events
window.mingusLandingPage.trackEvent('custom_event', {
    event_category: 'user_action',
    event_label: 'button_click',
    custom_parameter: 'value'
});
```

#### **Scroll Depth Tracking**

Automatically tracks scroll depth at 25%, 50%, 75%, and 90% thresholds.

### 7. Performance Monitoring

#### **Core Web Vitals**

- **LCP (Largest Contentful Paint)** monitoring
- **Memory usage** monitoring
- **Error tracking** and reporting

#### **Performance Optimizations**

- **Debounced scroll events** (100ms)
- **Intersection Observer** for animations
- **Hardware acceleration** for smooth animations
- **Reduced motion** support

## Implementation Guide

### 1. Basic Setup

Include the required files in your HTML:

```html
<!-- CSS -->
<link rel="stylesheet" href="/static/css/landing-page.css">

<!-- JavaScript -->
<script src="/static/js/landing-page.js"></script>

<!-- Analytics Configuration -->
<script>
    window.GA_TRACKING_ID = 'G-XXXXXXXXXX';
    window.MINGUS_ANALYTICS_ENDPOINT = '/api/analytics/track';
</script>
```

### 2. Assessment Modal Implementation

```html
<!-- Trigger Button -->
<button class="assessment-trigger">Start Assessment</button>

<!-- Modal Structure -->
<div id="assessment-modal" class="modal-overlay">
    <div class="modal-content">
        <button class="modal-close">×</button>
        
        <div class="modal-header">
            <h2 class="modal-title">Choose Your Assessment</h2>
            <p class="modal-subtitle">Select the tool that best fits your needs</p>
        </div>
        
        <div class="assessment-options">
            <div class="assessment-option" data-assessment-type="income-comparison">
                <div class="assessment-icon">💰</div>
                <div class="assessment-content">
                    <h3 class="assessment-title">Income Comparison Calculator</h3>
                    <p class="assessment-description">Compare your salary to peers...</p>
                </div>
            </div>
            <!-- More assessment options... -->
        </div>
    </div>
</div>
```

### 3. Animation Implementation

```html
<!-- Fade-in elements -->
<div class="fade-in">
    <h2>Animated Title</h2>
</div>

<!-- Progress bars -->
<div class="progress-bar-container">
    <div class="progress-bar" data-progress="85"></div>
</div>

<!-- User counts -->
<span class="user-count" data-count="15420">15,420</span>
```

### 4. FAQ Implementation

```html
<div class="faq-item">
    <button class="faq-toggle">
        How does the income comparison work?
        <span class="faq-icon">▼</span>
    </button>
    <div class="faq-content">
        <p>Detailed answer content...</p>
    </div>
</div>
```

## Configuration Options

### Global Configuration

```javascript
window.MINGUS_CONFIG = {
    enableSwipeGestures: true,
    enablePerformanceMonitoring: true,
    enableErrorTracking: true,
    animationDelay: 200,
    scrollThreshold: 100
};
```

### Analytics Configuration

```javascript
window.MINGUS_ANALYTICS_ENDPOINT = '/api/analytics/track';
window.GA_TRACKING_ID = 'G-XXXXXXXXXX';
```

## API Reference

### Class: MingusLandingPage

#### **Constructor**
```javascript
new MingusLandingPage()
```

#### **Methods**

**`openAssessmentModal()`**
Opens the assessment selection modal.

**`closeAssessmentModal()`**
Closes the assessment modal.

**`selectAssessment(assessmentType)`**
Selects an assessment and routes to it.

**Parameters:**
- `assessmentType` (string): One of 'income-comparison', 'job-matching', 'relationship-money', 'tax-impact'

**`trackEvent(eventName, parameters)`**
Tracks a custom analytics event.

**Parameters:**
- `eventName` (string): Event name
- `parameters` (object): Event parameters

**`animateProgressBars()`**
Animates all progress bars on the page.

**`animateUserCount()`**
Animates all user count numbers.

**`toggleFAQ(faqItem)`**
Toggles a FAQ item open/closed.

**Parameters:**
- `faqItem` (HTMLElement): The FAQ item element

**`smoothScrollToElement(elementId)`**
Smoothly scrolls to an element.

**Parameters:**
- `elementId` (string): ID of the target element

## Event Listeners

### Automatic Event Binding

The following events are automatically bound:

- **Assessment triggers**: All elements with `assessment-trigger` class
- **Modal close**: Click outside modal, escape key, close button
- **Assessment selection**: All elements with `assessment-option` class
- **Smooth scrolling**: All anchor links (`a[href^="#"]`)
- **FAQ toggles**: All elements with `faq-toggle` class
- **CTA tracking**: All elements with `cta-button` class

### Custom Event Binding

```javascript
// Listen for assessment selection
document.addEventListener('mingus_assessment_selected', (e) => {
    console.log('Assessment selected:', e.detail);
});

// Listen for modal events
document.addEventListener('mingus_modal_opened', (e) => {
    console.log('Modal opened');
});

document.addEventListener('mingus_modal_closed', (e) => {
    console.log('Modal closed');
});
```

## Accessibility Features

### Keyboard Navigation

- **Tab**: Navigate through interactive elements
- **Enter/Space**: Activate buttons and links
- **Escape**: Close modal
- **Arrow keys**: Navigate FAQ items

### Screen Reader Support

- Proper ARIA labels and roles
- Focus management
- Semantic HTML structure
- Descriptive alt text

### Reduced Motion Support

```css
@media (prefers-reduced-motion: reduce) {
    /* Disables animations for users who prefer reduced motion */
}
```

## Performance Considerations

### Optimization Features

1. **Intersection Observer**: Efficient animation triggering
2. **Debounced Events**: Prevents excessive function calls
3. **Hardware Acceleration**: Smooth animations
4. **Memory Management**: Automatic cleanup of observers
5. **Lazy Loading**: Animations only when needed

### Best Practices

1. **Minimize DOM queries**: Cache selectors when possible
2. **Use passive listeners**: For scroll and touch events
3. **Batch DOM updates**: Group multiple changes
4. **Optimize animations**: Use transform and opacity
5. **Monitor performance**: Built-in performance tracking

## Error Handling

### Built-in Error Handling

- **Modal errors**: Graceful fallbacks
- **Analytics errors**: Non-blocking tracking
- **Animation errors**: Fallback to static display
- **Network errors**: Offline functionality

### Custom Error Handling

```javascript
// Listen for errors
window.addEventListener('mingus_error', (e) => {
    console.error('MINGUS Error:', e.detail);
    // Handle error appropriately
});
```

## Browser Support

### Supported Browsers

- **Chrome**: 80+
- **Firefox**: 75+
- **Safari**: 13+
- **Edge**: 80+

### Polyfills

The code includes automatic polyfills for:
- Intersection Observer
- Custom Events
- Promise support

## Testing

### Manual Testing Checklist

- [ ] Modal opens and closes properly
- [ ] Assessment selection routes correctly
- [ ] Animations trigger on scroll
- [ ] FAQ items expand/collapse
- [ ] Mobile touch gestures work
- [ ] Analytics events fire
- [ ] Keyboard navigation works
- [ ] Screen reader compatibility
- [ ] Performance is acceptable

### Automated Testing

```javascript
// Example test structure
describe('MingusLandingPage', () => {
    test('should open modal', () => {
        const landingPage = new MingusLandingPage();
        landingPage.openAssessmentModal();
        expect(document.body.classList.contains('modal-open')).toBe(true);
    });
    
    test('should track events', () => {
        const landingPage = new MingusLandingPage();
        const mockGtag = jest.fn();
        global.gtag = mockGtag;
        
        landingPage.trackEvent('test_event', { test: true });
        expect(mockGtag).toHaveBeenCalledWith('event', 'test_event', expect.any(Object));
    });
});
```

## Troubleshooting

### Common Issues

1. **Modal not opening**: Check if element with ID 'assessment-modal' exists
2. **Animations not working**: Ensure elements have correct CSS classes
3. **Analytics not tracking**: Verify Google Analytics is loaded
4. **Mobile gestures not working**: Check touch event support

### Debug Mode

```javascript
// Enable debug logging
window.MINGUS_DEBUG = true;
```

This will log detailed information about:
- Event firing
- Animation triggers
- Performance metrics
- Error details

## Updates and Maintenance

### Version History

- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Added performance monitoring
- **v1.2.0**: Enhanced mobile support
- **v1.3.0**: Improved accessibility features

### Migration Guide

When updating versions, check for:
- Breaking changes in API
- New configuration options
- Deprecated methods
- Performance improvements

## Support

For technical support or questions about the MINGUS landing page JavaScript functionality, please refer to:

- **Documentation**: This guide
- **Examples**: `templates/landing_page_example.html`
- **Issues**: GitHub repository issues
- **Contact**: Development team

---

This JavaScript functionality provides a comprehensive, performant, and accessible foundation for the MINGUS landing page, with built-in analytics, animations, and mobile support.
