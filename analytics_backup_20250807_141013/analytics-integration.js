/**
 * MINGUS Analytics Integration
 * Connects analytics tracking to application components and user interactions
 */

class AnalyticsIntegration {
    constructor() {
        this.analytics = window.MINGUS.analytics;
        this.config = window.MINGUS.getAnalyticsConfig();
        this.trackedElements = new Set();
        this.modalTracking = new Map();
        
        this.init();
    }
    
    init() {
        if (!this.analytics || !this.analytics.isEnabled()) {
            console.warn('Analytics not available for integration');
            return;
        }
        
        this.setupEventListeners();
        this.setupModalTracking();
        this.setupFormTracking();
        this.setupCTATracking();
        this.setupAssessmentTracking();
        this.setupNavigationTracking();
        this.setupErrorTracking();
        
        console.log('Analytics integration initialized');
    }
    
    // ===== EVENT LISTENER SETUP =====
    
    setupEventListeners() {
        // Track page views
        this.trackPageView();
        
        // Track navigation changes
        this.setupNavigationTracking();
        
        // Track user interactions
        this.setupUserInteractionTracking();
        
        // Track form interactions
        this.setupFormInteractionTracking();
    }
    
    setupNavigationTracking() {
        // Track initial page view
        this.analytics.trackPageView();
        
        // Track navigation changes (for SPA)
        let currentPath = window.location.pathname;
        
        const trackNavigation = () => {
            const newPath = window.location.pathname;
            if (newPath !== currentPath) {
                this.analytics.track('page_view', {
                    page_path: newPath,
                    page_title: document.title,
                    navigation_type: 'spa_navigation'
                });
                currentPath = newPath;
            }
        };
        
        // Listen for popstate events (browser back/forward)
        window.addEventListener('popstate', trackNavigation);
        
        // Listen for pushstate/replacestate (programmatic navigation)
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;
        
        history.pushState = function(...args) {
            originalPushState.apply(history, args);
            setTimeout(trackNavigation, 0);
        };
        
        history.replaceState = function(...args) {
            originalReplaceState.apply(history, args);
            setTimeout(trackNavigation, 0);
        };
    }
    
    setupUserInteractionTracking() {
        // Track clicks on interactive elements
        document.addEventListener('click', (event) => {
            const target = event.target;
            
            // Track button clicks
            if (target.tagName === 'BUTTON' || target.closest('button')) {
                this.trackButtonClick(target);
            }
            
            // Track link clicks
            if (target.tagName === 'A' || target.closest('a')) {
                this.trackLinkClick(target);
            }
            
            // Track CTA clicks
            if (this.isCTAElement(target)) {
                this.trackCTAClick(target);
            }
        });
        
        // Track form interactions
        document.addEventListener('submit', (event) => {
            this.trackFormSubmission(event.target);
        });
        
        // Track input focus/blur for engagement
        document.addEventListener('focusin', (event) => {
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                this.trackFormInteraction('input_focus', event.target);
            }
        });
    }
    
    // ===== MODAL TRACKING =====
    
    setupModalTracking() {
        // Track modal opens/closes
        const modalObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        this.trackModalOpen(node);
                    }
                });
                
                mutation.removedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        this.trackModalClose(node);
                    }
                });
            });
        });
        
        modalObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Track modal interactions
        document.addEventListener('click', (event) => {
            const modal = event.target.closest('.modal, [data-modal], .dialog');
            if (modal) {
                this.trackModalInteraction(event.target, modal);
            }
        });
    }
    
    trackModalOpen(modalElement) {
        if (this.isModalElement(modalElement)) {
            const modalId = this.getModalId(modalElement);
            const modalType = this.getModalType(modalElement);
            
            this.analytics.trackModalInteraction('open', modalId, {
                modal_type: modalType,
                modal_title: this.getModalTitle(modalElement)
            });
            
            // Track specific modal types
            if (modalType === 'assessment_selection') {
                this.analytics.trackAssessmentModalOpened(modalId);
            }
        }
    }
    
    trackModalClose(modalElement) {
        if (this.isModalElement(modalElement)) {
            const modalId = this.getModalId(modalElement);
            const modalType = this.getModalType(modalElement);
            
            this.analytics.trackModalInteraction('close', modalId, {
                modal_type: modalType,
                close_method: 'user_action'
            });
        }
    }
    
    trackModalInteraction(element, modal) {
        const modalId = this.getModalId(modal);
        const modalType = this.getModalType(modal);
        const action = this.getModalAction(element);
        
        if (action) {
            this.analytics.trackModalInteraction(action, modalId, {
                modal_type: modalType,
                interaction_element: element.tagName,
                interaction_text: element.textContent?.trim()
            });
        }
    }
    
    // ===== FORM TRACKING =====
    
    setupFormTracking() {
        // Track form views
        const formObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting && this.isFormElement(entry.target)) {
                    this.trackFormView(entry.target);
                }
            });
        });
        
        // Observe all forms
        document.querySelectorAll('form').forEach(form => {
            formObserver.observe(form);
        });
        
        // Track form submissions
        document.addEventListener('submit', (event) => {
            this.trackFormSubmission(event.target);
        });
        
        // Track form field interactions
        document.addEventListener('input', (event) => {
            if (this.isFormField(event.target)) {
                this.trackFormFieldInteraction(event.target);
            }
        });
    }
    
    trackFormView(form) {
        const formId = this.getFormId(form);
        const formType = this.getFormType(form);
        
        this.analytics.track('form_view', {
            form_id: formId,
            form_type: formType,
            form_fields: this.getFormFieldCount(form)
        });
    }
    
    trackFormSubmission(form) {
        const formId = this.getFormId(form);
        const formType = this.getFormType(form);
        
        this.analytics.trackFormSubmission(formId, {
            form_type: formType,
            form_fields: this.getFormFieldCount(form),
            submission_method: 'web_form'
        });
        
        // Track as conversion if it's a lead form
        if (this.isLeadForm(formType)) {
            this.analytics.trackLeadGeneration('form_submission', {
                form_type: formType,
                form_id: formId
            });
        }
    }
    
    trackFormFieldInteraction(field) {
        const form = field.closest('form');
        if (form) {
            const formId = this.getFormId(form);
            const fieldType = field.type || 'text';
            const fieldName = field.name || field.id || 'unknown';
            
            this.analytics.track('form_field_interaction', {
                form_id: formId,
                field_type: fieldType,
                field_name: fieldName,
                interaction_type: 'input'
            });
        }
    }
    
    // ===== CTA TRACKING =====
    
    setupCTATracking() {
        // Track CTA button clicks
        document.addEventListener('click', (event) => {
            const target = event.target;
            
            if (this.isCTAElement(target)) {
                this.trackCTAClick(target);
            }
        });
    }
    
    trackCTAClick(element) {
        const buttonId = this.getButtonId(element);
        const buttonText = this.getButtonText(element);
        const buttonLocation = this.getButtonLocation(element);
        const ctaType = this.getCTAType(element);
        
        this.analytics.trackCTAClick(buttonId, buttonLocation, {
            button_text: buttonText,
            cta_type: ctaType,
            button_position: this.getButtonPosition(element)
        });
        
        // Track as conversion if it's a lead generation CTA
        if (this.isLeadGenerationCTA(ctaType)) {
            this.analytics.trackLeadGeneration('cta_click', {
                cta_type: ctaType,
                button_location: buttonLocation,
                button_text: buttonText
            });
        }
    }
    
    // ===== ASSESSMENT TRACKING =====
    
    setupAssessmentTracking() {
        // Track assessment selection
        document.addEventListener('click', (event) => {
            const target = event.target;
            
            if (this.isAssessmentElement(target)) {
                this.trackAssessmentSelection(target);
            }
        });
        
        // Track assessment progress
        this.setupAssessmentProgressTracking();
    }
    
    trackAssessmentSelection(element) {
        const assessmentType = this.getAssessmentType(element);
        const assessmentId = this.getAssessmentId(element);
        
        this.analytics.trackAssessmentSelection(assessmentType, {
            assessment_id: assessmentId,
            selection_method: 'click',
            element_type: element.tagName
        });
    }
    
    setupAssessmentProgressTracking() {
        // Track assessment steps
        const trackAssessmentStep = (step, data = {}) => {
            this.analytics.track('assessment_step', {
                step: step,
                ...data
            });
        };
        
        // Expose tracking function globally
        window.MINGUS = window.MINGUS || {};
        window.MINGUS.trackAssessmentStep = trackAssessmentStep;
        
        // Track assessment completion
        window.MINGUS.trackAssessmentCompletion = (type, data = {}) => {
            this.analytics.trackAssessmentCompletion(type, data);
        };
    }
    
    // ===== ERROR TRACKING =====
    
    setupErrorTracking() {
        // Track JavaScript errors
        window.addEventListener('error', (event) => {
            this.analytics.trackError('javascript_error', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error_stack: event.error?.stack
            });
        });
        
        // Track promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.analytics.trackError('promise_rejection', {
                reason: event.reason,
                promise: event.promise
            });
        });
        
        // Track network errors
        window.addEventListener('online', () => {
            this.analytics.track('network_status', { status: 'online' });
        });
        
        window.addEventListener('offline', () => {
            this.analytics.track('network_status', { status: 'offline' });
        });
    }
    
    // ===== UTILITY METHODS =====
    
    // Modal utilities
    isModalElement(element) {
        return element.classList.contains('modal') || 
               element.hasAttribute('data-modal') || 
               element.classList.contains('dialog') ||
               element.id?.includes('modal');
    }
    
    getModalId(modal) {
        return modal.id || modal.getAttribute('data-modal-id') || 'unknown_modal';
    }
    
    getModalType(modal) {
        if (modal.id?.includes('assessment')) return 'assessment_selection';
        if (modal.id?.includes('pricing')) return 'pricing';
        if (modal.id?.includes('contact')) return 'contact';
        if (modal.id?.includes('login')) return 'authentication';
        return 'general';
    }
    
    getModalTitle(modal) {
        const titleElement = modal.querySelector('.modal-title, .dialog-title, h1, h2, h3');
        return titleElement?.textContent?.trim() || 'Untitled Modal';
    }
    
    getModalAction(element) {
        if (element.classList.contains('close') || element.getAttribute('aria-label')?.includes('close')) {
            return 'close';
        }
        if (element.tagName === 'BUTTON' && element.textContent?.toLowerCase().includes('select')) {
            return 'select';
        }
        if (element.tagName === 'BUTTON' && element.textContent?.toLowerCase().includes('start')) {
            return 'start';
        }
        return null;
    }
    
    // Form utilities
    isFormElement(element) {
        return element.tagName === 'FORM';
    }
    
    isFormField(element) {
        return element.tagName === 'INPUT' || 
               element.tagName === 'TEXTAREA' || 
               element.tagName === 'SELECT';
    }
    
    getFormId(form) {
        return form.id || form.getAttribute('data-form-id') || 'unknown_form';
    }
    
    getFormType(form) {
        if (form.id?.includes('contact')) return 'contact_form';
        if (form.id?.includes('signup')) return 'signup_form';
        if (form.id?.includes('assessment')) return 'assessment_form';
        if (form.id?.includes('login')) return 'login_form';
        return 'general_form';
    }
    
    getFormFieldCount(form) {
        return form.querySelectorAll('input, textarea, select').length;
    }
    
    isLeadForm(formType) {
        return ['contact_form', 'signup_form', 'assessment_form'].includes(formType);
    }
    
    // Button utilities
    isCTAElement(element) {
        const button = element.tagName === 'BUTTON' ? element : element.closest('button');
        if (!button) return false;
        
        const text = button.textContent?.toLowerCase() || '';
        const classes = button.className?.toLowerCase() || '';
        const id = button.id?.toLowerCase() || '';
        
        return text.includes('start') || 
               text.includes('get') || 
               text.includes('begin') || 
               text.includes('sign up') || 
               text.includes('contact') ||
               classes.includes('cta') ||
               classes.includes('primary') ||
               id.includes('cta') ||
               id.includes('start') ||
               id.includes('signup');
    }
    
    getButtonId(element) {
        const button = element.tagName === 'BUTTON' ? element : element.closest('button');
        return button?.id || 'unknown_button';
    }
    
    getButtonText(element) {
        const button = element.tagName === 'BUTTON' ? element : element.closest('button');
        return button?.textContent?.trim() || 'Unknown';
    }
    
    getButtonLocation(element) {
        const button = element.tagName === 'BUTTON' ? element : element.closest('button');
        if (!button) return 'unknown';
        
        // Determine location based on context
        if (button.closest('.header, header')) return 'header';
        if (button.closest('.hero, .banner')) return 'hero';
        if (button.closest('.footer, footer')) return 'footer';
        if (button.closest('.sidebar')) return 'sidebar';
        if (button.closest('.modal, .dialog')) return 'modal';
        
        return 'content';
    }
    
    getButtonPosition(element) {
        const button = element.tagName === 'BUTTON' ? element : element.closest('button');
        if (!button) return 'unknown';
        
        const rect = button.getBoundingClientRect();
        return {
            x: Math.round(rect.left),
            y: Math.round(rect.top),
            width: Math.round(rect.width),
            height: Math.round(rect.height)
        };
    }
    
    getCTAType(element) {
        const text = element.textContent?.toLowerCase() || '';
        const id = element.id?.toLowerCase() || '';
        
        if (text.includes('start') || text.includes('begin') || id.includes('start')) {
            return 'primary_cta';
        }
        if (text.includes('learn') || text.includes('more') || id.includes('learn')) {
            return 'secondary_cta';
        }
        if (text.includes('contact') || id.includes('contact')) {
            return 'contact_cta';
        }
        if (text.includes('sign up') || text.includes('signup') || id.includes('signup')) {
            return 'signup_cta';
        }
        
        return 'general_cta';
    }
    
    isLeadGenerationCTA(ctaType) {
        return ['primary_cta', 'signup_cta'].includes(ctaType);
    }
    
    // Assessment utilities
    isAssessmentElement(element) {
        const assessmentElement = element.closest('[data-assessment], .assessment-option, .assessment-card');
        return assessmentElement !== null;
    }
    
    getAssessmentType(element) {
        const assessmentElement = element.closest('[data-assessment], .assessment-option, .assessment-card');
        if (!assessmentElement) return 'unknown';
        
        const dataType = assessmentElement.getAttribute('data-assessment');
        if (dataType) return dataType;
        
        const text = assessmentElement.textContent?.toLowerCase() || '';
        if (text.includes('income')) return 'income_comparison';
        if (text.includes('tax')) return 'tax_optimization';
        if (text.includes('career')) return 'career_advancement';
        if (text.includes('investment')) return 'investment_planning';
        
        return 'unknown';
    }
    
    getAssessmentId(element) {
        const assessmentElement = element.closest('[data-assessment], .assessment-option, .assessment-card');
        return assessmentElement?.id || 'unknown_assessment';
    }
    
    // Link utilities
    trackLinkClick(element) {
        const link = element.tagName === 'A' ? element : element.closest('a');
        if (!link) return;
        
        const href = link.href;
        const text = link.textContent?.trim();
        const isExternal = link.hostname !== window.location.hostname;
        
        this.analytics.track('link_click', {
            link_url: href,
            link_text: text,
            link_type: isExternal ? 'external' : 'internal',
            link_location: this.getButtonLocation(link)
        });
    }
    
    trackButtonClick(element) {
        const button = element.tagName === 'BUTTON' ? element : element.closest('button');
        if (!button) return;
        
        const buttonId = this.getButtonId(button);
        const buttonText = this.getButtonText(button);
        const buttonType = button.type || 'button';
        
        this.analytics.track('button_click', {
            button_id: buttonId,
            button_text: buttonText,
            button_type: buttonType,
            button_location: this.getButtonLocation(button)
        });
    }
    
    // Page view tracking
    trackPageView() {
        this.analytics.trackPageView();
    }
}

// Initialize analytics integration when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait for analytics to be available
    const initIntegration = () => {
        if (window.MINGUS && window.MINGUS.analytics) {
            window.MINGUS.analyticsIntegration = new AnalyticsIntegration();
        } else {
            setTimeout(initIntegration, 100);
        }
    };
    
    initIntegration();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsIntegration;
}
