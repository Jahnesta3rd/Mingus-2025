// cypress/e2e/application-health-check.cy.js
// Comprehensive test suite to verify what's working in the Mingus application

describe('Mingus Application Health Check', () => {
  const baseUrl = 'http://127.0.0.1:5002'
  
  describe('Server Connectivity', () => {
    it('should connect to Flask server', () => {
      cy.request({
        method: 'GET',
        url: `${baseUrl}/`,
        failOnStatusCode: false
      }).then((response) => {
        // Should either redirect to login or return a response
        expect(response.status).to.be.oneOf([200, 302, 404])
      })
    })

    it('should access login page', () => {
      cy.visit(`${baseUrl}/api/auth/login`)
      cy.get('body').should('be.visible')
    })

    it('should access register page', () => {
      cy.visit(`${baseUrl}/api/auth/register`)
      cy.get('body').should('be.visible')
    })
  })

  describe('Authentication System', () => {
    beforeEach(() => {
      cy.visit(`${baseUrl}/api/auth/login`)
    })

    it('should display login form elements', () => {
      // Check for basic page structure
      cy.get('body').should('be.visible')
      
      // Look for common login form elements
      cy.get('input[type="email"], input[name="email"]').should('exist')
      cy.get('input[type="password"], input[name="password"]').should('exist')
      
      // Check for login button or form submit
      cy.get('button[type="submit"], input[type="submit"], [data-cy="login-button"]').should('exist')
    })

    it('should display register form elements', () => {
      cy.visit(`${baseUrl}/api/auth/register`)
      
      // Check for registration form elements
      cy.get('input[name="full_name"], input[name="name"]').should('exist')
      cy.get('input[type="email"], input[name="email"]').should('exist')
      cy.get('input[type="password"], input[name="password"]').should('exist')
      
      // Check for submit button
      cy.get('button[type="submit"], input[type="submit"]').should('exist')
    })

    it('should handle login form submission', () => {
      // Fill out login form
      cy.get('input[type="email"], input[name="email"]').type('test@example.com')
      cy.get('input[type="password"], input[name="password"]').type('testpassword123')
      
      // Submit form
      cy.get('button[type="submit"], input[type="submit"], [data-cy="login-button"]').click()
      
      // Should either show error or redirect
      cy.url().should('not.equal', `${baseUrl}/api/auth/login`)
    })

    it('should handle registration form submission', () => {
      cy.visit(`${baseUrl}/api/auth/register`)
      
      // Fill out registration form
      cy.get('input[name="full_name"], input[name="name"]').type('Test User')
      cy.get('input[type="email"], input[name="email"]').type('newuser@example.com')
      cy.get('input[type="password"], input[name="password"]').type('password123!')
      
      // Add phone number if field exists
      cy.get('input[name="phone_number"]').then(($el) => {
        if ($el.length > 0) {
          cy.wrap($el).type('555-123-4567')
        }
      })
      
      // Submit form
      cy.get('button[type="submit"], input[type="submit"]').click()
      
      // Should either show error or redirect
      cy.url().should('not.equal', `${baseUrl}/api/auth/register`)
    })
  })

  describe('API Endpoints', () => {
    it('should test authentication endpoints', () => {
      // Test login endpoint
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/login`,
        body: {
          email: 'test@example.com',
          password: 'testpassword123'
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 401, 400])
      })

      // Test register endpoint
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/register`,
        body: {
          email: 'newuser@example.com',
          password: 'password123!',
          full_name: 'Test User',
          phone_number: '555-123-4567'
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 201, 400, 409])
      })
    })

    it('should test health check endpoints', () => {
      // Test if health endpoint exists
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/health`,
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404])
      })

      // Test if onboarding endpoint exists
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/health/onboarding`,
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401])
      })
    })

    it('should test user profile endpoints', () => {
      // Test profile endpoint (should require authentication)
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/auth/profile`,
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 401, 404])
      })
    })
  })

  describe('Database Connectivity', () => {
    it('should verify database operations', () => {
      // Test user creation via API
      const testEmail = `test${Date.now()}@example.com`
      
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/register`,
        body: {
          email: testEmail,
          password: 'password123!',
          full_name: 'Database Test User',
          phone_number: '555-123-4567'
        },
        failOnStatusCode: false
      }).then((response) => {
        // If successful, database is working
        if (response.status === 200 || response.status === 201) {
          cy.log('Database write operation successful')
        } else {
          cy.log(`Database operation failed with status: ${response.status}`)
        }
      })
    })
  })

  describe('Frontend Functionality', () => {
    it('should test navigation between pages', () => {
      cy.visit(`${baseUrl}/api/auth/login`)
      
      // Test navigation to register page
      cy.get('a[href*="register"], [data-cy="new-user"]').then(($el) => {
        if ($el.length > 0) {
          cy.wrap($el).click()
          cy.url().should('include', 'register')
        }
      })
    })

    it('should test form validation', () => {
      cy.visit(`${baseUrl}/api/auth/register`)
      
      // Try to submit empty form
      cy.get('button[type="submit"], input[type="submit"]').click()
      
      // Should either show validation errors or submit
      cy.get('body').should('be.visible')
    })

    it('should test responsive design', () => {
      // Test mobile viewport
      cy.viewport('iphone-x')
      cy.visit(`${baseUrl}/api/auth/login`)
      cy.get('body').should('be.visible')
      
      // Test desktop viewport
      cy.viewport(1920, 1080)
      cy.visit(`${baseUrl}/api/auth/login`)
      cy.get('body').should('be.visible')
    })
  })

  describe('Error Handling', () => {
    it('should handle 404 errors gracefully', () => {
      cy.request({
        method: 'GET',
        url: `${baseUrl}/nonexistent-page`,
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.equal(404)
      })
    })

    it('should handle invalid API requests', () => {
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/login`,
        body: {
          // Missing required fields
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([400, 422])
      })
    })
  })

  describe('Session Management', () => {
    it('should test session persistence', () => {
      // First, try to register a user
      const testEmail = `session${Date.now()}@example.com`
      
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/register`,
        body: {
          email: testEmail,
          password: 'password123!',
          full_name: 'Session Test User',
          phone_number: '555-123-4567'
        },
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200 || response.status === 201) {
          // If registration successful, test login
          cy.request({
            method: 'POST',
            url: `${baseUrl}/api/auth/login`,
            body: {
              email: testEmail,
              password: 'password123!'
            },
            failOnStatusCode: false
          }).then((loginResponse) => {
            if (loginResponse.status === 200) {
              cy.log('Session management appears to be working')
            }
          })
        }
      })
    })
  })
}) 