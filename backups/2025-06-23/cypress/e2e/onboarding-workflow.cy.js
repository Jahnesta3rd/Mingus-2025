/**
 * User Onboarding Workflow E2E Test
 * Tests the complete user journey from registration through health onboarding to dashboard
 */

describe('User Onboarding Workflow', () => {
  const testUser = {
    email: 'test.user@example.com',
    password: 'TestPassword123!',
    firstName: 'Test',
    lastName: 'User',
    phoneNumber: '1234567890'
  }

  beforeEach(() => {
    // Clear cookies and local storage before each test
    cy.clearCookies()
    cy.clearLocalStorage()
    
    // Visit the application
    cy.visit('http://localhost:5002')
  })

  it('should complete full user onboarding workflow', () => {
    cy.log('=== Starting Complete Onboarding Workflow ===')

    // Step 1: User Registration
    cy.log('Step 1: User Registration')
    cy.visit('http://localhost:5002/api/auth/register')
    cy.wait(1000)
    
    // Fill out registration form
    cy.get('input[name="email"]').type(testUser.email)
    cy.get('input[name="password"]').type(testUser.password)
    cy.get('input[name="first_name"]').type(testUser.firstName)
    cy.get('input[name="last_name"]').type(testUser.lastName)
    cy.get('input[name="phone_number"]').type(testUser.phoneNumber)
    
    // Submit registration
    cy.get('button[type="submit"]').click()
    
    // Wait for redirect or success
    cy.wait(2000)
    cy.log('Registration completed')

    // Step 2: Health Onboarding
    cy.log('Step 2: Health Onboarding')
    cy.visit('http://localhost:5002/api/health/onboarding')
    cy.wait(1000)
    
    // Verify onboarding page loaded
    cy.get('.onboarding-container').should('be.visible')
    cy.get('.logo').should('contain', 'Mingus')
    cy.get('#progressText').should('contain', 'Step 1 of 4')
    
    // Step 2.1: Introduction Step
    cy.log('Step 2.1: Introduction')
    cy.get('#step1').should('be.visible')
    cy.get('.step-title').should('contain', 'Discover How Your Wellness Affects Your Wealth')
    
    // Click "Start My Wellness Journey"
    cy.get('#startBtn').click()
    cy.wait(500)
    
    // Step 2.2: Health Check-in Step
    cy.log('Step 2.2: Health Check-in')
    cy.get('#step2').should('be.visible')
    cy.get('.step-title').should('contain', 'Your First Wellness Check-in')
    
    // Fill out health check-in form
    cy.get('#stressLevel').invoke('val', 6).trigger('change')
    cy.get('input[type="number"]').first().clear().type('120')
    cy.get('input[type="range"]').eq(1).invoke('val', 8).trigger('change')
    cy.get('input[type="number"]').eq(1).clear().type('15')
    
    // Complete check-in
    cy.get('#completeCheckinBtn').click()
    cy.wait(500)
    
    // Step 2.3: Timeline Step
    cy.log('Step 2.3: Timeline')
    cy.get('#step3').should('be.visible')
    cy.get('.step-title').should('contain', 'Building Your Insight Timeline')
    
    // Click "Set Up Reminders"
    cy.get('#setupRemindersBtn').click()
    cy.wait(500)
    
    // Step 2.4: Goals Selection Step
    cy.log('Step 2.4: Goals Selection')
    cy.get('#step4').should('be.visible')
    cy.get('.step-title').should('contain', 'Choose Your Wellness Goals')
    
    // Select some goals
    cy.get('.goal-card').first().click()
    cy.get('.goal-card').eq(2).click()
    
    // Complete onboarding
    cy.get('#finishOnboardingBtn').click()
    cy.wait(2000)
    
    cy.log('Onboarding completed')

    // Step 3: Verify Dashboard Access
    cy.log('Step 3: Dashboard Access')
    
    // Should redirect to dashboard
    cy.url().should('include', '/dashboard')
    cy.get('body').should('contain', 'Dashboard')
    
    cy.log('=== Onboarding Workflow Completed Successfully ===')
  })

  it('should handle onboarding with skip option', () => {
    cy.log('=== Testing Skip Onboarding Option ===')

    // Register user first
    cy.visit('http://localhost:5002/api/auth/register')
    cy.wait(1000)
    
    cy.get('input[name="email"]').type('skip.test@example.com')
    cy.get('input[name="password"]').type(testUser.password)
    cy.get('input[name="first_name"]').type('Skip')
    cy.get('input[name="last_name"]').type('Test')
    cy.get('input[name="phone_number"]').type(testUser.phoneNumber)
    
    cy.get('button[type="submit"]').click()
    cy.wait(2000)

    // Go to onboarding
    cy.visit('http://localhost:5002/api/health/onboarding')
    cy.wait(1000)
    
    // Click skip button
    cy.get('#skipBtn').click()
    
    // Should show confirmation dialog
    cy.on('window:confirm', () => true)
    
    // Should redirect to dashboard
    cy.url().should('include', '/dashboard')
    cy.log('Skip onboarding completed')
  })

  it('should handle onboarding navigation', () => {
    cy.log('=== Testing Onboarding Navigation ===')

    // Register user first
    cy.visit('http://localhost:5002/api/auth/register')
    cy.wait(1000)
    
    cy.get('input[name="email"]').type('nav.test@example.com')
    cy.get('input[name="password"]').type(testUser.password)
    cy.get('input[name="first_name"]').type('Nav')
    cy.get('input[name="last_name"]').type('Test')
    cy.get('input[name="phone_number"]').type(testUser.phoneNumber)
    
    cy.get('button[type="submit"]').click()
    cy.wait(2000)

    // Go to onboarding
    cy.visit('http://localhost:5002/api/health/onboarding')
    cy.wait(1000)
    
    // Test forward navigation
    cy.get('#startBtn').click()
    cy.wait(500)
    cy.get('#progressText').should('contain', 'Step 2 of 4')
    
    // Test back navigation
    cy.get('#backBtn1').click()
    cy.wait(500)
    cy.get('#progressText').should('contain', 'Step 1 of 4')
    
    cy.log('Navigation testing completed')
  })

  it('should handle onboarding with minimal data', () => {
    cy.log('=== Testing Minimal Onboarding ===')

    // Register user
    cy.visit('http://localhost:5002/api/auth/register')
    cy.wait(1000)
    
    cy.get('input[name="email"]').type('minimal.test@example.com')
    cy.get('input[name="password"]').type(testUser.password)
    cy.get('input[name="first_name"]').type('Minimal')
    cy.get('input[name="last_name"]').type('Test')
    cy.get('input[name="phone_number"]').type(testUser.phoneNumber)
    
    cy.get('button[type="submit"]').click()
    cy.wait(2000)

    // Go to onboarding
    cy.visit('http://localhost:5002/api/health/onboarding')
    cy.wait(1000)
    
    // Complete onboarding with minimal interaction
    cy.get('#startBtn').click()
    cy.wait(500)
    
    cy.get('#completeCheckinBtn').click()
    cy.wait(500)
    
    cy.get('#setupRemindersBtn').click()
    cy.wait(500)
    
    // Complete without selecting goals
    cy.get('#finishOnboardingBtn').click()
    cy.wait(2000)
    
    // Should still reach dashboard
    cy.url().should('include', '/dashboard')
    cy.log('Minimal onboarding completed')
  })

  it('should verify onboarding progress tracking', () => {
    cy.log('=== Testing Progress Tracking ===')

    // Register user
    cy.visit('http://localhost:5002/api/auth/register')
    cy.wait(1000)
    
    cy.get('input[name="email"]').type('progress.test@example.com')
    cy.get('input[name="password"]').type(testUser.password)
    cy.get('input[name="first_name"]').type('Progress')
    cy.get('input[name="last_name"]').type('Test')
    cy.get('input[name="phone_number"]').type(testUser.phoneNumber)
    
    cy.get('button[type="submit"]').click()
    cy.wait(2000)

    // Go to onboarding
    cy.visit('http://localhost:5002/api/health/onboarding')
    cy.wait(1000)
    
    // Check initial progress
    cy.get('#progressText').should('contain', 'Step 1 of 4')
    cy.get('#progressFill').should('have.css', 'width', '25%')
    
    // Move to step 2
    cy.get('#startBtn').click()
    cy.wait(500)
    cy.get('#progressText').should('contain', 'Step 2 of 4')
    cy.get('#progressFill').should('have.css', 'width', '50%')
    
    // Move to step 3
    cy.get('#completeCheckinBtn').click()
    cy.wait(500)
    cy.get('#progressText').should('contain', 'Step 3 of 4')
    cy.get('#progressFill').should('have.css', 'width', '75%')
    
    // Move to step 4
    cy.get('#setupRemindersBtn').click()
    cy.wait(500)
    cy.get('#progressText').should('contain', 'Step 4 of 4')
    cy.get('#progressFill').should('have.css', 'width', '100%')
    
    cy.log('Progress tracking verified')
  })

  afterEach(() => {
    cy.log('Test completed')
  })
}) 