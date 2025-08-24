"""
Admin Communication Management API Routes
Handles admin functions for communication policies and user consent management
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import joinedload
import uuid

from ..services.communication_preference_service import communication_preference_service
from ..models.communication_preferences import (
    CommunicationPreferences, ConsentRecord, AlertTypePreference,
    CommunicationDeliveryLog, OptOutRecord, UserEngagementMetrics, CommunicationPolicy,
    CommunicationChannel, AlertType, FrequencyType, ConsentStatus
)
from ..models.user import User
from ..database import get_db_session

logger = logging.getLogger(__name__)

# Create blueprint
admin_communication_bp = Blueprint('admin_communication', __name__, url_prefix='/api/admin/communication')


# Schema definitions
class CommunicationPolicySchema(Schema):
    """Schema for communication policies"""
    policy_name = fields.Str(required=True)
    policy_type = fields.Str(required=True, validate=lambda x: x in ['default', 'tier_based', 'region_based'])
    user_tier = fields.Str(validate=lambda x: x is None or x in ['free', 'premium', 'enterprise'])
    region = fields.Str()
    user_segment = fields.Str(validate=lambda x: x is None or x in ['new_user', 'engaged', 'at_risk'])
    
    default_channel = fields.Str(validate=lambda x: x in [c.value for c in CommunicationChannel])
    default_frequency = fields.Str(validate=lambda x: x in [f.value for f in FrequencyType])
    max_messages_per_day = fields.Integer(validate=lambda x: x > 0)
    max_messages_per_week = fields.Integer(validate=lambda x: x > 0)
    
    allowed_alert_types = fields.List(fields.Str(validate=lambda x: x in [a.value for a in AlertType]))
    marketing_content_allowed = fields.Boolean()
    
    require_double_optin = fields.Boolean()
    consent_retention_days = fields.Integer(validate=lambda x: x > 0)
    auto_optout_inactive_days = fields.Integer(validate=lambda x: x > 0)
    
    quiet_hours_start = fields.Str(validate=lambda x: len(x) == 5 and ':' in x)
    quiet_hours_end = fields.Str(validate=lambda x: len(x) == 5 and ':' in x)
    timezone_aware = fields.Boolean()
    
    is_active = fields.Boolean()
    priority = fields.Integer(validate=lambda x: 1 <= x <= 10)


class UserConsentFilterSchema(Schema):
    """Schema for filtering user consent data"""
    consent_type = fields.Str(validate=lambda x: x is None or x in ['sms', 'email', 'marketing'])
    consent_status = fields.Str(validate=lambda x: x is None or x in [s.value for s in ConsentStatus])
    user_tier = fields.Str(validate=lambda x: x is None or x in ['free', 'premium', 'enterprise'])
    region = fields.Str()
    date_from = fields.DateTime()
    date_to = fields.DateTime()
    limit = fields.Integer(validate=lambda x: x is None or (1 <= x <= 1000))
    offset = fields.Integer(validate=lambda x: x is None or x >= 0)


# Admin API Routes
@admin_communication_bp.route('/policies', methods=['GET'])
@jwt_required()
def get_policies():
    """Get all communication policies"""
    try:
        # TODO: Add admin authorization check
        admin_user_id = get_jwt_identity()
        
        db = get_db_session()
        policies = db.query(CommunicationPolicy).order_by(CommunicationPolicy.priority).all()
        
        policies_list = []
        for policy in policies:
            policies_list.append({
                'id': policy.id,
                'policy_name': policy.policy_name,
                'policy_type': policy.policy_type,
                'user_tier': policy.user_tier,
                'region': policy.region,
                'user_segment': policy.user_segment,
                'default_channel': policy.default_channel.value,
                'default_frequency': policy.default_frequency.value,
                'max_messages_per_day': policy.max_messages_per_day,
                'max_messages_per_week': policy.max_messages_per_week,
                'allowed_alert_types': policy.allowed_alert_types,
                'marketing_content_allowed': policy.marketing_content_allowed,
                'require_double_optin': policy.require_double_optin,
                'consent_retention_days': policy.consent_retention_days,
                'auto_optout_inactive_days': policy.auto_optout_inactive_days,
                'quiet_hours_start': policy.quiet_hours_start,
                'quiet_hours_end': policy.quiet_hours_end,
                'timezone_aware': policy.timezone_aware,
                'is_active': policy.is_active,
                'priority': policy.priority,
                'created_at': policy.created_at.isoformat() if policy.created_at else None,
                'updated_at': policy.updated_at.isoformat() if policy.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'data': policies_list
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting policies: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get policies'
        }), 500


@admin_communication_bp.route('/policies', methods=['POST'])
@jwt_required()
def create_policy():
    """Create a new communication policy"""
    try:
        # TODO: Add admin authorization check
        admin_user_id = get_jwt_identity()
        
        # Validate request data
        schema = CommunicationPolicySchema()
        data = request.get_json()
        
        try:
            validated_data = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        # Convert to enum values
        validated_data['default_channel'] = CommunicationChannel(validated_data['default_channel'])
        validated_data['default_frequency'] = FrequencyType(validated_data['default_frequency'])
        
        # Create policy
        db = get_db_session()
        policy = CommunicationPolicy(
            id=str(uuid.uuid4()),
            created_by=admin_user_id,
            **validated_data
        )
        
        db.add(policy)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Policy created successfully',
            'data': {
                'id': policy.id,
                'policy_name': policy.policy_name
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating policy: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create policy'
        }), 500


@admin_communication_bp.route('/policies/<policy_id>', methods=['PUT'])
@jwt_required()
def update_policy(policy_id):
    """Update a communication policy"""
    try:
        # TODO: Add admin authorization check
        admin_user_id = get_jwt_identity()
        
        # Validate request data
        schema = CommunicationPolicySchema()
        data = request.get_json()
        
        try:
            validated_data = schema.load(data, partial=True)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        # Convert to enum values if present
        if 'default_channel' in validated_data:
            validated_data['default_channel'] = CommunicationChannel(validated_data['default_channel'])
        if 'default_frequency' in validated_data:
            validated_data['default_frequency'] = FrequencyType(validated_data['default_frequency'])
        
        # Update policy
        db = get_db_session()
        policy = db.query(CommunicationPolicy).filter(CommunicationPolicy.id == policy_id).first()
        
        if not policy:
            return jsonify({
                'success': False,
                'error': 'Policy not found'
            }), 404
        
        for key, value in validated_data.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        policy.updated_by = admin_user_id
        policy.updated_at = datetime.utcnow()
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Policy updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating policy {policy_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update policy'
        }), 500


@admin_communication_bp.route('/policies/<policy_id>', methods=['DELETE'])
@jwt_required()
def delete_policy(policy_id):
    """Delete a communication policy"""
    try:
        # TODO: Add admin authorization check
        admin_user_id = get_jwt_identity()
        
        db = get_db_session()
        policy = db.query(CommunicationPolicy).filter(CommunicationPolicy.id == policy_id).first()
        
        if not policy:
            return jsonify({
                'success': False,
                'error': 'Policy not found'
            }), 404
        
        db.delete(policy)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Policy deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting policy {policy_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete policy'
        }), 500


@admin_communication_bp.route('/user-consent', methods=['GET'])
@jwt_required()
def get_user_consent_data():
    """Get user consent data with filtering"""
    try:
        # TODO: Add admin authorization check
        admin_user_id = get_jwt_identity()
        
        # Validate query parameters
        schema = UserConsentFilterSchema()
        try:
            filters = schema.load(request.args)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        db = get_db_session()
        
        # Build query
        query = db.query(ConsentRecord).options(
            joinedload(ConsentRecord.user)
        )
        
        # Apply filters
        if filters.get('consent_type'):
            query = query.filter(ConsentRecord.consent_type == filters['consent_type'])
        
        if filters.get('consent_status'):
            query = query.filter(ConsentRecord.consent_status == ConsentStatus(filters['consent_status']))
        
        if filters.get('date_from'):
            query = query.filter(ConsentRecord.created_at >= filters['date_from'])
        
        if filters.get('date_to'):
            query = query.filter(ConsentRecord.created_at <= filters['date_to'])
        
        # Apply pagination
        limit = filters.get('limit', 100)
        offset = filters.get('offset', 0)
        
        total_count = query.count()
        consent_records = query.order_by(desc(ConsentRecord.created_at)).offset(offset).limit(limit).all()
        
        # Format response
        records_list = []
        for record in consent_records:
            records_list.append({
                'id': record.id,
                'user_id': record.user_id,
                'user_email': record.user.email if record.user else None,
                'consent_type': record.consent_type,
                'consent_status': record.consent_status.value,
                'phone_number': record.phone_number,
                'ip_address': record.ip_address,
                'consent_source': record.consent_source,
                'legal_basis': record.legal_basis,
                'granted_at': record.granted_at.isoformat() if record.granted_at else None,
                'verified_at': record.verified_at.isoformat() if record.verified_at else None,
                'revoked_at': record.revoked_at.isoformat() if record.revoked_at else None,
                'created_at': record.created_at.isoformat() if record.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'records': records_list,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user consent data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get user consent data'
        }), 500


@admin_communication_bp.route('/user-consent/summary', methods=['GET'])
@jwt_required()
def get_consent_summary():
    """Get consent summary statistics"""
    try:
        # TODO: Add admin authorization check
        admin_user_id = get_jwt_identity()
        
        db = get_db_session()
        
        # Get consent statistics
        consent_stats = db.query(
            ConsentRecord.consent_type,
            ConsentRecord.consent_status,
            func.count(ConsentRecord.id).label('count')
        ).group_by(
            ConsentRecord.consent_type,
            ConsentRecord.consent_status
        ).all()
        
        # Get recent consent activity
        recent_consents = db.query(
            func.date(ConsentRecord.created_at).label('date'),
            func.count(ConsentRecord.id).label('count')
        ).filter(
            ConsentRecord.created_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(
            func.date(ConsentRecord.created_at)
        ).order_by(
            func.date(ConsentRecord.created_at)
        ).all()
        
        # Get opt-out statistics
        opt_out_stats = db.query(
            OptOutRecord.channel,
            func.count(OptOutRecord.id).label('count')
        ).group_by(
            OptOutRecord.channel
        ).all()
        
        # Format response
        summary = {
            'consent_statistics': [
                {
                    'consent_type': stat.consent_type,
                    'status': stat.consent_status.value,
                    'count': stat.count
                }
                for stat in consent_stats
            ],
            'recent_activity': [
                {
                    'date': stat.date.isoformat(),
                    'count': stat.count
                }
                for stat in recent_consents
            ],
            'opt_out_statistics': [
                {
                    'channel': stat.channel.value,
                    'count': stat.count
                }
                for stat in opt_out_stats
            ]
        }
        
        return jsonify({
            'success': True,
            'data': summary
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting consent summary: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get consent summary'
        }), 500


@admin_communication_bp.route('/user-consent/<user_id>', methods=['GET'])
@jwt_required()
def get_user_consent_detail(user_id):
    """Get detailed consent information for a specific user"""
    try:
        # TODO: Add admin authorization check
        admin_user_id = get_jwt_identity()
        
        # Get user consent report
        report = communication_preference_service.get_compliance_report(user_id)
        
        # Get user engagement summary
        engagement = communication_preference_service.get_user_engagement_summary(user_id)
        
        # Get user preferences
        preferences = communication_preference_service.get_user_preferences(user_id)
        
        # Get delivery logs
        db = get_db_session()
        delivery_logs = db.query(CommunicationDeliveryLog).filter(
            CommunicationDeliveryLog.user_id == user_id
        ).order_by(desc(CommunicationDeliveryLog.created_at)).limit(50).all()
        
        logs_list = []
        for log in delivery_logs:
            logs_list.append({
                'id': log.id,
                'alert_type': log.alert_type.value,
                'channel': log.channel.value,
                'status': log.status,
                'sent_at': log.sent_at.isoformat() if log.sent_at else None,
                'delivered_at': log.delivered_at.isoformat() if log.delivered_at else None,
                'opened_at': log.opened_at.isoformat() if log.opened_at else None,
                'clicked_at': log.clicked_at.isoformat() if log.clicked_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user_id,
                'compliance_report': report,
                'engagement_summary': engagement,
                'preferences': {
                    'sms_enabled': preferences.sms_enabled if preferences else None,
                    'email_enabled': preferences.email_enabled if preferences else None,
                    'marketing_content_enabled': preferences.marketing_content_enabled if preferences else None
                },
                'recent_deliveries': logs_list
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user consent detail for {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get user consent detail'
        }), 500


@admin_communication_bp.route('/analytics/delivery-rates', methods=['GET'])
@jwt_required()
def get_delivery_analytics():
    """Get delivery rate analytics"""
    try:
        # TODO: Add admin authorization check
        admin_user_id = get_jwt_identity()
        
        db = get_db_session()
        
        # Get delivery statistics by channel
        channel_stats = db.query(
            CommunicationDeliveryLog.channel,
            func.count(CommunicationDeliveryLog.id).label('total'),
            func.sum(func.case([(CommunicationDeliveryLog.status == 'delivered', 1)], else_=0)).label('delivered'),
            func.sum(func.case([(CommunicationDeliveryLog.status == 'failed', 1)], else_=0)).label('failed')
        ).group_by(
            CommunicationDeliveryLog.channel
        ).all()
        
        # Get delivery statistics by alert type
        alert_type_stats = db.query(
            CommunicationDeliveryLog.alert_type,
            func.count(CommunicationDeliveryLog.id).label('total'),
            func.sum(func.case([(CommunicationDeliveryLog.status == 'delivered', 1)], else_=0)).label('delivered'),
            func.sum(func.case([(CommunicationDeliveryLog.status == 'failed', 1)], else_=0)).label('failed')
        ).group_by(
            CommunicationDeliveryLog.alert_type
        ).all()
        
        # Get daily delivery trends
        daily_trends = db.query(
            func.date(CommunicationDeliveryLog.sent_at).label('date'),
            func.count(CommunicationDeliveryLog.id).label('total'),
            func.sum(func.case([(CommunicationDeliveryLog.status == 'delivered', 1)], else_=0)).label('delivered')
        ).filter(
            CommunicationDeliveryLog.sent_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(
            func.date(CommunicationDeliveryLog.sent_at)
        ).order_by(
            func.date(CommunicationDeliveryLog.sent_at)
        ).all()
        
        # Format response
        analytics = {
            'channel_statistics': [
                {
                    'channel': stat.channel.value,
                    'total': stat.total,
                    'delivered': stat.delivered,
                    'failed': stat.failed,
                    'delivery_rate': round((stat.delivered / stat.total * 100), 2) if stat.total > 0 else 0
                }
                for stat in channel_stats
            ],
            'alert_type_statistics': [
                {
                    'alert_type': stat.alert_type.value,
                    'total': stat.total,
                    'delivered': stat.delivered,
                    'failed': stat.failed,
                    'delivery_rate': round((stat.delivered / stat.total * 100), 2) if stat.total > 0 else 0
                }
                for stat in alert_type_stats
            ],
            'daily_trends': [
                {
                    'date': stat.date.isoformat(),
                    'total': stat.total,
                    'delivered': stat.delivered,
                    'delivery_rate': round((stat.delivered / stat.total * 100), 2) if stat.total > 0 else 0
                }
                for stat in daily_trends
            ]
        }
        
        return jsonify({
            'success': True,
            'data': analytics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting delivery analytics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get delivery analytics'
        }), 500


@admin_communication_bp.route('/analytics/engagement', methods=['GET'])
@jwt_required()
def get_engagement_analytics():
    """Get user engagement analytics"""
    try:
        # TODO: Add admin authorization check
        admin_user_id = get_jwt_identity()
        
        db = get_db_session()
        
        # Get engagement metrics summary
        engagement_summary = db.query(
            func.avg(UserEngagementMetrics.sms_engagement_rate).label('avg_sms_engagement'),
            func.avg(UserEngagementMetrics.email_engagement_rate).label('avg_email_engagement'),
            func.avg(UserEngagementMetrics.push_engagement_rate).label('avg_push_engagement'),
            func.count(UserEngagementMetrics.id).label('total_users')
        ).first()
        
        # Get engagement by user tier (if available)
        # This would require joining with user/subscription data
        
        # Get engagement trends
        engagement_trends = db.query(
            UserEngagementMetrics.engagement_trend,
            func.count(UserEngagementMetrics.id).label('count')
        ).group_by(
            UserEngagementMetrics.engagement_trend
        ).all()
        
        # Format response
        analytics = {
            'summary': {
                'average_sms_engagement': round(engagement_summary.avg_sms_engagement or 0, 2),
                'average_email_engagement': round(engagement_summary.avg_email_engagement or 0, 2),
                'average_push_engagement': round(engagement_summary.avg_push_engagement or 0, 2),
                'total_users': engagement_summary.total_users or 0
            },
            'trends': [
                {
                    'trend': stat.engagement_trend,
                    'user_count': stat.count
                }
                for stat in engagement_trends
            ]
        }
        
        return jsonify({
            'success': True,
            'data': analytics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting engagement analytics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get engagement analytics'
        }), 500 