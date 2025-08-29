"""
Comprehensive Security Monitoring System Tests
Tests for security event logging, anomaly detection, and alerting system
"""

import unittest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.security.comprehensive_security_monitor import (
    SecurityMonitor,
    SecurityEventType,
    SecuritySeverity,
    SecurityEvent,
    AnomalyDetector,
    SecurityMonitoringMiddleware,
    SecurityAlerter
)
from backend.security.assessment_security_integration import (
    AssessmentSecurityIntegration,
    SecurityIntegrationManager
)
from backend.config.security_monitoring_config import SecurityMonitoringConfig

class TestSecurityEventLogging(unittest.TestCase):
    """Test security event logging functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_redis_client = Mock()
        self.security_monitor = SecurityMonitor(self.mock_db_session, self.mock_redis_client)
    
    def test_log_security_event(self):
        """Test logging a security event"""
        # Mock request context
        with patch('backend.security.comprehensive_security_monitor.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Mozilla/5.0'
            mock_request.endpoint = 'test_endpoint'
            mock_request.method = 'POST'
            
            # Test logging an auth failure event
            event = self.security_monitor.log_security_event(
                event_type=SecurityEventType.AUTH_FAILURE,
                user_identifier='test_user',
                details={'reason': 'invalid_password'},
                severity=SecuritySeverity.WARNING
            )
            
            # Verify event was created correctly
            self.assertEqual(event.event_type, SecurityEventType.AUTH_FAILURE)
            self.assertEqual(event.user_identifier, 'test_user')
            self.assertEqual(event.severity, SecuritySeverity.WARNING)
            self.assertEqual(event.ip_address, '192.168.1.1')
            self.assertEqual(event.endpoint, 'test_endpoint')
            self.assertEqual(event.method, 'POST')
            self.assertEqual(event.details['reason'], 'invalid_password')
    
    def test_log_injection_attempt(self):
        """Test logging injection attempt events"""
        with patch('backend.security.comprehensive_security_monitor.request') as mock_request:
            mock_request.remote_addr = '10.0.0.1'
            mock_request.headers.get.return_value = 'curl/7.68.0'
            mock_request.endpoint = 'assessment_submit'
            mock_request.method = 'POST'
            
            # Test SQL injection attempt
            event = self.security_monitor.log_security_event(
                event_type=SecurityEventType.SQL_INJECTION_ATTEMPT,
                user_identifier='malicious_user',
                details={'payload': "'; DROP TABLE users; --"},
                severity=SecuritySeverity.CRITICAL
            )
            
            self.assertEqual(event.event_type, SecurityEventType.SQL_INJECTION_ATTEMPT)
            self.assertEqual(event.severity, SecuritySeverity.CRITICAL)
            self.assertIn('DROP TABLE', event.details['payload'])
    
    def test_alert_threshold_checking(self):
        """Test alert threshold checking"""
        # Mock Redis to return count above threshold
        self.mock_redis_client.get.return_value = '6'  # Above threshold of 5
        
        with patch('backend.security.comprehensive_security_monitor.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Mozilla/5.0'
            mock_request.endpoint = 'login'
            mock_request.method = 'POST'
            
            # This should trigger an alert
            event = self.security_monitor.log_security_event(
                event_type=SecurityEventType.AUTH_FAILURE,
                user_identifier='test_user',
                details={'reason': 'invalid_password'},
                severity=SecuritySeverity.WARNING
            )
            
            # Verify alert was triggered
            self.mock_redis_client.get.assert_called()

class TestAnomalyDetection(unittest.TestCase):
    """Test anomaly detection functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.anomaly_detector = AnomalyDetector()
    
    def test_suspiciously_fast_completion(self):
        """Test detection of suspiciously fast assessment completion"""
        assessment_data = {
            'type': 'ai_job_risk',
            'completion_time': 10,  # 10 seconds (very fast)
            'responses': {'q1': 'yes', 'q2': 'no'},
            'score': 75
        }
        
        anomalies = self.anomaly_detector.detect_assessment_anomalies('test_user', assessment_data)
        
        # Should detect suspiciously fast completion
        fast_completion_anomalies = [a for a in anomalies if a['type'] == 'suspiciously_fast_completion']
        self.assertGreater(len(fast_completion_anomalies), 0)
        self.assertEqual(fast_completion_anomalies[0]['value'], 10)
    
    def test_suspicious_answer_patterns(self):
        """Test detection of suspicious answer patterns"""
        # Test all identical answers
        assessment_data = {
            'type': 'relationship_impact',
            'completion_time': 300,
            'responses': {'q1': 'yes', 'q2': 'yes', 'q3': 'yes', 'q4': 'yes', 'q5': 'yes'},
            'score': 50
        }
        
        anomalies = self.anomaly_detector.detect_assessment_anomalies('test_user', assessment_data)
        
        pattern_anomalies = [a for a in anomalies if a['type'] == 'suspicious_answer_pattern']
        self.assertGreater(len(pattern_anomalies), 0)
    
    def test_sequential_pattern_detection(self):
        """Test detection of sequential patterns"""
        assessment_data = {
            'type': 'tax_impact',
            'completion_time': 180,
            'responses': {'q1': 1, 'q2': 2, 'q3': 3, 'q4': 4, 'q5': 5},
            'score': 60
        }
        
        anomalies = self.anomaly_detector.detect_assessment_anomalies('test_user', assessment_data)
        
        pattern_anomalies = [a for a in anomalies if a['type'] == 'suspicious_answer_pattern']
        self.assertGreater(len(pattern_anomalies), 0)
    
    def test_unusual_score_detection(self):
        """Test detection of unusual scores"""
        # Test score outside normal range
        assessment_data = {
            'type': 'ai_job_risk',
            'completion_time': 240,
            'responses': {'q1': 'yes', 'q2': 'no'},
            'score': 95  # Outside normal range (20-80)
        }
        
        anomalies = self.anomaly_detector.detect_assessment_anomalies('test_user', assessment_data)
        
        score_anomalies = [a for a in anomalies if a['type'] == 'unusual_score']
        self.assertGreater(len(score_anomalies), 0)
        self.assertEqual(score_anomalies[0]['value'], 95)

class TestSecurityMonitoringMiddleware(unittest.TestCase):
    """Test security monitoring middleware"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_redis_client = Mock()
        self.security_monitor = SecurityMonitor(self.mock_db_session, self.mock_redis_client)
        self.anomaly_detector = AnomalyDetector()
        self.middleware = SecurityMonitoringMiddleware(self.security_monitor, self.anomaly_detector)
    
    def test_assessment_submission_monitoring(self):
        """Test monitoring of assessment submissions"""
        assessment_data = {
            'type': 'ai_job_risk',
            'completion_time': 10,  # Suspiciously fast
            'responses': {'q1': 'yes', 'q2': 'yes', 'q3': 'yes'},  # Suspicious pattern
            'score': 75
        }
        
        with patch('backend.security.comprehensive_security_monitor.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Mozilla/5.0'
            mock_request.endpoint = 'assessment_submit'
            mock_request.method = 'POST'
            
            self.middleware.monitor_assessment_submission('test_user', assessment_data)
            
            # Verify security events were logged
            self.mock_db_session.execute.assert_called()
    
    def test_authentication_monitoring(self):
        """Test monitoring of authentication attempts"""
        with patch('backend.security.comprehensive_security_monitor.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Mozilla/5.0'
            mock_request.endpoint = 'login'
            mock_request.method = 'POST'
            
            # Test failed authentication
            self.middleware.monitor_authentication('test_user', False, {
                'reason': 'invalid_password',
                'attempt_count': 3
            })
            
            # Verify security event was logged
            self.mock_db_session.execute.assert_called()
    
    def test_suspicious_pattern_detection(self):
        """Test detection of suspicious patterns in responses"""
        # Test XSS attempt
        responses = {
            'q1': 'normal answer',
            'q2': '<script>alert("xss")</script>',
            'q3': 'another normal answer'
        }
        
        is_suspicious = self.middleware._detect_suspicious_patterns(responses)
        self.assertTrue(is_suspicious)
        
        # Test SQL injection attempt
        responses = {
            'q1': 'normal answer',
            'q2': "'; DROP TABLE users; --",
            'q3': 'another normal answer'
        }
        
        is_suspicious = self.middleware._detect_suspicious_patterns(responses)
        self.assertTrue(is_suspicious)
        
        # Test normal responses
        responses = {
            'q1': 'normal answer',
            'q2': 'another normal answer',
            'q3': 'yet another normal answer'
        }
        
        is_suspicious = self.middleware._detect_suspicious_patterns(responses)
        self.assertFalse(is_suspicious)

class TestSecurityAlerter(unittest.TestCase):
    """Test security alerting functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.alerter = SecurityAlerter(
            smtp_host='smtp.test.com',
            smtp_port=587,
            username='test@test.com',
            password='test_password'
        )
    
    @patch('smtplib.SMTP')
    def test_send_security_alert_email(self, mock_smtp):
        """Test sending security alert emails"""
        alert_data = {
            'event_type': 'auth_failure',
            'count': 5,
            'timeframe': 300,
            'latest_event': {
                'timestamp': '2023-01-01T12:00:00Z',
                'ip_address': '192.168.1.1',
                'user_agent': 'Mozilla/5.0',
                'endpoint': 'login',
                'user_identifier': 'test_user'
            }
        }
        
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        self.alerter.send_security_alert_email(alert_data)
        
        # Verify SMTP was called
        mock_smtp.assert_called_with('smtp.test.com', 587)
        mock_server.starttls.assert_called()
        mock_server.login.assert_called_with('test@test.com', 'test_password')
        mock_server.send_message.assert_called()
        mock_server.quit.assert_called()

class TestAssessmentSecurityIntegration(unittest.TestCase):
    """Test assessment security integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_redis_client = Mock()
        self.integration = AssessmentSecurityIntegration(self.mock_db_session, self.mock_redis_client)
    
    def test_secure_assessment_endpoint_decorator(self):
        """Test secure assessment endpoint decorator"""
        @self.integration.secure_assessment_endpoint
        def test_endpoint():
            return {'status': 'success'}
        
        with patch('backend.security.assessment_security_integration.request') as mock_request:
            mock_request.json = {
                'assessment_data': {
                    'type': 'ai_job_risk',
                    'completion_time': 240,
                    'responses': {'q1': 'yes', 'q2': 'no'},
                    'score': 75
                }
            }
            mock_request.method = 'POST'
            mock_request.endpoint = 'assessment_submit'
            mock_request.remote_addr = '192.168.1.1'
            
            result = test_endpoint()
            
            # Verify security monitoring was applied
            self.mock_db_session.execute.assert_called()
    
    def test_input_validation(self):
        """Test input validation for security threats"""
        with patch('backend.security.assessment_security_integration.request') as mock_request:
            # Test with malicious input
            mock_request.json = {
                'assessment_data': {
                    'type': 'ai_job_risk',
                    'responses': {
                        'q1': '<script>alert("xss")</script>',
                        'q2': "'; DROP TABLE users; --"
                    }
                }
            }
            mock_request.args = {}
            mock_request.method = 'POST'
            
            validation_result = self.integration._validate_assessment_input(mock_request)
            
            # Should detect security threats
            self.assertFalse(validation_result['valid'])
            self.assertGreater(len(validation_result['errors']), 0)
    
    def test_get_user_identifier(self):
        """Test user identifier extraction"""
        with patch('backend.security.assessment_security_integration.g') as mock_g:
            # Test with user_id in g context
            mock_g.user_id = 'test_user'
            
            user_id = self.integration._get_user_identifier()
            self.assertEqual(user_id, 'test_user')
            
            # Test fallback to IP address
            mock_g.user_id = None
            with patch('backend.security.assessment_security_integration.request') as mock_request:
                mock_request.remote_addr = '192.168.1.1'
                
                user_id = self.integration._get_user_identifier()
                self.assertEqual(user_id, '192.168.1.1')

class TestSecurityMonitoringConfig(unittest.TestCase):
    """Test security monitoring configuration"""
    
    def test_get_assessment_config(self):
        """Test getting assessment configuration"""
        config = SecurityMonitoringConfig.get_assessment_config('ai_job_risk')
        
        self.assertEqual(config['avg_completion_time'], 240)
        self.assertEqual(config['score_range'], (20, 80))
        self.assertEqual(config['min_questions'], 5)
        self.assertEqual(config['max_questions'], 20)
    
    def test_get_alert_threshold(self):
        """Test getting alert threshold configuration"""
        threshold = SecurityMonitoringConfig.get_alert_threshold('failed_logins')
        
        self.assertEqual(threshold['count'], 5)
        self.assertEqual(threshold['window'], 300)
        self.assertEqual(threshold['severity'], 'WARNING')
    
    def test_is_monitoring_enabled(self):
        """Test monitoring feature enablement"""
        # Test with default values
        self.assertTrue(SecurityMonitoringConfig.is_monitoring_enabled('real_time_monitoring'))
        self.assertTrue(SecurityMonitoringConfig.is_monitoring_enabled('email_alerts'))
        self.assertTrue(SecurityMonitoringConfig.is_monitoring_enabled('anomaly_detection'))
    
    def test_get_retention_days(self):
        """Test getting retention periods"""
        retention_days = SecurityMonitoringConfig.get_retention_days('security_events')
        self.assertEqual(retention_days, 90)
        
        retention_days = SecurityMonitoringConfig.get_retention_days('audit_log')
        self.assertEqual(retention_days, 365)

class TestSecurityIntegrationManager(unittest.TestCase):
    """Test security integration manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_redis_client = Mock()
        self.manager = SecurityIntegrationManager(self.mock_db_session, self.mock_redis_client)
    
    def test_setup_security_monitoring(self):
        """Test setting up security monitoring for Flask app"""
        mock_app = Mock()
        
        self.manager.setup_security_monitoring(mock_app)
        
        # Verify before_request and after_request were registered
        mock_app.before_request.assert_called()
        mock_app.after_request.assert_called()
    
    def test_log_request_for_security(self):
        """Test logging requests for security analysis"""
        with patch('backend.security.assessment_security_integration.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Mozilla/5.0'
            mock_request.endpoint = 'test_endpoint'
            mock_request.method = 'GET'
            mock_request.content_length = 100
            mock_request.content_type = 'application/json'
            
            self.manager._log_request_for_security()
            
            # Verify security event was logged
            self.mock_db_session.execute.assert_called()
    
    def test_check_suspicious_patterns(self):
        """Test checking for suspicious patterns in requests"""
        with patch('backend.security.assessment_security_integration.request') as mock_request:
            # Test suspicious user agent
            mock_request.headers = {
                'User-Agent': 'curl/7.68.0'
            }
            mock_request.remote_addr = '192.168.1.1'
            mock_request.endpoint = 'test_endpoint'
            
            self.manager._check_request_suspicious_patterns()
            
            # Verify security event was logged for suspicious user agent
            self.mock_db_session.execute.assert_called()

def run_comprehensive_tests():
    """Run all comprehensive security monitoring tests"""
    print("Running Comprehensive Security Monitoring Tests...")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestSecurityEventLogging,
        TestAnomalyDetection,
        TestSecurityMonitoringMiddleware,
        TestSecurityAlerter,
        TestAssessmentSecurityIntegration,
        TestSecurityMonitoringConfig,
        TestSecurityIntegrationManager
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
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
    sys.exit(0 if success else 1)
