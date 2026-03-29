// cypress/e2e/basic-auth-flow.cy.js
// Basic test to verify your current login/register setup

describe('Mingus Basic Authentication Flow', () => {
  beforeEach(() => {
    // Update this URL to match how you access your app
    cy.visit('/api/auth/login')
  })

  it('should display the login page elements', () => {
    // Check if your login page loads correctly
    cy.contains('Mingus').should('be.visible')
    cy.contains('Financial Wellness, Reimagined').should('be.visible')
    
    // Check form elements exist
    cy.get('input[name="email"]').should('be.visible')
    cy.get('input[name="password"]').should('be.visible')
    cy.get('[data-cy="login-button"]').should('contain', 'Sign In')
    cy.get('[data-cy="new-user"]').should('contain', 'New User')
    
    // Check OAuth buttons exist
    cy.contains('Google').should('be.visible')
    cy.contains('LinkedIn').should('be.visible')
  })

  it('should navigate to register page when New User clicked', () => {
    cy.get('[data-cy="new-user"]').click()
    
    // Should redirect to register page
    cy.url().should('include', '/register')
    
    // Check register page elements
    cy.contains('Create Your Account').should('be.visible')
    // or cy.contains('Create your account') - depending on which register.html you use
  })

  it('should attempt to submit login form', () => {
    // Fill out login form
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('testpassword')
    
    // Check the terms checkbox if it exists
    cy.get('#terms').check()
    
    // Submit form
    cy.get('[data-cy="login-button"]').click()
    
    // This will probably fail right now, but shows what should happen
    // When working, should either:
    // - Redirect to dashboard on success
    // - Show error message on failure
    cy.url().should('not.equal', 'http://localhost:5003/api/auth/login')
  })

  it('should show register form elements', () => {
    // Go to register page
    cy.get('[data-cy="new-user"]').click()
    
    // Check register form exists
    cy.get('input[name="full_name"]').should('be.visible')
    cy.get('input[name="email"]').should('be.visible')
    cy.get('input[name="phone_number"]').should('be.visible')
    cy.get('input[name="password"]').should('be.visible')
    
    // Check submit button
    cy.get('button[type="submit"]').should('be.visible')
  })

  // Optional: Test that will fail until you fix backend connection
  it.skip('should successfully register a new user', () => {
    cy.get('[data-cy="new-user"]').click()
    
    // Fill registration form
    cy.get('input[name="full_name"]').type('Test User')
    cy.get('input[name="email"]').type('newuser@example.com')
    cy.get('input[name="phone_number"]').type('555-123-4567')
    cy.get('input[name="password"]').type('password123')
    
    // Submit
    cy.get('button[type="submit"]').click()
    
    // Should redirect somewhere on success
    cy.url().should('not.include', '/register')
  })
})