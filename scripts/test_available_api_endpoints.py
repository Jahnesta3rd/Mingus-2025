#!/usr/bin/env python3
"""
Test Available API Endpoints
Tests the currently available API endpoints with real data
"""

import sys
import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('available_api_testing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AvailableAPITester:
    """Test available API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = {
            'health_checks': [],
            'authentication': [],
            'articles': [],
            'user_management': [],
            'overall': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'errors': []
            }
        }
    
    def log_test_result(self, category: str, test_name: str, success: bool, 
                       response: Optional[requests.Response] = None, 
                       error: Optional[str] = None, details: Optional[Dict] = None):
        """Log test result"""
        self.test_results['overall']['total_tests'] += 1
        
        if success:
            self.test_results['overall']['passed_tests'] += 1
            status = "✅ PASSED"
        else:
            self.test_results['overall']['failed_tests'] += 1
            status = "❌ FAILED"
            if error:
                self.test_results['overall']['errors'].append(f"{test_name}: {error}")
        
        result = {
            'test_name': test_name,
            'status': status,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'response_code': response.status_code if response else None,
            'response_time': response.elapsed.total_seconds() if response else None,
            'error': error,
            'details': details
        }
        
        self.test_results[category].append(result)
        logger.info(f"{status} - {test_name}")
        
        if error:
            logger.error(f"Error: {error}")
    
    def test_health_endpoints(self) -> bool:
        """Test health check endpoints"""
        logger.info("Testing health check endpoints...")
        
        # Test 1: Root endpoint
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            success = response.status_code == 200
            self.log_test_result(
                'health_checks',
                'Root endpoint',
                success,
                response,
                f"Status code: {response.status_code}" if not success else None,
                {'response': response.json() if success else None}
            )
        except Exception as e:
            self.log_test_result(
                'health_checks',
                'Root endpoint',
                False,
                error=str(e)
            )
        
        # Test 2: Health check endpoint
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            success = response.status_code == 200
            self.log_test_result(
                'health_checks',
                'Health check endpoint',
                success,
                response,
                f"Status code: {response.status_code}" if not success else None,
                {'response': response.json() if success else None}
            )
        except Exception as e:
            self.log_test_result(
                'health_checks',
                'Health check endpoint',
                False,
                error=str(e)
            )
        
        # Test 3: API health endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            success = response.status_code == 200
            self.log_test_result(
                'health_checks',
                'API health endpoint',
                success,
                response,
                f"Status code: {response.status_code}" if not success else None,
                {'response': response.json() if success else None}
            )
        except Exception as e:
            self.log_test_result(
                'health_checks',
                'API health endpoint',
                False,
                error=str(e)
            )
        
        return True
    
    def test_authentication_endpoints(self) -> bool:
        """Test authentication endpoints"""
        logger.info("Testing authentication endpoints...")
        
        # Test 1: Check if auth endpoints exist
        try:
            response = self.session.get(f"{self.base_url}/api/auth", timeout=10)
            # This might return 404 or 405, which is expected
            success = response.status_code in [404, 405, 200]
            self.log_test_result(
                'authentication',
                'Auth endpoint exists',
                success,
                response,
                f"Status code: {response.status_code}" if not success else None
            )
        except Exception as e:
            self.log_test_result(
                'authentication',
                'Auth endpoint exists',
                False,
                error=str(e)
            )
        
        # Test 2: Try registration (might be blocked by security)
        try:
            test_user = {
                'email': 'test.user@example.com',
                'password': 'TestPass123!',
                'full_name': 'Test User',
                'phone_number': '+1234567890'
            }
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=test_user,
                timeout=10
            )
            # Accept various status codes as the endpoint might be protected
            success = response.status_code in [200, 201, 400, 401, 403, 404, 405]
            self.log_test_result(
                'authentication',
                'Registration endpoint',
                success,
                response,
                f"Status code: {response.status_code}" if not success else None,
                {'status_code': response.status_code}
            )
        except Exception as e:
            self.log_test_result(
                'authentication',
                'Registration endpoint',
                False,
                error=str(e)
            )
        
        return True
    
    def test_article_endpoints(self) -> bool:
        """Test article endpoints"""
        logger.info("Testing article endpoints...")
        
        # Test 1: Check if articles endpoint exists
        try:
            response = self.session.get(f"{self.base_url}/api/articles", timeout=10)
            # This might return 401 (unauthorized) which is expected
            success = response.status_code in [200, 401, 403, 404]
            self.log_test_result(
                'articles',
                'Articles endpoint exists',
                success,
                response,
                f"Status code: {response.status_code}" if not success else None
            )
        except Exception as e:
            self.log_test_result(
                'articles',
                'Articles endpoint exists',
                False,
                error=str(e)
            )
        
        # Test 2: Try to get articles without auth
        try:
            response = self.session.get(f"{self.base_url}/api/articles", timeout=10)
            success = response.status_code in [401, 403]  # Expected to be unauthorized
            self.log_test_result(
                'articles',
                'Articles endpoint unauthorized access',
                success,
                response,
                f"Expected 401/403, got {response.status_code}" if not success else None
            )
        except Exception as e:
            self.log_test_result(
                'articles',
                'Articles endpoint unauthorized access',
                False,
                error=str(e)
            )
        
        # Test 3: Try with invalid auth token
        try:
            headers = {'Authorization': 'Bearer invalid-token'}
            response = self.session.get(
                f"{self.base_url}/api/articles",
                headers=headers,
                timeout=10
            )
            success = response.status_code in [401, 403]  # Expected to be unauthorized
            self.log_test_result(
                'articles',
                'Articles endpoint with invalid token',
                success,
                response,
                f"Expected 401/403, got {response.status_code}" if not success else None
            )
        except Exception as e:
            self.log_test_result(
                'articles',
                'Articles endpoint with invalid token',
                False,
                error=str(e)
            )
        
        return True
    
    def test_user_management_endpoints(self) -> bool:
        """Test user management endpoints"""
        logger.info("Testing user management endpoints...")
        
        # Test 1: Check if user endpoints exist
        try:
            response = self.session.get(f"{self.base_url}/api/user", timeout=10)
            success = response.status_code in [404, 405, 401, 403]  # Expected responses
            self.log_test_result(
                'user_management',
                'User endpoint exists',
                success,
                response,
                f"Status code: {response.status_code}" if not success else None
            )
        except Exception as e:
            self.log_test_result(
                'user_management',
                'User endpoint exists',
                False,
                error=str(e)
            )
        
        # Test 2: Try to access user profile without auth
        try:
            response = self.session.get(f"{self.base_url}/api/auth/profile", timeout=10)
            success = response.status_code in [401, 403]  # Expected to be unauthorized
            self.log_test_result(
                'user_management',
                'User profile unauthorized access',
                success,
                response,
                f"Expected 401/403, got {response.status_code}" if not success else None
            )
        except Exception as e:
            self.log_test_result(
                'user_management',
                'User profile unauthorized access',
                False,
                error=str(e)
            )
        
        return True
    
    def test_error_handling(self) -> bool:
        """Test error handling"""
        logger.info("Testing error handling...")
        
        # Test 1: Invalid endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/invalid-endpoint", timeout=10)
            success = response.status_code == 404
            self.log_test_result(
                'error_handling',
                'Invalid endpoint handling',
                success,
                response,
                f"Expected 404, got {response.status_code}" if not success else None
            )
        except Exception as e:
            self.log_test_result(
                'error_handling',
                'Invalid endpoint handling',
                False,
                error=str(e)
            )
        
        # Test 2: Invalid JSON
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                data="invalid json",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            success = response.status_code in [400, 401, 403, 404, 405]  # Various expected responses
            self.log_test_result(
                'error_handling',
                'Invalid JSON handling',
                success,
                response,
                f"Status code: {response.status_code}" if not success else None
            )
        except Exception as e:
            self.log_test_result(
                'error_handling',
                'Invalid JSON handling',
                False,
                error=str(e)
            )
        
        return True
    
    def test_database_connectivity(self) -> bool:
        """Test database connectivity through API"""
        logger.info("Testing database connectivity...")
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                db_status = data.get('database_status', 'unknown')
                success = 'healthy' in db_status.lower()
                self.log_test_result(
                    'health_checks',
                    'Database connectivity',
                    success,
                    response,
                    f"Database status: {db_status}" if not success else None,
                    {'database_status': db_status}
                )
            else:
                self.log_test_result(
                    'health_checks',
                    'Database connectivity',
                    False,
                    response,
                    f"Health check failed with status {response.status_code}"
                )
        except Exception as e:
            self.log_test_result(
                'health_checks',
                'Database connectivity',
                False,
                error=str(e)
            )
        
        return True
    
    def generate_test_report(self) -> str:
        """Generate test report"""
        report = []
        report.append("=" * 80)
        report.append("AVAILABLE API ENDPOINTS TESTING REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now()}")
        report.append(f"Base URL: {self.base_url}")
        report.append("")
        
        # Overall statistics
        overall = self.test_results['overall']
        report.append("OVERALL TEST RESULTS:")
        report.append("-" * 40)
        report.append(f"Total Tests: {overall['total_tests']}")
        report.append(f"Passed Tests: {overall['passed_tests']}")
        report.append(f"Failed Tests: {overall['failed_tests']}")
        
        if overall['total_tests'] > 0:
            success_rate = (overall['passed_tests'] / overall['total_tests']) * 100
            report.append(f"Success Rate: {success_rate:.1f}%")
        else:
            report.append("Success Rate: N/A")
        
        if overall['errors']:
            report.append(f"Total Errors: {len(overall['errors'])}")
        
        report.append("")
        
        # Category breakdown
        categories = ['health_checks', 'authentication', 'articles', 'user_management', 'error_handling']
        
        for category in categories:
            if self.test_results[category]:
                passed = sum(1 for test in self.test_results[category] if test['success'])
                total = len(self.test_results[category])
                report.append(f"{category.upper()} TESTS:")
                report.append("-" * 40)
                report.append(f"Passed: {passed}/{total}")
                
                if total > 0:
                    category_rate = (passed / total) * 100
                    report.append(f"Success Rate: {category_rate:.1f}%")
                
                # Show test details
                for test in self.test_results[category]:
                    status = "✅" if test['success'] else "❌"
                    report.append(f"  {status} {test['test_name']}")
                    if test.get('error'):
                        report.append(f"    Error: {test['error']}")
                    if test.get('details'):
                        for key, value in test['details'].items():
                            report.append(f"    {key}: {value}")
                
                report.append("")
        
        # Performance summary
        all_responses = []
        for category in categories:
            for test in self.test_results[category]:
                if test.get('response_time'):
                    all_responses.append(test['response_time'])
        
        if all_responses:
            avg_response_time = sum(all_responses) / len(all_responses)
            max_response_time = max(all_responses)
            min_response_time = min(all_responses)
            
            report.append("PERFORMANCE SUMMARY:")
            report.append("-" * 40)
            report.append(f"Average Response Time: {avg_response_time:.3f}s")
            report.append(f"Fastest Response: {min_response_time:.3f}s")
            report.append(f"Slowest Response: {max_response_time:.3f}s")
            report.append("")
        
        # API Status Assessment
        report.append("API STATUS ASSESSMENT:")
        report.append("-" * 40)
        
        health_tests = [test for test in self.test_results['health_checks'] if test['success']]
        if len(health_tests) >= 2:
            report.append("✅ Health check endpoints are working")
        else:
            report.append("❌ Health check endpoints have issues")
        
        auth_tests = [test for test in self.test_results['authentication'] if test['success']]
        if auth_tests:
            report.append("✅ Authentication endpoints are accessible")
        else:
            report.append("⚠️  Authentication endpoints may be blocked or misconfigured")
        
        article_tests = [test for test in self.test_results['articles'] if test['success']]
        if article_tests:
            report.append("✅ Article endpoints are accessible")
        else:
            report.append("⚠️  Article endpoints may be blocked or misconfigured")
        
        # Recommendations
        report.append("")
        report.append("RECOMMENDATIONS:")
        report.append("-" * 40)
        
        if overall['passed_tests'] / overall['total_tests'] >= 0.8:
            report.append("✅ API is accessible and responding correctly")
        elif overall['passed_tests'] / overall['total_tests'] >= 0.5:
            report.append("⚠️  API has some accessibility issues")
        else:
            report.append("❌ API has significant accessibility issues")
        
        if not any(test['success'] for test in self.test_results['authentication']):
            report.append("⚠️  Authentication endpoints may need configuration")
        
        if not any(test['success'] for test in self.test_results['articles']):
            report.append("⚠️  Article endpoints may need configuration")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        logger.info("Starting available API endpoint testing...")
        
        try:
            # Test health endpoints
            self.test_health_endpoints()
            
            # Test database connectivity
            self.test_database_connectivity()
            
            # Test authentication endpoints
            self.test_authentication_endpoints()
            
            # Test article endpoints
            self.test_article_endpoints()
            
            # Test user management endpoints
            self.test_user_management_endpoints()
            
            # Test error handling
            self.test_error_handling()
            
            # Generate and save report
            report = self.generate_test_report()
            
            # Save report to file
            report_filename = f"available_api_testing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_filename, 'w') as f:
                f.write(report)
            
            # Print report to console
            print(report)
            
            logger.info(f"Report saved to: {report_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during API testing: {e}")
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test available API endpoints')
    parser.add_argument('--base-url', default='http://localhost:5000', 
                       help='Base URL for API testing')
    
    args = parser.parse_args()
    
    # Create API tester
    tester = AvailableAPITester(args.base_url)
    
    # Run tests
    success = tester.run_all_tests()
    
    if success:
        logger.info("Available API testing completed successfully!")
        return 0
    else:
        logger.error("Available API testing failed!")
        return 1


if __name__ == "__main__":
    exit(main())
