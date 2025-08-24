/**
 * MINGUS Application Utilities
 * Cross-browser compatible utility functions with error handling and performance optimizations
 */

// ===== ERROR HANDLING =====
class AppError extends Error {
    constructor(message, code = 'UNKNOWN_ERROR', details = null) {
        super(message);
        this.name = 'AppError';
        this.code = code;
        this.details = details;
        this.timestamp = new Date().toISOString();
    }
}

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error caught:', event.error);
    logError('Global error', event.error);
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    logError('Unhandled promise rejection', event.reason);
});

// ===== LOGGING =====
const LOG_LEVELS = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3
};

let currentLogLevel = LOG_LEVELS.INFO;

function setLogLevel(level) {
    currentLogLevel = level;
}

function log(level, message, data = null) {
    if (level >= currentLogLevel) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level: Object.keys(LOG_LEVELS)[level],
            message,
            data
        };
        
        switch (level) {
            case LOG_LEVELS.DEBUG:
                console.debug(`[${timestamp}] DEBUG:`, message, data);
                break;
            case LOG_LEVELS.INFO:
                console.info(`[${timestamp}] INFO:`, message, data);
                break;
            case LOG_LEVELS.WARN:
                console.warn(`[${timestamp}] WARN:`, message, data);
                break;
            case LOG_LEVELS.ERROR:
                console.error(`[${timestamp}] ERROR:`, message, data);
                break;
        }
        
        // Send to analytics if available
        if (window.analytics && window.analytics.track) {
            window.analytics.track('app_log', logEntry);
        }
    }
}

function logDebug(message, data = null) {
    log(LOG_LEVELS.DEBUG, message, data);
}

function logInfo(message, data = null) {
    log(LOG_LEVELS.INFO, message, data);
}

function logWarn(message, data = null) {
    log(LOG_LEVELS.WARN, message, data);
}

function logError(message, error = null) {
    log(LOG_LEVELS.ERROR, message, error);
    
    // Show error boundary if critical
    if (error && error.code === 'CRITICAL_ERROR') {
        showErrorBoundary();
    }
}

// ===== DOM UTILITIES =====
const DOM = {
    // Create element with attributes
    create: (tag, attributes = {}, children = []) => {
        const element = document.createElement(tag);
        
        // Set attributes
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, value);
            } else {
                element.setAttribute(key, value);
            }
        });
        
        // Add children
        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else {
                element.appendChild(child);
            }
        });
        
        return element;
    },
    
    // Find element by selector
    find: (selector, parent = document) => {
        return parent.querySelector(selector);
    },
    
    // Find all elements by selector
    findAll: (selector, parent = document) => {
        return Array.from(parent.querySelectorAll(selector));
    },
    
    // Add event listener with error handling
    on: (element, event, handler, options = {}) => {
        try {
            element.addEventListener(event, handler, options);
        } catch (error) {
            logError(`Failed to add event listener for ${event}`, error);
        }
    },
    
    // Remove event listener
    off: (element, event, handler, options = {}) => {
        try {
            element.removeEventListener(event, handler, options);
        } catch (error) {
            logError(`Failed to remove event listener for ${event}`, error);
        }
    },
    
    // Toggle class
    toggleClass: (element, className) => {
        element.classList.toggle(className);
    },
    
    // Add class
    addClass: (element, className) => {
        element.classList.add(className);
    },
    
    // Remove class
    removeClass: (element, className) => {
        element.classList.remove(className);
    },
    
    // Check if element has class
    hasClass: (element, className) => {
        return element.classList.contains(className);
    }
};

// ===== STORAGE UTILITIES =====
const Storage = {
    // Check if localStorage is available
    isAvailable: () => {
        try {
            const test = '__storage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    },
    
    // Get item with error handling
    get: (key, defaultValue = null) => {
        if (!Storage.isAvailable()) {
            logWarn('localStorage not available');
            return defaultValue;
        }
        
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            logError(`Failed to get item from localStorage: ${key}`, error);
            return defaultValue;
        }
    },
    
    // Set item with error handling
    set: (key, value) => {
        if (!Storage.isAvailable()) {
            logWarn('localStorage not available');
            return false;
        }
        
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            logError(`Failed to set item in localStorage: ${key}`, error);
            return false;
        }
    },
    
    // Remove item
    remove: (key) => {
        if (!Storage.isAvailable()) {
            return false;
        }
        
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            logError(`Failed to remove item from localStorage: ${key}`, error);
            return false;
        }
    },
    
    // Clear all items
    clear: () => {
        if (!Storage.isAvailable()) {
            return false;
        }
        
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            logError('Failed to clear localStorage', error);
            return false;
        }
    }
};

// ===== VALIDATION UTILITIES =====
const Validation = {
    // Email validation
    isEmail: (email) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    // Phone validation (basic)
    isPhone: (phone) => {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
    },
    
    // URL validation
    isUrl: (url) => {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },
    
    // Required field validation
    isRequired: (value) => {
        return value !== null && value !== undefined && value.toString().trim() !== '';
    },
    
    // Min length validation
    minLength: (value, min) => {
        return value && value.toString().length >= min;
    },
    
    // Max length validation
    maxLength: (value, max) => {
        return value && value.toString().length <= max;
    },
    
    // Number validation
    isNumber: (value) => {
        return !isNaN(parseFloat(value)) && isFinite(value);
    },
    
    // Integer validation
    isInteger: (value) => {
        return Number.isInteger(Number(value));
    },
    
    // Positive number validation
    isPositive: (value) => {
        return Validation.isNumber(value) && Number(value) > 0;
    }
};

// ===== FORMATTING UTILITIES =====
const Format = {
    // Currency formatting
    currency: (amount, currency = 'USD', locale = 'en-US') => {
        try {
            return new Intl.NumberFormat(locale, {
                style: 'currency',
                currency: currency
            }).format(amount);
        } catch (error) {
            logError('Currency formatting failed', error);
            return `${currency} ${amount}`;
        }
    },
    
    // Number formatting
    number: (number, locale = 'en-US', options = {}) => {
        try {
            return new Intl.NumberFormat(locale, options).format(number);
        } catch (error) {
            logError('Number formatting failed', error);
            return number.toString();
        }
    },
    
    // Date formatting
    date: (date, locale = 'en-US', options = {}) => {
        try {
            const dateObj = new Date(date);
            return new Intl.DateTimeFormat(locale, options).format(dateObj);
        } catch (error) {
            logError('Date formatting failed', error);
            return date.toString();
        }
    },
    
    // Relative time formatting
    relativeTime: (date) => {
        try {
            const now = new Date();
            const target = new Date(date);
            const diff = now - target;
            const seconds = Math.floor(diff / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);
            
            if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
            if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
            if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
            return 'Just now';
        } catch (error) {
            logError('Relative time formatting failed', error);
            return 'Unknown time';
        }
    },
    
    // File size formatting
    fileSize: (bytes) => {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Phone number formatting
    phone: (phone, format = '(###) ###-####') => {
        const cleaned = phone.replace(/\D/g, '');
        let result = format;
        
        for (let i = 0; i < cleaned.length && result.includes('#'); i++) {
            result = result.replace('#', cleaned[i]);
        }
        
        return result.replace(/#/g, '_');
    }
};

// ===== PERFORMANCE UTILITIES =====
const Performance = {
    // Debounce function
    debounce: (func, wait, immediate = false) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func.apply(this, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(this, args);
        };
    },
    
    // Throttle function
    throttle: (func, limit) => {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // Measure execution time
    measure: (name, fn) => {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        logDebug(`Performance: ${name} took ${(end - start).toFixed(2)}ms`);
        return result;
    },
    
    // Lazy load images
    lazyLoadImages: () => {
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    }
};

// ===== BROWSER UTILITIES =====
const Browser = {
    // Check if browser supports feature
    supports: (feature) => {
        const features = {
            localStorage: () => Storage.isAvailable(),
            sessionStorage: () => {
                try {
                    const test = '__storage_test__';
                    sessionStorage.setItem(test, test);
                    sessionStorage.removeItem(test);
                    return true;
                } catch (e) {
                    return false;
                }
            },
            serviceWorker: () => 'serviceWorker' in navigator,
            pushManager: () => 'PushManager' in window,
            geolocation: () => 'geolocation' in navigator,
            webGL: () => {
                try {
                    const canvas = document.createElement('canvas');
                    return !!(window.WebGLRenderingContext && 
                        (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
                } catch (e) {
                    return false;
                }
            },
            webp: () => {
                return new Promise((resolve) => {
                    const webP = new Image();
                    webP.onload = webP.onerror = () => {
                        resolve(webP.height === 2);
                    };
                    webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
                });
            }
        };
        
        return features[feature] ? features[feature]() : false;
    },
    
    // Get browser info
    getInfo: () => {
        const userAgent = navigator.userAgent;
        const browserInfo = {
            userAgent,
            language: navigator.language,
            languages: navigator.languages,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine,
            platform: navigator.platform,
            vendor: navigator.vendor
        };
        
        // Detect browser
        if (userAgent.includes('Chrome')) {
            browserInfo.browser = 'Chrome';
        } else if (userAgent.includes('Firefox')) {
            browserInfo.browser = 'Firefox';
        } else if (userAgent.includes('Safari')) {
            browserInfo.browser = 'Safari';
        } else if (userAgent.includes('Edge')) {
            browserInfo.browser = 'Edge';
        } else if (userAgent.includes('MSIE') || userAgent.includes('Trident/')) {
            browserInfo.browser = 'Internet Explorer';
        } else {
            browserInfo.browser = 'Unknown';
        }
        
        return browserInfo;
    },
    
    // Check if mobile device
    isMobile: () => {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    
    // Check if touch device
    isTouch: () => {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
};

// ===== ANIMATION UTILITIES =====
const Animation = {
    // Smooth scroll to element
    scrollTo: (element, offset = 0, duration = 300) => {
        const target = typeof element === 'string' ? document.querySelector(element) : element;
        if (!target) return;
        
        const start = window.pageYOffset;
        const targetPosition = target.offsetTop - offset;
        const distance = targetPosition - start;
        let startTime = null;
        
        function animation(currentTime) {
            if (startTime === null) startTime = currentTime;
            const timeElapsed = currentTime - startTime;
            const run = ease(timeElapsed, start, distance, duration);
            window.scrollTo(0, run);
            if (timeElapsed < duration) requestAnimationFrame(animation);
        }
        
        function ease(t, b, c, d) {
            t /= d / 2;
            if (t < 1) return c / 2 * t * t + b;
            t--;
            return -c / 2 * (t * (t - 2) - 1) + b;
        }
        
        requestAnimationFrame(animation);
    },
    
    // Fade in element
    fadeIn: (element, duration = 300) => {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.min(progress / duration, 1);
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    },
    
    // Fade out element
    fadeOut: (element, duration = 300) => {
        let start = null;
        const initialOpacity = parseFloat(getComputedStyle(element).opacity);
        
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.max(initialOpacity - (progress / duration), 0);
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        }
        
        requestAnimationFrame(animate);
    }
};

// ===== EXPORT UTILITIES =====
window.MINGUS = window.MINGUS || {};
window.MINGUS.utils = {
    AppError,
    logDebug,
    logInfo,
    logWarn,
    logError,
    setLogLevel,
    DOM,
    Storage,
    Validation,
    Format,
    Performance,
    Browser,
    Animation
};

// Initialize utilities
document.addEventListener('DOMContentLoaded', () => {
    logInfo('MINGUS utilities initialized');
    
    // Initialize lazy loading
    if (Performance.lazyLoadImages) {
        Performance.lazyLoadImages();
    }
    
    // Log browser info in debug mode
    if (currentLogLevel === LOG_LEVELS.DEBUG) {
        logDebug('Browser info', Browser.getInfo());
    }
});
