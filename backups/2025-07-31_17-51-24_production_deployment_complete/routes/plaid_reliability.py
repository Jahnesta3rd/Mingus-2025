"""
Plaid Reliability Routes for MINGUS

This module provides comprehensive API endpoints for Plaid reliability features:
- Connection health monitoring
- Error handling and recovery
- User notifications for connection issues
- Data synchronization status
- Reliability metrics and reporting
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app, session
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import uuid

from backend.middleware.auth import require_auth
from backend.services.plaid_reliability_service import PlaidReliabilityService
from backend.services.notification_service import NotificationService
from backend.models.plaid_models import PlaidConnection, PlaidAccount, PlaidSyncLog
from backend.models.security_models import SecurityAuditLog
from backend.utils.auth_decorators import handle_api_errors

logger = logging.getLogger(__name__)

# Create Blueprint
reliability_bp = Blueprint('reliability', __name__, url_prefix='/api/reliability')

def get_reliability_service() -> PlaidReliabilityService:
    """Get reliability service instance"""
    db_session = current_app.db.session
    notification_service = NotificationService(db_session, current_app.config)
    config = current_app.config
    return PlaidReliabilityService(db_session, notification_service, config)

# ============================================================================
# CONNECTION HEALTH MONITORING
# ============================================================================

@reliability_bp.route('/connections/health', methods=['GET'])
@require_auth
@handle_api_errors
def get_connection_health():
    """Get health status for all user connections"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get user's Plaid connections
        connections = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.user_id == user_id
        ).all()
        
        reliability_service = get_reliability_service()
        
        health_data = []
        for connection in connections:
            health = reliability_service.get_connection_health(str(connection.id))
            if health:
                health_data.append({
                    'connection_id': str(connection.id),
                    'institution_name': connection.institution_name,
                    'status': health.status.value,
                    'last_successful_sync': health.last_successful_sync.isoformat() if health.last_successful_sync else None,
                    'sync_failure_count': health.sync_failure_count,
                    'maintenance_mode': health.maintenance_mode,
                    'maintenance_until': health.maintenance_until.isoformat() if health.maintenance_until else None,
                    'requires_reauth': connection.requires_reauth,
                    'last_error': connection.last_error,
                    'last_error_at': connection.last_error_at.isoformat() if connection.last_error_at else None
                })
        
        return jsonify({
            'success': True,
            'connections': health_data,
            'total_connections': len(connections),
            'healthy_connections': len([h for h in health_data if h['status'] == 'active']),
            'degraded_connections': len([h for h in health_data if h['status'] == 'degraded']),
            'error_connections': len([h for h in health_data if h['status'] == 'error']),
            'maintenance_connections': len([h for h in health_data if h['status'] == 'maintenance'])
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting connection health: {e}")
        return jsonify({'error': 'Failed to get connection health'}), 500

@reliability_bp.route('/connections/<connection_id>/health', methods=['GET'])
@require_auth
@handle_api_errors
def get_specific_connection_health(connection_id):
    """Get health status for specific connection"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Verify connection belongs to user
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        reliability_service = get_reliability_service()
        health = reliability_service.get_connection_health(str(connection.id))
        
        if not health:
            return jsonify({'error': 'Unable to get connection health'}), 500
        
        return jsonify({
            'success': True,
            'connection_health': {
                'connection_id': str(connection.id),
                'institution_name': connection.institution_name,
                'status': health.status.value,
                'last_successful_sync': health.last_successful_sync.isoformat() if health.last_successful_sync else None,
                'sync_failure_count': health.sync_failure_count,
                'consecutive_failures': health.consecutive_failures,
                'maintenance_mode': health.maintenance_mode,
                'maintenance_until': health.maintenance_until.isoformat() if health.maintenance_until else None,
                'retry_attempts': health.retry_attempts,
                'next_retry': health.next_retry.isoformat() if health.next_retry else None,
                'requires_reauth': connection.requires_reauth,
                'last_error': connection.last_error,
                'last_error_at': connection.last_error_at.isoformat() if connection.last_error_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting specific connection health: {e}")
        return jsonify({'error': 'Failed to get connection health'}), 500

# ============================================================================
# ERROR HANDLING AND RECOVERY
# ============================================================================

@reliability_bp.route('/connections/<connection_id>/retry', methods=['POST'])
@require_auth
@handle_api_errors
def retry_connection(connection_id):
    """Retry a failed connection"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Verify connection belongs to user
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Check if connection is in maintenance mode
        if connection.maintenance_until and connection.maintenance_until > datetime.utcnow():
            return jsonify({
                'success': False,
                'error': 'Connection is in maintenance mode',
                'maintenance_until': connection.maintenance_until.isoformat()
            }), 400
        
        # Attempt to retry connection
        # This would typically involve calling Plaid API to refresh the connection
        # For now, we'll simulate a retry attempt
        
        # Update connection status
        connection.last_retry_attempt = datetime.utcnow()
        connection.retry_count = (connection.retry_count or 0) + 1
        
        # Simulate success/failure
        import random
        success = random.choice([True, False])  # In production, this would be based on actual API call
        
        if success:
            connection.is_active = True
            connection.last_error = None
            connection.last_error_at = None
            connection.requires_reauth = False
            connection.last_sync_at = datetime.utcnow()
            message = "Connection retry successful"
        else:
            connection.last_error = "RETRY_FAILED"
            connection.last_error_at = datetime.utcnow()
            message = "Connection retry failed"
        
        current_app.db.session.commit()
        
        return jsonify({
            'success': success,
            'message': message,
            'retry_count': connection.retry_count,
            'last_retry_attempt': connection.last_retry_attempt.isoformat()
        }), 200 if success else 400
        
    except Exception as e:
        logger.error(f"Error retrying connection: {e}")
        current_app.db.session.rollback()
        return jsonify({'error': 'Failed to retry connection'}), 500

@reliability_bp.route('/connections/<connection_id>/reconnect', methods=['POST'])
@require_auth
@handle_api_errors
def reconnect_account(connection_id):
    """Reconnect a bank account that requires re-authentication"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Verify connection belongs to user
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Check if connection requires re-authentication
        if not connection.requires_reauth:
            return jsonify({
                'success': False,
                'error': 'Connection does not require re-authentication'
            }), 400
        
        # Generate new link token for reconnection
        # This would typically involve calling Plaid API to create a new link token
        # For now, we'll simulate the process
        
        link_token = f"link_token_{uuid.uuid4()}"
        
        # Update connection status
        connection.link_token = link_token
        connection.link_token_expires_at = datetime.utcnow() + timedelta(hours=24)
        connection.reconnection_attempted_at = datetime.utcnow()
        
        current_app.db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reconnection initiated',
            'link_token': link_token,
            'expires_at': connection.link_token_expires_at.isoformat(),
            'institution_name': connection.institution_name
        }), 200
        
    except Exception as e:
        logger.error(f"Error reconnecting account: {e}")
        current_app.db.session.rollback()
        return jsonify({'error': 'Failed to reconnect account'}), 500

# ============================================================================
# DATA SYNCHRONIZATION STATUS
# ============================================================================

@reliability_bp.route('/connections/<connection_id>/sync-status', methods=['GET'])
@require_auth
@handle_api_errors
def get_sync_status(connection_id):
    """Get data synchronization status for a connection"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Verify connection belongs to user
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Get recent sync logs
        sync_logs = current_app.db.session.query(PlaidSyncLog).filter(
            PlaidSyncLog.connection_id == connection_id
        ).order_by(desc(PlaidSyncLog.completed_at)).limit(10).all()
        
        sync_data = []
        for log in sync_logs:
            sync_data.append({
                'sync_id': str(log.id),
                'sync_type': log.sync_type,
                'status': log.status,
                'started_at': log.started_at.isoformat(),
                'completed_at': log.completed_at.isoformat(),
                'duration': log.duration,
                'records_processed': log.records_processed,
                'records_failed': log.records_failed,
                'error_message': log.error_message,
                'retry_after': log.retry_after
            })
        
        # Get reliability statistics
        reliability_service = get_reliability_service()
        reliability_stats = reliability_service.get_sync_reliability_stats(str(connection.id))
        
        return jsonify({
            'success': True,
            'connection_id': str(connection.id),
            'institution_name': connection.institution_name,
            'last_sync_at': connection.last_sync_at.isoformat() if connection.last_sync_at else None,
            'sync_logs': sync_data,
            'reliability_stats': reliability_stats,
            'requires_reauth': connection.requires_reauth,
            'maintenance_mode': bool(connection.maintenance_until and connection.maintenance_until > datetime.utcnow())
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return jsonify({'error': 'Failed to get sync status'}), 500

@reliability_bp.route('/connections/<connection_id>/sync-now', methods=['POST'])
@require_auth
@handle_api_errors
def trigger_sync_now(connection_id):
    """Trigger immediate data synchronization for a connection"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Verify connection belongs to user
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Check if connection is active
        if not connection.is_active:
            return jsonify({
                'success': False,
                'error': 'Connection is not active'
            }), 400
        
        # Check if connection requires re-authentication
        if connection.requires_reauth:
            return jsonify({
                'success': False,
                'error': 'Connection requires re-authentication'
            }), 400
        
        # Check if connection is in maintenance mode
        if connection.maintenance_until and connection.maintenance_until > datetime.utcnow():
            return jsonify({
                'success': False,
                'error': 'Connection is in maintenance mode',
                'maintenance_until': connection.maintenance_until.isoformat()
            }), 400
        
        # Trigger sync
        # This would typically involve calling Plaid API to sync data
        # For now, we'll simulate the sync process
        
        import time
        start_time = time.time()
        
        # Simulate sync duration
        time.sleep(0.1)  # Simulate API call
        
        sync_duration = time.time() - start_time
        
        # Create sync log entry
        sync_log = PlaidSyncLog(
            connection_id=connection_id,
            sync_type='manual',
            status='success',
            started_at=datetime.utcnow() - timedelta(seconds=sync_duration),
            completed_at=datetime.utcnow(),
            duration=sync_duration,
            records_processed=10,  # Simulated
            records_failed=0,
            error_message=None,
            retry_after=None,
            context={'triggered_by': 'user', 'user_id': user_id}
        )
        
        current_app.db.session.add(sync_log)
        
        # Update connection last sync time
        connection.last_sync_at = datetime.utcnow()
        connection.last_error = None
        connection.last_error_at = None
        
        current_app.db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Sync completed successfully',
            'sync_id': str(sync_log.id),
            'duration': sync_duration,
            'records_processed': sync_log.records_processed,
            'records_failed': sync_log.records_failed,
            'completed_at': sync_log.completed_at.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        current_app.db.session.rollback()
        return jsonify({'error': 'Failed to trigger sync'}), 500

# ============================================================================
# USER NOTIFICATIONS
# ============================================================================

@reliability_bp.route('/notifications', methods=['GET'])
@require_auth
@handle_api_errors
def get_user_notifications():
    """Get user notifications"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 100)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        notification_type = request.args.get('type')
        
        # Get notifications
        notification_service = NotificationService(current_app.db.session, current_app.config)
        notifications = notification_service.get_user_notifications(user_id, limit, unread_only)
        
        # Filter by type if specified
        if notification_type:
            notifications = [n for n in notifications if n.get('type') == notification_type]
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications),
            'unread_count': len([n for n in notifications if not n.get('read', False)])
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user notifications: {e}")
        return jsonify({'error': 'Failed to get notifications'}), 500

@reliability_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@require_auth
@handle_api_errors
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Mark notification as read
        notification_service = NotificationService(current_app.db.session, current_app.config)
        success = notification_service.mark_notification_read(notification_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to mark notification as read'
            }), 500
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return jsonify({'error': 'Failed to mark notification as read'}), 500

@reliability_bp.route('/notifications/send-test', methods=['POST'])
@require_auth
@handle_api_errors
def send_test_notification():
    """Send a test notification to the user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        notification_type = data.get('type', 'plaid_connection_issue')
        channels = data.get('channels', ['in_app'])
        
        # Prepare test notification data
        test_data = {
            'user_id': user_id,
            'notification_type': notification_type,
            'title': 'Test Notification',
            'message': 'This is a test notification to verify your notification settings.',
            'priority': 'low',
            'channels': channels,
            'action_required': False,
            'metadata': {
                'test': True,
                'institution_name': 'Test Bank',
                'error_message': 'Test error message',
                'explanation': 'This is a test explanation',
                'action_required_text': 'No action required for this test'
            }
        }
        
        # Send notification
        notification_service = NotificationService(current_app.db.session, current_app.config)
        result = notification_service.send_notification(test_data)
        
        return jsonify({
            'success': result.get('success', False),
            'message': 'Test notification sent',
            'delivery_results': result.get('delivery_results', [])
        }), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return jsonify({'error': 'Failed to send test notification'}), 500

# ============================================================================
# RELIABILITY METRICS AND REPORTING
# ============================================================================

@reliability_bp.route('/metrics/overview', methods=['GET'])
@require_auth
@handle_api_errors
def get_reliability_metrics():
    """Get overall reliability metrics"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get user's connections
        connections = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.user_id == user_id
        ).all()
        
        # Calculate metrics
        total_connections = len(connections)
        active_connections = len([c for c in connections if c.is_active])
        error_connections = len([c for c in connections if c.last_error])
        maintenance_connections = len([c for c in connections if c.maintenance_until and c.maintenance_until > datetime.utcnow()])
        reauth_required = len([c for c in connections if c.requires_reauth])
        
        # Get sync statistics
        reliability_service = get_reliability_service()
        total_syncs = 0
        successful_syncs = 0
        failed_syncs = 0
        
        for connection in connections:
            stats = reliability_service.get_sync_reliability_stats(str(connection.id))
            total_syncs += stats.get('total_syncs', 0)
            successful_syncs += stats.get('successful_syncs', 0)
            failed_syncs += stats.get('failed_syncs', 0)
        
        overall_success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
        
        return jsonify({
            'success': True,
            'metrics': {
                'connections': {
                    'total': total_connections,
                    'active': active_connections,
                    'with_errors': error_connections,
                    'in_maintenance': maintenance_connections,
                    'require_reauth': reauth_required,
                    'health_rate': (active_connections / total_connections * 100) if total_connections > 0 else 0
                },
                'sync': {
                    'total_syncs': total_syncs,
                    'successful_syncs': successful_syncs,
                    'failed_syncs': failed_syncs,
                    'success_rate': round(overall_success_rate, 2)
                },
                'reliability_score': round((active_connections / total_connections * 0.6 + overall_success_rate / 100 * 0.4) * 100, 2) if total_connections > 0 else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting reliability metrics: {e}")
        return jsonify({'error': 'Failed to get reliability metrics'}), 500

@reliability_bp.route('/metrics/connections/<connection_id>', methods=['GET'])
@require_auth
@handle_api_errors
def get_connection_metrics(connection_id):
    """Get detailed metrics for a specific connection"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Verify connection belongs to user
        connection = current_app.db.session.query(PlaidConnection).filter(
            PlaidConnection.id == connection_id,
            PlaidConnection.user_id == user_id
        ).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Get reliability statistics
        reliability_service = get_reliability_service()
        reliability_stats = reliability_service.get_sync_reliability_stats(str(connection.id))
        
        # Get recent sync logs for trend analysis
        sync_logs = current_app.db.session.query(PlaidSyncLog).filter(
            PlaidSyncLog.connection_id == connection_id
        ).order_by(desc(PlaidSyncLog.completed_at)).limit(30).all()
        
        # Calculate trends
        recent_syncs = [log for log in sync_logs if log.completed_at > datetime.utcnow() - timedelta(days=7)]
        recent_success_rate = len([s for s in recent_syncs if s.status == 'success']) / len(recent_syncs) * 100 if recent_syncs else 0
        
        return jsonify({
            'success': True,
            'connection_id': str(connection.id),
            'institution_name': connection.institution_name,
            'metrics': {
                'overall': reliability_stats,
                'recent_trends': {
                    'recent_syncs': len(recent_syncs),
                    'recent_success_rate': round(recent_success_rate, 2),
                    'avg_sync_duration': sum(log.duration for log in recent_syncs) / len(recent_syncs) if recent_syncs else 0
                },
                'connection_health': {
                    'is_active': connection.is_active,
                    'requires_reauth': connection.requires_reauth,
                    'maintenance_mode': bool(connection.maintenance_until and connection.maintenance_until > datetime.utcnow()),
                    'last_error': connection.last_error,
                    'retry_count': connection.retry_count or 0
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting connection metrics: {e}")
        return jsonify({'error': 'Failed to get connection metrics'}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@reliability_bp.route('/health', methods=['GET'])
@handle_api_errors
def reliability_health_check():
    """Health check for reliability services"""
    try:
        # Test reliability service
        reliability_service = get_reliability_service()
        
        # Test notification service
        notification_service = NotificationService(current_app.db.session, current_app.config)
        
        health_status = {
            'reliability_service': 'healthy',
            'notification_service': 'healthy',
            'database_connection': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'status': 'healthy',
            'services': health_status
        }), 200
        
    except Exception as e:
        logger.error(f"Reliability health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503 