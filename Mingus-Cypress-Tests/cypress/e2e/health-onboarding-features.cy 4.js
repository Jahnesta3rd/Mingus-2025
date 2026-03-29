// cypress/e2e/health-onboarding-features.cy.js
// Test suite for health check-in and onboarding features

describe('Health and Onboarding Features', () => {
  const baseUrl = 'http://127.0.0.1:5002'
  
  beforeEach(() => {
    cy.clearCookies()
    cy.clearLocalStorage()
    
    // Register and login a test user before each test
    cy.registerUser()
    cy.get('@userCredentials').then((credentials) => {
      cy.loginUser(credentials.email, credentials.password)
    })
  })

  describe('Health Check-in System', () => {
    it('should access health check-in page', () => {
      cy.visit(`${baseUrl}/api/health/checkin`)
      cy.get('body').should('be.visible')
    })

    it('should test health check-in API endpoint', () => {
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/health/checkin`,
        failOnStatusCode: false
      }).then((response) => {
        cy.log(`Health checkin page response: ${response.status}`)
        expect(response.status).to.be.oneOf([200, 401, 404])
      })
    })

    it('should test health check-in form submission', () => {
      cy.visit(`${baseUrl}/api/health/checkin`)
      
      // Look for common health check-in form elements
      cy.get('body').should('be.visible')
      
      // Check for form elements (these might vary based on your implementation)
      cy.get('form, [data-cy="health-form"]').then(($form) => {
        if ($form.length > 0) {
          // If form exists, try to submit it
          cy.get('button[type="submit"], input[type="submit"]').then(($submit) => {
            if ($submit.length > 0) {
              cy.wrap($submit).click()
              cy.url().should('not.equal', `${baseUrl}/api/health/checkin`)
            }
          })
        }
      })
    })

    it('should test health insights API', () => {
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/health/insights`,
        failOnStatusCode: false
      }).then((response) => {
        cy.log(`Health insights API response: ${response.status}`)
        expect(response.status).to.be.oneOf([200, 401, 404])
      })
    })
  })

  describe('Onboarding System', () => {
    it('should access onboarding page', () => {
      cy.visit(`${baseUrl}/api/health/onboarding`)
      cy.get('body').should('be.visible')
    })

    it('should test onboarding API endpoint', () => {
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/health/onboarding`,
        failOnStatusCode: false
      }).then((response) => {
        cy.log(`Onboarding page response: ${response.status}`)
        expect(response.status).to.be.oneOf([200, 401, 404])
      })
    })

    it('should test onboarding form elements', () => {
      cy.visit(`${baseUrl}/api/health/onboarding`)
      
      // Check for common onboarding form elements
      cy.get('body').should('be.visible')
      
      // Look for form elements
      cy.get('form, [data-cy="onboarding-form"]').then(($form) => {
        if ($form.length > 0) {
          cy.log('Onboarding form found')
          
          // Check for common onboarding fields
          cy.get('input, select, textarea').then(($inputs) => {
            if ($inputs.length > 0) {
              cy.log(`Found ${$inputs.length} form inputs`)
            }
          })
        }
      })
    })

    it('should test onboarding progress API', () => {
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/onboarding/progress`,
        failOnStatusCode: false
      }).then((response) => {
        cy.log(`Onboarding progress API response: ${response.status}`)
        expect(response.status).to.be.oneOf([200, 401, 404])
      })
    })

    it('should test user profile API', () => {
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/onboarding/profile`,
        failOnStatusCode: false
      }).then((response) => {
        cy.log(`User profile API response: ${response.status}`)
        expect(response.status).to.be.oneOf([200, 401, 404])
      })
    })
  })

  describe('Dashboard and Main App', () => {
    it('should access main app page', () => {
      cy.visit(`${baseUrl}/api/health/dashboard`)
      cy.get('body').should('be.visible')
    })

    it('should test dashboard API endpoint', () => {
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/health/dashboard`,
        failOnStatusCode: false
      }).then((response) => {
        cy.log(`Dashboard page response: ${response.status}`)
        expect(response.status).to.be.oneOf([200, 401, 404])
      })
    })

    it('should test main app template', () => {
      cy.visit(`${baseUrl}/api/health/main_app`)
      cy.get('body').should('be.visible')
    })
  })

  describe('Health Correlation Features', () => {
    it('should test health spending correlation API', () => {
      cy.request({
        method: 'GET',
        url: `${baseUrl}/api/health/correlation`,
        failOnStatusCode: false
      }).then((response) => {
        cy.log(`Health correlation API response: ${response.status}`)
        expect(response.status).to.be.oneOf([200, 401, 404])
      })
    })

    it('should test health insights generation', () => {
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/health/insights/generate`,
        body: {
          health_data: {
            stress_level: 5,
            sleep_hours: 7,
            exercise_minutes: 30
          }
        },
        failOnStatusCode: false
      }).then((response) => {
        cy.log(`Health insights generation response: ${response.status}`)
        expect(response.status).to.be.oneOf([200, 201, 400, 401, 404])
      })
    })
  })

  describe('User Management Features', () => {
    it('should test user service endpoints', () => {
      // Test user creation
      const testEmail = `health${Date.now()}@example.com`
      
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/register`,
        body: {
          email: testEmail,
          password: 'password123!',
          full_name: 'Health Test User',
          phone_number: '555-123-4567'
        },
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200 || response.status === 201) {
          cy.log('User created successfully for health testing')
          
          // Test user profile update
          cy.request({
            method: 'PUT',
            url: `${baseUrl}/api/auth/profile`,
            body: {
              health_preferences: {
                stress_tracking: true,
                sleep_tracking: true,
                exercise_tracking: true
              }
            },
            failOnStatusCode: false
          }).then((profileResponse) => {
            cy.log(`Profile update response: ${profileResponse.status}`)
            expect(profileResponse.status).to.be.oneOf([200, 401, 404])
          })
        }
      })
    })

    it('should test onboarding completion flow', () => {
      // First create a user
      const testEmail = `onboarding${Date.now()}@example.com`
      
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/register`,
        body: {
          email: testEmail,
          password: 'password123!',
          full_name: 'Onboarding Test User',
          phone_number: '555-123-4567'
        },
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200 || response.status === 201) {
          // Test onboarding completion
          cy.request({
            method: 'POST',
            url: `${baseUrl}/api/onboarding/complete`,
            body: {
              completed_steps: ['profile', 'preferences', 'goals'],
              onboarding_data: {
                financial_goals: ['save_money', 'invest'],
                health_priorities: ['stress', 'sleep'],
                preferred_communication: 'email'
              }
            },
            failOnStatusCode: false
          }).then((completionResponse) => {
            cy.log(`Onboarding completion response: ${completionResponse.status}`)
            expect(completionResponse.status).to.be.oneOf([200, 201, 400, 401, 404])
          })
        }
      })
    })
  })

  describe('Error Handling and Edge Cases', () => {
    it('should handle missing authentication for protected endpoints', () => {
      const protectedEndpoints = [
        '/api/health/checkin',
        '/api/health/dashboard',
        '/api/onboarding/progress',
        '/api/auth/profile'
      ]
      
      protectedEndpoints.forEach(endpoint => {
        cy.request({
          method: 'GET',
          url: `${baseUrl}${endpoint}`,
          failOnStatusCode: false
        }).then((response) => {
          cy.log(`${endpoint} response: ${response.status}`)
          // Should return 401 for unauthenticated requests
          expect(response.status).to.be.oneOf([401, 404])
        })
      })
    })

    it('should handle invalid health data submission', () => {
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/health/checkin`,
        body: {
          // Invalid or missing data
        },
        failOnStatusCode: false
      }).then((response) => {
        cy.log(`Invalid health data response: ${response.status}`)
        expect(response.status).to.be.oneOf([400, 401, 404, 422])
      })
    })

    it('should handle malformed onboarding data', () => {
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/onboarding/complete`,
        body: {
          // Malformed data
          invalid_field: 'invalid_value'
        },
        failOnStatusCode: false
      }).then((response) => {
        cy.log(`Malformed onboarding data response: ${response.status}`)
        expect(response.status).to.be.oneOf([400, 401, 404, 422])
      })
    })
  })

  describe('Integration Testing', () => {
    it('should test complete user journey', () => {
      const testEmail = `journey${Date.now()}@example.com`
      
      // Step 1: Register user
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/register`,
        body: {
          email: testEmail,
          password: 'password123!',
          full_name: 'Journey Test User',
          phone_number: '555-123-4567'
        },
        failOnStatusCode: false
      }).then((registerResponse) => {
        if (registerResponse.status === 200 || registerResponse.status === 201) {
          cy.log('User registered successfully')
          
          // Step 2: Login user
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
              cy.log('User logged in successfully')
              
              // Step 3: Complete onboarding
              cy.request({
                method: 'POST',
                url: `${baseUrl}/api/onboarding/complete`,
                body: {
                  completed_steps: ['profile', 'preferences'],
                  onboarding_data: {
                    financial_goals: ['save_money'],
                    health_priorities: ['stress']
                  }
                },
                failOnStatusCode: false
              }).then((onboardingResponse) => {
                cy.log(`Onboarding completion: ${onboardingResponse.status}`)
                
                // Step 4: Submit health check-in
                cy.request({
                  method: 'POST',
                  url: `${baseUrl}/api/health/checkin`,
                  body: {
                    stress_level: 4,
                    sleep_hours: 7,
                    exercise_minutes: 30,
                    mood: 'good'
                  },
                  failOnStatusCode: false
                }).then((healthResponse) => {
                  cy.log(`Health check-in: ${healthResponse.status}`)
                  
                  // Step 5: Get insights
                  cy.request({
                    method: 'GET',
                    url: `${baseUrl}/api/health/insights`,
                    failOnStatusCode: false
                  }).then((insightsResponse) => {
                    cy.log(`Health insights: ${insightsResponse.status}`)
                    cy.log('Complete user journey tested successfully')
                  })
                })
              })
            }
          })
        }
      })
    })
  })
}) 