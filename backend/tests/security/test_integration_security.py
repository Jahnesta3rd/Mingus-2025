"""
Integration Security Validation Tests for MINGUS Financial Application
====================================================================

This module provides comprehensive integration security testing:
1. Authentication + CSRF + JWT working together tests
2. PCI DSS compliance maintained tests
3. Security monitoring integration tests
4. Incident response integration tests
5. End-to-end security workflow tests
6. Cross-system security validation tests

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
import threading
import queue

from backend.auth.jwt_handler import JWTManager
from backend.auth.mfa_manager import MFAManager
from backend.auth.rbac_manager import RBACManager
from backend.auth.session_manager import SessionManager
from backend.security.csrf_protection_comprehensive import ComprehensiveCSRFProtection
from backend.security.csrf_middleware_comprehensive import (
    ComprehensiveCSRFMiddleware,
    require_financial_csrf,
    require_payment_csrf
)
from backend.security.csrf_monitoring import CSRFMonitoringSystem, SecurityEventType, SecuritySeverity
from backend.utils.audit_logger import AuditLogger
from backend.utils.security_monitoring import SecurityMonitoringSystem
from backend.utils.incident_response import IncidentResponseSystem

class TestIntegrationSecurity:
    """Test integration security controls"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
        app.config['STRIPE_SECRET_KEY'] = 'sk_test_fake_key'
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def jwt_manager(self, app):
        """Create JWT manager instance"""
        return JWTManager(app)
    
    @pytest.fixture
    def mfa_manager(self, app):
        """Create MFA manager instance"""
        return MFAManager(app)
    
    @pytest.fixture
    def rbac_manager(self, app):
        """Create RBAC manager instance"""
        return RBACManager(app)
    
    @pytest.fixture
    def session_manager(self, app):
        """Create session manager instance"""
        return SessionManager(app)
    
    @pytest.fixture
    def csrf_protection(self, app):
        """Create CSRF protection instance"""
        mock_redis = Mock()
        return ComprehensiveCSRFProtection(app, mock_redis)
    
    @pytest.fixture
    def csrf_middleware(self, app):
        """Create CSRF middleware instance"""
        mock_redis = Mock()
        return ComprehensiveCSRFMiddleware(app, mock_redis)
    
    @pytest.fixture
    def audit_logger(self, app):
        """Create audit logger instance"""
        return AuditLogger(app)
    
    @pytest.fixture
    def security_monitoring(self, app):
        """Create security monitoring instance"""
        return SecurityMonitoringSystem(app)
    
    @pytest.fixture
    def incident_response(self, app):
        """Create incident response instance"""
        return IncidentResponseSystem(app)

class TestAuthenticationCSRFJWTIntegration:
    """Test authentication, CSRF, and JWT working together"""
    
    def test_complete_security_workflow(self, client, jwt_manager, mfa_manager, rbac_manager, csrf_protection):
        """Test complete security workflow integration"""
        # Step 1: User authentication
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Step 2: MFA validation
        mfa_token = mfa_manager.generate_mfa_token('test_user')
        
        # Step 3: CSRF token generation
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Step 4: RBAC permission check
        with patch.object(rbac_manager, 'has_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Step 5: Complete request with all security layers
            response = client.post('/api/payments/create',
                                 headers={
                                     'Authorization': f'Bearer {access_token}',
                                     'X-MFA-Token': mfa_token,
                                     'X-CSRF-Token': csrf_token
                                 },
                                 json={
                                     'amount': 1000,
                                     'currency': 'usd',
                                     'payment_method': 'pm_test_123'
                                 })
            
            assert response.status_code == 200, "Complete security workflow should succeed"
    
    def test_security_layer_failure_cascade(self, client, jwt_manager, mfa_manager, rbac_manager, csrf_protection):
        """Test security layer failure cascade"""
        # Test JWT failure
        response = client.post('/api/payments/create',
                             headers={
                                 'Authorization': 'Bearer invalid_token',
                                 'X-MFA-Token': 'valid_mfa_token',
                                 'X-CSRF-Token': 'valid_csrf_token'
                             },
                             json={'amount': 1000, 'currency': 'usd'})
        
        assert response.status_code in [401, 403], "JWT failure should block request"
        
        # Test MFA failure
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        response = client.post('/api/payments/create',
                             headers={
                                 'Authorization': f'Bearer {access_token}',
                                 'X-MFA-Token': 'invalid_mfa_token',
                                 'X-CSRF-Token': 'valid_csrf_token'
                             },
                             json={'amount': 1000, 'currency': 'usd'})
        
        assert response.status_code in [401, 403], "MFA failure should block request"
        
        # Test CSRF failure
        mfa_token = mfa_manager.generate_mfa_token('test_user')
        response = client.post('/api/payments/create',
                             headers={
                                 'Authorization': f'Bearer {access_token}',
                                 'X-MFA-Token': mfa_token,
                                 'X-CSRF-Token': 'invalid_csrf_token'
                             },
                             json={'amount': 1000, 'currency': 'usd'})
        
        assert response.status_code in [403, 400], "CSRF failure should block request"
        
        # Test RBAC failure
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        with patch.object(rbac_manager, 'has_permission') as mock_permission:
            mock_permission.return_value = False
            
            response = client.post('/api/payments/create',
                                 headers={
                                     'Authorization': f'Bearer {access_token}',
                                     'X-MFA-Token': mfa_token,
                                     'X-CSRF-Token': csrf_token
                                 },
                                 json={'amount': 1000, 'currency': 'usd'})
            
            assert response.status_code in [401, 403], "RBAC failure should block request"
    
    def test_security_token_rotation_integration(self, client, jwt_manager, csrf_protection):
        """Test security token rotation integration"""
        # Generate initial tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Use tokens
        response = client.get('/api/financial/data',
                            headers={
                                'Authorization': f'Bearer {access_token}',
                                'X-CSRF-Token': csrf_token
                            })
        
        assert response.status_code == 200, "Initial tokens should work"
        
        # Rotate JWT token
        refresh_token = jwt_manager.generate_refresh_token('test_user')
        new_tokens = jwt_manager.refresh_tokens(refresh_token)
        
        # Rotate CSRF token
        new_csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        new_csrf_token = new_csrf_token_data['token']
        
        # Use new tokens
        response = client.get('/api/financial/data',
                            headers={
                                'Authorization': f'Bearer {new_tokens["access_token"]}',
                                'X-CSRF-Token': new_csrf_token
                            })
        
        assert response.status_code == 200, "Rotated tokens should work"
        
        # Verify old tokens are invalid
        response = client.get('/api/financial/data',
                            headers={
                                'Authorization': f'Bearer {access_token}',
                                'X-CSRF-Token': csrf_token
                            })
        
        assert response.status_code in [401, 403], "Old tokens should be invalid"

class TestPCIDSSComplianceIntegration:
    """Test PCI DSS compliance integration"""
    
    def test_pci_compliance_end_to_end(self, client, jwt_manager, mfa_manager, rbac_manager, csrf_protection, audit_logger):
        """Test PCI DSS compliance end-to-end"""
        # Generate all required tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        mfa_token = mfa_manager.generate_mfa_token('test_user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Mock Stripe payment
        with patch('stripe.PaymentIntent.create') as mock_stripe:
            mock_stripe.return_value = Mock(
                id='pi_test_123',
                status='succeeded',
                amount=1000,
                currency='usd'
            )
            
            # Process payment with all security controls
            with patch.object(rbac_manager, 'has_permission') as mock_permission:
                with patch.object(audit_logger, 'log_audit_event') as mock_audit:
                    mock_permission.return_value = True
                    
                    response = client.post('/api/payments/create',
                                         headers={
                                             'Authorization': f'Bearer {access_token}',
                                             'X-MFA-Token': mfa_token,
                                             'X-CSRF-Token': csrf_token
                                         },
                                         json={
                                             'amount': 1000,
                                             'currency': 'usd',
                                             'payment_method': 'pm_test_123'
                                         })
                    
                    assert response.status_code == 200, "PCI compliant payment should succeed"
                    
                    # Verify audit logging
                    mock_audit.assert_called()
                    
                    # Verify PCI compliance headers
                    assert 'X-PCI-Compliant' in response.headers, "Response should include PCI compliance header"
    
    def test_pci_compliance_violation_detection(self, client, jwt_manager, audit_logger, security_monitoring):
        """Test PCI DSS compliance violation detection"""
        # Generate valid JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Simulate PCI compliance violation (missing MFA)
        with patch.object(audit_logger, 'log_audit_event') as mock_audit:
            with patch.object(security_monitoring, 'detect_compliance_violation') as mock_detection:
                mock_detection.return_value = True
                
                response = client.post('/api/payments/create',
                                     headers={
                                         'Authorization': f'Bearer {access_token}'
                                         # Missing MFA and CSRF tokens
                                     },
                                     json={'amount': 1000, 'currency': 'usd'})
                
                assert response.status_code in [401, 403], "PCI violation should be detected"
                
                # Verify compliance violation logging
                mock_audit.assert_called()
                mock_detection.assert_called()
    
    def test_pci_compliance_encryption_integration(self, client, jwt_manager, rbac_manager):
        """Test PCI DSS compliance encryption integration"""
        # Generate valid JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test encrypted data access
        with patch.object(rbac_manager, 'has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/payments/history',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200, "Encrypted payment data should be accessible"
            
            # Verify encryption headers
            assert 'X-Encryption-Status' in response.headers, "Response should include encryption status"
            assert response.headers['X-Encryption-Status'] == 'AES-256-GCM', "Should use AES-256-GCM encryption"

class TestSecurityMonitoringIntegration:
    """Test security monitoring integration"""
    
    def test_security_monitoring_comprehensive(self, client, jwt_manager, csrf_protection, security_monitoring):
        """Test comprehensive security monitoring"""
        # Generate tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Test successful request monitoring
        with patch.object(security_monitoring, 'log_security_event') as mock_monitoring:
            response = client.get('/api/financial/data',
                                headers={
                                    'Authorization': f'Bearer {access_token}',
                                    'X-CSRF-Token': csrf_token
                                })
            
            assert response.status_code == 200, "Request should succeed"
            
            # Verify security monitoring
            mock_monitoring.assert_called()
    
    def test_security_monitoring_failure_detection(self, client, security_monitoring):
        """Test security monitoring failure detection"""
        # Test failed authentication monitoring
        with patch.object(security_monitoring, 'log_security_event') as mock_monitoring:
            response = client.get('/api/financial/data',
                                headers={'Authorization': 'Bearer invalid_token'})
            
            assert response.status_code in [401, 403], "Invalid token should be rejected"
            
            # Verify failure monitoring
            mock_monitoring.assert_called()
    
    def test_security_monitoring_alerting(self, client, security_monitoring):
        """Test security monitoring alerting"""
        # Simulate multiple failed attempts
        with patch.object(security_monitoring, 'send_security_alert') as mock_alert:
            for i in range(5):
                response = client.get('/api/financial/data',
                                    headers={'Authorization': 'Bearer invalid_token'})
            
            # Verify security alert
            mock_alert.assert_called()

class TestIncidentResponseIntegration:
    """Test incident response integration"""
    
    def test_incident_response_automation(self, client, incident_response):
        """Test incident response automation"""
        # Simulate security incident
        with patch.object(incident_response, 'handle_security_incident') as mock_incident:
            response = client.post('/api/payments/create',
                                 headers={'Authorization': 'Bearer invalid_token'},
                                 json={'amount': 1000, 'currency': 'usd'})
            
            assert response.status_code in [401, 403], "Security incident should be detected"
            
            # Verify incident response
            mock_incident.assert_called()
    
    def test_incident_response_escalation(self, client, incident_response):
        """Test incident response escalation"""
        # Simulate critical security incident
        with patch.object(incident_response, 'escalate_incident') as mock_escalation:
            # Multiple failed attempts
            for i in range(10):
                response = client.post('/api/payments/create',
                                     headers={'Authorization': 'Bearer invalid_token'},
                                     json={'amount': 1000, 'currency': 'usd'})
            
            # Verify incident escalation
            mock_escalation.assert_called()
    
    def test_incident_response_recovery(self, client, jwt_manager, incident_response):
        """Test incident response recovery"""
        # Generate valid token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test recovery after incident
        with patch.object(incident_response, 'recover_from_incident') as mock_recovery:
            response = client.get('/api/financial/data',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200, "Recovery should succeed"
            
            # Verify recovery process
            mock_recovery.assert_called()

class TestCrossSystemSecurityValidation:
    """Test cross-system security validation"""
    
    def test_authentication_session_integration(self, client, jwt_manager, session_manager):
        """Test authentication and session integration"""
        # Create session
        session_data = session_manager.create_session('test_user')
        session_id = session_data['session_id']
        
        # Generate JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test integrated authentication
        response = client.get('/api/financial/data',
                            headers={
                                'Authorization': f'Bearer {access_token}',
                                'X-Session-ID': session_id
                            })
        
        assert response.status_code == 200, "Integrated authentication should work"
        
        # Test session invalidation
        session_manager.invalidate_session(session_id)
        
        response = client.get('/api/financial/data',
                            headers={
                                'Authorization': f'Bearer {access_token}',
                                'X-Session-ID': session_id
                            })
        
        assert response.status_code in [401, 403], "Invalidated session should be rejected"
    
    def test_csrf_session_integration(self, client, csrf_protection, session_manager):
        """Test CSRF and session integration"""
        # Create session
        session_data = session_manager.create_session('test_user')
        session_id = session_data['session_id']
        
        # Generate CSRF token
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', session_id)
        csrf_token = csrf_token_data['token']
        
        # Test integrated CSRF protection
        response = client.post('/api/financial/data',
                             headers={
                                 'X-CSRF-Token': csrf_token,
                                 'X-Session-ID': session_id
                             },
                             json={'data': 'test'})
        
        assert response.status_code == 200, "Integrated CSRF protection should work"
        
        # Test session invalidation
        session_manager.invalidate_session(session_id)
        
        response = client.post('/api/financial/data',
                             headers={
                                 'X-CSRF-Token': csrf_token,
                                 'X-Session-ID': session_id
                             },
                             json={'data': 'test'})
        
        assert response.status_code in [401, 403], "Invalidated session should reject CSRF token"
    
    def test_rbac_mfa_integration(self, client, jwt_manager, mfa_manager, rbac_manager):
        """Test RBAC and MFA integration"""
        # Generate tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        mfa_token = mfa_manager.generate_mfa_token('test_user')
        
        # Test integrated RBAC and MFA
        with patch.object(rbac_manager, 'has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/admin/users',
                                headers={
                                    'Authorization': f'Bearer {access_token}',
                                    'X-MFA-Token': mfa_token
                                })
            
            assert response.status_code == 200, "Integrated RBAC and MFA should work"
        
        # Test MFA failure with RBAC
        with patch.object(rbac_manager, 'has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/admin/users',
                                headers={
                                    'Authorization': f'Bearer {access_token}',
                                    'X-MFA-Token': 'invalid_mfa_token'
                                })
            
            assert response.status_code in [401, 403], "MFA failure should block RBAC access"

class TestEndToEndSecurityWorkflow:
    """Test end-to-end security workflow"""
    
    def test_complete_user_journey_security(self, client, jwt_manager, mfa_manager, rbac_manager, csrf_protection, session_manager):
        """Test complete user journey security"""
        # Step 1: User login
        session_data = session_manager.create_session('test_user')
        session_id = session_data['session_id']
        
        # Step 2: Generate authentication tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        mfa_token = mfa_manager.generate_mfa_token('test_user')
        
        # Step 3: Generate CSRF token
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', session_id)
        csrf_token = csrf_token_data['token']
        
        # Step 4: Access financial data
        with patch.object(rbac_manager, 'has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/financial/data',
                                headers={
                                    'Authorization': f'Bearer {access_token}',
                                    'X-MFA-Token': mfa_token,
                                    'X-CSRF-Token': csrf_token,
                                    'X-Session-ID': session_id
                                })
            
            assert response.status_code == 200, "Financial data access should succeed"
        
        # Step 5: Create payment
        with patch('stripe.PaymentIntent.create') as mock_stripe:
            mock_stripe.return_value = Mock(
                id='pi_test_123',
                status='succeeded',
                amount=1000,
                currency='usd'
            )
            
            response = client.post('/api/payments/create',
                                 headers={
                                     'Authorization': f'Bearer {access_token}',
                                     'X-MFA-Token': mfa_token,
                                     'X-CSRF-Token': csrf_token,
                                     'X-Session-ID': session_id
                                 },
                                 json={
                                     'amount': 1000,
                                     'currency': 'usd',
                                     'payment_method': 'pm_test_123'
                                 })
            
            assert response.status_code == 200, "Payment creation should succeed"
        
        # Step 6: Logout
        session_manager.invalidate_session(session_id)
        jwt_manager.blacklist_token(access_token)
        
        # Step 7: Verify logout
        response = client.get('/api/financial/data',
                            headers={
                                'Authorization': f'Bearer {access_token}',
                                'X-MFA-Token': mfa_token,
                                'X-CSRF-Token': csrf_token,
                                'X-Session-ID': session_id
                            })
        
        assert response.status_code in [401, 403], "Logged out user should be rejected"
    
    def test_security_workflow_performance(self, client, jwt_manager, mfa_manager, rbac_manager, csrf_protection):
        """Test security workflow performance"""
        # Generate all tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        mfa_token = mfa_manager.generate_mfa_token('test_user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        start_time = time.time()
        
        # Execute multiple requests
        with patch.object(rbac_manager, 'has_permission') as mock_permission:
            mock_permission.return_value = True
            
            for i in range(100):
                response = client.get('/api/financial/data',
                                    headers={
                                        'Authorization': f'Bearer {access_token}',
                                        'X-MFA-Token': mfa_token,
                                        'X-CSRF-Token': csrf_token
                                    })
                
                assert response.status_code == 200, f"Request {i+1} should succeed"
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 100 requests in less than 5 seconds
        assert duration < 5.0, f"Security workflow took {duration}s, should be < 5s"
        assert duration / 100 < 0.05, "Should complete requests in < 50ms each"

class TestConcurrentSecurityValidation:
    """Test concurrent security validation"""
    
    def test_concurrent_authentication_validation(self, client, jwt_manager):
        """Test concurrent authentication validation"""
        # Generate multiple tokens
        tokens = []
        for i in range(50):
            token = jwt_manager.generate_access_token(f'test_user_{i}', 'user')
            tokens.append(token)
        
        results = queue.Queue()
        
        def validate_token(token):
            response = client.get('/api/financial/data',
                                headers={'Authorization': f'Bearer {token}'})
            results.put(response.status_code == 200)
        
        # Create multiple threads
        threads = []
        for token in tokens:
            thread = threading.Thread(target=validate_token, args=(token,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all validations succeeded
        success_count = 0
        while not results.empty():
            if results.get():
                success_count += 1
        
        assert success_count == 50, f"All {success_count} concurrent authentications should succeed"
    
    def test_concurrent_csrf_validation(self, client, csrf_protection):
        """Test concurrent CSRF validation"""
        # Generate multiple CSRF tokens
        csrf_tokens = []
        for i in range(50):
            csrf_token_data = csrf_protection.generate_csrf_token(f'test_user_{i}', f'test_session_{i}')
            csrf_tokens.append(csrf_token_data['token'])
        
        results = queue.Queue()
        
        def validate_csrf(csrf_token):
            response = client.post('/api/financial/data',
                                 headers={'X-CSRF-Token': csrf_token},
                                 json={'data': 'test'})
            results.put(response.status_code == 200)
        
        # Create multiple threads
        threads = []
        for csrf_token in csrf_tokens:
            thread = threading.Thread(target=validate_csrf, args=(csrf_token,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all validations succeeded
        success_count = 0
        while not results.empty():
            if results.get():
                success_count += 1
        
        assert success_count == 50, f"All {success_count} concurrent CSRF validations should succeed"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
