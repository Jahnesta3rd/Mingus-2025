#!/usr/bin/env python3
"""
Critical Authentication Issues Test Runner
Executes comprehensive authentication vulnerability testing for the MINGUS application.
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_critical_authentication_issues import CriticalAuthenticationTester

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import jwt
    except ImportError:
        missing_deps.append("PyJWT")
    
    try:
        import cryptography
    except ImportError:
        missing_deps.append("cryptography")
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Please install required dependencies:")
        print("pip install -r requirements-critical-auth-testing.txt")
        return False
    
    return True

def check_backend_availability(base_url: str) -> bool:
    """Check if the backend is available"""
    import requests
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except:
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            return response.status_code in [200, 404, 405]  # Any response means server is up
        except:
            return False

def generate_report(results: dict, output_dir: str = "reports"):
    """Generate a comprehensive test report"""
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create detailed report
    report_data = {
        "test_suite": "Critical Authentication Issues Testing",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": results['total_tests'],
            "passed": results['passed'],
            "failed": results['failed'],
            "errors": results['errors'],
            "success_rate": results['summary']['success_rate'],
            "overall_status": results['summary']['overall_status']
        },
        "critical_issues": [],
        "recommendations": []
    }
    
    # Analyze test results for critical issues
    for result in results.get('detailed_results', []):
        if result['status'] == 'FAIL' and result['severity'] == 'CRITICAL':
            report_data['critical_issues'].append({
                'test_name': result['test_name'],
                'description': result['description'],
                'details': result['details']
            })
    
    # Generate recommendations based on failures
    if results['failed'] > 0:
        report_data['recommendations'].append({
            'priority': 'CRITICAL',
            'action': 'Immediate security review required',
            'description': f"{results['failed']} authentication tests failed"
        })
    
    if results['errors'] > 0:
        report_data['recommendations'].append({
            'priority': 'HIGH',
            'action': 'Fix test environment issues',
            'description': f"{results['errors']} tests encountered errors"
        })
    
    # Save JSON report
    json_filename = f"{output_dir}/critical_auth_test_report_{timestamp}.json"
    with open(json_filename, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    # Generate markdown report
    md_filename = f"{output_dir}/critical_auth_test_report_{timestamp}.md"
    with open(md_filename, 'w') as f:
        f.write(f"# Critical Authentication Issues Test Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"- **Overall Status:** {report_data['summary']['overall_status']}\n")
        f.write(f"- **Success Rate:** {report_data['summary']['success_rate']:.1f}%\n")
        f.write(f"- **Total Tests:** {report_data['summary']['total_tests']}\n")
        f.write(f"- **Passed:** {report_data['summary']['passed']} ✅\n")
        f.write(f"- **Failed:** {report_data['summary']['failed']} ❌\n")
        f.write(f"- **Errors:** {report_data['summary']['errors']} 💥\n\n")
        
        if report_data['critical_issues']:
            f.write("## 🚨 Critical Issues\n\n")
            for issue in report_data['critical_issues']:
                f.write(f"### {issue['test_name']}\n")
                f.write(f"- **Description:** {issue['description']}\n")
                if issue['details']:
                    f.write(f"- **Details:** {json.dumps(issue['details'], indent=2)}\n")
                f.write("\n")
        
        if report_data['recommendations']:
            f.write("## 📋 Recommendations\n\n")
            for rec in report_data['recommendations']:
                f.write(f"### {rec['priority']} Priority\n")
                f.write(f"- **Action:** {rec['action']}\n")
                f.write(f"- **Description:** {rec['description']}\n\n")
        
        f.write("## Test Results\n\n")
        for result in results.get('detailed_results', []):
            status_emoji = {
                'PASS': '✅',
                'FAIL': '❌',
                'ERROR': '💥',
                'WARNING': '⚠️'
            }
            f.write(f"{status_emoji.get(result['status'], '❓')} **{result['test_name']}** - {result['status']}\n")
            f.write(f"  - {result['description']}\n")
            if result['details']:
                f.write(f"  - Details: {json.dumps(result['details'], indent=2)}\n")
            f.write("\n")
    
    print(f"📊 Reports generated:")
    print(f"  - JSON: {json_filename}")
    print(f"  - Markdown: {md_filename}")
    
    return json_filename, md_filename

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Critical Authentication Issues Testing Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_critical_auth_tests.py
  python run_critical_auth_tests.py --url http://localhost:8000
  python run_critical_auth_tests.py --verbose --output-dir ./security-reports
        """
    )
    
    parser.add_argument(
        '--url', 
        default='http://localhost:5000',
        help='Base URL of the MINGUS application (default: http://localhost:5000)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--output-dir',
        default='reports',
        help='Output directory for reports (default: reports)'
    )
    
    parser.add_argument(
        '--skip-dependency-check',
        action='store_true',
        help='Skip dependency check'
    )
    
    parser.add_argument(
        '--skip-backend-check',
        action='store_true',
        help='Skip backend availability check'
    )
    
    args = parser.parse_args()
    
    print("🔐 MINGUS Critical Authentication Issues Testing Suite")
    print("=" * 60)
    
    # Check dependencies
    if not args.skip_dependency_check:
        print("🔍 Checking dependencies...")
        if not check_dependencies():
            return 1
        print("✅ Dependencies check passed")
    
    # Check backend availability
    if not args.skip_backend_check:
        print(f"🔍 Checking backend availability at {args.url}...")
        if not check_backend_availability(args.url):
            print(f"❌ Backend not available at {args.url}")
            print("Please ensure the MINGUS backend is running before running tests.")
            return 1
        print("✅ Backend is available")
    
    # Run tests
    print("\n🚀 Starting critical authentication tests...")
    start_time = time.time()
    
    try:
        tester = CriticalAuthenticationTester(args.url)
        results = tester.run_all_tests()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️  Tests completed in {duration:.2f} seconds")
        
        # Generate reports
        print("\n📊 Generating reports...")
        json_file, md_file = generate_report(results, args.output_dir)
        
        # Print summary
        print("\n" + "=" * 60)
        print("CRITICAL AUTHENTICATION ISSUES TESTING SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed']} ✅")
        print(f"Failed: {results['failed']} ❌")
        print(f"Errors: {results['errors']} 💥")
        print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
        print(f"Overall Status: {results['summary']['overall_status']}")
        print("=" * 60)
        
        # Print critical issues if any
        critical_issues = [r for r in results.get('detailed_results', []) 
                          if r['status'] == 'FAIL' and r['severity'] == 'CRITICAL']
        
        if critical_issues:
            print("\n🚨 CRITICAL ISSUES DETECTED:")
            for issue in critical_issues:
                print(f"  ❌ {issue['test_name']}: {issue['description']}")
            print("\n⚠️  IMMEDIATE ACTION REQUIRED - Review detailed reports")
            return 1
        elif results['failed'] > 0:
            print("\n⚠️  Some tests failed - Review detailed reports")
            return 1
        else:
            print("\n✅ All critical authentication tests passed!")
            return 0
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
