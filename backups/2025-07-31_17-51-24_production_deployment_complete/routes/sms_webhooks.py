import logging
from flask import Blueprint, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from ..services.twilio_sms_service import twilio_sms_service

logger = logging.getLogger(__name__)

# Create Blueprint
sms_webhooks = Blueprint('sms_webhooks', __name__)

@sms_webhooks.route('/webhook/sms', methods=['POST'])
def handle_sms_webhook():
    """
    Handle incoming SMS webhooks from Twilio
    
    This endpoint processes:
    - Opt-out requests (STOP, CANCEL, UNSUBSCRIBE)
    - Help requests (HELP, SUPPORT, INFO)
    - Opt-in requests (START, YES, SUBSCRIBE)
    - Weekly check-in responses (1-10 stress levels)
    - Unknown responses
    """
    try:
        # Get webhook data from Twilio
        webhook_data = {
            'From': request.form.get('From'),
            'To': request.form.get('To'),
            'Body': request.form.get('Body'),
            'MessageSid': request.form.get('MessageSid'),
            'AccountSid': request.form.get('AccountSid'),
            'NumMedia': request.form.get('NumMedia'),
            'MediaUrl0': request.form.get('MediaUrl0'),
            'MediaContentType0': request.form.get('MediaContentType0')
        }
        
        logger.info(f"Received SMS webhook: {webhook_data['From']} -> {webhook_data['Body']}")
        
        # Process the SMS response
        result = twilio_sms_service.handle_opt_out_responses(webhook_data)
        
        # Create TwiML response
        resp = MessagingResponse()
        
        if result.get('success'):
            action = result.get('action')
            
            if action == 'opted_out':
                # Send opt-out confirmation
                resp.message(result.get('confirmation_message', 
                    "You have been unsubscribed from MINGUS SMS alerts. Reply START to resubscribe."))
                
            elif action == 'opted_in':
                # Send welcome message
                resp.message(result.get('welcome_message', 
                    "Welcome to MINGUS SMS alerts! You'll receive important financial updates and wellness check-ins."))
                
            elif action == 'help_requested':
                # Send help information
                resp.message(result.get('help_message', 
                    "Need help? Call +1-800-MINGUS-1 or email support@mingusapp.com. Reply STOP to unsubscribe."))
                
            elif action == 'weekly_checkin':
                # Send personalized response based on stress level
                resp.message(result.get('response_message', 
                    "Thanks for checking in! We're here to support your financial wellness journey."))
                
            elif action == 'unknown_response':
                # Send generic help message
                resp.message(result.get('help_message', 
                    "Thanks for your message! For support, call +1-800-MINGUS-1 or reply HELP. Reply STOP to unsubscribe."))
                
            else:
                # Default response
                resp.message("Thanks for your message! For support, call +1-800-MINGUS-1 or reply HELP.")
        else:
            # Error handling
            logger.error(f"Error processing SMS webhook: {result.get('error')}")
            resp.message("Sorry, there was an error processing your message. Please call +1-800-MINGUS-1 for support.")
        
        return str(resp)
        
    except Exception as e:
        logger.error(f"Error handling SMS webhook: {e}")
        
        # Return error response
        resp = MessagingResponse()
        resp.message("Sorry, there was an error processing your message. Please call +1-800-MINGUS-1 for support.")
        return str(resp)

@sms_webhooks.route('/webhook/sms/status', methods=['POST'])
def handle_sms_status_webhook():
    """
    Handle SMS delivery status webhooks from Twilio
    
    This endpoint receives delivery status updates for sent SMS messages
    """
    try:
        # Get status webhook data
        status_data = {
            'MessageSid': request.form.get('MessageSid'),
            'MessageStatus': request.form.get('MessageStatus'),
            'ErrorCode': request.form.get('ErrorCode'),
            'ErrorMessage': request.form.get('ErrorMessage'),
            'To': request.form.get('To'),
            'From': request.form.get('From'),
            'DateSent': request.form.get('DateSent'),
            'DateUpdated': request.form.get('DateUpdated')
        }
        
        logger.info(f"Received SMS status webhook: {status_data['MessageSid']} -> {status_data['MessageStatus']}")
        
        # Update delivery status in tracking system
        if status_data['MessageSid']:
            tracking_result = twilio_sms_service.track_delivery_status(status_data['MessageSid'])
            
            if tracking_result.get('success'):
                logger.info(f"Updated SMS delivery status: {status_data['MessageSid']} -> {status_data['MessageStatus']}")
            else:
                logger.error(f"Failed to update SMS delivery status: {tracking_result.get('error')}")
        
        # Return success response
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error handling SMS status webhook: {e}")
        return jsonify({'error': str(e)}), 500

@sms_webhooks.route('/webhook/sms/opt-in', methods=['POST'])
def handle_sms_opt_in():
    """
    Handle SMS opt-in requests
    
    This endpoint allows users to opt-in to SMS notifications
    """
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        user_id = data.get('user_id')
        
        if not phone_number:
            return jsonify({'error': 'Phone number is required'}), 400
        
        # Validate phone number
        if not twilio_sms_service.validate_phone_number(phone_number):
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        # Mark user as opted in
        if twilio_sms_service.redis_client:
            opt_in_key = f"sms_opt_in:{phone_number}"
            if user_id:
                opt_in_key = f"sms_opt_in:{user_id}"
            
            twilio_sms_service.redis_client.set(opt_in_key, "opted_in", ex=86400 * 365)  # 1 year
        
        # Send welcome SMS
        welcome_result = twilio_sms_service.send_sms(
            phone_number=phone_number,
            message="Welcome to MINGUS SMS alerts! You'll receive important financial updates and wellness check-ins. Reply STOP to unsubscribe anytime.",
            priority_level=twilio_sms_service.SMSPriority.LOW,
            user_id=user_id
        )
        
        if welcome_result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Successfully opted in to SMS notifications',
                'message_sid': welcome_result.get('message_sid')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send welcome message',
                'details': welcome_result.get('error')
            }), 500
        
    except Exception as e:
        logger.error(f"Error handling SMS opt-in: {e}")
        return jsonify({'error': str(e)}), 500

@sms_webhooks.route('/webhook/sms/opt-out', methods=['POST'])
def handle_sms_opt_out():
    """
    Handle SMS opt-out requests
    
    This endpoint allows users to opt-out of SMS notifications
    """
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        user_id = data.get('user_id')
        
        if not phone_number:
            return jsonify({'error': 'Phone number is required'}), 400
        
        # Mark user as opted out
        if twilio_sms_service.redis_client:
            opt_out_key = f"sms_opt_in:{phone_number}"
            if user_id:
                opt_out_key = f"sms_opt_in:{user_id}"
            
            twilio_sms_service.redis_client.set(opt_out_key, "opted_out", ex=86400 * 365)  # 1 year
        
        # Send confirmation SMS
        confirmation_result = twilio_sms_service.send_sms(
            phone_number=phone_number,
            message=f"You have been unsubscribed from MINGUS SMS alerts. Reply START to resubscribe. For support, call {twilio_sms_service.tcpa_compliance['support_phone']}.",
            priority_level=twilio_sms_service.SMSPriority.LOW,
            user_id=user_id
        )
        
        if confirmation_result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Successfully opted out of SMS notifications',
                'message_sid': confirmation_result.get('message_sid')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send confirmation message',
                'details': confirmation_result.get('error')
            }), 500
        
    except Exception as e:
        logger.error(f"Error handling SMS opt-out: {e}")
        return jsonify({'error': str(e)}), 500

@sms_webhooks.route('/api/sms/status/<message_sid>', methods=['GET'])
def get_sms_status(message_sid):
    """
    Get SMS delivery status by message SID
    """
    try:
        result = twilio_sms_service.track_delivery_status(message_sid)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 404
        
    except Exception as e:
        logger.error(f"Error getting SMS status: {e}")
        return jsonify({'error': str(e)}), 500

@sms_webhooks.route('/api/sms/statistics', methods=['GET'])
def get_sms_statistics():
    """
    Get SMS statistics and cost tracking
    """
    try:
        days = request.args.get('days', 30, type=int)
        stats = twilio_sms_service.get_sms_statistics(days)
        
        if 'error' in stats:
            return jsonify(stats), 500
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting SMS statistics: {e}")
        return jsonify({'error': str(e)}), 500

@sms_webhooks.route('/api/sms/templates', methods=['GET'])
def get_sms_templates():
    """
    Get available SMS templates
    """
    try:
        templates = {}
        for name, template in twilio_sms_service.sms_templates.items():
            templates[name] = {
                'name': template.name,
                'priority': template.priority.value,
                'max_retries': template.max_retries,
                'cost_per_message': template.cost_per_message,
                'variables': template.variables
            }
        
        return jsonify({
            'success': True,
            'templates': templates
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting SMS templates: {e}")
        return jsonify({'error': str(e)}), 500

@sms_webhooks.route('/api/sms/send', methods=['POST'])
def send_sms():
    """
    Send SMS message via API
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['phone_number', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Send SMS
        result = twilio_sms_service.send_sms(
            phone_number=data['phone_number'],
            message=data['message'],
            priority_level=getattr(twilio_sms_service.SMSPriority, data.get('priority', 'MEDIUM').upper()),
            template_name=data.get('template_name'),
            template_vars=data.get('template_vars'),
            user_id=data.get('user_id')
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return jsonify({'error': str(e)}), 500 