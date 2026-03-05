import { test, expect, chromium, Browser, BrowserContext, Page } from '@playwright/test';

const BASE_URL = 'https://test.mingusapp.com';

let browser: Browser;
let context: BrowserContext;
let page: Page;

test.describe('Persona 2 - Marcus', () => {
  test.beforeAll(async () => {
    browser = await chromium.launch({ headless: false });
    context = await browser.newContext();
    page = await context.newPage();
  });

  test.afterAll(async () => {
    await context.close();
    await browser.close();
  });

  // TODO: add tests for Persona 2 - Marcus
});
