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

// ***********************************************
// NEW COMMANDS FOR COMPREHENSIVE USER JOURNEY
// ***********************************************

/**
 * Complete profile setup step
 */
Cypress.Commands.add('completeProfileSetup', (profileData) => {
  cy.get('#age').type(profileData.age)
  cy.get('#gender').select(profileData.gender)
  cy.get('#location').type(profileData.location)
  cy.get('#income').type(profileData.income)
  cy.get('#household-size').type(profileData.householdSize)
  cy.get('#save-profile-btn').click()
  cy.wait(1000)
})

/**
 * Complete baseline assessment step
 */
Cypress.Commands.add('completeBaselineAssessment', (careerData, financialData) => {
  // Career information
  cy.get('#company-name').type(careerData.companyName)
  cy.get('#industry').select(careerData.industry)
  cy.get('#job-title').type(careerData.jobTitle)
  cy.get('#years-experience').type(careerData.yearsExperience)
  cy.get('#job-satisfaction').select(careerData.jobSatisfaction)
  
  // Financial information
  cy.get('#monthly-income').type(financialData.income)
  cy.get('#monthly-expenses').type(financialData.expenses)
  cy.get('#current-savings').type(financialData.savings)
  cy.get('#debt-amount').type(financialData.debt)
  
  cy.get('#save-baseline-btn').click()
  cy.wait(1000)
})

/**
 * Complete goal setting step
 */
Cypress.Commands.add('completeGoalSetting', (goalsData) => {
  // Select goal types
  goalsData.forEach((goal, index) => {
    cy.get('.goal-type-card').contains(goal.name).click()
  })
  
  // Configure each goal
  goalsData.forEach((goal, index) => {
    cy.get(`#${goal.type}-details`).click()
    cy.get('input[placeholder="0"]').type(goal.targetAmount)
    cy.get('button').contains('1 year').click()
    cy.get('textarea').type(goal.motivationNote)
    cy.get('#save-goal-btn').click()
    cy.wait(500)
  })
})

/**
 * Complete education and consent step
 */
Cypress.Commands.add('completeEducationConsent', () => {
  cy.get('#data-consent-checkbox').check()
  cy.get('#privacy-policy-checkbox').check()
  cy.get('#terms-of-service-checkbox').check()
  cy.get('#accept-consent-btn').click()
  cy.wait(1000)
})

/**
 * Complete app tour
 */
Cypress.Commands.add('completeAppTour', (tourData) => {
  tourData.steps.forEach((step, index) => {
    cy.get('#next-tour-step').click()
    cy.wait(500)
  })
  cy.get('#finish-tour-btn').click()
  cy.wait(1000)
})

/**
 * Complete onboarding completion step
 */
Cypress.Commands.add('completeOnboardingCompletion', (notificationData) => {
  cy.get('#weekly-checkin-checkbox').check()
  cy.get('#reminder-frequency').select(notificationData.frequency)
  cy.get('#notification-preferences').check()
  cy.get('#complete-onboarding-btn').click()
  cy.wait(2000)
})

/**
 * Verify dashboard elements
 */
Cypress.Commands.add('verifyDashboard', () => {
  cy.get('.dashboard-container').should('be.visible')
  cy.get('.health-summary').should('be.visible')
  cy.get('.financial-overview').should('be.visible')
  cy.get('.goals-progress').should('be.visible')
  cy.get('.insights-cards').should('be.visible')
})

/**
 * Test goal management
 */
Cypress.Commands.add('testGoalManagement', (goalData) => {
  cy.get('.goal-item').should('have.length.at.least', 1)
  cy.get('.goal-item').contains(goalData.name).should('be.visible')
  
  // Update goal progress
  cy.get('.goal-item').first().find('.update-progress-btn').click()
  cy.get('#progress-amount').type('5000')
  cy.get('#progress-notes').type('Monthly contribution')
  cy.get('#save-progress-btn').click()
  cy.wait(500)
  
  // Verify progress updated
  cy.get('.goal-progress-bar').should('contain', '33%')
})

/**
 * Test insights and recommendations
 */
Cypress.Commands.add('testInsights', (insightsData) => {
  cy.get('.job-security-insight').should('be.visible')
  cy.get('.emergency-fund-insight').should('be.visible')
  cy.get('.cash-flow-insight').should('be.visible')
  cy.get('.health-relationship-insight').should('be.visible')
  
  // Test insight interactions
  cy.get('.insight-card').first().find('.learn-more-btn').click()
  cy.get('.insight-details').should('be.visible')
  cy.get('#close-insight-btn').click()
  cy.wait(500)
})

/**
 * Test next steps checklist
 */
Cypress.Commands.add('testChecklist', (checklistData) => {
  cy.get('.checklist-container').should('be.visible')
  cy.get('.checklist-item').should('have.length.at.least', 3)
  
  // Complete checklist items
  cy.get('.checklist-item').first().find('.complete-checkbox').check()
  cy.get('.checklist-item').eq(1).find('.complete-checkbox').check()
  
  // Verify progress updates
  cy.get('.checklist-progress').should('contain', '67%')
})

/**
 * Test notifications and reminders
 */
Cypress.Commands.add('testNotifications', (notificationData) => {
  cy.get('.notification-preferences').should('be.visible')
  cy.get('#goal-reminders').check()
  cy.get('#insight-updates').check()
  cy.get('#weekly-checkins').check()
  
  cy.get('#save-notification-preferences').click()
  cy.wait(500)
})

/**
 * Test profile and settings
 */
Cypress.Commands.add('testProfileSettings', (userData, profileData) => {
  cy.get('.profile-container').should('be.visible')
  cy.get('body').should('contain', userData.firstName)
  cy.get('body').should('contain', userData.lastName)
  cy.get('body').should('contain', userData.email)
  
  // Update profile
  cy.get('#edit-profile-btn').click()
  cy.get('#bio').type(profileData.bio)
  cy.get('#save-profile-btn').click()
  cy.wait(500)
})

/**
 * Test logout and session management
 */
Cypress.Commands.add('testLogoutSession', (userData) => {
  cy.get('#user-menu').click()
  cy.get('#logout-btn').click()
  cy.wait(1000)
  
  // Verify logout
  cy.url().should('include', '/login')
  cy.get('body').should('contain', 'Sign In')
  
  // Test login with same credentials
  cy.get('input[name="email"]').type(userData.email)
  cy.get('input[name="password"]').type(userData.password)
  cy.get('button[type="submit"]').click()
  cy.wait(2000)
  
  // Verify successful login
  cy.url().should('include', '/dashboard')
  cy.get('.dashboard-container').should('be.visible')
})

/**
 * Test error scenarios
 */
Cypress.Commands.add('testErrorScenarios', (errorData) => {
  // Test invalid registration
  cy.get('input[name="email"]').type(errorData.invalidEmail)
  cy.get('input[name="password"]').type(errorData.weakPassword)
  cy.get('button[type="submit"]').click()
  
  // Should show validation errors
  cy.get('.error-message').should('be.visible')
  cy.get('body').should('contain', 'Please enter a valid email')
  cy.get('body').should('contain', 'Password must be stronger')
})

/**
 * Test mobile responsiveness
 */
Cypress.Commands.add('testMobileResponsiveness', (mobileData) => {
  // Set mobile viewport
  cy.viewport(mobileData.viewport)
  
  // Test key elements on mobile
  mobileData.elements.forEach(element => {
    cy.get(element).should('be.visible')
  })
  
  // Reset viewport
  cy.viewport(1280, 720)
})

/**
 * Test accessibility features
 */
Cypress.Commands.add('testAccessibility', (accessibilityData) => {
  // Test keyboard navigation
  cy.get('body').tab()
  cy.focused().should('have.attr', 'name', 'email')
  
  // Test screen reader compatibility
  accessibilityData.ariaLabels.forEach(label => {
    cy.get(`[aria-label="${label}"]`).should('exist')
  })
  
  // Test color contrast (basic check)
  cy.get('body').should('have.css', 'color')
})

/**
 * Complete entire onboarding flow
 */
Cypress.Commands.add('completeFullOnboarding', (testData) => {
  // Registration
  cy.registerUser(testData.user)
  
  // Profile setup
  cy.completeProfileSetup(testData.profile)
  
  // Baseline assessment
  cy.completeBaselineAssessment(testData.careerProfile, testData.financialProfile)
  
  // Goal setting
  cy.completeGoalSetting(testData.goals)
  
  // Education and consent
  cy.completeEducationConsent()
  
  // App tour
  cy.completeAppTour(testData.tour)
  
  // Onboarding completion
  cy.completeOnboardingCompletion(testData.notifications)
  
  // Verify dashboard access
  cy.verifyDashboard()
})

/**
 * Test complete user journey
 */
Cypress.Commands.add('testCompleteUserJourney', (testData) => {
  // Complete onboarding
  cy.completeFullOnboarding(testData)
  
  // Test goal management
  cy.testGoalManagement(testData.goals[0])
  
  // Test insights
  cy.testInsights(testData.insights)
  
  // Test checklist
  cy.testChecklist(testData.checklist)
  
  // Test notifications
  cy.testNotifications(testData.notifications)
  
  // Test profile settings
  cy.testProfileSettings(testData.user, testData.profile)
  
  // Test logout and session
  cy.testLogoutSession(testData.user)
})