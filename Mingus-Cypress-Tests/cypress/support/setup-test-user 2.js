// cypress/support/setup-test-user.js
// Setup script to ensure test user exists

const baseUrl = 'http://127.0.0.1:5002'

export const setupTestUser = () => {
  const testUser = {
    email: 'test@example.com',
    password: 'testpassword123!',
    fullName: 'Test User',
    phoneNumber: '555-123-4567'
  }

  // Check if test user exists by attempting login
  cy.request({
    method: 'POST',
    url: `${baseUrl}/api/auth/login`,
    body: {
      email: testUser.email,
      password: testUser.password
    },
    failOnStatusCode: false
  }).then((response) => {
    if (response.status !== 200) {
      // User doesn't exist or login failed, create new user
      cy.request({
        method: 'POST',
        url: `${baseUrl}/api/auth/register`,
        body: {
          email: testUser.email,
          password: testUser.password,
          full_name: testUser.fullName,
          phone_number: testUser.phoneNumber
        },
        failOnStatusCode: false
      }).then((registerResponse) => {
        if (registerResponse.status === 200 || registerResponse.status === 201) {
          cy.log('Test user created successfully')
        } else {
          cy.log(`Failed to create test user: ${registerResponse.status}`)
        }
      })
    } else {
      cy.log('Test user already exists')
    }
  })

  return testUser
}

export const cleanupTestUser = () => {
  // Cleanup test user if needed
  cy.request({
    method: 'POST',
    url: `${baseUrl}/api/auth/logout`,
    failOnStatusCode: false
  }).then(() => {
    cy.clearLocalStorage()
    cy.clearCookies()
  })
} 