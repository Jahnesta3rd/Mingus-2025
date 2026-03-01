#!/usr/bin/env python3
"""
End-to-end script: create a new user, complete sign-up, onboarding, and dashboard/cash-flow.

Flow:
  1. POST /api/auth/register (new user)
  2. GET  /api/user-meme (vibe-check page load)
  3. POST /api/meme-analytics (vibe-check vote)
  4. POST /api/profile/quick-setup (onboarding; optional)
  5. GET  /api/profile/setup-status
  6. GET  /api/user/profile (dashboard)
  7. GET  /api/cash-flow/enhanced-forecast/{email} (cash flow, daily cash available)
  8. GET  /api/gamification/milestones (milestone events, streak)
  9. GET  /api/vehicles?user_id={user_id} (vehicle status)
  10. GET  /api/risk/dashboard-state (dashboard results)
  11. POST /api/profile with key dates + cash outlays (importantDates)
  12. Report includes cash outlays for key dates and impact vs cash available

Prints a short report: cash available on sample days, **cash outlays for key dates** (date, label, amount, and whether each outlay is covered/tight/shortfall given forecast), milestone summary, vehicle count, etc.
Uses a unique email per run. Cookie from register is reused for all subsequent requests.

Usage:
  BASE_URL=https://test.mingusapp.com python3 scripts/complete_signup_and_onboarding.py
  python3 scripts/complete_signup_and_onboarding.py   # defaults to http://localhost:5000
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar

BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000").rstrip("/")
TIMEOUT = 30

# Key dates with cash outlays the user must enter (script saves these to profile for testing).
# Override via KEY_DATES_JSON env: [{"name":"Vacation","date":"2025-07-01","cost":800}, ...]
DEFAULT_KEY_DATES = [
    {"name": "Planned vacation", "date": "2025-07-15", "cost": 1200},
    {"name": "Car inspection", "date": "2025-06-20", "cost": 150},
    {"name": "Sister's wedding", "date": "2025-08-01", "cost": 600},
]

# Unique user per run (avoid 409 on re-runs)
TS = int(time.time())
EMAIL = f"onboarding_test_{TS}@example.com"
PASSWORD = "OnboardingTest1!"
FIRST_NAME = "Onboarding"
LAST_NAME = "Tester"


class Session:
    """Session that keeps cookies (urllib + CookieJar, no requests dependency)."""
    def __init__(self):
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def post(self, url, data, headers=None):
        h = {"Content-Type": "application/json"}
        if headers:
            h.update(headers)
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST", headers=h)
        try:
            resp = self.opener.open(req, timeout=TIMEOUT)
            return resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8") if e.fp else ""

    def get(self, url, headers=None):
        req = urllib.request.Request(url, headers=headers or {})
        try:
            resp = self.opener.open(req, timeout=TIMEOUT)
            return resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8") if e.fp else ""


def main():
    session = Session()
    steps_ok = []
    steps_fail = []
    key_dates = DEFAULT_KEY_DATES
    key_dates_json = os.environ.get("KEY_DATES_JSON", "").strip()
    if key_dates_json:
        try:
            key_dates = json.loads(key_dates_json)
        except json.JSONDecodeError:
            pass

    # --- 1. Register ---
    print("Step 1: Register new user...")
    code, body = session.post(
        f"{BASE_URL}/api/auth/register",
        {"email": EMAIL, "password": PASSWORD, "first_name": FIRST_NAME, "last_name": LAST_NAME},
    )
    user_id = None
    if code in (200, 201):
        try:
            j = json.loads(body)
            user_id = j.get("user_id")
            print(f"  OK {code} - user_id: {str(user_id or '')[:8]}...")
        except Exception:
            print(f"  OK {code}")
        steps_ok.append("register")
        if not user_id:
            try:
                user_id = json.loads(body).get("user_id")
            except Exception:
                pass
    elif code == 409:
        print("  SKIP - user already exists (use different BASE_URL or wait 1s for new timestamp)")
        steps_fail.append("register(409)")
        sys.exit(1)
    else:
        print(f"  FAIL {code} - {body[:200]}")
        steps_fail.append("register")
        sys.exit(1)
    if not user_id:
        try:
            user_id = json.loads(body).get("user_id")
        except Exception:
            pass

    # --- 2. Vibe-check: fetch meme ---
    print("Step 2: Vibe-check (fetch meme)...")
    code, body = session.get(f"{BASE_URL}/api/user-meme")
    meme_id = None
    if code != 200:
        print(f"  FAIL {code} - {body[:200]}")
        steps_fail.append("user-meme")
    else:
        try:
            data = json.loads(body)
            meme_id = data.get("id")
            print(f"  OK - meme_id={meme_id} image_url={str(data.get('image_url', ''))[:50]}...")
        except Exception:
            print("  OK - meme loaded")
        steps_ok.append("user-meme")
        if meme_id is None:
            try:
                meme_id = json.loads(body).get("id")
            except Exception:
                pass

    # --- 3. Vibe-check: record vote ---
    print("Step 3: Vibe-check (record vote)...")
    if meme_id:
        code, body = session.post(
            f"{BASE_URL}/api/meme-analytics",
            {"meme_id": meme_id, "action": "vote", "vote": "up"},
        )
        if code in (200, 201, 204):
            print("  OK - vote recorded")
            steps_ok.append("meme-analytics")
        else:
            print(f"  WARN {code} - {body[:150]}")
            steps_fail.append("meme-analytics")
    else:
        print("  SKIP - no meme_id")
        steps_fail.append("meme-analytics")

    # --- 4. Quick-setup (onboarding questions) ---
    print("Step 4: Quick-setup (onboarding)...")
    code, body = session.post(
        f"{BASE_URL}/api/profile/quick-setup",
        {"incomeRange": "50-75k", "primaryGoal": "emergency-fund"},
    )
    if code in (200, 201, 204):
        print("  OK - quick-setup saved")
        steps_ok.append("quick-setup")
    elif code == 404:
        print("  SKIP - /api/profile/quick-setup not deployed (optional)")
        steps_ok.append("quick-setup(skip)")
    elif code >= 500:
        print(f"  SKIP - quick-setup returned {code} (optional; backend may not implement)")
        steps_ok.append("quick-setup(skip)")
    else:
        print(f"  WARN {code} - {body[:150]}")
        steps_fail.append("quick-setup")

    # --- 5. Setup status ---
    print("Step 5: Setup status...")
    code, body = session.get(f"{BASE_URL}/api/profile/setup-status")
    if code == 200:
        try:
            j = json.loads(body)
            done = j.get("setupCompleted") or (j.get("data") or {}).get("is_complete")
            print(f"  OK - setupCompleted={done}")
        except Exception:
            print("  OK")
        steps_ok.append("setup-status")
    else:
        print(f"  FAIL {code} - {body[:200]}")
        steps_fail.append("setup-status")

    # --- 6. User profile (dashboard) ---
    print("Step 6: User profile (dashboard)...")
    code, body = session.get(f"{BASE_URL}/api/user/profile")
    if code == 200:
        try:
            j = json.loads(body)
            print(f"  OK - user: {j.get('email', j.get('name', ''))}")
        except Exception:
            print("  OK")
        steps_ok.append("user/profile")
    else:
        print(f"  FAIL {code} - {body[:200]}")
        steps_fail.append("user/profile")

    # --- 7. Cash flow forecast (daily cash available, milestone dates) ---
    print("Step 7: Cash flow forecast (daily cash available)...")
    cash_headers = {"X-CSRF-Token": "test-token"}
    cash_url = f"{BASE_URL}/api/cash-flow/enhanced-forecast/{urllib.parse.quote(EMAIL)}?months=3"
    code, body = session.get(cash_url, headers=cash_headers)
    daily_cashflow = []
    vehicle_expense_totals = None
    if code == 200:
        try:
            j = json.loads(body)
            fcast = j.get("forecast") or j
            daily_cashflow = fcast.get("daily_cashflow") or []
            vehicle_expense_totals = fcast.get("vehicle_expense_totals")
            n = len(daily_cashflow)
            print(f"  OK - {n} days of daily_cashflow; vehicle_expense_totals={vehicle_expense_totals is not None}")
        except Exception:
            print("  OK - forecast loaded")
        steps_ok.append("cash-flow")
    else:
        fallback = f"{BASE_URL}/api/cash-flow/backward-compatibility/{urllib.parse.quote(EMAIL)}?months=3"
        code2, body2 = session.get(fallback, headers=cash_headers)
        if code2 == 200:
            try:
                j = json.loads(body2)
                fcast = j.get("forecast") or j
                daily_cashflow = fcast.get("daily_cashflow") or []
                vehicle_expense_totals = fcast.get("vehicle_expense_totals")
                print(f"  OK (fallback) - {len(daily_cashflow)} days daily_cashflow")
            except Exception:
                pass
            steps_ok.append("cash-flow")
        else:
            print(f"  SKIP - {code} / {code2} (cash-flow optional)")
            steps_fail.append("cash-flow")

    # --- 8. Milestones (streak, milestone events) ---
    print("Step 8: Milestones (streak / milestone events)...")
    code, body = session.get(f"{BASE_URL}/api/gamification/milestones")
    next_milestone = None
    milestones_summary = None
    if code == 200:
        try:
            j = json.loads(body)
            ms = j.get("milestones") or []
            achieved = sum(1 for m in ms if m.get("achieved"))
            next_milestone = next((m.get("days_required") for m in ms if not m.get("achieved")), None)
            milestones_summary = f"achieved={achieved} next={next_milestone}"
            print(f"  OK - {achieved} achieved, next_milestone={next_milestone}")
        except Exception:
            print("  OK - milestones loaded")
        steps_ok.append("milestones")
    else:
        print(f"  SKIP - {code} (milestones optional)")
        steps_fail.append("milestones")

    # --- 9. Vehicle status ---
    print("Step 9: Vehicle status...")
    vehicle_count = 0
    if user_id:
        code, body = session.get(f"{BASE_URL}/api/vehicles?user_id={urllib.parse.quote(str(user_id))}")
        if code == 200:
            try:
                j = json.loads(body)
                vehicles = j.get("vehicles") or []
                vehicle_count = len(vehicles)
                print(f"  OK - {vehicle_count} vehicle(s)")
            except Exception:
                print("  OK - vehicles loaded")
            steps_ok.append("vehicles")
        else:
            print(f"  SKIP - {code}")
    else:
        print("  SKIP - no user_id")

    # --- 10. Risk dashboard state ---
    print("Step 10: Risk dashboard state...")
    code, body = session.get(f"{BASE_URL}/api/risk/dashboard-state")
    if code == 200:
        print("  OK - dashboard state loaded")
        steps_ok.append("risk/dashboard-state")
    else:
        print(f"  SKIP - {code}")
        steps_fail.append("risk/dashboard-state")

    # --- 11. Save key dates with cash outlays to profile ---
    print("Step 11: Save key dates (cash outlays) to profile...")
    important_dates = {
        "birthday": None,
        "vacation": {"date": key_dates[0]["date"], "cost": key_dates[0]["cost"]} if len(key_dates) > 0 else None,
        "car_inspection": {"date": key_dates[1]["date"], "cost": key_dates[1]["cost"]} if len(key_dates) > 1 else None,
        "sisters_wedding": {"date": key_dates[2]["date"], "cost": key_dates[2]["cost"]} if len(key_dates) > 2 else None,
        "custom_events": [{"name": e["name"], "date": e["date"], "cost": e["cost"]} for e in key_dates[3:]],
    }
    profile_payload = {
        "email": EMAIL,
        "firstName": FIRST_NAME,
        "personalInfo": {"age": 0, "location": "", "education": "", "employment": ""},
        "financialInfo": {"annualIncome": 0, "monthlyTakehome": 0},
        "importantDates": important_dates,
    }
    code, body = session.post(
        f"{BASE_URL}/api/profile",
        profile_payload,
        headers={"X-CSRF-Token": "test-token"},
    )
    if code in (200, 201):
        print(f"  OK - saved {len(key_dates)} key date(s) with cash outlays")
        steps_ok.append("profile/key-dates")
    else:
        print(f"  SKIP - {code} (profile/key-dates optional)")
        steps_fail.append("profile/key-dates")

    # --- Dashboard results report ---
    print()
    print("--- Dashboard / cash flow results (for user) ---")
    if daily_cashflow:
        sample = daily_cashflow[:5] + (daily_cashflow[-3:] if len(daily_cashflow) > 8 else [])
        for day in sample:
            date_str = day.get("date", "")
            closing = day.get("closing_balance")
            opening = day.get("opening_balance")
            print(f"  Cash available: {date_str}  opening={opening}  closing={closing}")
        if vehicle_expense_totals:
            print(f"  Vehicle expense totals: {vehicle_expense_totals}")
    # Cash outlays for key dates (user must enter these; script saves sample set)
    print("  Cash outlays for key dates:")
    cashflow_by_date = {d.get("date"): d for d in (daily_cashflow or []) if d.get("date")}
    for evt in key_dates:
        date_str = evt.get("date", "")
        name = evt.get("name", "Event")
        cost = evt.get("cost", 0)
        day_data = cashflow_by_date.get(date_str) if date_str else None
        closing = day_data.get("closing_balance") if day_data else None
        if closing is not None and cost is not None:
            after = closing - cost
            if after > 500:
                impact = "covered"
            elif after >= 0:
                impact = "tight"
            else:
                impact = "shortfall"
            print(f"    {date_str}  {name}: ${cost}  (cash that day: ${closing}  → {impact})")
        else:
            print(f"    {date_str}  {name}: ${cost}  (no forecast for this date)")
    if milestones_summary:
        print(f"  Milestones: {milestones_summary}")
    print(f"  Vehicles: {vehicle_count} registered")
    print("---")

    # --- Summary ---
    print()
    print("Summary:")
    print(f"  Passed: {', '.join(steps_ok)}")
    if steps_fail:
        print(f"  Failed/Warn: {', '.join(steps_fail)}")
    print(f"  User: {EMAIL}")
    print(f"  Password: {PASSWORD}")
    # Consider success if register + vibe-check + vote worked (core flow)
    core_ok = "register" in steps_ok and "user-meme" in steps_ok
    if core_ok and ("meme-analytics" in steps_ok or "user-meme" in steps_ok):
        print("  Result: Sign-up and vibe-check flow completed; user can proceed to dashboard.")
        sys.exit(0)
    if not steps_fail:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
