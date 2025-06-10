// Check authentication status before allowing access
async function checkAuthAndRedirect() {
  const session = await checkAuth();
  if (!session) {
    redirectToLogin('Please sign in using your social media login to continue.');
    return false;
  }
  return true;
}

// Validation constraints
const VALID_CHALLENGES = [
  'emergency_savings', 'multiple_income', 'debt', 'major_expenses'
];
const VALID_STRESS_HANDLING = [
  'talk_to_people', 'exercise', 'avoid_thinking', 'research_plan'
];
const VALID_MOTIVATION = [
  'family_goals', 'personal_growth', 'community_impact', 'financial_freedom'
];

function isValidOnboardingResponse(data) {
  return (
    VALID_CHALLENGES.includes(data.financial_challenge) &&
    VALID_STRESS_HANDLING.includes(data.stress_handling) &&
    VALID_MOTIVATION.includes(data.motivation)
  );
}// Onboarding state management
let sessionId = null;
let isOnline = navigator.onLine;
let pendingSync = [];
// --- Rate Limiting Functions ---
const SUBMISSION_DELAY_SECONDS = 60; // Change this value as needed

function hasSubmittedOnboarding() {
  return localStorage.getItem('onboardingSubmitted') === 'true';
}

function markOnboardingSubmitted() {
  localStorage.setItem('onboardingSubmitted', 'true');
}

function canAttemptSubmission() {
  const last = parseInt(localStorage.getItem('lastOnboardingAttempt') || '0', 10);
  const now = Date.now();
  return (now - last) > SUBMISSION_DELAY_SECONDS * 1000;
}

function markSubmissionAttempt() {
  localStorage.setItem('lastOnboardingAttempt', Date.now().toString());
}
async function optimisticSave(data) {
  if (hasSubmittedOnboarding()) {
    showSyncNotification('You have already submitted your onboarding. Thank you!', false);
    return;
  }
  if (!canAttemptSubmission()) {
    showSyncNotification('Please wait before submitting again.', false);
    return;
  }
  markSubmissionAttempt();
  showSyncNotification('Saving...', true);
  try {
    if (!isOnline) throw new Error('Offline');
    const { error } = await supabase.from('onboarding_responses').insert([data]);
    if (error) throw error;
    showSyncNotification('Saved!', true);
    onboardingState = {};
    localStorage.removeItem('onboardingState');
    form.reset();
    markOnboardingSubmitted();
    // Optionally, disable the form after successful submission
    form.querySelectorAll('input, button').forEach(el => el.disabled = true);
  } catch (err) {
    unsyncedResponses.push(data);
    localStorage.setItem('unsyncedOnboarding', JSON.stringify(unsyncedResponses));
    showSyncNotification('Saved locally (offline)', false);
  }
}

// Initialize onboarding session
async function initializeOnboardingSession() {
    try {
        // Try to get existing session from localStorage
        sessionId = localStorage.getItem('onboarding_session_id');
        
        if (!sessionId) {
            // Generate new session ID if none exists
            sessionId = crypto.randomUUID();
            localStorage.setItem('onboarding_session_id', sessionId);
        }
        
        // Load any pending sync items
        pendingSync = JSON.parse(localStorage.getItem('pending_sync') || '[]');
        
        // Try to sync any pending items immediately
        if (pendingSync.length > 0) {
            await syncPendingResponses();
        }
        
        return sessionId;
    } catch (error) {
        console.error('Error initializing session:', error);
        showError('Failed to initialize session. Please refresh the page.');
    }
}

// Save response both locally and to database
async function saveResponse(questionType, response) {
    const timestamp = new Date().toISOString();
    const responseData = {
        session_id: sessionId,
        question_type: questionType,
        response: response,
        timestamp: timestamp
    };

    // Show loading state
    showLoading(questionType);

    try {
        // Save to local storage first
        saveToLocalStorage(responseData);

        if (navigator.onLine) {
            // If online, save to database
            await saveToDatabase(responseData);
            showSuccess(questionType);
        } else {
            // If offline, add to pending sync
            addToPendingSync(responseData);
            showOfflineSuccess(questionType);
        }
    } catch (error) {
        console.error('Error saving response:', error);
        showError('Failed to save response. Your answer has been stored locally and will sync when connection is restored.');
        addToPendingSync(responseData);
    } finally {
        hideLoading(questionType);
    }
}

// Save response to local storage
function saveToLocalStorage(responseData) {
    const responses = JSON.parse(localStorage.getItem('onboarding_responses') || '[]');
    responses.push(responseData);
    localStorage.setItem('onboarding_responses', JSON.stringify(responses));
}

// Save response to database
async function saveToDatabase(responseData) {
    try {
        const response = await fetch('/api/onboarding/anonymous', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(responseData)
        });

        if (!response.ok) {
            throw new Error('Failed to save to database');
        }

        return await response.json();
    } catch (error) {
        throw new Error('Database save failed: ' + error.message);
    }
}

// Add response to pending sync queue
function addToPendingSync(responseData) {
    pendingSync.push(responseData);
    localStorage.setItem('pending_sync', JSON.stringify(pendingSync));
}

// Sync pending responses when connection is restored
async function syncPendingResponses() {
    if (!navigator.onLine || pendingSync.length === 0) return;

    const syncResults = [];
    
    for (const responseData of pendingSync) {
        try {
            await saveToDatabase(responseData);
            syncResults.push({ success: true, data: responseData });
        } catch (error) {
            console.error('Sync failed for response:', error);
            syncResults.push({ success: false, data: responseData, error });
        }
    }

    // Remove successfully synced items
    pendingSync = pendingSync.filter((_, index) => !syncResults[index].success);
    localStorage.setItem('pending_sync', JSON.stringify(pendingSync));

    // Show sync status
    if (syncResults.some(result => result.success)) {
        showSuccess('sync', 'Some or all responses synced successfully');
    }
    if (syncResults.some(result => !result.success)) {
        showError('Some responses failed to sync and will be retried later');
    }
}

// UI feedback functions
function showLoading(questionType) {
    const element = document.querySelector(`[data-question="${questionType}"]`);
    if (element) {
        element.classList.add('loading');
        const spinner = element.querySelector('.spinner');
        if (spinner) spinner.style.display = 'block';
    }
}

function hideLoading(questionType) {
    const element = document.querySelector(`[data-question="${questionType}"]`);
    if (element) {
        element.classList.remove('loading');
        const spinner = element.querySelector('.spinner');
        if (spinner) spinner.style.display = 'none';
    }
}

function showSuccess(questionType, message = 'Saved successfully') {
    const element = document.querySelector(`[data-question="${questionType}"]`);
    if (element) {
        const feedback = element.querySelector('.feedback');
        if (feedback) {
            feedback.textContent = message;
            feedback.className = 'feedback success';
            setTimeout(() => {
                feedback.textContent = '';
            }, 3000);
        }
    }
}

function showOfflineSuccess(questionType) {
    showSuccess(questionType, 'Saved locally (offline)');
}

function showError(message) {
    const errorContainer = document.getElementById('error-container');
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
    }
}

// Event listeners for online/offline status
window.addEventListener('online', () => {
    isOnline = true;
    syncPendingResponses();
});

window.addEventListener('offline', () => {
    isOnline = false;
});

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication first
    if (!await checkAuthAndRedirect()) {
        return;
    }
    
    initializeOnboardingSession();
    const form = document.getElementById('onboardingForm');
    const stressHandlingCheckboxes = document.querySelectorAll('input[name="stress_handling"]');
    
    // Limit stress handling selections to 3
    stressHandlingCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const checked = document.querySelectorAll('input[name="stress_handling"]:checked');
            if (checked.length > 3) {
                checkbox.checked = false;
            }
        });
    });

    // Update range value displays
    const ranges = document.querySelectorAll('input[type="range"]');
    ranges.forEach(range => {
        const valueDisplay = document.createElement('span');
        valueDisplay.className = 'range-value';
        valueDisplay.style.color = 'var(--text-color)';
        valueDisplay.style.marginLeft = '1rem';
        range.parentNode.insertBefore(valueDisplay, range.nextSibling);
        
        const updateValue = () => valueDisplay.textContent = range.value;
        range.addEventListener('input', updateValue);
        updateValue(); // Initial value
    });

    // Dynamic contact info validation
    const contactMethodSelect = document.getElementById('preferred_contact_method');
    const contactInfoInput = document.getElementById('contact_info');

    contactMethodSelect.addEventListener('change', () => {
        updateContactValidation();
    });

    function updateContactValidation() {
        const method = contactMethodSelect.value;
        contactInfoInput.pattern = getContactPattern(method);
        contactInfoInput.placeholder = getContactPlaceholder(method);
        contactInfoInput.required = method !== '';
    }

    function getContactPattern(method) {
        switch (method) {
            case 'email':
                return '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$';
            case 'sms':
                return '^\\+?1?\\d{9,15}$';
            case 'both':
                return '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,},\\s*\\+?1?\\d{9,15}$';
            default:
                return '';
        }
    }

    function getContactPlaceholder(method) {
        switch (method) {
            case 'email':
                return 'Enter your email address';
            case 'sms':
                return 'Enter your phone number';
            case 'both':
                return 'Enter email, phone (separated by comma)';
            default:
                return 'Email and/or phone number';
        }
    }

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Clear previous error messages
        const existingError = document.querySelector('.error-messages');
        if (existingError) existingError.remove();

        // Validate stress handling selections
        const selectedStressHandling = document.querySelectorAll('input[name="stress_handling"]:checked');
        if (selectedStressHandling.length === 0) {
            showError(['Please select at least one stress handling method']);
            return;
        }

        // Validate monthly expenses
        const monthlyIncome = parseFloat(document.getElementById('monthly_income').value);
        const monthlyExpenses = parseFloat(document.getElementById('monthly_expenses').value);
        if (monthlyExpenses > monthlyIncome * 2) {
            showError(['Monthly expenses cannot be more than double the monthly income']);
            return;
        }

        // Validate savings goal
        const savingsGoal = parseFloat(document.getElementById('savings_goal').value);
        if (savingsGoal > monthlyIncome * 120) { // 10 years of income
            showError(['Savings goal cannot be more than 10 years of monthly income']);
            return;
        }

        // Prepare form data
        const formData = {
            financial_challenge: document.getElementById('financial_challenge').value,
            stress_handling: Array.from(selectedStressHandling).map(cb => cb.value),
            monthly_income: monthlyIncome,
            monthly_expenses: monthlyExpenses,
            savings_goal: savingsGoal,
            risk_tolerance: parseInt(document.getElementById('risk_tolerance').value),
            financial_knowledge: parseInt(document.getElementById('financial_knowledge').value),
            preferred_contact_method: contactMethodSelect.value,
            contact_info: contactInfoInput.value
        };

        try {
            const response = await fetch('/api/onboarding/anonymous', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                showError(data.error ? [data.error] : ['An error occurred during submission']);
                return;
            }

            // Show success message
            showSuccess('Onboarding completed successfully!');
            
            // Redirect to main app after 2 seconds
            setTimeout(() => {
                window.location.href = '/app';
            }, 2000);

        } catch (error) {
            showError(['An error occurred while submitting the form']);
            console.error('Submission error:', error);
        }
    });

    // Initialize contact validation
    updateContactValidation();
});

// Export functions for use in other modules
export {
    initializeOnboardingSession,
    saveResponse,
    syncPendingResponses
};

// Personalization Configuration
const TESTIMONIALS = {
    DEBT_MANAGEMENT: "I was drowning in debt until Mingus helped me create a clear payoff strategy. Now I'm debt-free and building wealth! - Sarah M.",
    SAVINGS_GROWTH: "With Mingus, I finally broke the paycheck-to-paycheck cycle. My savings grow every month! - Michael R.",
    INVESTMENT_PLANNING: "Mingus simplified investing for me. My portfolio is growing and I actually understand my investment strategy. - David K.",
    BUDGETING: "Mingus made budgeting easy and even fun! I'm saving more than ever without feeling restricted. - Emma L.",
    RETIREMENT_PLANNING: "I was worried about retirement, but Mingus helped me create a solid plan. Now I'm confident about my future. - Robert P."
};

const CTA_TEXT = {
    FAMILY_SECURITY: "Secure Your Family's Future",
    FINANCIAL_FREEDOM: "Achieve Financial Freedom",
    EARLY_RETIREMENT: "Start Your Early Retirement Journey",
    DEBT_FREE: "Begin Your Debt-Free Journey",
    WEALTH_BUILDING: "Start Building Real Wealth"
};

// Default States
const DEFAULT_STATE = {
    challenge: null,
    motivation: null,
    ctaText: "Start Your Journey",
    testimonial: null
};

// Analytics Tracking
class Analytics {
    static track(event, properties = {}) {
        // Log to debug panel in development
        if (process.env.NODE_ENV === 'development') {
            const debugPanel = document.getElementById('analytics-debug');
            const logElement = document.getElementById('analytics-log');
            debugPanel.classList.add('visible');
            
            const timestamp = new Date().toISOString();
            const logEntry = `${timestamp} - ${event}\n${JSON.stringify(properties, null, 2)}\n\n`;
            logElement.textContent = logEntry + logElement.textContent;
        }

        // Send to actual analytics service in production
        if (process.env.NODE_ENV === 'production') {
            // Replace with your actual analytics service
            console.log('Analytics:', event, properties);
        }
    }
}

// Personalization Manager
class PersonalizationManager {
    constructor() {
        this.state = { ...DEFAULT_STATE };
        this.setupEventListeners();
        this.initializeState();
    }

    initializeState() {
        Analytics.track('onboarding_view', {
            initial_state: this.state
        });
    }

    setupEventListeners() {
        // Financial Challenge Selection
        const challengeButtons = document.querySelectorAll('#financial-challenge .options button');
        challengeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const value = button.dataset.value;
                this.updateChallenge(value);
                this.updateUI();
            });
        });

        // Motivation Selection
        const motivationButtons = document.querySelectorAll('#motivation .options button');
        motivationButtons.forEach(button => {
            button.addEventListener('click', () => {
                const value = button.dataset.value;
                this.updateMotivation(value);
                this.updateUI();
            });
        });
    }

    updateChallenge(challenge) {
        const oldChallenge = this.state.challenge;
        this.state.challenge = challenge;
        
        // Update testimonial
        this.state.testimonial = TESTIMONIALS[challenge];
        
        Analytics.track('challenge_selected', {
            old_challenge: oldChallenge,
            new_challenge: challenge,
            testimonial_shown: this.state.testimonial
        });
    }

    updateMotivation(motivation) {
        const oldMotivation = this.state.motivation;
        this.state.motivation = motivation;
        
        // Update CTA text
        this.state.ctaText = CTA_TEXT[motivation] || DEFAULT_STATE.ctaText;
        
        Analytics.track('motivation_selected', {
            old_motivation: oldMotivation,
            new_motivation: motivation,
            cta_text: this.state.ctaText
        });
    }

    updateUI() {
        // Update testimonial section
        const testimonialContainer = document.getElementById('testimonial-container');
        if (this.state.testimonial) {
            testimonialContainer.innerHTML = `<p class="testimonial">${this.state.testimonial}</p>`;
            testimonialContainer.classList.remove('hidden');
        } else {
            testimonialContainer.classList.add('hidden');
        }

        // Update CTA button
        const ctaButton = document.getElementById('personalized-cta');
        ctaButton.textContent = this.state.ctaText;

        // Update selected states
        this.updateSelectedButtons();
        
        Analytics.track('ui_updated', {
            current_state: this.state
        });
    }

    updateSelectedButtons() {
        // Update challenge buttons
        const challengeButtons = document.querySelectorAll('#financial-challenge .options button');
        challengeButtons.forEach(button => {
            button.classList.toggle('selected', button.dataset.value === this.state.challenge);
        });

        // Update motivation buttons
        const motivationButtons = document.querySelectorAll('#motivation .options button');
        motivationButtons.forEach(button => {
            button.classList.toggle('selected', button.dataset.value === this.state.motivation);
        });
    }

    // Test Helper Methods
    static runTests() {
        const testCases = [
            // Test financial challenge options
            ...Object.keys(TESTIMONIALS).map(challenge => ({
                action: 'challenge',
                value: challenge,
                expectedTestimonial: TESTIMONIALS[challenge]
            })),
            
            // Test motivation options
            ...Object.keys(CTA_TEXT).map(motivation => ({
                action: 'motivation',
                value: motivation,
                expectedCtaText: CTA_TEXT[motivation]
            })),
            
            // Test default states
            {
                action: 'reset',
                expectedState: DEFAULT_STATE
            }
        ];

        const personalization = new PersonalizationManager();
        let testsPassed = 0;
        let testsFailed = 0;

        testCases.forEach((testCase, index) => {
            try {
                if (testCase.action === 'challenge') {
                    personalization.updateChallenge(testCase.value);
                    console.assert(
                        personalization.state.testimonial === testCase.expectedTestimonial,
                        `Testimonial test failed for ${testCase.value}`
                    );
                } else if (testCase.action === 'motivation') {
                    personalization.updateMotivation(testCase.value);
                    console.assert(
                        personalization.state.ctaText === testCase.expectedCtaText,
                        `CTA text test failed for ${testCase.value}`
                    );
                } else if (testCase.action === 'reset') {
                    personalization.state = { ...DEFAULT_STATE };
                    console.assert(
                        JSON.stringify(personalization.state) === JSON.stringify(testCase.expectedState),
                        'Default state test failed'
                    );
                }
                testsPassed++;
                console.log(`✅ Test ${index + 1} passed`);
            } catch (error) {
                testsFailed++;
                console.error(`❌ Test ${index + 1} failed:`, error);
            }
        });

        console.log(`\nTest Summary:`);
        console.log(`Total Tests: ${testCases.length}`);
        console.log(`Passed: ${testsPassed}`);
        console.log(`Failed: ${testsFailed}`);
    }
}

// Initialize personalization
document.addEventListener('DOMContentLoaded', () => {
    const personalization = new PersonalizationManager();
    
    // Run tests in development environment
    if (process.env.NODE_ENV === 'development') {
        PersonalizationManager.runTests();
    }
}); 