# Mingus Application – Test Notes

## Playwright E2E Suites

Key E2E suites live under `tests/e2e`:

- `cross_browser.spec.ts` – desktop cross-browser coverage (Chromium, Firefox, WebKit).
- `mobile_testing.spec.ts` – mobile and tablet viewport behavior.
- `dashboard_access.spec.ts` – canonical dashboard auth/access behavior.
- `budget_tier_features.spec.ts` – budget-tier feature gating and UI checks.

### Budget Tier Feature Tests

`tests/e2e/budget_tier_features.spec.ts` assumes the app can successfully reach `/dashboard` after login. In environments where auth redirects back to `/login`, these tests call `ensureOnDashboard` and are **skipped** with a message like:

> `ensureOnDashboard: still on https://test.mingusapp.com/login — skipping (Dashboard auth redirect — covered in dashboard_access.spec.ts)`

This is expected: dashboard access itself is already exercised in `dashboard_access.spec.ts`. To get full coverage from the budget-tier suite, run it against an environment where a budget-tier user can reach `/dashboard` after login.

