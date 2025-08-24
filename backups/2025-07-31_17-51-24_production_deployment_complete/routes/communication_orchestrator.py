"""
Communication Orchestrator API Endpoints
Flask API endpoints for the communication orchestrator service
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging
from typing import Dict, Any

from ..services.communication_orchestrator import (
    CommunicationOrchestrator,
    TriggerType,
    CommunicationChannel,
    CommunicationPriority,
    send_smart_communication,
    get_communication_status,
    cancel_communication
)

logger = logging.getLogger(__name__)

# Create blueprint
communication_orchestrator_bp = Blueprint('communication_orchestrator', __name__)


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


@communication_orchestrator_bp.route('/api/communication/send', methods=['POST'])
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
        "channel": "sms",  // optional
        "priority": "critical",  // optional
        "scheduled_time": "2025-01-27T10:00:00Z"  // optional
    }
    
    Returns:
    {
        "success": true,
        "task_id": "abc123",
        "cost": 0.05,
        "message": "Communication scheduled successfully"
    }
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested communication send")
        
        # Parse request data
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
        logger.error(f"Error in send_communication endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@communication_orchestrator_bp.route('/api/communication/status/<task_id>', methods=['GET'])
@jwt_required()
def get_communication_task_status(task_id: str):
    """
    Get status of a communication task
    
    Args:
        task_id: Celery task ID
        
    Returns:
    {
        "task_id": "abc123",
        "status": "SUCCESS",
        "result": {...},
        "info": {...}
    }
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested status for task {task_id}")
        
        # Get task status
        status = get_communication_status(task_id)
        
        if 'error' in status:
            return jsonify(status), 500
        
        logger.info(f"Task status retrieved for {task_id}: {status['status']}")
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting communication status for task {task_id}: {e}")
        return jsonify({
            'error': 'Failed to get task status',
            'details': str(e)
        }), 500


@communication_orchestrator_bp.route('/api/communication/cancel/<task_id>', methods=['POST'])
@jwt_required()
def cancel_communication_task(task_id: str):
    """
    Cancel a scheduled communication task
    
    Args:
        task_id: Celery task ID
        
    Returns:
    {
        "success": true,
        "message": "Communication cancelled successfully"
    }
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested cancellation for task {task_id}")
        
        # Cancel task
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
        logger.error(f"Error cancelling communication task {task_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to cancel communication',
            'details': str(e)
        }), 500


@communication_orchestrator_bp.route('/api/communication/batch', methods=['POST'])
@jwt_required()
def send_batch_communications():
    """
    Send multiple communications in batch
    
    Request Body:
    {
        "communications": [
            {
                "user_id": 123,
                "trigger_type": "financial_alert",
                "data": {...},
                "channel": "sms",
                "priority": "critical"
            },
            {
                "user_id": 456,
                "trigger_type": "weekly_checkin",
                "data": {...},
                "channel": "email"
            }
        ]
    }
    
    Returns:
    {
        "success": true,
        "results": [
            {
                "user_id": 123,
                "success": true,
                "task_id": "abc123",
                "cost": 0.05
            },
            {
                "user_id": 456,
                "success": false,
                "error": "User has opted out"
            }
        ],
        "summary": {
            "total": 2,
            "successful": 1,
            "failed": 1,
            "total_cost": 0.05
        }
    }
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested batch communication send")
        
        # Parse request data
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
        logger.error(f"Error in batch communication endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@communication_orchestrator_bp.route('/api/communication/health', methods=['GET'])
@jwt_required()
def communication_health_check():
    """
    Health check for communication orchestrator
    
    Returns:
    {
        "status": "healthy",
        "services": {
            "preference_service": true,
            "analytics_service": true,
            "celery_integration": true
        },
        "timestamp": "2025-01-27T10:00:00Z"
    }
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested communication health check")
        
        # Get orchestrator instance
        orchestrator = CommunicationOrchestrator()
        
        # Check services
        services_status = {}
        
        # Check preference service
        try:
            test_prefs = orchestrator.preference_service.get_user_communication_prefs(1)
            services_status['preference_service'] = True
        except Exception as e:
            services_status['preference_service'] = False
            logger.error(f"Preference service health check failed: {e}")
        
        # Check analytics service
        try:
            test_analytics = orchestrator.analytics_service.get_user_communication_history(1, limit=1)
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
        
        # Determine overall status
        all_healthy = all(services_status.values())
        status = "healthy" if all_healthy else "degraded"
        
        response = {
            'status': status,
            'services': services_status,
            'timestamp': datetime.utcnow().isoformat()
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


@communication_orchestrator_bp.route('/api/communication/trigger-types', methods=['GET'])
@jwt_required()
def get_trigger_types():
    """
    Get available trigger types
    
    Returns:
    {
        "trigger_types": [
            {
                "value": "financial_alert",
                "name": "Financial Alert",
                "description": "Critical financial notifications",
                "default_channel": "sms",
                "default_priority": "critical"
            }
        ]
    }
    """
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
        logger.error(f"Error getting trigger types: {e}")
        return jsonify({
            'error': 'Failed to get trigger types',
            'details': str(e)
        }), 500


# Error handlers
@communication_orchestrator_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    logger.warning(f"Bad request in communication orchestrator API: {error}")
    return jsonify({
        "error": "Bad request",
        "message": str(error)
    }), 400


@communication_orchestrator_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal error in communication orchestrator API: {error}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500 