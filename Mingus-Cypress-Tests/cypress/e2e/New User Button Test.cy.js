describe('New User Button Test', () => {
  beforeEach(() => {
    // Visit your Flask app
    cy.visit('/')
  })

  it('should find and test the new user button', () => {
    // First, let's see what's on the page
    cy.get('body').should('exist')
    
    // Look for the new user button - try different selectors
    cy.get('[data-cy=new-user]', { timeout: 10000 })
      .should('be.visible')
      .should('not.be.disabled')
    
    // Click the button
    cy.get('[data-cy=new-user]').click()
    
    // Add assertions for what should happen after clicking
    // (adjust based on your app behavior)
    cy.url().should('include', '/register') // if it redirects
    // or
    // cy.contains('Create Account') // if modal opens
  })

  it('should debug - show all buttons on page', () => {
    cy.visit('/')
    
    // Find all buttons and log them
    cy.get('button').each(($button) => {
      cy.log('Button text:', $button.text())
      cy.log('Button attributes:', $button[0].outerHTML)
    })
    
    // Look for common new user selectors
    cy.get('body').then(($body) => {
      const selectors = [
        '[data-cy=new-user]',
        'button:contains("Sign Up")',
        'button:contains("Create Account")',
        'button:contains("New User")',
        'a:contains("Register")'
      ]
      
      selectors.forEach(selector => {
        if ($body.find(selector).length > 0) {
          cy.log(`Found element with selector: ${selector}`)
        }
      })
    })
  })
})