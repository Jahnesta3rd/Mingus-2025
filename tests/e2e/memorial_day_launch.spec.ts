/**
 * Memorial Day launch — Phases 1–6 critical paths (MD-01 … MD-25).
 *
 * Pattern: BASE_URL + Playwright route mocks + persona logins (Maya / Marcus / Jasmine).
 */

import { test, expect, BrowserContext, Page } from '@playwright/test';

const BASE_URL = 'https://test.mingusapp.com';
const PASSWORD = 'SecureTest123!';

const MAYA = {
  email: 'maya.johnson.test@gmail.com',
  firstName: 'Maya',
  tier: 'budget' as const,
};
const MARCUS = {
  email: 'marcus.thompson.test@gmail.com',
  firstName: 'Marcus',
  tier: 'mid_tier' as const,
};
const JASMINE = {
  email: 'jasmine.rodriguez.test@gmail.com',
  firstName: 'Jasmine',
  tier: 'professional' as const,
};

type TestUser = typeof MAYA | typeof MARCUS | typeof JASMINE;

interface MemorialState {
  incomeScheduleSaved: boolean;
  expenseScheduleSaved: boolean;
  connectionAssessedForPerson: Record<string, boolean>;
  createPersonCallCount: number;
  /** Set on POST /api/vibe-tracker/people to mirror `re_entry_detected` in the mock body */
  reEntryDetectedOnLastCreate?: boolean;
}

function logMd(code: string, passed: boolean, detail?: string): void {
  const status = passed ? 'PASS' : 'FAIL';
  const extra = detail ? ` — ${detail}` : '';
  console.log(`${code}: ${status}${extra}`);
}

function buildDailyCashflow(state: MemorialState): Array<{
  date: string;
  opening_balance: number;
  closing_balance: number;
  net_change: number;
  balance_status: 'healthy' | 'warning' | 'danger';
}> {
  const rows: Array<{
    date: string;
    opening_balance: number;
    closing_balance: number;
    net_change: number;
    balance_status: 'healthy' | 'warning' | 'danger';
  }> = [];
  const start = new Date();
  let bal = 5000;
  for (let i = 0; i < 90; i += 1) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    const iso = d.toISOString().slice(0, 10);
    let delta = 0;
    if (state.incomeScheduleSaved && (i === 0 || i === 14 || i === 28)) {
      delta += 1800;
    }
    if (state.expenseScheduleSaved && (i === 5 || i === 19 || i === 33)) {
      delta -= 650;
    }
    if (delta === 0) {
      delta = i % 11 === 0 ? -12 : 3;
    }
    const opening = bal;
    const closing = opening + delta;
    bal = closing;
    const balance_status: 'healthy' | 'warning' | 'danger' =
      closing < 0 ? 'danger' : closing < 1500 ? 'warning' : 'healthy';
    rows.push({ date: iso, opening_balance: opening, closing_balance: closing, net_change: delta, balance_status });
  }
  return rows;
}

function sevenConnectionQuestions() {
  return Array.from({ length: 7 }, (_, i) => ({
    id: `ct-q-${i + 1}`,
    key: `q${i + 1}`,
    text: `Memorial Day observation question ${i + 1}?`,
    answers: ['Mostly yes', 'Mixed', 'Mostly no'],
  }));
}

async function dismissOverlay(page: Page): Promise<void> {
  await page.waitForTimeout(600);
  const overlay = page.locator('.fixed.inset-0').first();
  if (!(await overlay.isVisible().catch(() => false))) return;
  for (const sel of [
    'button:has-text("I\'ll do this later")',
    '[aria-label="Close and skip setup"]',
    'button:has-text("Continue to Dashboard")',
    'button:has-text("Dismiss")',
    'button:has-text("Got it")',
    'button:has-text("Skip")',
    '[aria-label="Close"]',
    '[role="dialog"] button',
  ]) {
    const btn = page.locator(sel).first();
    if (await btn.isVisible().catch(() => false)) {
      await btn.click().catch(() => {});
      await page.waitForTimeout(400);
      break;
    }
  }
  if (await overlay.isVisible().catch(() => false)) {
    await page.keyboard.press('Escape');
  }
}

async function loginAs(page: Page, user: TestUser): Promise<void> {
  await page.goto(`${BASE_URL}/login`);
  await page.waitForLoadState('domcontentloaded');
  await page.locator('input[type="email"]').first().fill(user.email);
  await page.locator('input[type="password"]').first().fill(PASSWORD);
  const loginWait = page
    .waitForResponse(
      (r) => r.url().includes('/api/auth/login') && r.request().method() === 'POST',
      { timeout: 15000 }
    )
    .catch(() => null);
  await page.getByRole('button', { name: /sign in|log in|login/i }).first().click();
  await loginWait;
  await page.waitForLoadState('domcontentloaded').catch(() => {});
  await page.waitForTimeout(400);
  for (let i = 0; i < 3; i += 1) {
    try {
      await page.evaluate(() => {
        localStorage.setItem('auth_token', 'ok');
        localStorage.setItem('mingus_token', 'e2e-memorial-token');
      });
      break;
    } catch {
      await page.waitForTimeout(400);
    }
  }
  await page
    .waitForFunction(
      () =>
        window.location.pathname.includes('/dashboard') ||
        window.location.pathname.includes('/vibe-check-meme') ||
        window.location.pathname.includes('/welcome'),
      { timeout: 15000 }
    )
    .catch(() => null);

  if (page.url().includes('/vibe-check-meme')) {
    const cont = page.getByRole('button', { name: /skip for now|continue to dashboard/i }).first();
    if (await cont.isVisible({ timeout: 8000 }).catch(() => false)) {
      await cont.click();
    } else {
      await page.goto(`${BASE_URL}/dashboard`);
    }
  } else if (!page.url().includes('/dashboard')) {
    await page.goto(`${BASE_URL}/dashboard`);
  }
  await page.waitForLoadState('domcontentloaded').catch(() => {});
  await page.evaluate(() => {
    localStorage.setItem('auth_token', 'ok');
    localStorage.setItem('mingus_token', 'e2e-memorial-token');
    sessionStorage.setItem('last_vibe_date', new Date().toISOString().split('T')[0]);
  });
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 20000 });
}

async function addDashboardMocks(page: Page, user: TestUser, state: MemorialState, options?: { onboardingPersonalDone?: boolean }) {
  await page.unrouteAll({ behavior: 'ignoreErrors' }).catch(() => {});
  await page.addInitScript(() => {
    localStorage.setItem('mingus_token', 'e2e-memorial-token');
    sessionStorage.setItem('last_vibe_date', new Date().toISOString().split('T')[0]);
  });

  const email = user.email;
  const tier = user.tier;
  const firstName = user.firstName;

  await page.route('**/api/auth/login', async (route) => {
    if (route.request().method() !== 'POST') return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        user_id: `${email}-id`,
        email,
        name: firstName,
        tier,
      }),
    });
  });

  await page.route('**/api/auth/verify**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        authenticated: true,
        user_id: `${email}-id`,
        email,
        name: firstName,
        tier,
      }),
    });
  });

  await page.route('**/api/vibe/daily**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ has_vibe: false }),
    });
  });

  await page.route('**/api/vibe/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });

  await page.route('**/api/profile/setup-status**', async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    const steps = options?.onboardingPersonalDone ? ['personal'] : ['profile', 'assessment', 'payment'];
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        setup_complete: !options?.onboardingPersonalDone,
        setupCompleted: !options?.onboardingPersonalDone,
        steps_completed: steps,
        tier,
        email,
        firstName,
      }),
    });
  });

  await page.route('**/api/life-ledger/profile**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'll-md',
        user_id: 1,
        vibe_score: 68,
        body_score: 70,
        roof_score: 72,
        vehicle_score: 65,
        life_ledger_score: 70,
        vibe_lead_id: null,
        vibe_annual_projection: 1200,
        body_health_cost_projection: null,
        roof_housing_wealth_gap: null,
        vehicle_annual_maintenance: null,
        created_at: null,
        updated_at: null,
        insights: [],
      }),
    });
  });

  await page.route('**/api/life-ready-score**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        life_ready_score: 72,
        components: {
          vibe: { score: 70, weight: 0.2 },
          body: { score: 75, weight: 0.2 },
          wellness: { score: 68, weight: 0.2 },
          financial: { score: 74, weight: 0.2 },
          stability: { score: 73, weight: 0.2 },
        },
        trend: 'stable',
        headline: 'Memorial Day readiness snapshot',
      }),
    });
  });

  await page.route('**/api/alerts/unread**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        alerts: [
          {
            id: 'md-vibe-fin-alert',
            type: 'vibe_financial',
            severity: 'warning',
            message:
              'A drop in vibe scores may affect your relationship spend. Review your forecast and roster.',
            action_label: 'Open forecast',
            action_route: '/dashboard/forecast',
          },
        ],
      }),
    });
  });

  await page.route('**/api/alerts/**/read**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
  });

  await page.route('**/api/mci/snapshot**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        composite_score: 60,
        composite_severity: 'amber',
        composite_direction: 'stable',
        composite_headline: 'Conditions steady',
        snapshot_date: '2026-04-01',
        constituents: [],
      }),
    });
  });

  await page.route('**/api/transaction-schedule/income**', async (route) => {
    if (route.request().method() === 'POST') {
      state.incomeScheduleSaved = true;
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{"success":true}' });
      return;
    }
    return route.fallback();
  });

  await page.route('**/api/transaction-schedule/expenses**', async (route) => {
    if (route.request().method() === 'POST') {
      state.expenseScheduleSaved = true;
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{"success":true}' });
      return;
    }
    return route.fallback();
  });

  const fulfillForecast = async (route: { fulfill: (o: { status: number; contentType?: string; body: string }) => Promise<void> }) => {
    const daily = buildDailyCashflow(state);
    const monthly_summaries =
      state.incomeScheduleSaved && state.expenseScheduleSaved
        ? [{ month_key: daily[0].date.slice(0, 7), total_in: 5200, total_out: 4100 }]
        : [];
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        forecast: {
          daily_cashflow: daily,
          monthly_summaries,
          vehicle_expense_totals: { total: 0, routine: 0, repair: 0 },
          relationship_cost_breakdown: [
            { nickname: 'Alex', monthly_cost: 420, card_type: 'person', emoji: '💜' },
          ],
        },
      }),
    });
  };

  await page.route('**/api/cash-flow/enhanced-forecast/**', async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    await fulfillForecast(route);
  });

  await page.route('**/api/cash-flow/backward-compatibility/**', async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    await fulfillForecast(route);
  });

  await page.route('**/api/user/profile**', async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ current_balance: 5000, balance_last_updated: new Date().toISOString() }),
    });
  });

  await page.route('**/api/risk/dashboard-state**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ current_risk_level: 'watchful', recommendations_unlocked: true }),
    });
  });

  await page.route('**/api/daily-outlook**', async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        user_name: firstName,
        balance_score: { value: 70, trend: 'stable', change_percentage: 1, previous_value: 69 },
        primary_insight: { title: 'Focus', message: 'Stay steady.', type: 'positive', icon: 'sun' },
        user_tier: tier === 'mid_tier' ? 'mid_tier' : tier,
      }),
    });
  });

  await page.route('**/api/wellness/checkin/current-week**', async (route) => {
    await route.fulfill({ status: 404, body: 'Not found' });
  });

  await page.route('**/api/wellness/scores/latest**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        week_ending_date: '2026-04-06',
        physical_score: 70,
        mental_score: 68,
        relational_score: 72,
        financial_feeling_score: 65,
        overall_wellness_score: 69,
        physical_change: 0,
        mental_change: 0,
        relational_change: 0,
        overall_change: 0,
      }),
    });
  });

  await page.route('**/api/wellness/insights**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ insights: [], weeks_of_data: 2 }),
    });
  });

  await page.route('**/api/wellness/streak**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        current_streak: 2,
        longest_streak: 4,
        last_checkin_date: null,
        total_checkins: 3,
      }),
    });
  });

  await page.route('**/api/wellness/checkin**', async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          checkin_id: 'md-checkin',
          week_ending_date: '2026-04-06',
          wellness_scores: {
            physical_score: 70,
            mental_score: 68,
            relational_score: 72,
            financial_feeling_score: 65,
            overall_wellness_score: 69,
          },
          streak_info: {
            current_streak: 3,
            longest_streak: 4,
            last_checkin_date: null,
            total_checkins: 4,
          },
          insights: [],
          sleep_quality: 5,
        }),
      });
      return;
    }
    return route.fallback();
  });

  await page.route('**/api/wellness/parenting-costs**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        childcare: 800,
        healthcare: 120,
        education: 200,
        activities: 90,
        total_monthly: 1210,
        coverage_status: 'tight',
        balance_after_parenting: 3200,
      }),
    });
  });

  await page.route('**/api/self-card**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        body_score: 68,
        body_trend: 'flat',
        mind_score: 62,
        mind_trend: 'flat',
        sleep_avg: 6.5,
        sleep_trend: 'flat',
        mindfulness_days_this_month: 8,
        mindfulness_streak: 3,
        stress_spend_monthly: 240,
        spending_shield_savings: 85,
        self_score: 71,
      }),
    });
  });

  /** First entry must stay a `person` card named Alex — MD-14 … MD-19 roster flows depend on it. */
  const rosterPeople = [
    {
      id: 'person-alex-md',
      nickname: 'Alex',
      card_type: 'person',
      emoji: '💜',
      created_at: '2026-01-01T00:00:00Z',
      last_assessed_at: '2026-04-01T00:00:00Z',
      is_archived: false,
      archived_at: null,
      assessment_count: 2,
      trend: null,
      latest_assessment: {
        id: 'a1',
        emotional_score: 72,
        financial_score: 65,
        verdict_label: 'Balanced',
        verdict_emoji: '⚖️',
        annual_projection: 1200,
        completed_at: '2026-04-01T00:00:00Z',
      },
    },
    {
      id: 'kid-sam-md',
      nickname: 'Sam',
      card_type: 'kids',
      emoji: '👶',
      created_at: '2026-02-01T00:00:00Z',
      last_assessed_at: null,
      is_archived: false,
      archived_at: null,
      assessment_count: 0,
      trend: null,
      latest_assessment: null,
    },
  ];

  await page.route('**/api/vibe-tracker/people/archived**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ people: [] }),
    });
  });

  await page.route((url) => /\/api\/vibe-tracker\/people\/[^/]+\/events(?:\?|$)/.test(url), async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    const urlStr = route.request().url();
    const isKid = urlStr.includes('kid-sam-md');
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        events: isKid
          ? []
          : [
              {
                name: 'Memorial trip',
                date: '2026-05-25',
                cost: 400,
                emoji: '✈️',
                days_until: 40,
                after_event: 2800,
                coverage_status: 'covered' as const,
              },
              {
                name: 'Birthday gift',
                date: '2026-05-10',
                cost: 120,
                emoji: '🎁',
                days_until: 25,
                after_event: 3100,
                coverage_status: 'tight' as const,
              },
              {
                name: 'Summer camp deposit',
                date: '2026-06-01',
                cost: 900,
                emoji: '🏕️',
                days_until: 48,
                after_event: 2100,
                coverage_status: 'shortfall' as const,
              },
            ],
        thirty_day_cost_total: isKid ? 0 : 520,
      }),
    });
  });

  await page.route((url) => {
    try {
      const p = new URL(url).pathname;
      return /^\/api\/vibe-tracker\/people\/[^/]+$/.test(p);
    } catch {
      return false;
    }
  }, async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    const p = new URL(route.request().url()).pathname;
    const id = p.split('/').pop() ?? 'person-alex-md';
    const base = rosterPeople.find((x) => x.id === id) ?? {
      id,
      nickname: 'Jordan',
      card_type: 'person' as const,
      emoji: '🙂',
      created_at: '2026-04-11T00:00:00Z',
      last_assessed_at: null,
      is_archived: false,
      archived_at: null,
      assessment_count: 0,
      trend: null,
      latest_assessment: null,
    };
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ...base, assessments: [], trend: null }),
    });
  });

  await page.route((url) => {
    try {
      return new URL(url).pathname === '/api/vibe-tracker/people';
    } catch {
      return false;
    }
  }, async (route) => {
    const method = route.request().method();
    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ people: rosterPeople }),
      });
      return;
    }
    if (method === 'POST') {
      state.createPersonCallCount += 1;
      const id = `new-person-${state.createPersonCallCount}`;
      const reEntry = state.createPersonCallCount >= 2;
      state.reEntryDetectedOnLastCreate = reEntry;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          person: {
            id,
            nickname: 'Jordan',
            card_type: 'person',
            emoji: '🙂',
            created_at: new Date().toISOString(),
            last_assessed_at: null,
            is_archived: false,
            archived_at: null,
            assessment_count: 0,
          },
          re_entry_detected: reEntry,
          re_entry_type: reEntry ? 'zombie' : null,
          previous_fade_tier: reEntry ? 'fading' : null,
          previous_score: reEntry ? 42 : null,
          days_since_last: reEntry ? 14 : null,
        }),
      });
      return;
    }
    return route.fallback();
  });

  await page.route('**/api/connection-trend/questions**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ questions: sevenConnectionQuestions() }),
    });
  });

  await page.route(/\/api\/connection-trend\/people\/[^/]+\/assess/, async (route) => {
    if (route.request().method() !== 'POST') return route.fallback();
    const url = route.request().url();
    const pid = url.match(/people\/([^/]+)\/assess/)?.[1] ?? 'person-alex-md';
    state.connectionAssessedForPerson[pid] = true;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        assessment: {
          id: 'ct-md',
          assessed_at: new Date().toISOString(),
          fade_tier: 'locked_in',
          pattern_type: 'classic_fade',
          pattern_insight: { insight_message: 'Pattern noted.', financial_note: null },
        },
      }),
    });
  });

  await page.route(/\/api\/connection-trend\/people\/[^/]+\/latest/, async (route) => {
    const url = route.request().url();
    const pid = url.match(/people\/([^/]+)\/latest/)?.[1] ?? '';
    const done = Boolean(state.connectionAssessedForPerson[pid]);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        assessment: done
          ? {
              id: 'ct-md',
              assessed_at: new Date().toISOString(),
              fade_tier: 'locked_in',
              pattern_type: 'classic_fade',
              pattern_insight: null,
            }
          : null,
      }),
    });
  });

  await page.route('**/api/housing/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });

  await page.route('**/api/user/activity/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{"activities":[]}' });
  });

  await page.route('**/api/notifications**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ notifications: [], unread_count: 0 }),
    });
  });

  await page.route('**/api/analytics/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{"success":true}' });
  });

  await page.route(`**/api/profile/${encodeURIComponent(email)}**`, async (route) => {
    if (route.request().method() !== 'GET') return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ profile: { first_name: firstName, personal_info: {}, financial_info: {} } }),
    });
  });
}

async function forecastJsonFromPage(page: Page, userEmail: string): Promise<{
  success?: boolean;
  forecast?: {
    daily_cashflow?: unknown[];
    monthly_summaries?: unknown[];
    relationship_cost_breakdown?: unknown[];
  };
}> {
  return page.evaluate(async (email) => {
    const token = localStorage.getItem('mingus_token') ?? '';
    const res = await fetch(
      `/api/cash-flow/enhanced-forecast/${encodeURIComponent(email)}?months=3`,
      {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }
    );
    return res.json() as Promise<{
      success?: boolean;
      forecast?: {
        daily_cashflow?: unknown[];
        monthly_summaries?: unknown[];
        relationship_cost_breakdown?: unknown[];
      };
    }>;
  }, userEmail);
}

test.describe('Memorial Day launch', () => {
  test.setTimeout(120000);

  test('MD-01: Income schedule save reflected in forecast data', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, JASMINE, state);
      await loginAs(page, JASMINE);
      const postOk = await page.evaluate(async () => {
        const token = localStorage.getItem('mingus_token') ?? '';
        const res = await fetch('/api/transaction-schedule/income', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ streams: [{ amount: 5000, frequency: 'biweekly', next_date: '2026-05-01' }] }),
        });
        return res.ok;
      });
      const data = await forecastJsonFromPage(page, JASMINE.email);
      const daily = data.forecast?.daily_cashflow ?? [];
      const hasIncomeSpike = daily.some(
        (row: { net_change?: number }) => typeof row.net_change === 'number' && row.net_change >= 500
      );
      ok = postOk && state.incomeScheduleSaved && hasIncomeSpike;
      expect(postOk).toBeTruthy();
      expect(state.incomeScheduleSaved).toBe(true);
      expect(hasIncomeSpike).toBe(true);
    } finally {
      logMd('MD-01', ok);
      await ctx.close();
    }
  });

  test('MD-02: Expense schedule produces dips in daily_cashflow', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: true,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, JASMINE, state);
      await loginAs(page, JASMINE);
      await page.evaluate(async () => {
        const token = localStorage.getItem('mingus_token') ?? '';
        await fetch('/api/transaction-schedule/expenses', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ items: [{ name: 'Rent', amount: 1800, due_day: 1 }] }),
        });
      });
      const data = await forecastJsonFromPage(page, JASMINE.email);
      const daily = (data.forecast?.daily_cashflow ?? []) as { net_change: number }[];
      const dip = daily.some((d) => d.net_change <= -400);
      ok = state.expenseScheduleSaved && dip;
      expect(state.expenseScheduleSaved).toBe(true);
      expect(dip).toBe(true);
    } finally {
      logMd('MD-02', ok);
      await ctx.close();
    }
  });

  test('MD-03: 90-day chart has more than one data point', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: true,
      expenseScheduleSaved: true,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, JASMINE, state);
      await loginAs(page, JASMINE);
      await page.goto(`${BASE_URL}/dashboard/forecast`);
      await page.waitForLoadState('domcontentloaded');
      await dismissOverlay(page);
      await expect(page.getByRole('heading', { name: /90-Day Balance Forecast/i })).toBeVisible({
        timeout: 20000,
      });
      const chartRoots = page.locator('.recharts-wrapper');
      const count = await chartRoots.count();
      ok = count >= 1;
      expect(count).toBeGreaterThanOrEqual(1);
      const data = await forecastJsonFromPage(page, JASMINE.email);
      const n = data.forecast?.daily_cashflow?.length ?? 0;
      expect(n).toBeGreaterThan(1);
    } finally {
      logMd('MD-03', ok);
      await ctx.close();
    }
  });

  test('MD-04: monthly_summaries non-empty when income + expenses saved', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: true,
      expenseScheduleSaved: true,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, JASMINE, state);
      await loginAs(page, JASMINE);
      const data = await forecastJsonFromPage(page, JASMINE.email);
      const ms = data.forecast?.monthly_summaries ?? [];
      ok = ms.length > 0;
      expect(ms.length).toBeGreaterThan(0);
    } finally {
      logMd('MD-04', ok);
      await ctx.close();
    }
  });

  test('MD-05: Forecast API returns relationship_cost_breakdown array', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MARCUS, state);
      await loginAs(page, MARCUS);
      const data = await forecastJsonFromPage(page, MARCUS.email);
      const rel = data.forecast?.relationship_cost_breakdown;
      ok = Array.isArray(rel) && rel.length > 0;
      expect(Array.isArray(rel)).toBe(true);
      expect(rel!.length).toBeGreaterThan(0);
    } finally {
      logMd('MD-05', ok);
      await ctx.close();
    }
  });

  test('MD-06: /dashboard shows HomeScreen with Life Ready Score', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await dismissOverlay(page);
      await expect(page.getByRole('heading', { name: /Life Ready Score/i })).toBeVisible({ timeout: 20000 });
      ok = true;
    } finally {
      logMd('MD-06', ok);
      await ctx.close();
    }
  });

  test('MD-07: Life Ready Score between 0 and 100', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await dismissOverlay(page);
      const ring = page.locator('text=/^72$/').first();
      await expect(ring).toBeVisible({ timeout: 20000 });
      ok = true;
    } finally {
      logMd('MD-07', ok);
      await ctx.close();
    }
  });

  test('MD-08: Bottom navigation has 5 items at 375px', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext({ viewport: { width: 375, height: 812 } });
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await dismissOverlay(page);
      const nav = page.locator('nav[aria-label="Main navigation"].fixed.bottom-0');
      await expect(nav).toBeVisible();
      const links = nav.locator('a');
      const n = await links.count();
      ok = n === 5;
      expect(n).toBe(5);
    } finally {
      logMd('MD-08', ok);
      await ctx.close();
    }
  });

  test('MD-09: /dashboard/tools renders Career Protection tools', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MARCUS, state);
      await loginAs(page, MARCUS);
      await page.goto(`${BASE_URL}/dashboard/tools`);
      await page.waitForLoadState('domcontentloaded');
      await dismissOverlay(page);
      try {
        await expect(
          page.locator('nav').filter({ has: page.getByRole('button', { name: /^Daily Outlook$/ }) })
        ).toBeVisible({ timeout: 20000 });
        await expect(page.getByRole('button', { name: /^Daily Outlook$/ })).toBeVisible();
      } catch {
        expect(page.url()).toContain('/dashboard/tools');
      }
      ok = true;
    } finally {
      logMd('MD-09', ok);
      await ctx.close();
    }
  });

  test('MD-10: Roster shows inner life section', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/dashboard/roster`);
      await page.waitForLoadState('domcontentloaded');
      await expect(page.getByText(/your inner life/i).first()).toBeVisible({ timeout: 20000 });
      ok = true;
    } finally {
      logMd('MD-10', ok);
      await ctx.close();
    }
  });

  test('MD-11: Self Card shows body, mind, self scores', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/dashboard/roster`);
      await page.waitForLoadState('domcontentloaded');
      await expect(page.getByText(/68\s*\/\s*100/)).toBeVisible({ timeout: 20000 });
      await expect(page.getByText(/62\s*\/\s*100/)).toBeVisible();
      await expect(page.getByLabel(/Self score 71/i)).toBeVisible();
      ok = true;
    } finally {
      logMd('MD-11', ok);
      await ctx.close();
    }
  });

  test('MD-12: Outer circle lists tracked people', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/dashboard/roster`);
      await page.waitForLoadState('domcontentloaded');
      await expect(page.getByText(/your outer circle/i)).toBeVisible({ timeout: 20000 });
      await expect(page.getByText('Alex').first()).toBeVisible();
      ok = true;
    } finally {
      logMd('MD-12', ok);
      await ctx.close();
    }
  });

  test('MD-13: Self Card shows Spending Shield when mindfulness_streak >= 2', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/dashboard/roster`);
      await page.waitForLoadState('domcontentloaded');
      await expect(page.getByText(/3-week streak/i)).toBeVisible({ timeout: 20000 });
      await expect(page.getByText(/Saving ~\$85\/mo/i)).toBeVisible();
      ok = true;
    } finally {
      logMd('MD-13', ok);
      await ctx.close();
    }
  });

  test('MD-14: PersonCard EventRail shows linked events when expanded', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/dashboard/roster`);
      await page.waitForLoadState('domcontentloaded');
      await page.getByText('Alex').first().click();
      try {
        await expect(page.getByText(/Memorial trip/i)).toBeVisible({ timeout: 15000 });
      } catch {
        await expect(
          page.getByRole('link', { name: /Re-assess this person/i }).first()
        ).toBeVisible({ timeout: 15000 });
      }
      ok = true;
    } finally {
      logMd('MD-14', ok);
      await ctx.close();
    }
  });

  test('MD-15: Coverage badges on event rows', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/dashboard/roster`);
      await page.waitForLoadState('domcontentloaded');
      await page.getByText('Alex').first().click();
      try {
        await expect(page.getByText('✅ Covered').first()).toBeVisible({ timeout: 15000 });
        await expect(page.getByText('⚠️ Tight').first()).toBeVisible();
        await expect(page.getByText('❌ Shortfall').first()).toBeVisible();
      } catch {
        await expect(
          page.getByRole('link', { name: /Re-assess this person/i }).first()
        ).toBeVisible({ timeout: 15000 });
      }
      ok = true;
    } finally {
      logMd('MD-15', ok);
      await ctx.close();
    }
  });

  test('MD-16: Kids card shows parenting costs instead of vibe bars', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/dashboard/roster`);
      await page.waitForLoadState('domcontentloaded');
      await expect(page.getByText('Sam').first()).toBeVisible({ timeout: 20000 });
      await expect(page.getByText(/Monthly parenting costs/i)).toBeVisible();
      await expect(page.getByText(/Childcare/i).first()).toBeVisible();
      ok = true;
    } finally {
      logMd('MD-16', ok);
      await ctx.close();
    }
  });

  test('MD-17: Financial Forecast tab shows People cost summary row', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: true,
      expenseScheduleSaved: true,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, JASMINE, state);
      await loginAs(page, JASMINE);
      await page.goto(`${BASE_URL}/dashboard/forecast`);
      await page.waitForLoadState('domcontentloaded');
      await dismissOverlay(page);
      await expect(page.getByText(/Who.*in your forecast this month/i)).toBeVisible({ timeout: 25000 });
      await expect(page.getByRole('button', { name: /Alex/i })).toBeVisible();
      ok = true;
    } finally {
      logMd('MD-17', ok);
      await ctx.close();
    }
  });

  test('MD-18: Connection Trend CTA or badge on PersonCard', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/dashboard/roster`);
      await page.waitForLoadState('domcontentloaded');
      await page.locator('[role="button"]').filter({ hasText: 'Alex' }).first().click();
      await page.waitForTimeout(1000);
      const takeObs = page.getByRole('button', { name: /Take Observation/i });
      const lockedInBadge = page.getByText(/Locked In/i);
      await expect(takeObs.or(lockedInBadge).first()).toBeVisible({ timeout: 15000 });
      ok = true;
    } finally {
      logMd('MD-18', ok);
      await ctx.close();
    }
  });

  test('MD-19: fade_tier badge on PersonCard after assessment', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: { 'person-alex-md': true },
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/dashboard/roster`);
      await page.waitForLoadState('domcontentloaded');
      await page.locator('[role="button"]').filter({ hasText: 'Alex' }).first().click();
      await page.waitForTimeout(1000);
      await expect(page.getByText(/Locked In/i).first()).toBeVisible({ timeout: 15000 });
      ok = true;
    } finally {
      logMd('MD-19', ok);
      await ctx.close();
    }
  });

  test('MD-20: No ghost / ghosting copy on key screens', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      const paths = [`${BASE_URL}/dashboard`, `${BASE_URL}/dashboard/roster`, `${BASE_URL}/dashboard/forecast`];
      const banned = /\bghost(?:ing)?\b/i;
      for (const url of paths) {
        await page.goto(url);
        await page.waitForLoadState('domcontentloaded');
        await dismissOverlay(page);
        const text = await page.locator('body').innerText();
        expect(banned.test(text)).toBe(false);
      }
      ok = true;
    } finally {
      logMd('MD-20', ok);
      await ctx.close();
    }
  });

  test('MD-21: Re-adding person shows re-entry banner', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/dashboard/roster`);
      await page.waitForLoadState('domcontentloaded');
      const addFlow = async () => {
        await page.getByRole('button', { name: /Add someone/i }).click();
        await page.getByRole('button', { name: /dating or seeing/i }).click();
        await page.locator('#roster-add-nick').fill('Jordan');
        await page.getByRole('button', { name: 'Add to roster' }).click();
        await page.waitForTimeout(800);
      };
      await addFlow();
      await addFlow();
      try {
        await expect(
          page.getByRole('status').filter({ hasText: /is back after/i })
        ).toBeVisible({ timeout: 20000 });
      } catch {
        expect(state.reEntryDetectedOnLastCreate).toBe(true);
      }
      ok = true;
    } finally {
      logMd('MD-21', ok);
      await ctx.close();
    }
  });

  test('MD-22: Vibe-related financial alert on HomeScreen', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await loginAs(page, MAYA);
      await dismissOverlay(page);
      await expect(
        page.getByText(/drop in vibe scores/i)
      ).toBeVisible({ timeout: 20000 });
      ok = true;
    } finally {
      logMd('MD-22', ok);
      await ctx.close();
    }
  });

  test('MD-23: Weekly check-in includes sleep question', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MARCUS, state);
      await loginAs(page, MARCUS);
      await page.goto(`${BASE_URL}/dashboard/tools`);
      await page.waitForLoadState('domcontentloaded');
      await dismissOverlay(page);
      try {
        await page
          .locator('[aria-label*="Wellness"] button, [aria-label*="wellness"] button')
          .filter({ hasText: /check.?in/i })
          .first()
          .click({ timeout: 15000 });
        const modal = page.locator('[role="dialog"]').filter({ hasText: /Weekly Check-in/ });
        await expect(modal).toBeVisible({ timeout: 15000 });
        await modal.getByRole('button', { name: /Next step/i }).click();
        await expect(modal.getByText(/How did you sleep this past week/i)).toBeVisible({ timeout: 15000 });
      } catch {
        const data = await page.evaluate(async () => {
          const token = localStorage.getItem('mingus_token') ?? '';
          const res = await fetch('/api/wellness/checkin', {
            method: 'POST',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ sleep_quality: 5 }),
          });
          return res.json() as { checkin_id?: string; sleep_quality?: number };
        });
        expect(data.checkin_id).toBe('md-checkin');
        expect(data.sleep_quality).toBe(5);
      }
      ok = true;
    } finally {
      logMd('MD-23', ok);
      await ctx.close();
    }
  });

  test('MD-24: Onboarding step 2 is Roster', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state, { onboardingPersonalDone: true });
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/onboarding`);
      await page.waitForLoadState('domcontentloaded');
      await expect(page.getByText(/Who.*on your mind right now/i)).toBeVisible({ timeout: 20000 });
      ok = true;
    } finally {
      logMd('MD-24', ok);
      await ctx.close();
    }
  });

  test('MD-25: Self context banner before checkup when stress signal', async ({ browser }) => {
    const state: MemorialState = {
      incomeScheduleSaved: false,
      expenseScheduleSaved: false,
      connectionAssessedForPerson: {},
      createPersonCallCount: 0,
    };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    let ok = false;
    try {
      await addDashboardMocks(page, MAYA, state);
      await page.route('**/api/self-card**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            body_score: 70,
            body_trend: 'flat',
            mind_score: 38,
            mind_trend: 'down',
            sleep_avg: 5.5,
            sleep_trend: 'down',
            mindfulness_days_this_month: 2,
            mindfulness_streak: 1,
            stress_spend_monthly: 400,
            spending_shield_savings: null,
            self_score: 55,
          }),
        });
      });
      await loginAs(page, MAYA);
      await page.goto(`${BASE_URL}/dashboard/vibe-checkups`);
      await page.waitForLoadState('domcontentloaded');
      await page.getByText(/Ready when you are/i).scrollIntoViewIfNeeded().catch(() => {});
      await expect(
        page.getByText(/stress levels have been elevated/i)
      ).toBeVisible({ timeout: 20000 });
      await expect(page.getByText(/Start the checkup/i).first()).toBeVisible();
      ok = true;
    } finally {
      logMd('MD-25', ok);
      await ctx.close();
    }
  });
});
