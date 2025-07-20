// Google Analytics + Microsoft Clarity Integration
// This file provides comprehensive analytics tracking for both landing pages

class AnalyticsIntegration {
  constructor() {
    this.claritySessionId = null;
    this.userSegment = null;
    this.pageType = this.getPageType();
    this.startTime = Date.now();
    this.maxScroll = 0;
    this.ga4Id = this.getGA4Id();
    this.init();
  }

  init() {
    // Wait for both GA4 and Clarity to load
    this.waitForAnalytics();
    
    // Track page load
    this.trackPageView();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Track scroll depth
    this.trackScrollDepth();
    
    // Track time on page
    this.trackTimeOnPage();
  }

  getGA4Id() {
    const url = window.location.href.toLowerCase();
    if (url.includes('ratchet') || url.includes('ratchetmoney')) {
      return 'G-JR0VSXY6KB'; // Ratchet Money GA4 ID
    } else if (url.includes('mingus')) {
      return 'G-LR5TV15ZTM'; // MINGUS GA4 ID
    }
    return 'G-JR0VSXY6KB'; // Default to Ratchet Money
  }

  waitForAnalytics() {
    const checkAnalytics = () => {
      if (typeof gtag !== 'undefined' && typeof clarity !== 'undefined') {
        // Get Clarity session ID
        clarity('get', 'sessionId', (sessionId) => {
          this.claritySessionId = sessionId;
          this.sendToGA('clarity_session_started', {
            clarity_session_id: sessionId,
            page_type: this.pageType
          });
        });
      } else {
        setTimeout(checkAnalytics, 100);
      }
    };
    checkAnalytics();
  }

  trackPageView() {
    // Send page view to GA4
    if (typeof gtag !== 'undefined') {
      gtag('event', 'page_view', {
        page_title: document.title,
        page_location: window.location.href,
        page_type: this.pageType,
        clarity_session_id: this.claritySessionId,
        user_segment: this.userSegment
      });
    }

    // Track in Clarity
    if (typeof clarity !== 'undefined') {
      clarity('set', 'page_type', this.pageType);
      clarity('set', 'user_segment', this.userSegment);
      clarity('event', 'page_view', {
        page_title: document.title,
        page_type: this.pageType
      });
    }

    console.log('Page View Tracked:', {
      page: document.title,
      type: this.pageType,
      session: this.claritySessionId,
      ga4_id: this.ga4Id
    });
  }

  setupEventListeners() {
    // Track CTA clicks
    document.addEventListener('click', (e) => {
      if (e.target.matches('.cta, button[class*="cta"], .cta-button, .hero-cta')) {
        this.trackEvent('cta_clicked', {
          cta_text: e.target.textContent.trim(),
          cta_location: this.getElementLocation(e.target),
          cta_section: this.getSectionName(e.target),
          clarity_session_id: this.claritySessionId
        });
      }
    });

    // Track form interactions
    document.addEventListener('submit', (e) => {
      if (e.target.matches('form')) {
        this.trackEvent('form_submitted', {
          form_id: e.target.id || 'unknown',
          form_action: e.target.action,
          form_method: e.target.method,
          clarity_session_id: this.claritySessionId
        });
      }
    });

    // Track email signups
    document.addEventListener('input', (e) => {
      if (e.target.type === 'email' && e.target.value.includes('@')) {
        this.trackEvent('email_entered', {
          email_field: e.target.id || 'unknown',
          form_section: this.getSectionName(e.target),
          clarity_session_id: this.claritySessionId
        });
      }
    });

    // Track assessment starts
    document.addEventListener('click', (e) => {
      if (e.target.textContent.toLowerCase().includes('assessment') || 
          e.target.textContent.toLowerCase().includes('quiz') ||
          e.target.textContent.toLowerCase().includes('test')) {
        this.trackEvent('assessment_started', {
          trigger_element: e.target.textContent.trim(),
          trigger_location: this.getElementLocation(e.target),
          clarity_session_id: this.claritySessionId
        });
      }
    });
  }

  trackScrollDepth() {
    const trackScroll = () => {
      const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
      
      if (scrollPercent > this.maxScroll) {
        this.maxScroll = scrollPercent;
        
        // Track at 25%, 50%, 75%, 100%
        if ([25, 50, 75, 100].includes(this.maxScroll)) {
          this.trackEvent('scroll_depth', {
            scroll_percentage: this.maxScroll,
            page_type: this.pageType,
            clarity_session_id: this.claritySessionId
          });
        }
      }
    };

    window.addEventListener('scroll', trackScroll);
  }

  trackTimeOnPage() {
    // Track time on page every 30 seconds
    setInterval(() => {
      const timeOnPage = Math.round((Date.now() - this.startTime) / 1000);
      if (timeOnPage % 30 === 0) {
        this.trackEvent('time_on_page', {
          seconds_on_page: timeOnPage,
          page_type: this.pageType,
          clarity_session_id: this.claritySessionId
        });
      }
    }, 1000);

    // Track final time on page
    window.addEventListener('beforeunload', () => {
      const timeOnPage = Math.round((Date.now() - this.startTime) / 1000);
      this.trackEvent('page_exit', {
        seconds_on_page: timeOnPage,
        scroll_percentage: this.maxScroll,
        page_type: this.pageType,
        clarity_session_id: this.claritySessionId
      });
    });
  }

  trackEvent(eventName, parameters = {}) {
    // Send to GA4
    if (typeof gtag !== 'undefined') {
      gtag('event', eventName, {
        ...parameters,
        page_type: this.pageType,
        clarity_session_id: this.claritySessionId,
        user_segment: this.userSegment
      });
    }

    // Send to Clarity
    if (typeof clarity !== 'undefined') {
      clarity('event', eventName, {
        ...parameters,
        page_type: this.pageType
      });
    }

    // Log for debugging
    console.log('Analytics Event:', eventName, parameters);
  }

  getElementLocation(element) {
    const rect = element.getBoundingClientRect();
    return {
      x: Math.round(rect.left),
      y: Math.round(rect.top),
      section: this.getSectionName(element)
    };
  }

  getSectionName(element) {
    const section = element.closest('section');
    if (section) {
      return section.className || section.id || 'unknown';
    }
    
    // Check for common section identifiers
    const parent = element.closest('[class*="section"], [class*="hero"], [class*="cta"]');
    return parent ? parent.className : 'unknown';
  }

  getPageType() {
    const url = window.location.href.toLowerCase();
    if (url.includes('mingus')) {
      return 'mingus_landing';
    } else if (url.includes('ratchet')) {
      return 'ratchet_money_landing';
    }
    return 'unknown_landing';
  }

  setUserSegment(segment) {
    this.userSegment = segment;
    
    // Update GA4
    if (typeof gtag !== 'undefined') {
      gtag('config', this.ga4Id, {
        user_segment: segment
      });
    }

    // Update Clarity
    if (typeof clarity !== 'undefined') {
      clarity('set', 'user_segment', segment);
    }

    console.log('User Segment Set:', segment);
  }

  // Custom tracking methods
  trackMicroConversion(type, value = 1) {
    this.trackEvent('micro_conversion', {
      conversion_type: type,
      value: value,
      page_type: this.pageType
    });
  }

  trackEngagement(action, element) {
    this.trackEvent('user_engagement', {
      action: action,
      element_type: element.tagName.toLowerCase(),
      element_text: element.textContent.trim().substring(0, 50),
      page_type: this.pageType
    });
  }

  trackError(error, context) {
    this.trackEvent('error', {
      error_message: error.message,
      error_context: context,
      page_type: this.pageType
    });
  }
}

// Initialize analytics integration when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.analyticsIntegration = new AnalyticsIntegration();
  
  // Make it globally available
  window.trackEvent = (eventName, parameters) => {
    if (window.analyticsIntegration) {
      window.analyticsIntegration.trackEvent(eventName, parameters);
    }
  };
  
  window.setUserSegment = (segment) => {
    if (window.analyticsIntegration) {
      window.analyticsIntegration.setUserSegment(segment);
    }
  };
  
  console.log('Analytics Integration Initialized');
});

// Track page visibility changes
document.addEventListener('visibilitychange', () => {
  if (window.analyticsIntegration) {
    const eventName = document.hidden ? 'page_hidden' : 'page_visible';
    window.analyticsIntegration.trackEvent(eventName, {
      page_type: window.analyticsIntegration.pageType
    });
  }
});

// Track performance metrics
window.addEventListener('load', () => {
  if (window.analyticsIntegration && 'performance' in window) {
    const perfData = performance.getEntriesByType('navigation')[0];
    if (perfData) {
      window.analyticsIntegration.trackEvent('page_performance', {
        load_time: Math.round(perfData.loadEventEnd - perfData.loadEventStart),
        dom_content_loaded: Math.round(perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart),
        first_paint: Math.round(perfData.responseEnd - perfData.fetchStart),
        page_type: window.analyticsIntegration.pageType
      });
    }
  }
}); 