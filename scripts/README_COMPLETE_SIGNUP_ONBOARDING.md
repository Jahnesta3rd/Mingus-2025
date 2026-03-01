# Complete Sign-Up and Onboarding Script

`complete_signup_and_onboarding.py` runs an end-to-end flow as a new user: **sign up**, **vibe-check**, **onboarding**, and **dashboard/cash-flow components** (cash available on days, milestone events, vehicle status, risk dashboard).

## What it does

1. **Register** – `POST /api/auth/register` with a unique email (`onboarding_test_<timestamp>@example.com`), password, first and last name. Uses the returned cookie for later requests.
2. **Vibe-check (meme)** – `GET /api/user-meme` to load the meme shown on the vibe-check page.
3. **Vibe-check (vote)** – `POST /api/meme-analytics` with `action: vote`, `vote: up` to simulate the user voting.
4. **Quick-setup (onboarding)** – `POST /api/profile/quick-setup` with income range and primary goal. Skipped if 404 or 5xx (optional).
5. **Setup status** – `GET /api/profile/setup-status` to confirm onboarding completion.
6. **User profile** – `GET /api/user/profile` to confirm dashboard access.
7. **Cash flow forecast** – `GET /api/cash-flow/enhanced-forecast/{email}?months=3` (or backward-compatibility). Produces **daily cash available** (opening/closing balance by date) and **vehicle expense totals** for the dashboard.
8. **Milestones** – `GET /api/gamification/milestones` for **milestone events**, streak, and next milestone (spending/wellness milestones).
9. **Vehicle status** – `GET /api/vehicles?user_id={user_id}` for **vehicle count** and status.
10. **Risk dashboard state** – `GET /api/risk/dashboard-state` for **dashboard results**.
11. **Key dates (cash outlays)** – `POST /api/profile` with **importantDates** containing key dates and cash outlays the user must enter (e.g. vacation, car inspection, custom events). The script saves a default set of 3 key dates with outlays; you can override via **KEY_DATES_JSON** (see below).

The script prints a short **dashboard results report** that includes:
- Sample dates with **cash available** (opening/closing balance).
- **Cash outlays for key dates**: for each key date, the **date**, **label**, **amount**, and (when forecast is available) **cash that day** and whether the outlay is **covered** / **tight** / **shortfall**.
- Vehicle expense totals, milestones summary, and vehicle count.

The script uses only the Python standard library (`urllib`, `http.cookiejar`, `json`); no `requests` required.

## Usage

```bash
# Default: http://localhost:5000 (run backend locally)
python3 scripts/complete_signup_and_onboarding.py

# Against test deployment
BASE_URL=https://test.mingusapp.com python3 scripts/complete_signup_and_onboarding.py

# With custom key dates (cash outlays). JSON array: [{"name":"...","date":"YYYY-MM-DD","cost":number}, ...]
KEY_DATES_JSON='[{"name":"Vacation","date":"2025-08-01","cost":1500},{"name":"Car repair","date":"2025-07-15","cost":400}]' \
  BASE_URL=https://test.mingusapp.com python3 scripts/complete_signup_and_onboarding.py
```

## Output

- Each step prints OK / FAIL / SKIP / WARN.
- **Dashboard / cash flow results** section:
  - **Cash available** – For sample dates (first few and last few days of the forecast), opening and closing balance so the user can see cash on milestone/event days.
  - **Cash outlays for key dates** – For each key date the user must enter (or the script saves as sample): **date**, **label**, **cash outlay amount**; when daily forecast exists, **cash available that day** and whether the outlay is **covered**, **tight**, or **shortfall**.
  - **Vehicle expense totals** – If returned by the cash-flow API (total, routine, repair).
  - **Milestones** – Achieved count and next milestone (e.g. streak days).
  - **Vehicles** – Number of vehicles registered for the user.
- At the end, the script prints the **user email** and **password** used so you can log in in the app and confirm the flow in the UI.
- Exit code **0** if the core flow (register + vibe-check meme + vote) succeeded; **1** otherwise.

## Notes

- **Unique user per run** – Email includes a timestamp, so repeated runs create new users (avoid 409 on re-runs).
- **Cookies** – The script keeps cookies in a `CookieJar` and sends them on every request to the same host. If you see 401 on steps 5–6 after a successful register/vibe-check, the cookie may not be sent or accepted for those paths (e.g. proxy or auth configuration).
- **Quick-setup** – The `/api/profile/quick-setup` route may not be registered on all deployments; 404 or 5xx is treated as “skip” and does not fail the run.
- **Onboarding** – “Onboarding” here means: account creation, vibe-check (meme + vote), and (when available) quick-setup and setup-status. The script does not drive the full 6-step profile or assessment UI; it exercises the APIs that back the main sign-up and vibe-check flow.
- **Key dates and cash outlays** – The app expects the user to enter key dates (e.g. vacation, car inspection, wedding) with a cash outlay amount. The script saves a default set of three key dates with sample costs; the report shows cash outlays for key dates and impact (covered/tight/shortfall). Override with KEY_DATES_JSON.
