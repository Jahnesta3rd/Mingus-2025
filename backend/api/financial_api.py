"""
Financial API
Comprehensive financial data management endpoints with security and validation
"""

from flask import Blueprint, request, jsonify, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional

from ..middleware.rate_limiter import rate_limit
from ..middleware.validation import validate_request, get_common_schema
from ..services.financial_service import FinancialService
from ..utils.response_utils import api_response, error_response
from ..utils.security_utils import require_financial_access
from ..security.financial_csrf_protection import require_financial_csrf

logger = logging.getLogger(__name__)

financial_bp = Blueprint('financial', __name__, url_prefix='/api/v1/financial')

# Validation schemas
TRANSACTION_SCHEMA = {
    'amount': {
        'type': 'float',
        'required': True,
        'min_value': 0.01
    },
    'description': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 255
    },
    'category': {
        'type': 'string',
        'required': True,
        'max_length': 100
    },
    'transaction_date': {
        'type': 'date',
        'required': True
    },
    'transaction_type': {
        'type': 'enum',
        'values': ['income', 'expense', 'transfer'],
        'required': True
    },
    'account_id': {
        'type': 'integer',
        'required': False,
        'min_value': 1
    }
}

BUDGET_SCHEMA = {
    'name': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 100
    },
    'amount': {
        'type': 'float',
        'required': True,
        'min_value': 0.01
    },
    'category': {
        'type': 'string',
        'required': True,
        'max_length': 100
    },
    'period': {
        'type': 'enum',
        'values': ['monthly', 'weekly', 'yearly'],
        'required': True
    },
    'start_date': {
        'type': 'date',
        'required': True
    }
}

ACCOUNT_SCHEMA = {
    'name': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 100
    },
    'account_type': {
        'type': 'enum',
        'values': ['checking', 'savings', 'credit', 'investment', 'loan'],
        'required': True
    },
    'balance': {
        'type': 'float',
        'required': True
    },
    'currency': {
        'type': 'string',
        'required': True,
        'max_length': 3
    }
}

@financial_bp.route('/transactions', methods=['GET'])
@jwt_required()
@require_financial_access
@rate_limit('financial', max_requests=50, window=3600)
def get_transactions():
    """
    Get user transactions with filtering and pagination
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - start_date: Filter from date (ISO format)
    - end_date: Filter to date (ISO format)
    - category: Filter by category
    - transaction_type: Filter by type (income/expense/transfer)
    - min_amount: Minimum amount filter
    - max_amount: Maximum amount filter
    """
    try:
        current_user_id = get_jwt_identity()
        financial_service = FinancialService()
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        transaction_type = request.args.get('transaction_type')
        min_amount = request.args.get('min_amount')
        max_amount = request.args.get('max_amount')
        
        # Get transactions
        transactions, total_count = financial_service.get_user_transactions(
            user_id=current_user_id,
            page=page,
            per_page=per_page,
            start_date=start_date,
            end_date=end_date,
            category=category,
            transaction_type=transaction_type,
            min_amount=min_amount,
            max_amount=max_amount
        )
        
        return api_response(
            'Transactions retrieved successfully',
            {
                'transactions': transactions,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Get transactions error: {str(e)}")
        return error_response('Failed to retrieve transactions', str(e), 500)

@financial_bp.route('/transactions', methods=['POST'])
@jwt_required()
@require_financial_access
@require_financial_csrf
@rate_limit('financial', max_requests=20, window=3600)
@validate_request(TRANSACTION_SCHEMA)
def create_transaction():
    """
    Create a new transaction
    """
    try:
        current_user_id = get_jwt_identity()
        data = g.validated_data
        financial_service = FinancialService()
        
        # Create transaction
        transaction = financial_service.create_transaction(
            user_id=current_user_id,
            amount=data['amount'],
            description=data['description'],
            category=data['category'],
            transaction_date=data['transaction_date'],
            transaction_type=data['transaction_type'],
            account_id=data.get('account_id')
        )
        
        logger.info(f"Transaction created: {transaction.id} for user {current_user_id}")
        
        return api_response(
            'Transaction created successfully',
            {
                'transaction': {
                    'id': transaction.id,
                    'amount': transaction.amount,
                    'description': transaction.description,
                    'category': transaction.category,
                    'transaction_date': transaction.transaction_date.isoformat(),
                    'transaction_type': transaction.transaction_type,
                    'created_at': transaction.created_at.isoformat()
                }
            },
            201
        )
        
    except Exception as e:
        logger.error(f"Create transaction error: {str(e)}")
        return error_response('Failed to create transaction', str(e), 500)

@financial_bp.route('/transactions/<int:transaction_id>', methods=['GET'])
@jwt_required()
@require_financial_access
@rate_limit('financial', max_requests=50, window=3600)
def get_transaction(transaction_id: int):
    """
    Get a specific transaction
    """
    try:
        current_user_id = get_jwt_identity()
        financial_service = FinancialService()
        
        transaction = financial_service.get_transaction(
            transaction_id=transaction_id,
            user_id=current_user_id
        )
        
        if not transaction:
            return error_response('Transaction not found', 'Transaction not found or access denied', 404)
        
        return api_response(
            'Transaction retrieved successfully',
            {
                'transaction': {
                    'id': transaction.id,
                    'amount': transaction.amount,
                    'description': transaction.description,
                    'category': transaction.category,
                    'transaction_date': transaction.transaction_date.isoformat(),
                    'transaction_type': transaction.transaction_type,
                    'account_id': transaction.account_id,
                    'created_at': transaction.created_at.isoformat(),
                    'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Get transaction error: {str(e)}")
        return error_response('Failed to retrieve transaction', str(e), 500)

@financial_bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
@jwt_required()
@require_financial_access
@require_financial_csrf
@rate_limit('financial', max_requests=20, window=3600)
@validate_request(TRANSACTION_SCHEMA)
def update_transaction(transaction_id: int):
    """
    Update a transaction
    """
    try:
        current_user_id = get_jwt_identity()
        data = g.validated_data
        financial_service = FinancialService()
        
        # Update transaction
        transaction = financial_service.update_transaction(
            transaction_id=transaction_id,
            user_id=current_user_id,
            amount=data['amount'],
            description=data['description'],
            category=data['category'],
            transaction_date=data['transaction_date'],
            transaction_type=data['transaction_type'],
            account_id=data.get('account_id')
        )
        
        if not transaction:
            return error_response('Transaction not found', 'Transaction not found or access denied', 404)
        
        logger.info(f"Transaction updated: {transaction_id} by user {current_user_id}")
        
        return api_response(
            'Transaction updated successfully',
            {
                'transaction': {
                    'id': transaction.id,
                    'amount': transaction.amount,
                    'description': transaction.description,
                    'category': transaction.category,
                    'transaction_date': transaction.transaction_date.isoformat(),
                    'transaction_type': transaction.transaction_type,
                    'updated_at': transaction.updated_at.isoformat()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Update transaction error: {str(e)}")
        return error_response('Failed to update transaction', str(e), 500)

@financial_bp.route('/transactions/<int:transaction_id>', methods=['DELETE'])
@jwt_required()
@require_financial_access
@require_financial_csrf
@rate_limit('financial', max_requests=10, window=3600)
def delete_transaction(transaction_id: int):
    """
    Delete a transaction
    """
    try:
        current_user_id = get_jwt_identity()
        financial_service = FinancialService()
        
        success = financial_service.delete_transaction(
            transaction_id=transaction_id,
            user_id=current_user_id
        )
        
        if not success:
            return error_response('Transaction not found', 'Transaction not found or access denied', 404)
        
        logger.info(f"Transaction deleted: {transaction_id} by user {current_user_id}")
        
        return api_response('Transaction deleted successfully')
        
    except Exception as e:
        logger.error(f"Delete transaction error: {str(e)}")
        return error_response('Failed to delete transaction', str(e), 500)

@financial_bp.route('/budgets', methods=['GET'])
@jwt_required()
@require_financial_access
@rate_limit('financial', max_requests=30, window=3600)
def get_budgets():
    """
    Get user budgets
    """
    try:
        current_user_id = get_jwt_identity()
        financial_service = FinancialService()
        
        budgets = financial_service.get_user_budgets(current_user_id)
        
        return api_response(
            'Budgets retrieved successfully',
            {'budgets': budgets}
        )
        
    except Exception as e:
        logger.error(f"Get budgets error: {str(e)}")
        return error_response('Failed to retrieve budgets', str(e), 500)

@financial_bp.route('/budgets', methods=['POST'])
@jwt_required()
@require_financial_access
@require_financial_csrf
@rate_limit('financial', max_requests=10, window=3600)
@validate_request(BUDGET_SCHEMA)
def create_budget():
    """
    Create a new budget
    """
    try:
        current_user_id = get_jwt_identity()
        data = g.validated_data
        financial_service = FinancialService()
        
        budget = financial_service.create_budget(
            user_id=current_user_id,
            name=data['name'],
            amount=data['amount'],
            category=data['category'],
            period=data['period'],
            start_date=data['start_date']
        )
        
        logger.info(f"Budget created: {budget.id} for user {current_user_id}")
        
        return api_response(
            'Budget created successfully',
            {
                'budget': {
                    'id': budget.id,
                    'name': budget.name,
                    'amount': budget.amount,
                    'category': budget.category,
                    'period': budget.period,
                    'start_date': budget.start_date.isoformat(),
                    'created_at': budget.created_at.isoformat()
                }
            },
            201
        )
        
    except Exception as e:
        logger.error(f"Create budget error: {str(e)}")
        return error_response('Failed to create budget', str(e), 500)

@financial_bp.route('/accounts', methods=['GET'])
@jwt_required()
@require_financial_access
@rate_limit('financial', max_requests=30, window=3600)
def get_accounts():
    """
    Get user accounts
    """
    try:
        current_user_id = get_jwt_identity()
        financial_service = FinancialService()
        
        accounts = financial_service.get_user_accounts(current_user_id)
        
        return api_response(
            'Accounts retrieved successfully',
            {'accounts': accounts}
        )
        
    except Exception as e:
        logger.error(f"Get accounts error: {str(e)}")
        return error_response('Failed to retrieve accounts', str(e), 500)

@financial_bp.route('/accounts', methods=['POST'])
@jwt_required()
@require_financial_access
@require_financial_csrf
@rate_limit('financial', max_requests=10, window=3600)
@validate_request(ACCOUNT_SCHEMA)
def create_account():
    """
    Create a new account
    """
    try:
        current_user_id = get_jwt_identity()
        data = g.validated_data
        financial_service = FinancialService()
        
        account = financial_service.create_account(
            user_id=current_user_id,
            name=data['name'],
            account_type=data['account_type'],
            balance=data['balance'],
            currency=data['currency']
        )
        
        logger.info(f"Account created: {account.id} for user {current_user_id}")
        
        return api_response(
            'Account created successfully',
            {
                'account': {
                    'id': account.id,
                    'name': account.name,
                    'account_type': account.account_type,
                    'balance': account.balance,
                    'currency': account.currency,
                    'created_at': account.created_at.isoformat()
                }
            },
            201
        )
        
    except Exception as e:
        logger.error(f"Create account error: {str(e)}")
        return error_response('Failed to create account', str(e), 500)

@financial_bp.route('/summary', methods=['GET'])
@jwt_required()
@require_financial_access
@rate_limit('financial', max_requests=20, window=3600)
def get_financial_summary():
    """
    Get financial summary for user
    """
    try:
        current_user_id = get_jwt_identity()
        financial_service = FinancialService()
        
        # Get query parameters for date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        summary = financial_service.get_financial_summary(
            user_id=current_user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return api_response(
            'Financial summary retrieved successfully',
            {'summary': summary}
        )
        
    except Exception as e:
        logger.error(f"Get financial summary error: {str(e)}")
        return error_response('Failed to retrieve financial summary', str(e), 500)

@financial_bp.route('/analytics/spending', methods=['GET'])
@jwt_required()
@require_financial_access
@rate_limit('financial', max_requests=20, window=3600)
def get_spending_analytics():
    """
    Get spending analytics
    """
    try:
        current_user_id = get_jwt_identity()
        financial_service = FinancialService()
        
        # Get query parameters
        period = request.args.get('period', 'monthly')  # daily, weekly, monthly, yearly
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        analytics = financial_service.get_spending_analytics(
            user_id=current_user_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        return api_response(
            'Spending analytics retrieved successfully',
            {'analytics': analytics}
        )
        
    except Exception as e:
        logger.error(f"Get spending analytics error: {str(e)}")
        return error_response('Failed to retrieve spending analytics', str(e), 500)

@financial_bp.route('/categories', methods=['GET'])
@jwt_required()
@require_financial_access
@rate_limit('financial', max_requests=30, window=3600)
def get_categories():
    """
    Get available categories
    """
    try:
        current_user_id = get_jwt_identity()
        financial_service = FinancialService()
        
        categories = financial_service.get_categories(current_user_id)
        
        return api_response(
            'Categories retrieved successfully',
            {'categories': categories}
        )
        
    except Exception as e:
        logger.error(f"Get categories error: {str(e)}")
        return error_response('Failed to retrieve categories', str(e), 500)

@financial_bp.route('/categories', methods=['POST'])
@jwt_required()
@require_financial_access
@rate_limit('financial', max_requests=10, window=3600)
@validate_request({
    'name': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 100
    },
    'type': {
        'type': 'enum',
        'values': ['income', 'expense'],
        'required': True
    },
    'color': {
        'type': 'string',
        'required': False,
        'max_length': 7
    }
})
def create_category():
    """
    Create a new category
    """
    try:
        current_user_id = get_jwt_identity()
        data = g.validated_data
        financial_service = FinancialService()
        
        category = financial_service.create_category(
            user_id=current_user_id,
            name=data['name'],
            category_type=data['type'],
            color=data.get('color')
        )
        
        logger.info(f"Category created: {category.id} for user {current_user_id}")
        
        return api_response(
            'Category created successfully',
            {
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'type': category.type,
                    'color': category.color,
                    'created_at': category.created_at.isoformat()
                }
            },
            201
        )
        
    except Exception as e:
        logger.error(f"Create category error: {str(e)}")
        return error_response('Failed to create category', str(e), 500)

@financial_bp.route('/export', methods=['POST'])
@jwt_required()
@require_financial_access
@rate_limit('financial', max_requests=5, window=3600)
@validate_request({
    'format': {
        'type': 'enum',
        'values': ['csv', 'json', 'pdf'],
        'required': True
    },
    'start_date': {
        'type': 'date',
        'required': False
    },
    'end_date': {
        'type': 'date',
        'required': False
    },
    'include_transactions': {
        'type': 'boolean',
        'required': False
    }
})
def export_financial_data():
    """
    Export financial data
    """
    try:
        current_user_id = get_jwt_identity()
        data = g.validated_data
        financial_service = FinancialService()
        
        export_data = financial_service.export_financial_data(
            user_id=current_user_id,
            export_format=data['format'],
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            include_transactions=data.get('include_transactions', True)
        )
        
        logger.info(f"Financial data exported: {data['format']} for user {current_user_id}")
        
        return api_response(
            'Financial data exported successfully',
            {'export': export_data}
        )
        
    except Exception as e:
        logger.error(f"Export financial data error: {str(e)}")
        return error_response('Failed to export financial data', str(e), 500) 