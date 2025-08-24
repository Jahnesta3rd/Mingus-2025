"""
Compliance Reporting API Routes

This module provides comprehensive API routes for compliance reporting including regulatory
compliance monitoring, privacy policy automation, terms of service integration, user consent
tracking, data processing activity records, and incident reporting procedures.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.security.compliance_reporting_service import (
    ComplianceReportingService, ComplianceFramework, PolicyType, 
    ConsentStatus, IncidentSeverity, IncidentStatus
)
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService
from backend.security.data_protection_service import DataProtectionService
from backend.security.data_retention_service import DataRetentionService
from backend.middleware.auth import require_auth
from backend.utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
compliance_reporting_bp = Blueprint('compliance_reporting', __name__, url_prefix='/api/compliance')


@compliance_reporting_bp.route('/framework/<framework>/assessment', methods=['GET'])
@login_required
@require_auth
def assess_compliance_framework(framework):
    """Assess compliance for a specific framework (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Validate framework
        try:
            framework_enum = ComplianceFramework(framework)
        except ValueError:
            return error_response(f"Invalid framework: {framework}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Assess compliance
        assessment = compliance_service.assess_compliance_framework(framework_enum)
        
        return success_response(assessment, f"Compliance assessment for {framework} completed successfully")
        
    except Exception as e:
        logger.error(f"Error assessing compliance framework: {e}")
        return error_response("Failed to assess compliance framework", 500)


@compliance_reporting_bp.route('/frameworks', methods=['GET'])
@login_required
@require_auth
def get_compliance_frameworks():
    """Get all compliance frameworks"""
    try:
        frameworks = [
            {
                'framework': framework.value,
                'name': framework.value.upper(),
                'description': f'Compliance framework for {framework.value.upper()}'
            }
            for framework in ComplianceFramework
        ]
        
        return success_response({
            'frameworks': frameworks,
            'total_frameworks': len(frameworks)
        }, "Compliance frameworks retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting compliance frameworks: {e}")
        return error_response("Failed to retrieve compliance frameworks", 500)


@compliance_reporting_bp.route('/privacy-policy', methods=['GET'])
def get_privacy_policy():
    """Get active privacy policy"""
    try:
        data = request.get_json() or {}
        policy_type_str = data.get('policy_type', 'privacy_policy')
        language = data.get('language', 'en')
        
        # Validate policy type
        try:
            policy_type = PolicyType(policy_type_str)
        except ValueError:
            return error_response(f"Invalid policy type: {policy_type_str}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Get active policy
        policy = compliance_service.get_active_privacy_policy(policy_type, language)
        
        if not policy:
            return error_response("No active privacy policy found", 404)
        
        return success_response({
            'policy_id': policy.policy_id,
            'policy_type': policy.policy_type.value,
            'version': policy.version,
            'effective_date': policy.effective_date.isoformat(),
            'content': policy.content,
            'language': policy.language,
            'jurisdiction': policy.jurisdiction
        }, "Privacy policy retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting privacy policy: {e}")
        return error_response("Failed to retrieve privacy policy", 500)


@compliance_reporting_bp.route('/privacy-policy', methods=['POST'])
@login_required
@require_auth
def create_privacy_policy():
    """Create a new privacy policy (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        policy_type_str = data.get('policy_type')
        version = data.get('version')
        content = data.get('content')
        language = data.get('language', 'en')
        jurisdiction = data.get('jurisdiction', 'US')
        
        # Validate required fields
        if not all([policy_type_str, version, content]):
            return error_response("policy_type, version, and content are required", 400)
        
        # Validate policy type
        try:
            policy_type = PolicyType(policy_type_str)
        except ValueError:
            return error_response(f"Invalid policy type: {policy_type_str}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Create policy
        policy_id = compliance_service.create_privacy_policy(
            policy_type=policy_type,
            version=version,
            content=content,
            language=language,
            jurisdiction=jurisdiction
        )
        
        return success_response({
            'policy_id': policy_id,
            'message': 'Privacy policy created successfully'
        }, "Privacy policy created successfully")
        
    except Exception as e:
        logger.error(f"Error creating privacy policy: {e}")
        return error_response("Failed to create privacy policy", 500)


@compliance_reporting_bp.route('/privacy-policy/<policy_id>', methods=['PUT'])
@login_required
@require_auth
def update_privacy_policy(policy_id):
    """Update an existing privacy policy (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        content = data.get('content')
        version = data.get('version')
        
        if not all([content, version]):
            return error_response("content and version are required", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Update policy
        success = compliance_service.update_privacy_policy(
            policy_id=policy_id,
            content=content,
            version=version
        )
        
        if not success:
            return error_response("Privacy policy not found", 404)
        
        return success_response({
            'policy_id': policy_id,
            'message': 'Privacy policy updated successfully'
        }, "Privacy policy updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating privacy policy: {e}")
        return error_response("Failed to update privacy policy", 500)


@compliance_reporting_bp.route('/consent', methods=['POST'])
@login_required
@require_auth
def record_user_consent():
    """Record user consent"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        policy_id = data.get('policy_id')
        policy_type_str = data.get('policy_type')
        policy_version = data.get('policy_version')
        consent_status_str = data.get('consent_status', 'granted')
        consent_method = data.get('consent_method', 'web_form')
        expires_at = data.get('expires_at')
        
        # Validate required fields
        if not all([policy_id, policy_type_str, policy_version]):
            return error_response("policy_id, policy_type, and policy_version are required", 400)
        
        # Validate policy type
        try:
            policy_type = PolicyType(policy_type_str)
        except ValueError:
            return error_response(f"Invalid policy type: {policy_type_str}", 400)
        
        # Validate consent status
        try:
            consent_status = ConsentStatus(consent_status_str)
        except ValueError:
            return error_response(f"Invalid consent status: {consent_status_str}", 400)
        
        # Parse expires_at if provided
        expires_datetime = None
        if expires_at:
            try:
                expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            except ValueError:
                return error_response("Invalid expires_at format", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Record consent
        consent_id = compliance_service.record_user_consent(
            user_id=current_user.id,
            policy_id=policy_id,
            policy_type=policy_type,
            policy_version=policy_version,
            consent_status=consent_status,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            consent_method=consent_method,
            expires_at=expires_datetime
        )
        
        return success_response({
            'consent_id': consent_id,
            'message': 'User consent recorded successfully'
        }, "User consent recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording user consent: {e}")
        return error_response("Failed to record user consent", 500)


@compliance_reporting_bp.route('/consent/<policy_id>/withdraw', methods=['POST'])
@login_required
@require_auth
def withdraw_user_consent(policy_id):
    """Withdraw user consent"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Withdraw consent
        success = compliance_service.withdraw_user_consent(
            user_id=current_user.id,
            policy_id=policy_id
        )
        
        if not success:
            return error_response("No active consent found for this policy", 404)
        
        return success_response({
            'policy_id': policy_id,
            'message': 'User consent withdrawn successfully'
        }, "User consent withdrawn successfully")
        
    except Exception as e:
        logger.error(f"Error withdrawing user consent: {e}")
        return error_response("Failed to withdraw user consent", 500)


@compliance_reporting_bp.route('/consent/check/<policy_type>', methods=['GET'])
@login_required
@require_auth
def check_user_consent(policy_type):
    """Check if user has active consent for policy type"""
    try:
        # Validate policy type
        try:
            policy_type_enum = PolicyType(policy_type)
        except ValueError:
            return error_response(f"Invalid policy type: {policy_type}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Check consent
        has_consent = compliance_service.check_user_consent(
            user_id=current_user.id,
            policy_type=policy_type_enum
        )
        
        return success_response({
            'has_consent': has_consent,
            'policy_type': policy_type
        }, "User consent status checked successfully")
        
    except Exception as e:
        logger.error(f"Error checking user consent: {e}")
        return error_response("Failed to check user consent", 500)


@compliance_reporting_bp.route('/data-processing', methods=['POST'])
@login_required
@require_auth
def record_data_processing():
    """Record data processing activity (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        user_id = data.get('user_id')
        data_category = data.get('data_category')
        processing_purpose = data.get('processing_purpose')
        legal_basis = data.get('legal_basis')
        data_controller = data.get('data_controller')
        data_processor = data.get('data_processor')
        third_parties = data.get('third_parties', [])
        retention_period = data.get('retention_period')
        
        # Validate required fields
        required_fields = ['user_id', 'data_category', 'processing_purpose', 'legal_basis', 
                          'data_controller', 'data_processor', 'retention_period']
        for field in required_fields:
            if not data.get(field):
                return error_response(f"{field} is required", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Record data processing activity
        activity_id = compliance_service.record_data_processing_activity(
            user_id=user_id,
            data_category=data_category,
            processing_purpose=processing_purpose,
            legal_basis=legal_basis,
            data_controller=data_controller,
            data_processor=data_processor,
            third_parties=third_parties,
            retention_period=retention_period
        )
        
        return success_response({
            'activity_id': activity_id,
            'message': 'Data processing activity recorded successfully'
        }, "Data processing activity recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording data processing activity: {e}")
        return error_response("Failed to record data processing activity", 500)


@compliance_reporting_bp.route('/incident', methods=['POST'])
@login_required
@require_auth
def report_incident():
    """Report a compliance incident (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        incident_type = data.get('incident_type')
        severity_str = data.get('severity', 'medium')
        title = data.get('title')
        description = data.get('description')
        affected_users = data.get('affected_users', [])
        affected_data = data.get('affected_data', [])
        regulatory_reporting_required = data.get('regulatory_reporting_required', False)
        
        # Validate required fields
        if not all([incident_type, title, description]):
            return error_response("incident_type, title, and description are required", 400)
        
        # Validate severity
        try:
            severity = IncidentSeverity(severity_str)
        except ValueError:
            return error_response(f"Invalid severity: {severity_str}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Report incident
        incident_id = compliance_service.report_compliance_incident(
            incident_type=incident_type,
            severity=severity,
            title=title,
            description=description,
            affected_users=affected_users,
            affected_data=affected_data,
            regulatory_reporting_required=regulatory_reporting_required
        )
        
        return success_response({
            'incident_id': incident_id,
            'message': 'Compliance incident reported successfully'
        }, "Compliance incident reported successfully")
        
    except Exception as e:
        logger.error(f"Error reporting incident: {e}")
        return error_response("Failed to report incident", 500)


@compliance_reporting_bp.route('/incident/<incident_id>/status', methods=['PUT'])
@login_required
@require_auth
def update_incident_status(incident_id):
    """Update incident status (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        status_str = data.get('status')
        assigned_to = data.get('assigned_to')
        resolution_notes = data.get('resolution_notes')
        
        # Validate status
        try:
            status = IncidentStatus(status_str)
        except ValueError:
            return error_response(f"Invalid status: {status_str}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Update incident status
        success = compliance_service.update_incident_status(
            incident_id=incident_id,
            status=status,
            assigned_to=assigned_to,
            resolution_notes=resolution_notes
        )
        
        if not success:
            return error_response("Incident not found", 404)
        
        return success_response({
            'incident_id': incident_id,
            'status': status.value,
            'message': 'Incident status updated successfully'
        }, "Incident status updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating incident status: {e}")
        return error_response("Failed to update incident status", 500)


@compliance_reporting_bp.route('/report/generate', methods=['POST'])
@login_required
@require_auth
def generate_compliance_report():
    """Generate compliance report (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        framework_str = data.get('framework')
        report_period = data.get('report_period', 'Q1 2024')
        
        # Validate framework
        try:
            framework = ComplianceFramework(framework_str)
        except ValueError:
            return error_response(f"Invalid framework: {framework_str}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Generate report
        report_id = compliance_service.generate_compliance_report(
            framework=framework,
            report_period=report_period,
            generated_by=current_user.id
        )
        
        return success_response({
            'report_id': report_id,
            'framework': framework.value,
            'report_period': report_period,
            'message': 'Compliance report generated successfully'
        }, "Compliance report generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        return error_response("Failed to generate compliance report", 500)


@compliance_reporting_bp.route('/report/<report_id>', methods=['GET'])
@login_required
@require_auth
def get_compliance_report(report_id):
    """Get compliance report (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Get report
        report = compliance_service.compliance_reports.get(report_id)
        if not report:
            return error_response("Report not found", 404)
        
        return success_response({
            'report_id': report.report_id,
            'report_type': report.report_type,
            'framework': report.framework.value,
            'report_period': report.report_period,
            'generated_at': report.generated_at.isoformat(),
            'generated_by': report.generated_by,
            'compliance_score': report.compliance_score,
            'total_requirements': report.total_requirements,
            'implemented_requirements': report.implemented_requirements,
            'partially_implemented_requirements': report.partially_implemented_requirements,
            'not_implemented_requirements': report.not_implemented_requirements,
            'findings': report.findings,
            'recommendations': report.recommendations,
            'report_content': report.report_content
        }, "Compliance report retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting compliance report: {e}")
        return error_response("Failed to retrieve compliance report", 500)


@compliance_reporting_bp.route('/metrics', methods=['GET'])
@login_required
@require_auth
def get_compliance_metrics():
    """Get compliance metrics (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Get metrics
        metrics = compliance_service.get_compliance_metrics()
        
        return success_response(metrics, "Compliance metrics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting compliance metrics: {e}")
        return error_response("Failed to retrieve compliance metrics", 500)


@compliance_reporting_bp.route('/incidents', methods=['GET'])
@login_required
@require_auth
def get_compliance_incidents():
    """Get compliance incidents (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Get incidents
        incidents = [
            {
                'incident_id': incident.incident_id,
                'incident_type': incident.incident_type,
                'severity': incident.severity.value,
                'title': incident.title,
                'description': incident.description,
                'affected_users': incident.affected_users,
                'affected_data': incident.affected_data,
                'detected_at': incident.detected_at.isoformat(),
                'reported_at': incident.reported_at.isoformat(),
                'status': incident.status.value,
                'assigned_to': incident.assigned_to,
                'resolution_date': incident.resolution_date.isoformat() if incident.resolution_date else None,
                'resolution_notes': incident.resolution_notes,
                'regulatory_reporting_required': incident.regulatory_reporting_required,
                'regulatory_reporting_date': incident.regulatory_reporting_date.isoformat() if incident.regulatory_reporting_date else None,
                'remediation_actions': incident.remediation_actions
            }
            for incident in compliance_service.compliance_incidents.values()
        ]
        
        return success_response({
            'incidents': incidents,
            'total_incidents': len(incidents)
        }, "Compliance incidents retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting compliance incidents: {e}")
        return error_response("Failed to retrieve compliance incidents", 500)


@compliance_reporting_bp.route('/user-consents', methods=['GET'])
@login_required
@require_auth
def get_user_consents():
    """Get user's consent records"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        data_protection_service = DataProtectionService(db_session, None, audit_service)
        data_retention_service = DataRetentionService(db_session, access_control_service, audit_service, data_protection_service)
        compliance_service = ComplianceReportingService(db_session, access_control_service, audit_service, data_protection_service, data_retention_service)
        
        # Get user's consents
        user_consents = [
            {
                'consent_id': consent.consent_id,
                'policy_id': consent.policy_id,
                'policy_type': consent.policy_type.value,
                'policy_version': consent.policy_version,
                'consent_status': consent.consent_status.value,
                'granted_at': consent.granted_at.isoformat(),
                'withdrawn_at': consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
                'expires_at': consent.expires_at.isoformat() if consent.expires_at else None,
                'consent_method': consent.consent_method
            }
            for consent in compliance_service.user_consents.values()
            if consent.user_id == current_user.id
        ]
        
        return success_response({
            'consents': user_consents,
            'total_consents': len(user_consents)
        }, "User consents retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting user consents: {e}")
        return error_response("Failed to retrieve user consents", 500) 