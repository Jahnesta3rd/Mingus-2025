const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5002',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: false,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000,
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    env: {
      // Test environment variables
      apiUrl: 'http://localhost:5002/api',
      testUser: {
        email: 'test@example.com',
        password: 'TestPassword123!',
        firstName: 'John',
        lastName: 'Doe'
      },
      testCompany: {
        name: 'TechCorp',
        industry: 'technology',
        location: 'San Francisco, CA'
      }
    },
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/e2e.js',
    fixturesFolder: 'cypress/fixtures',
    screenshotsFolder: 'cypress/screenshots',
    videosFolder: 'cypress/videos',
    downloadsFolder: 'cypress/downloads'
  },
  
  component: {
    devServer: {
      framework: 'react',
      bundler: 'vite'
    },
    specPattern: 'cypress/component/**/*.cy.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/component.js'
  },
  
  retries: {
    runMode: 2,
    openMode: 0
  },
  
  watchForFileChanges: false,
  
  // Performance testing configuration
  performance: {
    enabled: true,
    thresholds: {
      pageLoadTime: 3000,
      apiResponseTime: 1000,
      renderTime: 500
    }
  }
})
