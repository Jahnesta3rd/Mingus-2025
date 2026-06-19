/**
 * E2E: Quick Spend Logger — FAB, bottom sheet, save flow, today log, #155 regression.
 * All API calls mocked via cy.intercept (no live database).
 */

/// <reference types="cypress" />

const TODAY = new Date().toISOString().slice(0, 10);

const MOCK_ENTRY = {
  id: 999,
  date: TODAY,
  amount: 6.75,
  spend_vibe: "on_the_go_eats",
  vibe_signal: "convenience_food",
  merchant_name: "Starbucks",
  merchant_group: "Coffee & Quick Bites",
  merchant_id: "starbucks",
  logged_at: new Date().toISOString(),
};

const MOCK_TODAY_EMPTY = {
  date: TODAY,
  entries: [],
  total: 0,
  count: 0,
};

const MOCK_TODAY_WITH_ENTRY = {
  date: TODAY,
  entries: [MOCK_ENTRY],
  total: 6.75,
  count: 1,
};

const MOCK_SUMMARY = {
  period_days: 30,
  start_date: TODAY,
  end_date: TODAY,
  total: 6.75,
  by_signal: { convenience_food: 6.75 },
  by_vibe: { on_the_go_eats: 6.75 },
};

const MOCK_EXPENSES_SUMMARY = {
  income_monthly: 2483.0,
  categories: [
    { name: "utilities", amount: 75.0 },
    { name: "Coffee & Quick Bites", amount: 6.75 },
  ],
};

const TEST_USER = {
  email: "test@mingus.com",
  password: "password123",
};

const MOCK_AUTH = {
  authenticated: true,
  user_id: "cypress-quick-spend-user",
  email: TEST_USER.email,
  name: "Cypress User",
  tier: "budget",
  token: "cypress-mock-jwt",
};

/** Matches weekly-checkin.cy.ts login + auth intercept pattern. */
function loginTestUser() {
  cy.intercept("GET", "/api/auth/verify", {
    statusCode: 200,
    body: MOCK_AUTH,
  }).as("authVerify");
  cy.intercept("POST", "/api/auth/login", {
    statusCode: 200,
    body: MOCK_AUTH,
  }).as("authLogin");
  cy.intercept("GET", "/api/auth/session-ready", {
    statusCode: 200,
    body: { ready: true },
  });
  cy.visit("/login");
  cy.get('input[name="email"]').type(TEST_USER.email);
  cy.get('input[name="password"]').type(TEST_USER.password);
  cy.get("form").submit();
  cy.url({ timeout: 15000 }).should("include", "/dashboard");
}

describe("Quick Spend Logger", () => {
  beforeEach(() => {
    cy.viewport(1280, 720);
    loginTestUser();

    cy.intercept("GET", "/api/expenses/quick-log/today", MOCK_TODAY_EMPTY).as(
      "getToday"
    );

    cy.intercept("POST", "/api/expenses/quick-log", {
      statusCode: 201,
      body: MOCK_ENTRY,
    }).as("postLog");

    cy.intercept("GET", "/api/expenses/quick-log/summary*", MOCK_SUMMARY).as(
      "getSummary"
    );

    cy.intercept("GET", "/api/expenses/summary/*", MOCK_EXPENSES_SUMMARY).as(
      "getExpensesSummary"
    );

    cy.visit("/dashboard");
    cy.wait("@getToday");
  });

  it("renders the Quick Spend FAB on the Today tab", () => {
    cy.get("[aria-label='Log a purchase']")
      .should("be.visible")
      .should("have.css", "position", "fixed");
  });

  it("opens the bottom sheet when FAB is tapped", () => {
    cy.get("[aria-label='Log a purchase']").click();
    cy.contains("Log a purchase").should("be.visible");
    cy.contains("How much?").should("be.visible");
  });

  it("closes the sheet when backdrop is tapped", () => {
    cy.get("[aria-label='Log a purchase']").click();
    cy.get("[data-testid='quick-spend-backdrop']").click({ force: true });
    cy.contains("Log a purchase").should("not.exist");
  });

  it("keeps Save disabled until amount and vibe are selected", () => {
    cy.get("[aria-label='Log a purchase']").click();
    cy.get("[data-testid='quick-spend-save']").should("be.disabled");

    cy.get("input[type='number']").type("6.75");
    cy.get("[data-testid='quick-spend-save']").should("be.disabled");

    cy.contains("On-the-go eats").click();
    cy.get("[data-testid='quick-spend-save']").should("not.be.disabled");
  });

  it("logs a spend entry and updates the today log", () => {
    cy.intercept("GET", "/api/expenses/quick-log/today", {
      body: MOCK_TODAY_WITH_ENTRY,
    }).as("getTodayAfterSave");

    cy.get("[aria-label='Log a purchase']").click();
    cy.get("input[type='number']").type("6.75");
    cy.contains("On-the-go eats").click();
    cy.contains("Starbucks").click();
    cy.get("[data-testid='quick-spend-save']").click();

    cy.wait("@postLog")
      .its("request.body")
      .should("deep.include", {
        amount: 6.75,
        spend_vibe: "on_the_go_eats",
        vibe_signal: "convenience_food",
      });

    cy.contains("Logged").should("be.visible");

    cy.contains("Log a purchase", { timeout: 3000 }).should("not.exist");
  });

  it("rejects amount of 0", () => {
    cy.get("[aria-label='Log a purchase']").click();
    cy.get("input[type='number']").type("0");
    cy.contains("On-the-go eats").click();
    cy.get("[data-testid='quick-spend-save']").should("be.disabled");
  });

  it("displays today log entries returned from the API", () => {
    cy.intercept("GET", "/api/expenses/quick-log/today", {
      body: MOCK_TODAY_WITH_ENTRY,
    }).as("getTodayPopulated");
    cy.reload();
    cy.wait("@getTodayPopulated");

    cy.contains("Starbucks").should("be.visible");
    cy.contains("$6.75").should("be.visible");
  });

  describe("Tracker #155 regression — Snapshot spending card", () => {
    it("calls /api/expenses/summary not a ghost URL", () => {
      cy.visit("/snapshot");
      cy.wait("@getExpensesSummary")
        .its("response.statusCode")
        .should("eq", 200);
    });

    it("spending card renders category data not empty state", () => {
      cy.visit("/snapshot");
      cy.wait("@getExpensesSummary");
      cy.contains("utilities").should("be.visible");
    });
  });
});
