# Analytics Tracking System Documentation

## Overview

This comprehensive analytics system for Ratchet Money provides complete tracking of user behavior, conversion funnels, A/B testing, and GDPR-compliant data collection. The system integrates with Google Analytics 4 and includes advanced features for optimizing lead magnet performance.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Google Analytics 4 Integration](#google-analytics-4-integration)
3. [Event Tracking](#event-tracking)
4. [Conversion Funnel Tracking](#conversion-funnel-tracking)
5. [A/B Testing Framework](#ab-testing-framework)
6. [User Behavior Tracking](#user-behavior-tracking)
7. [GDPR Compliance](#gdpr-compliance)
8. [Setup Instructions](#setup-instructions)
9. [Usage Examples](#usage-examples)
10. [Troubleshooting](#troubleshooting)

## System Architecture

### Components

- **Analytics Service**: Core tracking functionality with GA4 integration
- **React Hooks**: Easy-to-use hooks for component integration
- **A/B Testing Components**: Pre-built components for testing variations
- **GDPR Compliance**: Consent management and privacy controls
- **Analytics Dashboard**: Real-time performance monitoring

### Data Flow

1. User interaction → Event tracking → GA4
2. Session management → User behavior analysis
3. A/B test assignment → Variant tracking → Statistical analysis
4. Consent management → Privacy-compliant data collection

## Google Analytics 4 Integration

### Configuration

Set up Google Analytics 4 in your environment:

```bash
REACT_APP_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_RESPECT_DNT=true
REACT_APP_ANONYMIZE_IP=true
```

### GA4 Events

The system tracks the following GA4 events:

#### 1. Questionnaire Events

```typescript
// Questionnaire started
gtag('event', 'questionnaire_start', {
  session_id: 'session_123',
  user_id: 'user_456',
  timestamp: 1640995200000
})

// Question completed
gtag('event', 'question_completed', {
  question_number: 3,
  question_text: 'How do you typically feel about your financial situation?',
  response: 'Somewhat stressed',
  time_spent_seconds: 45,
  progress_percentage: 30
})

// Questionnaire abandoned
gtag('event', 'questionnaire_abandoned', {
  abandoned_at_question: 5,
  reason: 'page_hidden',
  time_spent_total: 180,
  progress_percentage: 50
})
```

#### 2. Conversion Events

```typescript
// Email submitted
gtag('event', 'email_submitted', {
  email_hash: 'abc123',
  segment: 'stress-free',
  score: 75,
  time_to_complete: 300
})

// Results viewed
gtag('event', 'results_viewed', {
  segment: 'stress-free',
  score: 75,
  time_on_results_page: 120
})

// CTA clicked
gtag('event', 'cta_clicked', {
  cta_type: 'primary',
  cta_text: 'Get Your Personalized Plan',
  destination: '/checkout',
  funnel_stage: 'results_viewed'
})
```

#### 3. Funnel Events

```typescript
// Funnel stage progression
gtag('event', 'funnel_stage', {
  stage: 'email_submitted',
  session_id: 'session_123',
  user_id: 'user_456',
  conversion_value: 75
})
```

#### 4. A/B Test Events

```typescript
// A/B test exposure
gtag('event', 'ab_test_exposure', {
  test_id: 'headline_test',
  variant: 'variant_a',
  session_id: 'session_123'
})

// A/B test conversion
gtag('event', 'ab_test_conversion', {
  test_id: 'headline_test',
  variant: 'variant_a',
  conversion_type: 'email_submitted'
})
```

#### 5. User Behavior Events

```typescript
// User behavior tracking
gtag('event', 'user_behavior', {
  action: 'scroll',
  scroll_percent: 75,
  session_id: 'session_123',
  timestamp: 1640995200000
})

// Time on page
gtag('event', 'time_on_page', {
  page_path: '/questionnaire',
  time_spent_seconds: 180,
  session_id: 'session_123'
})
```

## Event Tracking

### Core Events

#### Questionnaire Tracking

```typescript
import { useQuestionnaireAnalytics } from '../hooks/useAnalytics'

const Questionnaire = () => {
  const { trackStart, trackQuestionComplete, trackAbandonment } = useQuestionnaireAnalytics()

  useEffect(() => {
    trackStart() // Track questionnaire start
  }, [])

  const handleQuestionComplete = (questionNumber: number, questionText: string, response: string) => {
    trackQuestionComplete(questionNumber, questionText, response)
  }

  const handleAbandonment = () => {
    trackAbandonment('user_navigation')
  }

  return (
    // Questionnaire component
  )
}
```

#### Conversion Tracking

```typescript
import { useConversionFunnel } from '../hooks/useAnalytics'

const ResultsPage = () => {
  const { trackEmailSubmitted, trackResultsView, trackCTAClicked } = useConversionFunnel()

  useEffect(() => {
    trackResultsView(segment, score)
  }, [segment, score])

  const handleEmailSubmit = (email: string, segment: string, score: number) => {
    trackEmailSubmitted(segment, score)
  }

  const handleCTAClick = (ctaType: string, ctaText: string) => {
    trackCTAClicked(ctaType, ctaText)
  }

  return (
    // Results page component
  )
}
```

### Custom Events

```typescript
import { useUserBehaviorTracking } from '../hooks/useAnalytics'

const CustomComponent = () => {
  const { trackActivity } = useUserBehaviorTracking()

  const handleCustomAction = () => {
    trackActivity('custom_action', {
      action_type: 'button_click',
      element_id: 'custom-button',
      custom_data: 'value'
    })
  }

  return (
    <button onClick={handleCustomAction}>
      Custom Action
    </button>
  )
}
```

## Conversion Funnel Tracking

### Funnel Stages

The system tracks the following funnel stages:

1. **Landing Page View** - User lands on the page
2. **Questionnaire Start** - User begins the assessment
3. **Question Completed** - User answers questions
4. **Email Submitted** - User provides email
5. **Results Viewed** - User views results
6. **CTA Clicked** - User takes final action

### Funnel Analysis

```typescript
// Track funnel progression
const { trackFunnelStage } = useConversionFunnel()

// Track each stage
trackFunnelStage(FunnelStage.LANDING_PAGE_VIEW)
trackFunnelStage(FunnelStage.QUESTIONNAIRE_START)
trackFunnelStage(FunnelStage.EMAIL_SUBMITTED, {
  segment: 'stress-free',
  score: 75,
  conversion_value: 75
})
```

### Funnel Metrics

- **Conversion Rate**: Percentage of users who complete each stage
- **Dropoff Rate**: Percentage of users who abandon at each stage
- **Time to Convert**: Average time from start to completion
- **Segment Performance**: Conversion rates by user segment

## A/B Testing Framework

### Test Configuration

```typescript
// A/B test configuration
const abTests = [
  {
    id: 'headline_test',
    name: 'Landing Page Headlines',
    variants: ['control', 'variant_a', 'variant_b'],
    trafficSplit: { control: 33, variant_a: 33, variant_b: 34 },
    isActive: true
  },
  {
    id: 'question_order_test',
    name: 'Question Order Variations',
    variants: ['control', 'reversed', 'random'],
    trafficSplit: { control: 50, reversed: 25, random: 25 },
    isActive: true
  }
]
```

### Using A/B Test Components

#### Headline Testing

```typescript
import { HeadlineTest } from '../components/ABTesting'

const LandingPage = () => {
  return (
    <HeadlineTest
      testId="headline_test"
      controlHeadline="Transform Your Financial Life"
      variantAHeadline="🚀 Take Control of Your Money"
      variantBHeadline="Your Path to Financial Freedom"
      subheadline="Discover your money personality and get personalized strategies"
    />
  )
}
```

#### Question Order Testing

```typescript
import { QuestionOrderTest } from '../components/ABTesting'

const Questionnaire = () => {
  const questions = [
    { id: 'q1', text: 'How do you feel about money?', type: 'multiple_choice', options: ['Stressed', 'Confident', 'Neutral'] },
    { id: 'q2', text: 'What is your primary financial goal?', type: 'multiple_choice', options: ['Save', 'Invest', 'Pay Debt'] }
  ]

  return (
    <QuestionOrderTest
      testId="question_order_test"
      questions={questions}
      onQuestionComplete={(questionId, response) => {
        // Handle question completion
      }}
      currentQuestion={1}
    />
  )
}
```

#### Results Layout Testing

```typescript
import { ResultsLayoutTest } from '../components/ABTesting'

const ResultsPage = () => {
  return (
    <ResultsLayoutTest
      testId="results_layout_test"
      segment="stress-free"
      score={75}
      recommendations={[
        'Set up automatic savings',
        'Create a simple budget',
        'Build an emergency fund'
      ]}
      ctaText="Get Your Personalized Plan"
      onCTAClick={() => {
        // Handle CTA click
      }}
    />
  )
}
```

#### CTA Button Testing

```typescript
import { CTAButtonTest } from '../components/ABTesting'

const CTAButton = () => {
  return (
    <CTAButtonTest
      testId="cta_button_test"
      controlText="Get Started"
      urgentText="Start Now - Limited Time"
      benefitText="Transform Your Finances Today"
      onClick={() => {
        // Handle button click
      }}
    />
  )
}
```

### A/B Test Results

```typescript
import { ABTestResults } from '../components/ABTesting'

const TestResults = () => {
  const results = {
    control: { conversions: 45, impressions: 300 },
    variant_a: { conversions: 52, impressions: 300 },
    variant_b: { conversions: 68, impressions: 400 }
  }

  return (
    <ABTestResults
      testId="headline_test"
      results={results}
    />
  )
}
```

## User Behavior Tracking

### Automatic Tracking

The system automatically tracks:

- **Mouse movements** (every 5 seconds)
- **Clicks** (with element details)
- **Scroll behavior** (with scroll percentage)
- **Page visibility** (when user switches tabs)
- **Screen resizes** (responsive behavior)
- **Network status** (online/offline)

### Manual Tracking

```typescript
import { useUserBehaviorTracking } from '../hooks/useAnalytics'

const Component = () => {
  const { trackActivity, trackTimeOnPage } = useUserBehaviorTracking()

  // Track custom behavior
  const handleImportantAction = () => {
    trackActivity('important_action', {
      action_type: 'form_submit',
      form_id: 'lead_form',
      completion_time: 120
    })
  }

  // Track time on specific page
  useEffect(() => {
    const startTime = Date.now()
    return () => {
      const timeSpent = (Date.now() - startTime) / 1000
      trackTimeOnPage('/questionnaire', timeSpent)
    }
  }, [])

  return (
    // Component JSX
  )
}
```

### Device and Traffic Tracking

```typescript
import { useDeviceTracking } from '../hooks/useAnalytics'

const App = () => {
  // Automatically tracks device info and traffic sources
  useDeviceTracking()

  return (
    // App component
  )
}
```

## GDPR Compliance

### Consent Management

```typescript
import { GDPRConsent, PrivacyControls } from '../components/GDPRConsent'

const App = () => {
  return (
    <div>
      {/* Main app content */}
      
      {/* GDPR consent banner */}
      <GDPRConsent
        onConsentChange={(granted) => {
          console.log('Consent granted:', granted)
        }}
      />
      
      {/* Privacy controls (in settings page) */}
      <PrivacyControls />
    </div>
  )
}
```

### Consent Features

- **Cookie Banner**: Automatic consent request
- **Granular Control**: Individual cookie type preferences
- **Data Deletion**: User can request data deletion
- **Data Export**: User can export their data
- **Consent Withdrawal**: User can withdraw consent anytime

### Privacy Rights

Under GDPR, users have the right to:

1. **Access**: Request access to their personal data
2. **Rectification**: Request correction of inaccurate data
3. **Erasure**: Request deletion of their data
4. **Portability**: Export their data in a machine-readable format
5. **Objection**: Object to data processing
6. **Withdrawal**: Withdraw consent at any time

## Setup Instructions

### 1. Environment Configuration

```bash
# Analytics Configuration
REACT_APP_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_RESPECT_DNT=true
REACT_APP_ANONYMIZE_IP=true
REACT_APP_DEBUG_MODE=false

# A/B Testing
REACT_APP_AB_TESTING_ENABLED=true
REACT_APP_AB_TEST_CONFIDENCE_LEVEL=0.95
REACT_APP_AB_TEST_MIN_SAMPLE_SIZE=100

# GDPR Compliance
REACT_APP_GDPR_COMPLIANCE_ENABLED=true
REACT_APP_COOKIE_CONSENT_REQUIRED=true
```

### 2. Initialize Analytics

```typescript
import { useAnalytics } from '../hooks/useAnalytics'

const App = () => {
  const analytics = useAnalytics(userId)

  return (
    <div>
      {/* Your app content */}
    </div>
  )
}
```

### 3. Set Up A/B Tests

```typescript
// Configure A/B tests in your analytics service
const abTests = [
  {
    id: 'headline_test',
    name: 'Landing Page Headlines',
    variants: ['control', 'variant_a', 'variant_b'],
    trafficSplit: { control: 33, variant_a: 33, variant_b: 34 }
  }
]
```

### 4. Add GDPR Consent

```typescript
import { GDPRConsent } from '../components/GDPRConsent'

const App = () => {
  return (
    <div>
      <main>
        {/* Your app content */}
      </main>
      
      <GDPRConsent />
    </div>
  )
}
```

## Usage Examples

### Complete Questionnaire with Analytics

```typescript
import React, { useState, useEffect } from 'react'
import { useAnalytics } from '../hooks/useAnalytics'
import { HeadlineTest } from '../components/ABTesting'

const Questionnaire = () => {
  const [currentQuestion, setCurrentQuestion] = useState(1)
  const [responses, setResponses] = useState({})
  
  const {
    trackStart,
    trackQuestionComplete,
    trackEmailSubmit,
    trackResultsView
  } = useAnalytics()

  useEffect(() => {
    trackStart()
  }, [])

  const handleQuestionAnswer = (questionId: string, answer: string) => {
    trackQuestionComplete(currentQuestion, `Question ${currentQuestion}`, answer)
    setResponses(prev => ({ ...prev, [questionId]: answer }))
    setCurrentQuestion(prev => prev + 1)
  }

  const handleEmailSubmit = (email: string, segment: string, score: number) => {
    trackEmailSubmit(email, segment, score)
    trackResultsView(segment, score)
  }

  return (
    <div>
      <HeadlineTest
        testId="headline_test"
        controlHeadline="Discover Your Money Personality"
        variantAHeadline="🚀 What's Your Financial DNA?"
        variantBHeadline="Unlock Your Money Potential"
      />
      
      {/* Questionnaire content */}
    </div>
  )
}
```

### Analytics Dashboard

```typescript
import { AnalyticsDashboard } from '../components/AnalyticsDashboard'

const AdminPanel = () => {
  return (
    <div>
      <h1>Admin Dashboard</h1>
      <AnalyticsDashboard />
    </div>
  )
}
```

### Privacy Settings Page

```typescript
import { PrivacyControls, CookiePolicy } from '../components/GDPRConsent'

const PrivacySettings = () => {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Privacy Settings</h1>
      
      <div className="space-y-6">
        <PrivacyControls />
        <CookiePolicy />
      </div>
    </div>
  )
}
```

## Troubleshooting

### Common Issues

#### 1. Analytics Not Tracking

**Problem**: Events not appearing in Google Analytics
**Solution**:
- Check `REACT_APP_GOOGLE_ANALYTICS_ID` is set correctly
- Verify `REACT_APP_ENABLE_ANALYTICS=true`
- Check browser console for errors
- Ensure consent is granted

#### 2. A/B Tests Not Working

**Problem**: A/B test variants not showing
**Solution**:
- Verify test configuration is correct
- Check `REACT_APP_AB_TESTING_ENABLED=true`
- Ensure test is active and has valid variants
- Check session ID generation

#### 3. GDPR Consent Issues

**Problem**: Consent banner not showing or not working
**Solution**:
- Check `REACT_APP_GDPR_COMPLIANCE_ENABLED=true`
- Verify localStorage permissions
- Check for existing consent decisions
- Test in incognito mode

#### 4. Performance Issues

**Problem**: Analytics causing performance problems
**Solution**:
- Enable debug mode to identify bottlenecks
- Check for excessive event firing
- Implement event batching
- Use performance monitoring

### Debug Mode

Enable debug mode to see detailed analytics information:

```bash
REACT_APP_DEBUG_MODE=true
```

This will log all analytics events to the console for debugging.

### Performance Optimization

1. **Event Batching**: Group multiple events together
2. **Throttling**: Limit event frequency
3. **Lazy Loading**: Load analytics only when needed
4. **Caching**: Cache analytics data locally

### Best Practices

1. **Consent First**: Always check consent before tracking
2. **Minimal Data**: Only collect necessary data
3. **Clear Purpose**: Be transparent about data usage
4. **User Control**: Give users control over their data
5. **Regular Audits**: Regularly review analytics implementation

## Analytics Dashboard Features

### Real-time Metrics

- **Active Sessions**: Current users on the site
- **Conversion Rate**: Real-time conversion tracking
- **Funnel Performance**: Live funnel stage progression
- **A/B Test Results**: Current test performance

### Historical Data

- **Trend Analysis**: Performance over time
- **Segment Comparison**: Performance by user segment
- **Device Analysis**: Performance by device type
- **Traffic Source Analysis**: Performance by traffic source

### Export Capabilities

- **CSV Export**: Download data for external analysis
- **PDF Reports**: Generate printable reports
- **API Access**: Programmatic access to analytics data
- **Webhook Integration**: Real-time data streaming

This analytics system provides comprehensive tracking and optimization capabilities while maintaining GDPR compliance and user privacy. The modular design allows for easy customization and extension based on specific needs. 