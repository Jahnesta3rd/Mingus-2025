/**
 * Plaid Integration Frontend for MINGUS
 * 
 * This module provides comprehensive frontend functionality for Plaid integration:
 * - Plaid Link setup and bank account connection
 * - Transaction management and display
 * - Account balance monitoring
 * - Institution search and selection
 * - Connection management
 */

class PlaidIntegration {
    constructor() {
        this.plaid = null;
        this.linkToken = null;
        this.userId = null;
        this.connections = [];
        this.accounts = [];
        this.transactions = [];
        this.isInitialized = false;
        
        // Configuration
        this.config = {
            apiBaseUrl: '/api/plaid',
            linkTokenEndpoint: '/api/plaid/link-token',
            connectEndpoint: '/api/plaid/connect',
            accountsEndpoint: '/api/plaid/accounts',
            transactionsEndpoint: '/api/plaid/transactions',
            syncEndpoint: '/api/plaid/transactions/sync',
            institutionsEndpoint: '/api/plaid/institutions/search',
            connectionsEndpoint: '/api/plaid/connections',
            syncLogsEndpoint: '/api/plaid/sync-logs'
        };
        
        // Event handlers
        this.eventHandlers = {
            onSuccess: null,
            onExit: null,
            onLoad: null,
            onEvent: null
        };
        
        this.init();
    }
    
    /**
     * Initialize Plaid integration
     */
    async init() {
        try {
            // Check if Plaid script is loaded
            if (typeof Plaid !== 'undefined') {
                this.plaid = Plaid;
                this.isInitialized = true;
                console.log('Plaid integration initialized successfully');
            } else {
                // Load Plaid script dynamically
                await this.loadPlaidScript();
            }
            
            // Get user ID from session or localStorage
            this.userId = this.getUserId();
            
            // Initialize UI components
            this.initializeUI();
            
            // Load existing connections
            await this.loadConnections();
            
        } catch (error) {
            console.error('Error initializing Plaid integration:', error);
            this.showError('Failed to initialize Plaid integration');
        }
    }
    
    /**
     * Load Plaid script dynamically
     */
    async loadPlaidScript() {
        return new Promise((resolve, reject) => {
            // Check if script is already loaded
            if (document.querySelector('script[src*="plaid"]')) {
                this.plaid = window.Plaid;
                this.isInitialized = true;
                resolve();
                return;
            }
            
            const script = document.createElement('script');
            script.src = 'https://cdn.plaid.com/link/v2/stable/link-initialize.js';
            script.onload = () => {
                this.plaid = window.Plaid;
                this.isInitialized = true;
                console.log('Plaid script loaded successfully');
                resolve();
            };
            script.onerror = () => {
                reject(new Error('Failed to load Plaid script'));
            };
            document.head.appendChild(script);
        });
    }
    
    /**
     * Get user ID from session or localStorage
     */
    getUserId() {
        // Try to get from session storage first
        const sessionUserId = sessionStorage.getItem('user_id');
        if (sessionUserId) {
            return sessionUserId;
        }
        
        // Try to get from localStorage
        const localUserId = localStorage.getItem('user_id');
        if (localUserId) {
            return localUserId;
        }
        
        // Try to get from meta tag
        const metaUserId = document.querySelector('meta[name="user-id"]');
        if (metaUserId) {
            return metaUserId.getAttribute('content');
        }
        
        return null;
    }
    
    /**
     * Initialize UI components
     */
    initializeUI() {
        // Create Plaid Link button if it doesn't exist
        this.createPlaidLinkButton();
        
        // Create account management UI
        this.createAccountManagementUI();
        
        // Create transaction management UI
        this.createTransactionManagementUI();
        
        // Create sync controls
        this.createSyncControls();
    }
    
    /**
     * Create Plaid Link button
     */
    createPlaidLinkButton() {
        const container = document.getElementById('plaid-link-container') || 
                         document.querySelector('.plaid-link-container');
        
        if (!container) {
            console.warn('Plaid link container not found');
            return;
        }
        
        // Clear existing content
        container.innerHTML = '';
        
        // Create connect button
        const connectButton = document.createElement('button');
        connectButton.id = 'plaid-connect-button';
        connectButton.className = 'btn btn-primary plaid-connect-btn';
        connectButton.innerHTML = '<i class="fas fa-university"></i> Connect Bank Account';
        connectButton.onclick = () => this.openPlaidLink();
        
        container.appendChild(connectButton);
        
        // Create status indicator
        const statusIndicator = document.createElement('div');
        statusIndicator.id = 'plaid-status-indicator';
        statusIndicator.className = 'plaid-status-indicator';
        container.appendChild(statusIndicator);
    }
    
    /**
     * Create account management UI
     */
    createAccountManagementUI() {
        const container = document.getElementById('plaid-accounts-container') || 
                         document.querySelector('.plaid-accounts-container');
        
        if (!container) {
            return;
        }
        
        container.innerHTML = `
            <div class="plaid-accounts-header">
                <h3>Connected Bank Accounts</h3>
                <button class="btn btn-sm btn-outline-primary" onclick="plaidIntegration.refreshAccounts()">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
            </div>
            <div id="plaid-accounts-list" class="plaid-accounts-list">
                <div class="loading-spinner">Loading accounts...</div>
            </div>
        `;
    }
    
    /**
     * Create transaction management UI
     */
    createTransactionManagementUI() {
        const container = document.getElementById('plaid-transactions-container') || 
                         document.querySelector('.plaid-transactions-container');
        
        if (!container) {
            return;
        }
        
        container.innerHTML = `
            <div class="plaid-transactions-header">
                <h3>Recent Transactions</h3>
                <div class="plaid-transactions-controls">
                    <select id="plaid-account-filter" class="form-select form-select-sm">
                        <option value="">All Accounts</option>
                    </select>
                    <input type="date" id="plaid-start-date" class="form-control form-control-sm">
                    <input type="date" id="plaid-end-date" class="form-control form-control-sm">
                    <button class="btn btn-sm btn-primary" onclick="plaidIntegration.loadTransactions()">
                        <i class="fas fa-search"></i> Search
                    </button>
                    <button class="btn btn-sm btn-success" onclick="plaidIntegration.syncTransactions()">
                        <i class="fas fa-sync-alt"></i> Sync
                    </button>
                </div>
            </div>
            <div id="plaid-transactions-list" class="plaid-transactions-list">
                <div class="loading-spinner">Loading transactions...</div>
            </div>
        `;
        
        // Set default dates (last 30 days)
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        
        document.getElementById('plaid-end-date').value = endDate.toISOString().split('T')[0];
        document.getElementById('plaid-start-date').value = startDate.toISOString().split('T')[0];
    }
    
    /**
     * Create sync controls
     */
    createSyncControls() {
        const container = document.getElementById('plaid-sync-container') || 
                         document.querySelector('.plaid-sync-container');
        
        if (!container) {
            return;
        }
        
        container.innerHTML = `
            <div class="plaid-sync-header">
                <h4>Sync Status</h4>
                <button class="btn btn-sm btn-outline-secondary" onclick="plaidIntegration.loadSyncLogs()">
                    <i class="fas fa-history"></i> View Logs
                </button>
            </div>
            <div id="plaid-sync-status" class="plaid-sync-status">
                <div class="sync-status-item">
                    <span class="sync-label">Last Sync:</span>
                    <span class="sync-value" id="last-sync-time">Never</span>
                </div>
                <div class="sync-status-item">
                    <span class="sync-label">Connected Accounts:</span>
                    <span class="sync-value" id="connected-accounts-count">0</span>
                </div>
            </div>
        `;
    }
    
    /**
     * Open Plaid Link for bank account connection
     */
    async openPlaidLink() {
        try {
            if (!this.isInitialized) {
                throw new Error('Plaid not initialized');
            }
            
            // Get Link token
            const linkToken = await this.getLinkToken();
            if (!linkToken) {
                throw new Error('Failed to get Link token');
            }
            
            // Configure Plaid Link
            const config = {
                token: linkToken,
                onSuccess: (public_token, metadata) => {
                    this.handlePlaidSuccess(public_token, metadata);
                },
                onExit: (err, metadata) => {
                    this.handlePlaidExit(err, metadata);
                },
                onLoad: () => {
                    this.handlePlaidLoad();
                },
                onEvent: (eventName, metadata) => {
                    this.handlePlaidEvent(eventName, metadata);
                }
            };
            
            // Create and open Plaid Link
            const handler = this.plaid.create(config);
            handler.open();
            
        } catch (error) {
            console.error('Error opening Plaid Link:', error);
            this.showError('Failed to open Plaid Link');
        }
    }
    
    /**
     * Get Link token from server
     */
    async getLinkToken() {
        try {
            const response = await fetch(this.config.linkTokenEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    products: ['transactions', 'auth']
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.linkToken = data.link_token;
                return data.link_token;
            } else {
                throw new Error(data.error || 'Failed to get Link token');
            }
            
        } catch (error) {
            console.error('Error getting Link token:', error);
            throw error;
        }
    }
    
    /**
     * Handle Plaid Link success
     */
    async handlePlaidSuccess(publicToken, metadata) {
        try {
            console.log('Plaid Link success:', metadata);
            
            // Show loading state
            this.showLoading('Connecting bank account...');
            
            // Exchange public token for access token
            const response = await fetch(this.config.connectEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    public_token: publicToken
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(`Successfully connected ${data.institution_name} with ${data.accounts_count} accounts`);
                
                // Reload connections and accounts
                await this.loadConnections();
                await this.loadAccounts();
                
                // Trigger success callback
                if (this.eventHandlers.onSuccess) {
                    this.eventHandlers.onSuccess(data);
                }
                
            } else {
                throw new Error(data.error || 'Failed to connect bank account');
            }
            
        } catch (error) {
            console.error('Error handling Plaid success:', error);
            this.showError('Failed to connect bank account: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * Handle Plaid Link exit
     */
    handlePlaidExit(err, metadata) {
        console.log('Plaid Link exit:', err, metadata);
        
        if (err) {
            this.showError('Plaid Link error: ' + err.display_message);
        }
        
        // Trigger exit callback
        if (this.eventHandlers.onExit) {
            this.eventHandlers.onExit(err, metadata);
        }
    }
    
    /**
     * Handle Plaid Link load
     */
    handlePlaidLoad() {
        console.log('Plaid Link loaded');
        
        // Trigger load callback
        if (this.eventHandlers.onLoad) {
            this.eventHandlers.onLoad();
        }
    }
    
    /**
     * Handle Plaid Link events
     */
    handlePlaidEvent(eventName, metadata) {
        console.log('Plaid Link event:', eventName, metadata);
        
        // Trigger event callback
        if (this.eventHandlers.onEvent) {
            this.eventHandlers.onEvent(eventName, metadata);
        }
    }
    
    /**
     * Load user connections
     */
    async loadConnections() {
        try {
            const response = await fetch(this.config.connectionsEndpoint, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.connections = data.connections;
                this.updateConnectionStatus();
                return data.connections;
            } else {
                throw new Error(data.error || 'Failed to load connections');
            }
            
        } catch (error) {
            console.error('Error loading connections:', error);
            this.showError('Failed to load connections');
            return [];
        }
    }
    
    /**
     * Load user accounts
     */
    async loadAccounts() {
        try {
            const response = await fetch(this.config.accountsEndpoint, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.accounts = data.accounts;
                this.renderAccounts();
                this.updateAccountFilter();
                return data.accounts;
            } else {
                throw new Error(data.error || 'Failed to load accounts');
            }
            
        } catch (error) {
            console.error('Error loading accounts:', error);
            this.showError('Failed to load accounts');
            return [];
        }
    }
    
    /**
     * Load transactions
     */
    async loadTransactions(accountId = null, startDate = null, endDate = null) {
        try {
            // Get filter values
            if (!accountId) {
                accountId = document.getElementById('plaid-account-filter')?.value || '';
            }
            if (!startDate) {
                startDate = document.getElementById('plaid-start-date')?.value || '';
            }
            if (!endDate) {
                endDate = document.getElementById('plaid-end-date')?.value || '';
            }
            
            // Build query parameters
            const params = new URLSearchParams();
            if (accountId) params.append('account_id', accountId);
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);
            params.append('limit', '50');
            
            const response = await fetch(`${this.config.transactionsEndpoint}?${params}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.transactions = data.transactions;
                this.renderTransactions();
                return data.transactions;
            } else {
                throw new Error(data.error || 'Failed to load transactions');
            }
            
        } catch (error) {
            console.error('Error loading transactions:', error);
            this.showError('Failed to load transactions');
            return [];
        }
    }
    
    /**
     * Sync transactions
     */
    async syncTransactions(accountId = null) {
        try {
            this.showLoading('Syncing transactions...');
            
            const response = await fetch(this.config.syncEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    account_id: accountId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(`Synced ${data.total_synced} new transactions`);
                
                // Reload transactions
                await this.loadTransactions();
                
                // Update sync status
                this.updateSyncStatus();
                
            } else {
                throw new Error(data.error || 'Failed to sync transactions');
            }
            
        } catch (error) {
            console.error('Error syncing transactions:', error);
            this.showError('Failed to sync transactions: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * Render accounts list
     */
    renderAccounts() {
        const container = document.getElementById('plaid-accounts-list');
        if (!container) return;
        
        if (this.accounts.length === 0) {
            container.innerHTML = `
                <div class="no-accounts">
                    <i class="fas fa-university"></i>
                    <p>No bank accounts connected</p>
                    <button class="btn btn-primary" onclick="plaidIntegration.openPlaidLink()">
                        Connect Your First Account
                    </button>
                </div>
            `;
            return;
        }
        
        const accountsHtml = this.accounts.map(account => `
            <div class="account-card" data-account-id="${account.id}">
                <div class="account-header">
                    <div class="account-info">
                        <h4>${account.name}</h4>
                        <p class="account-mask">${account.mask ? `****${account.mask}` : ''}</p>
                        <p class="account-type">${account.type} - ${account.subtype}</p>
                    </div>
                    <div class="account-balance">
                        <span class="balance-amount">$${(account.current_balance || 0).toFixed(2)}</span>
                        <span class="balance-currency">${account.iso_currency_code}</span>
                    </div>
                </div>
                <div class="account-details">
                    <p class="institution-name">${account.institution_name}</p>
                    <p class="last-update">Last updated: ${this.formatDate(account.last_balance_update)}</p>
                </div>
                <div class="account-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="plaidIntegration.refreshAccountBalance('${account.id}')">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = accountsHtml;
    }
    
    /**
     * Render transactions list
     */
    renderTransactions() {
        const container = document.getElementById('plaid-transactions-list');
        if (!container) return;
        
        if (this.transactions.length === 0) {
            container.innerHTML = `
                <div class="no-transactions">
                    <i class="fas fa-receipt"></i>
                    <p>No transactions found</p>
                </div>
            `;
            return;
        }
        
        const transactionsHtml = this.transactions.map(transaction => `
            <div class="transaction-item" data-transaction-id="${transaction.id}">
                <div class="transaction-icon">
                    <i class="fas fa-${this.getTransactionIcon(transaction.category)}"></i>
                </div>
                <div class="transaction-details">
                    <div class="transaction-name">${transaction.name}</div>
                    <div class="transaction-meta">
                        <span class="transaction-date">${this.formatDate(transaction.date)}</span>
                        <span class="transaction-category">${transaction.category.join(' > ')}</span>
                        ${transaction.merchant_name ? `<span class="transaction-merchant">${transaction.merchant_name}</span>` : ''}
                    </div>
                </div>
                <div class="transaction-amount ${transaction.amount < 0 ? 'negative' : 'positive'}">
                    ${transaction.amount < 0 ? '-' : '+'}$${Math.abs(transaction.amount).toFixed(2)}
                </div>
                ${transaction.pending ? '<div class="transaction-pending">Pending</div>' : ''}
            </div>
        `).join('');
        
        container.innerHTML = transactionsHtml;
    }
    
    /**
     * Update connection status
     */
    updateConnectionStatus() {
        const indicator = document.getElementById('plaid-status-indicator');
        if (!indicator) return;
        
        if (this.connections.length === 0) {
            indicator.innerHTML = '<span class="status-disconnected">No accounts connected</span>';
        } else {
            const totalAccounts = this.connections.reduce((sum, conn) => sum + conn.account_count, 0);
            indicator.innerHTML = `
                <span class="status-connected">
                    <i class="fas fa-check-circle"></i>
                    ${this.connections.length} institution${this.connections.length > 1 ? 's' : ''}, ${totalAccounts} account${totalAccounts > 1 ? 's' : ''}
                </span>
            `;
        }
    }
    
    /**
     * Update account filter dropdown
     */
    updateAccountFilter() {
        const filter = document.getElementById('plaid-account-filter');
        if (!filter) return;
        
        // Clear existing options except "All Accounts"
        filter.innerHTML = '<option value="">All Accounts</option>';
        
        // Add account options
        this.accounts.forEach(account => {
            const option = document.createElement('option');
            option.value = account.id;
            option.textContent = `${account.name} (${account.institution_name})`;
            filter.appendChild(option);
        });
    }
    
    /**
     * Update sync status
     */
    updateSyncStatus() {
        const lastSyncTime = document.getElementById('last-sync-time');
        const connectedAccountsCount = document.getElementById('connected-accounts-count');
        
        if (lastSyncTime) {
            lastSyncTime.textContent = new Date().toLocaleString();
        }
        
        if (connectedAccountsCount) {
            connectedAccountsCount.textContent = this.accounts.length;
        }
    }
    
    /**
     * Refresh account balance
     */
    async refreshAccountBalance(accountId) {
        try {
            const response = await fetch(`${this.config.accountsEndpoint}/${accountId}/balance`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Balance updated successfully');
                await this.loadAccounts(); // Reload accounts to show updated balance
            } else {
                throw new Error(data.error || 'Failed to refresh balance');
            }
            
        } catch (error) {
            console.error('Error refreshing account balance:', error);
            this.showError('Failed to refresh balance');
        }
    }
    
    /**
     * Load sync logs
     */
    async loadSyncLogs() {
        try {
            const response = await fetch(this.config.syncLogsEndpoint, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showSyncLogsModal(data.sync_logs);
            } else {
                throw new Error(data.error || 'Failed to load sync logs');
            }
            
        } catch (error) {
            console.error('Error loading sync logs:', error);
            this.showError('Failed to load sync logs');
        }
    }
    
    /**
     * Show sync logs modal
     */
    showSyncLogsModal(logs) {
        const modalHtml = `
            <div class="modal fade" id="syncLogsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Sync Logs</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="sync-logs-list">
                                ${logs.map(log => `
                                    <div class="sync-log-item ${log.status}">
                                        <div class="sync-log-header">
                                            <span class="sync-type">${log.sync_type}</span>
                                            <span class="sync-status ${log.status}">${log.status}</span>
                                            <span class="sync-time">${this.formatDate(log.started_at)}</span>
                                        </div>
                                        <div class="sync-log-details">
                                            <span class="sync-items">${log.items_added} added, ${log.items_updated} updated</span>
                                            ${log.duration_seconds ? `<span class="sync-duration">${log.duration_seconds.toFixed(2)}s</span>` : ''}
                                        </div>
                                        ${log.error_message ? `<div class="sync-error">${log.error_message}</div>` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.getElementById('syncLogsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('syncLogsModal'));
        modal.show();
    }
    
    /**
     * Utility methods
     */
    formatDate(dateString) {
        if (!dateString) return 'Never';
        return new Date(dateString).toLocaleDateString();
    }
    
    getTransactionIcon(category) {
        const categoryMap = {
            'Food and Drink': 'utensils',
            'Transportation': 'car',
            'Shopping': 'shopping-cart',
            'Bills and Utilities': 'file-invoice-dollar',
            'Entertainment': 'film',
            'Health and Fitness': 'heartbeat',
            'Travel': 'plane',
            'Education': 'graduation-cap',
            'Personal Care': 'user',
            'Business Services': 'briefcase',
            'Government Services and Taxes': 'landmark',
            'Transfer': 'exchange-alt',
            'Income': 'money-bill-wave'
        };
        
        const primaryCategory = category[0];
        return categoryMap[primaryCategory] || 'receipt';
    }
    
    showLoading(message = 'Loading...') {
        // Create or update loading indicator
        let loading = document.getElementById('plaid-loading');
        if (!loading) {
            loading = document.createElement('div');
            loading.id = 'plaid-loading';
            loading.className = 'plaid-loading-overlay';
            document.body.appendChild(loading);
        }
        
        loading.innerHTML = `
            <div class="plaid-loading-content">
                <div class="spinner-border text-primary" role="status"></div>
                <p>${message}</p>
            </div>
        `;
        loading.style.display = 'flex';
    }
    
    hideLoading() {
        const loading = document.getElementById('plaid-loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `plaid-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    /**
     * Public methods for external use
     */
    refreshAccounts() {
        return this.loadAccounts();
    }
    
    refreshConnections() {
        return this.loadConnections();
    }
    
    setEventHandler(event, handler) {
        if (this.eventHandlers.hasOwnProperty(event)) {
            this.eventHandlers[event] = handler;
        }
    }
}

// Initialize Plaid integration when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.plaidIntegration = new PlaidIntegration();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PlaidIntegration;
} 