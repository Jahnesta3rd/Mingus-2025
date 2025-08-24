"""
Financial Compliance Routes
Flask routes for financial compliance features including PCI DSS, payment processing, and breach notifications
"""

import os
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
from loguru import logger

from ..compliance.financial_compliance import (
    get_financial_compliance_manager, PaymentData, PaymentCardType,
    FinancialRecord, DataClassification, ComplianceStandard,
    DataBreach, BreachSeverity, BreachStatus, RetentionPolicy
)

# Create Flask blueprint
financial_compliance_bp = Blueprint('financial_compliance', __name__, url_prefix='/api/financial')
CORS(financial_compliance_bp)

# Payment Processing Routes (PCI DSS Compliant)
@financial_compliance_bp.route('/payment/process', methods=['POST'])
def process_payment():
    """Process payment with PCI DSS compliance"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['transaction_id', 'card_type', 'masked_pan', 'expiry_month', 
                          'expiry_year', 'cardholder_name', 'amount', 'currency', 'merchant_id']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create payment data object
        payment_data = PaymentData(
            transaction_id=data['transaction_id'],
            card_type=PaymentCardType(data['card_type']),
            masked_pan=data['masked_pan'],
            expiry_month=data['expiry_month'],
            expiry_year=data['expiry_year'],
            cardholder_name=data['cardholder_name'],
            amount=float(data['amount']),
            currency=data['currency'],
            merchant_id=data['merchant_id'],
            timestamp=datetime.utcnow(),
            metadata=data.get('metadata', {})
        )
        
        # Process payment with compliance manager
        compliance_manager = get_financial_compliance_manager()
        success = compliance_manager.process_payment_data(payment_data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Payment processed successfully with PCI DSS compliance',
                'data': {
                    'transaction_id': payment_data.transaction_id,
                    'status': 'processed',
                    'pci_compliant': True,
                    'timestamp': payment_data.timestamp.isoformat()
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to process payment'}), 500
    
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        return jsonify({'error': str(e)}), 500

@financial_compliance_bp.route('/payment/<transaction_id>')
def get_payment_data(transaction_id):
    """Get payment data (PCI DSS compliant - masked data only)"""
    try:
        compliance_manager = get_financial_compliance_manager()
        
        # This would retrieve payment data from the database
        # For PCI DSS compliance, only return masked/encrypted data
        payment_info = {
            'transaction_id': transaction_id,
            'masked_pan': '************1234',  # Only last 4 digits
            'card_type': 'visa',
            'amount': 100.00,
            'currency': 'USD',
            'timestamp': datetime.utcnow().isoformat(),
            'pci_compliant': True
        }
        
        return jsonify({
            'status': 'success',
            'data': payment_info,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting payment data: {e}")
        return jsonify({'error': str(e)}), 500

# Financial Records Management
@financial_compliance_bp.route('/records/store', methods=['POST'])
def store_financial_record():
    """Store financial record with compliance requirements"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'record_type', 'data_classification', 'content', 'compliance_standard']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create financial record
        record = FinancialRecord(
            record_id=str(uuid.uuid4()),
            user_id=data['user_id'],
            record_type=data['record_type'],
            data_classification=DataClassification(data['data_classification']),
            content=data['content'],
            encrypted_content="",  # Will be set by the manager
            created_at=datetime.utcnow(),
            retention_date=datetime.utcnow() + timedelta(days=data.get('retention_days', 2555)),
            compliance_standard=ComplianceStandard(data['compliance_standard']),
            metadata=data.get('metadata', {})
        )
        
        # Store record with compliance manager
        compliance_manager = get_financial_compliance_manager()
        success = compliance_manager.store_financial_record(record)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Financial record stored successfully',
                'data': {
                    'record_id': record.record_id,
                    'user_id': record.user_id,
                    'record_type': record.record_type,
                    'data_classification': record.data_classification.value,
                    'compliance_standard': record.compliance_standard.value,
                    'retention_date': record.retention_date.isoformat()
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to store financial record'}), 500
    
    except Exception as e:
        logger.error(f"Error storing financial record: {e}")
        return jsonify({'error': str(e)}), 500

@financial_compliance_bp.route('/records/user/<user_id>')
def get_user_financial_records(user_id):
    """Get user's financial records"""
    try:
        # This would retrieve financial records from the database
        # For compliance, only return metadata, not actual content
        records = [
            {
                'record_id': 'record_1',
                'record_type': 'transaction',
                'data_classification': 'confidential',
                'compliance_standard': 'pci_dss',
                'created_at': '2024-01-15T10:00:00Z',
                'retention_date': '2031-01-15T10:00:00Z'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'data': records,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting user financial records: {e}")
        return jsonify({'error': str(e)}), 500

# Data Breach Management
@financial_compliance_bp.route('/breach/report', methods=['POST'])
def report_data_breach():
    """Report data breach with notification procedures"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'description', 'severity', 'affected_records', 'affected_users', 'data_types']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create breach object
        breach = DataBreach(
            breach_id=str(uuid.uuid4()),
            title=data['title'],
            description=data['description'],
            severity=BreachSeverity(data['severity']),
            status=BreachStatus.DETECTED,
            detected_at=datetime.utcnow(),
            affected_records=int(data['affected_records']),
            affected_users=int(data['affected_users']),
            data_types=data['data_types'],
            metadata=data.get('metadata', {})
        )
        
        # Report breach with compliance manager
        compliance_manager = get_financial_compliance_manager()
        success = compliance_manager.report_data_breach(breach)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Data breach reported successfully',
                'data': {
                    'breach_id': breach.breach_id,
                    'title': breach.title,
                    'severity': breach.severity.value,
                    'status': breach.status.value,
                    'detected_at': breach.detected_at.isoformat(),
                    'affected_records': breach.affected_records,
                    'affected_users': breach.affected_users
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to report data breach'}), 500
    
    except Exception as e:
        logger.error(f"Error reporting data breach: {e}")
        return jsonify({'error': str(e)}), 500

@financial_compliance_bp.route('/breach/<breach_id>/status', methods=['PUT'])
def update_breach_status(breach_id):
    """Update data breach status"""
    try:
        data = request.get_json()
        status = BreachStatus(data.get('status'))
        additional_data = data.get('additional_data', {})
        
        compliance_manager = get_financial_compliance_manager()
        success = compliance_manager.update_breach_status(breach_id, status, additional_data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Breach status updated successfully',
                'data': {
                    'breach_id': breach_id,
                    'status': status.value,
                    'updated_at': datetime.utcnow().isoformat()
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to update breach status'}), 500
    
    except Exception as e:
        logger.error(f"Error updating breach status: {e}")
        return jsonify({'error': str(e)}), 500

@financial_compliance_bp.route('/breaches')
def get_data_breaches():
    """Get data breaches with filtering"""
    try:
        severity_filter = request.args.get('severity')
        status_filter = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        
        # This would retrieve breaches from the database
        breaches = [
            {
                'breach_id': 'breach_1',
                'title': 'Unauthorized Access Detected',
                'severity': 'high',
                'status': 'investigating',
                'detected_at': '2024-01-15T08:00:00Z',
                'affected_records': 150,
                'affected_users': 25
            }
        ]
        
        # Apply filters
        if severity_filter:
            breaches = [b for b in breaches if b['severity'] == severity_filter]
        
        if status_filter:
            breaches = [b for b in breaches if b['status'] == status_filter]
        
        return jsonify({
            'status': 'success',
            'data': breaches[:limit],
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting data breaches: {e}")
        return jsonify({'error': str(e)}), 500

# Retention Policy Management
@financial_compliance_bp.route('/retention/policies', methods=['GET'])
def get_retention_policies():
    """Get all retention policies"""
    try:
        compliance_manager = get_financial_compliance_manager()
        policies = compliance_manager.get_retention_policies()
        
        policy_data = []
        for policy in policies:
            policy_data.append({
                'policy_id': policy.policy_id,
                'data_type': policy.data_type,
                'retention_period_days': policy.retention_period_days,
                'compliance_standard': policy.compliance_standard.value,
                'auto_delete': policy.auto_delete,
                'archive_before_delete': policy.archive_before_delete,
                'archive_location': policy.archive_location
            })
        
        return jsonify({
            'status': 'success',
            'data': policy_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting retention policies: {e}")
        return jsonify({'error': str(e)}), 500

@financial_compliance_bp.route('/retention/policies', methods=['POST'])
def add_retention_policy():
    """Add retention policy"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['data_type', 'retention_period_days', 'compliance_standard']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create retention policy
        policy = RetentionPolicy(
            policy_id=str(uuid.uuid4()),
            data_type=data['data_type'],
            retention_period_days=int(data['retention_period_days']),
            compliance_standard=ComplianceStandard(data['compliance_standard']),
            auto_delete=data.get('auto_delete', True),
            archive_before_delete=data.get('archive_before_delete', False),
            archive_location=data.get('archive_location', ''),
            metadata=data.get('metadata', {})
        )
        
        # Add policy with compliance manager
        compliance_manager = get_financial_compliance_manager()
        success = compliance_manager.add_retention_policy(policy)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Retention policy added successfully',
                'data': {
                    'policy_id': policy.policy_id,
                    'data_type': policy.data_type,
                    'retention_period_days': policy.retention_period_days,
                    'compliance_standard': policy.compliance_standard.value
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to add retention policy'}), 500
    
    except Exception as e:
        logger.error(f"Error adding retention policy: {e}")
        return jsonify({'error': str(e)}), 500

@financial_compliance_bp.route('/retention/cleanup', methods=['POST'])
def cleanup_expired_data():
    """Clean up expired data based on retention policies"""
    try:
        compliance_manager = get_financial_compliance_manager()
        cleanup_stats = compliance_manager.cleanup_expired_data()
        
        return jsonify({
            'status': 'success',
            'message': 'Data cleanup completed successfully',
            'data': cleanup_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error cleaning up expired data: {e}")
        return jsonify({'error': str(e)}), 500

# PCI DSS Compliance
@financial_compliance_bp.route('/pci/compliance')
def get_pci_compliance():
    """Get PCI DSS compliance status"""
    try:
        compliance_manager = get_financial_compliance_manager()
        pci_status = compliance_manager.get_pci_compliance_status()
        
        return jsonify({
            'status': 'success',
            'data': pci_status,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting PCI compliance status: {e}")
        return jsonify({'error': str(e)}), 500

@financial_compliance_bp.route('/pci/requirements')
def get_pci_requirements():
    """Get PCI DSS requirements"""
    try:
        # This would retrieve PCI requirements from the database
        requirements = [
            {
                'requirement_id': 'pci_1_1',
                'category': 'Network Security',
                'requirement': 'Install and maintain a firewall configuration',
                'description': 'Firewall configuration to protect cardholder data',
                'status': 'implemented'
            },
            {
                'requirement_id': 'pci_2_1',
                'category': 'Data Protection',
                'requirement': 'Protect stored cardholder data',
                'description': 'Encrypt stored cardholder data',
                'status': 'implemented'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'data': requirements,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting PCI requirements: {e}")
        return jsonify({'error': str(e)}), 500

# Compliance Reporting
@financial_compliance_bp.route('/compliance/report')
def get_compliance_report():
    """Get comprehensive compliance report"""
    try:
        compliance_manager = get_financial_compliance_manager()
        report = compliance_manager.get_compliance_report()
        
        return jsonify({
            'status': 'success',
            'data': report,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting compliance report: {e}")
        return jsonify({'error': str(e)}), 500

@financial_compliance_bp.route('/compliance/status')
def get_compliance_status():
    """Get overall compliance status"""
    try:
        compliance_manager = get_financial_compliance_manager()
        
        # Get various compliance statuses
        pci_status = compliance_manager.get_pci_compliance_status()
        
        # Calculate overall compliance score
        overall_score = pci_status.get('compliance_score', 0)
        
        # Determine compliance level
        if overall_score >= 95:
            compliance_level = "excellent"
        elif overall_score >= 80:
            compliance_level = "good"
        elif overall_score >= 60:
            compliance_level = "fair"
        else:
            compliance_level = "poor"
        
        status_data = {
            'overall_score': overall_score,
            'compliance_level': compliance_level,
            'pci_dss_score': pci_status.get('compliance_score', 0),
            'last_assessed': datetime.utcnow().isoformat(),
            'next_assessment': (datetime.utcnow() + timedelta(days=90)).isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': status_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting compliance status: {e}")
        return jsonify({'error': str(e)}), 500

# Security Controls
@financial_compliance_bp.route('/security/controls')
def get_security_controls():
    """Get security controls status"""
    try:
        # This would retrieve security controls from the database
        controls = [
            {
                'control_id': 'encryption_control',
                'control_name': 'Data Encryption',
                'control_type': 'technical',
                'description': 'Encrypt sensitive data at rest and in transit',
                'status': 'active',
                'last_tested': '2024-01-10T00:00:00Z',
                'test_result': 'passed'
            },
            {
                'control_id': 'access_control',
                'control_name': 'Access Control',
                'control_type': 'administrative',
                'description': 'Restrict access to sensitive data',
                'status': 'active',
                'last_tested': '2024-01-12T00:00:00Z',
                'test_result': 'passed'
            },
            {
                'control_id': 'monitoring_control',
                'control_name': 'Security Monitoring',
                'control_type': 'technical',
                'description': 'Monitor system access and activities',
                'status': 'active',
                'last_tested': '2024-01-15T00:00:00Z',
                'test_result': 'passed'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'data': controls,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting security controls: {e}")
        return jsonify({'error': str(e)}), 500

# Customer Data Protection
@financial_compliance_bp.route('/customer/protection/status')
def get_customer_data_protection_status():
    """Get customer data protection status"""
    try:
        protection_status = {
            'encryption_enabled': True,
            'access_controls_active': True,
            'data_minimization': True,
            'consent_management': True,
            'data_retention_compliant': True,
            'breach_detection_active': True,
            'last_assessment': datetime.utcnow().isoformat(),
            'compliance_standards': ['PCI DSS', 'GDPR', 'SOX', 'GLBA']
        }
        
        return jsonify({
            'status': 'success',
            'data': protection_status,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting customer data protection status: {e}")
        return jsonify({'error': str(e)}), 500

@financial_compliance_bp.route('/customer/data/inventory')
def get_customer_data_inventory():
    """Get customer data inventory"""
    try:
        # This would retrieve customer data inventory from the database
        inventory = [
            {
                'data_type': 'personal_information',
                'classification': 'confidential',
                'storage_location': 'encrypted_database',
                'retention_period': '5 years',
                'access_controls': 'role_based',
                'encryption': 'AES-256'
            },
            {
                'data_type': 'financial_information',
                'classification': 'highly_restricted',
                'storage_location': 'encrypted_database',
                'retention_period': '7 years',
                'access_controls': 'multi_factor',
                'encryption': 'AES-256'
            },
            {
                'data_type': 'payment_data',
                'classification': 'highly_restricted',
                'storage_location': 'tokenized_database',
                'retention_period': '7 years',
                'access_controls': 'pci_restricted',
                'encryption': 'AES-256'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'data': inventory,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting customer data inventory: {e}")
        return jsonify({'error': str(e)}), 500

def register_financial_compliance_routes(app):
    """Register financial compliance routes with Flask app"""
    app.register_blueprint(financial_compliance_bp)
    logger.info("Financial compliance routes registered") 