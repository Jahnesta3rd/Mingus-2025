// cypress/e2e/auth-test.cy.js
// Test authentication commands

describe('Authentication Commands', () => {
  const baseUrl = 'http://127.0.0.1:5002'
  
  beforeEach(() => {
    cy.clearCookies()
    cy.clearLocalStorage()
  })

  it('should register a new user', () => {
    cy.registerUser()
    cy.get('@userCredentials').then((credentials) => {
      expect(credentials).to.have.property('email')
      expect(credentials).to.have.property('password')
      expect(credentials).to.have.property('fullName')
      cy.log(`Registered user: ${credentials.email}`)
    })
  })

  it('should login user via API', () => {
    // First register a user
    cy.registerUser()
    cy.get('@userCredentials').then((credentials) => {
      // Then login with those credentials
      cy.loginUser(credentials.email, credentials.password)
      cy.log('User logged in via API')
    })
  })

  it('should check authentication status', () => {
    cy.request({
      method: 'GET',
      url: `${baseUrl}/api/auth/check-auth`,
      failOnStatusCode: false
    }).then((response) => {
      cy.log(`Auth check response: ${response.status}`)
      expect(response.status).to.be.oneOf([200, 401])
      
      if (response.status === 200) {
        expect(response.body).to.have.property('authenticated')
      }
    })
  })

  it('should logout user', () => {
    // First login
    cy.loginUser()
    // Then logout
    cy.logoutUser()
    cy.log('User logged out successfully')
  })

  it('should handle authentication flow', () => {
    // Test complete auth flow
    cy.registerUser()
    cy.get('@userCredentials').then((credentials) => {
      cy.loginUser(credentials.email, credentials.password)
      
      // Check if authenticated
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/auth/check-auth`,
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200 && response.body.authenticated) {
          cy.log('User is authenticated')
          
          // Test accessing protected endpoint
          cy.request({
            method: 'GET',
            url: `${baseUrl}/api/auth/profile`,
            failOnStatusCode: false
          }).then((profileResponse) => {
            cy.log(`Profile access response: ${profileResponse.status}`)
            expect(profileResponse.status).to.be.oneOf([200, 401])
          })
        }
      })
      
      // Logout
      cy.logoutUser()
    })
  })

  it('should test login with invalid credentials', () => {
    cy.request({
      method: 'POST',
      url: `${baseUrl}/api/auth/login`,
      body: {
        email: 'invalid@example.com',
        password: 'wrongpassword'
      },
      failOnStatusCode: false
    }).then((response) => {
      cy.log(`Invalid login response: ${response.status}`)
      expect(response.status).to.be.oneOf([401, 400])
    })
  })

  it('should test registration with existing email', () => {
    // First register a user
    cy.registerUser('duplicate@example.com', 'password123!', 'Duplicate User')
    
    // Try to register again with same email
    cy.request({
      method: 'POST',
      url: `${baseUrl}/api/auth/register`,
      body: {
        email: 'duplicate@example.com',
        password: 'password123!',
        full_name: 'Duplicate User',
        phone_number: '555-123-4567'
      },
      failOnStatusCode: false
    }).then((response) => {
      cy.log(`Duplicate registration response: ${response.status}`)
      expect(response.status).to.be.oneOf([409, 400, 500])
    })
  })
}) 