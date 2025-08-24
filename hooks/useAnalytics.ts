// hooks/useAnalytics.ts
import { useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import {
  trackEvent,
  trackPageView,
  identifyUser,
  trackConversion,
  trackError,
  trackPerformance,
  EVENT_CATEGORIES
} from '../lib/analytics';

interface UseAnalyticsOptions {
  enablePageTracking?: boolean;
  enableErrorTracking?: boolean;
  enablePerformanceTracking?: boolean;
  userId?: string;
  userProperties?: Record<string, any>;
}

export const useAnalytics = (options: UseAnalyticsOptions = {}) => {
  const router = useRouter();
  const {
    enablePageTracking = true,
    enableErrorTracking = true,
    enablePerformanceTracking = true,
    userId,
    userProperties = {}
  } = options;

  // Initialize user identification
  useEffect(() => {
    if (userId) {
      identifyUser(userId, userProperties);
    }
  }, [userId, userProperties]);

  // Track page views
  useEffect(() => {
    if (!enablePageTracking) return;

    const handleRouteChange = (url: string) => {
      const pageTitle = document.title || 'MINGUS';
      trackPageView(pageTitle, url);
    };

    // Track initial page load
    handleRouteChange(router.asPath);

    // Track route changes
    router.events.on('routeChangeComplete', handleRouteChange);

    return () => {
      router.events.off('routeChangeComplete', handleRouteChange);
    };
  }, [router, enablePageTracking]);

  // Track errors
  useEffect(() => {
    if (!enableErrorTracking) return;

    const handleError = (event: ErrorEvent) => {
      trackError(
        event.message,
        'JAVASCRIPT_ERROR',
        {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
          stack: event.error?.stack
        }
      );
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      trackError(
        event.reason?.message || 'Unhandled Promise Rejection',
        'PROMISE_REJECTION',
        {
          reason: event.reason
        }
      );
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, [enableErrorTracking]);

  // Track performance metrics
  useEffect(() => {
    if (!enablePerformanceTracking || typeof window === 'undefined') return;

    const trackPerformanceMetrics = () => {
      // Track page load time
      if ('performance' in window) {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigation) {
          trackPerformance('page_load_time', navigation.loadEventEnd - navigation.loadEventStart);
          trackPerformance('dom_content_loaded', navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart);
          trackPerformance('first_paint', performance.getEntriesByName('first-paint')[0]?.startTime || 0);
          trackPerformance('first_contentful_paint', performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0);
        }
      }
    };

    // Track performance after page load
    if (document.readyState === 'complete') {
      trackPerformanceMetrics();
    } else {
      window.addEventListener('load', trackPerformanceMetrics);
      return () => window.removeEventListener('load', trackPerformanceMetrics);
    }
  }, [enablePerformanceTracking]);

  // Track events
  const track = useCallback((
    eventName: string,
    properties: Record<string, any> = {},
    category: string = 'general'
  ) => {
    trackEvent(eventName, properties, category);
  }, []);

  // Track landing page events
  const trackLandingEvent = useCallback((
    eventName: string,
    properties: Record<string, any> = {}
  ) => {
    track(eventName, properties, EVENT_CATEGORIES.LANDING);
  }, [track]);

  // Track onboarding events
  const trackOnboardingEvent = useCallback((
    eventName: string,
    properties: Record<string, any> = {}
  ) => {
    track(eventName, properties, EVENT_CATEGORIES.ONBOARDING);
  }, [track]);

  // Track dashboard events
  const trackDashboardEvent = useCallback((
    eventName: string,
    properties: Record<string, any> = {}
  ) => {
    track(eventName, properties, EVENT_CATEGORIES.DASHBOARD);
  }, [track]);

  // Track feature events
  const trackFeatureEvent = useCallback((
    eventName: string,
    properties: Record<string, any> = {}
  ) => {
    track(eventName, properties, EVENT_CATEGORIES.FEATURES);
  }, [track]);

  // Track conversion events
  const trackConversionEvent = useCallback((
    conversionType: string,
    value: number,
    currency: string = 'USD',
    additionalProperties: Record<string, any> = {}
  ) => {
    trackConversion(conversionType, value, currency, additionalProperties);
  }, []);

  // Track engagement events
  const trackEngagementEvent = useCallback((
    eventName: string,
    properties: Record<string, any> = {}
  ) => {
    track(eventName, properties, EVENT_CATEGORIES.ENGAGEMENT);
  }, [track]);

  // Track form interactions
  const trackFormInteraction = useCallback((
    formName: string,
    action: 'start' | 'complete' | 'error' | 'abandon',
    additionalProperties: Record<string, any> = {}
  ) => {
    const eventName = `form_${action}`;
    const properties = {
      form_name: formName,
      ...additionalProperties
    };
    track(eventName, properties, EVENT_CATEGORIES.ENGAGEMENT);
  }, [track]);

  // Track button clicks
  const trackButtonClick = useCallback((
    buttonName: string,
    buttonLocation: string,
    additionalProperties: Record<string, any> = {}
  ) => {
    const properties = {
      button_name: buttonName,
      button_location: buttonLocation,
      ...additionalProperties
    };
    track('button_click', properties, EVENT_CATEGORIES.ENGAGEMENT);
  }, [track]);

  // Track scroll depth
  const trackScrollDepth = useCallback((depth: number) => {
    track('scroll_depth', { scroll_depth: depth }, EVENT_CATEGORIES.ENGAGEMENT);
  }, [track]);

  // Track time on page
  const trackTimeOnPage = useCallback((timeInSeconds: number) => {
    track('time_on_page', { time_on_page: timeInSeconds }, EVENT_CATEGORIES.ENGAGEMENT);
  }, [track]);

  // Track user identification
  const identify = useCallback((userId: string, properties: Record<string, any> = {}) => {
    identifyUser(userId, properties);
  }, []);

  // Track errors
  const trackErrorEvent = useCallback((
    errorMessage: string,
    errorCode: string,
    additionalProperties: Record<string, any> = {}
  ) => {
    trackError(errorMessage, errorCode, additionalProperties);
  }, []);

  // Track performance
  const trackPerformanceEvent = useCallback((
    metricName: string,
    value: number,
    additionalProperties: Record<string, any> = {}
  ) => {
    trackPerformance(metricName, value, additionalProperties);
  }, []);

  return {
    // Core tracking functions
    track,
    trackLandingEvent,
    trackOnboardingEvent,
    trackDashboardEvent,
    trackFeatureEvent,
    trackConversionEvent,
    trackEngagementEvent,

    // Specific event tracking
    trackFormInteraction,
    trackButtonClick,
    trackScrollDepth,
    trackTimeOnPage,

    // User management
    identify,

    // Error and performance tracking
    trackErrorEvent,
    trackPerformanceEvent
  };
};

// Specialized hooks for different contexts

// Hook for landing pages
export const useLandingAnalytics = (options: UseAnalyticsOptions = {}) => {
  const analytics = useAnalytics(options);

  const trackHeroCTA = useCallback((ctaType: string, additionalProperties: Record<string, any> = {}) => {
    analytics.trackLandingEvent('hero_cta_click', {
      cta_type: ctaType,
      ...additionalProperties
    });
  }, [analytics]);

  const trackFeatureSection = useCallback((sectionName: string, action: string, additionalProperties: Record<string, any> = {}) => {
    analytics.trackLandingEvent('feature_section_interaction', {
      section_name: sectionName,
      action,
      ...additionalProperties
    });
  }, [analytics]);

  const trackTestimonial = useCallback((testimonialId: string, action: string, additionalProperties: Record<string, any> = {}) => {
    analytics.trackLandingEvent('testimonial_interaction', {
      testimonial_id: testimonialId,
      action,
      ...additionalProperties
    });
  }, [analytics]);

  return {
    ...analytics,
    trackHeroCTA,
    trackFeatureSection,
    trackTestimonial
  };
};

// Hook for onboarding
export const useOnboardingAnalytics = (options: UseAnalyticsOptions = {}) => {
  const analytics = useAnalytics(options);

  const trackStepComplete = useCallback((step: number, additionalProperties: Record<string, any> = {}) => {
    analytics.trackOnboardingEvent('step_complete', {
      step_number: step,
      ...additionalProperties
    });
  }, [analytics]);

  const trackStepSkip = useCallback((step: number, reason: string, additionalProperties: Record<string, any> = {}) => {
    analytics.trackOnboardingEvent('step_skip', {
      step_number: step,
      skip_reason: reason,
      ...additionalProperties
    });
  }, [analytics]);

  const trackOnboardingComplete = useCallback((totalSteps: number, timeSpent: number, additionalProperties: Record<string, any> = {}) => {
    analytics.trackOnboardingEvent('onboarding_complete', {
      total_steps: totalSteps,
      time_spent: timeSpent,
      ...additionalProperties
    });
  }, [analytics]);

  return {
    ...analytics,
    trackStepComplete,
    trackStepSkip,
    trackOnboardingComplete
  };
};

// Hook for dashboard
export const useDashboardAnalytics = (options: UseAnalyticsOptions = {}) => {
  const analytics = useAnalytics(options);

  const trackWidgetInteraction = useCallback((widgetName: string, action: string, additionalProperties: Record<string, any> = {}) => {
    analytics.trackDashboardEvent('widget_interaction', {
      widget_name: widgetName,
      action,
      ...additionalProperties
    });
  }, [analytics]);

  const trackDataExport = useCallback((exportType: string, additionalProperties: Record<string, any> = {}) => {
    analytics.trackDashboardEvent('data_export', {
      export_type: exportType,
      ...additionalProperties
    });
  }, [analytics]);

  return {
    ...analytics,
    trackWidgetInteraction,
    trackDataExport
  };
}; 