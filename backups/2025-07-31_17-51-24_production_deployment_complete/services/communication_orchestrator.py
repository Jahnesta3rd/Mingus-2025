"""
Communication Orchestrator Service
Main Flask service for orchestrating smart communications with user preferences,
Celery task routing, analytics tracking, and failure handling
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.exc import SQLAlchemyError

from ..database import get_flask_db_session, get_current_db_session
from ..services.communication_preference_service import CommunicationPreferenceService
from ..services.analytics_service import AnalyticsService
from ..services.flask_analytics_service import FlaskAnalyticsService
from ..integration.flask_celery_integration import (
    execute_communication_task, 
    execute_analytics_task,
    get_flask_celery_integration
)

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Communication trigger types"""
    FINANCIAL_ALERT = "financial_alert"
    PAYMENT_REMINDER = "payment_reminder"
    WEEKLY_CHECKIN = "weekly_checkin"
    MILESTONE_CELEBRATION = "milestone_celebration"
    MONTHLY_REPORT = "monthly_report"
    CAREER_INSIGHT = "career_insight"
    EDUCATIONAL_CONTENT = "educational_content"
    ONBOARDING_SEQUENCE = "onboarding_sequence"
    BEHAVIORAL_TRIGGER = "behavioral_trigger"
    ENGAGEMENT_REACTIVATION = "engagement_reactivation"


class CommunicationChannel(Enum):
    """Communication channels"""
    SMS = "sms"
    EMAIL = "email"
    BOTH = "both"


class CommunicationPriority(Enum):
    """Communication priorities"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class CommunicationRequest:
    """Communication request data structure"""
    user_id: int
    trigger_type: TriggerType
    channel: CommunicationChannel
    priority: CommunicationPriority
    data: Dict[str, Any]
    scheduled_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class CommunicationResult:
    """Communication result data structure"""
    success: bool
    message_id: Optional[str] = None
    task_id: Optional[str] = None
    cost: float = 0.0
    error_message: Optional[str] = None
    fallback_used: bool = False
    analytics_tracked: bool = False


class CommunicationOrchestrator:
    """
    Main communication orchestrator service
    Handles smart communication routing, user preferences, and analytics tracking
    """
    
    def __init__(self):
        """Initialize the communication orchestrator"""
        self.preference_service = CommunicationPreferenceService()
        self.analytics_service = AnalyticsService()
        self.flask_analytics_service = FlaskAnalyticsService()
        self._celery_integration = None
    
    def _get_celery_integration(self):
        """Get Celery integration instance"""
        if not self._celery_integration:
            self._celery_integration = get_flask_celery_integration()
        return self._celery_integration
    
    def send_smart_communication(
        self, 
        user_id: int, 
        trigger_type: TriggerType, 
        data: Dict[str, Any],
        channel: Optional[CommunicationChannel] = None,
        priority: Optional[CommunicationPriority] = None,
        scheduled_time: Optional[datetime] = None
    ) -> CommunicationResult:
        """
        Send smart communication based on user preferences and trigger type
        
        Args:
            user_id: User ID
            trigger_type: Type of communication trigger
            data: Communication data
            channel: Preferred channel (optional, will use user preferences if not provided)
            priority: Communication priority (optional, will determine based on trigger type)
            scheduled_time: Scheduled send time (optional)
            
        Returns:
            CommunicationResult with success status and details
        """
        try:
            # Create communication request
            request = self._create_communication_request(
                user_id, trigger_type, data, channel, priority, scheduled_time
            )
            
            # Validate user preferences and consent
            validation_result = self._validate_communication_request(request)
            if not validation_result['valid']:
                return CommunicationResult(
                    success=False,
                    error_message=validation_result['reason']
                )
            
            # Determine optimal channel and timing
            optimized_request = self._optimize_communication_request(request)
            
            # Execute communication
            result = self._execute_communication(optimized_request)
            
            # Track analytics
            self._track_communication_analytics(result, optimized_request)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in send_smart_communication for user {user_id}: {e}")
            return CommunicationResult(
                success=False,
                error_message=str(e)
            )
    
    def _create_communication_request(
        self,
        user_id: int,
        trigger_type: TriggerType,
        data: Dict[str, Any],
        channel: Optional[CommunicationChannel],
        priority: Optional[CommunicationPriority],
        scheduled_time: Optional[datetime]
    ) -> CommunicationRequest:
        """Create communication request with defaults"""
        
        # Determine default priority based on trigger type
        if not priority:
            priority = self._get_default_priority(trigger_type)
        
        # Determine default channel based on trigger type
        if not channel:
            channel = self._get_default_channel(trigger_type)
        
        return CommunicationRequest(
            user_id=user_id,
            trigger_type=trigger_type,
            channel=channel,
            priority=priority,
            data=data,
            scheduled_time=scheduled_time
        )
    
    def _get_default_priority(self, trigger_type: TriggerType) -> CommunicationPriority:
        """Get default priority for trigger type"""
        priority_map = {
            TriggerType.FINANCIAL_ALERT: CommunicationPriority.CRITICAL,
            TriggerType.PAYMENT_REMINDER: CommunicationPriority.HIGH,
            TriggerType.WEEKLY_CHECKIN: CommunicationPriority.MEDIUM,
            TriggerType.MILESTONE_CELEBRATION: CommunicationPriority.MEDIUM,
            TriggerType.MONTHLY_REPORT: CommunicationPriority.LOW,
            TriggerType.CAREER_INSIGHT: CommunicationPriority.LOW,
            TriggerType.EDUCATIONAL_CONTENT: CommunicationPriority.LOW,
            TriggerType.ONBOARDING_SEQUENCE: CommunicationPriority.HIGH,
            TriggerType.BEHAVIORAL_TRIGGER: CommunicationPriority.MEDIUM,
            TriggerType.ENGAGEMENT_REACTIVATION: CommunicationPriority.HIGH,
        }
        return priority_map.get(trigger_type, CommunicationPriority.MEDIUM)
    
    def _get_default_channel(self, trigger_type: TriggerType) -> CommunicationChannel:
        """Get default channel for trigger type"""
        channel_map = {
            TriggerType.FINANCIAL_ALERT: CommunicationChannel.SMS,
            TriggerType.PAYMENT_REMINDER: CommunicationChannel.SMS,
            TriggerType.WEEKLY_CHECKIN: CommunicationChannel.SMS,
            TriggerType.MILESTONE_CELEBRATION: CommunicationChannel.EMAIL,
            TriggerType.MONTHLY_REPORT: CommunicationChannel.EMAIL,
            TriggerType.CAREER_INSIGHT: CommunicationChannel.EMAIL,
            TriggerType.EDUCATIONAL_CONTENT: CommunicationChannel.EMAIL,
            TriggerType.ONBOARDING_SEQUENCE: CommunicationChannel.BOTH,
            TriggerType.BEHAVIORAL_TRIGGER: CommunicationChannel.SMS,
            TriggerType.ENGAGEMENT_REACTIVATION: CommunicationChannel.BOTH,
        }
        return channel_map.get(trigger_type, CommunicationChannel.EMAIL)
    
    def _validate_communication_request(self, request: CommunicationRequest) -> Dict[str, Any]:
        """Validate communication request against user preferences"""
        try:
            # Check if user exists and is active
            user_prefs = self.preference_service.get_user_communication_prefs(request.user_id)
            if not user_prefs:
                return {
                    'valid': False,
                    'reason': f'User {request.user_id} not found or no preferences set'
                }
            
            # Check if user has opted out of communications
            if not user_prefs.get('sms_enabled', True) and not user_prefs.get('email_enabled', True):
                return {
                    'valid': False,
                    'reason': f'User {request.user_id} has opted out of all communications'
                }
            
            # Check channel-specific preferences
            if request.channel == CommunicationChannel.SMS:
                if not user_prefs.get('sms_enabled', True):
                    return {
                        'valid': False,
                        'reason': f'User {request.user_id} has opted out of SMS communications'
                    }
            elif request.channel == CommunicationChannel.EMAIL:
                if not user_prefs.get('email_enabled', True):
                    return {
                        'valid': False,
                        'reason': f'User {request.user_id} has opted out of email communications'
                    }
            
            # Check consent for specific message type
            consent_result = self.preference_service.check_consent_for_message_type(
                request.user_id,
                request.trigger_type.value,
                request.channel.value
            )
            
            if not consent_result['can_send']:
                return {
                    'valid': False,
                    'reason': consent_result.get('reason', 'Consent check failed')
                }
            
            # Check frequency limits
            frequency_check = self._check_frequency_limits(request)
            if not frequency_check['valid']:
                return {
                    'valid': False,
                    'reason': frequency_check['reason']
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating communication request: {e}")
            return {
                'valid': False,
                'reason': f'Validation error: {str(e)}'
            }
    
    def _check_frequency_limits(self, request: CommunicationRequest) -> Dict[str, Any]:
        """Check frequency limits for user communications"""
        try:
            # Get recent communications for this user and trigger type
            recent_communications = self.analytics_service.get_user_communication_history(
                request.user_id,
                limit=10,
                message_type=request.trigger_type.value
            )
            
            if not recent_communications:
                return {'valid': True}
            
            # Check daily limit (max 5 communications per day)
            today = datetime.utcnow().date()
            today_count = sum(
                1 for comm in recent_communications 
                if comm.sent_at.date() == today
            )
            
            if today_count >= 5:
                return {
                    'valid': False,
                    'reason': f'Daily communication limit reached for user {request.user_id}'
                }
            
            # Check hourly limit (max 2 communications per hour)
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            hourly_count = sum(
                1 for comm in recent_communications 
                if comm.sent_at >= hour_ago
            )
            
            if hourly_count >= 2:
                return {
                    'valid': False,
                    'reason': f'Hourly communication limit reached for user {request.user_id}'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error checking frequency limits: {e}")
            return {'valid': True}  # Allow communication if check fails
    
    def _optimize_communication_request(self, request: CommunicationRequest) -> CommunicationRequest:
        """Optimize communication request based on user preferences and analytics"""
        try:
            # Get user preferences
            user_prefs = self.preference_service.get_user_communication_prefs(request.user_id)
            
            # Optimize channel selection
            optimized_channel = self._optimize_channel_selection(request, user_prefs)
            
            # Optimize send time
            optimized_time = self._optimize_send_time(request, user_prefs)
            
            # Create optimized request
            return CommunicationRequest(
                user_id=request.user_id,
                trigger_type=request.trigger_type,
                channel=optimized_channel,
                priority=request.priority,
                data=request.data,
                scheduled_time=optimized_time,
                retry_count=request.retry_count,
                max_retries=request.max_retries
            )
            
        except Exception as e:
            logger.error(f"Error optimizing communication request: {e}")
            return request  # Return original request if optimization fails
    
    def _optimize_channel_selection(
        self, 
        request: CommunicationRequest, 
        user_prefs: Dict[str, Any]
    ) -> CommunicationChannel:
        """Optimize channel selection based on user preferences and engagement"""
        try:
            # If user has strong preference, respect it
            if request.channel == CommunicationChannel.SMS and not user_prefs.get('sms_enabled', True):
                return CommunicationChannel.EMAIL
            elif request.channel == CommunicationChannel.EMAIL and not user_prefs.get('email_enabled', True):
                return CommunicationChannel.SMS
            
            # Check engagement rates for each channel
            sms_engagement = self._get_channel_engagement_rate(request.user_id, 'sms')
            email_engagement = self._get_channel_engagement_rate(request.user_id, 'email')
            
            # If both channels are available, choose the one with better engagement
            if (user_prefs.get('sms_enabled', True) and 
                user_prefs.get('email_enabled', True)):
                
                if sms_engagement > email_engagement:
                    return CommunicationChannel.SMS
                else:
                    return CommunicationChannel.EMAIL
            
            # Default to original channel
            return request.channel
            
        except Exception as e:
            logger.error(f"Error optimizing channel selection: {e}")
            return request.channel
    
    def _get_channel_engagement_rate(self, user_id: int, channel: str) -> float:
        """Get engagement rate for a specific channel"""
        try:
            # Get recent communications for this user and channel
            recent_communications = self.analytics_service.get_user_communication_history(
                user_id,
                limit=50,
                channel=channel
            )
            
            if not recent_communications:
                return 0.0
            
            # Calculate engagement rate (opens/clicks for email, actions for SMS)
            total_sent = len(recent_communications)
            engaged = sum(
                1 for comm in recent_communications
                if (channel == 'email' and comm.opened_at) or
                   (channel == 'sms' and comm.action_taken)
            )
            
            return engaged / total_sent if total_sent > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error getting channel engagement rate: {e}")
            return 0.0
    
    def _optimize_send_time(
        self, 
        request: CommunicationRequest, 
        user_prefs: Dict[str, Any]
    ) -> Optional[datetime]:
        """Optimize send time based on user preferences and engagement patterns"""
        try:
            # If already scheduled, respect the schedule
            if request.scheduled_time:
                return request.scheduled_time
            
            # Get optimal send time from preferences
            optimal_time = self.preference_service.get_optimal_send_time(
                request.user_id,
                request.channel.value
            )
            
            if optimal_time:
                # Calculate next optimal send time
                now = datetime.utcnow()
                optimal_datetime = datetime.combine(now.date(), optimal_time)
                
                # If optimal time has passed today, schedule for tomorrow
                if optimal_datetime <= now:
                    optimal_datetime += timedelta(days=1)
                
                return optimal_datetime
            
            # Default to immediate send for critical communications
            if request.priority == CommunicationPriority.CRITICAL:
                return None
            
            # Default to next business day for non-critical communications
            return self._get_next_business_day()
            
        except Exception as e:
            logger.error(f"Error optimizing send time: {e}")
            return None
    
    def _get_next_business_day(self) -> datetime:
        """Get next business day datetime"""
        now = datetime.utcnow()
        next_day = now + timedelta(days=1)
        
        # Skip weekends
        while next_day.weekday() >= 5:  # Saturday = 5, Sunday = 6
            next_day += timedelta(days=1)
        
        # Set to 9 AM
        return next_day.replace(hour=9, minute=0, second=0, microsecond=0)
    
    def _execute_communication(self, request: CommunicationRequest) -> CommunicationResult:
        """Execute communication via Celery tasks"""
        try:
            # Determine Celery task based on trigger type and channel
            task_name = self._get_celery_task_name(request)
            
            # Prepare task parameters
            task_params = self._prepare_task_parameters(request)
            
            # Execute task
            celery_integration = self._get_celery_integration()
            if not celery_integration:
                return CommunicationResult(
                    success=False,
                    error_message="Celery integration not available"
                )
            
            # Execute task with context
            task_result = execute_communication_task(
                task_name,
                request.user_id,
                **task_params
            )
            
            # Handle task result
            if task_result and task_result.id:
                return CommunicationResult(
                    success=True,
                    task_id=task_result.id,
                    cost=self._estimate_communication_cost(request)
                )
            else:
                return CommunicationResult(
                    success=False,
                    error_message="Task execution failed"
                )
                
        except Exception as e:
            logger.error(f"Error executing communication: {e}")
            
            # Try fallback communication
            fallback_result = self._execute_fallback_communication(request)
            if fallback_result.success:
                fallback_result.fallback_used = True
                return fallback_result
            
            return CommunicationResult(
                success=False,
                error_message=str(e)
            )
    
    def _get_celery_task_name(self, request: CommunicationRequest) -> str:
        """Get Celery task name based on trigger type and channel"""
        task_map = {
            (TriggerType.FINANCIAL_ALERT, CommunicationChannel.SMS): 'backend.tasks.mingus_celery_tasks.send_critical_financial_alert',
            (TriggerType.PAYMENT_REMINDER, CommunicationChannel.SMS): 'backend.tasks.mingus_celery_tasks.send_payment_reminder',
            (TriggerType.WEEKLY_CHECKIN, CommunicationChannel.SMS): 'backend.tasks.mingus_celery_tasks.send_weekly_checkin',
            (TriggerType.MILESTONE_CELEBRATION, CommunicationChannel.SMS): 'backend.tasks.mingus_celery_tasks.send_milestone_reminder',
            (TriggerType.MONTHLY_REPORT, CommunicationChannel.EMAIL): 'backend.tasks.mingus_celery_tasks.send_monthly_report',
            (TriggerType.CAREER_INSIGHT, CommunicationChannel.EMAIL): 'backend.tasks.mingus_celery_tasks.send_career_insights',
            (TriggerType.EDUCATIONAL_CONTENT, CommunicationChannel.EMAIL): 'backend.tasks.mingus_celery_tasks.send_educational_content',
            (TriggerType.ONBOARDING_SEQUENCE, CommunicationChannel.EMAIL): 'backend.tasks.mingus_celery_tasks.send_onboarding_sequence',
        }
        
        # Default task based on channel
        default_tasks = {
            CommunicationChannel.SMS: 'backend.tasks.mingus_celery_tasks.send_sms_daily',
            CommunicationChannel.EMAIL: 'backend.tasks.mingus_celery_tasks.send_email_reports',
        }
        
        return task_map.get(
            (request.trigger_type, request.channel),
            default_tasks.get(request.channel, 'backend.tasks.mingus_celery_tasks.send_email_reports')
        )
    
    def _prepare_task_parameters(self, request: CommunicationRequest) -> Dict[str, Any]:
        """Prepare parameters for Celery task"""
        return {
            'trigger_type': request.trigger_type.value,
            'channel': request.channel.value,
            'priority': request.priority.value,
            'data': request.data,
            'scheduled_time': request.scheduled_time.isoformat() if request.scheduled_time else None,
            'retry_count': request.retry_count,
            'max_retries': request.max_retries
        }
    
    def _estimate_communication_cost(self, request: CommunicationRequest) -> float:
        """Estimate communication cost"""
        cost_map = {
            CommunicationChannel.SMS: 0.05,  # $0.05 per SMS
            CommunicationChannel.EMAIL: 0.001,  # $0.001 per email
        }
        return cost_map.get(request.channel, 0.01)
    
    def _execute_fallback_communication(self, request: CommunicationRequest) -> CommunicationResult:
        """Execute fallback communication when primary fails"""
        try:
            # Try alternative channel
            fallback_channel = (
                CommunicationChannel.EMAIL if request.channel == CommunicationChannel.SMS
                else CommunicationChannel.SMS
            )
            
            fallback_request = CommunicationRequest(
                user_id=request.user_id,
                trigger_type=request.trigger_type,
                channel=fallback_channel,
                priority=request.priority,
                data=request.data,
                scheduled_time=request.scheduled_time,
                retry_count=request.retry_count + 1,
                max_retries=request.max_retries
            )
            
            # Validate fallback request
            validation_result = self._validate_communication_request(fallback_request)
            if not validation_result['valid']:
                return CommunicationResult(
                    success=False,
                    error_message=f"Fallback communication failed: {validation_result['reason']}"
                )
            
            # Execute fallback
            return self._execute_communication(fallback_request)
            
        except Exception as e:
            logger.error(f"Error executing fallback communication: {e}")
            return CommunicationResult(
                success=False,
                error_message=f"Fallback communication failed: {str(e)}"
            )
    
    def _track_communication_analytics(self, result: CommunicationResult, request: CommunicationRequest):
        """Track communication analytics"""
        try:
            if result.success:
                # Track successful communication
                self.flask_analytics_service.track_message_sent(
                    user_id=request.user_id,
                    channel=request.channel.value,
                    message_type=request.trigger_type.value,
                    cost=result.cost
                )
                
                result.analytics_tracked = True
                logger.info(f"Analytics tracked for communication to user {request.user_id}")
            else:
                # Track failed communication
                self.flask_analytics_service.track_message_sent(
                    user_id=request.user_id,
                    channel=request.channel.value,
                    message_type=request.trigger_type.value,
                    cost=0.0
                )
                
                logger.warning(f"Failed communication tracked for user {request.user_id}: {result.error_message}")
                
        except Exception as e:
            logger.error(f"Error tracking communication analytics: {e}")
    
    def get_communication_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a communication task"""
        try:
            celery_integration = self._get_celery_integration()
            if not celery_integration or not celery_integration.celery_app:
                return {'status': 'unknown', 'error': 'Celery not available'}
            
            # Get task result
            task_result = celery_integration.celery_app.AsyncResult(task_id)
            
            return {
                'task_id': task_id,
                'status': task_result.status,
                'result': task_result.result if task_result.ready() else None,
                'info': task_result.info if hasattr(task_result, 'info') else None
            }
            
        except Exception as e:
            logger.error(f"Error getting communication status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def cancel_communication(self, task_id: str) -> bool:
        """Cancel a scheduled communication"""
        try:
            celery_integration = self._get_celery_integration()
            if not celery_integration or not celery_integration.celery_app:
                return False
            
            # Revoke task
            celery_integration.celery_app.control.revoke(task_id, terminate=True)
            
            logger.info(f"Communication task {task_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling communication: {e}")
            return False


# Global orchestrator instance
communication_orchestrator = None


def get_communication_orchestrator() -> CommunicationOrchestrator:
    """Get global communication orchestrator instance"""
    global communication_orchestrator
    if not communication_orchestrator:
        communication_orchestrator = CommunicationOrchestrator()
    return communication_orchestrator


# Convenience functions for easy usage
def send_smart_communication(
    user_id: int,
    trigger_type: TriggerType,
    data: Dict[str, Any],
    channel: Optional[CommunicationChannel] = None,
    priority: Optional[CommunicationPriority] = None,
    scheduled_time: Optional[datetime] = None
) -> CommunicationResult:
    """Convenience function to send smart communication"""
    orchestrator = get_communication_orchestrator()
    return orchestrator.send_smart_communication(
        user_id, trigger_type, data, channel, priority, scheduled_time
    )


def get_communication_status(task_id: str) -> Dict[str, Any]:
    """Convenience function to get communication status"""
    orchestrator = get_communication_orchestrator()
    return orchestrator.get_communication_status(task_id)


def cancel_communication(task_id: str) -> bool:
    """Convenience function to cancel communication"""
    orchestrator = get_communication_orchestrator()
    return orchestrator.cancel_communication(task_id) 