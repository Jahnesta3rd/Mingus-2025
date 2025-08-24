/**
 * Transaction Analytics Frontend Module
 * 
 * Provides client-side functionality for transaction processing, analysis,
 * and insight generation for MINGUS users.
 */

class TransactionAnalyticsManager {
    constructor() {
        this.apiBase = '/api/transaction-analytics';
        this.currentUser = null;
        this.insights = [];
        this.spendingCategories = [];
        this.budgetAlerts = [];
        this.anomalies = [];
        this.subscriptions = [];
        this.financialInsights = [];
        this.analyticsReports = [];
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadUserData();
        this.initializeCharts();
    }
    
    bindEvents() {
        // Process transactions button
        const processBtn = document.getElementById('process-transactions-btn');
        if (processBtn) {
            processBtn.addEventListener('click', () => this.processTransactions());
        }
        
        // Refresh insights button
        const refreshBtn = document.getElementById('refresh-insights-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshInsights());
        }
        
        // Filter controls
        this.bindFilterEvents();
        
        // Insight interaction events
        this.bindInsightEvents();
    }
    
    bindFilterEvents() {
        // Date range filter
        const dateRangeSelect = document.getElementById('date-range-filter');
        if (dateRangeSelect) {
            dateRangeSelect.addEventListener('change', () => this.applyFilters());
        }
        
        // Category filter
        const categoryFilter = document.getElementById('category-filter');
        if (categoryFilter) {
            categoryFilter.addEventListener('change', () => this.applyFilters());
        }
        
        // Insight type filter
        const insightTypeFilter = document.getElementById('insight-type-filter');
        if (insightTypeFilter) {
            insightTypeFilter.addEventListener('change', () => this.applyFilters());
        }
    }
    
    bindInsightEvents() {
        // Dismiss insight buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('dismiss-insight-btn')) {
                const insightId = e.target.dataset.insightId;
                this.dismissFinancialInsight(insightId);
            }
        });
        
        // Dismiss alert buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('dismiss-alert-btn')) {
                const alertId = e.target.dataset.alertId;
                this.dismissBudgetAlert(alertId);
            }
        });
        
        // Anomaly feedback buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('anomaly-feedback-btn')) {
                const anomalyId = e.target.dataset.anomalyId;
                const feedback = e.target.dataset.feedback;
                this.provideAnomalyFeedback(anomalyId, feedback);
            }
        });
    }
    
    async loadUserData() {
        try {
            // Load analytics summary
            await this.loadAnalyticsSummary();
            
            // Load initial data
            await Promise.all([
                this.loadInsights(),
                this.loadSpendingCategories(),
                this.loadBudgetAlerts(),
                this.loadAnomalies(),
                this.loadSubscriptions(),
                this.loadFinancialInsights()
            ]);
            
            this.updateDashboard();
            
        } catch (error) {
            console.error('Error loading user data:', error);
            this.showError('Failed to load analytics data');
        }
    }
    
    async processTransactions(options = {}) {
        try {
            this.showLoading('Processing transactions...');
            
            const requestData = {
                account_ids: options.accountIds || null,
                date_range: options.dateRange || null,
                force_reprocess: options.forceReprocess || false
            };
            
            const response = await fetch(`${this.apiBase}/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': this.getCSRFToken()
                },
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess(`Processed ${result.data.processed_count} transactions`);
                
                // Refresh data after processing
                await this.refreshInsights();
                
                // Update summary
                await this.loadAnalyticsSummary();
                this.updateDashboard();
                
            } else {
                this.showError(result.message || 'Failed to process transactions');
            }
            
        } catch (error) {
            console.error('Error processing transactions:', error);
            this.showError('Failed to process transactions');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadInsights(filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.insightType) params.append('insight_type', filters.insightType);
            if (filters.category) params.append('category', filters.category);
            if (filters.startDate) params.append('start_date', filters.startDate);
            if (filters.endDate) params.append('end_date', filters.endDate);
            if (filters.limit) params.append('limit', filters.limit);
            
            const response = await fetch(`${this.apiBase}/insights?${params}`);
            const result = await response.json();
            
            if (result.success) {
                this.insights = result.data.insights;
                this.renderInsights();
            } else {
                console.error('Failed to load insights:', result.message);
            }
            
        } catch (error) {
            console.error('Error loading insights:', error);
        }
    }
    
    async loadSpendingCategories(period = 'month') {
        try {
            const params = new URLSearchParams({ period });
            const response = await fetch(`${this.apiBase}/spending-categories?${params}`);
            const result = await response.json();
            
            if (result.success) {
                this.spendingCategories = result.data.categories;
                this.renderSpendingCategories();
                this.updateSpendingChart();
            } else {
                console.error('Failed to load spending categories:', result.message);
            }
            
        } catch (error) {
            console.error('Error loading spending categories:', error);
        }
    }
    
    async loadBudgetAlerts(filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.alertLevel) params.append('alert_level', filters.alertLevel);
            if (filters.isActive !== undefined) params.append('is_active', filters.isActive);
            if (filters.limit) params.append('limit', filters.limit);
            
            const response = await fetch(`${this.apiBase}/budget-alerts?${params}`);
            const result = await response.json();
            
            if (result.success) {
                this.budgetAlerts = result.data.alerts;
                this.renderBudgetAlerts();
            } else {
                console.error('Failed to load budget alerts:', result.message);
            }
            
        } catch (error) {
            console.error('Error loading budget alerts:', error);
        }
    }
    
    async loadAnomalies(filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.anomalyType) params.append('anomaly_type', filters.anomalyType);
            if (filters.severity) params.append('severity', filters.severity);
            if (filters.isConfirmed !== undefined) params.append('is_confirmed', filters.isConfirmed);
            if (filters.limit) params.append('limit', filters.limit);
            
            const response = await fetch(`${this.apiBase}/anomalies?${params}`);
            const result = await response.json();
            
            if (result.success) {
                this.anomalies = result.data.anomalies;
                this.renderAnomalies();
            } else {
                console.error('Failed to load anomalies:', result.message);
            }
            
        } catch (error) {
            console.error('Error loading anomalies:', error);
        }
    }
    
    async loadSubscriptions(filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.isActive !== undefined) params.append('is_active', filters.isActive);
            if (filters.recommendation) params.append('recommendation', filters.recommendation);
            
            const response = await fetch(`${this.apiBase}/subscriptions?${params}`);
            const result = await response.json();
            
            if (result.success) {
                this.subscriptions = result.data.subscriptions;
                this.renderSubscriptions();
                this.updateSubscriptionChart();
            } else {
                console.error('Failed to load subscriptions:', result.message);
            }
            
        } catch (error) {
            console.error('Error loading subscriptions:', error);
        }
    }
    
    async loadFinancialInsights(filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.insightType) params.append('insight_type', filters.insightType);
            if (filters.priority) params.append('priority', filters.priority);
            if (filters.isActionable !== undefined) params.append('is_actionable', filters.isActionable);
            if (filters.limit) params.append('limit', filters.limit);
            
            const response = await fetch(`${this.apiBase}/financial-insights?${params}`);
            const result = await response.json();
            
            if (result.success) {
                this.financialInsights = result.data.insights;
                this.renderFinancialInsights();
            } else {
                console.error('Failed to load financial insights:', result.message);
            }
            
        } catch (error) {
            console.error('Error loading financial insights:', error);
        }
    }
    
    async loadAnalyticsSummary() {
        try {
            const response = await fetch(`${this.apiBase}/summary`);
            const result = await response.json();
            
            if (result.success) {
                this.updateSummaryDisplay(result.data.summary);
            } else {
                console.error('Failed to load analytics summary:', result.message);
            }
            
        } catch (error) {
            console.error('Error loading analytics summary:', error);
        }
    }
    
    async refreshInsights() {
        await Promise.all([
            this.loadInsights(),
            this.loadSpendingCategories(),
            this.loadBudgetAlerts(),
            this.loadAnomalies(),
            this.loadSubscriptions(),
            this.loadFinancialInsights()
        ]);
    }
    
    async dismissFinancialInsight(insightId) {
        try {
            const response = await fetch(`${this.apiBase}/financial-insights/${insightId}/dismiss`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': this.getCSRFToken()
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Remove from local array
                this.financialInsights = this.financialInsights.filter(i => i.id !== insightId);
                this.renderFinancialInsights();
                this.showSuccess('Insight dismissed successfully');
            } else {
                this.showError(result.message || 'Failed to dismiss insight');
            }
            
        } catch (error) {
            console.error('Error dismissing insight:', error);
            this.showError('Failed to dismiss insight');
        }
    }
    
    async dismissBudgetAlert(alertId) {
        try {
            const response = await fetch(`${this.apiBase}/budget-alerts/${alertId}/dismiss`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': this.getCSRFToken()
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Remove from local array
                this.budgetAlerts = this.budgetAlerts.filter(a => a.id !== alertId);
                this.renderBudgetAlerts();
                this.showSuccess('Alert dismissed successfully');
            } else {
                this.showError(result.message || 'Failed to dismiss alert');
            }
            
        } catch (error) {
            console.error('Error dismissing alert:', error);
            this.showError('Failed to dismiss alert');
        }
    }
    
    async provideAnomalyFeedback(anomalyId, feedback) {
        try {
            const response = await fetch(`${this.apiBase}/anomalies/${anomalyId}/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': this.getCSRFToken()
                },
                body: JSON.stringify({ feedback })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Update local anomaly
                const anomaly = this.anomalies.find(a => a.id === anomalyId);
                if (anomaly) {
                    anomaly.user_feedback = feedback;
                    anomaly.is_confirmed = feedback === 'confirmed';
                    anomaly.is_false_positive = feedback === 'false_positive';
                }
                this.renderAnomalies();
                this.showSuccess('Feedback recorded successfully');
            } else {
                this.showError(result.message || 'Failed to record feedback');
            }
            
        } catch (error) {
            console.error('Error recording anomaly feedback:', error);
            this.showError('Failed to record feedback');
        }
    }
    
    applyFilters() {
        const dateRange = document.getElementById('date-range-filter')?.value;
        const category = document.getElementById('category-filter')?.value;
        const insightType = document.getElementById('insight-type-filter')?.value;
        
        const filters = {};
        if (dateRange && dateRange !== 'all') filters.dateRange = dateRange;
        if (category && category !== 'all') filters.category = category;
        if (insightType && insightType !== 'all') filters.insightType = insightType;
        
        this.loadInsights(filters);
    }
    
    renderInsights() {
        const container = document.getElementById('insights-container');
        if (!container) return;
        
        if (this.insights.length === 0) {
            container.innerHTML = '<p class="no-data">No insights available</p>';
            return;
        }
        
        const html = this.insights.map(insight => `
            <div class="insight-card" data-insight-id="${insight.id}">
                <div class="insight-header">
                    <span class="insight-category">${insight.category}</span>
                    <span class="insight-confidence">${(insight.confidence * 100).toFixed(1)}%</span>
                </div>
                <div class="insight-content">
                    <h4>${insight.merchant_name || 'Unknown Merchant'}</h4>
                    <p class="insight-type">${insight.transaction_type}</p>
                    <div class="insight-flags">
                        ${insight.is_recurring ? '<span class="flag recurring">Recurring</span>' : ''}
                        ${insight.is_subscription ? '<span class="flag subscription">Subscription</span>' : ''}
                        ${insight.is_anomaly ? '<span class="flag anomaly">Anomaly</span>' : ''}
                    </div>
                    <div class="insight-tags">
                        ${insight.tags ? JSON.parse(insight.tags).map(tag => `<span class="tag">${tag}</span>`).join('') : ''}
                    </div>
                </div>
                <div class="insight-risk">
                    <span class="risk-score">Risk: ${(insight.risk_score * 100).toFixed(1)}%</span>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    renderSpendingCategories() {
        const container = document.getElementById('spending-categories-container');
        if (!container) return;
        
        if (this.spendingCategories.length === 0) {
            container.innerHTML = '<p class="no-data">No spending categories available</p>';
            return;
        }
        
        const html = this.spendingCategories.map(category => `
            <div class="category-card">
                <div class="category-header">
                    <h4>${category.category_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                    <span class="category-amount">$${category.total_amount.toFixed(2)}</span>
                </div>
                <div class="category-stats">
                    <div class="stat">
                        <span class="stat-label">Transactions:</span>
                        <span class="stat-value">${category.transaction_count}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Average:</span>
                        <span class="stat-value">$${category.average_amount.toFixed(2)}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Trend:</span>
                        <span class="stat-value trend-${category.trend_direction || 'stable'}">${category.trend_direction || 'Stable'}</span>
                    </div>
                </div>
                ${category.budget_limit ? `
                    <div class="budget-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${Math.min(category.budget_percentage, 100)}%"></div>
                        </div>
                        <span class="budget-text">${category.budget_percentage.toFixed(1)}% of budget</span>
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    renderBudgetAlerts() {
        const container = document.getElementById('budget-alerts-container');
        if (!container) return;
        
        if (this.budgetAlerts.length === 0) {
            container.innerHTML = '<p class="no-data">No budget alerts</p>';
            return;
        }
        
        const html = this.budgetAlerts.map(alert => `
            <div class="alert-card alert-${alert.alert_level}" data-alert-id="${alert.id}">
                <div class="alert-header">
                    <h4>${alert.category_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                    <span class="alert-level">${alert.alert_level}</span>
                </div>
                <div class="alert-content">
                    <div class="alert-stats">
                        <div class="stat">
                            <span class="stat-label">Spent:</span>
                            <span class="stat-value">$${alert.current_spending.toFixed(2)}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Budget:</span>
                            <span class="stat-value">$${alert.budget_limit.toFixed(2)}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Used:</span>
                            <span class="stat-value">${alert.percentage_used.toFixed(1)}%</span>
                        </div>
                    </div>
                    ${alert.days_remaining ? `
                        <div class="days-remaining">
                            <span class="days-label">Days remaining:</span>
                            <span class="days-value">${alert.days_remaining}</span>
                        </div>
                    ` : ''}
                </div>
                <div class="alert-actions">
                    <button class="btn btn-secondary dismiss-alert-btn" data-alert-id="${alert.id}">
                        Dismiss
                    </button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    renderAnomalies() {
        const container = document.getElementById('anomalies-container');
        if (!container) return;
        
        if (this.anomalies.length === 0) {
            container.innerHTML = '<p class="no-data">No anomalies detected</p>';
            return;
        }
        
        const html = this.anomalies.map(anomaly => `
            <div class="anomaly-card anomaly-${anomaly.severity}" data-anomaly-id="${anomaly.id}">
                <div class="anomaly-header">
                    <h4>${anomaly.anomaly_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                    <span class="anomaly-severity">${anomaly.severity}</span>
                </div>
                <div class="anomaly-content">
                    <p class="anomaly-description">${anomaly.merchant_name || 'Unknown Merchant'}</p>
                    <div class="anomaly-stats">
                        <div class="stat">
                            <span class="stat-label">Expected:</span>
                            <span class="stat-value">${anomaly.expected_value ? `$${anomaly.expected_value.toFixed(2)}` : 'N/A'}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Actual:</span>
                            <span class="stat-value">$${anomaly.actual_value.toFixed(2)}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Deviation:</span>
                            <span class="stat-value">${anomaly.deviation_percentage ? `${anomaly.deviation_percentage.toFixed(1)}%` : 'N/A'}</span>
                        </div>
                    </div>
                </div>
                <div class="anomaly-actions">
                    <button class="btn btn-success anomaly-feedback-btn" data-anomaly-id="${anomaly.id}" data-feedback="confirmed">
                        Confirm
                    </button>
                    <button class="btn btn-warning anomaly-feedback-btn" data-anomaly-id="${anomaly.id}" data-feedback="false_positive">
                        False Positive
                    </button>
                    <button class="btn btn-secondary anomaly-feedback-btn" data-anomaly-id="${anomaly.id}" data-feedback="ignored">
                        Ignore
                    </button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    renderSubscriptions() {
        const container = document.getElementById('subscriptions-container');
        if (!container) return;
        
        if (this.subscriptions.length === 0) {
            container.innerHTML = '<p class="no-data">No subscriptions found</p>';
            return;
        }
        
        const html = this.subscriptions.map(subscription => `
            <div class="subscription-card">
                <div class="subscription-header">
                    <h4>${subscription.merchant_name}</h4>
                    <span class="subscription-cost">$${subscription.monthly_cost.toFixed(2)}/month</span>
                </div>
                <div class="subscription-content">
                    <div class="subscription-stats">
                        <div class="stat">
                            <span class="stat-label">Annual Cost:</span>
                            <span class="stat-value">$${subscription.annual_cost.toFixed(2)}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Transactions:</span>
                            <span class="stat-value">${subscription.transaction_count}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Billing Cycle:</span>
                            <span class="stat-value">${subscription.billing_cycle || 'Unknown'}</span>
                        </div>
                    </div>
                    ${subscription.recommendation ? `
                        <div class="subscription-recommendation">
                            <span class="recommendation-label">Recommendation:</span>
                            <span class="recommendation-value recommendation-${subscription.recommendation}">${subscription.recommendation}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    renderFinancialInsights() {
        const container = document.getElementById('financial-insights-container');
        if (!container) return;
        
        if (this.financialInsights.length === 0) {
            container.innerHTML = '<p class="no-data">No financial insights available</p>';
            return;
        }
        
        const html = this.financialInsights.map(insight => `
            <div class="insight-card insight-${insight.priority}" data-insight-id="${insight.id}">
                <div class="insight-header">
                    <h4>${insight.title}</h4>
                    <span class="insight-priority">${insight.priority}</span>
                </div>
                <div class="insight-content">
                    <p class="insight-description">${insight.description}</p>
                    <div class="insight-impact">
                        <span class="impact-score">Impact: ${(insight.impact_score * 100).toFixed(1)}%</span>
                    </div>
                    ${insight.is_actionable ? `
                        <div class="insight-action">
                            <span class="action-type">${insight.action_type || 'Review'}</span>
                            ${insight.action_description ? `<p class="action-description">${insight.action_description}</p>` : ''}
                        </div>
                    ` : ''}
                </div>
                <div class="insight-actions">
                    <button class="btn btn-secondary dismiss-insight-btn" data-insight-id="${insight.id}">
                        Dismiss
                    </button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    updateSummaryDisplay(summary) {
        const container = document.getElementById('analytics-summary');
        if (!container) return;
        
        container.innerHTML = `
            <div class="summary-grid">
                <div class="summary-item">
                    <span class="summary-label">Total Insights</span>
                    <span class="summary-value">${summary.total_insights}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Active Alerts</span>
                    <span class="summary-value">${summary.active_budget_alerts}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Active Subscriptions</span>
                    <span class="summary-value">${summary.active_subscriptions}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Unconfirmed Anomalies</span>
                    <span class="summary-value">${summary.unconfirmed_anomalies}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Actionable Insights</span>
                    <span class="summary-value">${summary.actionable_insights}</span>
                </div>
            </div>
        `;
    }
    
    updateDashboard() {
        this.updateSummaryDisplay({
            total_insights: this.insights.length,
            active_budget_alerts: this.budgetAlerts.filter(a => !a.is_dismissed).length,
            active_subscriptions: this.subscriptions.filter(s => s.is_active).length,
            unconfirmed_anomalies: this.anomalies.filter(a => !a.is_confirmed).length,
            actionable_insights: this.financialInsights.filter(i => i.is_actionable).length
        });
    }
    
    initializeCharts() {
        // Initialize spending chart
        this.initializeSpendingChart();
        
        // Initialize subscription chart
        this.initializeSubscriptionChart();
    }
    
    initializeSpendingChart() {
        const ctx = document.getElementById('spending-chart');
        if (!ctx) return;
        
        this.spendingChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    initializeSubscriptionChart() {
        const ctx = document.getElementById('subscription-chart');
        if (!ctx) return;
        
        this.subscriptionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Monthly Cost',
                    data: [],
                    backgroundColor: '#36A2EB'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
    }
    
    updateSpendingChart() {
        if (!this.spendingChart) return;
        
        const labels = this.spendingCategories.map(c => c.category_name.replace(/_/g, ' '));
        const data = this.spendingCategories.map(c => c.total_amount);
        
        this.spendingChart.data.labels = labels;
        this.spendingChart.data.datasets[0].data = data;
        this.spendingChart.update();
    }
    
    updateSubscriptionChart() {
        if (!this.subscriptionChart) return;
        
        const labels = this.subscriptions.map(s => s.merchant_name);
        const data = this.subscriptions.map(s => s.monthly_cost);
        
        this.subscriptionChart.data.labels = labels;
        this.subscriptionChart.data.datasets[0].data = data;
        this.subscriptionChart.update();
    }
    
    showLoading(message = 'Loading...') {
        const loadingEl = document.getElementById('loading-overlay');
        if (loadingEl) {
            loadingEl.querySelector('.loading-message').textContent = message;
            loadingEl.style.display = 'flex';
        }
    }
    
    hideLoading() {
        const loadingEl = document.getElementById('loading-overlay');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }
    
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
}

// Initialize the transaction analytics manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.transactionAnalyticsManager = new TransactionAnalyticsManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TransactionAnalyticsManager;
} 