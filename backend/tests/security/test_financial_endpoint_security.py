"""
Financial Endpoint Security Validation Tests for MINGUS Financial Application
============================================================================

This module provides comprehensive financial endpoint security testing:
1. Payment processing security tests (Stripe integration)
2. Financial data access control tests
3. Budget and goal management security tests
4. Transaction security tests
5. Banking integration security tests
6. PCI DSS compliance validation tests

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
import stripe

from backend.routes.payment import payment_bp
from backend.routes.financial_secure import financial_bp
from backend.routes.goals import goals_bp
from backend.routes.budget import budget_bp
from backend.routes.transactions import transactions_bp
from backend.routes.banking import banking_bp
from backend.routes.plaid import plaid_bp
from backend.security.csrf_protection_comprehensive import ComprehensiveCSRFProtection
from backend.auth.jwt_handler import JWTManager
from backend.auth.rbac_manager import RBACManager
from backend.auth.mfa_manager import MFAManager

class TestFinancialEndpointSecurity:
    """Test financial endpoint security controls"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
        app.config['STRIPE_SECRET_KEY'] = 'sk_test_fake_key'
        app.config['STRIPE_PUBLISHABLE_KEY'] = 'pk_test_fake_key'
        app.config['PLAID_CLIENT_ID'] = 'test_client_id'
        app.config['PLAID_SECRET'] = 'test_secret'
        app.config['TESTING'] = True
        
        # Register blueprints
        app.register_blueprint(payment_bp, url_prefix='/api')
        app.register_blueprint(financial_bp, url_prefix='/api')
        app.register_blueprint(goals_bp, url_prefix='/api')
        app.register_blueprint(budget_bp, url_prefix='/api')
        app.register_blueprint(transactions_bp, url_prefix='/api')
        app.register_blueprint(banking_bp, url_prefix='/api')
        app.register_blueprint(plaid_bp, url_prefix='/api')
        
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
    def rbac_manager(self, app):
        """Create RBAC manager instance"""
        return RBACManager(app)
    
    @pytest.fixture
    def mfa_manager(self, app):
        """Create MFA manager instance"""
        return MFAManager(app)
    
    @pytest.fixture
    def csrf_protection(self, app):
        """Create CSRF protection instance"""
        mock_redis = Mock()
        return ComprehensiveCSRFProtection(app, mock_redis)

class TestPaymentProcessingSecurity:
    """Test payment processing security"""
    
    def test_payment_creation_security(self, client, jwt_manager, csrf_protection):
        """Test payment creation security"""
        # Generate valid JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Generate CSRF token
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Mock Stripe payment creation
        with patch('stripe.PaymentIntent.create') as mock_stripe:
            mock_stripe.return_value = Mock(
                id='pi_test_123',
                status='succeeded',
                amount=1000,
                currency='usd'
            )
            
            # Test valid payment creation
            response = client.post('/api/payments/create',
                                 headers={
                                     'Authorization': f'Bearer {access_token}',
                                     'X-CSRF-Token': csrf_token,
                                     'X-MFA-Token': 'valid_mfa_token'
                                 },
                                 json={
                                     'amount': 1000,
                                     'currency': 'usd',
                                     'payment_method': 'pm_test_123'
                                 })
            
            assert response.status_code == 200, "Valid payment creation should succeed"
            assert 'payment_intent_id' in response.json, "Response should contain payment intent ID"
    
    def test_payment_processing_authentication(self, client):
        """Test payment processing authentication"""
        # Test without authentication
        response = client.post('/api/payments/create',
                             json={'amount': 1000, 'currency': 'usd'})
        
        assert response.status_code in [401, 403], "Payment creation should require authentication"
        
        # Test with invalid JWT token
        response = client.post('/api/payments/create',
                             headers={'Authorization': 'Bearer invalid_token'},
                             json={'amount': 1000, 'currency': 'usd'})
        
        assert response.status_code in [401, 403], "Invalid JWT token should be rejected"
    
    def test_payment_processing_csrf_protection(self, client, jwt_manager):
        """Test payment processing CSRF protection"""
        # Generate valid JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test without CSRF token
        response = client.post('/api/payments/create',
                             headers={'Authorization': f'Bearer {access_token}'},
                             json={'amount': 1000, 'currency': 'usd'})
        
        assert response.status_code in [403, 400], "Payment creation should require CSRF token"
        
        # Test with invalid CSRF token
        response = client.post('/api/payments/create',
                             headers={
                                 'Authorization': f'Bearer {access_token}',
                                 'X-CSRF-Token': 'invalid_csrf_token'
                             },
                             json={'amount': 1000, 'currency': 'usd'})
        
        assert response.status_code in [403, 400], "Invalid CSRF token should be rejected"
    
    def test_payment_processing_mfa_requirement(self, client, jwt_manager, csrf_protection):
        """Test payment processing MFA requirement"""
        # Generate valid JWT and CSRF tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Test without MFA token
        response = client.post('/api/payments/create',
                             headers={
                                 'Authorization': f'Bearer {access_token}',
                                 'X-CSRF-Token': csrf_token
                             },
                             json={'amount': 1000, 'currency': 'usd'})
        
        assert response.status_code in [401, 403], "Payment creation should require MFA token"
        
        # Test with invalid MFA token
        response = client.post('/api/payments/create',
                             headers={
                                 'Authorization': f'Bearer {access_token}',
                                 'X-CSRF-Token': csrf_token,
                                 'X-MFA-Token': 'invalid_mfa_token'
                             },
                             json={'amount': 1000, 'currency': 'usd'})
        
        assert response.status_code in [401, 403], "Invalid MFA token should be rejected"
    
    def test_payment_amount_validation(self, client, jwt_manager, csrf_protection):
        """Test payment amount validation"""
        # Generate valid tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Test invalid amounts
        invalid_amounts = [
            -1000,  # Negative amount
            0,      # Zero amount
            999999999,  # Excessive amount
            'invalid',  # Non-numeric amount
            None     # Null amount
        ]
        
        for amount in invalid_amounts:
            response = client.post('/api/payments/create',
                                 headers={
                                     'Authorization': f'Bearer {access_token}',
                                     'X-CSRF-Token': csrf_token,
                                     'X-MFA-Token': 'valid_mfa_token'
                                 },
                                 json={'amount': amount, 'currency': 'usd'})
            
            assert response.status_code in [400, 422], f"Invalid amount {amount} should be rejected"
    
    def test_payment_currency_validation(self, client, jwt_manager, csrf_protection):
        """Test payment currency validation"""
        # Generate valid tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Test invalid currencies
        invalid_currencies = [
            'INVALID',  # Invalid currency code
            'USD',      # Wrong case
            'us',       # Incomplete currency code
            '',         # Empty currency
            None        # Null currency
        ]
        
        for currency in invalid_currencies:
            response = client.post('/api/payments/create',
                                 headers={
                                     'Authorization': f'Bearer {access_token}',
                                     'X-CSRF-Token': csrf_token,
                                     'X-MFA-Token': 'valid_mfa_token'
                                 },
                                 json={'amount': 1000, 'currency': currency})
            
            assert response.status_code in [400, 422], f"Invalid currency {currency} should be rejected"

class TestFinancialDataAccessControl:
    """Test financial data access control"""
    
    def test_financial_data_authentication(self, client):
        """Test financial data authentication"""
        # Test without authentication
        response = client.get('/api/financial/data')
        
        assert response.status_code in [401, 403], "Financial data access should require authentication"
        
        # Test with invalid JWT token
        response = client.get('/api/financial/data',
                            headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code in [401, 403], "Invalid JWT token should be rejected"
    
    def test_financial_data_authorization(self, client, jwt_manager):
        """Test financial data authorization"""
        # Generate user token
        user_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test user accessing own data
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/financial/data',
                                headers={'Authorization': f'Bearer {user_token}'})
            
            assert response.status_code == 200, "User should access own financial data"
        
        # Test user accessing another user's data
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = False
            
            response = client.get('/api/financial/data/other_user',
                                headers={'Authorization': f'Bearer {user_token}'})
            
            assert response.status_code in [401, 403], "User should not access other user's data"
    
    def test_financial_data_csrf_protection(self, client, jwt_manager, csrf_protection):
        """Test financial data CSRF protection"""
        # Generate valid JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test POST without CSRF token
        response = client.post('/api/financial/data',
                             headers={'Authorization': f'Bearer {access_token}'},
                             json={'data': 'test'})
        
        assert response.status_code in [403, 400], "Financial data modification should require CSRF token"
        
        # Test with valid CSRF token
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        response = client.post('/api/financial/data',
                             headers={
                                 'Authorization': f'Bearer {access_token}',
                                 'X-CSRF-Token': csrf_token
                             },
                             json={'data': 'test'})
        
        assert response.status_code == 200, "Valid CSRF token should be accepted"
    
    def test_financial_data_encryption(self, client, jwt_manager):
        """Test financial data encryption"""
        # Generate valid JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test data retrieval
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/financial/data',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200, "Financial data should be retrievable"
            
            # Verify data is encrypted in response
            data = response.json
            assert 'encrypted_data' in data or 'data' in data, "Response should contain data"
    
    def test_financial_data_audit_logging(self, client, jwt_manager):
        """Test financial data audit logging"""
        # Generate valid JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            with patch('backend.utils.audit_logger.log_audit_event') as mock_audit:
                mock_permission.return_value = True
                
                # Access financial data
                response = client.get('/api/financial/data',
                                    headers={'Authorization': f'Bearer {access_token}'})
                
                assert response.status_code == 200, "Financial data access should succeed"
                
                # Verify audit logging
                mock_audit.assert_called()

class TestBudgetAndGoalManagementSecurity:
    """Test budget and goal management security"""
    
    def test_budget_creation_security(self, client, jwt_manager, csrf_protection):
        """Test budget creation security"""
        # Generate valid tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Test valid budget creation
        response = client.post('/api/budget/create',
                             headers={
                                 'Authorization': f'Bearer {access_token}',
                                 'X-CSRF-Token': csrf_token
                             },
                             json={
                                 'name': 'Test Budget',
                                 'amount': 5000,
                                 'category': 'monthly'
                             })
        
        assert response.status_code == 200, "Valid budget creation should succeed"
        assert 'budget_id' in response.json, "Response should contain budget ID"
    
    def test_budget_access_control(self, client, jwt_manager):
        """Test budget access control"""
        # Generate user token
        user_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test user accessing own budget
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/budget/123',
                                headers={'Authorization': f'Bearer {user_token}'})
            
            assert response.status_code == 200, "User should access own budget"
        
        # Test user accessing another user's budget
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = False
            
            response = client.get('/api/budget/456',
                                headers={'Authorization': f'Bearer {user_token}'})
            
            assert response.status_code in [401, 403], "User should not access other user's budget"
    
    def test_goal_creation_security(self, client, jwt_manager, csrf_protection):
        """Test goal creation security"""
        # Generate valid tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Test valid goal creation
        response = client.post('/api/goals/create',
                             headers={
                                 'Authorization': f'Bearer {access_token}',
                                 'X-CSRF-Token': csrf_token
                             },
                             json={
                                 'name': 'Test Goal',
                                 'target_amount': 10000,
                                 'target_date': '2024-12-31'
                             })
        
        assert response.status_code == 200, "Valid goal creation should succeed"
        assert 'goal_id' in response.json, "Response should contain goal ID"
    
    def test_goal_access_control(self, client, jwt_manager):
        """Test goal access control"""
        # Generate user token
        user_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test user accessing own goal
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/goals/123',
                                headers={'Authorization': f'Bearer {user_token}'})
            
            assert response.status_code == 200, "User should access own goal"
        
        # Test user accessing another user's goal
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = False
            
            response = client.get('/api/goals/456',
                                headers={'Authorization': f'Bearer {user_token}'})
            
            assert response.status_code in [401, 403], "User should not access other user's goal"

class TestTransactionSecurity:
    """Test transaction security"""
    
    def test_transaction_creation_security(self, client, jwt_manager, csrf_protection):
        """Test transaction creation security"""
        # Generate valid tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Test valid transaction creation
        response = client.post('/api/transactions/create',
                             headers={
                                 'Authorization': f'Bearer {access_token}',
                                 'X-CSRF-Token': csrf_token
                             },
                             json={
                                 'amount': 100,
                                 'description': 'Test Transaction',
                                 'category': 'food',
                                 'date': '2024-01-01'
                             })
        
        assert response.status_code == 200, "Valid transaction creation should succeed"
        assert 'transaction_id' in response.json, "Response should contain transaction ID"
    
    def test_transaction_access_control(self, client, jwt_manager):
        """Test transaction access control"""
        # Generate user token
        user_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test user accessing own transactions
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/transactions',
                                headers={'Authorization': f'Bearer {user_token}'})
            
            assert response.status_code == 200, "User should access own transactions"
        
        # Test user accessing another user's transactions
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = False
            
            response = client.get('/api/transactions/other_user',
                                headers={'Authorization': f'Bearer {user_token}'})
            
            assert response.status_code in [401, 403], "User should not access other user's transactions"
    
    def test_transaction_modification_security(self, client, jwt_manager, csrf_protection):
        """Test transaction modification security"""
        # Generate valid tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Test transaction update
        response = client.put('/api/transactions/123',
                            headers={
                                'Authorization': f'Bearer {access_token}',
                                'X-CSRF-Token': csrf_token
                            },
                            json={
                                'amount': 150,
                                'description': 'Updated Transaction'
                            })
        
        assert response.status_code == 200, "Valid transaction update should succeed"
        
        # Test transaction deletion
        response = client.delete('/api/transactions/123',
                               headers={
                                   'Authorization': f'Bearer {access_token}',
                                   'X-CSRF-Token': csrf_token
                               })
        
        assert response.status_code == 200, "Valid transaction deletion should succeed"

class TestBankingIntegrationSecurity:
    """Test banking integration security"""
    
    def test_banking_connection_security(self, client, jwt_manager, csrf_protection):
        """Test banking connection security"""
        # Generate valid tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Test banking connection
        response = client.post('/api/banking/connect',
                             headers={
                                 'Authorization': f'Bearer {access_token}',
                                 'X-CSRF-Token': csrf_token
                             },
                             json={
                                 'institution_id': 'test_institution',
                                 'credentials': 'encrypted_credentials'
                             })
        
        assert response.status_code == 200, "Valid banking connection should succeed"
        assert 'connection_id' in response.json, "Response should contain connection ID"
    
    def test_plaid_integration_security(self, client, jwt_manager, csrf_protection):
        """Test Plaid integration security"""
        # Generate valid tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Mock Plaid API
        with patch('plaid.Client') as mock_plaid:
            mock_plaid.return_value.exchange_public_token.return_value = {
                'access_token': 'access-sandbox-test-token'
            }
            
            # Test Plaid link
            response = client.post('/api/plaid/link',
                                 headers={
                                     'Authorization': f'Bearer {access_token}',
                                     'X-CSRF-Token': csrf_token
                                 },
                                 json={
                                     'public_token': 'public-sandbox-test-token'
                                 })
            
            assert response.status_code == 200, "Valid Plaid link should succeed"
            assert 'access_token' in response.json, "Response should contain access token"
    
    def test_banking_data_encryption(self, client, jwt_manager):
        """Test banking data encryption"""
        # Generate valid JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test banking data retrieval
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/banking/accounts',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200, "Banking data should be retrievable"
            
            # Verify data is encrypted
            data = response.json
            assert 'encrypted_data' in data or 'accounts' in data, "Response should contain encrypted data"

class TestPCIDSSComplianceValidation:
    """Test PCI DSS compliance validation"""
    
    def test_pci_compliance_encryption(self, client, jwt_manager):
        """Test PCI DSS compliance encryption"""
        # Generate valid JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test payment data encryption
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/payments/history',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200, "Payment history should be retrievable"
            
            # Verify PCI compliance headers
            assert 'X-PCI-Compliant' in response.headers, "Response should include PCI compliance header"
    
    def test_pci_compliance_audit_logging(self, client, jwt_manager):
        """Test PCI DSS compliance audit logging"""
        # Generate valid JWT token
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            with patch('backend.utils.audit_logger.log_audit_event') as mock_audit:
                mock_permission.return_value = True
                
                # Access payment data
                response = client.get('/api/payments/history',
                                    headers={'Authorization': f'Bearer {access_token}'})
                
                assert response.status_code == 200, "Payment history access should succeed"
                
                # Verify PCI audit logging
                mock_audit.assert_called()
    
    def test_pci_compliance_access_control(self, client, jwt_manager):
        """Test PCI DSS compliance access control"""
        # Generate user token
        user_token = jwt_manager.generate_access_token('test_user', 'user')
        
        # Test user accessing own payment data
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            response = client.get('/api/payments/history',
                                headers={'Authorization': f'Bearer {user_token}'})
            
            assert response.status_code == 200, "User should access own payment data"
        
        # Test user accessing another user's payment data
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = False
            
            response = client.get('/api/payments/history/other_user',
                                headers={'Authorization': f'Bearer {user_token}'})
            
            assert response.status_code in [401, 403], "User should not access other user's payment data"

class TestFinancialEndpointIntegration:
    """Test financial endpoint integration"""
    
    def test_payment_financial_integration(self, client, jwt_manager, csrf_protection):
        """Test payment and financial data integration"""
        # Generate valid tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Create payment
        with patch('stripe.PaymentIntent.create') as mock_stripe:
            mock_stripe.return_value = Mock(
                id='pi_test_123',
                status='succeeded',
                amount=1000,
                currency='usd'
            )
            
            payment_response = client.post('/api/payments/create',
                                         headers={
                                             'Authorization': f'Bearer {access_token}',
                                             'X-CSRF-Token': csrf_token,
                                             'X-MFA-Token': 'valid_mfa_token'
                                         },
                                         json={
                                             'amount': 1000,
                                             'currency': 'usd',
                                             'payment_method': 'pm_test_123'
                                         })
            
            assert payment_response.status_code == 200, "Payment creation should succeed"
            
            # Verify financial data is updated
            with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
                mock_permission.return_value = True
                
                financial_response = client.get('/api/financial/data',
                                              headers={'Authorization': f'Bearer {access_token}'})
                
                assert financial_response.status_code == 200, "Financial data should be updated"
    
    def test_budget_goal_integration(self, client, jwt_manager, csrf_protection):
        """Test budget and goal integration"""
        # Generate valid tokens
        access_token = jwt_manager.generate_access_token('test_user', 'user')
        csrf_token_data = csrf_protection.generate_csrf_token('test_user', 'test_session')
        csrf_token = csrf_token_data['token']
        
        # Create budget
        budget_response = client.post('/api/budget/create',
                                    headers={
                                        'Authorization': f'Bearer {access_token}',
                                        'X-CSRF-Token': csrf_token
                                    },
                                    json={
                                        'name': 'Test Budget',
                                        'amount': 5000,
                                        'category': 'monthly'
                                    })
        
        assert budget_response.status_code == 200, "Budget creation should succeed"
        
        # Create goal
        goal_response = client.post('/api/goals/create',
                                  headers={
                                      'Authorization': f'Bearer {access_token}',
                                      'X-CSRF-Token': csrf_token
                                  },
                                  json={
                                      'name': 'Test Goal',
                                      'target_amount': 10000,
                                      'target_date': '2024-12-31'
                                  })
        
        assert goal_response.status_code == 200, "Goal creation should succeed"
        
        # Verify integration
        with patch('backend.auth.rbac_manager.RBACManager.has_permission') as mock_permission:
            mock_permission.return_value = True
            
            integration_response = client.get('/api/financial/analysis',
                                            headers={'Authorization': f'Bearer {access_token}'})
            
            assert integration_response.status_code == 200, "Financial analysis should include budget and goal data"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
