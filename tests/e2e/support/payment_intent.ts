import type { Page } from '@playwright/test';

export default async function handlePaymentIntent(page: Page, userEmail: string): Promise<void> {
  const e2eSecret = process.env.E2E_PAYMENT_SECRET;

  if (!e2eSecret) {
    await page.route('**/api/create-payment-intent', async (route) => {
      if (route.request().method() !== 'POST') return route.continue();

      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ clientSecret: 'pi_test_mock_secret_for_e2e' }),
      });
    });

    // eslint-disable-next-line no-console
    console.log('Payment intent mocked — E2E_PAYMENT_SECRET not set');
    return;
  }

  await page.addInitScript(
    ({ secret, email }) => {
      const originalFetch = window.fetch.bind(window);

      window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
        try {
          const url =
            typeof input === 'string'
              ? input
              : input instanceof Request
                ? input.url
                : String(input);

          if (url.includes('/api/create-payment-intent')) {
            const nextInit: RequestInit = init ? { ...init } : {};

            const existingHeaders =
              nextInit.headers ??
              (input instanceof Request ? input.headers : undefined);

            const headers = new Headers(existingHeaders as HeadersInit | undefined);
            headers.set('X-E2E-Secret', secret);
            headers.set('X-E2E-User-Email', email);
            nextInit.headers = headers;

            return originalFetch(input, nextInit);
          }
        } catch {
          // Fall through to the original fetch.
        }

        return originalFetch(input, init);
      };
    },
    { secret: e2eSecret, email: userEmail },
  );
}
