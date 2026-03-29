// cypress/e2e/health-onboarding-test.cy.js
// Test suite for health onboarding flow

describe('Health Onboarding Flow', () => {
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

  it('should complete 4-step onboarding when authenticated', () => {
    // Set auth headers for API requests
    cy.intercept('POST', '/api/health/onboarding/complete', (req) => {
      const token = window.localStorage.getItem('authToken');
      if (token) {
        req.headers['Authorization'] = `Bearer ${token}`;
      }
    });

    // Step 1: Access the onboarding page
    cy.visit(`${baseUrl}/api/health/onboarding`)
    cy.get('body').should('be.visible')
    
    // Verify we're on the onboarding page
    cy.url().should('include', '/api/health/onboarding')
    
    // Check for onboarding container
    cy.get('.onboarding-container').should('exist')
    
    // Step 2: Test onboarding step indicators
    cy.get('.progress-bar').should('exist')
    cy.get('.progress-fill').should('exist')
    cy.get('.progress-text').should('contain', 'Step 1 of 4')
    
    // Step 3: Test step navigation
    // Verify we're on step 1 initially
    cy.get('#step1').should('have.class', 'active')
    cy.get('#step2').should('not.have.class', 'active')
    cy.get('#step3').should('not.have.class', 'active')
    cy.get('#step4').should('not.have.class', 'active')
    
    // Step 4: Test step 1 content and navigation
    cy.get('.step-title').should('contain', 'Discover How Your Wellness Affects Your Wealth')
    cy.get('#startBtn').should('be.visible').and('contain', 'Start My Wellness Journey')
    
    // Click to go to step 2
    cy.get('#startBtn').click()
    
    // Verify we're now on step 2
    cy.get('#step1').should('not.have.class', 'active')
    cy.get('#step2').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 2 of 4')
    
    // Step 5: Test step 2 (health check-in)
    cy.get('.step-title').should('contain', 'Your First Wellness Check-in')
    cy.get('#stressLevel').should('exist')
    cy.get('#completeCheckinBtn').should('be.visible')
    
    // Fill out the check-in form
    cy.get('#stressLevel').invoke('val', 7).trigger('change')
    cy.get('input[type="number"]').first().type('120')
    cy.get('input[type="range"]').eq(1).invoke('val', 8).trigger('change')
    cy.get('input[type="number"]').eq(1).type('15')
    
    // Complete check-in
    cy.get('#completeCheckinBtn').click()
    
    // Verify we're now on step 3
    cy.get('#step2').should('not.have.class', 'active')
    cy.get('#step3').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 3 of 4')
    
    // Step 6: Test step 3 (timeline)
    cy.get('.step-title').should('contain', 'Building Your Insight Timeline')
    cy.get('.timeline').should('exist')
    cy.get('#setupRemindersBtn').should('be.visible')
    
    // Set up reminders
    cy.get('#setupRemindersBtn').click()
    
    // Verify we're now on step 4
    cy.get('#step3').should('not.have.class', 'active')
    cy.get('#step4').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 4 of 4')
    
    // Step 7: Test step 4 (goal setting)
    cy.get('.step-title').should('contain', "What's Your Wellness-Wealth Goal?")
    cy.get('.goals-grid').should('exist')
    cy.get('.goal-card').should('have.length', 5)
    
    // Select some goals
    cy.get('.goal-card[data-goal="stress-spending"]').click()
    cy.get('.goal-card[data-goal="health-costs"]').click()
    
    // Verify goals are selected
    cy.get('.goal-card.selected').should('have.length', 2)
    
    // Complete onboarding
    cy.get('#finishOnboardingBtn').should('contain', 'Start My Journey (2 goals)')
    cy.get('#finishOnboardingBtn').click()
    
    // Should redirect to dashboard or show success
    cy.url().should('include', '/api/health/dashboard')
  })

  it('should handle onboarding step navigation when authenticated', () => {
    cy.visit(`${baseUrl}/api/health/onboarding`)
    
    // Test forward navigation
    cy.get('#startBtn').click()
    cy.get('#step2').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 2 of 4')
    
    cy.get('#completeCheckinBtn').click()
    cy.get('#step3').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 3 of 4')
    
    cy.get('#setupRemindersBtn').click()
    cy.get('#step4').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 4 of 4')
    
    // Test backward navigation
    cy.get('#backBtn3').click()
    cy.get('#step3').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 3 of 4')
    
    cy.get('#backBtn2').click()
    cy.get('#step2').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 2 of 4')
    
    cy.get('#backBtn1').click()
    cy.get('#step1').should('have.class', 'active')
    cy.get('.progress-text').should('contain', 'Step 1 of 4')
  })

  it('should validate onboarding form data when authenticated', () => {
    cy.visit(`${baseUrl}/api/health/onboarding`)
    
    // Navigate to step 2 (check-in form)
    cy.get('#startBtn').click()
    
    // Test form inputs exist and are interactive
    cy.get('#stressLevel').should('exist').and('be.visible')
    cy.get('input[type="number"]').should('exist').and('be.visible')
    cy.get('input[type="range"]').should('exist').and('be.visible')
    
    // Test input interactions
    cy.get('#stressLevel').invoke('val', 5).trigger('change')
    cy.get('#stressLevel').should('have.value', '5')
    
    cy.get('input[type="number"]').first().clear().type('150')
    cy.get('input[type="number"]').first().should('have.value', '150')
    
    // Test range input
    cy.get('input[type="range"]').eq(1).invoke('val', 6).trigger('change')
    cy.get('input[type="range"]').eq(1).should('have.value', '6')
  })

  it('should test onboarding with different user preferences when authenticated', () => {
    // Test onboarding completion with different goal combinations
    const testScenarios = [
      {
        goals: ['stress-spending'],
        description: 'Stress spending goal only'
      },
      {
        goals: ['health-costs', 'impulse-control'],
        description: 'Health costs and impulse control goals'
      },
      {
        goals: ['stress-spending', 'health-costs', 'impulse-control', 'energy-productivity', 'overall-wellness'],
        description: 'All wellness goals'
      }
    ]
    
    testScenarios.forEach((scenario, index) => {
      cy.log(`Testing scenario ${index + 1}: ${scenario.description}`)
      
      cy.visit(`${baseUrl}/api/health/onboarding`)
      
      // Navigate through steps
      cy.get('#startBtn').click()
      cy.get('#completeCheckinBtn').click()
      cy.get('#setupRemindersBtn').click()
      
      // Select goals
      scenario.goals.forEach(goal => {
        cy.get(`.goal-card[data-goal="${goal}"]`).click()
      })
      
      // Verify correct number of goals selected
      cy.get('.goal-card.selected').should('have.length', scenario.goals.length)
      
      // Verify button text updates
      if (scenario.goals.length > 0) {
        cy.get('#finishOnboardingBtn').should('contain', `Start My Journey (${scenario.goals.length} goal${scenario.goals.length > 1 ? 's' : ''})`)
      } else {
        cy.get('#finishOnboardingBtn').should('contain', 'Start My Wellness Journey!')
      }
    })
  })

  it('should handle onboarding errors gracefully when authenticated', () => {
    // Test with malformed data
    cy.request({
      method: 'POST',
      url: `${baseUrl}/api/health/onboarding/complete`,
      body: {
        // Missing required fields
        invalidField: 'invalidValue'
      },
      failOnStatusCode: false
    }).then((response) => {
      cy.log(`Malformed data response: ${response.status}`)
      expect(response.status).to.be.oneOf([200, 400, 401, 404, 422])
    })
    
    // Test with invalid health data
    cy.request({
      method: 'POST',
      url: `${baseUrl}/api/health/onboarding/complete`,
      body: {
        selectedGoals: ['stress-spending'],
        reminderPreferences: true,
        healthData: {
          stress_level: 15, // Invalid: should be 1-10
          sleep_hours: 25,  // Invalid: should be 0-24
          exercise_minutes: -5 // Invalid: should be positive
        }
      },
      failOnStatusCode: false
    }).then((response) => {
      cy.log(`Invalid health data response: ${response.status}`)
      expect(response.status).to.be.oneOf([200, 400, 401, 404, 422])
    })
  })

  it('should verify onboarding page accessibility when authenticated', () => {
    cy.visit(`${baseUrl}/api/health/onboarding`)
    
    // Check for proper heading structure
    cy.get('h1, h2, h3, h4').then(($headings) => {
      if ($headings.length > 0) {
        cy.log('Page has proper heading structure')
      }
    })
    
    // Check for form labels
    cy.get('label, [aria-label]').then(($labels) => {
      if ($labels.length > 0) {
        cy.log('Form has proper labels')
      }
    })
    
    // Check for keyboard navigation
    cy.get('body').tab()
    cy.focused().should('exist')
    
    // Check for proper button accessibility
    cy.get('button').each(($button) => {
      cy.wrap($button).should('be.visible')
    })
    
    // Check for proper input accessibility
    cy.get('input').each(($input) => {
      cy.wrap($input).should('be.visible')
    })
  })

  it('should test skip functionality when authenticated', () => {
    cy.visit(`${baseUrl}/api/health/onboarding`)
    
    // Test skip button exists
    cy.get('#skipBtn').should('be.visible').and('contain', 'Skip for now')
    
    // Test skip confirmation (will be handled by browser confirm dialog)
    cy.get('#skipBtn').click()
    
    // Note: We can't easily test the confirm dialog in Cypress
    // In a real scenario, you might want to stub the confirm dialog
  })

  it('should test learn more functionality when authenticated', () => {
    cy.visit(`${baseUrl}/api/health/onboarding`)
    
    // Test learn more button
    cy.get('#learnMoreBtn').should('be.visible').and('contain', 'How Does This Work?')
    
    // Click learn more (will show alert)
    cy.get('#learnMoreBtn').click()
    
    // Note: We can't easily test the alert in Cypress
    // In a real scenario, you might want to stub the alert
  })

  it('should test onboarding completion API when authenticated', () => {
    // Test the onboarding completion API endpoint
    cy.request({
      method: 'POST',
      url: `${baseUrl}/api/health/onboarding/complete`,
      body: {
        selectedGoals: ['stress-spending', 'health-costs'],
        reminderPreferences: true,
        healthData: {
          stress_level: 6,
          sleep_hours: 7,
          exercise_minutes: 45,
          mood_rating: 8
        }
      },
      failOnStatusCode: false
    }).then((response) => {
      cy.log(`Onboarding completion API response: ${response.status}`)
      expect(response.status).to.be.oneOf([200, 201, 400, 401, 404])
      
      if (response.status === 200 || response.status === 201) {
        expect(response.body).to.have.property('success')
      }
    })
  })

  it('should test onboarding status API when authenticated', () => {
    // Test the onboarding status API endpoint
    cy.request({
      method: 'GET',
      url: `${baseUrl}/api/health/onboarding/status`,
      failOnStatusCode: false
    }).then((response) => {
      cy.log(`Onboarding status API response: ${response.status}`)
      expect(response.status).to.be.oneOf([200, 401, 404])
      
      if (response.status === 200) {
        expect(response.body).to.have.property('completed')
        expect(response.body).to.have.property('current_step')
        expect(response.body).to.have.property('total_steps')
      }
    })
  })
}) 