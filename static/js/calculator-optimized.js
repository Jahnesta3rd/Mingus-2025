/**
 * Optimized AI Job Impact Calculator JavaScript
 * Implements lazy loading, progressive form submission, and performance optimizations
 */

// Performance tracking
const calculatorStartTime = Date.now();
const performanceMetrics = {
    formLoadTime: 0,
    calculationTime: 0,
    submissionTime: 0,
    cacheHits: 0,
    cacheMisses: 0
};

// Lazy loading configuration
const LAZY_LOAD_CONFIG = {
    threshold: 0.1,
    rootMargin: '50px',
    delay: 100
};

// Cache for job risk data
const jobRiskCache = new Map();
const CACHE_TTL = 2 * 60 * 60 * 1000; // 2 hours

// Progressive form submission
class ProgressiveForm {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.currentStep = 0;
        this.totalSteps = 0;
        this.formData = {};
        this.validationErrors = {};
        this.isSubmitting = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupLazyLoading();
        this.setupProgressiveValidation();
        this.setupPerformanceMonitoring();
    }
    
    setupEventListeners() {
        // Form submission with progressive enhancement
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });
        
        // Real-time validation
        this.form.addEventListener('input', (e) => {
            this.validateField(e.target);
        });
        
        // Keyboard navigation
        this.form.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.target.type !== 'textarea') {
                e.preventDefault();
                this.nextStep();
            }
        });
    }
    
    setupLazyLoading() {
        // Lazy load modal components
        const modalTriggers = document.querySelectorAll('[data-modal]');
        const modalObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadModal(entry.target.dataset.modal);
                    modalObserver.unobserve(entry.target);
                }
            });
        }, LAZY_LOAD_CONFIG);
        
        modalTriggers.forEach(trigger => modalObserver.observe(trigger));
        
        // Lazy load images
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadImage(entry.target);
                    imageObserver.unobserve(entry.target);
                }
            });
        }, LAZY_LOAD_CONFIG);
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    setupProgressiveValidation() {
        // Client-side validation rules
        this.validationRules = {
            job_title: {
                required: true,
                minLength: 2,
                maxLength: 100,
                pattern: /^[a-zA-Z\s\-\.]+$/
            },
            industry: {
                required: true,
                minLength: 2,
                maxLength: 50
            },
            email: {
                required: true,
                pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
            },
            first_name: {
                required: true,
                minLength: 1,
                maxLength: 50,
                pattern: /^[a-zA-Z\s\-']+$/
            }
        };
    }
    
    setupPerformanceMonitoring() {
        // Monitor form performance
        const formLoadEnd = Date.now();
        performanceMetrics.formLoadTime = formLoadEnd - calculatorStartTime;
        
        // Report performance metrics
        this.reportPerformanceMetrics();
    }
    
    async handleSubmit() {
        if (this.isSubmitting) return;
        
        this.isSubmitting = true;
        this.showLoadingState();
        
        try {
            // Validate form
            if (!this.validateForm()) {
                this.hideLoadingState();
                this.isSubmitting = false;
                return;
            }
            
            // Collect form data
            const formData = this.collectFormData();
            
            // Check cache for job risk data
            const cachedResult = this.getCachedResult(formData);
            if (cachedResult) {
                this.displayResults(cachedResult);
                this.hideLoadingState();
                this.isSubmitting = false;
                return;
            }
            
            // Submit assessment
            const startTime = Date.now();
            const result = await this.submitAssessment(formData);
            performanceMetrics.submissionTime = Date.now() - startTime;
            
            // Cache result
            this.cacheResult(formData, result);
            
            // Display results
            this.displayResults(result);
            
        } catch (error) {
            console.error('Assessment submission error:', error);
            this.showError('There was an error processing your assessment. Please try again.');
        } finally {
            this.hideLoadingState();
            this.isSubmitting = false;
        }
    }
    
    validateForm() {
        this.validationErrors = {};
        let isValid = true;
        
        // Validate each field
        Object.keys(this.validationRules).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field && !this.validateField(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    validateField(field) {
        const fieldName = field.name;
        const value = field.value.trim();
        const rules = this.validationRules[fieldName];
        
        if (!rules) return true;
        
        // Clear previous error
        this.clearFieldError(field);
        
        // Required validation
        if (rules.required && !value) {
            this.showFieldError(field, 'This field is required.');
            return false;
        }
        
        // Length validation
        if (rules.minLength && value.length < rules.minLength) {
            this.showFieldError(field, `Minimum ${rules.minLength} characters required.`);
            return false;
        }
        
        if (rules.maxLength && value.length > rules.maxLength) {
            this.showFieldError(field, `Maximum ${rules.maxLength} characters allowed.`);
            return false;
        }
        
        // Pattern validation
        if (rules.pattern && !rules.pattern.test(value)) {
            this.showFieldError(field, 'Please enter a valid value.');
            return false;
        }
        
        return true;
    }
    
    showFieldError(field, message) {
        this.validationErrors[field.name] = message;
        
        // Add error class
        field.classList.add('error');
        
        // Create or update error message
        let errorElement = field.parentNode.querySelector('.error-message');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'error-message';
            field.parentNode.appendChild(errorElement);
        }
        errorElement.textContent = message;
    }
    
    clearFieldError(field) {
        field.classList.remove('error');
        const errorElement = field.parentNode.querySelector('.error-message');
        if (errorElement) {
            errorElement.remove();
        }
        delete this.validationErrors[field.name];
    }
    
    collectFormData() {
        const formData = new FormData(this.form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (key.includes('[]')) {
                // Handle array fields
                const arrayKey = key.replace('[]', '');
                if (!data[arrayKey]) {
                    data[arrayKey] = [];
                }
                data[arrayKey].push(value);
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }
    
    getCachedResult(formData) {
        const cacheKey = this.generateCacheKey(formData);
        const cached = jobRiskCache.get(cacheKey);
        
        if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
            performanceMetrics.cacheHits++;
            return cached.data;
        }
        
        performanceMetrics.cacheMisses++;
        return null;
    }
    
    cacheResult(formData, result) {
        const cacheKey = this.generateCacheKey(formData);
        jobRiskCache.set(cacheKey, {
            data: result,
            timestamp: Date.now()
        });
        
        // Limit cache size
        if (jobRiskCache.size > 100) {
            const firstKey = jobRiskCache.keys().next().value;
            jobRiskCache.delete(firstKey);
        }
    }
    
    generateCacheKey(formData) {
        const keyData = {
            job_title: formData.job_title,
            industry: formData.industry,
            experience_level: formData.experience_level,
            tasks: formData.tasks_array?.sort(),
            remote_work: formData.remote_work_frequency,
            ai_usage: formData.ai_usage_frequency,
            team_size: formData.team_size,
            tech_skills: formData.tech_skills_level
        };
        
        return btoa(JSON.stringify(keyData));
    }
    
    async submitAssessment(formData) {
        const startTime = Date.now();
        
        try {
            const response = await fetch('/api/ai-job-assessment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            performanceMetrics.calculationTime = Date.now() - startTime;
            
            return result;
            
        } catch (error) {
            console.error('Assessment submission failed:', error);
            throw error;
        }
    }
    
    displayResults(results) {
        // Update scores
        document.getElementById('automation-score').textContent = results.automation_score + '%';
        document.getElementById('augmentation-score').textContent = results.augmentation_score + '%';
        
        // Update risk level
        const riskLevelDisplay = document.getElementById('risk-level-display');
        riskLevelDisplay.textContent = results.risk_level.charAt(0).toUpperCase() + results.risk_level.slice(1) + ' Risk';
        riskLevelDisplay.className = `risk-level risk-${results.risk_level}`;
        
        // Update recommendations
        const recommendationsList = document.getElementById('recommendations-list');
        recommendationsList.innerHTML = results.recommendations.map(rec => `
            <div class="recommendation-item">
                <div class="recommendation-icon"></div>
                <div class="recommendation-text">${rec}</div>
            </div>
        `).join('');
        
        // Show results section
        document.getElementById('calculator-form').style.display = 'none';
        document.getElementById('results-section').style.display = 'block';
        
        // Track conversion
        this.trackConversion(results);
    }
    
    showLoadingState() {
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="loading-spinner"></span> Calculating...';
        }
    }
    
    hideLoadingState() {
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Calculate My Risk';
        }
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message global-error';
        errorDiv.textContent = message;
        
        this.form.insertBefore(errorDiv, this.form.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
    
    loadModal(modalId) {
        // Lazy load modal content
        fetch(`/api/modal/${modalId}`)
            .then(response => response.text())
            .then(html => {
                const modalContainer = document.getElementById('modal-container');
                if (modalContainer) {
                    modalContainer.innerHTML = html;
                }
            })
            .catch(error => {
                console.error('Failed to load modal:', error);
            });
    }
    
    loadImage(img) {
        // Lazy load image
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        img.classList.add('loaded');
    }
    
    trackConversion(results) {
        // Track successful assessment completion
        if (typeof gtag !== 'undefined') {
            gtag('event', 'assessment_completed', {
                'event_category': 'ai_calculator',
                'event_label': results.risk_level,
                'value': results.automation_score
            });
        }
        
        // Track performance metrics
        this.reportPerformanceMetrics();
    }
    
    reportPerformanceMetrics() {
        // Send performance metrics to analytics
        const metrics = {
            form_load_time: performanceMetrics.formLoadTime,
            calculation_time: performanceMetrics.calculationTime,
            submission_time: performanceMetrics.submissionTime,
            cache_hit_ratio: performanceMetrics.cacheHits / (performanceMetrics.cacheHits + performanceMetrics.cacheMisses),
            total_time: Date.now() - calculatorStartTime
        };
        
        // Send to analytics endpoint
        fetch('/api/analytics/performance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(metrics)
        }).catch(error => {
            console.debug('Failed to send performance metrics:', error);
        });
    }
}

// Mobile optimization
class MobileOptimizer {
    constructor() {
        this.isMobile = window.innerWidth <= 768;
        this.init();
    }
    
    init() {
        if (this.isMobile) {
            this.optimizeForMobile();
        }
        
        // Handle orientation changes
        window.addEventListener('resize', () => {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth <= 768;
            
            if (wasMobile !== this.isMobile) {
                this.optimizeForMobile();
            }
        });
    }
    
    optimizeForMobile() {
        // Reduce data usage for mobile
        this.optimizeImages();
        this.optimizeFonts();
        this.optimizeTouchTargets();
        this.enableOfflineSupport();
    }
    
    optimizeImages() {
        // Use smaller images for mobile
        const images = document.querySelectorAll('img[data-mobile-src]');
        images.forEach(img => {
            if (this.isMobile) {
                img.src = img.dataset.mobileSrc;
            }
        });
    }
    
    optimizeFonts() {
        // Load only essential fonts for mobile
        if (this.isMobile) {
            const fontLink = document.querySelector('link[href*="fonts.googleapis.com"]');
            if (fontLink) {
                fontLink.href = fontLink.href + '&display=swap&subset=latin';
            }
        }
    }
    
    optimizeTouchTargets() {
        // Ensure touch targets are at least 44px
        const touchTargets = document.querySelectorAll('button, a, input[type="submit"]');
        touchTargets.forEach(target => {
            if (target.offsetHeight < 44 || target.offsetWidth < 44) {
                target.style.minHeight = '44px';
                target.style.minWidth = '44px';
            }
        });
    }
    
    enableOfflineSupport() {
        // Enable offline assessment completion
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('Service Worker registered for offline support');
                })
                .catch(error => {
                    console.log('Service Worker registration failed:', error);
                });
        }
    }
}

// Progressive Web App features
class PWAFeatures {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupInstallPrompt();
        this.setupOfflineDetection();
        this.setupBackgroundSync();
    }
    
    setupInstallPrompt() {
        let deferredPrompt;
        
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            
            // Show install button
            const installButton = document.getElementById('install-app');
            if (installButton) {
                installButton.style.display = 'block';
                installButton.addEventListener('click', () => {
                    deferredPrompt.prompt();
                    deferredPrompt.userChoice.then((choiceResult) => {
                        if (choiceResult.outcome === 'accepted') {
                            console.log('User accepted the install prompt');
                        }
                        deferredPrompt = null;
                        installButton.style.display = 'none';
                    });
                });
            }
        });
    }
    
    setupOfflineDetection() {
        window.addEventListener('online', () => {
            document.body.classList.remove('offline');
            this.syncOfflineData();
        });
        
        window.addEventListener('offline', () => {
            document.body.classList.add('offline');
        });
    }
    
    setupBackgroundSync() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            navigator.serviceWorker.ready.then(registration => {
                // Register background sync for offline submissions
                registration.sync.register('offline-assessment-sync');
            });
        }
    }
    
    async syncOfflineData() {
        // Sync any offline assessment submissions
        const offlineData = localStorage.getItem('offline_assessments');
        if (offlineData) {
            try {
                const assessments = JSON.parse(offlineData);
                for (const assessment of assessments) {
                    await this.submitOfflineAssessment(assessment);
                }
                localStorage.removeItem('offline_assessments');
            } catch (error) {
                console.error('Failed to sync offline data:', error);
            }
        }
    }
    
    async submitOfflineAssessment(assessment) {
        try {
            await fetch('/api/ai-job-assessment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(assessment)
            });
        } catch (error) {
            console.error('Failed to submit offline assessment:', error);
        }
    }
}

// Initialize optimizations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize progressive form
    const calculatorForm = new ProgressiveForm('ai-calculator-form');
    
    // Initialize mobile optimization
    const mobileOptimizer = new MobileOptimizer();
    
    // Initialize PWA features
    const pwaFeatures = new PWAFeatures();
    
    // Track page load performance
    window.addEventListener('load', () => {
        const loadTime = Date.now() - calculatorStartTime;
        console.log(`Page loaded in ${loadTime}ms`);
        
        // Report Core Web Vitals
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.name === 'LCP') {
                        console.log('LCP:', entry.startTime);
                    } else if (entry.name === 'FID') {
                        console.log('FID:', entry.processingStart - entry.startTime);
                    } else if (entry.name === 'CLS') {
                        console.log('CLS:', entry.value);
                    }
                }
            });
            
            observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] });
        }
    });
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ProgressiveForm, MobileOptimizer, PWAFeatures };
}
