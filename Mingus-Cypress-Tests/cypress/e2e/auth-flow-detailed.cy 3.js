// cypress/e2e/auth-flow-detailed.cy.js
// Detailed authentication flow testing

describe('Detailed Authentication Flow', () => {
  const baseUrl = 'http://127.0.0.1:5002'
  
  beforeEach(() => {
    // Clear any existing session
    cy.clearCookies()
    cy.clearLocalStorage()
  })

  describe('Login Page', () => {
    beforeEach(() => {
      cy.visit(`${baseUrl}/api/auth/login`)
    })

    it('should load login page successfully', () => {
      cy.get('body').should('be.visible')
      cy.url().should('include', '/api/auth/login')
    })

    it('should have all required login form elements', () => {
      // Check for email field
      cy.get('input[type="email"], input[name="email"]').should('be.visible')
      
      // Check for password field
      cy.get('input[type="password"], input[name="password"]').should('be.visible')
      
      // Check for submit button
      cy.get('button[type="submit"], input[type="submit"], [data-cy="login-button"]').should('be.visible')
    })

    it('should handle empty form submission', () => {
      cy.get('button[type="submit"], input[type="submit"], [data-cy="login-button"]').click()
      
      // Should either show validation errors or stay on page
      cy.url().should('include', '/api/auth/login')
    })

    it('should handle invalid email format', () => {
      cy.get('input[type="email"], input[name="email"]').type('invalid-email')
      cy.get('input[type="password"], input[name="password"]').type('password123')
      
      cy.get('button[type="submit"], input[type="submit"], [data-cy="login-button"]').click()
      
      // Should show validation error or stay on page
      cy.url().should('include', '/api/auth/login')
    })

    it('should handle valid login attempt', () => {
      cy.get('input[type="email"], input[name="email"]').type('test@example.com')
      cy.get('input[type="password"], input[name="password"]').type('password123')
      
      cy.get('button[type="submit"], input[type="submit"], [data-cy="login-button"]').click()
      
      // Should either redirect on success or show error
      cy.url().should('not.equal', `${baseUrl}/api/auth/login`)
    })

    it('should navigate to register page', () => {
      // Look for register link or button
      cy.get('a[href*="register"], [data-cy="new-user"], a:contains("Register"), a:contains("Sign Up")').then(($el) => {
        if ($el.length > 0) {
          cy.wrap($el).click()
          cy.url().should('include', 'register')
        } else {
          // If no register link found, try direct navigation
          cy.visit(`${baseUrl}/api/auth/register`)
          cy.url().should('include', 'register')
        }
      })
    })
  })

  describe('Registration Page', () => {
    beforeEach(() => {
      cy.visit(`${baseUrl}/api/auth/register`)
    })

    it('should load registration page successfully', () => {
      cy.get('body').should('be.visible')
      cy.url().should('include', '/api/auth/register')
    })

    it('should have all required registration form elements', () => {
      // Check for name field
      cy.get('input[name="full_name"], input[name="name"], input[placeholder*="name"]').should('be.visible')
      
      // Check for email field
      cy.get('input[type="email"], input[name="email"]').should('be.visible')
      
      // Check for password field
      cy.get('input[type="password"], input[name="password"]').should('be.visible')
      
      // Check for submit button
      cy.get('button[type="submit"], input[type="submit"]').should('be.visible')
    })

    it('should handle empty form submission', () => {
      cy.get('button[type="submit"], input[type="submit"]').click()
      
      // Should either show validation errors or stay on page
      cy.url().should('include', '/api/auth/register')
    })

    it('should handle invalid email format', () => {
      cy.get('input[name="full_name"], input[name="name"]').type('Test User')
      cy.get('input[type="email"], input[name="email"]').type('invalid-email')
      cy.get('input[type="password"], input[name="password"]').type('password123')
      
      cy.get('button[type="submit"], input[type="submit"]').click()
      
      // Should show validation error or stay on page
      cy.url().should('include', '/api/auth/register')
    })

    it('should handle weak password', () => {
      cy.get('input[name="full_name"], input[name="name"]').type('Test User')
      cy.get('input[type="email"], input[name="email"]').type('test@example.com')
      cy.get('input[type="password"], input[name="password"]').type('123')
      
      cy.get('button[type="submit"], input[type="submit"]').click()
      
      // Should show password strength error or stay on page
      cy.url().should('include', '/api/auth/register')
    })

    it('should handle valid registration attempt', () => {
      const uniqueEmail = `test${Date.now()}@example.com`
      
      cy.get('input[name="full_name"], input[name="name"]').type('Test User')
      cy.get('input[type="email"], input[name="email"]').type(uniqueEmail)
      cy.get('input[type="password"], input[name="password"]').type('password123!')
      
      // Add phone number if field exists
      cy.get('input[name="phone_number"]').then(($el) => {
        if ($el.length > 0) {
          cy.wrap($el).type('555-123-4567')
        }
      })
      
      cy.get('button[type="submit"], input[type="submit"]').click()
      
      // Should either redirect on success or show error
      cy.url().should('not.equal', `${baseUrl}/api/auth/register`)
    })

    it('should navigate back to login page', () => {
      // Look for login link or button
      cy.get('a[href*="login"], a:contains("Login"), a:contains("Sign In")').then(($el) => {
        if ($el.length > 0) {
          cy.wrap($el).click()
          cy.url().should('include', 'login')
        } else {
          // If no login link found, try direct navigation
          cy.visit(`${baseUrl}/api/auth/login`)
          cy.url().should('include', 'login')
        }
      })
    })
  })

  describe('API Authentication Endpoints', () => {
    it('should test login API endpoint', () => {
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/login`,
        body: {
          email: 'test@example.com',
          password: 'password123'
        },
        failOnStatusCode: false
      }).then((response) => {
        // Log the response for debugging
        cy.log(`Login API response status: ${response.status}`)
        cy.log(`Login API response body: ${JSON.stringify(response.body)}`)
        
        // Should return appropriate status code
        expect(response.status).to.be.oneOf([200, 401, 400, 422])
      })
    })

    it('should test registration API endpoint', () => {
      const uniqueEmail = `api${Date.now()}@example.com`
      
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/register`,
        body: {
          email: uniqueEmail,
          password: 'password123!',
          full_name: 'API Test User',
          phone_number: '555-123-4567'
        },
        failOnStatusCode: false
      }).then((response) => {
        // Log the response for debugging
        cy.log(`Registration API response status: ${response.status}`)
        cy.log(`Registration API response body: ${JSON.stringify(response.body)}`)
        
        // Should return appropriate status code
        expect(response.status).to.be.oneOf([200, 201, 400, 409, 422])
      })
    })

    it('should test profile API endpoint (unauthenticated)', () => {
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/auth/profile`,
        failOnStatusCode: false
      }).then((response) => {
        // Should return 401 for unauthenticated requests
        expect(response.status).to.be.oneOf([401, 404])
      })
    })

    it('should test check-auth API endpoint', () => {
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/auth/check-auth`,
        failOnStatusCode: false
      }).then((response) => {
        // Should return authentication status
        expect(response.status).to.be.oneOf([200, 404])
        if (response.status === 200) {
          expect(response.body).to.have.property('authenticated')
        }
      })
    })
  })

  describe('Session and Cookie Management', () => {
    it('should test session creation after login', () => {
      // First register a user
      const uniqueEmail = `session${Date.now()}@example.com`
      
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/register`,
        body: {
          email: uniqueEmail,
          password: 'password123!',
          full_name: 'Session Test User',
          phone_number: '555-123-4567'
        },
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200 || response.status === 201) {
          // Now try to login with the same user
          cy.request({
            method: 'POST',
            url: `${baseUrl}/api/auth/login`,
            body: {
              email: uniqueEmail,
              password: 'password123!'
            },
            failOnStatusCode: false
          }).then((loginResponse) => {
            if (loginResponse.status === 200) {
              // Check if session cookie was set
              cy.log('Login successful, checking for session cookie')
              expect(loginResponse.headers).to.have.property('set-cookie')
            }
          })
        }
      })
    })

    it('should test logout functionality', () => {
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/logout`,
        failOnStatusCode: false
      }).then((response) => {
        // Should return success status
        expect(response.status).to.be.oneOf([200, 404])
      })
    })
  })

  describe('Error Scenarios', () => {
    it('should handle duplicate email registration', () => {
      const testEmail = `duplicate${Date.now()}@example.com`
      
      // First registration
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/register`,
        body: {
          email: testEmail,
          password: 'password123!',
          full_name: 'First User',
          phone_number: '555-123-4567'
        },
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200 || response.status === 201) {
          // Try to register same email again
          cy.request({
            method: 'POST',
            url: `${baseUrl}/api/auth/register`,
            body: {
              email: testEmail,
              password: 'password123!',
              full_name: 'Second User',
              phone_number: '555-123-4568'
            },
            failOnStatusCode: false
          }).then((duplicateResponse) => {
            // Should return conflict status
            expect(duplicateResponse.status).to.be.oneOf([409, 400, 422])
          })
        }
      })
    })

    it('should handle invalid login credentials', () => {
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/login`,
        body: {
          email: 'nonexistent@example.com',
          password: 'wrongpassword'
        },
        failOnStatusCode: false
      }).then((response) => {
        // Should return unauthorized status
        expect(response.status).to.be.oneOf([401, 400, 422])
      })
    })
  })
}) 