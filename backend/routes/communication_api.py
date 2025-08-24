"""
Communication API Blueprint
Comprehensive Flask blueprint for all communication-related routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, optional_jwt_required
from datetime import datetime, timedelta
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional

# Import communication services
from ..services.communication_orchestrator import (
    CommunicationOrchestrator,
    TriggerType,
    CommunicationChannel,
    CommunicationPriority,
    send_smart_communication,
    get_communication_status,
    cancel_communication
)
from ..services.communication_preference_service import CommunicationPreferenceService
from ..services.flask_analytics_service import FlaskAnalyticsService
from ..services.flask_reporting_service import FlaskReportingService

# Import webhook handlers
from ..routes.webhook_handlers import (
    verify_twilio_signature,
    verify_resend_signature,
    get_message_id_from_twilio_sid,
    get_message_id_from_resend_id
)

logger = logging.getLogger(__name__)

# Create main communication blueprint
communication_api_bp = Blueprint('communication_api', __name__, url_prefix='/api/communication')


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def validate_trigger_type(trigger_type_str: str) -> TriggerType:
    """Validate and convert trigger type string to enum"""
    try:
        return TriggerType(trigger_type_str)
    except ValueError:
        raise ValueError(f"Invalid trigger type: {trigger_type_str}")


def validate_channel(channel_str: str) -> CommunicationChannel:
    """Validate and convert channel string to enum"""
    try:
        return CommunicationChannel(channel_str)
    except ValueError:
        raise ValueError(f"Invalid channel: {channel_str}")


def validate_priority(priority_str: str) -> CommunicationPriority:
    """Validate and convert priority string to enum"""
    try:
        priority_map = {
            'critical': CommunicationPriority.CRITICAL,
            'high': CommunicationPriority.HIGH,
            'medium': CommunicationPriority.MEDIUM,
            'low': CommunicationPriority.LOW
        }
        return priority_map[priority_str.lower()]
    except KeyError:
        raise ValueError(f"Invalid priority: {priority_str}")


def handle_communication_error(error: Exception, context: str = "") -> tuple:
    """Standardized error handling for communication endpoints"""
    logger.error(f"Communication API error in {context}: {error}")
    return jsonify({
        'success': False,
        'error': 'Communication service error',
        'details': str(error),
        'context': context
    }), 500


# =====================================================
# COMMUNICATION ORCHESTRATOR ENDPOINTS
# =====================================================

@communication_api_bp.route('/send', methods=['POST'])
@jwt_required()
def send_communication():
    """
    Send smart communication
    
    Request Body:
    {
        "user_id": 123,
        "trigger_type": "financial_alert",
        "data": {
            "amount": 100.50,
            "account": "checking",
            "threshold": 200.00
        },
        "channel": "sms",
        "priority": "critical",
        "scheduled_time": "2025-01-27T10:00:00Z"
    }
    """
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested communication send")
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['user_id', 'trigger_type', 'data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse and validate trigger type
        try:
            trigger_type = validate_trigger_type(data['trigger_type'])
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Parse optional fields
        channel = None
        if 'channel' in data:
            try:
                channel = validate_channel(data['channel'])
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        priority = None
        if 'priority' in data:
            try:
                priority = validate_priority(data['priority'])
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        scheduled_time = None
        if 'scheduled_time' in data:
            try:
                scheduled_time = datetime.fromisoformat(data['scheduled_time'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid scheduled_time format. Use ISO 8601 format.'}), 400
        
        # Send communication
        result = send_smart_communication(
            user_id=data['user_id'],
            trigger_type=trigger_type,
            data=data['data'],
            channel=channel,
            priority=priority,
            scheduled_time=scheduled_time
        )
        
        # Return response
        if result.success:
            response = {
                'success': True,
                'task_id': result.task_id,
                'cost': result.cost,
                'fallback_used': result.fallback_used,
                'analytics_tracked': result.analytics_tracked,
                'message': 'Communication scheduled successfully'
            }
            logger.info(f"Communication sent successfully for user {data['user_id']}, task_id: {result.task_id}")
            return jsonify(response), 200
        else:
            response = {
                'success': False,
                'error': result.error_message,
                'fallback_used': result.fallback_used
            }
            logger.warning(f"Communication failed for user {data['user_id']}: {result.error_message}")
            return jsonify(response), 400
            
    except Exception as e:
        return handle_communication_error(e, "send_communication")


@communication_api_bp.route('/status/<task_id>', methods=['GET'])
@jwt_required()
def get_communication_task_status(task_id: str):
    """Get status of a communication task"""
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested status for task {task_id}")
        
        status = get_communication_status(task_id)
        
        if 'error' in status:
            return jsonify(status), 500
        
        logger.info(f"Task status retrieved for {task_id}: {status['status']}")
        return jsonify(status), 200
        
    except Exception as e:
        return handle_communication_error(e, "get_communication_status")


@communication_api_bp.route('/cancel/<task_id>', methods=['POST'])
@jwt_required()
def cancel_communication_task(task_id: str):
    """Cancel a scheduled communication task"""
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested cancellation for task {task_id}")
        
        success = cancel_communication(task_id)
        
        if success:
            response = {
                'success': True,
                'message': 'Communication cancelled successfully'
            }
            logger.info(f"Communication task {task_id} cancelled successfully")
            return jsonify(response), 200
        else:
            response = {
                'success': False,
                'error': 'Failed to cancel communication'
            }
            logger.warning(f"Failed to cancel communication task {task_id}")
            return jsonify(response), 400
            
    except Exception as e:
        return handle_communication_error(e, "cancel_communication")


@communication_api_bp.route('/batch', methods=['POST'])
@jwt_required()
def send_batch_communications():
    """Send multiple communications in batch"""
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested batch communication send")
        
        data = request.get_json()
        if not data or 'communications' not in data:
            return jsonify({'error': 'No communications data provided'}), 400
        
        communications = data['communications']
        if not isinstance(communications, list):
            return jsonify({'error': 'Communications must be a list'}), 400
        
        # Process each communication
        results = []
        total_cost = 0.0
        
        for comm_data in communications:
            try:
                # Validate required fields
                if not all(field in comm_data for field in ['user_id', 'trigger_type', 'data']):
                    results.append({
                        'user_id': comm_data.get('user_id', 'unknown'),
                        'success': False,
                        'error': 'Missing required fields'
                    })
                    continue
                
                # Parse trigger type
                try:
                    trigger_type = validate_trigger_type(comm_data['trigger_type'])
                except ValueError as e:
                    results.append({
                        'user_id': comm_data['user_id'],
                        'success': False,
                        'error': str(e)
                    })
                    continue
                
                # Parse optional fields
                channel = None
                if 'channel' in comm_data:
                    try:
                        channel = validate_channel(comm_data['channel'])
                    except ValueError as e:
                        results.append({
                            'user_id': comm_data['user_id'],
                            'success': False,
                            'error': str(e)
                        })
                        continue
                
                priority = None
                if 'priority' in comm_data:
                    try:
                        priority = validate_priority(comm_data['priority'])
                    except ValueError as e:
                        results.append({
                            'user_id': comm_data['user_id'],
                            'success': False,
                            'error': str(e)
                        })
                        continue
                
                # Send communication
                result = send_smart_communication(
                    user_id=comm_data['user_id'],
                    trigger_type=trigger_type,
                    data=comm_data['data'],
                    channel=channel,
                    priority=priority
                )
                
                # Record result
                result_data = {
                    'user_id': comm_data['user_id'],
                    'success': result.success,
                    'task_id': result.task_id,
                    'cost': result.cost,
                    'fallback_used': result.fallback_used
                }
                
                if not result.success:
                    result_data['error'] = result.error_message
                else:
                    total_cost += result.cost
                
                results.append(result_data)
                
            except Exception as e:
                logger.error(f"Error processing batch communication for user {comm_data.get('user_id', 'unknown')}: {e}")
                results.append({
                    'user_id': comm_data.get('user_id', 'unknown'),
                    'success': False,
                    'error': str(e)
                })
        
        # Calculate summary
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        response = {
            'success': True,
            'results': results,
            'summary': {
                'total': len(results),
                'successful': successful,
                'failed': failed,
                'total_cost': total_cost
            }
        }
        
        logger.info(f"Batch communication completed: {successful} successful, {failed} failed")
        return jsonify(response), 200
        
    except Exception as e:
        return handle_communication_error(e, "batch_communications")


@communication_api_bp.route('/trigger-types', methods=['GET'])
@jwt_required()
def get_trigger_types():
    """Get available trigger types"""
    try:
        trigger_types = [
            {
                'value': TriggerType.FINANCIAL_ALERT.value,
                'name': 'Financial Alert',
                'description': 'Critical financial notifications',
                'default_channel': 'sms',
                'default_priority': 'critical'
            },
            {
                'value': TriggerType.PAYMENT_REMINDER.value,
                'name': 'Payment Reminder',
                'description': 'Payment due notifications',
                'default_channel': 'sms',
                'default_priority': 'high'
            },
            {
                'value': TriggerType.WEEKLY_CHECKIN.value,
                'name': 'Weekly Check-in',
                'description': 'Weekly engagement messages',
                'default_channel': 'sms',
                'default_priority': 'medium'
            },
            {
                'value': TriggerType.MILESTONE_CELEBRATION.value,
                'name': 'Milestone Celebration',
                'description': 'Achievement and milestone notifications',
                'default_channel': 'email',
                'default_priority': 'medium'
            },
            {
                'value': TriggerType.MONTHLY_REPORT.value,
                'name': 'Monthly Report',
                'description': 'Monthly financial summaries',
                'default_channel': 'email',
                'default_priority': 'low'
            },
            {
                'value': TriggerType.CAREER_INSIGHT.value,
                'name': 'Career Insight',
                'description': 'Career development content',
                'default_channel': 'email',
                'default_priority': 'low'
            },
            {
                'value': TriggerType.EDUCATIONAL_CONTENT.value,
                'name': 'Educational Content',
                'description': 'Financial education materials',
                'default_channel': 'email',
                'default_priority': 'low'
            },
            {
                'value': TriggerType.ONBOARDING_SEQUENCE.value,
                'name': 'Onboarding Sequence',
                'description': 'New user onboarding messages',
                'default_channel': 'both',
                'default_priority': 'high'
            },
            {
                'value': TriggerType.BEHAVIORAL_TRIGGER.value,
                'name': 'Behavioral Trigger',
                'description': 'Behavior-based communications',
                'default_channel': 'sms',
                'default_priority': 'medium'
            },
            {
                'value': TriggerType.ENGAGEMENT_REACTIVATION.value,
                'name': 'Engagement Reactivation',
                'description': 'Re-engagement campaigns',
                'default_channel': 'both',
                'default_priority': 'high'
            }
        ]
        
        return jsonify({'trigger_types': trigger_types}), 200
        
    except Exception as e:
        return handle_communication_error(e, "get_trigger_types")


# =====================================================
# USER PREFERENCE MANAGEMENT ENDPOINTS
# =====================================================

@communication_api_bp.route('/preferences/<int:user_id>', methods=['GET', 'PUT'])
@jwt_required()
def manage_user_preferences(user_id: int):
    """Get or update user communication preferences"""
    try:
        current_user_id = get_jwt_identity()
        preference_service = CommunicationPreferenceService()
        
        if request.method == 'GET':
            logger.info(f"User {current_user_id} requested preferences for user {user_id}")
            
            preferences = preference_service.get_user_communication_prefs(user_id)
            if not preferences:
                return jsonify({'error': 'User preferences not found'}), 404
            
            return jsonify({
                'success': True,
                'preferences': preferences
            }), 200
        
        elif request.method == 'PUT':
            logger.info(f"User {current_user_id} updating preferences for user {user_id}")
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No preference data provided'}), 400
            
            # Update preferences
            updated_prefs = preference_service.update_user_preferences(user_id, data)
            
            return jsonify({
                'success': True,
                'message': 'Preferences updated successfully',
                'preferences': updated_prefs
            }), 200
            
    except Exception as e:
        return handle_communication_error(e, "manage_user_preferences")


@communication_api_bp.route('/preferences/<int:user_id>/reset', methods=['POST'])
@jwt_required()
def reset_user_preferences(user_id: int):
    """Reset user preferences to defaults"""
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} resetting preferences for user {user_id}")
        
        preference_service = CommunicationPreferenceService()
        default_prefs = preference_service._get_smart_defaults(user_id)
        
        updated_prefs = preference_service.update_user_preferences(user_id, default_prefs)
        
        return jsonify({
            'success': True,
            'message': 'Preferences reset to defaults successfully',
            'preferences': updated_prefs
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "reset_user_preferences")


@communication_api_bp.route('/consent/sms', methods=['POST'])
@jwt_required()
def grant_sms_consent():
    """Grant SMS consent for a user"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'phone_number' not in data:
            return jsonify({'error': 'Phone number required'}), 400
        
        preference_service = CommunicationPreferenceService()
        result = preference_service.grant_sms_consent(
            user_id=data.get('user_id'),
            phone_number=data['phone_number'],
            consent_source=data.get('consent_source', 'api')
        )
        
        return jsonify({
            'success': True,
            'message': 'SMS consent granted successfully',
            'verification_required': result.get('verification_required', False)
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "grant_sms_consent")


@communication_api_bp.route('/consent/sms/verify', methods=['POST'])
@jwt_required()
def verify_sms_consent():
    """Verify SMS consent with verification code"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'phone_number' not in data or 'verification_code' not in data:
            return jsonify({'error': 'Phone number and verification code required'}), 400
        
        preference_service = CommunicationPreferenceService()
        result = preference_service.verify_phone_number(
            phone_number=data['phone_number'],
            verification_code=data['verification_code']
        )
        
        if result['verified']:
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
        return handle_communication_error(e, "verify_sms_consent")


@communication_api_bp.route('/consent/email', methods=['POST'])
@jwt_required()
def grant_email_consent():
    """Grant email consent for a user"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email required'}), 400
        
        preference_service = CommunicationPreferenceService()
        result = preference_service.grant_consent(
            user_id=data.get('user_id'),
            channel='email',
            message_types=data.get('message_types', ['all']),
            consent_source=data.get('consent_source', 'api')
        )
        
        return jsonify({
            'success': True,
            'message': 'Email consent granted successfully'
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "grant_email_consent")


@communication_api_bp.route('/consent/revoke', methods=['POST'])
@jwt_required()
def revoke_consent():
    """Revoke consent for a specific channel and message type"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'channel' not in data:
            return jsonify({'error': 'Channel required'}), 400
        
        preference_service = CommunicationPreferenceService()
        result = preference_service.revoke_consent(
            user_id=data.get('user_id'),
            channel=data['channel'],
            message_types=data.get('message_types', ['all']),
            reason=data.get('reason', 'user_request')
        )
        
        return jsonify({
            'success': True,
            'message': 'Consent revoked successfully'
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "revoke_consent")


@communication_api_bp.route('/opt-out', methods=['POST'])
@jwt_required()
def opt_out():
    """Opt out of communications"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'channel' not in data:
            return jsonify({'error': 'Channel required'}), 400
        
        preference_service = CommunicationPreferenceService()
        result = preference_service.handle_opt_out_request(
            user_id=data.get('user_id'),
            channel=data['channel'],
            message_type=data.get('message_type', 'all'),
            reason=data.get('reason', 'user_request')
        )
        
        return jsonify({
            'success': True,
            'message': 'Opt-out processed successfully'
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "opt_out")


@communication_api_bp.route('/consent/check', methods=['POST'])
@jwt_required()
def check_consent():
    """Check if user has consent for specific communication"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'message_type' not in data or 'channel' not in data:
            return jsonify({'error': 'Message type and channel required'}), 400
        
        preference_service = CommunicationPreferenceService()
        result = preference_service.check_consent_for_message_type(
            user_id=data.get('user_id'),
            message_type=data['message_type'],
            channel=data['channel']
        )
        
        return jsonify({
            'success': True,
            'can_send': result['can_send'],
            'reason': result.get('reason'),
            'consent_status': result.get('consent_status')
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "check_consent")


@communication_api_bp.route('/optimal-send-time', methods=['GET'])
@jwt_required()
def get_optimal_send_time():
    """Get optimal send time for user"""
    try:
        current_user_id = get_jwt_identity()
        user_id = request.args.get('user_id', type=int)
        channel = request.args.get('channel', 'sms')
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        preference_service = CommunicationPreferenceService()
        optimal_time = preference_service.get_optimal_send_time(user_id, channel)
        
        return jsonify({
            'success': True,
            'optimal_time': optimal_time.isoformat() if optimal_time else None,
            'channel': channel
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "get_optimal_send_time")


# =====================================================
# WEBHOOK HANDLERS
# =====================================================

@communication_api_bp.route('/webhooks/twilio', methods=['POST'])
def twilio_webhook():
    """Handle Twilio SMS status webhooks"""
    try:
        # Verify Twilio signature
        if not verify_twilio_signature(request):
            logger.warning("Invalid Twilio webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No webhook data'}), 400
        
        # Extract message details
        message_sid = data.get('MessageSid')
        message_status = data.get('MessageStatus')
        error_code = data.get('ErrorCode')
        error_message = data.get('ErrorMessage')
        
        logger.info(f"Twilio webhook received: {message_sid} - {message_status}")
        
        # Get internal message ID
        message_id = get_message_id_from_twilio_sid(message_sid)
        if not message_id:
            logger.warning(f"No internal message ID found for Twilio SID: {message_sid}")
            return jsonify({'error': 'Message not found'}), 404
        
        # Update analytics
        analytics_service = FlaskAnalyticsService()
        
        if message_status == 'delivered':
            analytics_service.track_message_delivered(message_id)
        elif message_status == 'failed':
            analytics_service.track_message_sent(
                user_id=0,  # Will be updated from database
                channel='sms',
                message_type='unknown',
                cost=0.0
            )
            logger.error(f"SMS delivery failed: {error_code} - {error_message}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error processing Twilio webhook: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500


@communication_api_bp.route('/webhooks/resend', methods=['POST'])
def resend_webhook():
    """Handle Resend email status webhooks"""
    try:
        # Verify Resend signature
        if not verify_resend_signature(request):
            logger.warning("Invalid Resend webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No webhook data'}), 400
        
        # Extract event details
        event_type = data.get('type')
        message_id = data.get('id')
        
        logger.info(f"Resend webhook received: {event_type} - {message_id}")
        
        # Get internal message ID
        internal_message_id = get_message_id_from_resend_id(message_id)
        if not internal_message_id:
            logger.warning(f"No internal message ID found for Resend ID: {message_id}")
            return jsonify({'error': 'Message not found'}), 404
        
        # Update analytics
        analytics_service = FlaskAnalyticsService()
        
        if event_type == 'email.delivered':
            analytics_service.track_message_delivered(internal_message_id)
        elif event_type == 'email.opened':
            analytics_service.track_message_opened(internal_message_id)
        elif event_type == 'email.clicked':
            analytics_service.track_user_action(internal_message_id, 'clicked')
        elif event_type == 'email.bounced':
            logger.warning(f"Email bounced: {message_id}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error processing Resend webhook: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500


@communication_api_bp.route('/webhooks/sms-opt-out', methods=['POST'])
def sms_opt_out_webhook():
    """Handle SMS opt-out replies"""
    try:
        # Verify Twilio signature
        if not verify_twilio_signature(request):
            logger.warning("Invalid Twilio opt-out webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No webhook data'}), 400
        
        # Extract opt-out details
        from_number = data.get('From')
        body = data.get('Body', '').strip().lower()
        
        if 'stop' in body or 'unsubscribe' in body or 'optout' in body:
            logger.info(f"SMS opt-out request from: {from_number}")
            
            # Process opt-out
            preference_service = CommunicationPreferenceService()
            result = preference_service.handle_opt_out_request(
                phone_number=from_number,
                channel='sms',
                message_type='all',
                reason='sms_stop_reply'
            )
            
            return jsonify({
                'success': True,
                'message': 'Opt-out processed successfully'
            }), 200
        
        return jsonify({'success': True, 'message': 'Message received'}), 200
        
    except Exception as e:
        logger.error(f"Error processing SMS opt-out webhook: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500


# =====================================================
# ANALYTICS API ENDPOINTS
# =====================================================

@communication_api_bp.route('/analytics/summary', methods=['GET'])
@jwt_required()
def get_communication_summary():
    """Get overall communication performance summary"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        analytics_service = FlaskAnalyticsService()
        summary = analytics_service.get_communication_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'success': True,
            'summary': summary
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "get_communication_summary")


@communication_api_bp.route('/analytics/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_engagement(user_id: int):
    """Get user-specific engagement analytics"""
    try:
        current_user_id = get_jwt_identity()
        
        analytics_service = FlaskAnalyticsService()
        history = analytics_service.get_user_communication_history(user_id)
        
        # Calculate engagement metrics
        total_communications = len(history)
        delivered = sum(1 for comm in history if comm.delivered_at)
        opened = sum(1 for comm in history if comm.opened_at)
        clicked = sum(1 for comm in history if comm.clicked_at)
        actions = sum(1 for comm in history if comm.action_taken)
        
        engagement_metrics = {
            'total_communications': total_communications,
            'delivery_rate': delivered / total_communications if total_communications > 0 else 0,
            'open_rate': opened / total_communications if total_communications > 0 else 0,
            'click_rate': clicked / total_communications if total_communications > 0 else 0,
            'action_rate': actions / total_communications if total_communications > 0 else 0,
            'recent_communications': [
                {
                    'id': comm.id,
                    'message_type': comm.message_type,
                    'channel': comm.channel,
                    'status': comm.status,
                    'sent_at': comm.sent_at.isoformat() if comm.sent_at else None,
                    'delivered_at': comm.delivered_at.isoformat() if comm.delivered_at else None,
                    'opened_at': comm.opened_at.isoformat() if comm.opened_at else None,
                    'action_taken': comm.action_taken
                }
                for comm in history[:10]  # Last 10 communications
            ]
        }
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'engagement_metrics': engagement_metrics
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "get_user_engagement")


@communication_api_bp.route('/analytics/channel-effectiveness', methods=['GET'])
@jwt_required()
def get_channel_effectiveness():
    """Get SMS vs Email performance comparison"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        analytics_service = FlaskAnalyticsService()
        
        # Get channel-specific metrics
        sms_stats = analytics_service.get_communication_stats(
            start_date=start_date,
            end_date=end_date,
            channel='sms'
        )
        
        email_stats = analytics_service.get_communication_stats(
            start_date=start_date,
            end_date=end_date,
            channel='email'
        )
        
        # Calculate effectiveness metrics
        sms_effectiveness = {
            'channel': 'sms',
            'total_sent': sms_stats.get('total_sent', 0),
            'delivery_rate': sms_stats.get('delivery_rate', 0),
            'cost_per_message': 0.05,
            'total_cost': sms_stats.get('total_sent', 0) * 0.05,
            'engagement_rate': sms_stats.get('action_rate', 0)
        }
        
        email_effectiveness = {
            'channel': 'email',
            'total_sent': email_stats.get('total_sent', 0),
            'delivery_rate': email_stats.get('delivery_rate', 0),
            'open_rate': email_stats.get('open_rate', 0),
            'click_rate': email_stats.get('click_rate', 0),
            'cost_per_message': 0.001,
            'total_cost': email_stats.get('total_sent', 0) * 0.001,
            'engagement_rate': email_stats.get('action_rate', 0)
        }
        
        # Recommendations
        recommendations = []
        if sms_effectiveness['delivery_rate'] > email_effectiveness['delivery_rate']:
            recommendations.append("SMS has higher delivery rate - consider for critical communications")
        if email_effectiveness['engagement_rate'] > sms_effectiveness['engagement_rate']:
            recommendations.append("Email has higher engagement - consider for educational content")
        if sms_effectiveness['total_cost'] > email_effectiveness['total_cost'] * 10:
            recommendations.append("SMS costs significantly more - consider email for non-critical communications")
        
        return jsonify({
            'success': True,
            'sms': sms_effectiveness,
            'email': email_effectiveness,
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "get_channel_effectiveness")


@communication_api_bp.route('/analytics/cost-tracking', methods=['GET'])
@jwt_required()
def get_cost_tracking():
    """Get detailed cost tracking and budget analysis"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        analytics_service = FlaskAnalyticsService()
        stats = analytics_service.get_communication_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate costs
        sms_cost = stats.get('sms_sent', 0) * 0.05
        email_cost = stats.get('email_sent', 0) * 0.001
        total_cost = sms_cost + email_cost
        
        # Get budget limits from config
        daily_budget = current_app.config.get('COMMUNICATION_COSTS', {}).get('daily_budget', 100.0)
        monthly_budget = current_app.config.get('COMMUNICATION_COSTS', {}).get('monthly_budget', 3000.0)
        
        # Calculate budget usage
        budget_analysis = {
            'total_cost': total_cost,
            'sms_cost': sms_cost,
            'email_cost': email_cost,
            'daily_budget': daily_budget,
            'monthly_budget': monthly_budget,
            'daily_budget_usage': (total_cost / daily_budget) * 100 if daily_budget > 0 else 0,
            'monthly_budget_usage': (total_cost / monthly_budget) * 100 if monthly_budget > 0 else 0,
            'cost_per_message': total_cost / stats.get('total_sent', 1) if stats.get('total_sent', 0) > 0 else 0,
            'roi_analysis': {
                'total_communications': stats.get('total_sent', 0),
                'total_engagements': stats.get('total_actions', 0),
                'engagement_rate': stats.get('action_rate', 0),
                'cost_per_engagement': total_cost / stats.get('total_actions', 1) if stats.get('total_actions', 0) > 0 else 0
            }
        }
        
        # Budget alerts
        alerts = []
        if budget_analysis['daily_budget_usage'] > 80:
            alerts.append("Daily budget usage exceeds 80%")
        if budget_analysis['monthly_budget_usage'] > 80:
            alerts.append("Monthly budget usage exceeds 80%")
        if budget_analysis['cost_per_engagement'] > 1.0:
            alerts.append("Cost per engagement is high - consider optimization")
        
        return jsonify({
            'success': True,
            'cost_analysis': budget_analysis,
            'alerts': alerts
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "get_cost_tracking")


# =====================================================
# REPORTING API ENDPOINTS
# =====================================================

@communication_api_bp.route('/reports/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_report():
    """Get comprehensive dashboard report"""
    try:
        current_user_id = get_jwt_identity()
        
        reporting_service = FlaskReportingService()
        dashboard_data = reporting_service.get_dashboard_summary()
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "get_dashboard_report")


@communication_api_bp.route('/reports/performance', methods=['GET'])
@jwt_required()
def get_performance_report():
    """Get performance metrics report"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        channel = request.args.get('channel')
        
        reporting_service = FlaskReportingService()
        performance_data = reporting_service.get_performance_metrics(
            start_date=start_date,
            end_date=end_date,
            channel=channel
        )
        
        return jsonify({
            'success': True,
            'performance': performance_data
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "get_performance_report")


@communication_api_bp.route('/reports/trends', methods=['GET'])
@jwt_required()
def get_trends_report():
    """Get trend analysis report"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get parameters
        metric = request.args.get('metric', 'delivery_rate')
        period = request.args.get('period', 'daily')
        days = request.args.get('days', 30, type=int)
        
        reporting_service = FlaskReportingService()
        trends_data = reporting_service.get_trend_analysis(
            metric=metric,
            period=period,
            days=days
        )
        
        return jsonify({
            'success': True,
            'trends': trends_data
        }), 200
        
    except Exception as e:
        return handle_communication_error(e, "get_trends_report")


# =====================================================
# HEALTH CHECK ENDPOINTS
# =====================================================

@communication_api_bp.route('/health', methods=['GET'])
@jwt_required()
def communication_health_check():
    """Health check for communication system"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get orchestrator instance
        orchestrator = CommunicationOrchestrator()
        
        # Check services
        services_status = {}
        
        # Check preference service
        try:
            preference_service = CommunicationPreferenceService()
            test_prefs = preference_service.get_user_communication_prefs(1)
            services_status['preference_service'] = True
        except Exception as e:
            services_status['preference_service'] = False
            logger.error(f"Preference service health check failed: {e}")
        
        # Check analytics service
        try:
            analytics_service = FlaskAnalyticsService()
            test_analytics = analytics_service.get_communication_stats()
            services_status['analytics_service'] = True
        except Exception as e:
            services_status['analytics_service'] = False
            logger.error(f"Analytics service health check failed: {e}")
        
        # Check Celery integration
        try:
            celery_integration = orchestrator._get_celery_integration()
            services_status['celery_integration'] = celery_integration is not None
        except Exception as e:
            services_status['celery_integration'] = False
            logger.error(f"Celery integration health check failed: {e}")
        
        # Check external services
        try:
            # Check Twilio configuration
            twilio_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            services_status['twilio_configured'] = bool(twilio_sid)
        except Exception as e:
            services_status['twilio_configured'] = False
        
        try:
            # Check Resend configuration
            resend_key = current_app.config.get('RESEND_API_KEY')
            services_status['resend_configured'] = bool(resend_key)
        except Exception as e:
            services_status['resend_configured'] = False
        
        # Determine overall status
        all_healthy = all(services_status.values())
        status = "healthy" if all_healthy else "degraded"
        
        response = {
            'status': status,
            'services': services_status,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
        
        logger.info(f"Communication health check completed: {status}")
        return jsonify(response), 200 if all_healthy else 503
        
    except Exception as e:
        logger.error(f"Error in communication health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Health check failed',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# =====================================================
# ERROR HANDLERS
# =====================================================

@communication_api_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    logger.warning(f"Bad request in communication API: {error}")
    return jsonify({
        "error": "Bad request",
        "message": str(error)
    }), 400


@communication_api_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    logger.warning(f"Unauthorized request in communication API: {error}")
    return jsonify({
        "error": "Unauthorized",
        "message": "Authentication required"
    }), 401


@communication_api_bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    logger.warning(f"Resource not found in communication API: {error}")
    return jsonify({
        "error": "Not found",
        "message": "Resource not found"
    }), 404


@communication_api_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal error in communication API: {error}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500 