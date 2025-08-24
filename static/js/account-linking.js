/**
 * Account Linking Frontend JavaScript for MINGUS
 * 
 * This module handles the complete account linking workflow:
 * - Plaid Link integration for account selection
 * - Multi-factor authentication handling
 * - Institution credential verification
 * - Account ownership verification
 * - Connection success confirmation
 */

class AccountLinkingManager {
    constructor() {
        this.currentSession = null;
        this.plaidHandler = null;
        this.currentStep = 'initiation';
        this.mfaSession = null;
        this.verificationSession = null;
        this.institutionSearchResults = [];
        
        // UI elements
        this.modal = null;
        this.stepContainer = null;
        this.progressBar = null;
        this.statusIndicator = null;
        
        // Configuration
        this.apiBaseUrl = '/api/account-linking';
        this.plaidEnv = window.PLAID_ENV || 'sandbox';
        this.maxRetries = 3;
        this.retryDelay = 2000;
        
        // Event handlers
        this.onSuccess = null;
        this.onError = null;
        this.onProgress = null;
        
        this.init();
    }
    
    init() {
        this.createModal();
        this.bindEvents();
        this.loadPlaidScript();
    }
    
    /**
     * Create the account linking modal
     */
    createModal() {
        const modalHtml = `
            <div id="account-linking-modal" class="account-linking-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Link Your Bank Account</h2>
                        <button class="close-btn" id="close-linking-modal">&times;</button>
                    </div>
                    
                    <div class="modal-body">
                        <!-- Progress Bar -->
                        <div class="progress-container">
                            <div class="progress-bar" id="linking-progress-bar">
                                <div class="progress-fill"></div>
                            </div>
                            <div class="progress-steps">
                                <div class="step active" data-step="initiation">
                                    <div class="step-icon">1</div>
                                    <div class="step-label">Start</div>
                                </div>
                                <div class="step" data-step="selection">
                                    <div class="step-icon">2</div>
                                    <div class="step-label">Select Accounts</div>
                                </div>
                                <div class="step" data-step="verification">
                                    <div class="step-icon">3</div>
                                    <div class="step-label">Verify</div>
                                </div>
                                <div class="step" data-step="completion">
                                    <div class="step-icon">4</div>
                                    <div class="step-label">Complete</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Status Indicator -->
                        <div class="status-indicator" id="linking-status-indicator">
                            <div class="status-icon"></div>
                            <div class="status-message">Initializing account linking...</div>
                        </div>
                        
                        <!-- Step Container -->
                        <div class="step-container" id="linking-step-container">
                            <!-- Steps will be dynamically loaded here -->
                        </div>
                    </div>
                    
                    <div class="modal-footer">
                        <button class="btn btn-secondary" id="cancel-linking">Cancel</button>
                        <button class="btn btn-primary" id="continue-linking" style="display: none;">Continue</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        this.modal = document.getElementById('account-linking-modal');
        this.stepContainer = document.getElementById('linking-step-container');
        this.progressBar = document.getElementById('linking-progress-bar');
        this.statusIndicator = document.getElementById('linking-status-indicator');
    }
    
    /**
     * Bind event handlers
     */
    bindEvents() {
        // Close modal
        document.getElementById('close-linking-modal').addEventListener('click', () => {
            this.closeModal();
        });
        
        // Cancel linking
        document.getElementById('cancel-linking').addEventListener('click', () => {
            this.cancelLinking();
        });
        
        // Continue button
        document.getElementById('continue-linking').addEventListener('click', () => {
            this.handleContinue();
        });
        
        // Modal backdrop click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
        
        // Keyboard events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('active')) {
                this.closeModal();
            }
        });
    }
    
    /**
     * Load Plaid script
     */
    loadPlaidScript() {
        if (window.Plaid) {
            this.initializePlaid();
            return;
        }
        
        const script = document.createElement('script');
        script.src = `https://cdn.plaid.com/link/v2/stable/link-initialize.js`;
        script.onload = () => {
            this.initializePlaid();
        };
        script.onerror = () => {
            this.showError('Failed to load Plaid script');
        };
        document.head.appendChild(script);
    }
    
    /**
     * Initialize Plaid
     */
    initializePlaid() {
        try {
            this.plaidHandler = Plaid.create({
                env: this.plaidEnv,
                clientName: 'MINGUS',
                products: ['transactions', 'auth', 'identity'],
                countryCodes: ['US'],
                language: 'en',
                onSuccess: (public_token, metadata) => {
                    this.handlePlaidSuccess(public_token, metadata);
                },
                onExit: (err, metadata) => {
                    this.handlePlaidExit(err, metadata);
                },
                onEvent: (eventName, metadata) => {
                    this.handlePlaidEvent(eventName, metadata);
                }
            });
        } catch (error) {
            console.error('Error initializing Plaid:', error);
            this.showError('Failed to initialize Plaid');
        }
    }
    
    /**
     * Start account linking process
     */
    async startLinking(institutionId = null) {
        try {
            this.showModal();
            this.updateStatus('Initializing account linking...', 'loading');
            this.updateProgress(0);
            
            // Initiate linking session
            const response = await this.apiCall('POST', '/initiate', {
                institution_id: institutionId
            });
            
            if (!response.success) {
                if (response.error === 'upgrade_required') {
                    this.showUpgradePrompt(response.upgrade_prompt);
                } else if (response.error === 'limit_reached') {
                    this.showLimitReachedPrompt(response);
                } else if (response.error === 'account_limit_exceeded') {
                    this.showAccountLimitExceededPrompt(response);
                } else {
                    this.showError(response.message || 'Failed to start account linking');
                }
                return;
            }
            
            this.currentSession = {
                sessionId: response.session_id,
                linkToken: response.link_token,
                expiresAt: response.expires_at,
                status: response.status,
                tierInfo: response.tier_info
            };
            
            this.updateStatus('Ready to connect your bank account', 'success');
            this.updateProgress(25);
            this.showInstitutionSelection();
            
        } catch (error) {
            console.error('Error starting account linking:', error);
            this.showError('Failed to start account linking process');
        }
    }
    
    /**
     * Show institution selection step
     */
    showInstitutionSelection() {
        const stepHtml = `
            <div class="linking-step" id="institution-selection-step">
                <div class="step-content">
                    <h3>Connect Your Bank Account</h3>
                    <p>Choose your bank or credit union to securely connect your accounts.</p>
                    
                    <div class="institution-search">
                        <div class="search-input">
                            <input type="text" id="institution-search" placeholder="Search for your bank...">
                            <button class="search-btn" id="search-institutions">Search</button>
                        </div>
                        
                        <div class="search-results" id="institution-results">
                            <!-- Search results will be populated here -->
                        </div>
                    </div>
                    
                    <div class="popular-institutions">
                        <h4>Popular Banks</h4>
                        <div class="institution-grid">
                            <div class="institution-card" data-institution="chase">
                                <img src="/static/images/banks/chase.png" alt="Chase">
                                <span>Chase</span>
                            </div>
                            <div class="institution-card" data-institution="bankofamerica">
                                <img src="/static/images/banks/bankofamerica.png" alt="Bank of America">
                                <span>Bank of America</span>
                            </div>
                            <div class="institution-card" data-institution="wellsfargo">
                                <img src="/static/images/banks/wellsfargo.png" alt="Wells Fargo">
                                <span>Wells Fargo</span>
                            </div>
                            <div class="institution-card" data-institution="citibank">
                                <img src="/static/images/banks/citibank.png" alt="Citibank">
                                <span>Citibank</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="manual-connect">
                        <p>Can't find your bank?</p>
                        <button class="btn btn-outline" id="manual-connect">Connect Manually</button>
                    </div>
                </div>
            </div>
        `;
        
        this.stepContainer.innerHTML = stepHtml;
        this.bindInstitutionSelectionEvents();
        this.updateStep('selection');
    }
    
    /**
     * Bind institution selection events
     */
    bindInstitutionSelectionEvents() {
        // Search functionality
        const searchInput = document.getElementById('institution-search');
        const searchBtn = document.getElementById('search-institutions');
        
        searchBtn.addEventListener('click', () => {
            this.searchInstitutions(searchInput.value);
        });
        
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchInstitutions(searchInput.value);
            }
        });
        
        // Popular institutions
        document.querySelectorAll('.institution-card').forEach(card => {
            card.addEventListener('click', () => {
                const institutionId = card.dataset.institution;
                this.connectInstitution(institutionId);
            });
        });
        
        // Manual connect
        document.getElementById('manual-connect').addEventListener('click', () => {
            this.openPlaidLink();
        });
    }
    
    /**
     * Search for institutions
     */
    async searchInstitutions(query) {
        if (!query.trim()) return;
        
        try {
            this.updateStatus('Searching for institutions...', 'loading');
            
            const response = await this.apiCall('GET', `/institutions/search?query=${encodeURIComponent(query)}`);
            
            if (!response.success) {
                this.showError('Failed to search institutions');
                return;
            }
            
            this.displayInstitutionResults(response.institutions);
            this.updateStatus('Institutions found', 'success');
            
        } catch (error) {
            console.error('Error searching institutions:', error);
            this.showError('Failed to search institutions');
        }
    }
    
    /**
     * Display institution search results
     */
    displayInstitutionResults(institutions) {
        const resultsContainer = document.getElementById('institution-results');
        
        if (!institutions || institutions.length === 0) {
            resultsContainer.innerHTML = '<p class="no-results">No institutions found. Try a different search term.</p>';
            return;
        }
        
        const resultsHtml = institutions.map(institution => `
            <div class="institution-result" data-institution-id="${institution.institution_id}">
                <div class="institution-info">
                    <img src="${institution.logo || '/static/images/banks/default.png'}" alt="${institution.name}">
                    <div class="institution-details">
                        <h4>${institution.name}</h4>
                        <p>${institution.products.join(', ')}</p>
                    </div>
                </div>
                <button class="connect-btn">Connect</button>
            </div>
        `).join('');
        
        resultsContainer.innerHTML = resultsHtml;
        
        // Bind connect events
        document.querySelectorAll('.institution-result').forEach(result => {
            result.addEventListener('click', () => {
                const institutionId = result.dataset.institutionId;
                this.connectInstitution(institutionId);
            });
        });
    }
    
    /**
     * Connect to specific institution
     */
    async connectInstitution(institutionId) {
        try {
            this.updateStatus('Connecting to your bank...', 'loading');
            
            // Start linking with specific institution
            await this.startLinking(institutionId);
            
            // Open Plaid Link
            this.openPlaidLink();
            
        } catch (error) {
            console.error('Error connecting to institution:', error);
            this.showError('Failed to connect to institution');
        }
    }
    
    /**
     * Open Plaid Link
     */
    openPlaidLink() {
        if (!this.plaidHandler || !this.currentSession?.linkToken) {
            this.showError('Plaid not initialized or link token missing');
            return;
        }
        
        try {
            this.plaidHandler.open();
        } catch (error) {
            console.error('Error opening Plaid Link:', error);
            this.showError('Failed to open bank selection');
        }
    }
    
    /**
     * Handle Plaid success
     */
    async handlePlaidSuccess(publicToken, metadata) {
        try {
            this.updateStatus('Processing your account selection...', 'loading');
            this.updateProgress(50);
            
            const response = await this.apiCall('POST', '/accounts/select', {
                session_id: this.currentSession.sessionId,
                public_token: publicToken,
                account_ids: metadata.accounts.map(acc => acc.id)
            });
            
            if (!response.success) {
                this.showError(response.message || 'Failed to process account selection');
                return;
            }
            
            this.currentSession.status = response.status;
            
            if (response.mfa_required) {
                this.handleMFARequired(response);
            } else if (response.verification_required) {
                this.handleVerificationRequired(response);
            } else {
                this.handleLinkingComplete(response);
            }
            
        } catch (error) {
            console.error('Error handling Plaid success:', error);
            this.showError('Failed to process account selection');
        }
    }
    
    /**
     * Handle Plaid exit
     */
    handlePlaidExit(err, metadata) {
        if (err) {
            console.error('Plaid exit error:', err);
            this.showError('Bank connection was cancelled or failed');
        } else {
            this.updateStatus('Bank selection cancelled', 'info');
        }
    }
    
    /**
     * Handle Plaid events
     */
    handlePlaidEvent(eventName, metadata) {
        console.log('Plaid event:', eventName, metadata);
        
        switch (eventName) {
            case 'OPEN':
                this.updateStatus('Select your bank accounts...', 'info');
                break;
            case 'SELECT_INSTITUTION':
                this.updateStatus('Connecting to your bank...', 'loading');
                break;
            case 'SELECT_ACCOUNT':
                this.updateStatus('Processing account selection...', 'loading');
                break;
            case 'SUBMIT_CREDENTIALS':
                this.updateStatus('Verifying credentials...', 'loading');
                break;
            case 'ERROR':
                this.showError('An error occurred during bank connection');
                break;
        }
    }
    
    /**
     * Handle MFA required
     */
    handleMFARequired(response) {
        this.mfaSession = {
            sessionId: response.mfa_session_id,
            type: response.mfa_type,
            questions: response.questions,
            expiresAt: response.expires_at
        };
        
        this.showMFAStep();
        this.updateProgress(60);
    }
    
    /**
     * Show MFA step
     */
    showMFAStep() {
        const stepHtml = `
            <div class="linking-step" id="mfa-step">
                <div class="step-content">
                    <h3>Additional Verification Required</h3>
                    <p>Your bank requires additional verification to complete the connection.</p>
                    
                    <div class="mfa-form">
                        <div class="mfa-type">
                            <span class="mfa-label">Verification Type:</span>
                            <span class="mfa-value">${this.getMFATypeLabel(this.mfaSession.type)}</span>
                        </div>
                        
                        <div class="mfa-questions">
                            ${this.mfaSession.questions.map((question, index) => `
                                <div class="mfa-question">
                                    <label for="mfa-answer-${index}">${question.question}</label>
                                    <input type="text" id="mfa-answer-${index}" 
                                           data-field="${question.field}" 
                                           placeholder="Enter your answer">
                                </div>
                            `).join('')}
                        </div>
                        
                        <div class="mfa-actions">
                            <button class="btn btn-outline" id="resend-mfa">Resend</button>
                            <button class="btn btn-primary" id="submit-mfa">Submit</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.stepContainer.innerHTML = stepHtml;
        this.bindMFAEvents();
        this.updateStep('verification');
        this.showContinueButton();
    }
    
    /**
     * Bind MFA events
     */
    bindMFAEvents() {
        document.getElementById('submit-mfa').addEventListener('click', () => {
            this.submitMFA();
        });
        
        document.getElementById('resend-mfa').addEventListener('click', () => {
            this.resendMFA();
        });
    }
    
    /**
     * Submit MFA answers
     */
    async submitMFA() {
        try {
            const answers = [];
            this.mfaSession.questions.forEach((question, index) => {
                const input = document.getElementById(`mfa-answer-${index}`);
                answers.push(input.value.trim());
            });
            
            if (answers.some(answer => !answer)) {
                this.showError('Please answer all questions');
                return;
            }
            
            this.updateStatus('Verifying your answers...', 'loading');
            
            const response = await this.apiCall('POST', '/mfa/challenge', {
                mfa_session_id: this.mfaSession.sessionId,
                answers: answers
            });
            
            if (!response.success) {
                if (response.error === 'mfa_incorrect') {
                    this.showError(response.message);
                } else {
                    this.showError(response.message || 'MFA verification failed');
                }
                return;
            }
            
            this.currentSession.status = response.status;
            
            if (response.verification_required) {
                this.handleVerificationRequired(response);
            } else {
                this.handleLinkingComplete(response);
            }
            
        } catch (error) {
            console.error('Error submitting MFA:', error);
            this.showError('Failed to submit MFA answers');
        }
    }
    
    /**
     * Resend MFA
     */
    async resendMFA() {
        try {
            this.updateStatus('Resending verification...', 'loading');
            
            const response = await this.apiCall('POST', '/mfa/resend', {
                mfa_session_id: this.mfaSession.sessionId
            });
            
            if (!response.success) {
                this.showError('Failed to resend verification');
                return;
            }
            
            this.updateStatus('Verification resent successfully', 'success');
            
        } catch (error) {
            console.error('Error resending MFA:', error);
            this.showError('Failed to resend verification');
        }
    }
    
    /**
     * Handle verification required
     */
    handleVerificationRequired(response) {
        this.verificationSession = {
            sessionId: response.verification_session_id,
            method: response.verification_method,
            microDeposits: response.micro_deposits,
            expiresAt: response.expires_at
        };
        
        this.showVerificationStep();
        this.updateProgress(75);
    }
    
    /**
     * Show verification step
     */
    showVerificationStep() {
        let stepHtml = `
            <div class="linking-step" id="verification-step">
                <div class="step-content">
                    <h3>Verify Account Ownership</h3>
                    <p>To complete the connection, we need to verify that you own this account.</p>
        `;
        
        if (this.verificationSession.method === 'micro_deposits') {
            stepHtml += `
                <div class="verification-form">
                    <div class="verification-method">
                        <span class="method-label">Verification Method:</span>
                        <span class="method-value">Micro-deposits</span>
                    </div>
                    
                    <div class="micro-deposits-info">
                        <p>We've sent two small deposits to your account. Please enter the amounts below:</p>
                        <div class="deposit-amounts">
                            ${this.verificationSession.microDeposits.map((deposit, index) => `
                                <div class="deposit-input">
                                    <label for="deposit-${index}">Deposit ${index + 1}</label>
                                    <input type="number" id="deposit-${index}" 
                                           step="0.01" min="0" 
                                           placeholder="0.00">
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="verification-actions">
                        <button class="btn btn-outline" id="resend-verification">Resend Deposits</button>
                        <button class="btn btn-primary" id="submit-verification">Verify</button>
                    </div>
                </div>
            `;
        } else {
            stepHtml += `
                <div class="verification-form">
                    <p>Additional verification is required. Please follow the instructions provided by your bank.</p>
                </div>
            `;
        }
        
        stepHtml += `
                </div>
            </div>
        `;
        
        this.stepContainer.innerHTML = stepHtml;
        this.bindVerificationEvents();
        this.updateStep('verification');
        this.showContinueButton();
    }
    
    /**
     * Bind verification events
     */
    bindVerificationEvents() {
        const submitBtn = document.getElementById('submit-verification');
        const resendBtn = document.getElementById('resend-verification');
        
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                this.submitVerification();
            });
        }
        
        if (resendBtn) {
            resendBtn.addEventListener('click', () => {
                this.resendVerification();
            });
        }
    }
    
    /**
     * Submit verification
     */
    async submitVerification() {
        try {
            if (this.verificationSession.method === 'micro_deposits') {
                const amounts = [];
                this.verificationSession.microDeposits.forEach((deposit, index) => {
                    const input = document.getElementById(`deposit-${index}`);
                    const amount = parseFloat(input.value);
                    if (isNaN(amount)) {
                        this.showError('Please enter valid deposit amounts');
                        return;
                    }
                    amounts.push(amount);
                });
                
                this.updateStatus('Verifying deposit amounts...', 'loading');
                
                const response = await this.apiCall('POST', '/verification/submit', {
                    verification_session_id: this.verificationSession.sessionId,
                    verification_data: { amounts: amounts }
                });
                
                if (!response.success) {
                    if (response.error === 'verification_incorrect') {
                        this.showError(response.message);
                    } else {
                        this.showError(response.message || 'Verification failed');
                    }
                    return;
                }
                
                this.handleLinkingComplete(response);
            }
            
        } catch (error) {
            console.error('Error submitting verification:', error);
            this.showError('Failed to submit verification');
        }
    }
    
    /**
     * Resend verification
     */
    async resendVerification() {
        try {
            this.updateStatus('Resending verification...', 'loading');
            
            const response = await this.apiCall('POST', '/verification/resend', {
                verification_session_id: this.verificationSession.sessionId
            });
            
            if (!response.success) {
                this.showError('Failed to resend verification');
                return;
            }
            
            this.verificationSession.microDeposits = response.micro_deposits;
            this.updateStatus('Verification resent successfully', 'success');
            
        } catch (error) {
            console.error('Error resending verification:', error);
            this.showError('Failed to resend verification');
        }
    }
    
    /**
     * Handle linking completion
     */
    handleLinkingComplete(response) {
        this.updateStatus('Account linking completed successfully!', 'success');
        this.updateProgress(100);
        this.updateStep('completion');
        
        this.showCompletionStep(response);
        
        // Trigger success callback
        if (this.onSuccess) {
            this.onSuccess(response);
        }
    }
    
    /**
     * Show completion step
     */
    showCompletionStep(response) {
        const stepHtml = `
            <div class="linking-step" id="completion-step">
                <div class="step-content">
                    <div class="completion-success">
                        <div class="success-icon">✓</div>
                        <h3>Account Successfully Linked!</h3>
                        <p>Your ${response.institution_name} account has been connected to MINGUS.</p>
                    </div>
                    
                    <div class="linked-accounts">
                        <h4>Linked Accounts (${response.accounts_linked})</h4>
                        <div class="account-list">
                            ${response.account_details.map(account => `
                                <div class="account-item">
                                    <div class="account-info">
                                        <span class="account-name">${account.name}</span>
                                        <span class="account-type">${account.type}</span>
                                    </div>
                                    <div class="account-balance">
                                        ${account.balance ? `$${account.balance.toFixed(2)}` : 'N/A'}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="next-steps">
                        <h4>What's Next?</h4>
                        <ul>
                            <li>Your account data will sync automatically</li>
                            <li>Set up spending alerts and notifications</li>
                            <li>Explore your financial insights and analytics</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
        
        this.stepContainer.innerHTML = stepHtml;
        this.hideContinueButton();
        
        // Auto-close after 5 seconds
        setTimeout(() => {
            this.closeModal();
        }, 5000);
    }
    
    /**
     * Handle continue button
     */
    handleContinue() {
        // This will be handled by specific step handlers
        console.log('Continue button clicked');
    }
    
    /**
     * Cancel linking process
     */
    async cancelLinking() {
        if (!this.currentSession?.sessionId) {
            this.closeModal();
            return;
        }
        
        try {
            await this.apiCall('POST', `/cancel/${this.currentSession.sessionId}`);
        } catch (error) {
            console.error('Error cancelling linking:', error);
        }
        
        this.closeModal();
    }
    
    /**
     * Show upgrade prompt
     */
    showUpgradePrompt(upgradePrompt) {
        const stepHtml = `
            <div class="linking-step" id="upgrade-step">
                <div class="step-content">
                    <div class="upgrade-prompt">
                        <div class="upgrade-icon">🔒</div>
                        <h3>${upgradePrompt.title}</h3>
                        <p>${upgradePrompt.message}</p>
                        
                        <div class="upgrade-benefits">
                            <h4>What you'll get:</h4>
                            <ul>
                                ${upgradePrompt.benefits.map(benefit => `<li>${benefit}</li>`).join('')}
                            </ul>
                        </div>
                        
                        ${upgradePrompt.preview_features.length > 0 ? `
                            <div class="preview-features">
                                <h4>Preview Features:</h4>
                                <ul>
                                    ${upgradePrompt.preview_features.map(feature => `<li>${feature}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        
                        <div class="upgrade-actions">
                            <button class="btn btn-primary" id="upgrade-now">
                                ${upgradePrompt.trial_available ? `Start ${upgradePrompt.trial_days}-Day Free Trial` : 'Upgrade Now'}
                            </button>
                            <button class="btn btn-outline" id="upgrade-later">Maybe Later</button>
                        </div>
                        
                        ${upgradePrompt.trial_available ? `
                            <p class="trial-note">No commitment required. Cancel anytime during your trial.</p>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        this.stepContainer.innerHTML = stepHtml;
        
        document.getElementById('upgrade-now').addEventListener('click', () => {
            window.location.href = upgradePrompt.upgrade_url;
        });
        
        document.getElementById('upgrade-later').addEventListener('click', () => {
            this.closeModal();
        });
    }
    
    /**
     * Show limit reached prompt
     */
    showLimitReachedPrompt(response) {
        const stepHtml = `
            <div class="linking-step" id="limit-reached-step">
                <div class="step-content">
                    <div class="limit-reached-prompt">
                        <div class="limit-icon">⚠️</div>
                        <h3>Limit Reached</h3>
                        <p>${response.message}</p>
                        
                        <div class="current-usage">
                            <h4>Your Current Usage:</h4>
                            <div class="usage-stats">
                                <div class="usage-stat">
                                    <span class="stat-label">Accounts:</span>
                                    <span class="stat-value">${response.usage.total_accounts}</span>
                                </div>
                                <div class="usage-stat">
                                    <span class="stat-label">Institutions:</span>
                                    <span class="stat-value">${response.usage.total_institutions}</span>
                                </div>
                                <div class="usage-stat">
                                    <span class="stat-label">Connections:</span>
                                    <span class="stat-value">${response.usage.total_connections}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="upgrade-benefits">
                            <h4>Upgrade to get more:</h4>
                            <ul>
                                ${response.upgrade_prompt.benefits.map(benefit => `<li>${benefit}</li>`).join('')}
                            </ul>
                        </div>
                        
                        <div class="upgrade-actions">
                            <button class="btn btn-primary" id="upgrade-now">
                                ${response.upgrade_prompt.trial_available ? `Start ${response.upgrade_prompt.trial_days}-Day Free Trial` : 'Upgrade Now'}
                            </button>
                            <button class="btn btn-outline" id="upgrade-later">Maybe Later</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.stepContainer.innerHTML = stepHtml;
        
        document.getElementById('upgrade-now').addEventListener('click', () => {
            window.location.href = response.upgrade_prompt.upgrade_url;
        });
        
        document.getElementById('upgrade-later').addEventListener('click', () => {
            this.closeModal();
        });
    }
    
    /**
     * Show account limit exceeded prompt
     */
    showAccountLimitExceededPrompt(response) {
        const stepHtml = `
            <div class="linking-step" id="account-limit-step">
                <div class="step-content">
                    <div class="account-limit-prompt">
                        <div class="limit-icon">📊</div>
                        <h3>Account Limit Exceeded</h3>
                        <p>${response.message}</p>
                        
                        <div class="limit-details">
                            <div class="limit-stat">
                                <span class="stat-label">Current Accounts:</span>
                                <span class="stat-value">${response.current_accounts}</span>
                            </div>
                            <div class="limit-stat">
                                <span class="stat-label">Trying to Add:</span>
                                <span class="stat-value">${response.requested_addition}</span>
                            </div>
                            <div class="limit-stat">
                                <span class="stat-label">Your Limit:</span>
                                <span class="stat-value">${response.limit}</span>
                            </div>
                        </div>
                        
                        <div class="upgrade-benefits">
                            <h4>Upgrade to unlock unlimited accounts:</h4>
                            <ul>
                                ${response.upgrade_prompt.benefits.map(benefit => `<li>${benefit}</li>`).join('')}
                            </ul>
                        </div>
                        
                        <div class="upgrade-actions">
                            <button class="btn btn-primary" id="upgrade-now">
                                ${response.upgrade_prompt.trial_available ? `Start ${response.upgrade_prompt.trial_days}-Day Free Trial` : 'Upgrade Now'}
                            </button>
                            <button class="btn btn-outline" id="upgrade-later">Maybe Later</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.stepContainer.innerHTML = stepHtml;
        
        document.getElementById('upgrade-now').addEventListener('click', () => {
            window.location.href = response.upgrade_prompt.upgrade_url;
        });
        
        document.getElementById('upgrade-later').addEventListener('click', () => {
            this.closeModal();
        });
    }
    
    /**
     * Show modal
     */
    showModal() {
        this.modal.classList.add('active');
        document.body.classList.add('modal-open');
    }
    
    /**
     * Close modal
     */
    closeModal() {
        this.modal.classList.remove('active');
        document.body.classList.remove('modal-open');
        this.reset();
    }
    
    /**
     * Reset linking process
     */
    reset() {
        this.currentSession = null;
        this.mfaSession = null;
        this.verificationSession = null;
        this.currentStep = 'initiation';
        this.stepContainer.innerHTML = '';
        this.updateProgress(0);
        this.updateStatus('Ready to connect your bank account', 'info');
        this.hideContinueButton();
    }
    
    /**
     * Update progress bar
     */
    updateProgress(percentage) {
        const progressFill = this.progressBar.querySelector('.progress-fill');
        progressFill.style.width = `${percentage}%`;
    }
    
    /**
     * Update step indicator
     */
    updateStep(step) {
        document.querySelectorAll('.progress-steps .step').forEach(stepEl => {
            stepEl.classList.remove('active', 'completed');
        });
        
        const steps = ['initiation', 'selection', 'verification', 'completion'];
        const currentIndex = steps.indexOf(step);
        
        for (let i = 0; i <= currentIndex; i++) {
            const stepEl = document.querySelector(`[data-step="${steps[i]}"]`);
            if (i < currentIndex) {
                stepEl.classList.add('completed');
            } else {
                stepEl.classList.add('active');
            }
        }
    }
    
    /**
     * Update status indicator
     */
    updateStatus(message, type = 'info') {
        const statusMessage = this.statusIndicator.querySelector('.status-message');
        const statusIcon = this.statusIndicator.querySelector('.status-icon');
        
        statusMessage.textContent = message;
        this.statusIndicator.className = `status-indicator status-${type}`;
        
        // Update icon based on type
        const icons = {
            'loading': '⏳',
            'success': '✓',
            'error': '✗',
            'info': 'ℹ'
        };
        
        statusIcon.textContent = icons[type] || icons.info;
    }
    
    /**
     * Show continue button
     */
    showContinueButton() {
        const continueBtn = document.getElementById('continue-linking');
        continueBtn.style.display = 'inline-block';
    }
    
    /**
     * Hide continue button
     */
    hideContinueButton() {
        const continueBtn = document.getElementById('continue-linking');
        continueBtn.style.display = 'none';
    }
    
    /**
     * Show error message
     */
    showError(message) {
        this.updateStatus(message, 'error');
        
        if (this.onError) {
            this.onError(message);
        }
    }
    
    /**
     * Get MFA type label
     */
    getMFATypeLabel(type) {
        const labels = {
            'sms': 'SMS Code',
            'email': 'Email Code',
            'phone': 'Phone Call',
            'security_questions': 'Security Questions',
            'authenticator_app': 'Authenticator App',
            'hardware_token': 'Hardware Token',
            'biometric': 'Biometric'
        };
        
        return labels[type] || type;
    }
    
    /**
     * Make API call
     */
    async apiCall(method, endpoint, data = null) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'API request failed');
        }
        
        return result;
    }
    
    /**
     * Set event handlers
     */
    onSuccess(callback) {
        this.onSuccess = callback;
    }
    
    onError(callback) {
        this.onError = callback;
    }
    
    onProgress(callback) {
        this.onProgress = callback;
    }
}

// Initialize account linking manager
let accountLinkingManager;

document.addEventListener('DOMContentLoaded', () => {
    accountLinkingManager = new AccountLinkingManager();
    
    // Global function to start account linking
    window.startAccountLinking = (institutionId = null) => {
        accountLinkingManager.startLinking(institutionId);
    };
    
    // Global function to open Plaid Link
    window.openPlaidLink = () => {
        accountLinkingManager.openPlaidLink();
    };
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AccountLinkingManager;
} 