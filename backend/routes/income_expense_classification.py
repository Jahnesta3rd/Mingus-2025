"""
Income vs Expense Classification API Routes

This module provides API endpoints for automatic classification of transactions
as income or expenses with detailed analysis and reporting.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json

from backend.banking.income_expense_classifier import IncomeExpenseClassifier
from backend.utils.auth_decorators import require_auth, handle_api_errors
from backend.utils.api_utils import validate_request_data, create_response
from backend.models.bank_account_models import PlaidTransaction

logger = logging.getLogger(__name__)

income_expense_classification_bp = Blueprint('income_expense_classification', __name__, url_prefix='/api/income-expense-classification')


@income_expense_classification_bp.route('/classify', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def classify_transactions():
    """
    Classify transactions as income, expense, or transfer
    
    Request body:
    {
        "transaction_ids": ["id1", "id2"],  # Optional
        "account_ids": ["account1", "account2"],  # Optional
        "date_range": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        },  # Optional
        "save_to_database": true  # Optional
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'transaction_ids': {'type': 'list', 'required': False},
            'account_ids': {'type': 'list', 'required': False},
            'date_range': {'type': 'dict', 'required': False},
            'save_to_database': {'type': 'bool', 'required': False, 'default': True}
        })
        
        # Parse date range if provided
        date_range = None
        if data.get('date_range'):
            start_date = datetime.fromisoformat(data['date_range']['start_date'])
            end_date = datetime.fromisoformat(data['date_range']['end_date'])
            date_range = (start_date, end_date)
        
        # Initialize classifier
        db_session = current_app.db.session
        classifier = IncomeExpenseClassifier(db_session)
        
        # Get transactions to classify
        query = db_session.query(PlaidTransaction).filter(
            PlaidTransaction.user_id == current_user.id
        )
        
        if data.get('transaction_ids'):
            query = query.filter(PlaidTransaction.id.in_(data['transaction_ids']))
        
        if data.get('account_ids'):
            query = query.filter(PlaidTransaction.account_id.in_(data['account_ids']))
        
        if date_range:
            query = query.filter(
                PlaidTransaction.date.between(date_range[0], date_range[1])
            )
        
        transactions = query.all()
        
        if not transactions:
            return create_response(
                success=True,
                message="No transactions found to classify",
                data={
                    'classifications': [],
                    'summary': {
                        'total_transactions': 0,
                        'income_count': 0,
                        'expense_count': 0,
                        'transfer_count': 0,
                        'total_income': 0.0,
                        'total_expenses': 0.0,
                        'net_amount': 0.0
                    }
                }
            )
        
        # Classify transactions
        classifications = classifier.batch_classify_transactions(transactions)
        
        # Save to database if requested
        if data.get('save_to_database', True):
            classifier.save_classifications_to_database(transactions, classifications)
        
        # Format response
        classifications_data = []
        for transaction, classification in zip(transactions, classifications):
            classifications_data.append({
                'transaction_id': str(transaction.id),
                'plaid_transaction_id': transaction.transaction_id,
                'amount': float(transaction.amount),
                'date': transaction.date.isoformat(),
                'merchant_name': transaction.merchant_name,
                'category': transaction.category,
                'transaction_type': classification.transaction_type.value,
                'income_category': classification.income_category.value if classification.income_category else None,
                'expense_category': classification.expense_category.value if classification.expense_category else None,
                'confidence_score': classification.confidence_score,
                'classification_confidence': classification.classification_confidence.value,
                'classification_method': classification.classification_method,
                'reasoning': classification.reasoning,
                'metadata': classification.metadata
            })
        
        # Generate summary
        summary = classifier._generate_classification_summary(transactions, classifications)
        
        return create_response(
            success=True,
            message=f"Classified {len(classifications_data)} transactions",
            data={
                'classifications': classifications_data,
                'summary': {
                    'total_transactions': summary.total_transactions,
                    'income_count': summary.income_count,
                    'expense_count': summary.expense_count,
                    'transfer_count': summary.transfer_count,
                    'unknown_count': summary.unknown_count,
                    'total_income': summary.total_income,
                    'total_expenses': summary.total_expenses,
                    'net_amount': summary.net_amount,
                    'income_categories': summary.income_categories,
                    'expense_categories': summary.expense_categories,
                    'confidence_distribution': summary.confidence_distribution,
                    'classification_accuracy': summary.classification_accuracy
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error classifying transactions: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during classification",
            status_code=500
        )


@income_expense_classification_bp.route('/classify/single', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def classify_single_transaction():
    """
    Classify a single transaction
    
    Request body:
    {
        "transaction_id": "transaction_id",
        "merchant_name": "merchant name"  # Optional
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'transaction_id': {'type': 'str', 'required': True},
            'merchant_name': {'type': 'str', 'required': False}
        })
        
        # Get transaction
        transaction = current_app.db.session.query(PlaidTransaction).filter(
            and_(
                PlaidTransaction.id == data['transaction_id'],
                PlaidTransaction.user_id == current_user.id
            )
        ).first()
        
        if not transaction:
            return create_response(
                success=False,
                message="Transaction not found",
                status_code=404
            )
        
        # Initialize classifier
        db_session = current_app.db.session
        classifier = IncomeExpenseClassifier(db_session)
        
        # Classify transaction
        classification = classifier.classify_transaction(
            transaction, 
            data.get('merchant_name')
        )
        
        return create_response(
            success=True,
            message="Transaction classified successfully",
            data={
                'transaction_id': str(transaction.id),
                'plaid_transaction_id': transaction.transaction_id,
                'amount': float(transaction.amount),
                'date': transaction.date.isoformat(),
                'merchant_name': transaction.merchant_name,
                'category': transaction.category,
                'transaction_type': classification.transaction_type.value,
                'income_category': classification.income_category.value if classification.income_category else None,
                'expense_category': classification.expense_category.value if classification.expense_category else None,
                'confidence_score': classification.confidence_score,
                'classification_confidence': classification.classification_confidence.value,
                'classification_method': classification.classification_method,
                'reasoning': classification.reasoning,
                'metadata': classification.metadata
            }
        )
        
    except Exception as e:
        logger.error(f"Error classifying single transaction: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during classification",
            status_code=500
        )


@income_expense_classification_bp.route('/summary', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_classification_summary():
    """
    Get classification summary for user transactions
    
    Query parameters:
    - account_ids: Filter by account IDs
    - date_range: Filter by date range
    - transaction_types: Filter by transaction types
    """
    try:
        account_ids = request.args.getlist('account_ids')
        transaction_types = request.args.getlist('transaction_types')
        
        # Parse date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        date_range = None
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            date_range = (start_dt, end_dt)
        
        # Initialize classifier
        db_session = current_app.db.session
        classifier = IncomeExpenseClassifier(db_session)
        
        # Get classification summary
        summary = classifier.classify_user_transactions(
            user_id=current_user.id,
            account_ids=account_ids if account_ids else None,
            date_range=date_range
        )
        
        # Filter by transaction types if specified
        if transaction_types:
            # This would require additional filtering logic
            pass
        
        return create_response(
            success=True,
            message="Retrieved classification summary",
            data={
                'total_transactions': summary.total_transactions,
                'income_count': summary.income_count,
                'expense_count': summary.expense_count,
                'transfer_count': summary.transfer_count,
                'unknown_count': summary.unknown_count,
                'total_income': summary.total_income,
                'total_expenses': summary.total_expenses,
                'net_amount': summary.net_amount,
                'income_categories': summary.income_categories,
                'expense_categories': summary.expense_categories,
                'confidence_distribution': summary.confidence_distribution,
                'classification_accuracy': summary.classification_accuracy
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving classification summary: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving summary",
            status_code=500
        )


@income_expense_classification_bp.route('/transactions', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_classified_transactions():
    """
    Get classified transactions with filtering
    
    Query parameters:
    - account_ids: Filter by account IDs
    - transaction_types: Filter by transaction types
    - income_categories: Filter by income categories
    - expense_categories: Filter by expense categories
    - confidence_min: Minimum confidence score
    - date_range: Filter by date range
    - limit: Number of transactions to return
    - offset: Pagination offset
    """
    try:
        # Parse query parameters
        account_ids = request.args.getlist('account_ids')
        transaction_types = request.args.getlist('transaction_types')
        income_categories = request.args.getlist('income_categories')
        expense_categories = request.args.getlist('expense_categories')
        confidence_min = float(request.args.get('confidence_min', 0.0))
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Parse date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = current_app.db.session.query(PlaidTransaction).filter(
            PlaidTransaction.user_id == current_user.id
        )
        
        if account_ids:
            query = query.filter(PlaidTransaction.account_id.in_(account_ids))
        
        if transaction_types:
            query = query.filter(PlaidTransaction.transaction_type.in_(transaction_types))
        
        if income_categories:
            query = query.filter(PlaidTransaction.income_category.in_(income_categories))
        
        if expense_categories:
            query = query.filter(PlaidTransaction.expense_category.in_(expense_categories))
        
        if confidence_min > 0:
            query = query.filter(PlaidTransaction.classification_confidence >= confidence_min)
        
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(
                PlaidTransaction.date.between(start_dt, end_dt)
            )
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        transactions = query.order_by(PlaidTransaction.date.desc()).offset(offset).limit(limit).all()
        
        # Format response
        transactions_data = []
        for tx in transactions:
            transactions_data.append({
                'id': str(tx.id),
                'transaction_id': tx.transaction_id,
                'account_id': tx.account_id,
                'amount': float(tx.amount),
                'date': tx.date.isoformat(),
                'merchant_name': tx.merchant_name,
                'category': tx.category,
                'transaction_type': tx.transaction_type,
                'income_category': tx.income_category,
                'expense_category': tx.expense_category,
                'classification_confidence': tx.classification_confidence,
                'classification_method': tx.classification_method,
                'classification_reasoning': json.loads(tx.classification_reasoning) if tx.classification_reasoning else [],
                'classification_metadata': json.loads(tx.classification_metadata) if tx.classification_metadata else {},
                'created_at': tx.created_at.isoformat()
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(transactions_data)} classified transactions",
            data={
                'transactions': transactions_data,
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving classified transactions: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving transactions",
            status_code=500
        )


@income_expense_classification_bp.route('/categories', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_classification_categories():
    """
    Get available classification categories
    
    Query parameters:
    - category_type: Filter by category type (income, expense, or all)
    """
    try:
        category_type = request.args.get('category_type', 'all')
        
        from backend.banking.income_expense_classifier import IncomeCategory, ExpenseCategory
        
        categories = {}
        
        if category_type in ['all', 'income']:
            categories['income'] = [
                {
                    'value': category.value,
                    'label': category.value.replace('_', ' ').title(),
                    'description': f"Income from {category.value.replace('_', ' ')}"
                }
                for category in IncomeCategory
            ]
        
        if category_type in ['all', 'expense']:
            categories['expense'] = [
                {
                    'value': category.value,
                    'label': category.value.replace('_', ' ').title(),
                    'description': f"Expense for {category.value.replace('_', ' ')}"
                }
                for category in ExpenseCategory
            ]
        
        return create_response(
            success=True,
            message="Retrieved classification categories",
            data=categories
        )
        
    except Exception as e:
        logger.error(f"Error retrieving classification categories: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving categories",
            status_code=500
        )


@income_expense_classification_bp.route('/statistics', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_classification_statistics():
    """
    Get detailed classification statistics
    
    Query parameters:
    - account_ids: Filter by account IDs
    - date_range: Filter by date range
    """
    try:
        account_ids = request.args.getlist('account_ids')
        
        # Parse date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        date_range = None
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            date_range = (start_dt, end_dt)
        
        # Initialize classifier
        db_session = current_app.db.session
        classifier = IncomeExpenseClassifier(db_session)
        
        # Get classification summary
        summary = classifier.classify_user_transactions(
            user_id=current_user.id,
            account_ids=account_ids if account_ids else None,
            date_range=date_range
        )
        
        # Calculate additional statistics
        from sqlalchemy import func
        
        # Get confidence distribution
        confidence_query = db_session.query(
            PlaidTransaction.classification_confidence,
            func.count(PlaidTransaction.id).label('count')
        ).filter(
            PlaidTransaction.user_id == current_user.id
        )
        
        if account_ids:
            confidence_query = confidence_query.filter(PlaidTransaction.account_id.in_(account_ids))
        
        if date_range:
            confidence_query = confidence_query.filter(
                PlaidTransaction.date.between(date_range[0], date_range[1])
            )
        
        confidence_stats = confidence_query.group_by(PlaidTransaction.classification_confidence).all()
        
        # Get method distribution
        method_query = db_session.query(
            PlaidTransaction.classification_method,
            func.count(PlaidTransaction.id).label('count')
        ).filter(
            PlaidTransaction.user_id == current_user.id
        )
        
        if account_ids:
            method_query = method_query.filter(PlaidTransaction.account_id.in_(account_ids))
        
        if date_range:
            method_query = method_query.filter(
                PlaidTransaction.date.between(date_range[0], date_range[1])
            )
        
        method_stats = method_query.group_by(PlaidTransaction.classification_method).all()
        
        # Format statistics
        confidence_distribution = {
            'high': 0,
            'medium': 0,
            'low': 0,
            'unknown': 0
        }
        
        for stat in confidence_stats:
            if stat.classification_confidence >= 0.8:
                confidence_distribution['high'] = stat.count
            elif stat.classification_confidence >= 0.6:
                confidence_distribution['medium'] = stat.count
            elif stat.classification_confidence >= 0.4:
                confidence_distribution['low'] = stat.count
            else:
                confidence_distribution['unknown'] = stat.count
        
        method_distribution = [
            {
                'method': stat.classification_method or 'unknown',
                'count': stat.count,
                'percentage': (stat.count / summary.total_transactions * 100) if summary.total_transactions > 0 else 0
            }
            for stat in method_stats
        ]
        
        return create_response(
            success=True,
            message="Retrieved classification statistics",
            data={
                'summary': {
                    'total_transactions': summary.total_transactions,
                    'income_count': summary.income_count,
                    'expense_count': summary.expense_count,
                    'transfer_count': summary.transfer_count,
                    'total_income': summary.total_income,
                    'total_expenses': summary.total_expenses,
                    'net_amount': summary.net_amount,
                    'classification_accuracy': summary.classification_accuracy
                },
                'confidence_distribution': confidence_distribution,
                'method_distribution': method_distribution,
                'income_categories': summary.income_categories,
                'expense_categories': summary.expense_categories
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving classification statistics: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving statistics",
            status_code=500
        )


@income_expense_classification_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for income vs expense classification service
    """
    try:
        # Check database connection
        db_session = current_app.db.session
        db_session.execute(text('SELECT 1'))
        
        return create_response(
            success=True,
            message="Income vs expense classification service is healthy",
            data={
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_response(
            success=False,
            message="Income vs expense classification service is unhealthy",
            status_code=503,
            data={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )


def register_income_expense_classification_routes(app):
    """Register income vs expense classification routes with the Flask app"""
    app.register_blueprint(income_expense_classification_bp)
    logger.info("Income vs expense classification routes registered successfully") 