#!/usr/bin/env python3
"""
Comprehensive Security Test Runner for Mingus Backend

Runs all security test suites:
1. Comprehensive Backend Security Tests
2. Rate Limiting Tests
3. Input Validation & Sanitization Tests
4. CORS Configuration Verification

Usage:
    python run_all_security_tests.py [--base-url http://localhost:5000] [--skip-rate-reset]
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

@dataclass
class TestSuiteResult:
    """Test suite result"""
    suite_name: str
    status: str  # 'PASS', 'FAIL', 'WARN'
    total_tests: int
    passed: int
    failed: int
    warnings: int
    execution_time: float
    details: Dict[str, Any]

class SecurityTestRunner:
    """Comprehensive security test runner"""
    
    def __init__(self, base_url: str = "http://localhost:5000", skip_rate_reset: bool = False):
        self.base_url = base_url
        self.skip_rate_reset = skip_rate_reset
        self.suite_results: List[TestSuiteResult] = []
        self.test_scripts = [
            {
                'name': 'Comprehensive Backend Security',
                'script': 'comprehensive_backend_security_tests.py',
                'args': ['--base-url', base_url]
            },
            {
                'name': 'Rate Limiting',
                'script': 'test_rate_limiting.py',
                'args': ['--base-url', base_url, '--limit', '100']
            },
            {
                'name': 'Input Validation & Sanitization',
                'script': 'test_input_validation_sanitization.py',
                'args': ['--base-url', base_url]
            },
            {
                'name': 'CORS Configuration',
                'script': 'verify_cors_configuration.py',
                'args': ['--base-url', base_url]
            }
        ]
        
        # Add skip-reset flag if requested
        if skip_rate_reset:
            for suite in self.test_scripts:
                if suite['name'] == 'Rate Limiting':
                    suite['args'].append('--skip-reset')
    
    def run_test_suite(self, suite_config: Dict) -> TestSuiteResult:
        """Run a single test suite"""
        suite_name = suite_config['name']
        script = suite_config['script']
        args = suite_config['args']
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}Running: {suite_name}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"Script: {script}")
        print(f"Arguments: {' '.join(args)}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")
        
        start_time = datetime.now()
        
        try:
            # Run the test script
            result = subprocess.run(
                [sys.executable, script] + args,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"{Colors.YELLOW}Stderr:{Colors.RESET}")
                print(result.stderr)
            
            # Parse results from JSON files if available
            # (Test scripts save results to JSON files)
            results_file = self._find_latest_results_file(suite_name)
            parsed_results = self._parse_results_file(results_file) if results_file else None
            
            # Determine status
            if result.returncode == 0:
                if parsed_results:
                    status = self._determine_status(parsed_results)
                    total = parsed_results.get('summary', {}).get('total', 0)
                    passed = parsed_results.get('summary', {}).get('passed', 0)
                    failed = parsed_results.get('summary', {}).get('failed', 0)
                    warnings = parsed_results.get('summary', {}).get('warnings', 0)
                else:
                    status = "PASS"
                    total = passed = failed = warnings = 0
            else:
                status = "FAIL"
                total = passed = failed = warnings = 0
            
            suite_result = TestSuiteResult(
                suite_name=suite_name,
                status=status,
                total_tests=total,
                passed=passed,
                failed=failed,
                warnings=warnings,
                execution_time=execution_time,
                details={
                    'returncode': result.returncode,
                    'script': script,
                    'results_file': results_file,
                    'parsed_results': parsed_results
                }
            )
            
            self.suite_results.append(suite_result)
            
            # Print suite summary
            status_color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
            status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            
            print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
            print(f"{status_color}{status_symbol} {suite_name} Complete{Colors.RESET}")
            print(f"  Status: {status_color}{status}{Colors.RESET}")
            print(f"  Total Tests: {total}")
            print(f"  {Colors.GREEN}Passed: {passed}{Colors.RESET}")
            print(f"  {Colors.RED}Failed: {failed}{Colors.RESET}")
            print(f"  {Colors.YELLOW}Warnings: {warnings}{Colors.RESET}")
            print(f"  Execution Time: {execution_time:.2f}s")
            print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")
            
            return suite_result
            
        except subprocess.TimeoutExpired:
            execution_time = (datetime.now() - start_time).total_seconds()
            print(f"{Colors.RED}❌ Test suite timed out after {execution_time:.2f} seconds{Colors.RESET}")
            
            suite_result = TestSuiteResult(
                suite_name=suite_name,
                status="FAIL",
                total_tests=0,
                passed=0,
                failed=0,
                warnings=0,
                execution_time=execution_time,
                details={'error': 'Timeout'}
            )
            self.suite_results.append(suite_result)
            return suite_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            print(f"{Colors.RED}❌ Error running test suite: {str(e)}{Colors.RESET}")
            
            suite_result = TestSuiteResult(
                suite_name=suite_name,
                status="FAIL",
                total_tests=0,
                passed=0,
                failed=0,
                warnings=0,
                execution_time=execution_time,
                details={'error': str(e)}
            )
            self.suite_results.append(suite_result)
            return suite_result
    
    def _find_latest_results_file(self, suite_name: str) -> str:
        """Find the latest results file for a test suite"""
        import glob
        
        patterns = {
            'Comprehensive Backend Security': 'backend_security_test_results_*.json',
            'Rate Limiting': 'rate_limiting_test_results_*.json',
            'Input Validation & Sanitization': 'input_validation_test_results_*.json',
            'CORS Configuration': 'cors_verification_results_*.json'
        }
        
        pattern = patterns.get(suite_name)
        if not pattern:
            return None
        
        files = glob.glob(pattern)
        if not files:
            return None
        
        # Return the most recent file
        return max(files, key=os.path.getctime)
    
    def _parse_results_file(self, filepath: str) -> Dict:
        """Parse results from JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not parse results file {filepath}: {e}{Colors.RESET}")
            return None
    
    def _determine_status(self, results: Dict) -> str:
        """Determine overall status from results"""
        summary = results.get('summary', {})
        failed = summary.get('failed', 0)
        warnings = summary.get('warnings', 0)
        total = summary.get('total', 0)
        
        if failed > 0:
            return "FAIL"
        elif warnings > total * 0.2:  # More than 20% warnings
            return "WARN"
        else:
            return "PASS"
    
    def run_all_tests(self):
        """Run all security test suites"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}MINGUS Backend Security Test Suite Runner{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Suites: {len(self.test_scripts)}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")
        
        # Run each test suite
        for suite_config in self.test_scripts:
            self.run_test_suite(suite_config)
        
        # Print overall summary
        self.print_overall_summary()
        
        # Save combined results
        self.save_combined_results()
    
    def print_overall_summary(self):
        """Print overall test summary"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}OVERALL SECURITY TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")
        
        total_suites = len(self.suite_results)
        total_tests = sum(r.total_tests for r in self.suite_results)
        total_passed = sum(r.passed for r in self.suite_results)
        total_failed = sum(r.failed for r in self.suite_results)
        total_warnings = sum(r.warnings for r in self.suite_results)
        total_time = sum(r.execution_time for r in self.suite_results)
        
        print(f"{Colors.BOLD}Test Suites:{Colors.RESET} {total_suites}")
        print(f"{Colors.BOLD}Total Tests:{Colors.RESET} {total_tests}")
        print(f"{Colors.GREEN}Total Passed:{Colors.RESET} {total_passed}")
        print(f"{Colors.RED}Total Failed:{Colors.RESET} {total_failed}")
        print(f"{Colors.YELLOW}Total Warnings:{Colors.RESET} {total_warnings}")
        print(f"{Colors.BOLD}Total Execution Time:{Colors.RESET} {total_time:.2f}s")
        
        if total_tests > 0:
            pass_rate = (total_passed / total_tests) * 100
            print(f"{Colors.BOLD}Pass Rate:{Colors.RESET} {pass_rate:.1f}%")
        
        print(f"\n{Colors.BOLD}Results by Suite:{Colors.RESET}\n")
        
        for result in self.suite_results:
            status_color = Colors.GREEN if result.status == "PASS" else Colors.RED if result.status == "FAIL" else Colors.YELLOW
            status_symbol = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⚠️"
            
            print(f"  {status_color}{status_symbol} {result.suite_name}{Colors.RESET}")
            print(f"    Status: {status_color}{result.status}{Colors.RESET}")
            print(f"    Tests: {result.total_tests} | {Colors.GREEN}Passed: {result.passed}{Colors.RESET} | {Colors.RED}Failed: {result.failed}{Colors.RESET} | {Colors.YELLOW}Warnings: {result.warnings}{Colors.RESET}")
            print(f"    Time: {result.execution_time:.2f}s")
            print()
        
        # Overall status
        if total_failed > 0:
            overall_status = f"{Colors.RED}❌ FAILED{Colors.RESET}"
        elif total_warnings > total_tests * 0.2:
            overall_status = f"{Colors.YELLOW}⚠️  WARNINGS{Colors.RESET}"
        else:
            overall_status = f"{Colors.GREEN}✅ PASSED{Colors.RESET}"
        
        print(f"{Colors.BOLD}Overall Status:{Colors.RESET} {overall_status}")
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")
    
    def save_combined_results(self):
        """Save combined test results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"all_security_tests_results_{timestamp}.json"
        
        total_tests = sum(r.total_tests for r in self.suite_results)
        total_passed = sum(r.passed for r in self.suite_results)
        total_failed = sum(r.failed for r in self.suite_results)
        total_warnings = sum(r.warnings for r in self.suite_results)
        
        results_dict = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'summary': {
                'total_suites': len(self.suite_results),
                'total_tests': total_tests,
                'total_passed': total_passed,
                'total_failed': total_failed,
                'total_warnings': total_warnings,
                'pass_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0
            },
            'suites': [asdict(r) for r in self.suite_results]
        }
        
        with open(filename, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"{Colors.CYAN}Combined results saved to: {filename}{Colors.RESET}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Comprehensive Security Test Runner')
    parser.add_argument(
        '--base-url',
        default='http://localhost:5000',
        help='Base URL of the backend API (default: http://localhost:5000)'
    )
    parser.add_argument(
        '--skip-rate-reset',
        action='store_true',
        help='Skip the rate limit reset test (saves 60 seconds)'
    )
    
    args = parser.parse_args()
    
    runner = SecurityTestRunner(base_url=args.base_url, skip_rate_reset=args.skip_rate_reset)
    runner.run_all_tests()

if __name__ == '__main__':
    main()
