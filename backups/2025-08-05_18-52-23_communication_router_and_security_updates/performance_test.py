#!/usr/bin/env python3
"""
MINGUS Application - PostgreSQL Performance Testing Suite
========================================================

- Realistic application queries for user, financial, health, and subscription operations
- Single-user, concurrent, bulk, and analytical scenarios
- Measures query times, pool stats, memory, CPU, and concurrency
- Generates detailed reports and optimization recommendations

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import time
import json
import logging
import argparse
import random
import string
import threading
import psutil
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Import models and config
from models import User, UserProfile, EncryptedFinancialProfile, UserHealthCheckin, Subscription, FeatureAccess
from config.environment import validate_and_load_environment, get_database_url

# Performance targets
TARGET_QUERY_TIME_MS = 500
TARGET_CONCURRENCY = 100

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('PerformanceTest')


def random_email():
    return f"test_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}@mingus.com"

def random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))


def measure_resource_usage():
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / 1024 / 1024  # MB
    cpu = process.cpu_percent(interval=0.1)
    return {'memory_mb': mem, 'cpu_percent': cpu}


def time_query(session, query, params=None):
    start = time.time()
    try:
        result = session.execute(text(query), params or {})
        rows = result.fetchall() if result.returns_rows else None
        duration = (time.time() - start) * 1000  # ms
        return {'success': True, 'duration_ms': duration, 'rowcount': len(rows) if rows else 0}
    except Exception as e:
        duration = (time.time() - start) * 1000
        return {'success': False, 'duration_ms': duration, 'error': str(e)}


def user_registration_and_login(session):
    email = random_email()
    password = random_password()
    # Registration
    reg_query = """
        INSERT INTO users (email, password_hash, is_active, is_verified, is_admin)
        VALUES (:email, :password_hash, true, true, false)
        RETURNING id
    """
    reg_result = time_query(session, reg_query, {'email': email, 'password_hash': password})
    # Login (simulate by selecting user)
    login_query = "SELECT id FROM users WHERE email = :email AND password_hash = :password_hash"
    login_result = time_query(session, login_query, {'email': email, 'password_hash': password})
    return {'registration': reg_result, 'login': login_result}


def financial_profile_update(session, user_id):
    # Simulate update
    update_query = """
        UPDATE encrypted_financial_profiles
        SET account_balance = account_balance + 100, updated_at = NOW()
        WHERE user_id = :user_id
        RETURNING id
    """
    return time_query(session, update_query, {'user_id': user_id})


def health_checkin_submission(session, user_id):
    insert_query = """
        INSERT INTO user_health_checkins (user_id, checkin_date, mood_score, stress_level, sleep_hours, exercise_minutes, wellness_score)
        VALUES (:user_id, CURRENT_DATE, 7, 5, 7.5, 30, 75.0)
        RETURNING id
    """
    return time_query(session, insert_query, {'user_id': user_id})


def cash_flow_calculation(session, user_id):
    # Simulate cash flow calculation
    query = """
        SELECT SUM(monthly_income) - SUM(monthly_expenses) AS cash_flow
        FROM encrypted_financial_profiles
        WHERE user_id = :user_id
    """
    return time_query(session, query, {'user_id': user_id})


def income_comparison_query(session, user_id):
    # Simulate income comparison
    query = """
        SELECT up.annual_income, AVG(up2.annual_income) AS peer_avg
        FROM user_profiles up
        JOIN user_profiles up2 ON up2.zip_code = up.zip_code
        WHERE up.user_id = :user_id
        GROUP BY up.annual_income
    """
    return time_query(session, query, {'user_id': user_id})


def subscription_status_check(session, user_id):
    query = "SELECT status FROM subscriptions WHERE user_id = :user_id ORDER BY start_date DESC LIMIT 1"
    return time_query(session, query, {'user_id': user_id})


def feature_access_validation(session, user_id):
    query = """
        SELECT fa.feature_name, fa.is_enabled
        FROM subscriptions s
        JOIN feature_access fa ON fa.subscription_plan_id = s.plan_id
        WHERE s.user_id = :user_id
    """
    return time_query(session, query, {'user_id': user_id})


def get_random_user_id(session):
    query = "SELECT id FROM users ORDER BY RANDOM() LIMIT 1"
    result = session.execute(text(query))
    row = result.fetchone()
    return row[0] if row else None


def single_user_operations(session):
    user_id = get_random_user_id(session)
    if not user_id:
        return {'error': 'No users found'}
    results = {
        'financial_profile_update': financial_profile_update(session, user_id),
        'health_checkin_submission': health_checkin_submission(session, user_id),
        'cash_flow_calculation': cash_flow_calculation(session, user_id),
        'income_comparison_query': income_comparison_query(session, user_id),
        'subscription_status_check': subscription_status_check(session, user_id),
        'feature_access_validation': feature_access_validation(session, user_id),
    }
    return results


def concurrent_user_simulation(engine, concurrency=TARGET_CONCURRENCY, ops_per_user=3):
    Session = sessionmaker(bind=engine)
    results = []
    def user_ops():
        session = Session()
        try:
            user_id = get_random_user_id(session)
            if not user_id:
                return {'error': 'No users found'}
            op_results = []
            for _ in range(ops_per_user):
                op = random.choice([
                    financial_profile_update,
                    health_checkin_submission,
                    cash_flow_calculation,
                    income_comparison_query,
                    subscription_status_check,
                    feature_access_validation
                ])
                op_results.append(op(session, user_id))
            return op_results
        finally:
            session.close()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(user_ops) for _ in range(concurrency)]
        for future in as_completed(futures):
            results.append(future.result())
    return results


def bulk_data_operations(session, bulk_size=1000):
    # Bulk insert users
    start = time.time()
    emails = [random_email() for _ in range(bulk_size)]
    password = random_password()
    insert_query = """
        INSERT INTO users (email, password_hash, is_active, is_verified, is_admin)
        VALUES (:email, :password_hash, true, true, false)
    """
    for email in emails:
        session.execute(text(insert_query), {'email': email, 'password_hash': password})
    session.commit()
    duration = (time.time() - start) * 1000
    return {'bulk_insert_users': {'count': bulk_size, 'duration_ms': duration}}


def complex_analytical_queries(session):
    # Example: Top 10 zip codes by average income
    query = """
        SELECT zip_code, AVG(annual_income) AS avg_income
        FROM user_profiles
        GROUP BY zip_code
        ORDER BY avg_income DESC
        LIMIT 10
    """
    return time_query(session, query)


def database_under_load(engine, duration_sec=10, concurrency=TARGET_CONCURRENCY):
    Session = sessionmaker(bind=engine)
    stop_time = time.time() + duration_sec
    op_counts = 0
    total_times = []
    def load_op():
        session = Session()
        try:
            user_id = get_random_user_id(session)
            if not user_id:
                return 0, 0
            start = time.time()
            op = random.choice([
                financial_profile_update,
                health_checkin_submission,
                cash_flow_calculation,
                income_comparison_query,
                subscription_status_check,
                feature_access_validation
            ])
            op(session, user_id)
            duration = (time.time() - start) * 1000
            return 1, duration
        finally:
            session.close()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        while time.time() < stop_time:
            futures.append(executor.submit(load_op))
        for future in as_completed(futures):
            count, duration = future.result()
            op_counts += count
            total_times.append(duration)
    avg_time = sum(total_times) / len(total_times) if total_times else 0
    return {'total_ops': op_counts, 'avg_time_ms': avg_time, 'op_count': len(total_times)}


def run_performance_tests(database_url, concurrency=TARGET_CONCURRENCY, bulk_size=1000, duration_sec=10):
    engine = create_engine(database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    report = {'start_time': datetime.now().isoformat()}
    resource_before = measure_resource_usage()
    report['resource_usage_before'] = resource_before
    logger.info('Running single user operations...')
    report['single_user_operations'] = single_user_operations(session)
    logger.info('Running user registration and login...')
    report['user_registration_and_login'] = user_registration_and_login(session)
    logger.info('Running bulk data operations...')
    report['bulk_data_operations'] = bulk_data_operations(session, bulk_size=bulk_size)
    logger.info(f'Running concurrent user simulation ({concurrency} users)...')
    report['concurrent_user_simulation'] = concurrent_user_simulation(engine, concurrency=concurrency)
    logger.info('Running complex analytical queries...')
    report['complex_analytical_queries'] = complex_analytical_queries(session)
    logger.info('Running database under load...')
    report['database_under_load'] = database_under_load(engine, duration_sec=duration_sec, concurrency=concurrency)
    resource_after = measure_resource_usage()
    report['resource_usage_after'] = resource_after
    report['end_time'] = datetime.now().isoformat()
    session.close()
    return report


def analyze_performance(report):
    # Analyze query times and concurrency
    all_times = []
    def extract_times(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == 'duration_ms' and isinstance(v, (int, float)):
                    all_times.append(v)
                else:
                    extract_times(v)
        elif isinstance(obj, list):
            for item in obj:
                extract_times(item)
    extract_times(report)
    if all_times:
        all_times.sort()
        p95 = all_times[int(0.95 * len(all_times)) - 1]
        avg = sum(all_times) / len(all_times)
    else:
        p95 = avg = 0
    # Recommendations
    recommendations = []
    if p95 > TARGET_QUERY_TIME_MS:
        recommendations.append(f"95th percentile query time ({p95:.1f}ms) exceeds target ({TARGET_QUERY_TIME_MS}ms)")
    if report['resource_usage_after']['memory_mb'] - report['resource_usage_before']['memory_mb'] > 200:
        recommendations.append("High memory usage increase detected")
    if report['resource_usage_after']['cpu_percent'] > 80:
        recommendations.append("High CPU utilization detected")
    if len(report.get('concurrent_user_simulation', [])) < TARGET_CONCURRENCY:
        recommendations.append(f"Concurrent user capacity below target ({TARGET_CONCURRENCY})")
    if not recommendations:
        recommendations.append("Performance is within target thresholds")
    return {
        'p95_query_time_ms': p95,
        'avg_query_time_ms': avg,
        'concurrent_user_capacity': len(report.get('concurrent_user_simulation', [])),
        'memory_usage_mb': report['resource_usage_after']['memory_mb'],
        'cpu_utilization_percent': report['resource_usage_after']['cpu_percent'],
        'recommendations': recommendations
    }


def main():
    parser = argparse.ArgumentParser(description="MINGUS PostgreSQL Performance Testing Suite")
    parser.add_argument('--database-url', help='Database URL (default: from environment)', default=None)
    parser.add_argument('--concurrency', type=int, default=TARGET_CONCURRENCY, help='Number of concurrent users')
    parser.add_argument('--bulk-size', type=int, default=1000, help='Bulk operation size')
    parser.add_argument('--duration-sec', type=int, default=10, help='Duration for load test (seconds)')
    parser.add_argument('--report-file', default='performance_report.json', help='Output JSON report file')
    args = parser.parse_args()

    # Validate environment
    try:
        env_manager = validate_and_load_environment()
        env_manager.print_environment_summary()
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        sys.exit(1)

    database_url = args.database_url or get_database_url()
    logger.info(f"Using database: {database_url}")
    report = run_performance_tests(
        database_url=database_url,
        concurrency=args.concurrency,
        bulk_size=args.bulk_size,
        duration_sec=args.duration_sec
    )
    analysis = analyze_performance(report)
    report['analysis'] = analysis
    with open(args.report_file, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Performance report saved to {args.report_file}")
    print("\n=== PERFORMANCE SUMMARY ===")
    print(json.dumps(analysis, indent=2))

if __name__ == "__main__":
    main() 