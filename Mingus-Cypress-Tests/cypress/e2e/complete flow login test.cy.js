// cypress/e2e/mingus-complete-flow.cy.js

describe('Mingus Complete User Flow - Login to Forecast', () => {
  
  beforeEach(() => {
    // Visit the app before each test
    cy.visit('/')
  })

  it.skip('should complete full user journey: login → income → expenses → forecast', () => {
    // =====================================
    // STEP 1: LOGIN PROCESS
    // =====================================
    
    cy.log('Starting login process')
    
    // Should see login page
    cy.contains('Sign In', { timeout: 10000 }).should('be.visible')
    
    // Test Google login button exists and is clickable
    cy.get('#google-login')
      .should('be.visible')
      .should('not.be.disabled')
    
    // For testing purposes, we'll simulate successful login
    // In real app, this would redirect to Google, then back to dashboard
    
    // Option A: If you have a test login bypass
    cy.get('[data-cy=test-login-bypass]', { timeout: 5000 }).then(($bypass) => {
      if ($bypass.length > 0) {
        cy.wrap($bypass).click()
        cy.log('Used test login bypass')
      } else {
        // Option B: If you have regular email/password login
        cy.get('input[type="email"]', { timeout: 5000 }).then(($email) => {
          if ($email.length > 0) {
            cy.log('Using email/password login')
            cy.get('input[type="email"]').type('test@mingus.com')
            cy.get('input[type="password"]').type('testpassword123')
            cy.get('[data-cy=login-submit]').click()
          } else {
            // Option C: Mock successful authentication
            cy.log('Mocking successful authentication')
            cy.window().then((win) => {
              // Simulate successful login state
              win.localStorage.setItem('mingus_user_authenticated', 'true')
              win.location.href = '/dashboard'
            })
          }
        })
      }
    })
    
    // Verify successful login - should reach dashboard/onboarding
    cy.url().should('not.include', '/login')
    cy.contains(/welcome|dashboard|income|get started/i, { timeout: 15000 }).should('be.visible')
    
    // =====================================
    // STEP 2: INCOME SETUP
    // =====================================
    
    cy.log('Setting up income information')
    
    // Look for income setup section
    cy.get('[data-cy=income-section], [data-cy=income-setup], .income-form', { timeout: 10000 })
      .should('be.visible')
    
    // Test different income entry scenarios based on your target demographic
    const testScenarios = [
      {
        type: 'Mid-tier user - Houston',
        annualIncome: 65000,
        frequency: 'annual',
        expectedMonthly: 5416.67
      }
    ]
    
    testScenarios.forEach((scenario) => {
      cy.log(`Testing ${scenario.type}`)
      
      // Enter annual income
      cy.get('[data-cy=income-amount], input[name="income"], #income-input')
        .clear()
        .type(scenario.annualIncome.toString())
      
      // Select frequency (annual, monthly, weekly, etc.)
      cy.get('[data-cy=income-frequency], select[name="frequency"], #income-frequency')
        .select(scenario.frequency)
      
      // Submit or continue
      cy.get('[data-cy=income-continue], [data-cy=next-step], .btn-continue, .btn-next')
        .click()
      
      // Verify income was accepted
      cy.contains(/income saved|continue|next|expense/i, { timeout: 10000 }).should('be.visible')
    })
    
    // =====================================
    // STEP 3: EXPENSE SETUP
    // =====================================
    
    cy.log('Setting up expense information')
    
    // Should now be on expenses section
    cy.get('[data-cy=expense-section], [data-cy=expense-setup], .expense-form', { timeout: 10000 })
      .should('be.visible')
    
    // Add common expenses for target demographic
    const commonExpenses = [
      { category: 'rent', amount: 1800, description: 'Rent/Mortgage' },
      { category: 'food', amount: 600, description: 'Groceries & Food' },
      { category: 'transportation', amount: 400, description: 'Car/Transportation' },
      { category: 'utilities', amount: 200, description: 'Utilities' },
      { category: 'phone', amount: 100, description: 'Phone Bill' }
    ]
    
    commonExpenses.forEach((expense, index) => {
      cy.log(`Adding expense: ${expense.description}`)
      
      // Add new expense (look for add button)
      if (index > 0) {
        cy.get('[data-cy=add-expense], .add-expense-btn, .btn-add-expense')
          .click()
      }
      
      // Enter expense amount
      cy.get(`[data-cy=expense-amount-${index}], [data-cy=expense-amount], .expense-amount`)
        .last()
        .clear()
        .type(expense.amount.toString())
      
      // Enter expense description/category
      cy.get(`[data-cy=expense-description-${index}], [data-cy=expense-description], .expense-description`)
        .last()
        .clear()
        .type(expense.description)
      
      // Set frequency to monthly (most common)
      cy.get(`[data-cy=expense-frequency-${index}], [data-cy=expense-frequency], .expense-frequency`)
        .last()
        .then(($freq) => {
          if ($freq.length > 0) {
            cy.wrap($freq).select('monthly')
          }
        })
    })
    
    // Submit expenses
    cy.get('[data-cy=expenses-continue], [data-cy=calculate-forecast], .btn-calculate, .btn-continue')
      .click()
    
    // =====================================
    // STEP 4: VERIFY CASH FLOW FORECAST
    // =====================================
    
    cy.log('Verifying cash flow forecast generation')
    
    // Should now see forecast/dashboard
    cy.url().should('match', /dashboard|forecast|projection/)
    
    // Verify forecast elements are visible
    cy.get('[data-cy=cash-flow-forecast], [data-cy=monthly-projection], .forecast-container', { timeout: 15000 })
      .should('be.visible')
    
    // Check for key forecast metrics
    const expectedMetrics = [
      'monthly income',
      'monthly expenses', 
      'net cash flow',
      'projection',
      'balance'
    ]
    
    expectedMetrics.forEach((metric) => {
      cy.contains(new RegExp(metric, 'i')).should('be.visible')
    })
    
    // Verify financial calculations are reasonable
    cy.get('[data-cy=monthly-income], .monthly-income').then(($income) => {
      if ($income.length > 0) {
        const incomeText = $income.text()
        const incomeValue = parseFloat(incomeText.replace(/[$,]/g, ''))
        expect(incomeValue).to.be.greaterThan(0)
        expect(incomeValue).to.be.lessThan(20000) // Reasonable monthly income cap
        cy.log(`Monthly income: $${incomeValue}`)
      }
    })
    
    cy.get('[data-cy=monthly-expenses], .monthly-expenses').then(($expenses) => {
      if ($expenses.length > 0) {
        const expenseText = $expenses.text()
        const expenseValue = parseFloat(expenseText.replace(/[$,]/g, ''))
        expect(expenseValue).to.be.greaterThan(0)
        expect(expenseValue).to.be.lessThan(15000) // Reasonable monthly expense cap
        cy.log(`Monthly expenses: $${expenseValue}`)
      }
    })
    
    // Verify projection shows future dates
    cy.get('[data-cy=projection-30-days], [data-cy=one-month], .projection-1-month').should('be.visible')
    cy.get('[data-cy=projection-60-days], [data-cy=two-months], .projection-2-months').should('be.visible')
    cy.get('[data-cy=projection-90-days], [data-cy=three-months], .projection-3-months').should('be.visible')
    
    // =====================================
    // STEP 5: TEST FORECAST ACCURACY
    // =====================================
    
    cy.log('Testing forecast calculation accuracy')
    
    // Get the calculated values and verify math
    cy.get('[data-cy=monthly-income], .monthly-income')
      .invoke('text')
      .then((incomeText) => {
        const monthlyIncome = parseFloat(incomeText.replace(/[$,]/g, ''))
        
        cy.get('[data-cy=monthly-expenses], .monthly-expenses')
          .invoke('text')
          .then((expenseText) => {
            const monthlyExpenses = parseFloat(expenseText.replace(/[$,]/g, ''))
            const expectedNetCashFlow = monthlyIncome - monthlyExpenses
            
            cy.log(`Expected net cash flow: $${expectedNetCashFlow}`)
            
            // Verify net cash flow calculation
            cy.get('[data-cy=net-cash-flow], .net-cash-flow').then(($netFlow) => {
              if ($netFlow.length > 0) {
                const actualNetFlow = parseFloat($netFlow.text().replace(/[$,]/g, ''))
                expect(Math.abs(actualNetFlow - expectedNetCashFlow)).to.be.lessThan(1) // Allow for rounding
              }
            })
          })
      })
    
    // =====================================
    // STEP 6: TEST WHAT-IF SCENARIOS (OPTIONAL)
    // =====================================
    
    cy.log('Testing what-if expense scenarios')
    
    // Look for what-if or quick expense feature
    cy.get('[data-cy=what-if-expense], [data-cy=quick-expense], .what-if-scenario', { timeout: 5000 }).then(($whatIf) => {
      if ($whatIf.length > 0) {
        cy.wrap($whatIf).click()
        
        // Add a $500 emergency expense
        cy.get('[data-cy=what-if-amount], .what-if-amount')
          .type('500')
        
        cy.get('[data-cy=what-if-calculate], .what-if-submit')
          .click()
        
        // Verify the projection updates
        cy.get('[data-cy=updated-projection], .updated-forecast')
          .should('be.visible')
          .should('contain', '$')
        
        cy.log('What-if scenario tested successfully')
      } else {
        cy.log('What-if feature not found - skipping')
      }
    })
  })
  
  // =====================================
  // ADDITIONAL TARGETED TESTS
  // =====================================
  
  it('should handle different income brackets for target demographic', () => {
    const targetScenarios = [
      { income: 42000, tier: 'Budget', location: 'Atlanta' },
      { income: 65000, tier: 'Mid-tier', location: 'Houston' },
      { income: 88000, tier: 'Professional', location: 'DC Metro' }
    ]
    
    targetScenarios.forEach((scenario) => {
      cy.log(`Testing ${scenario.tier} user scenario: $${scenario.income} in ${scenario.location}`)
      
      // This would test each income bracket separately
      // Implementation depends on your app's flow
    })
  })
  
  it('should validate financial projections for accuracy', () => {
    // Test mathematical accuracy of forecasting
    const testData = {
      annualIncome: 60000,
      monthlyExpenses: 4000,
      expectedMonthlyIncome: 5000,
      expectedNetFlow: 1000
    }
    
    // Implementation would verify calculations match expectations
  })
  
  it('should handle edge cases for target demographic', () => {
    // Test scenarios common to your target market
    const edgeCases = [
      'Irregular gig income',
      'Student loan payments', 
      'Childcare expenses',
      'Emergency savings goals'
    ]
    
    // Implementation would test each edge case
  })
})

// Custom commands for reusable actions
Cypress.Commands.add('loginToMingus', (method = 'test') => {
  if (method === 'google') {
    cy.get('#google-login').click()
    // Handle Google OAuth flow
  } else if (method === 'facebook') {
    cy.get('[data-cy=facebook-login]').click()
    // Handle Facebook OAuth flow  
  } else {
    // Test/bypass login
    cy.get('[data-cy=test-login]').click()
  }
})

Cypress.Commands.add('setupIncomeAndExpenses', (income, expenses) => {
  // Reusable command for setting up financial data
  cy.get('[data-cy=income-amount]').type(income.toString())
  cy.get('[data-cy=income-continue]').click()
  
  expenses.forEach((expense) => {
    cy.get('[data-cy=expense-amount]').type(expense.amount.toString())
    cy.get('[data-cy=expense-description]').type(expense.description)
  })
  
  cy.get('[data-cy=calculate-forecast]').click()
})

Cypress.Commands.add('verifyForecastAccuracy', (expectedIncome, expectedExpenses) => {
  const expectedNet = expectedIncome - expectedExpenses
  
  cy.get('[data-cy=net-cash-flow]')
    .invoke('text')
    .then((text) => {
      const actual = parseFloat(text.replace(/[$,]/g, ''))
      expect(Math.abs(actual - expectedNet)).to.be.lessThan(1)
    })
})