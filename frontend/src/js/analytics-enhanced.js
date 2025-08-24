/**
 * MINGUS Enhanced Analytics Service
 * Comprehensive dual-platform analytics with GA4 + Microsoft Clarity
 * Conversion tracking, behavioral insights, and A/B testing preparation
 */

class EnhancedAnalyticsService {
    constructor() {
        this.isInitialized = false;
        this.providers = new Map();
        this.events = [];
        this.maxEvents = 1000;
        this.sessionId = this.generateSessionId();
        this.userId = null;
        this.config = {};
        this.consentGranted = false;
        this.scrollDepthTracked = false;
        this.timeOnPageTracked = false;
        
        // GA4 Configuration
        this.ga4Config = {
            measurementId: null,
            debugMode: false,
            customDimensions: {},
            enhancedEcommerce: false
        };
        
        // Microsoft Clarity Configuration
        this.clarityConfig = {
            projectId: null,
            enabled: false,
            customTags: {},
            sessionRecording: true,
            heatmaps: true
        };
        
        // Event tracking state
        this.trackedEvents = new Set();
        this.conversionGoals = new Map();
        this.abTestVariants = new Map();
        
        // Initialize
        this.init();
    }
    
    // ===== INITIALIZATION =====
    init() {
        try {
            this.loadConfiguration();
            this.checkConsent();
            this.initializeProviders();
            this.setupEventListeners();
            this.startSessionTracking();
            this.setupScrollTracking();
            this.setupTimeOnPageTracking();
            this.setupErrorTracking();
            this.setupPerformanceTracking();
            this.isInitialized = true;
            
            console.log('Enhanced Analytics service initialized');
        } catch (error) {
            console.error('Failed to initialize enhanced analytics service', error);
        }
    }
    
    loadConfiguration() {
        this.config = {
            enabled: true,
            debug: false,
            privacy: {
                gdprCompliant: true,
                ipAnonymization: true,
                dataRetention: 26, // months
                consentRequired: true
            },
            providers: {
                ga4: {
                    enabled: false,
                    measurementId: null,
                    debugMode: false,
                    enhancedEcommerce: false,
                    customDimensions: {}
                },
                clarity: {
                    enabled: false,
                    projectId: null,
                    sessionRecording: true,
                    heatmaps: true,
                    customTags: {}
                }
            },
            events: {
                pageViews: true,
                userActions: true,
                errors: true,
                performance: true,
                conversions: true,
                scrollDepth: true,
                timeOnPage: true,
                modalInteractions: true,
                formSubmissions: true
            },
            conversionGoals: {
                leadGeneration: { value: 20, type: 'lead' },
                assessmentCompletion: { value: 50, type: 'conversion' },
                subscriptionSignup: { value: 100, type: 'revenue' }
            }
        };
        
        // Override with environment-specific config
        if (window.MINGUS && window.MINGUS.app) {
            const appConfig = window.MINGUS.app.getConfig();
            this.config = { ...this.config, ...appConfig.analytics };
        }
        
        // Set provider configs
        this.ga4Config = { ...this.ga4Config, ...this.config.providers.ga4 };
        this.clarityConfig = { ...this.clarityConfig, ...this.config.providers.clarity };
    }
    
    checkConsent() {
        // Check for existing consent
        const consent = localStorage.getItem('mingus_analytics_consent');
        if (consent === 'granted') {
            this.consentGranted = true;
        } else if (consent === 'denied') {
            this.consentGranted = false;
        } else {
            // Show consent banner if required
            this.showConsentBanner();
        }
    }
    
    showConsentBanner() {
        if (!this.config.privacy.consentRequired) {
            this.consentGranted = true;
            return;
        }
        
        const banner = document.createElement('div');
        banner.id = 'analytics-consent-banner';
        banner.innerHTML = `
            <div class="consent-banner">
                <div class="consent-content">
                    <p>We use cookies and analytics to improve your experience. 
                    <a href="/privacy" target="_blank">Learn more</a></p>
                    <div class="consent-buttons">
                        <button class="btn-accept">Accept</button>
                        <button class="btn-decline">Decline</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(banner);
        
        // Add event listeners
        banner.querySelector('.btn-accept').addEventListener('click', () => {
            this.grantConsent();
        });
        
        banner.querySelector('.btn-decline').addEventListener('click', () => {
            this.denyConsent();
        });
    }
    
    grantConsent() {
        this.consentGranted = true;
        localStorage.setItem('mingus_analytics_consent', 'granted');
        this.removeConsentBanner();
        this.initializeProviders();
    }
    
    denyConsent() {
        this.consentGranted = false;
        localStorage.setItem('mingus_analytics_consent', 'denied');
        this.removeConsentBanner();
    }
    
    removeConsentBanner() {
        const banner = document.getElementById('analytics-consent-banner');
        if (banner) {
            banner.remove();
        }
    }
    
    initializeProviders() {
        if (!this.consentGranted) return;
        
        // Initialize Google Analytics 4
        if (this.ga4Config.enabled && this.ga4Config.measurementId) {
            this.initializeGA4();
        }
        
        // Initialize Microsoft Clarity
        if (this.clarityConfig.enabled && this.clarityConfig.projectId) {
            this.initializeClarity();
        }
    }
    
    initializeGA4() {
        try {
            // Load GA4 script
            const script = document.createElement('script');
            script.async = true;
            script.src = `https://www.googletagmanager.com/gtag/js?id=${this.ga4Config.measurementId}`;
            document.head.appendChild(script);
            
            // Initialize gtag
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', this.ga4Config.measurementId, {
                debug_mode: this.ga4Config.debugMode,
                anonymize_ip: this.config.privacy.ipAnonymization,
                custom_map: this.ga4Config.customDimensions,
                enhanced_ecommerce: this.ga4Config.enhancedEcommerce
            });
            
            window.gtag = gtag;
            this.providers.set('ga4', { gtag, config: this.ga4Config });
            
            console.log('GA4 initialized successfully');
        } catch (error) {
            console.error('Failed to initialize GA4:', error);
        }
    }
    
    initializeClarity() {
        try {
            // Load Microsoft Clarity script
            const script = document.createElement('script');
            script.type = 'text/javascript';
            script.innerHTML = `
                (function(c,l,a,r,i,t,y){
                    c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
                    t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
                    y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
                })(window, document, "clarity", "script", "${this.clarityConfig.projectId}");
            `;
            document.head.appendChild(script);
            
            this.providers.set('clarity', { 
                clarity: window.clarity, 
                config: this.clarityConfig 
            });
            
            console.log('Microsoft Clarity initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Clarity:', error);
        }
    }
    
    // ===== EVENT TRACKING =====
    
    track(eventName, properties = {}, providers = ['ga4', 'clarity']) {
        if (!this.consentGranted || !this.isInitialized) return;
        
        const event = {
            name: eventName,
            properties: {
                ...properties,
                session_id: this.sessionId,
                user_id: this.userId,
                timestamp: new Date().toISOString(),
                page_url: window.location.href,
                page_title: document.title
            }
        };
        
        // Track to GA4
        if (providers.includes('ga4') && this.providers.has('ga4')) {
            this.trackToGA4(event);
        }
        
        // Track to Clarity
        if (providers.includes('clarity') && this.providers.has('clarity')) {
            this.trackToClarity(event);
        }
        
        // Store event locally
        this.events.push(event);
        if (this.events.length > this.maxEvents) {
            this.events.shift();
        }
        
        if (this.config.debug) {
            console.log('Analytics Event:', event);
        }
    }
    
    trackToGA4(event) {
        try {
            const { gtag } = this.providers.get('ga4');
            
            // Map event to GA4 format
            const ga4Event = {
                event: event.name,
                ...event.properties
            };
            
            gtag('event', event.name, event.properties);
            
        } catch (error) {
            console.error('Failed to track to GA4:', error);
        }
    }
    
    trackToClarity(event) {
        try {
            const { clarity } = this.providers.get('clarity');
            
            if (clarity && clarity.set) {
                // Set custom tags for Clarity
                clarity.set(event.name, event.properties);
            }
            
        } catch (error) {
            console.error('Failed to track to Clarity:', error);
        }
    }
    
    // ===== CONVERSION TRACKING =====
    
    trackConversion(eventName, value = 20, properties = {}) {
        const conversionEvent = {
            name: eventName,
            properties: {
                ...properties,
                conversion_value: value,
                conversion_type: 'lead_generation',
                goal_id: this.getGoalId(eventName)
            }
        };
        
        // Track to both platforms
        this.track(eventName, conversionEvent.properties, ['ga4', 'clarity']);
        
        // Track as conversion in GA4
        if (this.providers.has('ga4')) {
            this.trackConversionToGA4(eventName, value, properties);
        }
        
        console.log(`Conversion tracked: ${eventName} (value: ${value})`);
    }
    
    trackConversionToGA4(eventName, value, properties) {
        try {
            const { gtag } = this.providers.get('ga4');
            
            gtag('event', 'conversion', {
                send_to: `${this.ga4Config.measurementId}/AW-${this.getConversionId(eventName)}`,
                value: value,
                currency: 'USD',
                ...properties
            });
            
        } catch (error) {
            console.error('Failed to track conversion to GA4:', error);
        }
    }
    
    trackAssessmentSelection(assessmentType, properties = {}) {
        const eventProperties = {
            ...properties,
            assessment_type: assessmentType,
            assessment_category: this.getAssessmentCategory(assessmentType),
            user_segment: this.getUserSegment()
        };
        
        this.track('assessment_selected', eventProperties, ['ga4', 'clarity']);
        
        // Track as conversion if it's a lead generation event
        if (this.isLeadGenerationEvent(assessmentType)) {
            this.trackConversion('assessment_completion', 20, eventProperties);
        }
    }
    
    // ===== MODAL INTERACTION TRACKING =====
    
    trackModalInteraction(action, modalId, properties = {}) {
        const eventProperties = {
            ...properties,
            modal_id: modalId,
            modal_action: action, // 'open', 'close', 'select'
            modal_type: this.getModalType(modalId)
        };
        
        this.track(`modal_${action}`, eventProperties, ['ga4', 'clarity']);
        
        // Track specific modal events
        if (action === 'open' && modalId.includes('assessment')) {
            this.trackAssessmentModalOpened(modalId, properties);
        }
    }
    
    trackAssessmentModalOpened(modalId, properties = {}) {
        const assessmentType = this.extractAssessmentType(modalId);
        
        this.track('assessment_modal_opened', {
            ...properties,
            assessment_type: assessmentType,
            modal_id: modalId,
            user_intent: 'assessment_exploration'
        }, ['ga4', 'clarity']);
    }
    
    // ===== CTA TRACKING =====
    
    trackCTAClick(buttonId, location, properties = {}) {
        const eventProperties = {
            ...properties,
            button_id: buttonId,
            button_location: location,
            button_text: this.getButtonText(buttonId),
            cta_type: this.getCTAType(buttonId)
        };
        
        this.track('cta_clicked', eventProperties, ['ga4', 'clarity']);
        
        // Track conversion if it's a lead generation CTA
        if (this.isLeadGenerationCTA(buttonId)) {
            this.trackConversion('cta_conversion', 20, eventProperties);
        }
    }
    
    // ===== SCROLL DEPTH TRACKING =====
    
    setupScrollTracking() {
        if (!this.config.events.scrollDepth) return;
        
        let scrollDepthTracked = new Set();
        
        window.addEventListener('scroll', () => {
            const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
            
            // Track scroll milestones
            [25, 50, 75, 100].forEach(milestone => {
                if (scrollPercent >= milestone && !scrollDepthTracked.has(milestone)) {
                    scrollDepthTracked.add(milestone);
                    this.trackScrollDepth(milestone);
                }
            });
        });
    }
    
    trackScrollDepth(percent) {
        this.track('scroll_depth', {
            scroll_percentage: percent,
            page_section: this.getPageSection(percent)
        }, ['ga4', 'clarity']);
    }
    
    // ===== TIME ON PAGE TRACKING =====
    
    setupTimeOnPageTracking() {
        if (!this.config.events.timeOnPage) return;
        
        const startTime = Date.now();
        const milestones = [30, 60, 120, 300, 600]; // seconds
        let trackedMilestones = new Set();
        
        const trackTime = () => {
            const timeOnPage = Math.floor((Date.now() - startTime) / 1000);
            
            milestones.forEach(milestone => {
                if (timeOnPage >= milestone && !trackedMilestones.has(milestone)) {
                    trackedMilestones.add(milestone);
                    this.trackTimeOnPage(milestone);
                }
            });
        };
        
        setInterval(trackTime, 1000);
        
        // Track on page unload
        window.addEventListener('beforeunload', () => {
            const totalTime = Math.floor((Date.now() - startTime) / 1000);
            this.track('page_exit', {
                time_on_page: totalTime,
                exit_method: 'page_close'
            }, ['ga4', 'clarity']);
        });
    }
    
    trackTimeOnPage(seconds) {
        this.track('time_on_page', {
            time_seconds: seconds,
            engagement_level: this.getEngagementLevel(seconds)
        }, ['ga4', 'clarity']);
    }
    
    // ===== FORM TRACKING =====
    
    trackFormSubmission(formId, properties = {}) {
        const eventProperties = {
            ...properties,
            form_id: formId,
            form_type: this.getFormType(formId),
            submission_method: 'web_form'
        };
        
        this.track('form_submitted', eventProperties, ['ga4', 'clarity']);
        
        // Track as conversion if it's a lead form
        if (this.isLeadForm(formId)) {
            this.trackConversion('form_conversion', 20, eventProperties);
        }
    }
    
    // ===== ERROR TRACKING =====
    
    setupErrorTracking() {
        if (!this.config.events.errors) return;
        
        // JavaScript errors
        window.addEventListener('error', (event) => {
            this.trackError('javascript_error', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error_stack: event.error?.stack
            });
        });
        
        // Promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.trackError('promise_rejection', {
                reason: event.reason,
                promise: event.promise
            });
        });
    }
    
    trackError(errorType, properties = {}) {
        this.track('error', {
            error_type: errorType,
            ...properties
        }, ['ga4', 'clarity']);
    }
    
    // ===== PERFORMANCE TRACKING =====
    
    setupPerformanceTracking() {
        if (!this.config.events.performance) return;
        
        // Track page load performance
        window.addEventListener('load', () => {
            setTimeout(() => {
                this.trackPageLoadPerformance();
            }, 0);
        });
        
        // Track Core Web Vitals
        this.trackCoreWebVitals();
    }
    
    trackPageLoadPerformance() {
        const navigation = performance.getEntriesByType('navigation')[0];
        const paint = performance.getEntriesByType('paint');
        
        const metrics = {
            dom_content_loaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            load_complete: navigation.loadEventEnd - navigation.loadEventStart,
            first_paint: paint.find(p => p.name === 'first-paint')?.startTime,
            first_contentful_paint: paint.find(p => p.name === 'first-contentful-paint')?.startTime
        };
        
        this.track('page_performance', metrics, ['ga4', 'clarity']);
    }
    
    trackCoreWebVitals() {
        // LCP (Largest Contentful Paint)
        new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            
            this.track('web_vital_lcp', {
                value: lastEntry.startTime,
                element: lastEntry.element?.tagName
            }, ['ga4', 'clarity']);
        }).observe({ entryTypes: ['largest-contentful-paint'] });
        
        // FID (First Input Delay)
        new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach(entry => {
                this.track('web_vital_fid', {
                    value: entry.processingStart - entry.startTime,
                    element: entry.name
                }, ['ga4', 'clarity']);
            });
        }).observe({ entryTypes: ['first-input'] });
        
        // CLS (Cumulative Layout Shift)
        new PerformanceObserver((list) => {
            let clsValue = 0;
            const entries = list.getEntries();
            
            entries.forEach(entry => {
                if (!entry.hadRecentInput) {
                    clsValue += entry.value;
                }
            });
            
            this.track('web_vital_cls', {
                value: clsValue
            }, ['ga4', 'clarity']);
        }).observe({ entryTypes: ['layout-shift'] });
    }
    
    // ===== A/B TESTING SUPPORT =====
    
    setABTestVariant(testName, variant) {
        this.abTestVariants.set(testName, variant);
        
        // Track A/B test assignment
        this.track('ab_test_assigned', {
            test_name: testName,
            variant: variant,
            assignment_method: 'random'
        }, ['ga4', 'clarity']);
        
        // Set custom dimension for GA4
        if (this.providers.has('ga4')) {
            this.setCustomDimension(`ab_test_${testName}`, variant);
        }
        
        // Set custom tag for Clarity
        if (this.providers.has('clarity')) {
            this.setClarityTag(`ab_test_${testName}`, variant);
        }
    }
    
    setCustomDimension(name, value) {
        if (this.providers.has('ga4')) {
            const { gtag } = this.providers.get('ga4');
            gtag('config', this.ga4Config.measurementId, {
                custom_map: { [name]: value }
            });
        }
    }
    
    setClarityTag(name, value) {
        if (this.providers.has('clarity')) {
            const { clarity } = this.providers.get('clarity');
            if (clarity && clarity.set) {
                clarity.set(name, value);
            }
        }
    }
    
    // ===== USER IDENTIFICATION =====
    
    setUserId(userId) {
        this.userId = userId;
        
        // Set user ID in GA4
        if (this.providers.has('ga4')) {
            const { gtag } = this.providers.get('ga4');
            gtag('config', this.ga4Config.measurementId, {
                user_id: userId
            });
        }
        
        // Set user ID in Clarity
        if (this.providers.has('clarity')) {
            const { clarity } = this.providers.get('clarity');
            if (clarity && clarity.set) {
                clarity.set('user_id', userId);
            }
        }
    }
    
    // ===== UTILITY METHODS =====
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    getGoalId(eventName) {
        const goalMap = {
            'lead_generation': 'goal_lead',
            'assessment_completion': 'goal_assessment',
            'subscription_signup': 'goal_subscription'
        };
        return goalMap[eventName] || 'goal_custom';
    }
    
    getConversionId(eventName) {
        const conversionMap = {
            'lead_generation': '123456789',
            'assessment_completion': '987654321',
            'subscription_signup': '456789123'
        };
        return conversionMap[eventName] || '000000000';
    }
    
    getAssessmentCategory(type) {
        const categories = {
            'income_comparison': 'financial_analysis',
            'tax_optimization': 'tax_planning',
            'career_advancement': 'career_development',
            'investment_planning': 'wealth_building'
        };
        return categories[type] || 'general';
    }
    
    getUserSegment() {
        // Determine user segment based on behavior or profile
        return 'general_user';
    }
    
    isLeadGenerationEvent(type) {
        const leadEvents = ['income_comparison', 'tax_optimization', 'career_advancement'];
        return leadEvents.includes(type);
    }
    
    getModalType(modalId) {
        if (modalId.includes('assessment')) return 'assessment_selection';
        if (modalId.includes('pricing')) return 'pricing';
        if (modalId.includes('contact')) return 'contact';
        return 'general';
    }
    
    extractAssessmentType(modalId) {
        const types = ['income_comparison', 'tax_optimization', 'career_advancement', 'investment_planning'];
        return types.find(type => modalId.includes(type)) || 'unknown';
    }
    
    getButtonText(buttonId) {
        const button = document.getElementById(buttonId);
        return button ? button.textContent.trim() : 'unknown';
    }
    
    getCTAType(buttonId) {
        if (buttonId.includes('start')) return 'primary_cta';
        if (buttonId.includes('learn')) return 'secondary_cta';
        if (buttonId.includes('contact')) return 'contact_cta';
        return 'general_cta';
    }
    
    isLeadGenerationCTA(buttonId) {
        const leadCTAs = ['start_assessment', 'get_started', 'begin_analysis'];
        return leadCTAs.some(cta => buttonId.includes(cta));
    }
    
    getPageSection(percent) {
        if (percent <= 25) return 'header';
        if (percent <= 50) return 'content_above_fold';
        if (percent <= 75) return 'content_below_fold';
        return 'footer';
    }
    
    getEngagementLevel(seconds) {
        if (seconds < 30) return 'low';
        if (seconds < 120) return 'medium';
        if (seconds < 300) return 'high';
        return 'very_high';
    }
    
    getFormType(formId) {
        if (formId.includes('contact')) return 'contact_form';
        if (formId.includes('signup')) return 'signup_form';
        if (formId.includes('assessment')) return 'assessment_form';
        return 'general_form';
    }
    
    isLeadForm(formId) {
        const leadForms = ['contact_form', 'signup_form', 'assessment_form'];
        return leadForms.some(form => formId.includes(form));
    }
    
    // ===== PUBLIC API =====
    
    // Conversion tracking
    trackLeadGeneration(source = 'website', properties = {}) {
        this.trackConversion('lead_generation', 20, { source, ...properties });
    }
    
    trackAssessmentCompletion(type, properties = {}) {
        this.trackConversion('assessment_completion', 50, { assessment_type: type, ...properties });
    }
    
    trackSubscriptionSignup(plan, properties = {}) {
        this.trackConversion('subscription_signup', 100, { plan, ...properties });
    }
    
    // Event tracking shortcuts
    trackPageView(page = null) {
        const properties = {
            page_title: document.title,
            page_url: window.location.href,
            referrer: document.referrer
        };
        
        if (page) {
            properties.page_name = page;
        }
        
        this.track('page_view', properties, ['ga4', 'clarity']);
    }
    
    trackUserAction(action, element = null, properties = {}) {
        const eventProperties = {
            action_type: action,
            element_id: element?.id,
            element_class: element?.className,
            element_tag: element?.tagName,
            ...properties
        };
        
        this.track('user_action', eventProperties, ['ga4', 'clarity']);
    }
    
    // Utility methods
    getEvents() {
        return this.events;
    }
    
    clearEvents() {
        this.events = [];
    }
    
    isEnabled() {
        return this.isInitialized && this.consentGranted;
    }
    
    getProviderStatus() {
        return {
            ga4: this.providers.has('ga4'),
            clarity: this.providers.has('clarity'),
            consent: this.consentGranted
        };
    }
}

// Create global instance
window.MINGUS = window.MINGUS || {};
window.MINGUS.analytics = new EnhancedAnalyticsService();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedAnalyticsService;
}
