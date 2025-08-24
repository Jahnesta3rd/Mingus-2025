/**
 * Professional Dashboard JavaScript
 * Handles real-time data loading, chart rendering, and interactive features
 */

// Global variables
let dashboardData = {};
let charts = {};
let refreshInterval = null;
let currentTab = 'overview';

// Chart.js configuration
Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
Chart.defaults.color = '#6c757d';
Chart.defaults.plugins.legend.position = 'bottom';

/**
 * Initialize the Professional dashboard
 */
function initializeProfessionalDashboard() {
    console.log('Initializing Professional Dashboard...');
    
    // Show loading overlay
    showLoading();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial dashboard data
    loadDashboardData();
    
    // Set up auto-refresh
    setupAutoRefresh();
    
    // Hide loading overlay
    hideLoading();
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            switchTab(tab.dataset.tab);
        });
    });
    
    // Refresh button
    document.querySelector('.btn-secondary').addEventListener('click', refreshDashboard);
    
    // Export button
    document.querySelector('.btn-primary').addEventListener('click', exportData);
}

/**
 * Load dashboard data from API
 */
async function loadDashboardData() {
    try {
        console.log('Loading dashboard data...');
        
        // Load overview data
        const overviewResponse = await fetch('/api/professional/dashboard/overview');
        if (overviewResponse.ok) {
            const data = await overviewResponse.json();
            dashboardData = data.data;
            updateDashboard(data.data);
        } else {
            throw new Error('Failed to load dashboard data');
        }
        
        // Update last updated time
        updateLastUpdated();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data. Please try again.');
    }
}

/**
 * Update dashboard with new data
 */
function updateDashboard(data) {
    // Update quick stats
    updateQuickStats(data);
    
    // Update account balances
    updateAccountBalances(data.account_balances);
    
    // Update cash flow analysis
    updateCashFlowAnalysis(data.cash_flow_analysis);
    
    // Update spending analysis
    updateSpendingAnalysis(data.spending_analysis);
    
    // Update bill prediction
    updateBillPrediction(data.bill_prediction);
    
    // Update investment overview
    updateInvestmentOverview(data.investment_overview);
    
    // Update debt management
    updateDebtManagement(data.debt_management);
    
    // Update alerts
    updateAlerts(data.alerts);
    
    // Update insights
    updateInsights(data.insights);
    
    // Render charts
    renderCharts(data);
}

/**
 * Update quick stats section
 */
function updateQuickStats(data) {
    const totalBalance = data.account_balances?.total_balance || 0;
    const netCashflow = data.cash_flow_analysis?.projections?.[0]?.projected_net_flow || 0;
    const savingsRate = calculateSavingsRate(data);
    const alertCount = data.alerts?.length || 0;
    
    // Update total balance
    document.getElementById('total-balance').textContent = formatCurrency(totalBalance);
    document.getElementById('balance-change').textContent = formatChange(data.account_balances?.portfolio_metrics?.total_change_30d || 0);
    
    // Update net cash flow
    document.getElementById('net-cashflow').textContent = formatCurrency(netCashflow);
    document.getElementById('cashflow-change').textContent = formatChange(netCashflow);
    
    // Update savings rate
    document.getElementById('savings-rate').textContent = `${savingsRate.toFixed(1)}%`;
    document.getElementById('savings-change').textContent = 'This month';
    
    // Update alerts
    document.getElementById('alert-count').textContent = alertCount;
    document.getElementById('alert-status').textContent = alertCount > 0 ? 'Needs attention' : 'All clear';
}

/**
 * Update account balances section
 */
function updateAccountBalances(accountData) {
    if (!accountData || !accountData.accounts) return;
    
    const accountsSummary = document.getElementById('accounts-summary');
    const accountsGrid = document.getElementById('accounts-grid');
    
    // Update summary
    if (accountsSummary) {
        accountsSummary.innerHTML = accountData.accounts.map(account => `
            <div class="account-summary-item">
                <div class="account-info">
                    <h4>${account.account_name}</h4>
                    <p class="account-institution">${account.institution_name}</p>
                </div>
                <div class="account-balance-info">
                    <p class="balance">${formatCurrency(account.current_balance)}</p>
                    <p class="change ${account.balance_change_30d >= 0 ? 'positive' : 'negative'}">
                        ${formatChange(account.balance_change_30d)}
                    </p>
                </div>
            </div>
        `).join('');
    }
    
    // Update detailed grid
    if (accountsGrid) {
        accountsGrid.innerHTML = accountData.accounts.map(account => `
            <div class="account-card">
                <div class="account-header">
                    <span class="account-name">${account.account_name}</span>
                    <span class="account-type">${account.account_type}</span>
                </div>
                <div class="account-balance">${formatCurrency(account.current_balance)}</div>
                <div class="account-change ${account.balance_change_30d >= 0 ? 'positive' : 'negative'}">
                    ${formatChange(account.balance_change_30d)} (30 days)
                </div>
                <div class="account-details">
                    <div class="account-detail">
                        <span class="detail-label">Available:</span>
                        <span class="detail-value">${formatCurrency(account.available_balance)}</span>
                    </div>
                    <div class="account-detail">
                        <span class="detail-label">24h Change:</span>
                        <span class="detail-value ${account.balance_change_24h >= 0 ? 'positive' : 'negative'}">
                            ${formatChange(account.balance_change_24h)}
                        </span>
                    </div>
                    <div class="account-detail">
                        <span class="detail-label">7d Change:</span>
                        <span class="detail-value ${account.balance_change_7d >= 0 ? 'positive' : 'negative'}">
                            ${formatChange(account.balance_change_7d)}
                        </span>
                    </div>
                    <div class="account-detail">
                        <span class="detail-label">Last Updated:</span>
                        <span class="detail-value">${formatDate(account.last_updated)}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

/**
 * Update cash flow analysis section
 */
function updateCashFlowAnalysis(cashFlowData) {
    if (!cashFlowData || !cashFlowData.projections) return;
    
    // Update metrics
    const totalIncome = cashFlowData.projections.reduce((sum, p) => sum + p.projected_income, 0);
    const totalExpenses = cashFlowData.projections.reduce((sum, p) => sum + p.projected_expenses, 0);
    const netFlow = totalIncome - totalExpenses;
    const avgConfidence = cashFlowData.projections.reduce((sum, p) => sum + p.confidence_level, 0) / cashFlowData.projections.length;
    
    document.getElementById('projected-income').textContent = formatCurrency(totalIncome);
    document.getElementById('projected-expenses').textContent = formatCurrency(totalExpenses);
    document.getElementById('projected-net-flow').textContent = formatCurrency(netFlow);
    document.getElementById('confidence-level').textContent = `${(avgConfidence * 100).toFixed(1)}%`;
    
    // Render cash flow chart
    renderCashFlowChart(cashFlowData.projections);
}

/**
 * Update spending analysis section
 */
function updateSpendingAnalysis(spendingData) {
    if (!spendingData || !spendingData.spending_by_category) return;
    
    // Render spending charts
    renderSpendingCharts(spendingData);
    
    // Update category breakdown
    updateCategoryBreakdown(spendingData.spending_by_category);
}

/**
 * Update bill prediction section
 */
function updateBillPrediction(billData) {
    if (!billData) return;
    
    const totalBills = billData.upcoming_bills?.length || 0;
    const totalAmount = billData.upcoming_bills?.reduce((sum, bill) => sum + bill.amount, 0) || 0;
    const savingsOpportunity = billData.savings_opportunities?.reduce((sum, opp) => sum + opp.amount, 0) || 0;
    
    document.getElementById('total-bills').textContent = totalBills;
    document.getElementById('total-amount-due').textContent = formatCurrency(totalAmount);
    document.getElementById('savings-opportunity').textContent = formatCurrency(savingsOpportunity);
    
    // Update bills timeline
    updateBillsTimeline(billData.upcoming_bills);
    
    // Update payment optimization
    updatePaymentOptimization(billData.optimized_payments);
}

/**
 * Update investment overview section
 */
function updateInvestmentOverview(investmentData) {
    if (!investmentData) return;
    
    document.getElementById('portfolio-value').textContent = formatCurrency(investmentData.portfolio_value || 0);
    document.getElementById('portfolio-change').textContent = formatChange(investmentData.portfolio_performance?.change || 0);
    document.getElementById('diversification-score').textContent = `${(investmentData.diversification_score * 100).toFixed(1)}%`;
    document.getElementById('risk-level').textContent = investmentData.risk_assessment?.level || 'N/A';
    
    // Render investment charts
    renderInvestmentCharts(investmentData);
}

/**
 * Update debt management section
 */
function updateDebtManagement(debtData) {
    if (!debtData) return;
    
    document.getElementById('total-debt').textContent = formatCurrency(debtData.total_debt || 0);
    document.getElementById('debt-to-income').textContent = `${(debtData.debt_to_income_ratio * 100).toFixed(1)}%`;
    document.getElementById('monthly-interest').textContent = formatCurrency(debtData.interest_payments || 0);
    
    // Update debt strategies
    updateDebtStrategies(debtData);
}

/**
 * Update alerts section
 */
function updateAlerts(alerts) {
    if (!alerts || alerts.length === 0) return;
    
    const alertsContent = document.getElementById('alerts-content');
    if (alertsContent) {
        alertsContent.innerHTML = alerts.map(alert => `
            <div class="alert-item ${alert.severity}">
                <div class="alert-icon">
                    <i class="fas fa-${getAlertIcon(alert.type)}"></i>
                </div>
                <div class="alert-content">
                    <h4>${alert.title}</h4>
                    <p>${alert.message}</p>
                    <span class="alert-time">${formatDate(alert.timestamp)}</span>
                </div>
            </div>
        `).join('');
    }
}

/**
 * Update insights section
 */
function updateInsights(insights) {
    if (!insights || insights.length === 0) return;
    
    const insightsList = document.getElementById('insights-list');
    if (insightsList) {
        insightsList.innerHTML = insights.slice(0, 5).map(insight => `
            <div class="insight-item">
                <div class="insight-icon">
                    <i class="fas fa-${getInsightIcon(insight.type)}"></i>
                </div>
                <div class="insight-content">
                    <h4>${insight.title}</h4>
                    <p>${insight.description}</p>
                    <div class="insight-actions">
                        <button class="btn btn-sm" onclick="applyInsight('${insight.id}')">Apply</button>
                        <button class="btn btn-sm btn-secondary" onclick="dismissInsight('${insight.id}')">Dismiss</button>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

/**
 * Render all charts
 */
function renderCharts(data) {
    // Cash flow chart
    if (data.cash_flow_analysis?.projections) {
        renderCashFlowChart(data.cash_flow_analysis.projections);
    }
    
    // Spending charts
    if (data.spending_analysis) {
        renderSpendingCharts(data.spending_analysis);
    }
    
    // Investment charts
    if (data.investment_overview) {
        renderInvestmentCharts(data.investment_overview);
    }
}

/**
 * Render cash flow chart
 */
function renderCashFlowChart(projections) {
    const ctx = document.getElementById('cashflow-chart');
    if (!ctx) return;
    
    const labels = projections.map(p => p.month);
    const incomeData = projections.map(p => p.projected_income);
    const expenseData = projections.map(p => p.projected_expenses);
    const netData = projections.map(p => p.projected_net_flow);
    
    if (charts.cashFlow) {
        charts.cashFlow.destroy();
    }
    
    charts.cashFlow = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    borderColor: '#27ae60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Net Flow',
                    data: netData,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}

/**
 * Render spending charts
 */
function renderSpendingCharts(spendingData) {
    // Category pie chart
    const categoryCtx = document.getElementById('spending-categories-chart');
    if (categoryCtx && spendingData.spending_by_category) {
        const categories = spendingData.spending_by_category.slice(0, 8);
        const labels = categories.map(c => c.category_name);
        const data = categories.map(c => c.total_spent);
        const colors = generateColors(labels.length);
        
        if (charts.spendingCategories) {
            charts.spendingCategories.destroy();
        }
        
        charts.spendingCategories = new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff'
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
    
    // Spending trends chart
    const trendsCtx = document.getElementById('spending-trends-chart');
    if (trendsCtx && spendingData.spending_trends) {
        const trends = spendingData.spending_trends;
        const labels = Object.keys(trends);
        const data = Object.values(trends);
        
        if (charts.spendingTrends) {
            charts.spendingTrends.destroy();
        }
        
        charts.spendingTrends = new Chart(trendsCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Spending',
                    data: data,
                    backgroundColor: '#3498db',
                    borderColor: '#2980b9',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Render investment charts
 */
function renderInvestmentCharts(investmentData) {
    // Asset allocation chart
    const allocationCtx = document.getElementById('asset-allocation-chart');
    if (allocationCtx && investmentData.asset_allocation) {
        const allocation = investmentData.asset_allocation;
        const labels = Object.keys(allocation);
        const data = Object.values(allocation);
        const colors = generateColors(labels.length);
        
        if (charts.assetAllocation) {
            charts.assetAllocation.destroy();
        }
        
        charts.assetAllocation = new Chart(allocationCtx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff'
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
    
    // Performance chart
    const performanceCtx = document.getElementById('performance-chart');
    if (performanceCtx && investmentData.portfolio_performance) {
        const performance = investmentData.portfolio_performance;
        const labels = performance.history?.map(p => p.date) || [];
        const data = performance.history?.map(p => p.value) || [];
        
        if (charts.performance) {
            charts.performance.destroy();
        }
        
        charts.performance = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Portfolio Value',
                    data: data,
                    borderColor: '#27ae60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Switch between tabs
 */
function switchTab(tabName) {
    // Update active tab
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    currentTab = tabName;
    
    // Load tab-specific data if needed
    loadTabData(tabName);
}

/**
 * Load tab-specific data
 */
async function loadTabData(tabName) {
    try {
        let endpoint = '';
        
        switch (tabName) {
            case 'accounts':
                endpoint = '/api/professional/dashboard/account-balances';
                break;
            case 'cashflow':
                endpoint = '/api/professional/dashboard/cash-flow-analysis';
                break;
            case 'spending':
                endpoint = '/api/professional/dashboard/spending-analysis';
                break;
            case 'bills':
                endpoint = '/api/professional/dashboard/bill-prediction';
                break;
            case 'investments':
                endpoint = '/api/professional/dashboard/investment-overview';
                break;
            case 'debt':
                endpoint = '/api/professional/dashboard/debt-management';
                break;
        }
        
        if (endpoint) {
            const response = await fetch(endpoint);
            if (response.ok) {
                const data = await response.json();
                updateTabContent(tabName, data.data);
            }
        }
    } catch (error) {
        console.error(`Error loading ${tabName} data:`, error);
    }
}

/**
 * Refresh dashboard data
 */
async function refreshDashboard() {
    showLoading();
    await loadDashboardData();
    hideLoading();
}

/**
 * Refresh account balances
 */
async function refreshAccountBalances() {
    try {
        const response = await fetch('/api/professional/dashboard/account-balances?refresh=true');
        if (response.ok) {
            const data = await response.json();
            updateAccountBalances(data.data);
        }
    } catch (error) {
        console.error('Error refreshing account balances:', error);
    }
}

/**
 * Export dashboard data
 */
async function exportData() {
    try {
        const format = prompt('Enter export format (json, csv, pdf):', 'json');
        if (!format) return;
        
        const response = await fetch(`/api/professional/dashboard/export?format=${format}`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `mingus-dashboard-${new Date().toISOString().split('T')[0]}.${format}`;
            a.click();
            window.URL.revokeObjectURL(url);
        }
    } catch (error) {
        console.error('Error exporting data:', error);
        showError('Failed to export data. Please try again.');
    }
}

/**
 * Set up auto-refresh
 */
function setupAutoRefresh() {
    // Refresh every 5 minutes
    refreshInterval = setInterval(() => {
        loadDashboardData();
    }, 5 * 60 * 1000);
}

/**
 * Show loading overlay
 */
function showLoading() {
    document.getElementById('loading-overlay').classList.add('show');
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('show');
}

/**
 * Show error message
 */
function showError(message) {
    // Create error notification
    const notification = document.createElement('div');
    notification.className = 'error-notification';
    notification.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Update last updated time
 */
function updateLastUpdated() {
    const now = new Date();
    document.getElementById('update-time').textContent = now.toLocaleTimeString();
}

/**
 * Utility functions
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatChange(change) {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${formatCurrency(change)}`;
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

function calculateSavingsRate(data) {
    const income = data.cash_flow_analysis?.projections?.[0]?.projected_income || 0;
    const expenses = data.cash_flow_analysis?.projections?.[0]?.projected_expenses || 0;
    return income > 0 ? ((income - expenses) / income) * 100 : 0;
}

function generateColors(count) {
    const colors = [
        '#3498db', '#e74c3c', '#27ae60', '#f39c12', '#9b59b6',
        '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#16a085'
    ];
    
    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
}

function getAlertIcon(type) {
    const icons = {
        'balance': 'wallet',
        'bill': 'file-invoice-dollar',
        'spending': 'shopping-cart',
        'investment': 'chart-line',
        'default': 'exclamation-triangle'
    };
    return icons[type] || icons.default;
}

function getInsightIcon(type) {
    const icons = {
        'spending': 'shopping-cart',
        'savings': 'piggy-bank',
        'investment': 'chart-line',
        'debt': 'credit-card',
        'default': 'lightbulb'
    };
    return icons[type] || icons.default;
}

// Placeholder functions for additional features
function updateCategoryBreakdown(categories) {
    const breakdown = document.getElementById('category-breakdown');
    if (breakdown) {
        breakdown.innerHTML = categories.map(category => `
            <div class="category-item">
                <div class="category-info">
                    <h4>${category.category_name}</h4>
                    <p>${category.transaction_count} transactions</p>
                </div>
                <div class="category-amount">
                    <p class="amount">${formatCurrency(category.total_spent)}</p>
                    <p class="trend ${category.trend_percentage >= 0 ? 'positive' : 'negative'}">
                        ${category.trend_percentage >= 0 ? '+' : ''}${category.trend_percentage.toFixed(1)}%
                    </p>
                </div>
            </div>
        `).join('');
    }
}

function updateBillsTimeline(bills) {
    const timeline = document.getElementById('bills-timeline');
    if (timeline && bills) {
        timeline.innerHTML = bills.map(bill => `
            <div class="bill-item">
                <div class="bill-info">
                    <h4>${bill.bill_name}</h4>
                    <p class="bill-merchant">${bill.merchant}</p>
                </div>
                <div class="bill-amount">
                    <p class="amount">${formatCurrency(bill.amount)}</p>
                    <p class="due-date">Due: ${formatDate(bill.due_date)}</p>
                </div>
                <div class="bill-optimization">
                    <span class="optimization-score">${(bill.optimization_score * 100).toFixed(0)}%</span>
                    <p class="savings">Save ${formatCurrency(bill.savings_opportunity)}</p>
                </div>
            </div>
        `).join('');
    }
}

function updatePaymentOptimization(optimizedPayments) {
    const optimization = document.getElementById('payment-optimization');
    if (optimization && optimizedPayments) {
        optimization.innerHTML = `
            <h3>Payment Optimization</h3>
            <div class="optimization-summary">
                <p>Total savings opportunity: ${formatCurrency(optimizedPayments.reduce((sum, p) => sum + p.savings_opportunity, 0))}</p>
                <button class="btn btn-primary" onclick="applyOptimization()">Apply Optimization</button>
            </div>
        `;
    }
}

function updateDebtStrategies(debtData) {
    const snowballPlan = document.getElementById('snowball-plan');
    const avalanchePlan = document.getElementById('avalanche-plan');
    
    if (snowballPlan && debtData.debt_snowball_plan) {
        snowballPlan.innerHTML = debtData.debt_snowball_plan.accounts?.map(account => `
            <div class="debt-account">
                <span class="account-name">${account.name}</span>
                <span class="account-balance">${formatCurrency(account.balance)}</span>
                <span class="payoff-date">${formatDate(account.payoff_date)}</span>
            </div>
        `).join('') || '<p>No debt accounts found</p>';
    }
    
    if (avalanchePlan && debtData.debt_avalanche_plan) {
        avalanchePlan.innerHTML = debtData.debt_avalanche_plan.accounts?.map(account => `
            <div class="debt-account">
                <span class="account-name">${account.name}</span>
                <span class="account-balance">${formatCurrency(account.balance)}</span>
                <span class="payoff-date">${formatDate(account.payoff_date)}</span>
            </div>
        `).join('') || '<p>No debt accounts found</p>';
    }
}

// Additional placeholder functions
function applyInsight(insightId) {
    console.log('Applying insight:', insightId);
    // Implementation would apply the insight
}

function dismissInsight(insightId) {
    console.log('Dismissing insight:', insightId);
    // Implementation would dismiss the insight
}

function applyOptimization() {
    console.log('Applying payment optimization');
    // Implementation would apply payment optimization
}

function addAccount() {
    console.log('Adding new account');
    // Implementation would open account linking flow
}

function optimizePayments() {
    console.log('Optimizing payments');
    // Implementation would run payment optimization
}

function updateCashFlowProjection() {
    console.log('Updating cash flow projection');
    // Implementation would update projection period
}

function updateSpendingAnalysis() {
    console.log('Updating spending analysis');
    // Implementation would update spending period
}

function closeAlerts() {
    document.getElementById('alerts-panel').classList.remove('show');
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
}); 