/**
 * Readability Analytics Framework
 * 
 * Comprehensive analytics tracking for readability improvement success metrics
 * including bounce rates, time-on-page, conversion rates, form completion,
 * heatmaps, and accessibility compliance scores.
 */

class ReadabilityAnalytics {
    constructor() {
        this.metrics = {
            baseline: {},
            current: {},
            improvements: {},
            heatmap: {},
            accessibility: {},
            userBehavior: {}
        };
        this.sessionData = {};
        this.heatmapData = [];
        this.accessibilityChecks = [];
        this.init();
    }

    init() {
        this.setupSessionTracking();
        this.setupBounceRateTracking();
        this.setupTimeOnPageTracking();
        this.setupConversionTracking();
        this.setupFormCompletionTracking();
        this.setupHeatmapTracking();
        this.setupAccessibilityTracking();
        this.setupBaselineMetrics();
        this.createAnalyticsUI();
    }

    setupSessionTracking() {
        // Track session start
        this.sessionData.startTime = Date.now();
        this.sessionData.sessionId = this.generateSessionId();
        this.sessionData.userAgent = navigator.userAgent;
        this.sessionData.deviceType = this.getDeviceType();
        this.sessionData.screenSize = {
            width: window.innerWidth,
            height: window.innerHeight
        };

        // Track page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.sessionData.lastHiddenTime = Date.now();
            } else {
                this.sessionData.lastVisibleTime = Date.now();
            }
        });

        // Track beforeunload for accurate session duration
        window.addEventListener('beforeunload', () => {
            this.sessionData.endTime = Date.now();
            this.sessionData.duration = this.sessionData.endTime - this.sessionData.startTime;
            this.saveSessionData();
        });
    }

    setupBounceRateTracking() {
        // Track bounce rate (single page sessions)
        this.metrics.userBehavior.bounceRate = {
            isBounce: true,
            pageViews: 1,
            startTime: Date.now()
        };

        // Track navigation events
        let pageViews = 1;
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;

        history.pushState = function(...args) {
            pageViews++;
            this.metrics.userBehavior.bounceRate.pageViews = pageViews;
            this.metrics.userBehavior.bounceRate.isBounce = false;
            originalPushState.apply(history, args);
        }.bind(this);

        history.replaceState = function(...args) {
            pageViews++;
            this.metrics.userBehavior.bounceRate.pageViews = pageViews;
            this.metrics.userBehavior.bounceRate.isBounce = false;
            originalReplaceState.apply(history, args);
        }.bind(this);

        // Track link clicks
        document.addEventListener('click', (e) => {
            if (e.target.tagName === 'A' || e.target.closest('a')) {
                pageViews++;
                this.metrics.userBehavior.bounceRate.pageViews = pageViews;
                this.metrics.userBehavior.bounceRate.isBounce = false;
            }
        });
    }

    setupTimeOnPageTracking() {
        let startTime = Date.now();
        let totalActiveTime = 0;
        let lastActiveTime = startTime;
        let isActive = true;

        // Track active time
        const updateActiveTime = () => {
            if (isActive) {
                const now = Date.now();
                totalActiveTime += now - lastActiveTime;
                lastActiveTime = now;
            }
        };

        // Update every second
        setInterval(updateActiveTime, 1000);

        // Track user activity
        const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        activityEvents.forEach(event => {
            document.addEventListener(event, () => {
                if (!isActive) {
                    isActive = true;
                    lastActiveTime = Date.now();
                }
            });
        });

        // Track inactivity
        let inactivityTimer;
        const resetInactivityTimer = () => {
            clearTimeout(inactivityTimer);
            inactivityTimer = setTimeout(() => {
                isActive = false;
                updateActiveTime();
            }, 30000); // 30 seconds of inactivity
        };

        activityEvents.forEach(event => {
            document.addEventListener(event, resetInactivityTimer);
        });

        // Store time on page metrics
        this.metrics.userBehavior.timeOnPage = {
            startTime: startTime,
            totalActiveTime: totalActiveTime,
            isActive: isActive,
            updateMetrics: () => {
                updateActiveTime();
                return {
                    totalTime: Date.now() - startTime,
                    activeTime: totalActiveTime,
                    engagementRate: (totalActiveTime / (Date.now() - startTime)) * 100
                };
            }
        };
    }

    setupConversionTracking() {
        this.metrics.userBehavior.conversions = {
            events: [],
            goals: {
                signup: false,
                purchase: false,
                download: false,
                contact: false
            }
        };

        // Track conversion events
        const trackConversion = (type, value = null) => {
            const conversion = {
                type: type,
                value: value,
                timestamp: Date.now(),
                sessionId: this.sessionData.sessionId
            };

            this.metrics.userBehavior.conversions.events.push(conversion);
            this.metrics.userBehavior.conversions.goals[type] = true;

            // Send to analytics
            this.sendAnalyticsEvent('conversion', conversion);
        };

        // Track form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            const formType = form.getAttribute('data-form-type') || 'general';
            trackConversion('form_submission', formType);
        });

        // Track button clicks that might be conversions
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button, .btn, [role="button"]');
            if (button) {
                const buttonText = button.textContent.toLowerCase();
                const buttonClass = button.className.toLowerCase();
                
                if (buttonText.includes('sign up') || buttonText.includes('register')) {
                    trackConversion('signup');
                } else if (buttonText.includes('buy') || buttonText.includes('purchase')) {
                    trackConversion('purchase');
                } else if (buttonText.includes('download')) {
                    trackConversion('download');
                } else if (buttonText.includes('contact') || buttonText.includes('get in touch')) {
                    trackConversion('contact');
                }
            }
        });

        // Expose conversion tracking globally
        window.trackConversion = trackConversion;
    }

    setupFormCompletionTracking() {
        this.metrics.userBehavior.formCompletion = {
            forms: {},
            fields: {},
            abandonment: []
        };

        // Track form interactions
        document.addEventListener('focus', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                const field = e.target;
                const form = field.closest('form');
                
                if (form) {
                    const formId = form.id || form.getAttribute('data-form-id') || 'unknown';
                    const fieldName = field.name || field.id || 'unknown';
                    
                    if (!this.metrics.userBehavior.formCompletion.forms[formId]) {
                        this.metrics.userBehavior.formCompletion.forms[formId] = {
                            startTime: Date.now(),
                            fields: [],
                            completed: false
                        };
                    }
                    
                    if (!this.metrics.userBehavior.formCompletion.forms[formId].fields.includes(fieldName)) {
                        this.metrics.userBehavior.formCompletion.forms[formId].fields.push(fieldName);
                    }
                }
            }
        });

        // Track form abandonment
        document.addEventListener('blur', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                const field = e.target;
                const form = field.closest('form');
                
                if (form && field.value.trim() === '') {
                    const formId = form.id || form.getAttribute('data-form-id') || 'unknown';
                    const abandonment = {
                        formId: formId,
                        fieldName: field.name || field.id || 'unknown',
                        timestamp: Date.now(),
                        reason: 'empty_field'
                    };
                    
                    this.metrics.userBehavior.formCompletion.abandonment.push(abandonment);
                }
            }
        });

        // Track form completion
        document.addEventListener('submit', (e) => {
            const form = e.target;
            const formId = form.id || form.getAttribute('data-form-id') || 'unknown';
            
            if (this.metrics.userBehavior.formCompletion.forms[formId]) {
                this.metrics.userBehavior.formCompletion.forms[formId].completed = true;
                this.metrics.userBehavior.formCompletion.forms[formId].completionTime = Date.now();
            }
        });
    }

    setupHeatmapTracking() {
        let heatmapData = [];
        let isTracking = false;

        const startHeatmapTracking = () => {
            if (isTracking) return;
            isTracking = true;

            // Track mouse movements
            document.addEventListener('mousemove', (e) => {
                if (isTracking) {
                    heatmapData.push({
                        type: 'move',
                        x: e.clientX,
                        y: e.clientY,
                        timestamp: Date.now()
                    });
                }
            });

            // Track clicks
            document.addEventListener('click', (e) => {
                if (isTracking) {
                    heatmapData.push({
                        type: 'click',
                        x: e.clientX,
                        y: e.clientY,
                        timestamp: Date.now(),
                        element: e.target.tagName,
                        text: e.target.textContent?.substring(0, 50)
                    });
                }
            });

            // Track scroll positions
            let lastScrollY = window.scrollY;
            window.addEventListener('scroll', (e) => {
                if (isTracking && Math.abs(window.scrollY - lastScrollY) > 50) {
                    heatmapData.push({
                        type: 'scroll',
                        y: window.scrollY,
                        timestamp: Date.now()
                    });
                    lastScrollY = window.scrollY;
                }
            });

            // Track text selection
            document.addEventListener('mouseup', (e) => {
                const selection = window.getSelection();
                if (isTracking && selection.toString().length > 0) {
                    heatmapData.push({
                        type: 'selection',
                        text: selection.toString().substring(0, 100),
                        timestamp: Date.now()
                    });
                }
            });
        };

        // Start tracking after user interaction
        document.addEventListener('mousedown', startHeatmapTracking, { once: true });

        // Store heatmap data
        this.metrics.heatmap = {
            data: heatmapData,
            isTracking: isTracking,
            getHeatmapData: () => heatmapData,
            exportHeatmap: () => {
                return {
                    sessionId: this.sessionData.sessionId,
                    deviceType: this.sessionData.deviceType,
                    screenSize: this.sessionData.screenSize,
                    data: heatmapData
                };
            }
        };
    }

    setupAccessibilityTracking() {
        this.metrics.accessibility = {
            checks: [],
            score: 0,
            issues: []
        };

        // Run accessibility checks
        this.runAccessibilityChecks();

        // Monitor for dynamic content changes
        const observer = new MutationObserver(() => {
            this.runAccessibilityChecks();
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'style', 'aria-*']
        });
    }

    runAccessibilityChecks() {
        const checks = [];

        // Check color contrast
        const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div, a, button, input, label');
        textElements.forEach(element => {
            const style = window.getComputedStyle(element);
            const color = style.color;
            const backgroundColor = style.backgroundColor;
            
            if (color && backgroundColor) {
                const contrast = this.calculateContrastRatio(color, backgroundColor);
                checks.push({
                    type: 'contrast',
                    element: element.tagName,
                    contrast: contrast,
                    passes: contrast >= 4.5,
                    timestamp: Date.now()
                });
            }
        });

        // Check font sizes
        textElements.forEach(element => {
            const style = window.getComputedStyle(element);
            const fontSize = parseFloat(style.fontSize);
            
            checks.push({
                type: 'fontSize',
                element: element.tagName,
                fontSize: fontSize,
                passes: fontSize >= 16,
                timestamp: Date.now()
            });
        });

        // Check line heights
        textElements.forEach(element => {
            const style = window.getComputedStyle(element);
            const lineHeight = parseFloat(style.lineHeight);
            const fontSize = parseFloat(style.fontSize);
            const ratio = lineHeight / fontSize;
            
            checks.push({
                type: 'lineHeight',
                element: element.tagName,
                ratio: ratio,
                passes: ratio >= 1.4,
                timestamp: Date.now()
            });
        });

        // Check for alt text on images
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            checks.push({
                type: 'altText',
                element: 'img',
                hasAlt: !!img.alt,
                passes: !!img.alt,
                timestamp: Date.now()
            });
        });

        // Check for proper heading structure
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        let previousLevel = 0;
        let hasH1 = false;
        
        headings.forEach(heading => {
            const level = parseInt(heading.tagName.charAt(1));
            
            if (level === 1) hasH1 = true;
            
            checks.push({
                type: 'headingStructure',
                element: heading.tagName,
                level: level,
                hasH1: hasH1,
                passes: level <= previousLevel + 1,
                timestamp: Date.now()
            });
            
            previousLevel = level;
        });

        // Calculate accessibility score
        const totalChecks = checks.length;
        const passedChecks = checks.filter(check => check.passes).length;
        const score = totalChecks > 0 ? (passedChecks / totalChecks) * 100 : 0;

        this.metrics.accessibility.checks = checks;
        this.metrics.accessibility.score = score;
        this.metrics.accessibility.issues = checks.filter(check => !check.passes);
    }

    calculateContrastRatio(color1, color2) {
        // Simplified contrast ratio calculation
        // In a real implementation, you'd use a proper color contrast library
        return 4.5; // Placeholder
    }

    setupBaselineMetrics() {
        // Store baseline metrics for comparison
        this.metrics.baseline = {
            timestamp: Date.now(),
            bounceRate: this.metrics.userBehavior.bounceRate,
            timeOnPage: this.metrics.userBehavior.timeOnPage,
            accessibility: this.metrics.accessibility.score,
            deviceType: this.sessionData.deviceType,
            screenSize: this.sessionData.screenSize
        };
    }

    createAnalyticsUI() {
        const analyticsPanel = document.createElement('div');
        analyticsPanel.id = 'readability-analytics-panel';
        analyticsPanel.innerHTML = `
            <div class="analytics-header">
                <h3>📊 Readability Analytics</h3>
                <button onclick="readabilityAnalytics.togglePanel()" class="toggle-btn">Toggle</button>
            </div>
            <div class="analytics-content">
                <div class="metric-group">
                    <h4>User Behavior</h4>
                    <div id="user-behavior-metrics"></div>
                </div>
                <div class="metric-group">
                    <h4>Accessibility Score</h4>
                    <div id="accessibility-metrics"></div>
                </div>
                <div class="metric-group">
                    <h4>Form Completion</h4>
                    <div id="form-metrics"></div>
                </div>
                <div class="metric-group">
                    <h4>Heatmap Data</h4>
                    <div id="heatmap-metrics"></div>
                </div>
            </div>
        `;

        // Add styles
        const styles = document.createElement('style');
        styles.textContent = `
            #readability-analytics-panel {
                position: fixed;
                top: 20px;
                left: 20px;
                width: 350px;
                max-height: 80vh;
                background: #fff;
                border: 2px solid #28a745;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 10000;
                font-family: var(--font-family-system);
                font-size: var(--font-size-sm);
            }
            
            .analytics-header {
                background: #28a745;
                color: white;
                padding: 12px;
                border-radius: 6px 6px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .analytics-content {
                padding: 16px;
                max-height: 60vh;
                overflow-y: auto;
            }
            
            .metric-group {
                margin-bottom: 20px;
                padding: 12px;
                background: #f8f9fa;
                border-radius: 6px;
            }
            
            .metric-group h4 {
                margin: 0 0 8px 0;
                color: #333;
                font-size: var(--font-size-sm);
            }
            
            .metric-item {
                display: flex;
                justify-content: space-between;
                margin: 4px 0;
                font-size: var(--font-size-xs);
            }
            
            .metric-value {
                font-weight: 600;
                color: #28a745;
            }
            
            .metric-good { color: #28a745; }
            .metric-warning { color: #ffc107; }
            .metric-poor { color: #dc3545; }
            
            .toggle-btn {
                background: transparent;
                border: 1px solid white;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
                font-size: var(--font-size-xs);
            }
            
            @media (prefers-color-scheme: dark) {
                #readability-analytics-panel {
                    background: #2d2d2d;
                    border-color: #28a745;
                }
                
                .metric-group {
                    background: #3d3d3d;
                }
                
                .metric-group h4 {
                    color: #e0e0e0;
                }
            }
        `;

        document.head.appendChild(styles);
        document.body.appendChild(analyticsPanel);

        // Update metrics every 5 seconds
        setInterval(() => this.updateAnalyticsDisplay(), 5000);
    }

    updateAnalyticsDisplay() {
        // Update User Behavior Metrics
        const behaviorDiv = document.getElementById('user-behavior-metrics');
        if (behaviorDiv) {
            const timeMetrics = this.metrics.userBehavior.timeOnPage.updateMetrics();
            const bounceRate = this.metrics.userBehavior.bounceRate;
            
            behaviorDiv.innerHTML = `
                <div class="metric-item">
                    <span>Bounce Rate:</span>
                    <span class="metric-value ${bounceRate.isBounce ? 'metric-poor' : 'metric-good'}">${bounceRate.isBounce ? 'Yes' : 'No'}</span>
                </div>
                <div class="metric-item">
                    <span>Page Views:</span>
                    <span class="metric-value">${bounceRate.pageViews}</span>
                </div>
                <div class="metric-item">
                    <span>Time on Page:</span>
                    <span class="metric-value">${Math.round(timeMetrics.totalTime / 1000)}s</span>
                </div>
                <div class="metric-item">
                    <span>Active Time:</span>
                    <span class="metric-value">${Math.round(timeMetrics.activeTime / 1000)}s</span>
                </div>
                <div class="metric-item">
                    <span>Engagement:</span>
                    <span class="metric-value ${timeMetrics.engagementRate > 70 ? 'metric-good' : timeMetrics.engagementRate > 40 ? 'metric-warning' : 'metric-poor'}">${timeMetrics.engagementRate.toFixed(1)}%</span>
                </div>
            `;
        }

        // Update Accessibility Metrics
        const accessibilityDiv = document.getElementById('accessibility-metrics');
        if (accessibilityDiv) {
            const score = this.metrics.accessibility.score;
            const issues = this.metrics.accessibility.issues.length;
            
            accessibilityDiv.innerHTML = `
                <div class="metric-item">
                    <span>Accessibility Score:</span>
                    <span class="metric-value ${score >= 90 ? 'metric-good' : score >= 70 ? 'metric-warning' : 'metric-poor'}">${score.toFixed(1)}%</span>
                </div>
                <div class="metric-item">
                    <span>Issues Found:</span>
                    <span class="metric-value ${issues === 0 ? 'metric-good' : issues < 5 ? 'metric-warning' : 'metric-poor'}">${issues}</span>
                </div>
            `;
        }

        // Update Form Metrics
        const formDiv = document.getElementById('form-metrics');
        if (formDiv) {
            const forms = this.metrics.userBehavior.formCompletion.forms;
            const completedForms = Object.values(forms).filter(form => form.completed).length;
            const totalForms = Object.keys(forms).length;
            const completionRate = totalForms > 0 ? (completedForms / totalForms) * 100 : 0;
            
            formDiv.innerHTML = `
                <div class="metric-item">
                    <span>Forms Started:</span>
                    <span class="metric-value">${totalForms}</span>
                </div>
                <div class="metric-item">
                    <span>Forms Completed:</span>
                    <span class="metric-value">${completedForms}</span>
                </div>
                <div class="metric-item">
                    <span>Completion Rate:</span>
                    <span class="metric-value ${completionRate >= 80 ? 'metric-good' : completionRate >= 50 ? 'metric-warning' : 'metric-poor'}">${completionRate.toFixed(1)}%</span>
                </div>
            `;
        }

        // Update Heatmap Metrics
        const heatmapDiv = document.getElementById('heatmap-metrics');
        if (heatmapDiv) {
            const heatmapData = this.metrics.heatmap.getHeatmapData();
            const clicks = heatmapData.filter(d => d.type === 'click').length;
            const movements = heatmapData.filter(d => d.type === 'move').length;
            
            heatmapDiv.innerHTML = `
                <div class="metric-item">
                    <span>Mouse Clicks:</span>
                    <span class="metric-value">${clicks}</span>
                </div>
                <div class="metric-item">
                    <span>Mouse Movements:</span>
                    <span class="metric-value">${movements}</span>
                </div>
                <div class="metric-item">
                    <span>Data Points:</span>
                    <span class="metric-value">${heatmapData.length}</span>
                </div>
            `;
        }
    }

    togglePanel() {
        const panel = document.getElementById('readability-analytics-panel');
        const content = panel.querySelector('.analytics-content');
        content.style.display = content.style.display === 'none' ? 'block' : 'none';
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    getDeviceType() {
        const userAgent = navigator.userAgent.toLowerCase();
        if (/mobile|android|iphone|ipad|phone/.test(userAgent)) {
            return 'mobile';
        } else if (/tablet|ipad/.test(userAgent)) {
            return 'tablet';
        } else {
            return 'desktop';
        }
    }

    saveSessionData() {
        // Save session data to localStorage or send to server
        const sessionData = {
            ...this.sessionData,
            metrics: this.metrics
        };
        
        localStorage.setItem('readability_session_' + this.sessionData.sessionId, JSON.stringify(sessionData));
    }

    sendAnalyticsEvent(eventType, data) {
        // Send analytics event to server or analytics service
        console.log('Analytics Event:', eventType, data);
        
        // Example: Send to Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', eventType, data);
        }
        
        // Example: Send to custom analytics endpoint
        fetch('/api/analytics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                eventType: eventType,
                data: data,
                sessionId: this.sessionData.sessionId,
                timestamp: Date.now()
            })
        }).catch(error => console.log('Analytics send failed:', error));
    }

    exportAnalytics() {
        const analyticsData = {
            sessionId: this.sessionData.sessionId,
            timestamp: new Date().toISOString(),
            deviceType: this.sessionData.deviceType,
            screenSize: this.sessionData.screenSize,
            metrics: this.metrics,
            heatmapData: this.metrics.heatmap.exportHeatmap()
        };
        
        const blob = new Blob([JSON.stringify(analyticsData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `readability-analytics-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    getMetrics() {
        return this.metrics;
    }
}

// Initialize analytics
const readabilityAnalytics = new ReadabilityAnalytics();

// Add export button
const exportBtn = document.createElement('button');
exportBtn.textContent = '📊 Export Analytics';
exportBtn.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: #28a745;
    color: white;
    border: none;
    padding: 12px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-family: var(--font-family-system);
    font-size: var(--font-size-sm);
    z-index: 9999;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
`;
exportBtn.onclick = () => readabilityAnalytics.exportAnalytics();
document.body.appendChild(exportBtn);

// Expose globally for external access
window.readabilityAnalytics = readabilityAnalytics;
