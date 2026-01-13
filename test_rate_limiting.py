#!/usr/bin/env python3
"""
Comprehensive Rate Limiting Test Suite

Tests Flask-Limiter rate limiting functionality including:
- Default rate limits
- Rate limit exceeded responses
- Rate limit headers
- Different endpoints
- IP-based limiting
- Rate limit reset
- Concurrent requests

Usage:
    python test_rate_limiting.py [--base-url http://localhost:5000] [--limit 100]
"""

import os
import sys
import time
import json
import argparse
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
class RateLimitTestResult:
    """Rate limit test result"""
    test_name: str
    status: str  # 'PASS', 'FAIL', 'WARN'
    message: str
    details: Dict[str, Any]
    timestamp: str

class RateLimitingTester:
    """Comprehensive rate limiting tester"""
    
    def __init__(self, base_url: str = "http://localhost:5000", expected_limit: int = 100):
        self.base_url = base_url.rstrip('/')
        self.expected_limit = expected_limit
        self.results: List[RateLimitTestResult] = []
        self.session = requests.Session()
        
    def log_result(self, test_name: str, status: str, message: str, details: Dict = None):
        """Log test result"""
        result = RateLimitTestResult(
            test_name=test_name,
            status=status,
            message=message,
            details=details or {},
            timestamp=datetime.now().isoformat()
        )
        self.results.append(result)
        
        status_color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_color}{status_symbol} {test_name}{Colors.RESET}: {message}")
        if details:
            for key, value in details.items():
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, indent=2)
                print(f"    {Colors.CYAN}{key}{Colors.RESET}: {value}")
    
    # ============================================================================
    # BASIC RATE LIMIT TESTS
    # ============================================================================
    
    def test_basic_rate_limit(self):
        """Test basic rate limiting - make requests up to limit"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Test 1: Basic Rate Limiting{Colors.RESET}")
        
        endpoint = '/health'
        successful_requests = 0
        rate_limited_requests = 0
        
        print(f"Making {self.expected_limit + 10} requests to {endpoint}...")
        
        for i in range(self.expected_limit + 10):
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    successful_requests += 1
                elif response.status_code == 429:
                    rate_limited_requests += 1
                    if rate_limited_requests == 1:
                        # Check rate limit headers on first 429
                        headers = response.headers
                        self.log_result(
                            "Rate Limit Headers (429)",
                            "INFO",
                            "Checking rate limit headers",
                            {
                                'X-RateLimit-Limit': headers.get('X-RateLimit-Limit'),
                                'X-RateLimit-Remaining': headers.get('X-RateLimit-Remaining'),
                                'X-RateLimit-Reset': headers.get('X-RateLimit-Reset'),
                                'Retry-After': headers.get('Retry-After'),
                            }
                        )
                else:
                    self.log_result(
                        f"Unexpected Status Code",
                        "WARN",
                        f"Got status {response.status_code} instead of 200 or 429",
                        {'status_code': response.status_code}
                    )
                
                # Small delay to avoid overwhelming
                if i % 10 == 0:
                    time.sleep(0.1)
                    
            except Exception as e:
                self.log_result(
                    "Request Error",
                    "FAIL",
                    f"Error making request: {str(e)}",
                    {'error': str(e)}
                )
                break
        
        # Evaluate results
        if successful_requests <= self.expected_limit:
            self.log_result(
                "Basic Rate Limit",
                "PASS",
                f"Rate limiting working: {successful_requests} requests allowed (limit: {self.expected_limit})",
                {
                    'successful': successful_requests,
                    'rate_limited': rate_limited_requests,
                    'expected_limit': self.expected_limit
                }
            )
        else:
            self.log_result(
                "Basic Rate Limit",
                "FAIL",
                f"Rate limit not enforced: {successful_requests} requests allowed (limit: {self.expected_limit})",
                {
                    'successful': successful_requests,
                    'rate_limited': rate_limited_requests,
                    'expected_limit': self.expected_limit
                }
            )
    
    def test_rate_limit_headers(self):
        """Test rate limit headers in responses"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Test 2: Rate Limit Headers{Colors.RESET}")
        
        endpoint = '/health'
        
        try:
            response = self.session.get(f"{self.base_url}{endpoint}")
            headers = response.headers
            
            # Check for rate limit headers
            rate_limit_headers = {
                'X-RateLimit-Limit': headers.get('X-RateLimit-Limit'),
                'X-RateLimit-Remaining': headers.get('X-RateLimit-Remaining'),
                'X-RateLimit-Reset': headers.get('X-RateLimit-Reset'),
            }
            
            if any(rate_limit_headers.values()):
                self.log_result(
                    "Rate Limit Headers Present",
                    "PASS",
                    "Rate limit headers found in response",
                    rate_limit_headers
                )
                
                # Validate header values
                limit = headers.get('X-RateLimit-Limit')
                remaining = headers.get('X-RateLimit-Remaining')
                
                if limit:
                    try:
                        limit_int = int(limit)
                        if limit_int == self.expected_limit:
                            self.log_result(
                                "Rate Limit Header Value",
                                "PASS",
                                f"X-RateLimit-Limit matches expected: {limit_int}",
                                {}
                            )
                        else:
                            self.log_result(
                                "Rate Limit Header Value",
                                "WARN",
                                f"X-RateLimit-Limit mismatch: expected {self.expected_limit}, got {limit_int}",
                                {}
                            )
                    except ValueError:
                        self.log_result(
                            "Rate Limit Header Format",
                            "WARN",
                            f"X-RateLimit-Limit is not a number: {limit}",
                            {}
                        )
                
                if remaining:
                    try:
                        remaining_int = int(remaining)
                        if remaining_int >= 0:
                            self.log_result(
                                "Rate Limit Remaining",
                                "PASS",
                                f"X-RateLimit-Remaining is valid: {remaining_int}",
                                {}
                            )
                        else:
                            self.log_result(
                                "Rate Limit Remaining",
                                "WARN",
                                f"X-RateLimit-Remaining is negative: {remaining_int}",
                                {}
                            )
                    except ValueError:
                        self.log_result(
                            "Rate Limit Remaining Format",
                            "WARN",
                            f"X-RateLimit-Remaining is not a number: {remaining}",
                            {}
                        )
            else:
                self.log_result(
                    "Rate Limit Headers Present",
                    "WARN",
                    "Rate limit headers not found in response",
                    {'headers': dict(headers)}
                )
                
        except Exception as e:
            self.log_result(
                "Rate Limit Headers Test",
                "FAIL",
                f"Error testing headers: {str(e)}",
                {'error': str(e)}
            )
    
    def test_rate_limit_exceeded_response(self):
        """Test rate limit exceeded response format"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Test 3: Rate Limit Exceeded Response{Colors.RESET}")
        
        endpoint = '/health'
        
        # Make requests until we hit the limit
        print(f"Making requests until rate limit is exceeded...")
        for i in range(self.expected_limit + 5):
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 429:
                # Check 429 response
                self.log_result(
                    "Rate Limit Exceeded Status",
                    "PASS",
                    "Received 429 status code",
                    {'status_code': response.status_code}
                )
                
                # Check response body
                try:
                    body = response.json()
                    if 'error' in body or 'message' in body:
                        self.log_result(
                            "Rate Limit Error Message",
                            "PASS",
                            "Error message present in response",
                            {'body': body}
                        )
                    else:
                        self.log_result(
                            "Rate Limit Error Message",
                            "WARN",
                            "No error message in response body",
                            {'body': body}
                        )
                except:
                    self.log_result(
                        "Rate Limit Response Body",
                        "WARN",
                        "Response body is not JSON",
                        {'body': response.text[:100]}
                    )
                
                # Check Retry-After header
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    self.log_result(
                        "Retry-After Header",
                        "PASS",
                        f"Retry-After header present: {retry_after}",
                        {}
                    )
                else:
                    self.log_result(
                        "Retry-After Header",
                        "WARN",
                        "Retry-After header not present",
                        {}
                    )
                
                break
            time.sleep(0.01)
    
    def test_different_endpoints(self):
        """Test rate limiting across different endpoints"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Test 4: Rate Limiting Across Endpoints{Colors.RESET}")
        
        endpoints = ['/health', '/api/status']
        results = {}
        
        for endpoint in endpoints:
            try:
                # Make a few requests to each endpoint
                successful = 0
                for i in range(5):
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        successful += 1
                    time.sleep(0.1)
                
                results[endpoint] = successful
                
                self.log_result(
                    f"Endpoint Rate Limit: {endpoint}",
                    "PASS" if successful == 5 else "WARN",
                    f"{successful}/5 requests successful",
                    {'endpoint': endpoint, 'successful': successful}
                )
                
            except Exception as e:
                self.log_result(
                    f"Endpoint Rate Limit: {endpoint}",
                    "FAIL",
                    f"Error testing endpoint: {str(e)}",
                    {'error': str(e)}
                )
    
    def test_rate_limit_reset(self):
        """Test that rate limit resets after time window"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Test 5: Rate Limit Reset{Colors.RESET}")
        
        endpoint = '/health'
        
        # Exhaust rate limit
        print("Exhausting rate limit...")
        for i in range(self.expected_limit + 5):
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 429:
                break
            time.sleep(0.01)
        
        # Wait for rate limit window (1 minute)
        print(f"Waiting for rate limit window to reset (60 seconds)...")
        print("(This test will take 60 seconds)")
        
        wait_time = 60
        for remaining in range(wait_time, 0, -10):
            print(f"  Waiting {remaining} seconds...")
            time.sleep(10)
        
        # Try requests again
        print("Testing if rate limit has reset...")
        successful_after_reset = 0
        for i in range(5):
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 200:
                successful_after_reset += 1
            time.sleep(0.1)
        
        if successful_after_reset > 0:
            self.log_result(
                "Rate Limit Reset",
                "PASS",
                f"Rate limit reset working: {successful_after_reset}/5 requests successful after reset",
                {'successful_after_reset': successful_after_reset}
            )
        else:
            self.log_result(
                "Rate Limit Reset",
                "WARN",
                "Rate limit may not have reset, or window is longer than 60 seconds",
                {'successful_after_reset': successful_after_reset}
            )
    
    def test_concurrent_requests(self):
        """Test rate limiting with concurrent requests"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Test 6: Concurrent Requests{Colors.RESET}")
        
        endpoint = '/health'
        num_threads = 20
        num_requests_per_thread = 10
        
        def make_request(thread_id):
            """Make requests from a thread"""
            results = {'success': 0, 'rate_limited': 0, 'errors': 0}
            for i in range(num_requests_per_thread):
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        results['success'] += 1
                    elif response.status_code == 429:
                        results['rate_limited'] += 1
                    else:
                        results['errors'] += 1
                    time.sleep(0.01)
                except Exception as e:
                    results['errors'] += 1
            return results
        
        print(f"Making {num_threads} concurrent requests ({num_requests_per_thread} each)...")
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_threads)]
            all_results = []
            for future in as_completed(futures):
                all_results.append(future.result())
        
        # Aggregate results
        total_success = sum(r['success'] for r in all_results)
        total_rate_limited = sum(r['rate_limited'] for r in all_results)
        total_errors = sum(r['errors'] for r in all_results)
        
        self.log_result(
            "Concurrent Requests",
            "PASS" if total_rate_limited > 0 else "WARN",
            f"Concurrent requests handled: {total_success} success, {total_rate_limited} rate limited, {total_errors} errors",
            {
                'total_requests': num_threads * num_requests_per_thread,
                'successful': total_success,
                'rate_limited': total_rate_limited,
                'errors': total_errors
            }
        )
    
    def test_ip_based_limiting(self):
        """Test that rate limiting is IP-based"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Test 7: IP-Based Rate Limiting{Colors.RESET}")
        
        endpoint = '/health'
        
        # Create a new session (simulates different IP)
        new_session = requests.Session()
        
        # Exhaust rate limit with first session
        print("Exhausting rate limit with first session...")
        for i in range(self.expected_limit + 5):
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 429:
                break
            time.sleep(0.01)
        
        # Try with new session (should work if IP-based)
        print("Testing with new session (different IP simulation)...")
        new_session_successful = 0
        for i in range(5):
            try:
                response = new_session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    new_session_successful += 1
            except:
                pass
            time.sleep(0.1)
        
        # Note: This test may not work perfectly if both sessions share the same IP
        # But it tests the concept
        self.log_result(
            "IP-Based Rate Limiting",
            "INFO",
            f"New session results: {new_session_successful}/5 successful",
            {
                'note': 'Both sessions may share same IP, so results may vary',
                'new_session_successful': new_session_successful
            }
        )
    
    # ============================================================================
    # MAIN TEST RUNNER
    # ============================================================================
    
    def run_all_tests(self, skip_reset_test: bool = False):
        """Run all rate limiting tests"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}MINGUS Rate Limiting Test Suite{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"Target: {self.base_url}")
        print(f"Expected Limit: {self.expected_limit} requests per minute")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        # Run tests
        self.test_basic_rate_limit()
        self.test_rate_limit_headers()
        self.test_rate_limit_exceeded_response()
        self.test_different_endpoints()
        self.test_concurrent_requests()
        self.test_ip_based_limiting()
        
        if not skip_reset_test:
            self.test_rate_limit_reset()
        else:
            print(f"\n{Colors.YELLOW}⚠️  Skipping rate limit reset test (use --skip-reset to skip){Colors.RESET}")
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}RATE LIMITING TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        total = len(self.results)
        passed = len([r for r in self.results if r.status == "PASS"])
        failed = len([r for r in self.results if r.status == "FAIL"])
        warnings = len([r for r in self.results if r.status == "WARN"])
        info = len([r for r in self.results if r.status == "INFO"])
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnings: {warnings}{Colors.RESET}")
        print(f"{Colors.CYAN}Info: {info}{Colors.RESET}")
        
        # List failed tests
        failed_tests = [r for r in self.results if r.status == "FAIL"]
        if failed_tests:
            print(f"\n{Colors.BOLD}{Colors.RED}Failed Tests:{Colors.RESET}")
            for result in failed_tests:
                print(f"  ❌ {result.test_name}: {result.message}")
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    def save_results(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"rate_limiting_test_results_{timestamp}.json"
        
        results_dict = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'expected_limit': self.expected_limit,
            'summary': {
                'total': len(self.results),
                'passed': len([r for r in self.results if r.status == "PASS"]),
                'failed': len([r for r in self.results if r.status == "FAIL"]),
                'warnings': len([r for r in self.results if r.status == "WARN"]),
            },
            'results': [asdict(r) for r in self.results]
        }
        
        with open(filename, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"\n{Colors.CYAN}Results saved to: {filename}{Colors.RESET}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Rate Limiting Test Suite')
    parser.add_argument(
        '--base-url',
        default='http://localhost:5000',
        help='Base URL of the backend API (default: http://localhost:5000)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Expected rate limit per minute (default: 100)'
    )
    parser.add_argument(
        '--skip-reset',
        action='store_true',
        help='Skip the rate limit reset test (saves 60 seconds)'
    )
    
    args = parser.parse_args()
    
    tester = RateLimitingTester(base_url=args.base_url, expected_limit=args.limit)
    tester.run_all_tests(skip_reset_test=args.skip_reset)

if __name__ == '__main__':
    main()
