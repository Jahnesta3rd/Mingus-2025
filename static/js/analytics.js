/**
 * MINGUS Comprehensive Analytics & Conversion Tracking System
 * Dual Platform Integration: Google Analytics 4 + Microsoft Clarity
 * 
 * Features:
 * - GA4: Event tracking, ecommerce preparation, user engagement
 * - Clarity: Session recordings, heatmaps, behavior insights
 * - Cross-platform event correlation
 * - Privacy compliance (GDPR-ready)
 * - Performance monitoring
 * - A/B testing preparation
 * - Lead quality scoring
 * - Unified reporting preparation
 */

class MingusAnalytics {
    constructor() {
        // Configuration
        this.config = {
            ga4: {
                measurementId: 'G-XXXXXXXXXX', // Replace with actual GA4 ID
                debugMode: false,
                anonymizeIp: true,
                enableEcommerce: true
            },
            clarity: {
                projectId: 'XXXXXXXXXX', // Replace with actual Clarity Project ID
                enableSessionRecording: true,
                enableHeatmaps: true,
                enableClickTracking: true,
                enableScrollTracking: true
            },
            privacy: {
                gdprCompliant: true,
                requireConsent: true,
                dataRetentionDays: 26,
                anonymizeUserData: true
            },
            events: {
                // GA4 Event Names
                assessmentModalOpen: 'mingus_assessment_modal_open',
                assessmentSelected: 'mingus_assessment_selected',
                ctaClick: 'mingus_cta_click',
                formSubmission: 'mingus_form_submission',
                scrollDepth: 'mingus_scroll_depth',
                timeOnPage: 'mingus_time_on_page',
                conversion: 'mingus_conversion',
                error: 'mingus_error',
                performance: 'mingus_performance',
                
                // Clarity Custom Tags
                clarityAssessmentModal: 'assessment_modal_interaction',
                clarityAssessmentSelection: 'assessment_selection',
                clarityCTAClick: 'cta_click',
                clarityConversion: 'conversion_event',
                clarityUserSegment: 'user_segment',
                clarityTestVariant: 'ab_test_variant'
            },
            scrollMilestones: [25, 50, 75, 100],
            timeMilestones: [30, 60, 120, 300, 600], // seconds
            sessionTimeout: 1800000 // 30 minutes
        };

        // State management
        this.state = {
            userConsent: false,
            sessionStartTime: Date.now(),
            lastActivity: Date.now(),
            scrollDepthReached: new Set(),
            timeMilestonesReached: new Set(),
            userJourney: [],
            currentTestVariant: null,
            leadQualityScore: 0,
            isInitialized: false
        };

        // Initialize analytics
        this.init();
    }

    /**
     * Initialize analytics platforms
     */
    init() {
        try {
            // Check for user consent
            if (this.config.privacy.requireConsent) {
                this.checkUserConsent();
            } else {
                this.initializePlatforms();
            }

            // Setup session monitoring
            this.setupSessionMonitoring();
            
            // Setup scroll tracking
            this.setupScrollTracking();
            
            // Setup time tracking
            this.setupTimeTracking();
            
            // Setup error tracking
            this.setupErrorTracking();
            
            // Setup performance monitoring
            this.setupPerformanceMonitoring();

            this.state.isInitialized = true;
            console.log('MingusAnalytics: Initialized successfully');

        } catch (error) {
            console.error('MingusAnalytics: Initialization failed', error);
        }
    }

    /**
     * Check user consent for analytics
     */
    checkUserConsent() {
        const consent = localStorage.getItem('mingus_analytics_consent');
        
        if (consent === 'granted') {
            this.state.userConsent = true;
            this.initializePlatforms();
        } else if (consent === 'denied') {
            this.state.userConsent = false;
            this.setupOptOut();
        } else {
            this.showConsentBanner();
        }
    }

    /**
     * Show consent banner
     */
    showConsentBanner() {
        const banner = document.createElement('div');
        banner.id = 'analytics-consent-banner';
        banner.innerHTML = `
            <div style="position: fixed; bottom: 0; left: 0; right: 0; background: #1a1a2e; color: white; padding: 20px; z-index: 10000; border-top: 2px solid #667eea;">
                <div style="max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0 0 10px 0; color: #667eea;">We use cookies and analytics to improve your experience</h4>
                        <p style="margin: 0; font-size: 14px; opacity: 0.8;">
                            This helps us understand how you use our site and improve our services. 
                            Your data is anonymized and protected.
                        </p>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button id="accept-analytics" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                            Accept
                        </button>
                        <button id="decline-analytics" style="background: transparent; color: white; border: 1px solid #667eea; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                            Decline
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(banner);

        // Event listeners
        document.getElementById('accept-analytics').addEventListener('click', () => {
            this.grantConsent();
        });

        document.getElementById('decline-analytics').addEventListener('click', () => {
            this.denyConsent();
        });
    }

    /**
     * Grant analytics consent
     */
    grantConsent() {
        this.state.userConsent = true;
        localStorage.setItem('mingus_analytics_consent', 'granted');
        this.initializePlatforms();
        this.hideConsentBanner();
        
        // Track consent event
        this.trackEvent('mingus_consent_granted', {
            consent_type: 'analytics',
            timestamp: Date.now()
        });
    }

    /**
     * Deny analytics consent
     */
    denyConsent() {
        this.state.userConsent = false;
        localStorage.setItem('mingus_analytics_consent', 'denied');
        this.setupOptOut();
        this.hideConsentBanner();
        
        // Track consent event (without personal data)
        this.trackEvent('mingus_consent_denied', {
            consent_type: 'analytics',
            timestamp: Date.now()
        });
    }

    /**
     * Hide consent banner
     */
    hideConsentBanner() {
        const banner = document.getElementById('analytics-consent-banner');
        if (banner) {
            banner.remove();
        }
    }

    /**
     * Setup opt-out functionality
     */
    setupOptOut() {
        // GA4 opt-out
        if (window.gtag) {
            window.gtag('config', this.config.ga4.measurementId, {
                'anonymize_ip': true,
                'allow_google_signals': false,
                'allow_ad_personalization_signals': false
            });
        }

        // Clarity opt-out
        if (window.clarity) {
            window.clarity('stop');
        }
    }

    /**
     * Initialize analytics platforms
     */
    initializePlatforms() {
        this.initializeGA4();
        this.initializeClarity();
        this.setupCrossPlatformTracking();
    }

    /**
     * Initialize Google Analytics 4
     */
    initializeGA4() {
        // Load GA4 script
        const script = document.createElement('script');
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${this.config.ga4.measurementId}`;
        document.head.appendChild(script);

        script.onload = () => {
            window.dataLayer = window.dataLayer || [];
            
            window.gtag = function() {
                window.dataLayer.push(arguments);
            };

            window.gtag('js', new Date());
            window.gtag('config', this.config.ga4.measurementId, {
                'anonymize_ip': this.config.ga4.anonymizeIp,
                'allow_google_signals': this.state.userConsent,
                'allow_ad_personalization_signals': this.state.userConsent,
                'debug_mode': this.config.ga4.debugMode,
                'custom_map': {
                    'custom_parameter_1': 'user_segment',
                    'custom_parameter_2': 'lead_quality_score',
                    'custom_parameter_3': 'test_variant',
                    'custom_parameter_4': 'assessment_type',
                    'custom_parameter_5': 'conversion_value'
                }
            });

            // Enhanced ecommerce setup
            if (this.config.ga4.enableEcommerce) {
                this.setupEnhancedEcommerce();
            }

            console.log('GA4: Initialized successfully');
        };
    }

    /**
     * Initialize Microsoft Clarity
     */
    initializeClarity() {
        // Load Clarity script
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.innerHTML = `
            (function(c,l,a,r,i,t,y){
                c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
                t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
                y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
            })(window, document, "clarity", "script", "${this.config.clarity.projectId}");
        `;
        document.head.appendChild(script);

        // Wait for Clarity to load
        setTimeout(() => {
            if (window.clarity) {
                // Configure Clarity settings
                window.clarity('consent');
                
                // Setup custom tags
                this.setupClarityCustomTags();
                
                console.log('Clarity: Initialized successfully');
            }
        }, 1000);
    }

    /**
     * Setup Clarity custom tags
     */
    setupClarityCustomTags() {
        // User segment tag
        this.setClarityTag('user_segment', this.getUserSegment());
        
        // Test variant tag
        if (this.state.currentTestVariant) {
            this.setClarityTag('test_variant', this.state.currentTestVariant);
        }
        
        // Lead quality tag
        this.setClarityTag('lead_quality', this.state.leadQualityScore);
    }

    /**
     * Setup cross-platform tracking
     */
    setupCrossPlatformTracking() {
        // Unified event tracking
        this.setupUnifiedEventTracking();
        
        // User journey tracking
        this.setupUserJourneyTracking();
        
        // Conversion funnel tracking
        this.setupConversionFunnelTracking();
    }

    /**
     * Setup enhanced ecommerce (GA4)
     */
    setupEnhancedEcommerce() {
        // Product impressions
        this.trackProductImpression({
            product_id: 'mingus_assessment',
            product_name: 'MINGUS Assessment',
            product_category: 'financial_planning',
            price: 0,
            currency: 'USD'
        });
    }

    /**
     * Track conversion event
     */
    trackConversion(eventName, value = 20) {
        const eventData = {
            event_name: eventName,
            conversion_value: value,
            currency: 'USD',
            timestamp: Date.now(),
            user_segment: this.getUserSegment(),
            lead_quality_score: this.state.leadQualityScore
        };

        // GA4 conversion tracking
        this.trackGA4Event(this.config.events.conversion, {
            value: value,
            currency: 'USD',
            transaction_id: this.generateTransactionId(),
            items: [{
                item_id: 'mingus_assessment',
                item_name: 'MINGUS Assessment',
                price: value,
                quantity: 1
            }]
        });

        // Clarity conversion tracking
        this.setClarityTag(this.config.events.clarityConversion, eventData);
        this.setClarityTag('conversion_value', value);

        // Update lead quality score
        this.updateLeadQualityScore(value);

        // Track in user journey
        this.addToUserJourney('conversion', eventData);

        console.log('Conversion tracked:', eventData);
    }

    /**
     * Track assessment selection
     */
    trackAssessmentSelection(assessmentType) {
        const eventData = {
            assessment_type: assessmentType,
            timestamp: Date.now(),
            user_segment: this.getUserSegment(),
            session_duration: this.getSessionDuration()
        };

        // GA4 assessment tracking
        this.trackGA4Event(this.config.events.assessmentSelected, {
            assessment_type: assessmentType,
            custom_parameter_4: assessmentType,
            engagement_time_msec: this.getSessionDuration()
        });

        // Clarity assessment tracking
        this.setClarityTag(this.config.events.clarityAssessmentSelection, eventData);
        this.setClarityTag('assessment_type', assessmentType);

        // Track in user journey
        this.addToUserJourney('assessment_selection', eventData);

        // Update lead quality score
        this.updateLeadQualityScore(10);

        console.log('Assessment selection tracked:', eventData);
    }

    /**
     * Track modal interactions
     */
    trackModalInteraction(action, modalType = 'assessment') {
        const eventData = {
            modal_type: modalType,
            action: action,
            timestamp: Date.now(),
            session_duration: this.getSessionDuration()
        };

        // GA4 modal tracking
        this.trackGA4Event(this.config.events.assessmentModalOpen, {
            modal_type: modalType,
            action: action,
            engagement_time_msec: this.getSessionDuration()
        });

        // Clarity modal tracking
        this.setClarityTag(this.config.events.clarityAssessmentModal, eventData);
        this.setClarityTag('modal_interaction', `${modalType}_${action}`);

        // Track in user journey
        this.addToUserJourney('modal_interaction', eventData);

        console.log('Modal interaction tracked:', eventData);
    }

    /**
     * Track CTA button clicks
     */
    trackCTAClick(buttonLocation, buttonText, ctaType = 'primary') {
        const eventData = {
            button_location: buttonLocation,
            button_text: buttonText,
            cta_type: ctaType,
            timestamp: Date.now(),
            session_duration: this.getSessionDuration()
        };

        // GA4 CTA tracking
        this.trackGA4Event(this.config.events.ctaClick, {
            button_location: buttonLocation,
            button_text: buttonText,
            cta_type: ctaType,
            engagement_time_msec: this.getSessionDuration()
        });

        // Clarity CTA tracking
        this.setClarityTag(this.config.events.clarityCTAClick, eventData);
        this.setClarityTag('cta_click_location', buttonLocation);

        // Track in user journey
        this.addToUserJourney('cta_click', eventData);

        // Update lead quality score
        this.updateLeadQualityScore(5);

        console.log('CTA click tracked:', eventData);
    }

    /**
     * Track scroll depth
     */
    trackScrollDepth(depth) {
        if (this.state.scrollDepthReached.has(depth)) {
            return; // Already tracked
        }

        this.state.scrollDepthReached.add(depth);

        const eventData = {
            scroll_depth: depth,
            timestamp: Date.now(),
            session_duration: this.getSessionDuration()
        };

        // GA4 scroll tracking
        this.trackGA4Event(this.config.events.scrollDepth, {
            scroll_depth: depth,
            engagement_time_msec: this.getSessionDuration()
        });

        // Clarity scroll tracking
        this.setClarityTag('scroll_depth', depth);

        // Track in user journey
        this.addToUserJourney('scroll_depth', eventData);

        console.log('Scroll depth tracked:', depth + '%');
    }

    /**
     * Track time on page milestones
     */
    trackTimeMilestone(seconds) {
        if (this.state.timeMilestonesReached.has(seconds)) {
            return; // Already tracked
        }

        this.state.timeMilestonesReached.add(seconds);

        const eventData = {
            time_on_page: seconds,
            timestamp: Date.now(),
            session_duration: this.getSessionDuration()
        };

        // GA4 time tracking
        this.trackGA4Event(this.config.events.timeOnPage, {
            time_on_page: seconds,
            engagement_time_msec: this.getSessionDuration()
        });

        // Clarity time tracking
        this.setClarityTag('time_on_page', seconds);

        // Track in user journey
        this.addToUserJourney('time_milestone', eventData);

        console.log('Time milestone tracked:', seconds + ' seconds');
    }

    /**
     * Track form submissions
     */
    trackFormSubmission(formType, formData = {}) {
        const eventData = {
            form_type: formType,
            form_data: this.anonymizeFormData(formData),
            timestamp: Date.now(),
            session_duration: this.getSessionDuration()
        };

        // GA4 form tracking
        this.trackGA4Event(this.config.events.formSubmission, {
            form_type: formType,
            engagement_time_msec: this.getSessionDuration()
        });

        // Clarity form tracking
        this.setClarityTag('form_submission', eventData);
        this.setClarityTag('form_type', formType);

        // Track in user journey
        this.addToUserJourney('form_submission', eventData);

        // Update lead quality score
        this.updateLeadQualityScore(15);

        console.log('Form submission tracked:', eventData);
    }

    /**
     * Track errors
     */
    trackError(error, context = {}) {
        const eventData = {
            error_message: error.message,
            error_stack: error.stack,
            context: context,
            timestamp: Date.now(),
            session_duration: this.getSessionDuration()
        };

        // GA4 error tracking
        this.trackGA4Event(this.config.events.error, {
            error_message: error.message,
            error_type: error.name,
            engagement_time_msec: this.getSessionDuration()
        });

        // Clarity error tracking
        this.setClarityTag('javascript_error', eventData);

        console.error('Error tracked:', eventData);
    }

    /**
     * Track performance metrics
     */
    trackPerformance(metric, value) {
        const eventData = {
            metric: metric,
            value: value,
            timestamp: Date.now()
        };

        // GA4 performance tracking
        this.trackGA4Event(this.config.events.performance, {
            metric: metric,
            value: value
        });

        // Clarity performance tracking
        this.setClarityTag('performance_metric', eventData);

        console.log('Performance tracked:', eventData);
    }

    /**
     * Setup session monitoring
     */
    setupSessionMonitoring() {
        // Update last activity on user interaction
        const updateActivity = () => {
            this.state.lastActivity = Date.now();
        };

        // Track user interactions
        ['click', 'scroll', 'keypress', 'mousemove'].forEach(event => {
            document.addEventListener(event, updateActivity, { passive: true });
        });

        // Check for session timeout
        setInterval(() => {
            const timeSinceActivity = Date.now() - this.state.lastActivity;
            if (timeSinceActivity > this.config.sessionTimeout) {
                this.trackSessionEnd();
            }
        }, 60000); // Check every minute
    }

    /**
     * Setup scroll tracking
     */
    setupScrollTracking() {
        let scrollTimeout;
        
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            
            scrollTimeout = setTimeout(() => {
                const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
                
                // Track scroll milestones
                this.config.scrollMilestones.forEach(milestone => {
                    if (scrollPercent >= milestone) {
                        this.trackScrollDepth(milestone);
                    }
                });
            }, 100);
        }, { passive: true });
    }

    /**
     * Setup time tracking
     */
    setupTimeTracking() {
        setInterval(() => {
            const timeOnPage = Math.floor((Date.now() - this.state.sessionStartTime) / 1000);
            
            // Track time milestones
            this.config.timeMilestones.forEach(milestone => {
                if (timeOnPage >= milestone) {
                    this.trackTimeMilestone(milestone);
                }
            });
        }, 1000);
    }

    /**
     * Setup error tracking
     */
    setupErrorTracking() {
        // JavaScript errors
        window.addEventListener('error', (event) => {
            this.trackError(event.error, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });

        // Promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.trackError(new Error(event.reason), {
                type: 'unhandled_promise_rejection'
            });
        });
    }

    /**
     * Setup performance monitoring
     */
    setupPerformanceMonitoring() {
        // Core Web Vitals
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    switch (entry.entryType) {
                        case 'largest-contentful-paint':
                            this.trackPerformance('lcp', entry.startTime);
                            break;
                        case 'first-input':
                            this.trackPerformance('fid', entry.processingStart - entry.startTime);
                            break;
                        case 'layout-shift':
                            this.trackPerformance('cls', entry.value);
                            break;
                    }
                }
            });
            
            observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] });
        }

        // Page load time
        window.addEventListener('load', () => {
            const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
            this.trackPerformance('page_load_time', loadTime);
        });
    }

    /**
     * Setup unified event tracking
     */
    setupUnifiedEventTracking() {
        // Unified event handler
        this.trackEvent = (eventName, parameters = {}) => {
            // GA4 tracking
            this.trackGA4Event(eventName, parameters);
            
            // Clarity tracking
            this.setClarityTag(eventName, parameters);
            
            // Add to user journey
            this.addToUserJourney(eventName, parameters);
        };
    }

    /**
     * Setup user journey tracking
     */
    setupUserJourneyTracking() {
        // Track page views
        this.trackPageView();
        
        // Track user interactions
        this.setupInteractionTracking();
    }

    /**
     * Setup conversion funnel tracking
     */
    setupConversionFunnelTracking() {
        // Define funnel stages
        this.funnelStages = [
            'page_view',
            'scroll_engagement',
            'cta_click',
            'modal_open',
            'assessment_selection',
            'conversion'
        ];
        
        this.currentFunnelStage = 0;
    }

    /**
     * Track GA4 event
     */
    trackGA4Event(eventName, parameters = {}) {
        if (window.gtag && this.state.userConsent) {
            window.gtag('event', eventName, {
                ...parameters,
                custom_parameter_1: this.getUserSegment(),
                custom_parameter_2: this.state.leadQualityScore,
                custom_parameter_3: this.state.currentTestVariant
            });
        }
    }

    /**
     * Set Clarity custom tag
     */
    setClarityTag(tagName, value) {
        if (window.clarity && this.state.userConsent) {
            window.clarity('set', tagName, value);
        }
    }

    /**
     * Track page view
     */
    trackPageView() {
        const pageData = {
            page_title: document.title,
            page_url: window.location.href,
            referrer: document.referrer,
            timestamp: Date.now()
        };

        // GA4 page view
        this.trackGA4Event('page_view', pageData);

        // Clarity page view
        this.setClarityTag('page_view', pageData);

        // Add to user journey
        this.addToUserJourney('page_view', pageData);
    }

    /**
     * Setup interaction tracking
     */
    setupInteractionTracking() {
        // Track all CTA clicks
        document.addEventListener('click', (event) => {
            const target = event.target;
            
            if (target.matches('.cta-button, .assessment-trigger, .cta-button')) {
                const buttonText = target.textContent.trim();
                const buttonLocation = this.getElementLocation(target);
                const ctaType = target.classList.contains('primary') ? 'primary' : 'secondary';
                
                this.trackCTAClick(buttonLocation, buttonText, ctaType);
            }
        });
    }

    /**
     * Get element location for tracking
     */
    getElementLocation(element) {
        const rect = element.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let location = 'unknown';
        
        if (rect.top < viewportHeight * 0.33) {
            location = 'top';
        } else if (rect.top < viewportHeight * 0.66) {
            location = 'middle';
        } else {
            location = 'bottom';
        }
        
        if (rect.left < viewportWidth * 0.33) {
            location += '_left';
        } else if (rect.left < viewportWidth * 0.66) {
            location += '_center';
        } else {
            location += '_right';
        }
        
        return location;
    }

    /**
     * Get user segment
     */
    getUserSegment() {
        // Simple segmentation based on behavior
        if (this.state.leadQualityScore >= 50) {
            return 'high_value';
        } else if (this.state.leadQualityScore >= 25) {
            return 'medium_value';
        } else {
            return 'low_value';
        }
    }

    /**
     * Update lead quality score
     */
    updateLeadQualityScore(points) {
        this.state.leadQualityScore += points;
        
        // Update Clarity tag
        this.setClarityTag('lead_quality_score', this.state.leadQualityScore);
        
        // Track score update
        this.trackGA4Event('lead_quality_update', {
            new_score: this.state.leadQualityScore,
            points_added: points
        });
    }

    /**
     * Add event to user journey
     */
    addToUserJourney(eventType, eventData) {
        this.state.userJourney.push({
            type: eventType,
            data: eventData,
            timestamp: Date.now()
        });
        
        // Keep journey size manageable
        if (this.state.userJourney.length > 100) {
            this.state.userJourney = this.state.userJourney.slice(-50);
        }
    }

    /**
     * Get session duration
     */
    getSessionDuration() {
        return Date.now() - this.state.sessionStartTime;
    }

    /**
     * Generate transaction ID
     */
    generateTransactionId() {
        return 'mingus_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Anonymize form data
     */
    anonymizeFormData(formData) {
        const anonymized = {};
        
        Object.keys(formData).forEach(key => {
            if (key.toLowerCase().includes('email') || key.toLowerCase().includes('name')) {
                anonymized[key] = '[REDACTED]';
            } else {
                anonymized[key] = formData[key];
            }
        });
        
        return anonymized;
    }

    /**
     * Track session end
     */
    trackSessionEnd() {
        const sessionData = {
            session_duration: this.getSessionDuration(),
            user_journey_length: this.state.userJourney.length,
            lead_quality_score: this.state.leadQualityScore,
            scroll_depth_max: Math.max(...this.state.scrollDepthReached),
            time_milestones_reached: this.state.timeMilestonesReached.size
        };

        // GA4 session end
        this.trackGA4Event('session_end', sessionData);

        // Clarity session end
        this.setClarityTag('session_end', sessionData);

        console.log('Session ended:', sessionData);
    }

    /**
     * Get analytics data for reporting
     */
    getAnalyticsData() {
        return {
            session: {
                startTime: this.state.sessionStartTime,
                duration: this.getSessionDuration(),
                lastActivity: this.state.lastActivity
            },
            user: {
                segment: this.getUserSegment(),
                leadQualityScore: this.state.leadQualityScore,
                testVariant: this.state.currentTestVariant
            },
            journey: this.state.userJourney,
            scrollDepth: Array.from(this.state.scrollDepthReached),
            timeMilestones: Array.from(this.state.timeMilestonesReached)
        };
    }

    /**
     * Export data for analysis
     */
    exportData() {
        const data = this.getAnalyticsData();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `mingus_analytics_${Date.now()}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }
}

// Initialize analytics when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mingusAnalytics = new MingusAnalytics();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MingusAnalytics;
}
