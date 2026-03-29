describe('Flask App Basic Test', () => {
  it('should connect to Flask app', () => {
    cy.visit('/')  // This uses baseUrl (http://127.0.0.1:5002)
    cy.get('body').should('exist')
  })
})
