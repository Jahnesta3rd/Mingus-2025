/**
 * Job Recommendations Interface JavaScript
 * Comprehensive functionality for career advancement recommendations
 */

class JobRecommendationsInterface {
    constructor() {
        this.sessionId = null;
        this.recommendations = {};
        this.userProfile = {};
        this.financialImpact = {};
        this.successProbabilities = {};
        this.progress = {
            applications: 0,
            interviews: 0,
            offers: 0,
            skills: 0
        };
        
        this.init();
    }

    init() {
        this.loadData();
        this.setupEventListeners();
        this.initializeAnimations();
        this.loadProgress();
        this.setupAccessibility();
    }

    loadData() {
        // Load data from page context or API
        this.sessionId = document.querySelector('meta[name="session-id"]')?.content;
        this.recommendations = window.recommendationsData || {};
        this.userProfile = window.userProfileData || {};
        this.financialImpact = window.financialImpactData || {};
        this.successProbabilities = window.successProbabilitiesData || {};
    }

    setupEventListeners() {
        // Application buttons
        document.querySelectorAll('[data-action="apply"]').forEach(button => {
            button.addEventListener('click', (e) => {
                const tier = e.target.closest('.recommendation-card').dataset.tier;
                this.applyToJob(tier);
            });
        });

        // View details buttons
        document.querySelectorAll('[data-action="view-details"]').forEach(button => {
            button.addEventListener('click', (e) => {
                const tier = e.target.closest('.recommendation-card').dataset.tier;
                this.viewJobDetails(tier);
            });
        });

        // Save recommendation buttons
        document.querySelectorAll('[data-action="save"]').forEach(button => {
            button.addEventListener('click', (e) => {
                const tier = e.target.closest('.recommendation-card').dataset.tier;
                this.saveRecommendation(tier);
            });
        });

        // Progress update
        const updateProgressBtn = document.getElementById('update-progress');
        if (updateProgressBtn) {
            updateProgressBtn.addEventListener('click', () => this.showProgressModal());
        }

        // Download report
        const downloadBtn = document.getElementById('download-report');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadReport());
        }

        // Share results
        const shareBtn = document.getElementById('share-results');
        if (shareBtn) {
            shareBtn.addEventListener('click', () => this.shareResults());
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboardNavigation(e));
    }

    initializeAnimations() {
        // Intersection Observer for scroll animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, { threshold: 0.1 });

        // Observe recommendation cards
        document.querySelectorAll('.recommendation-card').forEach((card, index) => {
            card.style.animationDelay = `${index * 0.2}s`;
            observer.observe(card);
        });

        // Animate progress bars
        this.animateProgressBars();
    }

    animateProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar');
        progressBars.forEach(bar => {
            const targetWidth = bar.getAttribute('data-width') || '0%';
            setTimeout(() => {
                bar.style.width = targetWidth;
            }, 500);
        });
    }

    loadProgress() {
        const savedProgress = localStorage.getItem('careerProgress');
        if (savedProgress) {
            this.progress = JSON.parse(savedProgress);
            this.updateProgressDisplay();
        }
    }

    updateProgressDisplay() {
        document.getElementById('applications-submitted').textContent = this.progress.applications || 0;
        document.getElementById('interviews-scheduled').textContent = this.progress.interviews || 0;
        document.getElementById('offers-received').textContent = this.progress.offers || 0;
        document.getElementById('skills-developed').textContent = this.progress.skills || 0;

        // Calculate overall progress
        const total = (this.progress.applications || 0) + (this.progress.interviews || 0) + 
                     (this.progress.offers || 0) + (this.progress.skills || 0);
        const percentage = Math.min((total / 10) * 100, 100);
        
        const progressBar = document.getElementById('overall-progress');
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
    }

    applyToJob(tier) {
        const job = this.recommendations[tier];
        if (!job) return;

        // Track application
        this.trackEvent('job_application', { 
            tier, 
            company: job.company,
            salary_range: job.salary_range 
        });

        // Update progress
        this.progress.applications = (this.progress.applications || 0) + 1;
        this.saveProgress();

        // Show application modal
        this.showApplicationModal(tier);

        // Open application URL if available
        if (job.application_url) {
            window.open(job.application_url, '_blank');
        }

        this.showNotification(`Application started for ${job.title} at ${job.company}!`, 'success');
    }

    showApplicationModal(tier) {
        const job = this.recommendations[tier];
        const modalContent = `
            <div class="application-modal">
                <h3>Apply to ${job.title}</h3>
                <p>You're about to apply to <strong>${job.company}</strong> for the position of <strong>${job.title}</strong>.</p>
                
                <div class="application-checklist">
                    <h4>Before you apply, make sure you have:</h4>
                    <ul>
                        <li><input type="checkbox" id="resume-ready"> Updated resume tailored to this role</li>
                        <li><input type="checkbox" id="cover-letter"> Customized cover letter</li>
                        <li><input type="checkbox" id="portfolio"> Portfolio or work samples (if applicable)</li>
                        <li><input type="checkbox" id="references"> Updated references</li>
                    </ul>
                </div>
                
                <div class="application-tips">
                    <h4>Application Tips:</h4>
                    <ul>
                        <li>Customize your resume with keywords from the job description</li>
                        <li>Highlight relevant experience and achievements</li>
                        <li>Follow up within 3-5 business days</li>
                        <li>Prepare for potential phone screening</li>
                    </ul>
                </div>
            </div>
        `;

        this.showModal('Application Preparation', modalContent, 'Continue to Application', () => {
            this.completeApplication(tier);
        });
    }

    completeApplication(tier) {
        const job = this.recommendations[tier];
        
        // Mark application as completed
        this.trackEvent('application_completed', { tier, company: job.company });
        
        // Schedule follow-up reminder
        this.scheduleFollowUp(tier);
        
        this.hideModal();
        this.showNotification('Application submitted successfully!', 'success');
    }

    scheduleFollowUp(tier) {
        const job = this.recommendations[tier];
        const followUpDate = new Date();
        followUpDate.setDate(followUpDate.getDate() + 5); // 5 days from now

        const reminder = {
            id: `followup-${tier}-${Date.now()}`,
            type: 'followup',
            tier: tier,
            company: job.company,
            date: followUpDate.toISOString(),
            message: `Follow up on your application to ${job.company} for ${job.title}`
        };

        this.saveReminder(reminder);
    }

    viewJobDetails(tier) {
        const job = this.recommendations[tier];
        if (!job) return;

        const modalContent = `
            <div class="job-details-modal">
                <div class="job-header">
                    <h3>${job.title}</h3>
                    <div class="company-info">
                        <span class="company-name">${job.company}</span>
                        <span class="company-badge">${job.company_tier}</span>
                        <span class="location-badge">
                            <i class="fas fa-map-marker-alt"></i>
                            ${job.location}
                        </span>
                    </div>
                </div>

                <div class="job-content">
                    <div class="salary-info">
                        <h4>Compensation</h4>
                        <div class="salary-range">
                            $${job.salary_range.min.toLocaleString()} - $${job.salary_range.max.toLocaleString()}
                        </div>
                        <div class="salary-increase">
                            +$${job.income_impact.salary_increase_amount.toLocaleString()} 
                            (${(job.income_impact.salary_increase_percentage * 100).toFixed(1)}% increase)
                        </div>
                    </div>

                    <div class="job-description">
                        <h4>Job Description</h4>
                        <p>${job.description || 'Job description not available.'}</p>
                    </div>

                    <div class="requirements">
                        <h4>Requirements</h4>
                        <ul>
                            ${(job.requirements || []).map(req => `<li>${req}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="benefits">
                        <h4>Benefits</h4>
                        <ul>
                            ${(job.benefits || []).map(benefit => `<li>${benefit}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="company-info">
                        <h4>About ${job.company}</h4>
                        <p>${job.company_description || 'Company information not available.'}</p>
                    </div>
                </div>
            </div>
        `;

        this.showModal(`${job.title} at ${job.company}`, modalContent, 'Apply Now', () => {
            this.applyToJob(tier);
        });
    }

    saveRecommendation(tier) {
        const job = this.recommendations[tier];
        if (!job) return;

        const saved = JSON.parse(localStorage.getItem('savedRecommendations') || '[]');
        
        if (!saved.find(r => r.id === job.id)) {
            saved.push({
                ...job,
                savedAt: new Date().toISOString(),
                tier: tier
            });
            
            localStorage.setItem('savedRecommendations', JSON.stringify(saved));
            this.showNotification('Recommendation saved for later review!', 'success');
            
            // Update save button
            const saveBtn = document.querySelector(`[data-tier="${tier}"][data-action="save"]`);
            if (saveBtn) {
                saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved';
                saveBtn.classList.add('saved');
            }
        } else {
            this.showNotification('Recommendation already saved!', 'info');
        }
    }

    showProgressModal() {
        const modalContent = `
            <div class="progress-modal">
                <h3>Update Your Progress</h3>
                <p>Track your career advancement journey to stay motivated and see your progress.</p>
                
                <form id="progress-form">
                    <div class="form-group">
                        <label for="applications">Applications Submitted</label>
                        <input type="number" id="applications" class="form-control" 
                               value="${this.progress.applications || 0}" min="0">
                        <small>Total job applications you've submitted</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="interviews">Interviews Scheduled</label>
                        <input type="number" id="interviews" class="form-control" 
                               value="${this.progress.interviews || 0}" min="0">
                        <small>Phone or in-person interviews scheduled</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="offers">Offers Received</label>
                        <input type="number" id="offers" class="form-control" 
                               value="${this.progress.offers || 0}" min="0">
                        <small>Job offers you've received</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="skills">Skills Developed</label>
                        <input type="number" id="skills" class="form-control" 
                               value="${this.progress.skills || 0}" min="0">
                        <small>New skills you've learned or improved</small>
                    </div>
                </form>
                
                <div class="progress-motivation">
                    <h4>Keep Going! 🚀</h4>
                    <p>Every application brings you closer to your dream job. Stay persistent and celebrate small wins!</p>
                </div>
            </div>
        `;

        this.showModal('Update Progress', modalContent, 'Save Progress', () => {
            this.saveProgressFromForm();
        });
    }

    saveProgressFromForm() {
        this.progress = {
            applications: parseInt(document.getElementById('applications').value) || 0,
            interviews: parseInt(document.getElementById('interviews').value) || 0,
            offers: parseInt(document.getElementById('offers').value) || 0,
            skills: parseInt(document.getElementById('skills').value) || 0
        };

        this.saveProgress();
        this.hideModal();
        this.showNotification('Progress updated successfully!', 'success');
        
        // Show motivation message based on progress
        this.showMotivationMessage();
    }

    showMotivationMessage() {
        const total = this.progress.applications + this.progress.interviews + this.progress.offers + this.progress.skills;
        
        let message = '';
        if (total === 0) {
            message = "Ready to start your career advancement journey? Let's get your first application in!";
        } else if (total < 5) {
            message = "Great start! Keep building momentum with more applications.";
        } else if (total < 10) {
            message = "Excellent progress! You're building a strong foundation for success.";
        } else if (this.progress.offers > 0) {
            message = "Congratulations on your offers! You're making great progress toward your goals.";
        } else {
            message = "Outstanding dedication! Your persistence will pay off with the right opportunity.";
        }
        
        this.showNotification(message, 'info');
    }

    downloadReport() {
        const report = this.generateReport();
        const blob = new Blob([report], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `career-advancement-report-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        window.URL.revokeObjectURL(url);
        
        this.trackEvent('report_download');
        this.showNotification('Report downloaded successfully!', 'success');
    }

    generateReport() {
        let report = 'CAREER ADVANCEMENT REPORT\n';
        report += '========================\n\n';
        report += `Generated: ${new Date().toLocaleString()}\n`;
        report += `Session ID: ${this.sessionId}\n\n`;
        
        report += 'CURRENT POSITION\n';
        report += '================\n';
        report += `Field: ${this.userProfile.field_expertise?.primary_field || 'Not specified'}\n`;
        report += `Experience Level: ${this.userProfile.experience_level || 'Not specified'}\n`;
        report += `Current Salary: $${(this.userProfile.income_position?.estimated_salary || 0).toLocaleString()}\n`;
        report += `Market Percentile: ${(this.userProfile.income_position?.percentile || 0).toFixed(1)}%\n\n`;
        
        report += 'RECOMMENDED OPPORTUNITIES\n';
        report += '========================\n\n';
        
        Object.entries(this.recommendations).forEach(([tier, job]) => {
            report += `${tier.toUpperCase()} OPPORTUNITY\n`;
            report += `Title: ${job.title}\n`;
            report += `Company: ${job.company}\n`;
            report += `Location: ${job.location}\n`;
            report += `Salary: $${job.salary_range.min.toLocaleString()} - $${job.salary_range.max.toLocaleString()}\n`;
            report += `Success Probability: ${(this.successProbabilities[tier] * 100).toFixed(0)}%\n`;
            report += `Skills Match: ${(job.skill_gap_analysis?.skills_match_percentage * 100 || 0).toFixed(0)}%\n\n`;
        });
        
        report += 'PROGRESS SUMMARY\n';
        report += '================\n';
        report += `Applications Submitted: ${this.progress.applications}\n`;
        report += `Interviews Scheduled: ${this.progress.interviews}\n`;
        report += `Offers Received: ${this.progress.offers}\n`;
        report += `Skills Developed: ${this.progress.skills}\n\n`;
        
        report += 'NEXT STEPS\n';
        report += '==========\n';
        report += '1. Apply to recommended opportunities\n';
        report += '2. Develop missing skills through learning resources\n';
        report += '3. Network with professionals in your target companies\n';
        report += '4. Follow up on applications within 3-5 business days\n';
        report += '5. Prepare for interviews with company research\n\n';
        
        return report;
    }

    shareResults() {
        if (navigator.share) {
            navigator.share({
                title: 'My Career Advancement Opportunities',
                text: 'Check out my personalized job recommendations from Mingus!',
                url: window.location.href
            }).then(() => {
                this.trackEvent('results_shared_native');
            });
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(window.location.href).then(() => {
                this.showNotification('Link copied to clipboard!', 'success');
                this.trackEvent('results_shared_clipboard');
            }).catch(() => {
                this.showNotification('Unable to copy link. Please share manually.', 'error');
            });
        }
    }

    showModal(title, content, buttonText, buttonAction) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal" role="dialog" aria-labelledby="modal-title">
                <div class="modal-header">
                    <h3 id="modal-title">${title}</h3>
                    <button onclick="jobRecommendations.hideModal()" class="modal-close" aria-label="Close modal">&times;</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    <button onclick="jobRecommendations.hideModal()" class="btn btn-secondary">Cancel</button>
                    ${buttonText ? `<button onclick="jobRecommendations.executeModalAction()" class="btn btn-primary">${buttonText}</button>` : ''}
                </div>
            </div>
        `;
        
        // Store action for execution
        modal.dataset.action = buttonAction ? buttonAction.toString() : '';
        
        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('show'), 10);
        
        // Focus management
        const firstFocusable = modal.querySelector('button, input, textarea, select');
        if (firstFocusable) {
            firstFocusable.focus();
        }
    }

    hideModal() {
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300);
        }
    }

    executeModalAction() {
        const modal = document.querySelector('.modal-overlay');
        if (modal && modal.dataset.action) {
            eval(modal.dataset.action);
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.setAttribute('role', 'alert');
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button onclick="this.parentElement.remove()" class="notification-close" aria-label="Close notification">&times;</button>
        `;
        
        document.body.appendChild(notification);
        setTimeout(() => notification.classList.add('show'), 10);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    saveProgress() {
        localStorage.setItem('careerProgress', JSON.stringify(this.progress));
        this.updateProgressDisplay();
    }

    saveReminder(reminder) {
        const reminders = JSON.parse(localStorage.getItem('careerReminders') || '[]');
        reminders.push(reminder);
        localStorage.setItem('careerReminders', JSON.stringify(reminders));
    }

    handleKeyboardNavigation(e) {
        if (e.key === 'Escape') {
            this.hideModal();
        }
        
        // Tab navigation for modals
        if (e.key === 'Tab') {
            const modal = document.querySelector('.modal-overlay');
            if (modal) {
                const focusableElements = modal.querySelectorAll('button, input, textarea, select, [tabindex]:not([tabindex="-1"])');
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                } else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        }
    }

    setupAccessibility() {
        // Add ARIA labels and roles
        document.querySelectorAll('.recommendation-card').forEach((card, index) => {
            card.setAttribute('role', 'article');
            card.setAttribute('aria-labelledby', `job-title-${index}`);
        });

        // Add skip links
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'sr-only sr-only-focusable';
        skipLink.textContent = 'Skip to main content';
        document.body.insertBefore(skipLink, document.body.firstChild);

        // Add focus indicators
        document.addEventListener('focusin', (e) => {
            if (e.target.matches('button, input, textarea, select, a')) {
                e.target.classList.add('focus-visible');
            }
        });

        document.addEventListener('focusout', (e) => {
            e.target.classList.remove('focus-visible');
        });
    }

    trackEvent(event, data = {}) {
        // Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', event, {
                event_category: 'career_advancement',
                event_label: this.sessionId,
                ...data
            });
        }
        
        // Custom tracking
        console.log('Event tracked:', event, data);
        
        // Send to backend if needed
        this.sendAnalytics(event, data);
    }

    async sendAnalytics(event, data) {
        try {
            await fetch('/api/analytics/track', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    event,
                    data,
                    session_id: this.sessionId,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.log('Analytics tracking failed:', error);
        }
    }
}

// Initialize the interface when DOM is loaded
let jobRecommendations;

document.addEventListener('DOMContentLoaded', function() {
    jobRecommendations = new JobRecommendationsInterface();
});

// Service Worker for offline functionality
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('SW registered: ', registration);
            })
            .catch(function(registrationError) {
                console.log('SW registration failed: ', registrationError);
            });
    });
}

// Export for global access
window.jobRecommendations = jobRecommendations; 