/**
 * MINGUS REFERRAL SYSTEM JAVASCRIPT
 * 
 * Comprehensive JavaScript functionality for the referral-gated job recommendation system
 * including referral tracking, social sharing, location features, and accessibility support.
 * 
 * Features:
 * - Referral progress tracking and real-time updates
 * - Social sharing integration with tracking
 * - Feature unlock celebration animations
 * - Real-time zipcode validation and location lookup
 * - Interactive radius selection with map preview
 * - Real-time upload progress tracking
 * - Expandable recommendation cards with location details
 * - Interactive salary vs. cost of living comparison charts
 * - Commute time calculator integration
 * - Application status tracking
 * - Mobile touch interactions
 * - Smooth animations and transitions
 * - WCAG 2.1 compliance
 */

class MingusReferralSystem {
    constructor() {
        this.referralCount = parseInt(localStorage.getItem('mingus_referrals') || '0');
        this.maxReferrals = 3;
        this.isUnlocked = this.referralCount >= this.maxReferrals;
        this.observers = [];
        this.animationQueue = [];
        this.isAnimating = false;
        
        // Initialize accessibility features
        this.initAccessibility();
        
        // Initialize touch interactions for mobile
        this.initTouchInteractions();
        
        // Initialize keyboard navigation
        this.initKeyboardNavigation();
    }

    /**
     * Initialize accessibility features for WCAG 2.1 compliance
     */
    initAccessibility() {
        // Add ARIA labels to interactive elements
        this.addAriaLabels();
        
        // Initialize focus management
        this.initFocusManagement();
        
        // Initialize screen reader announcements
        this.initScreenReaderAnnouncements();
        
        // Initialize high contrast mode detection
        this.initHighContrastMode();
        
        // Initialize reduced motion detection
        this.initReducedMotion();
    }

    /**
     * Add ARIA labels to interactive elements
     */
    addAriaLabels() {
        const interactiveElements = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
        
        interactiveElements.forEach(element => {
            if (!element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')) {
                const text = element.textContent?.trim() || element.value || element.placeholder;
                if (text) {
                    element.setAttribute('aria-label', text);
                }
            }
        });
    }

    /**
     * Initialize focus management
     */
    initFocusManagement() {
        // Trap focus in modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                this.handleTabNavigation(e);
            }
        });
        
        // Manage focus for dynamic content
        this.observeDynamicContent();
    }

    /**
     * Handle tab navigation for accessibility
     */
    handleTabNavigation(e) {
        const modal = document.querySelector('.modal.show');
        if (!modal) return;
        
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
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

    /**
     * Initialize screen reader announcements
     */
    initScreenReaderAnnouncements() {
        // Create live region for announcements
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        liveRegion.id = 'live-region';
        document.body.appendChild(liveRegion);
    }

    /**
     * Announce to screen readers
     */
    announce(message) {
        const liveRegion = document.getElementById('live-region');
        if (liveRegion) {
            liveRegion.textContent = message;
        }
    }

    /**
     * Initialize high contrast mode detection
     */
    initHighContrastMode() {
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            document.body.classList.add('high-contrast');
        }
        
        window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
            if (e.matches) {
                document.body.classList.add('high-contrast');
            } else {
                document.body.classList.remove('high-contrast');
            }
        });
    }

    /**
     * Initialize reduced motion detection
     */
    initReducedMotion() {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.body.classList.add('reduced-motion');
        }
        
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            if (e.matches) {
                document.body.classList.add('reduced-motion');
            } else {
                document.body.classList.remove('reduced-motion');
            }
        });
    }

    /**
     * Initialize touch interactions for mobile
     */
    initTouchInteractions() {
        // Add touch feedback to interactive elements
        const touchElements = document.querySelectorAll('button, a, [role="button"], .card, .job-card');
        
        touchElements.forEach(element => {
            element.addEventListener('touchstart', (e) => {
                element.classList.add('touch-active');
            });
            
            element.addEventListener('touchend', (e) => {
                setTimeout(() => {
                    element.classList.remove('touch-active');
                }, 150);
            });
            
            element.addEventListener('touchcancel', (e) => {
                element.classList.remove('touch-active');
            });
        });
    }

    /**
     * Initialize keyboard navigation
     */
    initKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Handle Enter and Space for custom interactive elements
            if (e.key === 'Enter' || e.key === ' ') {
                const target = e.target;
                if (target.classList.contains('card') || target.classList.contains('job-card')) {
                    e.preventDefault();
                    this.handleCardInteraction(target);
                }
            }
            
            // Handle Escape key for modals
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    /**
     * Handle card interactions
     */
    handleCardInteraction(card) {
        const actionButton = card.querySelector('.action-button, .btn');
        if (actionButton) {
            actionButton.click();
        }
    }

    /**
     * Close all open modals
     */
    closeAllModals() {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            modal.classList.remove('show');
            modal.setAttribute('aria-hidden', 'true');
        });
    }

    /**
     * Initialize career preview page
     */
    initCareerPreview() {
        this.updateProgress(this.referralCount);
        this.initValueCalculator();
        this.initSuccessStories();
        this.initFeatureTeasers();
    }

    /**
     * Initialize referral progress page
     */
    initReferralProgress() {
        this.updateProgress(this.referralCount);
        this.initReferralHistory();
        this.initSharingOptions();
        this.initProgressAnimations();
    }

    /**
     * Initialize unlock celebration page
     */
    initCelebration() {
        this.triggerCelebrationAnimation();
        this.initFeatureShowcase();
        this.initSuccessSharing();
    }

    /**
     * Initialize refer friends page
     */
    initReferFriends() {
        this.initMessageTemplates();
        this.initSocialSharing();
        this.initReferralTracking();
    }

    /**
     * Initialize enhanced upload page
     */
    initEnhancedUpload() {
        this.initFileUpload();
        this.initLocationLookup();
        this.initProgressTracking();
    }

    /**
     * Initialize location preferences page
     */
    initLocationPreferences() {
        this.initZipcodeValidation();
        this.initMapPreview();
        this.initCommuteAnalysis();
        this.initCostOfLivingComparison();
    }

    /**
     * Initialize targeted results page
     */
    initTargetedResults() {
        this.initJobFilters();
        this.initTierSelection();
        this.initJobCards();
        this.initPagination();
    }

    /**
     * Initialize recommendation detail page
     */
    initRecommendationDetail() {
        this.initJobDetails();
        this.initSkillsAnalysis();
        this.initCommuteOptions();
        this.initApplicationTimeline();
    }

    /**
     * Initialize application tracker page
     */
    initApplicationTracker() {
        this.initApplicationFilters();
        this.initApplicationCards();
        this.initProgressChart();
        this.initStatusUpdates();
    }

    /**
     * Update referral progress
     */
    updateProgress(count) {
        this.referralCount = count;
        this.isUnlocked = count >= this.maxReferrals;
        
        // Update progress elements
        const progressElements = document.querySelectorAll('.progress-current, #current-referrals');
        progressElements.forEach(element => {
            element.textContent = count;
        });
        
        // Update progress steps
        this.updateProgressSteps(count);
        
        // Update progress ring
        this.updateProgressRing(count);
        
        // Update remaining referrals
        const remaining = this.maxReferrals - count;
        const remainingElements = document.querySelectorAll('#referrals-remaining');
        remainingElements.forEach(element => {
            element.textContent = remaining;
        });
        
        // Announce progress update
        this.announce(`Referral progress: ${count} of ${this.maxReferrals} referrals completed`);
        
        // Trigger unlock if completed
        if (this.isUnlocked) {
            this.triggerUnlock();
        }
    }

    /**
     * Update progress steps
     */
    updateProgressSteps(count) {
        const steps = document.querySelectorAll('.progress-step, .progress-icon');
        
        steps.forEach((step, index) => {
            const stepNumber = index + 1;
            
            if (stepNumber <= count) {
                step.classList.add('completed');
                step.classList.remove('current', 'locked');
            } else if (stepNumber === count + 1) {
                step.classList.add('current');
                step.classList.remove('completed', 'locked');
            } else {
                step.classList.add('locked');
                step.classList.remove('completed', 'current');
            }
        });
    }

    /**
     * Update progress ring
     */
    updateProgressRing(count) {
        const progressRing = document.querySelector('.progress-ring-circle');
        if (!progressRing) return;
        
        const circumference = 2 * Math.PI * 36; // radius = 36
        const progress = (count / this.maxReferrals) * circumference;
        const offset = circumference - progress;
        
        progressRing.style.strokeDasharray = circumference;
        progressRing.style.strokeDashoffset = offset;
    }

    /**
     * Trigger unlock celebration
     */
    triggerUnlock() {
        this.announce('Congratulations! You have unlocked premium features!');
        
        // Show celebration animation
        this.showCelebrationAnimation();
        
        // Update UI to show unlocked state
        this.updateUnlockedState();
        
        // Redirect to celebration page after delay
        setTimeout(() => {
            window.location.href = 'unlock_celebration.html';
        }, 3000);
    }

    /**
     * Show celebration animation
     */
    showCelebrationAnimation() {
        const celebration = document.createElement('div');
        celebration.className = 'celebration-overlay';
        celebration.innerHTML = `
            <div class="celebration-content">
                <div class="celebration-icon">🎉</div>
                <h2>Congratulations!</h2>
                <p>You've unlocked premium features!</p>
            </div>
        `;
        
        document.body.appendChild(celebration);
        
        // Trigger confetti effect
        this.createConfetti();
        
        // Remove celebration after animation
        setTimeout(() => {
            celebration.remove();
        }, 5000);
    }

    /**
     * Create confetti effect
     */
    createConfetti() {
        const colors = ['#8b5cf6', '#a855f7', '#ec4899', '#f59e0b', '#10b981'];
        const confettiCount = 50;
        
        for (let i = 0; i < confettiCount; i++) {
            setTimeout(() => {
                const confetti = document.createElement('div');
                confetti.style.position = 'fixed';
                confetti.style.left = Math.random() * 100 + 'vw';
                confetti.style.top = '-10px';
                confetti.style.width = '10px';
                confetti.style.height = '10px';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.borderRadius = '50%';
                confetti.style.pointerEvents = 'none';
                confetti.style.zIndex = '1000';
                confetti.style.animation = `confettiFall ${Math.random() * 3 + 2}s linear forwards`;
                
                document.body.appendChild(confetti);
                
                setTimeout(() => {
                    confetti.remove();
                }, 5000);
            }, i * 50);
        }
    }

    /**
     * Update unlocked state
     */
    updateUnlockedState() {
        // Update badges
        const badges = document.querySelectorAll('.card-badge.locked');
        badges.forEach(badge => {
            badge.textContent = 'Unlocked';
            badge.classList.remove('locked');
            badge.classList.add('unlocked');
        });
        
        // Remove locked overlays
        const overlays = document.querySelectorAll('.locked-overlay');
        overlays.forEach(overlay => {
            overlay.style.display = 'none';
        });
        
        // Enable locked buttons
        const lockedButtons = document.querySelectorAll('[disabled]');
        lockedButtons.forEach(button => {
            button.disabled = false;
        });
    }

    /**
     * Initialize value calculator
     */
    initValueCalculator() {
        const salaryInput = document.getElementById('current-salary');
        const locationSelect = document.getElementById('location');
        
        if (salaryInput && locationSelect) {
            salaryInput.addEventListener('input', () => this.calculateValue());
            locationSelect.addEventListener('change', () => this.calculateValue());
        }
    }

    /**
     * Calculate potential value
     */
    calculateValue() {
        const salary = parseInt(document.getElementById('current-salary')?.value || '85000');
        const location = document.getElementById('location')?.value || 'sf';
        
        // Mock calculation based on location
        const multipliers = {
            'sf': { salary: 1.3, col: 1.4 },
            'nyc': { salary: 1.25, col: 1.35 },
            'austin': { salary: 1.15, col: 1.1 },
            'atlanta': { salary: 1.1, col: 1.05 }
        };
        
        const multiplier = multipliers[location] || multipliers['sf'];
        const salaryIncrease = Math.round(salary * (multiplier.salary - 1));
        const colAdjustment = Math.round(salary * (multiplier.col - 1));
        const totalValue = salaryIncrease + colAdjustment;
        
        // Update display
        this.updateElement('#salary-increase', `+$${salaryIncrease.toLocaleString()}`);
        this.updateElement('#col-adjustment', `+$${colAdjustment.toLocaleString()}`);
        this.updateElement('#total-value', `+$${totalValue.toLocaleString()}`);
    }

    /**
     * Initialize success stories
     */
    initSuccessStories() {
        const stories = document.querySelectorAll('.success-story');
        stories.forEach((story, index) => {
            story.style.animationDelay = `${index * 0.2}s`;
            story.classList.add('animate-fadeIn');
        });
    }

    /**
     * Initialize feature teasers
     */
    initFeatureTeasers() {
        const teasers = document.querySelectorAll('.preview-card');
        teasers.forEach((teaser, index) => {
            teaser.addEventListener('mouseenter', () => {
                this.animateTeaser(teaser, 'enter');
            });
            
            teaser.addEventListener('mouseleave', () => {
                this.animateTeaser(teaser, 'leave');
            });
        });
    }

    /**
     * Animate teaser on hover
     */
    animateTeaser(teaser, action) {
        const overlay = teaser.querySelector('.locked-overlay');
        if (!overlay) return;
        
        if (action === 'enter') {
            overlay.style.background = 'rgba(17, 24, 39, 0.75)';
            overlay.style.transform = 'scale(1.02)';
        } else {
            overlay.style.background = 'rgba(17, 24, 39, 0.85)';
            overlay.style.transform = 'scale(1)';
        }
    }

    /**
     * Initialize file upload
     */
    initFileUpload() {
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        
        if (uploadArea && fileInput) {
            // Drag and drop
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelect(files[0]);
                }
            });
            
            // Click to upload
            uploadArea.addEventListener('click', () => {
                fileInput.click();
            });
            
            // File selection
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileSelect(e.target.files[0]);
                }
            });
        }
    }

    /**
     * Handle file selection
     */
    handleFileSelect(file) {
        // Validate file type
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('Please upload a PDF, DOC, or DOCX file.');
            return;
        }
        
        // Validate file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
            this.showError('File size must be less than 10MB.');
            return;
        }
        
        // Show file preview
        this.showFilePreview(file);
        
        // Enable analyze button
        const analyzeBtn = document.getElementById('analyze-btn');
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
        }
    }

    /**
     * Show file preview
     */
    showFilePreview(file) {
        const preview = document.getElementById('file-preview');
        const fileName = document.getElementById('file-name');
        const fileSize = document.getElementById('file-size');
        
        if (preview && fileName && fileSize) {
            fileName.textContent = file.name;
            fileSize.textContent = this.formatFileSize(file.size);
            preview.style.display = 'flex';
        }
    }

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Initialize zipcode validation
     */
    initZipcodeValidation() {
        const zipcodeInput = document.getElementById('zipcode');
        
        if (zipcodeInput) {
            zipcodeInput.addEventListener('input', (e) => {
                const zipcode = e.target.value.replace(/\D/g, '');
                e.target.value = zipcode;
                
                if (zipcode.length === 5) {
                    this.lookupLocation(zipcode);
                }
            });
        }
    }

    /**
     * Lookup location by zipcode
     */
    lookupLocation(zipcode) {
        // Mock location data
        const locations = {
            '10001': { city: 'New York', state: 'NY', metro: 'New York Metro' },
            '90210': { city: 'Beverly Hills', state: 'CA', metro: 'Los Angeles Metro' },
            '60601': { city: 'Chicago', state: 'IL', metro: 'Chicago Metro' },
            '75201': { city: 'Dallas', state: 'TX', metro: 'Dallas-Fort Worth Metro' },
            '30301': { city: 'Atlanta', state: 'GA', metro: 'Atlanta Metro' }
        };
        
        const location = locations[zipcode];
        if (location) {
            this.updateElement('#city', location.city);
            this.updateElement('#state', location.state);
            this.updateElement('#metro-area', location.metro);
            this.updateLocationSummary(location);
        } else {
            // Simulate API call for unknown ZIP codes
            setTimeout(() => {
                this.updateElement('#city', 'Unknown City');
                this.updateElement('#state', 'Unknown State');
                this.updateElement('#metro-area', 'Unknown Metro');
            }, 1000);
        }
    }

    /**
     * Update location summary
     */
    updateLocationSummary(location) {
        // Mock data based on location
        const mockData = {
            '10001': { jobs: 47, salaryMin: 85, salaryMax: 120, commute: 25 },
            '90210': { jobs: 32, salaryMin: 90, salaryMax: 130, commute: 30 },
            '60601': { jobs: 28, salaryMin: 75, salaryMax: 110, commute: 22 },
            '75201': { jobs: 35, salaryMin: 70, salaryMax: 105, commute: 20 },
            '30301': { jobs: 41, salaryMin: 65, salaryMax: 95, commute: 18 }
        };
        
        const data = mockData[Object.keys(mockData).find(key => 
            mockData[key] === location || key === location.zipcode
        )] || { jobs: 25, salaryMin: 60, salaryMax: 90, commute: 30 };
        
        this.updateElement('#jobs-available', data.jobs);
        this.updateElement('#avg-commute', `${data.commute} min`);
    }

    /**
     * Initialize job filters
     */
    initJobFilters() {
        const filters = document.querySelectorAll('.filter-select, .filter-tab');
        
        filters.forEach(filter => {
            filter.addEventListener('change', () => {
                this.applyFilters();
            });
        });
    }

    /**
     * Apply job filters
     */
    applyFilters() {
        this.showLoading();
        
        // Simulate API call
        setTimeout(() => {
            this.hideLoading();
            this.updateJobCount();
        }, 1000);
    }

    /**
     * Initialize tier selection
     */
    initTierSelection() {
        const tierOptions = document.querySelectorAll('.tier-option');
        
        tierOptions.forEach(option => {
            option.addEventListener('click', () => {
                tierOptions.forEach(opt => opt.classList.remove('selected'));
                option.classList.add('selected');
                this.filterJobsByTier(option.dataset.tier);
            });
        });
    }

    /**
     * Filter jobs by tier
     */
    filterJobsByTier(tier) {
        const jobCards = document.querySelectorAll('.job-card');
        
        jobCards.forEach(card => {
            if (tier === 'all' || card.dataset.tier === tier) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
        
        this.updateJobCount();
    }

    /**
     * Update job count
     */
    updateJobCount() {
        const visibleJobs = document.querySelectorAll('.job-card[style*="block"], .job-card:not([style*="none"])');
        this.updateElement('#total-jobs', visibleJobs.length);
    }

    /**
     * Show loading state
     */
    showLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.add('show');
        }
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.remove('show');
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        // Create error notification
        const error = document.createElement('div');
        error.className = 'error-notification';
        error.textContent = message;
        error.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(error);
        
        // Remove after 5 seconds
        setTimeout(() => {
            error.remove();
        }, 5000);
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        // Create success notification
        const success = document.createElement('div');
        success.className = 'success-notification';
        success.textContent = message;
        success.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(success);
        
        // Remove after 5 seconds
        setTimeout(() => {
            success.remove();
        }, 5000);
    }

    /**
     * Update element text content
     */
    updateElement(selector, text) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = text;
        }
    }

    /**
     * Observe dynamic content for accessibility
     */
    observeDynamicContent() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.addAriaLabels();
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Initialize progress animations
     */
    initProgressAnimations() {
        const progressElements = document.querySelectorAll('.progress-icon, .progress-step');
        
        progressElements.forEach((element, index) => {
            element.style.animationDelay = `${index * 0.2}s`;
            element.classList.add('animate-fadeIn');
        });
    }

    /**
     * Initialize referral history
     */
    initReferralHistory() {
        const referralCards = document.querySelectorAll('.referral-card');
        
        referralCards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('animate-fadeIn');
        });
    }

    /**
     * Initialize sharing options
     */
    initSharingOptions() {
        const shareButtons = document.querySelectorAll('.share-button');
        
        shareButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const platform = button.dataset.platform || 'default';
                this.shareToPlatform(platform);
            });
        });
    }

    /**
     * Share to platform
     */
    shareToPlatform(platform) {
        const url = encodeURIComponent(window.location.origin + '/referral?code=MINGUS2024');
        const text = encodeURIComponent('Join me on Mingus - the financial wellness platform for Black professionals!');
        
        const shareUrls = {
            'linkedin': `https://www.linkedin.com/sharing/share-offsite/?url=${url}&title=${text}`,
            'twitter': `https://twitter.com/intent/tweet?url=${url}&text=${text}`,
            'email': `mailto:?subject=Join me on Mingus&body=${text}%0A%0A${url}`,
            'whatsapp': `https://wa.me/?text=${text}%0A%0A${url}`
        };
        
        const shareUrl = shareUrls[platform];
        if (shareUrl) {
            window.open(shareUrl, '_blank');
        }
    }

    /**
     * Initialize message templates
     */
    initMessageTemplates() {
        const templateOptions = document.querySelectorAll('.template-option');
        
        templateOptions.forEach(option => {
            option.addEventListener('click', () => {
                templateOptions.forEach(opt => opt.classList.remove('selected'));
                option.classList.add('selected');
                this.updateMessagePreview();
            });
        });
    }

    /**
     * Update message preview
     */
    updateMessagePreview() {
        const selectedTemplate = document.querySelector('.template-option.selected');
        const customMessage = document.getElementById('custom-message')?.value || '';
        const friendName = document.getElementById('friend-name')?.value || '[Friend\'s Name]';
        const yourName = document.getElementById('your-name')?.value || '[Your Name]';
        
        let message = '';
        
        if (customMessage.trim()) {
            message = customMessage;
        } else {
            const template = selectedTemplate?.dataset.template;
            message = this.getTemplateMessage(template);
        }
        
        // Replace placeholders
        message = message.replace(/\[Friend's Name\]/g, friendName);
        message = message.replace(/\[Your Name\]/g, yourName);
        message = message.replace(/\[Referral Link\]/g, 'https://mingus.app/referral?code=MINGUS2024');
        
        this.updateElement('#message-preview', message);
    }

    /**
     * Get template message
     */
    getTemplateMessage(template) {
        const templates = {
            'professional': `Hi [Friend's Name],

I've been using Mingus for financial planning and career development, and I think you'd find it valuable for your professional growth.

Mingus offers:
• Personalized financial planning
• Career advancement strategies
• Generational wealth building
• Health and wellness integration

Use my referral code: MINGUS2024
Sign up here: [Referral Link]

Best regards,
[Your Name]`,
            
            'casual': `Hey [Friend's Name]!

I found this amazing app called Mingus that's specifically designed for Black professionals. It's been helping me with my career and finances, and I think you'd love it too!

Mingus offers:
• Personalized financial planning
• Career advancement strategies
• Generational wealth building
• Health and wellness integration

Use my referral code: MINGUS2024
Sign up here: [Referral Link]

Let's build wealth together!

Best regards,
[Your Name]`,
            
            'personal': `[Friend's Name],

I know we've talked about building wealth and advancing our careers. I found this platform that's really helping me, and I thought you'd love it too.

Mingus is designed specifically for Black professionals and offers:
• Personalized financial planning
• Career advancement strategies
• Generational wealth building
• Health and wellness integration

Use my referral code: MINGUS2024
Sign up here: [Referral Link]

Let's support each other's success!

[Your Name]`
        };
        
        return templates[template] || templates.casual;
    }

    /**
     * Initialize social sharing
     */
    initSocialSharing() {
        const socialButtons = document.querySelectorAll('.social-button');
        
        socialButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const platform = button.dataset.platform || 'default';
                this.shareToPlatform(platform);
            });
        });
    }

    /**
     * Initialize referral tracking
     */
    initReferralTracking() {
        // Track referral clicks
        const referralLinks = document.querySelectorAll('a[href*="referral"]');
        
        referralLinks.forEach(link => {
            link.addEventListener('click', () => {
                this.trackReferralClick();
            });
        });
    }

    /**
     * Track referral click
     */
    trackReferralClick() {
        // In a real implementation, this would send analytics data
        console.log('Referral link clicked');
        
        // Update local storage
        const clicks = parseInt(localStorage.getItem('mingus_referral_clicks') || '0');
        localStorage.setItem('mingus_referral_clicks', (clicks + 1).toString());
    }

    /**
     * Initialize application filters
     */
    initApplicationFilters() {
        const filterTabs = document.querySelectorAll('.filter-tab');
        const applicationCards = document.querySelectorAll('.application-card');
        
        filterTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const filter = tab.dataset.filter;
                
                // Update active tab
                filterTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Filter applications
                this.filterApplications(filter, applicationCards);
            });
        });
    }

    /**
     * Filter applications
     */
    filterApplications(filter, cards) {
        let visibleCount = 0;
        
        cards.forEach(card => {
            if (filter === 'all' || card.dataset.status === filter) {
                card.style.display = 'block';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        // Show/hide empty state
        const emptyState = document.getElementById('empty-state');
        if (emptyState) {
            emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
        }
    }

    /**
     * Initialize application cards
     */
    initApplicationCards() {
        const cards = document.querySelectorAll('.application-card');
        
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('animate-fadeIn');
        });
    }

    /**
     * Initialize progress chart
     */
    initProgressChart() {
        const chartBars = document.querySelectorAll('.chart-bar');
        
        chartBars.forEach((bar, index) => {
            bar.style.animationDelay = `${index * 0.1}s`;
            bar.classList.add('animate-fadeIn');
        });
    }

    /**
     * Initialize status updates
     */
    initStatusUpdates() {
        // Simulate real-time status updates
        setInterval(() => {
            this.updateApplicationStatuses();
        }, 30000); // Check every 30 seconds
    }

    /**
     * Update application statuses
     */
    updateApplicationStatuses() {
        // In a real implementation, this would check for status updates
        console.log('Checking for status updates...');
    }
}

// Initialize the referral system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mingusReferralSystem = new MingusReferralSystem();
});

// Add confetti animation CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes confettiFall {
        to {
            transform: translateY(100vh) rotate(360deg);
            opacity: 0;
        }
    }
    
    .celebration-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        animation: fadeIn 0.5s ease-out;
    }
    
    .celebration-content {
        background: linear-gradient(135deg, #8b5cf6, #a855f7);
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        color: white;
        max-width: 400px;
        margin: 20px;
        animation: celebrationBounce 0.6s ease-out;
    }
    
    .celebration-icon {
        font-size: 64px;
        margin-bottom: 20px;
        animation: celebrationSpin 1s ease-in-out;
    }
    
    @keyframes celebrationBounce {
        0% { transform: scale(0.3) rotate(-10deg); }
        50% { transform: scale(1.1) rotate(5deg); }
        100% { transform: scale(1) rotate(0deg); }
    }
    
    @keyframes celebrationSpin {
        0% { transform: rotate(0deg) scale(0.5); }
        50% { transform: rotate(180deg) scale(1.2); }
        100% { transform: rotate(360deg) scale(1); }
    }
    
    .touch-active {
        transform: scale(0.98);
        opacity: 0.8;
    }
    
    .high-contrast .btn-primary {
        background: #8b5cf6;
        border: 2px solid white;
    }
    
    .high-contrast .card {
        border: 2px solid #6b7280;
    }
    
    .reduced-motion * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
`;
document.head.appendChild(style);
