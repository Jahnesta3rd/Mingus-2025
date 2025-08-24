#!/usr/bin/env python3
"""
Plaid Integration Test Runner

This script provides a comprehensive test runner for all Plaid integration tests
including security, functionality, business logic, performance, and compliance testing.
"""

import os
import sys
import subprocess
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pytest


class PlaidTestRunner:
    """Comprehensive test runner for Plaid integration tests"""
    
    def __init__(self, output_dir: str = "test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_all_tests(self, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run all Plaid integration tests"""
        print("🚀 Starting Plaid Integration Test Suite...")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"⏰ Timestamp: {self.timestamp}")
        print("-" * 80)
        
        test_results = {
            'timestamp': self.timestamp,
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'test_categories': {},
            'performance_metrics': {},
            'security_results': {},
            'compliance_results': {},
            'duration': 0
        }
        
        start_time = time.time()
        
        # Run test categories
        test_categories = [
            ('security', 'tests/test_plaid_security.py'),
            ('integration', 'tests/plaid_integration_tests.py'),
            ('unit', 'tests/plaid_integration_tests.py::TestPlaidIntegrationFunctionality'),
            ('performance', 'tests/plaid_integration_tests.py::TestPlaidIntegrationPerformance'),
            ('compliance', 'tests/plaid_integration_tests.py::TestPlaidIntegrationCompliance')
        ]
        
        for category, test_path in test_categories:
            print(f"\n🔍 Running {category.upper()} tests...")
            category_results = self._run_test_category(category, test_path, verbose, parallel)
            test_results['test_categories'][category] = category_results
            
            # Update totals
            test_results['total_tests'] += category_results['total']
            test_results['passed'] += category_results['passed']
            test_results['failed'] += category_results['failed']
            test_results['skipped'] += category_results['skipped']
            test_results['errors'] += category_results['errors']
        
        test_results['duration'] = time.time() - start_time
        
        # Generate reports
        self._generate_reports(test_results)
        
        # Print summary
        self._print_summary(test_results)
        
        return test_results
    
    def run_security_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run security tests only"""
        print("🔒 Running Plaid Security Tests...")
        return self._run_test_category('security', 'tests/test_plaid_security.py', verbose)
    
    def run_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run integration tests only"""
        print("🔗 Running Plaid Integration Tests...")
        return self._run_test_category('integration', 'tests/plaid_integration_tests.py', verbose)
    
    def run_performance_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run performance tests only"""
        print("⚡ Running Plaid Performance Tests...")
        return self._run_test_category('performance', 'tests/plaid_integration_tests.py::TestPlaidIntegrationPerformance', verbose)
    
    def run_compliance_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run compliance tests only"""
        print("📋 Running Plaid Compliance Tests...")
        return self._run_test_category('compliance', 'tests/plaid_integration_tests.py::TestPlaidIntegrationCompliance', verbose)
    
    def _run_test_category(self, category: str, test_path: str, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run tests for a specific category"""
        pytest_args = [
            'pytest',
            test_path,
            '-v' if verbose else '-q',
            '--tb=short',
            '--strict-markers',
            '--disable-warnings',
            f'--html={self.output_dir}/{category}_report_{self.timestamp}.html',
            f'--json-report={self.output_dir}/{category}_report_{self.timestamp}.json',
            f'--json-report-file={self.output_dir}/{category}_report_{self.timestamp}.json'
        ]
        
        if parallel:
            pytest_args.extend(['-n', 'auto'])
        
        # Add category-specific markers
        if category == 'security':
            pytest_args.extend(['-m', 'security'])
        elif category == 'integration':
            pytest_args.extend(['-m', 'integration'])
        elif category == 'performance':
            pytest_args.extend(['-m', 'performance'])
        elif category == 'compliance':
            pytest_args.extend(['-m', 'compliance'])
        
        try:
            result = subprocess.run(pytest_args, capture_output=True, text=True, timeout=300)
            
            # Parse results
            results = self._parse_pytest_output(result.stdout, result.stderr, result.returncode)
            results['category'] = category
            results['test_path'] = test_path
            
            return results
            
        except subprocess.TimeoutExpired:
            return {
                'category': category,
                'test_path': test_path,
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 1,
                'error_message': 'Test execution timed out'
            }
        except Exception as e:
            return {
                'category': category,
                'test_path': test_path,
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 1,
                'error_message': str(e)
            }
    
    def _parse_pytest_output(self, stdout: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse pytest output to extract test results"""
        results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'stdout': stdout,
            'stderr': stderr,
            'return_code': return_code
        }
        
        # Parse test results from output
        lines = stdout.split('\n')
        for line in lines:
            if 'passed' in line and 'failed' in line and 'skipped' in line:
                # Extract numbers from summary line
                parts = line.split()
                for part in parts:
                    if part.isdigit():
                        if 'passed' in line and part in line.split()[:line.split().index('passed')]:
                            results['passed'] = int(part)
                        elif 'failed' in line and part in line.split()[:line.split().index('failed')]:
                            results['failed'] = int(part)
                        elif 'skipped' in line and part in line.split()[:line.split().index('skipped')]:
                            results['skipped'] = int(part)
                
                # Calculate total
                results['total'] = results['passed'] + results['failed'] + results['skipped']
                break
        
        return results
    
    def _generate_reports(self, test_results: Dict[str, Any]):
        """Generate comprehensive test reports"""
        # Generate JSON report
        json_report_path = self.output_dir / f"plaid_test_report_{self.timestamp}.json"
        with open(json_report_path, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        # Generate HTML report
        html_report_path = self.output_dir / f"plaid_test_report_{self.timestamp}.html"
        self._generate_html_report(test_results, html_report_path)
        
        # Generate markdown report
        md_report_path = self.output_dir / f"plaid_test_report_{self.timestamp}.md"
        self._generate_markdown_report(test_results, md_report_path)
        
        print(f"\n📊 Reports generated:")
        print(f"   JSON: {json_report_path}")
        print(f"   HTML: {html_report_path}")
        print(f"   Markdown: {md_report_path}")
    
    def _generate_html_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate HTML test report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Plaid Integration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .category {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .skipped {{ color: orange; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 20px 0; }}
        .metric {{ background-color: #f9f9f9; padding: 10px; border-radius: 5px; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Plaid Integration Test Report</h1>
        <p>Generated: {test_results['timestamp']}</p>
        <p>Duration: {test_results['duration']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>Test Summary</h2>
        <div class="metrics">
            <div class="metric">
                <h3>Total Tests</h3>
                <p>{test_results['total_tests']}</p>
            </div>
            <div class="metric passed">
                <h3>Passed</h3>
                <p>{test_results['passed']}</p>
            </div>
            <div class="metric failed">
                <h3>Failed</h3>
                <p>{test_results['failed']}</p>
            </div>
            <div class="metric skipped">
                <h3>Skipped</h3>
                <p>{test_results['skipped']}</p>
            </div>
        </div>
    </div>
    
    <div class="categories">
        <h2>Test Categories</h2>
"""
        
        for category, results in test_results['test_categories'].items():
            status_class = 'passed' if results['failed'] == 0 and results['errors'] == 0 else 'failed'
            html_content += f"""
        <div class="category {status_class}">
            <h3>{category.title()} Tests</h3>
            <p>Total: {results['total']} | Passed: {results['passed']} | Failed: {results['failed']} | Skipped: {results['skipped']}</p>
            <p>Test Path: {results['test_path']}</p>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _generate_markdown_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate markdown test report"""
        md_content = f"""# Plaid Integration Test Report

**Generated:** {test_results['timestamp']}  
**Duration:** {test_results['duration']:.2f} seconds

## Test Summary

| Metric | Count |
|--------|-------|
| Total Tests | {test_results['total_tests']} |
| Passed | {test_results['passed']} |
| Failed | {test_results['failed']} |
| Skipped | {test_results['skipped']} |
| Errors | {test_results['errors']} |

## Test Categories

"""
        
        for category, results in test_results['test_categories'].items():
            status = "✅ PASS" if results['failed'] == 0 and results['errors'] == 0 else "❌ FAIL"
            md_content += f"""### {category.title()} Tests {status}

- **Total:** {results['total']}
- **Passed:** {results['passed']}
- **Failed:** {results['failed']}
- **Skipped:** {results['skipped']}
- **Test Path:** {results['test_path']}

"""
        
        md_content += """## Recommendations

Based on the test results, consider the following:

1. **Security Tests**: Ensure all security tests pass before deployment
2. **Integration Tests**: Verify all integration points are working correctly
3. **Performance Tests**: Monitor performance metrics and optimize if needed
4. **Compliance Tests**: Ensure regulatory compliance requirements are met

## Next Steps

1. Review failed tests and fix issues
2. Run tests again to verify fixes
3. Deploy only after all critical tests pass
4. Monitor production performance and security
"""
        
        with open(output_path, 'w') as f:
            f.write(md_content)
    
    def _print_summary(self, test_results: Dict[str, Any]):
        """Print test summary to console"""
        print("\n" + "=" * 80)
        print("📋 PLAID INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        print(f"⏱️  Duration: {test_results['duration']:.2f} seconds")
        print(f"📊 Total Tests: {test_results['total_tests']}")
        print(f"✅ Passed: {test_results['passed']}")
        print(f"❌ Failed: {test_results['failed']}")
        print(f"⏭️  Skipped: {test_results['skipped']}")
        print(f"🚨 Errors: {test_results['errors']}")
        
        if test_results['total_tests'] > 0:
            success_rate = (test_results['passed'] / test_results['total_tests']) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\n📂 Test Categories:")
        for category, results in test_results['test_categories'].items():
            status = "✅ PASS" if results['failed'] == 0 and results['errors'] == 0 else "❌ FAIL"
            print(f"   {category.title()}: {status} ({results['passed']}/{results['total']})")
        
        print("\n" + "=" * 80)
        
        if test_results['failed'] > 0 or test_results['errors'] > 0:
            print("⚠️  Some tests failed. Please review the detailed reports.")
            sys.exit(1)
        else:
            print("🎉 All tests passed successfully!")


def main():
    """Main function for test runner"""
    parser = argparse.ArgumentParser(description='Plaid Integration Test Runner')
    parser.add_argument('--category', choices=['all', 'security', 'integration', 'performance', 'compliance'],
                       default='all', help='Test category to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--output-dir', default='test_reports', help='Output directory for reports')
    
    args = parser.parse_args()
    
    runner = PlaidTestRunner(args.output_dir)
    
    if args.category == 'all':
        runner.run_all_tests(args.verbose, args.parallel)
    elif args.category == 'security':
        runner.run_security_tests(args.verbose)
    elif args.category == 'integration':
        runner.run_integration_tests(args.verbose)
    elif args.category == 'performance':
        runner.run_performance_tests(args.verbose)
    elif args.category == 'compliance':
        runner.run_compliance_tests(args.verbose)


if __name__ == '__main__':
    main() 