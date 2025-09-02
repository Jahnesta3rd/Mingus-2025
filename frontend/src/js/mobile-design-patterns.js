/**
 * MINGUS Mobile Design Patterns
 * Mobile-specific design patterns for financial app interactions
 */

class MobileDesignPatterns {
    constructor() {
        this.bottomSheets = new Map();
        this.floatingActions = new Map();
        this.mobileModals = new Map();
        this.formWizards = new Map();
        
        this.init();
    }
    
    init() {
        this.setupBottomSheets();
        this.setupTouchFriendlyModals();
        this.setupMobileFormLayouts();
        this.setupFloatingActionButtons();
        this.setupMobileNavigation();
        this.setupTouchOptimization();
    }
    
    // ===== BOTTOM SHEETS FOR MOBILE-SPECIFIC ACTIONS =====
    setupBottomSheets() {
        // Financial action bottom sheets
        this.createFinancialActionSheet();
        this.createDataFilterSheet();
        this.createExportOptionsSheet();
        this.createSettingsSheet();
    }
    
    createFinancialActionSheet() {
        const actionSheet = document.createElement('div');
        actionSheet.className = 'bottom-sheet financial-actions';
        actionSheet.innerHTML = `
            <div class="bottom-sheet-handle"></div>
            <div class="bottom-sheet-header">
                <h3>Financial Actions</h3>
                <button class="bottom-sheet-close" aria-label="Close">×</button>
            </div>
            <div class="bottom-sheet-content">
                <div class="action-grid">
                    <button class="action-item" data-action="transfer">
                        <div class="action-icon">💸</div>
                        <span>Transfer Funds</span>
                    </button>
                    <button class="action-item" data-action="invest">
                        <div class="action-icon">📈</div>
                        <span>Invest</span>
                    </button>
                    <button class="action-item" data-action="save">
                        <div class="action-icon">💰</div>
                        <span>Save Money</span>
                    </button>
                    <button class="action-item" data-action="budget">
                        <div class="action-icon">📊</div>
                        <span>Budget</span>
                    </button>
                    <button class="action-item" data-action="analyze">
                        <div class="action-icon">🔍</div>
                        <span>Analyze</span>
                    </button>
                    <button class="action-item" data-action="export">
                        <div class="action-icon">📤</div>
                        <span>Export</span>
                    </button>
                </div>
            </div>
        `;
        
        this.setupBottomSheetBehavior(actionSheet, 'financial-actions');
        this.bottomSheets.set('financial-actions', actionSheet);
    }
    
    createDataFilterSheet() {
        const filterSheet = document.createElement('div');
        filterSheet.className = 'bottom-sheet data-filters';
        filterSheet.innerHTML = `
            <div class="bottom-sheet-handle"></div>
            <div class="bottom-sheet-header">
                <h3>Filter Data</h3>
                <button class="bottom-sheet-close" aria-label="Close">×</button>
            </div>
            <div class="bottom-sheet-content">
                <div class="filter-section">
                    <label>Date Range</label>
                    <div class="filter-options">
                        <button class="filter-option active" data-range="7d">7 Days</button>
                        <button class="filter-option" data-range="30d">30 Days</button>
                        <button class="filter-option" data-range="90d">90 Days</button>
                        <button class="filter-option" data-range="1y">1 Year</button>
                    </div>
                </div>
                <div class="filter-section">
                    <label>Categories</label>
                    <div class="filter-options">
                        <button class="filter-option active" data-category="all">All</button>
                        <button class="filter-option" data-category="income">Income</button>
                        <button class="filter-option" data-category="expenses">Expenses</button>
                        <button class="filter-option" data-category="investments">Investments</button>
                    </div>
                </div>
                <div class="filter-actions">
                    <button class="btn btn-secondary" data-action="reset">Reset</button>
                    <button class="btn btn-primary" data-action="apply">Apply Filters</button>
                </div>
            </div>
        `;
        
        this.setupBottomSheetBehavior(filterSheet, 'data-filters');
        this.bottomSheets.set('data-filters', filterSheet);
    }
    
    createExportOptionsSheet() {
        const exportSheet = document.createElement('div');
        exportSheet.className = 'bottom-sheet export-options';
        exportSheet.innerHTML = `
            <div class="bottom-sheet-handle"></div>
            <div class="bottom-sheet-header">
                <h3>Export Options</h3>
                <button class="bottom-sheet-close" aria-label="Close">×</button>
            </div>
            <div class="bottom-sheet-content">
                <div class="export-format">
                    <label>Format</label>
                    <div class="format-options">
                        <button class="format-option active" data-format="pdf">PDF</button>
                        <button class="format-option" data-format="csv">CSV</button>
                        <button class="format-option" data-format="excel">Excel</button>
                    </div>
                </div>
                <div class="export-range">
                    <label>Date Range</label>
                    <div class="range-inputs">
                        <input type="date" class="date-input" id="export-start-date">
                        <span>to</span>
                        <input type="date" class="date-input" id="export-end-date">
                    </div>
                </div>
                <div class="export-actions">
                    <button class="btn btn-primary" data-action="export">Export Data</button>
                </div>
            </div>
        `;
        
        this.setupBottomSheetBehavior(exportSheet, 'export-options');
        this.bottomSheets.set('export-options', exportSheet);
    }
    
    createSettingsSheet() {
        const settingsSheet = document.createElement('div');
        settingsSheet.className = 'bottom-sheet settings';
        settingsSheet.innerHTML = `
            <div class="bottom-sheet-handle"></div>
            <div class="bottom-sheet-header">
                <h3>Settings</h3>
                <button class="bottom-sheet-close" aria-label="Close">×</button>
            </div>
            <div class="bottom-sheet-content">
                <div class="setting-item">
                    <label>Notifications</label>
                    <label class="toggle-switch">
                        <input type="checkbox" checked>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <div class="setting-item">
                    <label>Haptic Feedback</label>
                    <label class="toggle-switch">
                        <input type="checkbox" checked>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <div class="setting-item">
                    <label>Dark Mode</label>
                    <label class="toggle-switch">
                        <input type="checkbox">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <div class="setting-item">
                    <label>Auto-save</label>
                    <label class="toggle-switch">
                        <input type="checkbox" checked>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
            </div>
        `;
        
        this.setupBottomSheetBehavior(settingsSheet, 'settings');
        this.bottomSheets.set('settings', settingsSheet);
    }
    
    setupBottomSheetBehavior(sheet, type) {
        // Add to DOM
        document.body.appendChild(sheet);
        
        // Setup drag behavior
        this.setupBottomSheetDrag(sheet);
        
        // Setup close behavior
        const closeBtn = sheet.querySelector('.bottom-sheet-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hideBottomSheet(type);
            });
        }
        
        // Setup action handlers
        this.setupBottomSheetActions(sheet, type);
        
        // Initially hidden
        sheet.style.display = 'none';
    }
    
    setupBottomSheetDrag(sheet) {
        let startY = 0;
        let currentY = 0;
        let isDragging = false;
        
        const handle = sheet.querySelector('.bottom-sheet-handle');
        if (!handle) return;
        
        handle.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
            isDragging = true;
            sheet.style.transition = 'none';
        }, { passive: true });
        
        handle.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            
            currentY = e.touches[0].clientY;
            const deltaY = currentY - startY;
            
            if (deltaY > 0) {
                sheet.style.transform = `translateY(${deltaY}px)`;
            }
        }, { passive: true });
        
        handle.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            
            isDragging = false;
            sheet.style.transition = 'transform 0.3s ease-out';
            
            const deltaY = currentY - startY;
            if (deltaY > 100) {
                // Close sheet if dragged down far enough
                this.hideBottomSheet(sheet.dataset.type || 'unknown');
            } else {
                // Snap back
                sheet.style.transform = '';
            }
        }, { passive: true });
    }
    
    setupBottomSheetActions(sheet, type) {
        const actionItems = sheet.querySelectorAll('.action-item, .filter-option, .format-option');
        
        actionItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const action = item.dataset.action || item.dataset.range || item.dataset.category || item.dataset.format;
                this.handleBottomSheetAction(type, action, item);
            });
        });
        
        // Handle special actions
        const specialActions = sheet.querySelectorAll('[data-action]');
        specialActions.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.dataset.action;
                this.handleBottomSheetSpecialAction(type, action, btn);
            });
        });
    }
    
    handleBottomSheetAction(type, action, element) {
        // Remove active class from siblings
        const siblings = element.parentNode.children;
        Array.from(siblings).forEach(sibling => {
            sibling.classList.remove('active');
        });
        
        // Add active class to current element
        element.classList.add('active');
        
        // Trigger haptic feedback
        if (window.touchManager) {
            window.touchManager.triggerHaptic('selection');
        }
        
        // Handle specific actions
        switch (type) {
            case 'financial-actions':
                this.handleFinancialAction(action);
                break;
            case 'data-filters':
                this.handleFilterChange(action);
                break;
            case 'export-options':
                this.handleExportOption(action);
                break;
        }
    }
    
    handleBottomSheetSpecialAction(type, action, button) {
        switch (action) {
            case 'reset':
                this.resetFilters();
                break;
            case 'apply':
                this.applyFilters();
                break;
            case 'export':
                this.exportData();
                break;
        }
        
        // Trigger haptic feedback
        if (window.touchManager) {
            window.touchManager.triggerHaptic('success');
        }
    }
    
    showBottomSheet(type) {
        const sheet = this.bottomSheets.get(type);
        if (sheet) {
            sheet.style.display = 'block';
            setTimeout(() => {
                sheet.classList.add('active');
            }, 10);
            
            // Trigger haptic feedback
            if (window.touchManager) {
                window.touchManager.triggerHaptic('medium');
            }
        }
    }
    
    hideBottomSheet(type) {
        const sheet = this.bottomSheets.get(type);
        if (sheet) {
            sheet.classList.remove('active');
            setTimeout(() => {
                sheet.style.display = 'none';
            }, 300);
        }
    }
    
    // ===== TOUCH-FRIENDLY MODAL DIALOGS =====
    setupTouchFriendlyModals() {
        this.createFinancialDataModal();
        this.createConfirmationModal();
        this.createInputModal();
    }
    
    createFinancialDataModal() {
        const modal = document.createElement('div');
        modal.className = 'mobile-modal financial-data-modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Financial Data</h3>
                    <button class="modal-close" aria-label="Close">×</button>
                </div>
                <div class="modal-body">
                    <div class="data-summary">
                        <div class="summary-item">
                            <span class="label">Total Assets</span>
                            <span class="value">$125,000</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">Monthly Income</span>
                            <span class="value">$8,500</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">Expenses</span>
                            <span class="value">$6,200</span>
                        </div>
                    </div>
                    <div class="data-chart">
                        <canvas id="financial-chart"></canvas>
                    </div>
                    <div class="data-actions">
                        <button class="btn btn-secondary">Export</button>
                        <button class="btn btn-primary">Share</button>
                    </div>
                </div>
            </div>
        `;
        
        this.setupMobileModal(modal, 'financial-data');
        this.mobileModals.set('financial-data', modal);
    }
    
    createConfirmationModal() {
        const modal = document.createElement('div');
        modal.className = 'mobile-modal confirmation-modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <div class="modal-body">
                    <div class="confirmation-icon">⚠️</div>
                    <h3>Confirm Action</h3>
                    <p>Are you sure you want to proceed with this action?</p>
                    <div class="confirmation-actions">
                        <button class="btn btn-secondary" data-action="cancel">Cancel</button>
                        <button class="btn btn-danger" data-action="confirm">Confirm</button>
                    </div>
                </div>
            </div>
        `;
        
        this.setupMobileModal(modal, 'confirmation');
        this.mobileModals.set('confirmation', modal);
    }
    
    createInputModal() {
        const modal = document.createElement('div');
        modal.className = 'mobile-modal input-modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Enter Amount</h3>
                    <button class="modal-close" aria-label="Close">×</button>
                </div>
                <div class="modal-body">
                    <div class="input-group">
                        <label for="amount-input">Amount</label>
                        <div class="amount-input-wrapper">
                            <span class="currency-symbol">$</span>
                            <input type="number" id="amount-input" placeholder="0.00" step="0.01" min="0">
                        </div>
                    </div>
                    <div class="quick-amounts">
                        <button class="quick-amount" data-amount="100">$100</button>
                        <button class="quick-amount" data-amount="500">$500</button>
                        <button class="quick-amount" data-amount="1000">$1,000</button>
                        <button class="quick-amount" data-amount="5000">$5,000</button>
                    </div>
                    <div class="input-actions">
                        <button class="btn btn-secondary" data-action="cancel">Cancel</button>
                        <button class="btn btn-primary" data-action="confirm">Confirm</button>
                    </div>
                </div>
            </div>
        `;
        
        this.setupMobileModal(modal, 'input');
        this.mobileModals.set('input', modal);
    }
    
    setupMobileModal(modal, type) {
        // Add to DOM
        document.body.appendChild(modal);
        
        // Setup close behavior
        const closeBtn = modal.querySelector('.modal-close');
        const overlay = modal.querySelector('.modal-overlay');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hideMobileModal(type);
            });
        }
        
        if (overlay) {
            overlay.addEventListener('click', () => {
                this.hideMobileModal(type);
            });
        }
        
        // Setup action handlers
        this.setupModalActions(modal, type);
        
        // Initially hidden
        modal.style.display = 'none';
    }
    
    setupModalActions(modal, type) {
        const actionButtons = modal.querySelectorAll('[data-action]');
        
        actionButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.dataset.action;
                this.handleModalAction(type, action, btn);
            });
        });
        
        // Setup quick amount buttons
        const quickAmounts = modal.querySelectorAll('.quick-amount');
        quickAmounts.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const amount = btn.dataset.amount;
                this.setQuickAmount(amount);
            });
        });
    }
    
    handleModalAction(type, action, button) {
        switch (action) {
            case 'cancel':
                this.hideMobileModal(type);
                break;
            case 'confirm':
                this.confirmModalAction(type);
                break;
        }
        
        // Trigger haptic feedback
        if (window.touchManager) {
            window.touchManager.triggerHaptic('selection');
        }
    }
    
    setQuickAmount(amount) {
        const input = document.getElementById('amount-input');
        if (input) {
            input.value = amount;
            input.focus();
        }
        
        // Trigger haptic feedback
        if (window.touchManager) {
            window.touchManager.triggerHaptic('light');
        }
    }
    
    showMobileModal(type, data = {}) {
        const modal = this.mobileModals.get(type);
        if (modal) {
            // Update modal content with data
            this.updateModalContent(modal, type, data);
            
            modal.style.display = 'block';
            setTimeout(() => {
                modal.classList.add('active');
            }, 10);
            
            // Trigger haptic feedback
            if (window.touchManager) {
                window.touchManager.triggerHaptic('medium');
            }
        }
    }
    
    hideMobileModal(type) {
        const modal = this.mobileModals.get(type);
        if (modal) {
            modal.classList.remove('active');
            setTimeout(() => {
                modal.style.display = 'none';
            }, 300);
        }
    }
    
    updateModalContent(modal, type, data) {
        // Update modal content based on type and data
        switch (type) {
            case 'confirmation':
                const title = modal.querySelector('h3');
                const message = modal.querySelector('p');
                if (title && data.title) title.textContent = data.title;
                if (message && data.message) message.textContent = data.message;
                break;
            case 'input':
                const input = modal.querySelector('input');
                if (input && data.defaultValue) input.value = data.defaultValue;
                break;
        }
    }
    
    // ===== MOBILE-SPECIFIC LAYOUTS FOR COMPLEX FINANCIAL FORMS =====
    setupMobileFormLayouts() {
        this.createWizardForm();
        this.createStepperForm();
        this.createTabbedForm();
    }
    
    createWizardForm() {
        const wizard = document.createElement('div');
        wizard.className = 'form-wizard';
        wizard.innerHTML = `
            <div class="wizard-progress">
                <div class="progress-step active" data-step="1">
                    <div class="step-number">1</div>
                    <div class="step-label">Basic Info</div>
                </div>
                <div class="progress-step" data-step="2">
                    <div class="step-number">2</div>
                    <div class="step-label">Financial Details</div>
                </div>
                <div class="progress-step" data-step="3">
                    <div class="step-number">3</div>
                    <div class="step-label">Review</div>
                </div>
            </div>
            <div class="wizard-content">
                <div class="wizard-step active" data-step="1">
                    <h3>Basic Information</h3>
                    <div class="form-group">
                        <label for="wizard-name">Full Name</label>
                        <input type="text" id="wizard-name" placeholder="Enter your full name">
                    </div>
                    <div class="form-group">
                        <label for="wizard-email">Email</label>
                        <input type="email" id="wizard-email" placeholder="Enter your email">
                    </div>
                    <div class="wizard-actions">
                        <button class="btn btn-primary" data-action="next">Next</button>
                    </div>
                </div>
                <div class="wizard-step" data-step="2">
                    <h3>Financial Details</h3>
                    <div class="form-group">
                        <label for="wizard-income">Monthly Income</label>
                        <input type="number" id="wizard-income" placeholder="Enter monthly income">
                    </div>
                    <div class="form-group">
                        <label for="wizard-expenses">Monthly Expenses</label>
                        <input type="number" id="wizard-expenses" placeholder="Enter monthly expenses">
                    </div>
                    <div class="wizard-actions">
                        <button class="btn btn-secondary" data-action="prev">Previous</button>
                        <button class="btn btn-primary" data-action="next">Next</button>
                    </div>
                </div>
                <div class="wizard-step" data-step="3">
                    <h3>Review Information</h3>
                    <div class="review-summary">
                        <div class="review-item">
                            <span class="label">Name:</span>
                            <span class="value" id="review-name"></span>
                        </div>
                        <div class="review-item">
                            <span class="label">Email:</span>
                            <span class="value" id="review-email"></span>
                        </div>
                        <div class="review-item">
                            <span class="label">Income:</span>
                            <span class="value" id="review-income"></span>
                        </div>
                        <div class="review-item">
                            <span class="label">Expenses:</span>
                            <span class="value" id="review-expenses"></span>
                        </div>
                    </div>
                    <div class="wizard-actions">
                        <button class="btn btn-secondary" data-action="prev">Previous</button>
                        <button class="btn btn-success" data-action="submit">Submit</button>
                    </div>
                </div>
            </div>
        `;
        
        this.setupWizardForm(wizard);
        this.formWizards.set('main-wizard', wizard);
    }
    
    setupWizardForm(wizard) {
        const nextButtons = wizard.querySelectorAll('[data-action="next"]');
        const prevButtons = wizard.querySelectorAll('[data-action="prev"]');
        const submitButton = wizard.querySelector('[data-action="submit"]');
        
        nextButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.nextWizardStep(wizard);
            });
        });
        
        prevButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.prevWizardStep(wizard);
            });
        });
        
        if (submitButton) {
            submitButton.addEventListener('click', () => {
                this.submitWizardForm(wizard);
            });
        }
        
        // Setup form validation
        this.setupWizardValidation(wizard);
    }
    
    setupWizardValidation(wizard) {
        const inputs = wizard.querySelectorAll('input');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateWizardField(input);
            });
            
            input.addEventListener('input', () => {
                this.clearWizardFieldError(input);
            });
        });
    }
    
    validateWizardField(field) {
        const value = field.value.trim();
        const type = field.type;
        const required = field.hasAttribute('required');
        
        if (required && !value) {
            this.showWizardFieldError(field, 'This field is required');
            return false;
        }
        
        if (type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                this.showWizardFieldError(field, 'Please enter a valid email');
                return false;
            }
        }
        
        return true;
    }
    
    showWizardFieldError(field, message) {
        field.classList.add('error');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }
    
    clearWizardFieldError(field) {
        field.classList.remove('error');
        
        const errorDiv = field.parentNode.querySelector('.field-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
    
    nextWizardStep(wizard) {
        const currentStep = wizard.querySelector('.wizard-step.active');
        const currentStepNum = parseInt(currentStep.dataset.step);
        const nextStep = wizard.querySelector(`[data-step="${currentStepNum + 1}"]`);
        
        if (nextStep && this.validateWizardStep(currentStep)) {
            currentStep.classList.remove('active');
            nextStep.classList.add('active');
            
            // Update progress
            this.updateWizardProgress(wizard, currentStepNum + 1);
            
            // Trigger haptic feedback
            if (window.touchManager) {
                window.touchManager.triggerHaptic('navigation');
            }
        }
    }
    
    prevWizardStep(wizard) {
        const currentStep = wizard.querySelector('.wizard-step.active');
        const currentStepNum = parseInt(currentStep.dataset.step);
        const prevStep = wizard.querySelector(`[data-step="${currentStepNum - 1}"]`);
        
        if (prevStep) {
            currentStep.classList.remove('active');
            prevStep.classList.add('active');
            
            // Update progress
            this.updateWizardProgress(wizard, currentStepNum - 1);
            
            // Trigger haptic feedback
            if (window.touchManager) {
                window.touchManager.triggerHaptic('navigation');
            }
        }
    }
    
    updateWizardProgress(wizard, stepNum) {
        const progressSteps = wizard.querySelectorAll('.progress-step');
        
        progressSteps.forEach((step, index) => {
            const stepNumber = index + 1;
            if (stepNumber <= stepNum) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });
    }
    
    validateWizardStep(step) {
        const inputs = step.querySelectorAll('input');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!this.validateWizardField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    submitWizardForm(wizard) {
        if (this.validateWizardForm(wizard)) {
            // Collect form data
            const formData = this.collectWizardData(wizard);
            
            // Show loading state
            if (window.touchManager) {
                window.touchManager.showLoading('Submitting form...');
            }
            
            // Simulate submission
            setTimeout(() => {
                if (window.touchManager) {
                    window.touchManager.hideLoading();
                }
                
                // Show success message
                this.showWizardSuccess(wizard);
            }, 2000);
        }
    }
    
    validateWizardForm(wizard) {
        const activeStep = wizard.querySelector('.wizard-step.active');
        return this.validateWizardStep(activeStep);
    }
    
    collectWizardData(wizard) {
        const inputs = wizard.querySelectorAll('input');
        const data = {};
        
        inputs.forEach(input => {
            data[input.id] = input.value;
        });
        
        return data;
    }
    
    showWizardSuccess(wizard) {
        const successMessage = document.createElement('div');
        successMessage.className = 'wizard-success';
        successMessage.innerHTML = `
            <div class="success-icon">✅</div>
            <h3>Form Submitted Successfully!</h3>
            <p>Thank you for your submission.</p>
        `;
        
        wizard.querySelector('.wizard-content').appendChild(successMessage);
        
        // Trigger haptic feedback
        if (window.touchManager) {
            window.touchManager.triggerHaptic('success');
        }
    }
    
    // ===== FLOATING ACTION BUTTONS =====
    setupFloatingActionButtons() {
        this.createMainFAB();
        this.createContextualFABs();
    }
    
    createMainFAB() {
        const mainFAB = document.createElement('button');
        mainFAB.className = 'fab main-fab';
        mainFAB.innerHTML = `
            <span class="fab-icon">+</span>
            <div class="fab-ripple"></div>
        `;
        
        mainFAB.addEventListener('click', () => {
            this.toggleMainFAB();
        });
        
        document.body.appendChild(mainFAB);
        this.floatingActions.set('main', mainFAB);
    }
    
    createContextualFABs() {
        // Create contextual FABs for different sections
        const sections = ['dashboard', 'analytics', 'portfolio'];
        
        sections.forEach(section => {
            const fab = document.createElement('button');
            fab.className = `fab contextual-fab ${section}-fab`;
            fab.innerHTML = `
                <span class="fab-icon">📊</span>
                <div class="fab-ripple"></div>
            `;
            
            fab.addEventListener('click', () => {
                this.handleContextualFAB(section);
            });
            
            document.body.appendChild(fab);
            this.floatingActions.set(section, fab);
        });
    }
    
    toggleMainFAB() {
        const mainFAB = this.floatingActions.get('main');
        if (mainFAB) {
            mainFAB.classList.toggle('active');
            
            // Show/hide contextual FABs
            this.toggleContextualFABs();
            
            // Trigger haptic feedback
            if (window.touchManager) {
                window.touchManager.triggerHaptic('selection');
            }
        }
    }
    
    toggleContextualFABs() {
        const mainFAB = this.floatingActions.get('main');
        const isActive = mainFAB.classList.contains('active');
        
        this.floatingActions.forEach((fab, key) => {
            if (key !== 'main') {
                if (isActive) {
                    fab.classList.add('active');
                } else {
                    fab.classList.remove('active');
                }
            }
        });
    }
    
    handleContextualFAB(section) {
        switch (section) {
            case 'dashboard':
                this.showBottomSheet('financial-actions');
                break;
            case 'analytics':
                this.showBottomSheet('data-filters');
                break;
            case 'portfolio':
                this.showBottomSheet('export-options');
                break;
        }
        
        // Trigger haptic feedback
        if (window.touchManager) {
            window.touchManager.triggerHaptic('selection');
        }
    }
    
    // ===== MOBILE NAVIGATION =====
    setupMobileNavigation() {
        this.createBottomNavigation();
        this.createBreadcrumbNavigation();
    }
    
    createBottomNavigation() {
        const bottomNav = document.createElement('nav');
        bottomNav.className = 'bottom-navigation';
        bottomNav.innerHTML = `
            <div class="nav-item active" data-page="dashboard">
                <div class="nav-icon">🏠</div>
                <span class="nav-label">Dashboard</span>
            </div>
            <div class="nav-item" data-page="analytics">
                <div class="nav-icon">📈</div>
                <span class="nav-label">Analytics</span>
            </div>
            <div class="nav-item" data-page="portfolio">
                <div class="nav-icon">💼</div>
                <span class="nav-label">Portfolio</span>
            </div>
            <div class="nav-item" data-page="settings">
                <div class="nav-icon">⚙️</div>
                <span class="nav-label">Settings</span>
            </div>
        `;
        
        this.setupBottomNavigation(bottomNav);
        document.body.appendChild(bottomNav);
    }
    
    setupBottomNavigation(nav) {
        const navItems = nav.querySelectorAll('.nav-item');
        
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                this.navigateToPage(page);
                
                // Update active state
                navItems.forEach(navItem => navItem.classList.remove('active'));
                item.classList.add('active');
                
                // Trigger haptic feedback
                if (window.touchManager) {
                    window.touchManager.triggerHaptic('navigation');
                }
            });
        });
    }
    
    navigateToPage(page) {
        // Handle page navigation
        const event = new CustomEvent('page-navigate', {
            detail: { page: page }
        });
        document.dispatchEvent(event);
    }
    
    // ===== TOUCH OPTIMIZATION =====
    setupTouchOptimization() {
        this.optimizeTouchTargets();
        this.setupTouchPrevention();
    }
    
    optimizeTouchTargets() {
        // Ensure all interactive elements meet minimum touch target size
        const interactiveElements = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
        
        interactiveElements.forEach(element => {
            const rect = element.getBoundingClientRect();
            const minSize = 44; // iOS minimum touch target size
            
            if (rect.width < minSize || rect.height < minSize) {
                element.style.minWidth = `${minSize}px`;
                element.style.minHeight = `${minSize}px`;
            }
        });
    }
    
    setupTouchPrevention() {
        // Prevent double-tap zoom on interactive elements
        const preventZoomElements = document.querySelectorAll('button, a, [role="button"]');
        
        preventZoomElements.forEach(element => {
            element.addEventListener('touchend', (e) => {
                if (e.target === element) {
                    e.preventDefault();
                }
            });
        });
    }
    
    // ===== PUBLIC API =====
    showBottomSheet(type) {
        this.showBottomSheet(type);
    }
    
    hideBottomSheet(type) {
        this.hideBottomSheet(type);
    }
    
    showModal(type, data = {}) {
        this.showMobileModal(type, data);
    }
    
    hideModal(type) {
        this.hideMobileModal(type);
    }
    
    // ===== ACTION HANDLERS =====
    handleFinancialAction(action) {
        console.log('Financial action:', action);
        // Handle different financial actions
    }
    
    handleFilterChange(filter) {
        console.log('Filter changed:', filter);
        // Handle filter changes
    }
    
    handleExportOption(option) {
        console.log('Export option:', option);
        // Handle export options
    }
    
    resetFilters() {
        console.log('Resetting filters');
        // Reset all filters
    }
    
    applyFilters() {
        console.log('Applying filters');
        // Apply current filters
    }
    
    exportData() {
        console.log('Exporting data');
        // Export data with current options
    }
    
    confirmModalAction(type) {
        console.log('Confirming modal action:', type);
        // Handle modal confirmation
    }
}

// Initialize mobile design patterns
document.addEventListener('DOMContentLoaded', () => {
    window.mobileDesign = new MobileDesignPatterns();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileDesignPatterns;
}
