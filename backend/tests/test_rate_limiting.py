"""
Unit Tests for Rate Limiting System
Comprehensive testing of rate limiting functionality
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, request, g
from backend.middleware.rate_limiter import (
    ComprehensiveRateLimiter, 
    SlidingWindowStrategy,
    get_rate_limiter,
    add_rate_limit_headers
)
from backend.middleware.rate_limit_decorators import (
    rate_limit,
    rate_limit_by_user,
    rate_limit_by_ip,
    rate_limit_financial,
    rate_limit_payment,
    rate_limit_auth,
    rate_limit_assessment,
    rate_limit_webhook
)
from backend.config.rate_limits import (
    RateLimitConfig,
    RateLimitSettings,
    RateLimitManager,
    get_rate_limit_manager
)
from backend.monitoring.rate_limit_monitoring import (
    RateLimitMonitor,
    RateLimitEvent,
    RateLimitAlert,
    get_rate_limit_monitor,
    record_rate_limit_event
)

class TestSlidingWindowStrategy:
    """Test sliding window rate limiting strategy"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.redis_mock = Mock()
        self.strategy = SlidingWindowStrategy(self.redis_mock)
        self.identifier = "test_user:123"
        self.limits = {'requests': 5, 'window': 60}
    
    def test_check_rate_limit_first_request(self):
        """Test first request in new window"""
        self.redis_mock.zcard.return_value = 0
        self.redis_mock.zrange.return_value = []
        
        result = self.strategy.check_rate_limit(self.identifier, self.limits)
        
        assert result['limited'] is False
        assert result['requests_made'] == 1
        assert result['remaining_requests'] == 4
        self.redis_mock.zadd.assert_called_once()
        self.redis_mock.expire.assert_called_once_with(
            f"rate_limit:{self.identifier}", 60
        )
    
    def test_check_rate_limit_within_limits(self):
        """Test request within rate limits"""
        self.redis_mock.zcard.return_value = 3
        self.redis_mock.zrange.return_value = []
        
        result = self.strategy.check_rate_limit(self.identifier, self.limits)
        
        assert result['limited'] is False
        assert result['requests_made'] == 4
        assert result['remaining_requests'] == 1
    
    def test_check_rate_limit_exceeded(self):
        """Test rate limit exceeded"""
        self.redis_mock.zcard.return_value = 5
        # Use a timestamp that will result in a positive retry_after
        current_time = time.time()
        self.redis_mock.zrange.return_value = [('old_request', current_time - 30)]  # 30 seconds ago
        
        result = self.strategy.check_rate_limit(self.identifier, self.limits)
        
        assert result['limited'] is True
        assert result['requests_made'] == 5
        assert result['retry_after'] > 0
    
    def test_check_rate_limit_cleanup_expired(self):
        """Test cleanup of expired entries"""
        self.redis_mock.zcard.return_value = 2
        self.redis_mock.zrange.return_value = []
        
        self.strategy.check_rate_limit(self.identifier, self.limits)
        
        # Should call zremrangebyscore to clean expired entries
        self.redis_mock.zremrangebyscore.assert_called_once()
    
    def test_get_remaining_requests(self):
        """Test getting remaining requests"""
        self.redis_mock.zcard.return_value = 2
        
        remaining = self.strategy.get_remaining_requests(self.identifier, self.limits)
        
        assert remaining == 3  # 5 - 2 = 3

class TestComprehensiveRateLimiter:
    """Test comprehensive rate limiter"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.redis_mock = Mock()
        self.limiter = ComprehensiveRateLimiter(self.redis_mock)
        self.request_mock = Mock()
        self.request_mock.remote_addr = '192.168.1.1'
        self.request_mock.headers = {'User-Agent': 'test-agent'}
    
    def test_get_identifier_authenticated_user(self):
        """Test identifier for authenticated user"""
        # Create a mock g object
        g_mock = Mock()
        g_mock.get.return_value = 'user123'
        
        with patch('backend.middleware.rate_limiter.g', g_mock):
            identifier = self.limiter.get_identifier(self.request_mock)
            
            assert identifier == 'user:user123'
    
    def test_get_identifier_unauthenticated_user(self):
        """Test identifier for unauthenticated user"""
        # Create a mock g object
        g_mock = Mock()
        g_mock.get.return_value = None
        
        with patch('backend.middleware.rate_limiter.g', g_mock):
            identifier = self.limiter.get_identifier(self.request_mock)
            
            assert identifier.startswith('ip:192.168.1.1:')
    
    def test_get_identifier_admin_ip(self):
        """Test identifier for admin IP"""
        self.limiter.admin_ips = ['192.168.1.1']
        
        identifier = self.limiter.get_identifier(self.request_mock)
        
        assert identifier == 'admin:192.168.1.1'
    
    def test_get_identifier_whitelisted_ip(self):
        """Test identifier for whitelisted IP"""
        self.limiter.whitelisted_ips = ['192.168.1.1']
        
        identifier = self.limiter.get_identifier(self.request_mock)
        
        assert identifier == 'whitelisted:192.168.1.1'
    
    def test_get_client_ip_forwarded_for(self):
        """Test getting client IP from X-Forwarded-For header"""
        self.request_mock.headers['X-Forwarded-For'] = '10.0.0.1, 192.168.1.1'
        
        ip = self.limiter._get_client_ip(self.request_mock)
        
        assert ip == '10.0.0.1'
    
    def test_get_client_ip_real_ip(self):
        """Test getting client IP from X-Real-IP header"""
        self.request_mock.headers['X-Real-IP'] = '10.0.0.1'
        
        ip = self.limiter._get_client_ip(self.request_mock)
        
        assert ip == '10.0.0.1'
    
    def test_is_rate_limited_admin_bypass(self):
        """Test admin IP bypasses rate limiting"""
        identifier = 'admin:192.168.1.1'
        
        result = self.limiter.is_rate_limited(identifier, 'login')
        
        assert result['limited'] is False
        assert result['bypassed'] is True
    
    def test_is_rate_limited_with_redis(self):
        """Test rate limiting with Redis strategy"""
        identifier = 'user:123'
        
        with patch.object(self.limiter.strategy, 'check_rate_limit') as mock_check:
            mock_check.return_value = {
                'limited': False,
                'requests_made': 1,
                'limit': 5,
                'window_remaining': 60,
                'remaining_requests': 4
            }
            
            result = self.limiter.is_rate_limited(identifier, 'login')
            
            assert result['limited'] is False
            mock_check.assert_called_once_with(identifier, self.limiter.rate_limits['login'])
    
    def test_is_rate_limited_fallback_memory(self):
        """Test rate limiting fallback to memory storage"""
        limiter_no_redis = ComprehensiveRateLimiter(None)
        identifier = 'user:123'
        
        result = limiter_no_redis.is_rate_limited(identifier, 'login')
        
        assert 'limited' in result
        assert 'requests_made' in result
    
    def test_get_cultural_context(self):
        """Test getting cultural context from request"""
        self.request_mock.path = '/api/financial/planning'
        self.request_mock.headers['Accept-Language'] = 'en-US,en;q=0.9'
        
        context = self.limiter._get_cultural_context(self.request_mock)
        
        assert context['financial_professional'] is True
        assert context['preferred_language'] == 'en-US'
    
    def test_get_rate_limit_message_cultural(self):
        """Test getting culturally appropriate message"""
        message = self.limiter.get_rate_limit_message('login', cultural=True)
        
        assert 'financial information' in message
        assert 'secure access' in message
    
    def test_get_rate_limit_message_default(self):
        """Test getting default message"""
        message = self.limiter.get_rate_limit_message('login', cultural=False)
        
        assert 'Too many login attempts' in message

class TestRateLimitDecorators:
    """Test rate limiting decorators"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock rate limiter
        self.rate_limiter_mock = Mock()
        self.rate_limiter_mock.get_identifier.return_value = 'test_user:123'
        self.rate_limiter_mock.is_rate_limited.return_value = {
            'limited': False,
            'requests_made': 1,
            'limit': 5,
            'window_remaining': 60,
            'remaining_requests': 4
        }
        self.rate_limiter_mock.get_rate_limit_message.return_value = 'Test message'
    
    @patch('backend.middleware.rate_limit_decorators.get_rate_limiter')
    def test_rate_limit_decorator_success(self, mock_get_limiter):
        """Test rate limit decorator with successful request"""
        mock_get_limiter.return_value = self.rate_limiter_mock
        
        @rate_limit('login')
        def test_endpoint():
            return {'status': 'success'}, 200
        
        with self.app.test_request_context('/test'):
            response = test_endpoint()
            
            assert response[0]['status'] == 'success'
            assert response[1] == 200
    
    @patch('backend.middleware.rate_limit_decorators.get_rate_limiter')
    def test_rate_limit_decorator_exceeded(self, mock_get_limiter):
        """Test rate limit decorator with rate limit exceeded"""
        self.rate_limiter_mock.is_rate_limited.return_value = {
            'limited': True,
            'requests_made': 5,
            'limit': 5,
            'window_remaining': 60,
            'retry_after': 60
        }
        mock_get_limiter.return_value = self.rate_limiter_mock
        
        @rate_limit('login')
        def test_endpoint():
            return {'status': 'success'}, 200
        
        with self.app.test_request_context('/test'):
            response = test_endpoint()
            
            assert response.status_code == 429
            assert 'Rate limit exceeded' in response.get_json()['error']
    
    @patch('backend.middleware.rate_limit_decorators.get_rate_limiter')
    def test_rate_limit_by_user_authenticated(self, mock_get_limiter):
        """Test user-based rate limiting with authenticated user"""
        mock_get_limiter.return_value = self.rate_limiter_mock
        
        @rate_limit_by_user('financial_api')
        def test_endpoint():
            return {'status': 'success'}, 200
        
        with self.app.test_request_context('/test'):
            with patch('backend.middleware.rate_limit_decorators.g') as g_mock:
                g_mock.get.return_value = 'user123'
                
                response = test_endpoint()
                
                assert response[0]['status'] == 'success'
                assert response[1] == 200
    
    @patch('backend.middleware.rate_limit_decorators.get_rate_limiter')
    def test_rate_limit_by_user_unauthenticated(self, mock_get_limiter):
        """Test user-based rate limiting with unauthenticated user"""
        mock_get_limiter.return_value = self.rate_limiter_mock
        
        @rate_limit_by_user('financial_api')
        def test_endpoint():
            return {'status': 'success'}, 200
        
        with self.app.test_request_context('/test'):
            with patch('backend.middleware.rate_limit_decorators.g') as g_mock:
                g_mock.get.return_value = None
                
                response = test_endpoint()
                
                assert response[1] == 401
                assert 'Authentication required' in response[0]['error']
    
    @patch('backend.middleware.rate_limit_decorators.get_rate_limiter')
    def test_rate_limit_by_ip(self, mock_get_limiter):
        """Test IP-based rate limiting"""
        mock_get_limiter.return_value = self.rate_limiter_mock
        
        @rate_limit_by_ip('api_general')
        def test_endpoint():
            return {'status': 'success'}, 200
        
        with self.app.test_request_context('/test'):
            response = test_endpoint()
            
            assert response[0]['status'] == 'success'
            assert response[1] == 200
    
    @patch('backend.middleware.rate_limit_decorators.get_rate_limiter')
    def test_rate_limit_financial(self, mock_get_limiter):
        """Test financial endpoint rate limiting"""
        mock_get_limiter.return_value = self.rate_limiter_mock
        
        @rate_limit_financial('financial_api')
        def test_endpoint():
            return {'status': 'success'}, 200
        
        with self.app.test_request_context('/test'):
            response = test_endpoint()
            
            assert response[0]['status'] == 'success'
            assert response[1] == 200
    
    @patch('backend.middleware.rate_limit_decorators.get_rate_limiter')
    def test_rate_limit_payment_authenticated(self, mock_get_limiter):
        """Test payment endpoint rate limiting with authenticated user"""
        mock_get_limiter.return_value = self.rate_limiter_mock
        
        @rate_limit_payment('payment')
        def test_endpoint():
            return {'status': 'success'}, 200
        
        with self.app.test_request_context('/test'):
            with patch('backend.middleware.rate_limit_decorators.g') as g_mock:
                g_mock.get.return_value = 'user123'
                
                response = test_endpoint()
                
                assert response[0]['status'] == 'success'
                assert response[1] == 200
    
    @patch('backend.middleware.rate_limit_decorators.get_rate_limiter')
    def test_rate_limit_payment_unauthenticated(self, mock_get_limiter):
        """Test payment endpoint rate limiting with unauthenticated user"""
        mock_get_limiter.return_value = self.rate_limiter_mock
        
        @rate_limit_payment('payment')
        def test_endpoint():
            return {'status': 'success'}, 200
        
        with self.app.test_request_context('/test'):
            with patch('backend.middleware.rate_limit_decorators.g') as g_mock:
                g_mock.get.return_value = None
                
                response = test_endpoint()
                
                assert response[1] == 401
                assert 'Authentication required' in response[0]['error']

class TestRateLimitConfiguration:
    """Test rate limit configuration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.manager = RateLimitManager()
    
    def test_rate_limit_config_creation(self):
        """Test rate limit configuration creation"""
        config = RateLimitConfig(
            requests=10,
            window=300,
            message="Test message",
            cultural_message="Cultural test message",
            priority="high"
        )
        
        assert config.requests == 10
        assert config.window == 300
        assert config.priority == "high"
    
    def test_rate_limit_settings_defaults(self):
        """Test default rate limit settings"""
        settings = RateLimitSettings()
        
        assert settings.login.requests == 5
        assert settings.login.window == 900
        assert settings.login.priority == "critical"
        assert "financial information" in settings.login.cultural_message
    
    def test_rate_limit_manager_config_loading(self):
        """Test rate limit manager configuration loading"""
        config = self.manager.get_rate_limit_config('login')
        
        assert config.requests == 5
        assert config.window == 900
        assert config.priority == "critical"
    
    def test_rate_limit_manager_environment_specific(self):
        """Test environment-specific configuration"""
        with patch.dict('os.environ', {'FLASK_ENV': 'development'}):
            manager = RateLimitManager()
            config = manager.get_environment_specific_config('login')
            
            assert config.requests == 25  # 5 * 5 for development
            assert config.window == 900
    
    def test_rate_limit_manager_priority_filtering(self):
        """Test filtering configurations by priority"""
        critical_configs = self.manager.get_config_by_priority('critical')
        
        assert 'login' in critical_configs
        assert 'password_reset' in critical_configs
        assert 'payment' in critical_configs
    
    def test_cultural_message_retrieval(self):
        """Test cultural message retrieval"""
        message = self.manager.get_cultural_message('login', cultural=True)
        
        assert "financial information" in message
        assert "secure access" in message
    
    def test_default_message_retrieval(self):
        """Test default message retrieval"""
        message = self.manager.get_cultural_message('login', cultural=False)
        
        assert "Too many login attempts" in message

class TestRateLimitMonitoring:
    """Test rate limit monitoring system"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.redis_mock = Mock()
        self.monitor = RateLimitMonitor(self.redis_mock)
    
    def test_rate_limit_event_creation(self):
        """Test rate limit event creation"""
        event = RateLimitEvent(
            timestamp=time.time(),
            identifier='test_user:123',
            endpoint_type='login',
            requests_made=3,
            limit=5,
            limited=False,
            ip_address='192.168.1.1',
            user_id='user123',
            user_agent='test-agent',
            endpoint='login',
            method='POST',
            path='/api/auth/login',
            cultural_context={'african_american_focused': True}
        )
        
        assert event.identifier == 'test_user:123'
        assert event.endpoint_type == 'login'
        assert event.limited is False
    
    def test_rate_limit_alert_creation(self):
        """Test rate limit alert creation"""
        alert = RateLimitAlert(
            alert_id='test_alert_123',
            timestamp=time.time(),
            alert_type='threshold',
            severity='medium',
            message='Test alert message',
            data={'test': 'data'},
            endpoint_type='login',
            identifier='test_user:123',
            cultural_context={'african_american_focused': True}
        )
        
        assert alert.alert_id == 'test_alert_123'
        assert alert.severity == 'medium'
        assert alert.alert_type == 'threshold'
    
    def test_monitor_event_recording(self):
        """Test event recording in monitor"""
        event = RateLimitEvent(
            timestamp=time.time(),
            identifier='test_user:123',
            endpoint_type='login',
            requests_made=3,
            limit=5,
            limited=False,
            ip_address='192.168.1.1',
            user_id='user123',
            user_agent='test-agent',
            endpoint='login',
            method='POST',
            path='/api/auth/login',
            cultural_context={'african_american_focused': True}
        )
        
        self.monitor.record_event(event)
        
        assert len(self.monitor.events) == 1
        assert self.monitor.events[0].identifier == 'test_user:123'
    
    def test_monitor_metrics_update(self):
        """Test metrics update in monitor"""
        event = RateLimitEvent(
            timestamp=time.time(),
            identifier='test_user:123',
            endpoint_type='login',
            requests_made=3,
            limit=5,
            limited=False,
            ip_address='192.168.1.1',
            user_id='user123',
            user_agent='test-agent',
            endpoint='login',
            method='POST',
            path='/api/auth/login',
            cultural_context={'african_american_focused': True}
        )
        
        self.monitor.record_event(event)
        
        assert self.monitor.metrics['total_requests'] == 1
        assert self.monitor.metrics['endpoint_login_requests'] == 1
    
    def test_monitor_threshold_alert(self):
        """Test threshold-based alert generation"""
        event = RateLimitEvent(
            timestamp=time.time(),
            identifier='test_user:123',
            endpoint_type='login',
            requests_made=4,  # 80% of limit (5)
            limit=5,
            limited=False,
            ip_address='192.168.1.1',
            user_id='user123',
            user_agent='test-agent',
            endpoint='login',
            method='POST',
            path='/api/auth/login',
            cultural_context={'african_american_focused': True}
        )
        
        self.monitor.record_event(event)
        
        # Should generate threshold alert
        alerts = [a for a in self.monitor.alerts if a.alert_type == 'threshold']
        assert len(alerts) > 0
        assert alerts[0].severity == 'medium'  # 80% threshold
    
    def test_monitor_violation_alert(self):
        """Test violation alert generation"""
        event = RateLimitEvent(
            timestamp=time.time(),
            identifier='test_user:123',
            endpoint_type='login',
            requests_made=5,  # At limit
            limit=5,
            limited=True,  # Rate limited
            ip_address='192.168.1.1',
            user_id='user123',
            user_agent='test-agent',
            endpoint='login',
            method='POST',
            path='/api/auth/login',
            cultural_context={'african_american_focused': True}
        )
        
        self.monitor.record_event(event)
        
        # Should generate violation alert
        alerts = [a for a in self.monitor.alerts if a.alert_type == 'violation']
        assert len(alerts) > 0
        assert alerts[0].severity == 'high'
    
    def test_monitor_suspicious_activity_detection(self):
        """Test suspicious activity detection"""
        # Create multiple rapid requests
        for i in range(10):
            event = RateLimitEvent(
                timestamp=time.time() + i,  # Slightly different timestamps
                identifier='test_user:123',
                endpoint_type='login',
                requests_made=1,
                limit=5,
                limited=False,
                ip_address='192.168.1.1',
                user_id='user123',
                user_agent='test-agent',
                endpoint='login',
                method='POST',
                path='/api/auth/login',
                cultural_context={'african_american_focused': True}
            )
            self.monitor.record_event(event)
        
        # Should generate suspicious activity alert
        alerts = [a for a in self.monitor.alerts if a.alert_type == 'suspicious']
        assert len(alerts) > 0
        assert 'rapid_requests' in alerts[0].data['pattern']
    
    def test_monitor_metrics_retrieval(self):
        """Test metrics retrieval from monitor"""
        # Record some events
        for i in range(5):
            event = RateLimitEvent(
                timestamp=time.time(),
                identifier=f'test_user:{i}',
                endpoint_type='login',
                requests_made=1,
                limit=5,
                limited=False,
                ip_address='192.168.1.1',
                user_id=f'user{i}',
                user_agent='test-agent',
                endpoint='login',
                method='POST',
                path='/api/auth/login',
                cultural_context={'african_american_focused': True}
            )
            self.monitor.record_event(event)
        
        metrics = self.monitor.get_metrics()
        
        assert metrics['total_requests'] == 5
        assert metrics['endpoint_login_requests'] == 5
        assert metrics['recent_events'] == 5
    
    def test_monitor_alerts_retrieval(self):
        """Test alerts retrieval from monitor"""
        # Generate some alerts
        event = RateLimitEvent(
            timestamp=time.time(),
            identifier='test_user:123',
            endpoint_type='login',
            requests_made=5,
            limit=5,
            limited=True,
            ip_address='192.168.1.1',
            user_id='user123',
            user_agent='test-agent',
            endpoint='login',
            method='POST',
            path='/api/auth/login',
            cultural_context={'african_american_focused': True}
        )
        
        self.monitor.record_event(event)
        
        alerts = self.monitor.get_alerts(hours=1)
        assert len(alerts) > 0

class TestRateLimitIntegration:
    """Test rate limiting system integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['REDIS_URL'] = 'redis://localhost:6379/0'
        self.client = self.app.test_client()
    
    @patch('redis.from_url')
    def test_rate_limiter_redis_integration(self, mock_redis_from_url):
        """Test rate limiter with Redis integration"""
        mock_redis = Mock()
        mock_redis_from_url.return_value = mock_redis
        mock_redis.ping.return_value = True
        
        # Test that rate limiter can be created with Redis
        limiter = ComprehensiveRateLimiter(mock_redis)
        
        assert limiter.redis_client == mock_redis
        assert limiter.strategy is not None
    
    def test_rate_limiter_memory_fallback(self):
        """Test rate limiter memory fallback when Redis unavailable"""
        limiter = ComprehensiveRateLimiter(None)
        
        assert limiter.redis_client is None
        assert limiter.strategy is None
        
        # Should still work with memory fallback
        result = limiter.is_rate_limited('test_user:123', 'login')
        assert 'limited' in result
    
    def test_decorator_integration(self):
        """Test decorator integration with Flask app"""
        @self.app.route('/test')
        @rate_limit('login')
        def test_endpoint():
            return {'status': 'success'}, 200
        
        with patch('backend.middleware.rate_limit_decorators.get_rate_limiter') as mock_get_limiter:
            mock_limiter = Mock()
            mock_limiter.get_identifier.return_value = 'test_user:123'
            mock_limiter.is_rate_limited.return_value = {
                'limited': False,
                'requests_made': 1,
                'limit': 5,
                'window_remaining': 60,
                'remaining_requests': 4
            }
            mock_limiter.get_rate_limit_message.return_value = 'Test message'
            mock_get_limiter.return_value = mock_limiter
            
            response = self.client.get('/test')
            assert response.status_code == 200
    
    def test_monitoring_integration(self):
        """Test monitoring integration with rate limiting"""
        monitor = RateLimitMonitor()
        
        # Record an event
        event_data = {
            'timestamp': time.time(),
            'identifier': 'test_user:123',
            'endpoint_type': 'login',
            'requests_made': 3,
            'limit': 5,
            'limited': False,
            'ip_address': '192.168.1.1',
            'user_id': 'user123',
            'user_agent': 'test-agent',
            'endpoint': 'login',
            'method': 'POST',
            'path': '/api/auth/login',
            'cultural_context': {'african_american_focused': True}
        }
        
        record_rate_limit_event(event_data)
        
        # Verify event was recorded
        retrieved_monitor = get_rate_limit_monitor()
        events = retrieved_monitor.get_events(hours=1)
        
        assert len(events) > 0
        assert events[0].identifier == 'test_user:123'

if __name__ == '__main__':
    pytest.main([__file__])
