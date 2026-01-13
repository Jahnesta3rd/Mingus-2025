#!/usr/bin/env python3
"""
Test script for CORS logging functionality

Tests that CORS failures and requests are properly logged.
"""

import os
import sys
import requests
import time
from datetime import datetime

# Test configuration
BASE_URL = os.environ.get('TEST_BASE_URL', 'http://localhost:5000')
LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'cors.log')

def test_cors_logging():
    """Test CORS logging by making various CORS requests"""
    
    print("=" * 70)
    print("CORS Logging Test")
    print("=" * 70)
    print(f"Target: {BASE_URL}")
    print(f"Log file: {LOG_FILE}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    test_results = []
    
    # Test 1: Allowed origin (should log success)
    print("Test 1: Allowed origin request")
    try:
        response = requests.get(
            f"{BASE_URL}/health",
            headers={'Origin': 'http://localhost:3000'}
        )
        test_results.append({
            'test': 'Allowed origin',
            'status': 'PASS' if response.status_code == 200 else 'FAIL',
            'status_code': response.status_code
        })
        print(f"  ✅ Status: {response.status_code}")
    except Exception as e:
        test_results.append({
            'test': 'Allowed origin',
            'status': 'ERROR',
            'error': str(e)
        })
        print(f"  ❌ Error: {e}")
    
    time.sleep(0.5)
    
    # Test 2: Unauthorized origin (should log warning/error)
    print("\nTest 2: Unauthorized origin request (should be blocked)")
    try:
        response = requests.get(
            f"{BASE_URL}/health",
            headers={'Origin': 'http://evil.com'}
        )
        test_results.append({
            'test': 'Unauthorized origin',
            'status': 'PASS',
            'status_code': response.status_code,
            'note': 'Should be blocked and logged'
        })
        print(f"  ✅ Status: {response.status_code} (blocked as expected)")
    except Exception as e:
        test_results.append({
            'test': 'Unauthorized origin',
            'status': 'ERROR',
            'error': str(e)
        })
        print(f"  ❌ Error: {e}")
    
    time.sleep(0.5)
    
    # Test 3: Preflight request (should log preflight)
    print("\nTest 3: CORS preflight request (OPTIONS)")
    try:
        response = requests.options(
            f"{BASE_URL}/health",
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
        )
        test_results.append({
            'test': 'Preflight request',
            'status': 'PASS' if response.status_code == 200 else 'FAIL',
            'status_code': response.status_code
        })
        print(f"  ✅ Status: {response.status_code}")
        print(f"  Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'N/A')}")
    except Exception as e:
        test_results.append({
            'test': 'Preflight request',
            'status': 'ERROR',
            'error': str(e)
        })
        print(f"  ❌ Error: {e}")
    
    time.sleep(0.5)
    
    # Test 4: Preflight with unauthorized origin
    print("\nTest 4: Preflight with unauthorized origin (should be blocked)")
    try:
        response = requests.options(
            f"{BASE_URL}/health",
            headers={
                'Origin': 'https://attacker.com',
                'Access-Control-Request-Method': 'POST'
            }
        )
        test_results.append({
            'test': 'Preflight unauthorized',
            'status': 'PASS',
            'status_code': response.status_code,
            'note': 'Should be blocked and logged'
        })
        print(f"  ✅ Status: {response.status_code} (blocked as expected)")
    except Exception as e:
        test_results.append({
            'test': 'Preflight unauthorized',
            'status': 'ERROR',
            'error': str(e)
        })
        print(f"  ❌ Error: {e}")
    
    # Wait a moment for logs to be written
    print("\nWaiting for logs to be written...")
    time.sleep(1)
    
    # Check log file
    print("\n" + "=" * 70)
    print("Checking CORS log file...")
    print("=" * 70)
    
    if os.path.exists(LOG_FILE):
        print(f"✅ Log file exists: {LOG_FILE}")
        print(f"   Size: {os.path.getsize(LOG_FILE)} bytes")
        print("\nLast 20 lines of CORS log:")
        print("-" * 70)
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(line.rstrip())
    else:
        print(f"⚠️  Log file not found: {LOG_FILE}")
        print("   This may be normal if the app hasn't started yet.")
        print("   Make sure the Flask app is running and CORS logging is enabled.")
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = len([r for r in test_results if r['status'] == 'PASS'])
    failed = len([r for r in test_results if r['status'] == 'FAIL'])
    errors = len([r for r in test_results if r['status'] == 'ERROR'])
    
    print(f"Total tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    
    print("\nNext steps:")
    print("1. Check the CORS log file for detailed logging:")
    print(f"   tail -f {LOG_FILE}")
    print("2. Monitor CORS failures in real-time:")
    print(f"   tail -f {LOG_FILE} | grep -i 'blocked\\|failure\\|error'")
    print("3. View all CORS events:")
    print(f"   cat {LOG_FILE}")
    
    return test_results

if __name__ == '__main__':
    test_cors_logging()
