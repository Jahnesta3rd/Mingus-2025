// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

// ***********************************************
// Custom commands for Mingus Application E2E Tests
// ***********************************************

// Custom commands for Mingus application

/**
 * Register a new user
 */
Cypress.Commands.add('registerUser', (userData) => {
  cy.request({
    method: 'POST',
    url: '/api/auth/register',
    body: {
      email: userData.email,
      password: userData.password,
      first_name: userData.firstName,
      last_name: userData.lastName,
      phone_number: userData.phoneNumber
    },
    failOnStatusCode: false
  }).then((response) => {
    if (response.status === 200 || response.status === 302) {
      cy.log('User registered successfully')
    } else {
      cy.log('User registration response:', response.status, response.body)
    }
  })
})

/**
 * Login user via API
 */
Cypress.Commands.add('loginUser', (email, password) => {
  cy.request({
    method: 'POST',
    url: '/api/auth/login',
    body: {
      email: email,
      password: password
    },
    failOnStatusCode: false
  }).then((response) => {
    if (response.status === 200) {
      cy.log('User logged in successfully')
      // Store session data if needed
      if (response.body.user) {
        cy.window().then((win) => {
          win.localStorage.setItem('user', JSON.stringify(response.body.user))
        })
      }
    } else {
      cy.log('Login response:', response.status, response.body)
    }
  })
})

/**
 * Complete health onboarding questionnaire
 */
Cypress.Commands.add('completeHealthOnboarding', (healthData) => {
  // Step 1: Basic Information
  cy.get('#age').type(healthData.age)
  cy.get('#gender').select(healthData.gender)
  cy.get('#height').type(healthData.height)
  cy.get('#weight').type(healthData.weight)
  cy.get('#activity-level').select(healthData.activityLevel)
  
  // Navigate to next step
  cy.get('.onboarding-nav button[data-step="next"]').click()
  
  // Step 2: Lifestyle
  cy.get('#sleep-hours').type(healthData.sleepHours)
  cy.get('#stress-level').select(healthData.stressLevel)
  cy.get('#diet-type').select(healthData.dietType)
  cy.get('#smoking-status').select(healthData.smokingStatus)
  cy.get('#alcohol-consumption').select(healthData.alcoholConsumption)
  
  // Navigate to next step
  cy.get('.onboarding-nav button[data-step="next"]').click()
  
  // Step 3: Health Goals
  healthData.healthGoals.forEach(goal => {
    cy.get(`input[value="${goal}"]`).check()
  })
  
  // Navigate to next step
  cy.get('.onboarding-nav button[data-step="next"]').click()
  
  // Step 4: Preferred Activities
  healthData.preferredActivities.forEach(activity => {
    cy.get(`input[value="${activity}"]`).check()
  })
  
  // Complete onboarding
  cy.get('.onboarding-nav button[data-step="complete"]').click()
})

/**
 * Complete financial questionnaire
 */
Cypress.Commands.add('completeFinancialQuestionnaire', (financialData) => {
  cy.get('#income').type(financialData.income)
  cy.get('#expenses').type(financialData.expenses)
  cy.get('#savings').type(financialData.savings)
  cy.get('#debt').type(financialData.debt)
  cy.get('#emergency-fund').type(financialData.emergencyFund)
  cy.get('#risk-tolerance').select(financialData.riskTolerance)
  
  financialData.investmentGoals.forEach(goal => {
    cy.get(`input[value="${goal}"]`).check()
  })
  
  cy.get('#save-financial-profile').click()
})

/**
 * Complete career questionnaire
 */
Cypress.Commands.add('completeCareerQuestionnaire', (careerData) => {
  cy.get('#industry').select(careerData.industry)
  cy.get('#job-title').type(careerData.jobTitle)
  cy.get('#years-experience').type(careerData.yearsExperience)
  cy.get('#company-size').select(careerData.companySize)
  cy.get('#job-satisfaction').select(careerData.jobSatisfaction)
  
  careerData.careerGoals.forEach(goal => {
    cy.get(`input[value="${goal}"]`).check()
  })
  
  if (careerData.willingToRelocate) {
    cy.get('#willing-relocate').check()
  }
  
  if (careerData.openToRemote) {
    cy.get('#open-remote').check()
  }
  
  cy.get('#save-career-profile').click()
})

/**
 * Wait for page to load and check for common elements
 */
Cypress.Commands.add('waitForPageLoad', () => {
  cy.get('body').should('be.visible')
  cy.wait(1000) // Allow for any animations or dynamic content
})

/**
 * Check if user is authenticated
 */
Cypress.Commands.add('checkAuthStatus', () => {
  cy.request({
    method: 'GET',
    url: '/api/auth/check-auth',
    failOnStatusCode: false
  }).then((response) => {
    return response.body.authenticated
  })
})

/**
 * Navigate to dashboard and verify access
 */
Cypress.Commands.add('navigateToDashboard', () => {
  cy.visit('/api/health/dashboard')
  cy.waitForPageLoad()
  
  // Check for dashboard elements
  cy.get('body').should('contain', 'Dashboard')
  cy.get('.dashboard-container').should('be.visible')
})