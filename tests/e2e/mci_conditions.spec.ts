/**
 * Mingus Conditions Index (MCI) Feature Tests
 *
 * Covers:
 *   MCI-01  Budget tier sees MCI strip in Daily Outlook
 *   MCI-02  Budget tier sees unlocked + locked constituents in expanded strip
 *   MCI-03  Mid-tier sees all 6 constituents unlocked (no upgrade locks)
 *   MCI-04  MCI panel appears in Financial Forecast tab (mid-tier)
 *   MCI-05  Budget tier sees locked MCI panel in Financial Forecast
 *   MCI-06  Strip collapse/expand toggle works
 */

import { test, expect, Browser, BrowserContext, Page, chromium } from '@playwright/test';

const BASE_URL = 'https://test.mingusapp.com';

const USERS = {
  budget: { email: 'maya.johnson.test@gmail.com', password: 'SecureTest123!', name: 'Maya', tier: 'budget' },
  mid: { email: 'marcus.thompson.test@gmail.com', password: 'SecureTest123!', name: 'Marcus', tier: 'mid' },
  professional: { email: 'jasmine.rodriguez.test@gmail.com', password: 'SecureTest123!', name: 'Jasmine', tier: 'professional' },
};

// Mock fixture returned from GET /api/mci/snapshot
const MCI_MOCK_SNAPSHOT = {
  composite_score: 62,
  composite_severity: 'amber',
  composite_direction: 'stable',
  composite_headline: 'Housing costs are rising in key metros',
  snapshot_date: '2026-03-15',
  next_refresh: '2026-03-22',
  constituents: [
    {
      name: 'labor_market_strength',
      slug: 'labor_market_strength',
      severity: 'green',
      headline: 'Labor market looks stable this month',
      source: 'BLS JOLTS',
      as_of: '2026-03-01',
      weight: 0.25,
      direction: 'flat',
      current_value: 1.0,
      previous_value: 1.0,
      raw: {},
    },
    {
      name: 'housing_affordability_pressure',
      slug: 'housing_affordability_pressure',
      severity: 'amber',
      headline: 'Mortgage affordability is under pressure',
      source: 'Freddie Mac PMMS',
      as_of: '2026-03-01',
      weight: 0.25,
      direction: 'flat',
      current_value: 1.0,
      previous_value: 1.0,
      raw: {},
    },
    {
      name: 'transportation_cost_burden',
      slug: 'transportation_cost_burden',
      severity: 'green',
      headline: 'Gas prices are steady for commuters',
      source: 'EIA gas prices',
      as_of: '2026-03-01',
      weight: 0.1,
      direction: 'flat',
      current_value: 1.0,
      previous_value: 1.0,
      raw: {},
    },
    {
      name: 'consumer_debt_conditions',
      slug: 'consumer_debt_conditions',
      severity: 'amber',
      headline: 'Credit card APRs remain elevated',
      source: 'Federal Reserve G.19',
      as_of: '2026-03-01',
      weight: 0.2,
      direction: 'flat',
      current_value: 1.0,
      previous_value: 1.0,
      raw: {},
    },
    {
      name: 'career_income_mobility',
      slug: 'career_income_mobility',
      severity: 'green',
      headline: 'Workers report stable quit-rate conditions',
      source: 'BLS JOLTS quit rate',
      as_of: '2026-03-01',
      weight: 0.15,
      direction: 'flat',
      current_value: 1.0,
      previous_value: 1.0,
      raw: {},
    },
    {
      name: 'wellness_cost_index',
      slug: 'wellness_cost_index',
      severity: 'amber',
      headline: 'Healthcare costs are steady in mid-income budgets',
      source: 'BLS CEX benchmarks',
      as_of: '2023-12-31',
      weight: 0.05,
      direction: 'flat',
      current_value: 1.0,
      previous_value: 1.0,
      raw: {},
    },
  ],
};

// ── Mock data for dashboard endpoints ─────────────────────────────────────────
const todayStr = new Date().toISOString().slice(0, 10);
const formattedTime = new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });

function makeDailyOutlook(userName: string, userTier: string) {
  return {
    user_name: userName,
    current_time: formattedTime,
    user_tier: userTier,
    // Some deployed frontend variants embed MCI data into the daily-outlook payload
    // instead of fetching `/api/mci/snapshot` directly.
    mci: MCI_MOCK_SNAPSHOT,
    mci_snapshot: MCI_MOCK_SNAPSHOT,
    mciData: MCI_MOCK_SNAPSHOT,
    mci_enabled: true,
    mciEnabled: true,
    has_mci: true,
    hasMci: true,
    show_mci: true,
    showMci: true,
    conditions_index_enabled: true,
    show_conditions_index: true,
    balance_score: {
      value: 71,
      trend: 'stable',
      change_percentage: 0,
      previous_value: 71,
    },
    primary_insight: {
      title: 'Today’s Focus',
      message: 'Focus on building financial resilience today.',
      type: 'positive',
      icon: 'sun',
    },
    quick_actions: [],
    encouragement_message: {
      text: 'Keep going — you are making progress.',
      type: 'reminder',
      emoji: '💡',
    },
    streak_data: {
      current_streak: 3,
      longest_streak: 5,
      milestone_reached: false,
      next_milestone: 5,
      progress_percentage: 60,
    },
    tomorrow_teaser: {
      title: 'Tomorrow',
      description: 'Focus on career development and financial momentum.',
      excitement_level: 7,
    },
  };
}

const CASHFLOW_FORECAST = {
  daily_cashflow: [
    {
      date: todayStr,
      opening_balance: 3400,
      closing_balance: 3450,
      net_change: 50,
      balance_status: 'healthy',
    },
  ],
  monthly_summaries: [],
  vehicle_expense_totals: { total: 0, routine: 0, repair: 0 },
};

// ── Helpers ──────────────────────────────────────────────────────────────────
let browser: Browser;
let context: BrowserContext;
let page: Page;

async function addDashboardMocks(p: Page, user: (typeof USERS)[keyof typeof USERS]) {
  const email = user.email;
  const firstName = user.name;
  const tierForVerify = user.tier === 'mid' ? 'mid_tier' : user.tier;

  await p.route('**/api/auth/verify**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        authenticated: true,
        user_id: `${email}-id`,
        email,
        name: firstName,
        tier: tierForVerify,
      }),
    });
  });

  await p.route('**/api/risk/dashboard-state**', async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ current_risk_level: 'watchful', recommendations_unlocked: true }),
    });
  });

  // Daily outlook drives DailyOutlookCard rendering (including embedded MCI strip).
  await p.route('**/api/daily-outlook**', async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(makeDailyOutlook(firstName, tierForVerify === 'mid_tier' ? 'mid_tier' : tierForVerify)),
    });
  });

  await p.route('**/api/cash-flow/enhanced-forecast/**', async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, forecast: CASHFLOW_FORECAST }),
    });
  });

  await p.route('**/api/cash-flow/backward-compatibility/**', async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, forecast: CASHFLOW_FORECAST }),
    });
  });

  await p.route('**/api/profile/setup-status**', async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        setup_complete: true,
        setupCompleted: true,
        steps_completed: ['profile', 'assessment', 'payment'],
        tier: tierForVerify,
        email,
        firstName,
        user_id: `${email}-id`,
      }),
    });
  });

  // Prevent tracking calls from producing test noise.
  await p.route('**/api/analytics/user-behavior/track-interaction', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{"success":true}' });
  });

  await p.route('**/api/wellness/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
  });

  await p.route('**/api/notifications**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ notifications: [], unread_count: 0 }),
    });
  });
}

async function dismissModal(p: Page) {
  await p.waitForTimeout(1000);

  const overlay = p.locator('.fixed.inset-0').first();
  try {
    await overlay.waitFor({ state: 'visible', timeout: 5000 });
  } catch {
    return;
  }

  const dismissSelectors = [
    'button:has-text("I\'ll do this later")',
    '[aria-label="Close and skip setup"]',
    'button:has-text("Continue to Dashboard")',
    'button:has-text("Close")',
    'button:has-text("Dismiss")',
    'button:has-text("Got it")',
    'button:has-text("Skip")',
    'button:has-text("Not now")',
    'button:has-text("Maybe later")',
    '[aria-label="Close"]',
    '[aria-label="Dismiss"]',
    '.modal button',
    '[role="dialog"] button',
  ];

  for (const selector of dismissSelectors) {
    const btn = p.locator(selector).first();
    const visible = await btn.isVisible().catch(() => false);
    if (visible) {
      await btn.click().catch(() => {});
      await p.waitForTimeout(500);
      break;
    }
  }

  const overlayStillVisible = await overlay.isVisible().catch(() => false);
  if (overlayStillVisible) {
    await p.keyboard.press('Escape');
    await p.waitForTimeout(500);
  }
}

async function navigateToTab(p: Page, tabName: string) {
  await dismissModal(p);
  const btn = p.getByRole('button', { name: new RegExp(tabName, 'i') }).first();
  await btn.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
  await btn.click({ force: true }).catch(() => {});
  // Wait for tab-specific content to be present; avoids asserting on the wrong tab.
  if (/daily outlook/i.test(tabName)) {
    await expect(p.getByText(/View all milestones/i).first()).toBeVisible({ timeout: 15000 }).catch(() => {});
  }
  if (/financial forecast/i.test(tabName)) {
    await expect(
      p.getByRole('heading', { name: /Market conditions affecting your forecast/i })
    ).toBeVisible({ timeout: 15000 }).catch(() => {});
  }
  await p.waitForTimeout(1500);
}

async function loginAndGoToDashboard(p: Page, ctx: BrowserContext, user: (typeof USERS)[keyof typeof USERS]) {
  await ctx.clearCookies();
  await p.goto(`${BASE_URL}/login`);
  await p.waitForLoadState('domcontentloaded');

  try {
    await p.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  } catch {
    // ignore
  }

  await addDashboardMocks(p, user);

  await p.route('**/api/auth/login', async (route) => {
    if (route.request().method() !== 'POST') return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        user_id: `${user.email}-id`,
        email: user.email,
        name: user.name,
        message: 'Login successful',
        tier: user.tier === 'mid' ? 'mid_tier' : user.tier,
      }),
    });
  });

  await p.waitForTimeout(500);
  await p.getByLabel(/email/i).first().fill(user.email);
  await p.getByLabel(/password/i).first().fill(user.password);

  const loginResponse = p.waitForResponse(
    (r) => r.url().includes('/api/auth/login') && r.request().method() === 'POST',
    { timeout: 15000 }
  );

  await p.getByRole('button', { name: /sign in|log in|login/i }).first().click();
  try {
    const resp = await loginResponse;
    if (!resp.ok()) {
      return;
    }
  } catch {
    // proceed
  }

  await p.waitForLoadState('domcontentloaded');
  await p.waitForTimeout(1000);

  for (let i = 0; i < 3; i++) {
    try {
      await p.evaluate(() => {
        localStorage.setItem('auth_token', 'ok');
        localStorage.setItem('mingus_token', 'e2e-dashboard-token');
      });
      break;
    } catch {
      await p.waitForTimeout(500);
    }
  }

  if (!p.url().includes('/dashboard')) {
    await p.goto(`${BASE_URL}/dashboard`);
    await p.waitForLoadState('domcontentloaded');
    await p.waitForTimeout(2000);
  }

  if (p.url().includes('vibe-check-meme')) {
    await p.goto(`${BASE_URL}/dashboard`);
    await p.waitForLoadState('domcontentloaded');
    await p.waitForTimeout(2000);
  }

  try {
    await p.evaluate(() => {
      localStorage.setItem('auth_token', 'ok');
      localStorage.setItem('mingus_token', 'e2e-dashboard-token');
    });
  } catch {
    // ignore
  }

  await dismissModal(p);
}

// ── Test Suite ────────────────────────────────────────────────────────────────
// Two serial groups so a Budget failure does not skip all Mid-tier MCI tests (and vice versa).
test.describe.serial('MCI Conditions Index — Budget tier', () => {
  test.setTimeout(180000);

  test.afterEach(async () => {
    try {
      await browser?.close();
    } catch {
      // ignore
    }
  });

  test.describe('Budget tier (maya)', () => {
    // Mock the MCI snapshot so the strip renders deterministically.
    let mciSnapshotHits = 0;
    let apiUrls: string[] = [];
    let mciLikeUrls: string[] = [];

    test.beforeEach(async () => {
      browser = await chromium.launch({ headless: process.env.PLAYWRIGHT_HEADED !== '1' });
      context = await browser.newContext({ storageState: '.auth/marcus.json' });
      page = await context.newPage();

      mciSnapshotHits = 0;
      apiUrls = [];
      mciLikeUrls = [];
      page.on('request', (req) => {
        const url = req.url();
        if (!url.includes('/api/')) return;
        if (apiUrls.includes(url)) return;
        apiUrls.push(url);
      });
      page.on('request', (req) => {
        const url = req.url();
        const l = url.toLowerCase();
        if (!l.includes('mci') && !l.includes('condition')) return;
        if (mciLikeUrls.includes(url)) return;
        mciLikeUrls.push(url);
      });
      await page.route('**/api/mci/snapshot*', async (route) => {
        if (route.request().method() !== 'GET') return route.fallback();
        mciSnapshotHits += 1;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(MCI_MOCK_SNAPSHOT),
        });
      });

      await loginAndGoToDashboard(page, context, USERS.budget);
    });

    test('MCI-01: Budget tier sees MCI strip in Daily Outlook', async () => {
      await navigateToTab(page, 'Daily Outlook');

      await expect(page.getByText(/Today’s Focus/i)).toBeVisible({ timeout: 15000 });

      await page.waitForTimeout(10000);

      const collapsedStrip = page.getByRole('button', { name: /View conditions/i }).first();

      await expect(collapsedStrip).toBeVisible({ timeout: 15000 });
      await expect(collapsedStrip.getByText(/62/).first()).toBeVisible({ timeout: 15000 });
      await expect(collapsedStrip.locator('text=Housing costs are rising in key metros').first()).toBeVisible();
      await expect(collapsedStrip.locator('text=View conditions').first()).toBeVisible();
    });

    test('MCI-02: Budget tier sees 2 unlocked + 4 locked constituents', async () => {
      await navigateToTab(page, 'Daily Outlook');

      const collapsedStrip = page.getByRole('button', { name: /View conditions/i }).first();
      await collapsedStrip.click();

      const expandedStrip = page.getByRole('button', { name: /Hide conditions/i }).first();
      await expect(expandedStrip).toBeVisible({ timeout: 15000 });

      await expect(expandedStrip.locator('text=labor_market_strength').first()).toBeVisible();
      await expect(expandedStrip.locator('text=housing_affordability_pressure').first()).toBeVisible();
      await expect(expandedStrip.locator('text=Upgrade to Mid-tier').first()).toBeVisible();
    });

    test('MCI-05: Budget tier sees locked MCI panel in Financial Forecast', async () => {
      await navigateToTab(page, 'Financial Forecast');

      await expect(
        page.getByText(
          'Upgrade to Mid-tier to see how market conditions affect your forecast'
        )
      ).toBeVisible();
      await expect(page.getByText('Market conditions affecting your forecast')).toHaveCount(0);
    });
  });
});

test.describe.serial('MCI Conditions Index — Mid tier', () => {
  test.setTimeout(180000);

  test.afterEach(async () => {
    try {
      await browser?.close();
    } catch {
      // ignore
    }
  });

  test.describe('Mid tier (marcus)', () => {
    test.beforeEach(async () => {
      browser = await chromium.launch({ headless: process.env.PLAYWRIGHT_HEADED !== '1' });
      context = await browser.newContext({ storageState: '.auth/marcus.json' });
      page = await context.newPage();

      await page.route('**/api/mci/snapshot*', async (route) => {
        if (route.request().method() !== 'GET') return route.fallback();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(MCI_MOCK_SNAPSHOT),
        });
      });

      await loginAndGoToDashboard(page, context, USERS.mid);
    });

    test('MCI-03: Mid-tier sees all 6 constituents unlocked', async () => {
      await navigateToTab(page, 'Daily Outlook');

      const collapsedStrip = page.getByRole('button', { name: /View conditions/i }).first();
      await collapsedStrip.click();

      const expandedStrip = page.getByRole('button', { name: /Hide conditions/i }).first();
      await expect(expandedStrip).toBeVisible({ timeout: 15000 });

      for (const c of MCI_MOCK_SNAPSHOT.constituents) {
        await expect(expandedStrip.locator(`text=${c.name}`).first()).toBeVisible();
      }
      await expect(expandedStrip.locator('text=Upgrade to Mid-tier')).toHaveCount(0);
    });

    test('MCI-04: MCI panel appears in Financial Forecast tab (mid-tier)', async () => {
      await navigateToTab(page, 'Financial Forecast');

      await expect(page.getByRole('heading', { name: 'Market conditions affecting your forecast' })).toBeVisible();

      await expect(
        page.getByText('Job market is strong — your income projection is stable.')
      ).toBeVisible();
      await expect(
        page.getByText('Rates are elevated — re-run your affordability calculator.')
      ).toBeVisible();
    });

    test('MCI-06: MCI strip collapse/expand toggle works', async () => {
      await navigateToTab(page, 'Daily Outlook');

      const collapsedStrip = page.getByRole('button', { name: /View conditions/i }).first();
      await expect(collapsedStrip).toBeVisible({ timeout: 15000 });

      const laborCollapsed = collapsedStrip.locator('text=labor_market_strength').first();
      await expect(laborCollapsed).toBeHidden();

      await collapsedStrip.click(); // expands the strip
      const expandedStrip = page.getByRole('button', { name: /Hide conditions/i }).first();
      await expect(expandedStrip).toBeVisible({ timeout: 15000 });

      const laborExpanded = expandedStrip.locator('text=labor_market_strength').first();
      await expect(laborExpanded).toBeVisible();

      await expandedStrip.click(); // collapses the strip
      const collapsedStripAgain = page.getByRole('button', { name: /View conditions/i }).first();
      const laborCollapsedAgain = collapsedStripAgain.locator('text=labor_market_strength').first();
      await expect(laborCollapsedAgain).toBeHidden();
    });
  });
});

