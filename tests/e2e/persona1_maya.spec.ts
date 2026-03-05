import { test, expect, chromium, Browser, BrowserContext, Page } from '@playwright/test';

const BASE_URL = 'https://test.mingusapp.com';

let browser: Browser;
let context: BrowserContext;
let page: Page;

test.describe('Persona 1 - Maya', () => {
  test.beforeAll(async () => {
    browser = await chromium.launch({ headless: false });
    context = await browser.newContext();
    page = await context.newPage();
  });

  test.afterAll(async () => {
    await context.close();
    await browser.close();
  });

  test('Maya completes AI Replacement Risk Assessment and continues to sign up', async () => {
    // 1. Navigate to landing page
    await page.goto(BASE_URL);
    await expect(page).toHaveURL(BASE_URL);

    // 2. Open AI Replacement Risk Assessment (button, link, or card)
    const assessmentTrigger = page.getByRole('button', { name: /AI Replacement Risk|Risk Assessment/i })
      .or(page.getByRole('link', { name: /AI Replacement Risk|Risk Assessment/i }))
      .or(page.getByText(/AI Replacement Risk|Risk Assessment/).first());
    await assessmentTrigger.first().click();
    await expect(
      page.getByRole('dialog').or(page.locator('[role="dialog"]')).or(page.getByText(/assessment|email|first name/i).first())
    ).toBeVisible({ timeout: 10000 });

    // 3–4. Fill email and first name
    await page.getByLabel(/email/i).or(page.getByPlaceholder(/email/i)).fill('maya.johnson.test@gmail.com');
    await page.getByLabel(/first name|firstname/i).or(page.getByPlaceholder(/first name|firstname/i)).fill('Maya');

    // 5. Answer each question (single-select radio — click label; radio has class="sr-only")
    await page.locator('label').filter({ hasText: /Administrative\/scheduling/i }).click();
    await page.locator('label').filter({ hasText: /Yes, in a minor way/i }).click();
    await page.locator('label').filter({ hasText: /Within a week or two/i }).click();
    await page.locator('label').filter({ hasText: /Sometimes/i }).click();
    await page.locator('label').filter({ hasText: /I adopt it when required/i }).click();
    await page.locator('label').filter({ hasText: /Somewhat/i }).click();
    await page.locator('label').filter({ hasText: /Mostly in my head/i }).click();
    await page.locator('label').filter({ hasText: /Not yet but I can see it coming/i }).click();
    await page.locator('label').filter({ hasText: /No time/i }).click();
    await page.locator('label').filter({ hasText: /50-75%/i }).click();

    // 6. Submit assessment and wait for result
    await page.getByRole('button', { name: /Complete Assessment/i }).click();
    const resultArea = page.getByRole('dialog').or(page.locator('[data-testid*="result"]')).or(page.getByText(/vulnerabilities|score|results?/i).first());
    await expect(resultArea).toBeVisible({ timeout: 15000 });

    // 7. Result headline contains expected text
    await expect(page.getByText(/Real vulnerabilities worth addressing now/i)).toBeVisible();

    // 8. Score between 38 and 48 displayed
    const scoreLocator = page.locator('text=/\\b(3[89]|4[0-8])\\b/');
    await expect(scoreLocator.first()).toBeVisible({ timeout: 5000 });
    const scoreText = await scoreLocator.first().textContent();
    const scoreMatch = scoreText?.match(/\b(3[89]|4[0-8])\b/);
    expect(scoreMatch).toBeTruthy();
    const score = parseInt(scoreMatch![1], 10);
    expect(score).toBeGreaterThanOrEqual(38);
    expect(score).toBeLessThanOrEqual(48);

    // 9. Continue to Sign Up
    await page.getByRole('button', { name: /Continue to Sign Up/i }).click();
    await expect(
      page.getByRole('form').or(page.getByText(/sign up|create account|register/i)).or(page.locator('input[type="password"]'))
    ).toBeVisible({ timeout: 10000 });
  });

  test('Maya completes Income Comparison Assessment', async () => {
    // 1. Navigate to landing page
    await page.goto(BASE_URL);
    await expect(page).toHaveURL(BASE_URL);

    // 2. Open Income Comparison Assessment (button, link, or card)
    const assessmentTrigger = page.getByRole('button', { name: /Income Comparison/i })
      .or(page.getByRole('link', { name: /Income Comparison/i }))
      .or(page.getByText(/Income Comparison/).first());
    await assessmentTrigger.first().click();
    await expect(
      page.getByRole('dialog').or(page.locator('[role="dialog"]')).or(page.getByText(/assessment|email|first name|income/i).first())
    ).toBeVisible({ timeout: 10000 });

    // 3. Fill email and first name if empty (app may not pre-fill), then assert
    const emailField = page.getByLabel(/email/i).or(page.getByPlaceholder(/email/i)).first();
    const emailValue = await emailField.inputValue();
    if (!emailValue) await emailField.fill('maya.johnson.test@gmail.com');
    await expect(emailField).toHaveValue('maya.johnson.test@gmail.com');

    const nameField = page.getByLabel(/first name|firstname/i).or(page.getByPlaceholder(/first name|firstname/i)).first();
    const nameValue = await nameField.inputValue();
    if (!nameValue) await nameField.fill('Maya');
    await expect(nameField).toHaveValue('Maya');

    // 4. Answer each question (click label; radio has class="sr-only")
    await page.locator('label').filter({ hasText: /1-2 years ago/i }).click();
    await page.locator('label').filter({ hasText: /No, I accepted without negotiating/i }).click();
    await page.locator('label').filter({ hasText: /Feel upset but probably do nothing/i }).click();
    await page.locator('label').filter({ hasText: /Rarely/i }).click();
    await page.locator('label').filter({ hasText: /Didn't ask for a raise/i }).click();
    await page.locator('label').filter({ hasText: /Mostly happened to me/i }).click();
    await page.locator('label').filter({ hasText: /Serious problem/i }).click();
    await page.locator('label').filter({ hasText: /Not applicable/i }).click();
    await page.locator('label').filter({ hasText: /Somewhat/i }).click();

    // 5. Submit and wait for result
    await page.getByRole('button', { name: /Complete Assessment/i }).click();
    const resultArea = page.getByRole('dialog').or(page.locator('[data-testid*="result"]')).or(page.getByText(/leaving real money|score|results?/i).first());
    await expect(resultArea).toBeVisible({ timeout: 15000 });

    // 6. Headline contains expected text
    await expect(page.getByText(/You know there's a gap – now it's time to act/i)).toBeVisible();

    // 7. Score between 18 and 32 displayed
    const scoreLocator = page.locator('text=/\\b(1[89]|2[0-9]|3[0-2])\\b/');
    await expect(scoreLocator.first()).toBeVisible({ timeout: 5000 });
    const scoreText = await scoreLocator.first().textContent();
    const scoreMatch = scoreText?.match(/\b(1[89]|2[0-9]|3[0-2])\b/);
    expect(scoreMatch).toBeTruthy();
    const score = parseInt(scoreMatch![1], 10);
    expect(score).toBeGreaterThanOrEqual(18);
    expect(score).toBeLessThanOrEqual(32);
  });

  test('Maya completes Cuffing Season Score Assessment', async () => {
    // 1. Navigate to landing page
    await page.goto(BASE_URL);
    await expect(page).toHaveURL(BASE_URL);

    // 2. Open Cuffing Season Score Assessment (button, link, or card)
    const assessmentTrigger = page.getByRole('button', { name: /Cuffing Season/i })
      .or(page.getByRole('link', { name: /Cuffing Season/i }))
      .or(page.getByText(/Cuffing Season/).first());
    await assessmentTrigger.first().click();
    await expect(
      page.getByRole('dialog').or(page.locator('[role="dialog"]')).or(page.getByText(/assessment|email|first name|cuffing/i).first())
    ).toBeVisible({ timeout: 10000 });

    // 3. Fill email and first name if empty, then assert (app may not pre-fill)
    const emailField = page.getByLabel(/email/i).or(page.getByPlaceholder(/email/i)).first();
    const emailValue = await emailField.inputValue();
    if (!emailValue) await emailField.fill('maya.johnson.test@gmail.com');
    await expect(emailField).toHaveValue('maya.johnson.test@gmail.com');

    const nameField = page.getByLabel(/first name|firstname/i).or(page.getByPlaceholder(/first name|firstname/i)).first();
    const nameValue = await nameField.inputValue();
    if (!nameValue) await nameField.fill('Maya');
    await expect(nameField).toHaveValue('Maya');

    // 4. Answer each question — Q1 single-select; Q2 multi-select (both); Q3–Q9 single-select
    await page.locator('label').filter({ hasText: /Financial stress/i }).first().click(); // Q1
    await page.locator('label').filter({ hasText: /Financial stress/i }).first().click(); // Q2 first checkbox
    await page.locator('label').filter({ hasText: /My own emotional state/i }).click();   // Q2 second checkbox
    await page.locator('label').filter({ hasText: /Somewhat misaligned/i }).click();
    await page.locator('label').filter({ hasText: /Sometimes/i }).click();
    await page.locator('label').filter({ hasText: /Quite a bit/i }).click();
    await page.locator('label').filter({ hasText: /Yes, it was a major issue/i }).click();
    await page.locator('label').filter({ hasText: /Financial entanglement/i }).click();
    await page.locator('label').filter({ hasText: /Somewhat/i }).click();
    await page.locator('label').filter({ hasText: /Somewhat guarded/i }).click();

    // 5. Submit and wait for result
    await page.getByRole('button', { name: /Complete Assessment/i }).click();
    const resultArea = page.getByRole('dialog').or(page.locator('[data-testid*="result"]')).or(page.getByText(/barriers|score|results?/i).first());
    await expect(resultArea).toBeVisible({ timeout: 15000 });

    // 6. Headline contains expected text
    await expect(page.getByText(/You're closer than you think – a few things are in the way/i)).toBeVisible();

    // 7. Score between 30 and 45 displayed
    const scoreLocator = page.locator('text=/\\b(3[0-9]|4[0-5])\\b/');
    await expect(scoreLocator.first()).toBeVisible({ timeout: 5000 });
    const scoreText = await scoreLocator.first().textContent();
    const scoreMatch = scoreText?.match(/\b(3[0-9]|4[0-5])\b/);
    expect(scoreMatch).toBeTruthy();
    const score = parseInt(scoreMatch![1], 10);
    expect(score).toBeGreaterThanOrEqual(30);
    expect(score).toBeLessThanOrEqual(45);
  });

  test('Maya completes Layoff Risk Assessment', async () => {
    // 1. Navigate to landing page
    await page.goto(BASE_URL);
    await expect(page).toHaveURL(BASE_URL);

    // 2. Open Layoff Risk Assessment (button, link, or card)
    const assessmentTrigger = page.getByRole('button', { name: /Layoff Risk/i })
      .or(page.getByRole('link', { name: /Layoff Risk/i }))
      .or(page.getByText(/Layoff Risk/).first());
    await assessmentTrigger.first().click();
    await expect(
      page.getByRole('dialog').or(page.locator('[role="dialog"]')).or(page.getByText(/assessment|email|first name|layoff/i).first())
    ).toBeVisible({ timeout: 10000 });

    // 3. Fill email and first name if empty, then assert (app may not pre-fill)
    const emailField = page.getByLabel(/email/i).or(page.getByPlaceholder(/email/i)).first();
    const emailValue = await emailField.inputValue();
    if (!emailValue) await emailField.fill('maya.johnson.test@gmail.com');
    await expect(emailField).toHaveValue('maya.johnson.test@gmail.com');

    const nameField = page.getByLabel(/first name|firstname/i).or(page.getByPlaceholder(/first name|firstname/i)).first();
    const nameValue = await nameField.inputValue();
    if (!nameValue) await nameField.fill('Maya');
    await expect(nameField).toHaveValue('Maya');

    // 4. Answer each question — Q1–Q4, Q6–Q9 single-select; Q5 checkbox (select only "Updated my resume")
    await page.locator('label').filter({ hasText: /Somewhat confident/i }).click();
    await page.locator('label').filter({ hasText: /It would take some ramp-up/i }).click();
    await page.locator('label').filter({ hasText: /No, I've only received positive signals/i }).click();
    await page.locator('label').filter({ hasText: /Neutral, they know my name/i }).click();
    // Q5: checkbox group — select ONLY "Updated my resume" (deselect any others if needed)
    await page.locator('label').filter({ hasText: /Updated my resume/i }).click();
    await page.locator('label').filter({ hasText: /I'd struggle significantly/i }).click();
    await page.locator('label').filter({ hasText: /It's inconsistent/i }).click();
    await page.locator('label').filter({ hasText: /Never that I know of/i }).click();
    await page.locator('label').filter({ hasText: /3-6 months/i }).click();

    // 5. Submit and wait for result
    await page.getByRole('button', { name: /Complete Assessment/i }).click();
    const resultArea = page.getByRole('dialog').or(page.locator('[data-testid*="result"]')).or(page.getByText(/Real risks|score|results?/i).first());
    await expect(resultArea).toBeVisible({ timeout: 15000 });

    // 6. Headline contains expected text
    await expect(page.getByText(/You have a solid base, but stay proactive/i)).toBeVisible();

    // 7. Score between 55 and 75 displayed
    const scoreLocator = page.locator('text=/\\b(5[5-9]|6[0-9]|7[0-5])\\b/');
    await expect(scoreLocator.first()).toBeVisible({ timeout: 5000 });
    const scoreText = await scoreLocator.first().textContent();
    const scoreMatch = scoreText?.match(/\b(5[5-9]|6[0-9]|7[0-5])\b/);
    expect(scoreMatch).toBeTruthy();
    const score = parseInt(scoreMatch![1], 10);
    expect(score).toBeGreaterThanOrEqual(55);
    expect(score).toBeLessThanOrEqual(75);
  });

  test('Maya completes Vehicle Financial Health Assessment', async () => {
    // 1. Navigate to landing page
    await page.goto(BASE_URL);
    await expect(page).toHaveURL(BASE_URL);

    // 2. Open Vehicle Financial Health Assessment (button, link, or card)
    const assessmentTrigger = page.getByRole('button', { name: /Vehicle Financial Health|Vehicle.*Assessment/i })
      .or(page.getByRole('link', { name: /Vehicle Financial Health|Vehicle.*Assessment/i }))
      .or(page.getByText(/Vehicle Financial Health|Vehicle.*Assessment/).first());
    await assessmentTrigger.first().click();
    await expect(
      page.getByRole('dialog').or(page.locator('[role="dialog"]')).or(page.getByText(/assessment|email|first name|vehicle/i).first())
    ).toBeVisible({ timeout: 10000 });

    // 3. Fill email and first name if empty, then assert (app may not pre-fill)
    const emailField = page.getByLabel(/email/i).or(page.getByPlaceholder(/email/i)).first();
    const emailValue = await emailField.inputValue();
    if (!emailValue) await emailField.fill('maya.johnson.test@gmail.com');
    await expect(emailField).toHaveValue('maya.johnson.test@gmail.com');

    const nameField = page.getByLabel(/first name|firstname/i).or(page.getByPlaceholder(/first name|firstname/i)).first();
    const nameValue = await nameField.inputValue();
    if (!nameValue) await nameField.fill('Maya');
    await expect(nameField).toHaveValue('Maya');

    // 4. Answer each question (single-select radio — click label)
    await page.locator('label').filter({ hasText: /I mainly focused on the monthly payment/i }).click();
    await page.locator('label').filter({ hasText: /Put it on a credit card/i }).click();
    await page.locator('label').filter({ hasText: /\$500-\$1,500/i }).click();
    await page.locator('label').filter({ hasText: /Unexpected repairs/i }).click();
    await page.locator('label').filter({ hasText: /Mostly financial with some preference/i }).click();
    await page.locator('label').filter({ hasText: /Possibly, I'm not sure/i }).click();
    await page.locator('label').filter({ hasText: /It would significantly disrupt my work/i }).click();
    await page.locator('label').filter({ hasText: /I have a general idea/i }).click();
    await page.locator('label').filter({ hasText: /More emergency savings going in/i }).click();

    // 5. Submit and wait for result
    await page.getByRole('button', { name: /Complete Assessment/i }).click();
    const resultArea = page.getByRole('dialog').or(page.locator('[data-testid*="result"]')).or(page.getByText(/managing|score|results?/i).first());
    await expect(resultArea).toBeVisible({ timeout: 15000 });

    // 6. Headline contains expected text (en-dash U+2013)
    await expect(page.getByText(/You're in decent shape – small steps can help/i)).toBeVisible();

    // 7. Score between 65 and 85 displayed
    const scoreLocator = page.locator('text=/\\b(6[5-9]|7[0-9]|8[0-5])\\b/');
    await expect(scoreLocator.first()).toBeVisible({ timeout: 5000 });
    const scoreText = await scoreLocator.first().textContent();
    const scoreMatch = scoreText?.match(/\b(6[5-9]|7[0-9]|8[0-5])\b/);
    expect(scoreMatch).toBeTruthy();
    const score = parseInt(scoreMatch![1], 10);
    expect(score).toBeGreaterThanOrEqual(65);
    expect(score).toBeLessThanOrEqual(85);
  });
});
