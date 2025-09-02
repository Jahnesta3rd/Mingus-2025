/**
 * Touch Target Accessibility Validator
 * Comprehensive tool to validate all interactive elements meet 44px minimum touch target standards
 * Tests actual mobile devices and provides detailed reporting
 */

class TouchTargetValidator {
    constructor() {
        this.results = {
            passed: [],
            failed: [],
            warnings: [],
            recommendations: []
        };
        this.minimumSize = 44; // 44px minimum touch target size
        this.minimumSpacing = 8; // 8px minimum spacing between adjacent targets
        this.devicePixelRatio = window.devicePixelRatio || 1;
        this.isMobile = this.detectMobileDevice();
        this.isTouchDevice = this.detectTouchDevice();
        
        this.init();
    }
    
    init() {
        this.announceToScreenReader('Touch target accessibility validator initialized');
        this.runComprehensiveAudit();
        this.generateReport();
        this.setupContinuousMonitoring();
    }
    
    detectMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               window.innerWidth <= 768;
    }
    
    detectTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    
    runComprehensiveAudit() {
        this.announceToScreenReader('Starting comprehensive touch target audit');
        
        // Audit all interactive elements
        this.auditButtons();
        this.auditFormControls();
        this.auditNavigationElements();
        this.auditCustomControls();
        this.auditTouchTargetSpacing();
        this.auditMobileSpecificIssues();
        
        this.announceToScreenReader(`Touch target audit completed. ${this.results.failed.length} issues found.`);
    }
    
    auditButtons() {
        const buttons = document.querySelectorAll('button, .btn, input[type="button"], input[type="submit"], input[type="reset"], input[type="file"]');
        
        buttons.forEach((button, index) => {
            const rect = button.getBoundingClientRect();
            const computedStyle = window.getComputedStyle(button);
            const padding = this.parsePadding(computedStyle.padding);
            
            // Calculate effective touch target size
            const effectiveWidth = rect.width + padding.left + padding.right;
            const effectiveHeight = rect.height + padding.top + padding.bottom;
            
            const result = {
                element: button,
                type: 'button',
                tagName: button.tagName,
                className: button.className,
                text: button.textContent?.trim() || button.value || 'No text',
                position: { x: rect.left, y: rect.top },
                size: { width: effectiveWidth, height: effectiveHeight },
                meetsStandards: effectiveWidth >= this.minimumSize && effectiveHeight >= this.minimumSize,
                issues: []
            };
            
            if (effectiveWidth < this.minimumSize) {
                result.issues.push(`Width ${effectiveWidth.toFixed(1)}px is below minimum ${this.minimumSize}px`);
            }
            
            if (effectiveHeight < this.minimumSize) {
                result.issues.push(`Height ${effectiveHeight.toFixed(1)}px is below minimum ${this.minimumSize}px`);
            }
            
            if (result.meetsStandards) {
                this.results.passed.push(result);
            } else {
                this.results.failed.push(result);
            }
        });
    }
    
    auditFormControls() {
        const formControls = document.querySelectorAll('input, select, textarea, .form-input, .form-select, .form-textarea');
        
        formControls.forEach((control, index) => {
            const rect = control.getBoundingClientRect();
            const computedStyle = window.getComputedStyle(control);
            const padding = this.parsePadding(computedStyle.padding);
            
            // Calculate effective touch target size
            const effectiveWidth = rect.width + padding.left + padding.right;
            const effectiveHeight = rect.height + padding.top + padding.bottom;
            
            const result = {
                element: control,
                type: 'form-control',
                tagName: control.tagName,
                inputType: control.type || 'N/A',
                className: control.className,
                placeholder: control.placeholder || 'No placeholder',
                position: { x: rect.left, y: rect.top },
                size: { width: effectiveWidth, height: effectiveHeight },
                meetsStandards: effectiveWidth >= this.minimumSize && effectiveHeight >= this.minimumSize,
                issues: []
            };
            
            if (effectiveWidth < this.minimumSize) {
                result.issues.push(`Width ${effectiveWidth.toFixed(1)}px is below minimum ${this.minimumSize}px`);
            }
            
            if (effectiveHeight < this.minimumSize) {
                result.issues.push(`Height ${effectiveHeight.toFixed(1)}px is below minimum ${this.minimumSize}px`);
            }
            
            // Check for iOS zoom prevention
            if (control.type === 'text' || control.type === 'email' || control.type === 'password' || control.type === 'number') {
                const fontSize = parseFloat(computedStyle.fontSize);
                if (fontSize < 16) {
                    result.issues.push(`Font size ${fontSize}px may cause zoom on iOS (should be 16px+)`);
                }
            }
            
            if (result.meetsStandards && result.issues.length === 0) {
                this.results.passed.push(result);
            } else {
                this.results.failed.push(result);
            }
        });
    }
    
    auditNavigationElements() {
        const navElements = document.querySelectorAll('.nav-links a, .nav-menu a, .navigation-link, .mobile-menu-btn, .hamburger-menu, .menu-toggle');
        
        navElements.forEach((nav, index) => {
            const rect = nav.getBoundingClientRect();
            const computedStyle = window.getComputedStyle(nav);
            const padding = this.parsePadding(computedStyle.padding);
            
            // Calculate effective touch target size
            const effectiveWidth = rect.width + padding.left + padding.right;
            const effectiveHeight = rect.height + padding.top + padding.bottom;
            
            const result = {
                element: nav,
                type: 'navigation',
                tagName: nav.tagName,
                className: nav.className,
                text: nav.textContent?.trim() || 'No text',
                href: nav.href || 'N/A',
                position: { x: rect.left, y: rect.top },
                size: { width: effectiveWidth, height: effectiveHeight },
                meetsStandards: effectiveWidth >= this.minimumSize && effectiveHeight >= this.minimumSize,
                issues: []
            };
            
            if (effectiveWidth < this.minimumSize) {
                result.issues.push(`Width ${effectiveWidth.toFixed(1)}px is below minimum ${this.minimumSize}px`);
            }
            
            if (effectiveHeight < this.minimumSize) {
                result.issues.push(`Height ${effectiveHeight.toFixed(1)}px is below minimum ${this.minimumSize}px`);
            }
            
            if (result.meetsStandards) {
                this.results.passed.push(result);
            } else {
                this.results.failed.push(result);
            }
        });
    }
    
    auditCustomControls() {
        // Audit custom controls like toggles, sliders, etc.
        const customControls = document.querySelectorAll('.toggle-switch, .switch-toggle, .range-slider, .custom-select, .dropdown-select');
        
        customControls.forEach((control, index) => {
            const rect = control.getBoundingClientRect();
            const computedStyle = window.getComputedStyle(control);
            
            const result = {
                element: control,
                type: 'custom-control',
                tagName: control.tagName,
                className: control.className,
                position: { x: rect.left, y: rect.top },
                size: { width: rect.width, height: rect.height },
                meetsStandards: rect.width >= this.minimumSize && rect.height >= this.minimumSize,
                issues: []
            };
            
            if (rect.width < this.minimumSize) {
                result.issues.push(`Width ${rect.width.toFixed(1)}px is below minimum ${this.minimumSize}px`);
            }
            
            if (rect.height < this.minimumSize) {
                result.issues.push(`Height ${rect.height.toFixed(1)}px is below minimum ${this.minimumSize}px`);
            }
            
            if (result.meetsStandards) {
                this.results.passed.push(result);
            } else {
                this.results.failed.push(result);
            }
        });
    }
    
    auditTouchTargetSpacing() {
        // Check spacing between adjacent touch targets
        const allInteractiveElements = document.querySelectorAll('button, .btn, input, select, textarea, a, .nav-links a, .nav-menu a');
        
        for (let i = 0; i < allInteractiveElements.length - 1; i++) {
            const current = allInteractiveElements[i];
            const next = allInteractiveElements[i + 1];
            
            const currentRect = current.getBoundingClientRect();
            const nextRect = next.getBoundingClientRect();
            
            // Calculate distance between elements
            const distanceX = Math.abs(nextRect.left - (currentRect.left + currentRect.width));
            const distanceY = Math.abs(nextRect.top - (currentRect.top + currentRect.height));
            
            const minDistance = this.minimumSpacing;
            
            if (distanceX < minDistance && distanceY < minDistance) {
                this.results.warnings.push({
                    type: 'spacing',
                    elements: [current, next],
                    distance: { x: distanceX, y: distanceY },
                    issue: `Elements are too close together. Minimum spacing should be ${minDistance}px`
                });
            }
        }
    }
    
    auditMobileSpecificIssues() {
        if (!this.isMobile) return;
        
        // Check for mobile-specific issues
        const smallText = document.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6');
        smallText.forEach(element => {
            const computedStyle = window.getComputedStyle(element);
            const fontSize = parseFloat(computedStyle.fontSize);
            
            if (fontSize < 16) {
                this.results.warnings.push({
                    type: 'mobile-typography',
                    element: element,
                    issue: `Font size ${fontSize}px may be too small for mobile reading`
                });
            }
        });
        
        // Check for proper viewport meta tag
        const viewportMeta = document.querySelector('meta[name="viewport"]');
        if (!viewportMeta || !viewportMeta.content.includes('width=device-width')) {
            this.results.warnings.push({
                type: 'viewport',
                issue: 'Viewport meta tag may not be properly configured for mobile'
            });
        }
    }
    
    parsePadding(paddingString) {
        const values = paddingString.split(' ').map(val => parseFloat(val) || 0);
        return {
            top: values[0] || 0,
            right: values[1] || values[0] || 0,
            bottom: values[2] || values[0] || 0,
            left: values[3] || values[1] || values[0] || 0
        };
    }
    
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            deviceInfo: {
                userAgent: navigator.userAgent,
                isMobile: this.isMobile,
                isTouchDevice: this.isTouchDevice,
                devicePixelRatio: this.devicePixelRatio,
                screenSize: {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            },
            summary: {
                totalElements: this.results.passed.length + this.results.failed.length,
                passed: this.results.passed.length,
                failed: this.results.failed.length,
                warnings: this.results.warnings.length,
                complianceRate: ((this.results.passed.length / (this.results.passed.length + this.results.failed.length)) * 100).toFixed(1)
            },
            results: this.results,
            recommendations: this.generateRecommendations()
        };
        
        this.displayReport(report);
        this.saveReport(report);
        
        return report;
    }
    
    generateRecommendations() {
        const recommendations = [];
        
        if (this.results.failed.length > 0) {
            recommendations.push({
                priority: 'high',
                category: 'touch-target-size',
                title: 'Fix undersized touch targets',
                description: `${this.results.failed.length} elements are below the 44px minimum touch target size`,
                actions: [
                    'Increase min-height and min-width to 44px for all interactive elements',
                    'Use CSS !important declarations to override existing styles',
                    'Test on actual mobile devices to verify touch target sizes'
                ]
            });
        }
        
        if (this.results.warnings.length > 0) {
            recommendations.push({
                priority: 'medium',
                category: 'spacing',
                title: 'Improve touch target spacing',
                description: 'Ensure minimum 8px spacing between adjacent touch targets',
                actions: [
                    'Add margin or gap properties to separate interactive elements',
                    'Use CSS Grid or Flexbox with proper gap values',
                    'Test touch target spacing on various mobile devices'
                ]
            });
        }
        
        if (this.isMobile && this.results.warnings.some(w => w.type === 'mobile-typography')) {
            recommendations.push({
                priority: 'medium',
                category: 'mobile-typography',
                title: 'Optimize mobile typography',
                description: 'Ensure readable font sizes on mobile devices',
                actions: [
                    'Use minimum 16px font size for body text on mobile',
                    'Implement responsive typography scaling',
                    'Test readability on various mobile screen sizes'
                ]
            });
        }
        
        return recommendations;
    }
    
    displayReport(report) {
        // Create visual report display
        const reportContainer = document.createElement('div');
        reportContainer.className = 'touch-target-report';
        reportContainer.innerHTML = `
            <div class="report-header">
                <h2>Touch Target Accessibility Report</h2>
                <div class="report-summary">
                    <div class="summary-item passed">
                        <span class="count">${report.summary.passed}</span>
                        <span class="label">Passed</span>
                    </div>
                    <div class="summary-item failed">
                        <span class="count">${report.summary.failed}</span>
                        <span class="label">Failed</span>
                    </div>
                    <div class="summary-item warnings">
                        <span class="count">${report.summary.warnings}</span>
                        <span class="label">Warnings</span>
                    </div>
                    <div class="summary-item compliance">
                        <span class="count">${report.summary.complianceRate}%</span>
                        <span class="label">Compliance</span>
                    </div>
                </div>
            </div>
            <div class="report-content">
                <div class="report-section">
                    <h3>Failed Elements (${report.summary.failed})</h3>
                    ${this.renderFailedElements(report.results.failed)}
                </div>
                <div class="report-section">
                    <h3>Warnings (${report.summary.warnings})</h3>
                    ${this.renderWarnings(report.results.warnings)}
                </div>
                <div class="report-section">
                    <h3>Recommendations</h3>
                    ${this.renderRecommendations(report.recommendations)}
                </div>
            </div>
        `;
        
        // Add styles
        const styles = document.createElement('style');
        styles.textContent = this.getReportStyles();
        document.head.appendChild(styles);
        
        // Insert report into page
        document.body.appendChild(reportContainer);
        
        // Announce report to screen reader
        this.announceToScreenReader(`Touch target report generated. ${report.summary.failed} elements failed accessibility standards.`);
    }
    
    renderFailedElements(failedElements) {
        if (failedElements.length === 0) {
            return '<p class="no-issues">No failed elements found!</p>';
        }
        
        return failedElements.map(element => `
            <div class="failed-element">
                <div class="element-info">
                    <strong>${element.type}</strong>: ${element.text || element.tagName}
                    <span class="element-class">${element.className}</span>
                </div>
                <div class="element-size">
                    Size: ${element.size.width.toFixed(1)}px × ${element.size.height.toFixed(1)}px
                    <span class="required">Required: ${this.minimumSize}px × ${this.minimumSize}px</span>
                </div>
                <div class="element-issues">
                    ${element.issues.map(issue => `<span class="issue">${issue}</span>`).join('')}
                </div>
            </div>
        `).join('');
    }
    
    renderWarnings(warnings) {
        if (warnings.length === 0) {
            return '<p class="no-warnings">No warnings found!</p>';
        }
        
        return warnings.map(warning => `
            <div class="warning-item">
                <strong>${warning.type}</strong>: ${warning.issue}
            </div>
        `).join('');
    }
    
    renderRecommendations(recommendations) {
        return recommendations.map(rec => `
            <div class="recommendation ${rec.priority}">
                <h4>${rec.title}</h4>
                <p>${rec.description}</p>
                <ul>
                    ${rec.actions.map(action => `<li>${action}</li>`).join('')}
                </ul>
            </div>
        `).join('');
    }
    
    getReportStyles() {
        return `
            .touch-target-report {
                position: fixed;
                top: 20px;
                right: 20px;
                width: 400px;
                max-height: 80vh;
                background: white;
                border: 2px solid #333;
                border-radius: 8px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                z-index: 10000;
                overflow-y: auto;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
            }
            
            .report-header {
                background: #f8f9fa;
                padding: 16px;
                border-bottom: 1px solid #dee2e6;
                border-radius: 8px 8px 0 0;
            }
            
            .report-header h2 {
                margin: 0 0 12px 0;
                font-size: 18px;
                color: #333;
            }
            
            .report-summary {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 8px;
            }
            
            .summary-item {
                text-align: center;
                padding: 8px;
                border-radius: 4px;
                background: white;
            }
            
            .summary-item.passed { background: #d4edda; color: #155724; }
            .summary-item.failed { background: #f8d7da; color: #721c24; }
            .summary-item.warnings { background: #fff3cd; color: #856404; }
            .summary-item.compliance { background: #d1ecf1; color: #0c5460; }
            
            .summary-item .count {
                display: block;
                font-size: 18px;
                font-weight: bold;
            }
            
            .summary-item .label {
                font-size: 12px;
                text-transform: uppercase;
            }
            
            .report-content {
                padding: 16px;
            }
            
            .report-section {
                margin-bottom: 20px;
            }
            
            .report-section h3 {
                margin: 0 0 12px 0;
                font-size: 16px;
                color: #333;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 8px;
            }
            
            .failed-element {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 12px;
                margin-bottom: 8px;
            }
            
            .element-info {
                margin-bottom: 8px;
            }
            
            .element-class {
                color: #6c757d;
                font-size: 12px;
                margin-left: 8px;
            }
            
            .element-size {
                margin-bottom: 8px;
                font-size: 13px;
            }
            
            .required {
                color: #dc3545;
                font-weight: bold;
                margin-left: 8px;
            }
            
            .element-issues {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
            }
            
            .issue {
                background: #dc3545;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 11px;
            }
            
            .warning-item {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
                padding: 8px;
                margin-bottom: 6px;
                color: #856404;
            }
            
            .recommendation {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 12px;
                margin-bottom: 8px;
            }
            
            .recommendation.high {
                border-left: 4px solid #dc3545;
            }
            
            .recommendation.medium {
                border-left: 4px solid #ffc107;
            }
            
            .recommendation h4 {
                margin: 0 0 8px 0;
                font-size: 14px;
                color: #333;
            }
            
            .recommendation p {
                margin: 0 0 8px 0;
                color: #6c757d;
            }
            
            .recommendation ul {
                margin: 0;
                padding-left: 20px;
                color: #6c757d;
            }
            
            .recommendation li {
                margin-bottom: 4px;
            }
            
            .no-issues, .no-warnings {
                color: #6c757d;
                font-style: italic;
                text-align: center;
                padding: 20px;
            }
        `;
    }
    
    saveReport(report) {
        // Save report to localStorage for persistence
        try {
            localStorage.setItem('touchTargetReport', JSON.stringify(report));
        } catch (e) {
            console.warn('Could not save report to localStorage:', e);
        }
        
        // Also log to console for debugging
        console.log('Touch Target Accessibility Report:', report);
    }
    
    setupContinuousMonitoring() {
        // Monitor for dynamic content changes
        const observer = new MutationObserver((mutations) => {
            let shouldReaudit = false;
            
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && 
                    (mutation.addedNodes.length > 0 || mutation.removedNodes.length > 0)) {
                    shouldReaudit = true;
                }
            });
            
            if (shouldReaudit) {
                setTimeout(() => {
                    this.announceToScreenReader('Content changed, re-running touch target audit');
                    this.runComprehensiveAudit();
                }, 1000);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    announceToScreenReader(message) {
        // Create and announce message to screen readers
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }
    
    // Public methods for external use
    getResults() {
        return this.results;
    }
    
    exportReport() {
        const report = this.generateReport();
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `touch-target-report-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }
    
    highlightIssues() {
        // Highlight failed elements on the page
        this.results.failed.forEach(result => {
            if (result.element) {
                result.element.style.outline = '3px solid #dc3545';
                result.element.style.outlineOffset = '2px';
                result.element.setAttribute('title', `Touch target too small: ${result.size.width.toFixed(1)}px × ${result.size.height.toFixed(1)}px (required: ${this.minimumSize}px × ${this.minimumSize}px)`);
            }
        });
        
        this.announceToScreenReader(`Highlighted ${this.results.failed.length} elements with touch target issues`);
    }
    
    clearHighlights() {
        // Remove issue highlights
        this.results.failed.forEach(result => {
            if (result.element) {
                result.element.style.outline = '';
                result.element.style.outlineOffset = '';
                result.element.removeAttribute('title');
            }
        });
        
        this.announceToScreenReader('Cleared all touch target issue highlights');
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.touchTargetValidator = new TouchTargetValidator();
    });
} else {
    window.touchTargetValidator = new TouchTargetValidator();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TouchTargetValidator;
}
