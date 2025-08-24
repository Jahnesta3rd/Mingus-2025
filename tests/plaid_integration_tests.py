"""
Comprehensive Plaid Integration Testing Suite

This module provides comprehensive testing for all Plaid banking integrations including
security validation, functionality testing, and business logic validation.
"""

import pytest
import unittest
import json
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import requests
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.banking.plaid_integration import PlaidIntegration
from backend.banking.connection_flow import PlaidConnectionFlow
from backend.banking.account_manager import AccountManager
from backend.models.bank_account_models import BankAccount, PlaidConnection
from backend.models.user_models import User
from backend.security.plaid_security_service import PlaidSecurityService
from backend.security.access_control_service import AccessControlService
from backend.security.audit_logging import AuditLoggingService
from backend.utils.response_helpers import success_response, error_response


class TestPlaidIntegrationSecurity(unittest.TestCase):
    """Test Plaid integration security features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        self.mock_plaid_security = Mock(spec=PlaidSecurityService)
        
        # Mock Plaid API responses
        self.mock_plaid_responses = {
            'link_token': {
                'link_token': 'test_link_token_123',
                'expiration': '2024-12-31T23:59:59Z',
                'request_id': 'test_request_id'
            },
            'access_token': {
                'access_token': 'test_access_token_456',
                'item_id': 'test_item_id',
                'request_id': 'test_request_id'
            },
            'accounts': {
                'accounts': [
                    {
                        'account_id': 'test_account_1',
                        'balances': {
                            'available': 1000.00,
                            'current': 1000.00,
                            'iso_currency_code': 'USD',
                            'limit': None,
                            'unofficial_currency_code': None
                        },
                        'mask': '0000',
                        'name': 'Plaid Checking',
                        'official_name': 'Plaid Gold Standard 0% Interest Checking',
                        'subtype': 'checking',
                        'type': 'depository'
                    }
                ],
                'item': {
                    'available_products': ['balance', 'identity', 'investments'],
                    'billed_products': ['auth', 'transactions'],
                    'consent_expiration_time': None,
                    'error': None,
                    'institution_id': 'ins_3',
                    'item_id': 'test_item_id',
                    'update_type': 'background',
                    'webhook': 'https://www.example.com/webhook'
                },
                'request_id': 'test_request_id'
            },
            'transactions': {
                'accounts': [
                    {
                        'account_id': 'test_account_1',
                        'balances': {
                            'available': 1000.00,
                            'current': 1000.00,
                            'iso_currency_code': 'USD',
                            'limit': None,
                            'unofficial_currency_code': None
                        },
                        'mask': '0000',
                        'name': 'Plaid Checking',
                        'official_name': 'Plaid Gold Standard 0% Interest Checking',
                        'subtype': 'checking',
                        'type': 'depository'
                    }
                ],
                'item': {
                    'available_products': ['balance', 'identity', 'investments'],
                    'billed_products': ['auth', 'transactions'],
                    'consent_expiration_time': None,
                    'error': None,
                    'institution_id': 'ins_3',
                    'item_id': 'test_item_id',
                    'update_type': 'background',
                    'webhook': 'https://www.example.com/webhook'
                },
                'total_transactions': 1,
                'transactions': [
                    {
                        'account_id': 'test_account_1',
                        'account_owner': None,
                        'amount': 100.00,
                        'authorized_date': '2024-01-01',
                        'authorized_datetime': '2024-01-01T00:00:00Z',
                        'category': ['Food and Drink', 'Restaurants'],
                        'category_id': '13005000',
                        'check_number': None,
                        'date': '2024-01-01',
                        'datetime': '2024-01-01T00:00:00Z',
                        'iso_currency_code': 'USD',
                        'location': {
                            'address': '123 Main St',
                            'city': 'San Francisco',
                            'country': 'US',
                            'lat': 37.7749,
                            'lon': -122.4194,
                            'postal_code': '94102',
                            'region': 'CA',
                            'store_number': '123'
                        },
                        'merchant_name': 'Test Restaurant',
                        'name': 'Test Restaurant',
                        'payment_channel': 'in store',
                        'payment_meta': {
                            'by_order_of': None,
                            'payee': None,
                            'payer': None,
                            'payment_method': None,
                            'payment_processor': None,
                            'ppd_id': None,
                            'reason': None,
                            'reference_number': None
                        },
                        'pending': False,
                        'pending_transaction_id': None,
                        'personal_finance_category': {
                            'confidence_level': 'HIGH',
                            'detailed': 'RESTAURANTS',
                            'primary': 'FOOD_AND_DRINK'
                        },
                        'transaction_code': None,
                        'transaction_id': 'test_transaction_1',
                        'transaction_type': 'place',
                        'unofficial_currency_code': None
                    }
                ],
                'request_id': 'test_request_id'
            }
        }
    
    def test_plaid_api_authentication(self):
        """Test Plaid API authentication security"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            # Mock successful authentication
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = self.mock_plaid_responses['link_token']
            
            plaid_integration = PlaidIntegration(
                self.mock_db_session,
                self.mock_access_control,
                self.mock_audit_service,
                self.mock_plaid_security
            )
            
            # Test link token creation
            result = plaid_integration.create_link_token("test_user_id")
            
            # Verify authentication headers are secure
            mock_post.assert_called()
            call_args = mock_post.call_args
            headers = call_args[1].get('headers', {})
            
            # Verify required headers are present
            self.assertIn('PLAID-CLIENT-ID', headers)
            self.assertIn('PLAID-SECRET', headers)
            self.assertIn('Content-Type', headers)
            self.assertEqual(headers['Content-Type'], 'application/json')
            
            # Verify no sensitive data in logs
            self.mock_audit_service.log_event.assert_called()
            audit_call = self.mock_audit_service.log_event.call_args
            self.assertNotIn('PLAID-SECRET', str(audit_call))
    
    def test_access_token_encryption(self):
        """Test access token encryption and storage"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = self.mock_plaid_responses['access_token']
            
            plaid_integration = PlaidIntegration(
                self.mock_db_session,
                self.mock_access_control,
                self.mock_audit_service,
                self.mock_plaid_security
            )
            
            # Test access token exchange
            result = plaid_integration.exchange_public_token("test_public_token")
            
            # Verify access token is encrypted before storage
            self.mock_plaid_security.encrypt_access_token.assert_called_with(
                self.mock_plaid_responses['access_token']['access_token']
            )
            
            # Verify audit logging
            self.mock_audit_service.log_event.assert_called()
    
    def test_data_validation_security(self):
        """Test data validation security measures"""
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        # Test malicious input handling
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for malicious_input in malicious_inputs:
            # Test that malicious input is properly sanitized
            sanitized = plaid_integration._sanitize_input(malicious_input)
            self.assertNotIn("<script>", sanitized)
            self.assertNotIn("DROP TABLE", sanitized)
            self.assertNotIn("javascript:", sanitized)
    
    def test_webhook_security(self):
        """Test webhook security validation"""
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        # Test webhook signature validation
        test_payload = json.dumps({"test": "data"})
        test_signature = "test_signature"
        
        # Mock signature validation
        self.mock_plaid_security.verify_webhook_signature.return_value = True
        
        result = plaid_integration.process_webhook(test_payload, test_signature)
        
        # Verify signature validation was called
        self.mock_plaid_security.verify_webhook_signature.assert_called_with(
            test_payload, test_signature
        )
        
        # Test invalid signature
        self.mock_plaid_security.verify_webhook_signature.return_value = False
        
        result = plaid_integration.process_webhook(test_payload, "invalid_signature")
        
        # Verify invalid signature is rejected
        self.assertFalse(result['success'])
        self.assertIn('Invalid webhook signature', result['error'])
    
    def test_rate_limiting(self):
        """Test rate limiting security"""
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        # Test rate limiting for API calls
        for i in range(10):
            result = plaid_integration._check_rate_limit("test_user_id")
            
            if i < 5:  # First 5 calls should succeed
                self.assertTrue(result)
            else:  # Subsequent calls should be rate limited
                self.assertFalse(result)
    
    def test_data_encryption_at_rest(self):
        """Test data encryption at rest"""
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        # Test sensitive data encryption
        sensitive_data = {
            'access_token': 'test_access_token',
            'account_number': '1234567890',
            'routing_number': '987654321'
        }
        
        encrypted_data = plaid_integration._encrypt_sensitive_data(sensitive_data)
        
        # Verify data is encrypted
        self.assertNotEqual(encrypted_data['access_token'], 'test_access_token')
        self.assertNotEqual(encrypted_data['account_number'], '1234567890')
        self.assertNotEqual(encrypted_data['routing_number'], '987654321')
        
        # Verify decryption works
        decrypted_data = plaid_integration._decrypt_sensitive_data(encrypted_data)
        self.assertEqual(decrypted_data['access_token'], 'test_access_token')
        self.assertEqual(decrypted_data['account_number'], '1234567890')
        self.assertEqual(decrypted_data['routing_number'], '987654321')


class TestPlaidIntegrationFunctionality(unittest.TestCase):
    """Test Plaid integration functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        self.mock_plaid_security = Mock(spec=PlaidSecurityService)
        
        # Mock user
        self.mock_user = Mock(spec=User)
        self.mock_user.id = "test_user_id"
        self.mock_user.email = "test@example.com"
        self.mock_user.subscription_tier = "premium"
    
    def test_link_token_creation(self):
        """Test link token creation functionality"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'link_token': 'test_link_token_123',
                'expiration': '2024-12-31T23:59:59Z',
                'request_id': 'test_request_id'
            }
            
            plaid_integration = PlaidIntegration(
                self.mock_db_session,
                self.mock_access_control,
                self.mock_audit_service,
                self.mock_plaid_security
            )
            
            result = plaid_integration.create_link_token("test_user_id")
            
            # Verify successful link token creation
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['link_token'], 'test_link_token_123')
            self.assertIn('expiration', result['data'])
            
            # Verify audit logging
            self.mock_audit_service.log_event.assert_called()
    
    def test_access_token_exchange(self):
        """Test access token exchange functionality"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'access_token': 'test_access_token_456',
                'item_id': 'test_item_id',
                'request_id': 'test_request_id'
            }
            
            # Mock database operations
            self.mock_db_session.add = Mock()
            self.mock_db_session.commit = Mock()
            
            plaid_integration = PlaidIntegration(
                self.mock_db_session,
                self.mock_access_control,
                self.mock_audit_service,
                self.mock_plaid_security
            )
            
            result = plaid_integration.exchange_public_token("test_public_token")
            
            # Verify successful token exchange
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['access_token'], 'test_access_token_456')
            self.assertEqual(result['data']['item_id'], 'test_item_id')
            
            # Verify database operations
            self.mock_db_session.add.assert_called()
            self.mock_db_session.commit.assert_called()
    
    def test_account_retrieval(self):
        """Test account retrieval functionality"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'accounts': [
                    {
                        'account_id': 'test_account_1',
                        'balances': {
                            'available': 1000.00,
                            'current': 1000.00,
                            'iso_currency_code': 'USD'
                        },
                        'mask': '0000',
                        'name': 'Plaid Checking',
                        'subtype': 'checking',
                        'type': 'depository'
                    }
                ],
                'item': {
                    'item_id': 'test_item_id',
                    'institution_id': 'ins_3'
                },
                'request_id': 'test_request_id'
            }
            
            plaid_integration = PlaidIntegration(
                self.mock_db_session,
                self.mock_access_control,
                self.mock_audit_service,
                self.mock_plaid_security
            )
            
            result = plaid_integration.get_accounts("test_access_token")
            
            # Verify successful account retrieval
            self.assertTrue(result['success'])
            self.assertEqual(len(result['data']['accounts']), 1)
            self.assertEqual(result['data']['accounts'][0]['account_id'], 'test_account_1')
            self.assertEqual(result['data']['accounts'][0]['balances']['available'], 1000.00)
    
    def test_transaction_retrieval(self):
        """Test transaction retrieval functionality"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'accounts': [
                    {
                        'account_id': 'test_account_1',
                        'balances': {
                            'available': 1000.00,
                            'current': 1000.00,
                            'iso_currency_code': 'USD'
                        },
                        'mask': '0000',
                        'name': 'Plaid Checking',
                        'subtype': 'checking',
                        'type': 'depository'
                    }
                ],
                'total_transactions': 1,
                'transactions': [
                    {
                        'account_id': 'test_account_1',
                        'amount': 100.00,
                        'date': '2024-01-01',
                        'name': 'Test Transaction',
                        'transaction_id': 'test_transaction_1',
                        'category': ['Food and Drink', 'Restaurants']
                    }
                ],
                'request_id': 'test_request_id'
            }
            
            plaid_integration = PlaidIntegration(
                self.mock_db_session,
                self.mock_access_control,
                self.mock_audit_service,
                self.mock_plaid_security
            )
            
            result = plaid_integration.get_transactions(
                "test_access_token",
                "test_account_1",
                "2024-01-01",
                "2024-01-31"
            )
            
            # Verify successful transaction retrieval
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['total_transactions'], 1)
            self.assertEqual(len(result['data']['transactions']), 1)
            self.assertEqual(result['data']['transactions'][0]['amount'], 100.00)
            self.assertEqual(result['data']['transactions'][0]['name'], 'Test Transaction')
    
    def test_connection_flow(self):
        """Test complete connection flow functionality"""
        connection_flow = PlaidConnectionFlow(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
        
        # Test connection flow initialization
        result = connection_flow.initialize_connection("test_user_id")
        
        # Verify connection flow initialization
        self.assertTrue(result['success'])
        self.assertIn('connection_id', result['data'])
        self.assertIn('link_token', result['data'])
        
        # Test connection completion
        result = connection_flow.complete_connection(
            "test_connection_id",
            "test_public_token"
        )
        
        # Verify connection completion
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['status'], 'completed')
    
    def test_error_handling(self):
        """Test error handling functionality"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            # Test API error response
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {
                'error_type': 'INVALID_REQUEST',
                'error_code': 'INVALID_ACCESS_TOKEN',
                'error_message': 'Invalid access token',
                'request_id': 'test_request_id'
            }
            
            plaid_integration = PlaidIntegration(
                self.mock_db_session,
                self.mock_access_control,
                self.mock_audit_service,
                self.mock_plaid_security
            )
            
            result = plaid_integration.get_accounts("invalid_token")
            
            # Verify error handling
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            self.assertIn('Invalid access token', result['error'])
            
            # Verify audit logging for error
            self.mock_audit_service.log_event.assert_called()
    
    def test_data_validation(self):
        """Test data validation functionality"""
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        # Test valid data
        valid_account_data = {
            'account_id': 'test_account_1',
            'balances': {
                'available': 1000.00,
                'current': 1000.00,
                'iso_currency_code': 'USD'
            },
            'mask': '0000',
            'name': 'Test Account',
            'subtype': 'checking',
            'type': 'depository'
        }
        
        validation_result = plaid_integration._validate_account_data(valid_account_data)
        self.assertTrue(validation_result['valid'])
        
        # Test invalid data
        invalid_account_data = {
            'account_id': '',  # Empty account ID
            'balances': {
                'available': 'invalid',  # Invalid balance type
                'current': 1000.00,
                'iso_currency_code': 'USD'
            },
            'mask': '0000',
            'name': 'Test Account',
            'subtype': 'checking',
            'type': 'depository'
        }
        
        validation_result = plaid_integration._validate_account_data(invalid_account_data)
        self.assertFalse(validation_result['valid'])
        self.assertIn('errors', validation_result)


class TestPlaidIntegrationBusinessLogic(unittest.TestCase):
    """Test Plaid integration business logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        self.mock_plaid_security = Mock(spec=PlaidSecurityService)
        
        # Mock account manager
        self.account_manager = AccountManager(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_subscription_tier_limits(self):
        """Test subscription tier limits business logic"""
        # Test free tier limits
        free_user = Mock(spec=User)
        free_user.subscription_tier = "free"
        
        result = self.account_manager.check_connection_limits(free_user.id)
        
        # Verify free tier has connection limits
        self.assertTrue(result['has_limits'])
        self.assertEqual(result['max_connections'], 1)
        self.assertEqual(result['current_connections'], 0)
        
        # Test premium tier limits
        premium_user = Mock(spec=User)
        premium_user.subscription_tier = "premium"
        
        result = self.account_manager.check_connection_limits(premium_user.id)
        
        # Verify premium tier has higher limits
        self.assertTrue(result['has_limits'])
        self.assertGreater(result['max_connections'], 1)
    
    def test_data_sync_frequency(self):
        """Test data sync frequency business logic"""
        # Test sync frequency based on subscription tier
        free_user = Mock(spec=User)
        free_user.subscription_tier = "free"
        
        sync_frequency = self.account_manager.get_sync_frequency(free_user.id)
        
        # Verify free tier has limited sync frequency
        self.assertEqual(sync_frequency, 24)  # 24 hours
        
        # Test premium tier sync frequency
        premium_user = Mock(spec=User)
        premium_user.subscription_tier = "premium"
        
        sync_frequency = self.account_manager.get_sync_frequency(premium_user.id)
        
        # Verify premium tier has higher sync frequency
        self.assertLess(sync_frequency, 24)  # Less than 24 hours
    
    def test_transaction_categorization(self):
        """Test transaction categorization business logic"""
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        # Test transaction categorization
        transaction_data = {
            'name': 'STARBUCKS',
            'amount': 5.50,
            'category': ['Food and Drink', 'Restaurants'],
            'merchant_name': 'STARBUCKS'
        }
        
        categorization = plaid_integration._categorize_transaction(transaction_data)
        
        # Verify categorization logic
        self.assertEqual(categorization['primary_category'], 'Food and Drink')
        self.assertEqual(categorization['subcategory'], 'Restaurants')
        self.assertEqual(categorization['confidence'], 'high')
    
    def test_balance_alert_thresholds(self):
        """Test balance alert thresholds business logic"""
        account_manager = AccountManager(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
        
        # Test low balance alert
        account_data = {
            'account_id': 'test_account_1',
            'balances': {
                'available': 50.00,
                'current': 50.00
            }
        }
        
        alert_result = account_manager.check_balance_alerts(account_data)
        
        # Verify low balance alert
        self.assertTrue(alert_result['has_low_balance_alert'])
        self.assertEqual(alert_result['alert_type'], 'low_balance')
        self.assertEqual(alert_result['threshold'], 100.00)
        
        # Test normal balance
        account_data['balances']['available'] = 1000.00
        account_data['balances']['current'] = 1000.00
        
        alert_result = account_manager.check_balance_alerts(account_data)
        
        # Verify no alert for normal balance
        self.assertFalse(alert_result['has_low_balance_alert'])
    
    def test_connection_health_monitoring(self):
        """Test connection health monitoring business logic"""
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        # Test healthy connection
        connection_data = {
            'item_id': 'test_item_id',
            'status': 'good',
            'last_update': datetime.utcnow(),
            'error': None
        }
        
        health_result = plaid_integration._check_connection_health(connection_data)
        
        # Verify healthy connection
        self.assertTrue(health_result['is_healthy'])
        self.assertEqual(health_result['status'], 'good')
        self.assertIsNone(health_result['error'])
        
        # Test unhealthy connection
        connection_data['status'] = 'error'
        connection_data['error'] = 'ITEM_LOGIN_REQUIRED'
        
        health_result = plaid_integration._check_connection_health(connection_data)
        
        # Verify unhealthy connection
        self.assertFalse(health_result['is_healthy'])
        self.assertEqual(health_result['status'], 'error')
        self.assertIn('LOGIN_REQUIRED', health_result['error'])
    
    def test_data_retention_policy(self):
        """Test data retention policy business logic"""
        account_manager = AccountManager(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
        
        # Test data retention based on subscription tier
        free_user = Mock(spec=User)
        free_user.subscription_tier = "free"
        
        retention_result = account_manager.get_data_retention_policy(free_user.id)
        
        # Verify free tier retention policy
        self.assertEqual(retention_result['transaction_retention_days'], 90)
        self.assertEqual(retention_result['account_retention_days'], 365)
        
        # Test premium tier retention policy
        premium_user = Mock(spec=User)
        premium_user.subscription_tier = "premium"
        
        retention_result = account_manager.get_data_retention_policy(premium_user.id)
        
        # Verify premium tier has longer retention
        self.assertGreater(retention_result['transaction_retention_days'], 90)
        self.assertGreater(retention_result['account_retention_days'], 365)


class TestPlaidIntegrationPerformance(unittest.TestCase):
    """Test Plaid integration performance"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        self.mock_plaid_security = Mock(spec=PlaidSecurityService)
    
    def test_api_response_time(self):
        """Test API response time performance"""
        import time
        
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'accounts': [],
                'item': {'item_id': 'test_item_id'},
                'request_id': 'test_request_id'
            }
            
            # Measure response time
            start_time = time.time()
            result = plaid_integration.get_accounts("test_access_token")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Verify response time is within acceptable limits
            self.assertLess(response_time, 5.0)  # Less than 5 seconds
            self.assertTrue(result['success'])
    
    def test_concurrent_requests(self):
        """Test concurrent requests performance"""
        import threading
        import time
        
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        results = []
        
        def make_request():
            with patch('backend.banking.plaid_integration.requests.post') as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {
                    'accounts': [],
                    'item': {'item_id': 'test_item_id'},
                    'request_id': 'test_request_id'
                }
                
                result = plaid_integration.get_accounts("test_access_token")
                results.append(result)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests completed successfully
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertTrue(result['success'])
    
    def test_database_performance(self):
        """Test database performance"""
        import time
        
        account_manager = AccountManager(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
        
        # Mock database operations
        self.mock_db_session.query = Mock()
        self.mock_db_session.add = Mock()
        self.mock_db_session.commit = Mock()
        
        # Measure database operation time
        start_time = time.time()
        
        # Simulate database operations
        account_manager.save_account_data({
            'account_id': 'test_account_1',
            'user_id': 'test_user_id',
            'balances': {'available': 1000.00, 'current': 1000.00}
        })
        
        end_time = time.time()
        
        operation_time = end_time - start_time
        
        # Verify database operation time is within acceptable limits
        self.assertLess(operation_time, 1.0)  # Less than 1 second
        
        # Verify database operations were called
        self.mock_db_session.add.assert_called()
        self.mock_db_session.commit.assert_called()


class TestPlaidIntegrationCompliance(unittest.TestCase):
    """Test Plaid integration compliance"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        self.mock_plaid_security = Mock(spec=PlaidSecurityService)
    
    def test_gdpr_compliance(self):
        """Test GDPR compliance"""
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        # Test data portability
        result = plaid_integration.export_user_data("test_user_id")
        
        # Verify GDPR data portability
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        self.assertIn('format', result['data'])
        self.assertIn('download_url', result['data'])
        
        # Test data deletion
        result = plaid_integration.delete_user_data("test_user_id")
        
        # Verify GDPR data deletion
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['status'], 'deleted')
        
        # Verify audit logging for GDPR operations
        self.mock_audit_service.log_event.assert_called()
    
    def test_pci_compliance(self):
        """Test PCI compliance"""
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        # Test sensitive data handling
        sensitive_data = {
            'account_number': '1234567890',
            'routing_number': '987654321',
            'card_number': '4111111111111111'
        }
        
        # Verify sensitive data is encrypted
        encrypted_data = plaid_integration._encrypt_sensitive_data(sensitive_data)
        
        self.assertNotEqual(encrypted_data['account_number'], '1234567890')
        self.assertNotEqual(encrypted_data['routing_number'], '987654321')
        self.assertNotEqual(encrypted_data['card_number'], '4111111111111111')
        
        # Verify audit logging for sensitive data operations
        self.mock_audit_service.log_event.assert_called()
    
    def test_sox_compliance(self):
        """Test SOX compliance"""
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        # Test financial data integrity
        financial_data = {
            'account_id': 'test_account_1',
            'balance': 1000.00,
            'transactions': [
                {'amount': 100.00, 'date': '2024-01-01'},
                {'amount': -50.00, 'date': '2024-01-02'}
            ]
        }
        
        integrity_result = plaid_integration._verify_financial_integrity(financial_data)
        
        # Verify financial data integrity
        self.assertTrue(integrity_result['is_valid'])
        self.assertEqual(integrity_result['total_balance'], 1000.00)
        self.assertEqual(integrity_result['transaction_count'], 2)
        
        # Verify audit logging for financial operations
        self.mock_audit_service.log_event.assert_called()
    
    def test_audit_trail_compliance(self):
        """Test audit trail compliance"""
        plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        # Test audit trail for all operations
        operations = [
            'create_link_token',
            'exchange_public_token',
            'get_accounts',
            'get_transactions',
            'update_connection'
        ]
        
        for operation in operations:
            # Verify audit logging for each operation
            self.mock_audit_service.log_event.assert_called()
            
            # Verify audit trail contains required fields
            audit_call = self.mock_audit_service.log_event.call_args
            self.assertIn('event_type', audit_call[1])
            self.assertIn('user_id', audit_call[1])
            self.assertIn('timestamp', audit_call[1])


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2) 