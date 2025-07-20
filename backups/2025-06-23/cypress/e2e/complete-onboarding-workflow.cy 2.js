/**
 * Complete User Onboarding Workflow E2E Test
 * Tests the entire user journey from registration through onboarding to dashboard access
 */

describe('Complete User Onboarding Workflow', () => {
  let testUserData

  beforeEach(() => {
    // Load test data
    cy.fixture('onboarding-data').then((data) => {
      testUserData = data
    })

    // Clear cookies and local storage before each test
    cy.clearCookies()
    cy.clearLocalStorage()
    
    // Visit the application
    cy.visit('http://localhost:5002')
  })

  it('should complete full user onboarding workflow', () => {
    // Step 1: User Registration
    cy.log('Starting user registration...')
    
    // Navigate to registration page
    cy.visit('http://localhost:5002/api/auth/register')
    cy.waitForPageLoad()
    
    // Fill out registration form
    cy.get('input[name="email"]').type(testUserData.user.email)
    cy.get('input[name="password"]').type(testUserData.user.password)
    cy.get('input[name="first_name"]').type(testUserData.user.firstName)
    cy.get('input[name="last_name"]').type(testUserData.user.lastName)
    cy.get('input[name="phone_number"]').type(testUserData.user.phoneNumber)
    
    // Submit registration
    cy.get('button[type="submit"]').click()
    
    // Should redirect to onboarding or show success message
    cy.url().should('include', '/onboarding').or('contain', 'success')
    cy.log('User registration completed')

    // Step 2: Health Onboarding
    cy.log('Starting health onboarding...')
    
    // Navigate to health onboarding
    cy.visit('http://localhost:5002/api/health/onboarding')
    cy.waitForPageLoad()
    
    // Check if onboarding form is present
    cy.get('.onboarding-container').should('be.visible')
    
    // Complete health onboarding using custom command
    cy.completeHealthOnboarding(testUserData.healthProfile)
    
    // Verify onboarding completion
    cy.get('.onboarding-complete').should('be.visible')
    cy.log('Health onboarding completed')

    // Step 3: Financial Questionnaire (if available)
    cy.log('Starting financial questionnaire...')
    
    // Navigate to financial questionnaire
    cy.visit('http://localhost:5002/api/financial/questionnaire')
    cy.waitForPageLoad()
    
    // Check if financial form is available
    cy.get('body').then(($body) => {
      if ($body.find('#income').length > 0) {
        cy.completeFinancialQuestionnaire(testUserData.financialProfile)
        cy.log('Financial questionnaire completed')
      } else {
        cy.log('Financial questionnaire not available, skipping')
      }
    })

    // Step 4: Career Questionnaire (if available)
    cy.log('Starting career questionnaire...')
    
    // Navigate to career questionnaire
    cy.visit('http://localhost:5002/api/career/questionnaire')
    cy.waitForPageLoad()
    
    // Check if career form is available
    cy.get('body').then(($body) => {
      if ($body.find('#industry').length > 0) {
        cy.completeCareerQuestionnaire(testUserData.careerProfile)
        cy.log('Career questionnaire completed')
      } else {
        cy.log('Career questionnaire not available, skipping')
      }
    })

    // Step 5: Access Dashboard
    cy.log('Accessing dashboard...')
    
    // Navigate to main dashboard
    cy.visit('http://localhost:5002/api/health/dashboard')
    cy.waitForPageLoad()
    
    // Verify dashboard access
    cy.get('body').should('contain', 'Dashboard')
    cy.get('.dashboard-container').should('be.visible')
    
    // Check for key dashboard elements
    cy.get('.health-summary').should('be.visible')
    cy.get('.recommendations').should('be.visible')
    cy.log('Dashboard access successful')

    // Step 6: Verify User Profile
    cy.log('Verifying user profile...')
    
    // Check user profile
    cy.visit('http://localhost:5002/api/auth/profile')
    cy.waitForPageLoad()
    
    // Verify profile data
    cy.get('body').should('contain', testUserData.user.firstName)
    cy.get('body').should('contain', testUserData.user.lastName)
    cy.get('body').should('contain', testUserData.user.email)
    cy.log('User profile verification completed')
  })

  it('should handle onboarding with missing optional data', () => {
    // Test with minimal required data
    const minimalUserData = {
      email: 'minimal.test@example.com',
      password: 'TestPassword123!',
      firstName: 'Minimal',
      lastName: 'Test',
      phoneNumber: '1234567890'
    }

    const minimalHealthData = {
      age: '25',
      gender: 'prefer-not-to-say',
      height: '170',
      weight: '65',
      activityLevel: 'low',
      sleepHours: '8',
      stressLevel: 'low',
      dietType: 'balanced',
      smokingStatus: 'never',
      alcoholConsumption: 'never',
      medicalConditions: [],
      medications: [],
      familyHistory: [],
      healthGoals: ['general-wellness'],
      preferredActivities: ['walking']
    }

    // Register user with minimal data
    cy.visit('http://localhost:5002/api/auth/register')
    cy.waitForPageLoad()
    
    cy.get('input[name="email"]').type(minimalUserData.email)
    cy.get('input[name="password"]').type(minimalUserData.password)
    cy.get('input[name="first_name"]').type(minimalUserData.firstName)
    cy.get('input[name="last_name"]').type(minimalUserData.lastName)
    cy.get('input[name="phone_number"]').type(minimalUserData.phoneNumber)
    
    cy.get('button[type="submit"]').click()
    
    // Complete minimal health onboarding
    cy.visit('http://localhost:5002/api/health/onboarding')
    cy.waitForPageLoad()
    
    cy.completeHealthOnboarding(minimalHealthData)
    
    // Verify dashboard access with minimal data
    cy.visit('http://localhost:5002/api/health/dashboard')
    cy.waitForPageLoad()
    
    cy.get('.dashboard-container').should('be.visible')
    cy.log('Minimal onboarding completed successfully')
  })

  it('should handle onboarding validation errors', () => {
    // Test with invalid data
    const invalidUserData = {
      email: 'invalid-email',
      password: 'weak',
      firstName: '',
      lastName: '',
      phoneNumber: 'invalid-phone'
    }

    // Try to register with invalid data
    cy.visit('http://localhost:5002/api/auth/register')
    cy.waitForPageLoad()
    
    cy.get('input[name="email"]').type(invalidUserData.email)
    cy.get('input[name="password"]').type(invalidUserData.password)
    cy.get('input[name="first_name"]').type(invalidUserData.firstName)
    cy.get('input[name="last_name"]').type(invalidUserData.lastName)
    cy.get('input[name="phone_number"]').type(invalidUserData.phoneNumber)
    
    cy.get('button[type="submit"]').click()
    
    // Should show validation errors
    cy.get('.error-message').should('be.visible')
    cy.get('body').should('contain', 'Invalid email format')
    cy.log('Validation errors handled correctly')
  })

  it('should complete onboarding and access all dashboard features', () => {
    // Complete full onboarding first
    cy.log('Completing full onboarding workflow...')
    
    // Register user
    cy.visit('http://localhost:5002/api/auth/register')
    cy.waitForPageLoad()
    
    cy.get('input[name="email"]').type(testUserData.user.email)
    cy.get('input[name="password"]').type(testUserData.user.password)
    cy.get('input[name="first_name"]').type(testUserData.user.firstName)
    cy.get('input[name="last_name"]').type(testUserData.user.lastName)
    cy.get('input[name="phone_number"]').type(testUserData.user.phoneNumber)
    
    cy.get('button[type="submit"]').click()
    
    // Complete health onboarding
    cy.visit('http://localhost:5002/api/health/onboarding')
    cy.waitForPageLoad()
    
    cy.completeHealthOnboarding(testUserData.healthProfile)
    
    // Access dashboard and test all features
    cy.visit('http://localhost:5002/api/health/dashboard')
    cy.waitForPageLoad()
    
    // Test health check-in feature
    cy.get('body').then(($body) => {
      if ($body.find('.health-checkin').length > 0) {
        cy.get('.health-checkin button').click()
        cy.get('#mood-rating').select('4')
        cy.get('#energy-level').select('3')
        cy.get('#stress-level').select('2')
        cy.get('#sleep-quality').select('5')
        cy.get('#physical-activity').select('moderate')
        cy.get('#submit-checkin').click()
        cy.get('.success-message').should('be.visible')
        cy.log('Health check-in completed')
      }
    })
    
    // Test insights generation
    cy.get('body').then(($body) => {
      if ($body.find('.generate-insights').length > 0) {
        cy.get('.generate-insights button').click()
        cy.wait(3000) // Wait for insights generation
        cy.get('.insights-container').should('be.visible')
        cy.log('Insights generation completed')
      }
    })
    
    // Test correlation analysis
    cy.get('body').then(($body) => {
      if ($body.find('.correlation-analysis').length > 0) {
        cy.get('.correlation-analysis button').click()
        cy.wait(2000) // Wait for analysis
        cy.get('.correlation-results').should('be.visible')
        cy.log('Correlation analysis completed')
      }
    })
    
    // Test main app navigation
    cy.visit('http://localhost:5002/api/health/main_app')
    cy.waitForPageLoad()
    
    cy.get('.main-app-container').should('be.visible')
    cy.log('Main app access successful')
  })

  it('should handle session persistence and logout', () => {
    // Complete onboarding first
    cy.log('Testing session persistence...')
    
    // Register and complete onboarding
    cy.visit('http://localhost:5002/api/auth/register')
    cy.waitForPageLoad()
    
    cy.get('input[name="email"]').type(testUserData.user.email)
    cy.get('input[name="password"]').type(testUserData.user.password)
    cy.get('input[name="first_name"]').type(testUserData.user.firstName)
    cy.get('input[name="last_name"]').type(testUserData.user.lastName)
    cy.get('input[name="phone_number"]').type(testUserData.user.phoneNumber)
    
    cy.get('button[type="submit"]').click()
    
    cy.visit('http://localhost:5002/api/health/onboarding')
    cy.waitForPageLoad()
    
    cy.completeHealthOnboarding(testUserData.healthProfile)
    
    // Access dashboard
    cy.visit('http://localhost:5002/api/health/dashboard')
    cy.waitForPageLoad()
    
    // Verify session persistence
    cy.get('.dashboard-container').should('be.visible')
    
    // Test logout
    cy.get('body').then(($body) => {
      if ($body.find('.logout-button').length > 0) {
        cy.get('.logout-button').click()
        cy.url().should('include', '/login')
        cy.log('Logout successful')
      } else {
        // Try API logout
        cy.request({
          method: 'POST',
          url: '/api/auth/logout',
          failOnStatusCode: false
        }).then((response) => {
          expect(response.status).to.be.oneOf([200, 302])
          cy.log('API logout successful')
        })
      }
    })
  })

  afterEach(() => {
    // Clean up test data if needed
    cy.log('Test completed, cleaning up...')
  })
}) 