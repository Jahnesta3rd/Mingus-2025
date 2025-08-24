/**
 * MINGUS Analytics Dashboard Configuration
 * Unified Reporting for GA4 + Clarity Integration
 * 
 * Features:
 * - Custom dashboard configurations
 * - Real-time data visualization
 * - Cross-platform metrics correlation
 * - Automated reporting
 * - Alert systems
 * - Data export capabilities
 */

class MingusAnalyticsDashboard {
    constructor(analytics, abTesting) {
        this.analytics = analytics;
        this.abTesting = abTesting;
        
        // Dashboard Configuration
        this.config = {
            dashboards: {
                overview: {
                    name: 'MINGUS Overview Dashboard',
                    description: 'Key performance indicators and user engagement metrics',
                    refreshInterval: 300000, // 5 minutes
                    widgets: [
                        {
                            id: 'conversion_funnel',
                            type: 'funnel',
                            title: 'Conversion Funnel',
                            metrics: ['page_view', 'scroll_engagement', 'cta_click', 'modal_open', 'assessment_selection', 'conversion'],
                            position: { x: 0, y: 0, w: 6, h: 4 }
                        },
                        {
                            id: 'user_engagement',
                            type: 'line_chart',
                            title: 'User Engagement Over Time',
                            metrics: ['scroll_depth', 'time_on_page', 'cta_click'],
                            position: { x: 6, y: 0, w: 6, h: 4 }
                        },
                        {
                            id: 'lead_quality',
                            type: 'gauge',
                            title: 'Lead Quality Score',
                            metrics: ['lead_quality_score'],
                            position: { x: 0, y: 4, w: 4, h: 3 }
                        },
                        {
                            id: 'ab_test_results',
                            type: 'bar_chart',
                            title: 'A/B Test Performance',
                            metrics: ['ab_test_conversion_rates'],
                            position: { x: 4, y: 4, w: 8, h: 3 }
                        }
                    ]
                },
                conversion_optimization: {
                    name: 'Conversion Optimization Dashboard',
                    description: 'Deep dive into conversion metrics and optimization opportunities',
                    refreshInterval: 600000, // 10 minutes
                    widgets: [
                        {
                            id: 'conversion_by_source',
                            type: 'pie_chart',
                            title: 'Conversions by Source',
                            metrics: ['conversion_source_attribution'],
                            position: { x: 0, y: 0, w: 4, h: 4 }
                        },
                        {
                            id: 'cta_performance',
                            type: 'table',
                            title: 'CTA Performance Analysis',
                            metrics: ['cta_click_rate', 'cta_conversion_rate'],
                            position: { x: 4, y: 0, w: 8, h: 4 }
                        },
                        {
                            id: 'user_journey_analysis',
                            type: 'sankey',
                            title: 'User Journey Flow',
                            metrics: ['user_journey_paths'],
                            position: { x: 0, y: 4, w: 12, h: 4 }
                        }
                    ]
                },
                user_behavior: {
                    name: 'User Behavior Dashboard',
                    description: 'Clarity insights and behavioral analysis',
                    refreshInterval: 900000, // 15 minutes
                    widgets: [
                        {
                            id: 'clarity_heatmaps',
                            type: 'heatmap',
                            title: 'Click Heatmaps',
                            metrics: ['clarity_click_heatmap'],
                            position: { x: 0, y: 0, w: 6, h: 4 }
                        },
                        {
                            id: 'scroll_analysis',
                            type: 'line_chart',
                            title: 'Scroll Depth Analysis',
                            metrics: ['scroll_depth_distribution'],
                            position: { x: 6, y: 0, w: 6, h: 4 }
                        },
                        {
                            id: 'session_recordings',
                            type: 'list',
                            title: 'Recent Session Recordings',
                            metrics: ['clarity_session_recordings'],
                            position: { x: 0, y: 4, w: 12, h: 4 }
                        }
                    ]
                },
                performance_monitoring: {
                    name: 'Performance Monitoring Dashboard',
                    description: 'Technical performance and Core Web Vitals',
                    refreshInterval: 300000, // 5 minutes
                    widgets: [
                        {
                            id: 'core_web_vitals',
                            type: 'gauge',
                            title: 'Core Web Vitals',
                            metrics: ['lcp', 'fid', 'cls'],
                            position: { x: 0, y: 0, w: 4, h: 3 }
                        },
                        {
                            id: 'page_load_times',
                            type: 'line_chart',
                            title: 'Page Load Performance',
                            metrics: ['page_load_time', 'time_to_interactive'],
                            position: { x: 4, y: 0, w: 8, h: 3 }
                        },
                        {
                            id: 'error_tracking',
                            type: 'table',
                            title: 'Error Tracking',
                            metrics: ['javascript_errors', 'performance_errors'],
                            position: { x: 0, y: 3, w: 12, h: 3 }
                        }
                    ]
                }
            },
            alerts: {
                conversion_drop: {
                    name: 'Conversion Rate Drop Alert',
                    condition: 'conversion_rate < 0.8 * avg_conversion_rate',
                    threshold: 0.8,
                    notification: {
                        email: true,
                        slack: true,
                        dashboard: true
                    }
                },
                performance_degradation: {
                    name: 'Performance Degradation Alert',
                    condition: 'lcp > 2500 || fid > 100 || cls > 0.1',
                    threshold: {
                        lcp: 2500,
                        fid: 100,
                        cls: 0.1
                    },
                    notification: {
                        email: true,
                        slack: true,
                        dashboard: true
                    }
                },
                ab_test_significance: {
                    name: 'A/B Test Significance Alert',
                    condition: 'ab_test_significance > 0.95',
                    threshold: 0.95,
                    notification: {
                        email: true,
                        slack: true,
                        dashboard: true
                    }
                }
            },
            reports: {
                daily: {
                    name: 'Daily Performance Report',
                    schedule: '0 9 * * *', // 9 AM daily
                    metrics: ['conversion_rate', 'lead_quality_score', 'user_engagement', 'performance_metrics'],
                    format: ['pdf', 'email']
                },
                weekly: {
                    name: 'Weekly Analytics Summary',
                    schedule: '0 10 * * 1', // 10 AM Monday
                    metrics: ['weekly_trends', 'ab_test_results', 'user_behavior_insights'],
                    format: ['pdf', 'email', 'slack']
                },
                monthly: {
                    name: 'Monthly Performance Review',
                    schedule: '0 11 1 * *', // 11 AM 1st of month
                    metrics: ['monthly_kpis', 'trend_analysis', 'optimization_recommendations'],
                    format: ['pdf', 'email', 'presentation']
                }
            },
            exports: {
                formats: ['csv', 'json', 'pdf', 'excel'],
                data_retention: {
                    raw_data: 90, // days
                    aggregated_data: 365, // days
                    reports: 730 // days
                }
            }
        };

        // Dashboard state
        this.state = {
            activeDashboard: 'overview',
            widgets: {},
            alerts: [],
            reports: [],
            isInitialized: false
        };

        // Initialize dashboard
        this.init();
    }

    /**
     * Initialize dashboard
     */
    init() {
        try {
            // Setup dashboard widgets
            this.setupWidgets();
            
            // Setup alerts
            this.setupAlerts();
            
            // Setup reports
            this.setupReports();
            
            // Setup real-time updates
            this.setupRealTimeUpdates();
            
            // Setup data export
            this.setupDataExport();

            this.state.isInitialized = true;
            console.log('MingusAnalyticsDashboard: Initialized successfully');

        } catch (error) {
            console.error('MingusAnalyticsDashboard: Initialization failed', error);
        }
    }

    /**
     * Setup dashboard widgets
     */
    setupWidgets() {
        const dashboard = this.config.dashboards[this.state.activeDashboard];
        
        dashboard.widgets.forEach(widget => {
            this.createWidget(widget);
        });
    }

    /**
     * Create widget
     */
    createWidget(widget) {
        const widgetElement = document.createElement('div');
        widgetElement.id = `widget-${widget.id}`;
        widgetElement.className = 'dashboard-widget';
        widgetElement.style.gridArea = `${widget.position.y + 1} / ${widget.position.x + 1} / span ${widget.position.h} / span ${widget.position.w}`;
        
        widgetElement.innerHTML = `
            <div class="widget-header">
                <h3>${widget.title}</h3>
                <div class="widget-controls">
                    <button class="refresh-widget" data-widget="${widget.id}">↻</button>
                    <button class="export-widget" data-widget="${widget.id}">📊</button>
                </div>
            </div>
            <div class="widget-content" id="widget-content-${widget.id}">
                <div class="loading">Loading...</div>
            </div>
        `;
        
        // Add to dashboard
        const dashboardContainer = document.getElementById('analytics-dashboard');
        if (dashboardContainer) {
            dashboardContainer.appendChild(widgetElement);
        }
        
        // Initialize widget data
        this.loadWidgetData(widget);
        
        // Store widget reference
        this.state.widgets[widget.id] = {
            element: widgetElement,
            config: widget,
            data: null,
            lastUpdate: null
        };
    }

    /**
     * Load widget data
     */
    loadWidgetData(widget) {
        switch (widget.type) {
            case 'funnel':
                this.loadFunnelData(widget);
                break;
            case 'line_chart':
                this.loadLineChartData(widget);
                break;
            case 'gauge':
                this.loadGaugeData(widget);
                break;
            case 'bar_chart':
                this.loadBarChartData(widget);
                break;
            case 'pie_chart':
                this.loadPieChartData(widget);
                break;
            case 'table':
                this.loadTableData(widget);
                break;
            case 'heatmap':
                this.loadHeatmapData(widget);
                break;
            case 'sankey':
                this.loadSankeyData(widget);
                break;
        }
    }

    /**
     * Load funnel data
     */
    loadFunnelData(widget) {
        const analyticsData = this.analytics.getAnalyticsData();
        const funnelData = this.calculateFunnelMetrics(analyticsData);
        
        this.renderFunnelChart(widget.id, funnelData);
    }

    /**
     * Calculate funnel metrics
     */
    calculateFunnelMetrics(analyticsData) {
        const journey = analyticsData.journey;
        const funnelStages = ['page_view', 'scroll_engagement', 'cta_click', 'modal_open', 'assessment_selection', 'conversion'];
        
        const funnelData = funnelStages.map(stage => {
            const stageEvents = journey.filter(event => event.type === stage);
            return {
                stage: stage,
                count: stageEvents.length,
                percentage: journey.length > 0 ? (stageEvents.length / journey.length) * 100 : 0
            };
        });
        
        return funnelData;
    }

    /**
     * Render funnel chart
     */
    renderFunnelChart(widgetId, data) {
        const container = document.getElementById(`widget-content-${widgetId}`);
        
        const chartHtml = `
            <div class="funnel-chart">
                ${data.map(stage => `
                    <div class="funnel-stage">
                        <div class="stage-label">${this.formatStageName(stage.stage)}</div>
                        <div class="stage-bar" style="width: ${stage.percentage}%"></div>
                        <div class="stage-count">${stage.count}</div>
                    </div>
                `).join('')}
            </div>
        `;
        
        container.innerHTML = chartHtml;
    }

    /**
     * Format stage name
     */
    formatStageName(stage) {
        return stage.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Load line chart data
     */
    loadLineChartData(widget) {
        const analyticsData = this.analytics.getAnalyticsData();
        const timeSeriesData = this.calculateTimeSeriesData(analyticsData, widget.metrics);
        
        this.renderLineChart(widget.id, timeSeriesData);
    }

    /**
     * Calculate time series data
     */
    calculateTimeSeriesData(analyticsData, metrics) {
        const journey = analyticsData.journey;
        const timeRanges = this.getTimeRanges();
        
        return timeRanges.map(range => {
            const rangeEvents = journey.filter(event => 
                event.timestamp >= range.start && event.timestamp <= range.end
            );
            
            const data = {};
            metrics.forEach(metric => {
                data[metric] = rangeEvents.filter(event => event.type === metric).length;
            });
            
            return {
                time: range.label,
                ...data
            };
        });
    }

    /**
     * Get time ranges for charts
     */
    getTimeRanges() {
        const now = Date.now();
        const ranges = [];
        
        // Last 24 hours in 2-hour intervals
        for (let i = 23; i >= 0; i--) {
            const start = now - (i + 1) * 2 * 60 * 60 * 1000;
            const end = now - i * 2 * 60 * 60 * 1000;
            ranges.push({
                start,
                end,
                label: new Date(start).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
            });
        }
        
        return ranges;
    }

    /**
     * Render line chart
     */
    renderLineChart(widgetId, data) {
        const container = document.getElementById(`widget-content-${widgetId}`);
        
        // Simple line chart using CSS
        const chartHtml = `
            <div class="line-chart">
                <div class="chart-container">
                    ${data.map(point => `
                        <div class="data-point" style="left: ${point.time}%; height: ${this.calculateHeight(point)}%">
                            <div class="point-value">${this.getMaxValue(point)}</div>
                        </div>
                    `).join('')}
                </div>
                <div class="chart-labels">
                    ${data.map(point => `
                        <div class="time-label">${point.time}</div>
                    `).join('')}
                </div>
            </div>
        `;
        
        container.innerHTML = chartHtml;
    }

    /**
     * Calculate height for chart point
     */
    calculateHeight(point) {
        const maxValue = this.getMaxValue(point);
        const maxPossible = Math.max(...Object.values(point).filter(v => typeof v === 'number'));
        return maxPossible > 0 ? (maxValue / maxPossible) * 100 : 0;
    }

    /**
     * Get max value from data point
     */
    getMaxValue(point) {
        return Math.max(...Object.values(point).filter(v => typeof v === 'number'));
    }

    /**
     * Load gauge data
     */
    loadGaugeData(widget) {
        const analyticsData = this.analytics.getAnalyticsData();
        const gaugeData = this.calculateGaugeMetrics(analyticsData, widget.metrics);
        
        this.renderGauge(widget.id, gaugeData);
    }

    /**
     * Calculate gauge metrics
     */
    calculateGaugeMetrics(analyticsData, metrics) {
        const data = {};
        
        metrics.forEach(metric => {
            switch (metric) {
                case 'lead_quality_score':
                    data[metric] = analyticsData.user.leadQualityScore;
                    break;
                case 'lcp':
                    data[metric] = this.getPerformanceMetric('lcp');
                    break;
                case 'fid':
                    data[metric] = this.getPerformanceMetric('fid');
                    break;
                case 'cls':
                    data[metric] = this.getPerformanceMetric('cls');
                    break;
            }
        });
        
        return data;
    }

    /**
     * Get performance metric
     */
    getPerformanceMetric(metric) {
        // This would typically come from the analytics system
        // For now, return mock data
        const mockData = {
            lcp: 1200,
            fid: 45,
            cls: 0.05
        };
        
        return mockData[metric] || 0;
    }

    /**
     * Render gauge
     */
    renderGauge(widgetId, data) {
        const container = document.getElementById(`widget-content-${widgetId}`);
        
        const gaugeHtml = Object.entries(data).map(([metric, value]) => `
            <div class="gauge-container">
                <div class="gauge-label">${this.formatMetricName(metric)}</div>
                <div class="gauge">
                    <div class="gauge-fill" style="transform: rotate(${this.calculateGaugeRotation(value, metric)}deg)"></div>
                    <div class="gauge-value">${this.formatGaugeValue(value, metric)}</div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = gaugeHtml;
    }

    /**
     * Format metric name
     */
    formatMetricName(metric) {
        return metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Calculate gauge rotation
     */
    calculateGaugeRotation(value, metric) {
        const maxValues = {
            lead_quality_score: 100,
            lcp: 2500,
            fid: 100,
            cls: 0.1
        };
        
        const maxValue = maxValues[metric] || 100;
        const percentage = Math.min(value / maxValue, 1);
        return percentage * 180; // 180 degrees for semi-circle
    }

    /**
     * Format gauge value
     */
    formatGaugeValue(value, metric) {
        switch (metric) {
            case 'lcp':
                return `${value}ms`;
            case 'fid':
                return `${value}ms`;
            case 'cls':
                return value.toFixed(3);
            default:
                return value;
        }
    }

    /**
     * Setup alerts
     */
    setupAlerts() {
        // Monitor for alert conditions
        setInterval(() => {
            this.checkAlerts();
        }, 60000); // Check every minute
    }

    /**
     * Check alerts
     */
    checkAlerts() {
        Object.entries(this.config.alerts).forEach(([alertId, alert]) => {
            const condition = this.evaluateAlertCondition(alert.condition);
            
            if (condition) {
                this.triggerAlert(alertId, alert);
            }
        });
    }

    /**
     * Evaluate alert condition
     */
    evaluateAlertCondition(condition) {
        // Simple condition evaluation
        // In a real implementation, this would be more sophisticated
        const analyticsData = this.analytics.getAnalyticsData();
        
        if (condition.includes('conversion_rate')) {
            const conversionRate = this.calculateConversionRate(analyticsData);
            const avgRate = 0.05; // Mock average rate
            return conversionRate < 0.8 * avgRate;
        }
        
        if (condition.includes('lcp')) {
            const lcp = this.getPerformanceMetric('lcp');
            return lcp > 2500;
        }
        
        return false;
    }

    /**
     * Calculate conversion rate
     */
    calculateConversionRate(analyticsData) {
        const journey = analyticsData.journey;
        const conversions = journey.filter(event => event.type === 'conversion').length;
        const totalSessions = analyticsData.session ? 1 : 0; // Simplified
        
        return totalSessions > 0 ? conversions / totalSessions : 0;
    }

    /**
     * Trigger alert
     */
    triggerAlert(alertId, alert) {
        const alertData = {
            id: alertId,
            name: alert.name,
            condition: alert.condition,
            timestamp: Date.now(),
            severity: 'warning'
        };
        
        // Add to alerts list
        this.state.alerts.push(alertData);
        
        // Send notifications
        this.sendAlertNotifications(alert, alertData);
        
        // Update dashboard
        this.updateAlertWidget(alertData);
        
        console.warn(`Alert triggered: ${alert.name}`, alertData);
    }

    /**
     * Send alert notifications
     */
    sendAlertNotifications(alert, alertData) {
        if (alert.notification.email) {
            this.sendEmailAlert(alertData);
        }
        
        if (alert.notification.slack) {
            this.sendSlackAlert(alertData);
        }
        
        if (alert.notification.dashboard) {
            this.showDashboardAlert(alertData);
        }
    }

    /**
     * Send email alert
     */
    sendEmailAlert(alertData) {
        // Implementation would send email via API
        console.log('Email alert sent:', alertData);
    }

    /**
     * Send Slack alert
     */
    sendSlackAlert(alertData) {
        // Implementation would send Slack message via webhook
        console.log('Slack alert sent:', alertData);
    }

    /**
     * Show dashboard alert
     */
    showDashboardAlert(alertData) {
        const alertElement = document.createElement('div');
        alertElement.className = 'dashboard-alert';
        alertElement.innerHTML = `
            <div class="alert-header">
                <span class="alert-title">${alertData.name}</span>
                <button class="alert-close">×</button>
            </div>
            <div class="alert-content">
                <p>Alert condition: ${alertData.condition}</p>
                <p>Time: ${new Date(alertData.timestamp).toLocaleString()}</p>
            </div>
        `;
        
        // Add to dashboard
        const dashboardContainer = document.getElementById('analytics-dashboard');
        if (dashboardContainer) {
            dashboardContainer.appendChild(alertElement);
        }
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            alertElement.remove();
        }, 10000);
    }

    /**
     * Update alert widget
     */
    updateAlertWidget(alertData) {
        const alertWidget = this.state.widgets['alerts'];
        if (alertWidget) {
            this.loadWidgetData(alertWidget.config);
        }
    }

    /**
     * Setup reports
     */
    setupReports() {
        // Schedule automated reports
        Object.entries(this.config.reports).forEach(([reportId, report]) => {
            this.scheduleReport(reportId, report);
        });
    }

    /**
     * Schedule report
     */
    scheduleReport(reportId, report) {
        // In a real implementation, this would use a proper scheduler
        // For now, we'll simulate scheduling
        console.log(`Report scheduled: ${report.name} - ${report.schedule}`);
    }

    /**
     * Setup real-time updates
     */
    setupRealTimeUpdates() {
        // Update dashboard widgets periodically
        setInterval(() => {
            this.updateDashboard();
        }, 300000); // Update every 5 minutes
    }

    /**
     * Update dashboard
     */
    updateDashboard() {
        Object.values(this.state.widgets).forEach(widget => {
            this.loadWidgetData(widget.config);
        });
    }

    /**
     * Setup data export
     */
    setupDataExport() {
        // Add export functionality to dashboard
        this.addExportControls();
    }

    /**
     * Add export controls
     */
    addExportControls() {
        const exportContainer = document.createElement('div');
        exportContainer.className = 'dashboard-export-controls';
        exportContainer.innerHTML = `
            <div class="export-section">
                <h4>Export Data</h4>
                <div class="export-buttons">
                    <button class="export-btn" data-format="csv">Export CSV</button>
                    <button class="export-btn" data-format="json">Export JSON</button>
                    <button class="export-btn" data-format="pdf">Export PDF</button>
                    <button class="export-btn" data-format="excel">Export Excel</button>
                </div>
            </div>
        `;
        
        // Add event listeners
        exportContainer.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const format = btn.dataset.format;
                this.exportDashboardData(format);
            });
        });
        
        // Add to dashboard
        const dashboardContainer = document.getElementById('analytics-dashboard');
        if (dashboardContainer) {
            dashboardContainer.appendChild(exportContainer);
        }
    }

    /**
     * Export dashboard data
     */
    exportDashboardData(format) {
        const data = {
            dashboard: this.state.activeDashboard,
            timestamp: Date.now(),
            analytics: this.analytics.getAnalyticsData(),
            abTesting: this.abTesting ? this.abTesting.getAllTestResults() : null,
            widgets: this.state.widgets,
            alerts: this.state.alerts
        };
        
        switch (format) {
            case 'csv':
                this.exportAsCSV(data);
                break;
            case 'json':
                this.exportAsJSON(data);
                break;
            case 'pdf':
                this.exportAsPDF(data);
                break;
            case 'excel':
                this.exportAsExcel(data);
                break;
        }
    }

    /**
     * Export as CSV
     */
    exportAsCSV(data) {
        // Implementation for CSV export
        console.log('Exporting as CSV:', data);
    }

    /**
     * Export as JSON
     */
    exportAsJSON(data) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `mingus_dashboard_${Date.now()}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }

    /**
     * Export as PDF
     */
    exportAsPDF(data) {
        // Implementation for PDF export
        console.log('Exporting as PDF:', data);
    }

    /**
     * Export as Excel
     */
    exportAsExcel(data) {
        // Implementation for Excel export
        console.log('Exporting as Excel:', data);
    }

    /**
     * Switch dashboard
     */
    switchDashboard(dashboardId) {
        this.state.activeDashboard = dashboardId;
        
        // Clear current widgets
        this.clearWidgets();
        
        // Load new dashboard
        this.setupWidgets();
    }

    /**
     * Clear widgets
     */
    clearWidgets() {
        Object.values(this.state.widgets).forEach(widget => {
            if (widget.element && widget.element.parentNode) {
                widget.element.parentNode.removeChild(widget.element);
            }
        });
        
        this.state.widgets = {};
    }

    /**
     * Get dashboard data
     */
    getDashboardData() {
        return {
            activeDashboard: this.state.activeDashboard,
            widgets: this.state.widgets,
            alerts: this.state.alerts,
            config: this.config
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MingusAnalyticsDashboard;
}
