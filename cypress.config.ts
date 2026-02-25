import { defineConfig } from 'cypress';

export default defineConfig({
  env: {
    LOGIN_EMAIL: process.env.CYPRESS_LOGIN_EMAIL,
    LOGIN_PASSWORD: process.env.CYPRESS_LOGIN_PASSWORD,
  },
  e2e: {
    baseUrl: process.env.CYPRESS_BASE_URL || 'http://localhost:5173',
    specPattern: 'cypress/e2e/**/*.cy.{js,ts}',
    supportFile: 'cypress/support/e2e.ts',
    fixturesFolder: 'cypress/fixtures',
    video: false,
    viewportWidth: 1280,
    viewportHeight: 720,
  },
});
