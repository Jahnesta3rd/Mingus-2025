"""
Data Synchronization API Routes for MINGUS

This module provides API endpoints for comprehensive data synchronization:
- Real-time balance updates
- Daily transaction synchronization
- Historical data backfill (24 months)
- Duplicate transaction detection
- Data consistency validation
"""

import logging
from flask import Blueprint, request, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import and_

from backend.middleware.auth import require_auth
from backend.middleware.error_handling import handle_api_errors
from backend.services.data_synchronization_service import DataSynchronizationService, SyncType
from backend.utils.validation import validate_request_data
from backend.utils.response import create_response

logger = logging.getLogger(__name__)

data_sync_bp = Blueprint('data_synchronization', __name__, url_prefix='/api/data-sync')

@data_sync_bp.route('/accounts/<account_id>/sync', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def sync_account_data(account_id: str):
    """
    Synchronize account data
    
    Request Body:
    {
        "sync_type": "transactions|balance|historical|backfill|validation",
        "force_sync": boolean (optional)
    }
    
    Response:
    {
        "success": true,
        "sync_result": {
            "success": boolean,
            "sync_type": "string",
            "account_id": "string",
            "records_processed": number,
            "records_created": number,
            "records_updated": number,
            "records_skipped": number,
            "duplicates_found": number,
            "errors": ["string"],
            "duration_seconds": number,
            "started_at": "string",
            "completed_at": "string"
        }
    }
    """
    try:
        # Validate request data
        data = request.get_json() or {}
        validation_result = validate_request_data(data, {
            'sync_type': {'type': 'string', 'required': False, 'enum': ['transactions', 'balance', 'historical', 'backfill', 'validation', 'all']},
            'force_sync': {'type': 'boolean', 'required': False}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize data synchronization service
        sync_service = DataSynchronizationService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Determine sync type
        sync_type_str = data.get('sync_type', 'transactions')
        sync_type_map = {
            'transactions': SyncType.TRANSACTIONS,
            'balance': SyncType.BALANCE,
            'historical': SyncType.HISTORICAL,
            'backfill': SyncType.BACKFILL,
            'validation': SyncType.VALIDATION,
            'all': SyncType.TRANSACTIONS  # Will sync all types
        }
        
        sync_type = sync_type_map.get(sync_type_str, SyncType.TRANSACTIONS)
        force_sync = data.get('force_sync', False)
        
        # Perform synchronization
        result = sync_service.sync_account_data(
            account_id=account_id,
            sync_type=sync_type,
            force_sync=force_sync
        )
        
        return create_response(
            success=result.success,
            sync_result={
                'success': result.success,
                'sync_type': result.sync_type.value,
                'account_id': result.account_id,
                'records_processed': result.records_processed,
                'records_created': result.records_created,
                'records_updated': result.records_updated,
                'records_skipped': result.records_skipped,
                'duplicates_found': result.duplicates_found,
                'errors': result.errors,
                'duration_seconds': result.duration_seconds,
                'started_at': result.started_at.isoformat(),
                'completed_at': result.completed_at.isoformat()
            }
        ), 200 if result.success else 500
        
    except Exception as e:
        logger.error(f"Error syncing account data for {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='sync_failed',
            message='Failed to sync account data'
        ), 500

@data_sync_bp.route('/accounts/bulk/sync', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def bulk_sync_accounts():
    """
    Synchronize all user accounts
    
    Request Body:
    {
        "sync_type": "transactions|balance|historical|backfill|validation",
        "force_sync": boolean (optional)
    }
    
    Response:
    {
        "success": true,
        "results": [
            {
                "account_id": "string",
                "success": boolean,
                "records_processed": number,
                "records_created": number,
                "errors": ["string"]
            }
        ],
        "summary": {
            "total_accounts": number,
            "successful_syncs": number,
            "failed_syncs": number,
            "total_records_created": number
        }
    }
    """
    try:
        # Validate request data
        data = request.get_json() or {}
        validation_result = validate_request_data(data, {
            'sync_type': {'type': 'string', 'required': False, 'enum': ['transactions', 'balance', 'historical', 'backfill', 'validation']},
            'force_sync': {'type': 'boolean', 'required': False}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize data synchronization service
        sync_service = DataSynchronizationService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Determine sync type
        sync_type_str = data.get('sync_type', 'transactions')
        sync_type_map = {
            'transactions': SyncType.TRANSACTIONS,
            'balance': SyncType.BALANCE,
            'historical': SyncType.HISTORICAL,
            'backfill': SyncType.BACKFILL,
            'validation': SyncType.VALIDATION
        }
        
        sync_type = sync_type_map.get(sync_type_str, SyncType.TRANSACTIONS)
        force_sync = data.get('force_sync', False)
        
        # Perform bulk synchronization
        results = sync_service.sync_all_accounts(
            sync_type=sync_type,
            user_id=str(current_user.id)
        )
        
        # Process results
        processed_results = []
        total_accounts = len(results)
        successful_syncs = 0
        failed_syncs = 0
        total_records_created = 0
        
        for result in results:
            processed_results.append({
                'account_id': result.account_id,
                'success': result.success,
                'records_processed': result.records_processed,
                'records_created': result.records_created,
                'records_updated': result.records_updated,
                'records_skipped': result.records_skipped,
                'duplicates_found': result.duplicates_found,
                'errors': result.errors,
                'duration_seconds': result.duration_seconds
            })
            
            if result.success:
                successful_syncs += 1
            else:
                failed_syncs += 1
            
            total_records_created += result.records_created
        
        summary = {
            'total_accounts': total_accounts,
            'successful_syncs': successful_syncs,
            'failed_syncs': failed_syncs,
            'total_records_created': total_records_created
        }
        
        return create_response(
            success=True,
            results=processed_results,
            summary=summary
        ), 200
        
    except Exception as e:
        logger.error(f"Error performing bulk sync: {str(e)}")
        return create_response(
            success=False,
            error='bulk_sync_failed',
            message='Failed to perform bulk synchronization'
        ), 500

@data_sync_bp.route('/accounts/<account_id>/balance', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def sync_account_balance(account_id: str):
    """
    Sync account balance only
    
    Response:
    {
        "success": true,
        "balance": {
            "current_balance": number,
            "available_balance": number,
            "currency": "string",
            "last_updated": "string"
        }
    }
    """
    try:
        # Initialize data synchronization service
        sync_service = DataSynchronizationService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Sync balance
        result = sync_service.sync_account_data(
            account_id=account_id,
            sync_type=SyncType.BALANCE,
            force_sync=True
        )
        
        if not result.success:
            return create_response(
                success=False,
                error='balance_sync_failed',
                message='Failed to sync account balance'
            ), 500
        
        # Get updated balance
        from backend.models.bank_account_models import BankAccount
        account = current_app.db_session.query(BankAccount).filter(
            BankAccount.id == account_id
        ).first()
        
        if not account:
            return create_response(
                success=False,
                error='account_not_found',
                message='Account not found'
            ), 404
        
        return create_response(
            success=True,
            balance={
                'current_balance': float(account.current_balance) if account.current_balance else 0.0,
                'available_balance': float(account.available_balance) if account.available_balance else 0.0,
                'currency': account.iso_currency_code,
                'last_updated': account.last_sync_at.isoformat() if account.last_sync_at else None
            }
        ), 200
        
    except Exception as e:
        logger.error(f"Error syncing account balance for {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='balance_sync_failed',
            message='Failed to sync account balance'
        ), 500

@data_sync_bp.route('/accounts/<account_id>/transactions', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def sync_account_transactions(account_id: str):
    """
    Sync account transactions only
    
    Request Body:
    {
        "force_sync": boolean (optional)
    }
    
    Response:
    {
        "success": true,
        "transactions": {
            "records_processed": number,
            "records_created": number,
            "records_updated": number,
            "records_skipped": number,
            "duplicates_found": number,
            "duration_seconds": number
        }
    }
    """
    try:
        # Validate request data
        data = request.get_json() or {}
        validation_result = validate_request_data(data, {
            'force_sync': {'type': 'boolean', 'required': False}
        })
        
        if not validation_result['valid']:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid request data',
                details=validation_result['errors']
            ), 400
        
        # Initialize data synchronization service
        sync_service = DataSynchronizationService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Sync transactions
        result = sync_service.sync_account_data(
            account_id=account_id,
            sync_type=SyncType.TRANSACTIONS,
            force_sync=data.get('force_sync', False)
        )
        
        if not result.success:
            return create_response(
                success=False,
                error='transaction_sync_failed',
                message='Failed to sync account transactions'
            ), 500
        
        return create_response(
            success=True,
            transactions={
                'records_processed': result.records_processed,
                'records_created': result.records_created,
                'records_updated': result.records_updated,
                'records_skipped': result.records_skipped,
                'duplicates_found': result.duplicates_found,
                'duration_seconds': result.duration_seconds
            }
        ), 200
        
    except Exception as e:
        logger.error(f"Error syncing account transactions for {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='transaction_sync_failed',
            message='Failed to sync account transactions'
        ), 500

@data_sync_bp.route('/accounts/<account_id>/historical', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def sync_historical_data(account_id: str):
    """
    Sync historical data (up to 24 months)
    
    Response:
    {
        "success": true,
        "historical": {
            "records_processed": number,
            "records_created": number,
            "records_skipped": number,
            "duplicates_found": number,
            "duration_seconds": number
        }
    }
    """
    try:
        # Initialize data synchronization service
        sync_service = DataSynchronizationService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Sync historical data
        result = sync_service.sync_account_data(
            account_id=account_id,
            sync_type=SyncType.HISTORICAL,
            force_sync=True
        )
        
        if not result.success:
            return create_response(
                success=False,
                error='historical_sync_failed',
                message='Failed to sync historical data'
            ), 500
        
        return create_response(
            success=True,
            historical={
                'records_processed': result.records_processed,
                'records_created': result.records_created,
                'records_skipped': result.records_skipped,
                'duplicates_found': result.duplicates_found,
                'duration_seconds': result.duration_seconds
            }
        ), 200
        
    except Exception as e:
        logger.error(f"Error syncing historical data for {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='historical_sync_failed',
            message='Failed to sync historical data'
        ), 500

@data_sync_bp.route('/accounts/<account_id>/backfill', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def backfill_historical_data(account_id: str):
    """
    Backfill missing historical data
    
    Response:
    {
        "success": true,
        "backfill": {
            "records_processed": number,
            "records_created": number,
            "gaps_filled": number
        }
    }
    """
    try:
        # Initialize data synchronization service
        sync_service = DataSynchronizationService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Backfill historical data
        result = sync_service.sync_account_data(
            account_id=account_id,
            sync_type=SyncType.BACKFILL,
            force_sync=True
        )
        
        if not result.success:
            return create_response(
                success=False,
                error='backfill_failed',
                message='Failed to backfill historical data'
            ), 500
        
        return create_response(
            success=True,
            backfill={
                'records_processed': result.records_processed,
                'records_created': result.records_created,
                'gaps_filled': result.records_processed
            }
        ), 200
        
    except Exception as e:
        logger.error(f"Error backfilling historical data for {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='backfill_failed',
            message='Failed to backfill historical data'
        ), 500

@data_sync_bp.route('/accounts/<account_id>/validate', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def validate_data_consistency(account_id: str):
    """
    Validate data consistency
    
    Response:
    {
        "success": true,
        "validation": {
            "consistency_check": boolean,
            "issues_found": number,
            "duplicates_found": number,
            "errors": ["string"]
        }
    }
    """
    try:
        # Initialize data synchronization service
        sync_service = DataSynchronizationService(
            db_session=current_app.db_session,
            config=current_app.config
        )
        
        # Validate data consistency
        result = sync_service.sync_account_data(
            account_id=account_id,
            sync_type=SyncType.VALIDATION,
            force_sync=True
        )
        
        return create_response(
            success=True,
            validation={
                'consistency_check': result.success,
                'issues_found': len(result.errors),
                'duplicates_found': result.duplicates_found,
                'errors': result.errors
            }
        ), 200
        
    except Exception as e:
        logger.error(f"Error validating data consistency for {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='validation_failed',
            message='Failed to validate data consistency'
        ), 500

@data_sync_bp.route('/accounts/<account_id>/sync-status', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_sync_status(account_id: str):
    """
    Get synchronization status for an account
    
    Response:
    {
        "success": true,
        "sync_status": {
            "last_balance_sync": "string",
            "last_transaction_sync": "string",
            "last_historical_sync": "string",
            "last_validation": "string",
            "next_sync_due": "string",
            "sync_health": "excellent|good|fair|poor"
        }
    }
    """
    try:
        from backend.models.bank_account_models import TransactionSync
        from datetime import datetime, timedelta
        
        # Get last sync records for each type
        sync_types = ['balance', 'transactions', 'historical', 'validation']
        sync_status = {}
        
        for sync_type in sync_types:
            last_sync = current_app.db_session.query(TransactionSync).filter(
                and_(
                    TransactionSync.account_id == account_id,
                    TransactionSync.sync_type == sync_type,
                    TransactionSync.status == 'completed'
                )
            ).order_by(TransactionSync.completed_at.desc()).first()
            
            if last_sync:
                sync_status[f'last_{sync_type}_sync'] = last_sync.completed_at.isoformat()
            else:
                sync_status[f'last_{sync_type}_sync'] = None
        
        # Calculate next sync due
        last_transaction_sync = sync_status.get('last_transaction_sync')
        if last_transaction_sync:
            last_sync_time = datetime.fromisoformat(last_transaction_sync.replace('Z', '+00:00'))
            next_sync_due = last_sync_time + timedelta(hours=6)
            sync_status['next_sync_due'] = next_sync_due.isoformat()
        else:
            sync_status['next_sync_due'] = datetime.utcnow().isoformat()
        
        # Determine sync health
        if not last_transaction_sync:
            sync_health = 'poor'
        else:
            last_sync_time = datetime.fromisoformat(last_transaction_sync.replace('Z', '+00:00'))
            hours_since_sync = (datetime.utcnow() - last_sync_time).total_seconds() / 3600
            
            if hours_since_sync <= 1:
                sync_health = 'excellent'
            elif hours_since_sync <= 6:
                sync_health = 'good'
            elif hours_since_sync <= 24:
                sync_health = 'fair'
            else:
                sync_health = 'poor'
        
        sync_status['sync_health'] = sync_health
        
        return create_response(
            success=True,
            sync_status=sync_status
        ), 200
        
    except Exception as e:
        logger.error(f"Error getting sync status for {account_id}: {str(e)}")
        return create_response(
            success=False,
            error='status_fetch_failed',
            message='Failed to get sync status'
        ), 500

@data_sync_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for data synchronization service
    
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

def register_data_synchronization_routes(app):
    """Register data synchronization routes with the Flask app"""
    app.register_blueprint(data_sync_bp)
    logger.info("Data synchronization routes registered successfully") 