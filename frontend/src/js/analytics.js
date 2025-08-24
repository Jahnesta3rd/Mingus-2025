/**
 * MINGUS Analytics Service
 * Comprehensive analytics with event tracking, performance monitoring, and user behavior analysis
 */

class AnalyticsService {
    constructor() {
        this.isInitialized = false;
        this.providers = new Map();
        this.events = [];
        this.maxEvents = 1000;
        this.sessionId = this.generateSessionId();
        this.userId = null;
        this.config = {};
        
        // Initialize
        this.init();
    }
    
    // ===== INITIALIZATION =====
    init() {
        try {
            this.loadConfiguration();
            this.initializeProviders();
            this.setupEventListeners();
            this.startSessionTracking();
            this.isInitialized = true;
            
            MINGUS.utils.logInfo('Analytics service initialized');
        } catch (error) {
            MINGUS.utils.logError('Failed to initialize analytics service', error);
        }
    }
    
    loadConfiguration() {
        this.config = {
            enabled: true,
            debug: false,
            providers: {
                google: {
                    enabled: false,
                    trackingId: null
                },
                mixpanel: {
                    enabled: false,
                    token: null
                },
                amplitude: {
                    enabled: false,
                    apiKey: null
                },
                custom: {
                    enabled: true,
                    endpoint: '/api/analytics'
                }
            },
            events: {
                pageViews: true,
                userActions: true,
                errors: true,
                performance: true,
                conversions: true
            }
        };
        
        // Override with environment-specific config
        if (window.MINGUS && window.MINGUS.app) {
            const appConfig = window.MINGUS.app.getConfig();
            this.config = { ...this.config, ...appConfig.analytics };
        }
    }
    
    initializeProviders() {
        // Initialize Google Analytics
        if (this.config.providers.google.enabled && this.config.providers.google.trackingId) {
            this.initializeGoogleAnalytics();
        }
        
        // Initialize Mixpanel
        if (this.config.providers.mixpanel.enabled && this.config.providers.mixpanel.token) {
            this.initializeMixpanel();
        }
        
        // Initialize Amplitude
        if (this.config.providers.amplitude.enabled && this.config.providers.amplitude.apiKey) {
            this.initializeAmplitude();
        }
        
        // Initialize custom analytics
        if (this.config.providers.custom.enabled) {
            this.initializeCustomAnalytics();
        }
    }
    
    setupEventListeners() {
        // Track page views
        if (this.config.events.pageViews) {
            this.trackPageView();
        }
        
        // Track user actions
        if (this.config.events.userActions) {
            this.setupUserActionTracking();
        }
        
        // Track errors
        if (this.config.events.errors) {
            this.setupErrorTracking();
        }
        
        // Track performance
        if (this.config.events.performance) {
            this.setupPerformanceTracking();
        }
        
        // Track conversions
        if (this.config.events.conversions) {
            this.setupConversionTracking();
        }
    }
    
    // ===== PROVIDER INITIALIZATION =====
    initializeGoogleAnalytics() {
        try {
            // Load Google Analytics script
            const script = document.createElement('script');
            script.async = true;
            script.src = `https://www.googletagmanager.com/gtag/js?id=${this.config.providers.google.trackingId}`;
            document.head.appendChild(script);
            
            // Initialize gtag
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', this.config.providers.google.trackingId, {
                page_title: document.title,
                page_location: window.location.href
            });
            
            this.providers.set('google', { gtag });
            MINGUS.utils.logInfo('Google Analytics initialized');
        } catch (error) {
            MINGUS.utils.logError('Failed to initialize Google Analytics', error);
        }
    }
    
    initializeMixpanel() {
        try {
            // Load Mixpanel script
            const script = document.createElement('script');
            script.src = 'https://cdn.mxpnl.com/libs/mixpanel-2.2.0.min.js';
            document.head.appendChild(script);
            
            script.onload = () => {
                window.mixpanel.init(this.config.providers.mixpanel.token);
                this.providers.set('mixpanel', window.mixpanel);
                MINGUS.utils.logInfo('Mixpanel initialized');
            };
        } catch (error) {
            MINGUS.utils.logError('Failed to initialize Mixpanel', error);
        }
    }
    
    initializeAmplitude() {
        try {
            // Load Amplitude script
            const script = document.createElement('script');
            script.src = 'https://cdn.amplitude.com/libs/amplitude-8.0.0-min.gz.js';
            document.head.appendChild(script);
            
            script.onload = () => {
                window.amplitude.getInstance().init(this.config.providers.amplitude.apiKey);
                this.providers.set('amplitude', window.amplitude);
                MINGUS.utils.logInfo('Amplitude initialized');
            };
        } catch (error) {
            MINGUS.utils.logError('Failed to initialize Amplitude', error);
        }
    }
    
    initializeCustomAnalytics() {
        this.providers.set('custom', {
            track: (event, properties) => this.sendToCustomEndpoint(event, properties)
        });
        MINGUS.utils.logInfo('Custom analytics initialized');
    }
    
    // ===== EVENT TRACKING =====
    track(event, properties = {}) {
        if (!this.isInitialized || !this.config.enabled) {
            return;
        }
        
        try {
            const eventData = {
                event,
                properties: {
                    ...properties,
                    timestamp: Date.now(),
                    sessionId: this.sessionId,
                    userId: this.userId,
                    url: window.location.href,
                    userAgent: navigator.userAgent,
                    screen: {
                        width: screen.width,
                        height: screen.height
                    },
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    }
                }
            };
            
            // Add to local events array
            this.events.push(eventData);
            if (this.events.length > this.maxEvents) {
                this.events.shift();
            }
            
            // Send to all providers
            this.providers.forEach((provider, name) => {
                try {
                    if (provider.track) {
                        provider.track(event, eventData.properties);
                    }
                } catch (error) {
                    MINGUS.utils.logError(`Failed to track event with ${name}`, error);
                }
            });
            
            if (this.config.debug) {
                MINGUS.utils.logDebug('Analytics event tracked', eventData);
            }
            
        } catch (error) {
            MINGUS.utils.logError('Failed to track event', error);
        }
    }
    
    trackPageView(page = null) {
        const pageData = page || {
            title: document.title,
            url: window.location.href,
            path: window.location.pathname,
            referrer: document.referrer
        };
        
        this.track('page_view', pageData);
    }
    
    trackUserAction(action, element = null, properties = {}) {
        const actionData = {
            action,
            element: element ? {
                tagName: element.tagName,
                id: element.id,
                className: element.className,
                text: element.textContent?.substring(0, 100)
            } : null,
            ...properties
        };
        
        this.track('user_action', actionData);
    }
    
    trackError(error, context = {}) {
        const errorData = {
            message: error.message,
            stack: error.stack,
            name: error.name,
            ...context
        };
        
        this.track('error', errorData);
    }
    
    trackPerformance(metric, value, properties = {}) {
        const performanceData = {
            metric,
            value,
            ...properties
        };
        
        this.track('performance', performanceData);
    }
    
    trackConversion(conversion, value = null, properties = {}) {
        const conversionData = {
            conversion,
            value,
            ...properties
        };
        
        this.track('conversion', conversionData);
    }
    
    // ===== USER ACTION TRACKING =====
    setupUserActionTracking() {
        // Track clicks
        document.addEventListener('click', (event) => {
            const element = event.target.closest('button, a, [data-track]');
            if (element) {
                const trackData = element.dataset.track;
                const action = trackData || 'click';
                this.trackUserAction(action, element);
            }
        });
        
        // Track form submissions
        document.addEventListener('submit', (event) => {
            const form = event.target;
            const formId = form.id || form.className;
            this.trackUserAction('form_submit', form, { formId });
        });
        
        // Track input focus
        document.addEventListener('focus', (event) => {
            const element = event.target;
            if (element.matches('input, textarea, select')) {
                this.trackUserAction('input_focus', element, { fieldType: element.type });
            }
        }, true);
        
        // Track scroll depth
        this.trackScrollDepth();
    }
    
    trackScrollDepth() {
        let maxScrollDepth = 0;
        const trackScroll = MINGUS.utils.Performance.throttle(() => {
            const scrollTop = window.pageYOffset;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercent = Math.round((scrollTop / docHeight) * 100);
            
            if (scrollPercent > maxScrollDepth) {
                maxScrollDepth = scrollPercent;
                
                // Track at 25%, 50%, 75%, 100%
                if ([25, 50, 75, 100].includes(maxScrollDepth)) {
                    this.track('scroll_depth', { depth: maxScrollDepth });
                }
            }
        }, 100);
        
        window.addEventListener('scroll', trackScroll);
    }
    
    // ===== ERROR TRACKING =====
    setupErrorTracking() {
        // Track JavaScript errors
        window.addEventListener('error', (event) => {
            this.trackError(event.error, {
                type: 'javascript_error',
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });
        
        // Track unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.trackError(event.reason, {
                type: 'unhandled_rejection'
            });
        });
        
        // Track resource loading errors
        window.addEventListener('error', (event) => {
            if (event.target !== window) {
                this.trackError(new Error('Resource loading failed'), {
                    type: 'resource_error',
                    resource: event.target.src || event.target.href,
                    tagName: event.target.tagName
                });
            }
        }, true);
    }
    
    // ===== PERFORMANCE TRACKING =====
    setupPerformanceTracking() {
        // Track page load performance
        window.addEventListener('load', () => {
            setTimeout(() => {
                this.trackPageLoadPerformance();
            }, 0);
        });
        
        // Track Core Web Vitals
        this.trackCoreWebVitals();
        
        // Track resource timing
        this.trackResourceTiming();
    }
    
    trackPageLoadPerformance() {
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            this.trackPerformance('page_load', {
                dns: navigation.domainLookupEnd - navigation.domainLookupStart,
                tcp: navigation.connectEnd - navigation.connectStart,
                ttfb: navigation.responseStart - navigation.requestStart,
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                load: navigation.loadEventEnd - navigation.loadEventStart,
                total: navigation.loadEventEnd - navigation.fetchStart
            });
        }
    }
    
    trackCoreWebVitals() {
        if ('PerformanceObserver' in window) {
            // Largest Contentful Paint (LCP)
            const lcpObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                if (lastEntry) {
                    this.trackPerformance('LCP', lastEntry.startTime);
                }
            });
            lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
            
            // First Input Delay (FID)
            const fidObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    this.trackPerformance('FID', entry.processingStart - entry.startTime);
                });
            });
            fidObserver.observe({ entryTypes: ['first-input'] });
            
            // Cumulative Layout Shift (CLS)
            const clsObserver = new PerformanceObserver((list) => {
                let clsValue = 0;
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                });
                this.trackPerformance('CLS', clsValue);
            });
            clsObserver.observe({ entryTypes: ['layout-shift'] });
        }
    }
    
    trackResourceTiming() {
        if ('PerformanceObserver' in window) {
            const resourceObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.initiatorType === 'fetch' || entry.initiatorType === 'xmlhttprequest') {
                        this.trackPerformance('api_call', {
                            name: entry.name,
                            duration: entry.duration,
                            size: entry.transferSize
                        });
                    }
                });
            });
            resourceObserver.observe({ entryTypes: ['resource'] });
        }
    }
    
    // ===== CONVERSION TRACKING =====
    setupConversionTracking() {
        // Track successful logins
        if (window.MINGUS && window.MINGUS.auth) {
            window.MINGUS.auth.on('login', (user) => {
                this.trackConversion('login', null, { userId: user.id });
            });
        }
        
        // Track form completions
        document.addEventListener('submit', (event) => {
            const form = event.target;
            const formType = form.dataset.formType || 'general';
            this.trackConversion('form_completion', null, { formType });
        });
        
        // Track button clicks that might be conversions
        document.addEventListener('click', (event) => {
            const element = event.target.closest('[data-conversion]');
            if (element) {
                const conversion = element.dataset.conversion;
                const value = element.dataset.value;
                this.trackConversion(conversion, value);
            }
        });
    }
    
    // ===== SESSION TRACKING =====
    startSessionTracking() {
        // Track session start
        this.track('session_start', {
            referrer: document.referrer,
            utm_source: this.getUrlParameter('utm_source'),
            utm_medium: this.getUrlParameter('utm_medium'),
            utm_campaign: this.getUrlParameter('utm_campaign')
        });
        
        // Track session end
        window.addEventListener('beforeunload', () => {
            this.track('session_end', {
                sessionDuration: Date.now() - this.sessionStartTime
            });
            
            // Send events synchronously before page unload
            this.flushEvents();
        });
        
        // Track visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') {
                this.track('page_hide');
            } else if (document.visibilityState === 'visible') {
                this.track('page_show');
            }
        });
    }
    
    // ===== CUSTOM ENDPOINT =====
    async sendToCustomEndpoint(event, properties) {
        try {
            const response = await fetch(this.config.providers.custom.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    event,
                    properties,
                    timestamp: Date.now()
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            MINGUS.utils.logError('Failed to send analytics to custom endpoint', error);
        }
    }
    
    // ===== UTILITY METHODS =====
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    setUserId(userId) {
        this.userId = userId;
        
        // Update user ID in all providers
        this.providers.forEach((provider, name) => {
            try {
                if (provider.identify) {
                    provider.identify(userId);
                }
            } catch (error) {
                MINGUS.utils.logError(`Failed to set user ID in ${name}`, error);
            }
        });
    }
    
    getUrlParameter(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }
    
    flushEvents() {
        // Send all pending events
        this.events.forEach(eventData => {
            this.sendToCustomEndpoint(eventData.event, eventData.properties);
        });
        
        this.events = [];
    }
    
    // ===== PUBLIC API =====
    identify(userId, traits = {}) {
        this.setUserId(userId);
        
        // Set user traits in providers
        this.providers.forEach((provider, name) => {
            try {
                if (provider.identify) {
                    provider.identify(userId, traits);
                }
            } catch (error) {
                MINGUS.utils.logError(`Failed to identify user in ${name}`, error);
            }
        });
    }
    
    alias(userId, previousId) {
        this.providers.forEach((provider, name) => {
            try {
                if (provider.alias) {
                    provider.alias(userId, previousId);
                }
            } catch (error) {
                MINGUS.utils.logError(`Failed to alias user in ${name}`, error);
            }
        });
    }
    
    setUserProperties(properties) {
        this.providers.forEach((provider, name) => {
            try {
                if (provider.setUserProperties) {
                    provider.setUserProperties(properties);
                }
            } catch (error) {
                MINGUS.utils.logError(`Failed to set user properties in ${name}`, error);
            }
        });
    }
    
    getEvents() {
        return [...this.events];
    }
    
    clearEvents() {
        this.events = [];
    }
}

// ===== EXPORT ANALYTICS SERVICE =====
const analytics = new AnalyticsService();

// Make available globally
window.MINGUS = window.MINGUS || {};
window.MINGUS.analytics = analytics;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsService;
}
