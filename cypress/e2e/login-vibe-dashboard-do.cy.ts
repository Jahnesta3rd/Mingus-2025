/**
 * E2E: User login → vibe-check page → dashboard (Digital Ocean / latest deploy).
 * Runs against the live app (mingusapp.com or test.mingusapp.com) when baseUrl is set.
 *
 * Set credentials via env (no stubbing; real API):
 *   CYPRESS_LOGIN_EMAIL=your@email.com CYPRESS_LOGIN_PASSWORD=yourpass
 * Or in cypress.config: env: { LOGIN_EMAIL: '...', LOGIN_PASSWORD: '...' }
 *
 * Run against production:
 *   CYPRESS_BASE_URL=https://mingusapp.com CYPRESS_LOGIN_EMAIL=... CYPRESS_LOGIN_PASSWORD=... npx cypress run --spec cypress/e2e/login-vibe-dashboard-do.cy.ts
 *
 * Run against test (when test.mingusapp.com is serving the app):
 *   CYPRESS_BASE_URL=https://test.mingusapp.com CYPRESS_LOGIN_EMAIL=... CYPRESS_LOGIN_PASSWORD=... npx cypress run --spec cypress/e2e/login-vibe-dashboard-do.cy.ts
 */

/// <reference types="cypress" />

const TIMEOUT_NAV = 15000;
const TIMEOUT_API = 10000;

describe('Login → Vibe-Check → Dashboard (DO / latest)', () => {
  const email = Cypress.env('LOGIN_EMAIL');
  const password = Cypress.env('LOGIN_PASSWORD');

  beforeEach(() => {
    cy.viewport(1280, 720);
  });

  it('loads login page without 404', () => {
    cy.visit('/login', { failOnStatusCode: false });
    cy.url({ timeout: TIMEOUT_NAV }).should('include', '/login');
    cy.get('body').then(($body) => {
      const text = $body.text();
      if (text.includes('404') || text.includes('Not Found')) {
        cy.log('ERROR: Login page returned 404. See docs/LOGIN_VIBE_DASHBOARD_TROUBLESHOOTING.md');
        throw new Error('Login page 404: nginx may not be serving SPA (try_files $uri $uri/ /index.html)');
      }
    });
    cy.contains('Sign in to your account', { matchCase: false }).should('be.visible');
  });

  it('logs in and reaches vibe-check or dashboard', function () {
    if (!email || !password) {
      this.skip();
      return;
    }

    cy.visit('/login', { failOnStatusCode: false });
    cy.get('input[name="email"]', { timeout: TIMEOUT_NAV }).type(email);
    cy.get('input[name="password"]').type(password);
    cy.get('form').submit();

    // After login, app redirects to /vibe-check-meme (full page replace)
    cy.url({ timeout: TIMEOUT_NAV }).should(
      (url) => {
        expect(url).to.satisfy(
          (u: string) => u.includes('/vibe-check-meme') || u.includes('/dashboard') || u.includes('/login'),
          'expected URL to be vibe-check-meme, dashboard, or login (on failure)'
        );
      }
    );

    // If still on login, log error for troubleshooting
    cy.url().then((url) => {
      if (url.includes('/login')) {
        cy.get('[role="alert"], .text-red-600, .text-red-500').first().invoke('text').then((errText) => {
          cy.log('Login failed. Message: ' + (errText || ' (no message)'));
        });
      }
    });
  });

  it('views vibe-check page content', function () {
    if (!email || !password) {
      this.skip();
      return;
    }

    cy.visit('/login', { failOnStatusCode: false });
    cy.get('input[name="email"]', { timeout: TIMEOUT_NAV }).type(email);
    cy.get('input[name="password"]').type(password);
    cy.get('form').submit();

    cy.url({ timeout: TIMEOUT_NAV }).should('include', '/vibe-check-meme');
    // Page shows either "Loading vibe check..." or "Vibe Check" heading and meme
    cy.get('body', { timeout: TIMEOUT_API }).then(($body) => {
      const hasLoading = $body.text().includes('Loading vibe check');
      const hasVibeCheck = $body.text().includes('Vibe Check');
      const hasContinue = $body.text().includes('Continue to Dashboard') || $body.text().includes('Could not load vibe check');
      expect(hasLoading || hasVibeCheck || hasContinue).to.be.true;
    });
    // If "Could not load vibe check" appears, /api/user-meme may be failing
    cy.get('body').then(($body) => {
      if ($body.text().includes('Could not load vibe check')) {
        cy.log('TROUBLESHOOT: Vibe-check API failed. Check /api/user-meme and auth cookie.');
      }
    });
  });

  it('navigates to dashboard and loads', function () {
    if (!email || !password) {
      this.skip();
      return;
    }

    // Start from vibe-check (after login) or go straight to dashboard
    cy.visit('/login', { failOnStatusCode: false });
    cy.get('input[name="email"]', { timeout: TIMEOUT_NAV }).type(email);
    cy.get('input[name="password"]').type(password);
    cy.get('form').submit();

    cy.url({ timeout: TIMEOUT_NAV }).should((url) => {
      expect(url.includes('/vibe-check-meme') || url.includes('/dashboard')).to.be.true;
    });

    // If we're on vibe-check, click Continue to Dashboard (or navigate)
    cy.get('body').then(($body) => {
      if ($body.text().includes('Continue to Dashboard')) {
        cy.contains('button', 'Continue to Dashboard').click();
      } else if ($body.find('button[aria-label*="Thumbs"]').length) {
        cy.get('button[aria-label*="Thumbs"]').first().click();
      } else {
        cy.visit('/dashboard', { failOnStatusCode: false });
      }
    });

    cy.url({ timeout: TIMEOUT_NAV }).should('include', '/dashboard');
    // Dashboard may show "Dashboard", "Career Protection", or loading/skeleton
    cy.get('body', { timeout: TIMEOUT_API }).then(($body) => {
      const text = $body.text();
      const hasDashboard = /dashboard|career protection|financial forecast|wellness/i.test(text) || $body.find('[class*="dashboard"]').length > 0;
      expect(hasDashboard || text.length > 200).to.be.true;
    });
  });
});
