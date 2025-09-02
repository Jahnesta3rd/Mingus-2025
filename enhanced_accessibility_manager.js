/**
 * Mingus Financial Services - Enhanced Accessibility Manager
 * WCAG 2.1 AA Compliance with Advanced Visual Accessibility Features
 * 
 * Features:
 * - Color contrast testing and validation
 * - Visual indicators beyond color
 * - Motion and animation accessibility
 * - Keyboard navigation enhancement
 * - Focus management
 * - High contrast mode detection
 * - Reduced motion support
 */

class EnhancedAccessibilityManager {
    constructor() {
        this.isHighContrastMode = false;
        this.isReducedMotion = false;
        this.currentFocusIndex = 0;
        this.focusableElements = [];
        this.contrastTestResults = {};
        this.accessibilitySettings = this.loadAccessibilitySettings();
        
        this.init();
    }

    /**
     * Initialize accessibility features
     */
    init() {
        this.detectUserPreferences();
        this.setupEventListeners();
        this.enhanceKeyboardNavigation();
        this.setupFocusManagement();
        this.initializeVisualIndicators();
        this.setupMotionAccessibility();
        this.runContrastAudit();
        this.announceAccessibilityFeatures();
    }

    /**
     * Detect user accessibility preferences
     */
    detectUserPreferences() {
        // Detect high contrast mode
        this.isHighContrastMode = window.matchMedia('(prefers-contrast: high)').matches;
        
        // Detect reduced motion preference
        this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        // Apply preferences immediately
        this.applyUserPreferences();
        
        // Listen for preference changes
        window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
            this.isHighContrastMode = e.matches;
            this.applyUserPreferences();
        });
        
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            this.isReducedMotion = e.matches;
            this.applyUserPreferences();
        });
    }

    /**
     * Apply user accessibility preferences
     */
    applyUserPreferences() {
        const body = document.body;
        
        if (this.isHighContrastMode) {
            body.classList.add('high-contrast-mode');
            body.classList.remove('normal-contrast-mode');
        } else {
            body.classList.remove('high-contrast-mode');
            body.classList.add('normal-contrast-mode');
        }
        
        if (this.isReducedMotion) {
            body.classList.add('reduced-motion');
            body.classList.remove('normal-motion');
        } else {
            body.classList.remove('reduced-motion');
            body.classList.add('normal-motion');
        }
        
        // Update CSS custom properties
        this.updateCSSVariables();
    }

    /**
     * Update CSS custom properties based on preferences
     */
    updateCSSVariables() {
        const root = document.documentElement;
        
        if (this.isHighContrastMode) {
            root.style.setProperty('--focus-color', '#ffffff');
            root.style.setProperty('--focus-outline', '4px solid #ffffff');
        } else {
            root.style.setProperty('--focus-color', '#00d4aa');
            root.style.setProperty('--focus-outline', '3px solid #00d4aa');
        }
        
        if (this.isReducedMotion) {
            root.style.setProperty('--transition-duration', '0.01ms');
            root.style.setProperty('--animation-duration', '0.01ms');
        } else {
            root.style.setProperty('--transition-duration', '0.3s');
            root.style.setProperty('--animation-duration', '0.3s');
        }
    }

    /**
     * Setup event listeners for accessibility features
     */
    setupEventListeners() {
        // Focus management
        document.addEventListener('focusin', this.handleFocusIn.bind(this));
        document.addEventListener('focusout', this.handleFocusOut.bind(this));
        
        // Keyboard navigation
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
        
        // Mouse and touch events for hover effects
        document.addEventListener('mouseenter', this.handleMouseEnter.bind(this), true);
        document.addEventListener('mouseleave', this.handleMouseLeave.bind(this), true);
        
        // Form validation accessibility
        document.addEventListener('invalid', this.handleFormInvalid.bind(this));
        document.addEventListener('input', this.handleFormInput.bind(this));
        
        // Page visibility changes
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    }

    /**
     * Handle focus in events
     */
    handleFocusIn(event) {
        const target = event.target;
        
        // Add focus indicator class
        target.classList.add('focus-visible');
        
        // Announce focus changes for screen readers
        this.announceFocusChange(target);
        
        // Update focus index
        this.updateFocusIndex(target);
        
        // Ensure focus is visible
        this.ensureFocusVisibility(target);
    }

    /**
     * Handle focus out events
     */
    handleFocusOut(event) {
        const target = event.target;
        
        // Remove focus indicator class
        target.classList.remove('focus-visible');
        
        // Remove any temporary focus styles
        target.style.outline = '';
        target.style.outlineOffset = '';
    }

    /**
     * Handle keyboard navigation
     */
    handleKeyDown(event) {
        const target = event.target;
        
        switch (event.key) {
            case 'Tab':
                this.handleTabNavigation(event);
                break;
            case 'Enter':
            case ' ':
                this.handleActivation(event);
                break;
            case 'Escape':
                this.handleEscape(event);
                break;
            case 'ArrowUp':
            case 'ArrowDown':
            case 'ArrowLeft':
            case 'ArrowRight':
                this.handleArrowNavigation(event);
                break;
        }
    }

    /**
     * Handle tab navigation
     */
    handleTabNavigation(event) {
        // Update focusable elements list
        this.updateFocusableElements();
        
        // Ensure focus is visible
        setTimeout(() => {
            const activeElement = document.activeElement;
            if (activeElement) {
                this.ensureFocusVisibility(activeElement);
            }
        }, 0);
    }

    /**
     * Handle element activation
     */
    handleActivation(event) {
        const target = event.target;
        
        // Prevent default for space key on buttons
        if (event.key === ' ' && target.tagName === 'BUTTON') {
            event.preventDefault();
        }
        
        // Add activation feedback
        this.addActivationFeedback(target);
    }

    /**
     * Handle escape key
     */
    handleEscape(event) {
        // Close modals, dropdowns, etc.
        this.closeActiveOverlays();
        
        // Return focus to trigger element
        this.returnFocusToTrigger();
    }

    /**
     * Handle arrow key navigation
     */
    handleArrowNavigation(event) {
        const target = event.target;
        
        // Handle custom select components
        if (target.classList.contains('custom-select')) {
            this.handleCustomSelectNavigation(event);
        }
        
        // Handle custom dropdown components
        if (target.classList.contains('custom-dropdown')) {
            this.handleCustomDropdownNavigation(event);
        }
        
        // Handle data table navigation
        if (target.closest('.data-table')) {
            this.handleTableNavigation(event);
        }
    }

    /**
     * Enhance keyboard navigation
     */
    enhanceKeyboardNavigation() {
        // Add tabindex to interactive elements
        this.addTabIndexToInteractiveElements();
        
        // Ensure proper tab order
        this.optimizeTabOrder();
        
        // Add keyboard shortcuts
        this.addKeyboardShortcuts();
    }

    /**
     * Add tabindex to interactive elements
     */
    addTabIndexToInteractiveElements() {
        const interactiveSelectors = [
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            'a[href]',
            '[tabindex]',
            '[role="button"]',
            '[role="link"]',
            '[role="menuitem"]',
            '[role="tab"]'
        ];
        
        const interactiveElements = document.querySelectorAll(interactiveSelectors.join(','));
        
        interactiveElements.forEach((element, index) => {
            if (!element.hasAttribute('tabindex')) {
                element.setAttribute('tabindex', '0');
            }
        });
    }

    /**
     * Optimize tab order
     */
    optimizeTabOrder() {
        // Ensure logical tab order
        const focusableElements = this.getFocusableElements();
        
        focusableElements.forEach((element, index) => {
            element.setAttribute('tabindex', index + 1);
        });
    }

    /**
     * Add keyboard shortcuts
     */
    addKeyboardShortcuts() {
        // Skip to main content
        document.addEventListener('keydown', (event) => {
            if (event.key === 'S' && event.altKey) {
                event.preventDefault();
                this.skipToMainContent();
            }
        });
        
        // Toggle high contrast mode
        document.addEventListener('keydown', (event) => {
            if (event.key === 'H' && event.altKey) {
                event.preventDefault();
                this.toggleHighContrastMode();
            }
        });
        
        // Toggle reduced motion
        document.addEventListener('keydown', (event) => {
            if (event.key === 'M' && event.altKey) {
                event.preventDefault();
                this.toggleReducedMotion();
            }
        });
    }

    /**
     * Setup focus management
     */
    setupFocusManagement() {
        // Create focus trap for modals
        this.setupFocusTraps();
        
        // Manage focus for dynamic content
        this.setupDynamicFocusManagement();
        
        // Ensure focus restoration
        this.setupFocusRestoration();
    }

    /**
     * Setup focus traps for modals
     */
    setupFocusTraps() {
        const modals = document.querySelectorAll('[role="dialog"], .modal, .popup');
        
        modals.forEach(modal => {
            this.createFocusTrap(modal);
        });
    }

    /**
     * Create focus trap for a modal
     */
    createFocusTrap(modal) {
        const focusableElements = modal.querySelectorAll(
            'button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        modal.addEventListener('keydown', (event) => {
            if (event.key === 'Tab') {
                if (event.shiftKey) {
                    if (document.activeElement === firstElement) {
                        event.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        event.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });
    }

    /**
     * Setup dynamic focus management
     */
    setupDynamicFocusManagement() {
        // Observe DOM changes for new interactive elements
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.enhanceNewElements(node);
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Enhance newly added elements
     */
    enhanceNewElements(element) {
        // Add accessibility attributes to new interactive elements
        const interactiveElements = element.querySelectorAll(
            'button, input, select, textarea, a[href]'
        );
        
        interactiveElements.forEach(el => {
            this.addAccessibilityAttributes(el);
        });
    }

    /**
     * Add accessibility attributes to elements
     */
    addAccessibilityAttributes(element) {
        // Add ARIA labels if missing
        if (element.tagName === 'BUTTON' && !element.getAttribute('aria-label')) {
            const text = element.textContent.trim();
            if (text) {
                element.setAttribute('aria-label', text);
            }
        }
        
        // Add role if appropriate
        if (element.tagName === 'BUTTON' && !element.getAttribute('role')) {
            element.setAttribute('role', 'button');
        }
        
        // Add tabindex if missing
        if (!element.hasAttribute('tabindex')) {
            element.setAttribute('tabindex', '0');
        }
    }

    /**
     * Initialize visual indicators beyond color
     */
    initializeVisualIndicators() {
        // Add patterns to financial status indicators
        this.addPatternsToStatusIndicators();
        
        // Add icons to form validation states
        this.addIconsToFormValidation();
        
        // Add text labels to color-coded elements
        this.addTextLabelsToColorCodedElements();
        
        // Enhance error states with multiple visual cues
        this.enhanceErrorStates();
    }

    /**
     * Add patterns to status indicators
     */
    addPatternsToStatusIndicators() {
        const statusIndicators = document.querySelectorAll('.status-indicator');
        
        statusIndicators.forEach(indicator => {
            if (indicator.classList.contains('status-profit')) {
                indicator.style.backgroundImage = 'repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(255,255,255,0.1) 2px, rgba(255,255,255,0.1) 4px)';
            } else if (indicator.classList.contains('status-loss')) {
                indicator.style.backgroundImage = 'repeating-linear-gradient(-45deg, transparent, transparent 2px, rgba(255,255,255,0.1) 2px, rgba(255,255,255,0.1) 4px)';
            } else if (indicator.classList.contains('status-neutral')) {
                indicator.style.backgroundImage = 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.1) 2px, rgba(255,255,255,0.1) 4px)';
            }
        });
    }

    /**
     * Add icons to form validation
     */
    addIconsToFormValidation() {
        const formInputs = document.querySelectorAll('input, select, textarea');
        
        formInputs.forEach(input => {
            const wrapper = document.createElement('div');
            wrapper.className = 'form-input-wrapper';
            
            // Add validation icon
            const icon = document.createElement('span');
            icon.className = 'validation-icon';
            icon.setAttribute('aria-hidden', 'true');
            
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(input);
            wrapper.appendChild(icon);
            
            // Update icon based on validation state
            this.updateValidationIcon(input, icon);
        });
    }

    /**
     * Update validation icon
     */
    updateValidationIcon(input, icon) {
        const updateIcon = () => {
            if (input.validity.valid && input.value) {
                icon.textContent = '✓';
                icon.className = 'validation-icon valid';
                input.classList.add('valid');
                input.classList.remove('invalid');
            } else if (input.validity.valid === false) {
                icon.textContent = '✗';
                icon.className = 'validation-icon invalid';
                input.classList.add('invalid');
                input.classList.remove('valid');
            } else {
                icon.textContent = '';
                icon.className = 'validation-icon';
                input.classList.remove('valid', 'invalid');
            }
        };
        
        input.addEventListener('input', updateIcon);
        input.addEventListener('blur', updateIcon);
        updateIcon(); // Initial state
    }

    /**
     * Add text labels to color-coded elements
     */
    addTextLabelsToColorCodedElements() {
        // Add labels to financial data cells
        const financialCells = document.querySelectorAll('[data-financial-status]');
        
        financialCells.forEach(cell => {
            const status = cell.getAttribute('data-financial-status');
            const value = cell.textContent;
            
            // Add descriptive text
            const label = document.createElement('span');
            label.className = 'financial-status-label';
            label.textContent = `Status: ${status}`;
            label.setAttribute('aria-label', `Financial status: ${status}, Value: ${value}`);
            
            cell.appendChild(label);
        });
    }

    /**
     * Enhance error states with multiple visual cues
     */
    enhanceErrorStates() {
        const errorElements = document.querySelectorAll('.error, .error-message, [aria-invalid="true"]');
        
        errorElements.forEach(element => {
            // Add error icon
            if (!element.querySelector('.error-icon')) {
                const icon = document.createElement('span');
                icon.className = 'error-icon';
                icon.textContent = '⚠';
                icon.setAttribute('aria-hidden', 'true');
                element.insertBefore(icon, element.firstChild);
            }
            
            // Add error pattern
            element.style.backgroundImage = 'repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(231, 76, 60, 0.1) 2px, rgba(231, 76, 60, 0.1) 4px)';
            
            // Add border animation
            element.style.borderLeft = '4px solid #e74c3c';
            element.style.animation = 'error-pulse 2s infinite';
        });
    }

    /**
     * Setup motion accessibility
     */
    setupMotionAccessibility() {
        // Add motion controls
        this.addMotionControls();
        
        // Implement safe animations
        this.implementSafeAnimations();
        
        // Add pause controls for auto-playing content
        this.addPauseControls();
    }

    /**
     * Add motion controls
     */
    addMotionControls() {
        // Create motion control panel
        const controlPanel = document.createElement('div');
        controlPanel.className = 'motion-control-panel';
        controlPanel.setAttribute('role', 'region');
        controlPanel.setAttribute('aria-label', 'Motion and animation controls');
        
        controlPanel.innerHTML = `
            <button class="motion-control-btn" id="pause-motion" aria-label="Pause all animations">
                ⏸ Pause Motion
            </button>
            <button class="motion-control-btn" id="resume-motion" aria-label="Resume all animations" style="display: none;">
                ▶ Resume Motion
            </button>
            <button class="motion-control-btn" id="toggle-motion" aria-label="Toggle motion preferences">
                ${this.isReducedMotion ? 'Enable' : 'Disable'} Motion
            </button>
        `;
        
        // Add to page
        document.body.appendChild(controlPanel);
        
        // Add event listeners
        this.setupMotionControlEvents(controlPanel);
    }

    /**
     * Setup motion control events
     */
    setupMotionControlEvents(controlPanel) {
        const pauseBtn = controlPanel.querySelector('#pause-motion');
        const resumeBtn = controlPanel.querySelector('#resume-motion');
        const toggleBtn = controlPanel.querySelector('#toggle-motion');
        
        pauseBtn.addEventListener('click', () => {
            this.pauseAllAnimations();
            pauseBtn.style.display = 'none';
            resumeBtn.style.display = 'inline-block';
        });
        
        resumeBtn.addEventListener('click', () => {
            this.resumeAllAnimations();
            resumeBtn.style.display = 'none';
            pauseBtn.style.display = 'inline-block';
        });
        
        toggleBtn.addEventListener('click', () => {
            this.toggleMotionPreferences();
        });
    }

    /**
     * Pause all animations
     */
    pauseAllAnimations() {
        const animatedElements = document.querySelectorAll('.animate, [style*="animation"], [style*="transition"]');
        
        animatedElements.forEach(element => {
            element.style.animationPlayState = 'paused';
            element.style.transition = 'none';
        });
        
        // Add paused class to body
        document.body.classList.add('motion-paused');
    }

    /**
     * Resume all animations
     */
    resumeAllAnimations() {
        const animatedElements = document.querySelectorAll('.animate, [style*="animation"], [style*="transition"]');
        
        animatedElements.forEach(element => {
            element.style.animationPlayState = 'running';
            element.style.transition = '';
        });
        
        // Remove paused class from body
        document.body.classList.remove('motion-paused');
    }

    /**
     * Toggle motion preferences
     */
    toggleMotionPreferences() {
        this.isReducedMotion = !this.isReducedMotion;
        this.applyUserPreferences();
        
        // Update button text
        const toggleBtn = document.querySelector('#toggle-motion');
        if (toggleBtn) {
            toggleBtn.textContent = `${this.isReducedMotion ? 'Enable' : 'Disable'} Motion`;
        }
    }

    /**
     * Run color contrast audit
     */
    runContrastAudit() {
        this.contrastTestResults = {};
        
        // Test all text/background combinations
        const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, a, label, button, input, select, textarea');
        
        textElements.forEach(element => {
            const contrastRatio = this.calculateContrastRatio(element);
            const elementPath = this.getElementPath(element);
            
            this.contrastTestResults[elementPath] = {
                element: element,
                contrastRatio: contrastRatio,
                passes: contrastRatio >= 4.5,
                wcagLevel: contrastRatio >= 7.0 ? 'AAA' : contrastRatio >= 4.5 ? 'AA' : 'Fail'
            };
        });
        
        // Log results
        this.logContrastAuditResults();
        
        // Fix failing contrast ratios
        this.fixFailingContrastRatios();
    }

    /**
     * Calculate contrast ratio between text and background
     */
    calculateContrastRatio(element) {
        const styles = window.getComputedStyle(element);
        const textColor = this.parseColor(styles.color);
        const backgroundColor = this.parseColor(styles.backgroundColor);
        
        if (!textColor || !backgroundColor) {
            return 0;
        }
        
        const textLuminance = this.calculateLuminance(textColor);
        const backgroundLuminance = this.calculateLuminance(backgroundColor);
        
        const lighter = Math.max(textLuminance, backgroundLuminance);
        const darker = Math.min(textLuminance, backgroundLuminance);
        
        return (lighter + 0.05) / (darker + 0.05);
    }

    /**
     * Parse color string to RGB values
     */
    parseColor(colorString) {
        // Handle named colors
        const colorMap = {
            'black': [0, 0, 0],
            'white': [255, 255, 255],
            'red': [255, 0, 0],
            'green': [0, 128, 0],
            'blue': [0, 0, 255],
            'yellow': [255, 255, 0],
            'cyan': [0, 255, 255],
            'magenta': [255, 0, 255]
        };
        
        if (colorMap[colorString.toLowerCase()]) {
            return colorMap[colorString.toLowerCase()];
        }
        
        // Handle hex colors
        if (colorString.startsWith('#')) {
            const hex = colorString.slice(1);
            const r = parseInt(hex.slice(0, 2), 16);
            const g = parseInt(hex.slice(2, 4), 16);
            const b = parseInt(hex.slice(4, 6), 16);
            return [r, g, b];
        }
        
        // Handle rgb/rgba colors
        const rgbMatch = colorString.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/);
        if (rgbMatch) {
            return [parseInt(rgbMatch[1]), parseInt(rgbMatch[2]), parseInt(rgbMatch[3])];
        }
        
        return null;
    }

    /**
     * Calculate luminance of a color
     */
    calculateLuminance(rgb) {
        const [r, g, b] = rgb.map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    }

    /**
     * Get element path for identification
     */
    getElementPath(element) {
        const path = [];
        let current = element;
        
        while (current && current !== document.body) {
            let selector = current.tagName.toLowerCase();
            
            if (current.id) {
                selector += `#${current.id}`;
            } else if (current.className) {
                selector += `.${current.className.split(' ').join('.')}`;
            }
            
            path.unshift(selector);
            current = current.parentElement;
        }
        
        return path.join(' > ');
    }

    /**
     * Log contrast audit results
     */
    logContrastAuditResults() {
        const totalElements = Object.keys(this.contrastTestResults).length;
        const passingElements = Object.values(this.contrastTestResults).filter(result => result.passes).length;
        const failingElements = totalElements - passingElements;
        
        console.log('=== Color Contrast Audit Results ===');
        console.log(`Total elements tested: ${totalElements}`);
        console.log(`Passing WCAG AA (4.5:1): ${passingElements}`);
        console.log(`Failing WCAG AA: ${failingElements}`);
        console.log(`Compliance rate: ${((passingElements / totalElements) * 100).toFixed(1)}%`);
        
        if (failingElements > 0) {
            console.log('\nFailing elements:');
            Object.entries(this.contrastTestResults)
                .filter(([path, result]) => !result.passes)
                .forEach(([path, result]) => {
                    console.log(`- ${path}: ${result.contrastRatio.toFixed(2)}:1 (${result.wcagLevel})`);
                });
        }
    }

    /**
     * Fix failing contrast ratios
     */
    fixFailingContrastRatios() {
        Object.entries(this.contrastTestResults)
            .filter(([path, result]) => !result.passes)
            .forEach(([path, result]) => {
                this.fixElementContrast(result.element);
            });
    }

    /**
     * Fix contrast for a specific element
     */
    fixElementContrast(element) {
        const styles = window.getComputedStyle(element);
        const currentColor = styles.color;
        const backgroundColor = styles.backgroundColor;
        
        // Try different color combinations to achieve 4.5:1 ratio
        const colorOptions = [
            '#ffffff', // White
            '#000000', // Black
            '#e0e0e0', // Light gray
            '#404040', // Dark gray
            '#00d4aa', // Primary teal
            '#667eea'  // Secondary blue
        ];
        
        for (const color of colorOptions) {
            const testElement = element.cloneNode(true);
            testElement.style.color = color;
            testElement.style.backgroundColor = backgroundColor;
            
            const contrastRatio = this.calculateContrastRatio(testElement);
            
            if (contrastRatio >= 4.5) {
                element.style.color = color;
                console.log(`Fixed contrast for ${this.getElementPath(element)}: ${contrastRatio.toFixed(2)}:1`);
                break;
            }
        }
    }

    /**
     * Announce accessibility features to screen readers
     */
    announceAccessibilityFeatures() {
        const announcement = document.createElement('div');
        announcement.className = 'sr-only';
        announcement.setAttribute('aria-live', 'polite');
        announcement.textContent = 'Accessibility features enabled: High contrast mode, reduced motion support, enhanced keyboard navigation, and visual indicators beyond color.';
        
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => {
            announcement.remove();
        }, 1000);
    }

    /**
     * Announce focus changes
     */
    announceFocusChange(element) {
        const announcement = document.createElement('div');
        announcement.className = 'sr-only';
        announcement.setAttribute('aria-live', 'polite');
        
        let text = '';
        if (element.tagName === 'BUTTON') {
            text = `Button: ${element.textContent.trim() || element.getAttribute('aria-label') || 'Unlabeled button'}`;
        } else if (element.tagName === 'INPUT') {
            text = `Input: ${element.getAttribute('placeholder') || element.getAttribute('aria-label') || 'Text input'}`;
        } else if (element.tagName === 'A') {
            text = `Link: ${element.textContent.trim() || element.getAttribute('aria-label') || 'Unlabeled link'}`;
        } else {
            text = `Focused: ${element.textContent.trim() || element.getAttribute('aria-label') || 'Element'}`;
        }
        
        announcement.textContent = text;
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            announcement.remove();
        }, 1000);
    }

    /**
     * Ensure focus visibility
     */
    ensureFocusVisibility(element) {
        // Add high visibility focus indicator
        element.style.outline = '3px solid var(--focus-color)';
        element.style.outlineOffset = '3px';
        element.style.borderRadius = '4px';
        
        // Add focus ring animation
        element.style.animation = 'focus-ring 0.3s ease-out';
        
        // Ensure element is in viewport
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Update focus index
     */
    updateFocusIndex(element) {
        const focusableElements = this.getFocusableElements();
        this.currentFocusIndex = focusableElements.indexOf(element);
    }

    /**
     * Get all focusable elements
     */
    getFocusableElements() {
        const focusableSelectors = [
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            'a[href]',
            '[tabindex]:not([tabindex="-1"])',
            '[role="button"]',
            '[role="link"]',
            '[role="menuitem"]',
            '[role="tab"]'
        ];
        
        return Array.from(document.querySelectorAll(focusableSelectors.join(',')))
            .filter(element => {
                const styles = window.getComputedStyle(element);
                return styles.display !== 'none' && styles.visibility !== 'hidden';
            });
    }

    /**
     * Update focusable elements list
     */
    updateFocusableElements() {
        this.focusableElements = this.getFocusableElements();
    }

    /**
     * Skip to main content
     */
    skipToMainContent() {
        const mainContent = document.querySelector('main, [role="main"], #main-content');
        if (mainContent) {
            mainContent.focus();
            mainContent.scrollIntoView({ behavior: 'smooth' });
        }
    }

    /**
     * Toggle high contrast mode
     */
    toggleHighContrastMode() {
        this.isHighContrastMode = !this.isHighContrastMode;
        this.applyUserPreferences();
        
        // Announce change
        const announcement = document.createElement('div');
        announcement.className = 'sr-only';
        announcement.setAttribute('aria-live', 'polite');
        announcement.textContent = `High contrast mode ${this.isHighContrastMode ? 'enabled' : 'disabled'}`;
        
        document.body.appendChild(announcement);
        setTimeout(() => announcement.remove(), 1000);
    }

    /**
     * Toggle reduced motion
     */
    toggleReducedMotion() {
        this.isReducedMotion = !this.isReducedMotion;
        this.applyUserPreferences();
        
        // Announce change
        const announcement = document.createElement('div');
        announcement.className = 'sr-only';
        announcement.setAttribute('aria-live', 'polite');
        announcement.textContent = `Motion ${this.isReducedMotion ? 'reduced' : 'enabled'}`;
        
        document.body.appendChild(announcement);
        setTimeout(() => announcement.remove(), 1000);
    }

    /**
     * Load accessibility settings from localStorage
     */
    loadAccessibilitySettings() {
        const defaultSettings = {
            highContrast: false,
            reducedMotion: false,
            fontSize: 'normal',
            lineSpacing: 'normal',
            focusIndicator: 'enhanced'
        };
        
        try {
            const saved = localStorage.getItem('mingus-accessibility-settings');
            return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
        } catch (error) {
            console.warn('Could not load accessibility settings:', error);
            return defaultSettings;
        }
    }

    /**
     * Save accessibility settings to localStorage
     */
    saveAccessibilitySettings() {
        try {
            localStorage.setItem('mingus-accessibility-settings', JSON.stringify(this.accessibilitySettings));
        } catch (error) {
            console.warn('Could not save accessibility settings:', error);
        }
    }

    /**
     * Handle form validation accessibility
     */
    handleFormInvalid(event) {
        const element = event.target;
        
        // Add error styling
        element.classList.add('invalid');
        
        // Announce error
        const errorMessage = element.validationMessage;
        this.announceFormError(errorMessage);
        
        // Add error icon
        this.addErrorIcon(element);
    }

    /**
     * Handle form input
     */
    handleFormInput(event) {
        const element = event.target;
        
        // Remove error styling if valid
        if (element.validity.valid) {
            element.classList.remove('invalid');
            this.removeErrorIcon(element);
        }
    }

    /**
     * Announce form error
     */
    announceFormError(message) {
        const announcement = document.createElement('div');
        announcement.className = 'sr-only';
        announcement.setAttribute('aria-live', 'assertive');
        announcement.textContent = `Error: ${message}`;
        
        document.body.appendChild(announcement);
        setTimeout(() => announcement.remove(), 3000);
    }

    /**
     * Add error icon to form element
     */
    addErrorIcon(element) {
        if (!element.parentNode.querySelector('.form-error-icon')) {
            const icon = document.createElement('span');
            icon.className = 'form-error-icon';
            icon.textContent = '⚠';
            icon.setAttribute('aria-hidden', 'true');
            
            element.parentNode.appendChild(icon);
        }
    }

    /**
     * Remove error icon from form element
     */
    removeErrorIcon(element) {
        const icon = element.parentNode.querySelector('.form-error-icon');
        if (icon) {
            icon.remove();
        }
    }

    /**
     * Handle mouse enter for hover effects
     */
    handleMouseEnter(event) {
        const target = event.target;
        
        // Add hover class
        target.classList.add('hover');
        
        // Ensure hover effects work with keyboard focus
        if (target.matches(':focus')) {
            target.classList.add('hover-focus');
        }
    }

    /**
     * Handle mouse leave for hover effects
     */
    handleMouseLeave(event) {
        const target = event.target;
        
        // Remove hover class
        target.classList.remove('hover');
        target.classList.remove('hover-focus');
    }

    /**
     * Handle page visibility changes
     */
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden, pause animations
            this.pauseAllAnimations();
        } else {
            // Page is visible, resume animations if not in reduced motion mode
            if (!this.isReducedMotion) {
                this.resumeAllAnimations();
            }
        }
    }

    /**
     * Close active overlays
     */
    closeActiveOverlays() {
        // Close modals
        const modals = document.querySelectorAll('[role="dialog"], .modal, .popup');
        modals.forEach(modal => {
            if (modal.style.display !== 'none') {
                modal.style.display = 'none';
                modal.setAttribute('aria-hidden', 'true');
            }
        });
        
        // Close dropdowns
        const dropdowns = document.querySelectorAll('.dropdown, [role="menu"]');
        dropdowns.forEach(dropdown => {
            if (dropdown.classList.contains('open')) {
                dropdown.classList.remove('open');
                dropdown.setAttribute('aria-expanded', 'false');
            }
        });
    }

    /**
     * Return focus to trigger element
     */
    returnFocusToTrigger() {
        const trigger = document.querySelector('[data-focus-trigger]');
        if (trigger) {
            trigger.focus();
        }
    }

    /**
     * Handle custom select navigation
     */
    handleCustomSelectNavigation(event) {
        const select = event.target;
        const options = select.querySelectorAll('[role="option"]');
        const currentIndex = Array.from(options).findIndex(option => option.getAttribute('aria-selected') === 'true');
        
        let newIndex = currentIndex;
        
        if (event.key === 'ArrowDown') {
            newIndex = Math.min(currentIndex + 1, options.length - 1);
        } else if (event.key === 'ArrowUp') {
            newIndex = Math.max(currentIndex - 1, 0);
        }
        
        if (newIndex !== currentIndex) {
            options[currentIndex].setAttribute('aria-selected', 'false');
            options[newIndex].setAttribute('aria-selected', 'true');
            options[newIndex].focus();
        }
    }

    /**
     * Handle custom dropdown navigation
     */
    handleCustomDropdownNavigation(event) {
        const dropdown = event.target;
        const menu = dropdown.querySelector('[role="menu"]');
        const items = menu.querySelectorAll('[role="menuitem"]');
        const currentIndex = Array.from(items).findIndex(item => item === document.activeElement);
        
        let newIndex = currentIndex;
        
        if (event.key === 'ArrowDown') {
            newIndex = Math.min(currentIndex + 1, items.length - 1);
        } else if (event.key === 'ArrowUp') {
            newIndex = Math.max(currentIndex - 1, 0);
        }
        
        if (newIndex !== currentIndex) {
            items[newIndex].focus();
        }
    }

    /**
     * Handle table navigation
     */
    handleTableNavigation(event) {
        const table = event.target.closest('.data-table');
        const cells = table.querySelectorAll('td, th');
        const currentIndex = Array.from(cells).findIndex(cell => cell === document.activeElement);
        
        let newIndex = currentIndex;
        const rowLength = table.querySelector('tr').cells.length;
        
        if (event.key === 'ArrowRight') {
            newIndex = Math.min(currentIndex + 1, cells.length - 1);
        } else if (event.key === 'ArrowLeft') {
            newIndex = Math.max(currentIndex - 1, 0);
        } else if (event.key === 'ArrowDown') {
            newIndex = Math.min(currentIndex + rowLength, cells.length - 1);
        } else if (event.key === 'ArrowUp') {
            newIndex = Math.max(currentIndex - rowLength, 0);
        }
        
        if (newIndex !== currentIndex && newIndex >= 0 && newIndex < cells.length) {
            cells[newIndex].focus();
        }
    }

    /**
     * Add activation feedback
     */
    addActivationFeedback(element) {
        // Add visual feedback
        element.style.transform = 'scale(0.95)';
        element.style.transition = 'transform 0.1s ease';
        
        // Remove feedback after animation
        setTimeout(() => {
            element.style.transform = '';
            element.style.transition = '';
        }, 100);
    }

    /**
     * Get accessibility status
     */
    getAccessibilityStatus() {
        return {
            highContrastMode: this.isHighContrastMode,
            reducedMotion: this.isReducedMotion,
            focusableElements: this.focusableElements.length,
            contrastTestResults: this.contrastTestResults,
            settings: this.accessibilitySettings
        };
    }
}

// Initialize accessibility manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.mingusAccessibility = new EnhancedAccessibilityManager();
    });
} else {
    window.mingusAccessibility = new EnhancedAccessibilityManager();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedAccessibilityManager;
}
