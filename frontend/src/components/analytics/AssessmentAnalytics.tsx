import React, { createContext, useContext, useEffect, useRef, useCallback } from 'react';

// Analytics event types
export enum AnalyticsEventType {
  ASSESSMENT_LANDING_VIEWED = 'assessment_landing_viewed',
  ASSESSMENT_STARTED = 'assessment_started',
  ASSESSMENT_QUESTION_ANSWERED = 'assessment_question_answered',
  ASSESSMENT_COMPLETED = 'assessment_completed',
  EMAIL_CAPTURED = 'email_captured',
  CONVERSION_MODAL_OPENED = 'conversion_modal_opened',
  PAYMENT_INITIATED = 'payment_initiated',
  SOCIAL_PROOF_INTERACTION = 'social_proof_interaction',
  ASSESSMENT_ABANDONED = 'assessment_abandoned',
  ASSESSMENT_RESUMED = 'assessment_resumed',
  ASSESSMENT_SHARED = 'assessment_shared',
  LEAD_QUALIFIED = 'lead_qualified'
}

// Analytics event interface
export interface AnalyticsEvent {
  event_type: AnalyticsEventType;
  session_id: string;
  assessment_type?: string;
  assessment_id?: string;
  properties?: Record<string, any>;
  page_load_time?: number;
  time_on_page?: number;
}

// Analytics context interface
interface AnalyticsContextType {
  trackEvent: (event: AnalyticsEvent) => Promise<void>;
  trackPageView: (assessmentType?: string) => Promise<void>;
  trackAssessmentStart: (assessmentType: string, assessmentId?: string) => Promise<void>;
  trackQuestionAnswered: (questionId: string, questionNumber?: number, timeSpent?: number) => Promise<void>;
  trackAssessmentCompleted: (assessmentType: string, score?: number, riskLevel?: string, completionTime?: number) => Promise<void>;
  trackEmailCapture: (email: string, leadSource?: string) => Promise<void>;
  trackConversionModal: (modalType?: string, triggerSource?: string) => Promise<void>;
  trackPaymentInitiated: (paymentAmount: number, paymentMethod?: string, subscriptionType?: string) => Promise<void>;
  trackSocialProofInteraction: (interactionType: string) => Promise<void>;
  getSessionId: () => string;
  getUTMParams: () => Record<string, string>;
}

// Analytics context
const AnalyticsContext = createContext<AnalyticsContextType | null>(null);

// Analytics provider props
interface AnalyticsProviderProps {
  children: React.ReactNode;
  apiBaseUrl?: string;
  enableTracking?: boolean;
  debugMode?: boolean;
}

// Analytics provider component
export const AnalyticsProvider: React.FC<AnalyticsProviderProps> = ({
  children,
  apiBaseUrl = '/api/analytics',
  enableTracking = true,
  debugMode = false
}) => {
  const sessionId = useRef<string>(generateSessionId());
  const pageStartTime = useRef<number>(Date.now());
  const currentAssessmentType = useRef<string | null>(null);
  const currentAssessmentId = useRef<string | null>(null);
  const questionStartTime = useRef<number | null>(null);

  // Generate session ID
  function generateSessionId(): string {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Get UTM parameters from URL
  const getUTMParams = useCallback((): Record<string, string> => {
    const urlParams = new URLSearchParams(window.location.search);
    return {
      utm_source: urlParams.get('utm_source') || '',
      utm_medium: urlParams.get('utm_medium') || '',
      utm_campaign: urlParams.get('utm_campaign') || '',
      utm_term: urlParams.get('utm_term') || '',
      utm_content: urlParams.get('utm_content') || ''
    };
  }, []);

  // Get page load time
  const getPageLoadTime = useCallback((): number => {
    if (performance && performance.timing) {
      return performance.timing.loadEventEnd - performance.timing.navigationStart;
    }
    return Date.now() - pageStartTime.current;
  }, []);

  // Get time on page
  const getTimeOnPage = useCallback((): number => {
    return Date.now() - pageStartTime.current;
  }, []);

  // Track event to backend
  const trackEvent = useCallback(async (event: AnalyticsEvent): Promise<void> => {
    if (!enableTracking) {
      if (debugMode) {
        console.log('Analytics tracking disabled:', event);
      }
      return;
    }

    try {
      const eventData = {
        ...event,
        session_id: sessionId.current,
        page_load_time: getPageLoadTime(),
        time_on_page: getTimeOnPage(),
        ...getUTMParams()
      };

      const response = await fetch(`${apiBaseUrl}/track-event`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(eventData)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (debugMode) {
        console.log('Analytics event tracked:', eventData);
      }
    } catch (error) {
      console.error('Error tracking analytics event:', error);
      if (debugMode) {
        console.log('Failed analytics event:', event);
      }
    }
  }, [apiBaseUrl, enableTracking, debugMode, getPageLoadTime, getTimeOnPage, getUTMParams]);

  // Track page view
  const trackPageView = useCallback(async (assessmentType?: string): Promise<void> => {
    await trackEvent({
      event_type: AnalyticsEventType.ASSESSMENT_LANDING_VIEWED,
      session_id: sessionId.current,
      assessment_type: assessmentType,
      properties: {
        page_url: window.location.href,
        referrer: document.referrer
      }
    });
  }, [trackEvent]);

  // Track assessment start
  const trackAssessmentStart = useCallback(async (assessmentType: string, assessmentId?: string): Promise<void> => {
    currentAssessmentType.current = assessmentType;
    currentAssessmentId.current = assessmentId || null;
    pageStartTime.current = Date.now();

    await trackEvent({
      event_type: AnalyticsEventType.ASSESSMENT_STARTED,
      session_id: sessionId.current,
      assessment_type: assessmentType,
      assessment_id: assessmentId,
      properties: {
        estimated_duration: 10, // Default estimate
        questions_count: 15 // Default estimate
      }
    });
  }, [trackEvent]);

  // Track question answered
  const trackQuestionAnswered = useCallback(async (
    questionId: string, 
    questionNumber?: number, 
    timeSpent?: number
  ): Promise<void> => {
    const timeSpentOnQuestion = timeSpent || (questionStartTime.current ? Date.now() - questionStartTime.current : 0);
    questionStartTime.current = Date.now();

    await trackEvent({
      event_type: AnalyticsEventType.ASSESSMENT_QUESTION_ANSWERED,
      session_id: sessionId.current,
      assessment_type: currentAssessmentType.current || undefined,
      assessment_id: currentAssessmentId.current || undefined,
      properties: {
        question_id: questionId,
        question_number: questionNumber,
        time_spent: timeSpentOnQuestion,
        answer_type: 'user_input'
      }
    });
  }, [trackEvent]);

  // Track assessment completed
  const trackAssessmentCompleted = useCallback(async (
    assessmentType: string, 
    score?: number, 
    riskLevel?: string, 
    completionTime?: number
  ): Promise<void> => {
    const finalCompletionTime = completionTime || (Date.now() - pageStartTime.current);

    await trackEvent({
      event_type: AnalyticsEventType.ASSESSMENT_COMPLETED,
      session_id: sessionId.current,
      assessment_type: assessmentType,
      assessment_id: currentAssessmentId.current || undefined,
      properties: {
        score: score,
        risk_level: riskLevel,
        completion_time: finalCompletionTime,
        questions_answered: 15, // This should be dynamic based on actual questions
        conversion_eligible: score && score > 50 // Example logic
      }
    });

    // Reset assessment tracking
    currentAssessmentType.current = null;
    currentAssessmentId.current = null;
  }, [trackEvent]);

  // Track email capture
  const trackEmailCapture = useCallback(async (email: string, leadSource: string = 'assessment'): Promise<void> => {
    await trackEvent({
      event_type: AnalyticsEventType.EMAIL_CAPTURED,
      session_id: sessionId.current,
      assessment_type: currentAssessmentType.current || undefined,
      properties: {
        email: email,
        lead_source: leadSource,
        conversion_eligible: true
      }
    });
  }, [trackEvent]);

  // Track conversion modal
  const trackConversionModal = useCallback(async (modalType: string = 'conversion', triggerSource?: string): Promise<void> => {
    await trackEvent({
      event_type: AnalyticsEventType.CONVERSION_MODAL_OPENED,
      session_id: sessionId.current,
      assessment_type: currentAssessmentType.current || undefined,
      properties: {
        modal_type: modalType,
        trigger_source: triggerSource,
        conversion_value: 99 // Example value
      }
    });
  }, [trackEvent]);

  // Track payment initiated
  const trackPaymentInitiated = useCallback(async (
    paymentAmount: number, 
    paymentMethod: string = 'stripe', 
    subscriptionType: string = 'monthly'
  ): Promise<void> => {
    await trackEvent({
      event_type: AnalyticsEventType.PAYMENT_INITIATED,
      session_id: sessionId.current,
      assessment_type: currentAssessmentType.current || undefined,
      properties: {
        payment_amount: paymentAmount,
        payment_method: paymentMethod,
        currency: 'USD',
        subscription_type: subscriptionType
      }
    });
  }, [trackEvent]);

  // Track social proof interaction
  const trackSocialProofInteraction = useCallback(async (interactionType: string): Promise<void> => {
    await trackEvent({
      event_type: AnalyticsEventType.SOCIAL_PROOF_INTERACTION,
      session_id: sessionId.current,
      assessment_type: currentAssessmentType.current || undefined,
      properties: {
        interaction_type: interactionType
      }
    });
  }, [trackEvent]);

  // Get session ID
  const getSessionId = useCallback((): string => {
    return sessionId.current;
  }, []);

  // Track page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page hidden - could track abandonment
        if (currentAssessmentType.current) {
          trackEvent({
            event_type: AnalyticsEventType.ASSESSMENT_ABANDONED,
            session_id: sessionId.current,
            assessment_type: currentAssessmentType.current,
            properties: {
              time_spent: Date.now() - pageStartTime.current
            }
          });
        }
      } else {
        // Page visible again - could track resumption
        if (currentAssessmentType.current) {
          trackEvent({
            event_type: AnalyticsEventType.ASSESSMENT_RESUMED,
            session_id: sessionId.current,
            assessment_type: currentAssessmentType.current,
            properties: {
              time_away: 0 // This would need to be calculated
            }
          });
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [trackEvent]);

  // Track before unload
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (currentAssessmentType.current) {
        // Send synchronous request to track abandonment
        navigator.sendBeacon(`${apiBaseUrl}/track-event`, JSON.stringify({
          event_type: AnalyticsEventType.ASSESSMENT_ABANDONED,
          session_id: sessionId.current,
          assessment_type: currentAssessmentType.current,
          properties: {
            time_spent: Date.now() - pageStartTime.current
          }
        }));
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [apiBaseUrl]);

  // Context value
  const contextValue: AnalyticsContextType = {
    trackEvent,
    trackPageView,
    trackAssessmentStart,
    trackQuestionAnswered,
    trackAssessmentCompleted,
    trackEmailCapture,
    trackConversionModal,
    trackPaymentInitiated,
    trackSocialProofInteraction,
    getSessionId,
    getUTMParams
  };

  return (
    <AnalyticsContext.Provider value={contextValue}>
      {children}
    </AnalyticsContext.Provider>
  );
};

// Hook to use analytics
export const useAnalytics = (): AnalyticsContextType => {
  const context = useContext(AnalyticsContext);
  if (!context) {
    throw new Error('useAnalytics must be used within an AnalyticsProvider');
  }
  return context;
};

// Hook to track page views automatically
export const usePageViewTracking = (assessmentType?: string) => {
  const { trackPageView } = useAnalytics();

  useEffect(() => {
    trackPageView(assessmentType);
  }, [trackPageView, assessmentType]);
};

// Hook to track assessment progress
export const useAssessmentTracking = (assessmentType: string, assessmentId?: string) => {
  const { trackAssessmentStart, trackQuestionAnswered, trackAssessmentCompleted } = useAnalytics();

  const startAssessment = useCallback(() => {
    trackAssessmentStart(assessmentType, assessmentId);
  }, [trackAssessmentStart, assessmentType, assessmentId]);

  const answerQuestion = useCallback((questionId: string, questionNumber?: number, timeSpent?: number) => {
    trackQuestionAnswered(questionId, questionNumber, timeSpent);
  }, [trackQuestionAnswered]);

  const completeAssessment = useCallback((score?: number, riskLevel?: string, completionTime?: number) => {
    trackAssessmentCompleted(assessmentType, score, riskLevel, completionTime);
  }, [trackAssessmentCompleted, assessmentType]);

  return {
    startAssessment,
    answerQuestion,
    completeAssessment
  };
};

// Hook to track conversion events
export const useConversionTracking = () => {
  const { trackEmailCapture, trackConversionModal, trackPaymentInitiated } = useAnalytics();

  const captureEmail = useCallback((email: string, leadSource?: string) => {
    trackEmailCapture(email, leadSource);
  }, [trackEmailCapture]);

  const openConversionModal = useCallback((modalType?: string, triggerSource?: string) => {
    trackConversionModal(modalType, triggerSource);
  }, [trackConversionModal]);

  const initiatePayment = useCallback((paymentAmount: number, paymentMethod?: string, subscriptionType?: string) => {
    trackPaymentInitiated(paymentAmount, paymentMethod, subscriptionType);
  }, [trackPaymentInitiated]);

  return {
    captureEmail,
    openConversionModal,
    initiatePayment
  };
};

// Hook to track social proof interactions
export const useSocialProofTracking = () => {
  const { trackSocialProofInteraction } = useAnalytics();

  const trackInteraction = useCallback((interactionType: string) => {
    trackSocialProofInteraction(interactionType);
  }, [trackSocialProofInteraction]);

  return {
    trackInteraction
  };
};

export default AnalyticsProvider;
