"""
End-to-End Workflow Tests
Comprehensive tests for complete user journeys and workflows
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

class TestUserWorkflows:
    """Test complete user workflows and journeys"""
    
    def test_user_onboarding_workflow(self, client, test_workflow_data):
        """Test complete user onboarding workflow"""
        workflow_data = test_workflow_data['user_onboarding']
        
        # Step 1: User Registration
        registration_data = workflow_data['registration']
        response = client.post('/api/v1/auth/register',
                             json=registration_data,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Extract tokens for subsequent requests
        tokens = data['data']['tokens']
        user_id = data['data']['user']['id']
        auth_headers = {'Authorization': f"Bearer {tokens['access_token']}"}
        
        # Step 2: Profile Update
        profile_data = workflow_data['profile_update']
        response = client.put('/api/v1/auth/profile',
                            json=profile_data,
                            headers=auth_headers,
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['full_name'] == profile_data['full_name']
        
        # Step 3: Financial Setup - Create Account
        account_data = workflow_data['financial_setup']['account']
        response = client.post('/api/v1/financial/accounts',
                             json=account_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] == True
        account_id = data['data']['account']['id']
        
        # Step 4: Financial Setup - Create Budget
        budget_data = workflow_data['financial_setup']['budget']
        response = client.post('/api/v1/financial/budgets',
                             json=budget_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] == True
        budget_id = data['data']['budget']['id']
        
        # Step 5: Verify Financial Summary
        response = client.get('/api/v1/financial/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        summary = data['data']['summary']
        assert summary['total_balance'] == account_data['balance']
        assert len(summary['recent_transactions']) == 0  # No transactions yet
    
    def test_financial_management_workflow(self, client, test_user, auth_headers, test_workflow_data):
        """Test complete financial management workflow"""
        workflow_data = test_workflow_data['financial_management']
        
        # Step 1: Create Initial Account
        account_data = {
            'name': 'Primary Checking',
            'account_type': 'checking',
            'balance': 5000.00,
            'currency': 'USD'
        }
        
        response = client.post('/api/v1/financial/accounts',
                             json=account_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        account_id = json.loads(response.data)['data']['account']['id']
        
        # Step 2: Create Budget
        budget_data = {
            'name': 'Monthly Budget',
            'amount': 2000.00,
            'category': 'General',
            'period': 'monthly',
            'start_date': datetime.now().date().isoformat()
        }
        
        response = client.post('/api/v1/financial/budgets',
                             json=budget_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        budget_id = json.loads(response.data)['data']['budget']['id']
        
        # Step 3: Add Income Transaction
        income_data = workflow_data['transactions'][1]  # Salary deposit
        income_data['account_id'] = account_id
        
        response = client.post('/api/v1/financial/transactions',
                             json=income_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        income_id = json.loads(response.data)['data']['transaction']['id']
        
        # Step 4: Add Expense Transaction
        expense_data = workflow_data['transactions'][0]  # Grocery shopping
        expense_data['account_id'] = account_id
        
        response = client.post('/api/v1/financial/transactions',
                             json=expense_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        expense_id = json.loads(response.data)['data']['transaction']['id']
        
        # Step 5: Check Financial Summary
        response = client.get('/api/v1/financial/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        summary = data['data']['summary']
        
        # Verify calculations
        expected_balance = account_data['balance'] + income_data['amount'] - expense_data['amount']
        assert summary['total_balance'] == expected_balance
        assert summary['total_income'] == income_data['amount']
        assert summary['total_expenses'] == expense_data['amount']
        assert summary['net_income'] == income_data['amount'] - expense_data['amount']
        
        # Step 6: Check Spending Analytics
        response = client.get('/api/v1/financial/analytics/spending',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        analytics = data['data']['analytics']
        
        assert 'spending_by_category' in analytics
        assert 'spending_trends' in analytics
        assert 'top_spending_categories' in analytics
        
        # Step 7: Update Budget
        budget_adjustment = workflow_data['budget_adjustment']
        response = client.put(f'/api/v1/financial/budgets/{budget_id}',
                            json={'amount': budget_adjustment['amount']},
                            headers=auth_headers,
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['budget']['amount'] == budget_adjustment['amount']
        
        # Step 8: Export Financial Data
        export_data = {
            'format': 'csv',
            'include_transactions': True
        }
        
        response = client.post('/api/v1/financial/export',
                             json=export_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'download_url' in data['data']['export']
    
    def test_authentication_workflow(self, client, test_workflow_data):
        """Test complete authentication workflow"""
        workflow_data = test_workflow_data['user_onboarding']
        
        # Step 1: Register User
        registration_data = workflow_data['registration']
        response = client.post('/api/v1/auth/register',
                             json=registration_data,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        tokens = data['data']['tokens']
        user_id = data['data']['user']['id']
        
        # Step 2: Login with Remember Me
        login_data = {
            'email': registration_data['email'],
            'password': registration_data['password'],
            'remember_me': True
        }
        
        response = client.post('/api/v1/auth/login',
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        new_tokens = data['data']['tokens']
        
        # Verify longer expiration for remember me
        assert new_tokens['expires_in'] == 86400  # 24 hours
        
        # Step 3: Check Authentication Status
        auth_headers = {'Authorization': f"Bearer {new_tokens['access_token']}"}
        response = client.get('/api/v1/auth/check-auth',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['user_id'] == user_id
        
        # Step 4: Refresh Token
        response = client.post('/api/v1/auth/refresh',
                             headers={'Authorization': f"Bearer {new_tokens['refresh_token']}"})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        refreshed_token = data['data']['access_token']
        
        # Step 5: Use Refreshed Token
        new_auth_headers = {'Authorization': f"Bearer {refreshed_token}"}
        response = client.get('/api/v1/auth/profile',
                            headers=new_auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Step 6: Logout
        response = client.post('/api/v1/auth/logout',
                             headers=new_auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Step 7: Verify Token is Invalidated
        response = client.get('/api/v1/auth/profile',
                            headers=new_auth_headers)
        
        assert response.status_code == 401
    
    def test_password_reset_workflow(self, client, test_user):
        """Test complete password reset workflow"""
        # Step 1: Request Password Reset
        reset_data = {
            'email': test_user.email
        }
        
        with patch('backend.services.auth_service.AuthService.send_password_reset_email') as mock_send:
            mock_send.return_value = True
            
            response = client.post('/api/v1/auth/password/reset',
                                 json=reset_data,
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            
            # Verify email was sent
            mock_send.assert_called_once_with(test_user.email)
        
        # Step 2: Login with Old Password (should still work until reset)
        login_data = {
            'email': test_user.email,
            'password': 'SecurePass123!'
        }
        
        response = client.post('/api/v1/auth/login',
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        tokens = data['data']['tokens']
        auth_headers = {'Authorization': f"Bearer {tokens['access_token']}"}
        
        # Step 3: Update Password
        password_data = {
            'current_password': 'SecurePass123!',
            'new_password': 'NewSecurePass456!'
        }
        
        response = client.post('/api/v1/auth/password/update',
                             json=password_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Step 4: Verify Old Password No Longer Works
        response = client.post('/api/v1/auth/login',
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] == False
        
        # Step 5: Login with New Password
        new_login_data = {
            'email': test_user.email,
            'password': 'NewSecurePass456!'
        }
        
        response = client.post('/api/v1/auth/login',
                             json=new_login_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_transaction_management_workflow(self, client, auth_headers, test_user):
        """Test complete transaction management workflow"""
        # Step 1: Create Account
        account_data = {
            'name': 'Test Account',
            'account_type': 'checking',
            'balance': 1000.00,
            'currency': 'USD'
        }
        
        response = client.post('/api/v1/financial/accounts',
                             json=account_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        account_id = json.loads(response.data)['data']['account']['id']
        
        # Step 2: Create Multiple Transactions
        transactions = [
            {
                'amount': 50.00,
                'description': 'Grocery shopping',
                'category': 'Food & Dining',
                'transaction_date': datetime.now().date().isoformat(),
                'transaction_type': 'expense',
                'account_id': account_id
            },
            {
                'amount': 2000.00,
                'description': 'Salary deposit',
                'category': 'Income',
                'transaction_date': datetime.now().date().isoformat(),
                'transaction_type': 'income',
                'account_id': account_id
            },
            {
                'amount': 25.00,
                'description': 'Gas station',
                'category': 'Transportation',
                'transaction_date': datetime.now().date().isoformat(),
                'transaction_type': 'expense',
                'account_id': account_id
            }
        ]
        
        transaction_ids = []
        for transaction in transactions:
            response = client.post('/api/v1/financial/transactions',
                                 json=transaction,
                                 headers=auth_headers,
                                 content_type='application/json')
            
            assert response.status_code == 201
            transaction_ids.append(json.loads(response.data)['data']['transaction']['id'])
        
        # Step 3: Get All Transactions
        response = client.get('/api/v1/financial/transactions',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']['transactions']) == 3
        
        # Step 4: Filter Transactions
        response = client.get('/api/v1/financial/transactions?transaction_type=expense',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        expense_transactions = data['data']['transactions']
        assert all(t['transaction_type'] == 'expense' for t in expense_transactions)
        assert len(expense_transactions) == 2
        
        # Step 5: Update Transaction
        update_data = {
            'amount': 75.00,
            'description': 'Updated grocery shopping',
            'category': 'Food & Dining',
            'transaction_date': datetime.now().date().isoformat(),
            'transaction_type': 'expense'
        }
        
        response = client.put(f'/api/v1/financial/transactions/{transaction_ids[0]}',
                            json=update_data,
                            headers=auth_headers,
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['transaction']['amount'] == update_data['amount']
        assert data['data']['transaction']['description'] == update_data['description']
        
        # Step 6: Delete Transaction
        response = client.delete(f'/api/v1/financial/transactions/{transaction_ids[2]}',
                               headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Step 7: Verify Transaction is Deleted
        response = client.get(f'/api/v1/financial/transactions/{transaction_ids[2]}',
                            headers=auth_headers)
        
        assert response.status_code == 404
        
        # Step 8: Check Updated Summary
        response = client.get('/api/v1/financial/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        summary = data['data']['summary']
        
        # Should have 2 transactions now (1 income, 1 expense)
        assert summary['total_income'] == 2000.00
        assert summary['total_expenses'] == 75.00  # Updated amount
        assert summary['net_income'] == 1925.00
    
    def test_budget_tracking_workflow(self, client, auth_headers, test_user):
        """Test complete budget tracking workflow"""
        # Step 1: Create Multiple Budgets
        budgets = [
            {
                'name': 'Food Budget',
                'amount': 500.00,
                'category': 'Food & Dining',
                'period': 'monthly',
                'start_date': datetime.now().date().isoformat()
            },
            {
                'name': 'Transportation Budget',
                'amount': 200.00,
                'category': 'Transportation',
                'period': 'monthly',
                'start_date': datetime.now().date().isoformat()
            },
            {
                'name': 'Entertainment Budget',
                'amount': 300.00,
                'category': 'Entertainment',
                'period': 'monthly',
                'start_date': datetime.now().date().isoformat()
            }
        ]
        
        budget_ids = []
        for budget in budgets:
            response = client.post('/api/v1/financial/budgets',
                                 json=budget,
                                 headers=auth_headers,
                                 content_type='application/json')
            
            assert response.status_code == 201
            budget_ids.append(json.loads(response.data)['data']['budget']['id'])
        
        # Step 2: Create Account
        account_data = {
            'name': 'Budget Account',
            'account_type': 'checking',
            'balance': 2000.00,
            'currency': 'USD'
        }
        
        response = client.post('/api/v1/financial/accounts',
                             json=account_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        account_id = json.loads(response.data)['data']['account']['id']
        
        # Step 3: Add Transactions to Track Budgets
        transactions = [
            {
                'amount': 100.00,
                'description': 'Grocery shopping',
                'category': 'Food & Dining',
                'transaction_date': datetime.now().date().isoformat(),
                'transaction_type': 'expense',
                'account_id': account_id
            },
            {
                'amount': 50.00,
                'description': 'Gas station',
                'category': 'Transportation',
                'transaction_date': datetime.now().date().isoformat(),
                'transaction_type': 'expense',
                'account_id': account_id
            },
            {
                'amount': 75.00,
                'description': 'Movie tickets',
                'category': 'Entertainment',
                'transaction_date': datetime.now().date().isoformat(),
                'transaction_type': 'expense',
                'account_id': account_id
            }
        ]
        
        for transaction in transactions:
            response = client.post('/api/v1/financial/transactions',
                                 json=transaction,
                                 headers=auth_headers,
                                 content_type='application/json')
            
            assert response.status_code == 201
        
        # Step 4: Check Budget Status in Summary
        response = client.get('/api/v1/financial/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        summary = data['data']['summary']
        
        assert 'budget_status' in summary
        budget_status = summary['budget_status']
        
        # Verify budget tracking
        assert len(budget_status) == 3
        for status in budget_status:
            assert 'category' in status
            assert 'budget_amount' in status
            assert 'spent_amount' in status
            assert 'remaining_amount' in status
            assert 'percentage_used' in status
        
        # Step 5: Update Budget
        response = client.put(f'/api/v1/financial/budgets/{budget_ids[0]}',
                            json={'amount': 600.00},
                            headers=auth_headers,
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['budget']['amount'] == 600.00
        
        # Step 6: Check Updated Budget Status
        response = client.get('/api/v1/financial/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        summary = data['data']['summary']
        
        # Find the updated budget status
        food_budget_status = next(
            (status for status in summary['budget_status'] 
             if status['category'] == 'Food & Dining'), None
        )
        
        assert food_budget_status is not None
        assert food_budget_status['budget_amount'] == 600.00
        assert food_budget_status['spent_amount'] == 100.00
        assert food_budget_status['remaining_amount'] == 500.00
    
    def test_error_handling_workflow(self, client, auth_headers):
        """Test error handling in workflows"""
        # Test invalid transaction creation
        invalid_transaction = {
            'amount': -100.00,  # Invalid negative amount
            'description': '',  # Empty description
            'category': 'A' * 101,  # Too long category
            'transaction_type': 'invalid_type'  # Invalid type
        }
        
        response = client.post('/api/v1/financial/transactions',
                             json=invalid_transaction,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert data['error'] == 'ValidationError'
        assert len(data['details']['validation_errors']) == 4
        
        # Test accessing non-existent resource
        response = client.get('/api/v1/financial/transactions/99999',
                            headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
        assert data['error'] == 'NotFoundError'
        
        # Test unauthorized access
        response = client.get('/api/v1/financial/transactions')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] == False
        assert data['error'] == 'UnauthorizedError'
        
        # Test rate limiting
        responses = []
        for i in range(51):  # Exceed rate limit
            response = client.get('/api/v1/financial/transactions',
                                headers=auth_headers)
            responses.append(response)
        
        assert responses[-1].status_code == 429
        data = json.loads(responses[-1].data)
        assert data['success'] == False
        assert data['error'] == 'RateLimitError'
    
    def test_data_consistency_workflow(self, client, auth_headers, test_user):
        """Test data consistency across workflow operations"""
        # Step 1: Create initial state
        account_data = {
            'name': 'Consistency Test Account',
            'account_type': 'checking',
            'balance': 1000.00,
            'currency': 'USD'
        }
        
        response = client.post('/api/v1/financial/accounts',
                             json=account_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        account_id = json.loads(response.data)['data']['account']['id']
        
        # Step 2: Add transaction
        transaction_data = {
            'amount': 100.00,
            'description': 'Test transaction',
            'category': 'Test Category',
            'transaction_date': datetime.now().date().isoformat(),
            'transaction_type': 'expense',
            'account_id': account_id
        }
        
        response = client.post('/api/v1/financial/transactions',
                             json=transaction_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        transaction_id = json.loads(response.data)['data']['transaction']['id']
        
        # Step 3: Verify data consistency across endpoints
        # Check transaction list
        response = client.get('/api/v1/financial/transactions',
                            headers=auth_headers)
        
        assert response.status_code == 200
        transactions = json.loads(response.data)['data']['transactions']
        assert len(transactions) == 1
        assert transactions[0]['amount'] == transaction_data['amount']
        
        # Check transaction detail
        response = client.get(f'/api/v1/financial/transactions/{transaction_id}',
                            headers=auth_headers)
        
        assert response.status_code == 200
        transaction = json.loads(response.data)['data']['transaction']
        assert transaction['amount'] == transaction_data['amount']
        assert transaction['description'] == transaction_data['description']
        
        # Check financial summary
        response = client.get('/api/v1/financial/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        summary = json.loads(response.data)['data']['summary']
        assert summary['total_expenses'] == transaction_data['amount']
        assert summary['net_income'] == -transaction_data['amount']
        
        # Step 4: Update transaction and verify consistency
        update_data = {
            'amount': 150.00,
            'description': 'Updated test transaction',
            'category': 'Updated Category',
            'transaction_date': datetime.now().date().isoformat(),
            'transaction_type': 'expense'
        }
        
        response = client.put(f'/api/v1/financial/transactions/{transaction_id}',
                            json=update_data,
                            headers=auth_headers,
                            content_type='application/json')
        
        assert response.status_code == 200
        
        # Verify consistency after update
        response = client.get('/api/v1/financial/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        summary = json.loads(response.data)['data']['summary']
        assert summary['total_expenses'] == update_data['amount']
        assert summary['net_income'] == -update_data['amount']
        
        # Step 5: Delete transaction and verify consistency
        response = client.delete(f'/api/v1/financial/transactions/{transaction_id}',
                               headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify consistency after deletion
        response = client.get('/api/v1/financial/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        summary = json.loads(response.data)['data']['summary']
        assert summary['total_expenses'] == 0
        assert summary['net_income'] == 0 