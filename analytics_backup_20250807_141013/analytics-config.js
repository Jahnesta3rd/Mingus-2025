/**
 * MINGUS Analytics Configuration
 * Configuration for Google Analytics 4 and Microsoft Clarity
 */

window.MINGUS = window.MINGUS || {};

// Analytics Configuration
window.MINGUS.analyticsConfig = {
    // ===== GOOGLE ANALYTICS 4 CONFIGURATION =====
    ga4: {
        enabled: true,
        measurementId: 'G-XXXXXXXXXX', // Replace with your GA4 Measurement ID
        debugMode: false, // Set to true for development
        enhancedEcommerce: true,
        customDimensions: {
            // Custom dimensions for GA4
            'user_segment': 'cd1',
            'assessment_type': 'cd2',
            'conversion_source': 'cd3',
            'ab_test_variant': 'cd4',
            'user_engagement_level': 'cd5'
        },
        customMetrics: {
            // Custom metrics for GA4
            'assessment_completion_rate': 'cm1',
            'time_to_conversion': 'cm2',
            'user_engagement_score': 'cm3'
        },
        conversionGoals: {
            // Conversion tracking goals
            'lead_generation': {
                id: 'AW-123456789/lead_generation',
                value: 20,
                currency: 'USD'
            },
            'assessment_completion': {
                id: 'AW-123456789/assessment_completion',
                value: 50,
                currency: 'USD'
            },
            'subscription_signup': {
                id: 'AW-123456789/subscription_signup',
                value: 100,
                currency: 'USD'
            }
        }
    },

    // ===== MICROSOFT CLARITY CONFIGURATION =====
    clarity: {
        enabled: true,
        projectId: 'your-clarity-project-id', // Replace with your Clarity Project ID
        sessionRecording: true,
        heatmaps: true,
        customTags: {
            // Custom tags for Clarity session recordings
            'user_segment': 'general_user',
            'assessment_type': 'none',
            'conversion_stage': 'visitor',
            'ab_test_variant': 'control'
        },
        privacySettings: {
            // Privacy settings for Clarity
            maskTextInputs: true,
            maskUserInput: true,
            maskImages: false,
            maskButtons: false
        }
    },

    // ===== EVENT TRACKING CONFIGURATION =====
    events: {
        // Page view tracking
        pageViews: {
            enabled: true,
            trackVirtualPageViews: true,
            trackHashChanges: true
        },

        // User interaction tracking
        userActions: {
            enabled: true,
            trackClicks: true,
            trackFormInteractions: true,
            trackScrollDepth: true,
            trackTimeOnPage: true
        },

        // Conversion tracking
        conversions: {
            enabled: true,
            trackLeadGeneration: true,
            trackAssessmentCompletions: true,
            trackSubscriptionSignups: true,
            trackFormSubmissions: true
        },

        // Performance tracking
        performance: {
            enabled: true,
            trackPageLoadTimes: true,
            trackCoreWebVitals: true,
            trackResourceTiming: true
        },

        // Error tracking
        errors: {
            enabled: true,
            trackJavaScriptErrors: true,
            trackPromiseRejections: true,
            trackNetworkErrors: true
        },

        // Modal interaction tracking
        modalInteractions: {
            enabled: true,
            trackOpens: true,
            trackCloses: true,
            trackSelections: true
        }
    },

    // ===== PRIVACY AND COMPLIANCE =====
    privacy: {
        gdprCompliant: true,
        consentRequired: true,
        ipAnonymization: true,
        dataRetention: 26, // months
        cookieConsent: {
            required: true,
            bannerText: 'We use cookies and analytics to improve your experience.',
            privacyUrl: '/privacy',
            acceptText: 'Accept',
            declineText: 'Decline'
        }
    },

    // ===== A/B TESTING CONFIGURATION =====
    abTesting: {
        enabled: true,
        tests: {
            'cta_button_color': {
                variants: ['blue', 'green', 'purple'],
                defaultVariant: 'blue'
            },
            'headline_text': {
                variants: ['original', 'benefit_focused', 'urgency_focused'],
                defaultVariant: 'original'
            },
            'pricing_display': {
                variants: ['monthly', 'annual', 'both'],
                defaultVariant: 'monthly'
            }
        }
    },

    // ===== USER SEGMENTATION =====
    userSegmentation: {
        enabled: true,
        segments: {
            'new_visitor': {
                criteria: 'first_visit',
                description: 'First-time visitors'
            },
            'returning_user': {
                criteria: 'returning_visit',
                description: 'Returning visitors'
            },
            'high_engagement': {
                criteria: 'time_on_site > 300',
                description: 'Highly engaged users'
            },
            'assessment_interested': {
                criteria: 'assessment_modal_opened',
                description: 'Users interested in assessments'
            }
        }
    },

    // ===== CONVERSION FUNNELS =====
    conversionFunnels: {
        enabled: true,
        funnels: {
            'lead_generation': {
                steps: [
                    'page_view',
                    'cta_click',
                    'form_view',
                    'form_submission'
                ],
                goal: 'lead_generation'
            },
            'assessment_completion': {
                steps: [
                    'assessment_modal_opened',
                    'assessment_selected',
                    'assessment_started',
                    'assessment_completed'
                ],
                goal: 'assessment_completion'
            },
            'subscription_signup': {
                steps: [
                    'pricing_page_view',
                    'plan_selected',
                    'checkout_started',
                    'payment_completed'
                ],
                goal: 'subscription_signup'
            }
        }
    },

    // ===== DEBUGGING AND DEVELOPMENT =====
    debug: {
        enabled: false, // Set to true for development
        logEvents: false,
        showDebugPanel: false,
        trackAllInteractions: false
    },

    // ===== ENVIRONMENT-SPECIFIC SETTINGS =====
    environments: {
        development: {
            ga4: {
                debugMode: true,
                measurementId: 'G-DEV-XXXXXXXX'
            },
            clarity: {
                enabled: false // Disable Clarity in development
            },
            debug: {
                enabled: true,
                logEvents: true,
                showDebugPanel: true
            }
        },
        staging: {
            ga4: {
                debugMode: false,
                measurementId: 'G-STAGING-XXXXXXXX'
            },
            clarity: {
                enabled: true,
                projectId: 'staging-clarity-id'
            }
        },
        production: {
            ga4: {
                debugMode: false,
                measurementId: 'G-PRODUCTION-XXXXXXXX'
            },
            clarity: {
                enabled: true,
                projectId: 'production-clarity-id'
            }
        }
    }
};

// ===== HELPER FUNCTIONS =====

// Get current environment
window.MINGUS.getEnvironment = function() {
    const hostname = window.location.hostname;
    
    if (hostname.includes('localhost') || hostname.includes('127.0.0.1')) {
        return 'development';
    } else if (hostname.includes('staging') || hostname.includes('test')) {
        return 'staging';
    } else {
        return 'production';
    }
};

// Get environment-specific configuration
window.MINGUS.getAnalyticsConfig = function() {
    const environment = window.MINGUS.getEnvironment();
    const baseConfig = window.MINGUS.analyticsConfig;
    const envConfig = baseConfig.environments[environment] || {};
    
    // Merge configurations
    return {
        ...baseConfig,
        ga4: { ...baseConfig.ga4, ...envConfig.ga4 },
        clarity: { ...baseConfig.clarity, ...envConfig.clarity },
        debug: { ...baseConfig.debug, ...envConfig.debug }
    };
};

// Validate configuration
window.MINGUS.validateAnalyticsConfig = function() {
    const config = window.MINGUS.getAnalyticsConfig();
    const errors = [];
    
    // Validate GA4 configuration
    if (config.ga4.enabled) {
        if (!config.ga4.measurementId || config.ga4.measurementId === 'G-XXXXXXXXXX') {
            errors.push('GA4 Measurement ID is not configured');
        }
    }
    
    // Validate Clarity configuration
    if (config.clarity.enabled) {
        if (!config.clarity.projectId || config.clarity.projectId === 'your-clarity-project-id') {
            errors.push('Microsoft Clarity Project ID is not configured');
        }
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
};

// Initialize configuration validation
document.addEventListener('DOMContentLoaded', function() {
    const validation = window.MINGUS.validateAnalyticsConfig();
    
    if (!validation.isValid) {
        console.warn('Analytics Configuration Issues:', validation.errors);
        
        // Show warning in development
        if (window.MINGUS.getEnvironment() === 'development') {
            const warning = document.createElement('div');
            warning.style.cssText = `
                position: fixed;
                top: 10px;
                left: 10px;
                background: #f39c12;
                color: white;
                padding: 10px;
                border-radius: 4px;
                z-index: 10000;
                font-family: monospace;
                font-size: 12px;
            `;
            warning.innerHTML = `
                <strong>Analytics Config Issues:</strong><br>
                ${validation.errors.join('<br>')}
            `;
            document.body.appendChild(warning);
        }
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.MINGUS.analyticsConfig;
}
