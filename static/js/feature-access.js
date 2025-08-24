/**
 * Feature Access Control - Frontend Module
 * 
 * This module provides frontend functionality for:
 * - Feature access checking and graceful degradation
 * - Upgrade prompts and trial offers
 * - Educational content display
 * - Alternative suggestions for budget users
 */

class FeatureAccessManager {
    constructor() {
        this.baseUrl = '/api/features';
        this.currentUser = null;
        this.featureCache = new Map();
        this.upgradePrompts = new Map();
        this.init();
    }

    async init() {
        try {
            // Get current user info
            await this.getCurrentUser();
            
            // Initialize upgrade prompts
            this.initializeUpgradePrompts();
            
            // Set up global error handlers
            this.setupErrorHandlers();
            
            console.log('Feature Access Manager initialized');
        } catch (error) {
            console.error('Error initializing Feature Access Manager:', error);
        }
    }

    async getCurrentUser() {
        try {
            const response = await fetch('/api/user/current', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                this.currentUser = await response.json();
            }
        } catch (error) {
            console.error('Error getting current user:', error);
        }
    }

    initializeUpgradePrompts() {
        // Health & Wellness Upgrade Prompt
        this.upgradePrompts.set('health_analytics', {
            title: 'Unlock Advanced Health Analytics',
            message: 'Get unlimited health check-ins and personalized insights to optimize your wellness journey.',
            benefits: [
                'Unlimited health check-ins',
                'Advanced health analytics',
                'Personalized wellness recommendations',
                'Health-finance correlation insights'
            ],
            cta: 'Upgrade to Mid-Tier',
            price: '$35/month'
        });

        // AI Insights Upgrade Prompt
        this.upgradePrompts.set('ai_insights', {
            title: 'Experience AI-Powered Insights',
            message: 'Get personalized recommendations and predictive analytics to make smarter financial decisions.',
            benefits: [
                '50 AI insights per month',
                'Personalized recommendations',
                'Predictive analytics',
                'Pattern recognition'
            ],
            cta: 'Upgrade to Mid-Tier',
            price: '$35/month'
        });

        // Financial Reports Upgrade Prompt
        this.upgradePrompts.set('financial_reports', {
            title: 'Unlimited Financial Reports',
            message: 'Generate as many financial reports as you need with advanced customization options.',
            benefits: [
                'Unlimited financial reports',
                'Custom report templates',
                'Advanced financial analytics',
                'White-label reports'
            ],
            cta: 'Upgrade to Mid-Tier',
            price: '$35/month'
        });

        // Career Risk Management Upgrade Prompt
        this.upgradePrompts.set('career_risk_management', {
            title: 'Protect Your Career & Income',
            message: 'Assess and manage career-related financial risks with advanced modeling and strategies.',
            benefits: [
                'Advanced risk modeling',
                'Personalized career strategies',
                'Industry trend analysis',
                'Transition planning tools'
            ],
            cta: 'Upgrade to Mid-Tier',
            price: '$35/month'
        });

        // API Access Upgrade Prompt
        this.upgradePrompts.set('api_access', {
            title: 'Unlock API Access',
            message: 'Integrate MINGUS with your own applications and workflows.',
            benefits: [
                '10,000 API requests per month',
                'Priority API support',
                'Custom integrations',
                'Webhook support'
            ],
            cta: 'Upgrade to Professional',
            price: '$75/month'
        });
    }

    setupErrorHandlers() {
        // Global error handler for feature access errors
        window.addEventListener('feature-access-error', (event) => {
            this.handleFeatureAccessError(event.detail);
        });

        // Handle 402 Payment Required responses
        window.addEventListener('fetch-error', (event) => {
            if (event.detail.status === 402) {
                this.handlePaymentRequired(event.detail);
            }
        });
    }

    async checkFeatureAccess(featureId, context = {}) {
        try {
            const cacheKey = `${featureId}_${JSON.stringify(context)}`;
            
            // Check cache first
            if (this.featureCache.has(cacheKey)) {
                const cached = this.featureCache.get(cacheKey);
                if (Date.now() - cached.timestamp < 60000) { // 1 minute cache
                    return cached.data;
                }
            }

            const response = await fetch(`${this.baseUrl}/check-access/${featureId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            // Cache the result
            this.featureCache.set(cacheKey, {
                data: result,
                timestamp: Date.now()
            });

            return result;
        } catch (error) {
            console.error('Error checking feature access:', error);
            return {
                success: false,
                error: 'network_error',
                message: 'Unable to check feature access'
            };
        }
    }

    async getFeatureSummary() {
        try {
            const response = await fetch(`${this.baseUrl}/summary`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            return await response.json();
        } catch (error) {
            console.error('Error getting feature summary:', error);
            return {
                success: false,
                error: 'network_error',
                message: 'Unable to get feature summary'
            };
        }
    }

    async startFeatureTrial(featureId) {
        try {
            const response = await fetch(`${this.baseUrl}/trial/start/${featureId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showTrialStartedModal(featureId, result);
            }

            return result;
        } catch (error) {
            console.error('Error starting feature trial:', error);
            return {
                success: false,
                error: 'network_error',
                message: 'Unable to start trial'
            };
        }
    }

    async getGracefulDegradationInfo(featureId) {
        try {
            const response = await fetch(`${this.baseUrl}/graceful-degradation/${featureId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            return await response.json();
        } catch (error) {
            console.error('Error getting graceful degradation info:', error);
            return {
                success: false,
                error: 'network_error',
                message: 'Unable to get degradation info'
            };
        }
    }

    handleFeatureAccessError(error) {
        const { featureId, reason, currentTier, requiredTier } = error;

        switch (reason) {
            case 'subscription_required':
                this.showSubscriptionRequiredModal(featureId);
                break;
            case 'upgrade_required':
                this.showUpgradeRequiredModal(featureId, currentTier, requiredTier);
                break;
            case 'usage_limit_exceeded':
                this.showUsageLimitModal(featureId, error.currentUsage, error.usageLimits);
                break;
            default:
                this.showGenericAccessDeniedModal(featureId);
        }
    }

    handlePaymentRequired(error) {
        const featureId = this.extractFeatureIdFromUrl();
        if (featureId) {
            this.showSubscriptionRequiredModal(featureId);
        }
    }

    showSubscriptionRequiredModal(featureId) {
        const modal = this.createModal({
            title: 'Subscription Required',
            message: 'A subscription is required to access this feature. Start your journey with MINGUS today!',
            type: 'subscription_required',
            featureId: featureId,
            actions: [
                {
                    text: 'View Plans',
                    action: () => this.navigateToPricing(),
                    primary: true
                },
                {
                    text: 'Learn More',
                    action: () => this.showEducationalContent(featureId),
                    secondary: true
                },
                {
                    text: 'Cancel',
                    action: () => this.closeModal(),
                    secondary: true
                }
            ]
        });

        this.showModal(modal);
    }

    showUpgradeRequiredModal(featureId, currentTier, requiredTier) {
        const prompt = this.upgradePrompts.get(featureId);
        if (!prompt) {
            this.showGenericUpgradeModal(featureId, currentTier, requiredTier);
            return;
        }

        const modal = this.createModal({
            title: prompt.title,
            message: prompt.message,
            type: 'upgrade_required',
            featureId: featureId,
            benefits: prompt.benefits,
            price: prompt.price,
            actions: [
                {
                    text: prompt.cta,
                    action: () => this.navigateToUpgrade(currentTier),
                    primary: true
                },
                {
                    text: 'Start Trial',
                    action: () => this.startFeatureTrial(featureId),
                    secondary: true
                },
                {
                    text: 'Learn More',
                    action: () => this.showEducationalContent(featureId),
                    secondary: true
                },
                {
                    text: 'Cancel',
                    action: () => this.closeModal(),
                    secondary: true
                }
            ]
        });

        this.showModal(modal);
    }

    showUsageLimitModal(featureId, currentUsage, usageLimits) {
        const modal = this.createModal({
            title: 'Usage Limit Reached',
            message: 'You have reached your monthly usage limit for this feature. Upgrade for unlimited access!',
            type: 'usage_limit',
            featureId: featureId,
            currentUsage: currentUsage,
            usageLimits: usageLimits,
            actions: [
                {
                    text: 'Upgrade Now',
                    action: () => this.navigateToUpgrade(),
                    primary: true
                },
                {
                    text: 'View Usage',
                    action: () => this.showUsageDetails(featureId),
                    secondary: true
                },
                {
                    text: 'Cancel',
                    action: () => this.closeModal(),
                    secondary: true
                }
            ]
        });

        this.showModal(modal);
    }

    showTrialStartedModal(featureId, trialInfo) {
        const modal = this.createModal({
            title: 'Trial Started!',
            message: `Your ${trialInfo.duration_days}-day trial for this feature has begun. Enjoy exploring the premium features!`,
            type: 'trial_started',
            featureId: featureId,
            trialInfo: trialInfo,
            actions: [
                {
                    text: 'Start Using',
                    action: () => this.closeModal(),
                    primary: true
                },
                {
                    text: 'View Trial Status',
                    action: () => this.showTrialStatus(featureId),
                    secondary: true
                }
            ]
        });

        this.showModal(modal);
    }

    showEducationalContent(featureId) {
        this.getGracefulDegradationInfo(featureId).then(result => {
            if (result.success && result.educational_content) {
                const modal = this.createModal({
                    title: 'Learn About Premium Features',
                    message: result.educational_content,
                    type: 'educational',
                    featureId: featureId,
                    alternativeSuggestions: result.alternative_suggestions,
                    actions: [
                        {
                            text: 'Upgrade Now',
                            action: () => this.navigateToUpgrade(),
                            primary: true
                        },
                        {
                            text: 'Try Alternatives',
                            action: () => this.showAlternativeFeatures(featureId, result.alternative_suggestions),
                            secondary: true
                        },
                        {
                            text: 'Close',
                            action: () => this.closeModal(),
                            secondary: true
                        }
                    ]
                });

                this.showModal(modal);
            }
        });
    }

    showAlternativeFeatures(featureId, alternatives) {
        const modal = this.createModal({
            title: 'Alternative Features',
            message: 'Here are some alternative features you can use with your current plan:',
            type: 'alternatives',
            featureId: featureId,
            alternatives: alternatives,
            actions: [
                {
                    text: 'Explore Alternatives',
                    action: () => this.navigateToAlternatives(alternatives),
                    primary: true
                },
                {
                    text: 'Upgrade Instead',
                    action: () => this.navigateToUpgrade(),
                    secondary: true
                },
                {
                    text: 'Close',
                    action: () => this.closeModal(),
                    secondary: true
                }
            ]
        });

        this.showModal(modal);
    }

    createModal(config) {
        const modal = document.createElement('div');
        modal.className = 'feature-access-modal';
        modal.innerHTML = this.generateModalHTML(config);
        
        // Add event listeners
        this.addModalEventListeners(modal, config);
        
        return modal;
    }

    generateModalHTML(config) {
        const { title, message, type, actions, benefits, price, currentUsage, usageLimits, alternatives } = config;

        let contentHTML = `<p>${message}</p>`;

        // Add benefits list
        if (benefits && benefits.length > 0) {
            contentHTML += `
                <div class="benefits-list">
                    <h4>Benefits:</h4>
                    <ul>
                        ${benefits.map(benefit => `<li>${benefit}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Add usage information
        if (currentUsage && usageLimits) {
            contentHTML += `
                <div class="usage-info">
                    <h4>Current Usage:</h4>
                    <p>You've used ${currentUsage[Object.keys(currentUsage)[0]]} of your monthly limit.</p>
                </div>
            `;
        }

        // Add alternatives
        if (alternatives && alternatives.length > 0) {
            contentHTML += `
                <div class="alternatives-list">
                    <h4>Alternative Features:</h4>
                    <ul>
                        ${alternatives.map(alt => `<li>${alt}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Add price if available
        if (price) {
            contentHTML += `<div class="price-info"><strong>${price}</strong></div>`;
        }

        const actionsHTML = actions.map(action => {
            const buttonClass = action.primary ? 'btn-primary' : 'btn-secondary';
            return `<button class="btn ${buttonClass}" data-action="${action.text.toLowerCase().replace(' ', '_')}">${action.text}</button>`;
        }).join('');

        return `
            <div class="modal-overlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${title}</h3>
                        <button class="modal-close" data-action="close">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${contentHTML}
                    </div>
                    <div class="modal-footer">
                        ${actionsHTML}
                    </div>
                </div>
            </div>
        `;
    }

    addModalEventListeners(modal, config) {
        const { actions } = config;

        // Close button
        modal.querySelector('.modal-close').addEventListener('click', () => {
            this.closeModal();
        });

        // Action buttons
        actions.forEach(action => {
            const button = modal.querySelector(`[data-action="${action.text.toLowerCase().replace(' ', '_')}"]`);
            if (button) {
                button.addEventListener('click', action.action);
            }
        });

        // Overlay click to close
        modal.querySelector('.modal-overlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.closeModal();
            }
        });
    }

    showModal(modal) {
        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';
        
        // Add animation
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }

    closeModal() {
        const modal = document.querySelector('.feature-access-modal');
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(modal);
                document.body.style.overflow = '';
            }, 300);
        }
    }

    navigateToPricing() {
        window.location.href = '/pricing';
    }

    navigateToUpgrade(currentTier = null) {
        const upgradeUrl = currentTier ? `/upgrade?from=${currentTier}` : '/upgrade';
        window.location.href = upgradeUrl;
    }

    navigateToAlternatives(alternatives) {
        // Navigate to a page showing alternative features
        window.location.href = '/features/alternatives';
    }

    showUsageDetails(featureId) {
        window.location.href = `/features/usage/${featureId}`;
    }

    showTrialStatus(featureId) {
        window.location.href = `/features/trial/status/${featureId}`;
    }

    extractFeatureIdFromUrl() {
        const path = window.location.pathname;
        const featurePatterns = [
            /\/health\/checkin/,
            /\/ai\/insights/,
            /\/financial\/reports/,
            /\/career\/risk/,
            /\/data\/export/
        ];

        for (const pattern of featurePatterns) {
            if (pattern.test(path)) {
                return path.split('/')[2]; // Extract feature ID
            }
        }

        return null;
    }

    // Utility method to check feature access before making API calls
    async ensureFeatureAccess(featureId, fallbackAction = null) {
        const accessResult = await this.checkFeatureAccess(featureId);
        
        if (!accessResult.success || !accessResult.has_access) {
            // Dispatch error event
            window.dispatchEvent(new CustomEvent('feature-access-error', {
                detail: accessResult
            }));
            
            // Execute fallback action if provided
            if (fallbackAction && typeof fallbackAction === 'function') {
                fallbackAction(accessResult);
            }
            
            return false;
        }
        
        return true;
    }

    // Method to gracefully degrade feature functionality
    async gracefulDegrade(featureId, fullFunction, degradedFunction) {
        const hasAccess = await this.ensureFeatureAccess(featureId);
        
        if (hasAccess) {
            return fullFunction();
        } else {
            return degradedFunction();
        }
    }
}

// Initialize the feature access manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.featureAccessManager = new FeatureAccessManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FeatureAccessManager;
} 