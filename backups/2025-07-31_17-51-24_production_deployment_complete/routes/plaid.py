"""
Plaid API Routes for MINGUS

This module provides comprehensive API endpoints for Plaid integration:
- Bank account linking via Plaid Link
- Account balance retrieval
- Transaction history access (up to 24 months)
- Account identity verification
- Real-time balance updates via webhooks
- Subscription tier integration with upgrade prompts
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app, session
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import uuid

from backend.middleware.auth import require_auth
from backend.integrations.plaid_integration import (
    PlaidIntegrationService, 
    PlaidConfig, 
    PlaidEnvironment,
    PlaidProduct,
    create_plaid_config_from_env,
    validate_plaid_config
)
from backend.models.plaid_models import (
    PlaidConnection, 
    PlaidAccount, 
    PlaidTransaction, 
    PlaidInstitution, 
    PlaidSyncLog,
    PlaidIdentity
)
from backend.services.plaid_subscription_service import (
    PlaidSubscriptionService,
    PlaidFeature
)
from backend.utils.auth_decorators import handle_api_errors

logger = logging.getLogger(__name__)

# Create Blueprint
plaid_bp = Blueprint('plaid', __name__, url_prefix='/api/plaid')

def get_plaid_service() -> PlaidIntegrationService:
    """Get Plaid integration service instance"""
    config = create_plaid_config_from_env()
    if not validate_plaid_config(config):
        raise ValueError("Invalid Plaid configuration")
    
    db_session = current_app.db.session
    return PlaidIntegrationService(db_session, config)

def get_plaid_subscription_service() -> PlaidSubscriptionService:
    """Get Plaid subscription service instance"""
    db_session = current_app.db.session
    feature_access_service = current_app.feature_access_service
    return PlaidSubscriptionService(db_session, feature_access_service)

# ============================================================================
# SUBSCRIPTION TIER INTEGRATION
# ============================================================================

@plaid_bp.route('/subscription/status', methods=['GET'])
@require_auth
@handle_api_errors
def get_plaid_subscription_status():
    """Get Plaid subscription status and limits for the current user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        subscription_service = get_plaid_subscription_service()
        
        # Get user's tier and limits
        tier_limits = subscription_service.get_tier_limits(str(user_id))
        usage_metrics = subscription_service.get_user_usage_metrics(str(user_id))
        upgrade_recommendations = subscription_service.get_upgrade_recommendations(str(user_id))
        
        # Get tier comparison
        tier_comparison = subscription_service.get_tier_comparison()
        
        return jsonify({
            'success': True,
            'current_tier': {
                'name': tier_limits.tier,
                'limits': {
                    'max_accounts': tier_limits.max_accounts,
                    'max_connections': tier_limits.max_connections,
                    'transaction_history_months': tier_limits.transaction_history_months,
                    'real_time_updates': tier_limits.real_time_updates,
                    'advanced_analytics': tier_limits.advanced_analytics,
                    'manual_entry_only': tier_limits.manual_entry_only
                }
            },
            'usage_metrics': {
                'total_connections': usage_metrics.total_connections,
                'total_accounts': usage_metrics.total_accounts,
                'active_connections': usage_metrics.active_connections,
                'active_accounts': usage_metrics.active_accounts,
                'last_transaction_sync': usage_metrics.last_transaction_sync.isoformat() if usage_metrics.last_transaction_sync else None,
                'total_transactions': usage_metrics.total_transactions,
                'usage_percentage': usage_metrics.usage_percentage
            },
            'upgrade_recommendations': [
                {
                    'feature': rec.feature.value,
                    'current_usage': rec.current_usage,
                    'current_limit': rec.current_limit,
                    'upgrade_tier': rec.upgrade_tier,
                    'upgrade_benefits': rec.upgrade_benefits,
                    'upgrade_price': rec.upgrade_price,
                    'trial_available': rec.trial_available,
                    'trial_duration_days': rec.trial_duration_days
                }
                for rec in upgrade_recommendations
            ],
            'tier_comparison': tier_comparison
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting Plaid subscription status: {e}")
        return jsonify({'error': 'Failed to get subscription status'}), 500

@plaid_bp.route('/subscription/limits', methods=['GET'])
@require_auth
@handle_api_errors
def check_plaid_limits():
    """Check if user can perform Plaid operations based on their tier"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        subscription_service = get_plaid_subscription_service()
        
        # Check various Plaid operations
        can_add_connection, connection_message, connection_upgrade = subscription_service.can_add_connection(str(user_id))
        can_add_account, account_message, account_upgrade = subscription_service.can_add_account(str(user_id))
        can_access_history, history_message, history_upgrade = subscription_service.can_access_transaction_history(str(user_id))
        can_access_analytics, analytics_message, analytics_upgrade = subscription_service.can_access_advanced_analytics(str(user_id))
        
        # Check for violations
        violations = subscription_service.enforce_tier_limits(str(user_id))
        
        return jsonify({
            'success': True,
            'limits': {
                'can_add_connection': can_add_connection,
                'connection_message': connection_message,
                'connection_upgrade': connection_upgrade._asdict() if connection_upgrade else None,
                
                'can_add_account': can_add_account,
                'account_message': account_message,
                'account_upgrade': account_upgrade._asdict() if account_upgrade else None,
                
                'can_access_history': can_access_history,
                'history_message': history_message,
                'history_upgrade': history_upgrade._asdict() if history_upgrade else None,
                
                'can_access_analytics': can_access_analytics,
                'analytics_message': analytics_message,
                'analytics_upgrade': analytics_upgrade._asdict() if analytics_upgrade else None
            },
            'violations': violations
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking Plaid limits: {e}")
        return jsonify({'error': 'Failed to check limits'}), 500

# ============================================================================
# BANK ACCOUNT LINKING VIA PLAID LINK (WITH TIER CHECKS)
# ============================================================================

@plaid_bp.route('/link-token', methods=['POST'])
@require_auth
@handle_api_errors
def create_link_token():
    """Create a Plaid Link token for connecting bank accounts (with tier checks)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Check if user can add connections
        subscription_service = get_plaid_subscription_service()
        can_add_connection, message, upgrade_prompt = subscription_service.can_add_connection(str(user_id))
        
        if not can_add_connection:
            return jsonify({
                'error': 'Cannot create Link token',
                'message': message,
                'upgrade_required': True,
                'upgrade_prompt': upgrade_prompt._asdict() if upgrade_prompt else None
            }), 403
        
        # Get request data
        data = request.get_json() or {}
        products = data.get('products', ['transactions', 'auth', 'identity'])
        
        # Convert product strings to PlaidProduct enums
        plaid_products = []
        for product in products:
            try:
                plaid_products.append(PlaidProduct(product))
            except ValueError:
                return jsonify({'error': f'Invalid product: {product}'}), 400
        
        # Create Plaid service
        plaid_service = get_plaid_service()
        
        # Create Link token
        link_token = plaid_service.create_link_token(str(user_id), plaid_products)
        
        response_data = {
            'success': True,
            'link_token': link_token.link_token,
            'expiration': link_token.expiration.isoformat(),
            'request_id': link_token.request_id
        }
        
        # Add upgrade prompt if approaching limits
        if upgrade_prompt:
            response_data['upgrade_prompt'] = upgrade_prompt._asdict()
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error creating Link token: {e}")
        return jsonify({'error': 'Failed to create Link token'}), 500

@plaid_bp.route('/connect', methods=['POST'])
@require_auth
@handle_api_errors
def connect_bank_account():
    """Connect a bank account using public token (with tier checks)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Check if user can add connections
        subscription_service = get_plaid_subscription_service()
        can_add_connection, message, upgrade_prompt = subscription_service.can_add_connection(str(user_id))
        
        if not can_add_connection:
            return jsonify({
                'error': 'Cannot connect bank account',
                'message': message,
                'upgrade_required': True,
                'upgrade_prompt': upgrade_prompt._asdict() if upgrade_prompt else None
            }), 403
        
        data = request.get_json()
        if not data or 'public_token' not in data:
            return jsonify({'error': 'Public token is required'}), 400
        
        public_token = data['public_token']
        
        # Create Plaid service
        plaid_service = get_plaid_service()
        
        # Exchange public token for access token and create connection
        connection = plaid_service.exchange_public_token(public_token, str(user_id))
        
        response_data = {
            'success': True,
            'connection_id': str(connection.id),
            'institution_name': connection.institution_name,
            'message': 'Bank account connected successfully'
        }
        
        # Add upgrade prompt if approaching limits
        if upgrade_prompt:
            response_data['upgrade_prompt'] = upgrade_prompt._asdict()
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error connecting bank account: {e}")
        return jsonify({'error': 'Failed to connect bank account'}), 500

@plaid_bp.route('/connections', methods=['GET'])
@require_auth
@handle_api_errors
def get_connections():
    """Get all connections for the current user (with tier information)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get connections from database
        connections = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.user_id == user_id,
            PlaidConnection.is_active == True
        ).all()
        
        # Get subscription information
        subscription_service = get_plaid_subscription_service()
        tier_limits = subscription_service.get_tier_limits(str(user_id))
        usage_metrics = subscription_service.get_user_usage_metrics(str(user_id))
        
        # Create Plaid service for status information
        plaid_service = get_plaid_service()
        
        connection_data = []
        for connection in connections:
            status = plaid_service.get_connection_status(connection)
            connection_data.append({
                'id': str(connection.id),
                'institution_name': connection.institution_name,
                'institution_id': connection.institution_id,
                'is_active': connection.is_active,
                'last_sync_at': connection.last_sync_at.isoformat() if connection.last_sync_at else None,
                'created_at': connection.created_at.isoformat(),
                'status': status
            })
        
        return jsonify({
            'success': True,
            'connections': connection_data,
            'count': len(connection_data),
            'tier_limits': {
                'max_connections': tier_limits.max_connections,
                'max_accounts': tier_limits.max_accounts
            },
            'usage': {
                'active_connections': usage_metrics.active_connections,
                'active_accounts': usage_metrics.active_accounts,
                'usage_percentage': usage_metrics.usage_percentage
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        return jsonify({'error': 'Failed to get connections'}), 500

@plaid_bp.route('/connections/<connection_id>', methods=['DELETE'])
@require_auth
@handle_api_errors
def remove_connection(connection_id):
    """Remove a Plaid connection"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get connection
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Create Plaid service
        plaid_service = get_plaid_service()
        
        # Remove connection
        success = plaid_service.remove_connection(connection)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Connection removed successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to remove connection'}), 500
        
    except Exception as e:
        logger.error(f"Error removing connection: {e}")
        return jsonify({'error': 'Failed to remove connection'}), 500

# ============================================================================
# ACCOUNT BALANCE RETRIEVAL (WITH TIER CHECKS)
# ============================================================================

@plaid_bp.route('/accounts/<connection_id>/balances', methods=['GET'])
@require_auth
@handle_api_errors
def get_account_balances(connection_id):
    """Get account balances for a connection (with tier checks)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Check if user has access to balance retrieval
        subscription_service = get_plaid_subscription_service()
        access_result = subscription_service.check_plaid_feature_access(
            str(user_id), 
            PlaidFeature.ACCOUNT_BALANCE_RETRIEVAL
        )
        
        if not access_result.has_access:
            return jsonify({
                'error': 'Cannot access account balances',
                'message': access_result.reason,
                'upgrade_required': access_result.upgrade_required,
                'educational_content': access_result.educational_content,
                'alternative_suggestions': access_result.alternative_suggestions,
                'upgrade_benefits': access_result.upgrade_benefits
            }), 403
        
        # Get connection
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id,
            PlaidConnection.is_active == True
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Create Plaid service
        plaid_service = get_plaid_service()
        
        # Get account balances
        balances = plaid_service.get_account_balances(connection)
        
        balance_data = []
        for balance in balances:
            balance_data.append({
                'account_id': balance.account_id,
                'current_balance': balance.current_balance,
                'available_balance': balance.available_balance,
                'iso_currency_code': balance.iso_currency_code,
                'unofficial_currency_code': balance.unofficial_currency_code,
                'limit': balance.limit,
                'last_updated_datetime': balance.last_updated_datetime.isoformat() if balance.last_updated_datetime else None
            })
        
        return jsonify({
            'success': True,
            'balances': balance_data,
            'connection_id': str(connection.id),
            'institution_name': connection.institution_name
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting account balances: {e}")
        return jsonify({'error': 'Failed to get account balances'}), 500

# ============================================================================
# TRANSACTION HISTORY ACCESS (WITH TIER CHECKS)
# ============================================================================

@plaid_bp.route('/transactions/<connection_id>', methods=['GET'])
@require_auth
@handle_api_errors
def get_transactions(connection_id):
    """Get transaction history for a connection (with tier checks)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        account_ids = request.args.getlist('account_ids')
        
        # Calculate months requested
        months_requested = 24  # Default to 24 months
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                months_requested = ((end.year - start.year) * 12) + (end.month - start.month)
            except ValueError:
                pass
        
        # Check if user can access transaction history
        subscription_service = get_plaid_subscription_service()
        can_access_history, message, upgrade_prompt = subscription_service.can_access_transaction_history(
            str(user_id), months_requested
        )
        
        if not can_access_history:
            return jsonify({
                'error': 'Cannot access transaction history',
                'message': message,
                'upgrade_required': True,
                'upgrade_prompt': upgrade_prompt._asdict() if upgrade_prompt else None
            }), 403
        
        # Get connection
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id,
            PlaidConnection.is_active == True
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Create Plaid service
        plaid_service = get_plaid_service()
        
        # Get transaction history
        transactions = plaid_service.get_transaction_history(
            connection, 
            start_date=start_date, 
            end_date=end_date,
            account_ids=account_ids if account_ids else None
        )
        
        transaction_data = []
        for transaction in transactions:
            transaction_data.append({
                'transaction_id': transaction.transaction_id,
                'pending_transaction_id': transaction.pending_transaction_id,
                'name': transaction.name,
                'amount': transaction.amount,
                'date': transaction.date,
                'datetime': transaction.datetime,
                'authorized_date': transaction.authorized_date,
                'authorized_datetime': transaction.authorized_datetime,
                'merchant_name': transaction.merchant_name,
                'logo_url': transaction.logo_url,
                'website': transaction.website,
                'category': transaction.category,
                'category_id': transaction.category_id,
                'personal_finance_category': transaction.personal_finance_category,
                'pending': transaction.pending,
                'payment_channel': transaction.payment_channel,
                'transaction_type': transaction.transaction_type,
                'transaction_code': transaction.transaction_code,
                'location': transaction.location,
                'payment_meta': transaction.payment_meta,
                'iso_currency_code': transaction.iso_currency_code,
                'unofficial_currency_code': transaction.unofficial_currency_code,
                'account_owner': transaction.account_owner,
                'check_number': transaction.check_number
            })
        
        response_data = {
            'success': True,
            'transactions': transaction_data,
            'count': len(transaction_data),
            'connection_id': str(connection.id),
            'institution_name': connection.institution_name
        }
        
        # Add upgrade prompt if approaching limits
        if upgrade_prompt:
            response_data['upgrade_prompt'] = upgrade_prompt._asdict()
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return jsonify({'error': 'Failed to get transactions'}), 500

@plaid_bp.route('/transactions/sync/<connection_id>', methods=['POST'])
@require_auth
@handle_api_errors
def sync_transactions(connection_id):
    """Sync transactions for a connection"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json() or {}
        cursor = data.get('cursor')
        
        # Get connection
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id,
            PlaidConnection.is_active == True
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Create Plaid service
        plaid_service = get_plaid_service()
        
        # Sync transactions
        transactions, next_cursor, has_more = plaid_service.sync_transactions(connection, cursor)
        
        transaction_data = []
        for transaction in transactions:
            transaction_data.append({
                'transaction_id': transaction.transaction_id,
                'name': transaction.name,
                'amount': transaction.amount,
                'date': transaction.date,
                'pending': transaction.pending,
                'category': transaction.category
            })
        
        return jsonify({
            'success': True,
            'transactions': transaction_data,
            'count': len(transaction_data),
            'next_cursor': next_cursor,
            'has_more': has_more
        }), 200
        
    except Exception as e:
        logger.error(f"Error syncing transactions: {e}")
        return jsonify({'error': 'Failed to sync transactions'}), 500

@plaid_bp.route('/transactions', methods=['GET'])
@require_auth
@handle_api_errors
def get_all_transactions():
    """Get all transactions for the current user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        account_id = request.args.get('account_id')
        
        # Build query
        query = current_app.db.session.query(PlaidTransaction).filter(
            PlaidTransaction.user_id == user_id,
            PlaidTransaction.is_active == True
        )
        
        if start_date:
            query = query.filter(PlaidTransaction.date >= start_date)
        if end_date:
            query = query.filter(PlaidTransaction.date <= end_date)
        if account_id:
            query = query.filter(PlaidTransaction.account_id == account_id)
        
        # Get total count
        total_count = query.count()
        
        # Get paginated results
        transactions = query.order_by(desc(PlaidTransaction.date)).offset((page - 1) * per_page).limit(per_page).all()
        
        transaction_data = []
        for transaction in transactions:
            transaction_data.append({
                'id': str(transaction.id),
                'transaction_id': transaction.plaid_transaction_id,
                'name': transaction.name,
                'amount': transaction.amount,
                'date': transaction.date,
                'merchant_name': transaction.merchant_name,
                'category': transaction.category,
                'pending': transaction.pending,
                'account_id': str(transaction.account_id),
                'connection_id': str(transaction.connection_id)
            })
        
        return jsonify({
            'success': True,
            'transactions': transaction_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting all transactions: {e}")
        return jsonify({'error': 'Failed to get transactions'}), 500

# ============================================================================
# IDENTITY VERIFICATION (WITH TIER CHECKS)
# ============================================================================

@plaid_bp.route('/identity/<connection_id>', methods=['GET'])
@require_auth
@handle_api_errors
def get_account_identity(connection_id):
    """Get account identity information for a connection (with tier checks)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Check if user has access to identity verification
        subscription_service = get_plaid_subscription_service()
        access_result = subscription_service.check_plaid_feature_access(
            str(user_id), 
            PlaidFeature.IDENTITY_VERIFICATION
        )
        
        if not access_result.has_access:
            return jsonify({
                'error': 'Cannot access identity verification',
                'message': access_result.reason,
                'upgrade_required': access_result.upgrade_required,
                'educational_content': access_result.educational_content,
                'alternative_suggestions': access_result.alternative_suggestions,
                'upgrade_benefits': access_result.upgrade_benefits
            }), 403
        
        # Get connection
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id,
            PlaidConnection.is_active == True
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Create Plaid service
        plaid_service = get_plaid_service()
        
        # Get account identity
        identity = plaid_service.get_account_identity(connection)
        
        return jsonify({
            'success': True,
            'identity': {
                'names': identity.names,
                'phone_numbers': identity.phone_numbers,
                'emails': identity.emails,
                'addresses': identity.addresses,
                'account_ids': identity.account_ids
            },
            'connection_id': str(connection.id),
            'institution_name': connection.institution_name
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting account identity: {e}")
        return jsonify({'error': 'Failed to get account identity'}), 500

@plaid_bp.route('/identity', methods=['GET'])
@require_auth
@handle_api_errors
def get_all_identities():
    """Get all identity information for the current user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get identities from database
        identities = current_app.db.session.query(PlaidIdentity).filter(
            PlaidIdentity.user_id == user_id,
            PlaidIdentity.is_active == True
        ).all()
        
        identity_data = []
        for identity in identities:
            identity_data.append({
                'id': str(identity.id),
                'connection_id': str(identity.connection_id),
                'names': identity.names,
                'phone_numbers': identity.phone_numbers,
                'emails': identity.emails,
                'addresses': identity.addresses,
                'account_ids': identity.account_ids,
                'created_at': identity.created_at.isoformat(),
                'updated_at': identity.updated_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'identities': identity_data,
            'count': len(identity_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting all identities: {e}")
        return jsonify({'error': 'Failed to get identities'}), 500

# ============================================================================
# ADVANCED ANALYTICS (WITH TIER CHECKS)
# ============================================================================

@plaid_bp.route('/analytics/<connection_id>', methods=['GET'])
@require_auth
@handle_api_errors
def get_advanced_analytics(connection_id):
    """Get advanced analytics for a connection (with tier checks)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Check if user can access advanced analytics
        subscription_service = get_plaid_subscription_service()
        can_access_analytics, message, upgrade_prompt = subscription_service.can_access_advanced_analytics(str(user_id))
        
        if not can_access_analytics:
            return jsonify({
                'error': 'Cannot access advanced analytics',
                'message': message,
                'upgrade_required': True,
                'upgrade_prompt': upgrade_prompt._asdict() if upgrade_prompt else None
            }), 403
        
        # Get connection
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id,
            PlaidConnection.is_active == True
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # This would implement advanced analytics logic
        # For now, return a placeholder response
        analytics_data = {
            'spending_patterns': {
                'top_categories': [],
                'monthly_trends': [],
                'unusual_spending': []
            },
            'financial_insights': {
                'savings_rate': 0.0,
                'debt_to_income': 0.0,
                'emergency_fund_status': 'unknown'
            },
            'recommendations': []
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics_data,
            'connection_id': str(connection.id),
            'institution_name': connection.institution_name
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting advanced analytics: {e}")
        return jsonify({'error': 'Failed to get advanced analytics'}), 500

# ============================================================================
# UPGRADE PROMPTS AND TRIALS
# ============================================================================

@plaid_bp.route('/upgrade/recommendations', methods=['GET'])
@require_auth
@handle_api_errors
def get_upgrade_recommendations():
    """Get upgrade recommendations for Plaid features"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        subscription_service = get_plaid_subscription_service()
        recommendations = subscription_service.get_upgrade_recommendations(str(user_id))
        
        return jsonify({
            'success': True,
            'recommendations': [
                {
                    'feature': rec.feature.value,
                    'current_usage': rec.current_usage,
                    'current_limit': rec.current_limit,
                    'upgrade_tier': rec.upgrade_tier,
                    'upgrade_benefits': rec.upgrade_benefits,
                    'upgrade_price': rec.upgrade_price,
                    'trial_available': rec.trial_available,
                    'trial_duration_days': rec.trial_duration_days
                }
                for rec in recommendations
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting upgrade recommendations: {e}")
        return jsonify({'error': 'Failed to get upgrade recommendations'}), 500

@plaid_bp.route('/trial/start', methods=['POST'])
@require_auth
@handle_api_errors
def start_plaid_trial():
    """Start a trial for Plaid features"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data or 'feature' not in data:
            return jsonify({'error': 'Feature is required'}), 400
        
        feature = data['feature']
        
        # This would implement trial logic
        # For now, return a placeholder response
        return jsonify({
            'success': True,
            'trial_started': True,
            'feature': feature,
            'trial_end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
            'message': f'Trial started for {feature}'
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting trial: {e}")
        return jsonify({'error': 'Failed to start trial'}), 500

# ============================================================================
# EXISTING ENDPOINTS (UPDATED WITH TIER CHECKS)
# ============================================================================

@plaid_bp.route('/accounts', methods=['GET'])
@require_auth
@handle_api_errors
def get_accounts():
    """Get all accounts for the current user (with tier information)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get subscription information
        subscription_service = get_plaid_subscription_service()
        tier_limits = subscription_service.get_tier_limits(str(user_id))
        usage_metrics = subscription_service.get_user_usage_metrics(str(user_id))
        
        # Get accounts from database
        accounts = current_app.db.session.query(PlaidAccount).filter(
            PlaidAccount.user_id == user_id,
            PlaidAccount.is_active == True
        ).all()
        
        account_data = []
        for account in accounts:
            account_data.append({
                'id': str(account.id),
                'connection_id': str(account.connection_id),
                'plaid_account_id': account.plaid_account_id,
                'name': account.name,
                'mask': account.mask,
                'official_name': account.official_name,
                'type': account.type,
                'subtype': account.subtype,
                'current_balance': account.current_balance,
                'available_balance': account.available_balance,
                'iso_currency_code': account.iso_currency_code,
                'unofficial_currency_code': account.unofficial_currency_code,
                'limit': account.limit,
                'last_balance_update': account.last_balance_update.isoformat() if account.last_balance_update else None,
                'created_at': account.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'accounts': account_data,
            'count': len(account_data),
            'tier_limits': {
                'max_accounts': tier_limits.max_accounts,
                'max_connections': tier_limits.max_connections
            },
            'usage': {
                'active_accounts': usage_metrics.active_accounts,
                'usage_percentage': usage_metrics.usage_percentage
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        return jsonify({'error': 'Failed to get accounts'}), 500

# Keep other existing endpoints with similar tier checks...
# (sync_transactions, get_all_transactions, get_all_identities, etc.)

# ============================================================================
# WEBHOOK AND HEALTH ENDPOINTS (NO TIER CHECKS NEEDED)
# ============================================================================

@plaid_bp.route('/webhook', methods=['POST'])
@handle_api_errors
def handle_webhook():
    """Handle Plaid webhook events for real-time updates"""
    try:
        # Import webhook handler
        from backend.webhooks.plaid_webhooks import handle_plaid_webhook
        
        # Handle webhook
        return handle_plaid_webhook()
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@plaid_bp.route('/health', methods=['GET'])
@handle_api_errors
def health_check():
    """Health check for Plaid integration"""
    try:
        # Test Plaid configuration
        config = create_plaid_config_from_env()
        is_valid = validate_plaid_config(config)
        
        if not is_valid:
            return jsonify({
                'status': 'unhealthy',
                'error': 'Invalid Plaid configuration'
            }), 503
        
        return jsonify({
            'status': 'healthy',
            'environment': config.environment.value,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

# ============================================================================
# SANDBOX UTILITIES (FOR TESTING)
# ============================================================================

@plaid_bp.route('/sandbox/public-token', methods=['POST'])
@require_auth
@handle_api_errors
def create_sandbox_public_token():
    """Create a sandbox public token for testing"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data or 'institution_id' not in data:
            return jsonify({'error': 'Institution ID is required'}), 400
        
        institution_id = data['institution_id']
        initial_products = data.get('initial_products', ['auth', 'transactions', 'identity'])
        
        # Create Plaid service
        plaid_service = get_plaid_service()
        
        # Create sandbox public token
        public_token = plaid_service.create_sandbox_public_token(institution_id, initial_products)
        
        return jsonify({
            'success': True,
            'public_token': public_token,
            'institution_id': institution_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating sandbox public token: {e}")
        return jsonify({'error': 'Failed to create sandbox public token'}), 500

# ============================================================================
# INSTITUTION SEARCH
# ============================================================================

@plaid_bp.route('/institutions/search', methods=['GET'])
@require_auth
@handle_api_errors
def search_institutions():
    """Search for financial institutions"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Get institutions from database
        institutions = current_app.db.session.query(PlaidInstitution).filter(
            PlaidInstitution.name.ilike(f'%{query}%'),
            PlaidInstitution.is_active == True
        ).limit(20).all()
        
        institution_data = []
        for institution in institutions:
            institution_data.append({
                'id': str(institution.id),
                'plaid_institution_id': institution.plaid_institution_id,
                'name': institution.name,
                'logo': institution.logo,
                'primary_color': institution.primary_color,
                'url': institution.url,
                'products': institution.products,
                'oauth': institution.oauth
            })
        
        return jsonify({
            'success': True,
            'institutions': institution_data,
            'count': len(institution_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching institutions: {e}")
        return jsonify({'error': 'Failed to search institutions'}), 500 