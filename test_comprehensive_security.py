"""
Comprehensive Security System Tests
Tests for rate limiting and API security implementation
"""

import unittest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, request, g
from flask.testing import FlaskClient

# Import security components
from backend.middleware.rate_limiter import AdvancedRateLimiter, rate_limited
from backend.middleware.api_validation import APIValidator, validate_api_request
from backend.middleware.security_integration import (
    secure_endpoint, 
    secure_assessment_endpoint,
    SecurityMiddleware
)

class TestAdvancedRateLimiter(unittest.TestCase):
    """Test advanced rate limiting functionality"""
    
    def setUp(self):
        self.rate_limiter = AdvancedRateLimiter()
        self.mock_request = Mock()
        self.mock_request.remote_addr = '192.168.1.1'
        self.mock_request.headers = {'User-Agent': 'TestAgent'}
    
    def test_get_identifier_user_authenticated(self):
        """Test identifier generation for authenticated users"""
        g.user_id = '12345'
        
        identifier = self.rate_limiter.get_identifier(self.mock_request)
        self.assertEqual(identifier, 'user:12345')
    
    def test_get_identifier_anonymous_user(self):
        """Test identifier generation for anonymous users"""
        g.user_id = None
        
        identifier = self.rate_limiter.get_identifier(self.mock_request)
        self.assertTrue(identifier.startswith('ip:192.168.1.1:'))
    
    @patch('backend.middleware.rate_limiter.redis.Redis')
    def test_redis_rate_limiting(self, mock_redis):
        """Test Redis-based rate limiting"""
        # Mock Redis client
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        rate_limiter = AdvancedRateLimiter(mock_redis_client)
        
        # First request - should be allowed
        mock_redis_client.get.return_value = None
        result = rate_limiter.is_rate_limited('test_user', 'assessment_submit')
        
        self.assertFalse(result['limited'])
        self.assertEqual(result['requests_made'], 1)
        
        # Second request - should be allowed
        mock_redis_client.get.return_value = json.dumps({
            'requests': 1,
            'window_start': time.time()
        })
        result = rate_limiter.is_rate_limited('test_user', 'assessment_submit')
        
        self.assertFalse(result['limited'])
        self.assertEqual(result['requests_made'], 2)
        
        # Fourth request - should be limited
        mock_redis_client.get.return_value = json.dumps({
            'requests': 3,
            'window_start': time.time()
        })
        result = rate_limiter.is_rate_limited('test_user', 'assessment_submit')
        
        self.assertTrue(result['limited'])
        self.assertEqual(result['requests_made'], 3)
    
    def test_memory_rate_limiting(self):
        """Test in-memory rate limiting fallback"""
        rate_limiter = AdvancedRateLimiter()  # No Redis client
        
        # First request - should be allowed
        result = rate_limiter.is_rate_limited('test_user', 'assessment_submit')
        self.assertFalse(result['limited'])
        self.assertEqual(result['requests_made'], 1)
        
        # Second request - should be allowed
        result = rate_limiter.is_rate_limited('test_user', 'assessment_submit')
        self.assertFalse(result['limited'])
        self.assertEqual(result['requests_made'], 2)
        
        # Fourth request - should be limited
        result = rate_limiter.is_rate_limited('test_user', 'assessment_submit')
        self.assertTrue(result['limited'])
        self.assertEqual(result['requests_made'], 3)

class TestAPIValidator(unittest.TestCase):
    """Test API request validation functionality"""
    
    def setUp(self):
        self.validator = APIValidator()
        self.app = Flask(__name__)
        self.client = self.app.test_client()
    
    def test_request_size_validation(self):
        """Test request size validation"""
        # Test normal request
        with self.app.test_request_context('/test', data='{"test": "data"}'):
            result = self.validator.validate_request()
            self.assertTrue(result['valid'])
        
        # Test oversized request
        self.validator.max_request_size = 10  # 10 bytes
        with self.app.test_request_context('/test', data='{"test": "data"}'):
            request.content_length = 100
            result = self.validator.validate_request()
            self.assertFalse(result['valid'])
            self.assertEqual(result['code'], 413)
    
    def test_content_type_validation(self):
        """Test content type validation"""
        # Test allowed content type
        with self.app.test_request_context('/test', content_type='application/json'):
            result = self.validator.validate_request()
            self.assertTrue(result['valid'])
        
        # Test disallowed content type
        with self.app.test_request_context('/test', content_type='text/plain'):
            result = self.validator.validate_request()
            self.assertFalse(result['valid'])
            self.assertEqual(result['code'], 415)
    
    def test_required_headers_validation(self):
        """Test required headers validation"""
        # Test missing required header
        with self.app.test_request_context('/test'):
            request.headers = {}
            result = self.validator.validate_request()
            self.assertFalse(result['valid'])
            self.assertEqual(result['code'], 400)
        
        # Test with required headers
        with self.app.test_request_context('/test'):
            request.headers = {'User-Agent': 'TestAgent', 'Accept': 'application/json'}
            result = self.validator.validate_request()
            self.assertTrue(result['valid'])
    
    def test_suspicious_pattern_detection(self):
        """Test suspicious pattern detection"""
        # Test XSS pattern
        with self.app.test_request_context('/test', data='<script>alert("xss")</script>'):
            result = self.validator.validate_request()
            self.assertFalse(result['valid'])
            self.assertEqual(result['code'], 400)
        
        # Test SQL injection pattern
        with self.app.test_request_context('/test', data='union select * from users'):
            result = self.validator.validate_request()
            self.assertFalse(result['valid'])
            self.assertEqual(result['code'], 400)
        
        # Test normal data
        with self.app.test_request_context('/test', data='{"normal": "data"}'):
            result = self.validator.validate_request()
            self.assertTrue(result['valid'])
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        # Test HTML escaping
        sanitized = self.validator.sanitize_input('<script>alert("xss")</script>')
        self.assertIn('&lt;script&gt;', sanitized)
        
        # Test null byte removal
        sanitized = self.validator.sanitize_input('test\x00data')
        self.assertEqual(sanitized, 'testdata')
        
        # Test dictionary sanitization
        data = {'key': '<script>alert("xss")</script>'}
        sanitized = self.validator.sanitize_input(data)
        self.assertIn('&lt;script&gt;', sanitized['key'])

class TestSecurityIntegration(unittest.TestCase):
    """Test security integration functionality"""
    
    def setUp(self):
        self.app = Flask(__name__)
        self.client = self.app.test_client()
        
        @self.app.route('/test-secure', methods=['POST'])
        @secure_endpoint(
            endpoint_type='test',
            custom_rate_limits={'requests': 2, 'window': 60},
            max_request_size=1024,
            allowed_content_types=['application/json']
        )
        def test_endpoint():
            return {'success': True}
        
        @self.app.route('/test-assessment', methods=['POST'])
        @secure_assessment_endpoint()
        def test_assessment():
            return {'success': True}
    
    @patch('backend.middleware.security_integration.get_rate_limiter')
    @patch('backend.middleware.security_integration.get_api_validator')
    def test_secure_endpoint_success(self, mock_get_validator, mock_get_limiter):
        """Test successful secure endpoint execution"""
        # Mock validator
        mock_validator = Mock()
        mock_validator.validate_request.return_value = {'valid': True}
        mock_validator.sanitize_input.return_value = {'test': 'data'}
        mock_get_validator.return_value = mock_validator
        
        # Mock rate limiter
        mock_limiter = Mock()
        mock_limiter.is_rate_limited.return_value = {
            'limited': False,
            'requests_made': 1,
            'limit': 2,
            'window_remaining': 60
        }
        mock_get_limiter.return_value = mock_limiter
        
        # Test request
        response = self.client.post('/test-secure', 
                                  json={'test': 'data'},
                                  headers={'User-Agent': 'TestAgent', 'Accept': 'application/json'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('X-RateLimit-Limit', response.headers)
    
    @patch('backend.middleware.security_integration.get_rate_limiter')
    @patch('backend.middleware.security_integration.get_api_validator')
    def test_secure_endpoint_rate_limited(self, mock_get_validator, mock_get_limiter):
        """Test rate limited endpoint"""
        # Mock validator
        mock_validator = Mock()
        mock_validator.validate_request.return_value = {'valid': True}
        mock_get_validator.return_value = mock_validator
        
        # Mock rate limiter - rate limited
        mock_limiter = Mock()
        mock_limiter.is_rate_limited.return_value = {
            'limited': True,
            'requests_made': 3,
            'limit': 2,
            'window_remaining': 45
        }
        mock_get_limiter.return_value = mock_limiter
        
        # Test request
        response = self.client.post('/test-secure', 
                                  json={'test': 'data'},
                                  headers={'User-Agent': 'TestAgent', 'Accept': 'application/json'})
        
        self.assertEqual(response.status_code, 429)
        self.assertIn('retry_after', response.get_json())
    
    @patch('backend.middleware.security_integration.get_rate_limiter')
    @patch('backend.middleware.security_integration.get_api_validator')
    def test_secure_endpoint_validation_failed(self, mock_get_validator, mock_get_limiter):
        """Test validation failed endpoint"""
        # Mock validator - validation failed
        mock_validator = Mock()
        mock_validator.validate_request.return_value = {
            'valid': False, 
            'reason': 'Request too large', 
            'code': 413
        }
        mock_get_validator.return_value = mock_validator
        
        # Mock rate limiter
        mock_limiter = Mock()
        mock_get_limiter.return_value = mock_limiter
        
        # Test request
        response = self.client.post('/test-secure', 
                                  json={'test': 'data'},
                                  headers={'User-Agent': 'TestAgent', 'Accept': 'application/json'})
        
        self.assertEqual(response.status_code, 413)
        self.assertIn('Request too large', response.get_json()['message'])

class TestSecurityMiddleware(unittest.TestCase):
    """Test Flask security middleware"""
    
    def setUp(self):
        self.app = Flask(__name__)
        self.middleware = SecurityMiddleware()
        self.middleware.init_app(self.app)
        
        @self.app.route('/test', methods=['GET'])
        def test_endpoint():
            return {'success': True}
    
    def test_security_headers(self):
        """Test security headers are added to responses"""
        response = self.app.test_client().get('/test')
        
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertIn('X-Frame-Options', response.headers)
        self.assertIn('X-XSS-Protection', response.headers)
        self.assertIn('Strict-Transport-Security', response.headers)
        self.assertIn('Content-Security-Policy', response.headers)
    
    def test_error_handlers(self):
        """Test error handlers for security violations"""
        # Test rate limit exceeded
        response = self.app.test_client().get('/nonexistent')
        # This should trigger a 404, but we can test the error handler structure
        
        # Test that error handlers are registered
        self.assertIn('429', self.app.error_handler_spec[None])
        self.assertIn('413', self.app.error_handler_spec[None])
        self.assertIn('415', self.app.error_handler_spec[None])
        self.assertIn('400', self.app.error_handler_spec[None])

class TestRateLimitDecorators(unittest.TestCase):
    """Test rate limiting decorators"""
    
    def setUp(self):
        self.app = Flask(__name__)
        
        @self.app.route('/test-rate-limited', methods=['POST'])
        @rate_limited('test_endpoint')
        def test_endpoint():
            return {'success': True}
    
    @patch('backend.middleware.rate_limiter.get_rate_limiter')
    def test_rate_limited_decorator(self, mock_get_limiter):
        """Test rate limited decorator"""
        # Mock rate limiter
        mock_limiter = Mock()
        mock_limiter.get_identifier.return_value = 'test_user'
        mock_limiter.is_rate_limited.return_value = {
            'limited': False,
            'requests_made': 1,
            'limit': 100,
            'window_remaining': 3600
        }
        mock_get_limiter.return_value = mock_limiter
        
        # Test request
        response = self.app.test_client().post('/test-rate-limited', 
                                              json={'test': 'data'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('X-RateLimit-Limit', response.headers)

class TestAPIValidationDecorators(unittest.TestCase):
    """Test API validation decorators"""
    
    def setUp(self):
        self.app = Flask(__name__)
        
        @self.app.route('/test-validated', methods=['POST'])
        @validate_api_request
        def test_endpoint():
            return {'success': True}
    
    @patch('backend.middleware.api_validation.get_api_validator')
    def test_validate_api_request_decorator(self, mock_get_validator):
        """Test API validation decorator"""
        # Mock validator
        mock_validator = Mock()
        mock_validator.validate_request.return_value = {'valid': True}
        mock_validator.sanitize_input.return_value = {'test': 'data'}
        mock_get_validator.return_value = mock_validator
        
        # Test request
        response = self.app.test_client().post('/test-validated', 
                                              json={'test': 'data'},
                                              headers={'User-Agent': 'TestAgent', 'Accept': 'application/json'})
        
        self.assertEqual(response.status_code, 200)

class TestSecurityEventLogging(unittest.TestCase):
    """Test security event logging"""
    
    @patch('backend.monitoring.logging_config.log_security_event')
    def test_rate_limit_violation_logging(self, mock_log_event):
        """Test rate limit violation logging"""
        rate_limiter = AdvancedRateLimiter()
        
        # Mock request context
        with patch('backend.middleware.rate_limiter.request') as mock_request:
            mock_request.endpoint = 'test_endpoint'
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers = {'User-Agent': 'TestAgent'}
            mock_request.method = 'POST'
            mock_request.path = '/test'
            
            g.user_id = '12345'
            
            # Test logging
            limit_info = {
                'requests_made': 4,
                'limit': 3,
                'window_remaining': 240
            }
            
            rate_limiter.log_rate_limit_violation('user:12345', 'assessment_submit', limit_info)
            
            # Verify logging was called
            mock_log_event.assert_called_once()
            call_args = mock_log_event.call_args
            self.assertEqual(call_args[0][0], 'rate_limit_exceeded')
            self.assertIn('assessment_submit', call_args[0][1]['endpoint_type'])

def run_comprehensive_tests():
    """Run all comprehensive security tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestAdvancedRateLimiter,
        TestAPIValidator,
        TestSecurityIntegration,
        TestSecurityMiddleware,
        TestRateLimitDecorators,
        TestAPIValidationDecorators,
        TestSecurityEventLogging
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("COMPREHENSIVE SECURITY TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_comprehensive_tests()
    exit(0 if success else 1)
