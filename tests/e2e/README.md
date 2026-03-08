# E2E Playwright tests

Persona specs: `persona1_maya.spec.ts`, `persona2_marcus.spec.ts`, `persona3_jasmine.spec.ts`.  
Final verification: `final_verification.spec.ts`.

**Backend test mode (recommended for full suite):** To avoid assessment-email failures affecting the suite, run the backend with email skipped in test mode. Set one of:

- `FLASK_ENV=testing`
- `TESTING=1` or `TESTING=true`

Then start the app (e.g. gunicorn or `python app.py`). The assessment API will still return 201 and results but will not send the results email, so the whole suite and future tests (e.g. dashboard with persona data) run reliably.

**When writing or editing tests from prompts**, follow **[PLAYWRIGHT_CURSOR_PROMPT_GUIDELINES.md](./PLAYWRIGHT_CURSOR_PROMPT_GUIDELINES.md)** so that:

- Every prompt includes the Playwright preamble (target spec file + base URL).
- Navigation uses explicit URLs or selectors; assessment question types (radio/checkbox/dropdown) are declared.
- Stripe payment steps use iframe-scoped locators.
- Waits and assertions are explicit; verification checklists become `expect()` assertions.
- FINAL-B stays in unit tests; FINAL-D sets viewport; cleanup uses `afterAll` and test reset/DB cleanup where applicable.
