/**
 * Bank Connection Flow Frontend for MINGUS
 * 
 * This module provides a comprehensive and secure bank connection user experience:
 * - Intuitive step-by-step flow management
 * - Subscription tier integration with upgrade prompts
 * - Plaid Link integration with MFA and verification handling
 * - Progress tracking and analytics
 * - Responsive design with modern UI components
 */

class BankConnectionFlow {
    constructor() {
        this.sessionId = null;
        this.currentStep = null;
        this.currentState = null;
        this.plaidHandler = null;
        this.isInitialized = false;
        this.flowData = {};
        this.upgradePrompt = null;
        
        // Configuration
        this.config = {
            apiBaseUrl: '/api/bank-connection',
            plaidEnv: 'sandbox', // Will be set from backend
            clientName: 'MINGUS',
            products: ['auth', 'transactions', 'identity'],
            countryCodes: ['US'],
            language: 'en'
        };
        
        // Event handlers
        this.eventHandlers = {
            onStepChange: null,
            onStateChange: null,
            onUpgradePrompt: null,
            onSuccess: null,
            onError: null,
            onCancel: null
        };
        
        // UI elements
        this.ui = {
            container: null,
            progressBar: null,
            stepContent: null,
            navigationButtons: null,
            upgradeModal: null,
            loadingOverlay: null,
            errorDisplay: null
        };
        
        this.init();
    }
    
    /**
     * Initialize the bank connection flow
     */
    async init() {
        try {
            // Initialize Plaid
            await this.initializePlaid();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Initialize UI components
            this.initializeUI();
            
            this.isInitialized = true;
            console.log('Bank connection flow initialized successfully');
            
        } catch (error) {
            console.error('Error initializing bank connection flow:', error);
            this.showError('Failed to initialize bank connection flow');
        }
    }
    
    /**
     * Initialize Plaid
     */
    async initializePlaid() {
        try {
            // Load Plaid script if not already loaded
            if (typeof Plaid === 'undefined') {
                await this.loadPlaidScript();
            }
            
            console.log('Plaid initialized successfully');
            
        } catch (error) {
            console.error('Error initializing Plaid:', error);
            throw error;
        }
    }
    
    /**
     * Load Plaid script
     */
    loadPlaidScript() {
        return new Promise((resolve, reject) => {
            if (document.querySelector('script[src*="plaid"]')) {
                resolve();
                return;
            }
            
            const script = document.createElement('script');
            script.src = 'https://cdn.plaid.com/link/v2/stable/link-initialize.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Global event listeners
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="proceed"]')) {
                this.handleProceed();
            } else if (e.target.matches('[data-action="skip-upgrade"]')) {
                this.handleSkipUpgrade();
            } else if (e.target.matches('[data-action="upgrade"]')) {
                this.handleUpgrade();
            } else if (e.target.matches('[data-action="cancel"]')) {
                this.handleCancel();
            } else if (e.target.matches('[data-action="extend-session"]')) {
                this.handleExtendSession();
            }
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.handleCancel();
            } else if (e.key === 'Enter' && e.target.matches('[data-action="proceed"]')) {
                this.handleProceed();
            }
        });
    }
    
    /**
     * Initialize UI components
     */
    initializeUI() {
        // Find or create container
        this.ui.container = document.getElementById('bank-connection-flow') || 
                           this.createContainer();
        
        // Initialize UI elements
        this.ui.progressBar = this.ui.container.querySelector('.progress-bar');
        this.ui.stepContent = this.ui.container.querySelector('.step-content');
        this.ui.navigationButtons = this.ui.container.querySelector('.navigation-buttons');
        this.ui.upgradeModal = this.ui.container.querySelector('.upgrade-modal');
        this.ui.loadingOverlay = this.ui.container.querySelector('.loading-overlay');
        this.ui.errorDisplay = this.ui.container.querySelector('.error-display');
        
        // Create initial UI structure
        this.createUIStructure();
    }
    
    /**
     * Create container if it doesn't exist
     */
    createContainer() {
        const container = document.createElement('div');
        container.id = 'bank-connection-flow';
        container.className = 'bank-connection-flow';
        document.body.appendChild(container);
        return container;
    }
    
    /**
     * Create UI structure
     */
    createUIStructure() {
        this.ui.container.innerHTML = `
            <div class="flow-container">
                <!-- Progress Bar -->
                <div class="progress-section">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-text">
                        <span class="current-step">Step 1 of 6</span>
                        <span class="estimated-time">2-3 minutes remaining</span>
                    </div>
                </div>
                
                <!-- Step Content -->
                <div class="step-content">
                    <!-- Content will be dynamically loaded -->
                </div>
                
                <!-- Navigation Buttons -->
                <div class="navigation-buttons">
                    <button class="btn btn-secondary" data-action="cancel">
                        Cancel
                    </button>
                    <button class="btn btn-primary" data-action="proceed">
                        Continue
                    </button>
                </div>
                
                <!-- Loading Overlay -->
                <div class="loading-overlay" style="display: none;">
                    <div class="loading-spinner"></div>
                    <p>Processing...</p>
                </div>
                
                <!-- Error Display -->
                <div class="error-display" style="display: none;">
                    <div class="error-content">
                        <h3>Something went wrong</h3>
                        <p class="error-message"></p>
                        <button class="btn btn-primary" data-action="retry">Try Again</button>
                    </div>
                </div>
            </div>
            
            <!-- Upgrade Modal -->
            <div class="upgrade-modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2 class="upgrade-title"></h2>
                        <button class="modal-close" data-action="skip-upgrade">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p class="upgrade-message"></p>
                        <div class="upgrade-benefits">
                            <h3>What you'll get:</h3>
                            <ul class="benefits-list"></ul>
                        </div>
                        <div class="trial-info">
                            <p class="trial-text"></p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" data-action="skip-upgrade">
                            Continue with current plan
                        </button>
                        <button class="btn btn-primary" data-action="upgrade">
                            Upgrade Now
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Start the bank connection flow
     */
    async startFlow() {
        try {
            this.showLoading('Starting bank connection...');
            
            const response = await fetch(`${this.config.apiBaseUrl}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.sessionId = data.session_id;
                this.currentStep = data.next_step;
                this.currentState = data.current_state;
                this.flowData = data.data || {};
                this.upgradePrompt = data.upgrade_prompt;
                
                // Update UI
                this.updateProgress();
                this.renderCurrentStep();
                
                // Trigger event
                if (this.eventHandlers.onStepChange) {
                    this.eventHandlers.onStepChange(this.currentStep, this.flowData);
                }
                
                this.hideLoading();
                
            } else {
                throw new Error(data.error || 'Failed to start connection flow');
            }
            
        } catch (error) {
            console.error('Error starting flow:', error);
            this.showError('Failed to start bank connection flow: ' + error.message);
        }
    }
    
    /**
     * Proceed to next step
     */
    async handleProceed() {
        try {
            if (!this.sessionId) {
                throw new Error('No active session');
            }
            
            this.showLoading('Processing...');
            
            const response = await fetch(`${this.config.apiBaseUrl}/${this.sessionId}/proceed`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    step_data: this.getStepData()
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.currentStep = data.next_step;
                this.currentState = data.current_state;
                this.flowData = data.data || {};
                this.upgradePrompt = data.upgrade_prompt;
                
                // Update UI
                this.updateProgress();
                this.renderCurrentStep();
                
                // Handle redirect if needed
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                    return;
                }
                
                // Trigger events
                if (this.eventHandlers.onStepChange) {
                    this.eventHandlers.onStepChange(this.currentStep, this.flowData);
                }
                
                if (this.eventHandlers.onStateChange) {
                    this.eventHandlers.onStateChange(this.currentState);
                }
                
                this.hideLoading();
                
            } else {
                throw new Error(data.error || 'Failed to proceed to next step');
            }
            
        } catch (error) {
            console.error('Error proceeding to next step:', error);
            this.showError('Failed to proceed: ' + error.message);
        }
    }
    
    /**
     * Handle Plaid success
     */
    async handlePlaidSuccess(publicToken, metadata) {
        try {
            if (!this.sessionId) {
                throw new Error('No active session');
            }
            
            this.showLoading('Connecting your bank account...');
            
            const response = await fetch(`${this.config.apiBaseUrl}/${this.sessionId}/plaid-success`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    public_token: publicToken,
                    metadata: metadata
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.currentStep = data.next_step;
                this.currentState = data.current_state;
                this.flowData = data.data || {};
                
                // Update UI
                this.updateProgress();
                this.renderCurrentStep();
                
                // Handle redirect if needed
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                    return;
                }
                
                this.hideLoading();
                
            } else {
                throw new Error(data.error || 'Failed to connect bank account');
            }
            
        } catch (error) {
            console.error('Error handling Plaid success:', error);
            this.showError('Failed to connect bank account: ' + error.message);
        }
    }
    
    /**
     * Handle MFA response
     */
    async handleMFAResponse(mfaAnswers) {
        try {
            if (!this.sessionId) {
                throw new Error('No active session');
            }
            
            this.showLoading('Verifying your identity...');
            
            const response = await fetch(`${this.config.apiBaseUrl}/${this.sessionId}/mfa-response`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    mfa_answers: mfaAnswers
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.currentStep = data.next_step;
                this.currentState = data.current_state;
                this.flowData = data.data || {};
                
                // Update UI
                this.updateProgress();
                this.renderCurrentStep();
                
                this.hideLoading();
                
            } else {
                throw new Error(data.error || 'Failed to verify identity');
            }
            
        } catch (error) {
            console.error('Error handling MFA response:', error);
            this.showError('Failed to verify identity: ' + error.message);
        }
    }
    
    /**
     * Handle upgrade request
     */
    async handleUpgrade() {
        try {
            if (!this.sessionId) {
                throw new Error('No active session');
            }
            
            this.showLoading('Processing upgrade...');
            
            const response = await fetch(`${this.config.apiBaseUrl}/${this.sessionId}/upgrade`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    upgrade_tier: this.upgradePrompt?.upgrade_tier || 'mid_tier',
                    start_trial: true
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                throw new Error(data.error || 'Failed to process upgrade');
            }
            
        } catch (error) {
            console.error('Error handling upgrade:', error);
            this.showError('Failed to process upgrade: ' + error.message);
        }
    }
    
    /**
     * Handle skip upgrade
     */
    async handleSkipUpgrade() {
        try {
            if (!this.sessionId) {
                throw new Error('No active session');
            }
            
            this.showLoading('Continuing with current plan...');
            
            const response = await fetch(`${this.config.apiBaseUrl}/${this.sessionId}/skip-upgrade`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.currentStep = data.next_step;
                this.currentState = data.current_state;
                this.flowData = data.data || {};
                
                // Update UI
                this.updateProgress();
                this.renderCurrentStep();
                
                this.hideLoading();
                
            } else {
                throw new Error(data.error || 'Failed to skip upgrade');
            }
            
        } catch (error) {
            console.error('Error skipping upgrade:', error);
            this.showError('Failed to skip upgrade: ' + error.message);
        }
    }
    
    /**
     * Handle cancel
     */
    async handleCancel() {
        try {
            if (!this.sessionId) {
                this.cleanup();
                return;
            }
            
            const confirmed = confirm('Are you sure you want to cancel the bank connection? Your progress will be lost.');
            if (!confirmed) {
                return;
            }
            
            this.showLoading('Cancelling...');
            
            const response = await fetch(`${this.config.apiBaseUrl}/${this.sessionId}/cancel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    this.cleanup();
                }
            } else {
                this.cleanup();
            }
            
        } catch (error) {
            console.error('Error cancelling flow:', error);
            this.cleanup();
        }
    }
    
    /**
     * Handle extend session
     */
    async handleExtendSession() {
        try {
            if (!this.sessionId) {
                return;
            }
            
            const response = await fetch(`${this.config.apiBaseUrl}/${this.sessionId}/extend`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    console.log('Session extended successfully');
                }
            }
            
        } catch (error) {
            console.error('Error extending session:', error);
        }
    }
    
    /**
     * Render current step
     */
    renderCurrentStep() {
        if (!this.ui.stepContent) {
            return;
        }
        
        let content = '';
        
        switch (this.currentStep) {
            case 'welcome':
                content = this.renderWelcomeStep();
                break;
            case 'tier_upgrade':
                content = this.renderTierUpgradeStep();
                break;
            case 'security_info':
                content = this.renderSecurityInfoStep();
                break;
            case 'bank_selection':
                content = this.renderBankSelectionStep();
                break;
            case 'account_linking':
                content = this.renderAccountLinkingStep();
                break;
            case 'mfa_processing':
                content = this.renderMFAProcessingStep();
                break;
            case 'verification':
                content = this.renderVerificationStep();
                break;
            case 'success':
                content = this.renderSuccessStep();
                break;
            default:
                content = this.renderErrorStep('Unknown step: ' + this.currentStep);
        }
        
        this.ui.stepContent.innerHTML = content;
        this.updateNavigationButtons();
    }
    
    /**
     * Render welcome step
     */
    renderWelcomeStep() {
        return `
            <div class="step-welcome">
                <div class="welcome-header">
                    <h1>Welcome to Secure Bank Connection</h1>
                    <p>Connect your bank accounts to unlock powerful financial insights and take control of your financial future.</p>
                </div>
                
                <div class="welcome-benefits">
                    <h2>What you'll get:</h2>
                    <ul>
                        <li>🔒 Bank-level security for your data</li>
                        <li>📊 Automatic transaction categorization</li>
                        <li>💰 Real-time balance monitoring</li>
                        <li>📈 Spending pattern analysis</li>
                        <li>🎯 Budget tracking and alerts</li>
                        <li>📋 Financial goal progress tracking</li>
                    </ul>
                </div>
                
                <div class="security-highlight">
                    <div class="security-icon">🔐</div>
                    <div class="security-text">
                        <h3>Your Security is Our Priority</h3>
                        <p>We use bank-level encryption and never store your login credentials. Your data is protected with the same security standards as major financial institutions.</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Render tier upgrade step
     */
    renderTierUpgradeStep() {
        if (!this.upgradePrompt) {
            return this.renderErrorStep('No upgrade prompt available');
        }
        
        return `
            <div class="step-upgrade">
                <div class="upgrade-header">
                    <h1>${this.upgradePrompt.title || 'Upgrade Your Plan'}</h1>
                    <p>${this.upgradePrompt.message || 'To connect your bank accounts, you\'ll need to upgrade your plan.'}</p>
                </div>
                
                <div class="upgrade-benefits">
                    <h2>What you'll get with ${this.upgradePrompt.recommended_tier}:</h2>
                    <ul>
                        ${(this.upgradePrompt.benefits || []).map(benefit => `<li>✅ ${benefit}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="upgrade-pricing">
                    <div class="price-display">
                        <span class="price">$${this.upgradePrompt.upgrade_price || '19.99'}</span>
                        <span class="period">/month</span>
                    </div>
                    ${this.upgradePrompt.trial_available ? `
                        <div class="trial-offer">
                            <span class="trial-badge">7-Day Free Trial</span>
                            <p>Try all features free for 7 days, cancel anytime</p>
                        </div>
                    ` : ''}
                </div>
                
                <div class="upgrade-actions">
                    <button class="btn btn-secondary" data-action="skip-upgrade">
                        Continue with current plan
                    </button>
                    <button class="btn btn-primary" data-action="upgrade">
                        Start Free Trial
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Render security info step
     */
    renderSecurityInfoStep() {
        const securityInfo = this.flowData.security_info || {};
        
        return `
            <div class="step-security">
                <div class="security-header">
                    <h1>${securityInfo.title || 'Bank-Level Security'}</h1>
                    <p>${securityInfo.description || 'Your financial data is protected with bank-level encryption and security measures.'}</p>
                </div>
                
                <div class="security-features">
                    ${(securityInfo.features || []).map(feature => `
                        <div class="security-feature">
                            <div class="feature-icon">🔒</div>
                            <div class="feature-text">${feature}</div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="privacy-info">
                    <h3>Privacy & Data Usage</h3>
                    <p>${this.flowData.privacy_policy || 'We only access the data you authorize and never share your personal information with third parties.'}</p>
                    <p>${this.flowData.data_usage || 'We use your financial data to provide personalized insights and recommendations to help you achieve your financial goals.'}</p>
                </div>
            </div>
        `;
    }
    
    /**
     * Render bank selection step
     */
    renderBankSelectionStep() {
        const supportedBanks = this.flowData.supported_banks || [];
        const searchTips = this.flowData.search_tips || [];
        
        return `
            <div class="step-bank-selection">
                <div class="selection-header">
                    <h1>Select Your Bank</h1>
                    <p>Search for your bank to get started with secure account linking.</p>
                </div>
                
                <div class="bank-search">
                    <div class="search-input">
                        <input type="text" id="bank-search" placeholder="Search for your bank..." />
                        <button class="search-btn">🔍</button>
                    </div>
                </div>
                
                <div class="popular-banks">
                    <h3>Popular Banks</h3>
                    <div class="bank-grid">
                        ${supportedBanks.slice(0, 6).map(bank => `
                            <div class="bank-item" data-bank="${bank}">
                                <div class="bank-logo">🏦</div>
                                <div class="bank-name">${bank}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="search-tips">
                    <h3>Search Tips</h3>
                    <ul>
                        ${searchTips.map(tip => `<li>💡 ${tip}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    /**
     * Render account linking step
     */
    renderAccountLinkingStep() {
        const plaidConfig = this.flowData.plaid_config || {};
        
        return `
            <div class="step-account-linking">
                <div class="linking-header">
                    <h1>Connect Your Bank Account</h1>
                    <p>You'll be redirected to your bank's secure login page to authorize the connection.</p>
                </div>
                
                <div class="plaid-container">
                    <div id="plaid-link-container">
                        <!-- Plaid Link will be rendered here -->
                    </div>
                </div>
                
                <div class="linking-info">
                    <div class="info-item">
                        <div class="info-icon">🔒</div>
                        <div class="info-text">
                            <h3>Secure Connection</h3>
                            <p>Your bank credentials are never stored by MINGUS. We use Plaid's secure infrastructure to connect to your bank.</p>
                        </div>
                    </div>
                    
                    <div class="info-item">
                        <div class="info-icon">📊</div>
                        <div class="info-text">
                            <h3>Read-Only Access</h3>
                            <p>We only request read-only access to your account information. We cannot make any transactions on your behalf.</p>
                        </div>
                    </div>
                    
                    <div class="info-item">
                        <div class="info-icon">⚡</div>
                        <div class="info-text">
                            <h3>Quick Setup</h3>
                            <p>The connection process typically takes 2-3 minutes and only needs to be done once per bank account.</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Render MFA processing step
     */
    renderMFAProcessingStep() {
        const mfaQuestions = this.flowData.mfa_questions || [];
        const instructions = this.flowData.mfa_instructions || '';
        
        return `
            <div class="step-mfa">
                <div class="mfa-header">
                    <h1>Additional Verification Required</h1>
                    <p>${instructions}</p>
                </div>
                
                <div class="mfa-form">
                    <form id="mfa-form">
                        ${mfaQuestions.map((question, index) => `
                            <div class="mfa-question">
                                <label for="mfa-answer-${index}">${question.question || question.text}</label>
                                <input type="text" id="mfa-answer-${index}" name="mfa-answer-${index}" 
                                       placeholder="Enter your answer" required />
                            </div>
                        `).join('')}
                        
                        <button type="submit" class="btn btn-primary">Verify</button>
                    </form>
                </div>
            </div>
        `;
    }
    
    /**
     * Render verification step
     */
    renderVerificationStep() {
        const verificationType = this.flowData.verification_type || 'standard';
        const instructions = this.flowData.verification_instructions || '';
        
        return `
            <div class="step-verification">
                <div class="verification-header">
                    <h1>Account Verification</h1>
                    <p>${instructions}</p>
                </div>
                
                <div class="verification-content">
                    <div class="verification-type">
                        <h3>Verification Type: ${verificationType}</h3>
                        <p>Please complete the verification process to secure your connection.</p>
                    </div>
                    
                    <div class="verification-form">
                        <!-- Verification form will be rendered based on type -->
                        <p>Verification form will be displayed here based on the required verification type.</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Render success step
     */
    renderSuccessStep() {
        const successMessage = this.flowData.success_message || 'Bank account connected successfully!';
        const nextSteps = this.flowData.next_steps || [];
        
        return `
            <div class="step-success">
                <div class="success-header">
                    <div class="success-icon">🎉</div>
                    <h1>Connection Successful!</h1>
                    <p>${successMessage}</p>
                </div>
                
                <div class="success-details">
                    <div class="connection-info">
                        <h3>Connection Details</h3>
                        <p><strong>Bank:</strong> ${this.flowData.institution_name || 'Unknown'}</p>
                        <p><strong>Accounts:</strong> ${this.flowData.accounts_count || 0} connected</p>
                        <p><strong>Status:</strong> <span class="status-active">Active</span></p>
                    </div>
                </div>
                
                <div class="next-steps">
                    <h3>What's Next?</h3>
                    <ul>
                        ${nextSteps.map(step => `<li>✅ ${step}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="success-actions">
                    <button class="btn btn-primary" onclick="window.location.href='/dashboard/banking'">
                        Go to Dashboard
                    </button>
                    <button class="btn btn-secondary" onclick="window.location.href='/dashboard'">
                        Continue Setup
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Render error step
     */
    renderErrorStep(message) {
        return `
            <div class="step-error">
                <div class="error-header">
                    <div class="error-icon">❌</div>
                    <h1>Something went wrong</h1>
                    <p>${message}</p>
                </div>
                
                <div class="error-actions">
                    <button class="btn btn-primary" data-action="retry">
                        Try Again
                    </button>
                    <button class="btn btn-secondary" data-action="cancel">
                        Cancel
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Update progress bar
     */
    updateProgress() {
        if (!this.ui.progressBar) {
            return;
        }
        
        // Get progress from backend
        this.getProgress().then(progress => {
            if (progress && this.ui.progressBar) {
                const progressFill = this.ui.progressBar.querySelector('.progress-fill');
                const currentStep = this.ui.progressBar.querySelector('.current-step');
                const estimatedTime = this.ui.progressBar.querySelector('.estimated-time');
                
                if (progressFill) {
                    progressFill.style.width = `${progress.progress_percentage || 0}%`;
                }
                
                if (currentStep) {
                    currentStep.textContent = `Step ${progress.steps_completed || 1} of ${progress.total_steps || 6}`;
                }
                
                if (estimatedTime) {
                    estimatedTime.textContent = progress.estimated_time_remaining || '2-3 minutes remaining';
                }
            }
        });
    }
    
    /**
     * Get progress from backend
     */
    async getProgress() {
        try {
            if (!this.sessionId) {
                return null;
            }
            
            const response = await fetch(`${this.config.apiBaseUrl}/${this.sessionId}/progress`);
            if (response.ok) {
                const data = await response.json();
                return data.success ? data.progress : null;
            }
        } catch (error) {
            console.error('Error getting progress:', error);
        }
        return null;
    }
    
    /**
     * Update navigation buttons
     */
    updateNavigationButtons() {
        if (!this.ui.navigationButtons) {
            return;
        }
        
        const proceedBtn = this.ui.navigationButtons.querySelector('[data-action="proceed"]');
        const cancelBtn = this.ui.navigationButtons.querySelector('[data-action="cancel"]');
        
        if (proceedBtn) {
            // Hide proceed button for certain steps
            const hideProceedSteps = ['account_linking', 'success'];
            if (hideProceedSteps.includes(this.currentStep)) {
                proceedBtn.style.display = 'none';
            } else {
                proceedBtn.style.display = 'block';
                proceedBtn.textContent = this.getProceedButtonText();
            }
        }
        
        if (cancelBtn) {
            // Show cancel button for all steps except success
            cancelBtn.style.display = this.currentStep === 'success' ? 'none' : 'block';
        }
    }
    
    /**
     * Get proceed button text based on current step
     */
    getProceedButtonText() {
        switch (this.currentStep) {
            case 'welcome':
                return 'Get Started';
            case 'tier_upgrade':
                return 'Continue';
            case 'security_info':
                return 'I Understand';
            case 'bank_selection':
                return 'Continue to Connection';
            case 'mfa_processing':
                return 'Verify';
            case 'verification':
                return 'Complete Verification';
            default:
                return 'Continue';
        }
    }
    
    /**
     * Get step data for form submission
     */
    getStepData() {
        const stepData = {};
        
        // Get form data if available
        const forms = this.ui.container.querySelectorAll('form');
        forms.forEach(form => {
            const formData = new FormData(form);
            for (let [key, value] of formData.entries()) {
                stepData[key] = value;
            }
        });
        
        // Get input data
        const inputs = this.ui.container.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.name && input.value) {
                stepData[input.name] = input.value;
            }
        });
        
        return stepData;
    }
    
    /**
     * Show loading overlay
     */
    showLoading(message = 'Loading...') {
        if (this.ui.loadingOverlay) {
            this.ui.loadingOverlay.querySelector('p').textContent = message;
            this.ui.loadingOverlay.style.display = 'flex';
        }
    }
    
    /**
     * Hide loading overlay
     */
    hideLoading() {
        if (this.ui.loadingOverlay) {
            this.ui.loadingOverlay.style.display = 'none';
        }
    }
    
    /**
     * Show error
     */
    showError(message) {
        if (this.ui.errorDisplay) {
            this.ui.errorDisplay.querySelector('.error-message').textContent = message;
            this.ui.errorDisplay.style.display = 'block';
        }
        
        if (this.eventHandlers.onError) {
            this.eventHandlers.onError(message);
        }
    }
    
    /**
     * Hide error
     */
    hideError() {
        if (this.ui.errorDisplay) {
            this.ui.errorDisplay.style.display = 'none';
        }
    }
    
    /**
     * Set event handler
     */
    on(event, handler) {
        if (this.eventHandlers.hasOwnProperty(event)) {
            this.eventHandlers[event] = handler;
        }
    }
    
    /**
     * Cleanup resources
     */
    cleanup() {
        // Remove event listeners
        document.removeEventListener('click', this.handleClick);
        document.removeEventListener('keydown', this.handleKeydown);
        
        // Remove container
        if (this.ui.container && this.ui.container.parentNode) {
            this.ui.container.parentNode.removeChild(this.ui.container);
        }
        
        // Reset state
        this.sessionId = null;
        this.currentStep = null;
        this.currentState = null;
        this.isInitialized = false;
        
        if (this.eventHandlers.onCancel) {
            this.eventHandlers.onCancel();
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BankConnectionFlow;
} else if (typeof window !== 'undefined') {
    window.BankConnectionFlow = BankConnectionFlow;
} 