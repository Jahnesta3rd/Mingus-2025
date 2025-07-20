// cypress/e2e/simple-user-journey.cy.js
// Simplified end-to-end test for core user journey

describe('Simple User Journey: Registration to Dashboard', () => {
  const baseUrl = 'http://127.0.0.1:5002'
  
  // Sample user data for testing
  const testUser = {
    email: `testuser${Date.now()}@example.com`,
    password: 'TestPass123!',
    firstName: 'Test',
    lastName: 'User',
    phoneNumber: '1234567890'
  }

  beforeEach(() => {
    cy.clearCookies()
    cy.clearLocalStorage()
  })

  it('should complete basic user journey with sample data', () => {
    // Step 1: Register a new user
    cy.log('Step 1: User Registration')
    cy.visit(`${baseUrl}/api/auth/register`)
    
    // Debug: check URL and page title
    cy.url().then(url => cy.log('Current URL:', url))
    cy.title().then(title => cy.log('Page title:', title))
    
    // Debug: log HTML and take screenshot
    cy.document().then(doc => {
      cy.log('Page HTML:', doc.documentElement.innerHTML)
    })
    cy.screenshot('registration-page-debug')
    
    // Debug: check what elements are present
    cy.get('body').then($body => {
      cy.log('Body text:', $body.text())
      cy.log('Form elements found:', $body.find('form').length)
      cy.log('Input elements found:', $body.find('input').length)
      cy.log('First name inputs found:', $body.find('#first_name').length)
      cy.log('Last name inputs found:', $body.find('#last_name').length)
    })
    
    // Wait for page to load
    cy.get('body').should('be.visible')
    
    // Fill out registration form
    cy.get('#first_name').should('be.visible').type(testUser.firstName)
    cy.get('#last_name').should('be.visible').type(testUser.lastName)
    cy.get('#email').should('be.visible').type(testUser.email)
    cy.get('#phone_number').should('be.visible').type(testUser.phoneNumber)
    cy.get('#password').should('be.visible').type(testUser.password)
    
    // Submit registration form
    cy.get('#registerForm').submit()
    
    // Wait for redirect to onboarding (up to 10 seconds)
    cy.url({ timeout: 10000 }).should('include', '/api/health/onboarding')
    
    // Step 2: Complete onboarding (4-step JavaScript flow)
    cy.log('Step 2: Health Onboarding')
    cy.url().should('include', '/api/health/onboarding')
    
    // Wait for onboarding page to load
    cy.get('body').should('be.visible')
    
    // Step 1: Click "Start My Wellness Journey"
    cy.get('#startBtn').should('be.visible').click()
    
    // Step 2: Complete health check-in
    cy.get('#completeCheckinBtn').should('be.visible').click()
    
    // Step 3: Set up reminders
    cy.get('#setupRemindersBtn').should('be.visible').click()
    
    // Step 4: Select goals and finish
    cy.get('.goal-card').first().click() // Select first goal
    cy.get('#finishOnboardingBtn').should('be.visible').click()
    
    // Wait for redirect to dashboard
    cy.url({ timeout: 10000 }).should('include', '/api/health/dashboard')
    
    // Step 3: Verify dashboard access
    cy.log('Step 3: Dashboard Access')
    cy.url().should('include', '/api/health/dashboard')
    cy.get('body').should('be.visible')
    
    // Verify user is logged in by checking for user-specific content
    cy.get('body').should('contain', 'Welcome')
    
    cy.log('✅ User journey completed successfully!')
  })

  it('should handle login for existing user', () => {
    cy.log('Testing login functionality')
    cy.visit(`${baseUrl}/api/auth/login`)
    
    // Fill out login form
    cy.get('#email').should('be.visible').type('test@example.com')
    cy.get('#password').should('be.visible').type('TestPass123!')
    
    // Submit login form (correct form ID)
    cy.get('#login-form').submit()
    
    // Should redirect to dashboard or show success
    cy.url().should('not.include', '/api/auth/login')
    
    cy.log('✅ Login test completed')
  })

  it('should handle basic error scenarios', () => {
    cy.log('Testing error handling')
    
    // Test unauthorized access to protected route
    cy.request({
      method: 'GET',
      url: `${baseUrl}/api/health/dashboard`,
      failOnStatusCode: false
    }).then((response) => {
      expect(response.status).to.be.oneOf([401, 404])
    })
    
    // Test invalid registration data
    cy.request({
      method: 'POST',
      url: `${baseUrl}/api/auth/register`,
      headers: { 'Content-Type': 'application/json' },
      body: { email: 'invalid-email', password: '123' },
      failOnStatusCode: false
    }).then((response) => {
      expect(response.status).to.equal(400)
    })
    
    cy.log('✅ Error handling test completed')
  })
}) 