/**
 * MINGUS Core JavaScript
 * Core functionality and initialization
 */

// Global MINGUS namespace
window.MINGUS = window.MINGUS || {};

// Core application class
class MINGUSCore {
    constructor() {
        this.isInitialized = false;
        this.config = {};
        this.modules = new Map();
        
        this.init();
    }
    
    init() {
        try {
            this.loadConfiguration();
            this.initializeModules();
            this.setupEventListeners();
            this.isInitialized = true;
            
            console.log('MINGUS Core initialized successfully');
        } catch (error) {
            console.error('Failed to initialize MINGUS Core:', error);
        }
    }
    
    loadConfiguration() {
        this.config = {
            app: {
                name: 'MINGUS',
                version: '1.0.0',
                environment: this.getEnvironment()
            },
            api: {
                baseUrl: '/api',
                timeout: 30000
            },
            features: {
                analytics: true,
                notifications: true,
                realtime: true
            }
        };
    }
    
    getEnvironment() {
        const hostname = window.location.hostname;
        
        if (hostname.includes('localhost') || hostname.includes('127.0.0.1')) {
            return 'development';
        } else if (hostname.includes('staging') || hostname.includes('test')) {
            return 'staging';
        } else {
            return 'production';
        }
    }
    
    initializeModules() {
        // Initialize core modules
        this.registerModule('config', window.MINGUS.config || {});
        this.registerModule('utils', window.MINGUS.utils || {});
        this.registerModule('api', window.MINGUS.api || {});
        this.registerModule('auth', window.MINGUS.auth || {});
        this.registerModule('router', window.MINGUS.router || {});
        this.registerModule('components', window.MINGUS.components || {});
        this.registerModule('analytics', window.MINGUS.analytics || {});
    }
    
    registerModule(name, module) {
        this.modules.set(name, module);
        window.MINGUS[name] = module;
    }
    
    getModule(name) {
        return this.modules.get(name);
    }
    
    setupEventListeners() {
        // Global error handling
        window.addEventListener('error', (event) => {
            this.handleError(event.error || event);
        });
        
        // Unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError(event.reason);
        });
        
        // Page visibility changes
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
        
        // Online/offline status
        window.addEventListener('online', () => {
            this.handleOnlineStatus(true);
        });
        
        window.addEventListener('offline', () => {
            this.handleOnlineStatus(false);
        });
    }
    
    handleError(error) {
        console.error('MINGUS Error:', error);
        
        // Send to analytics if available
        if (this.getModule('analytics') && this.getModule('analytics').trackError) {
            this.getModule('analytics').trackError('javascript_error', {
                message: error.message,
                stack: error.stack,
                url: window.location.href
            });
        }
    }
    
    handleVisibilityChange() {
        const isVisible = !document.hidden;
        
        // Pause/resume analytics tracking
        if (this.getModule('analytics')) {
            if (isVisible) {
                this.getModule('analytics').resumeTracking();
            } else {
                this.getModule('analytics').pauseTracking();
            }
        }
    }
    
    handleOnlineStatus(isOnline) {
        if (isOnline) {
            console.log('MINGUS: Back online');
            // Resume any paused operations
        } else {
            console.log('MINGUS: Gone offline');
            // Pause operations that require network
        }
    }
    
    // Utility methods
    getConfig() {
        return this.config;
    }
    
    isReady() {
        return this.isInitialized;
    }
    
    // Module management
    loadModule(name, moduleLoader) {
        try {
            const module = moduleLoader();
            this.registerModule(name, module);
            return module;
        } catch (error) {
            console.error(`Failed to load module ${name}:`, error);
            return null;
        }
    }
    
    // Application lifecycle
    start() {
        console.log('MINGUS application starting...');
        
        // Initialize router if available
        if (this.getModule('router') && this.getModule('router').init) {
            this.getModule('router').init();
        }
        
        // Initialize components if available
        if (this.getModule('components') && this.getModule('components').init) {
            this.getModule('components').init();
        }
        
        console.log('MINGUS application started successfully');
    }
    
    stop() {
        console.log('MINGUS application stopping...');
        
        // Cleanup modules
        this.modules.forEach((module, name) => {
            if (module && module.cleanup) {
                module.cleanup();
            }
        });
        
        console.log('MINGUS application stopped');
    }
}

// Initialize core when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.MINGUS.core = new MINGUSCore();
    
    // Start the application
    setTimeout(() => {
        window.MINGUS.core.start();
    }, 100);
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MINGUSCore;
}
