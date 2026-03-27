# Playwright + Cursor Prompt Guidelines

Use this document when writing or refining Playwright test prompts so Cursor generates correct, runnable specs. **Prepend or embed these rules in every Playwright-related prompt.**

---

## 1. Playwright Preamble (Every Prompt)

Every prompt must start with a line that tells Cursor **which file to write to** and **what base URL to use**. Without this, Cursor may create a new file or use the wrong URL.

**Template:**

```
Write this as a Playwright test in tests/e2e/<spec_file>.spec.ts. The app runs at <BASE_URL>.
```

**Examples by persona:**

- Persona 1 (Maya): `tests/e2e/persona1_maya.spec.ts` — `http://localhost:5173` or `https://test.mingusapp.com`
- Persona 2 (Marcus): `tests/e2e/persona2_marcus.spec.ts`
- Persona 3 (Jasmine): `tests/e2e/persona3_jasmine.spec.ts`
- Final verification: `tests/e2e/final_verification.spec.ts`

**Include the preamble even when appending to an existing spec** so Cursor knows the target file and can build correct `page.goto(BASE_URL)` or `page.goto(BASE_URL + '/some-path')` calls.

---

## 2. Specify the Actual URL or Selector for Every Navigation Step

Prompts like "Open the AI Replacement Risk Assessment" or "Return to the landing page" are ambiguous for Playwright. For each navigation step, do one of the following:

- **Option A — Direct URL:** Give the exact route, e.g.  
  `Navigate to http://localhost:5173/` or `Then go to /checkout`.
- **Option B — Explicit UI path:** Describe how to get there from the current page, e.g.  
  "The assessment is launched from the landing page via a button labeled **AI Replacement Risk** or **AI Replacement Risk Assessment** — use `page.getByRole('button', { name: /AI Replacement Risk/i })` and click it. Do not assume a route like `/assessments/ai-risk` unless that route exists."

**Landing page:** `page.goto(BASE_URL)` or `page.goto(BASE_URL + '/')`.  
**Checkout:** `page.goto(BASE_URL + '/checkout')`.  
**Signup (dedicated step):** `page.goto(BASE_URL + '/signup')` or navigate by clicking "Continue to Sign Up" from assessment results.

Always specify either the URL or the exact selector strategy (role, test id, or label) so Cursor does not guess.

---

## 3. Declare Input Types for Every Question

Assessment prompts include answer tables. Playwright code differs for **radio** vs **dropdown** vs **checkbox**. For every question, state the input type:

- **Single-select (one option):** "This question is a **radio group**. Select exactly one option by clicking the label or the radio; use `page.locator('label').filter({ hasText: /option text/i }).click()`."
- **Multi-select (e.g. "select both"):** "This question uses **checkboxes**. Select all indicated options; call `.click()` for each option (e.g. 'Financial stress' and 'My own emotional state') so both are checked."
- **Dropdown:** "This question is a **dropdown**. Use `page.getByRole('combobox').selectOption({ label: /option text/i })` or the appropriate select selector."

**Default rule to add to assessment prompts:**  
"Unless otherwise marked, all assessment questions are **single-select radio buttons**. Only questions explicitly marked '(select both)' or '(multi-select)' are checkboxes — for those, click each option in the list."

Example for Cuffing Season:  
"Financial stress, My own emotional state — **select both** (checkboxes). Click the label for 'Financial stress', then click the label for 'My own emotional state'."

---

## 4. Stripe iframe Handling (Payment / Sign-Up Prompts P1-F, P2-F, P3-F)

Prompts that say "Use test card 4242 4242 4242 4242" must state that **Stripe renders card inputs inside cross-origin iframes**. Standard `page.fill()` will not work. Add this instruction:

> The card number, expiry, CVV, and ZIP fields are inside **Stripe iframes**. Use `page.frameLocator()` to scope all card input interactions. Prefer title-based selectors first, then fall back to `iframe[name^="__privateStripeFrame"]` by index.
>
> - **Card number:**  
>   `page.frameLocator('iframe[title*="card number"], iframe[title*="Card number"]').first()` then `.locator('input[name="cardnumber"], input[name="number"]').fill('4242424242424242')`
> - **Expiry:**  
>   `page.frameLocator('iframe[title*="expiration"], iframe[title*="expiry"]').first()` then `.locator('input[name="exp-date"], input[name="expiry"]').fill('1228')`
> - **CVC:**  
>   `page.frameLocator('iframe[title*="CVC"], iframe[title*="cvc"]').first()` then `.locator('input[name="cvc"]').fill('123')`
> - **ZIP / Postal:**  
>   `page.frameLocator('iframe[title*="postal"], iframe[title*="Postal"]').first()` then `.locator('input[name="postal"], input[name="postalCode"]').fill('30032')`
>
> If title-based frames are not found, iterate over `page.locator('iframe[name^="__privateStripeFrame"]')` by index and use `page.frameLocator('iframe[name^="__privateStripeFrame"]').nth(i)` to find and fill each field. Wait for the payment form to be visible (e.g. Stripe iframes present) before filling.

Without this, payment steps will fail silently.

---

## 5. Explicit Wait Conditions After State Changes

After actions that change server or client state (submit assessment, sign-up, onboarding save, payment), **do not assert immediately**. Add explicit wait anchors so the test does not run assertions before the UI updates:

- **After clicking Submit / Complete Assessment:**  
  "Wait for the **result modal or result area** to be visible (e.g. text containing 'score', 'results', or a result dialog) before asserting the headline or score. Use `await expect(resultArea).toBeVisible({ timeout: 20000 })` or similar."
- **After completing sign-up (Create Account & Continue):**  
  "Wait for the **URL to change** to `/checkout` (or next step) before proceeding. Use `await expect(page).toHaveURL(/\/checkout/, { timeout: 15000 })`."
- **After payment (Pay now):**  
  "Wait for navigation or for the success/redirect state (e.g. URL contains `/checkout`, `/login`, or `/dashboard`) before asserting. Use a short `page.waitForTimeout(2000)` or `expect(page).toHaveURL(...)` with a timeout."

Add a line to each prompt that involves a state change:  
"**Wait condition:** [what to wait for] before [what to assert or do next]."

---

## 6. Convert Verification Checklists to Assertions

Prompts that use `[ ]` checkbox-style verification (e.g. P-H, FINAL) must be turned into **Playwright `expect()` assertions**, not manual checks or `console.log`. Cursor should generate failing tests when a condition is not met.

**Bad (manual):**  
"[ ] Savings rate shows negative (−5.4%) with alert styling"

**Good (assertion):**  
"Verify the savings rate element **contains** the text `−5.4%` (or `-5.4%`) and has an error/alert CSS class or red/warning styling. Use:  
`await expect(page.getByText(/-5\\.4%|−5\\.4%/)).toBeVisible();`  
and, if possible,  
`await expect(savingsRateLocator).toHaveClass(/error|alert|danger|text-red/);`  
or check computed color."

**Rule:** Every checklist item must be written as a verifiable condition with a specific `expect(...)` so that Cursor produces a hard failure, not an observation.

---

## 7. FINAL-B: Not Playwright — Use Unit Tests

**FINAL-B** asks to "run a scoring unit test against expected outputs." That is **algorithmic/unit testing**, not browser UI. It should **not** be implemented as a Playwright spec.

- **Remove FINAL-B from the Playwright prompt set** (or mark it as non-Playwright).
- **Add a note** for Cursor:  
  "Scoring consistency and expected-output checks belong in a **unit test** (e.g. Jest or Vitest), not in Playwright. Implement in `tests/unit/scoring.test.ts` (or the project’s unit test path). Reference this file when FINAL-B is requested."

Do not generate Playwright code for pure scoring logic.

---

## 8. FINAL-D: Viewport for 375px Spot Check

**FINAL-D** asks for a 375px viewport spot check. Tell Cursor how to set the viewport so the test is deterministic:

- "At the **start of each persona block** (or the mobile section of FINAL-D), set the viewport to mobile:  
  `await page.setViewportSize({ width: 375, height: 812 });`  
  Do this **before** navigating or performing the mobile steps."
- Optionally: "Use `page.setViewportSize({ width: 375, height: 812 })` in a `test.beforeEach` or at the top of the test that checks mobile layout."

---

## 9. beforeAll / afterAll and Database Cleanup

Persona transition notes ("clear session storage", "delete test cookies") must be expressed as **test hooks**, not prose. Add to each persona’s **final prompt** (or to a shared "Persona cleanup" section):

- **Clear browser state:**  
  "In `test.afterAll`, close the context and browser. If the next persona reuses the same file, ensure `test.beforeAll` starts with a fresh context and cleared cookies/storage so no session leaks between personas."

- **Database cleanup (test users):**  
  "After all tests for this persona pass, add an `afterAll` hook that cleans up test data created during the run. Prefer one of:
  1. **Test reset API:** If the app exposes a test-only endpoint (e.g. `POST /api/test/reset` or `DELETE /api/test/users/:email`), call it with the test user email.
  2. **Direct DB (only in test env):** If no API exists, run cleanup SQL via a Node helper, e.g. `child_process.execSync('psql $DATABASE_URL -c "DELETE FROM users WHERE email = \'maya.johnson.test@gmail.com\'"')` or the project’s DB runner — **only when running in a dedicated test environment**."

**Example instruction to add:**  
"After all tests for this persona, add `test.afterAll(async () => { ... })` that: (1) closes context and browser; (2) if applicable, calls the app’s test reset API or runs cleanup SQL to delete the test user (e.g. `DELETE FROM users WHERE email = '...'`). Document the cleanup method in a comment."

---

## Quick Reference

| # | Topic              | Action |
|---|--------------------|--------|
| 1 | Preamble           | Start every prompt with: "Write this as a Playwright test in tests/e2e/<file>.spec.ts. The app runs at <BASE_URL>." |
| 2 | Navigation         | For each step, give exact URL or selector (e.g. button/link label + `getByRole`/`getByTestId`). |
| 3 | Input types        | State "radio", "checkbox", or "dropdown" per question; add default: "All single-select unless marked (select both)." |
| 4 | Stripe             | Instruct: use `page.frameLocator('iframe[title*="..."]')` or `iframe[name^="__privateStripeFrame"]` for card/expiry/CVC/ZIP. |
| 5 | Waits              | After submit/sign-up/payment, add: "Wait for [element/URL] before asserting." |
| 6 | Checklists         | Turn every `[ ]` into an `expect(...)` assertion with a concrete locator and condition. |
| 7 | FINAL-B            | Exclude from Playwright; point to `tests/unit/scoring.test.ts`. |
| 8 | FINAL-D            | Add: "Set viewport with `page.setViewportSize({ width: 375, height: 812 })` before mobile steps." |
| 9 | Cleanup            | Add `afterAll` that closes context/browser and, if applicable, calls test reset API or cleanup SQL for test user. |
