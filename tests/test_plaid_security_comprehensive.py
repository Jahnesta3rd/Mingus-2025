"""
Comprehensive Plaid Security Testing Suite

This module provides comprehensive security testing for Plaid banking integrations
including data encryption validation, access control verification, token security
and rotation testing, API endpoint security scanning, data privacy compliance
testing, and penetration testing for banking features.
"""

import pytest
import unittest
import json
import hashlib
import hmac
import base64
import secrets
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import cryptography.fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import requests
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.security.plaid_security_service import PlaidSecurityService
from backend.security.access_control_service import AccessControlService
from backend.security.audit_logging import AuditLoggingService
from backend.banking.plaid_integration import PlaidIntegration
from backend.models.user_models import User
from backend.models.bank_account_models import BankAccount, PlaidConnection


class TestDataEncryptionValidation(unittest.TestCase):
    """Test data encryption validation for Plaid integrations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        
        self.plaid_security = PlaidSecurityService(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_access_token_encryption_strength(self):
        """Test access token encryption strength and validation"""
        # Test data
        original_token = "access-sandbox-12345678-1234-1234-1234-123456789012"
        
        # Encrypt access token
        encrypted_token = self.plaid_security.encrypt_access_token(original_token)
        
        # Verify encryption strength
        self.assertNotEqual(encrypted_token, original_token)
        self.assertIsInstance(encrypted_token, str)
        self.assertGreater(len(encrypted_token), len(original_token))
        
        # Verify encryption uses strong algorithm
        self.assertTrue(encrypted_token.startswith('gAAAAA'))  # Fernet base64 prefix
        
        # Test decryption
        decrypted_token = self.plaid_security.decrypt_access_token(encrypted_token)
        self.assertEqual(decrypted_token, original_token)
    
    def test_sensitive_data_encryption_validation(self):
        """Test sensitive data encryption validation"""
        # Test various sensitive data types
        sensitive_data_sets = [
            {
                'account_number': '1234567890',
                'routing_number': '987654321',
                'card_number': '4111111111111111',
                'cvv': '123',
                'ssn': '123-45-6789'
            },
            {
                'bank_credentials': 'username:password',
                'api_keys': 'sk_test_1234567890abcdef',
                'private_keys': '-----BEGIN PRIVATE KEY-----'
            },
            {
                'personal_info': {
                    'name': 'John Doe',
                    'email': 'john.doe@example.com',
                    'phone': '123-456-7890',
                    'address': '123 Main St, City, State 12345'
                }
            }
        ]
        
        for sensitive_data in sensitive_data_sets:
            # Encrypt sensitive data
            encrypted_data = self.plaid_security.encrypt_sensitive_data(sensitive_data)
            
            # Verify all sensitive fields are encrypted
            for key, value in sensitive_data.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        encrypted_value = encrypted_data[key][sub_key]
                        self.assertNotEqual(encrypted_value, sub_value)
                        self.assertIsInstance(encrypted_value, str)
                else:
                    encrypted_value = encrypted_data[key]
                    self.assertNotEqual(encrypted_value, value)
                    self.assertIsInstance(encrypted_value, str)
            
            # Test decryption
            decrypted_data = self.plaid_security.decrypt_sensitive_data(encrypted_data)
            
            # Verify decryption restores original data
            for key, value in sensitive_data.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        self.assertEqual(decrypted_data[key][sub_key], sub_value)
                else:
                    self.assertEqual(decrypted_data[key], value)
    
    def test_encryption_key_rotation_validation(self):
        """Test encryption key rotation validation"""
        # Test data
        original_token = "access-sandbox-12345678-1234-1234-1234-123456789012"
        
        # Encrypt with current key
        encrypted_token_1 = self.plaid_security.encrypt_access_token(original_token)
        
        # Rotate encryption key
        rotation_result = self.plaid_security.rotate_encryption_key()
        self.assertTrue(rotation_result['success'])
        self.assertIn('new_key_id', rotation_result)
        
        # Encrypt with new key
        encrypted_token_2 = self.plaid_security.encrypt_access_token(original_token)
        
        # Verify different encryption results
        self.assertNotEqual(encrypted_token_1, encrypted_token_2)
        
        # Verify both can be decrypted
        decrypted_1 = self.plaid_security.decrypt_access_token(encrypted_token_1)
        decrypted_2 = self.plaid_security.decrypt_access_token(encrypted_token_2)
        
        self.assertEqual(decrypted_1, original_token)
        self.assertEqual(decrypted_2, original_token)
        
        # Verify key rotation audit trail
        self.mock_audit_service.log_event.assert_called()
    
    def test_encryption_performance_validation(self):
        """Test encryption performance validation"""
        import time
        
        # Test large data encryption performance
        large_data = {
            'large_field': 'x' * 10000,  # 10KB of data
            'multiple_fields': ['field_' + str(i) + '_' + 'x' * 1000 for i in range(10)]
        }
        
        # Measure encryption time
        start_time = time.time()
        encrypted_data = self.plaid_security.encrypt_sensitive_data(large_data)
        encryption_time = time.time() - start_time
        
        # Measure decryption time
        start_time = time.time()
        decrypted_data = self.plaid_security.decrypt_sensitive_data(encrypted_data)
        decryption_time = time.time() - start_time
        
        # Verify performance is acceptable
        self.assertLess(encryption_time, 5.0)  # Less than 5 seconds
        self.assertLess(decryption_time, 5.0)  # Less than 5 seconds
        
        # Verify data integrity
        self.assertEqual(decrypted_data['large_field'], large_data['large_field'])
        self.assertEqual(decrypted_data['multiple_fields'], large_data['multiple_fields'])
    
    def test_encryption_algorithm_validation(self):
        """Test encryption algorithm validation"""
        # Test that encryption uses strong algorithms
        test_data = "sensitive_test_data"
        
        # Encrypt data
        encrypted_data = self.plaid_security.encrypt_access_token(test_data)
        
        # Verify encryption algorithm characteristics
        # Fernet uses AES-128 in CBC mode with PKCS7 padding
        self.assertTrue(encrypted_data.startswith('gAAAAA'))  # Base64 encoded
        self.assertEqual(len(encrypted_data), 108)  # Standard Fernet token length
        
        # Verify decryption works
        decrypted_data = self.plaid_security.decrypt_access_token(encrypted_data)
        self.assertEqual(decrypted_data, test_data)


class TestAccessControlVerification(unittest.TestCase):
    """Test access control verification for Plaid integrations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        
        self.plaid_security = PlaidSecurityService(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_user_permission_verification(self):
        """Test user permission verification for Plaid operations"""
        # Mock user with different permission levels
        test_users = [
            {'id': 'user_1', 'role': 'admin', 'permissions': ['plaid_read', 'plaid_write', 'plaid_admin']},
            {'id': 'user_2', 'role': 'user', 'permissions': ['plaid_read']},
            {'id': 'user_3', 'role': 'guest', 'permissions': []}
        ]
        
        for user in test_users:
            # Mock access control service
            self.mock_access_control.get_user_permissions.return_value = user['permissions']
            self.mock_access_control.has_role.return_value = user['role'] == 'admin'
            
            # Test different Plaid operations
            operations = [
                ('get_accounts', 'plaid_read'),
                ('create_link_token', 'plaid_write'),
                ('delete_connection', 'plaid_admin')
            ]
            
            for operation, required_permission in operations:
                # Test permission verification
                has_permission = self.plaid_security.verify_user_permission(
                    user['id'], 
                    operation, 
                    required_permission
                )
                
                expected_permission = required_permission in user['permissions']
                self.assertEqual(has_permission, expected_permission)
    
    def test_role_based_access_control(self):
        """Test role-based access control for Plaid features"""
        # Test different roles and their access levels
        role_tests = [
            {
                'role': 'admin',
                'allowed_operations': ['get_accounts', 'create_link_token', 'delete_connection', 'view_audit_logs'],
                'denied_operations': []
            },
            {
                'role': 'user',
                'allowed_operations': ['get_accounts', 'create_link_token'],
                'denied_operations': ['delete_connection', 'view_audit_logs']
            },
            {
                'role': 'guest',
                'allowed_operations': [],
                'denied_operations': ['get_accounts', 'create_link_token', 'delete_connection', 'view_audit_logs']
            }
        ]
        
        for role_test in role_tests:
            # Mock role
            self.mock_access_control.has_role.return_value = role_test['role'] == 'admin'
            self.mock_access_control.get_user_permissions.return_value = role_test['allowed_operations']
            
            # Test allowed operations
            for operation in role_test['allowed_operations']:
                access_granted = self.plaid_security.verify_operation_access('test_user', operation)
                self.assertTrue(access_granted, f"Role {role_test['role']} should have access to {operation}")
            
            # Test denied operations
            for operation in role_test['denied_operations']:
                access_granted = self.plaid_security.verify_operation_access('test_user', operation)
                self.assertFalse(access_granted, f"Role {role_test['role']} should not have access to {operation}")
    
    def test_resource_ownership_verification(self):
        """Test resource ownership verification"""
        # Mock user and their resources
        user_id = "test_user_123"
        user_resources = {
            'accounts': ['account_1', 'account_2'],
            'connections': ['connection_1'],
            'transactions': ['transaction_1', 'transaction_2', 'transaction_3']
        }
        
        # Mock database queries
        self.mock_db_session.query.return_value.filter.return_value.first.return_value = user_resources
        
        # Test resource ownership verification
        test_cases = [
            ('account_1', 'accounts', True),
            ('account_3', 'accounts', False),
            ('connection_1', 'connections', True),
            ('connection_2', 'connections', False),
            ('transaction_1', 'transactions', True),
            ('transaction_4', 'transactions', False)
        ]
        
        for resource_id, resource_type, expected_ownership in test_cases:
            ownership_verified = self.plaid_security.verify_resource_ownership(
                user_id, 
                resource_id, 
                resource_type
            )
            self.assertEqual(ownership_verified, expected_ownership)
    
    def test_session_validation(self):
        """Test session validation and security"""
        # Test valid session
        valid_session = {
            'user_id': 'test_user',
            'session_id': 'session_123',
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=1),
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }
        
        session_valid = self.plaid_security.validate_session(valid_session)
        self.assertTrue(session_valid)
        
        # Test expired session
        expired_session = valid_session.copy()
        expired_session['expires_at'] = datetime.utcnow() - timedelta(hours=1)
        
        session_valid = self.plaid_security.validate_session(expired_session)
        self.assertFalse(session_valid)
        
        # Test session with suspicious activity
        suspicious_session = valid_session.copy()
        suspicious_session['ip_address'] = '192.168.1.999'  # Invalid IP
        
        session_valid = self.plaid_security.validate_session(suspicious_session)
        self.assertFalse(session_valid)
    
    def test_api_rate_limiting_verification(self):
        """Test API rate limiting verification"""
        user_id = "test_user"
        
        # Test rate limiting for different operations
        operations = ['get_accounts', 'get_transactions', 'create_link_token']
        
        for operation in operations:
            # Test normal usage (should be allowed)
            for i in range(5):
                rate_limit_result = self.plaid_security.check_rate_limit(user_id, operation)
                self.assertTrue(rate_limit_result['allowed'])
            
            # Test rate limit exceeded
            rate_limit_result = self.plaid_security.check_rate_limit(user_id, operation)
            self.assertFalse(rate_limit_result['allowed'])
            self.assertIn('rate_limit', rate_limit_result['error'])
            
            # Test rate limit reset
            self.plaid_security.reset_rate_limit(user_id, operation)
            rate_limit_result = self.plaid_security.check_rate_limit(user_id, operation)
            self.assertTrue(rate_limit_result['allowed'])


class TestTokenSecurityAndRotationTesting(unittest.TestCase):
    """Test token security and rotation for Plaid integrations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        
        self.plaid_security = PlaidSecurityService(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_access_token_validation(self):
        """Test access token validation and security"""
        # Test valid tokens
        valid_tokens = [
            "access-sandbox-12345678-1234-1234-1234-123456789012",
            "access-development-87654321-4321-4321-4321-210987654321",
            "access-production-abcdef12-3456-3456-3456-12abcdef3456"
        ]
        
        for token in valid_tokens:
            validation_result = self.plaid_security.validate_access_token(token)
            self.assertTrue(validation_result['is_valid'])
            self.assertIsNone(validation_result['error'])
        
        # Test invalid tokens
        invalid_tokens = [
            "",  # Empty token
            "invalid-token",  # Invalid format
            "access-sandbox-",  # Incomplete token
            "access-sandbox-12345678-1234-1234-1234-123456789012" * 10,  # Too long
            "access-invalid-12345678-1234-1234-1234-123456789012",  # Invalid environment
            "access-sandbox-12345678-1234-1234-1234-12345678901",  # Too short
        ]
        
        for token in invalid_tokens:
            validation_result = self.plaid_security.validate_access_token(token)
            self.assertFalse(validation_result['is_valid'])
            self.assertIsNotNone(validation_result['error'])
    
    def test_token_rotation_mechanism(self):
        """Test token rotation mechanism"""
        # Test automatic token rotation
        original_token = "access-sandbox-12345678-1234-1234-1234-123456789012"
        
        # Mock token age
        token_age = timedelta(days=90)  # 90 days old
        
        # Test token rotation trigger
        rotation_needed = self.plaid_security.should_rotate_token(original_token, token_age)
        self.assertTrue(rotation_needed)
        
        # Test token rotation process
        rotation_result = self.plaid_security.rotate_access_token(original_token)
        self.assertTrue(rotation_result['success'])
        self.assertIn('new_token', rotation_result)
        self.assertNotEqual(rotation_result['new_token'], original_token)
        
        # Verify old token is invalidated
        old_token_valid = self.plaid_security.validate_access_token(original_token)
        self.assertFalse(old_token_valid['is_valid'])
        
        # Verify new token is valid
        new_token_valid = self.plaid_security.validate_access_token(rotation_result['new_token'])
        self.assertTrue(new_token_valid['is_valid'])
    
    def test_token_storage_security(self):
        """Test token storage security"""
        # Test token encryption in storage
        original_token = "access-sandbox-12345678-1234-1234-1234-123456789012"
        
        # Encrypt token for storage
        encrypted_token = self.plaid_security.encrypt_access_token(original_token)
        
        # Verify token is not stored in plain text
        self.assertNotEqual(encrypted_token, original_token)
        self.assertNotIn(original_token, encrypted_token)
        
        # Test token retrieval and decryption
        decrypted_token = self.plaid_security.decrypt_access_token(encrypted_token)
        self.assertEqual(decrypted_token, original_token)
        
        # Test token storage audit trail
        self.mock_audit_service.log_event.assert_called()
    
    def test_token_expiration_handling(self):
        """Test token expiration handling"""
        # Test token expiration detection
        expired_token = "access-sandbox-12345678-1234-1234-1234-123456789012"
        expiration_date = datetime.utcnow() - timedelta(days=1)
        
        # Test expired token detection
        is_expired = self.plaid_security.is_token_expired(expired_token, expiration_date)
        self.assertTrue(is_expired)
        
        # Test valid token
        valid_token = "access-sandbox-87654321-4321-4321-4321-210987654321"
        valid_expiration = datetime.utcnow() + timedelta(days=30)
        
        is_expired = self.plaid_security.is_token_expired(valid_token, valid_expiration)
        self.assertFalse(is_expired)
        
        # Test token refresh mechanism
        refresh_result = self.plaid_security.refresh_expired_token(expired_token)
        self.assertTrue(refresh_result['success'])
        self.assertIn('new_token', refresh_result)
    
    def test_token_compromise_detection(self):
        """Test token compromise detection"""
        # Test suspicious token usage patterns
        suspicious_patterns = [
            {
                'token': 'access-sandbox-12345678-1234-1234-1234-123456789012',
                'usage_count': 1000,  # Excessive usage
                'ip_addresses': ['192.168.1.1', '192.168.1.2', '10.0.0.1'],  # Multiple IPs
                'user_agents': ['Mozilla/5.0', 'curl/7.68.0', 'PostmanRuntime/7.28.0']  # Multiple user agents
            }
        ]
        
        for pattern in suspicious_patterns:
            compromise_detected = self.plaid_security.detect_token_compromise(
                pattern['token'],
                pattern['usage_count'],
                pattern['ip_addresses'],
                pattern['user_agents']
            )
            
            self.assertTrue(compromise_detected['is_compromised'])
            self.assertIn('suspicious_activity', compromise_detected['reasons'])
            
            # Test token revocation
            revocation_result = self.plaid_security.revoke_compromised_token(pattern['token'])
            self.assertTrue(revocation_result['success'])


class TestAPIEndpointSecurityScanning(unittest.TestCase):
    """Test API endpoint security scanning for Plaid integrations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        self.mock_plaid_security = Mock(spec=PlaidSecurityService)
        
        self.plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
    
    def test_api_authentication_headers_validation(self):
        """Test API authentication headers validation"""
        # Test required headers
        required_headers = ['PLAID-CLIENT-ID', 'PLAID-SECRET', 'Content-Type']
        
        headers = self.plaid_integration.get_authentication_headers()
        
        for header in required_headers:
            self.assertIn(header, headers)
            self.assertIsNotNone(headers[header])
            self.assertGreater(len(headers[header]), 0)
        
        # Test header format validation
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertTrue(headers['PLAID-CLIENT-ID'].startswith('client_'))
        self.assertTrue(len(headers['PLAID-SECRET']) >= 32)
    
    def test_api_endpoint_input_validation(self):
        """Test API endpoint input validation"""
        # Test valid inputs
        valid_inputs = [
            {'user_id': 'user_123', 'access_token': 'access-sandbox-12345678-1234-1234-1234-123456789012'},
            {'account_id': 'account_456', 'start_date': '2024-01-01', 'end_date': '2024-01-31'},
            {'public_token': 'public-sandbox-12345678-1234-1234-1234-123456789012'}
        ]
        
        for valid_input in valid_inputs:
            validation_result = self.plaid_integration.validate_api_input(valid_input)
            self.assertTrue(validation_result['is_valid'])
            self.assertIsNone(validation_result['error'])
        
        # Test invalid inputs
        invalid_inputs = [
            {'user_id': '', 'access_token': 'valid_token'},  # Empty user_id
            {'account_id': 'account_456', 'start_date': 'invalid_date'},  # Invalid date
            {'public_token': 'invalid_token_format'},  # Invalid token format
            {'user_id': 'user_123', 'access_token': None},  # None value
            {'user_id': 'user_123', 'access_token': 'access-sandbox-12345678-1234-1234-1234-123456789012' * 10}  # Too long
        ]
        
        for invalid_input in invalid_inputs:
            validation_result = self.plaid_integration.validate_api_input(invalid_input)
            self.assertFalse(validation_result['is_valid'])
            self.assertIsNotNone(validation_result['error'])
    
    def test_api_rate_limiting_validation(self):
        """Test API rate limiting validation"""
        # Test rate limiting for different endpoints
        endpoints = [
            '/api/plaid/create-link-token',
            '/api/plaid/exchange-public-token',
            '/api/plaid/get-accounts',
            '/api/plaid/get-transactions'
        ]
        
        for endpoint in endpoints:
            # Test normal usage
            for i in range(10):
                rate_limit_result = self.plaid_integration.check_api_rate_limit(endpoint, 'user_123')
                self.assertTrue(rate_limit_result['allowed'])
            
            # Test rate limit exceeded
            rate_limit_result = self.plaid_integration.check_api_rate_limit(endpoint, 'user_123')
            self.assertFalse(rate_limit_result['allowed'])
            self.assertIn('rate_limit', rate_limit_result['error'])
    
    def test_api_response_validation(self):
        """Test API response validation"""
        # Test valid responses
        valid_responses = [
            {
                'accounts': [{'account_id': 'test_1', 'balances': {'available': 1000.0}}],
                'item': {'item_id': 'item_1'},
                'request_id': 'req_123'
            },
            {
                'link_token': 'link-sandbox-12345678-1234-1234-1234-123456789012',
                'expiration': '2024-12-31T23:59:59Z',
                'request_id': 'req_456'
            }
        ]
        
        for response in valid_responses:
            validation_result = self.plaid_integration.validate_api_response(response)
            self.assertTrue(validation_result['is_valid'])
            self.assertIsNone(validation_result['error'])
        
        # Test invalid responses
        invalid_responses = [
            {},  # Empty response
            {'error': 'Invalid request'},  # Error response
            {'accounts': None},  # Null data
            {'accounts': [{'account_id': '', 'balances': None}]},  # Invalid data structure
        ]
        
        for response in invalid_responses:
            validation_result = self.plaid_integration.validate_api_response(response)
            self.assertFalse(validation_result['is_valid'])
            self.assertIsNotNone(validation_result['error'])
    
    def test_api_error_handling_validation(self):
        """Test API error handling validation"""
        # Test various error scenarios
        error_scenarios = [
            {
                'status_code': 400,
                'error_type': 'INVALID_REQUEST',
                'error_code': 'INVALID_ACCESS_TOKEN',
                'expected_handling': 'retry_with_new_token'
            },
            {
                'status_code': 401,
                'error_type': 'ITEM_ERROR',
                'error_code': 'ITEM_LOGIN_REQUIRED',
                'expected_handling': 'require_user_action'
            },
            {
                'status_code': 429,
                'error_type': 'RATE_LIMIT_EXCEEDED',
                'error_code': 'RATE_LIMIT_EXCEEDED',
                'expected_handling': 'retry_with_backoff'
            },
            {
                'status_code': 500,
                'error_type': 'API_ERROR',
                'error_code': 'INTERNAL_SERVER_ERROR',
                'expected_handling': 'retry_later'
            }
        ]
        
        for scenario in error_scenarios:
            error_response = {
                'error_type': scenario['error_type'],
                'error_code': scenario['error_code'],
                'error_message': 'Test error message',
                'request_id': 'req_123'
            }
            
            handling_result = self.plaid_integration.handle_api_error(
                scenario['status_code'], 
                error_response
            )
            
            self.assertEqual(handling_result['handling_strategy'], scenario['expected_handling'])
            self.assertIn('error_details', handling_result)
            self.assertIn('retry_after', handling_result)


class TestDataPrivacyComplianceTesting(unittest.TestCase):
    """Test data privacy compliance for Plaid integrations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        
        self.plaid_security = PlaidSecurityService(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_gdpr_data_portability(self):
        """Test GDPR data portability compliance"""
        user_id = "test_user_123"
        
        # Test data export
        export_result = self.plaid_security.export_user_data_gdpr(user_id)
        
        self.assertTrue(export_result['success'])
        self.assertIn('data_export', export_result)
        self.assertIn('format', export_result['data_export'])
        self.assertIn('download_url', export_result['data_export'])
        
        # Verify exported data structure
        exported_data = export_result['data_export']
        self.assertIn('user_info', exported_data)
        self.assertIn('bank_accounts', exported_data)
        self.assertIn('transactions', exported_data)
        self.assertIn('plaid_connections', exported_data)
        
        # Verify data format
        self.assertIn(exported_data['format'], ['json', 'csv', 'xml'])
    
    def test_gdpr_data_deletion(self):
        """Test GDPR data deletion compliance"""
        user_id = "test_user_123"
        
        # Test data deletion
        deletion_result = self.plaid_security.delete_user_data_gdpr(user_id)
        
        self.assertTrue(deletion_result['success'])
        self.assertEqual(deletion_result['status'], 'deleted')
        self.assertIn('deleted_data_types', deletion_result)
        self.assertIn('deletion_timestamp', deletion_result)
        
        # Verify all data types are deleted
        expected_data_types = ['user_info', 'bank_accounts', 'transactions', 'plaid_connections']
        for data_type in expected_data_types:
            self.assertIn(data_type, deletion_result['deleted_data_types'])
        
        # Verify audit trail
        self.mock_audit_service.log_event.assert_called()
    
    def test_user_consent_management(self):
        """Test user consent management"""
        user_id = "test_user_123"
        
        # Test consent granting
        consent_result = self.plaid_security.manage_user_consent(
            user_id, 
            "plaid_data_sharing", 
            True
        )
        
        self.assertTrue(consent_result['success'])
        self.assertEqual(consent_result['consent_status'], 'granted')
        self.assertIn('consent_timestamp', consent_result)
        self.assertIn('consent_id', consent_result)
        
        # Test consent withdrawal
        withdrawal_result = self.plaid_security.manage_user_consent(
            user_id, 
            "plaid_data_sharing", 
            False
        )
        
        self.assertTrue(withdrawal_result['success'])
        self.assertEqual(withdrawal_result['consent_status'], 'withdrawn')
        
        # Test consent history
        history_result = self.plaid_security.get_consent_history(user_id)
        self.assertTrue(history_result['success'])
        self.assertIn('consent_history', history_result)
        self.assertGreater(len(history_result['consent_history']), 0)
    
    def test_data_minimization_validation(self):
        """Test data minimization validation"""
        # Test that only necessary data is collected
        test_data = {
            'user_id': 'test_user_123',
            'email': 'test@example.com',
            'bank_accounts': [
                {
                    'account_id': 'acc_123',
                    'account_name': 'Checking Account',
                    'account_type': 'checking',
                    'balance': 1000.0,
                    'account_number': '****1234',  # Masked
                    'routing_number': '****5678'   # Masked
                }
            ],
            'transactions': [
                {
                    'transaction_id': 'txn_123',
                    'amount': 100.0,
                    'date': '2024-01-01',
                    'category': ['Food and Drink'],
                    'merchant_name': 'Restaurant'
                }
            ]
        }
        
        # Validate data minimization
        minimization_result = self.plaid_security.validate_data_minimization(test_data)
        
        self.assertTrue(minimization_result['is_minimized'])
        self.assertIn('data_types', minimization_result)
        self.assertIn('unnecessary_fields', minimization_result)
        
        # Verify sensitive data is properly masked
        for account in test_data['bank_accounts']:
            self.assertTrue(account['account_number'].startswith('****'))
            self.assertTrue(account['routing_number'].startswith('****'))
    
    def test_data_retention_policy_compliance(self):
        """Test data retention policy compliance"""
        user_id = "test_user_123"
        
        # Test retention policy validation
        retention_result = self.plaid_security.validate_retention_policy_compliance(user_id)
        
        self.assertTrue(retention_result['is_compliant'])
        self.assertIn('retention_policies', retention_result)
        self.assertIn('data_types', retention_result['retention_policies'])
        self.assertIn('retention_periods', retention_result['retention_policies'])
        
        # Test data cleanup for expired data
        cleanup_result = self.plaid_security.cleanup_expired_data()
        
        self.assertTrue(cleanup_result['success'])
        self.assertIn('cleaned_records', cleanup_result)
        self.assertIn('data_types_cleaned', cleanup_result)
        
        # Verify cleanup audit trail
        self.mock_audit_service.log_event.assert_called()


class TestPenetrationTestingForBankingFeatures(unittest.TestCase):
    """Test penetration testing for banking features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        self.mock_plaid_security = Mock(spec=PlaidSecurityService)
        
        self.plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        # Test malicious SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' UNION SELECT * FROM users --",
            "'; UPDATE users SET password='hacked'; --"
        ]
        
        for malicious_input in malicious_inputs:
            # Test input sanitization
            sanitized_input = self.plaid_integration.sanitize_input(malicious_input)
            
            # Verify SQL injection is prevented
            self.assertNotIn("DROP TABLE", sanitized_input)
            self.assertNotIn("INSERT INTO", sanitized_input)
            self.assertNotIn("UPDATE", sanitized_input)
            self.assertNotIn("UNION SELECT", sanitized_input)
            
            # Test database query safety
            query_safe = self.plaid_integration.is_query_safe(sanitized_input)
            self.assertTrue(query_safe)
    
    def test_xss_prevention(self):
        """Test XSS prevention"""
        # Test malicious XSS attempts
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for malicious_input in malicious_inputs:
            # Test XSS prevention
            sanitized_input = self.plaid_integration.sanitize_input(malicious_input)
            
            # Verify XSS is prevented
            self.assertNotIn("<script>", sanitized_input)
            self.assertNotIn("javascript:", sanitized_input)
            self.assertNotIn("data:text/html", sanitized_input)
            self.assertNotIn("onerror=", sanitized_input)
            self.assertNotIn("onload=", sanitized_input)
            
            # Test output encoding
            encoded_output = self.plaid_integration.encode_output(sanitized_input)
            self.assertNotIn("<script>", encoded_output)
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        # Test CSRF token validation
        valid_token = self.plaid_integration.generate_csrf_token("user_123")
        
        # Test valid token
        token_valid = self.plaid_integration.validate_csrf_token("user_123", valid_token)
        self.assertTrue(token_valid)
        
        # Test invalid token
        invalid_token = "invalid_token"
        token_valid = self.plaid_integration.validate_csrf_token("user_123", invalid_token)
        self.assertFalse(token_valid)
        
        # Test expired token
        expired_token = self.plaid_integration.generate_csrf_token("user_123")
        # Simulate token expiration
        self.plaid_integration.expire_csrf_token(expired_token)
        token_valid = self.plaid_integration.validate_csrf_token("user_123", expired_token)
        self.assertFalse(token_valid)
    
    def test_authentication_bypass_prevention(self):
        """Test authentication bypass prevention"""
        # Test various authentication bypass attempts
        bypass_attempts = [
            {'user_id': '', 'token': 'valid_token'},
            {'user_id': 'user_123', 'token': ''},
            {'user_id': 'user_123', 'token': None},
            {'user_id': 'admin', 'token': 'user_token'},
            {'user_id': 'user_123', 'token': 'expired_token'}
        ]
        
        for attempt in bypass_attempts:
            # Test authentication validation
            auth_valid = self.plaid_integration.validate_authentication(
                attempt['user_id'], 
                attempt['token']
            )
            self.assertFalse(auth_valid)
    
    def test_privilege_escalation_prevention(self):
        """Test privilege escalation prevention"""
        # Test privilege escalation attempts
        escalation_attempts = [
            {
                'user_id': 'user_123',
                'requested_role': 'admin',
                'current_role': 'user'
            },
            {
                'user_id': 'user_123',
                'requested_permission': 'plaid_admin',
                'current_permissions': ['plaid_read']
            },
            {
                'user_id': 'user_123',
                'requested_resource': 'admin_dashboard',
                'user_role': 'user'
            }
        ]
        
        for attempt in escalation_attempts:
            # Test privilege escalation prevention
            escalation_prevented = self.plaid_integration.prevent_privilege_escalation(
                attempt['user_id'],
                attempt.get('requested_role'),
                attempt.get('requested_permission'),
                attempt.get('requested_resource')
            )
            self.assertTrue(escalation_prevented)
    
    def test_session_hijacking_prevention(self):
        """Test session hijacking prevention"""
        # Test session security measures
        user_id = "user_123"
        session_id = "session_456"
        
        # Test session binding to IP
        session_bound = self.plaid_integration.bind_session_to_ip(session_id, "192.168.1.1")
        self.assertTrue(session_bound)
        
        # Test session validation with different IP
        session_valid = self.plaid_integration.validate_session_ip(session_id, "192.168.1.2")
        self.assertFalse(session_valid)
        
        # Test session binding to user agent
        agent_bound = self.plaid_integration.bind_session_to_user_agent(session_id, "Mozilla/5.0")
        self.assertTrue(agent_bound)
        
        # Test session validation with different user agent
        session_valid = self.plaid_integration.validate_session_user_agent(session_id, "curl/7.68.0")
        self.assertFalse(session_valid)
    
    def test_data_exfiltration_prevention(self):
        """Test data exfiltration prevention"""
        # Test data access monitoring
        user_id = "user_123"
        
        # Test normal data access
        normal_access = self.plaid_integration.monitor_data_access(
            user_id, 
            "get_accounts", 
            "account_123"
        )
        self.assertTrue(normal_access['allowed'])
        
        # Test suspicious data access patterns
        suspicious_patterns = [
            {'access_count': 1000, 'time_period': '1_hour'},
            {'unusual_hours': True, 'access_time': '03:00'},
            {'bulk_export': True, 'data_amount': 'large'},
            {'unusual_location': True, 'ip_address': 'foreign_ip'}
        ]
        
        for pattern in suspicious_patterns:
            access_monitored = self.plaid_integration.detect_suspicious_access(
                user_id, 
                pattern
            )
            self.assertTrue(access_monitored['suspicious'])
            self.assertIn('detection_reason', access_monitored)
    
    def test_api_abuse_prevention(self):
        """Test API abuse prevention"""
        # Test API rate limiting
        endpoint = "/api/plaid/get-accounts"
        user_id = "user_123"
        
        # Test normal API usage
        for i in range(10):
            api_allowed = self.plaid_integration.check_api_rate_limit(endpoint, user_id)
            self.assertTrue(api_allowed['allowed'])
        
        # Test rate limit exceeded
        api_allowed = self.plaid_integration.check_api_rate_limit(endpoint, user_id)
        self.assertFalse(api_allowed['allowed'])
        
        # Test API abuse detection
        abuse_detected = self.plaid_integration.detect_api_abuse(endpoint, user_id)
        self.assertTrue(abuse_detected['is_abuse'])
        self.assertIn('abuse_type', abuse_detected)
        
        # Test API blocking
        block_result = self.plaid_integration.block_abusive_user(user_id)
        self.assertTrue(block_result['blocked'])
        self.assertIn('block_duration', block_result)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2) 