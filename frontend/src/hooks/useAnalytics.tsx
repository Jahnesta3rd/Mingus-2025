import { useCallback } from 'react';

interface AnalyticsEvent {
  event_type: string;
  user_id?: string;
  session_id?: string;
  page_url: string;
  element_id?: string;
  element_text?: string;
  interaction_data?: Record<string, any>;
  timestamp?: string;
}

export const useAnalytics = () => {
  const getSessionId = useCallback((): string => {
    let sessionId = sessionStorage.getItem('mingus_session_id');
    if (!sessionId) {
      sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem('mingus_session_id', sessionId);
    }
    return sessionId;
  }, []);

  const getUserId = useCallback((): string => {
    return localStorage.getItem('mingus_user_id') || 'anonymous';
  }, []);

  const trackPageView = useCallback(async (page: string, metadata?: Record<string, any>) => {
    try {
      const event: AnalyticsEvent = {
        event_type: 'page_view',
        user_id: getUserId(),
        session_id: getSessionId(),
        page_url: page,
        interaction_data: metadata,
        timestamp: new Date().toISOString()
      };

      await fetch('/api/analytics/user-behavior/track-interaction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': getCSRFToken()
        },
        body: JSON.stringify(event)
      });
    } catch (error) {
      console.error('Failed to track page view:', error);
    }
  }, [getSessionId, getUserId]);

  const trackInteraction = useCallback(async (interactionType: string, data?: Record<string, any>) => {
    try {
      const event: AnalyticsEvent = {
        event_type: interactionType,
        user_id: getUserId(),
        session_id: getSessionId(),
        page_url: window.location.pathname,
        interaction_data: data,
        timestamp: new Date().toISOString()
      };

      await fetch('/api/analytics/user-behavior/track-interaction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': getCSRFToken()
        },
        body: JSON.stringify(event)
      });
    } catch (error) {
      console.error('Failed to track interaction:', error);
    }
  }, [getSessionId, getUserId]);

  const trackError = useCallback(async (error: Error, context?: Record<string, any>) => {
    try {
      const event: AnalyticsEvent = {
        event_type: 'error',
        user_id: getUserId(),
        session_id: getSessionId(),
        page_url: window.location.pathname,
        interaction_data: {
          error_message: error.message,
          error_stack: error.stack,
          ...context
        },
        timestamp: new Date().toISOString()
      };

      await fetch('/api/analytics/user-behavior/track-interaction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': getCSRFToken()
        },
        body: JSON.stringify(event)
      });
    } catch (trackingError) {
      console.error('Failed to track error:', trackingError);
    }
  }, [getSessionId, getUserId]);

  return {
    trackPageView,
    trackInteraction,
    trackError,
    getSessionId,
    getUserId
  };
};

const getCSRFToken = (): string => {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute('content') || '';
  }
  
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrf_token') {
      return value;
    }
  }
  
  return '';
};
