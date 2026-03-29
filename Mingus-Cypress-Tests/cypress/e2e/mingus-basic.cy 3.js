describe('Basic Flask Test', () => {
  it('should have a page title', () => {
    
  
    // CORRECT - use relative URL (uses baseUrl from config):
    cy.visit('/')
    
    cy.title().should('not.be.empty')
  })
})