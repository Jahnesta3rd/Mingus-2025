#!/usr/bin/env python3
"""
Comprehensive API Testing Script
Tests all 15+ API endpoints with real data, authentication, recommendations, progress tracking, and rate limiting
"""

import sys
import os
import json
import time
import requests
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_testing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class APITester:
    """Comprehensive API testing system"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = {
            'authentication': [],
            'user_management': [],
            'articles': [],
            'recommendations': [],
            'progress_tracking': [],
            'bookmarks': [],
            'rate_limiting': [],
            'error_handling': [],
            'overall': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'errors': []
            }
        }
        
        # Test data
        self.test_users = {
            'beginner': {
                'email': 'test.beginner@example.com',
                'password': 'TestPass123!',
                'full_name': 'Test Beginner User',
                'phone_number': '+1234567890'
            },
            'intermediate': {
                'email': 'test.intermediate@example.com',
                'password': 'TestPass123!',
                'full_name': 'Test Intermediate User',
                'phone_number': '+1234567891'
            },
            'advanced': {
                'email': 'test.advanced@example.com',
                'password': 'TestPass123!',
                'full_name': 'Test Advanced User',
                'phone_number': '+1234567892'
            }
        }
        
        self.auth_tokens = {}
        self.test_articles = []
    
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
    
    def test_authentication_endpoints(self) -> bool:
        """Test authentication endpoints"""
        logger.info("Testing authentication endpoints...")
        
        # Test 1: User Registration
        for user_type, user_data in self.test_users.items():
            try:
                response = self.session.post(
                    f"{self.base_url}/api/auth/register",
                    json=user_data,
                    timeout=10
                )
                
                success = response.status_code in [200, 201, 409]  # 409 for existing user
                self.log_test_result(
                    'authentication',
                    f'Register {user_type} user',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None,
                    {'status_code': response.status_code, 'response': response.json() if response.content else None}
                )
                
            except Exception as e:
                self.log_test_result(
                    'authentication',
                    f'Register {user_type} user',
                    False,
                    error=str(e)
                )
        
        # Test 2: User Login
        for user_type, user_data in self.test_users.items():
            try:
                response = self.session.post(
                    f"{self.base_url}/api/auth/login",
                    json={
                        'email': user_data['email'],
                        'password': user_data['password']
                    },
                    timeout=10
                )
                
                success = response.status_code == 200
                if success:
                    data = response.json()
                    if 'access_token' in data:
                        self.auth_tokens[user_type] = data['access_token']
                
                self.log_test_result(
                    'authentication',
                    f'Login {user_type} user',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None,
                    {'status_code': response.status_code, 'has_token': 'access_token' in data if success else False}
                )
                
            except Exception as e:
                self.log_test_result(
                    'authentication',
                    f'Login {user_type} user',
                    False,
                    error=str(e)
                )
        
        # Test 3: Check Authentication Status
        for user_type, token in self.auth_tokens.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.get(
                    f"{self.base_url}/api/auth/check-auth",
                    headers=headers,
                    timeout=10
                )
                
                success = response.status_code == 200
                self.log_test_result(
                    'authentication',
                    f'Check auth status {user_type}',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None
                )
                
            except Exception as e:
                self.log_test_result(
                    'authentication',
                    f'Check auth status {user_type}',
                    False,
                    error=str(e)
                )
        
        # Test 4: Get User Profile
        for user_type, token in self.auth_tokens.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.get(
                    f"{self.base_url}/api/auth/profile",
                    headers=headers,
                    timeout=10
                )
                
                success = response.status_code == 200
                self.log_test_result(
                    'authentication',
                    f'Get profile {user_type}',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None
                )
                
            except Exception as e:
                self.log_test_result(
                    'authentication',
                    f'Get profile {user_type}',
                    False,
                    error=str(e)
                )
        
        return len(self.auth_tokens) > 0
    
    def test_article_endpoints(self) -> bool:
        """Test article-related endpoints"""
        logger.info("Testing article endpoints...")
        
        if not self.auth_tokens:
            logger.warning("No auth tokens available for article testing")
            return False
        
        # Test 1: Get Articles List
        for user_type, token in self.auth_tokens.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.get(
                    f"{self.base_url}/api/articles",
                    headers=headers,
                    timeout=10
                )
                
                success = response.status_code == 200
                if success:
                    data = response.json()
                    if 'articles' in data and data['articles']:
                        self.test_articles = data['articles'][:3]  # Store first 3 articles for testing
                
                self.log_test_result(
                    'articles',
                    f'Get articles list {user_type}',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None,
                    {'article_count': len(self.test_articles) if success else 0}
                )
                
            except Exception as e:
                self.log_test_result(
                    'articles',
                    f'Get articles list {user_type}',
                    False,
                    error=str(e)
                )
        
        # Test 2: Get Specific Article
        if self.test_articles:
            for user_type, token in self.auth_tokens.items():
                for i, article in enumerate(self.test_articles[:2]):  # Test first 2 articles
                    try:
                        headers = {'Authorization': f'Bearer {token}'}
                        response = self.session.get(
                            f"{self.base_url}/api/articles/{article.get('id', 'test-id')}",
                            headers=headers,
                            timeout=10
                        )
                        
                        success = response.status_code in [200, 404]  # 404 is acceptable for test IDs
                        self.log_test_result(
                            'articles',
                            f'Get article {i+1} {user_type}',
                            success,
                            response,
                            f"Status code: {response.status_code}" if not success else None
                        )
                        
                    except Exception as e:
                        self.log_test_result(
                            'articles',
                            f'Get article {i+1} {user_type}',
                            False,
                            error=str(e)
                        )
        
        # Test 3: Search Articles
        for user_type, token in self.auth_tokens.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.get(
                    f"{self.base_url}/api/articles/search",
                    headers=headers,
                    params={'q': 'financial', 'phase': 'DO'},
                    timeout=10
                )
                
                success = response.status_code == 200
                self.log_test_result(
                    'articles',
                    f'Search articles {user_type}',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None
                )
                
            except Exception as e:
                self.log_test_result(
                    'articles',
                    f'Search articles {user_type}',
                    False,
                    error=str(e)
                )
        
        return True
    
    def test_recommendation_endpoints(self) -> bool:
        """Test article recommendation endpoints"""
        logger.info("Testing recommendation endpoints...")
        
        if not self.auth_tokens:
            logger.warning("No auth tokens available for recommendation testing")
            return False
        
        # Test 1: Get Article Recommendations
        for user_type, token in self.auth_tokens.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.get(
                    f"{self.base_url}/api/articles/recommendations",
                    headers=headers,
                    timeout=10
                )
                
                success = response.status_code == 200
                self.log_test_result(
                    'recommendations',
                    f'Get recommendations {user_type}',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None
                )
                
            except Exception as e:
                self.log_test_result(
                    'recommendations',
                    f'Get recommendations {user_type}',
                    False,
                    error=str(e)
                )
        
        # Test 2: Get Personalized Recommendations
        for user_type, token in self.auth_tokens.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.get(
                    f"{self.base_url}/api/articles/recommendations/personalized",
                    headers=headers,
                    params={'limit': 5, 'phase': 'DO'},
                    timeout=10
                )
                
                success = response.status_code == 200
                self.log_test_result(
                    'recommendations',
                    f'Get personalized recommendations {user_type}',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None
                )
                
            except Exception as e:
                self.log_test_result(
                    'recommendations',
                    f'Get personalized recommendations {user_type}',
                    False,
                    error=str(e)
                )
        
        return True
    
    def test_progress_tracking_endpoints(self) -> bool:
        """Test progress tracking endpoints"""
        logger.info("Testing progress tracking endpoints...")
        
        if not self.auth_tokens or not self.test_articles:
            logger.warning("No auth tokens or articles available for progress tracking testing")
            return False
        
        # Test 1: Mark Article as Read
        for user_type, token in self.auth_tokens.items():
            for i, article in enumerate(self.test_articles[:2]):
                try:
                    headers = {'Authorization': f'Bearer {token}'}
                    response = self.session.post(
                        f"{self.base_url}/api/articles/{article.get('id', 'test-id')}/read",
                        headers=headers,
                        json={'progress_percentage': 100},
                        timeout=10
                    )
                    
                    success = response.status_code in [200, 201, 404]  # 404 acceptable for test IDs
                    self.log_test_result(
                        'progress_tracking',
                        f'Mark article {i+1} as read {user_type}',
                        success,
                        response,
                        f"Status code: {response.status_code}" if not success else None
                    )
                    
                except Exception as e:
                    self.log_test_result(
                        'progress_tracking',
                        f'Mark article {i+1} as read {user_type}',
                        False,
                        error=str(e)
                    )
        
        # Test 2: Get Reading Progress
        for user_type, token in self.auth_tokens.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.get(
                    f"{self.base_url}/api/articles/progress",
                    headers=headers,
                    timeout=10
                )
                
                success = response.status_code == 200
                self.log_test_result(
                    'progress_tracking',
                    f'Get reading progress {user_type}',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None
                )
                
            except Exception as e:
                self.log_test_result(
                    'progress_tracking',
                    f'Get reading progress {user_type}',
                    False,
                    error=str(e)
                )
        
        # Test 3: Update Reading Progress
        for user_type, token in self.auth_tokens.items():
            for i, article in enumerate(self.test_articles[:2]):
                try:
                    headers = {'Authorization': f'Bearer {token}'}
                    response = self.session.put(
                        f"{self.base_url}/api/articles/{article.get('id', 'test-id')}/progress",
                        headers=headers,
                        json={'progress_percentage': 75, 'time_spent': 300},
                        timeout=10
                    )
                    
                    success = response.status_code in [200, 404]  # 404 acceptable for test IDs
                    self.log_test_result(
                        'progress_tracking',
                        f'Update progress article {i+1} {user_type}',
                        success,
                        response,
                        f"Status code: {response.status_code}" if not success else None
                    )
                    
                except Exception as e:
                    self.log_test_result(
                        'progress_tracking',
                        f'Update progress article {i+1} {user_type}',
                        False,
                        error=str(e)
                    )
        
        return True
    
    def test_bookmark_endpoints(self) -> bool:
        """Test bookmark endpoints"""
        logger.info("Testing bookmark endpoints...")
        
        if not self.auth_tokens or not self.test_articles:
            logger.warning("No auth tokens or articles available for bookmark testing")
            return False
        
        # Test 1: Add Bookmark
        for user_type, token in self.auth_tokens.items():
            for i, article in enumerate(self.test_articles[:2]):
                try:
                    headers = {'Authorization': f'Bearer {token}'}
                    response = self.session.post(
                        f"{self.base_url}/api/articles/{article.get('id', 'test-id')}/bookmark",
                        headers=headers,
                        json={'folder': 'favorites'},
                        timeout=10
                    )
                    
                    success = response.status_code in [200, 201, 404]  # 404 acceptable for test IDs
                    self.log_test_result(
                        'bookmarks',
                        f'Add bookmark article {i+1} {user_type}',
                        success,
                        response,
                        f"Status code: {response.status_code}" if not success else None
                    )
                    
                except Exception as e:
                    self.log_test_result(
                        'bookmarks',
                        f'Add bookmark article {i+1} {user_type}',
                        False,
                        error=str(e)
                    )
        
        # Test 2: Get Bookmarks
        for user_type, token in self.auth_tokens.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.get(
                    f"{self.base_url}/api/articles/bookmarks",
                    headers=headers,
                    timeout=10
                )
                
                success = response.status_code == 200
                self.log_test_result(
                    'bookmarks',
                    f'Get bookmarks {user_type}',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None
                )
                
            except Exception as e:
                self.log_test_result(
                    'bookmarks',
                    f'Get bookmarks {user_type}',
                    False,
                    error=str(e)
                )
        
        # Test 3: Remove Bookmark
        for user_type, token in self.auth_tokens.items():
            for i, article in enumerate(self.test_articles[:2]):
                try:
                    headers = {'Authorization': f'Bearer {token}'}
                    response = self.session.delete(
                        f"{self.base_url}/api/articles/{article.get('id', 'test-id')}/bookmark",
                        headers=headers,
                        timeout=10
                    )
                    
                    success = response.status_code in [200, 204, 404]  # 404 acceptable for test IDs
                    self.log_test_result(
                        'bookmarks',
                        f'Remove bookmark article {i+1} {user_type}',
                        success,
                        response,
                        f"Status code: {response.status_code}" if not success else None
                    )
                    
                except Exception as e:
                    self.log_test_result(
                        'bookmarks',
                        f'Remove bookmark article {i+1} {user_type}',
                        False,
                        error=str(e)
                    )
        
        return True
    
    def test_rate_limiting(self) -> bool:
        """Test rate limiting functionality"""
        logger.info("Testing rate limiting...")
        
        if not self.auth_tokens:
            logger.warning("No auth tokens available for rate limiting testing")
            return False
        
        # Test 1: Rapid Login Attempts
        try:
            user_data = self.test_users['beginner']
            responses = []
            
            for i in range(15):  # Try 15 rapid requests
                response = self.session.post(
                    f"{self.base_url}/api/auth/login",
                    json={
                        'email': user_data['email'],
                        'password': 'wrongpassword'  # Wrong password to trigger rate limiting
                    },
                    timeout=5
                )
                responses.append(response)
                time.sleep(0.1)  # Small delay between requests
            
            # Check if rate limiting kicked in
            rate_limited = any(r.status_code == 429 for r in responses)
            self.log_test_result(
                'rate_limiting',
                'Login rate limiting',
                rate_limited,
                responses[-1] if responses else None,
                "Rate limiting not triggered" if not rate_limited else None,
                {'total_requests': len(responses), 'rate_limited_requests': sum(1 for r in responses if r.status_code == 429)}
            )
            
        except Exception as e:
            self.log_test_result(
                'rate_limiting',
                'Login rate limiting',
                False,
                error=str(e)
            )
        
        # Test 2: API Endpoint Rate Limiting
        if self.auth_tokens:
            try:
                token = list(self.auth_tokens.values())[0]
                headers = {'Authorization': f'Bearer {token}'}
                responses = []
                
                for i in range(50):  # Try 50 rapid API requests
                    response = self.session.get(
                        f"{self.base_url}/api/articles",
                        headers=headers,
                        timeout=5
                    )
                    responses.append(response)
                    time.sleep(0.05)  # Small delay between requests
                
                # Check if rate limiting kicked in
                rate_limited = any(r.status_code == 429 for r in responses)
                self.log_test_result(
                    'rate_limiting',
                    'API endpoint rate limiting',
                    rate_limited,
                    responses[-1] if responses else None,
                    "Rate limiting not triggered" if not rate_limited else None,
                    {'total_requests': len(responses), 'rate_limited_requests': sum(1 for r in responses if r.status_code == 429)}
                )
                
            except Exception as e:
                self.log_test_result(
                    'rate_limiting',
                    'API endpoint rate limiting',
                    False,
                    error=str(e)
                )
        
        return True
    
    def test_error_handling(self) -> bool:
        """Test error handling"""
        logger.info("Testing error handling...")
        
        # Test 1: Invalid Authentication
        try:
            response = self.session.get(
                f"{self.base_url}/api/articles",
                headers={'Authorization': 'Bearer invalid-token'},
                timeout=10
            )
            
            success = response.status_code == 401
            self.log_test_result(
                'error_handling',
                'Invalid authentication token',
                success,
                response,
                f"Expected 401, got {response.status_code}" if not success else None
            )
            
        except Exception as e:
            self.log_test_result(
                'error_handling',
                'Invalid authentication token',
                False,
                error=str(e)
            )
        
        # Test 2: Missing Authentication
        try:
            response = self.session.get(
                f"{self.base_url}/api/articles",
                timeout=10
            )
            
            success = response.status_code == 401
            self.log_test_result(
                'error_handling',
                'Missing authentication',
                success,
                response,
                f"Expected 401, got {response.status_code}" if not success else None
            )
            
        except Exception as e:
            self.log_test_result(
                'error_handling',
                'Missing authentication',
                False,
                error=str(e)
            )
        
        # Test 3: Invalid Endpoint
        try:
            response = self.session.get(
                f"{self.base_url}/api/invalid-endpoint",
                timeout=10
            )
            
            success = response.status_code == 404
            self.log_test_result(
                'error_handling',
                'Invalid endpoint',
                success,
                response,
                f"Expected 404, got {response.status_code}" if not success else None
            )
            
        except Exception as e:
            self.log_test_result(
                'error_handling',
                'Invalid endpoint',
                False,
                error=str(e)
            )
        
        # Test 4: Invalid JSON
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                data="invalid json",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 400
            self.log_test_result(
                'error_handling',
                'Invalid JSON payload',
                success,
                response,
                f"Expected 400, got {response.status_code}" if not success else None
            )
            
        except Exception as e:
            self.log_test_result(
                'error_handling',
                'Invalid JSON payload',
                False,
                error=str(e)
            )
        
        return True
    
    def test_user_management_endpoints(self) -> bool:
        """Test user management endpoints"""
        logger.info("Testing user management endpoints...")
        
        if not self.auth_tokens:
            logger.warning("No auth tokens available for user management testing")
            return False
        
        # Test 1: Update User Profile
        for user_type, token in self.auth_tokens.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.put(
                    f"{self.base_url}/api/auth/profile",
                    headers=headers,
                    json={
                        'full_name': f'Updated {user_type} User',
                        'phone_number': '+1234567899'
                    },
                    timeout=10
                )
                
                success = response.status_code in [200, 201]
                self.log_test_result(
                    'user_management',
                    f'Update profile {user_type}',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None
                )
                
            except Exception as e:
                self.log_test_result(
                    'user_management',
                    f'Update profile {user_type}',
                    False,
                    error=str(e)
                )
        
        # Test 2: Get User Assessment Data
        for user_type, token in self.auth_tokens.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.get(
                    f"{self.base_url}/api/user/assessment",
                    headers=headers,
                    timeout=10
                )
                
                success = response.status_code in [200, 404]  # 404 if no assessment data
                self.log_test_result(
                    'user_management',
                    f'Get assessment data {user_type}',
                    success,
                    response,
                    f"Status code: {response.status_code}" if not success else None
                )
                
            except Exception as e:
                self.log_test_result(
                    'user_management',
                    f'Get assessment data {user_type}',
                    False,
                    error=str(e)
                )
        
        return True
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE API TESTING REPORT")
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
        categories = ['authentication', 'user_management', 'articles', 'recommendations', 
                     'progress_tracking', 'bookmarks', 'rate_limiting', 'error_handling']
        
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
                
                # Show failed tests
                failed_tests = [test for test in self.test_results[category] if not test['success']]
                if failed_tests:
                    report.append("Failed Tests:")
                    for test in failed_tests[:5]:  # Show first 5 failures
                        report.append(f"  • {test['test_name']}: {test.get('error', 'Unknown error')}")
                    if len(failed_tests) > 5:
                        report.append(f"  ... and {len(failed_tests) - 5} more")
                
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
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("-" * 40)
        
        if overall['failed_tests'] > 0:
            report.append("⚠️  Some tests failed. Review the failed tests above.")
        
        if overall['passed_tests'] / overall['total_tests'] >= 0.9:
            report.append("✅ API is performing well overall.")
        elif overall['passed_tests'] / overall['total_tests'] >= 0.7:
            report.append("⚠️  API has some issues that should be addressed.")
        else:
            report.append("❌ API has significant issues that need immediate attention.")
        
        if any(test.get('response_time', 0) > 2.0 for category in categories for test in self.test_results[category]):
            report.append("⚠️  Some endpoints are responding slowly (>2s).")
        
        if not any(test['success'] for test in self.test_results['rate_limiting']):
            report.append("⚠️  Rate limiting may not be working properly.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_all_tests(self) -> bool:
        """Run all comprehensive API tests"""
        logger.info("Starting comprehensive API testing...")
        
        try:
            # Test authentication endpoints
            auth_success = self.test_authentication_endpoints()
            
            # Test user management endpoints
            self.test_user_management_endpoints()
            
            # Test article endpoints
            self.test_article_endpoints()
            
            # Test recommendation endpoints
            self.test_recommendation_endpoints()
            
            # Test progress tracking endpoints
            self.test_progress_tracking_endpoints()
            
            # Test bookmark endpoints
            self.test_bookmark_endpoints()
            
            # Test rate limiting
            self.test_rate_limiting()
            
            # Test error handling
            self.test_error_handling()
            
            # Generate and save report
            report = self.generate_test_report()
            
            # Save report to file
            report_filename = f"api_testing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
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
    
    parser = argparse.ArgumentParser(description='Comprehensive API testing')
    parser.add_argument('--base-url', default='http://localhost:5000', 
                       help='Base URL for API testing')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port number for API testing')
    
    args = parser.parse_args()
    
    # Construct base URL
    base_url = args.base_url
    if not base_url.startswith('http'):
        base_url = f"http://localhost:{args.port}"
    
    # Create API tester
    tester = APITester(base_url)
    
    # Run tests
    success = tester.run_all_tests()
    
    if success:
        logger.info("API testing completed successfully!")
        return 0
    else:
        logger.error("API testing failed!")
        return 1


if __name__ == "__main__":
    exit(main())
