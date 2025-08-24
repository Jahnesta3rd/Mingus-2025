/**
 * MINGUS Landing Page JavaScript
 * Comprehensive functionality for assessment modals, animations, and analytics
 */

class MingusLandingPage {
    constructor() {
        this.isModalOpen = false;
        this.animationObserver = null;
        this.scrollObserver = null;
        this.animatedElements = new Set();
        
        // Assessment route mapping
        this.assessmentRoutes = {
            'income-comparison': '/assessment/income-comparison',
            'job-matching': '/assessment/job-matching',
            'relationship-money': '/assessment/relationship-money',
            'tax-impact': '/assessment/tax-impact'
        };
        
        // Analytics configuration
        this.analyticsConfig = {
            trackingId: window.GA_TRACKING_ID || 'G-XXXXXXXXXX',
            customEvents: {
                modalOpen: 'mingus_assessment_modal_open',
                assessmentSelect: 'mingus_assessment_selected',
                ctaClick: 'mingus_cta_click',
                scrollDepth: 'mingus_scroll_depth'
            }
        };
        
        this.init();
    }
    
    /**
     * Initialize all functionality
     */
    init() {
        this.setupEventListeners();
        this.setupIntersectionObservers();
        this.setupScrollEffects();
        this.setupMobileTouchInteractions();
        this.initializeAnalytics();
    }
    
    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Assessment trigger buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.assessment-trigger')) {
                e.preventDefault();
                this.openAssessmentModal();
            }
        });
        
        // Modal close events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeAssessmentModal();
            }
        });
        
        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isModalOpen) {
                this.closeAssessmentModal();
            }
        });
        
        // Assessment selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.assessment-option')) {
                e.preventDefault();
                const assessmentType = e.target.closest('.assessment-option').dataset.assessmentType;
                this.selectAssessment(assessmentType);
            }
        });
        
        // Smooth scrolling for anchor links
        document.addEventListener('click', (e) => {
            if (e.target.matches('a[href^="#"]')) {
                e.preventDefault();
                const targetId = e.target.getAttribute('href').substring(1);
                this.smoothScrollToElement(targetId);
            }
        });
        
        // FAQ toggle functionality
        document.addEventListener('click', (e) => {
            if (e.target.closest('.faq-toggle')) {
                e.preventDefault();
                this.toggleFAQ(e.target.closest('.faq-item'));
            }
        });
        
        // CTA tracking
        document.addEventListener('click', (e) => {
            if (e.target.closest('.cta-button')) {
                this.trackEvent(this.analyticsConfig.customEvents.ctaClick, {
                    button_text: e.target.textContent.trim(),
                    button_location: e.target.closest('section')?.className || 'unknown'
                });
            }
        });
    }
    
    /**
     * Setup intersection observers for animations
     */
    setupIntersectionObservers() {
        // Animation observer for fade-in elements
        this.animationObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !this.animatedElements.has(entry.target)) {
                    this.animatedElements.add(entry.target);
                    
                    // Add visible class to trigger animations
                    entry.target.classList.add('visible');
                    
                    // Special handling for different animation types
                    if (entry.target.classList.contains('progress-bar')) {
                        this.animateProgressBars();
                    } else if (entry.target.classList.contains('user-count')) {
                        this.animateUserCount();
                    } else if (entry.target.classList.contains('slide-in-left')) {
                        this.animateSlideInLeft(entry.target);
                    } else if (entry.target.classList.contains('slide-in-right')) {
                        this.animateSlideInRight(entry.target);
                    } else if (entry.target.classList.contains('scale-in')) {
                        this.animateScaleIn(entry.target);
                    }
                    
                    // Track animation event
                    this.trackEvent('mingus_animation_triggered', {
                        animation_type: this.getAnimationType(entry.target),
                        element_type: entry.target.tagName.toLowerCase(),
                        element_class: entry.target.className
                    });
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        // Observe all animated elements
        const animatedElements = document.querySelectorAll(
            '.fade-in, .slide-in-left, .slide-in-right, .scale-in, .progress-bar, .user-count'
        );
        
        animatedElements.forEach(el => {
            this.animationObserver.observe(el);
        });
        
        // Setup staggered animations for lists and grids
        this.setupStaggeredAnimations();
    }
    
    /**
     * Setup staggered animations for lists and grids
     */
    setupStaggeredAnimations() {
        const staggeredContainers = document.querySelectorAll('.features-grid, .testimonials-grid, .assessment-options');
        
        staggeredContainers.forEach(container => {
            const items = container.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right, .scale-in');
            
            items.forEach((item, index) => {
                item.style.transitionDelay = `${index * 0.1}s`;
            });
        });
    }
    
    /**
     * Get animation type for tracking
     */
    getAnimationType(element) {
        if (element.classList.contains('fade-in')) return 'fade-in';
        if (element.classList.contains('slide-in-left')) return 'slide-in-left';
        if (element.classList.contains('slide-in-right')) return 'slide-in-right';
        if (element.classList.contains('scale-in')) return 'scale-in';
        if (element.classList.contains('progress-bar')) return 'progress-bar';
        if (element.classList.contains('user-count')) return 'user-count';
        return 'unknown';
    }
    
    /**
     * Animate slide in from left
     */
    animateSlideInLeft(element) {
        element.style.transform = 'translateX(0)';
        element.style.opacity = '1';
    }
    
    /**
     * Animate slide in from right
     */
    animateSlideInRight(element) {
        element.style.transform = 'translateX(0)';
        element.style.opacity = '1';
    }
    
    /**
     * Animate scale in
     */
    animateScaleIn(element) {
        element.style.transform = 'scale(1)';
        element.style.opacity = '1';
    }
    
    /**
     * Setup scroll effects
     */
    setupScrollEffects() {
        let scrollDepth = 0;
        const scrollThresholds = [25, 50, 75, 90];
        const trackedDepths = new Set();
        
        window.addEventListener('scroll', this.debounce(() => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercent = Math.round((scrollTop / docHeight) * 100);
            
            // Header background opacity
            const header = document.querySelector('.header');
            if (header) {
                if (scrollTop > 100) {
                    header.classList.add('header-scrolled');
                } else {
                    header.classList.remove('header-scrolled');
                }
            }
            
            // Track scroll depth
            scrollThresholds.forEach(threshold => {
                if (scrollPercent >= threshold && !trackedDepths.has(threshold)) {
                    trackedDepths.add(threshold);
                    this.trackEvent(this.analyticsConfig.customEvents.scrollDepth, {
                        scroll_percentage: threshold
                    });
                }
            });
        }, 100));
    }
    
    /**
     * Setup mobile touch interactions
     */
    setupMobileTouchInteractions() {
        let touchStartY = 0;
        let touchEndY = 0;
        
        // Touch start
        document.addEventListener('touchstart', (e) => {
            touchStartY = e.changedTouches[0].screenY;
        }, { passive: true });
        
        // Touch end
        document.addEventListener('touchend', (e) => {
            touchEndY = e.changedTouches[0].screenY;
            this.handleSwipeGesture(touchStartY, touchEndY);
        }, { passive: true });
        
        // Prevent zoom on double tap
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (e) => {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    }
    
    /**
     * Handle swipe gestures
     */
    handleSwipeGesture(startY, endY) {
        const swipeThreshold = 50;
        const diff = startY - endY;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                // Swipe up - could trigger assessment modal
                if (this.isModalOpen) {
                    this.closeAssessmentModal();
                }
            } else {
                // Swipe down - could open assessment modal
                if (!this.isModalOpen) {
                    this.openAssessmentModal();
                }
            }
        }
    }
    
    /**
     * Assessment Modal Functions
     */
    
    /**
     * Open assessment modal with enhanced animations
     */
    openAssessmentModal() {
        try {
            const modal = document.getElementById('assessment-modal');
            if (!modal) {
                console.error('Assessment modal not found');
                return;
            }
            
            // Show modal overlay
            modal.classList.add('modal-active');
            document.body.classList.add('modal-open');
            this.isModalOpen = true;
            
            // Focus management
            const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
            
            // Track event
            this.trackEvent(this.analyticsConfig.customEvents.modalOpen, {
                modal_type: 'assessment_selection',
                trigger_location: 'landing_page'
            });
            
            // Add entrance animation with requestAnimationFrame
            requestAnimationFrame(() => {
                modal.classList.add('modal-entered');
                
                // Animate assessment options with stagger
                const options = modal.querySelectorAll('.assessment-option');
                options.forEach((option, index) => {
                    setTimeout(() => {
                        option.style.opacity = '0';
                        option.style.transform = 'translateY(20px)';
                        
                        requestAnimationFrame(() => {
                            option.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
                            option.style.opacity = '1';
                            option.style.transform = 'translateY(0)';
                        });
                    }, index * 100);
                });
            });
            
        } catch (error) {
            console.error('Error opening assessment modal:', error);
        }
    }
    
    /**
     * Close assessment modal with enhanced animations
     */
    closeAssessmentModal() {
        try {
            const modal = document.getElementById('assessment-modal');
            if (!modal) return;
            
            // Animate assessment options out
            const options = modal.querySelectorAll('.assessment-option');
            options.forEach((option, index) => {
                setTimeout(() => {
                    option.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                    option.style.opacity = '0';
                    option.style.transform = 'translateY(-20px)';
                }, index * 50);
            });
            
            // Remove entrance animation
            setTimeout(() => {
                modal.classList.remove('modal-entered');
                
                // Hide modal after animation
                setTimeout(() => {
                    modal.classList.remove('modal-active');
                    document.body.classList.remove('modal-open');
                    this.isModalOpen = false;
                    
                    // Reset option animations
                    options.forEach(option => {
                        option.style.transition = '';
                        option.style.opacity = '';
                        option.style.transform = '';
                    });
                    
                    // Return focus to trigger element
                    const trigger = document.querySelector('.assessment-trigger:focus');
                    if (trigger) {
                        trigger.focus();
                    }
                }, 300);
            }, 200);
            
        } catch (error) {
            console.error('Error closing assessment modal:', error);
        }
    }
    
    /**
     * Select assessment type
     */
    selectAssessment(assessmentType) {
        try {
            // Validate assessment type
            if (!this.assessmentRoutes[assessmentType]) {
                console.error('Invalid assessment type:', assessmentType);
                return;
            }
            
            // Track selection
            this.trackEvent(this.analyticsConfig.customEvents.assessmentSelect, {
                assessment_type: assessmentType,
                assessment_name: this.getAssessmentDisplayName(assessmentType)
            });
            
            // Close modal
            this.closeAssessmentModal();
            
            // Route to assessment
            setTimeout(() => {
                window.location.href = this.assessmentRoutes[assessmentType];
            }, 350);
            
        } catch (error) {
            console.error('Error selecting assessment:', error);
        }
    }
    
    /**
     * Get assessment display name
     */
    getAssessmentDisplayName(assessmentType) {
        const names = {
            'income-comparison': 'Income Comparison Calculator',
            'job-matching': 'AI Job Lead Magnet',
            'relationship-money': 'Relationship & Money Score',
            'tax-impact': 'Tax Bill Impact Calculator'
        };
        return names[assessmentType] || assessmentType;
    }
    
    /**
     * Animation Functions
     */
    
    /**
     * Animate progress bars with shimmer effect
     */
    animateProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar');
        
        progressBars.forEach((bar, index) => {
            const targetWidth = bar.getAttribute('data-progress') || '0';
            const delay = index * 200; // Stagger animation
            
            setTimeout(() => {
                // Add animating class for shimmer effect
                bar.classList.add('animating');
                bar.style.width = '0%';
                bar.style.opacity = '1';
                
                // Animate to target width with easing
                setTimeout(() => {
                    bar.style.transition = 'width 1s ease-in-out';
                    bar.style.width = targetWidth + '%';
                    
                    // Remove animating class after animation completes
                    setTimeout(() => {
                        bar.classList.remove('animating');
                        bar.classList.add('animate');
                    }, 1000);
                }, 100);
            }, delay);
        });
    }
    
    /**
     * Animate user count numbers with bounce effect
     */
    animateUserCount() {
        const userCounts = document.querySelectorAll('.user-count');
        
        userCounts.forEach((element, index) => {
            const targetNumber = parseInt(element.getAttribute('data-count') || '0');
            const delay = index * 300; // Stagger animation
            const duration = 2000; // 2 seconds
            const startTime = Date.now();
            
            setTimeout(() => {
                // Add animating class for bounce effect
                element.classList.add('animating');
                
                const animate = () => {
                    const elapsed = Date.now() - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    
                    // Easing function for smooth animation
                    const easeOutQuart = 1 - Math.pow(1 - progress, 4);
                    const currentNumber = Math.floor(targetNumber * easeOutQuart);
                    
                    element.textContent = this.formatNumber(currentNumber);
                    
                    if (progress < 1) {
                        requestAnimationFrame(animate);
                    } else {
                        element.textContent = this.formatNumber(targetNumber);
                        element.classList.remove('animating');
                        element.classList.add('counted');
                        
                        // Track completion
                        this.trackEvent('mingus_counter_completed', {
                            target_number: targetNumber,
                            element_id: element.id || 'unknown'
                        });
                    }
                };
                
                animate();
            }, delay);
        });
    }
    
    /**
     * Toggle FAQ item with enhanced animations
     */
    toggleFAQ(faqItem) {
        if (!faqItem) return;
        
        const isExpanded = faqItem.classList.contains('faq-expanded');
        const content = faqItem.querySelector('.faq-content');
        const icon = faqItem.querySelector('.faq-icon');
        
        // Track FAQ interaction
        this.trackEvent('mingus_faq_toggle', {
            action: isExpanded ? 'close' : 'open',
            question: faqItem.querySelector('.faq-toggle')?.textContent?.trim() || 'unknown'
        });
        
        // Close other FAQ items with smooth animation
        document.querySelectorAll('.faq-item.faq-expanded').forEach(item => {
            if (item !== faqItem) {
                this.closeFAQItem(item);
            }
        });
        
        // Toggle current item
        if (isExpanded) {
            this.closeFAQItem(faqItem);
        } else {
            this.openFAQItem(faqItem);
        }
    }
    
    /**
     * Open FAQ item with animation
     */
    openFAQItem(faqItem) {
        const content = faqItem.querySelector('.faq-content');
        const icon = faqItem.querySelector('.faq-icon');
        
        // Add expanded class
        faqItem.classList.add('faq-expanded');
        
        // Animate content
        if (content) {
            // Set initial state
            content.style.maxHeight = '0px';
            content.style.opacity = '0';
            content.style.transform = 'translateY(-10px)';
            
            // Trigger animation
            requestAnimationFrame(() => {
                content.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                content.style.maxHeight = content.scrollHeight + 'px';
                content.style.opacity = '1';
                content.style.transform = 'translateY(0)';
            });
        }
        
        // Animate icon
        if (icon) {
            icon.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            icon.style.transform = 'rotate(180deg)';
        }
        
        // Add hover effect
        faqItem.style.borderColor = 'rgba(102, 126, 234, 0.5)';
        faqItem.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.1)';
    }
    
    /**
     * Close FAQ item with animation
     */
    closeFAQItem(faqItem) {
        const content = faqItem.querySelector('.faq-content');
        const icon = faqItem.querySelector('.faq-icon');
        
        // Remove expanded class
        faqItem.classList.remove('faq-expanded');
        
        // Animate content
        if (content) {
            content.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            content.style.maxHeight = '0px';
            content.style.opacity = '0';
            content.style.transform = 'translateY(-10px)';
        }
        
        // Animate icon
        if (icon) {
            icon.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            icon.style.transform = 'rotate(0deg)';
        }
        
        // Remove hover effect
        faqItem.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        faqItem.style.boxShadow = 'none';
    }
    
    /**
     * Utility Functions
     */
    
    /**
     * Smooth scroll to element
     */
    smoothScrollToElement(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const headerHeight = document.querySelector('.header')?.offsetHeight || 0;
        const targetPosition = element.offsetTop - headerHeight - 20;
        
        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    }
    
    /**
     * Format number with commas
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
    
    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Analytics Integration
     */
    
    /**
     * Initialize analytics
     */
    initializeAnalytics() {
        // Check if gtag is available
        if (typeof gtag !== 'undefined') {
            console.log('Google Analytics initialized');
        } else {
            console.warn('Google Analytics not loaded');
        }
    }
    
    /**
     * Track custom events
     */
    trackEvent(eventName, parameters = {}) {
        try {
            // Google Analytics 4
            if (typeof gtag !== 'undefined') {
                gtag('event', eventName, {
                    event_category: 'mingus_landing_page',
                    event_label: parameters.event_label || 'landing_page',
                    ...parameters
                });
            }
            
            // Custom analytics tracking
            const eventData = {
                event: eventName,
                timestamp: new Date().toISOString(),
                url: window.location.href,
                user_agent: navigator.userAgent,
                ...parameters
            };
            
            // Send to custom analytics endpoint if available
            if (window.MINGUS_ANALYTICS_ENDPOINT) {
                fetch(window.MINGUS_ANALYTICS_ENDPOINT, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(eventData)
                }).catch(error => {
                    console.warn('Analytics tracking failed:', error);
                });
            }
            
            console.log('Event tracked:', eventName, parameters);
            
        } catch (error) {
            console.error('Error tracking event:', error);
        }
    }
    
    /**
     * Performance and Error Handling
     */
    
    /**
     * Performance monitoring and optimization
     */
    monitorPerformance() {
        // Monitor Core Web Vitals
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.entryType === 'largest-contentful-paint') {
                        this.trackEvent('mingus_lcp', {
                            lcp_value: entry.startTime
                        });
                    }
                }
            });
            
            observer.observe({ entryTypes: ['largest-contentful-paint'] });
        }
        
        // Monitor memory usage
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                if (memory.usedJSHeapSize > memory.jsHeapSizeLimit * 0.8) {
                    console.warn('High memory usage detected');
                    this.optimizeMemoryUsage();
                }
            }, 30000);
        }
        
        // Monitor animation performance
        this.monitorAnimationPerformance();
    }
    
    /**
     * Monitor animation performance
     */
    monitorAnimationPerformance() {
        let frameCount = 0;
        let lastTime = performance.now();
        
        const checkFrameRate = (currentTime) => {
            frameCount++;
            
            if (currentTime - lastTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                
                if (fps < 30) {
                    console.warn('Low animation frame rate detected:', fps);
                    this.optimizeAnimations();
                }
                
                frameCount = 0;
                lastTime = currentTime;
            }
            
            requestAnimationFrame(checkFrameRate);
        };
        
        requestAnimationFrame(checkFrameRate);
    }
    
    /**
     * Optimize memory usage
     */
    optimizeMemoryUsage() {
        // Clear animation observers for off-screen elements
        const offScreenElements = document.querySelectorAll('.fade-in:not(.visible), .slide-in-left:not(.visible), .slide-in-right:not(.visible)');
        
        offScreenElements.forEach(element => {
            if (this.animationObserver) {
                this.animationObserver.unobserve(element);
            }
        });
        
        // Clear unused event listeners
        this.cleanupEventListeners();
    }
    
    /**
     * Optimize animations for performance
     */
    optimizeAnimations() {
        // Reduce animation complexity on low-end devices
        const isLowEndDevice = navigator.hardwareConcurrency <= 2 || 
                              navigator.deviceMemory <= 4;
        
        if (isLowEndDevice) {
            document.body.classList.add('reduced-animations');
            
            // Disable complex animations
            const complexAnimations = document.querySelectorAll('.shimmer, .glow, .pulse');
            complexAnimations.forEach(element => {
                element.style.animation = 'none';
            });
        }
    }
    
    /**
     * Cleanup event listeners
     */
    cleanupEventListeners() {
        // Remove unused event listeners to prevent memory leaks
        const elements = document.querySelectorAll('[data-event-cleanup]');
        elements.forEach(element => {
            element.removeEventListener('click', element._clickHandler);
            element.removeEventListener('touchstart', element._touchHandler);
        });
    }
    
    /**
     * Error handling
     */
    setupErrorHandling() {
        window.addEventListener('error', (e) => {
            console.error('JavaScript error:', e.error);
            this.trackEvent('mingus_error', {
                error_message: e.message,
                error_filename: e.filename,
                error_lineno: e.lineno
            });
        });
        
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled promise rejection:', e.reason);
            this.trackEvent('mingus_promise_error', {
                error_message: e.reason
            });
        });
    }
}

/**
 * Initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    try {
        // Initialize landing page functionality
        window.mingusLandingPage = new MingusLandingPage();
        
        // Setup performance monitoring
        window.mingusLandingPage.monitorPerformance();
        
        // Setup error handling
        window.mingusLandingPage.setupErrorHandling();
        
        console.log('MINGUS Landing Page initialized successfully');
        
    } catch (error) {
        console.error('Error initializing MINGUS Landing Page:', error);
    }
});

/**
 * Export for module usage
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MingusLandingPage;
}
