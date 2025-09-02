/**
 * MINGUS Touch Interaction System
 * Comprehensive touch feedback and interaction management for mobile financial app
 */

class TouchInteractionManager {
    constructor() {
        this.isHapticSupported = this.checkHapticSupport();
        this.touchElements = new Set();
        this.loadingStates = new Map();
        this.touchFeedbackQueue = [];
        this.isProcessingFeedback = false;
        
        this.init();
    }
    
    init() {
        this.setupTouchFeedback();
        this.setupHapticFeedback();
        this.setupLoadingStates();
        this.setupTouchRegistration();
        this.setupPerformanceOptimization();
    }
    
    // ===== HAPTIC FEEDBACK SUPPORT =====
    checkHapticSupport() {
        return 'vibrate' in navigator || 
               'navigator' in window && 'vibrate' in navigator ||
               'webkitVibrate' in navigator;
    }
    
    setupHapticFeedback() {
        if (!this.isHapticSupported) return;
        
        // Haptic feedback patterns for different interactions
        this.hapticPatterns = {
            light: [10],
            medium: [20],
            heavy: [30],
            success: [20, 50, 20],
            error: [100, 50, 100],
            warning: [50, 100, 50],
            navigation: [15, 30, 15],
            selection: [25],
            confirmation: [30, 60, 30]
        };
    }
    
    triggerHapticFeedback(pattern = 'light') {
        if (!this.isHapticSupported) return;
        
        const vibrationPattern = this.hapticPatterns[pattern] || this.hapticPatterns.light;
        
        try {
            if (navigator.vibrate) {
                navigator.vibrate(vibrationPattern);
            } else if (navigator.webkitVibrate) {
                navigator.webkitVibrate(vibrationPattern);
            }
        } catch (error) {
            console.warn('Haptic feedback failed:', error);
        }
    }
    
    // ===== VISUAL TOUCH FEEDBACK =====
    setupTouchFeedback() {
        // Enhanced touch feedback for all interactive elements
        this.setupButtonTouchFeedback();
        this.setupFormTouchFeedback();
        this.setupNavigationTouchFeedback();
        this.setupFinancialDataTouchFeedback();
    }
    
    setupButtonTouchFeedback() {
        const buttons = document.querySelectorAll('.btn, button, [role="button"], .interactive');
        
        buttons.forEach(button => {
            this.addTouchFeedback(button, {
                scale: 0.95,
                shadow: 'var(--shadow-heavy)',
                backgroundColor: 'var(--primary-light)',
                hapticPattern: 'selection'
            });
        });
    }
    
    setupFormTouchFeedback() {
        const formElements = document.querySelectorAll('input, select, textarea, .form-control');
        
        formElements.forEach(element => {
            this.addTouchFeedback(element, {
                scale: 1.02,
                borderColor: 'var(--primary-color)',
                backgroundColor: 'var(--background-color)',
                hapticPattern: 'light'
            });
        });
    }
    
    setupNavigationTouchFeedback() {
        const navElements = document.querySelectorAll('.nav-links a, .mobile-menu-btn, .breadcrumb a');
        
        navElements.forEach(element => {
            this.addTouchFeedback(element, {
                scale: 0.98,
                backgroundColor: 'var(--primary-color)',
                color: 'white',
                hapticPattern: 'navigation'
            });
        });
    }
    
    setupFinancialDataTouchFeedback() {
        const financialElements = document.querySelectorAll('.chart-container, .data-card, .metric-item');
        
        financialElements.forEach(element => {
            this.addTouchFeedback(element, {
                scale: 1.05,
                shadow: 'var(--shadow-heavy)',
                borderColor: 'var(--accent-color)',
                hapticPattern: 'selection'
            });
        });
    }
    
    addTouchFeedback(element, options = {}) {
        if (!element || this.touchElements.has(element)) return;
        
        this.touchElements.add(element);
        
        const defaultOptions = {
            scale: 0.95,
            shadow: 'var(--shadow-medium)',
            backgroundColor: 'var(--primary-color)',
            color: 'white',
            borderColor: 'var(--primary-color)',
            hapticPattern: 'light',
            duration: 150
        };
        
        const config = { ...defaultOptions, ...options };
        
        // Touch start feedback
        element.addEventListener('touchstart', (e) => {
            this.handleTouchStart(element, config, e);
        }, { passive: true });
        
        // Touch end feedback
        element.addEventListener('touchend', (e) => {
            this.handleTouchEnd(element, config, e);
        }, { passive: true });
        
        // Touch cancel feedback
        element.addEventListener('touchcancel', (e) => {
            this.handleTouchCancel(element, config, e);
        }, { passive: true });
        
        // Mouse feedback for desktop testing
        element.addEventListener('mousedown', (e) => {
            this.handleMouseDown(element, config, e);
        });
        
        element.addEventListener('mouseup', (e) => {
            this.handleMouseUp(element, config, e);
        });
        
        element.addEventListener('mouseleave', (e) => {
            this.handleMouseLeave(element, config, e);
        });
    }
    
    handleTouchStart(element, config, event) {
        // Prevent default to avoid double-tap zoom on iOS
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'SELECT') {
            return;
        }
        
        this.applyTouchFeedback(element, config, true);
        this.triggerHapticFeedback(config.hapticPattern);
        
        // Add touch ripple effect
        this.createTouchRipple(element, event);
    }
    
    handleTouchEnd(element, config, event) {
        this.applyTouchFeedback(element, config, false);
        
        // Add success feedback for form submissions
        if (element.type === 'submit' || element.closest('form')) {
            this.triggerHapticFeedback('success');
        }
    }
    
    handleTouchCancel(element, config, event) {
        this.applyTouchFeedback(element, config, false);
    }
    
    handleMouseDown(element, config, event) {
        this.applyTouchFeedback(element, config, true);
    }
    
    handleMouseUp(element, config, event) {
        this.applyTouchFeedback(element, config, false);
    }
    
    handleMouseLeave(element, config, event) {
        this.applyTouchFeedback(element, config, false);
    }
    
    applyTouchFeedback(element, config, isActive) {
        const duration = config.duration || 150;
        
        if (isActive) {
            element.style.transform = `scale(${config.scale})`;
            element.style.boxShadow = config.shadow;
            element.style.transition = `all ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            
            if (config.backgroundColor) {
                element.style.backgroundColor = config.backgroundColor;
            }
            if (config.color) {
                element.style.color = config.color;
            }
            if (config.borderColor) {
                element.style.borderColor = config.borderColor;
            }
        } else {
            element.style.transform = '';
            element.style.boxShadow = '';
            element.style.backgroundColor = '';
            element.style.color = '';
            element.style.borderColor = '';
        }
    }
    
    createTouchRipple(element, event) {
        const ripple = document.createElement('div');
        ripple.className = 'touch-ripple';
        
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.touches[0].clientX - rect.left - size / 2;
        const y = event.touches[0].clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple-animation 0.6s linear;
            pointer-events: none;
            z-index: 1000;
        `;
        
        element.style.position = 'relative';
        element.appendChild(ripple);
        
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }
    
    // ===== LOADING STATES =====
    setupLoadingStates() {
        // Global loading state management
        this.createLoadingOverlay();
        this.setupFormLoadingStates();
        this.setupFinancialCalculationLoading();
    }
    
    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'global-loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <p class="loading-text">Processing...</p>
            </div>
        `;
        
        document.body.appendChild(overlay);
    }
    
    setupFormLoadingStates() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                this.showFormLoading(form);
            });
        });
    }
    
    setupFinancialCalculationLoading() {
        // Monitor financial calculation triggers
        document.addEventListener('financial-calculation-start', () => {
            this.showFinancialLoading();
        });
        
        document.addEventListener('financial-calculation-complete', () => {
            this.hideFinancialLoading();
        });
    }
    
    showFormLoading(form) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.innerHTML = `
                <span class="loading-spinner-small"></span>
                Processing...
            `;
            
            this.loadingStates.set(form, {
                button: submitButton,
                originalText: originalText
            });
        }
    }
    
    hideFormLoading(form) {
        const state = this.loadingStates.get(form);
        if (state) {
            state.button.disabled = false;
            state.button.textContent = state.originalText;
            this.loadingStates.delete(form);
        }
    }
    
    showFinancialLoading() {
        const overlay = document.getElementById('global-loading-overlay');
        if (overlay) {
            overlay.classList.add('active');
            overlay.querySelector('.loading-text').textContent = 'Calculating financial data...';
        }
    }
    
    hideFinancialLoading() {
        const overlay = document.getElementById('global-loading-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }
    
    // ===== TOUCH REGISTRATION INDICATORS =====
    setupTouchRegistration() {
        this.createTouchIndicators();
        this.setupTouchFeedbackQueue();
    }
    
    createTouchIndicators() {
        // Create visual indicators for touch registration
        const style = document.createElement('style');
        style.textContent = `
            .touch-indicator {
                position: fixed;
                width: 20px;
                height: 20px;
                background: var(--primary-color);
                border-radius: 50%;
                pointer-events: none;
                z-index: 10000;
                opacity: 0.8;
                transform: translate(-50%, -50%);
                animation: touch-indicator-fade 0.3s ease-out;
            }
            
            @keyframes touch-indicator-fade {
                0% { opacity: 0.8; transform: translate(-50%, -50%) scale(0.5); }
                100% { opacity: 0; transform: translate(-50%, -50%) scale(1.5); }
            }
            
            .touch-ripple {
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.3);
                transform: scale(0);
                animation: ripple-animation 0.6s linear;
                pointer-events: none;
            }
            
            @keyframes ripple-animation {
                to {
                    transform: scale(2);
                    opacity: 0;
                }
            }
            
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 10000;
                backdrop-filter: blur(5px);
            }
            
            .loading-overlay.active {
                display: flex;
            }
            
            .loading-content {
                background: var(--surface-color);
                padding: 2rem;
                border-radius: var(--border-radius-lg);
                text-align: center;
                box-shadow: var(--shadow-heavy);
            }
            
            .loading-spinner {
                width: 50px;
                height: 50px;
                border: 4px solid var(--border-color);
                border-top: 4px solid var(--primary-color);
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem;
            }
            
            .loading-spinner-small {
                display: inline-block;
                width: 16px;
                height: 16px;
                border: 2px solid transparent;
                border-top: 2px solid currentColor;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 0.5rem;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    setupTouchFeedbackQueue() {
        // Queue touch feedback to prevent overwhelming the UI
        this.processTouchFeedbackQueue();
    }
    
    processTouchFeedbackQueue() {
        if (this.touchFeedbackQueue.length === 0 || this.isProcessingFeedback) {
            return;
        }
        
        this.isProcessingFeedback = true;
        
        const feedback = this.touchFeedbackQueue.shift();
        this.executeTouchFeedback(feedback);
        
        setTimeout(() => {
            this.isProcessingFeedback = false;
            this.processTouchFeedbackQueue();
        }, 50);
    }
    
    executeTouchFeedback(feedback) {
        // Execute queued touch feedback
        if (feedback && feedback.element && feedback.config) {
            this.applyTouchFeedback(feedback.element, feedback.config, feedback.isActive);
        }
    }
    
    // ===== PERFORMANCE OPTIMIZATION =====
    setupPerformanceOptimization() {
        // Optimize touch performance on mobile devices
        this.optimizeTouchPerformance();
        this.setupTouchThrottling();
    }
    
    optimizeTouchPerformance() {
        // Use passive event listeners for better scroll performance
        const touchElements = document.querySelectorAll('[data-touch-optimized]');
        
        touchElements.forEach(element => {
            element.addEventListener('touchstart', () => {}, { passive: true });
            element.addEventListener('touchmove', () => {}, { passive: true });
            element.addEventListener('touchend', () => {}, { passive: true });
        });
    }
    
    setupTouchThrottling() {
        // Throttle touch events for better performance
        let touchTimeout;
        
        document.addEventListener('touchstart', () => {
            clearTimeout(touchTimeout);
            touchTimeout = setTimeout(() => {
                this.processTouchFeedbackQueue();
            }, 16); // ~60fps
        }, { passive: true });
    }
    
    // ===== PUBLIC API =====
    addElement(element, options = {}) {
        this.addTouchFeedback(element, options);
    }
    
    removeElement(element) {
        if (this.touchElements.has(element)) {
            this.touchElements.delete(element);
        }
    }
    
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('global-loading-overlay');
        if (overlay) {
            overlay.querySelector('.loading-text').textContent = message;
            overlay.classList.add('active');
        }
    }
    
    hideLoading() {
        const overlay = document.getElementById('global-loading-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }
    
    triggerHaptic(pattern) {
        this.triggerHapticFeedback(pattern);
    }
}

// Initialize touch interaction manager
document.addEventListener('DOMContentLoaded', () => {
    window.touchManager = new TouchInteractionManager();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TouchInteractionManager;
}
