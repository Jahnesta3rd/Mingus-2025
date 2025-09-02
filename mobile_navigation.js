/**
 * MINGUS Mobile Navigation Implementation
 * Comprehensive mobile navigation and interaction system
 * Fixes for all identified mobile responsive issues
 */

class MobileNavigation {
    constructor() {
        this.mobileMenuBtn = document.querySelector('.mobile-menu-btn');
        this.navLinks = document.querySelector('.nav-links');
        this.modalContainer = document.querySelector('#modal-container');
        this.modalOverlay = document.querySelector('.modal-overlay');
        this.modalContent = document.querySelector('.modal-content');
        this.modalClose = document.querySelector('.modal-close');
        this.isMenuOpen = false;
        this.isModalOpen = false;
        this.touchStartY = 0;
        this.touchEndY = 0;
        this.touchStartX = 0;
        this.touchEndX = 0;
        this.scrollPosition = 0;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupTouchGestures();
        this.setupKeyboardNavigation();
        this.setupAccessibility();
        this.setupModalHandling();
        this.setupResizeHandling();
        this.setupOrientationHandling();
    }
    
    setupEventListeners() {
        // Mobile menu toggle
        if (this.mobileMenuBtn) {
            this.mobileMenuBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleMobileMenu();
            });
            
            // Update ARIA attributes
            this.mobileMenuBtn.setAttribute('aria-expanded', 'false');
            this.mobileMenuBtn.setAttribute('aria-controls', 'nav-links');
            this.mobileMenuBtn.setAttribute('aria-label', 'Toggle mobile menu');
        }
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isMenuOpen && 
                !this.navLinks.contains(e.target) && 
                !this.mobileMenuBtn.contains(e.target)) {
                this.closeMobileMenu();
            }
        });
        
        // Close menu on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (this.isMenuOpen) {
                    this.closeMobileMenu();
                }
                if (this.isModalOpen) {
                    this.closeModal();
                }
            }
        });
        
        // Handle navigation link clicks
        if (this.navLinks) {
            this.navLinks.addEventListener('click', (e) => {
                if (e.target.tagName === 'A') {
                    // Close mobile menu when a link is clicked
                    setTimeout(() => {
                        this.closeMobileMenu();
                    }, 100);
                }
            });
        }
        
        // Prevent body scroll when menu is open
        document.addEventListener('touchmove', (e) => {
            if (this.isMenuOpen) {
                e.preventDefault();
            }
        }, { passive: false });
    }
    
    setupTouchGestures() {
        // Swipe to close menu
        if (this.navLinks) {
            this.navLinks.addEventListener('touchstart', (e) => {
                this.touchStartY = e.touches[0].clientY;
                this.touchStartX = e.touches[0].clientX;
            });
            
            this.navLinks.addEventListener('touchmove', (e) => {
                this.touchEndY = e.touches[0].clientY;
                this.touchEndX = e.touches[0].clientX;
            });
            
            this.navLinks.addEventListener('touchend', () => {
                const swipeDistanceY = this.touchStartY - this.touchEndY;
                const swipeDistanceX = this.touchStartX - this.touchEndX;
                const minSwipeDistance = 50;
                
                // Swipe down to close menu
                if (swipeDistanceY < -minSwipeDistance && this.isMenuOpen) {
                    this.closeMobileMenu();
                }
                
                // Swipe left to close menu
                if (swipeDistanceX < -minSwipeDistance && this.isMenuOpen) {
                    this.closeMobileMenu();
                }
            });
        }
        
        // Touch feedback for buttons
        const touchElements = document.querySelectorAll('.btn, .mobile-menu-btn, .nav-links a');
        touchElements.forEach(element => {
            element.addEventListener('touchstart', () => {
                element.style.transform = 'scale(0.95)';
            });
            
            element.addEventListener('touchend', () => {
                element.style.transform = '';
            });
        });
    }
    
    setupKeyboardNavigation() {
        // Handle keyboard navigation within menu
        if (this.navLinks) {
            const menuItems = this.navLinks.querySelectorAll('a');
            
            menuItems.forEach((item, index) => {
                item.addEventListener('keydown', (e) => {
                    switch (e.key) {
                        case 'ArrowDown':
                            e.preventDefault();
                            const nextItem = menuItems[index + 1] || menuItems[0];
                            nextItem.focus();
                            break;
                        case 'ArrowUp':
                            e.preventDefault();
                            const prevItem = menuItems[index - 1] || menuItems[menuItems.length - 1];
                            prevItem.focus();
                            break;
                        case 'Home':
                            e.preventDefault();
                            menuItems[0].focus();
                            break;
                        case 'End':
                            e.preventDefault();
                            menuItems[menuItems.length - 1].focus();
                            break;
                    }
                });
            });
        }
        
        // Trap focus in mobile menu when open
        document.addEventListener('keydown', (e) => {
            if (this.isMenuOpen && e.key === 'Tab') {
                const focusableElements = this.navLinks.querySelectorAll(
                    'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
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
    }
    
    setupAccessibility() {
        // Add ARIA labels and roles
        if (this.mobileMenuBtn) {
            this.mobileMenuBtn.setAttribute('role', 'button');
            this.mobileMenuBtn.setAttribute('aria-haspopup', 'true');
        }
        
        if (this.navLinks) {
            this.navLinks.setAttribute('role', 'menu');
            this.navLinks.setAttribute('aria-label', 'Main navigation menu');
            
            const menuItems = this.navLinks.querySelectorAll('li');
            menuItems.forEach(item => {
                item.setAttribute('role', 'none');
                const link = item.querySelector('a');
                if (link) {
                    link.setAttribute('role', 'menuitem');
                }
            });
        }
        
        // Announce menu state changes to screen readers
        this.announceToScreenReader = (message) => {
            const announcement = document.createElement('div');
            announcement.setAttribute('aria-live', 'polite');
            announcement.setAttribute('aria-atomic', 'true');
            announcement.className = 'sr-only';
            announcement.textContent = message;
            document.body.appendChild(announcement);
            
            setTimeout(() => {
                document.body.removeChild(announcement);
            }, 1000);
        };
    }
    
    setupModalHandling() {
        // Modal open/close functionality
        if (this.modalContainer) {
            // Close modal when clicking overlay
            if (this.modalOverlay) {
                this.modalOverlay.addEventListener('click', () => {
                    this.closeModal();
                });
            }
            
            // Close modal with close button
            if (this.modalClose) {
                this.modalClose.addEventListener('click', () => {
                    this.closeModal();
                });
            }
            
            // Prevent modal content clicks from closing modal
            if (this.modalContent) {
                this.modalContent.addEventListener('click', (e) => {
                    e.stopPropagation();
                });
            }
        }
        
        // Global modal open function
        window.openModal = (content, options = {}) => {
            this.openModal(content, options);
        };
        
        // Global modal close function
        window.closeModal = () => {
            this.closeModal();
        };
    }
    
    setupResizeHandling() {
        // Handle window resize
        window.addEventListener('resize', () => {
            // Close mobile menu on larger screens
            if (window.innerWidth > 768 && this.isMenuOpen) {
                this.closeMobileMenu();
            }
            
            // Recalculate modal positioning
            if (this.isModalOpen) {
                this.repositionModal();
            }
        });
    }
    
    setupOrientationHandling() {
        // Handle orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                // Close mobile menu on orientation change
                if (window.innerWidth > 768 && this.isMenuOpen) {
                    this.closeMobileMenu();
                }
                
                // Reposition modal after orientation change
                if (this.isModalOpen) {
                    this.repositionModal();
                }
                
                // Announce orientation change to screen readers
                this.announceToScreenReader('Orientation changed');
            }, 100);
        });
    }
    
    toggleMobileMenu() {
        if (this.isMenuOpen) {
            this.closeMobileMenu();
        } else {
            this.openMobileMenu();
        }
    }
    
    openMobileMenu() {
        if (!this.navLinks || !this.mobileMenuBtn) return;
        
        this.isMenuOpen = true;
        this.navLinks.classList.add('active');
        this.mobileMenuBtn.classList.add('active');
        this.mobileMenuBtn.setAttribute('aria-expanded', 'true');
        
        // Store scroll position
        this.scrollPosition = window.pageYOffset;
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        document.body.style.position = 'fixed';
        document.body.style.top = `-${this.scrollPosition}px`;
        document.body.style.width = '100%';
        
        // Focus first menu item
        const firstMenuItem = this.navLinks.querySelector('a');
        if (firstMenuItem) {
            setTimeout(() => {
                firstMenuItem.focus();
            }, 100);
        }
        
        // Announce to screen readers
        this.announceToScreenReader('Mobile menu opened');
        
        // Add escape key listener
        this.escapeListener = (e) => {
            if (e.key === 'Escape') {
                this.closeMobileMenu();
            }
        };
        document.addEventListener('keydown', this.escapeListener);
    }
    
    closeMobileMenu() {
        if (!this.navLinks || !this.mobileMenuBtn) return;
        
        this.isMenuOpen = false;
        this.navLinks.classList.remove('active');
        this.mobileMenuBtn.classList.remove('active');
        this.mobileMenuBtn.setAttribute('aria-expanded', 'false');
        
        // Restore body scroll
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        window.scrollTo(0, this.scrollPosition);
        
        // Return focus to menu button
        this.mobileMenuBtn.focus();
        
        // Announce to screen readers
        this.announceToScreenReader('Mobile menu closed');
        
        // Remove escape key listener
        if (this.escapeListener) {
            document.removeEventListener('keydown', this.escapeListener);
        }
    }
    
    openModal(content, options = {}) {
        if (!this.modalContainer) return;
        
        this.isModalOpen = true;
        
        // Set modal content
        const modalBody = this.modalContainer.querySelector('.modal-body');
        if (modalBody) {
            if (typeof content === 'string') {
                modalBody.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                modalBody.innerHTML = '';
                modalBody.appendChild(content);
            }
        }
        
        // Apply options
        if (options.className) {
            this.modalContent.className = `modal-content ${options.className}`;
        }
        
        if (options.size) {
            this.modalContent.classList.add(`modal-${options.size}`);
        }
        
        // Show modal
        this.modalContainer.style.display = 'flex';
        this.modalContainer.setAttribute('aria-hidden', 'false');
        
        // Focus management
        setTimeout(() => {
            // Focus first focusable element in modal
            const focusableElements = this.modalContent.querySelectorAll(
                'button, input, select, textarea, a, [tabindex]:not([tabindex="-1"])'
            );
            if (focusableElements.length > 0) {
                focusableElements[0].focus();
            } else {
                this.modalClose.focus();
            }
        }, 100);
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        
        // Announce to screen readers
        this.announceToScreenReader('Modal opened');
        
        // Add escape key listener
        this.modalEscapeListener = (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        };
        document.addEventListener('keydown', this.modalEscapeListener);
    }
    
    closeModal() {
        if (!this.modalContainer) return;
        
        this.isModalOpen = false;
        
        // Hide modal
        this.modalContainer.style.display = 'none';
        this.modalContainer.setAttribute('aria-hidden', 'true');
        
        // Clear content
        const modalBody = this.modalContainer.querySelector('.modal-body');
        if (modalBody) {
            modalBody.innerHTML = '';
        }
        
        // Reset modal classes
        this.modalContent.className = 'modal-content';
        
        // Restore body scroll
        document.body.style.overflow = '';
        
        // Announce to screen readers
        this.announceToScreenReader('Modal closed');
        
        // Remove escape key listener
        if (this.modalEscapeListener) {
            document.removeEventListener('keydown', this.modalEscapeListener);
        }
    }
    
    repositionModal() {
        if (!this.modalContent || !this.isModalOpen) return;
        
        // Ensure modal is properly positioned
        this.modalContent.style.top = '50%';
        this.modalContent.style.left = '50%';
        this.modalContent.style.transform = 'translate(-50%, -50%)';
    }
}

// Subscription Modal Handler
class SubscriptionModal {
    constructor() {
        this.tierCards = document.querySelectorAll('.tier-card');
        this.selectedTier = null;
        this.init();
    }
    
    init() {
        this.setupTierSelection();
        this.setupPaymentHandling();
    }
    
    setupTierSelection() {
        this.tierCards.forEach(card => {
            card.addEventListener('click', () => {
                this.selectTier(card);
            });
            
            // Keyboard support
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.selectTier(card);
                }
            });
            
            // Make cards focusable
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'button');
            card.setAttribute('aria-pressed', 'false');
        });
    }
    
    selectTier(card) {
        // Remove previous selection
        this.tierCards.forEach(c => {
            c.classList.remove('selected');
            c.setAttribute('aria-pressed', 'false');
        });
        
        // Select new tier
        card.classList.add('selected');
        card.setAttribute('aria-pressed', 'true');
        this.selectedTier = card.dataset.tier;
        
        // Focus the button in the selected card
        const button = card.querySelector('button');
        if (button) {
            button.focus();
        }
    }
    
    setupPaymentHandling() {
        // Handle payment button clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.tier-card button')) {
                e.preventDefault();
                this.processPayment(e.target);
            }
        });
    }
    
    processPayment(button) {
        const card = button.closest('.tier-card');
        const tier = card.dataset.tier;
        const amount = card.dataset.amount;
        
        if (!tier || !amount) {
            console.error('Missing tier or amount data');
            return;
        }
        
        // Show loading state
        button.disabled = true;
        button.textContent = 'Processing...';
        
        // Simulate payment processing
        setTimeout(() => {
            // Reset button
            button.disabled = false;
            button.textContent = `Subscribe $${amount}`;
            
            // Show success message
            this.showSuccessMessage(tier, amount);
        }, 2000);
    }
    
    showSuccessMessage(tier, amount) {
        const message = `
            <div class="success-message">
                <h3>Thank you for subscribing!</h3>
                <p>You have successfully subscribed to the ${tier} plan for $${amount}/month.</p>
                <button class="btn btn-primary" onclick="window.closeModal()">Continue</button>
            </div>
        `;
        
        // Update modal content
        const modalBody = document.querySelector('.modal-body');
        if (modalBody) {
            modalBody.innerHTML = message;
        }
    }
}

// Form Validation Handler
class MobileFormValidation {
    constructor() {
        this.forms = document.querySelectorAll('form');
        this.init();
    }
    
    init() {
        this.setupFormValidation();
        this.setupInputHandling();
    }
    
    setupFormValidation() {
        this.forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });
            
            // Real-time validation
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });
                
                input.addEventListener('input', () => {
                    this.clearFieldError(input);
                });
            });
        });
    }
    
    setupInputHandling() {
        // Prevent zoom on iOS for number inputs
        const numberInputs = document.querySelectorAll('input[type="number"]');
        numberInputs.forEach(input => {
            input.addEventListener('focus', () => {
                input.style.fontSize = '16px';
            });
        });
        
        // Auto-resize textareas
        const textareas = document.querySelectorAll('textarea');
        textareas.forEach(textarea => {
            textarea.addEventListener('input', () => {
                textarea.style.height = 'auto';
                textarea.style.height = textarea.scrollHeight + 'px';
            });
        });
    }
    
    validateForm(form) {
        let isValid = true;
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        const required = field.hasAttribute('required');
        
        // Clear previous errors
        this.clearFieldError(field);
        
        // Check required fields
        if (required && !value) {
            this.showFieldError(field, 'This field is required');
            return false;
        }
        
        // Email validation
        if (type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                this.showFieldError(field, 'Please enter a valid email address');
                return false;
            }
        }
        
        // Number validation
        if (type === 'number' && value) {
            const numValue = parseFloat(value);
            if (isNaN(numValue)) {
                this.showFieldError(field, 'Please enter a valid number');
                return false;
            }
            
            const min = field.getAttribute('min');
            const max = field.getAttribute('max');
            
            if (min && numValue < parseFloat(min)) {
                this.showFieldError(field, `Value must be at least ${min}`);
                return false;
            }
            
            if (max && numValue > parseFloat(max)) {
                this.showFieldError(field, `Value must be no more than ${max}`);
                return false;
            }
        }
        
        return true;
    }
    
    showFieldError(field, message) {
        field.classList.add('error');
        
        // Create error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.textContent = message;
        errorDiv.setAttribute('role', 'alert');
        
        // Insert after field
        field.parentNode.insertBefore(errorDiv, field.nextSibling);
    }
    
    clearFieldError(field) {
        field.classList.remove('error');
        
        // Remove error message
        const errorDiv = field.parentNode.querySelector('.form-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
}

// Touch Gesture Handler
class TouchGestureHandler {
    constructor() {
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.minSwipeDistance = 50;
        this.init();
    }
    
    init() {
        this.setupTouchListeners();
    }
    
    setupTouchListeners() {
        // Global touch start
        document.addEventListener('touchstart', (e) => {
            this.touchStartX = e.touches[0].clientX;
            this.touchStartY = e.touches[0].clientY;
        });
        
        // Global touch end
        document.addEventListener('touchend', (e) => {
            this.touchEndX = e.changedTouches[0].clientX;
            this.touchEndY = e.changedTouches[0].clientY;
            
            this.handleSwipe();
        });
        
        // Prevent default touch behaviors that might interfere
        document.addEventListener('touchmove', (e) => {
            // Allow scrolling but prevent other default behaviors
            if (e.target.closest('.modal-content') || e.target.closest('.nav-links')) {
                // Allow scrolling within modals and nav
                return;
            }
        }, { passive: true });
    }
    
    handleSwipe() {
        const deltaX = this.touchEndX - this.touchStartX;
        const deltaY = this.touchEndY - this.touchStartY;
        
        // Determine swipe direction
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            // Horizontal swipe
            if (Math.abs(deltaX) > this.minSwipeDistance) {
                if (deltaX > 0) {
                    this.handleSwipeRight();
                } else {
                    this.handleSwipeLeft();
                }
            }
        } else {
            // Vertical swipe
            if (Math.abs(deltaY) > this.minSwipeDistance) {
                if (deltaY > 0) {
                    this.handleSwipeDown();
                } else {
                    this.handleSwipeUp();
                }
            }
        }
    }
    
    handleSwipeLeft() {
        // Close mobile menu
        if (window.mobileNav && window.mobileNav.isMenuOpen) {
            window.mobileNav.closeMobileMenu();
        }
    }
    
    handleSwipeRight() {
        // Could be used for navigation or other gestures
    }
    
    handleSwipeDown() {
        // Close mobile menu
        if (window.mobileNav && window.mobileNav.isMenuOpen) {
            window.mobileNav.closeMobileMenu();
        }
    }
    
    handleSwipeUp() {
        // Could be used for navigation or other gestures
    }
}

// Performance Optimizer
class MobilePerformanceOptimizer {
    constructor() {
        this.init();
    }
    
    init() {
        this.optimizeImages();
        this.setupLazyLoading();
        this.optimizeAnimations();
    }
    
    optimizeImages() {
        // Add loading="lazy" to images
        const images = document.querySelectorAll('img:not([loading])');
        images.forEach(img => {
            img.setAttribute('loading', 'lazy');
        });
        
        // Optimize image sizes for mobile
        if (window.innerWidth <= 768) {
            images.forEach(img => {
                const src = img.src;
                if (src && !src.includes('mobile')) {
                    // Could implement responsive image loading here
                }
            });
        }
    }
    
    setupLazyLoading() {
        // Intersection Observer for lazy loading
        if ('IntersectionObserver' in window) {
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
            
            const lazyImages = document.querySelectorAll('img[data-src]');
            lazyImages.forEach(img => imageObserver.observe(img));
        }
    }
    
    optimizeAnimations() {
        // Reduce animations on mobile for better performance
        if (window.innerWidth <= 768) {
            document.documentElement.style.setProperty('--transition', '0.2s ease');
        }
        
        // Respect reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.documentElement.style.setProperty('--transition', '0.01s ease');
        }
    }
}

// Initialize all mobile functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize mobile navigation
    window.mobileNav = new MobileNavigation();
    
    // Initialize subscription modal
    window.subscriptionModal = new SubscriptionModal();
    
    // Initialize form validation
    window.formValidation = new MobileFormValidation();
    
    // Initialize touch gestures
    window.touchHandler = new TouchGestureHandler();
    
    // Initialize performance optimizer
    window.performanceOptimizer = new MobilePerformanceOptimizer();
    
    // Add mobile-specific classes to body
    document.body.classList.add('mobile-ready');
    
    // Announce mobile readiness to screen readers
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = 'Mobile navigation ready';
    document.body.appendChild(announcement);
    
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        MobileNavigation,
        SubscriptionModal,
        MobileFormValidation,
        TouchGestureHandler,
        MobilePerformanceOptimizer
    };
}
