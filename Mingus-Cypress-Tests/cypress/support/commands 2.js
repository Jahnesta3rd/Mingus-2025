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

// Authentication Commands
Cypress.Commands.add('loginUser', (email = 'test@example.com', password = 'testpassword123!') => {
  // Option 1: Login via API
  cy.request({
    method: 'POST',
    url: 'http://127.0.0.1:5002/api/auth/login',
    body: {
      email: email,
      password: password
    },
    failOnStatusCode: false
  }).then((response) => {
    if (response.status === 200) {
      // Store auth token if provided
      if (response.body.token) {
        window.localStorage.setItem('authToken', response.body.token);
      }
      // Set session cookie for Flask session auth
      if (response.headers['set-cookie']) {
        cy.setCookie('session', response.headers['set-cookie'][0]);
      }
      cy.log('User logged in successfully via API');
    } else {
      cy.log(`Login failed with status: ${response.status}`);
    }
  });
});

Cypress.Commands.add('loginUserUI', (email = 'test@example.com', password = 'testpassword123!') => {
  // Option 2: Login via UI (slower but more realistic)
  cy.visit('http://127.0.0.1:5002/api/auth/login');
  cy.get('input[name="email"], input[type="email"], [data-cy="email"]').type(email);
  cy.get('input[name="password"], input[type="password"], [data-cy="password"]').type(password);
  cy.get('button[type="submit"], input[type="submit"], [data-cy="login-button"]').click();
  cy.url().should('not.include', '/login');
  cy.log('User logged in successfully via UI');
});

Cypress.Commands.add('registerUser', (email = `test${Date.now()}@example.com`, password = 'testpassword123!', fullName = 'Test User') => {
  // Register a new user via API
  cy.request({
    method: 'POST',
    url: 'http://127.0.0.1:5002/api/auth/register',
    body: {
      email: email,
      password: password,
      full_name: fullName,
      phone_number: '555-123-4567'
    },
    failOnStatusCode: false
  }).then((response) => {
    if (response.status === 200 || response.status === 201) {
      cy.log('User registered successfully');
      // Store credentials for later use
      const credentials = { email, password, fullName };
      cy.wrap(credentials).as('userCredentials');
    } else {
      cy.log(`Registration failed with status: ${response.status}`);
      // Still create credentials object for testing
      const credentials = { email, password, fullName };
      cy.wrap(credentials).as('userCredentials');
    }
  });
});

Cypress.Commands.add('logoutUser', () => {
  // Logout user
  cy.request({
    method: 'POST',
    url: 'http://127.0.0.1:5002/api/auth/logout',
    failOnStatusCode: false
  }).then(() => {
    // Clear local storage and cookies
    cy.clearLocalStorage();
    cy.clearCookies();
    cy.log('User logged out successfully');
  });
});

Cypress.Commands.add('ensureAuthenticated', () => {
  // Ensure user is authenticated, login if not
  cy.request({
    method: 'GET',
    url: 'http://127.0.0.1:5002/api/auth/check-auth',
    failOnStatusCode: false
  }).then((response) => {
    if (response.status !== 200 || !response.body.authenticated) {
      cy.log('User not authenticated, logging in...');
      cy.loginUser();
    } else {
      cy.log('User already authenticated');
    }
  });
});

// Health-specific commands
Cypress.Commands.add('completeHealthCheckin', (data = {}) => {
  const defaultData = {
    stress_level: 5,
    physical_activity_minutes: 30,
    relationships_rating: 7,
    mindfulness_minutes: 10
  };
  
  const checkinData = { ...defaultData, ...data };
  
  cy.request({
    method: 'POST',
    url: 'http://127.0.0.1:5002/api/health/checkin',
    body: checkinData,
    failOnStatusCode: false
  }).then((response) => {
    if (response.status === 201) {
      cy.log('Health check-in completed successfully');
    } else {
      cy.log(`Health check-in failed with status: ${response.status}`);
    }
  });
});

Cypress.Commands.add('getHealthSummary', () => {
  cy.request({
    method: 'GET',
    url: 'http://127.0.0.1:5002/api/health/summary',
    failOnStatusCode: false
  }).then((response) => {
    if (response.status === 200) {
      cy.log('Health summary retrieved successfully');
      cy.wrap(response.body).as('healthSummary');
    } else {
      cy.log(`Health summary failed with status: ${response.status}`);
    }
  });
});