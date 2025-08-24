"""
Webhook Handlers for External Services
Handles webhooks from Twilio (SMS) and Resend (Email) for status updates
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields, ValidationError
import logging
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

from ..services.flask_analytics_service import (
    track_message_delivered,
    track_message_opened,
    track_user_action
)
from ..models.communication_analytics import CommunicationMetrics
from ..database import get_db_session

logger = logging.getLogger(__name__)

# Create blueprint
webhook_handlers_bp = Blueprint('webhook_handlers', __name__)


# Schema definitions for webhook validation
class TwilioWebhookSchema(Schema):
    """Schema for Twilio webhook validation"""
    MessageSid = fields.Str(required=True)
    MessageStatus = fields.Str(required=True)
    To = fields.Str(required=True)
    From = fields.Str(required=True)
    ErrorCode = fields.Str(required=False)
    ErrorMessage = fields.Str(required=False)
    SmsSid = fields.Str(required=False)
    SmsStatus = fields.Str(required=False)


class ResendWebhookSchema(Schema):
    """Schema for Resend webhook validation"""
    type = fields.Str(required=True)
    data = fields.Dict(required=True)
    created_at = fields.Str(required=True)


class ResendEmailDeliveredSchema(Schema):
    """Schema for Resend email delivered event"""
    id = fields.Str(required=True)
    from_ = fields.Str(data_key='from', required=True)
    to = fields.List(fields.Str(), required=True)
    subject = fields.Str(required=True)
    created_at = fields.Str(required=True)


class ResendEmailOpenedSchema(Schema):
    """Schema for Resend email opened event"""
    id = fields.Str(required=True)
    from_ = fields.Str(data_key='from', required=True)
    to = fields.List(fields.Str(), required=True)
    subject = fields.Str(required=True)
    opened_at = fields.Str(required=True)


def verify_twilio_signature(request_body: str, signature: str, auth_token: str) -> bool:
    """
    Verify Twilio webhook signature
    
    Args:
        request_body: Raw request body
        signature: X-Twilio-Signature header
        auth_token: Twilio auth token
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Create expected signature
        expected_signature = hmac.new(
            auth_token.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
        
    except Exception as e:
        logger.error(f"Error verifying Twilio signature: {e}")
        return False


def verify_resend_signature(request_body: str, signature: str, webhook_secret: str) -> bool:
    """
    Verify Resend webhook signature
    
    Args:
        request_body: Raw request body
        signature: Resend-Signature header
        webhook_secret: Resend webhook secret
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Create expected signature
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
        
    except Exception as e:
        logger.error(f"Error verifying Resend signature: {e}")
        return False


def get_message_id_from_twilio_sid(sms_sid: str) -> Optional[int]:
    """
    Extract message ID from Twilio SID or find by phone number
    
    Args:
        sms_sid: Twilio SMS SID
        
    Returns:
        Message ID or None if not found
    """
    try:
        db = get_db_session()
        
        # Try to find by SID first (if we store it)
        # For now, we'll need to implement a way to map SID to our message ID
        # This could be done by storing the SID in the communication_metrics table
        # or by using a separate mapping table
        
        # For this implementation, we'll assume the SID contains our message ID
        # or we can find it by phone number and recent timestamp
        message = db.query(CommunicationMetrics).filter(
            CommunicationMetrics.channel == "sms",
            CommunicationMetrics.sent_at >= datetime.utcnow() - timedelta(hours=1)
        ).order_by(CommunicationMetrics.sent_at.desc()).first()
        
        return message.id if message else None
        
    except Exception as e:
        logger.error(f"Error getting message ID from Twilio SID: {e}")
        return None


def get_message_id_from_resend_id(email_id: str) -> Optional[int]:
    """
    Extract message ID from Resend email ID
    
    Args:
        email_id: Resend email ID
        
    Returns:
        Message ID or None if not found
    """
    try:
        db = get_db_session()
        
        # Try to find by email ID (if we store it)
        # Similar to Twilio, we need a way to map Resend ID to our message ID
        message = db.query(CommunicationMetrics).filter(
            CommunicationMetrics.channel == "email",
            CommunicationMetrics.sent_at >= datetime.utcnow() - timedelta(hours=1)
        ).order_by(CommunicationMetrics.sent_at.desc()).first()
        
        return message.id if message else None
        
    except Exception as e:
        logger.error(f"Error getting message ID from Resend ID: {e}")
        return None


@webhook_handlers_bp.route('/webhooks/twilio', methods=['POST'])
def twilio_webhook():
    """
    Handle Twilio SMS status webhooks
    
    Expected webhook events:
    - delivered: SMS was delivered to recipient
    - failed: SMS delivery failed
    - undelivered: SMS was not delivered
    - sent: SMS was sent to carrier
    """
    try:
        # Get raw request body for signature verification
        request_body = request.get_data(as_text=True)
        
        # Verify Twilio signature
        signature = request.headers.get('X-Twilio-Signature')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        
        if not auth_token:
            logger.error("TWILIO_AUTH_TOKEN not configured")
            return jsonify({"error": "Configuration error"}), 500
        
        if not signature or not verify_twilio_signature(request_body, signature, auth_token):
            logger.warning("Invalid Twilio webhook signature")
            return jsonify({"error": "Invalid signature"}), 401
        
        # Validate webhook data
        schema = TwilioWebhookSchema()
        try:
            data = schema.load(request.form)
        except ValidationError as e:
            logger.error(f"Invalid Twilio webhook data: {e.messages}")
            return jsonify({"error": "Invalid data"}), 400
        
        # Extract webhook data
        message_sid = data.get('MessageSid') or data.get('SmsSid')
        message_status = data.get('MessageStatus') or data.get('SmsStatus')
        to_number = data.get('To')
        from_number = data.get('From')
        error_code = data.get('ErrorCode')
        error_message = data.get('ErrorMessage')
        
        logger.info(f"Twilio webhook received: {message_sid} - {message_status}")
        
        # Get our message ID from Twilio SID
        message_id = get_message_id_from_twilio_sid(message_sid)
        
        if not message_id:
            logger.warning(f"Message ID not found for Twilio SID: {message_sid}")
            return jsonify({"error": "Message not found"}), 404
        
        # Handle different status types
        if message_status == "delivered":
            # Track message delivered
            success = track_message_delivered(message_id)
            if success:
                logger.info(f"Tracked SMS delivered: {message_id}")
            else:
                logger.error(f"Failed to track SMS delivered: {message_id}")
                
        elif message_status == "failed" or message_status == "undelivered":
            # Log delivery failure
            logger.warning(f"SMS delivery failed: {message_id} - {error_code}: {error_message}")
            
            # Update message status to failed
            try:
                db = get_db_session()
                message = db.query(CommunicationMetrics).filter(
                    CommunicationMetrics.id == message_id
                ).first()
                
                if message:
                    message.status = "failed"
                    db.commit()
                    logger.info(f"Updated message status to failed: {message_id}")
                    
            except Exception as e:
                logger.error(f"Failed to update message status: {e}")
                
        elif message_status == "sent":
            # Message sent to carrier (not necessarily delivered)
            logger.info(f"SMS sent to carrier: {message_id}")
            
        else:
            # Unknown status
            logger.info(f"Unknown SMS status: {message_status} for message {message_id}")
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        logger.error(f"Error processing Twilio webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500


@webhook_handlers_bp.route('/webhooks/resend', methods=['POST'])
def resend_webhook():
    """
    Handle Resend email event webhooks
    
    Expected webhook events:
    - email.delivered: Email was delivered
    - email.opened: Email was opened
    - email.clicked: Email link was clicked
    - email.complained: Email was marked as spam
    - email.bounced: Email bounced
    """
    try:
        # Get raw request body for signature verification
        request_body = request.get_data(as_text=True)
        
        # Verify Resend signature
        signature = request.headers.get('Resend-Signature')
        webhook_secret = current_app.config.get('RESEND_WEBHOOK_SECRET')
        
        if not webhook_secret:
            logger.error("RESEND_WEBHOOK_SECRET not configured")
            return jsonify({"error": "Configuration error"}), 500
        
        if not signature or not verify_resend_signature(request_body, signature, webhook_secret):
            logger.warning("Invalid Resend webhook signature")
            return jsonify({"error": "Invalid signature"}), 401
        
        # Parse webhook data
        try:
            webhook_data = json.loads(request_body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in Resend webhook: {e}")
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Validate webhook structure
        schema = ResendWebhookSchema()
        try:
            validated_data = schema.load(webhook_data)
        except ValidationError as e:
            logger.error(f"Invalid Resend webhook structure: {e.messages}")
            return jsonify({"error": "Invalid webhook structure"}), 400
        
        event_type = validated_data['type']
        event_data = validated_data['data']
        created_at = validated_data['created_at']
        
        logger.info(f"Resend webhook received: {event_type}")
        
        # Handle different event types
        if event_type == "email.delivered":
            # Validate email delivered data
            delivered_schema = ResendEmailDeliveredSchema()
            try:
                email_data = delivered_schema.load(event_data)
            except ValidationError as e:
                logger.error(f"Invalid email delivered data: {e.messages}")
                return jsonify({"error": "Invalid email data"}), 400
            
            # Get our message ID from Resend email ID
            message_id = get_message_id_from_resend_id(email_data['id'])
            
            if message_id:
                # Track message delivered
                success = track_message_delivered(message_id)
                if success:
                    logger.info(f"Tracked email delivered: {message_id}")
                else:
                    logger.error(f"Failed to track email delivered: {message_id}")
            else:
                logger.warning(f"Message ID not found for Resend email: {email_data['id']}")
                
        elif event_type == "email.opened":
            # Validate email opened data
            opened_schema = ResendEmailOpenedSchema()
            try:
                email_data = opened_schema.load(event_data)
            except ValidationError as e:
                logger.error(f"Invalid email opened data: {e.messages}")
                return jsonify({"error": "Invalid email data"}), 400
            
            # Get our message ID from Resend email ID
            message_id = get_message_id_from_resend_id(email_data['id'])
            
            if message_id:
                # Track message opened
                success = track_message_opened(message_id)
                if success:
                    logger.info(f"Tracked email opened: {message_id}")
                else:
                    logger.error(f"Failed to track email opened: {message_id}")
            else:
                logger.warning(f"Message ID not found for Resend email: {email_data['id']}")
                
        elif event_type == "email.clicked":
            # Handle email link clicks
            email_id = event_data.get('id')
            message_id = get_message_id_from_resend_id(email_id)
            
            if message_id:
                # Track user action (clicked link)
                success = track_user_action(message_id, "clicked_link")
                if success:
                    logger.info(f"Tracked email clicked: {message_id}")
                else:
                    logger.error(f"Failed to track email clicked: {message_id}")
            else:
                logger.warning(f"Message ID not found for Resend email: {email_id}")
                
        elif event_type == "email.complained":
            # Handle spam complaints
            email_id = event_data.get('id')
            message_id = get_message_id_from_resend_id(email_id)
            
            if message_id:
                # Track user action (marked as spam)
                success = track_user_action(message_id, "marked_as_spam")
                if success:
                    logger.info(f"Tracked email complained: {message_id}")
                else:
                    logger.error(f"Failed to track email complained: {message_id}")
            else:
                logger.warning(f"Message ID not found for Resend email: {email_id}")
                
        elif event_type == "email.bounced":
            # Handle email bounces
            email_id = event_data.get('id')
            bounce_type = event_data.get('bounce_type', 'unknown')
            message_id = get_message_id_from_resend_id(email_id)
            
            if message_id:
                # Update message status to failed
                try:
                    db = get_db_session()
                    message = db.query(CommunicationMetrics).filter(
                        CommunicationMetrics.id == message_id
                    ).first()
                    
                    if message:
                        message.status = "failed"
                        db.commit()
                        logger.info(f"Updated message status to failed (bounced): {message_id}")
                        
                except Exception as e:
                    logger.error(f"Failed to update message status: {e}")
                    
                # Track bounce event
                success = track_user_action(message_id, f"email_bounced_{bounce_type}")
                if success:
                    logger.info(f"Tracked email bounced: {message_id} - {bounce_type}")
                else:
                    logger.error(f"Failed to track email bounced: {message_id}")
            else:
                logger.warning(f"Message ID not found for Resend email: {email_id}")
                
        else:
            # Unknown event type
            logger.info(f"Unknown Resend event type: {event_type}")
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        logger.error(f"Error processing Resend webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500


@webhook_handlers_bp.route('/webhooks/health', methods=['GET'])
def webhook_health_check():
    """
    Health check endpoint for webhook handlers
    """
    try:
        return jsonify({
            "status": "healthy",
            "service": "webhook_handlers",
            "endpoints": {
                "twilio": "/webhooks/twilio",
                "resend": "/webhooks/resend"
            },
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Webhook health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "service": "webhook_handlers",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


# Error handlers for webhook blueprint
@webhook_handlers_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    logger.warning(f"Bad request in webhook: {error}")
    return jsonify({"error": "Bad request"}), 400


@webhook_handlers_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    logger.warning(f"Unauthorized webhook request: {error}")
    return jsonify({"error": "Unauthorized"}), 401


@webhook_handlers_bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    logger.warning(f"Webhook endpoint not found: {error}")
    return jsonify({"error": "Not found"}), 404


@webhook_handlers_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal error in webhook: {error}")
    return jsonify({"error": "Internal server error"}), 500 