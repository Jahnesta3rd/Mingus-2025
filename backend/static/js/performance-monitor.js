/**
 * Performance Monitoring Library for Flask Financial Application
 * Collects Core Web Vitals and other performance metrics
 */

class PerformanceMonitor {
    constructor(config = {}) {
        this.config = {
            endpoint: config.endpoint || '/monitoring/web-vitals',
            sampleRate: config.sampleRate || 1.0, // 100% sampling
            maxRetries: config.maxRetries || 3,
            retryDelay: config.retryDelay || 1000,
            enableDebug: config.enableDebug || false,
            customMetrics: config.customMetrics || {},
            ...config
        };
        
        this.metrics = new Map();
        this.retryCount = 0;
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        try {
            // Initialize Core Web Vitals collection
            this.initCoreWebVitals();
            
            // Initialize custom metrics
            this.initCustomMetrics();
            
            // Initialize performance observer
            this.initPerformanceObserver();
            
            // Initialize navigation timing
            this.initNavigationTiming();
            
            // Initialize resource timing
            this.initResourceTiming();
            
            // Initialize user interaction metrics
            this.initUserInteractionMetrics();
            
            this.isInitialized = true;
            this.log('Performance monitor initialized');
            
        } catch (error) {
            this.log('Error initializing performance monitor:', error);
        }
    }
    
    initCoreWebVitals() {
        // Largest Contentful Paint (LCP)
        if ('PerformanceObserver' in window) {
            try {
                const lcpObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    
                    if (lastEntry) {
                        this.recordWebVital('LCP', lastEntry.startTime, {
                            element: lastEntry.element?.tagName || 'unknown',
                            size: lastEntry.size || 0,
                            id: lastEntry.id || 'unknown'
                        });
                    }
                });
                
                lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
            } catch (error) {
                this.log('LCP observer error:', error);
            }
            
            // First Input Delay (FID)
            try {
                const fidObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    
                    entries.forEach(entry => {
                        this.recordWebVital('FID', entry.processingStart - entry.startTime, {
                            name: entry.name,
                            target: entry.target?.tagName || 'unknown'
                        });
                    });
                });
                
                fidObserver.observe({ entryTypes: ['first-input'] });
            } catch (error) {
                this.log('FID observer error:', error);
            }
            
            // Cumulative Layout Shift (CLS)
            try {
                let clsValue = 0;
                let clsEntries = [];
                
                const clsObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    
                    entries.forEach(entry => {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                            clsEntries.push(entry);
                        }
                    });
                    
                    // Record CLS when it changes significantly
                    if (clsEntries.length > 0) {
                        this.recordWebVital('CLS', clsValue, {
                            entries: clsEntries.length,
                            sources: clsEntries.map(e => e.sources?.[0]?.node?.tagName || 'unknown')
                        });
                    }
                });
                
                clsObserver.observe({ entryTypes: ['layout-shift'] });
            } catch (error) {
                this.log('CLS observer error:', error);
            }
        }
        
        // Time to First Byte (TTFB) - fallback method
        if (performance.timing) {
            const navigationStart = performance.timing.navigationStart;
            const responseStart = performance.timing.responseStart;
            
            if (navigationStart && responseStart) {
                const ttfb = responseStart - navigationStart;
                this.recordWebVital('TTFB', ttfb);
            }
        }
        
        // Modern Navigation Timing API
        if (performance.getEntriesByType) {
            const navigationEntries = performance.getEntriesByType('navigation');
            if (navigationEntries.length > 0) {
                const nav = navigationEntries[0];
                if (nav.responseStart > 0) {
                    const ttfb = nav.responseStart - nav.fetchStart;
                    this.recordWebVital('TTFB', ttfb);
                }
            }
        }
    }
    
    initCustomMetrics() {
        // Custom business metrics
        this.config.customMetrics.forEach(metric => {
            if (metric.name && metric.value !== undefined) {
                this.recordCustomMetric(metric.name, metric.value, metric.metadata);
            }
        });
    }
    
    initPerformanceObserver() {
        if ('PerformanceObserver' in window) {
            try {
                // Long Tasks
                const longTaskObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    
                    entries.forEach(entry => {
                        if (entry.duration > 50) { // 50ms threshold
                            this.recordCustomMetric('long_task', entry.duration, {
                                name: entry.name,
                                startTime: entry.startTime,
                                duration: entry.duration
                            });
                        }
                    });
                });
                
                longTaskObserver.observe({ entryTypes: ['longtask'] });
                
                // Paint Timing
                const paintObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    
                    entries.forEach(entry => {
                        this.recordCustomMetric('paint', entry.startTime, {
                            name: entry.name,
                            startTime: entry.startTime
                        });
                    });
                });
                
                paintObserver.observe({ entryTypes: ['paint'] });
                
            } catch (error) {
                this.log('Performance observer error:', error);
            }
        }
    }
    
    initNavigationTiming() {
        // Navigation Timing API metrics
        if (performance.timing) {
            const timing = performance.timing;
            const navigationStart = timing.navigationStart;
            
            if (navigationStart) {
                const metrics = {
                    'dom_loading': timing.domLoading - navigationStart,
                    'dom_interactive': timing.domInteractive - navigationStart,
                    'dom_content_loaded': timing.domContentLoadedEventEnd - navigationStart,
                    'dom_complete': timing.domComplete - navigationStart,
                    'load_complete': timing.loadEventEnd - navigationStart,
                    'redirect_count': timing.navigationType === 1 ? 0 : timing.redirectCount,
                    'redirect_time': timing.redirectEnd - timing.redirectStart,
                    'dns_lookup': timing.domainLookupEnd - timing.domainLookupStart,
                    'tcp_connection': timing.connectEnd - timing.connectStart,
                    'server_response': timing.responseEnd - timing.requestStart,
                    'dom_parsing': timing.domInteractive - timing.domLoading,
                    'resource_loading': timing.loadEventEnd - timing.domContentLoadedEventEnd
                };
                
                Object.entries(metrics).forEach(([name, value]) => {
                    if (value > 0) {
                        this.recordCustomMetric(name, value);
                    }
                });
            }
        }
        
        // Modern Navigation Timing API
        if (performance.getEntriesByType) {
            const navigationEntries = performance.getEntriesByType('navigation');
            if (navigationEntries.length > 0) {
                const nav = navigationEntries[0];
                
                const metrics = {
                    'dom_content_loaded_event': nav.domContentLoadedEventEnd - nav.domContentLoadedEventStart,
                    'load_event': nav.loadEventEnd - nav.loadEventStart,
                    'dom_interactive': nav.domInteractive - nav.fetchStart,
                    'dom_complete': nav.domComplete - nav.fetchStart,
                    'redirect_count': nav.redirectCount,
                    'redirect_time': nav.redirectEnd - nav.redirectStart,
                    'dns_lookup': nav.domainLookupEnd - nav.domainLookupStart,
                    'tcp_connection': nav.connectEnd - nav.connectStart,
                    'server_response': nav.responseEnd - nav.requestStart
                };
                
                Object.entries(metrics).forEach(([name, value]) => {
                    if (value > 0) {
                        this.recordCustomMetric(name, value);
                    }
                });
            }
        }
    }
    
    initResourceTiming() {
        if ('PerformanceObserver' in window) {
            try {
                const resourceObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    
                    entries.forEach(entry => {
                        // Only track external resources
                        if (entry.initiatorType && entry.name !== window.location.href) {
                            const resourceMetrics = {
                                'resource_dns': entry.domainLookupEnd - entry.domainLookupStart,
                                'resource_tcp': entry.connectEnd - entry.connectStart,
                                'resource_ttfb': entry.responseStart - entry.requestStart,
                                'resource_download': entry.responseEnd - entry.responseStart,
                                'resource_total': entry.duration,
                                'resource_size': entry.transferSize || 0
                            };
                            
                            Object.entries(resourceMetrics).forEach(([name, value]) => {
                                if (value > 0) {
                                    this.recordCustomMetric(name, value, {
                                        resource: entry.name,
                                        type: entry.initiatorType,
                                        size: entry.transferSize || 0
                                    });
                                }
                            });
                        }
                    });
                });
                
                resourceObserver.observe({ entryTypes: ['resource'] });
                
            } catch (error) {
                this.log('Resource timing observer error:', error);
            }
        }
    }
    
    initUserInteractionMetrics() {
        // Track user interactions
        let interactionCount = 0;
        let lastInteractionTime = Date.now();
        
        const interactionEvents = ['click', 'input', 'scroll', 'keydown', 'touchstart'];
        
        interactionEvents.forEach(eventType => {
            document.addEventListener(eventType, (event) => {
                interactionCount++;
                const now = Date.now();
                const timeSinceLastInteraction = now - lastInteractionTime;
                
                this.recordCustomMetric('user_interaction', timeSinceLastInteraction, {
                    type: eventType,
                    target: event.target?.tagName || 'unknown',
                    interaction_count: interactionCount
                });
                
                lastInteractionTime = now;
            }, { passive: true });
        });
        
        // Track page visibility changes
        if ('hidden' in document) {
            document.addEventListener('visibilitychange', () => {
                const isHidden = document.hidden;
                this.recordCustomMetric('page_visibility', isHidden ? 0 : 1, {
                    hidden: isHidden,
                    timestamp: Date.now()
                });
            });
        }
        
        // Track focus events
        window.addEventListener('focus', () => {
            this.recordCustomMetric('window_focus', 1, {
                timestamp: Date.now()
            });
        });
        
        window.addEventListener('blur', () => {
            this.recordCustomMetric('window_blur', 1, {
                timestamp: Date.now()
            });
        });
    }
    
    recordWebVital(metricName, value, metadata = {}) {
        // Apply sampling
        if (Math.random() > this.config.sampleRate) {
            return;
        }
        
        const metric = {
            metric_name: metricName,
            value: value,
            timestamp: new Date().toISOString(),
            page_url: window.location.href,
            user_id: this.getUserId(),
            device_type: this.getDeviceType(),
            browser: this.getBrowserInfo(),
            metadata: metadata
        };
        
        this.metrics.set(`${metricName}_${Date.now()}`, metric);
        this.sendMetric(metric);
        
        this.log(`Web Vital recorded: ${metricName} = ${value}`, metadata);
    }
    
    recordCustomMetric(name, value, metadata = {}) {
        // Apply sampling
        if (Math.random() > this.config.sampleRate) {
            return;
        }
        
        const metric = {
            metric_name: name,
            value: value,
            timestamp: new Date().toISOString(),
            page_url: window.location.href,
            user_id: this.getUserId(),
            device_type: this.getDeviceType(),
            browser: this.getBrowserInfo(),
            metadata: metadata
        };
        
        this.metrics.set(`${name}_${Date.now()}`, metric);
        this.sendMetric(metric);
        
        this.log(`Custom metric recorded: ${name} = ${value}`, metadata);
    }
    
    async sendMetric(metric) {
        try {
            const response = await fetch(this.config.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(metric)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.retryCount = 0; // Reset retry count on success
            
        } catch (error) {
            this.log('Error sending metric:', error);
            
            // Retry logic
            if (this.retryCount < this.config.maxRetries) {
                this.retryCount++;
                setTimeout(() => {
                    this.sendMetric(metric);
                }, this.config.retryDelay * this.retryCount);
            }
        }
    }
    
    getUserId() {
        // Try to get user ID from various sources
        try {
            // Check for user ID in localStorage
            const userId = localStorage.getItem('user_id');
            if (userId) return userId;
            
            // Check for user ID in sessionStorage
            const sessionUserId = sessionStorage.getItem('user_id');
            if (sessionUserId) return sessionUserId;
            
            // Check for user ID in cookies
            const cookies = document.cookie.split(';');
            for (const cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'user_id' && value) {
                    return value;
                }
            }
            
            // Generate anonymous ID if none found
            let anonymousId = localStorage.getItem('anonymous_user_id');
            if (!anonymousId) {
                anonymousId = 'anon_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('anonymous_user_id', anonymousId);
            }
            return anonymousId;
            
        } catch (error) {
            this.log('Error getting user ID:', error);
            return 'unknown';
        }
    }
    
    getDeviceType() {
        try {
            const userAgent = navigator.userAgent.toLowerCase();
            
            if (/mobile|android|iphone|ipad|phone/i.test(userAgent)) {
                return 'mobile';
            } else if (/tablet|ipad/i.test(userAgent)) {
                return 'tablet';
            } else {
                return 'desktop';
            }
        } catch (error) {
            return 'unknown';
        }
    }
    
    getBrowserInfo() {
        try {
            const userAgent = navigator.userAgent;
            
            if (userAgent.includes('Chrome')) return 'Chrome';
            if (userAgent.includes('Firefox')) return 'Firefox';
            if (userAgent.includes('Safari')) return 'Safari';
            if (userAgent.includes('Edge')) return 'Edge';
            if (userAgent.includes('MSIE') || userAgent.includes('Trident/')) return 'Internet Explorer';
            
            return 'Unknown';
        } catch (error) {
            return 'Unknown';
        }
    }
    
    log(...args) {
        if (this.config.enableDebug) {
            console.log('[PerformanceMonitor]', ...args);
        }
    }
    
    // Public API methods
    getMetrics() {
        return Array.from(this.metrics.values());
    }
    
    clearMetrics() {
        this.metrics.clear();
    }
    
    setConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }
    
    // Force send all pending metrics
    async flushMetrics() {
        const metrics = Array.from(this.metrics.values());
        this.metrics.clear();
        
        for (const metric of metrics) {
            await this.sendMetric(metric);
        }
        
        this.log(`Flushed ${metrics.length} metrics`);
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.performanceMonitor = new PerformanceMonitor();
    });
} else {
    window.performanceMonitor = new PerformanceMonitor();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceMonitor;
}

// Export for ES6 modules
if (typeof exports !== 'undefined') {
    exports.PerformanceMonitor = PerformanceMonitor;
}
