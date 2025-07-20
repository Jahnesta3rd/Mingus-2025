// Welcome Page Interactivity Module
class WelcomePage {
    constructor() {
        this.checkAuth();
        // State Management
        this.state = {
            currentStep: 1,
            selections: this.loadFromLocalStorage() || {},
            formData: {},
            analytics: {
                pageLoadTime: new Date(),
                interactions: []
            }
        };

        // DOM Elements
        this.elements = {
            progressBar: document.querySelector('.progress-bar .progress-fill'),
            questionCards: document.querySelectorAll('.question-card'),
            formSteps: document.querySelectorAll('.form-step'),
            navButtons: document.querySelectorAll('[data-nav]'),
            form: document.getElementById('signup-form')
        };

        this.initializeEventListeners();
        this.initializeAnalytics();
        this.restoreUserSelections();
    }

    async checkAuth() {
        const session = await checkAuth();
        if (!session) {
            redirectToLogin('Please sign in using your social media login to continue.');
            return;
        }
    }

    // Event Listeners
    initializeEventListeners() {
        // Question Selection
        this.elements.questionCards.forEach(card => {
            card.addEventListener('click', (e) => this.handleQuestionSelection(e));
        });

        // Form Navigation
        this.elements.navButtons.forEach(button => {
            button.addEventListener('click', (e) => this.handleNavigation(e));
        });

        // Form Submission
        if (this.elements.form) {
            this.elements.form.addEventListener('submit', (e) => this.handleFormSubmission(e));
        }

        // Smooth Scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => this.handleSmoothScroll(e));
        });

        // Scroll Animation Triggers
        this.initializeScrollObserver();

        // Form Input Validation
        document.querySelectorAll('.form-input').forEach(input => {
            input.addEventListener('input', (e) => this.validateInput(e.target));
            input.addEventListener('blur', (e) => this.validateInput(e.target));
        });
    }

    // Question Selection Logic
    handleQuestionSelection(e) {
        const card = e.currentTarget;
        const question = card.dataset.question;
        const value = card.dataset.value;

        // Remove previous selection
        card.parentElement.querySelectorAll('.question-card').forEach(c => {
            c.classList.remove('selected');
        });

        // Add new selection
        card.classList.add('selected');

        // Store selection
        this.state.selections[question] = value;
        this.saveToLocalStorage();

        // Track interaction
        this.trackAnalytics('question_selection', { question, value });

        // Animate progress
        this.updateProgress();
    }

    // Form Validation and Progression
    validateInput(input) {
        const value = input.value.trim();
        const name = input.name;
        let isValid = true;
        let errorMessage = '';

        // Validation rules
        switch (name) {
            case 'email':
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                isValid = emailRegex.test(value);
                errorMessage = 'Please enter a valid email address';
                break;
            case 'name':
                isValid = value.length >= 2;
                errorMessage = 'Name must be at least 2 characters long';
                break;
            // Add more validation rules as needed
        }

        // Update UI
        const errorElement = input.parentElement.querySelector('.form-error');
        if (!isValid && value !== '') {
            input.classList.add('input-error');
            if (errorElement) {
                errorElement.textContent = errorMessage;
                errorElement.classList.remove('hidden');
            }
        } else {
            input.classList.remove('input-error');
            if (errorElement) {
                errorElement.classList.add('hidden');
            }
        }

        return isValid;
    }

    validateStep(step) {
        const stepElement = this.elements.formSteps[step - 1];
        const inputs = stepElement.querySelectorAll('.form-input');
        let isValid = true;

        inputs.forEach(input => {
            if (!this.validateInput(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    handleNavigation(e) {
        const button = e.currentTarget;
        const direction = button.dataset.nav;
        const currentStep = this.state.currentStep;

        if (direction === 'next' && !this.validateStep(currentStep)) {
            this.showError('Please fill in all required fields correctly');
            return;
        }

        const nextStep = direction === 'next' ? currentStep + 1 : currentStep - 1;
        this.navigateToStep(nextStep);
    }

    navigateToStep(step) {
        // Validate step bounds
        if (step < 1 || step > this.elements.formSteps.length) return;

        // Update state
        this.state.currentStep = step;

        // Update UI
        this.elements.formSteps.forEach((stepElement, index) => {
            if (index + 1 === step) {
                stepElement.classList.add('active');
                stepElement.classList.remove('exiting');
            } else {
                stepElement.classList.remove('active');
                if (index + 1 < step) {
                    stepElement.classList.add('exiting');
                }
            }
        });

        // Update progress
        this.updateProgress();

        // Track progression
        this.trackAnalytics('form_progression', { step });
    }

    // Progress Management
    updateProgress() {
        const totalSteps = this.elements.formSteps.length;
        const progress = (this.state.currentStep / totalSteps) * 100;
        
        this.elements.progressBar.style.width = `${progress}%`;
        this.elements.progressBar.setAttribute('aria-valuenow', progress);
    }

    // Local Storage Management
    saveToLocalStorage() {
        try {
            localStorage.setItem('mingus_welcome_state', JSON.stringify({
                selections: this.state.selections,
                lastUpdated: new Date()
            }));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    }

    loadFromLocalStorage() {
        try {
            const saved = localStorage.getItem('mingus_welcome_state');
            return saved ? JSON.parse(saved).selections : null;
        } catch (error) {
            console.error('Error loading from localStorage:', error);
            return null;
        }
    }

    restoreUserSelections() {
        if (!this.state.selections) return;

        // Restore question selections
        Object.entries(this.state.selections).forEach(([question, value]) => {
            const card = document.querySelector(`.question-card[data-question="${question}"][data-value="${value}"]`);
            if (card) {
                card.classList.add('selected');
            }
        });

        // Update progress
        this.updateProgress();
    }

    // Smooth Scrolling
    handleSmoothScroll(e) {
        e.preventDefault();
        const targetId = e.currentTarget.getAttribute('href');
        const targetElement = document.querySelector(targetId);

        if (targetElement) {
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });

            // Track scroll interaction
            this.trackAnalytics('smooth_scroll', { target: targetId });
        }
    }

    // Scroll Animation Observer
    initializeScrollObserver() {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                        // Track visibility
                        this.trackAnalytics('section_visible', {
                            section: entry.target.id || 'unknown'
                        });
                    }
                });
            },
            {
                threshold: 0.1,
                rootMargin: '0px 0px -10% 0px'
            }
        );

        // Observe all animated elements
        document.querySelectorAll('.section-reveal, .scroll-fade').forEach(
            element => observer.observe(element)
        );
    }

    // Form Submission
    async handleFormSubmission(e) {
        e.preventDefault();

        if (!this.validateStep(this.state.currentStep)) {
            this.showError('Please fill in all required fields correctly');
            return;
        }

        // Show loading state
        this.showLoading();

        try {
            // Collect form data
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());

            // Combine with selections
            const submitData = {
                ...data,
                selections: this.state.selections
            };

            // Track submission
            this.trackAnalytics('form_submission', { data: submitData });

            // Simulate API call (replace with actual API call)
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Show success state
            this.showSuccess();

            // Clear local storage
            localStorage.removeItem('mingus_welcome_state');

        } catch (error) {
            console.error('Submission error:', error);
            this.showError('An error occurred. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    // UI State Management
    showLoading() {
        const button = this.elements.form.querySelector('button[type="submit"]');
        if (button) {
            button.classList.add('loading');
            button.disabled = true;
        }
    }

    hideLoading() {
        const button = this.elements.form.querySelector('button[type="submit"]');
        if (button) {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }

    showSuccess() {
        const successMessage = document.createElement('div');
        successMessage.className = 'success-message';
        successMessage.setAttribute('role', 'alert');
        successMessage.textContent = 'Successfully submitted! Redirecting...';
        
        this.elements.form.appendChild(successMessage);

        // Simulate redirect
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 2000);
    }

    showError(message) {
        const errorMessage = document.createElement('div');
        errorMessage.className = 'error-message';
        errorMessage.setAttribute('role', 'alert');
        errorMessage.textContent = message;

        this.elements.form.appendChild(errorMessage);

        setTimeout(() => {
            errorMessage.remove();
        }, 5000);
    }

    // Analytics
    initializeAnalytics() {
        // Page load tracking
        this.trackAnalytics('page_load', {
            timestamp: this.state.analytics.pageLoadTime,
            url: window.location.href
        });

        // Track when user leaves page
        window.addEventListener('beforeunload', () => {
            this.trackAnalytics('page_exit', {
                duration: new Date() - this.state.analytics.pageLoadTime
            });
        });
    }

    trackAnalytics(event, data) {
        const analyticsData = {
            event,
            timestamp: new Date(),
            data
        };

        // Store interaction
        this.state.analytics.interactions.push(analyticsData);

        // Log to console (replace with actual analytics service)
        console.log('Analytics:', analyticsData);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.welcomePage = new WelcomePage();
}); 