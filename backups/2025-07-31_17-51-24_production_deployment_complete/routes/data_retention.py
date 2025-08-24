"""
Data Retention and Deletion API Routes

This module provides comprehensive API routes for data retention and deletion including
user-requested data deletion, legal hold management, data portability requests, and
retention policy management.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.security.data_retention_service import (
    DataRetentionService, RetentionPolicyType, DeletionType, 
    LegalHoldStatus, DataPortabilityFormat
)
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService
from backend.security.data_protection_service import DataProtectionService
from backend.middleware.auth import require_auth
from backend.utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
data_retention_bp = Blueprint('data_retention', __name__, url_prefix='/api/data-retention')


@data_retention_bp.route('/deletion-request', methods=['POST'])
@login_required
@require_auth
def request_data_deletion():
    """Request data deletion for the current user"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        data_categories = data.get('data_categories', [])
        reason = data.get('reason', 'User requested deletion')
        scheduled_at = data.get('scheduled_at')
        
        if not data_categories:
            return error_response("Data categories are required", 400)
        
        # Parse scheduled_at if provided
        scheduled_datetime = None
        if scheduled_at:
            try:
                scheduled_datetime = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            except ValueError:
                return error_response("Invalid scheduled_at format", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Request data deletion
        request_id = retention_service.request_data_deletion(
            user_id=current_user.id,
            data_categories=data_categories,
            reason=reason,
            scheduled_at=scheduled_datetime
        )
        
        return success_response({
            'request_id': request_id,
            'status': 'pending',
            'message': 'Data deletion request submitted successfully'
        }, "Data deletion request submitted successfully")
        
    except Exception as e:
        logger.error(f"Error requesting data deletion: {e}")
        return error_response("Failed to submit deletion request", 500)


@data_retention_bp.route('/deletion-requests', methods=['GET'])
@login_required
@require_auth
def get_deletion_requests():
    """Get user's deletion requests"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Get user's deletion requests
        user_requests = [
            {
                'request_id': req.request_id,
                'deletion_type': req.deletion_type.value,
                'data_categories': req.data_categories,
                'reason': req.reason,
                'status': req.status,
                'requested_at': req.requested_at.isoformat(),
                'scheduled_at': req.scheduled_at.isoformat() if req.scheduled_at else None,
                'completed_at': req.completed_at.isoformat() if req.completed_at else None,
                'legal_hold_active': req.legal_hold_active
            }
            for req in retention_service.deletion_requests.values()
            if req.user_id == current_user.id
        ]
        
        return success_response({
            'deletion_requests': user_requests,
            'total_requests': len(user_requests)
        }, "Deletion requests retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting deletion requests: {e}")
        return error_response("Failed to retrieve deletion requests", 500)


@data_retention_bp.route('/deletion-request/<request_id>', methods=['GET'])
@login_required
@require_auth
def get_deletion_request(request_id):
    """Get specific deletion request details"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Get deletion request
        deletion_request = retention_service.deletion_requests.get(request_id)
        if not deletion_request:
            return error_response("Deletion request not found", 404)
        
        if deletion_request.user_id != current_user.id:
            return error_response("Access denied", 403)
        
        return success_response({
            'request_id': deletion_request.request_id,
            'deletion_type': deletion_request.deletion_type.value,
            'data_categories': deletion_request.data_categories,
            'reason': deletion_request.reason,
            'status': deletion_request.status,
            'requested_at': deletion_request.requested_at.isoformat(),
            'scheduled_at': deletion_request.scheduled_at.isoformat() if deletion_request.scheduled_at else None,
            'completed_at': deletion_request.completed_at.isoformat() if deletion_request.completed_at else None,
            'legal_hold_active': deletion_request.legal_hold_active,
            'deletion_method': deletion_request.deletion_method,
            'metadata': deletion_request.metadata
        }, "Deletion request details retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting deletion request: {e}")
        return error_response("Failed to retrieve deletion request", 500)


@data_retention_bp.route('/deletion-request/<request_id>/cancel', methods=['POST'])
@login_required
@require_auth
def cancel_deletion_request(request_id):
    """Cancel a deletion request"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Get deletion request
        deletion_request = retention_service.deletion_requests.get(request_id)
        if not deletion_request:
            return error_response("Deletion request not found", 404)
        
        if deletion_request.user_id != current_user.id:
            return error_response("Access denied", 403)
        
        if deletion_request.status != 'pending':
            return error_response("Cannot cancel non-pending request", 400)
        
        # Cancel request
        deletion_request.status = 'cancelled'
        deletion_request.metadata['cancelled_by'] = current_user.id
        deletion_request.metadata['cancelled_at'] = datetime.utcnow().isoformat()
        
        return success_response({
            'request_id': request_id,
            'status': 'cancelled',
            'message': 'Deletion request cancelled successfully'
        }, "Deletion request cancelled successfully")
        
    except Exception as e:
        logger.error(f"Error cancelling deletion request: {e}")
        return error_response("Failed to cancel deletion request", 500)


@data_retention_bp.route('/legal-hold', methods=['POST'])
@login_required
@require_auth
def create_legal_hold():
    """Create a legal hold (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        user_id = data.get('user_id')
        case_number = data.get('case_number')
        case_description = data.get('case_description')
        legal_authority = data.get('legal_authority')
        contact_person = data.get('contact_person')
        contact_email = data.get('contact_email')
        affected_data_types = data.get('affected_data_types', [])
        hold_end_date = data.get('hold_end_date')
        
        # Validate required fields
        required_fields = ['user_id', 'case_number', 'case_description', 'legal_authority', 'contact_person', 'contact_email']
        for field in required_fields:
            if not data.get(field):
                return error_response(f"{field} is required", 400)
        
        # Parse hold_end_date if provided
        hold_end_datetime = None
        if hold_end_date:
            try:
                hold_end_datetime = datetime.fromisoformat(hold_end_date.replace('Z', '+00:00'))
            except ValueError:
                return error_response("Invalid hold_end_date format", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Create legal hold
        hold_id = retention_service.create_legal_hold(
            user_id=user_id,
            case_number=case_number,
            case_description=case_description,
            legal_authority=legal_authority,
            contact_person=contact_person,
            contact_email=contact_email,
            affected_data_types=affected_data_types,
            hold_end_date=hold_end_datetime
        )
        
        return success_response({
            'hold_id': hold_id,
            'status': 'active',
            'message': 'Legal hold created successfully'
        }, "Legal hold created successfully")
        
    except Exception as e:
        logger.error(f"Error creating legal hold: {e}")
        return error_response("Failed to create legal hold", 500)


@data_retention_bp.route('/legal-hold/<hold_id>/release', methods=['POST'])
@login_required
@require_auth
def release_legal_hold(hold_id):
    """Release a legal hold (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        release_reason = data.get('release_reason', 'Admin released hold')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Release legal hold
        success = retention_service.release_legal_hold(
            hold_id=hold_id,
            released_by=current_user.id,
            release_reason=release_reason
        )
        
        if not success:
            return error_response("Legal hold not found or already released", 404)
        
        return success_response({
            'hold_id': hold_id,
            'status': 'released',
            'message': 'Legal hold released successfully'
        }, "Legal hold released successfully")
        
    except Exception as e:
        logger.error(f"Error releasing legal hold: {e}")
        return error_response("Failed to release legal hold", 500)


@data_retention_bp.route('/legal-holds', methods=['GET'])
@login_required
@require_auth
def get_legal_holds():
    """Get legal holds (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Get legal holds
        legal_holds = [
            {
                'hold_id': hold.hold_id,
                'user_id': hold.user_id,
                'case_number': hold.case_number,
                'case_description': hold.case_description,
                'legal_authority': hold.legal_authority,
                'contact_person': hold.contact_person,
                'contact_email': hold.contact_email,
                'status': hold.status.value,
                'hold_start_date': hold.hold_start_date.isoformat(),
                'hold_end_date': hold.hold_end_date.isoformat() if hold.hold_end_date else None,
                'affected_data_types': hold.affected_data_types,
                'created_at': hold.created_at.isoformat(),
                'updated_at': hold.updated_at.isoformat()
            }
            for hold in retention_service.legal_holds.values()
        ]
        
        return success_response({
            'legal_holds': legal_holds,
            'total_holds': len(legal_holds)
        }, "Legal holds retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting legal holds: {e}")
        return error_response("Failed to retrieve legal holds", 500)


@data_retention_bp.route('/portability-request', methods=['POST'])
@login_required
@require_auth
def request_data_portability():
    """Request data portability for the current user"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        data_categories = data.get('data_categories', [])
        format_str = data.get('format', 'json')
        
        if not data_categories:
            return error_response("Data categories are required", 400)
        
        # Validate format
        try:
            format_enum = DataPortabilityFormat(format_str)
        except ValueError:
            return error_response("Invalid format. Supported formats: json, csv, xml, pdf, zip", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Request data portability
        request_id = retention_service.request_data_portability(
            user_id=current_user.id,
            data_categories=data_categories,
            format=format_enum
        )
        
        return success_response({
            'request_id': request_id,
            'status': 'processing',
            'message': 'Data portability request submitted successfully'
        }, "Data portability request submitted successfully")
        
    except Exception as e:
        logger.error(f"Error requesting data portability: {e}")
        return error_response("Failed to submit portability request", 500)


@data_retention_bp.route('/portability-requests', methods=['GET'])
@login_required
@require_auth
def get_portability_requests():
    """Get user's portability requests"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Get user's portability requests
        user_requests = [
            {
                'request_id': req.request_id,
                'data_categories': req.data_categories,
                'format': req.format.value,
                'status': req.status,
                'requested_at': req.requested_at.isoformat(),
                'completed_at': req.completed_at.isoformat() if req.completed_at else None,
                'file_size': req.file_size,
                'download_url': req.download_url,
                'expires_at': req.expires_at.isoformat() if req.expires_at else None
            }
            for req in retention_service.portability_requests.values()
            if req.user_id == current_user.id
        ]
        
        return success_response({
            'portability_requests': user_requests,
            'total_requests': len(user_requests)
        }, "Portability requests retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting portability requests: {e}")
        return error_response("Failed to retrieve portability requests", 500)


@data_retention_bp.route('/portability-request/<request_id>/download', methods=['GET'])
@login_required
@require_auth
def download_portability_data(request_id):
    """Download portability data file"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Get portability request
        portability_request = retention_service.portability_requests.get(request_id)
        if not portability_request:
            return error_response("Portability request not found", 404)
        
        if portability_request.user_id != current_user.id:
            return error_response("Access denied", 403)
        
        if portability_request.status != 'completed':
            return error_response("Portability request not completed", 400)
        
        if not portability_request.file_path:
            return error_response("No file available for download", 404)
        
        # Check if file has expired
        if portability_request.expires_at and datetime.utcnow() > portability_request.expires_at:
            return error_response("Download link has expired", 410)
        
        # Send file
        return send_file(
            portability_request.file_path,
            as_attachment=True,
            download_name=f"user_data_{request_id}.{portability_request.format.value}"
        )
        
    except Exception as e:
        logger.error(f"Error downloading portability data: {e}")
        return error_response("Failed to download data", 500)


@data_retention_bp.route('/retention-policies', methods=['GET'])
@login_required
@require_auth
def get_retention_policies():
    """Get retention policies"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Get retention policies
        policies = [
            {
                'policy_id': policy.policy_id,
                'policy_type': policy.policy_type.value,
                'name': policy.name,
                'description': policy.description,
                'retention_period_days': policy.retention_period_days,
                'deletion_method': policy.deletion_method,
                'legal_hold_required': policy.legal_hold_required,
                'notification_required': policy.notification_required,
                'is_active': policy.is_active,
                'created_at': policy.created_at.isoformat(),
                'updated_at': policy.updated_at.isoformat()
            }
            for policy in retention_service.retention_policies.values()
        ]
        
        return success_response({
            'retention_policies': policies,
            'total_policies': len(policies)
        }, "Retention policies retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting retention policies: {e}")
        return error_response("Failed to retrieve retention policies", 500)


@data_retention_bp.route('/retention-records', methods=['GET'])
@login_required
@require_auth
def get_retention_records():
    """Get user's retention records"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Get user's retention records
        user_records = [
            {
                'record_id': record.record_id,
                'data_type': record.data_type,
                'data_id': record.data_id,
                'policy_id': record.policy_id,
                'created_at': record.created_at.isoformat(),
                'expires_at': record.expires_at.isoformat(),
                'deletion_scheduled': record.deletion_scheduled,
                'deletion_date': record.deletion_date.isoformat() if record.deletion_date else None,
                'legal_hold_status': record.legal_hold_status.value,
                'legal_hold_expires': record.legal_hold_expires.isoformat() if record.legal_hold_expires else None
            }
            for record in retention_service.retention_records.values()
            if record.user_id == current_user.id
        ]
        
        return success_response({
            'retention_records': user_records,
            'total_records': len(user_records)
        }, "Retention records retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting retention records: {e}")
        return error_response("Failed to retrieve retention records", 500)


@data_retention_bp.route('/metrics', methods=['GET'])
@login_required
@require_auth
def get_retention_metrics():
    """Get data retention metrics (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Get retention metrics
        metrics = retention_service.get_retention_metrics()
        
        return success_response(metrics, "Retention metrics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting retention metrics: {e}")
        return error_response("Failed to retrieve retention metrics", 500)


@data_retention_bp.route('/subscription-cancellation/<user_id>', methods=['POST'])
@login_required
@require_auth
def handle_subscription_cancellation(user_id):
    """Handle subscription cancellation data cleanup (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Handle subscription cancellation
        request_id = retention_service.handle_subscription_cancellation(user_id)
        
        return success_response({
            'request_id': request_id,
            'user_id': user_id,
            'message': 'Subscription cancellation data cleanup scheduled successfully'
        }, "Subscription cancellation data cleanup scheduled successfully")
        
    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {e}")
        return error_response("Failed to handle subscription cancellation", 500)


@data_retention_bp.route('/process-deletions', methods=['POST'])
@login_required
@require_auth
def process_deletion_requests():
    """Process pending deletion requests (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        
        # Process deletion requests
        results = retention_service.process_deletion_requests()
        
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        return success_response({
            'results': results,
            'total_processed': len(results),
            'successful': successful,
            'failed': failed
        }, f"Processed {len(results)} deletion requests. {successful} successful, {failed} failed")
        
    except Exception as e:
        logger.error(f"Error processing deletion requests: {e}")
        return error_response("Failed to process deletion requests", 500) 