#!/usr/bin/env python3
"""
Test script for Mingus Flask Application Health Check Endpoints

This script tests all health check endpoints to ensure they are working correctly
and returning the expected responses.

Usage:
    python tests/test_health_endpoints.py
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:5003"
TIMEOUT = 10  # seconds

class HealthCheckTester:
    """Test class for health check endpoints"""
    
    def __init__(self, base_url: str = BASE_URL, timeout: int = TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.results = []
        
    def test_endpoint(self, endpoint: str, expected_status: int = 200, description: str = "") -> Dict[str, Any]:
        """Test a single health check endpoint"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response_time = time.time() - start_time
            
            result = {
                'endpoint': endpoint,
                'url': url,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'response_time': round(response_time * 1000, 2),  # ms
                'success': response.status_code == expected_status,
                'description': description,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Try to parse JSON response
            try:
                result['response_data'] = response.json()
            except json.JSONDecodeError:
                result['response_data'] = response.text
                result['json_parse_error'] = True
            
            # Additional validation for health check responses
            if response.status_code == 200:
                if isinstance(result['response_data'], dict):
                    # Check for required fields in health responses
                    if 'status' in result['response_data']:
                        result['health_status'] = result['response_data']['status']
                    elif 'success' in result['response_data']:
                        result['health_status'] = 'success' if result['response_data']['success'] else 'failed'
                    elif 'data' in result['response_data']:
                        if isinstance(result['response_data']['data'], dict):
                            if 'overall_status' in result['response_data']['data']:
                                result['health_status'] = result['response_data']['data']['overall_status']
                            elif 'ready' in result['response_data']['data']:
                                result['health_status'] = 'ready' if result['response_data']['data']['ready'] else 'not_ready'
                            elif 'alive' in result['response_data']['data']:
                                result['health_status'] = 'alive' if result['response_data']['data']['alive'] else 'not_alive'
            
        except requests.exceptions.Timeout:
            result = {
                'endpoint': endpoint,
                'url': url,
                'status_code': None,
                'expected_status': expected_status,
                'response_time': None,
                'success': False,
                'description': description,
                'error': 'Timeout',
                'timestamp': datetime.utcnow().isoformat()
            }
        except requests.exceptions.ConnectionError:
            result = {
                'endpoint': endpoint,
                'url': url,
                'status_code': None,
                'expected_status': expected_status,
                'response_time': None,
                'success': False,
                'description': description,
                'error': 'Connection Error',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            result = {
                'endpoint': endpoint,
                'url': url,
                'status_code': None,
                'expected_status': expected_status,
                'response_time': None,
                'success': False,
                'description': description,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        self.results.append(result)
        return result
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all health check endpoint tests"""
        print("🔍 Testing Mingus Flask Application Health Check Endpoints")
        print("=" * 60)
        
        # Define all endpoints to test
        endpoints = [
            # Basic health endpoints
            ('/health', 200, 'Basic application health check'),
            ('/health/standard', 200, 'Standardized health check with consistent response format'),
            ('/health/metrics', 200, 'Health check with comprehensive Prometheus metrics'),
            ('/health/detailed', 200, 'Detailed health check with comprehensive system checks'),
            ('/health/database', 200, 'Database health check with connection pool monitoring'),
            ('/health/redis', 200, 'Redis health check with cache operations and memory monitoring'),
            ('/health/external', 200, 'External services health check (Supabase, Stripe, Resend, Twilio)'),
            
            # Prometheus metrics endpoint
            ('/metrics', 200, 'Prometheus metrics endpoint'),
            
            # System health endpoints
            ('/api/system/health/', 200, 'Comprehensive system health check'),
            ('/api/system/health/simple', 200, 'Simple health check for load balancers'),
            ('/api/system/health/detailed', 200, 'Detailed health check with system info'),
            
            # Kubernetes/Container orchestration endpoints
            ('/api/system/health/readiness', 200, 'Kubernetes readiness probe'),
            ('/api/system/health/liveness', 200, 'Kubernetes liveness probe'),
            ('/api/system/health/startup', 200, 'Kubernetes startup probe'),
            
            # Individual service health checks
            ('/api/system/health/database', 200, 'Database health check'),
            ('/api/system/health/redis', 200, 'Redis health check'),
            ('/api/system/health/external', 200, 'External services health check'),
            ('/api/system/health/resources', 200, 'System resources health check'),
            ('/api/system/health/application', 200, 'Application health check'),
            
            # Monitoring metrics endpoint
            ('/api/system/health/metrics', 200, 'Health metrics for monitoring systems'),
        ]
        
        # Run tests
        for endpoint, expected_status, description in endpoints:
            print(f"\n📡 Testing: {endpoint}")
            print(f"   Description: {description}")
            
            result = self.test_endpoint(endpoint, expected_status, description)
            
            if result['success']:
                print(f"   ✅ PASS - Status: {result['status_code']}, Time: {result['response_time']}ms")
                if 'health_status' in result:
                    print(f"   Health Status: {result['health_status']}")
            else:
                print(f"   ❌ FAIL - Expected: {expected_status}, Got: {result.get('status_code', 'N/A')}")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
        
        return self.results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result['success']:
                    print(f"   - {result['endpoint']}: {result.get('error', f'Status {result.get("status_code", "N/A")}')}")
        
        # Performance summary
        response_times = [r['response_time'] for r in self.results if r['response_time'] is not None]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print(f"\n⚡ PERFORMANCE:")
            print(f"   Average Response Time: {avg_response_time:.2f}ms")
            print(f"   Fastest Response: {min_response_time:.2f}ms")
            print(f"   Slowest Response: {max_response_time:.2f}ms")
        
        return passed_tests == total_tests
    
    def save_results(self, filename: str = "health_check_results.json"):
        """Save test results to JSON file"""
        output = {
            'test_run': {
                'timestamp': datetime.utcnow().isoformat(),
                'base_url': self.base_url,
                'timeout': self.timeout
            },
            'results': self.results,
            'summary': {
                'total_tests': len(self.results),
                'passed_tests': sum(1 for r in self.results if r['success']),
                'failed_tests': sum(1 for r in self.results if not r['success'])
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")

def main():
    """Main function"""
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server is running but root endpoint returned status {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("   Make sure the Flask application is running on port 5003")
        print("   Run: python app.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        sys.exit(1)
    
    # Run tests
    tester = HealthCheckTester()
    results = tester.run_all_tests()
    
    # Print summary
    success = tester.print_summary()
    
    # Save results
    tester.save_results()
    
    # Exit with appropriate code
    if success:
        print("\n🎉 All health check endpoints are working correctly!")
        sys.exit(0)
    else:
        print("\n⚠️  Some health check endpoints failed. Check the details above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 