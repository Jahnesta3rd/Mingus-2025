# MINGUS Application Integration Guide

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [API Documentation](#api-documentation)
7. [Component System](#component-system)
8. [Authentication](#authentication)
9. [Routing](#routing)
10. [Analytics](#analytics)
11. [Testing](#testing)
12. [Performance Optimization](#performance-optimization)
13. [Security](#security)
14. [Accessibility](#accessibility)
15. [Deployment](#deployment)
16. [Troubleshooting](#troubleshooting)

## Overview

The MINGUS Application is a comprehensive, production-ready financial assessment platform built with modern web technologies. It features a modular architecture with robust error handling, comprehensive testing, and extensive accessibility features.

### Key Features

- **Modular Architecture**: Clean separation of concerns with service-based architecture
- **Cross-Browser Compatibility**: Works across all modern browsers with progressive enhancement
- **Accessibility First**: WCAG 2.1 AA compliant with comprehensive ARIA support
- **Performance Optimized**: Critical CSS inlining, lazy loading, and performance monitoring
- **Security Hardened**: XSS prevention, CSRF protection, and secure authentication
- **Comprehensive Testing**: Automated test suite covering functionality, performance, and accessibility
- **Analytics Ready**: Built-in analytics with support for multiple providers
- **SEO Optimized**: Semantic HTML, structured data, and meta tag optimization

## Quick Start

### Prerequisites

- Node.js 16+ 
- Modern web browser
- Web server (Apache, Nginx, or built-in development server)

### Basic Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/mingus-app.git
   cd mingus-app
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

5. **Open in browser**
   ```
   http://localhost:3000
   ```

## Architecture

### Core Services

The application is built around several core services:

```
MINGUS Application
├── App (Main Application)
├── Utils (Utility Functions)
├── API (HTTP Client)
├── Auth (Authentication)
├── Router (Client-side Routing)
├── Components (UI Components)
└── Analytics (Event Tracking)
```

### Service Dependencies

```
App
├── Utils (Required)
├── API (Required)
├── Auth (Required)
├── Router (Required)
├── Components (Required)
└── Analytics (Optional)
```

### Data Flow

```
User Action → Router → Component → API → Backend
     ↓
Analytics ← Event Tracking ← User Interaction
```

## Installation & Setup

### Development Environment

1. **Install Node.js dependencies**
   ```bash
   npm install
   ```

2. **Install development tools**
   ```bash
   npm install -g eslint prettier
   ```

3. **Configure linting**
   ```bash
   npm run lint:fix
   ```

4. **Run tests**
   ```bash
   npm test
   ```

### Production Build

1. **Build for production**
   ```bash
   npm run build
   ```

2. **Optimize assets**
   ```bash
   npm run optimize
   ```

3. **Generate service worker**
   ```bash
   npm run generate-sw
   ```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Application
NODE_ENV=development
PORT=3000
BASE_URL=http://localhost:3000

# API Configuration
API_BASE_URL=http://localhost:5000/api
API_TIMEOUT=30000
API_RETRY_ATTEMPTS=3

# Authentication
JWT_SECRET=your-jwt-secret
JWT_EXPIRY=24h
SESSION_SECRET=your-session-secret

# Database
DATABASE_URL=postgresql://user:password@localhost/mingus
REDIS_URL=redis://localhost:6379

# Analytics
GOOGLE_ANALYTICS_ID=GA-XXXXXXXXX
MIXPANEL_TOKEN=your-mixpanel-token
AMPLITUDE_API_KEY=your-amplitude-key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# File Storage
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=your-bucket-name

# Security
CORS_ORIGIN=http://localhost:3000
CSRF_SECRET=your-csrf-secret
RATE_LIMIT_WINDOW=15m
RATE_LIMIT_MAX=100
```

### Application Configuration

The main configuration is in `src/js/config.js`:

```javascript
const config = {
    // API Configuration
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:5000/api',
    API_TIMEOUT: parseInt(process.env.API_TIMEOUT) || 30000,
    API_RETRY_ATTEMPTS: parseInt(process.env.API_RETRY_ATTEMPTS) || 3,
    
    // Authentication
    TOKEN_KEY: 'mingus_auth_token',
    USER_KEY: 'mingus_user_data',
    
    // WebSocket
    WS_URL: process.env.WS_URL || 'ws://localhost:5000/ws',
    
    // Analytics
    ANALYTICS: {
        enabled: true,
        providers: {
            google: {
                enabled: !!process.env.GOOGLE_ANALYTICS_ID,
                trackingId: process.env.GOOGLE_ANALYTICS_ID
            },
            mixpanel: {
                enabled: !!process.env.MIXPANEL_TOKEN,
                token: process.env.MIXPANEL_TOKEN
            },
            amplitude: {
                enabled: !!process.env.AMPLITUDE_API_KEY,
                apiKey: process.env.AMPLITUDE_API_KEY
            }
        }
    },
    
    // Features
    FEATURES: {
        serviceWorker: true,
        pushNotifications: true,
        offlineSupport: true,
        performanceMonitoring: true
    }
};
```

## API Documentation

### Core API Methods

#### Authentication

```javascript
// Login
const result = await MINGUS.auth.login({
    email: 'user@example.com',
    password: 'password123'
});

// Register
const result = await MINGUS.auth.register({
    email: 'user@example.com',
    password: 'password123',
    firstName: 'John',
    lastName: 'Doe'
});

// Logout
await MINGUS.auth.logout();

// Check authentication status
const isLoggedIn = MINGUS.auth.isLoggedIn();
const currentUser = MINGUS.auth.getCurrentUser();
```

#### API Requests

```javascript
// GET request
const data = await MINGUS.api.get('/users/profile');

// POST request
const result = await MINGUS.api.post('/users/profile', {
    firstName: 'John',
    lastName: 'Doe'
});

// PUT request
const result = await MINGUS.api.put('/users/profile/123', {
    firstName: 'Jane'
});

// DELETE request
await MINGUS.api.delete('/users/profile/123');

// Cached request
const data = await MINGUS.api.getCached('/users/profile', {}, {
    forceRefresh: false
});
```

#### Navigation

```javascript
// Navigate to route
MINGUS.router.navigate('/dashboard');

// Navigate with data
MINGUS.router.navigate('/assessment/123', {
    data: { assessmentId: '123' }
});

// Replace current route
MINGUS.router.replace('/login');

// Go back/forward
MINGUS.router.back();
MINGUS.router.forward();

// Refresh current page
MINGUS.router.refresh();
```

#### Components

```javascript
// Create button
const button = MINGUS.components.create('Button', {
    text: 'Click Me',
    variant: 'primary',
    onClick: () => console.log('Clicked!')
});

// Create modal
const modal = MINGUS.components.showModal({
    title: 'Confirmation',
    content: 'Are you sure?',
    onConfirm: () => console.log('Confirmed'),
    onCancel: () => console.log('Cancelled')
});

// Create form
const form = MINGUS.components.create('Form', {
    fields: [
        { type: 'email', name: 'email', label: 'Email', required: true },
        { type: 'password', name: 'password', label: 'Password', required: true }
    ],
    onSubmit: (data) => console.log('Form submitted:', data)
});
```

#### Analytics

```javascript
// Track custom event
MINGUS.analytics.track('button_click', {
    buttonName: 'submit',
    page: 'checkout'
});

// Track page view
MINGUS.analytics.trackPageView({
    title: 'Checkout Page',
    url: '/checkout'
});

// Track user action
MINGUS.analytics.trackUserAction('form_submit', formElement, {
    formType: 'registration'
});

// Track conversion
MINGUS.analytics.trackConversion('purchase', 99.99, {
    productId: '123',
    category: 'premium'
});

// Identify user
MINGUS.analytics.identify('user123', {
    email: 'user@example.com',
    plan: 'premium'
});
```

## Component System

### Available Components

#### Button
```javascript
MINGUS.components.create('Button', {
    text: 'Click Me',
    variant: 'primary', // primary, secondary, accent, outline, ghost
    size: 'medium', // small, medium, large
    disabled: false,
    loading: false,
    icon: 'arrow-right',
    onClick: () => console.log('Clicked')
});
```

#### Modal
```javascript
MINGUS.components.showModal({
    title: 'Confirmation',
    content: 'Are you sure?',
    size: 'medium', // small, medium, large
    closable: true,
    backdrop: true,
    onConfirm: () => console.log('Confirmed'),
    onCancel: () => console.log('Cancelled'),
    confirmText: 'Yes',
    cancelText: 'No'
});
```

#### Form
```javascript
MINGUS.components.create('Form', {
    fields: [
        { type: 'text', name: 'firstName', label: 'First Name', required: true },
        { type: 'email', name: 'email', label: 'Email', required: true },
        { type: 'password', name: 'password', label: 'Password', required: true },
        { 
            type: 'select', 
            name: 'country', 
            label: 'Country',
            options: [
                { value: 'us', label: 'United States' },
                { value: 'ca', label: 'Canada' }
            ]
        }
    ],
    onSubmit: (data) => console.log('Form data:', data),
    onReset: () => console.log('Form reset')
});
```

#### Card
```javascript
MINGUS.components.create('Card', {
    title: 'User Profile',
    content: '<p>User information here</p>',
    footer: '<button>Edit Profile</button>'
});
```

#### Alert
```javascript
MINGUS.components.create('Alert', {
    message: 'This is an important message',
    type: 'info', // success, warning, error, info
    closable: true
});
```

#### Progress
```javascript
MINGUS.components.create('Progress', {
    value: 75,
    max: 100,
    text: '75% Complete'
});
```

### Custom Components

To create a custom component:

```javascript
// Register custom component
MINGUS.components.register('CustomComponent', (config) => {
    const element = document.createElement('div');
    element.className = 'custom-component';
    element.innerHTML = `<h3>${config.title}</h3><p>${config.content}</p>`;
    return element;
});

// Use custom component
const custom = MINGUS.components.create('CustomComponent', {
    title: 'My Custom Component',
    content: 'This is custom content'
});
```

## Authentication

### Authentication Flow

1. **User Registration**
   ```javascript
   const result = await MINGUS.auth.register({
       email: 'user@example.com',
       password: 'password123',
       firstName: 'John',
       lastName: 'Doe'
   });
   ```

2. **User Login**
   ```javascript
   const result = await MINGUS.auth.login({
       email: 'user@example.com',
       password: 'password123'
   });
   ```

3. **Token Management**
   ```javascript
   // Get current token
   const token = MINGUS.auth.getToken();
   
   // Check if token is valid
   const isValid = MINGUS.auth.isTokenValid(token);
   
   // Refresh token
   await MINGUS.auth.refreshToken();
   ```

4. **Session Management**
   ```javascript
   // Check if user is logged in
   const isLoggedIn = MINGUS.auth.isLoggedIn();
   
   // Get current user
   const user = MINGUS.auth.getCurrentUser();
   
   // Check permissions
   const hasPermission = MINGUS.auth.hasPermission('admin');
   const hasRole = MINGUS.auth.hasRole('user');
   ```

### Security Features

- **JWT Tokens**: Secure token-based authentication
- **Token Refresh**: Automatic token refresh before expiration
- **Session Timeout**: Configurable session timeout with user activity tracking
- **Cross-Tab Synchronization**: Session state synchronized across browser tabs
- **Secure Storage**: Tokens stored securely in localStorage with encryption

## Routing

### Route Configuration

Routes are automatically registered based on the application structure:

```javascript
// Public routes
MINGUS.router.register('/', {
    component: 'Dashboard',
    title: 'Dashboard',
    public: true
});

// Protected routes
MINGUS.router.register('/dashboard', {
    component: 'Dashboard',
    title: 'Dashboard',
    requiresAuth: true
});

// Routes with parameters
MINGUS.router.register('/assessment/:id', {
    component: 'AssessmentDetail',
    title: 'Assessment',
    requiresAuth: true
});
```

### Navigation Guards

```javascript
// Add custom navigation guard
MINGUS.router.addNavigationGuard(async (route, data) => {
    // Check if user has permission
    if (route.requiresPermission) {
        const hasPermission = MINGUS.auth.hasPermission(route.requiresPermission);
        if (!hasPermission) {
            MINGUS.router.navigate('/403');
            return false;
        }
    }
    return true;
});
```

### Route Parameters

```javascript
// Navigate with parameters
MINGUS.router.navigate('/assessment/123');

// Access parameters in component
const params = context.params; // { id: '123' }
```

## Analytics

### Event Tracking

```javascript
// Track custom events
MINGUS.analytics.track('assessment_started', {
    assessmentId: '123',
    category: 'financial'
});

// Track user actions
MINGUS.analytics.trackUserAction('button_click', buttonElement, {
    buttonType: 'submit'
});

// Track errors
MINGUS.analytics.trackError(error, {
    context: 'form_submission',
    userId: 'user123'
});

// Track performance
MINGUS.analytics.trackPerformance('page_load', 1500, {
    page: '/dashboard'
});
```

### User Identification

```javascript
// Identify user
MINGUS.analytics.identify('user123', {
    email: 'user@example.com',
    plan: 'premium',
    signupDate: '2024-01-01'
});

// Set user properties
MINGUS.analytics.setUserProperties({
    lastLogin: new Date().toISOString(),
    loginCount: 5
});

// Alias user
MINGUS.analytics.alias('user123', 'anonymous123');
```

### Conversion Tracking

```javascript
// Track conversions
MINGUS.analytics.trackConversion('purchase', 99.99, {
    productId: 'premium_plan',
    category: 'subscription'
});

// Track form completions
MINGUS.analytics.trackConversion('form_completion', null, {
    formType: 'registration'
});
```

## Testing

### Running Tests

```bash
# Run all tests
npm test

# Run specific test categories
npm test -- --category="Core Functionality"

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

### Test Categories

1. **Core Functionality**
   - Application initialization
   - Authentication flow
   - Navigation system
   - API integration
   - Component rendering
   - Form handling
   - Modal functionality
   - Error handling

2. **Performance**
   - Page load performance
   - Component performance
   - Memory usage
   - Network performance
   - Animation performance

3. **Accessibility**
   - Keyboard navigation
   - Screen reader compatibility
   - Color contrast
   - Focus management
   - ARIA labels
   - Semantic HTML

4. **Cross-Browser Compatibility**
   - Chrome compatibility
   - Firefox compatibility
   - Safari compatibility
   - Edge compatibility
   - Mobile browser compatibility

5. **Security**
   - XSS prevention
   - CSRF protection
   - Input validation
   - Authentication security
   - Data encryption

6. **SEO**
   - Meta tags
   - Structured data
   - URL structure
   - Page speed
   - Mobile friendliness

### Writing Custom Tests

```javascript
// Add custom test
MINGUS.testSuite.register('Custom Tests', [
    {
        name: 'Custom Functionality Test',
        test: async function() {
            const result = { passed: false, details: [] };
            
            try {
                // Test implementation
                const testResult = await someFunction();
                
                if (testResult.success) {
                    result.passed = true;
                    result.details.push('Test passed successfully');
                } else {
                    result.details.push('Test failed');
                }
            } catch (error) {
                result.details.push(`Error: ${error.message}`);
            }
            
            return result;
        }
    }
]);
```

## Performance Optimization

### Critical CSS

Critical CSS is automatically inlined in the HTML head:

```html
<style id="critical-css">
    /* Critical CSS for above-the-fold content */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        /* ... */
    }
    
    /* Essential styles for immediate rendering */
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.6;
        color: var(--text-color);
        background-color: var(--background-color);
    }
    
    /* Header and navigation styles */
    .header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
    }
</style>
```

### Lazy Loading

Images and components are lazy-loaded:

```html
<!-- Lazy-loaded image -->
<img data-src="/images/hero.jpg" class="lazy" alt="Hero image">

<!-- Lazy-loaded component -->
<div data-component="HeavyComponent" data-props='{"id": "123"}'></div>
```

### Service Worker

Service worker for offline support and caching:

```javascript
// Service worker registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed');
            });
    });
}
```

### Performance Monitoring

Core Web Vitals are automatically monitored:

```javascript
// LCP (Largest Contentful Paint)
const lcpObserver = new PerformanceObserver((list) => {
    const entries = list.getEntries();
    const lastEntry = entries[entries.length - 1];
    if (lastEntry) {
        MINGUS.analytics.trackPerformance('LCP', lastEntry.startTime);
    }
});

// FID (First Input Delay)
const fidObserver = new PerformanceObserver((list) => {
    const entries = list.getEntries();
    entries.forEach(entry => {
        MINGUS.analytics.trackPerformance('FID', 
            entry.processingStart - entry.startTime);
    });
});

// CLS (Cumulative Layout Shift)
const clsObserver = new PerformanceObserver((list) => {
    let clsValue = 0;
    const entries = list.getEntries();
    entries.forEach(entry => {
        if (!entry.hadRecentInput) {
            clsValue += entry.value;
        }
    });
    MINGUS.analytics.trackPerformance('CLS', clsValue);
});
```

## Security

### XSS Prevention

All user input is automatically sanitized:

```javascript
// Safe content rendering
const safeContent = MINGUS.utils.DOM.sanitize(userInput);
element.innerHTML = safeContent;

// Text content (always safe)
element.textContent = userInput;
```

### CSRF Protection

CSRF tokens are automatically included in forms:

```html
<form>
    <input type="hidden" name="csrf_token" value="generated-token">
    <!-- form fields -->
</form>
```

### Input Validation

Comprehensive input validation:

```javascript
// Email validation
const isValidEmail = MINGUS.utils.Validation.isEmail(email);

// Required field validation
const isRequired = MINGUS.utils.Validation.isRequired(value);

// Length validation
const isValidLength = MINGUS.utils.Validation.minLength(value, 8);

// Number validation
const isValidNumber = MINGUS.utils.Validation.isNumber(value);
```

### Authentication Security

Secure authentication practices:

```javascript
// Secure token storage
MINGUS.auth.setToken(token);

// Token validation
const isValid = MINGUS.auth.isTokenValid(token);

// Automatic token refresh
await MINGUS.auth.refreshToken();

// Secure logout
await MINGUS.auth.logout();
```

## Accessibility

### ARIA Support

Comprehensive ARIA attributes:

```html
<!-- Navigation -->
<nav role="navigation" aria-label="Main navigation">
    <ul role="menubar">
        <li role="none">
            <a href="/dashboard" role="menuitem" aria-current="page">Dashboard</a>
        </li>
    </ul>
</nav>

<!-- Modal -->
<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <h2 id="modal-title">Modal Title</h2>
    <button class="modal-close" aria-label="Close modal">×</button>
</div>

<!-- Form -->
<form role="form">
    <label for="email">Email</label>
    <input type="email" id="email" aria-describedby="email-help" required>
    <div id="email-help">Enter your email address</div>
</form>
```

### Keyboard Navigation

Full keyboard support:

```javascript
// Tab navigation
document.addEventListener('keydown', (event) => {
    if (event.key === 'Tab') {
        // Handle tab navigation
        MINGUS.app.handleTabNavigation(event);
    }
});

// Escape key for modals
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        MINGUS.components.hideTopModal();
    }
});
```

### Focus Management

Proper focus management:

```javascript
// Focus trap in modals
const focusableElements = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
);

// Focus first element
focusableElements[0].focus();

// Skip link
<a href="#main-content" class="skip-link">Skip to main content</a>
```

### Screen Reader Support

Screen reader compatibility:

```html
<!-- Semantic HTML -->
<main role="main" id="main-content">
    <section aria-labelledby="section-title">
        <h2 id="section-title">Section Title</h2>
        <p>Section content</p>
    </section>
</main>

<!-- Status messages -->
<div role="status" aria-live="polite" class="sr-only">
    Form submitted successfully
</div>
```

## Deployment

### Production Build

```bash
# Build for production
npm run build

# Optimize assets
npm run optimize

# Generate service worker
npm run generate-sw

# Run production server
npm start
```

### Environment Configuration

```bash
# Production environment
NODE_ENV=production
PORT=3000
BASE_URL=https://your-domain.com
API_BASE_URL=https://api.your-domain.com
```

### Deployment Checklist

- [ ] Environment variables configured
- [ ] SSL certificate installed
- [ ] Database migrations run
- [ ] Static assets optimized
- [ ] Service worker generated
- [ ] Analytics configured
- [ ] Error monitoring set up
- [ ] Performance monitoring enabled
- [ ] Security headers configured
- [ ] Backup strategy implemented

### Docker Deployment

```dockerfile
# Dockerfile
FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:password@db:5432/mingus
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=mingus
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## Troubleshooting

### Common Issues

#### Application Not Loading

```javascript
// Check if MINGUS is available
if (typeof MINGUS === 'undefined') {
    console.error('MINGUS application not loaded');
}

// Check if app is initialized
if (!MINGUS.app.isAppInitialized()) {
    console.error('Application not initialized');
}
```

#### Authentication Issues

```javascript
// Check authentication status
const isLoggedIn = MINGUS.auth.isLoggedIn();
console.log('Logged in:', isLoggedIn);

// Check token validity
const token = MINGUS.auth.getToken();
const isValid = MINGUS.auth.isTokenValid(token);
console.log('Token valid:', isValid);
```

#### API Connection Issues

```javascript
// Test API connection
try {
    const health = await MINGUS.api.healthCheck();
    console.log('API health:', health);
} catch (error) {
    console.error('API connection failed:', error);
}
```

#### Performance Issues

```javascript
// Check performance metrics
const navigation = performance.getEntriesByType('navigation')[0];
if (navigation) {
    console.log('Page load time:', 
        navigation.loadEventEnd - navigation.fetchStart);
}
```

### Debug Mode

Enable debug mode for detailed logging:

```javascript
// Enable debug logging
MINGUS.utils.setLogLevel(MINGUS.utils.LOG_LEVELS.DEBUG);

// Access debug information
console.log('MINGUS Debug:', window.MINGUS_DEBUG);
```

### Error Reporting

Errors are automatically captured and reported:

```javascript
// Custom error handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    // Send to error reporting service
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    // Send to error reporting service
});
```

### Support

For additional support:

- **Documentation**: [docs.mingus.com](https://docs.mingus.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/mingus-app/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/mingus-app/discussions)
- **Email**: support@mingus.com

---

This integration guide provides comprehensive documentation for the MINGUS Application. For specific implementation details, refer to the individual service documentation and code comments.
