/**
 * Data Synchronization JavaScript for MINGUS
 * 
 * This module provides comprehensive data synchronization features:
 * - Real-time balance updates
 * - Daily transaction synchronization
 * - Historical data backfill (24 months)
 * - Duplicate transaction detection
 * - Data consistency validation
 */

class DataSynchronizationManager {
    constructor() {
        this.syncInProgress = false;
        this.syncQueue = [];
        this.syncResults = {};
        this.syncCallbacks = {};
        
        // Configuration
        this.config = {
            autoSyncInterval: 6 * 60 * 60 * 1000, // 6 hours
            balanceSyncInterval: 60 * 60 * 1000,  // 1 hour
            maxRetries: 3,
            retryDelay: 5000 // 5 seconds
        };
        
        // Event handlers
        this.onSyncStarted = null;
        this.onSyncCompleted = null;
        this.onSyncFailed = null;
        this.onBalanceUpdated = null;
        this.onTransactionsSynced = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.startAutoSync();
    }
    
    /**
     * Bind global events
     */
    bindEvents() {
        // Manual sync triggers
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="sync-account"]')) {
                e.preventDefault();
                const accountId = e.target.dataset.accountId;
                const syncType = e.target.dataset.syncType || 'transactions';
                this.syncAccount(accountId, syncType);
            }
            
            if (e.target.matches('[data-action="sync-balance"]')) {
                e.preventDefault();
                const accountId = e.target.dataset.accountId;
                this.syncBalance(accountId);
            }
            
            if (e.target.matches('[data-action="sync-transactions"]')) {
                e.preventDefault();
                const accountId = e.target.dataset.accountId;
                this.syncTransactions(accountId);
            }
            
            if (e.target.matches('[data-action="sync-historical"]')) {
                e.preventDefault();
                const accountId = e.target.dataset.accountId;
                this.syncHistorical(accountId);
            }
            
            if (e.target.matches('[data-action="validate-data"]')) {
                e.preventDefault();
                const accountId = e.target.dataset.accountId;
                this.validateData(accountId);
            }
            
            if (e.target.matches('[data-action="backfill-data"]')) {
                e.preventDefault();
                const accountId = e.target.dataset.accountId;
                this.backfillData(accountId);
            }
            
            if (e.target.matches('[data-action="bulk-sync"]')) {
                e.preventDefault();
                const syncType = e.target.dataset.syncType || 'transactions';
                this.bulkSync(syncType);
            }
        });
    }
    
    /**
     * Start automatic synchronization
     */
    startAutoSync() {
        // Auto sync transactions every 6 hours
        setInterval(() => {
            this.autoSyncTransactions();
        }, this.config.autoSyncInterval);
        
        // Auto sync balances every hour
        setInterval(() => {
            this.autoSyncBalances();
        }, this.config.balanceSyncInterval);
    }
    
    /**
     * Sync account data
     */
    async syncAccount(accountId, syncType = 'transactions', forceSync = false) {
        try {
            if (this.syncInProgress) {
                this.addToQueue(accountId, syncType, forceSync);
                return;
            }
            
            this.syncInProgress = true;
            this.updateSyncUI(accountId, 'starting', syncType);
            
            if (this.onSyncStarted) {
                this.onSyncStarted(accountId, syncType);
            }
            
            const response = await this.apiCall('POST', `/api/data-sync/accounts/${accountId}/sync`, {
                sync_type: syncType,
                force_sync: forceSync
            });
            
            if (response.success) {
                const result = response.sync_result;
                this.syncResults[accountId] = result;
                
                this.updateSyncUI(accountId, 'completed', syncType, result);
                
                if (this.onSyncCompleted) {
                    this.onSyncCompleted(accountId, syncType, result);
                }
                
                // Show success notification
                this.showNotification('success', `Sync completed: ${result.records_created} new records`);
                
                // Trigger specific callbacks
                if (syncType === 'balance' && this.onBalanceUpdated) {
                    this.onBalanceUpdated(accountId, result);
                } else if (syncType === 'transactions' && this.onTransactionsSynced) {
                    this.onTransactionsSynced(accountId, result);
                }
                
            } else {
                this.updateSyncUI(accountId, 'failed', syncType);
                
                if (this.onSyncFailed) {
                    this.onSyncFailed(accountId, syncType, response.error);
                }
                
                this.showNotification('error', `Sync failed: ${response.message}`);
            }
            
        } catch (error) {
            console.error('Error syncing account:', error);
            this.updateSyncUI(accountId, 'failed', syncType);
            
            if (this.onSyncFailed) {
                this.onSyncFailed(accountId, syncType, error.message);
            }
            
            this.showNotification('error', 'Sync failed: Network error');
        } finally {
            this.syncInProgress = false;
            this.processQueue();
        }
    }
    
    /**
     * Sync account balance
     */
    async syncBalance(accountId) {
        try {
            this.updateSyncUI(accountId, 'starting', 'balance');
            
            const response = await this.apiCall('POST', `/api/data-sync/accounts/${accountId}/balance`);
            
            if (response.success) {
                const balance = response.balance;
                this.updateBalanceDisplay(accountId, balance);
                
                if (this.onBalanceUpdated) {
                    this.onBalanceUpdated(accountId, { balance });
                }
                
                this.showNotification('success', 'Balance updated successfully');
                
            } else {
                this.showNotification('error', `Balance sync failed: ${response.message}`);
            }
            
        } catch (error) {
            console.error('Error syncing balance:', error);
            this.showNotification('error', 'Balance sync failed: Network error');
        }
    }
    
    /**
     * Sync account transactions
     */
    async syncTransactions(accountId, forceSync = false) {
        try {
            this.updateSyncUI(accountId, 'starting', 'transactions');
            
            const response = await this.apiCall('POST', `/api/data-sync/accounts/${accountId}/transactions`, {
                force_sync: forceSync
            });
            
            if (response.success) {
                const transactions = response.transactions;
                
                if (this.onTransactionsSynced) {
                    this.onTransactionsSynced(accountId, transactions);
                }
                
                this.showNotification('success', `Transactions synced: ${transactions.records_created} new records`);
                
            } else {
                this.showNotification('error', `Transaction sync failed: ${response.message}`);
            }
            
        } catch (error) {
            console.error('Error syncing transactions:', error);
            this.showNotification('error', 'Transaction sync failed: Network error');
        }
    }
    
    /**
     * Sync historical data
     */
    async syncHistorical(accountId) {
        try {
            this.updateSyncUI(accountId, 'starting', 'historical');
            
            const response = await this.apiCall('POST', `/api/data-sync/accounts/${accountId}/historical`);
            
            if (response.success) {
                const historical = response.historical;
                
                this.showNotification('success', `Historical data synced: ${historical.records_created} records`);
                
            } else {
                this.showNotification('error', `Historical sync failed: ${response.message}`);
            }
            
        } catch (error) {
            console.error('Error syncing historical data:', error);
            this.showNotification('error', 'Historical sync failed: Network error');
        }
    }
    
    /**
     * Backfill missing data
     */
    async backfillData(accountId) {
        try {
            this.updateSyncUI(accountId, 'starting', 'backfill');
            
            const response = await this.apiCall('POST', `/api/data-sync/accounts/${accountId}/backfill`);
            
            if (response.success) {
                const backfill = response.backfill;
                
                this.showNotification('success', `Data backfilled: ${backfill.records_created} records created`);
                
            } else {
                this.showNotification('error', `Backfill failed: ${response.message}`);
            }
            
        } catch (error) {
            console.error('Error backfilling data:', error);
            this.showNotification('error', 'Backfill failed: Network error');
        }
    }
    
    /**
     * Validate data consistency
     */
    async validateData(accountId) {
        try {
            this.updateSyncUI(accountId, 'starting', 'validation');
            
            const response = await this.apiCall('POST', `/api/data-sync/accounts/${accountId}/validate`);
            
            if (response.success) {
                const validation = response.validation;
                
                if (validation.consistency_check) {
                    this.showNotification('success', 'Data validation passed');
                } else {
                    this.showNotification('warning', `Data validation issues found: ${validation.issues_found} issues`);
                    this.showValidationIssues(accountId, validation);
                }
                
            } else {
                this.showNotification('error', `Validation failed: ${response.message}`);
            }
            
        } catch (error) {
            console.error('Error validating data:', error);
            this.showNotification('error', 'Validation failed: Network error');
        }
    }
    
    /**
     * Bulk sync all accounts
     */
    async bulkSync(syncType = 'transactions') {
        try {
            this.showNotification('info', 'Starting bulk synchronization...');
            
            const response = await this.apiCall('POST', '/api/data-sync/accounts/bulk/sync', {
                sync_type: syncType
            });
            
            if (response.success) {
                const summary = response.summary;
                
                this.showNotification('success', 
                    `Bulk sync completed: ${summary.successful_syncs}/${summary.total_accounts} accounts, ${summary.total_records_created} records created`
                );
                
                // Update all account displays
                this.updateBulkSyncResults(response.results);
                
            } else {
                this.showNotification('error', `Bulk sync failed: ${response.message}`);
            }
            
        } catch (error) {
            console.error('Error performing bulk sync:', error);
            this.showNotification('error', 'Bulk sync failed: Network error');
        }
    }
    
    /**
     * Get sync status for an account
     */
    async getSyncStatus(accountId) {
        try {
            const response = await this.apiCall('GET', `/api/data-sync/accounts/${accountId}/sync-status`);
            
            if (response.success) {
                return response.sync_status;
            } else {
                console.error('Failed to get sync status:', response.message);
                return null;
            }
            
        } catch (error) {
            console.error('Error getting sync status:', error);
            return null;
        }
    }
    
    /**
     * Auto sync transactions
     */
    async autoSyncTransactions() {
        try {
            // Get all active accounts
            const accounts = this.getActiveAccounts();
            
            for (const account of accounts) {
                const status = await this.getSyncStatus(account.id);
                
                if (status && status.sync_health === 'poor') {
                    // Only sync accounts that need it
                    this.syncAccount(account.id, 'transactions', false);
                }
            }
            
        } catch (error) {
            console.error('Error in auto sync transactions:', error);
        }
    }
    
    /**
     * Auto sync balances
     */
    async autoSyncBalances() {
        try {
            // Get all active accounts
            const accounts = this.getActiveAccounts();
            
            for (const account of accounts) {
                this.syncBalance(account.id);
            }
            
        } catch (error) {
            console.error('Error in auto sync balances:', error);
        }
    }
    
    /**
     * Update sync UI
     */
    updateSyncUI(accountId, status, syncType, result = null) {
        const syncButton = document.querySelector(`[data-action="sync-account"][data-account-id="${accountId}"]`);
        const statusIndicator = document.querySelector(`[data-sync-status="${accountId}"]`);
        
        if (syncButton) {
            switch (status) {
                case 'starting':
                    syncButton.disabled = true;
                    syncButton.textContent = 'Syncing...';
                    syncButton.classList.add('syncing');
                    break;
                    
                case 'completed':
                    syncButton.disabled = false;
                    syncButton.textContent = 'Sync';
                    syncButton.classList.remove('syncing');
                    syncButton.classList.add('synced');
                    
                    // Show sync results
                    if (result) {
                        this.showSyncResults(accountId, result);
                    }
                    break;
                    
                case 'failed':
                    syncButton.disabled = false;
                    syncButton.textContent = 'Sync Failed';
                    syncButton.classList.remove('syncing');
                    syncButton.classList.add('failed');
                    break;
            }
        }
        
        if (statusIndicator) {
            statusIndicator.className = `sync-status-indicator ${status}`;
            statusIndicator.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        }
    }
    
    /**
     * Update balance display
     */
    updateBalanceDisplay(accountId, balance) {
        const balanceElement = document.querySelector(`[data-balance="${accountId}"]`);
        const lastUpdatedElement = document.querySelector(`[data-last-updated="${accountId}"]`);
        
        if (balanceElement) {
            balanceElement.textContent = `$${balance.current_balance.toFixed(2)}`;
        }
        
        if (lastUpdatedElement) {
            lastUpdatedElement.textContent = new Date(balance.last_updated).toLocaleString();
        }
    }
    
    /**
     * Show sync results
     */
    showSyncResults(accountId, result) {
        const resultsHtml = `
            <div class="sync-results" data-account-id="${accountId}">
                <div class="results-header">
                    <h4>Sync Results</h4>
                    <button class="close-results" onclick="this.parentElement.parentElement.remove()">&times;</button>
                </div>
                <div class="results-content">
                    <div class="result-item">
                        <span class="label">Records Processed:</span>
                        <span class="value">${result.records_processed}</span>
                    </div>
                    <div class="result-item">
                        <span class="label">Records Created:</span>
                        <span class="value">${result.records_created}</span>
                    </div>
                    <div class="result-item">
                        <span class="label">Records Updated:</span>
                        <span class="value">${result.records_updated}</span>
                    </div>
                    <div class="result-item">
                        <span class="label">Records Skipped:</span>
                        <span class="value">${result.records_skipped}</span>
                    </div>
                    <div class="result-item">
                        <span class="label">Duplicates Found:</span>
                        <span class="value">${result.duplicates_found}</span>
                    </div>
                    <div class="result-item">
                        <span class="label">Duration:</span>
                        <span class="value">${result.duration_seconds.toFixed(2)}s</span>
                    </div>
                </div>
            </div>
        `;
        
        // Insert results into the page
        const accountCard = document.querySelector(`[data-account-id="${accountId}"]`);
        if (accountCard) {
            accountCard.insertAdjacentHTML('beforeend', resultsHtml);
        }
    }
    
    /**
     * Show validation issues
     */
    showValidationIssues(accountId, validation) {
        const issuesHtml = `
            <div class="validation-issues" data-account-id="${accountId}">
                <div class="issues-header">
                    <h4>Data Validation Issues</h4>
                    <button class="close-issues" onclick="this.parentElement.parentElement.remove()">&times;</button>
                </div>
                <div class="issues-content">
                    <div class="issue-summary">
                        <span class="issues-count">${validation.issues_found} issues found</span>
                        <span class="duplicates-count">${validation.duplicates_found} duplicates</span>
                    </div>
                    <div class="issues-list">
                        ${validation.errors.map(error => `<div class="issue-item">${error}</div>`).join('')}
                    </div>
                </div>
            </div>
        `;
        
        // Insert issues into the page
        const accountCard = document.querySelector(`[data-account-id="${accountId}"]`);
        if (accountCard) {
            accountCard.insertAdjacentHTML('beforeend', issuesHtml);
        }
    }
    
    /**
     * Update bulk sync results
     */
    updateBulkSyncResults(results) {
        results.forEach(result => {
            this.updateSyncUI(result.account_id, result.success ? 'completed' : 'failed', 'bulk');
            
            if (result.success) {
                this.syncResults[result.account_id] = result;
            }
        });
    }
    
    /**
     * Add sync to queue
     */
    addToQueue(accountId, syncType, forceSync) {
        this.syncQueue.push({ accountId, syncType, forceSync });
    }
    
    /**
     * Process sync queue
     */
    async processQueue() {
        if (this.syncQueue.length > 0 && !this.syncInProgress) {
            const nextSync = this.syncQueue.shift();
            await this.syncAccount(nextSync.accountId, nextSync.syncType, nextSync.forceSync);
        }
    }
    
    /**
     * Get active accounts
     */
    getActiveAccounts() {
        // This should be implemented based on your account management system
        // For now, return an empty array
        return [];
    }
    
    /**
     * Show notification
     */
    showNotification(type, message) {
        const notification = document.createElement('div');
        notification.className = `sync-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${this.getNotificationIcon(type)}</span>
                <span class="notification-message">${message}</span>
                <button class="close-notification" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    /**
     * Get notification icon
     */
    getNotificationIcon(type) {
        const icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        return icons[type] || 'ℹ️';
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
    onSyncStarted(callback) {
        this.onSyncStarted = callback;
    }
    
    onSyncCompleted(callback) {
        this.onSyncCompleted = callback;
    }
    
    onSyncFailed(callback) {
        this.onSyncFailed = callback;
    }
    
    onBalanceUpdated(callback) {
        this.onBalanceUpdated = callback;
    }
    
    onTransactionsSynced(callback) {
        this.onTransactionsSynced = callback;
    }
}

// Initialize data synchronization manager
const dataSyncManager = new DataSynchronizationManager();

// Export for global access
window.dataSyncManager = dataSyncManager; 