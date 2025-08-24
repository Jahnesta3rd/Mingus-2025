"""
Plaid Functional Testing Suite

This module provides comprehensive functional testing for Plaid banking integrations
including bank account connection flow, transaction data retrieval and processing,
balance update accuracy validation, webhook processing reliability, error handling
and recovery testing, and multi-account management testing.
"""

import pytest
import unittest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.banking.plaid_integration import PlaidIntegration
from backend.banking.connection_flow import PlaidConnectionFlow
from backend.banking.account_manager import AccountManager
from backend.models.bank_account_models import BankAccount, PlaidConnection
from backend.models.user_models import User
from backend.security.access_control_service import AccessControlService
from backend.security.audit_logging import AuditLoggingService
from backend.security.plaid_security_service import PlaidSecurityService


class TestBankAccountConnectionFlow(unittest.TestCase):
    """Test bank account connection flow functionality"""
    
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
        
        # Initialize services
        self.plaid_integration = PlaidIntegration(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service,
            self.mock_plaid_security
        )
        
        self.connection_flow = PlaidConnectionFlow(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_complete_connection_flow_success(self):
        """Test complete successful bank account connection flow"""
        # Mock Plaid API responses
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            # Mock link token creation
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'link_token': 'test_link_token_123',
                'expiration': '2024-12-31T23:59:59Z',
                'request_id': 'test_request_id'
            }
            
            # Step 1: Create link token
            link_result = self.plaid_integration.create_link_token(self.mock_user.id)
            self.assertTrue(link_result['success'])
            self.assertEqual(link_result['data']['link_token'], 'test_link_token_123')
            
            # Mock access token exchange
            mock_post.return_value.json.return_value = {
                'access_token': 'access-sandbox-12345678-1234-1234-1234-123456789012',
                'item_id': 'test_item_id',
                'request_id': 'test_request_id'
            }
            
            # Step 2: Exchange public token for access token
            exchange_result = self.plaid_integration.exchange_public_token("test_public_token")
            self.assertTrue(exchange_result['success'])
            self.assertEqual(exchange_result['data']['access_token'], 'access-sandbox-12345678-1234-1234-1234-123456789012')
            
            # Mock account retrieval
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
                        'name': 'Test Checking Account',
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
            
            # Step 3: Retrieve accounts
            accounts_result = self.plaid_integration.get_accounts(exchange_result['data']['access_token'])
            self.assertTrue(accounts_result['success'])
            self.assertEqual(len(accounts_result['data']['accounts']), 1)
            
            # Verify database operations
            self.mock_db_session.add.assert_called()
            self.mock_db_session.commit.assert_called()
            
            # Verify audit logging
            self.mock_audit_service.log_event.assert_called()
    
    def test_connection_flow_with_multiple_accounts(self):
        """Test connection flow with multiple bank accounts"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            # Mock link token creation
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'link_token': 'test_link_token_123',
                'expiration': '2024-12-31T23:59:59Z',
                'request_id': 'test_request_id'
            }
            
            # Create link token
            link_result = self.plaid_integration.create_link_token(self.mock_user.id)
            self.assertTrue(link_result['success'])
            
            # Mock access token exchange
            mock_post.return_value.json.return_value = {
                'access_token': 'access-sandbox-12345678-1234-1234-1234-123456789012',
                'item_id': 'test_item_id',
                'request_id': 'test_request_id'
            }
            
            # Exchange public token
            exchange_result = self.plaid_integration.exchange_public_token("test_public_token")
            self.assertTrue(exchange_result['success'])
            
            # Mock multiple accounts
            mock_post.return_value.json.return_value = {
                'accounts': [
                    {
                        'account_id': 'test_checking_1',
                        'balances': {
                            'available': 1000.00,
                            'current': 1000.00,
                            'iso_currency_code': 'USD'
                        },
                        'mask': '0000',
                        'name': 'Test Checking Account',
                        'subtype': 'checking',
                        'type': 'depository'
                    },
                    {
                        'account_id': 'test_savings_1',
                        'balances': {
                            'available': 5000.00,
                            'current': 5000.00,
                            'iso_currency_code': 'USD'
                        },
                        'mask': '1111',
                        'name': 'Test Savings Account',
                        'subtype': 'savings',
                        'type': 'depository'
                    },
                    {
                        'account_id': 'test_credit_1',
                        'balances': {
                            'available': 10000.00,
                            'current': 10000.00,
                            'iso_currency_code': 'USD'
                        },
                        'mask': '2222',
                        'name': 'Test Credit Card',
                        'subtype': 'credit card',
                        'type': 'credit'
                    }
                ],
                'item': {
                    'item_id': 'test_item_id',
                    'institution_id': 'ins_3'
                },
                'request_id': 'test_request_id'
            }
            
            # Retrieve accounts
            accounts_result = self.plaid_integration.get_accounts(exchange_result['data']['access_token'])
            self.assertTrue(accounts_result['success'])
            self.assertEqual(len(accounts_result['data']['accounts']), 3)
            
            # Verify different account types
            account_types = [acc['subtype'] for acc in accounts_result['data']['accounts']]
            self.assertIn('checking', account_types)
            self.assertIn('savings', account_types)
            self.assertIn('credit card', account_types)
    
    def test_connection_flow_error_handling(self):
        """Test connection flow error handling"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            # Mock API error
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {
                'error_type': 'INVALID_REQUEST',
                'error_code': 'INVALID_PUBLIC_TOKEN',
                'error_message': 'Invalid public token',
                'request_id': 'test_request_id'
            }
            
            # Test error handling
            result = self.plaid_integration.exchange_public_token("invalid_token")
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            self.assertIn('Invalid public token', result['error'])
            
            # Verify audit logging for error
            self.mock_audit_service.log_event.assert_called()
    
    def test_connection_flow_timeout_handling(self):
        """Test connection flow timeout handling"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            # Mock timeout
            mock_post.side_effect = Exception("Request timeout")
            
            # Test timeout handling
            result = self.plaid_integration.create_link_token(self.mock_user.id)
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            
            # Verify audit logging for timeout
            self.mock_audit_service.log_event.assert_called()
    
    def test_connection_flow_validation(self):
        """Test connection flow data validation"""
        # Test invalid user ID
        result = self.plaid_integration.create_link_token("")
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
        # Test invalid public token
        result = self.plaid_integration.exchange_public_token("")
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestTransactionDataRetrievalAndProcessing(unittest.TestCase):
    """Test transaction data retrieval and processing functionality"""
    
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
    
    def test_transaction_retrieval_success(self):
        """Test successful transaction retrieval"""
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
                        'name': 'Test Checking Account',
                        'subtype': 'checking',
                        'type': 'depository'
                    }
                ],
                'total_transactions': 3,
                'transactions': [
                    {
                        'account_id': 'test_account_1',
                        'amount': 100.00,
                        'date': '2024-01-01',
                        'name': 'Test Restaurant',
                        'transaction_id': 'test_transaction_1',
                        'category': ['Food and Drink', 'Restaurants'],
                        'merchant_name': 'Test Restaurant',
                        'pending': False
                    },
                    {
                        'account_id': 'test_account_1',
                        'amount': -50.00,
                        'date': '2024-01-02',
                        'name': 'ATM Withdrawal',
                        'transaction_id': 'test_transaction_2',
                        'category': ['Transfer', 'ATM'],
                        'merchant_name': 'ATM',
                        'pending': False
                    },
                    {
                        'account_id': 'test_account_1',
                        'amount': 2000.00,
                        'date': '2024-01-03',
                        'name': 'Salary Deposit',
                        'transaction_id': 'test_transaction_3',
                        'category': ['Transfer', 'Deposit'],
                        'merchant_name': 'Employer',
                        'pending': False
                    }
                ],
                'request_id': 'test_request_id'
            }
            
            # Retrieve transactions
            result = self.plaid_integration.get_transactions(
                "test_access_token",
                "test_account_1",
                "2024-01-01",
                "2024-01-31"
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['total_transactions'], 3)
            self.assertEqual(len(result['data']['transactions']), 3)
            
            # Verify transaction processing
            transactions = result['data']['transactions']
            self.assertEqual(transactions[0]['amount'], 100.00)
            self.assertEqual(transactions[0]['category'], ['Food and Drink', 'Restaurants'])
            self.assertEqual(transactions[1]['amount'], -50.00)
            self.assertEqual(transactions[2]['amount'], 2000.00)
    
    def test_transaction_categorization_processing(self):
        """Test transaction categorization processing"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'accounts': [{'account_id': 'test_account_1'}],
                'total_transactions': 1,
                'transactions': [
                    {
                        'account_id': 'test_account_1',
                        'amount': 100.00,
                        'date': '2024-01-01',
                        'name': 'STARBUCKS',
                        'transaction_id': 'test_transaction_1',
                        'category': ['Food and Drink', 'Restaurants'],
                        'merchant_name': 'STARBUCKS',
                        'personal_finance_category': {
                            'confidence_level': 'HIGH',
                            'detailed': 'RESTAURANTS',
                            'primary': 'FOOD_AND_DRINK'
                        },
                        'pending': False
                    }
                ],
                'request_id': 'test_request_id'
            }
            
            # Retrieve and process transactions
            result = self.plaid_integration.get_transactions(
                "test_access_token",
                "test_account_1",
                "2024-01-01",
                "2024-01-31"
            )
            
            self.assertTrue(result['success'])
            transaction = result['data']['transactions'][0]
            
            # Verify categorization
            self.assertEqual(transaction['category'], ['Food and Drink', 'Restaurants'])
            self.assertEqual(transaction['personal_finance_category']['primary'], 'FOOD_AND_DRINK')
            self.assertEqual(transaction['personal_finance_category']['confidence_level'], 'HIGH')
    
    def test_transaction_data_validation(self):
        """Test transaction data validation"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'accounts': [{'account_id': 'test_account_1'}],
                'total_transactions': 1,
                'transactions': [
                    {
                        'account_id': 'test_account_1',
                        'amount': 'invalid_amount',  # Invalid amount
                        'date': 'invalid_date',     # Invalid date
                        'name': '',                 # Empty name
                        'transaction_id': 'test_transaction_1',
                        'category': ['Food and Drink', 'Restaurants'],
                        'pending': False
                    }
                ],
                'request_id': 'test_request_id'
            }
            
            # Test data validation
            result = self.plaid_integration.get_transactions(
                "test_access_token",
                "test_account_1",
                "2024-01-01",
                "2024-01-31"
            )
            
            # Should handle invalid data gracefully
            self.assertTrue(result['success'])
            # Verify validation was applied
            self.mock_audit_service.log_event.assert_called()
    
    def test_large_transaction_dataset_processing(self):
        """Test processing of large transaction datasets"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            # Generate large dataset
            large_transactions = []
            for i in range(100):
                large_transactions.append({
                    'account_id': 'test_account_1',
                    'amount': 10.00 + i,
                    'date': f'2024-01-{(i % 31) + 1:02d}',
                    'name': f'Transaction {i}',
                    'transaction_id': f'test_transaction_{i}',
                    'category': ['Food and Drink', 'Restaurants'],
                    'pending': False
                })
            
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'accounts': [{'account_id': 'test_account_1'}],
                'total_transactions': 100,
                'transactions': large_transactions,
                'request_id': 'test_request_id'
            }
            
            # Process large dataset
            start_time = time.time()
            result = self.plaid_integration.get_transactions(
                "test_access_token",
                "test_account_1",
                "2024-01-01",
                "2024-01-31"
            )
            processing_time = time.time() - start_time
            
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['total_transactions'], 100)
            self.assertEqual(len(result['data']['transactions']), 100)
            
            # Verify performance
            self.assertLess(processing_time, 5.0)  # Should process in under 5 seconds


class TestBalanceUpdateAccuracyValidation(unittest.TestCase):
    """Test balance update accuracy validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        self.mock_plaid_security = Mock(spec=PlaidSecurityService)
        
        self.account_manager = AccountManager(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_balance_update_accuracy(self):
        """Test balance update accuracy validation"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
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
                        'name': 'Test Checking Account',
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
            
            # Test balance update
            result = self.account_manager.update_account_balances("test_access_token")
            
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['updated_accounts'], 1)
            
            # Verify balance accuracy
            updated_account = result['data']['accounts'][0]
            self.assertEqual(updated_account['available_balance'], 1000.00)
            self.assertEqual(updated_account['current_balance'], 1000.00)
            self.assertEqual(updated_account['currency'], 'USD')
    
    def test_balance_discrepancy_detection(self):
        """Test balance discrepancy detection"""
        # Mock existing account with different balance
        existing_account = Mock(spec=BankAccount)
        existing_account.id = "test_account_1"
        existing_account.available_balance = 950.00  # Different from Plaid
        existing_account.current_balance = 950.00
        existing_account.currency = "USD"
        
        self.mock_db_session.query.return_value.filter.return_value.first.return_value = existing_account
        
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'accounts': [
                    {
                        'account_id': 'test_account_1',
                        'balances': {
                            'available': 1000.00,  # Different from database
                            'current': 1000.00,
                            'iso_currency_code': 'USD'
                        },
                        'mask': '0000',
                        'name': 'Test Checking Account',
                        'subtype': 'checking',
                        'type': 'depository'
                    }
                ],
                'item': {'item_id': 'test_item_id'},
                'request_id': 'test_request_id'
            }
            
            # Test discrepancy detection
            result = self.account_manager.update_account_balances("test_access_token")
            
            self.assertTrue(result['success'])
            self.assertIn('discrepancies', result['data'])
            self.assertEqual(len(result['data']['discrepancies']), 1)
            
            discrepancy = result['data']['discrepancies'][0]
            self.assertEqual(discrepancy['account_id'], 'test_account_1')
            self.assertEqual(discrepancy['old_balance'], 950.00)
            self.assertEqual(discrepancy['new_balance'], 1000.00)
            self.assertEqual(discrepancy['difference'], 50.00)
    
    def test_balance_update_with_transactions(self):
        """Test balance update with transaction reconciliation"""
        # Mock transactions
        mock_transactions = [
            {'amount': 100.00, 'date': '2024-01-01'},
            {'amount': -50.00, 'date': '2024-01-02'},
            {'amount': 2000.00, 'date': '2024-01-03'}
        ]
        
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            # Mock balance response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'accounts': [
                    {
                        'account_id': 'test_account_1',
                        'balances': {
                            'available': 2050.00,  # 1000 + 100 - 50 + 2000
                            'current': 2050.00,
                            'iso_currency_code': 'USD'
                        },
                        'mask': '0000',
                        'name': 'Test Checking Account',
                        'subtype': 'checking',
                        'type': 'depository'
                    }
                ],
                'item': {'item_id': 'test_item_id'},
                'request_id': 'test_request_id'
            }
            
            # Test balance reconciliation
            result = self.account_manager.reconcile_balance_with_transactions(
                "test_access_token",
                "test_account_1",
                mock_transactions,
                1000.00  # Starting balance
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['calculated_balance'], 2050.00)
            self.assertEqual(result['data']['plaid_balance'], 2050.00)
            self.assertTrue(result['data']['balance_matches'])
    
    def test_balance_update_error_handling(self):
        """Test balance update error handling"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            # Mock API error
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {
                'error_type': 'ITEM_ERROR',
                'error_code': 'ITEM_LOGIN_REQUIRED',
                'error_message': 'The user\'s login is required',
                'request_id': 'test_request_id'
            }
            
            # Test error handling
            result = self.account_manager.update_account_balances("invalid_token")
            
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            self.assertIn('LOGIN_REQUIRED', result['error'])
            
            # Verify audit logging
            self.mock_audit_service.log_event.assert_called()


class TestWebhookProcessingReliability(unittest.TestCase):
    """Test webhook processing reliability"""
    
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
    
    def test_transaction_webhook_processing(self):
        """Test transaction webhook processing"""
        webhook_payload = {
            'webhook_type': 'TRANSACTIONS',
            'webhook_code': 'INITIAL_UPDATE',
            'item_id': 'test_item_id',
            'new_transactions': 3,
            'removed_transactions': [],
            'modified_transactions': [],
            'initial_update_complete': True,
            'historical_update_complete': True
        }
        
        # Mock webhook signature validation
        self.mock_plaid_security.verify_webhook_signature.return_value = True
        
        # Mock transaction retrieval
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'accounts': [{'account_id': 'test_account_1'}],
                'total_transactions': 3,
                'transactions': [
                    {
                        'account_id': 'test_account_1',
                        'amount': 100.00,
                        'date': '2024-01-01',
                        'name': 'New Transaction',
                        'transaction_id': 'new_transaction_1',
                        'category': ['Food and Drink', 'Restaurants'],
                        'pending': False
                    }
                ],
                'request_id': 'test_request_id'
            }
            
            # Process webhook
            result = self.plaid_integration.process_webhook(
                json.dumps(webhook_payload),
                "test_signature"
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['webhook_type'], 'TRANSACTIONS')
            self.assertEqual(result['data']['new_transactions'], 3)
            
            # Verify signature validation was called
            self.mock_plaid_security.verify_webhook_signature.assert_called_with(
                json.dumps(webhook_payload),
                "test_signature"
            )
    
    def test_account_webhook_processing(self):
        """Test account webhook processing"""
        webhook_payload = {
            'webhook_type': 'ACCOUNTS',
            'webhook_code': 'ACCOUNT_UPDATED',
            'item_id': 'test_item_id',
            'account_ids': ['test_account_1', 'test_account_2']
        }
        
        # Mock webhook signature validation
        self.mock_plaid_security.verify_webhook_signature.return_value = True
        
        # Process webhook
        result = self.plaid_integration.process_webhook(
            json.dumps(webhook_payload),
            "test_signature"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['webhook_type'], 'ACCOUNTS')
        self.assertEqual(len(result['data']['account_ids']), 2)
    
    def test_webhook_replay_attack_prevention(self):
        """Test webhook replay attack prevention"""
        webhook_payload = {
            'webhook_type': 'TRANSACTIONS',
            'webhook_code': 'INITIAL_UPDATE',
            'item_id': 'test_item_id',
            'new_transactions': 1
        }
        
        # Mock webhook signature validation
        self.mock_plaid_security.verify_webhook_signature.return_value = True
        
        # Process webhook first time
        result1 = self.plaid_integration.process_webhook(
            json.dumps(webhook_payload),
            "test_signature"
        )
        self.assertTrue(result1['success'])
        
        # Process same webhook again (replay attack)
        result2 = self.plaid_integration.process_webhook(
            json.dumps(webhook_payload),
            "test_signature"
        )
        self.assertFalse(result2['success'])
        self.assertIn('replay', result2['error'])
    
    def test_webhook_invalid_signature_handling(self):
        """Test webhook invalid signature handling"""
        webhook_payload = {
            'webhook_type': 'TRANSACTIONS',
            'webhook_code': 'INITIAL_UPDATE',
            'item_id': 'test_item_id',
            'new_transactions': 1
        }
        
        # Mock invalid signature
        self.mock_plaid_security.verify_webhook_signature.return_value = False
        
        # Process webhook with invalid signature
        result = self.plaid_integration.process_webhook(
            json.dumps(webhook_payload),
            "invalid_signature"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('Invalid webhook signature', result['error'])
    
    def test_webhook_error_handling(self):
        """Test webhook error handling"""
        # Test invalid webhook payload
        result = self.plaid_integration.process_webhook(
            "invalid_json",
            "test_signature"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
        # Test missing webhook type
        invalid_payload = {
            'webhook_code': 'INITIAL_UPDATE',
            'item_id': 'test_item_id'
        }
        
        self.mock_plaid_security.verify_webhook_signature.return_value = True
        
        result = self.plaid_integration.process_webhook(
            json.dumps(invalid_payload),
            "test_signature"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestErrorHandlingAndRecoveryTesting(unittest.TestCase):
    """Test error handling and recovery functionality"""
    
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
    
    def test_api_error_recovery(self):
        """Test API error recovery mechanisms"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            # Mock temporary API error followed by success
            mock_post.side_effect = [
                Mock(status_code=500, json=lambda: {'error': 'Internal server error'}),
                Mock(status_code=200, json=lambda: {
                    'link_token': 'test_link_token_123',
                    'expiration': '2024-12-31T23:59:59Z',
                    'request_id': 'test_request_id'
                })
            ]
            
            # Test retry mechanism
            result = self.plaid_integration.create_link_token("test_user_id")
            
            # Should succeed after retry
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['link_token'], 'test_link_token_123')
            
            # Verify retry attempts were made
            self.assertEqual(mock_post.call_count, 2)
    
    def test_database_error_recovery(self):
        """Test database error recovery"""
        # Mock database error
        self.mock_db_session.commit.side_effect = SQLAlchemyError("Database connection error")
        
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'access_token': 'test_access_token',
                'item_id': 'test_item_id',
                'request_id': 'test_request_id'
            }
            
            # Test database error handling
            result = self.plaid_integration.exchange_public_token("test_public_token")
            
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            self.assertIn('Database', result['error'])
            
            # Verify rollback was attempted
            self.mock_db_session.rollback.assert_called()
    
    def test_network_timeout_recovery(self):
        """Test network timeout recovery"""
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            # Mock timeout
            mock_post.side_effect = Exception("Request timeout")
            
            # Test timeout handling
            result = self.plaid_integration.get_accounts("test_access_token")
            
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            self.assertIn('timeout', result['error'].lower())
    
    def test_partial_data_recovery(self):
        """Test partial data recovery"""
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
                        'name': 'Test Account',
                        'subtype': 'checking',
                        'type': 'depository'
                    },
                    {
                        'account_id': 'test_account_2',
                        'balances': None,  # Missing balance data
                        'mask': '1111',
                        'name': 'Test Account 2',
                        'subtype': 'savings',
                        'type': 'depository'
                    }
                ],
                'item': {'item_id': 'test_item_id'},
                'request_id': 'test_request_id'
            }
            
            # Test partial data handling
            result = self.plaid_integration.get_accounts("test_access_token")
            
            self.assertTrue(result['success'])
            self.assertEqual(len(result['data']['accounts']), 2)
            
            # Verify partial data was handled gracefully
            account1 = result['data']['accounts'][0]
            account2 = result['data']['accounts'][1]
            
            self.assertIsNotNone(account1['balances'])
            self.assertIsNone(account2['balances'])  # Missing data handled gracefully
    
    def test_graceful_degradation(self):
        """Test graceful degradation when services are unavailable"""
        # Mock service unavailability
        self.mock_audit_service.log_event.side_effect = Exception("Audit service unavailable")
        
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'link_token': 'test_link_token_123',
                'expiration': '2024-12-31T23:59:59Z',
                'request_id': 'test_request_id'
            }
            
            # Test graceful degradation
            result = self.plaid_integration.create_link_token("test_user_id")
            
            # Should still succeed even if audit service fails
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['link_token'], 'test_link_token_123')


class TestMultiAccountManagementTesting(unittest.TestCase):
    """Test multi-account management functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock(spec=Session)
        self.mock_access_control = Mock(spec=AccessControlService)
        self.mock_audit_service = Mock(spec=AuditLoggingService)
        self.mock_plaid_security = Mock(spec=PlaidSecurityService)
        
        self.account_manager = AccountManager(
            self.mock_db_session,
            self.mock_access_control,
            self.mock_audit_service
        )
    
    def test_multi_account_connection_management(self):
        """Test multi-account connection management"""
        # Mock multiple accounts from different institutions
        mock_accounts = [
            {
                'account_id': 'chase_checking_1',
                'balances': {'available': 1000.00, 'current': 1000.00},
                'mask': '0000',
                'name': 'Chase Checking',
                'subtype': 'checking',
                'type': 'depository',
                'institution_id': 'ins_1'
            },
            {
                'account_id': 'chase_savings_1',
                'balances': {'available': 5000.00, 'current': 5000.00},
                'mask': '1111',
                'name': 'Chase Savings',
                'subtype': 'savings',
                'type': 'depository',
                'institution_id': 'ins_1'
            },
            {
                'account_id': 'boa_checking_1',
                'balances': {'available': 2000.00, 'current': 2000.00},
                'mask': '2222',
                'name': 'Bank of America Checking',
                'subtype': 'checking',
                'type': 'depository',
                'institution_id': 'ins_2'
            }
        ]
        
        with patch('backend.banking.plaid_integration.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'accounts': mock_accounts,
                'item': {'item_id': 'test_item_id'},
                'request_id': 'test_request_id'
            }
            
            # Test multi-account management
            result = self.account_manager.manage_multiple_accounts("test_access_token", "test_user_id")
            
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['total_accounts'], 3)
            self.assertEqual(result['data']['institutions'], 2)
            
            # Verify account grouping by institution
            self.assertIn('chase_checking_1', result['data']['accounts'])
            self.assertIn('chase_savings_1', result['data']['accounts'])
            self.assertIn('boa_checking_1', result['data']['accounts'])
    
    def test_account_priority_management(self):
        """Test account priority management"""
        # Mock accounts with different priorities
        mock_accounts = [
            {
                'account_id': 'primary_checking',
                'balances': {'available': 1000.00, 'current': 1000.00},
                'mask': '0000',
                'name': 'Primary Checking',
                'subtype': 'checking',
                'type': 'depository',
                'priority': 'primary'
            },
            {
                'account_id': 'secondary_checking',
                'balances': {'available': 500.00, 'current': 500.00},
                'mask': '1111',
                'name': 'Secondary Checking',
                'subtype': 'checking',
                'type': 'depository',
                'priority': 'secondary'
            },
            {
                'account_id': 'savings_account',
                'balances': {'available': 5000.00, 'current': 5000.00},
                'mask': '2222',
                'name': 'Savings Account',
                'subtype': 'savings',
                'type': 'depository',
                'priority': 'savings'
            }
        ]
        
        # Test account priority management
        result = self.account_manager.set_account_priorities("test_user_id", mock_accounts)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['primary_account'], 'primary_checking')
        self.assertEqual(result['data']['secondary_accounts'], ['secondary_checking'])
        self.assertEqual(result['data']['savings_accounts'], ['savings_account'])
    
    def test_account_sync_coordination(self):
        """Test account sync coordination"""
        # Mock multiple accounts requiring sync
        mock_accounts = [
            {'account_id': 'account_1', 'last_sync': '2024-01-01T00:00:00Z'},
            {'account_id': 'account_2', 'last_sync': '2024-01-02T00:00:00Z'},
            {'account_id': 'account_3', 'last_sync': '2024-01-03T00:00:00Z'}
        ]
        
        # Test sync coordination
        result = self.account_manager.coordinate_account_sync("test_user_id", mock_accounts)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['accounts_to_sync'], 3)
        self.assertIn('sync_schedule', result['data'])
        self.assertIn('estimated_duration', result['data'])
    
    def test_account_error_isolation(self):
        """Test account error isolation"""
        # Mock some accounts with errors
        mock_accounts = [
            {
                'account_id': 'working_account',
                'status': 'active',
                'balances': {'available': 1000.00, 'current': 1000.00}
            },
            {
                'account_id': 'error_account',
                'status': 'error',
                'error': 'ITEM_LOGIN_REQUIRED'
            },
            {
                'account_id': 'another_working_account',
                'status': 'active',
                'balances': {'available': 2000.00, 'current': 2000.00}
            }
        ]
        
        # Test error isolation
        result = self.account_manager.handle_account_errors("test_user_id", mock_accounts)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['working_accounts'], 2)
        self.assertEqual(result['data']['error_accounts'], 1)
        self.assertEqual(result['data']['error_accounts'][0]['account_id'], 'error_account')
        
        # Verify working accounts are still accessible
        self.assertIn('working_account', result['data']['accessible_accounts'])
        self.assertIn('another_working_account', result['data']['accessible_accounts'])
    
    def test_account_data_consistency(self):
        """Test account data consistency across multiple accounts"""
        # Mock accounts with potential data inconsistencies
        mock_accounts = [
            {
                'account_id': 'account_1',
                'balances': {'available': 1000.00, 'current': 1000.00},
                'last_updated': '2024-01-01T00:00:00Z'
            },
            {
                'account_id': 'account_2',
                'balances': {'available': 2000.00, 'current': 2000.00},
                'last_updated': '2024-01-01T01:00:00Z'  # Different timestamp
            },
            {
                'account_id': 'account_3',
                'balances': {'available': 3000.00, 'current': 3000.00},
                'last_updated': '2024-01-01T00:00:00Z'
            }
        ]
        
        # Test data consistency validation
        result = self.account_manager.validate_account_consistency("test_user_id", mock_accounts)
        
        self.assertTrue(result['success'])
        self.assertIn('consistency_check', result['data'])
        self.assertIn('inconsistencies', result['data'])
        
        # Verify consistency issues are identified
        if result['data']['inconsistencies']:
            self.assertIn('account_2', [inc['account_id'] for inc in result['data']['inconsistencies']])


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2) 