"""
Financial Integration Tests
Comprehensive tests for financial API endpoints and frontend integration
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

class TestFinancialIntegration:
    """Test financial integration between frontend and backend"""
    
    def test_get_transactions_success(self, client, auth_headers, test_transactions):
        """Test successful transaction retrieval"""
        response = client.get('/api/v1/financial/transactions',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Transactions retrieved successfully'
        assert 'data' in data
        assert 'transactions' in data['data']
        assert 'pagination' in data['data']
        
        # Verify pagination structure
        pagination = data['data']['pagination']
        assert 'page' in pagination
        assert 'per_page' in pagination
        assert 'total_count' in pagination
        assert 'total_pages' in pagination
        assert pagination['page'] == 1
        assert pagination['per_page'] == 20
        assert pagination['total_count'] == 5  # 5 test transactions
        
        # Verify transactions
        transactions = data['data']['transactions']
        assert len(transactions) == 5
        assert all('id' in t for t in transactions)
        assert all('amount' in t for t in transactions)
        assert all('description' in t for t in transactions)
        assert all('category' in t for t in transactions)
    
    def test_get_transactions_with_filters(self, client, auth_headers, test_transactions):
        """Test transaction retrieval with filters"""
        # Test category filter
        response = client.get('/api/v1/financial/transactions?category=Food%20%26%20Dining',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        transactions = data['data']['transactions']
        assert all(t['category'] == 'Food & Dining' for t in transactions)
        
        # Test amount range filter
        response = client.get('/api/v1/financial/transactions?min_amount=75&max_amount=125',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        transactions = data['data']['transactions']
        assert all(75 <= t['amount'] <= 125 for t in transactions)
        
        # Test date range filter
        start_date = datetime.now().date().isoformat()
        end_date = (datetime.now() + timedelta(days=1)).date().isoformat()
        
        response = client.get(f'/api/v1/financial/transactions?start_date={start_date}&end_date={end_date}',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should return all transactions within date range
        assert len(data['data']['transactions']) > 0
    
    def test_get_transactions_pagination(self, client, auth_headers, test_transactions):
        """Test transaction pagination"""
        # Test first page
        response = client.get('/api/v1/financial/transactions?page=1&per_page=2',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        pagination = data['data']['pagination']
        assert pagination['page'] == 1
        assert pagination['per_page'] == 2
        assert pagination['total_count'] == 5
        assert pagination['total_pages'] == 3
        assert pagination['has_next'] == True
        assert pagination['has_prev'] == False
        
        transactions = data['data']['transactions']
        assert len(transactions) == 2
        
        # Test second page
        response = client.get('/api/v1/financial/transactions?page=2&per_page=2',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        pagination = data['data']['pagination']
        assert pagination['page'] == 2
        assert pagination['has_next'] == True
        assert pagination['has_prev'] == True
    
    def test_create_transaction_success(self, client, auth_headers, test_validation_schemas):
        """Test successful transaction creation"""
        transaction_data = test_validation_schemas['transaction']
        
        response = client.post('/api/v1/financial/transactions',
                             json=transaction_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Transaction created successfully'
        assert 'data' in data
        assert 'transaction' in data['data']
        
        transaction = data['data']['transaction']
        assert transaction['amount'] == transaction_data['amount']
        assert transaction['description'] == transaction_data['description']
        assert transaction['category'] == transaction_data['category']
        assert transaction['transaction_type'] == transaction_data['transaction_type']
        assert 'id' in transaction
        assert 'created_at' in transaction
    
    def test_create_transaction_validation_errors(self, client, auth_headers):
        """Test transaction creation with validation errors"""
        invalid_data = {
            'amount': -50.00,  # Negative amount
            'description': '',  # Empty description
            'category': 'A' * 101,  # Too long category
            'transaction_type': 'invalid_type'  # Invalid type
        }
        
        response = client.post('/api/v1/financial/transactions',
                             json=invalid_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'ValidationError'
        assert 'validation_errors' in data['details']
        
        # Check specific validation errors
        errors = data['details']['validation_errors']
        error_fields = [error['field'] for error in errors]
        assert 'amount' in error_fields
        assert 'description' in error_fields
        assert 'category' in error_fields
        assert 'transaction_type' in error_fields
    
    def test_get_transaction_detail_success(self, client, auth_headers, test_transactions):
        """Test successful transaction detail retrieval"""
        transaction_id = test_transactions[0].id
        
        response = client.get(f'/api/v1/financial/transactions/{transaction_id}',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Transaction retrieved successfully'
        assert 'data' in data
        assert 'transaction' in data['data']
        
        transaction = data['data']['transaction']
        assert transaction['id'] == transaction_id
        assert 'amount' in transaction
        assert 'description' in transaction
        assert 'category' in transaction
        assert 'transaction_date' in transaction
        assert 'transaction_type' in transaction
        assert 'created_at' in transaction
    
    def test_get_transaction_detail_not_found(self, client, auth_headers):
        """Test transaction detail retrieval for non-existent transaction"""
        response = client.get('/api/v1/financial/transactions/99999',
                            headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'NotFoundError'
        assert 'Transaction not found' in data['message']
    
    def test_update_transaction_success(self, client, auth_headers, test_transactions):
        """Test successful transaction update"""
        transaction_id = test_transactions[0].id
        update_data = {
            'amount': 150.75,
            'description': 'Updated transaction description',
            'category': 'Updated Category',
            'transaction_date': datetime.now().date().isoformat(),
            'transaction_type': 'income'
        }
        
        response = client.put(f'/api/v1/financial/transactions/{transaction_id}',
                            json=update_data,
                            headers=auth_headers,
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Transaction updated successfully'
        assert 'data' in data
        assert 'transaction' in data['data']
        
        transaction = data['data']['transaction']
        assert transaction['amount'] == update_data['amount']
        assert transaction['description'] == update_data['description']
        assert transaction['category'] == update_data['category']
        assert transaction['transaction_type'] == update_data['transaction_type']
        assert 'updated_at' in transaction
    
    def test_delete_transaction_success(self, client, auth_headers, test_transactions):
        """Test successful transaction deletion"""
        transaction_id = test_transactions[0].id
        
        response = client.delete(f'/api/v1/financial/transactions/{transaction_id}',
                               headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Transaction deleted successfully'
        
        # Verify transaction is deleted
        response = client.get(f'/api/v1/financial/transactions/{transaction_id}',
                            headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_budgets_success(self, client, auth_headers, test_budgets):
        """Test successful budget retrieval"""
        response = client.get('/api/v1/financial/budgets',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Budgets retrieved successfully'
        assert 'data' in data
        assert 'budgets' in data['data']
        
        budgets = data['data']['budgets']
        assert len(budgets) == 3  # 3 test budgets
        assert all('id' in b for b in budgets)
        assert all('name' in b for b in budgets)
        assert all('amount' in b for b in budgets)
        assert all('category' in b for b in budgets)
        assert all('period' in b for b in budgets)
    
    def test_create_budget_success(self, client, auth_headers, test_validation_schemas):
        """Test successful budget creation"""
        budget_data = test_validation_schemas['budget']
        
        response = client.post('/api/v1/financial/budgets',
                             json=budget_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Budget created successfully'
        assert 'data' in data
        assert 'budget' in data['data']
        
        budget = data['data']['budget']
        assert budget['name'] == budget_data['name']
        assert budget['amount'] == budget_data['amount']
        assert budget['category'] == budget_data['category']
        assert budget['period'] == budget_data['period']
        assert 'id' in budget
        assert 'created_at' in budget
    
    def test_get_accounts_success(self, client, auth_headers, test_accounts):
        """Test successful account retrieval"""
        response = client.get('/api/v1/financial/accounts',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Accounts retrieved successfully'
        assert 'data' in data
        assert 'accounts' in data['data']
        
        accounts = data['data']['accounts']
        assert len(accounts) == 3  # 3 test accounts
        assert all('id' in a for a in accounts)
        assert all('name' in a for a in accounts)
        assert all('account_type' in a for a in accounts)
        assert all('balance' in a for a in accounts)
        assert all('currency' in a for a in accounts)
    
    def test_create_account_success(self, client, auth_headers, test_validation_schemas):
        """Test successful account creation"""
        account_data = test_validation_schemas['account']
        
        response = client.post('/api/v1/financial/accounts',
                             json=account_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Account created successfully'
        assert 'data' in data
        assert 'account' in data['data']
        
        account = data['data']['account']
        assert account['name'] == account_data['name']
        assert account['account_type'] == account_data['account_type']
        assert account['balance'] == account_data['balance']
        assert account['currency'] == account_data['currency']
        assert 'id' in account
        assert 'created_at' in account
    
    def test_get_financial_summary_success(self, client, auth_headers, test_transactions, test_budgets, test_accounts):
        """Test successful financial summary retrieval"""
        response = client.get('/api/v1/financial/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Financial summary retrieved successfully'
        assert 'data' in data
        assert 'summary' in data['data']
        
        summary = data['data']['summary']
        assert 'total_income' in summary
        assert 'total_expenses' in summary
        assert 'net_income' in summary
        assert 'total_balance' in summary
        assert 'budget_status' in summary
        assert 'recent_transactions' in summary
    
    def test_get_spending_analytics_success(self, client, auth_headers, test_transactions):
        """Test successful spending analytics retrieval"""
        response = client.get('/api/v1/financial/analytics/spending',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Spending analytics retrieved successfully'
        assert 'data' in data
        assert 'analytics' in data['data']
        
        analytics = data['data']['analytics']
        assert 'spending_by_category' in analytics
        assert 'spending_trends' in analytics
        assert 'top_spending_categories' in analytics
        assert 'monthly_spending' in analytics
    
    def test_get_categories_success(self, client, auth_headers):
        """Test successful categories retrieval"""
        response = client.get('/api/v1/financial/categories',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Categories retrieved successfully'
        assert 'data' in data
        assert 'categories' in data['data']
        
        categories = data['data']['categories']
        assert len(categories) > 0
        assert all('id' in c for c in categories)
        assert all('name' in c for c in categories)
        assert all('type' in c for c in categories)
    
    def test_create_category_success(self, client, auth_headers):
        """Test successful category creation"""
        category_data = {
            'name': 'Test Category',
            'type': 'expense',
            'color': '#FF5733'
        }
        
        response = client.post('/api/v1/financial/categories',
                             json=category_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Category created successfully'
        assert 'data' in data
        assert 'category' in data['data']
        
        category = data['data']['category']
        assert category['name'] == category_data['name']
        assert category['type'] == category_data['type']
        assert category['color'] == category_data['color']
        assert 'id' in category
        assert 'created_at' in category
    
    def test_export_financial_data_success(self, client, auth_headers, test_transactions):
        """Test successful financial data export"""
        export_data = {
            'format': 'csv',
            'start_date': datetime.now().date().isoformat(),
            'end_date': (datetime.now() + timedelta(days=30)).date().isoformat(),
            'include_transactions': True
        }
        
        response = client.post('/api/v1/financial/export',
                             json=export_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Financial data exported successfully'
        assert 'data' in data
        assert 'export' in data['data']
        
        export_info = data['data']['export']
        assert 'download_url' in export_info
        assert 'file_name' in export_info
        assert 'file_size' in export_info
        assert 'format' in export_info
    
    def test_export_financial_data_invalid_format(self, client, auth_headers):
        """Test financial data export with invalid format"""
        export_data = {
            'format': 'invalid_format',
            'include_transactions': True
        }
        
        response = client.post('/api/v1/financial/export',
                             json=export_data,
                             headers=auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'ValidationError'
        assert 'validation_errors' in data['details']
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to financial endpoints"""
        # Test without authentication headers
        response = client.get('/api/v1/financial/transactions')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'UnauthorizedError'
        assert 'Authentication required' in data['message']
    
    def test_invalid_token_access(self, client):
        """Test access with invalid token"""
        response = client.get('/api/v1/financial/transactions',
                            headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert 'Invalid token' in data['message']
    
    def test_rate_limiting_on_financial_endpoints(self, client, auth_headers):
        """Test rate limiting on financial endpoints"""
        # Make multiple requests to exceed rate limit
        responses = []
        for i in range(51):  # Exceed the 50 requests per hour limit
            response = client.get('/api/v1/financial/transactions',
                                headers=auth_headers)
            responses.append(response)
        
        # The 51st request should be rate limited
        assert responses[-1].status_code == 429
        data = json.loads(responses[-1].data)
        
        assert data['success'] == False
        assert data['error'] == 'RateLimitError'
        assert 'Rate limit exceeded' in data['message']
        
        # Check rate limit headers
        assert 'X-RateLimit-Limit' in responses[-1].headers
        assert 'X-RateLimit-Remaining' in responses[-1].headers
        assert 'X-RateLimit-Reset' in responses[-1].headers
        assert 'Retry-After' in responses[-1].headers
    
    def test_transaction_amount_validation(self, client, auth_headers):
        """Test transaction amount validation"""
        invalid_amounts = [
            {'amount': -100.00},  # Negative amount
            {'amount': 0.00},     # Zero amount
            {'amount': 0.001},    # Too small amount
            {'amount': 999999999.99}  # Very large amount
        ]
        
        base_data = {
            'description': 'Test transaction',
            'category': 'Food & Dining',
            'transaction_date': datetime.now().date().isoformat(),
            'transaction_type': 'expense'
        }
        
        for invalid_amount in invalid_amounts:
            transaction_data = {**base_data, **invalid_amount}
            
            response = client.post('/api/v1/financial/transactions',
                                 json=transaction_data,
                                 headers=auth_headers,
                                 content_type='application/json')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data['success'] == False
            assert data['error'] == 'ValidationError'
            
            # Check that amount validation error is present
            errors = data['details']['validation_errors']
            amount_errors = [e for e in errors if e['field'] == 'amount']
            assert len(amount_errors) > 0
    
    def test_transaction_type_validation(self, client, auth_headers):
        """Test transaction type validation"""
        invalid_types = ['invalid_type', 'payment', 'withdrawal', 'deposit']
        
        base_data = {
            'amount': 100.00,
            'description': 'Test transaction',
            'category': 'Food & Dining',
            'transaction_date': datetime.now().date().isoformat()
        }
        
        for invalid_type in invalid_types:
            transaction_data = {**base_data, 'transaction_type': invalid_type}
            
            response = client.post('/api/v1/financial/transactions',
                                 json=transaction_data,
                                 headers=auth_headers,
                                 content_type='application/json')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data['success'] == False
            assert data['error'] == 'ValidationError'
            
            # Check that transaction_type validation error is present
            errors = data['details']['validation_errors']
            type_errors = [e for e in errors if e['field'] == 'transaction_type']
            assert len(type_errors) > 0
    
    def test_budget_period_validation(self, client, auth_headers):
        """Test budget period validation"""
        invalid_periods = ['invalid_period', 'daily', 'quarterly', 'annually']
        
        base_data = {
            'name': 'Test Budget',
            'amount': 500.00,
            'category': 'Food & Dining',
            'start_date': datetime.now().date().isoformat()
        }
        
        for invalid_period in invalid_periods:
            budget_data = {**base_data, 'period': invalid_period}
            
            response = client.post('/api/v1/financial/budgets',
                                 json=budget_data,
                                 headers=auth_headers,
                                 content_type='application/json')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data['success'] == False
            assert data['error'] == 'ValidationError'
            
            # Check that period validation error is present
            errors = data['details']['validation_errors']
            period_errors = [e for e in errors if e['field'] == 'period']
            assert len(period_errors) > 0
    
    def test_account_type_validation(self, client, auth_headers):
        """Test account type validation"""
        invalid_types = ['invalid_type', 'debit', 'investment_account', 'loan_account']
        
        base_data = {
            'name': 'Test Account',
            'balance': 1000.00,
            'currency': 'USD'
        }
        
        for invalid_type in invalid_types:
            account_data = {**base_data, 'account_type': invalid_type}
            
            response = client.post('/api/v1/financial/accounts',
                                 json=account_data,
                                 headers=auth_headers,
                                 content_type='application/json')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data['success'] == False
            assert data['error'] == 'ValidationError'
            
            # Check that account_type validation error is present
            errors = data['details']['validation_errors']
            type_errors = [e for e in errors if e['field'] == 'account_type']
            assert len(type_errors) > 0
    
    def test_currency_validation(self, client, auth_headers):
        """Test currency validation"""
        invalid_currencies = ['INVALID', 'US', 'DOLLAR', '123', '']
        
        base_data = {
            'name': 'Test Account',
            'account_type': 'checking',
            'balance': 1000.00
        }
        
        for invalid_currency in invalid_currencies:
            account_data = {**base_data, 'currency': invalid_currency}
            
            response = client.post('/api/v1/financial/accounts',
                                 json=account_data,
                                 headers=auth_headers,
                                 content_type='application/json')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data['success'] == False
            assert data['error'] == 'ValidationError'
            
            # Check that currency validation error is present
            errors = data['details']['validation_errors']
            currency_errors = [e for e in errors if e['field'] == 'currency']
            assert len(currency_errors) > 0 