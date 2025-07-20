import { Database } from '../types/database'

type Lead = Database['public']['Tables']['leads']['Row']

// Analytics configuration
interface AnalyticsConfig {
  googleAnalyticsId: string
  enableTracking: boolean
  respectDNT: boolean
  anonymizeIP: boolean
  sessionTimeout: number
  debugMode: boolean
}

// Event tracking interface
interface AnalyticsEvent {
  eventName: string
  parameters: Record<string, any>
  timestamp?: number
  sessionId?: string
  userId?: string
}

// Conversion funnel stages
export enum FunnelStage {
  LANDING_PAGE_VIEW = 'landing_page_view',
  QUESTIONNAIRE_START = 'questionnaire_start',
  QUESTION_COMPLETED = 'question_completed',
  EMAIL_SUBMITTED = 'email_submitted',
  RESULTS_VIEWED = 'results_viewed',
  CTA_CLICKED = 'cta_clicked'
}

// A/B test configuration
interface ABTestConfig {
  id: string
  name: string
  variants: string[]
  trafficSplit: Record<string, number>
  isActive: boolean
  startDate: Date
  endDate?: Date
}

// User session data
interface UserSession {
  sessionId: string
  userId?: string
  startTime: number
  lastActivity: number
  deviceInfo: DeviceInfo
  trafficSource: TrafficSource
  funnelStage: FunnelStage
  questionProgress: number
  timeOnPage: number
}

// Device information
interface DeviceInfo {
  userAgent: string
  screenResolution: string
  viewportSize: string
  deviceType: 'desktop' | 'tablet' | 'mobile'
  browser: string
  os: string
  language: string
}

// Traffic source information
interface TrafficSource {
  utmSource?: string
  utmMedium?: string
  utmCampaign?: string
  utmTerm?: string
  utmContent?: string
  referrer?: string
  landingPage: string
}

// Analytics service class
export class AnalyticsService {
  private config: AnalyticsConfig
  private session: UserSession | null = null
  private abTests: Map<string, ABTestConfig> = new Map()
  private questionStartTimes: Map<number, number> = new Map()
  private consentGranted: boolean = false

  constructor() {
    this.config = {
      googleAnalyticsId: process.env.REACT_APP_GOOGLE_ANALYTICS_ID || '',
      enableTracking: process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
      respectDNT: process.env.REACT_APP_RESPECT_DNT === 'true',
      anonymizeIP: process.env.REACT_APP_ANONYMIZE_IP === 'true',
      sessionTimeout: parseInt(process.env.REACT_APP_SESSION_TIMEOUT || '1800000'), // 30 minutes
      debugMode: process.env.REACT_APP_DEBUG_MODE === 'true'
    }

    this.initializeAnalytics()
    this.loadABTests()
  }

  // Initialize Google Analytics 4
  private initializeAnalytics(): void {
    if (!this.config.enableTracking || !this.config.googleAnalyticsId) {
      return
    }

    // Check Do Not Track
    if (this.config.respectDNT && navigator.doNotTrack === '1') {
      this.log('Analytics disabled due to Do Not Track preference')
      return
    }

    // Load Google Analytics script
    const script = document.createElement('script')
    script.async = true
    script.src = `https://www.googletagmanager.com/gtag/js?id=${this.config.googleAnalyticsId}`
    document.head.appendChild(script)

    // Initialize gtag
    window.dataLayer = window.dataLayer || []
    function gtag(...args: any[]) {
      window.dataLayer.push(args)
    }
    gtag('js', new Date())
    gtag('config', this.config.googleAnalyticsId, {
      anonymize_ip: this.config.anonymizeIP,
      send_page_view: false // We'll handle page views manually
    })

    // Store gtag function globally
    window.gtag = gtag
  }

  // Initialize user session
  public initializeSession(userId?: string): void {
    if (!this.consentGranted) {
      this.log('Analytics session not initialized - consent not granted')
      return
    }

    const sessionId = this.generateSessionId()
    const deviceInfo = this.getDeviceInfo()
    const trafficSource = this.getTrafficSource()

    this.session = {
      sessionId,
      userId,
      startTime: Date.now(),
      lastActivity: Date.now(),
      deviceInfo,
      trafficSource,
      funnelStage: FunnelStage.LANDING_PAGE_VIEW,
      questionProgress: 0,
      timeOnPage: 0
    }

    this.trackEvent('session_start', {
      session_id: sessionId,
      user_id: userId,
      device_type: deviceInfo.deviceType,
      browser: deviceInfo.browser,
      os: deviceInfo.os,
      traffic_source: trafficSource.utmSource || 'direct',
      landing_page: trafficSource.landingPage
    })

    // Track landing page view
    this.trackPageView('Landing Page', '/')
  }

  // Track page view
  public trackPageView(pageTitle: string, pagePath: string): void {
    if (!this.shouldTrack()) return

    this.trackEvent('page_view', {
      page_title: pageTitle,
      page_path: pagePath,
      page_location: window.location.href
    })

    // Update session
    if (this.session) {
      this.session.lastActivity = Date.now()
    }
  }

  // Track questionnaire start
  public trackQuestionnaireStart(): void {
    if (!this.shouldTrack()) return

    this.trackEvent('questionnaire_start', {
      session_id: this.session?.sessionId,
      user_id: this.session?.userId,
      timestamp: Date.now()
    })

    if (this.session) {
      this.session.funnelStage = FunnelStage.QUESTIONNAIRE_START
      this.session.lastActivity = Date.now()
    }
  }

  // Track question completion
  public trackQuestionCompleted(questionNumber: number, questionText: string, response: string, timeSpent: number): void {
    if (!this.shouldTrack()) return

    this.trackEvent('question_completed', {
      question_number: questionNumber,
      question_text: questionText,
      response: this.anonymizeResponse(response),
      time_spent_seconds: timeSpent,
      session_id: this.session?.sessionId,
      user_id: this.session?.userId,
      progress_percentage: (questionNumber / 10) * 100 // Assuming 10 questions
    })

    if (this.session) {
      this.session.questionProgress = questionNumber
      this.session.lastActivity = Date.now()
      this.session.funnelStage = FunnelStage.QUESTION_COMPLETED
    }

    // Track question start time for next question
    this.questionStartTimes.set(questionNumber + 1, Date.now())
  }

  // Track questionnaire abandonment
  public trackQuestionnaireAbandoned(abandonedAtQuestion: number, reason?: string): void {
    if (!this.shouldTrack()) return

    this.trackEvent('questionnaire_abandoned', {
      abandoned_at_question: abandonedAtQuestion,
      reason: reason || 'user_navigation',
      session_id: this.session?.sessionId,
      user_id: this.session?.userId,
      time_spent_total: this.getTotalTimeSpent(),
      progress_percentage: (abandonedAtQuestion / 10) * 100
    })
  }

  // Track email submission
  public trackEmailSubmitted(email: string, segment: string, score: number): void {
    if (!this.shouldTrack()) return

    this.trackEvent('email_submitted', {
      email_hash: this.hashEmail(email),
      segment: segment,
      score: score,
      session_id: this.session?.sessionId,
      user_id: this.session?.userId,
      time_to_complete: this.getTotalTimeSpent()
    })

    if (this.session) {
      this.session.funnelStage = FunnelStage.EMAIL_SUBMITTED
      this.session.lastActivity = Date.now()
    }
  }

  // Track results viewed
  public trackResultsViewed(segment: string, score: number): void {
    if (!this.shouldTrack()) return

    this.trackEvent('results_viewed', {
      segment: segment,
      score: score,
      session_id: this.session?.sessionId,
      user_id: this.session?.userId,
      time_on_results_page: 0 // Will be updated when user leaves
    })

    if (this.session) {
      this.session.funnelStage = FunnelStage.RESULTS_VIEWED
      this.session.lastActivity = Date.now()
    }
  }

  // Track CTA click
  public trackCTAClick(ctaType: string, ctaText: string, destination: string): void {
    if (!this.shouldTrack()) return

    this.trackEvent('cta_clicked', {
      cta_type: ctaType,
      cta_text: ctaText,
      destination: destination,
      session_id: this.session?.sessionId,
      user_id: this.session?.userId,
      funnel_stage: this.session?.funnelStage
    })

    if (this.session) {
      this.session.funnelStage = FunnelStage.CTA_CLICKED
      this.session.lastActivity = Date.now()
    }
  }

  // Track conversion funnel
  public trackFunnelStage(stage: FunnelStage, additionalData?: Record<string, any>): void {
    if (!this.shouldTrack()) return

    this.trackEvent('funnel_stage', {
      stage: stage,
      session_id: this.session?.sessionId,
      user_id: this.session?.userId,
      ...additionalData
    })

    if (this.session) {
      this.session.funnelStage = stage
      this.session.lastActivity = Date.now()
    }
  }

  // A/B Testing Framework
  public getABTestVariant(testId: string): string {
    if (!this.abTests.has(testId)) {
      return 'control'
    }

    const test = this.abTests.get(testId)!
    if (!test.isActive) {
      return 'control'
    }

    // Generate consistent variant based on session ID
    const sessionId = this.session?.sessionId || 'anonymous'
    const hash = this.hashString(sessionId + testId)
    const random = hash % 100

    let cumulative = 0
    for (const [variant, percentage] of Object.entries(test.trafficSplit)) {
      cumulative += percentage
      if (random < cumulative) {
        return variant
      }
    }

    return 'control'
  }

  // Track A/B test exposure
  public trackABTestExposure(testId: string, variant: string): void {
    if (!this.shouldTrack()) return

    this.trackEvent('ab_test_exposure', {
      test_id: testId,
      variant: variant,
      session_id: this.session?.sessionId,
      user_id: this.session?.userId
    })
  }

  // Track A/B test conversion
  public trackABTestConversion(testId: string, variant: string, conversionType: string): void {
    if (!this.shouldTrack()) return

    this.trackEvent('ab_test_conversion', {
      test_id: testId,
      variant: variant,
      conversion_type: conversionType,
      session_id: this.session?.sessionId,
      user_id: this.session?.userId
    })
  }

  // User behavior tracking
  public trackUserBehavior(action: string, data?: Record<string, any>): void {
    if (!this.shouldTrack()) return

    this.trackEvent('user_behavior', {
      action: action,
      session_id: this.session?.sessionId,
      user_id: this.session?.userId,
      timestamp: Date.now(),
      ...data
    })
  }

  // Track time spent on page
  public trackTimeOnPage(pagePath: string, timeSpent: number): void {
    if (!this.shouldTrack()) return

    this.trackEvent('time_on_page', {
      page_path: pagePath,
      time_spent_seconds: timeSpent,
      session_id: this.session?.sessionId,
      user_id: this.session?.userId
    })
  }

  // Track device and browser information
  public trackDeviceInfo(): void {
    if (!this.shouldTrack()) return

    const deviceInfo = this.getDeviceInfo()
    this.trackEvent('device_info', {
      device_type: deviceInfo.deviceType,
      browser: deviceInfo.browser,
      os: deviceInfo.os,
      screen_resolution: deviceInfo.screenResolution,
      viewport_size: deviceInfo.viewportSize,
      language: deviceInfo.language,
      session_id: this.session?.sessionId,
      user_id: this.session?.userId
    })
  }

  // Track traffic source performance
  public trackTrafficSource(): void {
    if (!this.shouldTrack()) return

    const trafficSource = this.getTrafficSource()
    this.trackEvent('traffic_source', {
      utm_source: trafficSource.utmSource,
      utm_medium: trafficSource.utmMedium,
      utm_campaign: trafficSource.utmCampaign,
      utm_term: trafficSource.utmTerm,
      utm_content: trafficSource.utmContent,
      referrer: trafficSource.referrer,
      landing_page: trafficSource.landingPage,
      session_id: this.session?.sessionId,
      user_id: this.session?.userId
    })
  }

  // GDPR Compliance
  public setConsent(consentGranted: boolean): void {
    this.consentGranted = consentGranted
    
    if (consentGranted) {
      this.trackEvent('consent_granted', {
        timestamp: Date.now(),
        session_id: this.session?.sessionId
      })
    } else {
      this.trackEvent('consent_denied', {
        timestamp: Date.now(),
        session_id: this.session?.sessionId
      })
    }
  }

  public deleteUserData(userId: string): Promise<void> {
    // Implement data deletion for GDPR compliance
    return Promise.resolve()
  }

  public exportUserData(userId: string): Promise<any> {
    // Implement data export for GDPR compliance
    return Promise.resolve({})
  }

  // Utility methods
  private shouldTrack(): boolean {
    return this.config.enableTracking && 
           this.consentGranted && 
           this.session !== null &&
           (!this.config.respectDNT || navigator.doNotTrack !== '1')
  }

  private trackEvent(eventName: string, parameters: Record<string, any>): void {
    if (!this.shouldTrack()) return

    // Send to Google Analytics 4
    if (window.gtag) {
      window.gtag('event', eventName, parameters)
    }

    // Log for debugging
    if (this.config.debugMode) {
      this.log(`Analytics Event: ${eventName}`, parameters)
    }

    // Store event for batch processing
    this.storeEvent({
      eventName,
      parameters,
      timestamp: Date.now(),
      sessionId: this.session?.sessionId,
      userId: this.session?.userId
    })
  }

  private storeEvent(event: AnalyticsEvent): void {
    // Store event in localStorage for batch processing
    const events = JSON.parse(localStorage.getItem('analytics_events') || '[]')
    events.push(event)
    localStorage.setItem('analytics_events', JSON.stringify(events.slice(-100))) // Keep last 100 events
  }

  private generateSessionId(): string {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  }

  private getDeviceInfo(): DeviceInfo {
    const userAgent = navigator.userAgent
    const screen = window.screen
    const viewport = {
      width: window.innerWidth,
      height: window.innerHeight
    }

    return {
      userAgent,
      screenResolution: `${screen.width}x${screen.height}`,
      viewportSize: `${viewport.width}x${viewport.height}`,
      deviceType: this.getDeviceType(viewport.width),
      browser: this.getBrowser(userAgent),
      os: this.getOS(userAgent),
      language: navigator.language
    }
  }

  private getDeviceType(width: number): 'desktop' | 'tablet' | 'mobile' {
    if (width >= 1024) return 'desktop'
    if (width >= 768) return 'tablet'
    return 'mobile'
  }

  private getBrowser(userAgent: string): string {
    if (userAgent.includes('Chrome')) return 'Chrome'
    if (userAgent.includes('Firefox')) return 'Firefox'
    if (userAgent.includes('Safari')) return 'Safari'
    if (userAgent.includes('Edge')) return 'Edge'
    return 'Other'
  }

  private getOS(userAgent: string): string {
    if (userAgent.includes('Windows')) return 'Windows'
    if (userAgent.includes('Mac')) return 'macOS'
    if (userAgent.includes('Linux')) return 'Linux'
    if (userAgent.includes('Android')) return 'Android'
    if (userAgent.includes('iOS')) return 'iOS'
    return 'Other'
  }

  private getTrafficSource(): TrafficSource {
    const urlParams = new URLSearchParams(window.location.search)
    
    return {
      utmSource: urlParams.get('utm_source') || undefined,
      utmMedium: urlParams.get('utm_medium') || undefined,
      utmCampaign: urlParams.get('utm_campaign') || undefined,
      utmTerm: urlParams.get('utm_term') || undefined,
      utmContent: urlParams.get('utm_content') || undefined,
      referrer: document.referrer || undefined,
      landingPage: window.location.pathname
    }
  }

  private anonymizeResponse(response: string): string {
    // Anonymize sensitive responses while keeping structure
    return response.length > 10 ? response.substring(0, 10) + '...' : response
  }

  private hashEmail(email: string): string {
    // Simple hash for email privacy
    let hash = 0
    for (let i = 0; i < email.length; i++) {
      const char = email.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36)
  }

  private hashString(str: string): number {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    return Math.abs(hash)
  }

  private getTotalTimeSpent(): number {
    if (!this.session) return 0
    return (Date.now() - this.session.startTime) / 1000
  }

  private loadABTests(): void {
    // Load A/B test configurations
    const tests: ABTestConfig[] = [
      {
        id: 'headline_test',
        name: 'Landing Page Headlines',
        variants: ['control', 'variant_a', 'variant_b'],
        trafficSplit: { control: 33, variant_a: 33, variant_b: 34 },
        isActive: true,
        startDate: new Date()
      },
      {
        id: 'question_order_test',
        name: 'Question Order Variations',
        variants: ['control', 'reversed', 'random'],
        trafficSplit: { control: 50, reversed: 25, random: 25 },
        isActive: true,
        startDate: new Date()
      },
      {
        id: 'cta_button_test',
        name: 'CTA Button Variations',
        variants: ['control', 'urgent', 'benefit'],
        trafficSplit: { control: 33, urgent: 33, benefit: 34 },
        isActive: true,
        startDate: new Date()
      }
    ]

    tests.forEach(test => this.abTests.set(test.id, test))
  }

  private log(message: string, data?: any): void {
    if (this.config.debugMode) {
      console.log(`[Analytics] ${message}`, data)
    }
  }
}

// Global analytics instance
export const analytics = new AnalyticsService()

// Type declarations for global objects
declare global {
  interface Window {
    gtag: (...args: any[]) => void
    dataLayer: any[]
  }
} 