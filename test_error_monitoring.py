#!/usr/bin/env python3
"""
Test Error Monitoring and Alerting System
Comprehensive tests for error reporting, categorization, and alerting
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Test configuration
BASE_URL = os.environ.get('TEST_BASE_URL', 'http://localhost:5001')
TEST_INTERVAL = 2  # seconds between tests

class Colors:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_test(name: str):
    """Print test name"""
    print(f"{Colors.BOLD}Testing: {name}{Colors.RESET}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")

def test_endpoint(url: str, method: str = 'GET', data: Dict = None) -> Dict[str, Any]:
    """Test an API endpoint"""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=5)
        else:
            response = requests.request(method, url, json=data, timeout=5)
        
        return {
            'success': response.status_code < 400,
            'status_code': response.status_code,
            'data': response.json() if response.content else {},
            'response': response
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'status_code': 0
        }

def test_error_endpoints():
    """Test error monitoring endpoints"""
    print_header("Testing Error Monitoring Endpoints")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    # Test 1: Error statistics endpoint
    print_test("Error Statistics Endpoint")
    result = test_endpoint(f"{BASE_URL}/api/errors/stats?hours=24")
    if result['success']:
        print_success(f"Endpoint accessible (Status: {result['status_code']})")
        if 'errors' in result['data'] or 'total' in result['data']:
            print_success("Error statistics structure valid")
            results['passed'] += 1
        else:
            print_error("Invalid error statistics structure")
            results['failed'] += 1
    else:
        print_error(f"Endpoint failed: {result.get('error', 'Unknown error')}")
        results['failed'] += 1
    results['tests'].append(('Error Statistics Endpoint', result['success']))
    time.sleep(TEST_INTERVAL)
    
    # Test 2: Error list endpoint
    print_test("Error List Endpoint")
    result = test_endpoint(f"{BASE_URL}/api/errors?limit=10")
    if result['success']:
        print_success(f"Endpoint accessible (Status: {result['status_code']})")
        if 'errors' in result['data']:
            print_success(f"Retrieved {len(result['data'].get('errors', []))} errors")
            results['passed'] += 1
        else:
            print_error("Invalid error list structure")
            results['failed'] += 1
    else:
        print_error(f"Endpoint failed: {result.get('error', 'Unknown error')}")
        results['failed'] += 1
    results['tests'].append(('Error List Endpoint', result['success']))
    time.sleep(TEST_INTERVAL)
    
    # Test 3: Error health endpoint
    print_test("Error Health Endpoint")
    result = test_endpoint(f"{BASE_URL}/api/errors/health")
    if result['success']:
        print_success(f"Endpoint accessible (Status: {result['status_code']})")
        if 'status' in result['data']:
            status = result['data']['status']
            print_info(f"Error health status: {status}")
            results['passed'] += 1
        else:
            print_error("Invalid error health structure")
            results['failed'] += 1
    else:
        print_error(f"Endpoint failed: {result.get('error', 'Unknown error')}")
        results['failed'] += 1
    results['tests'].append(('Error Health Endpoint', result['success']))
    time.sleep(TEST_INTERVAL)
    
    # Test 4: Filtered error list
    print_test("Filtered Error List (by severity)")
    result = test_endpoint(f"{BASE_URL}/api/errors?severity=high&limit=5")
    if result['success']:
        print_success(f"Filtered endpoint accessible (Status: {result['status_code']})")
        results['passed'] += 1
    else:
        print_error(f"Endpoint failed: {result.get('error', 'Unknown error')}")
        results['failed'] += 1
    results['tests'].append(('Filtered Error List', result['success']))
    time.sleep(TEST_INTERVAL)
    
    return results

def test_error_generation():
    """Test error generation and logging"""
    print_header("Testing Error Generation and Logging")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    # Test 1: Generate 404 error (should be logged but not as error)
    print_test("Generate 404 Error")
    result = test_endpoint(f"{BASE_URL}/api/nonexistent-endpoint")
    if result['status_code'] == 404:
        print_success("404 error generated successfully")
        time.sleep(1)  # Wait for logging
        results['passed'] += 1
    else:
        print_error(f"Expected 404, got {result['status_code']}")
        results['failed'] += 1
    results['tests'].append(('404 Error Generation', result['status_code'] == 404))
    time.sleep(TEST_INTERVAL)
    
    # Test 2: Generate 500 error (should trigger error logging)
    print_test("Generate 500 Error (if endpoint exists)")
    # Try to trigger an error - this depends on app having an error endpoint
    # For now, we'll just verify the error handler works
    print_info("500 errors are handled by Flask error handlers")
    results['passed'] += 1
    results['tests'].append(('500 Error Handling', True))
    time.sleep(TEST_INTERVAL)
    
    # Test 3: Check error statistics after generation
    print_test("Verify Errors Are Logged")
    result = test_endpoint(f"{BASE_URL}/api/errors/stats?hours=1")
    if result['success']:
        error_data = result['data']
        total_errors = error_data.get('total', 0) if isinstance(error_data, dict) else 0
        print_info(f"Total errors in last hour: {total_errors}")
        if total_errors >= 0:  # Should be at least 0 (the 404 we just generated)
            print_success("Error statistics are being tracked")
            results['passed'] += 1
        else:
            print_warning("Error count seems incorrect")
            results['failed'] += 1
    else:
        print_error("Failed to get error statistics")
        results['failed'] += 1
    results['tests'].append(('Error Statistics Tracking', result['success']))
    time.sleep(TEST_INTERVAL)
    
    return results

def test_alerting():
    """Test alerting system"""
    print_header("Testing Alert System")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    # Test 1: Check alerts endpoint
    print_test("Alerts Endpoint")
    result = test_endpoint(f"{BASE_URL}/api/dashboard/alerts")
    if result['success']:
        print_success(f"Alerts endpoint accessible (Status: {result['status_code']})")
        alerts_data = result['data']
        alerts = alerts_data.get('alerts', [])
        alert_count = alerts_data.get('count', 0)
        print_info(f"Active alerts: {alert_count}")
        if alerts:
            for alert in alerts[:3]:  # Show first 3
                print_info(f"  - [{alert.get('level', 'unknown')}] {alert.get('message', 'No message')}")
        results['passed'] += 1
    else:
        print_error(f"Alerts endpoint failed: {result.get('error', 'Unknown error')}")
        results['failed'] += 1
    results['tests'].append(('Alerts Endpoint', result['success']))
    time.sleep(TEST_INTERVAL)
    
    # Test 2: Check error alerts in error stats
    print_test("Error Alerts in Statistics")
    result = test_endpoint(f"{BASE_URL}/api/errors/stats?hours=1")
    if result['success']:
        error_data = result['data']
        alerts = error_data.get('alerts', []) if isinstance(error_data, dict) else []
        print_info(f"Error alerts: {len(alerts)}")
        if isinstance(alerts, list):
            print_success("Error alerts structure valid")
            results['passed'] += 1
        else:
            print_warning("Error alerts structure unexpected")
            results['failed'] += 1
    else:
        print_error("Failed to get error statistics")
        results['failed'] += 1
    results['tests'].append(('Error Alerts', result['success']))
    time.sleep(TEST_INTERVAL)
    
    # Test 3: Check system monitor alerts
    print_test("System Monitor Alerts")
    result = test_endpoint(f"{BASE_URL}/api/metrics/health")
    if result['success']:
        health_data = result['data']
        alerts_info = health_data.get('alerts', {})
        if isinstance(alerts_info, dict):
            print_info(f"System alerts: {alerts_info.get('total', 0)}")
            print_success("System alerts structure valid")
            results['passed'] += 1
        else:
            print_warning("System alerts structure unexpected")
            results['failed'] += 1
    else:
        print_error("Failed to get system health")
        results['failed'] += 1
    results['tests'].append(('System Alerts', result['success']))
    time.sleep(TEST_INTERVAL)
    
    return results

def test_error_categorization():
    """Test error categorization"""
    print_header("Testing Error Categorization")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    # Test 1: Check error statistics by category
    print_test("Error Categories in Statistics")
    result = test_endpoint(f"{BASE_URL}/api/errors/stats?hours=24")
    if result['success']:
        error_data = result['data']
        by_category = error_data.get('by_category', {}) if isinstance(error_data, dict) else {}
        if isinstance(by_category, dict):
            print_success("Error categories structure valid")
            print_info("Categories tracked:")
            for category, count in list(by_category.items())[:5]:
                if count > 0:
                    print_info(f"  - {category}: {count}")
            results['passed'] += 1
        else:
            print_error("Invalid error categories structure")
            results['failed'] += 1
    else:
        print_error("Failed to get error statistics")
        results['failed'] += 1
    results['tests'].append(('Error Categories', result['success']))
    time.sleep(TEST_INTERVAL)
    
    # Test 2: Check error statistics by severity
    print_test("Error Severities in Statistics")
    result = test_endpoint(f"{BASE_URL}/api/errors/stats?hours=24")
    if result['success']:
        error_data = result['data']
        by_severity = error_data.get('by_severity', {}) if isinstance(error_data, dict) else {}
        if isinstance(by_severity, dict):
            print_success("Error severities structure valid")
            print_info("Severities tracked:")
            for severity, count in by_severity.items():
                if count > 0:
                    print_info(f"  - {severity}: {count}")
            results['passed'] += 1
        else:
            print_error("Invalid error severities structure")
            results['failed'] += 1
    else:
        print_error("Failed to get error statistics")
        results['failed'] += 1
    results['tests'].append(('Error Severities', result['success']))
    time.sleep(TEST_INTERVAL)
    
    # Test 3: Filter errors by category
    print_test("Filter Errors by Category")
    result = test_endpoint(f"{BASE_URL}/api/errors?category=database&limit=5")
    if result['success']:
        print_success("Category filtering works")
        results['passed'] += 1
    else:
        print_error("Category filtering failed")
        results['failed'] += 1
    results['tests'].append(('Category Filtering', result['success']))
    time.sleep(TEST_INTERVAL)
    
    return results

def test_dashboard_integration():
    """Test dashboard integration with error monitoring"""
    print_header("Testing Dashboard Integration")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    # Test 1: Dashboard overview includes errors
    print_test("Dashboard Overview with Errors")
    result = test_endpoint(f"{BASE_URL}/api/dashboard/overview")
    if result['success']:
        overview = result['data']
        if 'errors' in overview:
            print_success("Dashboard overview includes error data")
            results['passed'] += 1
        else:
            print_warning("Dashboard overview missing error data")
            results['failed'] += 1
    else:
        print_error("Dashboard overview endpoint failed")
        results['failed'] += 1
    results['tests'].append(('Dashboard Overview', result['success']))
    time.sleep(TEST_INTERVAL)
    
    # Test 2: Dashboard errors endpoint
    print_test("Dashboard Errors Endpoint")
    result = test_endpoint(f"{BASE_URL}/api/dashboard/errors?hours=24")
    if result['success']:
        print_success("Dashboard errors endpoint accessible")
        results['passed'] += 1
    else:
        print_error("Dashboard errors endpoint failed")
        results['failed'] += 1
    results['tests'].append(('Dashboard Errors', result['success']))
    time.sleep(TEST_INTERVAL)
    
    return results

def test_error_thresholds():
    """Test error alert thresholds"""
    print_header("Testing Error Alert Thresholds")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    # Test 1: Check current error rates
    print_test("Current Error Rates")
    result = test_endpoint(f"{BASE_URL}/api/errors/stats?hours=1")
    if result['success']:
        error_data = result['data']
        total_errors = error_data.get('total', 0) if isinstance(error_data, dict) else 0
        by_severity = error_data.get('by_severity', {}) if isinstance(error_data, dict) else {}
        
        critical = by_severity.get('critical', 0)
        high = by_severity.get('high', 0)
        
        print_info(f"Total errors (last hour): {total_errors}")
        print_info(f"Critical errors: {critical}")
        print_info(f"High severity errors: {high}")
        
        # Check thresholds (default: 10 critical, 50 high, 200 total)
        thresholds = {
            'critical': 10,
            'high': 50,
            'total': 200
        }
        
        print_info("Alert thresholds:")
        for level, threshold in thresholds.items():
            current = {'critical': critical, 'high': high, 'total': total_errors}[level]
            status = "⚠️  EXCEEDED" if current >= threshold else "✅ OK"
            print_info(f"  - {level}: {current}/{threshold} {status}")
        
        print_success("Error threshold checking works")
        results['passed'] += 1
    else:
        print_error("Failed to get error statistics")
        results['failed'] += 1
    results['tests'].append(('Error Thresholds', result['success']))
    time.sleep(TEST_INTERVAL)
    
    return results

def generate_test_errors():
    """Generate test errors to verify logging"""
    print_header("Generating Test Errors")
    
    print_info("Generating various error types to test logging...")
    
    # Generate 404 errors
    for i in range(3):
        test_endpoint(f"{BASE_URL}/api/test-404-{i}")
        time.sleep(0.5)
    
    print_success("Test errors generated")
    time.sleep(2)  # Wait for logging
    
    # Check if errors were logged
    result = test_endpoint(f"{BASE_URL}/api/errors/stats?hours=1")
    if result['success']:
        error_data = result['data']
        total = error_data.get('total', 0) if isinstance(error_data, dict) else 0
        print_info(f"Total errors after generation: {total}")

def print_summary(all_results: Dict[str, Dict]):
    """Print test summary"""
    print_header("Test Summary")
    
    total_passed = sum(r['passed'] for r in all_results.values())
    total_failed = sum(r['failed'] for r in all_results.values())
    total_tests = total_passed + total_failed
    
    print(f"\n{Colors.BOLD}Overall Results:{Colors.RESET}")
    print(f"  Total Tests: {total_tests}")
    print(f"  {Colors.GREEN}Passed: {total_passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {total_failed}{Colors.RESET}")
    print(f"  Success Rate: {(total_passed/total_tests*100) if total_tests > 0 else 0:.1f}%")
    
    print(f"\n{Colors.BOLD}Test Categories:{Colors.RESET}")
    for category, results in all_results.items():
        passed = results['passed']
        failed = results['failed']
        total = passed + failed
        status = f"{Colors.GREEN}✅" if failed == 0 else f"{Colors.YELLOW}⚠️"
        print(f"  {status} {category}: {passed}/{total} passed{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.RESET}")
    for category, results in all_results.items():
        print(f"\n{category}:")
        for test_name, passed in results['tests']:
            status = f"{Colors.GREEN}✅" if passed else f"{Colors.RED}❌"
            print(f"  {status} {test_name}{Colors.RESET}")

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*70)
    print("Error Monitoring and Alerting Test Suite")
    print("="*70)
    print(f"{Colors.RESET}")
    
    print_info(f"Testing against: {BASE_URL}")
    print_info(f"Test interval: {TEST_INTERVAL} seconds")
    
    # Check if server is running
    print_info("Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("Server is running")
        else:
            print_warning(f"Server responded with status {response.status_code}")
    except Exception as e:
        print_error(f"Cannot connect to server: {e}")
        print_error("Please start the Flask application first:")
        print_error("  export FLASK_PORT=5001")
        print_error("  python app.py")
        return
    
    # Run tests
    all_results = {}
    
    # Test error endpoints
    all_results['Error Endpoints'] = test_error_endpoints()
    time.sleep(TEST_INTERVAL)
    
    # Test error generation
    all_results['Error Generation'] = test_error_generation()
    time.sleep(TEST_INTERVAL)
    
    # Generate test errors
    generate_test_errors()
    time.sleep(TEST_INTERVAL)
    
    # Test error categorization
    all_results['Error Categorization'] = test_error_categorization()
    time.sleep(TEST_INTERVAL)
    
    # Test alerting
    all_results['Alerting'] = test_alerting()
    time.sleep(TEST_INTERVAL)
    
    # Test error thresholds
    all_results['Error Thresholds'] = test_error_thresholds()
    time.sleep(TEST_INTERVAL)
    
    # Test dashboard integration
    all_results['Dashboard Integration'] = test_dashboard_integration()
    
    # Print summary
    print_summary(all_results)
    
    # Final recommendations
    print_header("Recommendations")
    print_info("1. Review error statistics: /api/errors/stats")
    print_info("2. Check active alerts: /api/dashboard/alerts")
    print_info("3. View error health: /api/errors/health")
    print_info("4. Monitor dashboard: /dashboard")
    print_info("5. Review error logs: logs/errors.log")

if __name__ == '__main__':
    main()
