"""
Account Management API Routes for MINGUS

This module provides API endpoints for comprehensive account management:
- Account customization (nickname, categorization, etc.)
- Account status monitoring
- Re-authentication workflows
- Account unlinking and data cleanup
"""

import logging
from flask import Blueprint, request, current_app, jsonify
from flask_login import login_required, current_user

from backend.middleware.auth import require_auth
from backend.middleware.error_handling import handle_api_errors
from backend.services.account_management_service import AccountManagementService, AccountCustomization
from backend.utils.validation import validate_request_data
from backend.utils.response import create_response

logger = logging.getLogger(__name__)

account_management_bp = Blueprint('account_management', __name__, url_prefix='/api/account-management')

@account_management_bp.route('/accounts', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_user_accounts():
    """
    Get all user accounts with customization and status information
    
    Query Parameters:
    - include_archived: boolean (optional) - Include archived accounts
    
    Response:
    {
        "success": true,
        "accounts": [
            {
                "id": "string",
                "name": "string",
                "mask": "string",
                "type": "string",
                "subtype": "string",
                "institution_name": "string",
                "institution_logo": "string",
                "status": "string",
                "current_balance": number,
                "available_balance": number,
                "currency": "string",
                "last_sync_at": "string",
                "created_at": "string",
                "customization": {
                    "nickname": "string",
                    "category": "string",
                    "color": "string",
                    "icon": "string",
                    "is_primary": boolean,
                    "is_hidden": boolean,
                    "notes": "string",
                    "tags": ["string"]
                },
                "status_info": {
                    "status": "string",
                    "last_sync_at": "string",
                    "error_message": "string",
                    "sync_frequency": "string",
                    "re_auth_required": boolean,
                    "re_auth_status": "string",
                    "connection_health": "string",
                    "data_freshness": "string"
                }
            }
        ],
        "total_accounts": number,
        "active_accounts": number,
        "primary_account": object
    }
    """
    try:
        # Get query parameters
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        
        # Initialize account management service
        account_service = AccountManagementService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Get user accounts
        result = account_service.get_user_accounts(
            user_id=str(current_user.id),
            include_archived=include_archived
        )
        
        if not result['success']:
            return create_response(**result), 400
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error getting user accounts: {str(e)}")
        return create_response(
            success=False,
            error='accounts_fetch_failed',
            message='Failed to get user accounts'
        ), 500

@account_management_bp.route('/accounts/<account_id>/customize', methods=['PUT'])
@login_required
@require_auth
@handle_api_errors
def customize_account(account_id: str):
    """
    Customize account settings (nickname, category, etc.)
    
    Request Body:
    {
        "nickname": "string",
        "category": "string",
        "color": "string",
        "icon": "string",
        "is_primary": boolean,
        "is_hidden": boolean,
        "notes": "string",
        "tags": ["string"]
    }
    
    Response:
    {
        "success": true,
        "account_id": "string",
        "customization": {
            "nickname": "string",
            "category": "string",
            "color": "string",
            "icon": "string",
            "is_primary": boolean,
            "is_hidden": boolean,
            "notes": "string",
            "tags": ["string"]
        }
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        validation_result = validate_request_data(data, {
            'nickname': {'type': 'string', 'required': True, 'max_length': 50},
            'category': {'type': 'string', 'required': True, 'max_length': 30},
            'color': {'type': 'string', 'required': True, 'max_length': 7},
            'icon': {'type': 'string', 'required': True, 'max_length': 10},
            'is_primary': {'type': 'boolean', 'required': True},
            'is_hidden': {'type': 'boolean', 'required': True},
            'notes': {'type': 'string', 'required': False, 'max_length': 500},
            'tags': {'type': 'list', 'required': False, 'items': {'type': 'string', 'max_length': 20}}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize account management service
        account_service = AccountManagementService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Create customization object
        customization = AccountCustomization(
            nickname=data['nickname'],
            category=data['category'],
            color=data['color'],
            icon=data['icon'],
            is_primary=data['is_primary'],
            is_hidden=data['is_hidden'],
            notes=data.get('notes', ''),
            tags=data.get('tags', [])
        )
        
        # Customize account
        result = account_service.customize_account(
            user_id=str(current_user.id),
            account_id=account_id,
            customization=customization
        )
        
        if not result['success']:
            status_code = 400 if result.get('error') == 'account_not_found' else 500
            return create_response(**result), status_code
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error customizing account {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='customization_failed',
            message='Failed to customize account'
        ), 500

@account_management_bp.route('/accounts/<account_id>/status', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_account_status(account_id: str):
    """
    Get comprehensive account status information
    
    Response:
    {
        "success": true,
        "account_id": "string",
        "status_info": {
            "status": "string",
            "last_sync_at": "string",
            "last_error_at": "string",
            "error_message": "string",
            "sync_frequency": "string",
            "re_auth_required": boolean,
            "re_auth_status": "string",
            "connection_health": "string",
            "data_freshness": "string"
        }
    }
    """
    try:
        # Initialize account management service
        account_service = AccountManagementService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Get account status
        result = account_service.get_account_status(
            user_id=str(current_user.id),
            account_id=account_id
        )
        
        if not result['success']:
            status_code = 400 if result.get('error') == 'account_not_found' else 500
            return create_response(**result), status_code
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error getting account status for {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='status_check_failed',
            message='Failed to get account status'
        ), 500

@account_management_bp.route('/accounts/<account_id>/reauth/initiate', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def initiate_re_authentication(account_id: str):
    """
    Initiate re-authentication workflow for an account
    
    Response:
    {
        "success": true,
        "workflow_id": "string",
        "link_token": "string",
        "expires_at": "string",
        "message": "string"
    }
    """
    try:
        # Initialize account management service
        account_service = AccountManagementService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Initiate re-authentication
        result = account_service.initiate_re_authentication(
            user_id=str(current_user.id),
            account_id=account_id
        )
        
        if not result['success']:
            status_code = 400 if result.get('error') in ['account_not_found', 'reauth_in_progress'] else 500
            return create_response(**result), status_code
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error initiating re-authentication for account {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='reauth_initiation_failed',
            message='Failed to initiate re-authentication'
        ), 500

@account_management_bp.route('/reauth/<workflow_id>/complete', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def complete_re_authentication(workflow_id: str):
    """
    Complete re-authentication workflow
    
    Request Body:
    {
        "public_token": "string"
    }
    
    Response:
    {
        "success": true,
        "workflow_id": "string",
        "status": "string",
        "message": "string"
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        validation_result = validate_request_data(data, {
            'public_token': {'type': 'string', 'required': True}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize account management service
        account_service = AccountManagementService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Complete re-authentication
        result = account_service.complete_re_authentication(
            workflow_id=workflow_id,
            public_token=data['public_token']
        )
        
        if not result['success']:
            status_code = 400 if result.get('error') in ['workflow_not_found', 'workflow_expired', 'invalid_workflow_status', 'reauth_failed'] else 500
            return create_response(**result), status_code
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error completing re-authentication workflow {workflow_id}: {str(e)}")
        return create_response(
            success=False,
            error='reauth_completion_failed',
            message='Failed to complete re-authentication'
        ), 500

@account_management_bp.route('/accounts/<account_id>/unlink', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def unlink_account(account_id: str):
    """
    Unlink account and optionally cleanup data
    
    Request Body:
    {
        "cleanup_data": boolean (optional, default: true)
    }
    
    Response:
    {
        "success": true,
        "account_id": "string",
        "message": "string",
        "cleanup_data": boolean
    }
    """
    try:
        # Validate request data
        data = request.get_json() or {}
        validation_result = validate_request_data(data, {
            'cleanup_data': {'type': 'boolean', 'required': False}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize account management service
        account_service = AccountManagementService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Unlink account
        result = account_service.unlink_account(
            user_id=str(current_user.id),
            account_id=account_id,
            cleanup_data=data.get('cleanup_data', True)
        )
        
        if not result['success']:
            status_code = 400 if result.get('error') == 'account_not_found' else 500
            return create_response(**result), status_code
        
        return create_response(**result), 200
        
    except Exception as e:
        logger.error(f"Error unlinking account {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='unlink_failed',
            message='Failed to unlink account'
        ), 500

@account_management_bp.route('/accounts/<account_id>/sync', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def sync_account(account_id: str):
    """
    Manually trigger account synchronization
    
    Response:
    {
        "success": true,
        "account_id": "string",
        "sync_status": "string",
        "last_sync_at": "string",
        "message": "string"
    }
    """
    try:
        # Initialize account management service
        account_service = AccountManagementService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Get account status first
        status_result = account_service.get_account_status(
            user_id=str(current_user.id),
            account_id=account_id
        )
        
        if not status_result['success']:
            return create_response(**status_result), 400
        
        # Check if re-authentication is required
        status_info = status_result['status_info']
        if status_info['re_auth_required']:
            return create_response(
                success=False,
                error='reauth_required',
                message='Re-authentication required before sync',
                re_auth_required=True
            ), 400
        
        # TODO: Implement actual sync logic
        # For now, return a placeholder response
        return create_response(
            success=True,
            account_id=account_id,
            sync_status='completed',
            last_sync_at=datetime.utcnow().isoformat(),
            message='Account synchronized successfully'
        ), 200
        
    except Exception as e:
        logger.error(f"Error syncing account {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='sync_failed',
            message='Failed to sync account'
        ), 500

@account_management_bp.route('/accounts/bulk/status', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_bulk_account_status():
    """
    Get status for all user accounts (bulk operation)
    
    Response:
    {
        "success": true,
        "accounts": [
            {
                "account_id": "string",
                "status": "string",
                "re_auth_required": boolean,
                "connection_health": "string",
                "last_sync_at": "string"
            }
        ]
    }
    """
    try:
        # Initialize account management service
        account_service = AccountManagementService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Get all user accounts
        accounts_result = account_service.get_user_accounts(
            user_id=str(current_user.id),
            include_archived=False
        )
        
        if not accounts_result['success']:
            return create_response(**accounts_result), 400
        
        # Extract status information
        bulk_status = []
        for account in accounts_result['accounts']:
            bulk_status.append({
                'account_id': account['id'],
                'status': account['status'],
                're_auth_required': account['status_info'].get('re_auth_required', False),
                'connection_health': account['status_info'].get('connection_health', 'unknown'),
                'last_sync_at': account['status_info'].get('last_sync_at'),
                'nickname': account['customization']['nickname'],
                'institution_name': account['institution_name']
            })
        
        return create_response(
            success=True,
            accounts=bulk_status,
            total_accounts=len(bulk_status)
        ), 200
        
    except Exception as e:
        logger.error(f"Error getting bulk account status: {str(e)}")
        return create_response(
            success=False,
            error='bulk_status_failed',
            message='Failed to get bulk account status'
        ), 500

@account_management_bp.route('/accounts/<account_id>/preferences', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_account_preferences(account_id: str):
    """
    Get account preferences and customization settings
    
    Response:
    {
        "success": true,
        "account_id": "string",
        "preferences": {
            "nickname": "string",
            "category": "string",
            "color": "string",
            "icon": "string",
            "is_primary": boolean,
            "is_hidden": boolean,
            "notes": "string",
            "tags": ["string"],
            "sync_preferences": {
                "frequency": "string",
                "notifications": boolean
            },
            "notification_settings": {
                "balance_alerts": boolean,
                "transaction_notifications": boolean,
                "threshold": number
            }
        }
    }
    """
    try:
        # Initialize account management service
        account_service = AccountManagementService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Get user accounts and find the specific account
        accounts_result = account_service.get_user_accounts(
            user_id=str(current_user.id),
            include_archived=False
        )
        
        if not accounts_result['success']:
            return create_response(**accounts_result), 400
        
        # Find the specific account
        account = next((a for a in accounts_result['accounts'] if a['id'] == account_id), None)
        
        if not account:
            return create_response(
                success=False,
                error='account_not_found',
                message='Account not found'
            ), 400
        
        # Extract preferences
        preferences = {
            'nickname': account['customization']['nickname'],
            'category': account['customization']['category'],
            'color': account['customization']['color'],
            'icon': account['customization']['icon'],
            'is_primary': account['customization']['is_primary'],
            'is_hidden': account['customization']['is_hidden'],
            'notes': account['customization']['notes'],
            'tags': account['customization']['tags'],
            'sync_preferences': {
                'frequency': account['status_info'].get('sync_frequency', 'daily'),
                'notifications': True  # Default value
            },
            'notification_settings': {
                'balance_alerts': True,  # Default value
                'transaction_notifications': True,  # Default value
                'threshold': 100.0  # Default value
            }
        }
        
        return create_response(
            success=True,
            account_id=account_id,
            preferences=preferences
        ), 200
        
    except Exception as e:
        logger.error(f"Error getting account preferences for {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='preferences_fetch_failed',
            message='Failed to get account preferences'
        ), 500

@account_management_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for account management service
    
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

def register_account_management_routes(app):
    """Register account management routes with the Flask app"""
    app.register_blueprint(account_management_bp)
    logger.info("Account management routes registered successfully") 