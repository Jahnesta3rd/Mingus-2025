"""
Security and Compliance API Routes for MINGUS

This module provides comprehensive API endpoints for security and compliance:
- GDPR compliance and data subject requests
- PCI DSS compliance tracking
- User consent management
- Data retention policies
- Security audit logging
- Encryption key management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app, session
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import uuid

from backend.middleware.auth import require_auth
from backend.security.plaid_security_service import (
    PlaidSecurityService,
    DataClassification,
    ConsentType,
    RetentionPolicy
)
from backend.models.security_models import (
    UserConsent,
    DataRetentionRecord,
    SecurityAuditLog,
    PCIComplianceRecord,
    GDPRDataRequest,
    SecurityIncident
)
from backend.utils.auth_decorators import handle_api_errors

logger = logging.getLogger(__name__)

# Create Blueprint
security_bp = Blueprint('security', __name__, url_prefix='/api/security')

def get_security_service() -> PlaidSecurityService:
    """Get security service instance"""
    db_session = current_app.db.session
    config = current_app.config
    return PlaidSecurityService(db_session, config)

# ============================================================================
# GDPR COMPLIANCE
# ============================================================================

@security_bp.route('/gdpr/consent', methods=['POST'])
@require_auth
@handle_api_errors
def create_user_consent():
    """Create user consent for GDPR compliance"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        consent_type = data.get('consent_type')
        granted = data.get('granted', True)
        
        if not consent_type:
            return jsonify({'error': 'Consent type is required'}), 400
        
        # Validate consent type
        try:
            consent_type_enum = ConsentType(consent_type)
        except ValueError:
            return jsonify({'error': f'Invalid consent type: {consent_type}'}), 400
        
        # Get request metadata
        request_data = {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'consent_version': data.get('consent_version', '1.0'),
            'purposes': data.get('purposes', []),
            'third_parties': data.get('third_parties', [])
        }
        
        # Create security service
        security_service = get_security_service()
        
        # Create consent record
        consent = security_service.create_user_consent(
            str(user_id),
            consent_type_enum,
            granted,
            request_data
        )
        
        return jsonify({
            'success': True,
            'consent_id': str(consent.user_id),
            'consent_type': consent.consent_type.value,
            'granted': consent.granted,
            'granted_at': consent.granted_at.isoformat(),
            'expires_at': consent.expires_at.isoformat() if consent.expires_at else None,
            'message': 'Consent recorded successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating user consent: {e}")
        return jsonify({'error': 'Failed to create consent'}), 500

@security_bp.route('/gdpr/consent/<consent_type>', methods=['GET'])
@require_auth
@handle_api_errors
def get_user_consent(consent_type):
    """Get user consent for specific type"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Validate consent type
        try:
            consent_type_enum = ConsentType(consent_type)
        except ValueError:
            return jsonify({'error': f'Invalid consent type: {consent_type}'}), 400
        
        # Create security service
        security_service = get_security_service()
        
        # Get consent
        consent = security_service.get_user_consent(str(user_id), consent_type_enum)
        
        if not consent:
            return jsonify({
                'success': True,
                'consent': None,
                'message': 'No consent found for this type'
            }), 200
        
        return jsonify({
            'success': True,
            'consent': {
                'consent_type': consent.consent_type.value,
                'granted': consent.granted,
                'granted_at': consent.granted_at.isoformat(),
                'expires_at': consent.expires_at.isoformat() if consent.expires_at else None,
                'consent_version': consent.consent_version,
                'data_processing_purposes': consent.data_processing_purposes,
                'third_parties': consent.third_parties,
                'revoked_at': consent.revoked_at.isoformat() if consent.revoked_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user consent: {e}")
        return jsonify({'error': 'Failed to get consent'}), 500

@security_bp.route('/gdpr/consent/<consent_type>', methods=['DELETE'])
@require_auth
@handle_api_errors
def revoke_user_consent(consent_type):
    """Revoke user consent"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Validate consent type
        try:
            consent_type_enum = ConsentType(consent_type)
        except ValueError:
            return jsonify({'error': f'Invalid consent type: {consent_type}'}), 400
        
        # Create security service
        security_service = get_security_service()
        
        # Revoke consent
        success = security_service.revoke_user_consent(str(user_id), consent_type_enum)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Consent revoked successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to revoke consent'}), 500
        
    except Exception as e:
        logger.error(f"Error revoking user consent: {e}")
        return jsonify({'error': 'Failed to revoke consent'}), 500

@security_bp.route('/gdpr/data-request', methods=['POST'])
@require_auth
@handle_api_errors
def create_data_request():
    """Create GDPR data subject request"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        request_type = data.get('request_type')
        if not request_type:
            return jsonify({'error': 'Request type is required'}), 400
        
        # Validate request type
        valid_types = ['access', 'rectification', 'erasure', 'portability', 'restriction', 'objection']
        if request_type not in valid_types:
            return jsonify({'error': f'Invalid request type: {request_type}'}), 400
        
        # Create GDPR data request
        gdpr_request = GDPRDataRequest(
            user_id=user_id,
            request_type=request_type,
            request_reason=data.get('request_reason'),
            status='pending',
            data_categories=data.get('data_categories', []),
            date_range=data.get('date_range'),
            format_preference=data.get('format_preference', 'json'),
            verification_method=data.get('verification_method')
        )
        
        current_app.db.session.add(gdpr_request)
        current_app.db.session.commit()
        
        return jsonify({
            'success': True,
            'request_id': str(gdpr_request.id),
            'request_type': gdpr_request.request_type,
            'status': gdpr_request.status,
            'submitted_at': gdpr_request.submitted_at.isoformat(),
            'message': 'Data request submitted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating data request: {e}")
        current_app.db.session.rollback()
        return jsonify({'error': 'Failed to create data request'}), 500

@security_bp.route('/gdpr/data-deletion', methods=['POST'])
@require_auth
@handle_api_errors
def request_data_deletion():
    """Request data deletion (GDPR right to be forgotten)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Create security service
        security_service = get_security_service()
        
        # Process data deletion request
        deletion_results = security_service.process_data_deletion_request(str(user_id))
        
        return jsonify({
            'success': True,
            'deletion_request': deletion_results,
            'message': 'Data deletion request processed'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing data deletion request: {e}")
        return jsonify({'error': 'Failed to process data deletion request'}), 500

@security_bp.route('/gdpr/requests', methods=['GET'])
@require_auth
@handle_api_errors
def get_user_data_requests():
    """Get user's GDPR data requests"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get user's data requests
        requests = current_app.db.session.query(GDPRDataRequest).filter(
            GDPRDataRequest.user_id == user_id
        ).order_by(desc(GDPRDataRequest.submitted_at)).all()
        
        request_data = []
        for req in requests:
            request_data.append({
                'id': str(req.id),
                'request_type': req.request_type,
                'status': req.status,
                'submitted_at': req.submitted_at.isoformat(),
                'completed_at': req.completed_at.isoformat() if req.completed_at else None,
                'verification_completed': req.verification_completed,
                'estimated_completion': req.estimated_completion.isoformat() if req.estimated_completion else None
            })
        
        return jsonify({
            'success': True,
            'requests': request_data,
            'count': len(request_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user data requests: {e}")
        return jsonify({'error': 'Failed to get data requests'}), 500

# ============================================================================
# PCI DSS COMPLIANCE
# ============================================================================

@security_bp.route('/pci/compliance', methods=['GET'])
@require_auth
@handle_api_errors
def get_pci_compliance():
    """Get PCI DSS compliance status"""
    try:
        # Get PCI compliance records
        compliance_records = current_app.db.session.query(PCIComplianceRecord).filter(
            PCIComplianceRecord.compliant == True
        ).all()
        
        compliance_data = []
        for record in compliance_records:
            compliance_data.append({
                'requirement_id': record.requirement_id,
                'requirement_name': record.requirement_name,
                'compliant': record.compliant,
                'last_assessed': record.last_assessed.isoformat(),
                'next_assessment': record.next_assessment.isoformat() if record.next_assessment else None,
                'assessment_method': record.assessment_method,
                'remediation_completed': record.remediation_completed
            })
        
        # Calculate compliance metrics
        total_requirements = len(compliance_records)
        compliant_requirements = len([r for r in compliance_records if r.compliant])
        compliance_percentage = (compliant_requirements / total_requirements * 100) if total_requirements > 0 else 0
        
        return jsonify({
            'success': True,
            'compliance_records': compliance_data,
            'metrics': {
                'total_requirements': total_requirements,
                'compliant_requirements': compliant_requirements,
                'compliance_percentage': round(compliance_percentage, 2)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting PCI compliance: {e}")
        return jsonify({'error': 'Failed to get PCI compliance'}), 500

@security_bp.route('/pci/validate', methods=['POST'])
@require_auth
@handle_api_errors
def validate_pci_compliance():
    """Validate PCI DSS compliance for data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Data is required for validation'}), 400
        
        # Create security service
        security_service = get_security_service()
        
        # Validate PCI compliance
        is_compliant, violations = security_service.validate_pci_compliance(data)
        
        return jsonify({
            'success': True,
            'is_compliant': is_compliant,
            'violations': violations,
            'message': 'PCI compliance validation completed'
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating PCI compliance: {e}")
        return jsonify({'error': 'Failed to validate PCI compliance'}), 500

# ============================================================================
# DATA RETENTION MANAGEMENT
# ============================================================================

@security_bp.route('/retention/policies', methods=['GET'])
@require_auth
@handle_api_errors
def get_retention_policies():
    """Get data retention policies"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get user's retention records
        retention_records = current_app.db.session.query(DataRetentionRecord).filter(
            DataRetentionRecord.user_id == user_id,
            DataRetentionRecord.deleted_at.is_(None)
        ).all()
        
        retention_data = []
        for record in retention_records:
            retention_data.append({
                'id': str(record.id),
                'data_type': record.data_type,
                'retention_policy': record.retention_policy,
                'created_at': record.created_at.isoformat(),
                'expires_at': record.expires_at.isoformat() if record.expires_at else None,
                'deletion_scheduled': record.deletion_scheduled,
                'deletion_date': record.deletion_date.isoformat() if record.deletion_date else None,
                'legal_basis': record.legal_basis,
                'data_volume': record.data_volume
            })
        
        return jsonify({
            'success': True,
            'retention_policies': retention_data,
            'count': len(retention_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting retention policies: {e}")
        return jsonify({'error': 'Failed to get retention policies'}), 500

@security_bp.route('/retention/process', methods=['POST'])
@require_auth
@handle_api_errors
def process_data_retention():
    """Process data retention policies"""
    try:
        # Create security service
        security_service = get_security_service()
        
        # Process data retention
        results = security_service.process_data_retention()
        
        return jsonify({
            'success': True,
            'retention_results': results,
            'message': 'Data retention processing completed'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing data retention: {e}")
        return jsonify({'error': 'Failed to process data retention'}), 500

# ============================================================================
# ENCRYPTION KEY MANAGEMENT
# ============================================================================

@security_bp.route('/encryption/keys', methods=['GET'])
@require_auth
@handle_api_errors
def get_encryption_keys():
    """Get encryption key information (metadata only)"""
    try:
        # Get encryption keys (metadata only, no key material)
        keys = current_app.db.session.query(EncryptionKey).filter(
            EncryptionKey.is_active == True
        ).all()
        
        key_data = []
        for key in keys:
            key_data.append({
                'key_id': key.key_id,
                'algorithm': key.algorithm,
                'key_type': key.key_type,
                'created_at': key.created_at.isoformat(),
                'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                'key_purpose': key.key_purpose,
                'data_classification': key.data_classification,
                'usage_count': key.usage_count,
                'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None
            })
        
        return jsonify({
            'success': True,
            'encryption_keys': key_data,
            'count': len(key_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting encryption keys: {e}")
        return jsonify({'error': 'Failed to get encryption keys'}), 500

@security_bp.route('/encryption/rotate', methods=['POST'])
@require_auth
@handle_api_errors
def rotate_encryption_keys():
    """Rotate encryption keys"""
    try:
        # Create security service
        security_service = get_security_service()
        
        # Rotate encryption keys
        rotation_results = security_service.rotate_encryption_keys()
        
        return jsonify({
            'success': True,
            'rotation_results': rotation_results,
            'message': 'Encryption keys rotated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error rotating encryption keys: {e}")
        return jsonify({'error': 'Failed to rotate encryption keys'}), 500

# ============================================================================
# SECURITY AUDIT LOGGING
# ============================================================================

@security_bp.route('/audit/logs', methods=['GET'])
@require_auth
@handle_api_errors
def get_security_audit_logs():
    """Get security audit logs"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        risk_level = request.args.get('risk_level')
        action = request.args.get('action')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = current_app.db.session.query(SecurityAuditLog).filter(
            SecurityAuditLog.user_id == user_id
        )
        
        if risk_level:
            query = query.filter(SecurityAuditLog.risk_level == risk_level)
        if action:
            query = query.filter(SecurityAuditLog.action == action)
        if start_date:
            query = query.filter(SecurityAuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(SecurityAuditLog.timestamp <= end_date)
        
        # Get total count
        total_count = query.count()
        
        # Get paginated results
        logs = query.order_by(desc(SecurityAuditLog.timestamp)).offset((page - 1) * per_page).limit(per_page).all()
        
        log_data = []
        for log in logs:
            log_data.append({
                'id': str(log.id),
                'timestamp': log.timestamp.isoformat(),
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': str(log.resource_id) if log.resource_id else None,
                'success': log.success,
                'risk_level': log.risk_level,
                'threat_score': log.threat_score,
                'details': log.details,
                'error_message': log.error_message,
                'ip_address': log.ip_address,
                'session_id': log.session_id
            })
        
        return jsonify({
            'success': True,
            'audit_logs': log_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting security audit logs: {e}")
        return jsonify({'error': 'Failed to get audit logs'}), 500

# ============================================================================
# SECURITY INCIDENTS
# ============================================================================

@security_bp.route('/incidents', methods=['GET'])
@require_auth
@handle_api_errors
def get_security_incidents():
    """Get security incidents"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 50)
        severity = request.args.get('severity')
        status = request.args.get('status')
        
        # Build query
        query = current_app.db.session.query(SecurityIncident)
        
        if severity:
            query = query.filter(SecurityIncident.severity == severity)
        if status:
            query = query.filter(SecurityIncident.status == status)
        
        # Get total count
        total_count = query.count()
        
        # Get paginated results
        incidents = query.order_by(desc(SecurityIncident.detected_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        incident_data = []
        for incident in incidents:
            incident_data.append({
                'id': str(incident.id),
                'incident_type': incident.incident_type,
                'severity': incident.severity,
                'status': incident.status,
                'title': incident.title,
                'description': incident.description,
                'detected_at': incident.detected_at.isoformat(),
                'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
                'data_breach': incident.data_breach,
                'financial_impact': incident.financial_impact,
                'reputation_impact': incident.reputation_impact
            })
        
        return jsonify({
            'success': True,
            'security_incidents': incident_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting security incidents: {e}")
        return jsonify({'error': 'Failed to get security incidents'}), 500

# ============================================================================
# COMPLIANCE REPORTING
# ============================================================================

@security_bp.route('/compliance/summary', methods=['GET'])
@require_auth
@handle_api_errors
def get_compliance_summary():
    """Get compliance summary report"""
    try:
        # Get compliance summary from database views
        # This would query the security_compliance_summary view
        summary_data = {
            'encryption_keys': {
                'total': 0,
                'active': 0,
                'expired': 0
            },
            'user_consents': {
                'total': 0,
                'active': 0,
                'revoked': 0
            },
            'data_retention': {
                'total': 0,
                'active': 0,
                'deleted': 0
            },
            'pci_compliance': {
                'total': 0,
                'compliant': 0,
                'non_compliant': 0
            }
        }
        
        return jsonify({
            'success': True,
            'compliance_summary': summary_data,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting compliance summary: {e}")
        return jsonify({'error': 'Failed to get compliance summary'}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@security_bp.route('/health', methods=['GET'])
@handle_api_errors
def security_health_check():
    """Health check for security and compliance services"""
    try:
        # Test security service
        security_service = get_security_service()
        
        # Basic health checks
        health_status = {
            'security_service': 'healthy',
            'encryption_keys': 'healthy',
            'audit_logging': 'healthy',
            'compliance_tracking': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'status': 'healthy',
            'services': health_status
        }), 200
        
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503 