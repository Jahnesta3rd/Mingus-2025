/**
 * Account Management JavaScript for MINGUS
 * 
 * This module provides comprehensive account management features:
 * - Account customization (nickname, categorization, etc.)
 * - Account status monitoring
 * - Re-authentication workflows
 * - Account unlinking and data cleanup
 */

class AccountManagementManager {
    constructor() {
        this.accounts = [];
        this.currentAccount = null;
        this.reAuthWorkflow = null;
        this.modal = null;
        this.stepContainer = null;
        this.progressBar = null;
        this.statusDisplay = null;
        
        // Event handlers
        this.onAccountsLoaded = null;
        this.onAccountUpdated = null;
        this.onReAuthRequired = null;
        this.onAccountUnlinked = null;
        
        this.init();
    }
    
    init() {
        this.createModal();
        this.bindGlobalEvents();
        this.loadAccounts();
    }
    
    /**
     * Create account management modal
     */
    createModal() {
        const modalHtml = `
            <div id="account-management-modal" class="account-management-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2 id="modal-title">Account Management</h2>
                        <button class="close-btn" id="close-modal">&times;</button>
                    </div>
                    
                    <div class="modal-body">
                        <div class="progress-container">
                            <div class="progress-bar" id="progress-bar">
                                <div class="progress-fill" id="progress-fill"></div>
                            </div>
                            <div class="status-display" id="status-display"></div>
                        </div>
                        
                        <div class="step-container" id="step-container">
                            <!-- Step content will be dynamically loaded here -->
                        </div>
                    </div>
                    
                    <div class="modal-footer">
                        <div class="action-buttons" id="action-buttons">
                            <!-- Action buttons will be dynamically loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Get modal elements
        this.modal = document.getElementById('account-management-modal');
        this.stepContainer = document.getElementById('step-container');
        this.progressBar = document.getElementById('progress-fill');
        this.statusDisplay = document.getElementById('status-display');
        
        // Bind modal events
        this.bindModalEvents();
    }
    
    /**
     * Bind modal events
     */
    bindModalEvents() {
        // Close button
        document.getElementById('close-modal').addEventListener('click', () => {
            this.closeModal();
        });
        
        // Click outside to close
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
        
        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('active')) {
                this.closeModal();
            }
        });
    }
    
    /**
     * Bind global events
     */
    bindGlobalEvents() {
        // Account management triggers
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="manage-accounts"]')) {
                e.preventDefault();
                this.showAccountList();
            }
            
            if (e.target.matches('[data-action="customize-account"]')) {
                e.preventDefault();
                const accountId = e.target.dataset.accountId;
                this.showCustomizationForm(accountId);
            }
            
            if (e.target.matches('[data-action="view-account-status"]')) {
                e.preventDefault();
                const accountId = e.target.dataset.accountId;
                this.showAccountStatus(accountId);
            }
            
            if (e.target.matches('[data-action="reauth-account"]')) {
                e.preventDefault();
                const accountId = e.target.dataset.accountId;
                this.initiateReAuthentication(accountId);
            }
            
            if (e.target.matches('[data-action="unlink-account"]')) {
                e.preventDefault();
                const accountId = e.target.dataset.accountId;
                this.showUnlinkConfirmation(accountId);
            }
        });
    }
    
    /**
     * Load user accounts
     */
    async loadAccounts() {
        try {
            this.updateStatus('Loading accounts...', 'loading');
            
            const response = await this.apiCall('GET', '/api/account-management/accounts');
            
            if (response.success) {
                this.accounts = response.accounts;
                this.renderAccountList();
                
                if (this.onAccountsLoaded) {
                    this.onAccountsLoaded(this.accounts);
                }
                
                this.updateStatus('Accounts loaded successfully', 'success');
            } else {
                this.updateStatus('Failed to load accounts', 'error');
                this.showError(response.message || 'Failed to load accounts');
            }
        } catch (error) {
            console.error('Error loading accounts:', error);
            this.updateStatus('Error loading accounts', 'error');
            this.showError('Failed to load accounts');
        }
    }
    
    /**
     * Show account list
     */
    showAccountList() {
        const stepHtml = `
            <div class="account-list-step">
                <div class="step-content">
                    <h3>Your Bank Accounts</h3>
                    <p>Manage your connected bank accounts and their settings.</p>
                    
                    <div class="account-grid" id="account-grid">
                        ${this.accounts.map(account => this.renderAccountCard(account)).join('')}
                    </div>
                    
                    <div class="account-summary">
                        <div class="summary-stat">
                            <span class="stat-label">Total Accounts:</span>
                            <span class="stat-value">${this.accounts.length}</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Active Accounts:</span>
                            <span class="stat-value">${this.accounts.filter(a => a.status === 'active').length}</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Primary Account:</span>
                            <span class="stat-value">${this.accounts.find(a => a.customization.is_primary)?.customization.nickname || 'None'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.stepContainer.innerHTML = stepHtml;
        this.updateModalTitle('Account Management');
        this.showModal();
        this.updateProgress(100);
    }
    
    /**
     * Render account card
     */
    renderAccountCard(account) {
        const statusClass = this.getStatusClass(account.status);
        const statusIcon = this.getStatusIcon(account.status);
        const reAuthBadge = account.status_info.re_auth_required ? '<span class="reauth-badge">Re-auth Required</span>' : '';
        
        return `
            <div class="account-card ${statusClass}" data-account-id="${account.id}">
                <div class="account-header">
                    <div class="account-icon" style="background-color: ${account.customization.color}">
                        ${account.customization.icon}
                    </div>
                    <div class="account-info">
                        <h4 class="account-name">${account.customization.nickname}</h4>
                        <p class="account-details">
                            ${account.institution_name} • ${account.mask}
                            ${account.customization.is_primary ? '<span class="primary-badge">Primary</span>' : ''}
                        </p>
                    </div>
                    <div class="account-status">
                        <span class="status-indicator ${statusClass}">
                            ${statusIcon} ${account.status}
                        </span>
                        ${reAuthBadge}
                    </div>
                </div>
                
                <div class="account-balance">
                    <span class="balance-label">Current Balance:</span>
                    <span class="balance-amount">$${account.current_balance.toFixed(2)}</span>
                </div>
                
                <div class="account-actions">
                    <button class="btn btn-outline btn-sm" data-action="customize-account" data-account-id="${account.id}">
                        Customize
                    </button>
                    <button class="btn btn-outline btn-sm" data-action="view-account-status" data-account-id="${account.id}">
                        Status
                    </button>
                    ${account.status_info.re_auth_required ? 
                        `<button class="btn btn-warning btn-sm" data-action="reauth-account" data-account-id="${account.id}">
                            Re-authenticate
                        </button>` : ''
                    }
                    <button class="btn btn-danger btn-sm" data-action="unlink-account" data-account-id="${account.id}">
                        Unlink
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Show account customization form
     */
    async showCustomizationForm(accountId) {
        try {
            this.updateStatus('Loading account details...', 'loading');
            
            const account = this.accounts.find(a => a.id === accountId);
            if (!account) {
                this.showError('Account not found');
                return;
            }
            
            this.currentAccount = account;
            
            const stepHtml = `
                <div class="customization-step">
                    <div class="step-content">
                        <h3>Customize Account</h3>
                        <p>Personalize your account settings and appearance.</p>
                        
                        <form id="customization-form" class="customization-form">
                            <div class="form-group">
                                <label for="nickname">Account Nickname</label>
                                <input type="text" id="nickname" name="nickname" 
                                       value="${account.customization.nickname}" 
                                       maxlength="50" required>
                                <small>Give your account a memorable name</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="category">Category</label>
                                <select id="category" name="category" required>
                                    <option value="checking" ${account.customization.category === 'checking' ? 'selected' : ''}>Checking</option>
                                    <option value="savings" ${account.customization.category === 'savings' ? 'selected' : ''}>Savings</option>
                                    <option value="credit_card" ${account.customization.category === 'credit_card' ? 'selected' : ''}>Credit Card</option>
                                    <option value="loan" ${account.customization.category === 'loan' ? 'selected' : ''}>Loan</option>
                                    <option value="investment" ${account.customization.category === 'investment' ? 'selected' : ''}>Investment</option>
                                    <option value="business" ${account.customization.category === 'business' ? 'selected' : ''}>Business</option>
                                    <option value="other" ${account.customization.category === 'other' ? 'selected' : ''}>Other</option>
                                </select>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="color">Color</label>
                                    <input type="color" id="color" name="color" 
                                           value="${account.customization.color}">
                                </div>
                                
                                <div class="form-group">
                                    <label for="icon">Icon</label>
                                    <select id="icon" name="icon">
                                        <option value="🏦" ${account.customization.icon === '🏦' ? 'selected' : ''}>🏦 Bank</option>
                                        <option value="💳" ${account.customization.icon === '💳' ? 'selected' : ''}>💳 Card</option>
                                        <option value="💰" ${account.customization.icon === '💰' ? 'selected' : ''}>💰 Money</option>
                                        <option value="📈" ${account.customization.icon === '📈' ? 'selected' : ''}>📈 Investment</option>
                                        <option value="🏢" ${account.customization.icon === '🏢' ? 'selected' : ''}>🏢 Business</option>
                                        <option value="🎯" ${account.customization.icon === '🎯' ? 'selected' : ''}>🎯 Target</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label for="notes">Notes</label>
                                <textarea id="notes" name="notes" rows="3" 
                                          maxlength="500">${account.customization.notes || ''}</textarea>
                                <small>Optional notes about this account</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="tags">Tags</label>
                                <input type="text" id="tags" name="tags" 
                                       value="${account.customization.tags.join(', ')}" 
                                       placeholder="Enter tags separated by commas">
                                <small>Tags to help organize your accounts</small>
                            </div>
                            
                            <div class="form-checkboxes">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="is_primary" name="is_primary" 
                                           ${account.customization.is_primary ? 'checked' : ''}>
                                    <span class="checkmark"></span>
                                    Set as primary account
                                </label>
                                
                                <label class="checkbox-label">
                                    <input type="checkbox" id="is_hidden" name="is_hidden" 
                                           ${account.customization.is_hidden ? 'checked' : ''}>
                                    <span class="checkmark"></span>
                                    Hide from dashboard
                                </label>
                            </div>
                        </form>
                    </div>
                </div>
            `;
            
            this.stepContainer.innerHTML = stepHtml;
            this.updateModalTitle('Customize Account');
            this.showActionButtons([
                { text: 'Save Changes', class: 'btn-primary', action: () => this.saveCustomization() },
                { text: 'Cancel', class: 'btn-outline', action: () => this.showAccountList() }
            ]);
            this.showModal();
            this.updateProgress(50);
            this.updateStatus('Ready to customize', 'success');
            
        } catch (error) {
            console.error('Error showing customization form:', error);
            this.showError('Failed to load customization form');
        }
    }
    
    /**
     * Save account customization
     */
    async saveCustomization() {
        try {
            this.updateStatus('Saving changes...', 'loading');
            
            const form = document.getElementById('customization-form');
            const formData = new FormData(form);
            
            const customization = {
                nickname: formData.get('nickname'),
                category: formData.get('category'),
                color: formData.get('color'),
                icon: formData.get('icon'),
                notes: formData.get('notes'),
                tags: formData.get('tags').split(',').map(tag => tag.trim()).filter(tag => tag),
                is_primary: formData.get('is_primary') === 'on',
                is_hidden: formData.get('is_hidden') === 'on'
            };
            
            const response = await this.apiCall('PUT', `/api/account-management/accounts/${this.currentAccount.id}/customize`, customization);
            
            if (response.success) {
                // Update local account data
                const accountIndex = this.accounts.findIndex(a => a.id === this.currentAccount.id);
                if (accountIndex !== -1) {
                    this.accounts[accountIndex].customization = response.customization;
                }
                
                this.updateStatus('Changes saved successfully', 'success');
                
                if (this.onAccountUpdated) {
                    this.onAccountUpdated(this.currentAccount.id, response.customization);
                }
                
                // Show success message and return to account list
                setTimeout(() => {
                    this.showAccountList();
                }, 1500);
            } else {
                this.updateStatus('Failed to save changes', 'error');
                this.showError(response.message || 'Failed to save changes');
            }
        } catch (error) {
            console.error('Error saving customization:', error);
            this.updateStatus('Error saving changes', 'error');
            this.showError('Failed to save changes');
        }
    }
    
    /**
     * Show account status
     */
    async showAccountStatus(accountId) {
        try {
            this.updateStatus('Loading account status...', 'loading');
            
            const response = await this.apiCall('GET', `/api/account-management/accounts/${accountId}/status`);
            
            if (response.success) {
                const account = this.accounts.find(a => a.id === accountId);
                const statusInfo = response.status_info;
                
                const stepHtml = `
                    <div class="status-step">
                        <div class="step-content">
                            <h3>Account Status</h3>
                            <p>Detailed status information for ${account.customization.nickname}.</p>
                            
                            <div class="status-overview">
                                <div class="status-card ${this.getStatusClass(statusInfo.status)}">
                                    <div class="status-header">
                                        <span class="status-icon">${this.getStatusIcon(statusInfo.status)}</span>
                                        <h4>${statusInfo.status.toUpperCase()}</h4>
                                    </div>
                                    <div class="status-details">
                                        <div class="status-item">
                                            <span class="label">Connection Health:</span>
                                            <span class="value ${this.getHealthClass(statusInfo.connection_health)}">
                                                ${statusInfo.connection_health}
                                            </span>
                                        </div>
                                        <div class="status-item">
                                            <span class="label">Data Freshness:</span>
                                            <span class="value">${statusInfo.data_freshness}</span>
                                        </div>
                                        <div class="status-item">
                                            <span class="label">Sync Frequency:</span>
                                            <span class="value">${statusInfo.sync_frequency}</span>
                                        </div>
                                        <div class="status-item">
                                            <span class="label">Last Sync:</span>
                                            <span class="value">${statusInfo.last_sync_at ? new Date(statusInfo.last_sync_at).toLocaleString() : 'Never'}</span>
                                        </div>
                                        ${statusInfo.error_message ? `
                                            <div class="status-item error">
                                                <span class="label">Error:</span>
                                                <span class="value">${statusInfo.error_message}</span>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                            
                            ${statusInfo.re_auth_required ? `
                                <div class="reauth-warning">
                                    <div class="warning-icon">⚠️</div>
                                    <div class="warning-content">
                                        <h4>Re-authentication Required</h4>
                                        <p>This account needs to be re-authenticated to continue syncing data.</p>
                                        <button class="btn btn-warning" onclick="accountManager.initiateReAuthentication('${accountId}')">
                                            Re-authenticate Now
                                        </button>
                                    </div>
                                </div>
                            ` : ''}
                            
                            <div class="status-actions">
                                <button class="btn btn-outline" onclick="accountManager.syncAccount('${accountId}')">
                                    Sync Now
                                </button>
                                <button class="btn btn-outline" onclick="accountManager.showAccountList()">
                                    Back to Accounts
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                this.stepContainer.innerHTML = stepHtml;
                this.updateModalTitle('Account Status');
                this.showModal();
                this.updateProgress(100);
                this.updateStatus('Status loaded', 'success');
            } else {
                this.updateStatus('Failed to load status', 'error');
                this.showError(response.message || 'Failed to load account status');
            }
        } catch (error) {
            console.error('Error loading account status:', error);
            this.updateStatus('Error loading status', 'error');
            this.showError('Failed to load account status');
        }
    }
    
    /**
     * Initiate re-authentication
     */
    async initiateReAuthentication(accountId) {
        try {
            this.updateStatus('Initiating re-authentication...', 'loading');
            
            const response = await this.apiCall('POST', `/api/account-management/accounts/${accountId}/reauth/initiate`);
            
            if (response.success) {
                this.reAuthWorkflow = {
                    workflowId: response.workflow_id,
                    accountId: accountId,
                    linkToken: response.link_token,
                    expiresAt: response.expires_at
                };
                
                this.showReAuthenticationStep();
            } else {
                this.updateStatus('Failed to initiate re-authentication', 'error');
                this.showError(response.message || 'Failed to initiate re-authentication');
            }
        } catch (error) {
            console.error('Error initiating re-authentication:', error);
            this.updateStatus('Error initiating re-authentication', 'error');
            this.showError('Failed to initiate re-authentication');
        }
    }
    
    /**
     * Show re-authentication step
     */
    showReAuthenticationStep() {
        const stepHtml = `
            <div class="reauth-step">
                <div class="step-content">
                    <h3>Re-authenticate Account</h3>
                    <p>Please re-authenticate your bank account to continue syncing data.</p>
                    
                    <div class="reauth-info">
                        <div class="info-card">
                            <div class="info-icon">🔐</div>
                            <div class="info-content">
                                <h4>Secure Re-authentication</h4>
                                <p>This process is secure and will only take a few moments.</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="reauth-actions">
                        <button class="btn btn-primary" id="start-reauth">
                            Start Re-authentication
                        </button>
                        <button class="btn btn-outline" onclick="accountManager.showAccountList()">
                            Cancel
                        </button>
                    </div>
                    
                    <div class="reauth-timer" id="reauth-timer" style="display: none;">
                        <p>Session expires in: <span id="timer-display"></span></p>
                    </div>
                </div>
            </div>
        `;
        
        this.stepContainer.innerHTML = stepHtml;
        this.updateModalTitle('Re-authenticate Account');
        this.showModal();
        this.updateProgress(75);
        this.updateStatus('Ready to re-authenticate', 'success');
        
        // Bind re-authentication events
        document.getElementById('start-reauth').addEventListener('click', () => {
            this.startReAuthentication();
        });
    }
    
    /**
     * Start re-authentication process
     */
    startReAuthentication() {
        if (!this.reAuthWorkflow) {
            this.showError('No re-authentication workflow found');
            return;
        }
        
        // Initialize Plaid Link for re-authentication
        if (window.Plaid) {
            const handler = window.Plaid.create({
                token: this.reAuthWorkflow.linkToken,
                onSuccess: (public_token, metadata) => {
                    this.completeReAuthentication(public_token);
                },
                onExit: (err, metadata) => {
                    if (err) {
                        this.showError('Re-authentication was cancelled or failed');
                    }
                    this.showAccountList();
                },
                onEvent: (eventName, metadata) => {
                    console.log('Plaid event:', eventName, metadata);
                }
            });
            
            handler.open();
        } else {
            this.showError('Plaid is not available');
        }
    }
    
    /**
     * Complete re-authentication
     */
    async completeReAuthentication(publicToken) {
        try {
            this.updateStatus('Completing re-authentication...', 'loading');
            
            const response = await this.apiCall('POST', `/api/account-management/reauth/${this.reAuthWorkflow.workflowId}/complete`, {
                public_token: publicToken
            });
            
            if (response.success) {
                this.updateStatus('Re-authentication completed successfully', 'success');
                
                // Refresh accounts
                await this.loadAccounts();
                
                if (this.onReAuthRequired) {
                    this.onReAuthRequired(this.reAuthWorkflow.accountId, false);
                }
                
                // Show success and return to account list
                setTimeout(() => {
                    this.showAccountList();
                }, 2000);
            } else {
                this.updateStatus('Re-authentication failed', 'error');
                this.showError(response.message || 'Re-authentication failed');
            }
        } catch (error) {
            console.error('Error completing re-authentication:', error);
            this.updateStatus('Error completing re-authentication', 'error');
            this.showError('Failed to complete re-authentication');
        }
    }
    
    /**
     * Show unlink confirmation
     */
    showUnlinkConfirmation(accountId) {
        const account = this.accounts.find(a => a.id === accountId);
        if (!account) {
            this.showError('Account not found');
            return;
        }
        
        const stepHtml = `
            <div class="unlink-step">
                <div class="step-content">
                    <h3>Unlink Account</h3>
                    <p>Are you sure you want to unlink <strong>${account.customization.nickname}</strong>?</p>
                    
                    <div class="unlink-warning">
                        <div class="warning-icon">⚠️</div>
                        <div class="warning-content">
                            <h4>What happens when you unlink:</h4>
                            <ul>
                                <li>Account will no longer sync data</li>
                                <li>Transaction history will be preserved</li>
                                <li>You can re-link the account later</li>
                                <li>Account settings will be saved</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="unlink-options">
                        <label class="checkbox-label">
                            <input type="checkbox" id="cleanup_data" checked>
                            <span class="checkmark"></span>
                            Clean up account data (recommended)
                        </label>
                    </div>
                    
                    <div class="unlink-actions">
                        <button class="btn btn-danger" onclick="accountManager.unlinkAccount('${accountId}')">
                            Yes, Unlink Account
                        </button>
                        <button class="btn btn-outline" onclick="accountManager.showAccountList()">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        this.stepContainer.innerHTML = stepHtml;
        this.updateModalTitle('Unlink Account');
        this.showModal();
        this.updateProgress(90);
        this.updateStatus('Confirm unlink action', 'warning');
    }
    
    /**
     * Unlink account
     */
    async unlinkAccount(accountId) {
        try {
            this.updateStatus('Unlinking account...', 'loading');
            
            const cleanupData = document.getElementById('cleanup_data').checked;
            
            const response = await this.apiCall('POST', `/api/account-management/accounts/${accountId}/unlink`, {
                cleanup_data: cleanupData
            });
            
            if (response.success) {
                this.updateStatus('Account unlinked successfully', 'success');
                
                // Remove account from local list
                this.accounts = this.accounts.filter(a => a.id !== accountId);
                
                if (this.onAccountUnlinked) {
                    this.onAccountUnlinked(accountId);
                }
                
                // Show success and return to account list
                setTimeout(() => {
                    this.showAccountList();
                }, 2000);
            } else {
                this.updateStatus('Failed to unlink account', 'error');
                this.showError(response.message || 'Failed to unlink account');
            }
        } catch (error) {
            console.error('Error unlinking account:', error);
            this.updateStatus('Error unlinking account', 'error');
            this.showError('Failed to unlink account');
        }
    }
    
    /**
     * Sync account
     */
    async syncAccount(accountId) {
        try {
            this.updateStatus('Syncing account...', 'loading');
            
            const response = await this.apiCall('POST', `/api/account-management/accounts/${accountId}/sync`);
            
            if (response.success) {
                this.updateStatus('Account synced successfully', 'success');
                
                // Refresh accounts
                await this.loadAccounts();
                
                setTimeout(() => {
                    this.showAccountStatus(accountId);
                }, 1500);
            } else {
                if (response.error === 'reauth_required') {
                    this.updateStatus('Re-authentication required', 'warning');
                    this.showError('This account needs to be re-authenticated before syncing');
                    
                    setTimeout(() => {
                        this.initiateReAuthentication(accountId);
                    }, 2000);
                } else {
                    this.updateStatus('Sync failed', 'error');
                    this.showError(response.message || 'Failed to sync account');
                }
            }
        } catch (error) {
            console.error('Error syncing account:', error);
            this.updateStatus('Error syncing account', 'error');
            this.showError('Failed to sync account');
        }
    }
    
    /**
     * Show modal
     */
    showModal() {
        this.modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    /**
     * Close modal
     */
    closeModal() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
        this.reset();
    }
    
    /**
     * Reset modal state
     */
    reset() {
        this.currentAccount = null;
        this.reAuthWorkflow = null;
        this.stepContainer.innerHTML = '';
        this.updateProgress(0);
        this.updateStatus('', '');
        this.hideActionButtons();
    }
    
    /**
     * Update modal title
     */
    updateModalTitle(title) {
        document.getElementById('modal-title').textContent = title;
    }
    
    /**
     * Update progress bar
     */
    updateProgress(percentage) {
        this.progressBar.style.width = `${percentage}%`;
    }
    
    /**
     * Update status display
     */
    updateStatus(message, type) {
        if (message) {
            this.statusDisplay.textContent = message;
            this.statusDisplay.className = `status-display ${type}`;
            this.statusDisplay.style.display = 'block';
        } else {
            this.statusDisplay.style.display = 'none';
        }
    }
    
    /**
     * Show action buttons
     */
    showActionButtons(buttons) {
        const actionButtons = document.getElementById('action-buttons');
        actionButtons.innerHTML = buttons.map(button => 
            `<button class="btn ${button.class}" onclick="${button.action.toString()}()">${button.text}</button>`
        ).join('');
    }
    
    /**
     * Hide action buttons
     */
    hideActionButtons() {
        document.getElementById('action-buttons').innerHTML = '';
    }
    
    /**
     * Show error message
     */
    showError(message) {
        // Create error notification
        const notification = document.createElement('div');
        notification.className = 'error-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <span class="error-icon">❌</span>
                <span class="error-message">${message}</span>
                <button class="close-notification">&times;</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Close button
        notification.querySelector('.close-notification').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }
    
    /**
     * Get status class
     */
    getStatusClass(status) {
        const statusClasses = {
            'active': 'status-active',
            'inactive': 'status-inactive',
            'error': 'status-error',
            'pending_verification': 'status-pending',
            'maintenance': 'status-maintenance',
            'disconnected': 'status-disconnected',
            'archived': 'status-archived'
        };
        return statusClasses[status] || 'status-unknown';
    }
    
    /**
     * Get status icon
     */
    getStatusIcon(status) {
        const statusIcons = {
            'active': '✅',
            'inactive': '⏸️',
            'error': '❌',
            'pending_verification': '⏳',
            'maintenance': '🔧',
            'disconnected': '🔌',
            'archived': '📁'
        };
        return statusIcons[status] || '❓';
    }
    
    /**
     * Get health class
     */
    getHealthClass(health) {
        const healthClasses = {
            'excellent': 'health-excellent',
            'good': 'health-good',
            'fair': 'health-fair',
            'poor': 'health-poor',
            'unknown': 'health-unknown'
        };
        return healthClasses[health] || 'health-unknown';
    }
    
    /**
     * Make API call
     */
    async apiCall(method, endpoint, data = null) {
        try {
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
            
            const response = await fetch(endpoint, options);
            const result = await response.json();
            
            return result;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
    
    /**
     * Event handlers
     */
    onAccountsLoaded(callback) {
        this.onAccountsLoaded = callback;
    }
    
    onAccountUpdated(callback) {
        this.onAccountUpdated = callback;
    }
    
    onReAuthRequired(callback) {
        this.onReAuthRequired = callback;
    }
    
    onAccountUnlinked(callback) {
        this.onAccountUnlinked = callback;
    }
}

// Initialize account management
const accountManager = new AccountManagementManager();

// Export for global access
window.accountManager = accountManager; 