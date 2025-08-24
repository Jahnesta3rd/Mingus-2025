#!/usr/bin/env python3
"""
MINGUS Application - End-to-End Testing Suite
============================================

- Simulates real user workflows and validates all features with PostgreSQL
- Covers registration, onboarding, subscription, health, financial, career, admin, and API
- Includes browser automation (Selenium) for UI flows
- Includes performance/load testing for realistic user scenarios
- Produces a detailed pass/fail report for each scenario

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import time
import json
import logging
import requests
import traceback
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Optional: Selenium for browser automation
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5002/api')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
REPORT_FILE = 'e2e_test_report.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('E2ETest')

@dataclass
class E2EResult:
    scenario: str
    step: str
    passed: bool
    details: Any = None
    error: Optional[str] = None
    duration: Optional[float] = None

class MingusE2ETestSuite:
    def __init__(self, api_base: str, frontend_url: str):
        self.api_base = api_base
        self.frontend_url = frontend_url
        self.results: List[E2EResult] = []
        self.session = requests.Session()

    def run(self):
        self.run_scenario(self.new_user_registration_and_onboarding)
        self.run_scenario(self.subscription_tier_selection_and_payment)
        self.run_scenario(self.health_data_entry_and_insights)
        self.run_scenario(self.financial_goal_setting_and_tracking)
        self.run_scenario(self.career_advancement_features)
        self.run_scenario(self.administrative_functions)
        self.run_scenario(self.api_endpoint_tests)
        if SELENIUM_AVAILABLE:
            self.run_scenario(self.browser_automation_tests)
        self.run_scenario(self.performance_under_load)
        self.generate_report()

    def run_scenario(self, scenario_func):
        scenario = scenario_func.__name__.replace('_', ' ').title()
        logger.info(f"Running scenario: {scenario}")
        for result in scenario_func():
            self.results.append(result)
            status = '✅' if result.passed else '❌'
            logger.info(f"{status} {result.scenario} - {result.step}")
            if not result.passed and result.error:
                logger.error(f"    Error: {result.error}")

    # -------------------
    # SCENARIOS
    # -------------------
    def new_user_registration_and_onboarding(self) -> List[E2EResult]:
        results = []
        try:
            start = time.time()
            email = f"e2e_{int(time.time())}@mingus.com"
            password = "Test1234!"
            # Register
            r = self.session.post(f"{self.api_base}/auth/register", json={
                'email': email,
                'password': password,
                'first_name': 'E2E',
                'last_name': 'User',
                'zip_code': '12345'
            }, timeout=5)
            reg_ok = r.status_code in (200, 201)
            results.append(E2EResult('Registration/Onboarding', 'Register', reg_ok, {'status': r.status_code}, None if reg_ok else r.text, time.time()-start))
            # Login
            l = self.session.post(f"{self.api_base}/auth/login", json={
                'email': email,
                'password': password
            }, timeout=5)
            login_ok = l.status_code == 200 and 'access_token' in l.json()
            token = l.json().get('access_token') if login_ok else None
            results.append(E2EResult('Registration/Onboarding', 'Login', login_ok, {'status': l.status_code}, None if login_ok else l.text, time.time()-start))
            # Onboarding (simulate step completion)
            if token:
                headers = {'Authorization': f'Bearer {token}'}
                r = self.session.post(f"{self.api_base}/onboarding/complete", headers=headers, timeout=5)
                onboard_ok = r.status_code in (200, 201)
                results.append(E2EResult('Registration/Onboarding', 'Onboarding Complete', onboard_ok, {'status': r.status_code}, None if onboard_ok else r.text, time.time()-start))
        except Exception as e:
            results.append(E2EResult('Registration/Onboarding', 'Exception', False, None, traceback.format_exc()))
        return results

    def subscription_tier_selection_and_payment(self) -> List[E2EResult]:
        results = []
        try:
            start = time.time()
            # Simulate selecting a tier and payment (mocked)
            r = self.session.post(f"{self.api_base}/subscription/select", json={
                'plan': 'Professional',
                'payment_token': 'tok_test_visa'  # Simulated
            }, timeout=5)
            ok = r.status_code in (200, 201)
            results.append(E2EResult('Subscription', 'Tier Selection & Payment', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
        except Exception as e:
            results.append(E2EResult('Subscription', 'Exception', False, None, traceback.format_exc()))
        return results

    def health_data_entry_and_insights(self) -> List[E2EResult]:
        results = []
        try:
            start = time.time()
            r = self.session.post(f"{self.api_base}/health/checkin", json={
                'mood_score': 8,
                'stress_level': 4,
                'sleep_hours': 7.0,
                'exercise_minutes': 20
            }, timeout=5)
            ok = r.status_code in (200, 201)
            results.append(E2EResult('Health', 'Checkin', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
            # Insights
            r = self.session.get(f"{self.api_base}/health/insights", timeout=5)
            ok = r.status_code == 200 and 'insights' in r.json()
            results.append(E2EResult('Health', 'Insights', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
        except Exception as e:
            results.append(E2EResult('Health', 'Exception', False, None, traceback.format_exc()))
        return results

    def financial_goal_setting_and_tracking(self) -> List[E2EResult]:
        results = []
        try:
            start = time.time()
            # Set goal
            r = self.session.post(f"{self.api_base}/financial/goal", json={
                'goal_type': 'savings',
                'amount': 10000,
                'target_date': '2025-12-31'
            }, timeout=5)
            ok = r.status_code in (200, 201)
            results.append(E2EResult('Financial', 'Set Goal', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
            # Track progress
            r = self.session.get(f"{self.api_base}/financial/progress", timeout=5)
            ok = r.status_code == 200 and 'progress' in r.json()
            results.append(E2EResult('Financial', 'Track Progress', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
            # Forecast
            r = self.session.get(f"{self.api_base}/financial/forecast", timeout=5)
            ok = r.status_code == 200 and 'forecast' in r.json()
            results.append(E2EResult('Financial', 'Forecast', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
        except Exception as e:
            results.append(E2EResult('Financial', 'Exception', False, None, traceback.format_exc()))
        return results

    def career_advancement_features(self) -> List[E2EResult]:
        results = []
        try:
            start = time.time()
            # Income comparison lead magnet
            r = self.session.post(f"{self.api_base}/income-analysis/analyze", json={
                'age_range': '25-27',
                'race': 'African American',
                'education_level': 'Bachelors',
                'location': 'Atlanta',
                'salary': 85000,
                'industry': 'Technology',
                'years_experience': '6-10'
            }, timeout=5)
            ok = r.status_code == 200 and 'results' in r.json()
            results.append(E2EResult('Career', 'Income Comparison', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
            # Job matching (mocked)
            r = self.session.get(f"{self.api_base}/career/match", timeout=5)
            ok = r.status_code == 200 and 'matches' in r.json()
            results.append(E2EResult('Career', 'Job Matching', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
        except Exception as e:
            results.append(E2EResult('Career', 'Exception', False, None, traceback.format_exc()))
        return results

    def administrative_functions(self) -> List[E2EResult]:
        results = []
        try:
            start = time.time()
            # Admin login (assume admin credentials are set in env)
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@mingus.com')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin_password_change_in_production')
            l = self.session.post(f"{self.api_base}/auth/login", json={
                'email': admin_email,
                'password': admin_password
            }, timeout=5)
            login_ok = l.status_code == 200 and 'access_token' in l.json()
            results.append(E2EResult('Admin', 'Admin Login', login_ok, {'status': l.status_code}, None if login_ok else l.text, time.time()-start))
            # Admin dashboard (mocked)
            if login_ok:
                token = l.json().get('access_token')
                headers = {'Authorization': f'Bearer {token}'}
                r = self.session.get(f"{self.api_base}/admin/dashboard", headers=headers, timeout=5)
                ok = r.status_code == 200
                results.append(E2EResult('Admin', 'Dashboard Access', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
        except Exception as e:
            results.append(E2EResult('Admin', 'Exception', False, None, traceback.format_exc()))
        return results

    def api_endpoint_tests(self) -> List[E2EResult]:
        results = []
        endpoints = [
            ('GET', '/auth/check-auth'),
            ('GET', '/financial/summary'),
            ('GET', '/health/summary'),
            ('GET', '/subscription/status'),
            ('GET', '/feature-access/list'),
        ]
        for method, path in endpoints:
            try:
                start = time.time()
                url = f"{self.api_base}{path}"
                r = self.session.request(method, url, timeout=5)
                ok = r.status_code == 200
                results.append(E2EResult('API', f'{method} {path}', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
            except Exception as e:
                results.append(E2EResult('API', f'{method} {path}', False, None, traceback.format_exc()))
        return results

    def browser_automation_tests(self) -> List[E2EResult]:
        if not SELENIUM_AVAILABLE:
            return []
        results = []
        try:
            start = time.time()
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.frontend_url)
            # Simulate registration flow
            driver.find_element(By.NAME, 'email').send_keys(f"e2e_{int(time.time())}@mingus.com")
            driver.find_element(By.NAME, 'password').send_keys('Test1234!')
            driver.find_element(By.NAME, 'register').click()
            time.sleep(2)
            ok = 'dashboard' in driver.current_url
            results.append(E2EResult('Browser', 'Registration Flow', ok, {'url': driver.current_url}, None if ok else 'Registration failed', time.time()-start))
            driver.quit()
        except Exception as e:
            results.append(E2EResult('Browser', 'Exception', False, None, traceback.format_exc()))
        return results

    def performance_under_load(self) -> List[E2EResult]:
        results = []
        def user_flow():
            try:
                email = f"load_{int(time.time())}_{os.getpid()}@mingus.com"
                password = "Test1234!"
                self.session.post(f"{self.api_base}/auth/register", json={
                    'email': email,
                    'password': password,
                    'first_name': 'Load',
                    'last_name': 'Test',
                    'zip_code': '12345'
                }, timeout=5)
                l = self.session.post(f"{self.api_base}/auth/login", json={
                    'email': email,
                    'password': password
                }, timeout=5)
                return l.status_code == 200
            except Exception:
                return False
        start = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(user_flow) for _ in range(20)]
            results_ok = sum(1 for f in as_completed(futures) if f.result())
        duration = time.time() - start
        results.append(E2EResult('Performance', '20 Concurrent User Flows', results_ok == 20, {'success': results_ok}, None if results_ok == 20 else f"{results_ok}/20 succeeded", duration))
        return results

    def generate_report(self):
        # Group by scenario
        report = {'summary': {}, 'results': []}
        scenarios = set(r.scenario for r in self.results)
        for sc in scenarios:
            sc_results = [r for r in self.results if r.scenario == sc]
            passed = sum(1 for r in sc_results if r.passed)
            failed = sum(1 for r in sc_results if not r.passed)
            report['summary'][sc] = {'passed': passed, 'failed': failed, 'total': len(sc_results)}
        report['results'] = [r.__dict__ for r in self.results]
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2)
        print("\n=== E2E TEST SUMMARY ===")
        for sc, s in report['summary'].items():
            status = '✅' if s['failed'] == 0 else '❌'
            print(f"{status} {sc}: {s['passed']}/{s['total']} passed, {s['failed']} failed")
        if any(s['failed'] for s in report['summary'].values()):
            print(f"\n❌ Some tests failed. See {REPORT_FILE} for details.")
        else:
            print(f"\n✅ All tests passed! See {REPORT_FILE} for details.")


def main():
    suite = MingusE2ETestSuite(API_BASE_URL, FRONTEND_URL)
    suite.run()

if __name__ == "__main__":
    main() 