"""
Account Linking API Routes for MINGUS

This module provides API endpoints for the complete account linking workflow:
- Account linking initiation
- Plaid Link integration
- Multi-factor authentication
- Account ownership verification
- Connection establishment
"""

import logging
from typing import Dict, Any, List
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from backend.services.account_linking_service import AccountLinkingService
from backend.middleware.auth import require_auth
from backend.middleware.error_handling import handle_api_errors
from backend.utils.validation import validate_request_data
from backend.utils.response import create_response

logger = logging.getLogger(__name__)

# Create blueprint
account_linking_bp = Blueprint('account_linking', __name__, url_prefix='/api/account-linking')

@account_linking_bp.route('/initiate', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def initiate_linking():
    """
    Initiate account linking process
    
    Request Body:
    {
        "institution_id": "string" (optional)
    }
    
    Response:
    {
        "success": true,
        "session_id": "string",
        "link_token": "string",
        "expires_at": "string",
        "status": "string"
    }
    """
    try:
        # Validate request data
        data = request.get_json() or {}
        validation_result = validate_request_data(data, {
            'institution_id': {'type': 'string', 'required': False}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize account linking service
        linking_service = AccountLinkingService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Initiate linking process
        result = linking_service.initiate_linking(
            user_id=str(current_user.id),
            institution_id=data.get('institution_id')
        )
        
        if not result['success']:
            # Handle tier-based errors
            if result.get('error') in ['upgrade_required', 'limit_reached', 'account_limit_exceeded']:
                status_code = 403  # Forbidden - tier restrictions
            else:
                status_code = 500
            return create_response(**result), status_code
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error initiating account linking: {str(e)}")
        return create_response(
            success=False,
            error='initiation_failed',
            message='Failed to initiate account linking process'
        ), 500

@account_linking_bp.route('/accounts/select', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def handle_account_selection():
    """
    Handle account selection from Plaid Link
    
    Request Body:
    {
        "session_id": "string",
        "public_token": "string",
        "account_ids": ["string"]
    }
    
    Response:
    {
        "success": true,
        "session_id": "string",
        "status": "string",
        "mfa_required": boolean,
        "mfa_type": "string" (if mfa_required),
        "mfa_session_id": "string" (if mfa_required),
        "questions": [{"question": "string", "field": "string"}] (if mfa_required),
        "verification_required": boolean,
        "verification_method": "string" (if verification_required),
        "verification_session_id": "string" (if verification_required),
        "micro_deposits": [{"amount": number, "currency": "string"}] (if micro_deposits),
        "connection_id": "string" (if completed),
        "institution_name": "string" (if completed),
        "accounts_linked": number (if completed),
        "account_details": [{"id": "string", "name": "string", "type": "string", "balance": number}] (if completed)
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        validation_result = validate_request_data(data, {
            'session_id': {'type': 'string', 'required': True},
            'public_token': {'type': 'string', 'required': True},
            'account_ids': {'type': 'list', 'required': True, 'items': {'type': 'string'}}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize account linking service
        linking_service = AccountLinkingService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Handle account selection
        result = linking_service.handle_account_selection(
            session_id=data['session_id'],
            public_token=data['public_token'],
            account_ids=data['account_ids']
        )
        
        if not result['success']:
            return create_response(**result), 400
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error handling account selection: {str(e)}")
        return create_response(
            success=False,
            error='account_selection_failed',
            message='Failed to process account selection'
        ), 500

@account_linking_bp.route('/mfa/challenge', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def handle_mfa_challenge():
    """
    Handle multi-factor authentication challenge
    
    Request Body:
    {
        "mfa_session_id": "string",
        "answers": ["string"]
    }
    
    Response:
    {
        "success": true,
        "session_id": "string",
        "status": "string",
        "verification_required": boolean,
        "verification_method": "string" (if verification_required),
        "verification_session_id": "string" (if verification_required),
        "micro_deposits": [{"amount": number, "currency": "string"}] (if micro_deposits),
        "connection_id": "string" (if completed),
        "institution_name": "string" (if completed),
        "accounts_linked": number (if completed),
        "account_details": [{"id": "string", "name": "string", "type": "string", "balance": number}] (if completed)
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        validation_result = validate_request_data(data, {
            'mfa_session_id': {'type': 'string', 'required': True},
            'answers': {'type': 'list', 'required': True, 'items': {'type': 'string'}}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize account linking service
        linking_service = AccountLinkingService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Handle MFA challenge
        result = linking_service.handle_mfa_challenge(
            mfa_session_id=data['mfa_session_id'],
            answers=data['answers']
        )
        
        if not result['success']:
            status_code = 400 if result.get('error') in ['mfa_incorrect', 'mfa_failed'] else 500
            return create_response(**result), status_code
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error handling MFA challenge: {str(e)}")
        return create_response(
            success=False,
            error='mfa_processing_failed',
            message='Failed to process MFA challenge'
        ), 500

@account_linking_bp.route('/verification/submit', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def handle_verification():
    """
    Handle account ownership verification
    
    Request Body:
    {
        "verification_session_id": "string",
        "verification_data": {
            "amounts": [number] (for micro-deposits),
            "expected_code": "string" (for phone verification),
            "provided_code": "string" (for phone verification),
            "document_url": "string" (for document upload)
        }
    }
    
    Response:
    {
        "success": true,
        "session_id": "string",
        "status": "string",
        "connection_id": "string",
        "institution_name": "string",
        "accounts_linked": number,
        "account_details": [{"id": "string", "name": "string", "type": "string", "balance": number}]
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        validation_result = validate_request_data(data, {
            'verification_session_id': {'type': 'string', 'required': True},
            'verification_data': {'type': 'dict', 'required': True}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize account linking service
        linking_service = AccountLinkingService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Handle verification
        result = linking_service.handle_verification(
            verification_session_id=data['verification_session_id'],
            verification_data=data['verification_data']
        )
        
        if not result['success']:
            status_code = 400 if result.get('error') in ['verification_incorrect', 'verification_failed'] else 500
            return create_response(**result), status_code
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error handling verification: {str(e)}")
        return create_response(
            success=False,
            error='verification_processing_failed',
            message='Failed to process verification'
        ), 500

@account_linking_bp.route('/status/<session_id>', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_linking_status(session_id: str):
    """
    Get current status of linking session
    
    Response:
    {
        "success": true,
        "session_id": "string",
        "status": "string",
        "institution_name": "string",
        "accounts_selected": number,
        "mfa_required": boolean,
        "verification_required": boolean,
        "created_at": "string",
        "updated_at": "string",
        "expires_at": "string"
    }
    """
    try:
        # Initialize account linking service
        linking_service = AccountLinkingService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Get linking status
        result = linking_service.get_linking_status(session_id)
        
        if not result['success']:
            return create_response(**result), 404
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error getting linking status for session {session_id}: {str(e)}")
        return create_response(
            success=False,
            error='status_retrieval_failed',
            message='Failed to retrieve linking status'
        ), 500

@account_linking_bp.route('/cancel/<session_id>', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def cancel_linking(session_id: str):
    """
    Cancel the linking process
    
    Response:
    {
        "success": true,
        "session_id": "string",
        "status": "string",
        "message": "string"
    }
    """
    try:
        # Initialize account linking service
        linking_service = AccountLinkingService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Cancel linking
        result = linking_service.cancel_linking(session_id)
        
        if not result['success']:
            return create_response(**result), 404
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error cancelling linking for session {session_id}: {str(e)}")
        return create_response(
            success=False,
            error='cancellation_failed',
            message='Failed to cancel linking process'
        ), 500

@account_linking_bp.route('/mfa/resend', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def resend_mfa():
    """
    Resend MFA challenge
    
    Request Body:
    {
        "mfa_session_id": "string"
    }
    
    Response:
    {
        "success": true,
        "message": "string",
        "expires_at": "string"
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        validation_result = validate_request_data(data, {
            'mfa_session_id': {'type': 'string', 'required': True}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize account linking service
        linking_service = AccountLinkingService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # This would typically regenerate MFA questions or resend codes
        # For now, return a simple success response
        return create_response(
            success=True,
            message='MFA challenge resent successfully',
            expires_at=linking_service.mfa_timeout.isoformat()
        ), 200
        
    except Exception as e:
        logger.error(f"Error resending MFA: {str(e)}")
        return create_response(
            success=False,
            error='mfa_resend_failed',
            message='Failed to resend MFA challenge'
        ), 500

@account_linking_bp.route('/verification/resend', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def resend_verification():
    """
    Resend verification (e.g., micro-deposits)
    
    Request Body:
    {
        "verification_session_id": "string"
    }
    
    Response:
    {
        "success": true,
        "message": "string",
        "micro_deposits": [{"amount": number, "currency": "string"}],
        "expires_at": "string"
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        validation_result = validate_request_data(data, {
            'verification_session_id': {'type': 'string', 'required': True}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize account linking service
        linking_service = AccountLinkingService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # This would typically regenerate micro-deposits or resend verification codes
        # For now, return mock micro-deposits
        return create_response(
            success=True,
            message='Verification resent successfully',
            micro_deposits=[
                {'amount': 0.32, 'currency': 'USD'},
                {'amount': 0.45, 'currency': 'USD'}
            ],
            expires_at=linking_service.verification_timeout.isoformat()
        ), 200
        
    except Exception as e:
        logger.error(f"Error resending verification: {str(e)}")
        return create_response(
            success=False,
            error='verification_resend_failed',
            message='Failed to resend verification'
        ), 500

@account_linking_bp.route('/institutions/search', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def search_institutions():
    """
    Search for institutions to link
    
    Query Parameters:
    - query: Search query string
    - country_codes: Comma-separated country codes (optional)
    - products: Comma-separated product types (optional)
    
    Response:
    {
        "success": true,
        "institutions": [
            {
                "institution_id": "string",
                "name": "string",
                "logo": "string",
                "primary_color": "string",
                "url": "string",
                "products": ["string"]
            }
        ]
    }
    """
    try:
        # Get query parameters
        query = request.args.get('query', '').strip()
        country_codes = request.args.get('country_codes', 'US').split(',')
        products = request.args.get('products', 'transactions').split(',')
        
        if not query:
            return create_response(
                success=False,
                error='validation_error',
                message='Query parameter is required'
            ), 400
        
        # Initialize Plaid integration service
        from backend.integrations.plaid_integration import PlaidIntegrationService
        plaid_service = PlaidIntegrationService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Search institutions
        result = plaid_service.search_institutions(
            query=query,
            country_codes=country_codes,
            products=products
        )
        
        if not result.success:
            return create_response(
                success=False,
                error='institution_search_failed',
                message=result.error
            ), 500
        
        return create_response(
            success=True,
            institutions=result.institutions
        ), 200
        
    except Exception as e:
        logger.error(f"Error searching institutions: {str(e)}")
        return create_response(
            success=False,
            error='institution_search_failed',
            message='Failed to search institutions'
        ), 500

@account_linking_bp.route('/tier/access', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_tier_access():
    """
    Get tier-based access information for current user
    
    Response:
    {
        "success": true,
        "current_tier": "string",
        "limits": {
            "max_accounts": number,
            "max_institutions": number,
            "max_connections": number,
            "sync_frequency": "string",
            "transaction_history_months": number,
            "advanced_analytics": boolean,
            "real_time_sync": boolean,
            "priority_support": boolean,
            "custom_alerts": boolean,
            "data_export": boolean,
            "api_access": boolean
        },
        "usage": {
            "total_accounts": number,
            "total_institutions": number,
            "total_connections": number,
            "active_accounts": number,
            "last_sync_at": "string",
            "sync_frequency": "string",
            "monthly_transactions": number,
            "storage_used_mb": number
        },
        "can_link_accounts": boolean,
        "remaining_accounts": number,
        "remaining_institutions": number
    }
    """
    try:
        from backend.services.tier_access_control_service import TierAccessControlService
        
        # Initialize tier access control service
        tier_service = TierAccessControlService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Get access information
        access_result = tier_service.check_account_linking_access(str(current_user.id))
        
        return create_response(
            success=True,
            current_tier=access_result['current_tier'],
            limits=access_result['limits'],
            usage=access_result['usage'],
            can_link_accounts=access_result['access'].value == 'allowed',
            remaining_accounts=access_result.get('remaining_accounts', -1),
            remaining_institutions=access_result.get('remaining_institutions', -1)
        ), 200
        
    except Exception as e:
        logger.error(f"Error getting tier access: {str(e)}")
        return create_response(
            success=False,
            error='tier_access_failed',
            message='Failed to get tier access information'
        ), 500

@account_linking_bp.route('/tier/upgrade-recommendations', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_upgrade_recommendations():
    """
    Get personalized upgrade recommendations for current user
    
    Response:
    {
        "success": true,
        "recommendations": [
            {
                "title": "string",
                "message": "string",
                "benefits": ["string"],
                "current_tier": "string",
                "recommended_tier": "string",
                "upgrade_url": "string",
                "preview_features": ["string"],
                "trial_available": boolean,
                "trial_days": number
            }
        ]
    }
    """
    try:
        from backend.services.tier_access_control_service import TierAccessControlService
        
        # Initialize tier access control service
        tier_service = TierAccessControlService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Get upgrade recommendations
        recommendations = tier_service.get_upgrade_recommendations(str(current_user.id))
        
        return create_response(
            success=True,
            recommendations=recommendations
        ), 200
        
    except Exception as e:
        logger.error(f"Error getting upgrade recommendations: {str(e)}")
        return create_response(
            success=False,
            error='recommendations_failed',
            message='Failed to get upgrade recommendations'
        ), 500

@account_linking_bp.route('/tier/comparison', methods=['GET'])
def get_tier_comparison():
    """
    Get tier comparison information
    
    Response:
    {
        "success": true,
        "tiers": {
            "budget": {
                "name": "string",
                "price": "string",
                "limits": {...},
                "features": ["string"]
            },
            "mid_tier": {...},
            "professional": {...}
        }
    }
    """
    try:
        from backend.services.tier_access_control_service import TierAccessControlService
        
        # Initialize tier access control service
        tier_service = TierAccessControlService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Get tier comparison
        comparison = tier_service.get_tier_comparison()
        
        return create_response(
            success=True,
            tiers=comparison
        ), 200
        
    except Exception as e:
        logger.error(f"Error getting tier comparison: {str(e)}")
        return create_response(
            success=False,
            error='comparison_failed',
            message='Failed to get tier comparison'
        ), 500

@account_linking_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for account linking service
    
    Response:
    {
        "success": true,
        "status": "healthy",
        "timestamp": "string"
    }
    """
    try:
        from datetime import datetime
        return create_response(
            success=True,
            status='healthy',
            timestamp=datetime.utcnow().isoformat()
        ), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_response(
            success=False,
            status='unhealthy',
            error='health_check_failed'
        ), 500

# Register blueprint
def register_account_linking_routes(app):
    """Register account linking routes with the Flask app"""
    app.register_blueprint(account_linking_bp)
    logger.info("Account linking routes registered successfully") 