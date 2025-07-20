// cypress/e2e/complete-user-journey.cy.js
// Complete end-to-end test for user journey: Registration → Onboarding → Dashboard

describe('Complete User Journey: Registration to Dashboard', () => {
  const baseUrl = 'http://127.0.0.1:5002'
  
  // Sample user data for testing
  const testUser = {
    email: `testuser${Date.now()}@example.com`,
    password: 'TestPass123!',
    fullName: 'Test User',
    phoneNumber: '1234567890'
  }

  beforeEach(() => {
    cy.clearCookies()
    cy.clearLocalStorage()
    cy.clearSessionStorage()
  })

  it('should complete full user journey: register → login → onboarding → dashboard', () => {
    // Step 1: Register a new user
    cy.log('Step 1: User Registration')
    cy.visit(`${baseUrl}/api/auth/register`)
    
    // Fill out registration form
    cy.get('input[name="email"]').type(testUser.email)
    cy.get('input[name="password"]').type(testUser.password)
    cy.get('input[name="full_name"]').type(testUser.fullName)
    cy.get('input[name="phone_number"]').type(testUser.phoneNumber)
    
    // Submit registration
    cy.get('button[type="submit"]').click()
    
    // Should redirect to onboarding after successful registration
    cy.url().should('include', '/api/health/onboarding')
    cy.log('✅ Registration successful, redirected to onboarding')

    // Step 2: Complete 4-step onboarding process
    cy.log('Step 2: Health Onboarding Process')
    
    // Verify we're on the onboarding page
    cy.get('.onboarding-container').should('exist')
    cy.get('.progress-text').should('contain', 'Step 1 of 4')
    
    // Step 2.1: Welcome/Introduction (Step 1)
    cy.log('Step 2.1: Welcome Introduction')
    cy.get('#step1').should('have.class', 'active')
    cy.get('.step-title').should('contain', 'Discover How Your Wellness Affects Your Wealth')
    cy.get('#startBtn').should('be.visible').and('contain', 'Start My Wellness Journey')
    
    // Click to start onboarding
    cy.get('#startBtn').click()
    
    // Step 2.2: Health Check-in (Step 2)
    cy.log('Step 2.2: Health Check-in')
    cy.get('#step2').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 2 of 4')
    cy.get('.step-title').should('contain', 'Your First Wellness Check-in')
    
    // Fill out health check-in form with sample data
    cy.get('#stressLevel').invoke('val', 6).trigger('change')
    cy.get('#energyLevel').invoke('val', 7).trigger('change')
    cy.get('#moodRating').invoke('val', 8).trigger('change')
    cy.get('#relationshipsRating').invoke('val', 7).trigger('change')
    
    // Fill in optional fields
    cy.get('input[placeholder*="minutes"]').first().type('45') // Physical activity
    cy.get('input[placeholder*="minutes"]').eq(1).type('20')   // Mindfulness
    
    // Select activity level
    cy.get('select[name="physical_activity_level"]').select('moderate')
    
    // Select mindfulness type
    cy.get('select[name="mindfulness_type"]').select('meditation')
    
    // Complete check-in
    cy.get('#completeCheckinBtn').click()
    
    // Step 2.3: Timeline Setup (Step 3)
    cy.log('Step 2.3: Timeline Setup')
    cy.get('#step3').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 3 of 4')
    cy.get('.step-title').should('contain', 'Building Your Insight Timeline')
    
    // Verify timeline elements exist
    cy.get('.timeline').should('exist')
    cy.get('.timeline-item').should('have.length.at.least', 1)
    
    // Set up reminders
    cy.get('#setupRemindersBtn').click()
    
    // Step 2.4: Goal Setting (Step 4)
    cy.log('Step 2.4: Goal Setting')
    cy.get('#step4').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 4 of 4')
    cy.get('.step-title').should('contain', "What's Your Wellness-Wealth Goal?")
    
    // Verify goals are displayed
    cy.get('.goals-grid').should('exist')
    cy.get('.goal-card').should('have.length', 5)
    
    // Select multiple wellness goals
    cy.get('.goal-card[data-goal="stress-spending"]').click()
    cy.get('.goal-card[data-goal="health-costs"]').click()
    cy.get('.goal-card[data-goal="energy-productivity"]').click()
    
    // Verify goals are selected
    cy.get('.goal-card.selected').should('have.length', 3)
    
    // Complete onboarding
    cy.get('#finishOnboardingBtn').should('contain', 'Start My Journey (3 goals)')
    cy.get('#finishOnboardingBtn').click()
    
    // Step 3: Verify redirect to dashboard
    cy.log('Step 3: Dashboard Access')
    cy.url().should('include', '/api/health/dashboard')
    cy.log('✅ Onboarding completed, redirected to dashboard')

    // Step 4: Verify dashboard content
    cy.log('Step 4: Dashboard Verification')
    
    // Check for dashboard elements
    cy.get('.dashboard-container').should('exist')
    cy.get('.welcome-message').should('contain', testUser.fullName)
    
    // Verify health summary is displayed
    cy.get('.health-summary').should('exist')
    cy.get('.health-metrics').should('exist')
    
    // Check for recent check-in data
    cy.get('.recent-checkin').should('exist')
    cy.get('.checkin-date').should('exist')
    
    // Verify wellness goals are displayed
    cy.get('.wellness-goals').should('exist')
    cy.get('.goal-item').should('have.length', 3)
    
    // Check for insights or recommendations
    cy.get('.insights-section').should('exist')
    cy.get('.recommendation-card').should('exist')
    
    cy.log('✅ Dashboard loaded successfully with user data')
  })

  it('should handle login flow for existing user', () => {
    // First register a user
    cy.log('Preparing: Register test user')
    cy.visit(`${baseUrl}/api/auth/register`)
    cy.get('input[name="email"]').type(testUser.email)
    cy.get('input[name="password"]').type(testUser.password)
    cy.get('input[name="full_name"]').type(testUser.fullName)
    cy.get('input[name="phone_number"]').type(testUser.phoneNumber)
    cy.get('button[type="submit"]').click()
    
    // Complete onboarding quickly
    cy.url().should('include', '/api/health/onboarding')
    cy.get('#startBtn').click()
    cy.get('#completeCheckinBtn').click()
    cy.get('#setupRemindersBtn').click()
    cy.get('.goal-card[data-goal="stress-spending"]').click()
    cy.get('#finishOnboardingBtn').click()
    
    // Now test login flow
    cy.log('Step 1: Login with existing user')
    cy.visit(`${baseUrl}/api/auth/login`)
    
    // Fill login form
    cy.get('input[name="email"]').type(testUser.email)
    cy.get('input[name="password"]').type(testUser.password)
    cy.get('button[type="submit"]').click()
    
    // Should redirect to dashboard
    cy.url().should('include', '/api/health/dashboard')
    cy.get('.dashboard-container').should('exist')
    cy.log('✅ Login successful, dashboard accessible')
  })

  it('should handle dashboard navigation and features', () => {
    // Register and complete onboarding first
    cy.log('Preparing: Complete user setup')
    cy.visit(`${baseUrl}/api/auth/register`)
    cy.get('input[name="email"]').type(testUser.email)
    cy.get('input[name="password"]').type(testUser.password)
    cy.get('input[name="full_name"]').type(testUser.fullName)
    cy.get('input[name="phone_number"]').type(testUser.phoneNumber)
    cy.get('button[type="submit"]').click()
    
    // Quick onboarding
    cy.url().should('include', '/api/health/onboarding')
    cy.get('#startBtn').click()
    cy.get('#completeCheckinBtn').click()
    cy.get('#setupRemindersBtn').click()
    cy.get('.goal-card[data-goal="stress-spending"]').click()
    cy.get('#finishOnboardingBtn').click()
    
    // Test dashboard features
    cy.log('Step 1: Dashboard Navigation')
    cy.url().should('include', '/api/health/dashboard')
    
    // Test navigation menu
    cy.get('.nav-menu').should('exist')
    cy.get('.nav-item').should('have.length.at.least', 3)
    
    // Test health check-in button
    cy.get('.checkin-button').should('exist').and('contain', 'Check In')
    cy.get('.checkin-button').click()
    
    // Should open check-in form or modal
    cy.get('.checkin-form').should('exist')
    cy.get('.checkin-form input[type="range"]').first().invoke('val', 5).trigger('change')
    cy.get('.checkin-form button[type="submit"]').click()
    
    // Should return to dashboard
    cy.url().should('include', '/api/health/dashboard')
    cy.log('✅ Health check-in completed')
    
    // Test profile access
    cy.get('.profile-link').click()
    cy.get('.profile-section').should('exist')
    cy.get('.user-info').should('contain', testUser.fullName)
    cy.get('.user-info').should('contain', testUser.email)
    
    // Return to dashboard
    cy.get('.dashboard-link').click()
    cy.url().should('include', '/api/health/dashboard')
    cy.log('✅ Profile navigation working')
  })

  it('should handle error scenarios gracefully', () => {
    cy.log('Step 1: Test invalid registration')
    cy.visit(`${baseUrl}/api/auth/register`)
    
    // Try to register with invalid data
    cy.get('input[name="email"]').type('invalid-email')
    cy.get('input[name="password"]').type('weak')
    cy.get('input[name="full_name"]').type('')
    cy.get('button[type="submit"]').click()
    
    // Should show validation errors
    cy.get('.error-message').should('exist')
    cy.log('✅ Validation errors displayed correctly')
    
    // Test login with non-existent user
    cy.log('Step 2: Test invalid login')
    cy.visit(`${baseUrl}/api/auth/login`)
    cy.get('input[name="email"]').type('nonexistent@example.com')
    cy.get('input[name="password"]').type('wrongpassword')
    cy.get('button[type="submit"]').click()
    
    // Should show login error
    cy.get('.error-message').should('exist')
    cy.log('✅ Login errors handled correctly')
    
    // Test accessing protected routes without auth
    cy.log('Step 3: Test unauthorized access')
    cy.visit(`${baseUrl}/api/health/dashboard`)
    cy.url().should('include', '/api/auth/login')
    cy.log('✅ Unauthorized access redirected to login')
  })

  it('should persist user data across sessions', () => {
    // Register and complete onboarding
    cy.log('Step 1: Complete initial setup')
    cy.visit(`${baseUrl}/api/auth/register`)
    cy.get('input[name="email"]').type(testUser.email)
    cy.get('input[name="password"]').type(testUser.password)
    cy.get('input[name="full_name"]').type(testUser.fullName)
    cy.get('input[name="phone_number"]').type(testUser.phoneNumber)
    cy.get('button[type="submit"]').click()
    
    // Complete onboarding
    cy.url().should('include', '/api/health/onboarding')
    cy.get('#startBtn').click()
    cy.get('#completeCheckinBtn').click()
    cy.get('#setupRemindersBtn').click()
    cy.get('.goal-card[data-goal="stress-spending"]').click()
    cy.get('#finishOnboardingBtn').click()
    
    // Verify dashboard loads
    cy.url().should('include', '/api/health/dashboard')
    cy.get('.dashboard-container').should('exist')
    
    // Reload page to test persistence
    cy.log('Step 2: Test data persistence')
    cy.reload()
    
    // Should still be on dashboard with user data
    cy.url().should('include', '/api/health/dashboard')
    cy.get('.dashboard-container').should('exist')
    cy.get('.welcome-message').should('contain', testUser.fullName)
    cy.get('.wellness-goals').should('exist')
    cy.log('✅ User data persists across page reloads')
  })
}) 