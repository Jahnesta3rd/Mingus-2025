"""
Communication Preferences API Routes
Handles user communication preferences, consent management, and compliance
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from typing import Dict, Any
import logging
from datetime import datetime
from sqlalchemy import and_
import uuid

from ..services.communication_preference_service import communication_preference_service
from ..models.communication_preferences import (
    CommunicationChannel, AlertType, FrequencyType, ConsentStatus, UserSegment
)
from ..models.user import User
from ..database import get_db_session

logger = logging.getLogger(__name__)

communication_preferences_bp = Blueprint('communication_preferences', __name__, url_prefix='/api/communication-preferences')

# ============================================================================
# MARSHMALLOW SCHEMAS
# ============================================================================

class CommunicationPreferencesSchema(Schema):
    """Schema for communication preferences"""
    id = fields.Str(dump_only=True)
    user_id = fields.Int(dump_only=True)
    sms_enabled = fields.Bool()
    email_enabled = fields.Bool()
    push_enabled = fields.Bool()
    in_app_enabled = fields.Bool()
    preferred_sms_time = fields.Str()  # HH:MM format
    preferred_email_day = fields.Int(validate=lambda x: 0 <= x <= 6)  # 0=Monday, 6=Sunday
    alert_types_sms = fields.Dict()
    alert_types_email = fields.Dict()
    frequency_preference = fields.Str(validate=lambda x: x in [f.value for f in FrequencyType])
    financial_alerts_enabled = fields.Bool()
    career_content_enabled = fields.Bool()
    wellness_content_enabled = fields.Bool()
    marketing_content_enabled = fields.Bool()
    preferred_email_time = fields.Str()  # HH:MM format
    timezone = fields.Str()
    user_segment = fields.Str(validate=lambda x: x in [s.value for s in UserSegment])
    auto_adjust_frequency = fields.Bool()
    engagement_based_optimization = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class SMSConsentSchema(Schema):
    """Schema for SMS consent"""
    phone_number = fields.Str(required=True)
    consent_source = fields.Str(required=True, validate=lambda x: x in ['web_form', 'mobile_app', 'api', 'sms_reply'])
    ip_address = fields.Str()
    user_agent = fields.Str()


class PhoneVerificationSchema(Schema):
    """Schema for phone verification"""
    verification_code = fields.Str(required=True, validate=lambda x: len(x) == 6 and x.isdigit())


class ConsentRequestSchema(Schema):
    """Schema for consent requests"""
    consent_type = fields.Str(required=True, validate=lambda x: x in ['sms', 'email', 'marketing'])
    legal_basis = fields.Str(validate=lambda x: x in ['consent', 'legitimate_interest', 'contract'])
    purpose = fields.Str()
    data_retention_period = fields.Int()
    consent_source = fields.Str(required=True, validate=lambda x: x in ['web_form', 'mobile_app', 'api'])


class OptOutRequestSchema(Schema):
    """Schema for opt-out requests"""
    channel = fields.Str(required=True, validate=lambda x: x in [c.value for c in CommunicationChannel])
    message_type = fields.Str(validate=lambda x: x in [a.value for a in AlertType])
    reason = fields.Str()


class MessageConsentCheckSchema(Schema):
    """Schema for message consent checks"""
    message_type = fields.Str(required=True, validate=lambda x: x in [a.value for a in AlertType])
    channel = fields.Str(required=True, validate=lambda x: x in [c.value for c in CommunicationChannel])


# ============================================================================
# REQUESTED FLASK ROUTE HANDLERS
# ============================================================================

@communication_preferences_bp.route('/preferences/<int:user_id>', methods=['GET', 'PUT'])
@jwt_required()
def user_preferences(user_id):
    """
    GET: Retrieve user communication preferences
    PUT: Update user communication preferences
    """
    try:
        # Verify user can access these preferences (admin or own user)
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            # Check if user is admin (you may need to implement admin check)
            # For now, we'll allow access if authenticated
            pass
        
        if request.method == 'GET':
            # Get user preferences using SQLAlchemy session
            preferences = communication_preference_service.get_user_communication_prefs(user_id)
            
            if not preferences:
                # Create default preferences if none exist
                preferences = communication_preference_service.create_user_preferences(user_id)
                preferences = communication_preference_service.get_user_communication_prefs(user_id)
            
            return jsonify({
                'success': True,
                'data': preferences
            }), 200
            
        elif request.method == 'PUT':
            # Validate request data
            schema = CommunicationPreferencesSchema()
            try:
                validated_data = schema.load(request.json)
            except ValidationError as e:
                return jsonify({
                    'success': False,
                    'error': 'Validation error',
                    'details': e.messages
                }), 400
            
            # Update preferences using SQLAlchemy session
            success = communication_preference_service.update_user_preferences(user_id, validated_data)
            
            if success:
                # Get updated preferences
                preferences = communication_preference_service.get_user_communication_prefs(user_id)
                
                return jsonify({
                    'success': True,
                    'data': preferences,
                    'message': 'Preferences updated successfully'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update preferences'
                }), 500
                
    except Exception as e:
        logger.error(f"Error handling preferences for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@communication_preferences_bp.route('/sms-consent', methods=['POST'])
@jwt_required()
def sms_consent():
    """
    POST: Grant SMS consent for TCPA compliance
    """
    try:
        user_id = get_jwt_identity()
        
        # Validate request data
        schema = SMSConsentSchema()
        try:
            validated_data = schema.load(request.json)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        # Grant SMS consent using SQLAlchemy session
        sms_consent = communication_preference_service.grant_sms_consent(
            user_id=user_id,
            phone_number=validated_data['phone_number'],
            consent_source=validated_data['consent_source'],
            ip_address=validated_data.get('ip_address') or request.remote_addr,
            user_agent=validated_data.get('user_agent') or request.headers.get('User-Agent')
        )
        
        return jsonify({
            'success': True,
            'data': {
                'consent_granted': sms_consent.consent_granted,
                'consent_granted_at': sms_consent.consent_granted_at.isoformat() if sms_consent.consent_granted_at else None,
                'phone_verified': sms_consent.phone_verified,
                'message': 'SMS consent granted successfully'
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error granting SMS consent for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to grant SMS consent'
        }), 500


@communication_preferences_bp.route('/opt-out', methods=['POST'])
@jwt_required()
def opt_out():
    """
    POST: Handle user opt-out request
    """
    try:
        user_id = get_jwt_identity()
        
        # Validate request data
        schema = OptOutRequestSchema()
        try:
            validated_data = schema.load(request.json)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        # Handle opt-out using SQLAlchemy session
        success = communication_preference_service.handle_opt_out_request(
            user_id=user_id,
            channel=CommunicationChannel(validated_data['channel']),
            message_type=validated_data.get('message_type'),
            reason=validated_data.get('reason')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully opted out of {validated_data["channel"]} communications'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to process opt-out request'
            }), 500
        
    except Exception as e:
        logger.error(f"Error processing opt-out for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process opt-out request'
        }), 500


@communication_preferences_bp.route('/webhook/sms-opt-out', methods=['POST'])
def sms_opt_out_webhook():
    """
    Webhook handler for SMS opt-out replies (STOP messages)
    This endpoint is called by Twilio when a user replies with STOP
    """
    try:
        # Get data from Twilio webhook
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Extract phone number from Twilio webhook
        phone_number = data.get('From') or data.get('from')
        message_body = data.get('Body') or data.get('body', '').strip().upper()
        
        if not phone_number:
            logger.error("SMS opt-out webhook: No phone number provided")
            return jsonify({
                'success': False,
                'error': 'Phone number required'
            }), 400
        
        # Check if message contains STOP
        if 'STOP' in message_body:
            logger.info(f"Processing SMS STOP request for phone number: {phone_number}")
            
            # Handle SMS STOP using database function
            db = get_db_session()
            try:
                success = db.execute(
                    "SELECT handle_sms_stop_request(:phone_number)",
                    {'phone_number': phone_number}
                ).scalar()
                
                if success:
                    logger.info(f"Successfully processed SMS STOP for {phone_number}")
                    return jsonify({
                        'success': True,
                        'message': 'Successfully opted out of SMS communications'
                    }), 200
                else:
                    logger.warning(f"Phone number not found for SMS STOP: {phone_number}")
                    return jsonify({
                        'success': False,
                        'error': 'Phone number not found'
                    }), 404
                    
            except Exception as e:
                logger.error(f"Database error processing SMS STOP for {phone_number}: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Database error'
                }), 500
            finally:
                db.close()
        else:
            # Not a STOP message, log for monitoring
            logger.info(f"Non-STOP SMS received from {phone_number}: {message_body}")
            return jsonify({
                'success': True,
                'message': 'Message received (not a STOP request)'
            }), 200
            
    except Exception as e:
        logger.error(f"Error processing SMS opt-out webhook: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# ============================================================================
# ADDITIONAL HELPER ROUTES
# ============================================================================

@communication_preferences_bp.route('/preferences/<int:user_id>/consent-check', methods=['POST'])
@jwt_required()
def check_consent(user_id):
    """
    POST: Check if user has consented to receive a specific message type
    """
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            pass  # Admin check could be added here
        
        # Validate request data
        schema = MessageConsentCheckSchema()
        try:
            validated_data = schema.load(request.json)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        # Check consent using SQLAlchemy session
        can_send, reason = communication_preference_service.check_consent_for_message_type(
            user_id=user_id,
            message_type=validated_data['message_type'],
            channel=CommunicationChannel(validated_data['channel'])
        )
        
        return jsonify({
            'success': True,
            'data': {
                'can_send': can_send,
                'reason': reason,
                'message_type': validated_data['message_type'],
                'channel': validated_data['channel']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking consent for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to check consent'
        }), 500


@communication_preferences_bp.route('/preferences/<int:user_id>/optimal-time', methods=['GET'])
@jwt_required()
def get_optimal_send_time(user_id):
    """
    GET: Get optimal send time for user
    """
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            pass  # Admin check could be added here
        
        channel = request.args.get('channel', 'email')
        
        if channel not in [c.value for c in CommunicationChannel]:
            return jsonify({
                'success': False,
                'error': 'Invalid channel'
            }), 400
        
        # Get optimal send time using SQLAlchemy session
        optimal_time = communication_preference_service.get_optimal_send_time(
            user_id=user_id,
            channel=CommunicationChannel(channel)
        )
        
        return jsonify({
            'success': True,
            'data': {
                'optimal_send_time': optimal_time.isoformat() if optimal_time else None,
                'channel': channel
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting optimal send time for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get optimal send time'
        }), 500


@communication_preferences_bp.route('/preferences/<int:user_id>/verify-phone', methods=['POST'])
@jwt_required()
def verify_phone_number(user_id):
    """
    POST: Verify phone number with SMS code
    """
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403
        
        # Validate request data
        schema = PhoneVerificationSchema()
        try:
            validated_data = schema.load(request.json)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        # Verify phone number using SQLAlchemy session
        success = communication_preference_service.verify_phone_number(
            user_id=user_id,
            verification_code=validated_data['verification_code']
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Phone number verified successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid verification code'
            }), 400
        
    except Exception as e:
        logger.error(f"Error verifying phone number for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to verify phone number'
        }), 500


# ============================================================================
# PUBLIC ENDPOINTS (No authentication required)
# ============================================================================

@communication_preferences_bp.route('/public/opt-out', methods=['POST'])
def public_opt_out():
    """
    Public opt-out endpoint for email communications
    """
    try:
        email = request.json.get('email') if request.is_json else request.form.get('email')
        channel = request.json.get('channel', 'email') if request.is_json else request.form.get('channel', 'email')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email required'
            }), 400
        
        # Find user by email
        db = get_db_session()
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Handle opt-out using SQLAlchemy session
        success = communication_preference_service.handle_opt_out_request(
            user_id=user.id,
            channel=CommunicationChannel(channel),
            reason='Public opt-out request'
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully opted out of {channel} communications'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to process opt-out request'
            }), 500
        
    except Exception as e:
        logger.error(f"Error processing public opt-out: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process opt-out request'
        }), 500


@communication_preferences_bp.route('/public/consent', methods=['POST'])
def public_consent():
    """
    Public consent endpoint for email communications
    """
    try:
        email = request.json.get('email') if request.is_json else request.form.get('email')
        consent_type = request.json.get('consent_type', 'email') if request.is_json else request.form.get('consent_type', 'email')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email required'
            }), 400
        
        # Find user by email
        db = get_db_session()
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Grant consent
        if consent_type == 'sms':
            phone_number = request.json.get('phone_number') if request.is_json else request.form.get('phone_number')
            if not phone_number:
                return jsonify({
                    'success': False,
                    'error': 'Phone number required for SMS consent'
                }), 400
            
            sms_consent = communication_preference_service.grant_sms_consent(
                user_id=user.id,
                phone_number=phone_number,
                consent_source='web_form',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify({
                'success': True,
                'message': 'SMS consent granted successfully'
            }), 200
        else:
            # Grant email consent
            preferences = db.query(CommunicationPreferences).filter(
                CommunicationPreferences.user_id == user.id
            ).first()
            
            if not preferences:
                return jsonify({
                    'success': False,
                    'error': 'Communication preferences not found'
                }), 404
            
            consent_record = ConsentRecord(
                id=str(uuid.uuid4()),
                user_id=user.id,
                preferences_id=preferences.id,
                consent_type=consent_type,
                consent_status=ConsentStatus.GRANTED,
                legal_basis='consent',
                purpose='Marketing communications',
                consent_source='web_form',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                granted_at=datetime.utcnow()
            )
            
            db.add(consent_record)
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'Email consent granted successfully'
            }), 200
        
    except Exception as e:
        logger.error(f"Error processing public consent: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process consent request'
        }), 500


# ============================================================================
# LEGACY ROUTES (for backward compatibility)
# ============================================================================

@communication_preferences_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """Get current user's communication preferences"""
    try:
        user_id = get_jwt_identity()
        
        preferences = communication_preference_service.get_user_communication_prefs(user_id)
        
        if not preferences:
            # Create default preferences
            preferences = communication_preference_service.create_user_preferences(user_id)
            preferences = communication_preference_service.get_user_communication_prefs(user_id)
        
        return jsonify({
            'success': True,
            'data': preferences
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get preferences'
        }), 500


@communication_preferences_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """Update current user's communication preferences"""
    try:
        user_id = get_jwt_identity()
        
        # Validate request data
        schema = CommunicationPreferencesSchema()
        try:
            validated_data = schema.load(request.json)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        # Update preferences
        success = communication_preference_service.update_user_preferences(user_id, validated_data)
        
        if success:
            # Get updated preferences
            preferences = communication_preference_service.get_user_communication_prefs(user_id)
            
            return jsonify({
                'success': True,
                'data': preferences,
                'message': 'Preferences updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update preferences'
            }), 500
        
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update preferences'
        }), 500


@communication_preferences_bp.route('/preferences/reset', methods=['POST'])
@jwt_required()
def reset_preferences():
    """Reset user preferences to defaults"""
    try:
        user_id = get_jwt_identity()
        
        # Get user segment for appropriate defaults
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        
        # Determine user segment (simplified logic)
        user_segment = UserSegment.NEW_USER  # Default
        if user and user.customer and user.customer.subscription_tier == 'premium':
            user_segment = UserSegment.PREMIUM_SUBSCRIBER
        
        # Create new preferences with defaults
        communication_preference_service.create_user_preferences(user_id, user_segment)
        
        # Get new preferences
        preferences = communication_preference_service.get_user_communication_prefs(user_id)
        
        return jsonify({
            'success': True,
            'data': preferences,
            'message': 'Preferences reset to defaults'
        }), 200
        
    except Exception as e:
        logger.error(f"Error resetting preferences: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to reset preferences'
        }), 500


@communication_preferences_bp.route('/consent/sms', methods=['POST'])
@jwt_required()
def grant_sms_consent():
    """Grant SMS consent for TCPA compliance"""
    try:
        user_id = get_jwt_identity()
        
        # Validate request data
        schema = SMSConsentSchema()
        try:
            validated_data = schema.load(request.json)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        # Grant SMS consent
        sms_consent = communication_preference_service.grant_sms_consent(
            user_id=user_id,
            phone_number=validated_data['phone_number'],
            consent_source=validated_data['consent_source'],
            ip_address=validated_data.get('ip_address'),
            user_agent=validated_data.get('user_agent')
        )
        
        return jsonify({
            'success': True,
            'data': {
                'consent_granted': sms_consent.consent_granted,
                'consent_granted_at': sms_consent.consent_granted_at.isoformat() if sms_consent.consent_granted_at else None,
                'phone_verified': sms_consent.phone_verified,
                'message': 'SMS consent granted successfully'
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error granting SMS consent: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to grant SMS consent'
        }), 500


@communication_preferences_bp.route('/consent/sms/verify', methods=['POST'])
@jwt_required()
def verify_phone_number():
    """Verify phone number with SMS code"""
    try:
        user_id = get_jwt_identity()
        
        # Validate request data
        schema = PhoneVerificationSchema()
        try:
            validated_data = schema.load(request.json)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        # Verify phone number
        success = communication_preference_service.verify_phone_number(
            user_id=user_id,
            verification_code=validated_data['verification_code']
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Phone number verified successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid verification code'
            }), 400
        
    except Exception as e:
        logger.error(f"Error verifying phone number: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to verify phone number'
        }), 500


@communication_preferences_bp.route('/consent/email', methods=['POST'])
@jwt_required()
def grant_email_consent():
    """Grant email consent for GDPR compliance"""
    try:
        user_id = get_jwt_identity()
        
        # Validate request data
        schema = ConsentRequestSchema()
        try:
            validated_data = schema.load(request.json)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        # Create consent record
        db = get_db_session()
        preferences = db.query(CommunicationPreferences).filter(
            CommunicationPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            return jsonify({
                'success': False,
                'error': 'Communication preferences not found'
            }), 404
        
        consent_record = ConsentRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            preferences_id=preferences.id,
            consent_type=validated_data['consent_type'],
            consent_status=ConsentStatus.GRANTED,
            legal_basis=validated_data.get('legal_basis'),
            purpose=validated_data.get('purpose'),
            data_retention_period=validated_data.get('data_retention_period'),
            consent_source=validated_data['consent_source'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            granted_at=datetime.utcnow()
        )
        
        db.add(consent_record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'consent_granted': True,
                'consent_granted_at': consent_record.granted_at.isoformat(),
                'message': 'Email consent granted successfully'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error granting email consent: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to grant email consent'
        }), 500


@communication_preferences_bp.route('/consent/revoke', methods=['POST'])
@jwt_required()
def revoke_consent():
    """Revoke consent for communications"""
    try:
        user_id = get_jwt_identity()
        
        # Validate request data
        schema = ConsentRequestSchema()
        try:
            validated_data = schema.load(request.json)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        db = get_db_session()
        
        if validated_data['consent_type'] == 'sms':
            # Revoke SMS consent
            sms_consent = db.query(SMSConsent).filter(
                SMSConsent.user_id == user_id
            ).first()
            
            if sms_consent:
                sms_consent.opted_out = True
                sms_consent.opted_out_at = datetime.utcnow()
                sms_consent.opt_out_reason = 'User revoked consent'
                sms_consent.opt_out_method = 'api'
        else:
            # Revoke email consent
            consent_record = db.query(ConsentRecord).filter(
                and_(
                    ConsentRecord.user_id == user_id,
                    ConsentRecord.consent_type == validated_data['consent_type']
                )
            ).first()
            
            if consent_record:
                consent_record.consent_status = ConsentStatus.REVOKED
                consent_record.revoked_at = datetime.utcnow()
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'{validated_data["consent_type"].upper()} consent revoked successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error revoking consent: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to revoke consent'
        }), 500


@communication_preferences_bp.route('/consent/check', methods=['POST'])
@jwt_required()
def check_consent():
    """Check if user has consented to receive a specific message type"""
    try:
        user_id = get_jwt_identity()
        
        # Validate request data
        schema = MessageConsentCheckSchema()
        try:
            validated_data = schema.load(request.json)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }), 400
        
        # Check consent
        can_send, reason = communication_preference_service.check_consent_for_message_type(
            user_id=user_id,
            message_type=validated_data['message_type'],
            channel=CommunicationChannel(validated_data['channel'])
        )
        
        return jsonify({
            'success': True,
            'data': {
                'can_send': can_send,
                'reason': reason,
                'message_type': validated_data['message_type'],
                'channel': validated_data['channel']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking consent: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to check consent'
        }), 500


@communication_preferences_bp.route('/optimal-send-time', methods=['GET'])
@jwt_required()
def get_optimal_send_time():
    """Get optimal send time for user"""
    try:
        user_id = get_jwt_identity()
        channel = request.args.get('channel', 'email')
        
        if channel not in [c.value for c in CommunicationChannel]:
            return jsonify({
                'success': False,
                'error': 'Invalid channel'
            }), 400
        
        optimal_time = communication_preference_service.get_optimal_send_time(
            user_id=user_id,
            channel=CommunicationChannel(channel)
        )
        
        return jsonify({
            'success': True,
            'data': {
                'optimal_send_time': optimal_time.isoformat() if optimal_time else None,
                'channel': channel
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting optimal send time: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get optimal send time'
        }), 500


@communication_preferences_bp.route('/engagement', methods=['GET'])
@jwt_required()
def get_engagement_summary():
    """Get user engagement summary"""
    try:
        user_id = get_jwt_identity()
        
        engagement = communication_preference_service.get_user_engagement_summary(user_id)
        
        return jsonify({
            'success': True,
            'data': engagement
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting engagement summary: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get engagement summary'
        }), 500


@communication_preferences_bp.route('/compliance-report', methods=['GET'])
@jwt_required()
def get_compliance_report():
    """Get compliance report for user"""
    try:
        user_id = get_jwt_identity()
        
        report = communication_preference_service.get_compliance_report(user_id)
        
        return jsonify({
            'success': True,
            'data': report
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting compliance report: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get compliance report'
        }), 500


@communication_preferences_bp.route('/opt-out/sms-stop', methods=['POST'])
def handle_sms_stop():
    """Handle SMS STOP requests (public endpoint)"""
    try:
        # Get phone number from request
        phone_number = request.json.get('phone_number') if request.is_json else request.form.get('phone_number')
        
        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'Phone number required'
            }), 400
        
        # Handle SMS STOP
        db = get_db_session()
        success = db.execute(
            "SELECT handle_sms_stop_request(:phone_number)",
            {'phone_number': phone_number}
        ).scalar()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Successfully opted out of SMS communications'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Phone number not found'
            }), 404
        
    except Exception as e:
        logger.error(f"Error handling SMS STOP: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process SMS STOP request'
        }), 500 