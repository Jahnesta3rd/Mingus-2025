// Google Analytics + Microsoft Clarity Configuration
// Configuration for both landing pages with actual IDs

const CLARITY_CONFIG = {
  // Ratchet Money Landing Page
  RATCHET_MONEY: {
    GA4_MEASUREMENT_ID: "G-JR0VSXY6KB",
    CLARITY_PROJECT_ID: "seg861um4a",
    STREAM_URL: "https://www.ratchetmoney.com",
    STREAM_ID: "11508604974"
  },
  
  // MINGUS Landing Page
  MINGUS: {
    GA4_MEASUREMENT_ID: "G-LR5TV15ZTM",
    CLARITY_PROJECT_ID: "shdin8hbm3",
    STREAM_URL: "https://www.mingusapp.com",
    STREAM_ID: "11508636183"
  },
  
  // Configuration options
  ENABLE_SESSION_RECORDING: true,
  ENABLE_HEATMAPS: true,
  ENABLE_ANALYTICS: true,
  
  // Custom events to track
  CUSTOM_EVENTS: {
    ASSESSMENT_STARTED: "assessment_started",
    ASSESSMENT_COMPLETED: "assessment_completed", 
    EMAIL_SIGNUP: "email_signup",
    CTA_CLICKED: "cta_clicked",
    PDF_DOWNLOADED: "pdf_downloaded",
    SCROLL_DEPTH: "scroll_depth",
    TIME_ON_PAGE: "time_on_page",
    PAGE_EXIT: "page_exit",
    MICRO_CONVERSION: "micro_conversion"
  }
};

// Helper function to get Clarity script with Project ID
function getClarityScript(projectId) {
  return `
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "${projectId}");
  `;
}

// Helper function to get GA4 script with Measurement ID
function getGA4Script(measurementId, pageTitle) {
  return `
    <script async src="https://www.googletagmanager.com/gtag/js?id=${measurementId}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', '${measurementId}', {
        page_title: '${pageTitle}',
        page_location: window.location.href,
        custom_map: {
          'custom_parameter_1': 'clarity_session_id',
          'custom_parameter_2': 'user_segment'
        }
      });
    </script>
  `;
}

// Helper function to track custom events
function trackClarityEvent(eventName, properties = {}) {
  if (typeof clarity !== 'undefined') {
    clarity("event", eventName, properties);
  }
}

// Helper function to track GA4 events
function trackGA4Event(eventName, properties = {}) {
  if (typeof gtag !== 'undefined') {
    gtag("event", eventName, properties);
  }
}

// Helper function to track to both platforms
function trackEvent(eventName, properties = {}) {
  trackGA4Event(eventName, properties);
  trackClarityEvent(eventName, properties);
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { 
    CLARITY_CONFIG, 
    getClarityScript, 
    getGA4Script,
    trackClarityEvent,
    trackGA4Event,
    trackEvent
  };
} 