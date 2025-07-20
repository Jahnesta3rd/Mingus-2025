/**
 * Complete User Journey E2E Test
 * Tests the entire user experience from registration through all onboarding steps
 * to dashboard usage, goal setting, insights, and ongoing engagement
 */

describe('Complete User Journey', () => {
  let testUserData
  let sessionData

  beforeEach(() => {
    // Load comprehensive test data
    cy.fixture('onboarding-data').then((data) => {
      testUserData = data
    })

    // Clear cookies and local storage before each test
    cy.clearCookies()
    cy.clearLocalStorage()
    
    // Visit the application
    cy.visit('http://localhost:5002')
  })

  it('should complete full user journey from registration to active usage', () => {
    cy.log('=== STARTING COMPLETE USER JOURNEY TEST ===')

    // **STEP 1: Welcome & Registration**
    cy.log('Step 1: Welcome & Registration')
    cy.visit('http://localhost:5002/api/auth/register')
    cy.waitForPageLoad()
    
    // Verify welcome page elements
    cy.get('body').should('contain', 'Mingus')
    cy.get('input[name="email"]').should('be.visible')
    cy.get('input[name="password"]').should('be.visible')
    
    // Fill registration form
    cy.get('input[name="email"]').type(testUserData.user.email)
    cy.get('input[name="password"]').type(testUserData.user.password)
    cy.get('input[name="first_name"]').type(testUserData.user.firstName)
    cy.get('input[name="last_name"]').type(testUserData.user.lastName)
    cy.get('input[name="phone_number"]').type(testUserData.user.phoneNumber)
    
    // Accept terms of service
    cy.get('input[type="checkbox"]').check()
    
    // Submit registration
    cy.get('button[type="submit"]').click()
    
    // Verify email verification or redirect
    cy.url().should('include', '/onboarding').or('contain', 'verify')
    cy.log('Registration completed')

    // **STEP 2: Profile Setup**
    cy.log('Step 2: Profile Setup')
    cy.visit('http://localhost:5002/onboarding/profile')
    cy.waitForPageLoad()
    
    // Verify profile setup page
    cy.get('.onboarding-container').should('be.visible')
    cy.get('#progressText').should('contain', 'Step 2 of 9')
    
    // Fill basic information
    cy.get('#age').type(testUserData.healthProfile.age)
    cy.get('#gender').select(testUserData.healthProfile.gender)
    cy.get('#location').type('San Francisco, CA')
    cy.get('#income').type(testUserData.financialProfile.income)
    cy.get('#household-size').type('2')
    
    // Submit profile
    cy.get('#save-profile-btn').click()
    cy.wait(1000)
    cy.log('Profile setup completed')

    // **STEP 3: Baseline Assessment**
    cy.log('Step 3: Baseline Assessment')
    cy.visit('http://localhost:5002/onboarding/baseline')
    cy.waitForPageLoad()
    
    // Career Check-in
    cy.get('#company-name').type('Tech Corp')
    cy.get('#industry').select(testUserData.careerProfile.industry)
    cy.get('#job-title').type(testUserData.careerProfile.jobTitle)
    cy.get('#years-experience').type(testUserData.careerProfile.yearsExperience)
    cy.get('#job-satisfaction').select('satisfied')
    
    // Financial Snapshot
    cy.get('#monthly-income').type(testUserData.financialProfile.income)
    cy.get('#monthly-expenses').type(testUserData.financialProfile.expenses)
    cy.get('#current-savings').type(testUserData.financialProfile.savings)
    cy.get('#debt-amount').type(testUserData.financialProfile.debt)
    
    // Submit baseline
    cy.get('#save-baseline-btn').click()
    cy.wait(1000)
    cy.log('Baseline assessment completed')

    // **STEP 4: Personalization & Goal Setting**
    cy.log('Step 4: Personalization & Goal Setting')
    cy.visit('http://localhost:5002/onboarding/financial-goals')
    cy.waitForPageLoad()
    
    // Verify goal setting interface
    cy.get('.goal-type-card').should('have.length.at.least', 5)
    
    // Select goal types
    cy.get('.goal-type-card').contains('Emergency Fund').click()
    cy.get('.goal-type-card').contains('Home Purchase').click()
    cy.get('.goal-type-card').contains('Retirement Savings').click()
    
    // Configure first goal (Emergency Fund)
    cy.get('#emergency-fund-details').click()
    cy.get('input[placeholder="0"]').type('15000')
    cy.get('button').contains('1 year').click()
    cy.get('textarea').type('Building security for my family')
    cy.get('#save-goal-btn').click()
    cy.wait(500)
    
    // Configure second goal (Home Purchase)
    cy.get('#home-purchase-details').click()
    cy.get('input[placeholder="0"]').type('80000')
    cy.get('button').contains('2 years').click()
    cy.get('textarea').type('Buy a house in my childhood neighborhood')
    cy.get('#save-goal-btn').click()
    cy.wait(500)
    
    // Verify smart suggestions and feasibility analysis
    cy.get('.smart-suggestions').should('be.visible')
    cy.get('.feasibility-checker').should('be.visible')
    cy.log('Goal setting completed')

    // **STEP 5: Education & Consent**
    cy.log('Step 5: Education & Consent')
    cy.visit('http://localhost:5002/onboarding/education')
    cy.waitForPageLoad()
    
    // Verify education content
    cy.get('.education-content').should('be.visible')
    cy.get('body').should('contain', 'How It Works')
    cy.get('body').should('contain', 'Data Privacy')
    
    // Accept data consent
    cy.get('#data-consent-checkbox').check()
    cy.get('#privacy-policy-checkbox').check()
    cy.get('#terms-of-service-checkbox').check()
    
    // Submit consent
    cy.get('#accept-consent-btn').click()
    cy.wait(1000)
    cy.log('Education & consent completed')

    // **STEP 6: Initial Insights**
    cy.log('Step 6: Initial Insights')
    cy.visit('http://localhost:5002/onboarding/insights')
    cy.waitForPageLoad()
    
    // Verify insights are generated
    cy.get('.insights-container').should('be.visible')
    cy.get('.job-security-score').should('be.visible')
    cy.get('.emergency-fund-recommendation').should('be.visible')
    cy.get('.cash-flow-analysis').should('be.visible')
    
    // Verify empowering language
    cy.get('body').should('contain', 'Great job')
    cy.get('body').should('contain', 'You\'re on track')
    cy.get('body').should('contain', 'Next steps')
    
    // Continue to next step
    cy.get('#continue-to-premium-btn').click()
    cy.wait(1000)
    cy.log('Initial insights completed')

    // **STEP 7: Premium Preview**
    cy.log('Step 7: Premium Preview')
    cy.visit('http://localhost:5002/onboarding/premium')
    cy.waitForPageLoad()
    
    // Verify premium features display
    cy.get('.tier-comparison').should('be.visible')
    cy.get('.feature-list').should('be.visible')
    cy.get('.testimonials').should('be.visible')
    
    // Skip premium for now (continue with free tier)
    cy.get('#continue-free-btn').click()
    cy.wait(1000)
    cy.log('Premium preview completed')

    // **STEP 8: App Tour**
    cy.log('Step 8: App Tour')
    cy.visit('http://localhost:5002/onboarding/tour')
    cy.waitForPageLoad()
    
    // Verify tour interface
    cy.get('.tour-container').should('be.visible')
    cy.get('.tour-step').should('be.visible')
    
    // Complete tour steps
    cy.get('#next-tour-step').click()
    cy.wait(500)
    cy.get('#next-tour-step').click()
    cy.wait(500)
    cy.get('#next-tour-step').click()
    cy.wait(500)
    
    // Complete tour
    cy.get('#finish-tour-btn').click()
    cy.wait(1000)
    cy.log('App tour completed')

    // **STEP 9: Onboarding Completion**
    cy.log('Step 9: Onboarding Completion')
    cy.visit('http://localhost:5002/onboarding/completion')
    cy.waitForPageLoad()
    
    // Verify congratulations screen
    cy.get('.congratulations-container').should('be.visible')
    cy.get('body').should('contain', 'Congratulations')
    cy.get('body').should('contain', 'You\'re all set')
    
    // Set up engagement preferences
    cy.get('#weekly-checkin-checkbox').check()
    cy.get('#reminder-frequency').select('weekly')
    cy.get('#notification-preferences').check()
    
    // Complete onboarding
    cy.get('#complete-onboarding-btn').click()
    cy.wait(2000)
    cy.log('Onboarding completion finished')

    // **STEP 10: Dashboard Access & Usage**
    cy.log('Step 10: Dashboard Access & Usage')
    cy.visit('http://localhost:5002/dashboard')
    cy.waitForPageLoad()
    
    // Verify dashboard elements
    cy.get('.dashboard-container').should('be.visible')
    cy.get('.health-summary').should('be.visible')
    cy.get('.financial-overview').should('be.visible')
    cy.get('.goals-progress').should('be.visible')
    cy.get('.insights-cards').should('be.visible')
    
    // Test dashboard navigation
    cy.get('#goals-tab').click()
    cy.get('.goals-list').should('be.visible')
    
    cy.get('#insights-tab').click()
    cy.get('.insights-list').should('be.visible')
    
    cy.get('#profile-tab').click()
    cy.get('.profile-settings').should('be.visible')
    
    cy.log('Dashboard access verified')

    // **STEP 11: Goal Management**
    cy.log('Step 11: Goal Management')
    cy.visit('http://localhost:5002/goals')
    cy.waitForPageLoad()
    
    // Verify goals are displayed
    cy.get('.goal-item').should('have.length.at.least', 2)
    cy.get('.goal-item').contains('Emergency Fund').should('be.visible')
    cy.get('.goal-item').contains('Home Purchase').should('be.visible')
    
    // Update goal progress
    cy.get('.goal-item').first().find('.update-progress-btn').click()
    cy.get('#progress-amount').type('5000')
    cy.get('#progress-notes').type('Monthly contribution')
    cy.get('#save-progress-btn').click()
    cy.wait(500)
    
    // Verify progress updated
    cy.get('.goal-progress-bar').should('contain', '33%')
    cy.log('Goal management completed')

    // **STEP 12: Insights & Recommendations**
    cy.log('Step 12: Insights & Recommendations')
    cy.visit('http://localhost:5002/insights')
    cy.waitForPageLoad()
    
    // Verify insights are personalized
    cy.get('.job-security-insight').should('be.visible')
    cy.get('.emergency-fund-insight').should('be.visible')
    cy.get('.cash-flow-insight').should('be.visible')
    cy.get('.health-relationship-insight').should('be.visible')
    
    // Test insight interactions
    cy.get('.insight-card').first().find('.learn-more-btn').click()
    cy.get('.insight-details').should('be.visible')
    cy.get('#close-insight-btn').click()
    cy.wait(500)
    
    cy.log('Insights & recommendations verified')

    // **STEP 13: Next Steps Checklist**
    cy.log('Step 13: Next Steps Checklist')
    cy.visit('http://localhost:5002/checklist')
    cy.waitForPageLoad()
    
    // Verify personalized checklist
    cy.get('.checklist-container').should('be.visible')
    cy.get('.checklist-item').should('have.length.at.least', 3)
    
    // Complete checklist items
    cy.get('.checklist-item').first().find('.complete-checkbox').check()
    cy.get('.checklist-item').eq(1).find('.complete-checkbox').check()
    
    // Verify progress updates
    cy.get('.checklist-progress').should('contain', '67%')
    cy.log('Next steps checklist completed')

    // **STEP 14: Notifications & Reminders**
    cy.log('Step 14: Notifications & Reminders')
    cy.visit('http://localhost:5002/notifications')
    cy.waitForPageLoad()
    
    // Verify notification preferences
    cy.get('.notification-preferences').should('be.visible')
    cy.get('#goal-reminders').check()
    cy.get('#insight-updates').check()
    cy.get('#weekly-checkins').check()
    
    // Save preferences
    cy.get('#save-notification-preferences').click()
    cy.wait(500)
    
    cy.log('Notifications & reminders configured')

    // **STEP 15: Profile & Settings**
    cy.log('Step 15: Profile & Settings')
    cy.visit('http://localhost:5002/profile')
    cy.waitForPageLoad()
    
    // Verify profile information
    cy.get('.profile-container').should('be.visible')
    cy.get('body').should('contain', testUserData.user.firstName)
    cy.get('body').should('contain', testUserData.user.lastName)
    cy.get('body').should('contain', testUserData.user.email)
    
    // Update profile
    cy.get('#edit-profile-btn').click()
    cy.get('#bio').type('Financial wellness enthusiast')
    cy.get('#save-profile-btn').click()
    cy.wait(500)
    
    cy.log('Profile & settings completed')

    // **STEP 16: Logout & Session Management**
    cy.log('Step 16: Logout & Session Management')
    cy.get('#user-menu').click()
    cy.get('#logout-btn').click()
    cy.wait(1000)
    
    // Verify logout
    cy.url().should('include', '/login')
    cy.get('body').should('contain', 'Sign In')
    
    // Test login with same credentials
    cy.get('input[name="email"]').type(testUserData.user.email)
    cy.get('input[name="password"]').type(testUserData.user.password)
    cy.get('button[type="submit"]').click()
    cy.wait(2000)
    
    // Verify successful login
    cy.url().should('include', '/dashboard')
    cy.get('.dashboard-container').should('be.visible')
    
    cy.log('=== COMPLETE USER JOURNEY TEST FINISHED ===')
  })

  it('should handle error scenarios gracefully', () => {
    cy.log('=== TESTING ERROR SCENARIOS ===')

    // Test invalid registration
    cy.visit('http://localhost:5002/api/auth/register')
    cy.get('input[name="email"]').type('invalid-email')
    cy.get('input[name="password"]').type('weak')
    cy.get('button[type="submit"]').click()
    
    // Should show validation errors
    cy.get('.error-message').should('be.visible')
    cy.get('body').should('contain', 'Please enter a valid email')
    cy.get('body').should('contain', 'Password must be stronger')

    // Test network errors
    cy.intercept('POST', '/api/auth/register', { statusCode: 500 })
    cy.get('input[name="email"]').clear().type('test@example.com')
    cy.get('input[name="password"]').clear().type('ValidPassword123!')
    cy.get('button[type="submit"]').click()
    
    // Should show error message
    cy.get('.error-message').should('contain', 'Something went wrong')

    cy.log('Error scenarios handled correctly')
  })

  it('should test mobile responsiveness', () => {
    cy.log('=== TESTING MOBILE RESPONSIVENESS ===')

    // Set mobile viewport
    cy.viewport('iphone-x')
    
    // Test registration on mobile
    cy.visit('http://localhost:5002/api/auth/register')
    cy.get('input[name="email"]').should('be.visible')
    cy.get('input[name="password"]').should('be.visible')
    
    // Test onboarding on mobile
    cy.visit('http://localhost:5002/onboarding/profile')
    cy.get('.onboarding-container').should('be.visible')
    
    // Test dashboard on mobile
    cy.visit('http://localhost:5002/dashboard')
    cy.get('.dashboard-container').should('be.visible')
    
    // Reset viewport
    cy.viewport(1280, 720)
    
    cy.log('Mobile responsiveness verified')
  })

  it('should test accessibility features', () => {
    cy.log('=== TESTING ACCESSIBILITY ===')

    // Test keyboard navigation
    cy.visit('http://localhost:5002/api/auth/register')
    cy.get('body').tab()
    cy.focused().should('have.attr', 'name', 'email')
    
    // Test screen reader compatibility
    cy.get('input[name="email"]').should('have.attr', 'aria-label')
    cy.get('button[type="submit"]').should('have.attr', 'aria-label')
    
    // Test color contrast (basic check)
    cy.get('body').should('have.css', 'color')
    
    cy.log('Accessibility features verified')
  })
}) 