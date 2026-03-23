import { defineConfig, devices } from '@playwright/test';

// Cap V8 heap before Playwright spawns workers (child processes inherit env).
const nodeHeapMb = process.env.PLAYWRIGHT_NODE_HEAP_MB || '2048';
if (!/\b--max-old-space-size=/.test(process.env.NODE_OPTIONS ?? '')) {
  process.env.NODE_OPTIONS = [process.env.NODE_OPTIONS, `--max-old-space-size=${nodeHeapMb}`]
    .filter(Boolean)
    .join(' ')
    .trim();
}

export default defineConfig({
  testDir: 'tests/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: 2,
  timeout: 120_000,
  reporter: 'html',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'https://test.mingusapp.com',
    trace: 'on-first-retry',
    actionTimeout: 15_000,
    launchOptions: {
      args: ['--disable-dev-shm-usage', '--disable-gpu'],
      handleSIGINT: true,
      handleSIGTERM: true,
    },
  },
  projects: [
    {
      name: 'default',
      testIgnore: '**/auth.spec.ts',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'chromium',
      testIgnore: '**/auth.spec.ts',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      testIgnore: '**/auth.spec.ts',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      testIgnore: '**/auth.spec.ts',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'auth',
      testMatch: '**/auth.spec.ts',
      use: { ...devices['Desktop Chrome'] },
      workers: 1,
    },
  ],
});
