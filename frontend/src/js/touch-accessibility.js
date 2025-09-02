/**
 * MINGUS Touch Accessibility System
 * Comprehensive accessibility support for touch interactions and assistive technology
 */

class TouchAccessibilityManager {
    constructor() {
        this.focusableElements = new Set();
        this.focusTraps = new Map();
        this.announcements = new Map();
        this.alternativeControls = new Map();
        this.accessibilitySettings = {
            hapticEnabled: true,
            soundEnabled: false,
            highContrast: false,
            reducedMotion: false,
            screenReaderMode: false
        };
        
        this.init();
    }
    
    init() {
        this.setupAccessibilityDetection();
        this.setupAssistiveTechnologySupport();
        this.setupFocusManagement();
        this.setupAlternativeInteractions();
        this.setupAccessibilityTesting();
        this.setupSettingsIntegration();
    }
    
    // ===== ACCESSIBILITY DETECTION =====
    setupAccessibilityDetection() {
        // Detect user accessibility preferences
        this.detectAccessibilityPreferences();
        this.detectAssistiveTechnology();
        this.detectDeviceCapabilities();
    }
    
    detectAccessibilityPreferences() {
        // Check for reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.accessibilitySettings.reducedMotion = true;
            this.applyReducedMotion();
        }
        
        // Check for high contrast preference
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            this.accessibilitySettings.highContrast = true;
            this.applyHighContrast();
        }
        
        // Check for color scheme preference
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.applyDarkMode();
        }
        
        // Listen for preference changes
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            this.accessibilitySettings.reducedMotion = e.matches;
            this.applyReducedMotion();
        });
        
        window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
            this.accessibilitySettings.highContrast = e.matches;
            this.applyHighContrast();
        });
    }
    
    detectAssistiveTechnology() {
        // Detect screen readers
        this.detectScreenReader();
        
        // Detect voice control software
        this.detectVoiceControl();
        
        // Detect switch navigation
        this.detectSwitchNavigation();
    }
    
    detectScreenReader() {
        // Check for common screen reader indicators
        const screenReaderIndicators = [
            'aria-hidden',
            'role',
            'aria-label',
            'aria-describedby'
        ];
        
        const hasScreenReader = screenReaderIndicators.some(indicator => {
            return document.querySelector(`[${indicator}]`);
        });
        
        if (hasScreenReader) {
            this.accessibilitySettings.screenReaderMode = true;
            this.enableScreenReaderMode();
        }
    }
    
    detectVoiceControl() {
        // Check for voice control software
        const voiceControlIndicators = [
            'speech',
            'voice',
            'dictation'
        ];
        
        // Listen for voice control events
        document.addEventListener('speechstart', () => {
            this.enableVoiceControlMode();
        });
        
        document.addEventListener('speechend', () => {
            this.disableVoiceControlMode();
        });
    }
    
    detectSwitchNavigation() {
        // Check for switch navigation devices
        let lastKeyTime = 0;
        let keyCount = 0;
        
        document.addEventListener('keydown', (e) => {
            const currentTime = Date.now();
            
            if (currentTime - lastKeyTime < 1000) {
                keyCount++;
                if (keyCount > 5) {
                    this.enableSwitchNavigationMode();
                }
            } else {
                keyCount = 1;
            }
            
            lastKeyTime = currentTime;
        });
    }
    
    detectDeviceCapabilities() {
        // Check for touch capabilities
        if ('ontouchstart' in window) {
            this.enableTouchAccessibility();
        }
        
        // Check for haptic feedback support
        if ('vibrate' in navigator) {
            this.accessibilitySettings.hapticEnabled = true;
        }
        
        // Check for audio capabilities
        if ('AudioContext' in window || 'webkitAudioContext' in window) {
            this.accessibilitySettings.soundEnabled = true;
        }
    }
    
    // ===== ASSISTIVE TECHNOLOGY SUPPORT =====
    setupAssistiveTechnologySupport() {
        this.setupScreenReaderSupport();
        this.setupVoiceControlSupport();
        this.setupSwitchNavigationSupport();
        this.setupBrailleDisplaySupport();
    }
    
    setupScreenReaderSupport() {
        // Enhanced ARIA support for financial data
        this.enhanceFinancialDataARIA();
        this.setupLiveRegions();
        this.setupLandmarkNavigation();
    }
    
    enhanceFinancialDataARIA() {
        // Add comprehensive ARIA labels to financial elements
        const financialElements = document.querySelectorAll('.financial-data-item, .chart-container, .metric-card');
        
        financialElements.forEach((element, index) => {
            // Add role and state information
            element.setAttribute('role', 'button');
            element.setAttribute('tabindex', '0');
            element.setAttribute('aria-expanded', 'false');
            element.setAttribute('aria-describedby', `financial-desc-${index}`);
            
            // Create description element
            const description = document.createElement('div');
            description.id = `financial-desc-${index}`;
            description.className = 'sr-only';
            description.textContent = this.generateFinancialDescription(element);
            
            element.appendChild(description);
            
            // Add keyboard support
            element.addEventListener('keydown', (e) => {
                this.handleFinancialElementKeyboard(e, element);
            });
        });
    }
    
    generateFinancialDescription(element) {
        // Generate accessible description for financial data
        const title = element.querySelector('.title, .label, h3, h4')?.textContent || 'Financial data item';
        const value = element.querySelector('.value, .amount, .number')?.textContent || '';
        const change = element.querySelector('.change, .trend')?.textContent || '';
        
        let description = `${title}`;
        if (value) description += `, ${value}`;
        if (change) description += `, ${change}`;
        
        return description;
    }
    
    setupLiveRegions() {
        // Create live regions for dynamic content updates
        const liveRegions = [
            { id: 'financial-updates', type: 'polite' },
            { id: 'navigation-alerts', type: 'assertive' },
            { id: 'form-status', type: 'polite' },
            { id: 'chart-updates', type: 'polite' }
        ];
        
        liveRegions.forEach(region => {
            const liveRegion = document.createElement('div');
            liveRegion.id = region.id;
            liveRegion.setAttribute('aria-live', region.type);
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            
            document.body.appendChild(liveRegion);
            this.announcements.set(region.id, liveRegion);
        });
    }
    
    setupLandmarkNavigation() {
        // Add landmark roles for better navigation
        const landmarks = [
            { selector: 'header', role: 'banner' },
            { selector: 'nav', role: 'navigation' },
            { selector: 'main', role: 'main' },
            { selector: 'aside', role: 'complementary' },
            { selector: 'footer', role: 'contentinfo' }
        ];
        
        landmarks.forEach(landmark => {
            const element = document.querySelector(landmark.selector);
            if (element) {
                element.setAttribute('role', landmark.role);
            }
        });
        
        // Add skip links
        this.createSkipLinks();
    }
    
    createSkipLinks() {
        const skipLinks = [
            { href: '#main-content', text: 'Skip to main content' },
            { href: '#navigation', text: 'Skip to navigation' },
            { href: '#financial-summary', text: 'Skip to financial summary' },
            { href: '#footer', text: 'Skip to footer' }
        ];
        
        skipLinks.forEach(link => {
            const skipLink = document.createElement('a');
            skipLink.href = link.href;
            skipLink.textContent = link.text;
            skipLink.className = 'skip-link';
            
            document.body.insertBefore(skipLink, document.body.firstChild);
        });
    }
    
    setupVoiceControlSupport() {
        // Voice command recognition for financial actions
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            this.setupSpeechRecognition();
        }
        
        // Voice feedback for actions
        this.setupVoiceFeedback();
    }
    
    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = (event) => {
            const command = event.results[event.results.length - 1][0].transcript.toLowerCase();
            this.handleVoiceCommand(command);
        };
        
        // Start listening when voice control mode is enabled
        this.voiceRecognition = recognition;
    }
    
    handleVoiceCommand(command) {
        // Handle voice commands for financial actions
        const commands = {
            'show dashboard': () => this.navigateToPage('dashboard'),
            'show analytics': () => this.navigateToPage('analytics'),
            'show portfolio': () => this.navigateToPage('portfolio'),
            'transfer money': () => this.showBottomSheet('financial-actions'),
            'export data': () => this.showBottomSheet('export-options'),
            'filter data': () => this.showBottomSheet('data-filters'),
            'refresh': () => this.refreshFinancialData(),
            'help': () => this.showAccessibilityHelp()
        };
        
        for (const [cmd, action] of Object.entries(commands)) {
            if (command.includes(cmd)) {
                action();
                this.announceToScreenReader(`Executing command: ${cmd}`);
                break;
            }
        }
    }
    
    setupVoiceFeedback() {
        // Text-to-speech for financial data
        if ('speechSynthesis' in window) {
            this.speechSynthesis = window.speechSynthesis;
        }
    }
    
    speakText(text, priority = 'low') {
        if (this.speechSynthesis && this.accessibilitySettings.soundEnabled) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.9;
            utterance.pitch = 1;
            utterance.volume = 0.8;
            
            if (priority === 'high') {
                this.speechSynthesis.cancel();
            }
            
            this.speechSynthesis.speak(utterance);
        }
    }
    
    setupSwitchNavigationSupport() {
        // Support for switch navigation devices
        this.setupSwitchControls();
        this.setupScanningMode();
    }
    
    setupSwitchControls() {
        // Create switch-accessible controls
        const switchControls = document.querySelectorAll('.switch-control, [data-switch-enabled]');
        
        switchControls.forEach(control => {
            control.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.activateSwitchControl(control);
                }
            });
            
            control.addEventListener('focus', () => {
                this.highlightSwitchControl(control);
            });
        });
    }
    
    setupScanningMode() {
        // Auto-scanning mode for switch users
        let scanInterval = null;
        let currentFocusIndex = 0;
        
        const startScanning = () => {
            const focusableElements = this.getFocusableElements();
            
            scanInterval = setInterval(() => {
                if (currentFocusIndex >= focusableElements.length) {
                    currentFocusIndex = 0;
                }
                
                focusableElements[currentFocusIndex].focus();
                currentFocusIndex++;
            }, 2000); // 2 second scan interval
        };
        
        const stopScanning = () => {
            if (scanInterval) {
                clearInterval(scanInterval);
                scanInterval = null;
            }
        };
        
        // Toggle scanning mode with spacebar
        document.addEventListener('keydown', (e) => {
            if (e.key === ' ' && e.ctrlKey) {
                e.preventDefault();
                if (scanInterval) {
                    stopScanning();
                } else {
                    startScanning();
                }
            }
        });
    }
    
    // ===== FOCUS MANAGEMENT =====
    setupFocusManagement() {
        this.setupFocusTrapping();
        this.setupFocusIndicators();
        this.setupFocusOrder();
        this.setupFocusRestoration();
    }
    
    setupFocusTrapping() {
        // Trap focus within modals and bottom sheets
        const focusableContainers = document.querySelectorAll('.modal-content, .bottom-sheet, .form-wizard');
        
        focusableContainers.forEach(container => {
            this.createFocusTrap(container);
        });
    }
    
    createFocusTrap(container) {
        const focusableElements = this.getFocusableElements(container);
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (!firstElement || !lastElement) return;
        
        const trapId = `trap-${Date.now()}`;
        
        container.addEventListener('keydown', (e) => {
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
        
        this.focusTraps.set(trapId, {
            container: container,
            firstElement: firstElement,
            lastElement: lastElement
        });
    }
    
    setupFocusIndicators() {
        // Enhanced focus indicators for better visibility
        const style = document.createElement('style');
        style.textContent = `
            .focus-indicator {
                outline: 3px solid var(--primary-color) !important;
                outline-offset: 2px !important;
                border-radius: var(--border-radius) !important;
            }
            
            .focus-indicator-high-contrast {
                outline: 4px solid #ffffff !important;
                outline-offset: 1px !important;
                box-shadow: 0 0 0 2px #000000 !important;
            }
            
            .sr-only {
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                padding: 0 !important;
                margin: -1px !important;
                overflow: hidden !important;
                clip: rect(0, 0, 0, 0) !important;
                white-space: nowrap !important;
                border: 0 !important;
            }
        `;
        
        document.head.appendChild(style);
        
        // Apply focus indicators
        this.applyFocusIndicators();
    }
    
    applyFocusIndicators() {
        const focusableElements = this.getFocusableElements();
        
        focusableElements.forEach(element => {
            element.addEventListener('focus', () => {
                this.addFocusIndicator(element);
            });
            
            element.addEventListener('blur', () => {
                this.removeFocusIndicator(element);
            });
        });
    }
    
    addFocusIndicator(element) {
        if (this.accessibilitySettings.highContrast) {
            element.classList.add('focus-indicator-high-contrast');
        } else {
            element.classList.add('focus-indicator');
        }
    }
    
    removeFocusIndicator(element) {
        element.classList.remove('focus-indicator', 'focus-indicator-high-contrast');
    }
    
    setupFocusOrder() {
        // Ensure logical focus order for keyboard navigation
        const focusableElements = this.getFocusableElements();
        
        focusableElements.forEach((element, index) => {
            element.setAttribute('tabindex', index === 0 ? '0' : '0');
        });
    }
    
    setupFocusRestoration() {
        // Restore focus when modals close or navigation changes
        let lastFocusedElement = null;
        
        document.addEventListener('focusin', (e) => {
            lastFocusedElement = e.target;
        });
        
        // Restore focus after modal closes
        document.addEventListener('modal-closed', () => {
            if (lastFocusedElement && lastFocusedElement.focus) {
                lastFocusedElement.focus();
            }
        });
    }
    
    // ===== ALTERNATIVE INTERACTION METHODS =====
    setupAlternativeInteractions() {
        this.setupKeyboardAlternatives();
        this.setupVoiceAlternatives();
        this.setupGestureAlternatives();
        this.setupSwitchAlternatives();
    }
    
    setupKeyboardAlternatives() {
        // Keyboard shortcuts for touch actions
        this.setupKeyboardShortcuts();
        this.setupKeyboardNavigation();
    }
    
    setupKeyboardShortcuts() {
        const shortcuts = {
            'Alt+D': () => this.showBottomSheet('financial-actions'),
            'Alt+F': () => this.showBottomSheet('data-filters'),
            'Alt+E': () => this.showBottomSheet('export-options'),
            'Alt+S': () => this.showBottomSheet('settings'),
            'Alt+H': () => this.showAccessibilityHelp(),
            'Escape': () => this.closeAllOverlays()
        };
        
        document.addEventListener('keydown', (e) => {
            const key = this.getKeyCombo(e);
            
            if (shortcuts[key]) {
                e.preventDefault();
                shortcuts[key]();
            }
        });
    }
    
    getKeyCombo(event) {
        const modifiers = [];
        if (event.altKey) modifiers.push('Alt');
        if (event.ctrlKey) modifiers.push('Ctrl');
        if (event.shiftKey) modifiers.push('Shift');
        
        const key = event.key.toUpperCase();
        return modifiers.length > 0 ? `${modifiers.join('+')}+${key}` : key;
    }
    
    setupKeyboardNavigation() {
        // Enhanced keyboard navigation for financial data
        const financialContainers = document.querySelectorAll('.financial-data-container');
        
        financialContainers.forEach(container => {
            container.addEventListener('keydown', (e) => {
                switch (e.key) {
                    case 'ArrowLeft':
                        e.preventDefault();
                        this.navigateFinancialData('prev');
                        break;
                    case 'ArrowRight':
                        e.preventDefault();
                        this.navigateFinancialData('next');
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        this.expandFinancialSection();
                        break;
                    case 'ArrowDown':
                        e.preventDefault();
                        this.collapseFinancialSection();
                        break;
                    case 'Enter':
                    case ' ':
                        e.preventDefault();
                        this.activateFinancialElement(container);
                        break;
                }
            });
        });
    }
    
    setupVoiceAlternatives() {
        // Voice commands as alternative to touch
        this.setupVoiceCommands();
        this.setupVoiceFeedback();
    }
    
    setupVoiceCommands() {
        // Additional voice commands for financial actions
        const voiceCommands = {
            'transfer funds': () => this.showBottomSheet('financial-actions'),
            'invest money': () => this.showBottomSheet('financial-actions'),
            'save money': () => this.showBottomSheet('financial-actions'),
            'create budget': () => this.showBottomSheet('financial-actions'),
            'analyze spending': () => this.showBottomSheet('data-filters'),
            'export report': () => this.showBottomSheet('export-options'),
            'show settings': () => this.showBottomSheet('settings')
        };
        
        // Extend existing voice command handler
        this.voiceCommands = { ...this.voiceCommands, ...voiceCommands };
    }
    
    setupGestureAlternatives() {
        // Alternative gesture patterns for users with motor difficulties
        this.setupLargeGestures();
        this.setupSlowGestures();
        this.setupGestureAssistance();
    }
    
    setupLargeGestures() {
        // Larger gesture areas for easier interaction
        const gestureElements = document.querySelectorAll('[data-gesture-enabled]');
        
        gestureElements.forEach(element => {
            element.addEventListener('touchstart', (e) => {
                // Increase touch target size
                element.style.transform = 'scale(1.1)';
            });
            
            element.addEventListener('touchend', () => {
                element.style.transform = '';
            });
        });
    }
    
    setupSlowGestures() {
        // Support for slower gesture recognition
        let gestureTimeout = null;
        
        document.addEventListener('touchstart', () => {
            if (gestureTimeout) {
                clearTimeout(gestureTimeout);
            }
            
            gestureTimeout = setTimeout(() => {
                // Show gesture assistance
                this.showGestureAssistance();
            }, 2000); // 2 second delay for slow gestures
        });
    }
    
    setupGestureAssistance() {
        // Visual assistance for gesture recognition
        const assistance = document.createElement('div');
        assistance.className = 'gesture-assistance';
        assistance.innerHTML = `
            <div class="assistance-content">
                <h3>Gesture Assistance</h3>
                <p>You can also use these alternatives:</p>
                <ul>
                    <li>Keyboard: Arrow keys for navigation</li>
                    <li>Voice: Say "help" for voice commands</li>
                    <li>Switch: Use Tab key for navigation</li>
                </ul>
            </div>
        `;
        
        assistance.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: var(--surface-color);
            padding: 1rem;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-heavy);
            z-index: 10000;
            max-width: 300px;
        `;
        
        document.body.appendChild(assistance);
        
        setTimeout(() => {
            if (assistance.parentNode) {
                assistance.parentNode.removeChild(assistance);
            }
        }, 5000);
    }
    
    // ===== ACCESSIBILITY TESTING =====
    setupAccessibilityTesting() {
        this.setupAutomatedTesting();
        this.setupManualTesting();
        this.setupUserTesting();
    }
    
    setupAutomatedTesting() {
        // Automated accessibility testing
        this.runAccessibilityAudit();
        this.setupContinuousMonitoring();
    }
    
    runAccessibilityAudit() {
        // Run automated accessibility checks
        const auditResults = {
            ariaLabels: this.checkARIALabels(),
            focusOrder: this.checkFocusOrder(),
            colorContrast: this.checkColorContrast(),
            touchTargets: this.checkTouchTargets(),
            keyboardNavigation: this.checkKeyboardNavigation()
        };
        
        console.log('Accessibility Audit Results:', auditResults);
        
        // Fix any issues found
        this.fixAccessibilityIssues(auditResults);
    }
    
    checkARIALabels() {
        const elementsWithoutLabels = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby]), input:not([aria-label]):not([aria-labelledby])');
        return Array.from(elementsWithoutLabels).map(el => ({
            element: el,
            issue: 'Missing ARIA label'
        }));
    }
    
    checkFocusOrder() {
        const focusableElements = this.getFocusableElements();
        const tabIndexes = Array.from(focusableElements).map(el => parseInt(el.getAttribute('tabindex') || '0'));
        
        // Check for logical tab order
        const hasLogicalOrder = tabIndexes.every((index, i) => i === 0 || index >= tabIndexes[i - 1]);
        
        return {
            hasLogicalOrder,
            tabIndexes
        };
    }
    
    checkColorContrast() {
        // Basic color contrast checking
        const textElements = document.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6');
        const contrastIssues = [];
        
        textElements.forEach(element => {
            const style = window.getComputedStyle(element);
            const color = style.color;
            const backgroundColor = style.backgroundColor;
            
            // Simple contrast check (this would need a proper contrast calculation library)
            if (color === backgroundColor) {
                contrastIssues.push({
                    element: element,
                    issue: 'Text and background colors are the same'
                });
            }
        });
        
        return contrastIssues;
    }
    
    checkTouchTargets() {
        const interactiveElements = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
        const smallTargets = [];
        
        interactiveElements.forEach(element => {
            const rect = element.getBoundingClientRect();
            const minSize = 44; // iOS minimum touch target size
            
            if (rect.width < minSize || rect.height < minSize) {
                smallTargets.push({
                    element: element,
                    currentSize: { width: rect.width, height: rect.height },
                    requiredSize: minSize
                });
            }
        });
        
        return smallTargets;
    }
    
    checkKeyboardNavigation() {
        const focusableElements = this.getFocusableElements();
        const navigationIssues = [];
        
        focusableElements.forEach(element => {
            if (!element.hasAttribute('tabindex') && element.tagName !== 'A') {
                navigationIssues.push({
                    element: element,
                    issue: 'Element not keyboard accessible'
                });
            }
        });
        
        return navigationIssues;
    }
    
    fixAccessibilityIssues(issues) {
        // Fix ARIA label issues
        if (issues.ariaLabels) {
            issues.ariaLabels.forEach(issue => {
                this.fixARIALabel(issue.element);
            });
        }
        
        // Fix touch target issues
        if (issues.touchTargets) {
            issues.touchTargets.forEach(issue => {
                this.fixTouchTarget(issue.element, issue.requiredSize);
            });
        }
        
        // Fix keyboard navigation issues
        if (issues.keyboardNavigation) {
            issues.keyboardNavigation.forEach(issue => {
                this.fixKeyboardNavigation(issue.element);
            });
        }
    }
    
    fixARIALabel(element) {
        // Generate appropriate ARIA label
        let label = '';
        
        if (element.tagName === 'BUTTON') {
            label = element.textContent || 'Button';
        } else if (element.tagName === 'INPUT') {
            const placeholder = element.placeholder;
            const type = element.type;
            label = placeholder || `${type} input`;
        }
        
        if (label) {
            element.setAttribute('aria-label', label);
        }
    }
    
    fixTouchTarget(element, requiredSize) {
        // Ensure minimum touch target size
        element.style.minWidth = `${requiredSize}px`;
        element.style.minHeight = `${requiredSize}px`;
    }
    
    fixKeyboardNavigation(element) {
        // Make element keyboard accessible
        element.setAttribute('tabindex', '0');
        
        if (element.tagName === 'BUTTON') {
            element.setAttribute('role', 'button');
        }
    }
    
    // ===== SETTINGS INTEGRATION =====
    setupSettingsIntegration() {
        this.createAccessibilitySettings();
        this.setupSettingsPersistence();
    }
    
    createAccessibilitySettings() {
        const settingsPanel = document.createElement('div');
        settingsPanel.className = 'accessibility-settings-panel';
        settingsPanel.innerHTML = `
            <div class="settings-header">
                <h3>Accessibility Settings</h3>
                <button class="settings-close" aria-label="Close settings">×</button>
            </div>
            <div class="settings-content">
                <div class="setting-group">
                    <label class="setting-label">
                        <input type="checkbox" id="haptic-enabled" ${this.accessibilitySettings.hapticEnabled ? 'checked' : ''}>
                        Enable Haptic Feedback
                    </label>
                </div>
                <div class="setting-group">
                    <label class="setting-label">
                        <input type="checkbox" id="sound-enabled" ${this.accessibilitySettings.soundEnabled ? 'checked' : ''}>
                        Enable Sound Feedback
                    </label>
                </div>
                <div class="setting-group">
                    <label class="setting-label">
                        <input type="checkbox" id="high-contrast" ${this.accessibilitySettings.highContrast ? 'checked' : ''}>
                        High Contrast Mode
                    </label>
                </div>
                <div class="setting-group">
                    <label class="setting-label">
                        <input type="checkbox" id="reduced-motion" ${this.accessibilitySettings.reducedMotion ? 'checked' : ''}>
                        Reduced Motion
                    </label>
                </div>
                <div class="setting-group">
                    <label class="setting-label">
                        <input type="checkbox" id="screen-reader-mode" ${this.accessibilitySettings.screenReaderMode ? 'checked' : ''}>
                        Screen Reader Mode
                    </label>
                </div>
            </div>
        `;
        
        this.setupSettingsControls(settingsPanel);
        document.body.appendChild(settingsPanel);
        settingsPanel.style.display = 'none';
        
        this.settingsPanel = settingsPanel;
    }
    
    setupSettingsControls(panel) {
        const checkboxes = panel.querySelectorAll('input[type="checkbox"]');
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const setting = e.target.id.replace('-enabled', '').replace('-', '');
                const value = e.target.checked;
                
                this.updateAccessibilitySetting(setting, value);
            });
        });
        
        const closeBtn = panel.querySelector('.settings-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hideAccessibilitySettings();
            });
        }
    }
    
    updateAccessibilitySetting(setting, value) {
        this.accessibilitySettings[setting] = value;
        
        // Apply setting changes
        switch (setting) {
            case 'haptic':
                this.toggleHapticFeedback(value);
                break;
            case 'sound':
                this.toggleSoundFeedback(value);
                break;
            case 'highContrast':
                this.toggleHighContrast(value);
                break;
            case 'reducedMotion':
                this.toggleReducedMotion(value);
                break;
            case 'screenReaderMode':
                this.toggleScreenReaderMode(value);
                break;
        }
        
        // Save settings
        this.saveAccessibilitySettings();
        
        // Announce change
        this.announceToScreenReader(`${setting} ${value ? 'enabled' : 'disabled'}`);
    }
    
    // ===== UTILITY METHODS =====
    getFocusableElements(container = document) {
        const focusableSelectors = [
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            'a[href]',
            '[tabindex]:not([tabindex="-1"])',
            '[role="button"]',
            '[role="tab"]',
            '[role="menuitem"]'
        ];
        
        return container.querySelectorAll(focusableSelectors.join(', '));
    }
    
    announceToScreenReader(message, priority = 'polite') {
        const liveRegion = this.announcements.get('financial-updates');
        if (liveRegion) {
            liveRegion.textContent = message;
        }
        
        // Also use speech synthesis if available
        this.speakText(message, priority);
    }
    
    showAccessibilitySettings() {
        if (this.settingsPanel) {
            this.settingsPanel.style.display = 'block';
        }
    }
    
    hideAccessibilitySettings() {
        if (this.settingsPanel) {
            this.settingsPanel.style.display = 'none';
        }
    }
    
    // ===== PUBLIC API =====
    enableScreenReaderMode() {
        this.accessibilitySettings.screenReaderMode = true;
        this.announceToScreenReader('Screen reader mode enabled');
    }
    
    enableVoiceControlMode() {
        this.announceToScreenReader('Voice control mode enabled');
    }
    
    disableVoiceControlMode() {
        this.announceToScreenReader('Voice control mode disabled');
    }
    
    enableSwitchNavigationMode() {
        this.announceToScreenReader('Switch navigation mode enabled');
    }
    
    enableTouchAccessibility() {
        this.announceToScreenReader('Touch accessibility enabled');
    }
    
    showAccessibilityHelp() {
        const helpContent = `
            <div class="accessibility-help">
                <h3>Accessibility Help</h3>
                <p>Here are some ways to use this app:</p>
                <ul>
                    <li>Use Tab key to navigate between elements</li>
                    <li>Use Enter or Space to activate buttons</li>
                    <li>Use arrow keys for navigation</li>
                    <li>Say "help" for voice commands</li>
                    <li>Use Ctrl+Space to toggle scanning mode</li>
                </ul>
                <button class="btn btn-primary" onclick="this.parentElement.remove()">Got it</button>
            </div>
        `;
        
        const helpElement = document.createElement('div');
        helpElement.innerHTML = helpContent;
        helpElement.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: var(--surface-color);
            padding: 2rem;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-heavy);
            z-index: 10000;
            max-width: 400px;
        `;
        
        document.body.appendChild(helpElement);
    }
    
    closeAllOverlays() {
        // Close all open overlays
        const overlays = document.querySelectorAll('.modal, .bottom-sheet, .accessibility-settings-panel');
        overlays.forEach(overlay => {
            overlay.style.display = 'none';
        });
    }
}

// Initialize touch accessibility manager
document.addEventListener('DOMContentLoaded', () => {
    window.touchAccessibility = new TouchAccessibilityManager();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TouchAccessibilityManager;
}
