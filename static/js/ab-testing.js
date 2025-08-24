/**
 * MINGUS A/B Testing Module
 * Integrated with Analytics System for Comprehensive Testing
 * 
 * Features:
 * - Variant assignment and tracking
 * - Statistical significance calculation
 * - Integration with GA4 and Clarity
 * - Conversion rate optimization
 * - Real-time results monitoring
 * - Privacy-compliant testing
 */

class MingusABTesting {
    constructor(analytics) {
        this.analytics = analytics;
        
        // A/B Testing Configuration
        this.config = {
            tests: {
                cta_button_text: {
                    name: 'CTA Button Text Test',
                    variants: {
                        control: {
                            name: 'Control',
                            text: 'Start Assessment',
                            weight: 0.5
                        },
                        variant_a: {
                            name: 'Variant A',
                            text: 'Get Your Free Analysis',
                            weight: 0.25
                        },
                        variant_b: {
                            name: 'Variant B',
                            text: 'Discover Your Financial Future',
                            weight: 0.25
                        }
                    },
                    metrics: ['cta_click', 'conversion'],
                    significance_level: 0.05
                },
                hero_headline: {
                    name: 'Hero Headline Test',
                    variants: {
                        control: {
                            name: 'Control',
                            headline: 'Transform Your Financial Future',
                            weight: 0.5
                        },
                        variant_a: {
                            name: 'Variant A',
                            headline: 'Unlock Your Wealth Potential',
                            weight: 0.25
                        },
                        variant_b: {
                            name: 'Variant B',
                            headline: 'Master Your Money Journey',
                            weight: 0.25
                        }
                    },
                    metrics: ['scroll_depth', 'cta_click', 'conversion'],
                    significance_level: 0.05
                },
                assessment_modal_layout: {
                    name: 'Assessment Modal Layout Test',
                    variants: {
                        control: {
                            name: 'Control',
                            layout: 'grid',
                            weight: 0.5
                        },
                        variant_a: {
                            name: 'Variant A',
                            layout: 'list',
                            weight: 0.25
                        },
                        variant_b: {
                            name: 'Variant B',
                            layout: 'cards',
                            weight: 0.25
                        }
                    },
                    metrics: ['modal_open', 'assessment_selection', 'conversion'],
                    significance_level: 0.05
                }
            },
            storage: {
                prefix: 'mingus_ab_',
                expiry_days: 30
            },
            tracking: {
                enable_real_time: true,
                minimum_sample_size: 100,
                confidence_interval: 0.95
            }
        };

        // Test state
        this.state = {
            activeTests: {},
            results: {},
            userAssignments: {},
            isInitialized: false
        };

        // Initialize A/B testing
        this.init();
    }

    /**
     * Initialize A/B testing
     */
    init() {
        try {
            // Load user assignments
            this.loadUserAssignments();
            
            // Assign variants for active tests
            this.assignVariants();
            
            // Apply variants to DOM
            this.applyVariants();
            
            // Setup tracking
            this.setupTracking();
            
            // Setup real-time monitoring
            if (this.config.tracking.enable_real_time) {
                this.setupRealTimeMonitoring();
            }

            this.state.isInitialized = true;
            console.log('MingusABTesting: Initialized successfully');

        } catch (error) {
            console.error('MingusABTesting: Initialization failed', error);
        }
    }

    /**
     * Load user assignments from storage
     */
    loadUserAssignments() {
        try {
            const stored = localStorage.getItem(this.config.storage.prefix + 'assignments');
            if (stored) {
                const assignments = JSON.parse(stored);
                
                // Check expiry
                if (assignments.timestamp && 
                    Date.now() - assignments.timestamp < this.config.storage.expiry_days * 24 * 60 * 60 * 1000) {
                    this.state.userAssignments = assignments.data || {};
                }
            }
        } catch (error) {
            console.error('Error loading user assignments:', error);
        }
    }

    /**
     * Save user assignments to storage
     */
    saveUserAssignments() {
        try {
            const data = {
                data: this.state.userAssignments,
                timestamp: Date.now()
            };
            localStorage.setItem(this.config.storage.prefix + 'assignments', JSON.stringify(data));
        } catch (error) {
            console.error('Error saving user assignments:', error);
        }
    }

    /**
     * Assign variants for active tests
     */
    assignVariants() {
        Object.keys(this.config.tests).forEach(testId => {
            if (!this.state.userAssignments[testId]) {
                const variant = this.assignVariant(testId);
                this.state.userAssignments[testId] = variant;
                
                // Track assignment
                this.trackVariantAssignment(testId, variant);
            }
        });
        
        this.saveUserAssignments();
    }

    /**
     * Assign variant based on weights
     */
    assignVariant(testId) {
        const test = this.config.tests[testId];
        const random = Math.random();
        let cumulativeWeight = 0;
        
        for (const [variantId, variant] of Object.entries(test.variants)) {
            cumulativeWeight += variant.weight;
            if (random <= cumulativeWeight) {
                return variantId;
            }
        }
        
        // Fallback to control
        return 'control';
    }

    /**
     * Apply variants to DOM
     */
    applyVariants() {
        Object.keys(this.state.userAssignments).forEach(testId => {
            const variantId = this.state.userAssignments[testId];
            const test = this.config.tests[testId];
            const variant = test.variants[variantId];
            
            this.applyVariant(testId, variantId, variant);
        });
    }

    /**
     * Apply specific variant to DOM
     */
    applyVariant(testId, variantId, variant) {
        switch (testId) {
            case 'cta_button_text':
                this.applyCTAButtonText(variant);
                break;
            case 'hero_headline':
                this.applyHeroHeadline(variant);
                break;
            case 'assessment_modal_layout':
                this.applyModalLayout(variant);
                break;
        }
        
        // Add variant class to body for CSS targeting
        document.body.classList.add(`ab-test-${testId}-${variantId}`);
        
        // Track variant application
        this.trackVariantApplication(testId, variantId, variant);
    }

    /**
     * Apply CTA button text variant
     */
    applyCTAButtonText(variant) {
        const ctaButtons = document.querySelectorAll('.cta-button, .assessment-trigger');
        ctaButtons.forEach(button => {
            button.textContent = variant.text;
            button.setAttribute('data-ab-variant', variant.name);
        });
    }

    /**
     * Apply hero headline variant
     */
    applyHeroHeadline(variant) {
        const heroTitle = document.querySelector('.hero-title, h1');
        if (heroTitle) {
            heroTitle.textContent = variant.headline;
            heroTitle.setAttribute('data-ab-variant', variant.name);
        }
    }

    /**
     * Apply modal layout variant
     */
    applyModalLayout(variant) {
        const modal = document.getElementById('assessment-modal');
        if (modal) {
            modal.setAttribute('data-layout', variant.layout);
            modal.setAttribute('data-ab-variant', variant.name);
            
            // Apply layout-specific classes
            modal.classList.remove('layout-grid', 'layout-list', 'layout-cards');
            modal.classList.add(`layout-${variant.layout}`);
        }
    }

    /**
     * Setup tracking for A/B tests
     */
    setupTracking() {
        // Track all relevant events
        this.setupEventTracking();
        
        // Track conversion events
        this.setupConversionTracking();
        
        // Track engagement metrics
        this.setupEngagementTracking();
    }

    /**
     * Setup event tracking
     */
    setupEventTracking() {
        // Override analytics tracking to include test data
        const originalTrackEvent = this.analytics.trackEvent;
        
        this.analytics.trackEvent = (eventName, parameters = {}) => {
            // Add A/B test data to all events
            const testData = this.getTestDataForEvent(eventName);
            const enhancedParameters = {
                ...parameters,
                ...testData
            };
            
            // Call original tracking
            originalTrackEvent.call(this.analytics, eventName, enhancedParameters);
        };
    }

    /**
     * Setup conversion tracking
     */
    setupConversionTracking() {
        // Track conversions with test context
        const originalTrackConversion = this.analytics.trackConversion;
        
        this.analytics.trackConversion = (eventName, value = 20) => {
            // Add test data to conversion
            const testData = this.getTestDataForEvent('conversion');
            const enhancedParameters = {
                event_name: eventName,
                value: value,
                ...testData
            };
            
            // Call original conversion tracking
            originalTrackConversion.call(this.analytics, eventName, value);
            
            // Track conversion for A/B test results
            this.trackTestConversion(testData.test_id, testData.variant_id, value);
        };
    }

    /**
     * Setup engagement tracking
     */
    setupEngagementTracking() {
        // Track engagement metrics for each test
        Object.keys(this.state.userAssignments).forEach(testId => {
            const variantId = this.state.userAssignments[testId];
            
            // Track scroll depth
            this.trackEngagementMetric(testId, variantId, 'scroll_depth');
            
            // Track time on page
            this.trackEngagementMetric(testId, variantId, 'time_on_page');
            
            // Track CTA clicks
            this.trackEngagementMetric(testId, variantId, 'cta_click');
        });
    }

    /**
     * Get test data for event
     */
    getTestDataForEvent(eventName) {
        const testData = {};
        
        Object.keys(this.state.userAssignments).forEach(testId => {
            const variantId = this.state.userAssignments[testId];
            const test = this.config.tests[testId];
            
            // Check if this event is relevant for this test
            if (test.metrics.includes(eventName)) {
                testData.test_id = testId;
                testData.variant_id = variantId;
                testData.variant_name = test.variants[variantId].name;
                testData.test_name = test.name;
            }
        });
        
        return testData;
    }

    /**
     * Track variant assignment
     */
    trackVariantAssignment(testId, variantId) {
        const test = this.config.tests[testId];
        const variant = test.variants[variantId];
        
        // Track in analytics
        this.analytics.trackEvent('ab_test_assignment', {
            test_id: testId,
            test_name: test.name,
            variant_id: variantId,
            variant_name: variant.name,
            assignment_method: 'weighted_random'
        });
        
        // Set Clarity tag
        this.analytics.setClarityTag('ab_test_assignment', {
            test_id: testId,
            variant_id: variantId
        });
    }

    /**
     * Track variant application
     */
    trackVariantApplication(testId, variantId, variant) {
        // Track in analytics
        this.analytics.trackEvent('ab_test_variant_applied', {
            test_id: testId,
            variant_id: variantId,
            variant_name: variant.name,
            application_timestamp: Date.now()
        });
        
        // Set Clarity tag
        this.analytics.setClarityTag('ab_test_variant', variantId);
    }

    /**
     * Track test conversion
     */
    trackTestConversion(testId, variantId, value) {
        if (!this.state.results[testId]) {
            this.state.results[testId] = {};
        }
        
        if (!this.state.results[testId][variantId]) {
            this.state.results[testId][variantId] = {
                conversions: 0,
                impressions: 0,
                revenue: 0,
                events: []
            };
        }
        
        this.state.results[testId][variantId].conversions++;
        this.state.results[testId][variantId].revenue += value;
        
        // Track event
        this.state.results[testId][variantId].events.push({
            type: 'conversion',
            value: value,
            timestamp: Date.now()
        });
        
        // Save results
        this.saveResults();
        
        // Check for statistical significance
        this.checkStatisticalSignificance(testId);
    }

    /**
     * Track engagement metric
     */
    trackEngagementMetric(testId, variantId, metric) {
        if (!this.state.results[testId]) {
            this.state.results[testId] = {};
        }
        
        if (!this.state.results[testId][variantId]) {
            this.state.results[testId][variantId] = {
                conversions: 0,
                impressions: 0,
                revenue: 0,
                events: []
            };
        }
        
        // Track event
        this.state.results[testId][variantId].events.push({
            type: metric,
            timestamp: Date.now()
        });
        
        // Save results
        this.saveResults();
    }

    /**
     * Save test results
     */
    saveResults() {
        try {
            localStorage.setItem(this.config.storage.prefix + 'results', JSON.stringify(this.state.results));
        } catch (error) {
            console.error('Error saving test results:', error);
        }
    }

    /**
     * Load test results
     */
    loadResults() {
        try {
            const stored = localStorage.getItem(this.config.storage.prefix + 'results');
            if (stored) {
                this.state.results = JSON.parse(stored);
            }
        } catch (error) {
            console.error('Error loading test results:', error);
        }
    }

    /**
     * Check statistical significance
     */
    checkStatisticalSignificance(testId) {
        const test = this.config.tests[testId];
        const results = this.state.results[testId];
        
        if (!results) return;
        
        // Calculate conversion rates
        const conversionRates = {};
        const sampleSizes = {};
        
        Object.keys(test.variants).forEach(variantId => {
            if (results[variantId]) {
                const data = results[variantId];
                conversionRates[variantId] = data.conversions / Math.max(data.impressions, 1);
                sampleSizes[variantId] = data.impressions;
            }
        });
        
        // Check if we have enough data
        const totalSampleSize = Object.values(sampleSizes).reduce((sum, size) => sum + size, 0);
        
        if (totalSampleSize >= this.config.tracking.minimum_sample_size) {
            // Perform statistical test
            const significance = this.performStatisticalTest(conversionRates, sampleSizes);
            
            if (significance.isSignificant) {
                this.reportSignificantResult(testId, significance);
            }
        }
    }

    /**
     * Perform statistical test (Chi-square test)
     */
    performStatisticalTest(conversionRates, sampleSizes) {
        // Simple chi-square test for conversion rates
        const variants = Object.keys(conversionRates);
        const controlRate = conversionRates.control || 0;
        
        let chiSquare = 0;
        let degreesOfFreedom = variants.length - 1;
        
        variants.forEach(variantId => {
            if (variantId !== 'control') {
                const observed = conversionRates[variantId] * sampleSizes[variantId];
                const expected = controlRate * sampleSizes[variantId];
                
                if (expected > 0) {
                    chiSquare += Math.pow(observed - expected, 2) / expected;
                }
            }
        });
        
        // Critical value for 95% confidence (simplified)
        const criticalValue = 3.841; // For 1 degree of freedom
        
        return {
            isSignificant: chiSquare > criticalValue,
            chiSquare: chiSquare,
            criticalValue: criticalValue,
            confidence: chiSquare > criticalValue ? 'high' : 'low'
        };
    }

    /**
     * Report significant result
     */
    reportSignificantResult(testId, significance) {
        const test = this.config.tests[testId];
        const results = this.state.results[testId];
        
        console.log(`🚀 A/B Test "${test.name}" shows significant results!`, {
            test_id: testId,
            significance: significance,
            results: results
        });
        
        // Track significant result
        this.analytics.trackEvent('ab_test_significant_result', {
            test_id: testId,
            test_name: test.name,
            chi_square: significance.chiSquare,
            confidence: significance.confidence,
            results: results
        });
        
        // Send notification (could be webhook, email, etc.)
        this.sendSignificanceNotification(testId, significance, results);
    }

    /**
     * Send significance notification
     */
    sendSignificanceNotification(testId, significance, results) {
        // This could be a webhook to your analytics dashboard
        // or an email notification system
        const notification = {
            type: 'ab_test_significance',
            test_id: testId,
            significance: significance,
            results: results,
            timestamp: Date.now()
        };
        
        // Example: Send to analytics endpoint
        fetch('/api/analytics/ab-test-significance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(notification)
        }).catch(error => {
            console.error('Error sending significance notification:', error);
        });
    }

    /**
     * Setup real-time monitoring
     */
    setupRealTimeMonitoring() {
        // Monitor results every 5 minutes
        setInterval(() => {
            this.loadResults();
            Object.keys(this.config.tests).forEach(testId => {
                this.checkStatisticalSignificance(testId);
            });
        }, 5 * 60 * 1000);
    }

    /**
     * Get test results summary
     */
    getTestResults(testId) {
        const results = this.state.results[testId];
        if (!results) return null;
        
        const test = this.config.tests[testId];
        const summary = {};
        
        Object.keys(test.variants).forEach(variantId => {
            if (results[variantId]) {
                const data = results[variantId];
                summary[variantId] = {
                    name: test.variants[variantId].name,
                    conversions: data.conversions,
                    impressions: data.impressions,
                    revenue: data.revenue,
                    conversion_rate: data.conversions / Math.max(data.impressions, 1),
                    avg_order_value: data.conversions > 0 ? data.revenue / data.conversions : 0
                };
            }
        });
        
        return summary;
    }

    /**
     * Get all test results
     */
    getAllTestResults() {
        const allResults = {};
        
        Object.keys(this.config.tests).forEach(testId => {
            allResults[testId] = {
                test_name: this.config.tests[testId].name,
                results: this.getTestResults(testId),
                user_assignment: this.state.userAssignments[testId]
            };
        });
        
        return allResults;
    }

    /**
     * Export test data
     */
    exportTestData() {
        const data = {
            config: this.config,
            state: this.state,
            results: this.getAllTestResults(),
            export_timestamp: Date.now()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `mingus_ab_test_data_${Date.now()}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }

    /**
     * Reset test for current user
     */
    resetTest(testId) {
        delete this.state.userAssignments[testId];
        this.saveUserAssignments();
        
        // Reassign variant
        const variant = this.assignVariant(testId);
        this.state.userAssignments[testId] = variant;
        this.applyVariant(testId, variant, this.config.tests[testId].variants[variant]);
        
        console.log(`Test "${testId}" reset for current user`);
    }

    /**
     * Get current user's test assignments
     */
    getUserAssignments() {
        return this.state.userAssignments;
    }

    /**
     * Check if user is in specific test variant
     */
    isUserInVariant(testId, variantId) {
        return this.state.userAssignments[testId] === variantId;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MingusABTesting;
}
