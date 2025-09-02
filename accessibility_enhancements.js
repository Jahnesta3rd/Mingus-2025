// Mingus Financial Services - Accessibility Enhancements
// WCAG 2.1 AA Compliance Implementation

(function() {
    'use strict';
    
    // Accessibility configuration
    const ACCESSIBILITY_CONFIG = {
        keyboardShortcuts: {
            "navigation": {
                "dashboard": "Alt + D",
                "assessments": "Alt + A", 
                "analytics": "Alt + L",
                "profile": "Alt + P",
                "help": "F1",
                "search": "Ctrl + K"
            },
            "financial_tools": {
                "income_comparison": "Alt + I",
                "tax_calculator": "Alt + T",
                "budget_planner": "Alt + B",
                "investment_analyzer": "Alt + V",
                "debt_payoff": "Alt + E",
                "retirement_planner": "Alt + R"
            },
            "actions": {
                "save": "Ctrl + S",
                "print": "Ctrl + P",
                "export": "Ctrl + E",
                "refresh": "F5",
                "close": "Escape",
                "submit": "Enter"
            }
        },
        focusIndicatorClass: 'accessibility-focus',
        skipLinkId: 'skip-to-main',
        liveRegionId: 'accessibility-live-region',
        highContrastClass: 'high-contrast-mode',
        reducedMotionClass: 'reduced-motion'
    };
    
    // Initialize accessibility features
    function initAccessibility() {
        setupKeyboardNavigation();
        setupFocusIndicators();
        setupSkipLinks();
        setupLiveRegions();
        setupHighContrastToggle();
        setupReducedMotionSupport();
        setupScreenReaderAnnouncements();
        setupFormAccessibility();
        setupTableAccessibility();
        setupImageAccessibility();
        setupChartAccessibility();
        setupModalAccessibility();
        setupNavigationAccessibility();
    }
    
    // Keyboard navigation setup
    function setupKeyboardNavigation() {
        // Add keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Navigation shortcuts
            if (e.altKey) {
                switch(e.key.toLowerCase()) {
                    case 'd':
                        e.preventDefault();
                        navigateToDashboard();
                        break;
                    case 'a':
                        e.preventDefault();
                        navigateToAssessments();
                        break;
                    case 'l':
                        e.preventDefault();
                        navigateToAnalytics();
                        break;
                    case 'p':
                        e.preventDefault();
                        navigateToProfile();
                        break;
                }
            }
            
            // Financial tools shortcuts
            if (e.altKey) {
                switch(e.key.toLowerCase()) {
                    case 'i':
                        e.preventDefault();
                        openIncomeComparison();
                        break;
                    case 't':
                        e.preventDefault();
                        openTaxCalculator();
                        break;
                    case 'b':
                        e.preventDefault();
                        openBudgetPlanner();
                        break;
                    case 'v':
                        e.preventDefault();
                        openInvestmentAnalyzer();
                        break;
                }
            }
        });
        
        // Ensure all interactive elements are keyboard accessible
        const interactiveElements = document.querySelectorAll('a, button, input, textarea, select, [tabindex]');
        interactiveElements.forEach(element => {
            if (!element.hasAttribute('tabindex')) {
                element.setAttribute('tabindex', '0');
            }
        });
    }
    
    // Focus indicators
    function setupFocusIndicators() {
        const style = document.createElement('style');
        style.textContent = `
            .accessibility-focus {
                outline: 3px solid #00d4aa !important;
                outline-offset: 2px !important;
                border-radius: 4px !important;
            }
            
            .accessibility-focus:focus {
                outline: 3px solid #00d4aa !important;
                outline-offset: 2px !important;
            }
            
            /* High contrast mode */
            .high-contrast-mode .accessibility-focus {
                outline: 4px solid #ffffff !important;
                outline-offset: 3px !important;
            }
            
            /* Reduced motion support */
            .reduced-motion * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        `;
        document.head.appendChild(style);
        
        // Add focus indicators to all focusable elements
        document.addEventListener('focusin', function(e) {
            e.target.classList.add(ACCESSIBILITY_CONFIG.focusIndicatorClass);
        });
        
        document.addEventListener('focusout', function(e) {
            e.target.classList.remove(ACCESSIBILITY_CONFIG.focusIndicatorClass);
        });
    }
    
    // Skip links
    function setupSkipLinks() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.id = ACCESSIBILITY_CONFIG.skipLinkId;
        skipLink.className = 'skip-link';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: #00d4aa;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 10000;
            transition: top 0.3s;
        `;
        
        skipLink.addEventListener('focus', function() {
            this.style.top = '6px';
        });
        
        skipLink.addEventListener('blur', function() {
            this.style.top = '-40px';
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
    }
    
    // Live regions for screen reader announcements
    function setupLiveRegions() {
        const liveRegion = document.createElement('div');
        liveRegion.id = ACCESSIBILITY_CONFIG.liveRegionId;
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.style.cssText = `
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        `;
        document.body.appendChild(liveRegion);
    }
    
    // High contrast mode toggle
    function setupHighContrastToggle() {
        const toggle = document.createElement('button');
        toggle.textContent = 'Toggle High Contrast';
        toggle.setAttribute('aria-label', 'Toggle high contrast mode');
        toggle.className = 'accessibility-toggle';
        toggle.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
            padding: 8px 12px;
            background: #333;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        `;
        
        toggle.addEventListener('click', function() {
            document.body.classList.toggle(ACCESSIBILITY_CONFIG.highContrastClass);
            announceToScreenReader(
                document.body.classList.contains(ACCESSIBILITY_CONFIG.highContrastClass) 
                    ? 'High contrast mode enabled' 
                    : 'High contrast mode disabled'
            );
        });
        
        document.body.appendChild(toggle);
    }
    
    // Reduced motion support
    function setupReducedMotionSupport() {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.body.classList.add(ACCESSIBILITY_CONFIG.reducedMotionClass);
        }
    }
    
    // Screen reader announcements
    function setupScreenReaderAnnouncements() {
        window.announceToScreenReader = function(message) {
            const liveRegion = document.getElementById(ACCESSIBILITY_CONFIG.liveRegionId);
            if (liveRegion) {
                liveRegion.textContent = message;
                setTimeout(() => {
                    liveRegion.textContent = '';
                }, 1000);
            }
        };
    }
    
    // Form accessibility
    function setupFormAccessibility() {
        // Add ARIA attributes to form inputs
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (!input.hasAttribute('aria-label') && !input.hasAttribute('aria-labelledby')) {
                const label = input.closest('label') || document.querySelector(`label[for="${input.id}"]`);
                if (label) {
                    input.setAttribute('aria-labelledby', label.id || 'label-' + Math.random().toString(36).substr(2, 9));
                }
            }
            
            // Add error handling
            if (input.hasAttribute('aria-invalid')) {
                input.addEventListener('blur', function() {
                    if (this.value && this.checkValidity()) {
                        this.setAttribute('aria-invalid', 'false');
                    }
                });
            }
        });
    }
    
    // Table accessibility
    function setupTableAccessibility() {
        const tables = document.querySelectorAll('table');
        tables.forEach(table => {
            if (!table.hasAttribute('role')) {
                table.setAttribute('role', 'table');
            }
            
            const headers = table.querySelectorAll('th');
            headers.forEach(header => {
                if (!header.hasAttribute('scope')) {
                    header.setAttribute('scope', 'col');
                }
            });
        });
    }
    
    // Image accessibility
    function setupImageAccessibility() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.hasAttribute('alt')) {
                // Generate alt text based on context
                const context = img.closest('[data-context]')?.getAttribute('data-context') || 'image';
                img.setAttribute('alt', `${context} image`);
            }
            
            // Add loading optimization
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
        });
    }
    
    // Chart accessibility
    function setupChartAccessibility() {
        // Add ARIA labels to charts and graphs
        const charts = document.querySelectorAll('.chart, .graph, [data-chart]');
        charts.forEach(chart => {
            if (!chart.hasAttribute('aria-label')) {
                const chartType = chart.getAttribute('data-chart-type') || 'chart';
                const chartTitle = chart.getAttribute('data-chart-title') || 'Data visualization';
                chart.setAttribute('aria-label', `${chartTitle} - ${chartType}`);
                chart.setAttribute('role', 'img');
            }
        });
        
        // Add descriptions for complex charts
        const complexCharts = document.querySelectorAll('[data-chart-complex="true"]');
        complexCharts.forEach(chart => {
            const descriptionId = 'chart-desc-' + Math.random().toString(36).substr(2, 9);
            const description = chart.getAttribute('data-chart-description') || 'Complex data visualization';
            
            const descElement = document.createElement('div');
            descElement.id = descriptionId;
            descElement.className = 'sr-only';
            descElement.textContent = description;
            
            chart.appendChild(descElement);
            chart.setAttribute('aria-describedby', descriptionId);
        });
    }
    
    // Modal accessibility
    function setupModalAccessibility() {
        const modals = document.querySelectorAll('.modal, [role="dialog"]');
        modals.forEach(modal => {
            // Ensure modal has proper ARIA attributes
            if (!modal.hasAttribute('aria-modal')) {
                modal.setAttribute('aria-modal', 'true');
            }
            
            if (!modal.hasAttribute('aria-label') && !modal.hasAttribute('aria-labelledby')) {
                const modalTitle = modal.querySelector('.modal-title, h1, h2, h3');
                if (modalTitle) {
                    modal.setAttribute('aria-labelledby', modalTitle.id || 'modal-title-' + Math.random().toString(36).substr(2, 9));
                }
            }
            
            // Trap focus within modal
            const focusableElements = modal.querySelectorAll('a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])');
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
            if (firstElement && lastElement) {
                modal.addEventListener('keydown', function(e) {
                    if (e.key === 'Tab') {
                        if (e.shiftKey) {
                            if (document.activeElement === firstElement) {
                                e.preventDefault();
                                lastElement.focus();
                            }
                        } else {
                            if (document.activeElement === lastElement) {
                                e.preventDefault();
                                firstElement.focus();
                            }
                        }
                    }
                });
            }
        });
    }
    
    // Navigation accessibility
    function setupNavigationAccessibility() {
        const navs = document.querySelectorAll('nav');
        navs.forEach(nav => {
            if (!nav.hasAttribute('aria-label')) {
                nav.setAttribute('aria-label', 'Main navigation');
            }
        });
        
        // Add current page indicators
        const currentPage = window.location.pathname;
        const navLinks = document.querySelectorAll('nav a');
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPage) {
                link.setAttribute('aria-current', 'page');
            }
        });
    }
    
    // Navigation functions
    function navigateToDashboard() {
        announceToScreenReader('Navigating to dashboard');
        // Implementation for dashboard navigation
        const dashboardLink = document.querySelector('a[href="#dashboard"], a[href="/dashboard"]');
        if (dashboardLink) {
            dashboardLink.click();
        }
    }
    
    function navigateToAssessments() {
        announceToScreenReader('Navigating to assessments');
        // Implementation for assessments navigation
        const assessmentsLink = document.querySelector('a[href="#assessments"], a[href="/assessments"]');
        if (assessmentsLink) {
            assessmentsLink.click();
        }
    }
    
    function navigateToAnalytics() {
        announceToScreenReader('Navigating to analytics');
        // Implementation for analytics navigation
        const analyticsLink = document.querySelector('a[href="#analytics"], a[href="/analytics"]');
        if (analyticsLink) {
            analyticsLink.click();
        }
    }
    
    function navigateToProfile() {
        announceToScreenReader('Navigating to profile');
        // Implementation for profile navigation
        const profileLink = document.querySelector('a[href="#profile"], a[href="/profile"]');
        if (profileLink) {
            profileLink.click();
        }
    }
    
    // Financial tools functions
    function openIncomeComparison() {
        announceToScreenReader('Opening income comparison tool');
        // Implementation for income comparison
        const incomeTool = document.querySelector('[data-tool="income-comparison"]');
        if (incomeTool) {
            incomeTool.click();
        }
    }
    
    function openTaxCalculator() {
        announceToScreenReader('Opening tax calculator');
        // Implementation for tax calculator
        const taxTool = document.querySelector('[data-tool="tax-calculator"]');
        if (taxTool) {
            taxTool.click();
        }
    }
    
    function openBudgetPlanner() {
        announceToScreenReader('Opening budget planner');
        // Implementation for budget planner
        const budgetTool = document.querySelector('[data-tool="budget-planner"]');
        if (budgetTool) {
            budgetTool.click();
        }
    }
    
    function openInvestmentAnalyzer() {
        announceToScreenReader('Opening investment analyzer');
        // Implementation for investment analyzer
        const investmentTool = document.querySelector('[data-tool="investment-analyzer"]');
        if (investmentTool) {
            investmentTool.click();
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAccessibility);
    } else {
        initAccessibility();
    }
    
    // Export for global access
    window.MingusAccessibility = {
        init: initAccessibility,
        announce: announceToScreenReader,
        config: ACCESSIBILITY_CONFIG
    };
    
})();
