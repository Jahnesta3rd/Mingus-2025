/**
 * Screen Reader Accessibility JavaScript
 * Comprehensive screen reader support for financial application
 * Compatible with NVDA, JAWS, VoiceOver, and TalkBack
 */

(function() {
    'use strict';

    const ScreenReaderAccessibility = {
        // Initialize screen reader accessibility features
        init: function() {
            this.setupLiveRegions();
            this.setupFinancialAnnouncements();
            this.setupFormAccessibility();
            this.setupDynamicContentAnnouncements();
            this.setupTableAccessibility();
            this.setupModalAccessibility();
            this.setupProgressAnnouncements();
            this.setupCurrencyFormatting();
            this.setupPercentageFormatting();
            
            console.log('🔊 Screen reader accessibility features initialized');
        },

        // ===== LIVE REGIONS =====
        setupLiveRegions: function() {
            // Create live regions for different types of announcements
            const liveRegions = [
                { id: 'status-live', ariaLive: 'polite', ariaAtomic: 'true' },
                { id: 'alert-live', ariaLive: 'assertive', ariaAtomic: 'true' },
                { id: 'log-live', ariaLive: 'polite', ariaAtomic: 'false' },
                { id: 'financial-live', ariaLive: 'polite', ariaAtomic: 'true' }
            ];

            liveRegions.forEach(region => {
                if (!document.getElementById(region.id)) {
                    const liveRegion = document.createElement('div');
                    liveRegion.id = region.id;
                    liveRegion.setAttribute('aria-live', region.ariaLive);
                    liveRegion.setAttribute('aria-atomic', region.ariaAtomic);
                    liveRegion.className = 'sr-only';
                    document.body.appendChild(liveRegion);
                }
            });
        },

        // ===== FINANCIAL ANNOUNCEMENTS =====
        setupFinancialAnnouncements: function() {
            // Announce financial data changes
            this.announceFinancialChange = function(type, value, context = '') {
                let message = '';
                
                switch (type) {
                    case 'currency':
                        message = `Amount updated to ${this.formatCurrency(value)}`;
                        break;
                    case 'percentage':
                        message = `Percentage updated to ${this.formatPercentage(value)}`;
                        break;
                    case 'calculation':
                        message = `Calculation result: ${context} ${this.formatCurrency(value)}`;
                        break;
                    case 'balance':
                        message = `Balance updated to ${this.formatCurrency(value)}`;
                        break;
                    case 'budget':
                        message = `Budget ${context}: ${this.formatCurrency(value)}`;
                        break;
                    default:
                        message = `${type}: ${value}`;
                }
                
                this.announce(message, 'polite', 'financial-live');
            };

            // Monitor financial data changes
            this.observeFinancialChanges();
        },

        observeFinancialChanges: function() {
            // Observe DOM changes for financial data
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === Node.TEXT_NODE) {
                                const text = node.textContent;
                                // Detect currency amounts
                                const currencyMatch = text.match(/\$[\d,]+\.?\d*/);
                                if (currencyMatch) {
                                    this.announceFinancialChange('currency', currencyMatch[0]);
                                }
                                // Detect percentages
                                const percentageMatch = text.match(/(\d+(?:\.\d+)?)%/);
                                if (percentageMatch) {
                                    this.announceFinancialChange('percentage', percentageMatch[0]);
                                }
                            }
                        });
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        },

        // ===== FORM ACCESSIBILITY =====
        setupFormAccessibility: function() {
            // Enhance form labels and associations
            this.enhanceFormLabels();
            
            // Setup form validation announcements
            this.setupFormValidation();
            
            // Setup auto-complete support
            this.setupAutoComplete();
        },

        enhanceFormLabels: function() {
            // Add missing labels to form inputs
            const inputs = document.querySelectorAll('input:not([aria-label]):not([aria-labelledby])');
            inputs.forEach(input => {
                if (!input.id && !input.getAttribute('placeholder')) {
                    const label = this.generateFinancialLabel(input);
                    input.setAttribute('aria-label', label);
                }
            });

            // Enhance financial input labels
            const financialInputs = document.querySelectorAll('.currency-input input, .percentage-input input');
            financialInputs.forEach(input => {
                const type = input.closest('.currency-input') ? 'currency' : 'percentage';
                const currentLabel = input.getAttribute('aria-label') || '';
                const enhancedLabel = `${currentLabel} in ${type === 'currency' ? 'dollars' : 'percentage'}`;
                input.setAttribute('aria-label', enhancedLabel);
            });
        },

        generateFinancialLabel: function(input) {
            const type = input.type || 'text';
            const name = input.name || 'input';
            const placeholder = input.placeholder || '';
            
            // Generate context-aware labels for financial inputs
            if (name.toLowerCase().includes('income') || name.toLowerCase().includes('salary')) {
                return 'Annual income before taxes';
            } else if (name.toLowerCase().includes('expense') || name.toLowerCase().includes('spending')) {
                return 'Monthly expense amount';
            } else if (name.toLowerCase().includes('savings') || name.toLowerCase().includes('investment')) {
                return 'Savings or investment amount';
            } else if (name.toLowerCase().includes('debt') || name.toLowerCase().includes('loan')) {
                return 'Debt or loan amount';
            } else if (name.toLowerCase().includes('rate') || name.toLowerCase().includes('percentage')) {
                return `${name.charAt(0).toUpperCase() + name.slice(1)} rate in percentage`;
            } else {
                return `${name.charAt(0).toUpperCase() + name.slice(1)} ${type}`;
            }
        },

        setupFormValidation: function() {
            // Announce form validation errors
            document.addEventListener('invalid', (e) => {
                e.preventDefault();
                const input = e.target;
                const message = input.validationMessage;
                
                // Announce validation error
                this.announce(`Validation error: ${message}`, 'assertive', 'alert-live');
                
                // Add error styling
                input.classList.add('error');
                
                // Focus on first error
                if (!document.querySelector('.error')) {
                    input.focus();
                }
            });

            // Clear error styling on input
            document.addEventListener('input', (e) => {
                const input = e.target;
                if (input.classList.contains('error')) {
                    input.classList.remove('error');
                }
            });
        },

        setupAutoComplete: function() {
            // Add autocomplete attributes to financial form fields
            const financialInputs = document.querySelectorAll('input[name*="income"], input[name*="expense"], input[name*="savings"], input[name*="debt"]');
            financialInputs.forEach(input => {
                if (input.name.toLowerCase().includes('income')) {
                    input.setAttribute('autocomplete', 'off'); // Financial data shouldn't auto-complete
                } else if (input.name.toLowerCase().includes('expense')) {
                    input.setAttribute('autocomplete', 'off');
                } else if (input.name.toLowerCase().includes('savings')) {
                    input.setAttribute('autocomplete', 'off');
                } else if (input.name.toLowerCase().includes('debt')) {
                    input.setAttribute('autocomplete', 'off');
                }
            });
        },

        // ===== DYNAMIC CONTENT ANNOUNCEMENTS =====
        setupDynamicContentAnnouncements: function() {
            // Announce new content additions
            this.announceNewContent = function(content, type = 'polite') {
                let message = '';
                
                switch (type) {
                    case 'table':
                        message = `New ${content} data loaded`;
                        break;
                    case 'chart':
                        message = `Chart updated with ${content}`;
                        break;
                    case 'form':
                        message = `Form ${content} completed`;
                        break;
                    case 'navigation':
                        message = `Navigated to ${content}`;
                        break;
                    default:
                        message = content;
                }
                
                this.announce(message, type, 'status-live');
            };

            // Monitor for dynamic content changes
            this.observeDynamicContent();
        },

        observeDynamicContent: function() {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                // Check for new financial tables
                                if (node.classList && node.classList.contains('financial-data-table')) {
                                    this.announceNewContent('financial table', 'polite');
                                }
                                
                                // Check for new charts
                                if (node.classList && node.classList.contains('chart')) {
                                    this.announceNewContent('chart data', 'polite');
                                }
                                
                                // Check for form submissions
                                if (node.classList && node.classList.contains('form-success')) {
                                    this.announceNewContent('submission successful', 'polite');
                                }
                            }
                        });
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        },

        // ===== TABLE ACCESSIBILITY =====
        setupTableAccessibility: function() {
            // Enhance financial data tables
            this.enhanceFinancialTables();
            
            // Setup table navigation
            this.setupTableNavigation();
        },

        enhanceFinancialTables: function() {
            const tables = document.querySelectorAll('.financial-data-table, table[data-type="financial"]');
            tables.forEach(table => {
                // Add summary attribute if missing
                if (!table.getAttribute('summary')) {
                    table.setAttribute('summary', 'Financial data table with currency amounts and calculations');
                }
                
                // Add role for better screen reader support
                table.setAttribute('role', 'table');
                
                // Enhance headers
                const headers = table.querySelectorAll('th');
                headers.forEach((header, index) => {
                    if (!header.getAttribute('scope')) {
                        header.setAttribute('scope', 'col');
                    }
                    
                    // Add financial context to headers
                    const headerText = header.textContent.toLowerCase();
                    if (headerText.includes('amount') || headerText.includes('cost') || headerText.includes('price')) {
                        header.setAttribute('aria-label', `${header.textContent} in dollars`);
                    } else if (headerText.includes('rate') || headerText.includes('percentage')) {
                        header.setAttribute('aria-label', `${header.textContent} in percentage`);
                    }
                });
                
                // Enhance data cells
                const cells = table.querySelectorAll('td');
                cells.forEach(cell => {
                    const cellText = cell.textContent;
                    const currencyMatch = cellText.match(/\$[\d,]+\.?\d*/);
                    const percentageMatch = cellText.match(/(\d+(?:\.\d+)?)%/);
                    
                    if (currencyMatch) {
                        cell.setAttribute('aria-label', `Amount: ${this.formatCurrencyForScreenReader(cellText)}`);
                    } else if (percentageMatch) {
                        cell.setAttribute('aria-label', `Rate: ${this.formatPercentageForScreenReader(cellText)}`);
                    }
                });
            });
        },

        setupTableNavigation: function() {
            // Add keyboard navigation for financial tables
            document.addEventListener('keydown', (e) => {
                const table = e.target.closest('.financial-data-table, table[data-type="financial"]');
                if (!table) return;
                
                const currentCell = e.target.closest('td, th');
                if (!currentCell) return;
                
                const currentRow = currentCell.parentElement;
                const currentRowIndex = Array.from(currentRow.parentElement.children).indexOf(currentRow);
                const currentCellIndex = Array.from(currentRow.children).indexOf(currentCell);
                
                let nextCell = null;
                
                switch (e.key) {
                    case 'ArrowUp':
                        if (currentRowIndex > 0) {
                            const prevRow = currentRow.parentElement.children[currentRowIndex - 1];
                            nextCell = prevRow.children[currentCellIndex];
                        }
                        break;
                    case 'ArrowDown':
                        if (currentRowIndex < currentRow.parentElement.children.length - 1) {
                            const nextRow = currentRow.parentElement.children[currentRowIndex + 1];
                            nextCell = nextRow.children[currentCellIndex];
                        }
                        break;
                    case 'ArrowLeft':
                        if (currentCellIndex > 0) {
                            nextCell = currentRow.children[currentCellIndex - 1];
                        }
                        break;
                    case 'ArrowRight':
                        if (currentCellIndex < currentRow.children.length - 1) {
                            nextCell = currentRow.children[currentCellIndex + 1];
                        }
                        break;
                }
                
                if (nextCell) {
                    e.preventDefault();
                    nextCell.focus();
                    
                    // Announce cell content for screen readers
                    const cellText = nextCell.textContent;
                    if (cellText) {
                        this.announce(`Focused on: ${cellText}`, 'polite', 'status-live');
                    }
                }
            });
        },

        // ===== MODAL ACCESSIBILITY =====
        setupModalAccessibility: function() {
            // Enhance modal accessibility
            this.enhanceModals();
            
            // Setup modal announcements
            this.setupModalAnnouncements();
        },

        enhanceModals: function() {
            const modals = document.querySelectorAll('.modal, .dialog, [role="dialog"]');
            modals.forEach(modal => {
                // Add proper ARIA attributes
                if (!modal.getAttribute('aria-modal')) {
                    modal.setAttribute('aria-modal', 'true');
                }
                
                // Add accessible name
                if (!modal.getAttribute('aria-labelledby') && !modal.getAttribute('aria-label')) {
                    const title = modal.querySelector('h1, h2, h3, h4, h5, h6');
                    if (title) {
                        const titleId = title.id || `modal-title-${Math.random().toString(36).substr(2, 9)}`;
                        title.id = titleId;
                        modal.setAttribute('aria-labelledby', titleId);
                    }
                }
                
                // Add description
                if (!modal.getAttribute('aria-describedby')) {
                    const description = modal.querySelector('.modal-description, .dialog-description');
                    if (description) {
                        const descId = description.id || `modal-desc-${Math.random().toString(36).substr(2, 9)}`;
                        description.id = descId;
                        modal.setAttribute('aria-describedby', descId);
                    }
                }
            });
        },

        setupModalAnnouncements: function() {
            // Announce modal open/close
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'aria-hidden') {
                        const modal = mutation.target;
                        const isHidden = modal.getAttribute('aria-hidden') === 'true';
                        
                        if (isHidden) {
                            this.announce('Modal closed', 'polite', 'status-live');
                        } else {
                            const title = modal.querySelector('h1, h2, h3, h4, h5, h6');
                            const modalTitle = title ? title.textContent : 'Modal';
                            this.announce(`${modalTitle} opened`, 'polite', 'status-live');
                        }
                    }
                });
            });

            const modals = document.querySelectorAll('.modal, .dialog, [role="dialog"]');
            modals.forEach(modal => {
                observer.observe(modal, {
                    attributes: true,
                    attributeFilter: ['aria-hidden']
                });
            });
        },

        // ===== PROGRESS ANNOUNCEMENTS =====
        setupProgressAnnouncements: function() {
            // Monitor progress bar changes
            const progressBars = document.querySelectorAll('.progress-bar, [role="progressbar"]');
            progressBars.forEach(progressBar => {
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        if (mutation.type === 'attributes' && mutation.attributeName === 'aria-valuenow') {
                            const currentValue = progressBar.getAttribute('aria-valuenow');
                            const maxValue = progressBar.getAttribute('aria-valuemax') || 100;
                            const percentage = Math.round((currentValue / maxValue) * 100);
                            
                            this.announce(`Progress: ${percentage}% complete`, 'polite', 'status-live');
                        }
                    });
                });

                observer.observe(progressBar, {
                    attributes: true,
                    attributeFilter: ['aria-valuenow']
                });
            });
        },

        // ===== CURRENCY FORMATTING =====
        setupCurrencyFormatting: function() {
            // Format currency for screen reader announcements
            this.formatCurrency = function(amount) {
                const num = parseFloat(amount.toString().replace(/[$,]/g, ''));
                if (isNaN(num)) return amount;
                
                return new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    minimumFractionDigits: 2
                }).format(num);
            };

            this.formatCurrencyForScreenReader = function(text) {
                const num = parseFloat(text.replace(/[$,]/g, ''));
                if (isNaN(num)) return text;
                
                const dollars = Math.floor(num);
                const cents = Math.round((num - dollars) * 100);
                
                if (cents === 0) {
                    return `${dollars} dollars`;
                } else {
                    return `${dollars} dollars and ${cents} cents`;
                }
            };
        },

        // ===== PERCENTAGE FORMATTING =====
        setupPercentageFormatting: function() {
            // Format percentage for screen reader announcements
            this.formatPercentage = function(value) {
                const num = parseFloat(value.toString().replace('%', ''));
                if (isNaN(num)) return value;
                
                return `${num.toFixed(1)}%`;
            };

            this.formatPercentageForScreenReader = function(text) {
                const num = parseFloat(text.replace('%', ''));
                if (isNaN(num)) return text;
                
                return `${num.toFixed(1)} percent`;
            };
        },

        // ===== UTILITY FUNCTIONS =====
        announce: function(message, priority = 'polite', regionId = 'status-live') {
            const region = document.getElementById(regionId);
            if (region) {
                region.textContent = message;
                
                // Clear message after announcement
                setTimeout(() => {
                    region.textContent = '';
                }, 3000);
            }
        },

        // Public API
        announceFinancialChange: function(type, value, context) {
            this.announceFinancialChange(type, value, context);
        },

        announceNewContent: function(content, type) {
            this.announceNewContent(content, type);
        }
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            ScreenReaderAccessibility.init();
        });
    } else {
        ScreenReaderAccessibility.init();
    }

    // Make ScreenReaderAccessibility object globally available
    window.ScreenReaderAccessibility = ScreenReaderAccessibility;
})();
