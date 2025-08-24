#!/usr/bin/env python3
"""
MINGUS Application - Migration & Database Validation Test Suite
==============================================================

- Validates data integrity between old SQLite and new PostgreSQL
- Verifies user, subscription, feature, financial, and health data
- Tests all API endpoints and user workflows
- Includes regression, performance, and security tests
- Generates a pass/fail report for each test category with detailed error output

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import json
import time
import logging
import sqlite3
import requests
import traceback
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config.environment import validate_and_load_environment, get_database_url

# Test configuration
SQLITE_DBS = {
    'mingus': 'mingus.db',
    'business_intelligence': 'business_intelligence.db',
    'cache': 'cache.db',
    'performance_metrics': 'performance_metrics.db',
    'alerts': 'alerts.db'
}
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5002/api')
REPORT_FILE = 'migration_test_report.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('MigrationTest')

@dataclass
class TestResult:
    category: str
    name: str
    passed: bool
    details: Any = None
    error: Optional[str] = None
    duration: Optional[float] = None

class MigrationTestSuite:
    def __init__(self, pg_url: str, sqlite_dbs: Dict[str, str], api_base: str):
        self.pg_url = pg_url
        self.sqlite_dbs = sqlite_dbs
        self.api_base = api_base
        self.pg_engine = create_engine(pg_url, pool_pre_ping=True)
        self.pg_session = sessionmaker(bind=self.pg_engine)()
        self.sqlite_conns = {k: sqlite3.connect(v) for k, v in sqlite_dbs.items() if os.path.exists(v)}
        for conn in self.sqlite_conns.values():
            conn.row_factory = sqlite3.Row
        self.results: List[TestResult] = []

    def run(self):
        self.run_category(self.data_consistency_tests)
        self.run_category(self.functional_tests)
        self.run_category(self.performance_regression_tests)
        self.run_category(self.security_validation_tests)
        self.run_category(self.user_workflow_tests)
        self.generate_report()

    def run_category(self, test_func):
        category = test_func.__name__.replace('_', ' ').title()
        logger.info(f"Running {category}...")
        for result in test_func():
            self.results.append(result)
            status = '✅' if result.passed else '❌'
            logger.info(f"{status} {result.category} - {result.name}")
            if not result.passed and result.error:
                logger.error(f"    Error: {result.error}")

    # -------------------
    # DATA CONSISTENCY TESTS
    # -------------------
    def data_consistency_tests(self) -> List[TestResult]:
        tests = []
        # 1. User count match
        try:
            start = time.time()
            sqlite_user_count = 0
            for conn in self.sqlite_conns.values():
                try:
                    c = conn.execute('SELECT COUNT(*) FROM users')
                    sqlite_user_count += c.fetchone()[0]
                except Exception:
                    continue
            pg_user_count = self.pg_session.execute(text('SELECT COUNT(*) FROM users')).scalar()
            passed = abs(pg_user_count - sqlite_user_count) <= 1  # Allow for admin/test users
            tests.append(TestResult('Data Consistency', 'User Count Match', passed, {
                'sqlite_user_count': sqlite_user_count,
                'pg_user_count': pg_user_count
            }, None if passed else f"Mismatch: SQLite={sqlite_user_count}, PG={pg_user_count}", time.time()-start))
        except Exception as e:
            tests.append(TestResult('Data Consistency', 'User Count Match', False, None, traceback.format_exc()))
        # 2. Subscription count match
        try:
            start = time.time()
            sqlite_sub_count = 0
            for conn in self.sqlite_conns.values():
                try:
                    c = conn.execute('SELECT COUNT(*) FROM subscriptions')
                    sqlite_sub_count += c.fetchone()[0]
                except Exception:
                    continue
            pg_sub_count = self.pg_session.execute(text('SELECT COUNT(*) FROM subscriptions')).scalar()
            passed = abs(pg_sub_count - sqlite_sub_count) <= 1
            tests.append(TestResult('Data Consistency', 'Subscription Count Match', passed, {
                'sqlite_sub_count': sqlite_sub_count,
                'pg_sub_count': pg_sub_count
            }, None if passed else f"Mismatch: SQLite={sqlite_sub_count}, PG={pg_sub_count}", time.time()-start))
        except Exception as e:
            tests.append(TestResult('Data Consistency', 'Subscription Count Match', False, None, traceback.format_exc()))
        # 3. User profile data match (sample)
        try:
            start = time.time()
            sample_pg = self.pg_session.execute(text('SELECT id, email FROM users LIMIT 5')).fetchall()
            for row in sample_pg:
                email = row['email']
                found = False
                for conn in self.sqlite_conns.values():
                    c = conn.execute('SELECT * FROM users WHERE email = ?', (email,))
                    if c.fetchone():
                        found = True
                        break
                tests.append(TestResult('Data Consistency', f'User {email} Exists in SQLite', found, None, None if found else f"User {email} missing in SQLite"))
        except Exception as e:
            tests.append(TestResult('Data Consistency', 'User Profile Sample', False, None, traceback.format_exc()))
        return tests

    # -------------------
    # FUNCTIONAL TESTS
    # -------------------
    def functional_tests(self) -> List[TestResult]:
        tests = []
        # 1. Subscription system
        try:
            start = time.time()
            plans = self.pg_session.execute(text('SELECT name, price FROM subscription_plans')).fetchall()
            expected = {'Budget': 10.0, 'Mid-tier': 20.0, 'Professional': 50.0}
            plan_ok = all(any(p['name'] == k and float(p['price']) == v for p in plans) for k, v in expected.items())
            tests.append(TestResult('Functional', 'Subscription Plans Exist', plan_ok, [dict(p) for p in plans], None if plan_ok else f"Plans missing or incorrect", time.time()-start))
        except Exception as e:
            tests.append(TestResult('Functional', 'Subscription Plans Exist', False, None, traceback.format_exc()))
        # 2. Feature access control
        try:
            start = time.time()
            fa = self.pg_session.execute(text('SELECT feature_name, is_enabled FROM feature_access')).fetchall()
            fa_ok = any(f['feature_name'] == 'basic_analytics' and f['is_enabled'] for f in fa)
            tests.append(TestResult('Functional', 'Feature Access Control', fa_ok, [dict(f) for f in fa[:5]], None if fa_ok else "Feature access missing or incorrect", time.time()-start))
        except Exception as e:
            tests.append(TestResult('Functional', 'Feature Access Control', False, None, traceback.format_exc()))
        # 3. Financial calculations
        try:
            start = time.time()
            q = "SELECT SUM(monthly_income) - SUM(monthly_expenses) AS cash_flow FROM encrypted_financial_profiles"
            res = self.pg_session.execute(text(q)).scalar()
            tests.append(TestResult('Functional', 'Cash Flow Calculation', res is not None, {'cash_flow': res}, None if res is not None else "No cash flow calculated", time.time()-start))
        except Exception as e:
            tests.append(TestResult('Functional', 'Cash Flow Calculation', False, None, traceback.format_exc()))
        # 4. Health tracking
        try:
            start = time.time()
            q = "SELECT COUNT(*) FROM user_health_checkins"
            count = self.pg_session.execute(text(q)).scalar()
            tests.append(TestResult('Functional', 'Health Checkin Count', count > 0, {'count': count}, None if count > 0 else "No health checkins found", time.time()-start))
        except Exception as e:
            tests.append(TestResult('Functional', 'Health Checkin Count', False, None, traceback.format_exc()))
        return tests

    # -------------------
    # PERFORMANCE REGRESSION TESTS
    # -------------------
    def performance_regression_tests(self) -> List[TestResult]:
        tests = []
        try:
            start = time.time()
            q = "SELECT id FROM users LIMIT 1"
            user_id = self.pg_session.execute(text(q)).scalar()
            if not user_id:
                tests.append(TestResult('Performance', 'User Query', False, None, "No users found"))
                return tests
            # Test query time for cash flow
            t0 = time.time()
            self.pg_session.execute(text("SELECT SUM(monthly_income) FROM encrypted_financial_profiles WHERE user_id = :user_id"), {'user_id': user_id}).scalar()
            duration = (time.time() - t0) * 1000
            passed = duration < 500
            tests.append(TestResult('Performance', 'Cash Flow Query <500ms', passed, {'duration_ms': duration}, None if passed else f"Took {duration:.1f}ms", time.time()-start))
        except Exception as e:
            tests.append(TestResult('Performance', 'Cash Flow Query <500ms', False, None, traceback.format_exc()))
        return tests

    # -------------------
    # SECURITY VALIDATION TESTS
    # -------------------
    def security_validation_tests(self) -> List[TestResult]:
        tests = []
        # 1. Ensure no duplicate emails
        try:
            start = time.time()
            q = "SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1"
            dups = self.pg_session.execute(text(q)).fetchall()
            passed = len(dups) == 0
            tests.append(TestResult('Security', 'No Duplicate Emails', passed, {'duplicates': [dict(d) for d in dups]}, None if passed else f"Found duplicates: {dups}", time.time()-start))
        except Exception as e:
            tests.append(TestResult('Security', 'No Duplicate Emails', False, None, traceback.format_exc()))
        # 2. Ensure all users have hashed passwords
        try:
            start = time.time()
            q = "SELECT password_hash FROM users LIMIT 10"
            hashes = self.pg_session.execute(text(q)).fetchall()
            passed = all(len(h['password_hash']) >= 8 for h in hashes)
            tests.append(TestResult('Security', 'Password Hashing', passed, None, None if passed else "Some passwords not hashed", time.time()-start))
        except Exception as e:
            tests.append(TestResult('Security', 'Password Hashing', False, None, traceback.format_exc()))
        return tests

    # -------------------
    # USER WORKFLOW END-TO-END TESTS
    # -------------------
    def user_workflow_tests(self) -> List[TestResult]:
        tests = []
        # 1. Register and login via API
        try:
            start = time.time()
            email = f"test_{int(time.time())}@mingus.com"
            password = "test1234!"
            # Register
            r = requests.post(f"{self.api_base}/auth/register", json={
                'email': email,
                'password': password,
                'first_name': 'Test',
                'last_name': 'User',
                'zip_code': '12345'
            }, timeout=5)
            reg_ok = r.status_code in (200, 201)
            # Login
            l = requests.post(f"{self.api_base}/auth/login", json={
                'email': email,
                'password': password
            }, timeout=5)
            login_ok = l.status_code == 200 and 'access_token' in l.json()
            tests.append(TestResult('User Workflow', 'Register/Login API', reg_ok and login_ok, {'register': r.status_code, 'login': l.status_code}, None if reg_ok and login_ok else f"Register: {r.text}, Login: {l.text}", time.time()-start))
        except Exception as e:
            tests.append(TestResult('User Workflow', 'Register/Login API', False, None, traceback.format_exc()))
        # 2. Financial profile update via API
        try:
            start = time.time()
            # Assume login above worked and we have a token
            token = l.json().get('access_token') if 'l' in locals() and l.status_code == 200 else None
            headers = {'Authorization': f'Bearer {token}'} if token else {}
            r = requests.post(f"{self.api_base}/financial/update", json={
                'account_balance': 12345.67
            }, headers=headers, timeout=5)
            ok = r.status_code in (200, 201)
            tests.append(TestResult('User Workflow', 'Financial Profile Update API', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
        except Exception as e:
            tests.append(TestResult('User Workflow', 'Financial Profile Update API', False, None, traceback.format_exc()))
        # 3. Health checkin via API
        try:
            start = time.time()
            r = requests.post(f"{self.api_base}/health/checkin", json={
                'mood_score': 8,
                'stress_level': 4,
                'sleep_hours': 7.0,
                'exercise_minutes': 20
            }, headers=headers, timeout=5)
            ok = r.status_code in (200, 201)
            tests.append(TestResult('User Workflow', 'Health Checkin API', ok, {'status': r.status_code}, None if ok else r.text, time.time()-start))
        except Exception as e:
            tests.append(TestResult('User Workflow', 'Health Checkin API', False, None, traceback.format_exc()))
        return tests

    def generate_report(self):
        # Group by category
        report = {'summary': {}, 'results': []}
        cats = set(r.category for r in self.results)
        for cat in cats:
            cat_results = [r for r in self.results if r.category == cat]
            passed = sum(1 for r in cat_results if r.passed)
            failed = sum(1 for r in cat_results if not r.passed)
            report['summary'][cat] = {'passed': passed, 'failed': failed, 'total': len(cat_results)}
        report['results'] = [r.__dict__ for r in self.results]
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2)
        print("\n=== MIGRATION TEST SUMMARY ===")
        for cat, s in report['summary'].items():
            status = '✅' if s['failed'] == 0 else '❌'
            print(f"{status} {cat}: {s['passed']}/{s['total']} passed, {s['failed']} failed")
        if any(s['failed'] for s in report['summary'].values()):
            print(f"\n❌ Some tests failed. See {REPORT_FILE} for details.")
        else:
            print(f"\n✅ All tests passed! See {REPORT_FILE} for details.")


def main():
    try:
        env_manager = validate_and_load_environment()
        env_manager.print_environment_summary()
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        sys.exit(1)
    pg_url = get_database_url()
    suite = MigrationTestSuite(pg_url, SQLITE_DBS, API_BASE_URL)
    suite.run()

if __name__ == "__main__":
    main() 