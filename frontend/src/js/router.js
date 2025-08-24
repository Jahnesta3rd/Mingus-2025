/**
 * MINGUS Router Service
 * Client-side routing with navigation guards, history management, and dynamic loading
 */

class Router {
    constructor() {
        this.routes = new Map();
        this.currentRoute = null;
        this.history = [];
        this.maxHistoryLength = 50;
        this.loadingStates = new Map();
        this.navigationGuards = [];
        
        // Initialize
        this.init();
    }
    
    // ===== INITIALIZATION =====
    init() {
        // Setup event listeners
        this.setupEventListeners();
        
        // Register default routes
        this.registerDefaultRoutes();
        
        // Handle initial route
        this.handleInitialRoute();
    }
    
    setupEventListeners() {
        // Handle browser back/forward
        window.addEventListener('popstate', (event) => {
            this.handlePopState(event);
        });
        
        // Handle link clicks
        document.addEventListener('click', (event) => {
            this.handleLinkClick(event);
        });
        
        // Handle form submissions
        document.addEventListener('submit', (event) => {
            this.handleFormSubmit(event);
        });
    }
    
    registerDefaultRoutes() {
        // Public routes
        this.register('/', {
            component: 'Dashboard',
            title: 'Dashboard',
            public: true
        });
        
        this.register('/login', {
            component: 'Login',
            title: 'Login',
            public: true
        });
        
        this.register('/register', {
            component: 'Register',
            title: 'Register',
            public: true
        });
        
        this.register('/forgot-password', {
            component: 'ForgotPassword',
            title: 'Forgot Password',
            public: true
        });
        
        // Protected routes
        this.register('/dashboard', {
            component: 'Dashboard',
            title: 'Dashboard',
            requiresAuth: true
        });
        
        this.register('/assessments', {
            component: 'Assessments',
            title: 'Assessments',
            requiresAuth: true
        });
        
        this.register('/assessments/:id', {
            component: 'AssessmentDetail',
            title: 'Assessment',
            requiresAuth: true
        });
        
        this.register('/analytics', {
            component: 'Analytics',
            title: 'Analytics',
            requiresAuth: true
        });
        
        this.register('/profile', {
            component: 'Profile',
            title: 'Profile',
            requiresAuth: true
        });
        
        this.register('/settings', {
            component: 'Settings',
            title: 'Settings',
            requiresAuth: true
        });
        
        // Error routes
        this.register('/404', {
            component: 'NotFound',
            title: 'Page Not Found',
            public: true
        });
        
        this.register('/500', {
            component: 'ServerError',
            title: 'Server Error',
            public: true
        });
    }
    
    handleInitialRoute() {
        const path = window.location.pathname;
        this.navigate(path, { replace: true, silent: true });
    }
    
    // ===== ROUTE REGISTRATION =====
    register(path, config) {
        const route = {
            path,
            pattern: this.createRoutePattern(path),
            params: this.extractRouteParams(path),
            ...config
        };
        
        this.routes.set(path, route);
        MINGUS.utils.logDebug('Route registered', { path, config });
    }
    
    createRoutePattern(path) {
        return new RegExp('^' + path.replace(/:[^/]+/g, '([^/]+)') + '$');
    }
    
    extractRouteParams(path) {
        const params = [];
        const matches = path.match(/:[^/]+/g);
        
        if (matches) {
            matches.forEach(match => {
                params.push(match.slice(1));
            });
        }
        
        return params;
    }
    
    // ===== NAVIGATION =====
    async navigate(path, options = {}) {
        try {
            const { replace = false, silent = false, data = {} } = options;
            
            // Find matching route
            const route = this.findRoute(path);
            
            if (!route) {
                MINGUS.utils.logWarn('Route not found', { path });
                return this.navigate('/404', { replace });
            }
            
            // Run navigation guards
            const guardResult = await this.runNavigationGuards(route, data);
            if (guardResult === false) {
                MINGUS.utils.logInfo('Navigation blocked by guard');
                return;
            }
            
            // Update browser history
            if (!silent) {
                if (replace) {
                    window.history.replaceState(data, route.title, path);
                } else {
                    window.history.pushState(data, route.title, path);
                }
            }
            
            // Update current route
            this.currentRoute = route;
            
            // Add to history
            this.addToHistory(path, route);
            
            // Update page title
            this.updatePageTitle(route.title);
            
            // Load and render component
            await this.loadAndRenderComponent(route, path, data);
            
            // Update navigation state
            this.updateNavigationState(path);
            
            // Track analytics
            this.trackPageView(path, route);
            
            MINGUS.utils.logInfo('Navigation completed', { path, route: route.component });
            
        } catch (error) {
            MINGUS.utils.logError('Navigation failed', error);
            this.handleNavigationError(error);
        }
    }
    
    findRoute(path) {
        // First try exact match
        if (this.routes.has(path)) {
            return this.routes.get(path);
        }
        
        // Then try pattern matching
        for (const [routePath, route] of this.routes) {
            if (route.pattern && route.pattern.test(path)) {
                return route;
            }
        }
        
        return null;
    }
    
    // ===== NAVIGATION GUARDS =====
    addNavigationGuard(guard) {
        this.navigationGuards.push(guard);
    }
    
    async runNavigationGuards(route, data) {
        for (const guard of this.navigationGuards) {
            try {
                const result = await guard(route, data);
                if (result === false) {
                    return false;
                }
            } catch (error) {
                MINGUS.utils.logError('Navigation guard error', error);
                return false;
            }
        }
        return true;
    }
    
    // ===== COMPONENT LOADING =====
    async loadAndRenderComponent(route, path, data) {
        try {
            // Show loading state
            this.showLoadingState();
            
            // Extract route parameters
            const params = this.extractRouteParamsFromPath(route, path);
            
            // Load component
            const component = await this.loadComponent(route.component);
            
            // Render component
            await this.renderComponent(component, {
                route,
                path,
                params,
                data
            });
            
        } catch (error) {
            MINGUS.utils.logError('Component loading failed', error);
            throw error;
        } finally {
            this.hideLoadingState();
        }
    }
    
    async loadComponent(componentName) {
        // Check if component is already loaded
        if (window.MINGUS.components && window.MINGUS.components[componentName]) {
            return window.MINGUS.components[componentName];
        }
        
        // Dynamic import component
        try {
            const module = await import(`/src/components/${componentName}.js`);
            return module.default || module;
        } catch (error) {
            MINGUS.utils.logError(`Failed to load component: ${componentName}`, error);
            throw error;
        }
    }
    
    async renderComponent(component, context) {
        const appContainer = document.getElementById('app');
        
        if (!appContainer) {
            throw new Error('App container not found');
        }
        
        // Clear container
        appContainer.innerHTML = '';
        
        // Render component
        if (typeof component === 'function') {
            const rendered = await component(context);
            if (typeof rendered === 'string') {
                appContainer.innerHTML = rendered;
            } else if (rendered instanceof Element) {
                appContainer.appendChild(rendered);
            }
        } else if (typeof component === 'string') {
            appContainer.innerHTML = component;
        } else {
            throw new Error('Invalid component format');
        }
        
        // Initialize component if it has an init method
        if (component.init && typeof component.init === 'function') {
            await component.init(context);
        }
    }
    
    // ===== ROUTE PARAMETERS =====
    extractRouteParamsFromPath(route, path) {
        const params = {};
        
        if (route.params.length > 0) {
            const matches = path.match(route.pattern);
            if (matches) {
                route.params.forEach((param, index) => {
                    params[param] = matches[index + 1];
                });
            }
        }
        
        return params;
    }
    
    // ===== HISTORY MANAGEMENT =====
    addToHistory(path, route) {
        this.history.push({
            path,
            route: route.component,
            timestamp: Date.now()
        });
        
        // Limit history length
        if (this.history.length > this.maxHistoryLength) {
            this.history.shift();
        }
    }
    
    getHistory() {
        return [...this.history];
    }
    
    goBack() {
        if (window.history.length > 1) {
            window.history.back();
        }
    }
    
    goForward() {
        window.history.forward();
    }
    
    // ===== EVENT HANDLERS =====
    handlePopState(event) {
        const path = window.location.pathname;
        this.navigate(path, { silent: true });
    }
    
    handleLinkClick(event) {
        const link = event.target.closest('a');
        
        if (!link) return;
        
        const href = link.getAttribute('href');
        
        // Skip external links, mailto, tel, etc.
        if (!href || href.startsWith('http') || href.startsWith('mailto:') || href.startsWith('tel:')) {
            return;
        }
        
        // Skip if target is not _self
        if (link.getAttribute('target') && link.getAttribute('target') !== '_self') {
            return;
        }
        
        // Prevent default behavior
        event.preventDefault();
        
        // Navigate to route
        this.navigate(href);
    }
    
    handleFormSubmit(event) {
        const form = event.target;
        const action = form.getAttribute('action');
        
        if (action && action.startsWith('/')) {
            // Handle form submission as navigation
            event.preventDefault();
            this.navigate(action, { data: { form: form } });
        }
    }
    
    // ===== UI UPDATES =====
    showLoadingState() {
        const loadingElement = document.querySelector('.loading');
        if (loadingElement) {
            loadingElement.style.display = 'flex';
        }
    }
    
    hideLoadingState() {
        const loadingElement = document.querySelector('.loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
    
    updatePageTitle(title) {
        document.title = title ? `${title} - MINGUS` : 'MINGUS';
    }
    
    updateNavigationState(path) {
        // Update active navigation links
        const navLinks = document.querySelectorAll('.nav-links a');
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href === path) {
                link.setAttribute('aria-current', 'page');
                MINGUS.utils.DOM.addClass(link, 'active');
            } else {
                link.removeAttribute('aria-current');
                MINGUS.utils.DOM.removeClass(link, 'active');
            }
        });
    }
    
    // ===== ERROR HANDLING =====
    handleNavigationError(error) {
        MINGUS.utils.logError('Navigation error', error);
        
        // Show error notification
        window.dispatchEvent(new CustomEvent('showNotification', {
            detail: {
                message: 'Failed to load page. Please try again.',
                type: 'error'
            }
        }));
        
        // Navigate to error page
        this.navigate('/500', { replace: true });
    }
    
    // ===== UTILITY METHODS =====
    getCurrentRoute() {
        return this.currentRoute;
    }
    
    getCurrentPath() {
        return window.location.pathname;
    }
    
    isCurrentPath(path) {
        return this.getCurrentPath() === path;
    }
    
    // ===== ANALYTICS =====
    trackPageView(path, route) {
        if (window.analytics && window.analytics.track) {
            window.analytics.track('page_view', {
                path,
                title: route.title,
                component: route.component
            });
        }
    }
    
    // ===== PUBLIC API =====
    go(path, options = {}) {
        return this.navigate(path, options);
    }
    
    replace(path, options = {}) {
        return this.navigate(path, { ...options, replace: true });
    }
    
    back() {
        this.goBack();
    }
    
    forward() {
        this.goForward();
    }
    
    refresh() {
        const currentPath = this.getCurrentPath();
        this.navigate(currentPath, { replace: true });
    }
}

// ===== DEFAULT NAVIGATION GUARDS =====
const defaultGuards = {
    // Authentication guard
    authGuard: async (route, data) => {
        if (route.requiresAuth && !MINGUS.auth.isLoggedIn()) {
            MINGUS.utils.logInfo('Authentication required, redirecting to login');
            MINGUS.router.navigate('/login', { 
                replace: true,
                data: { redirect: route.path }
            });
            return false;
        }
        
        if (route.public && MINGUS.auth.isLoggedIn()) {
            // Redirect logged-in users away from public pages
            if (route.path === '/login' || route.path === '/register') {
                MINGUS.router.navigate('/dashboard', { replace: true });
                return false;
            }
        }
        
        return true;
    },
    
    // Loading guard
    loadingGuard: async (route, data) => {
        // Check if component is already loading
        if (MINGUS.router.loadingStates.get(route.component)) {
            MINGUS.utils.logWarn('Component already loading', { component: route.component });
            return false;
        }
        
        return true;
    },
    
    // Permission guard
    permissionGuard: async (route, data) => {
        if (route.requiresPermission) {
            const hasPermission = MINGUS.auth.hasPermission(route.requiresPermission);
            if (!hasPermission) {
                MINGUS.utils.logWarn('Permission denied', { 
                    permission: route.requiresPermission,
                    user: MINGUS.auth.getCurrentUser()
                });
                MINGUS.router.navigate('/403', { replace: true });
                return false;
            }
        }
        
        return true;
    }
};

// ===== EXPORT ROUTER =====
const router = new Router();

// Add default guards
router.addNavigationGuard(defaultGuards.authGuard);
router.addNavigationGuard(defaultGuards.loadingGuard);
router.addNavigationGuard(defaultGuards.permissionGuard);

// Make available globally
window.MINGUS = window.MINGUS || {};
window.MINGUS.router = router;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Router;
}
