"""
Budget Tier API Routes for MINGUS

This module provides API endpoints for Budget tier functionality:
- Manual transaction entry
- Basic expense tracking
- 1-month cash flow forecasting
- Upgrade prompts with banking insights
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.services.budget_tier_service import BudgetTierService
from backend.services.tier_access_control_service import TierAccessControlService
from backend.services.notification_service import NotificationService
from backend.utils.validation import validate_amount, validate_date
from backend.utils.response import success_response, error_response
from backend.utils.auth import get_current_user_id

logger = logging.getLogger(__name__)

# Create Blueprint
budget_tier_bp = Blueprint('budget_tier', __name__, url_prefix='/api/budget-tier')


@budget_tier_bp.route('/transactions', methods=['POST'])
@login_required
def add_manual_transaction():
    """
    Add a manual transaction entry for Budget tier users
    
    Request Body:
    {
        "name": "Transaction name",
        "amount": 100.50,
        "entry_type": "expense",  // income, expense, transfer, refund
        "category": "food_dining",
        "date": "2024-01-15",
        "description": "Optional description",
        "merchant_name": "Optional merchant",
        "tags": ["tag1", "tag2"],
        "is_recurring": false,
        "recurring_frequency": "monthly"  // optional
    }
    
    Returns:
    {
        "success": true,
        "transaction_id": "uuid",
        "transaction": {...},
        "insights": [...],
        "monthly_usage": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return error_response("No data provided", 400)
        
        # Validate required fields
        required_fields = ['name', 'amount', 'entry_type', 'category', 'date']
        for field in required_fields:
            if field not in data:
                return error_response(f"Missing required field: {field}", 400)
        
        # Validate amount
        try:
            amount = Decimal(str(data['amount']))
            if amount <= 0:
                return error_response("Amount must be greater than 0", 400)
        except (ValueError, TypeError):
            return error_response("Invalid amount format", 400)
        
        # Validate date
        try:
            transaction_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return error_response("Invalid date format (use YYYY-MM-DD)", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        
        # Add transaction
        result = budget_service.add_manual_transaction(user_id, data)
        
        if result['success']:
            return success_response("Transaction added successfully", result)
        else:
            return error_response(result['error'], 400 if 'upgrade_required' not in result else 402)
            
    except Exception as e:
        logger.error(f"Error adding manual transaction: {str(e)}")
        return error_response("Internal server error", 500)


@budget_tier_bp.route('/transactions', methods=['GET'])
@login_required
def get_manual_transactions():
    """
    Get manual transactions for Budget tier users
    
    Query Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - category: Filter by category
    - entry_type: Filter by entry type
    - limit: Number of transactions to return (default: 50)
    - offset: Number of transactions to skip (default: 0)
    
    Returns:
    {
        "success": true,
        "transactions": [...],
        "total_count": 100,
        "filters": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        category = request.args.get('category')
        entry_type = request.args.get('entry_type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return error_response("Invalid start_date format", 400)
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return error_response("Invalid end_date format", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        
        # Get transactions (placeholder implementation)
        transactions = []
        total_count = 0
        
        return success_response("Transactions retrieved successfully", {
            'transactions': transactions,
            'total_count': total_count,
            'filters': {
                'start_date': start_date_str,
                'end_date': end_date_str,
                'category': category,
                'entry_type': entry_type,
                'limit': limit,
                'offset': offset
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting manual transactions: {str(e)}")
        return error_response("Internal server error", 500)


@budget_tier_bp.route('/expense-summary', methods=['GET'])
@login_required
def get_expense_summary():
    """
    Get basic expense tracking summary for Budget tier users
    
    Query Parameters:
    - start_date: Start date (YYYY-MM-DD, defaults to current month start)
    - end_date: End date (YYYY-MM-DD, defaults to current month end)
    
    Returns:
    {
        "success": true,
        "summary": {...},
        "upgrade_insights": [...],
        "period": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return error_response("Invalid start_date format", 400)
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return error_response("Invalid end_date format", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        
        # Get expense summary
        result = budget_service.get_expense_summary(user_id, start_date, end_date)
        
        if result['success']:
            return success_response("Expense summary retrieved successfully", result)
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        logger.error(f"Error getting expense summary: {str(e)}")
        return error_response("Internal server error", 500)


@budget_tier_bp.route('/cash-flow-forecast', methods=['POST'])
@login_required
def generate_cash_flow_forecast():
    """
    Generate 1-month cash flow forecast for Budget tier users
    
    Request Body:
    {
        "opening_balance": 1000.00  // optional
    }
    
    Returns:
    {
        "success": true,
        "forecast": {...},
        "upgrade_insights": [...],
        "monthly_usage": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json() or {}
        
        # Validate opening balance if provided
        opening_balance = None
        if 'opening_balance' in data:
            try:
                opening_balance = Decimal(str(data['opening_balance']))
                if opening_balance < 0:
                    return error_response("Opening balance cannot be negative", 400)
            except (ValueError, TypeError):
                return error_response("Invalid opening balance format", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        
        # Generate forecast
        result = budget_service.generate_cash_flow_forecast(user_id, opening_balance)
        
        if result['success']:
            return success_response("Cash flow forecast generated successfully", result)
        else:
            return error_response(result['error'], 400 if 'upgrade_required' not in result else 402)
            
    except Exception as e:
        logger.error(f"Error generating cash flow forecast: {str(e)}")
        return error_response("Internal server error", 500)


@budget_tier_bp.route('/upgrade-insights', methods=['GET'])
@login_required
def get_upgrade_insights():
    """
    Get banking insights for upgrade prompts for Budget tier users
    
    Returns:
    {
        "success": true,
        "insights": [...],
        "upgrade_benefits": [...],
        "tier_comparison": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        
        # Get upgrade insights
        result = budget_service.get_upgrade_insights(user_id)
        
        if result['success']:
            return success_response("Upgrade insights retrieved successfully", result)
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        logger.error(f"Error getting upgrade insights: {str(e)}")
        return error_response("Internal server error", 500)


@budget_tier_bp.route('/categories', methods=['GET'])
@login_required
def get_expense_categories():
    """
    Get available expense categories for Budget tier users
    
    Returns:
    {
        "success": true,
        "categories": [
            {
                "value": "food_dining",
                "label": "Food & Dining",
                "description": "Restaurants, groceries, and food delivery"
            }
        ]
    }
    """
    try:
        from backend.services.budget_tier_service import ExpenseCategory
        
        categories = [
            {
                'value': category.value,
                'label': category.value.replace('_', ' ').title(),
                'description': f"Expenses related to {category.value.replace('_', ' ')}"
            }
            for category in ExpenseCategory
        ]
        
        return success_response("Categories retrieved successfully", {
            'categories': categories
        })
        
    except Exception as e:
        logger.error(f"Error getting expense categories: {str(e)}")
        return error_response("Internal server error", 500)


@budget_tier_bp.route('/usage', methods=['GET'])
@login_required
def get_usage_limits():
    """
    Get current usage and limits for Budget tier users
    
    Returns:
    {
        "success": true,
        "usage": {
            "transactions": {
                "used": 45,
                "limit": 100,
                "remaining": 55
            },
            "forecasts": {
                "used": 1,
                "limit": 2,
                "remaining": 1
            }
        }
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        
        # Get usage metrics (placeholder implementation)
        usage = {
            'transactions': {
                'used': 45,  # This would be calculated from database
                'limit': budget_service.max_manual_transactions_per_month,
                'remaining': budget_service.max_manual_transactions_per_month - 45
            },
            'forecasts': {
                'used': 1,  # This would be calculated from database
                'limit': budget_service.max_cash_flow_forecasts_per_month,
                'remaining': budget_service.max_cash_flow_forecasts_per_month - 1
            }
        }
        
        return success_response("Usage limits retrieved successfully", {
            'usage': usage
        })
        
    except Exception as e:
        logger.error(f"Error getting usage limits: {str(e)}")
        return error_response("Internal server error", 500)


@budget_tier_bp.route('/transactions/<transaction_id>', methods=['PUT'])
@login_required
def update_manual_transaction(transaction_id):
    """
    Update a manual transaction for Budget tier users
    
    Request Body:
    {
        "name": "Updated transaction name",
        "amount": 150.00,
        "category": "transportation",
        "description": "Updated description"
    }
    
    Returns:
    {
        "success": true,
        "transaction": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return error_response("No data provided", 400)
        
        # Validate amount if provided
        if 'amount' in data:
            try:
                amount = Decimal(str(data['amount']))
                if amount <= 0:
                    return error_response("Amount must be greater than 0", 400)
            except (ValueError, TypeError):
                return error_response("Invalid amount format", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        
        # Update transaction (placeholder implementation)
        # This would typically update the transaction in the database
        
        return success_response("Transaction updated successfully", {
            'transaction_id': transaction_id,
            'updated_fields': list(data.keys())
        })
        
    except Exception as e:
        logger.error(f"Error updating manual transaction: {str(e)}")
        return error_response("Internal server error", 500)


@budget_tier_bp.route('/transactions/<transaction_id>', methods=['DELETE'])
@login_required
def delete_manual_transaction(transaction_id):
    """
    Delete a manual transaction for Budget tier users
    
    Returns:
    {
        "success": true,
        "message": "Transaction deleted successfully"
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        
        # Delete transaction (placeholder implementation)
        # This would typically delete the transaction from the database
        
        return success_response("Transaction deleted successfully")
        
    except Exception as e:
        logger.error(f"Error deleting manual transaction: {str(e)}")
        return error_response("Internal server error", 500)


# Error handlers
@budget_tier_bp.errorhandler(400)
def bad_request(error):
    return error_response("Bad request", 400)


@budget_tier_bp.errorhandler(401)
def unauthorized(error):
    return error_response("Unauthorized", 401)


@budget_tier_bp.errorhandler(403)
def forbidden(error):
    return error_response("Forbidden", 403)


@budget_tier_bp.errorhandler(404)
def not_found(error):
    return error_response("Not found", 404)


@budget_tier_bp.errorhandler(500)
def internal_error(error):
    return error_response("Internal server error", 500) 