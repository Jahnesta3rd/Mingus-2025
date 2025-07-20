import { useEffect, useRef, useCallback } from 'react'
import { analytics, FunnelStage } from '../services/analytics'

// Analytics hook for questionnaire tracking
export function useQuestionnaireAnalytics() {
  const questionStartTime = useRef<number>(Date.now())
  const currentQuestion = useRef<number>(1)

  // Track questionnaire start
  const trackStart = useCallback(() => {
    analytics.trackQuestionnaireStart()
    analytics.trackFunnelStage(FunnelStage.QUESTIONNAIRE_START)
  }, [])

  // Track question completion
  const trackQuestionComplete = useCallback((
    questionNumber: number,
    questionText: string,
    response: string
  ) => {
    const timeSpent = (Date.now() - questionStartTime.current) / 1000
    analytics.trackQuestionCompleted(questionNumber, questionText, response, timeSpent)
    
    // Reset timer for next question
    questionStartTime.current = Date.now()
    currentQuestion.current = questionNumber + 1
  }, [])

  // Track questionnaire abandonment
  const trackAbandonment = useCallback((reason?: string) => {
    analytics.trackQuestionnaireAbandoned(currentQuestion.current, reason)
  }, [])

  // Track email submission
  const trackEmailSubmit = useCallback((
    email: string,
    segment: string,
    score: number
  ) => {
    analytics.trackEmailSubmitted(email, segment, score)
    analytics.trackFunnelStage(FunnelStage.EMAIL_SUBMITTED)
  }, [])

  // Track results view
  const trackResultsView = useCallback((segment: string, score: number) => {
    analytics.trackResultsViewed(segment, score)
    analytics.trackFunnelStage(FunnelStage.RESULTS_VIEWED)
  }, [])

  // Track CTA click
  const trackCTAClick = useCallback((
    ctaType: string,
    ctaText: string,
    destination: string
  ) => {
    analytics.trackCTAClick(ctaType, ctaText, destination)
    analytics.trackFunnelStage(FunnelStage.CTA_CLICKED)
  }, [])

  // Track page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // User left the page - track abandonment
        trackAbandonment('page_hidden')
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [trackAbandonment])

  // Track beforeunload
  useEffect(() => {
    const handleBeforeUnload = () => {
      trackAbandonment('page_unload')
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [trackAbandonment])

  return {
    trackStart,
    trackQuestionComplete,
    trackAbandonment,
    trackEmailSubmit,
    trackResultsView,
    trackCTAClick
  }
}

// Analytics hook for A/B testing
export function useABTesting(testId: string) {
  const variant = analytics.getABTestVariant(testId)

  // Track A/B test exposure
  useEffect(() => {
    analytics.trackABTestExposure(testId, variant)
  }, [testId, variant])

  // Track A/B test conversion
  const trackConversion = useCallback((conversionType: string) => {
    analytics.trackABTestConversion(testId, variant, conversionType)
  }, [testId, variant])

  return {
    variant,
    trackConversion
  }
}

// Analytics hook for user behavior tracking
export function useUserBehaviorTracking() {
  const pageStartTime = useRef<number>(Date.now())
  const lastActivity = useRef<number>(Date.now())

  // Track user activity
  const trackActivity = useCallback((action: string, data?: Record<string, any>) => {
    analytics.trackUserBehavior(action, data)
    lastActivity.current = Date.now()
  }, [])

  // Track time on page
  const trackTimeOnPage = useCallback((pagePath: string) => {
    const timeSpent = (Date.now() - pageStartTime.current) / 1000
    analytics.trackTimeOnPage(pagePath, timeSpent)
    pageStartTime.current = Date.now()
  }, [])

  // Track mouse movements and clicks
  useEffect(() => {
    const handleMouseMove = () => {
      const now = Date.now()
      if (now - lastActivity.current > 5000) { // Track every 5 seconds
        trackActivity('mouse_movement')
      }
    }

    const handleClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      trackActivity('click', {
        element: target.tagName,
        element_id: target.id,
        element_class: target.className,
        text_content: target.textContent?.substring(0, 50)
      })
    }

    const handleScroll = () => {
      const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
      trackActivity('scroll', { scroll_percent: Math.round(scrollPercent) })
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('click', handleClick)
    document.addEventListener('scroll', handleScroll)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('click', handleClick)
      document.removeEventListener('scroll', handleScroll)
    }
  }, [trackActivity])

  // Track page visibility
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        trackActivity('page_hidden')
      } else {
        trackActivity('page_visible')
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [trackActivity])

  return {
    trackActivity,
    trackTimeOnPage
  }
}

// Analytics hook for conversion funnel tracking
export function useConversionFunnel() {
  const funnelStage = useRef<FunnelStage>(FunnelStage.LANDING_PAGE_VIEW)

  // Track funnel stage progression
  const trackFunnelStage = useCallback((stage: FunnelStage, data?: Record<string, any>) => {
    analytics.trackFunnelStage(stage, data)
    funnelStage.current = stage
  }, [])

  // Track landing page view
  const trackLandingPageView = useCallback(() => {
    trackFunnelStage(FunnelStage.LANDING_PAGE_VIEW)
  }, [trackFunnelStage])

  // Track questionnaire start
  const trackQuestionnaireStart = useCallback(() => {
    trackFunnelStage(FunnelStage.QUESTIONNAIRE_START)
  }, [trackFunnelStage])

  // Track question completion
  const trackQuestionCompleted = useCallback((questionNumber: number, totalQuestions: number) => {
    const progress = (questionNumber / totalQuestions) * 100
    trackFunnelStage(FunnelStage.QUESTION_COMPLETED, {
      question_number: questionNumber,
      progress_percentage: progress
    })
  }, [trackFunnelStage])

  // Track email submission
  const trackEmailSubmitted = useCallback((segment: string, score: number) => {
    trackFunnelStage(FunnelStage.EMAIL_SUBMITTED, {
      segment,
      score,
      conversion_value: score // Use score as conversion value
    })
  }, [trackFunnelStage])

  // Track results viewed
  const trackResultsViewed = useCallback((segment: string, score: number) => {
    trackFunnelStage(FunnelStage.RESULTS_VIEWED, {
      segment,
      score
    })
  }, [trackFunnelStage])

  // Track CTA click
  const trackCTAClicked = useCallback((ctaType: string, ctaText: string) => {
    trackFunnelStage(FunnelStage.CTA_CLICKED, {
      cta_type: ctaType,
      cta_text: ctaText
    })
  }, [trackFunnelStage])

  return {
    currentStage: funnelStage.current,
    trackLandingPageView,
    trackQuestionnaireStart,
    trackQuestionCompleted,
    trackEmailSubmitted,
    trackResultsViewed,
    trackCTAClicked
  }
}

// Analytics hook for device and traffic tracking
export function useDeviceTracking() {
  // Track device information on mount
  useEffect(() => {
    analytics.trackDeviceInfo()
    analytics.trackTrafficSource()
  }, [])

  // Track screen size changes
  useEffect(() => {
    const handleResize = () => {
      analytics.trackUserBehavior('screen_resize', {
        width: window.innerWidth,
        height: window.innerHeight
      })
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Track network status
  useEffect(() => {
    const handleOnline = () => {
      analytics.trackUserBehavior('network_online')
    }

    const handleOffline = () => {
      analytics.trackUserBehavior('network_offline')
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])
}

// Analytics hook for session management
export function useAnalyticsSession(userId?: string) {
  // Initialize session on mount
  useEffect(() => {
    analytics.initializeSession(userId)
  }, [userId])

  // Track session timeout
  useEffect(() => {
    const checkSessionTimeout = () => {
      // Session timeout logic can be implemented here
      analytics.trackUserBehavior('session_check')
    }

    const interval = setInterval(checkSessionTimeout, 60000) // Check every minute
    return () => clearInterval(interval)
  }, [])

  return {
    // Session management methods can be exposed here
  }
}

// Analytics hook for GDPR compliance
export function useAnalyticsConsent() {
  const [consentGranted, setConsentGranted] = useState<boolean>(false)

  // Check for existing consent
  useEffect(() => {
    const savedConsent = localStorage.getItem('analytics_consent')
    if (savedConsent) {
      const consent = JSON.parse(savedConsent)
      setConsentGranted(consent.granted)
      analytics.setConsent(consent.granted)
    }
  }, [])

  // Grant consent
  const grantConsent = useCallback(() => {
    setConsentGranted(true)
    analytics.setConsent(true)
    localStorage.setItem('analytics_consent', JSON.stringify({
      granted: true,
      timestamp: Date.now()
    }))
  }, [])

  // Deny consent
  const denyConsent = useCallback(() => {
    setConsentGranted(false)
    analytics.setConsent(false)
    localStorage.setItem('analytics_consent', JSON.stringify({
      granted: false,
      timestamp: Date.now()
    }))
  }, [])

  // Delete user data
  const deleteUserData = useCallback(async (userId: string) => {
    await analytics.deleteUserData(userId)
  }, [])

  // Export user data
  const exportUserData = useCallback(async (userId: string) => {
    return await analytics.exportUserData(userId)
  }, [])

  return {
    consentGranted,
    grantConsent,
    denyConsent,
    deleteUserData,
    exportUserData
  }
}

// Combined analytics hook for easy use
export function useAnalytics(userId?: string) {
  const questionnaire = useQuestionnaireAnalytics()
  const behavior = useUserBehaviorTracking()
  const funnel = useConversionFunnel()
  const consent = useAnalyticsConsent()

  // Initialize device tracking
  useDeviceTracking()

  // Initialize session
  useAnalyticsSession(userId)

  return {
    ...questionnaire,
    ...behavior,
    ...funnel,
    ...consent
  }
}

// Missing import
import { useState } from 'react' 