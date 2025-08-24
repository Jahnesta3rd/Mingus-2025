#!/usr/bin/env python3
"""
Mingus Application Test Runner
Runs comprehensive test suite and generates reports
"""

import os
import subprocess
from datetime import datetime


def run_tests():
    """Run the complete test suite."""
    print("\n🧪 Starting Mingus Application Test Suite")
    print("=" * 50)

    # Create reports directory
    os.makedirs('reports', exist_ok=True)

    # Test groups (logical order)
    test_commands = [
        {
            'name': 'API Endpoints',
            'command': ['pytest', 'tests/mingus_suite/test_api_endpoints.py', '-v'],
            'marker': 'api',
        },
        {
            'name': 'User Registration',
            'command': ['pytest', 'tests/mingus_suite/test_user_registration.py', '-v'],
            'marker': 'fast',
        },
        {
            'name': 'Profile Completion',
            'command': ['pytest', 'tests/mingus_suite/test_profile_completion.py', '-v'],
            'marker': 'fast',
        },
        {
            'name': 'All Tests with Coverage',
            'command': [
                'pytest',
                '--cov=backend',
                '--cov-report=html',
                '--html=reports/test_report.html',
            ],
            'marker': 'all',
        },
    ]

    results = []
    for test_group in test_commands:
        print(f"\n🔍 Running {test_group['name']} Tests...")
        try:
            result = subprocess.run(test_group['command'], capture_output=True, text=True)
            results.append({
                'name': test_group['name'],
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
            })
            if result.returncode == 0:
                print(f"✅ {test_group['name']} - PASSED")
            else:
                print(f"❌ {test_group['name']} - FAILED")
                print(f"Error: {result.stderr[:200]}...")
        except Exception as e:
            print(f"❌ Error running {test_group['name']}: {e}")
            results.append({
                'name': test_group['name'],
                'success': False,
                'output': '',
                'errors': str(e),
            })

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    if passed == total:
        print("🎉 ALL TESTS PASSED! Ready for external developer.")
    else:
        print("⚠ Some tests failed. Review and fix before external developer.")
    print("\nDetailed reports generated in 'reports/' directory")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    run_tests()


