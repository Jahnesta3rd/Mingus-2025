/**
 * Job Security Workflow E2E Tests
 * Tests complete user journey from registration to job security insights
 */

describe('Job Security Workflow', () => {
  beforeEach(() => {
    // Clear cookies and local storage before each test
    cy.clearCookies()
    cy.clearLocalStorage()
    
    // Visit the application
    cy.visit('/')
  })

  it('should complete full job security onboarding workflow', () => {
    // Step 1: User registration
    cy.get('[data-testid="register-link"]').click()
    
    cy.get('[data-testid="email-input"]').type(Cypress.env('testUser').email)
    cy.get('[data-testid="password-input"]').type(Cypress.env('testUser').password)
    cy.get('[data-testid="first-name-input"]').type(Cypress.env('testUser').firstName)
    cy.get('[data-testid="last-name-input"]').type(Cypress.env('testUser').lastName)
    cy.get('[data-testid="phone-input"]').type('1234567890')
    
    cy.get('[data-testid="register-button"]').click()
    
    // Should redirect to onboarding
    cy.url().should('include', '/onboarding')
    
    // Step 2: Job security onboarding
    cy.get('[data-testid="job-security-onboarding-start"]').click()
    
    // Employment information step
    cy.get('[data-testid="company-name-input"]').type(Cypress.env('testCompany').name)
    cy.get('[data-testid="industry-select"]').select(Cypress.env('testCompany').industry)
    cy.get('[data-testid="job-title-input"]').type('Software Engineer')
    cy.get('[data-testid="years-experience-input"]').type('5')
    cy.get('[data-testid="current-salary-input"]').type('80000')
    cy.get('[data-testid="tenure-months-input"]').type('24')
    cy.get('[data-testid="department-select"]').select('engineering')
    cy.get('[data-testid="role-level-select"]').select('senior')
    
    cy.get('[data-testid="next-step-button"]').click()
    
    // Skills information step
    cy.get('[data-testid="technical-skills-input"]').type('python, javascript, react')
    cy.get('[data-testid="soft-skills-input"]').type('leadership, communication')
    cy.get('[data-testid="certifications-input"]').type('AWS, PMP')
    cy.get('[data-testid="willingness-relocate-checkbox"]').check()
    cy.get('[data-testid="remote-work-checkbox"]').check()
    
    cy.get('[data-testid="next-step-button"]').click()
    
    // Financial information step
    cy.get('[data-testid="current-savings-input"]').type('15000')
    cy.get('[data-testid="monthly-expenses-input"]').type('4000')
    cy.get('[data-testid="debt-payments-input"]').type('800')
    cy.get('[data-testid="emergency-fund-input"]').type('8000')
    cy.get('[data-testid="investment-assets-input"]').type('25000')
    
    cy.get('[data-testid="next-step-button"]').click()
    
    // Complete onboarding
    cy.get('[data-testid="complete-onboarding-button"]').click()
    
    // Should redirect to dashboard
    cy.url().should('include', '/dashboard')
  })

  it('should display job security dashboard with risk assessment', () => {
    // Login first
    cy.login(Cypress.env('testUser').email, Cypress.env('testUser').password)
    
    // Navigate to job security dashboard
    cy.visit('/job-security/dashboard')
    
    // Check dashboard elements
    cy.get('[data-testid="risk-assessment-card"]').should('be.visible')
    cy.get('[data-testid="risk-score"]').should('be.visible')
    cy.get('[data-testid="risk-level"]').should('be.visible')
    cy.get('[data-testid="risk-factors"]').should('be.visible')
    
    // Check recommendations section
    cy.get('[data-testid="recommendations-section"]').should('be.visible')
    cy.get('[data-testid="skills-recommendations"]').should('be.visible')
    cy.get('[data-testid="financial-recommendations"]').should('be.visible')
    cy.get('[data-testid="career-recommendations"]').should('be.visible')
    
    // Check financial planning section
    cy.get('[data-testid="financial-planning-section"]').should('be.visible')
    cy.get('[data-testid="emergency-fund-status"]').should('be.visible')
    cy.get('[data-testid="investment-strategy"]').should('be.visible')
    
    // Check goals section
    cy.get('[data-testid="goals-section"]').should('be.visible')
    cy.get('[data-testid="current-goals"]').should('be.visible')
    cy.get('[data-testid="recommended-goals"]').should('be.visible')
  })

  it('should create and track job security goals', () => {
    // Login first
    cy.login(Cypress.env('testUser').email, Cypress.env('testUser').password)
    
    // Navigate to goals page
    cy.visit('/job-security/goals')
    
    // Create new goal
    cy.get('[data-testid="create-goal-button"]').click()
    
    cy.get('[data-testid="goal-type-select"]').select('skill_development')
    cy.get('[data-testid="goal-name-input"]').type('Learn Machine Learning')
    cy.get('[data-testid="goal-description-input"]').type('Complete ML certification to improve job security')
    cy.get('[data-testid="goal-target-amount-input"]').type('2000')
    cy.get('[data-testid="goal-timeline-months-input"]').type('6')
    cy.get('[data-testid="goal-priority-select"]').select('high')
    
    cy.get('[data-testid="save-goal-button"]').click()
    
    // Verify goal was created
    cy.get('[data-testid="goal-item"]').should('contain', 'Learn Machine Learning')
    
    // Update goal progress
    cy.get('[data-testid="goal-progress-button"]').first().click()
    cy.get('[data-testid="progress-percentage-input"]').clear().type('25')
    cy.get('[data-testid="progress-notes-input"]').type('Completed first course module')
    cy.get('[data-testid="save-progress-button"]').click()
    
    // Verify progress was updated
    cy.get('[data-testid="goal-progress"]').should('contain', '25%')
  })

  it('should display and manage notifications', () => {
    // Login first
    cy.login(Cypress.env('testUser').email, Cypress.env('testUser').password)
    
    // Navigate to notifications
    cy.visit('/job-security/notifications')
    
    // Check notifications are displayed
    cy.get('[data-testid="notification-item"]').should('have.length.greaterThan', 0)
    
    // Mark notification as read
    cy.get('[data-testid="mark-read-button"]').first().click()
    
    // Verify notification is marked as read
    cy.get('[data-testid="notification-item"]').first().should('have.class', 'read')
    
    // Test notification preferences
    cy.get('[data-testid="notification-preferences-button"]').click()
    
    cy.get('[data-testid="risk-alerts-checkbox"]').check()
    cy.get('[data-testid="recommendation-updates-checkbox"]').check()
    cy.get('[data-testid="goal-reminders-checkbox"]').check()
    cy.get('[data-testid="frequency-select"]').select('weekly')
    
    cy.get('[data-testid="save-preferences-button"]').click()
    
    // Verify preferences were saved
    cy.get('[data-testid="success-message"]').should('contain', 'Preferences saved')
  })

  it('should display career transition planning', () => {
    // Login first
    cy.login(Cypress.env('testUser').email, Cypress.env('testUser').password)
    
    // Navigate to career transition
    cy.visit('/job-security/career-transition')
    
    // Check transition planning elements
    cy.get('[data-testid="transition-timeline"]').should('be.visible')
    cy.get('[data-testid="target-industries"]').should('be.visible')
    cy.get('[data-testid="skill-gaps"]').should('be.visible')
    
    // Explore target industries
    cy.get('[data-testid="industry-item"]').first().click()
    
    // Check industry details
    cy.get('[data-testid="industry-growth-rate"]').should('be.visible')
    cy.get('[data-testid="industry-salary-range"]').should('be.visible')
    cy.get('[data-testid="transition-difficulty"]').should('be.visible')
    
    // Create transition plan
    cy.get('[data-testid="create-transition-plan-button"]').click()
    
    cy.get('[data-testid="target-industry-select"]').select('healthcare')
    cy.get('[data-testid="target-role-input"]').type('Healthcare Data Analyst')
    cy.get('[data-testid="timeline-months-input"]').type('12')
    cy.get('[data-testid="estimated-cost-input"]').type('5000')
    
    cy.get('[data-testid="save-transition-plan-button"]').click()
    
    // Verify plan was created
    cy.get('[data-testid="transition-plan"]').should('contain', 'Healthcare Data Analyst')
  })

  it('should export job security report', () => {
    // Login first
    cy.login(Cypress.env('testUser').email, Cypress.env('testUser').password)
    
    // Navigate to export page
    cy.visit('/job-security/export')
    
    // Select export options
    cy.get('[data-testid="format-select"]').select('pdf')
    cy.get('[data-testid="include-risk-assessment-checkbox"]').check()
    cy.get('[data-testid="include-recommendations-checkbox"]').check()
    cy.get('[data-testid="include-financial-plan-checkbox"]').check()
    
    // Request export
    cy.get('[data-testid="request-export-button"]').click()
    
    // Check export status
    cy.get('[data-testid="export-status"]').should('contain', 'Processing')
    
    // Wait for export to complete
    cy.get('[data-testid="export-status"]', { timeout: 30000 }).should('contain', 'Complete')
    
    // Download export
    cy.get('[data-testid="download-button"]').click()
    
    // Verify download
    cy.readFile('cypress/downloads/job-security-report.pdf').should('exist')
  })

  it('should test accessibility features', () => {
    // Login first
    cy.login(Cypress.env('testUser').email, Cypress.env('testUser').password)
    
    // Navigate to dashboard
    cy.visit('/job-security/dashboard')
    
    // Test keyboard navigation
    cy.get('body').tab()
    cy.focused().should('be.visible')
    
    // Test screen reader compatibility
    cy.get('[data-testid="risk-assessment-card"]').should('have.attr', 'aria-label')
    cy.get('[data-testid="risk-score"]').should('have.attr', 'aria-describedby')
    
    // Test high contrast mode
    cy.get('[data-testid="theme-toggle"]').click()
    cy.get('body').should('have.class', 'high-contrast')
    
    // Test focus indicators
    cy.get('[data-testid="recommendations-section"]').focus()
    cy.get('[data-testid="recommendations-section"]').should('have.css', 'outline')
  })

  it('should test responsive design', () => {
    // Login first
    cy.login(Cypress.env('testUser').email, Cypress.env('testUser').password)
    
    // Test desktop view
    cy.viewport(1280, 720)
    cy.visit('/job-security/dashboard')
    cy.get('[data-testid="dashboard-layout"]').should('be.visible')
    
    // Test tablet view
    cy.viewport(768, 1024)
    cy.get('[data-testid="mobile-menu-button"]').should('be.visible')
    cy.get('[data-testid="dashboard-layout"]').should('be.visible')
    
    // Test mobile view
    cy.viewport(375, 667)
    cy.get('[data-testid="mobile-menu-button"]').click()
    cy.get('[data-testid="mobile-menu"]').should('be.visible')
    
    // Test navigation on mobile
    cy.get('[data-testid="mobile-menu-item-goals"]').click()
    cy.url().should('include', '/goals')
  })

  it('should test error handling', () => {
    // Test invalid login
    cy.visit('/login')
    cy.get('[data-testid="email-input"]').type('invalid@example.com')
    cy.get('[data-testid="password-input"]').type('wrongpassword')
    cy.get('[data-testid="login-button"]').click()
    
    cy.get('[data-testid="error-message"]').should('contain', 'Invalid email or password')
    
    // Test network error handling
    cy.intercept('GET', '/api/job-security/dashboard', { forceNetworkError: true })
    cy.visit('/job-security/dashboard')
    
    cy.get('[data-testid="error-message"]').should('contain', 'Network error')
    
    // Test server error handling
    cy.intercept('GET', '/api/job-security/risk-assessment', { statusCode: 500 })
    cy.get('[data-testid="retry-button"]').click()
    
    cy.get('[data-testid="error-message"]').should('contain', 'Server error')
  })

  it('should test performance metrics', () => {
    // Login first
    cy.login(Cypress.env('testUser').email, Cypress.env('testUser').password)
    
    // Test page load performance
    cy.visit('/job-security/dashboard', {
      onBeforeLoad: (win) => {
        win.performance.mark('page-load-start')
      }
    })
    
    cy.get('[data-testid="risk-assessment-card"]').should('be.visible').then(() => {
      cy.window().then((win) => {
        win.performance.mark('page-load-end')
        win.performance.measure('page-load', 'page-load-start', 'page-load-end')
        
        const measure = win.performance.getEntriesByName('page-load')[0]
        expect(measure.duration).to.be.lessThan(3000) // 3 seconds threshold
      })
    })
    
    // Test API response time
    cy.intercept('GET', '/api/job-security/risk-assessment').as('riskAssessment')
    cy.get('[data-testid="refresh-risk-button"]').click()
    
    cy.wait('@riskAssessment').then((interception) => {
      expect(interception.response.statusCode).to.equal(200)
      expect(interception.response.duration).to.be.lessThan(1000) // 1 second threshold
    })
  })
})

// Custom commands
Cypress.Commands.add('login', (email, password) => {
  cy.visit('/login')
  cy.get('[data-testid="email-input"]').type(email)
  cy.get('[data-testid="password-input"]').type(password)
  cy.get('[data-testid="login-button"]').click()
  cy.url().should('include', '/dashboard')
}) 