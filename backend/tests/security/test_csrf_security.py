"""
CSRF Protection Security Validation Tests for MINGUS Financial Application
=========================================================================

This module provides comprehensive CSRF protection security testing:
1. CSRF protection validation on all financial endpoints
2. Token generation and validation tests
3. React integration validation tests
4. CSRF failure handling and logging tests
5. PCI DSS compliance validation tests
6. Token rotation and cleanup tests

Author: MINGUS Development Team
Date: January 2025
"""

import pytest
import json
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, session, request
import redis

from backend.security.csrf_protection_comprehensive import ComprehensiveCSRFProtection
from backend.security.csrf_middleware_comprehensive import (
    ComprehensiveCSRFMiddleware,
    require_csrf,
    require_financial_csrf,
    require_payment_csrf,
    require_budget_csrf,
    require_goals_csrf
)
from backend.security.csrf_monitoring import CSRFMonitoringSystem, SecurityEventType, SecuritySeverity

class TestCSRFProtectionSecurity:
    """Test CSRF protection security controls"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def redis_client(self):
        """Create mock Redis client"""
        mock_redis = Mock(spec=redis.Redis)
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        mock_redis.scan_iter.return_value = []
        return mock_redis
    
    @pytest.fixture
    def csrf_protection(self, app, redis_client):
        """Create CSRF protection instance"""
        return ComprehensiveCSRFProtection(app, redis_client)
    
    @pytest.fixture
    def csrf_middleware(self, app, redis_client):
        """Create CSRF middleware instance"""
        return ComprehensiveCSRFMiddleware(app, redis_client)

class TestCSRFProtectionOnFinancialEndpoints:
    """Test CSRF protection on all financial endpoints"""
    
    def test_payment_endpoints_csrf_protection(self, client):
        """Test CSRF protection on payment endpoints"""
        payment_endpoints = [
            '/api/payments/create',
            '/api/payment/process',
            '/api/payments/refund',
            '/api/payment/methods/attach',
            '/api/payment/methods/detach'
        ]
        
        for endpoint in payment_endpoints:
            # Test without CSRF token
            response = client.post(endpoint, json={'data': 'test'})
            assert response.status_code in [403, 400], f"CSRF protection should be active on {endpoint}"
            
            # Test with invalid CSRF token
            response = client.post(endpoint, 
                                 headers={'X-CSRF-Token': 'invalid_token'},
                                 json={'data': 'test'})
            assert response.status_code in [403, 400], f"Invalid CSRF token should be rejected on {endpoint}"
    
    def test_financial_data_endpoints_csrf_protection(self, client):
        """Test CSRF protection on financial data endpoints"""
        financial_endpoints = [
            '/api/financial/data',
            '/api/financial/analysis',
            '/api/financial/reports',
            '/api/financial/export'
        ]
        
        for endpoint in financial_endpoints:
            # Test POST/PUT/DELETE without CSRF token
            for method in ['POST', 'PUT', 'DELETE']:
                response = getattr(client, method.lower())(endpoint, json={'data': 'test'})
                assert response.status_code in [403, 400], f"CSRF protection should be active on {method} {endpoint}"
    
    def test_budget_endpoints_csrf_protection(self, client):
        """Test CSRF protection on budget endpoints"""
        budget_endpoints = [
            '/api/budget/create',
            '/api/budget/update',
            '/api/budget/delete',
            '/api/budget/categories'
        ]
        
        for endpoint in budget_endpoints:
            # Test without CSRF token
            response = client.post(endpoint, json={'data': 'test'})
            assert response.status_code in [403, 400], f"CSRF protection should be active on {endpoint}"
    
    def test_goals_endpoints_csrf_protection(self, client):
        """Test CSRF protection on goals endpoints"""
        goals_endpoints = [
            '/api/goals/create',
            '/api/goals/update',
            '/api/goals/delete',
            '/api/goals/progress'
        ]
        
        for endpoint in goals_endpoints:
            # Test without CSRF token
            response = client.post(endpoint, json={'data': 'test'})
            assert response.status_code in [403, 400], f"CSRF protection should be active on {endpoint}"
    
    def test_subscription_endpoints_csrf_protection(self, client):
        """Test CSRF protection on subscription endpoints"""
        subscription_endpoints = [
            '/api/subscription/create',
            '/api/subscription/update',
            '/api/subscription/cancel',
            '/api/subscription/upgrade'
        ]
        
        for endpoint in subscription_endpoints:
            # Test without CSRF token
            response = client.post(endpoint, json={'data': 'test'})
            assert response.status_code in [403, 400], f"CSRF protection should be active on {endpoint}"
    
    def test_banking_endpoints_csrf_protection(self, client):
        """Test CSRF protection on banking endpoints"""
        banking_endpoints = [
            '/api/banking/connect',
            '/api/banking/disconnect',
            '/api/banking/accounts',
            '/api/plaid/link',
            '/api/plaid/unlink'
        ]
        
        for endpoint in banking_endpoints:
            # Test without CSRF token
            response = client.post(endpoint, json={'data': 'test'})
            assert response.status_code in [403, 400], f"CSRF protection should be active on {endpoint}"

class TestCSRFTokenGenerationAndValidation:
    """Test CSRF token generation and validation"""
    
    def test_token_generation_security(self, csrf_protection):
        """Test CSRF token generation security"""
        with patch('backend.security.csrf_protection_comprehensive.session', {}):
            with patch('backend.security.csrf_protection_comprehensive.g', Mock()):
                # Generate multiple tokens
                tokens = []
                for i in range(10):
                    token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
                    tokens.append(token_data['token'])
                
                # Verify all tokens are unique
                assert len(set(tokens)) == 10, "All generated tokens should be unique"
                
                # Verify token format
                for token in tokens:
                    assert len(token) > 20, "Token should be sufficiently long"
                    assert isinstance(token, str), "Token should be a string"
    
    def test_token_validation_security(self, csrf_protection):
        """Test CSRF token validation security"""
        # Mock Redis response for valid token
        token_data = {
            'token': 'test_token',
            'token_id': 'test_token_id',
            'hash': 'test_hash',
            'timestamp': int(time.time()),
            'user_id': 'test_user',
            'session_id': 'test_session'
        }
        
        csrf_protection.redis_client.get.return_value = json.dumps(token_data)
        csrf_protection.redis_client.scan_iter.return_value = ['csrf_token:test_token_id']
        
        with patch('backend.security.csrf_protection_comprehensive.session', {'user_id': 'test_user', 'session_id': 'test_session'}):
            with patch('backend.security.csrf_protection_comprehensive.g', Mock()):
                with patch('backend.security.csrf_protection_comprehensive.current_app') as mock_app:
                    mock_app.config = {'SECRET_KEY': 'test-secret-key'}
                    
                    # Mock HMAC validation
                    with patch('backend.security.csrf_protection_comprehensive.hmac.new') as mock_hmac:
                        mock_hmac.return_value.hexdigest.return_value = 'test_hash'
                        
                        # Test valid token
                        is_valid = csrf_protection.validate_csrf_token('test_token')
                        assert is_valid is True, "Valid token should be accepted"
                        
                        # Test invalid token
                        is_valid = csrf_protection.validate_csrf_token('invalid_token')
                        assert is_valid is False, "Invalid token should be rejected"
    
    def test_token_expiration_handling(self, csrf_protection):
        """Test CSRF token expiration handling"""
        # Mock expired token
        expired_time = int(time.time()) - 2000  # 2000 seconds ago
        token_data = {
            'token': 'expired_token',
            'token_id': 'expired_token_id',
            'hash': 'test_hash',
            'timestamp': expired_time,
            'user_id': 'test_user',
            'session_id': 'test_session'
        }
        
        csrf_protection.redis_client.get.return_value = json.dumps(token_data)
        csrf_protection.redis_client.scan_iter.return_value = ['csrf_token:expired_token_id']
        
        with patch('backend.security.csrf_protection_comprehensive.session', {'user_id': 'test_user', 'session_id': 'test_session'}):
            with patch('backend.security.csrf_protection_comprehensive.g', Mock()):
                is_valid = csrf_protection.validate_csrf_token('expired_token')
                assert is_valid is False, "Expired token should be rejected"
    
    def test_token_rotation_security(self, csrf_protection):
        """Test CSRF token rotation security"""
        # Mock old token for rotation
        old_time = int(time.time()) - 1000  # 1000 seconds ago
        token_data = {
            'token': 'old_token',
            'token_id': 'old_token_id',
            'hash': 'test_hash',
            'timestamp': old_time,
            'user_id': 'test_user',
            'session_id': 'test_session'
        }
        
        csrf_protection.redis_client.get.return_value = json.dumps(token_data)
        csrf_protection.redis_client.scan_iter.return_value = ['csrf_token:old_token_id']
        
        # Test token rotation
        with patch('backend.security.csrf_protection_comprehensive.secrets.token_urlsafe') as mock_secrets:
            mock_secrets.side_effect = ['new_token', 'new_token_id']
            
            csrf_protection._rotate_user_tokens()
            
            # Verify new token was created
            assert mock_secrets.call_count >= 2, "New token should be generated during rotation"

class TestCSRFFailureHandlingAndLogging:
    """Test CSRF failure handling and logging"""
    
    def test_csrf_failure_logging(self, csrf_protection):
        """Test CSRF failure logging"""
        with patch('backend.security.csrf_protection_comprehensive.logger') as mock_logger:
            # Simulate CSRF failure
            csrf_protection._log_csrf_failure(
                Mock(path='/api/payments/create', method='POST', remote_addr='127.0.0.1'),
                Exception("CSRF validation failed")
            )
            
            # Verify logging was called
            mock_logger.warning.assert_called()
    
    def test_csrf_failure_alerting(self, csrf_protection):
        """Test CSRF failure alerting"""
        with patch('backend.security.csrf_protection_comprehensive.current_app') as mock_app:
            mock_app.config = {'FLASK_ENV': 'production'}
            
            with patch.object(csrf_protection, '_send_security_alert') as mock_alert:
                # Simulate CSRF failure in production
                csrf_protection._log_csrf_failure(
                    Mock(path='/api/payments/create', method='POST', remote_addr='127.0.0.1'),
                    Exception("CSRF validation failed")
                )
                
                # Verify alert was sent
                mock_alert.assert_called()
    
    def test_csrf_failure_response_format(self, csrf_protection):
        """Test CSRF failure response format"""
        with patch('backend.security.csrf_protection_comprehensive.request') as mock_request:
            mock_request.headers = {'X-Request-ID': 'test-request-id'}
            
            response, status_code = csrf_protection._create_csrf_error_response(
                Exception("CSRF validation failed")
            )
            
            assert status_code == 403, "CSRF failure should return 403 status"
            assert 'error' in response.json, "Response should contain error field"
            assert 'message' in response.json, "Response should contain message field"
            assert 'code' in response.json, "Response should contain code field"
            assert response.json['code'] == 'CSRF_TOKEN_INVALID', "Error code should be CSRF_TOKEN_INVALID"

class TestCSRFDecorators:
    """Test CSRF protection decorators"""
    
    def test_require_csrf_decorator(self, app, client):
        """Test require_csrf decorator"""
        @app.route('/test', methods=['POST'])
        @require_csrf
        def test_endpoint():
            return {'success': True}
        
        with patch('backend.security.csrf_middleware_comprehensive.comprehensive_csrf') as mock_csrf:
            # Test with valid token
            mock_csrf.validate_csrf_token.return_value = True
            
            response = client.post('/test', 
                                 headers={'X-CSRF-Token': 'valid_token'},
                                 json={'data': 'test'})
            
            assert response.status_code == 200, "Valid CSRF token should be accepted"
            
            # Test with invalid token
            mock_csrf.validate_csrf_token.return_value = False
            
            response = client.post('/test', 
                                 headers={'X-CSRF-Token': 'invalid_token'},
                                 json={'data': 'test'})
            
            assert response.status_code == 403, "Invalid CSRF token should be rejected"
    
    def test_require_financial_csrf_decorator(self, app, client):
        """Test require_financial_csrf decorator"""
        @app.route('/financial/test', methods=['POST'])
        @require_financial_csrf
        def test_financial_endpoint():
            return {'success': True}
        
        with patch('backend.security.csrf_middleware_comprehensive.comprehensive_csrf') as mock_csrf:
            # Test with valid token
            mock_csrf.validate_csrf_token.return_value = True
            
            response = client.post('/financial/test', 
                                 headers={'X-CSRF-Token': 'valid_token'},
                                 json={'data': 'test'})
            
            assert response.status_code == 200, "Valid financial CSRF token should be accepted"
            
            # Test with invalid token
            mock_csrf.validate_csrf_token.return_value = False
            
            response = client.post('/financial/test', 
                                 headers={'X-CSRF-Token': 'invalid_token'},
                                 json={'data': 'test'})
            
            assert response.status_code == 403, "Invalid financial CSRF token should be rejected"
            assert response.json['code'] == 'FINANCIAL_CSRF_INVALID', "Should return financial CSRF error code"
    
    def test_require_payment_csrf_decorator(self, app, client):
        """Test require_payment_csrf decorator"""
        @app.route('/payment/test', methods=['POST'])
        @require_payment_csrf
        def test_payment_endpoint():
            return {'success': True}
        
        with patch('backend.security.csrf_middleware_comprehensive.comprehensive_csrf') as mock_csrf:
            # Test with valid token
            mock_csrf.validate_csrf_token.return_value = True
            
            response = client.post('/payment/test', 
                                 headers={'X-CSRF-Token': 'valid_token'},
                                 json={'data': 'test'})
            
            assert response.status_code == 200, "Valid payment CSRF token should be accepted"
            
            # Test with invalid token
            mock_csrf.validate_csrf_token.return_value = False
            
            response = client.post('/payment/test', 
                                 headers={'X-CSRF-Token': 'invalid_token'},
                                 json={'data': 'test'})
            
            assert response.status_code == 403, "Invalid payment CSRF token should be rejected"
            assert response.json['code'] == 'PAYMENT_CSRF_INVALID', "Should return payment CSRF error code"

class TestCSRFMonitoringAndCompliance:
    """Test CSRF monitoring and PCI DSS compliance"""
    
    def test_csrf_monitoring_system(self, redis_client):
        """Test CSRF monitoring system"""
        monitoring = CSRFMonitoringSystem(redis_client)
        
        # Test security event logging
        monitoring.log_security_event(
            SecurityEventType.CSRF_VALIDATION_FAILED,
            SecuritySeverity.HIGH,
            user_id='test_user',
            details={'endpoint': '/api/payments/create'}
        )
        
        # Verify metrics were updated
        assert monitoring.current_metrics.validation_failures == 1
        assert monitoring.current_metrics.security_events == 1
    
    def test_pci_compliance_tracking(self, redis_client):
        """Test PCI DSS compliance tracking"""
        monitoring = CSRFMonitoringSystem(redis_client)
        
        # Test PCI compliance violation logging
        monitoring.log_security_event(
            SecurityEventType.PCI_COMPLIANCE_VIOLATION,
            SecuritySeverity.CRITICAL,
            user_id='test_user',
            pci_compliance=True,
            details={'violation': 'csrf_token_missing'}
        )
        
        # Verify PCI violation was tracked
        assert monitoring.current_metrics.pci_violations == 1
        assert monitoring.current_metrics.security_events == 1
    
    def test_csrf_dashboard_data(self, redis_client):
        """Test CSRF dashboard data generation"""
        monitoring = CSRFMonitoringSystem(redis_client)
        
        # Add some test events
        monitoring.log_security_event(
            SecurityEventType.CSRF_TOKEN_GENERATED,
            SecuritySeverity.LOW,
            user_id='test_user'
        )
        
        monitoring.log_security_event(
            SecurityEventType.CSRF_VALIDATION_FAILED,
            SecuritySeverity.HIGH,
            user_id='test_user'
        )
        
        dashboard_data = monitoring.get_dashboard_data()
        
        assert 'timestamp' in dashboard_data
        assert 'health_score' in dashboard_data
        assert 'metrics' in dashboard_data
        assert 'recent_events' in dashboard_data
        assert 'alerts' in dashboard_data
        assert 'status' in dashboard_data
        
        # Verify health score calculation
        assert 0 <= dashboard_data['health_score'] <= 100

class TestCSRFTokenCleanupAndRotation:
    """Test CSRF token cleanup and rotation"""
    
    def test_token_cleanup_security(self, csrf_protection):
        """Test CSRF token cleanup security"""
        # Mock expired tokens
        expired_tokens = [
            {'key': 'csrf_token:expired1', 'data': {'timestamp': int(time.time()) - 2000}},
            {'key': 'csrf_token:expired2', 'data': {'timestamp': int(time.time()) - 3000}},
            {'key': 'csrf_token:valid', 'data': {'timestamp': int(time.time()) - 100}}
        ]
        
        csrf_protection.redis_client.scan_iter.return_value = [token['key'] for token in expired_tokens]
        csrf_protection.redis_client.get.side_effect = [json.dumps(token['data']) for token in expired_tokens]
        
        # Test cleanup
        csrf_protection._cleanup_expired_tokens()
        
        # Verify expired tokens were deleted
        assert csrf_protection.redis_client.delete.call_count >= 2, "Expired tokens should be deleted"
    
    def test_token_rotation_security(self, csrf_protection):
        """Test CSRF token rotation security"""
        # Mock old tokens for rotation
        old_tokens = [
            {'key': 'csrf_token:old1', 'data': {'timestamp': int(time.time()) - 1000}},
            {'key': 'csrf_token:old2', 'data': {'timestamp': int(time.time()) - 1200}}
        ]
        
        csrf_protection.redis_client.scan_iter.return_value = [token['key'] for token in old_tokens]
        csrf_protection.redis_client.get.side_effect = [json.dumps(token['data']) for token in old_tokens]
        
        # Test rotation
        with patch('backend.security.csrf_protection_comprehensive.secrets.token_urlsafe') as mock_secrets:
            mock_secrets.side_effect = ['new_token1', 'new_id1', 'new_token2', 'new_id2']
            
            csrf_protection._rotate_user_tokens()
            
            # Verify new tokens were created
            assert mock_secrets.call_count >= 4, "New tokens should be generated during rotation"

class TestCSRFPerformanceAndScalability:
    """Test CSRF protection performance and scalability"""
    
    def test_token_generation_performance(self, csrf_protection):
        """Test CSRF token generation performance"""
        start_time = time.time()
        
        with patch('backend.security.csrf_protection_comprehensive.session', {}):
            with patch('backend.security.csrf_protection_comprehensive.g', Mock()):
                # Generate 100 tokens
                for _ in range(100):
                    csrf_protection.generate_csrf_token('test_user', 'test_session')
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should generate 100 tokens in less than 1 second
        assert duration < 1.0, f"Token generation took {duration}s, should be < 1s"
        assert duration / 100 < 0.01, "Should generate tokens in < 10ms each"
    
    def test_token_validation_performance(self, csrf_protection):
        """Test CSRF token validation performance"""
        # Mock Redis response
        token_data = {
            'token': 'test_token',
            'token_id': 'test_token_id',
            'hash': 'test_hash',
            'timestamp': int(time.time()),
            'user_id': 'test_user',
            'session_id': 'test_session'
        }
        
        csrf_protection.redis_client.get.return_value = json.dumps(token_data)
        csrf_protection.redis_client.scan_iter.return_value = ['csrf_token:test_token_id']
        
        start_time = time.time()
        
        with patch('backend.security.csrf_protection_comprehensive.session', {'user_id': 'test_user', 'session_id': 'test_session'}):
            with patch('backend.security.csrf_protection_comprehensive.g', Mock()):
                with patch('backend.security.csrf_protection_comprehensive.current_app') as mock_app:
                    mock_app.config = {'SECRET_KEY': 'test-secret-key'}
                    
                    with patch('backend.security.csrf_protection_comprehensive.hmac.new') as mock_hmac:
                        mock_hmac.return_value.hexdigest.return_value = 'test_hash'
                        
                        # Validate 100 tokens
                        for _ in range(100):
                            csrf_protection.validate_csrf_token('test_token')
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should validate 100 tokens in less than 1 second
        assert duration < 1.0, f"Token validation took {duration}s, should be < 1s"
        assert duration / 100 < 0.01, "Should validate tokens in < 10ms each"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
