/**
 * MINGUS Application
 * Main application entry point and lifecycle management
 */

class MINGUSApp {
    constructor() {
        this.isInitialized = false;
        this.isReady = false;
        this.services = new Map();
        this.eventListeners = new Map();
        this.config = {};
        
        // Initialize
        this.init();
    }
    
    // ===== INITIALIZATION =====
    async init() {
        try {
            MINGUS.utils.logInfo('Initializing MINGUS application...');
            
            // Load configuration
            await this.loadConfiguration();
            
            // Initialize core services
            await this.initializeServices();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize UI
            await this.initializeUI();
            
            // Mark as initialized
            this.isInitialized = true;
            
            // Trigger ready event
            this.triggerReady();
            
            MINGUS.utils.logInfo('MINGUS application initialized successfully');
            
        } catch (error) {
            MINGUS.utils.logError('Failed to initialize MINGUS application', error);
            this.handleInitializationError(error);
        }
    }
    
    async loadConfiguration() {
        try {
            // Load environment-specific configuration
            const env = this.getEnvironment();
            this.config = {
                ...config, // Global config from config.js
                environment: env,
                debug: env === 'development',
                apiUrl: this.getApiUrl(env),
                wsUrl: this.getWebSocketUrl(env)
            };
            
            MINGUS.utils.logInfo('Configuration loaded', { environment: env });
            
        } catch (error) {
            MINGUS.utils.logError('Failed to load configuration', error);
            throw error;
        }
    }
    
    async initializeServices() {
        const services = [
            { name: 'utils', instance: MINGUS.utils },
            { name: 'api', instance: MINGUS.api },
            { name: 'auth', instance: MINGUS.auth },
            { name: 'router', instance: MINGUS.router },
            { name: 'components', instance: MINGUS.components }
        ];
        
        for (const service of services) {
            try {
                if (service.instance && typeof service.instance.init === 'function') {
                    await service.instance.init();
                }
                this.services.set(service.name, service.instance);
                MINGUS.utils.logDebug(`Service initialized: ${service.name}`);
            } catch (error) {
                MINGUS.utils.logError(`Failed to initialize service: ${service.name}`, error);
                throw error;
            }
        }
    }
    
    setupEventListeners() {
        // Application lifecycle events
        this.on('app:ready', this.handleAppReady.bind(this));
        this.on('app:error', this.handleAppError.bind(this));
        
        // Navigation events
        this.on('route:changed', this.handleRouteChanged.bind(this));
        this.on('route:error', this.handleRouteError.bind(this));
        
        // Authentication events
        this.on('auth:login', this.handleAuthLogin.bind(this));
        this.on('auth:logout', this.handleAuthLogout.bind(this));
        this.on('auth:error', this.handleAuthError.bind(this));
        
        // API events
        this.on('api:error', this.handleApiError.bind(this));
        this.on('api:offline', this.handleApiOffline.bind(this));
        this.on('api:online', this.handleApiOnline.bind(this));
        
        // UI events
        this.on('ui:notification', this.handleNotification.bind(this));
        this.on('ui:modal', this.handleModal.bind(this));
        
        // Performance events
        this.on('performance:slow', this.handlePerformanceIssue.bind(this));
        
        // Error events
        this.on('error:unhandled', this.handleUnhandledError.bind(this));
    }
    
    async initializeUI() {
        try {
            // Initialize mobile menu
            this.initializeMobileMenu();
            
            // Initialize navigation
            this.initializeNavigation();
            
            // Initialize error boundary
            this.initializeErrorBoundary();
            
            // Initialize accessibility features
            this.initializeAccessibility();
            
            // Initialize performance monitoring
            this.initializePerformanceMonitoring();
            
            MINGUS.utils.logInfo('UI initialized successfully');
            
        } catch (error) {
            MINGUS.utils.logError('Failed to initialize UI', error);
            throw error;
        }
    }
    
    // ===== UI INITIALIZATION =====
    initializeMobileMenu() {
        const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
        const navLinks = document.querySelector('.nav-links');
        
        if (mobileMenuBtn && navLinks) {
            MINGUS.utils.DOM.on(mobileMenuBtn, 'click', () => {
                MINGUS.utils.DOM.toggleClass(navLinks, 'active');
                const isExpanded = MINGUS.utils.DOM.hasClass(navLinks, 'active');
                mobileMenuBtn.setAttribute('aria-expanded', isExpanded);
            });
        }
    }
    
    initializeNavigation() {
        // Handle navigation link clicks
        const navLinks = document.querySelectorAll('.nav-links a');
        navLinks.forEach(link => {
            MINGUS.utils.DOM.on(link, 'click', (event) => {
                const href = link.getAttribute('href');
                if (href && href.startsWith('#')) {
                    event.preventDefault();
                    const targetId = href.slice(1);
                    const targetElement = document.getElementById(targetId);
                    if (targetElement) {
                        MINGUS.utils.Animation.scrollTo(targetElement, 80);
                    }
                }
            });
        });
    }
    
    initializeErrorBoundary() {
        const errorBoundary = document.getElementById('error-boundary');
        if (errorBoundary) {
            // Hide error boundary initially
            errorBoundary.style.display = 'none';
        }
    }
    
    initializeAccessibility() {
        // Add skip link functionality
        const skipLink = document.querySelector('.skip-link');
        if (skipLink) {
            MINGUS.utils.DOM.on(skipLink, 'click', (event) => {
                event.preventDefault();
                const targetId = skipLink.getAttribute('href').slice(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    targetElement.focus();
                }
            });
        }
        
        // Add focus management for modals
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Tab') {
                this.handleTabNavigation(event);
            }
        });
    }
    
    initializePerformanceMonitoring() {
        // Monitor Core Web Vitals
        if ('PerformanceObserver' in window) {
            try {
                // Monitor Largest Contentful Paint (LCP)
                const lcpObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    if (lastEntry) {
                        this.trackPerformanceMetric('LCP', lastEntry.startTime);
                    }
                });
                lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
                
                // Monitor First Input Delay (FID)
                const fidObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach(entry => {
                        this.trackPerformanceMetric('FID', entry.processingStart - entry.startTime);
                    });
                });
                fidObserver.observe({ entryTypes: ['first-input'] });
                
                // Monitor Cumulative Layout Shift (CLS)
                const clsObserver = new PerformanceObserver((list) => {
                    let clsValue = 0;
                    const entries = list.getEntries();
                    entries.forEach(entry => {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                        }
                    });
                    this.trackPerformanceMetric('CLS', clsValue);
                });
                clsObserver.observe({ entryTypes: ['layout-shift'] });
                
            } catch (error) {
                MINGUS.utils.logError('Performance monitoring setup failed', error);
            }
        }
    }
    
    // ===== EVENT HANDLING =====
    handleAppReady() {
        this.isReady = true;
        MINGUS.utils.logInfo('Application ready');
        
        // Remove loading state
        const loadingElement = document.querySelector('.loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
        
        // Trigger custom event
        window.dispatchEvent(new CustomEvent('mingus:ready'));
    }
    
    handleAppError(error) {
        MINGUS.utils.logError('Application error', error);
        this.showErrorBoundary();
    }
    
    handleRouteChanged(data) {
        MINGUS.utils.logInfo('Route changed', data);
        
        // Update analytics
        if (window.analytics && window.analytics.track) {
            window.analytics.track('page_view', {
                path: data.path,
                title: data.title
            });
        }
    }
    
    handleRouteError(error) {
        MINGUS.utils.logError('Route error', error);
        this.showNotification('Failed to load page. Please try again.', 'error');
    }
    
    handleAuthLogin(user) {
        MINGUS.utils.logInfo('User logged in', { user: user.email });
        
        // Update UI
        this.updateUIForUser(user);
        
        // Track analytics
        if (window.analytics && window.analytics.track) {
            window.analytics.track('user_login', {
                user_id: user.id,
                email: user.email
            });
        }
    }
    
    handleAuthLogout() {
        MINGUS.utils.logInfo('User logged out');
        
        // Update UI
        this.updateUIForGuest();
        
        // Track analytics
        if (window.analytics && window.analytics.track) {
            window.analytics.track('user_logout');
        }
    }
    
    handleAuthError(error) {
        MINGUS.utils.logError('Authentication error', error);
        this.showNotification('Authentication failed. Please try again.', 'error');
    }
    
    handleApiError(error) {
        MINGUS.utils.logError('API error', error);
        
        // Show appropriate error message
        let message = 'A network error occurred. Please try again.';
        if (error.code === 'UNAUTHORIZED') {
            message = 'Your session has expired. Please log in again.';
        } else if (error.code === 'FORBIDDEN') {
            message = 'You do not have permission to perform this action.';
        } else if (error.code === 'NOT_FOUND') {
            message = 'The requested resource was not found.';
        }
        
        this.showNotification(message, 'error');
    }
    
    handleApiOffline() {
        MINGUS.utils.logWarn('API is offline');
        this.showNotification('You are currently offline. Some features may be unavailable.', 'warning');
    }
    
    handleApiOnline() {
        MINGUS.utils.logInfo('API is online');
        this.showNotification('Connection restored.', 'success');
    }
    
    handleNotification(data) {
        MINGUS.components.showNotification(data);
    }
    
    handleModal(data) {
        if (data.action === 'show') {
            MINGUS.components.showModal(data.config);
        } else if (data.action === 'hide') {
            MINGUS.components.hideModal(data.id);
        }
    }
    
    handlePerformanceIssue(metric) {
        MINGUS.utils.logWarn('Performance issue detected', metric);
        
        // Send to analytics
        if (window.analytics && window.analytics.track) {
            window.analytics.track('performance_issue', metric);
        }
    }
    
    handleUnhandledError(error) {
        MINGUS.utils.logError('Unhandled error', error);
        this.showErrorBoundary();
    }
    
    // ===== UI UPDATES =====
    updateUIForUser(user) {
        const usernameElement = document.getElementById('username');
        const loginBtn = document.getElementById('loginBtn');
        
        if (usernameElement) {
            usernameElement.textContent = user.firstName || user.email;
        }
        
        if (loginBtn) {
            loginBtn.textContent = 'Logout';
            loginBtn.onclick = () => MINGUS.auth.logout();
        }
    }
    
    updateUIForGuest() {
        const usernameElement = document.getElementById('username');
        const loginBtn = document.getElementById('loginBtn');
        
        if (usernameElement) {
            usernameElement.textContent = 'Guest';
        }
        
        if (loginBtn) {
            loginBtn.textContent = 'Login';
            loginBtn.onclick = () => MINGUS.components.showLoginModal();
        }
    }
    
    showErrorBoundary() {
        const errorBoundary = document.getElementById('error-boundary');
        if (errorBoundary) {
            errorBoundary.style.display = 'flex';
        }
    }
    
    showNotification(message, type = 'info') {
        MINGUS.components.showNotification({ message, type });
    }
    
    // ===== ACCESSIBILITY HELPERS =====
    handleTabNavigation(event) {
        const activeModal = document.querySelector('.modal-container.active');
        if (activeModal) {
            const focusableElements = activeModal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length === 0) return;
            
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
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
    }
    
    // ===== PERFORMANCE MONITORING =====
    trackPerformanceMetric(name, value) {
        const thresholds = {
            LCP: { good: 2500, poor: 4000 },
            FID: { good: 100, poor: 300 },
            CLS: { good: 0.1, poor: 0.25 }
        };
        
        const threshold = thresholds[name];
        if (threshold) {
            let rating = 'good';
            if (value > threshold.poor) {
                rating = 'poor';
            } else if (value > threshold.good) {
                rating = 'needs-improvement';
            }
            
            // Track to analytics
            if (window.analytics && window.analytics.track) {
                window.analytics.track('performance_metric', {
                    name,
                    value,
                    rating
                });
            }
            
            // Log poor performance
            if (rating === 'poor') {
                this.emit('performance:slow', { name, value, rating });
            }
        }
    }
    
    // ===== UTILITY METHODS =====
    getEnvironment() {
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'development';
        } else if (hostname.includes('staging') || hostname.includes('test')) {
            return 'staging';
        } else {
            return 'production';
        }
    }
    
    getApiUrl(environment) {
        switch (environment) {
            case 'development':
                return 'http://localhost:5000/api';
            case 'staging':
                return 'https://api-staging.mingus.com';
            case 'production':
                return 'https://api.mingus.com';
            default:
                return config.API_BASE_URL;
        }
    }
    
    getWebSocketUrl(environment) {
        switch (environment) {
            case 'development':
                return 'ws://localhost:5000/ws';
            case 'staging':
                return 'wss://ws-staging.mingus.com';
            case 'production':
                return 'wss://ws.mingus.com';
            default:
                return null;
        }
    }
    
    // ===== EVENT SYSTEM =====
    on(event, handler) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(handler);
    }
    
    off(event, handler) {
        if (this.eventListeners.has(event)) {
            const handlers = this.eventListeners.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    MINGUS.utils.logError(`Error in event handler for ${event}`, error);
                }
            });
        }
    }
    
    // ===== SERVICE ACCESS =====
    getService(name) {
        return this.services.get(name);
    }
    
    // ===== PUBLIC API =====
    isAppReady() {
        return this.isReady;
    }
    
    isAppInitialized() {
        return this.isInitialized;
    }
    
    getConfig() {
        return { ...this.config };
    }
    
    triggerReady() {
        this.emit('app:ready');
    }
    
    // ===== ERROR HANDLING =====
    handleInitializationError(error) {
        MINGUS.utils.logError('Initialization failed', error);
        
        // Show error boundary
        this.showErrorBoundary();
        
        // Emit error event
        this.emit('app:error', error);
    }
}

// ===== GLOBAL ERROR HANDLING =====
window.addEventListener('error', (event) => {
    if (window.MINGUS && window.MINGUS.app) {
        window.MINGUS.app.emit('error:unhandled', event.error);
    }
});

window.addEventListener('unhandledrejection', (event) => {
    if (window.MINGUS && window.MINGUS.app) {
        window.MINGUS.app.emit('error:unhandled', event.reason);
    }
});

// ===== APPLICATION STARTUP =====
document.addEventListener('DOMContentLoaded', () => {
    // Initialize application
    const app = new MINGUSApp();
    
    // Make available globally
    window.MINGUS = window.MINGUS || {};
    window.MINGUS.app = app;
    
    // Export for module systems
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = MINGUSApp;
    }
});

// ===== DEVELOPMENT HELPERS =====
if (typeof window !== 'undefined') {
    // Expose app for debugging in development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        window.MINGUS_DEBUG = {
            app: null,
            utils: null,
            api: null,
            auth: null,
            router: null,
            components: null
        };
        
        // Update debug object when app is ready
        const updateDebug = () => {
            if (window.MINGUS) {
                window.MINGUS_DEBUG.app = window.MINGUS.app;
                window.MINGUS_DEBUG.utils = window.MINGUS.utils;
                window.MINGUS_DEBUG.api = window.MINGUS.api;
                window.MINGUS_DEBUG.auth = window.MINGUS.auth;
                window.MINGUS_DEBUG.router = window.MINGUS.router;
                window.MINGUS_DEBUG.components = window.MINGUS.components;
            }
        };
        
        // Check periodically for app initialization
        const debugInterval = setInterval(() => {
            if (window.MINGUS && window.MINGUS.app) {
                updateDebug();
                clearInterval(debugInterval);
            }
        }, 100);
    }
}
