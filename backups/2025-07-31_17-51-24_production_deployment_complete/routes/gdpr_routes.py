"""
GDPR Compliance Routes
Flask routes for GDPR compliance features
"""

import os
import json
from typing import Dict, List, Any
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_cors import CORS
from loguru import logger
import io

from ..gdpr.compliance_manager import (
    get_gdpr_manager, ConsentType, DataCategory, RequestType, RequestStatus,
    PrivacyPolicy, CookiePolicy
)

# Create Flask blueprint
gdpr_bp = Blueprint('gdpr', __name__, url_prefix='/api/gdpr')
CORS(gdpr_bp)

# Consent Management Routes
@gdpr_bp.route('/consent/record', methods=['POST'])
def record_consent():
    """Record user consent"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        consent_type = ConsentType(data.get('consent_type'))
        granted = data.get('granted', False)
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        gdpr_manager = get_gdpr_manager()
        success = gdpr_manager.record_consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_version=data.get('consent_version', '1.0'),
            privacy_policy_version=data.get('privacy_policy_version', '1.0'),
            cookie_policy_version=data.get('cookie_policy_version', '1.0'),
            metadata=data.get('metadata', {})
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Consent recorded successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to record consent'}), 500
    
    except Exception as e:
        logger.error(f"Error recording consent: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/consent/withdraw', methods=['POST'])
def withdraw_consent():
    """Withdraw user consent"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        consent_type = ConsentType(data.get('consent_type'))
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        gdpr_manager = get_gdpr_manager()
        success = gdpr_manager.withdraw_consent(
            user_id=user_id,
            consent_type=consent_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Consent withdrawn successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to withdraw consent'}), 500
    
    except Exception as e:
        logger.error(f"Error withdrawing consent: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/consent/user/<user_id>')
def get_user_consents(user_id):
    """Get user's consent records"""
    try:
        gdpr_manager = get_gdpr_manager()
        consents = gdpr_manager.get_user_consents(user_id)
        
        consent_data = []
        for consent in consents:
            consent_data.append({
                'consent_type': consent.consent_type.value,
                'granted': consent.granted,
                'timestamp': consent.timestamp.isoformat(),
                'withdrawal_timestamp': consent.withdrawal_timestamp.isoformat() if consent.withdrawal_timestamp else None,
                'ip_address': consent.ip_address,
                'user_agent': consent.user_agent,
                'consent_version': consent.consent_version,
                'privacy_policy_version': consent.privacy_policy_version,
                'cookie_policy_version': consent.cookie_policy_version,
                'metadata': consent.metadata
            })
        
        return jsonify({
            'status': 'success',
            'data': consent_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting user consents: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/consent/check/<user_id>/<consent_type>')
def check_consent(user_id, consent_type):
    """Check if user has valid consent for specific type"""
    try:
        gdpr_manager = get_gdpr_manager()
        has_consent = gdpr_manager.has_valid_consent(user_id, ConsentType(consent_type))
        
        return jsonify({
            'status': 'success',
            'data': {
                'user_id': user_id,
                'consent_type': consent_type,
                'has_consent': has_consent
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error checking consent: {e}")
        return jsonify({'error': str(e)}), 500

# GDPR Rights Routes
@gdpr_bp.route('/request/create', methods=['POST'])
def create_gdpr_request():
    """Create GDPR request"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        request_type = RequestType(data.get('request_type'))
        description = data.get('description', '')
        data_categories = [DataCategory(cat) for cat in data.get('data_categories', [])]
        verification_method = data.get('verification_method', 'email')
        
        gdpr_manager = get_gdpr_manager()
        request_id = gdpr_manager.create_gdpr_request(
            user_id=user_id,
            request_type=request_type,
            description=description,
            data_categories=data_categories,
            verification_method=verification_method
        )
        
        if request_id:
            return jsonify({
                'status': 'success',
                'data': {
                    'request_id': request_id,
                    'status': 'pending'
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to create GDPR request'}), 500
    
    except Exception as e:
        logger.error(f"Error creating GDPR request: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/request/<request_id>')
def get_gdpr_request(request_id):
    """Get GDPR request by ID"""
    try:
        gdpr_manager = get_gdpr_manager()
        gdpr_request = gdpr_manager.get_gdpr_request(request_id)
        
        if gdpr_request:
            request_data = {
                'request_id': gdpr_request.request_id,
                'user_id': gdpr_request.user_id,
                'request_type': gdpr_request.request_type.value,
                'status': gdpr_request.status.value,
                'created_at': gdpr_request.created_at.isoformat(),
                'updated_at': gdpr_request.updated_at.isoformat(),
                'completed_at': gdpr_request.completed_at.isoformat() if gdpr_request.completed_at else None,
                'description': gdpr_request.description,
                'data_categories': [cat.value for cat in gdpr_request.data_categories],
                'verification_method': gdpr_request.verification_method,
                'verification_completed': gdpr_request.verification_completed,
                'rejection_reason': gdpr_request.rejection_reason,
                'metadata': gdpr_request.metadata
            }
            
            return jsonify({
                'status': 'success',
                'data': request_data,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'GDPR request not found'}), 404
    
    except Exception as e:
        logger.error(f"Error getting GDPR request: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/request/user/<user_id>')
def get_user_requests(user_id):
    """Get user's GDPR requests"""
    try:
        gdpr_manager = get_gdpr_manager()
        requests = gdpr_manager.get_user_requests(user_id)
        
        request_data = []
        for req in requests:
            request_data.append({
                'request_id': req.request_id,
                'request_type': req.request_type.value,
                'status': req.status.value,
                'created_at': req.created_at.isoformat(),
                'updated_at': req.updated_at.isoformat(),
                'completed_at': req.completed_at.isoformat() if req.completed_at else None,
                'description': req.description,
                'data_categories': [cat.value for cat in req.data_categories],
                'verification_method': req.verification_method,
                'verification_completed': req.verification_completed,
                'rejection_reason': req.rejection_reason,
                'metadata': req.metadata
            })
        
        return jsonify({
            'status': 'success',
            'data': request_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting user requests: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/request/<request_id>/status', methods=['PUT'])
def update_request_status(request_id):
    """Update GDPR request status"""
    try:
        data = request.get_json()
        status = RequestStatus(data.get('status'))
        rejection_reason = data.get('rejection_reason')
        
        gdpr_manager = get_gdpr_manager()
        success = gdpr_manager.update_request_status(
            request_id=request_id,
            status=status,
            rejection_reason=rejection_reason
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Request status updated successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to update request status'}), 500
    
    except Exception as e:
        logger.error(f"Error updating request status: {e}")
        return jsonify({'error': str(e)}), 500

# Data Export and Deletion Routes
@gdpr_bp.route('/export/<user_id>')
def export_user_data(user_id):
    """Export user data for GDPR right to access"""
    try:
        data_categories = request.args.get('data_categories', '').split(',')
        data_categories = [DataCategory(cat) for cat in data_categories if cat]
        
        gdpr_manager = get_gdpr_manager()
        export_data = gdpr_manager.export_user_data(user_id, data_categories)
        
        if export_data:
            # Create file-like object for sending
            file_obj = io.BytesIO(export_data)
            file_obj.seek(0)
            
            filename = f"gdpr_export_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
            
            return send_file(
                file_obj,
                mimetype='application/zip',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({'error': 'Failed to export user data'}), 500
    
    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/delete/<user_id>', methods=['POST'])
def delete_user_data(user_id):
    """Delete user data for GDPR right to erasure"""
    try:
        data = request.get_json() or {}
        data_categories = [DataCategory(cat) for cat in data.get('data_categories', [])]
        
        gdpr_manager = get_gdpr_manager()
        success = gdpr_manager.delete_user_data(user_id, data_categories)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'User data deleted successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to delete user data'}), 500
    
    except Exception as e:
        logger.error(f"Error deleting user data: {e}")
        return jsonify({'error': str(e)}), 500

# Policy Management Routes
@gdpr_bp.route('/policy/privacy')
def get_privacy_policy():
    """Get privacy policy"""
    try:
        version = request.args.get('version')
        gdpr_manager = get_gdpr_manager()
        policy = gdpr_manager.get_privacy_policy(version)
        
        if policy:
            policy_data = {
                'version': policy.version,
                'effective_date': policy.effective_date.isoformat(),
                'content': policy.content,
                'language': policy.language,
                'region': policy.region,
                'data_controller': policy.data_controller,
                'data_processor': policy.data_processor,
                'contact_email': policy.contact_email,
                'contact_phone': policy.contact_phone,
                'metadata': policy.metadata
            }
            
            return jsonify({
                'status': 'success',
                'data': policy_data,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Privacy policy not found'}), 404
    
    except Exception as e:
        logger.error(f"Error getting privacy policy: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/policy/privacy', methods=['POST'])
def add_privacy_policy():
    """Add privacy policy"""
    try:
        data = request.get_json()
        
        policy = PrivacyPolicy(
            version=data.get('version'),
            effective_date=datetime.fromisoformat(data.get('effective_date')),
            content=data.get('content'),
            language=data.get('language', 'en'),
            region=data.get('region', 'EU'),
            data_controller=data.get('data_controller', ''),
            data_processor=data.get('data_processor', ''),
            contact_email=data.get('contact_email', ''),
            contact_phone=data.get('contact_phone', ''),
            metadata=data.get('metadata', {})
        )
        
        gdpr_manager = get_gdpr_manager()
        success = gdpr_manager.add_privacy_policy(policy)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Privacy policy added successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to add privacy policy'}), 500
    
    except Exception as e:
        logger.error(f"Error adding privacy policy: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/policy/cookie')
def get_cookie_policy():
    """Get cookie policy"""
    try:
        version = request.args.get('version')
        gdpr_manager = get_gdpr_manager()
        policy = gdpr_manager.get_cookie_policy(version)
        
        if policy:
            policy_data = {
                'version': policy.version,
                'effective_date': policy.effective_date.isoformat(),
                'cookies': policy.cookies,
                'language': policy.language,
                'region': policy.region,
                'metadata': policy.metadata
            }
            
            return jsonify({
                'status': 'success',
                'data': policy_data,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Cookie policy not found'}), 404
    
    except Exception as e:
        logger.error(f"Error getting cookie policy: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/policy/cookie', methods=['POST'])
def add_cookie_policy():
    """Add cookie policy"""
    try:
        data = request.get_json()
        
        policy = CookiePolicy(
            version=data.get('version'),
            effective_date=datetime.fromisoformat(data.get('effective_date')),
            cookies=data.get('cookies', []),
            language=data.get('language', 'en'),
            region=data.get('region', 'EU'),
            metadata=data.get('metadata', {})
        )
        
        gdpr_manager = get_gdpr_manager()
        success = gdpr_manager.add_cookie_policy(policy)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Cookie policy added successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to add cookie policy'}), 500
    
    except Exception as e:
        logger.error(f"Error adding cookie policy: {e}")
        return jsonify({'error': str(e)}), 500

# Audit Trail Routes
@gdpr_bp.route('/audit/<user_id>')
def get_user_audit_trails(user_id):
    """Get user's audit trails"""
    try:
        limit = request.args.get('limit', 100, type=int)
        gdpr_manager = get_gdpr_manager()
        audit_trails = gdpr_manager.get_user_audit_trails(user_id, limit)
        
        audit_data = []
        for audit in audit_trails:
            audit_data.append({
                'audit_id': audit.audit_id,
                'action': audit.action,
                'timestamp': audit.timestamp.isoformat(),
                'ip_address': audit.ip_address,
                'user_agent': audit.user_agent,
                'resource_type': audit.resource_type,
                'resource_id': audit.resource_id,
                'old_value': audit.old_value,
                'new_value': audit.new_value,
                'metadata': audit.metadata
            })
        
        return jsonify({
            'status': 'success',
            'data': audit_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting audit trails: {e}")
        return jsonify({'error': str(e)}), 500

# Data Inventory Routes
@gdpr_bp.route('/inventory/<user_id>')
def get_user_data_inventory(user_id):
    """Get user's data inventory"""
    try:
        gdpr_manager = get_gdpr_manager()
        inventory = gdpr_manager.get_user_data_inventory(user_id)
        
        return jsonify({
            'status': 'success',
            'data': inventory,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting data inventory: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/inventory/<user_id>', methods=['POST'])
def add_data_inventory_entry(user_id):
    """Add data inventory entry"""
    try:
        data = request.get_json()
        data_category = DataCategory(data.get('data_category'))
        data_type = data.get('data_type')
        storage_location = data.get('storage_location')
        retention_period = data.get('retention_period')
        processing_purpose = data.get('processing_purpose')
        legal_basis = data.get('legal_basis')
        metadata = data.get('metadata', {})
        
        gdpr_manager = get_gdpr_manager()
        success = gdpr_manager.add_data_inventory_entry(
            user_id=user_id,
            data_category=data_category,
            data_type=data_type,
            storage_location=storage_location,
            retention_period=retention_period,
            processing_purpose=processing_purpose,
            legal_basis=legal_basis,
            metadata=metadata
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Data inventory entry added successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to add data inventory entry'}), 500
    
    except Exception as e:
        logger.error(f"Error adding data inventory entry: {e}")
        return jsonify({'error': str(e)}), 500

# Compliance Report Routes
@gdpr_bp.route('/report/<user_id>')
def get_compliance_report(user_id):
    """Get GDPR compliance report for user"""
    try:
        gdpr_manager = get_gdpr_manager()
        report = gdpr_manager.get_compliance_report(user_id)
        
        return jsonify({
            'status': 'success',
            'data': report,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting compliance report: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/report')
def get_global_compliance_report():
    """Get global GDPR compliance report"""
    try:
        gdpr_manager = get_gdpr_manager()
        report = gdpr_manager.get_compliance_report()
        
        return jsonify({
            'status': 'success',
            'data': report,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting global compliance report: {e}")
        return jsonify({'error': str(e)}), 500

# Cookie Consent Management Routes
@gdpr_bp.route('/cookie/consent', methods=['POST'])
def set_cookie_consent():
    """Set cookie consent preferences"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        cookie_preferences = data.get('cookie_preferences', {})
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        gdpr_manager = get_gdpr_manager()
        
        # Record consent for each cookie category
        for category, granted in cookie_preferences.items():
            consent_type = ConsentType(category)
            gdpr_manager.record_consent(
                user_id=user_id,
                consent_type=consent_type,
                granted=granted,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'cookie_preference': True}
            )
        
        return jsonify({
            'status': 'success',
            'message': 'Cookie consent preferences saved',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error setting cookie consent: {e}")
        return jsonify({'error': str(e)}), 500

@gdpr_bp.route('/cookie/preferences/<user_id>')
def get_cookie_preferences(user_id):
    """Get user's cookie preferences"""
    try:
        gdpr_manager = get_gdpr_manager()
        consents = gdpr_manager.get_user_consents(user_id)
        
        # Filter for cookie-related consents
        cookie_consents = {}
        for consent in consents:
            if consent.consent_type in [ConsentType.NECESSARY, ConsentType.ANALYTICS, 
                                      ConsentType.FUNCTIONAL, ConsentType.ADVERTISING]:
                cookie_consents[consent.consent_type.value] = {
                    'granted': consent.granted,
                    'timestamp': consent.timestamp.isoformat(),
                    'withdrawn': consent.withdrawal_timestamp is not None
                }
        
        return jsonify({
            'status': 'success',
            'data': cookie_consents,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting cookie preferences: {e}")
        return jsonify({'error': str(e)}), 500

def register_gdpr_routes(app):
    """Register GDPR routes with Flask app"""
    app.register_blueprint(gdpr_bp)
    logger.info("GDPR compliance routes registered") 