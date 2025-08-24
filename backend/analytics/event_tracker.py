"""
Event Tracker for MINGUS Analytics
==================================

Comprehensive analytics event tracking system providing:
- Subscription lifecycle event tracking
- Feature access event tracking
- Conversion and churn event tracking
- Business metrics tracking
- Event aggregation and reporting
- Real-time analytics
- Performance monitoring

Author: MINGUS Development Team
Date: January 2025
"""

import logging
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid

from ..config.base import Config
from ..models.analytics import AnalyticsEvent, EventMetrics

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Analytics event types"""
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    TRIAL_ENDING = "trial_ending"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    FEATURE_ACCESS_GRANTED = "feature_access_granted"
    FEATURE_ACCESS_REVOKED = "feature_access_revoked"
    FEATURE_ACCESS_CHANGED = "feature_access_changed"
    CONVERSION = "conversion"
    CHURN = "churn"
    TRIAL_CONVERSION_OPPORTUNITY = "trial_conversion_opportunity"
    USER_SIGNUP = "user_signup"
    USER_LOGIN = "user_login"
    FEATURE_USAGE = "feature_usage"


class EventCategory(Enum):
    """Event categories"""
    SUBSCRIPTION = "subscription"
    FEATURE = "feature"
    USER = "user"
    BUSINESS = "business"
    PAYMENT = "payment"


@dataclass
class EventData:
    """Event data structure"""
    event_id: str
    event_type: EventType
    event_category: EventCategory
    user_id: str
    customer_id: str
    timestamp: datetime
    properties: Dict[str, Any]
    session_id: Optional[str] = None
    source: str = "webhook"
    version: str = "1.0"


@dataclass
class EventResult:
    """Event result data structure"""
    success: bool
    event_id: str
    event_name: str
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class EventTracker:
    """Comprehensive analytics event tracking service"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Event tracking configuration
        self.tracking_config = {
            'enabled': True,
            'batch_size': 100,
            'flush_interval_seconds': 60,
            'max_retry_attempts': 3,
            'event_ttl_days': 365,
            'real_time_tracking': True,
            'aggregation_enabled': True
        }
        
        # Event definitions
        self.event_definitions = {
            EventType.SUBSCRIPTION_CREATED: {
                'category': EventCategory.SUBSCRIPTION,
                'properties': ['subscription_id', 'subscription_tier', 'amount', 'currency', 'billing_cycle'],
                'metrics': ['subscription_count', 'revenue', 'conversion_rate']
            },
            EventType.SUBSCRIPTION_UPDATED: {
                'category': EventCategory.SUBSCRIPTION,
                'properties': ['subscription_id', 'old_tier', 'new_tier', 'amount_change', 'reason'],
                'metrics': ['upgrade_rate', 'downgrade_rate', 'revenue_change']
            },
            EventType.SUBSCRIPTION_CANCELLED: {
                'category': EventCategory.SUBSCRIPTION,
                'properties': ['subscription_id', 'subscription_tier', 'cancellation_reason', 'retention_attempts'],
                'metrics': ['churn_rate', 'retention_rate', 'lifetime_value']
            },
            EventType.FEATURE_ACCESS_GRANTED: {
                'category': EventCategory.FEATURE,
                'properties': ['feature_name', 'access_level', 'subscription_tier', 'grant_reason'],
                'metrics': ['feature_adoption_rate', 'feature_usage_rate']
            },
            EventType.FEATURE_ACCESS_REVOKED: {
                'category': EventCategory.FEATURE,
                'properties': ['feature_name', 'access_level', 'revoke_reason', 'subscription_tier'],
                'metrics': ['feature_removal_rate', 'downgrade_impact']
            },
            EventType.CONVERSION: {
                'category': EventCategory.BUSINESS,
                'properties': ['conversion_type', 'subscription_tier', 'amount', 'funnel_stage'],
                'metrics': ['conversion_rate', 'revenue', 'funnel_performance']
            },
            EventType.CHURN: {
                'category': EventCategory.BUSINESS,
                'properties': ['churn_type', 'subscription_tier', 'lifetime_days', 'churn_reason'],
                'metrics': ['churn_rate', 'lifetime_value', 'retention_impact']
            }
        }
        
        # Performance metrics
        self.performance_metrics = {
            'events_tracked': 0,
            'events_failed': 0,
            'average_tracking_time_ms': 0.0,
            'batch_flushes': 0,
            'real_time_events': 0
        }
    
    def track_subscription_created(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track subscription creation event"""
        try:
            start_time = time.time()
            
            # Prepare event properties
            properties = {
                'subscription_id': analytics_data.get('subscription_id'),
                'subscription_tier': analytics_data.get('subscription_tier'),
                'subscription_status': analytics_data.get('subscription_status'),
                'customer_id': analytics_data.get('customer_id'),
                'user_id': analytics_data.get('user_id'),
                'timestamp': analytics_data.get('timestamp'),
                'feature_changes': analytics_data.get('feature_changes', {}),
                'source': 'webhook'
            }
            
            # Track the event
            event_result = self._track_event(
                EventType.SUBSCRIPTION_CREATED,
                analytics_data.get('user_id'),
                analytics_data.get('customer_id'),
                properties
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, event_result['success'])
            
            return {
                'success': event_result['success'],
                'event_id': event_result['event_id'],
                'event_name': 'subscription_created',
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error tracking subscription created event: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_id': None,
                'event_name': 'subscription_created'
            }
    
    def track_subscription_updated(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track subscription update event"""
        try:
            start_time = time.time()
            
            # Prepare event properties
            properties = {
                'subscription_id': analytics_data.get('subscription_id'),
                'subscription_tier': analytics_data.get('subscription_tier'),
                'subscription_status': analytics_data.get('subscription_status'),
                'customer_id': analytics_data.get('customer_id'),
                'user_id': analytics_data.get('user_id'),
                'timestamp': analytics_data.get('timestamp'),
                'feature_changes': analytics_data.get('feature_changes', {}),
                'source': 'webhook'
            }
            
            # Track the event
            event_result = self._track_event(
                EventType.SUBSCRIPTION_UPDATED,
                analytics_data.get('user_id'),
                analytics_data.get('customer_id'),
                properties
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, event_result['success'])
            
            return {
                'success': event_result['success'],
                'event_id': event_result['event_id'],
                'event_name': 'subscription_updated',
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error tracking subscription updated event: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_id': None,
                'event_name': 'subscription_updated'
            }
    
    def track_subscription_cancelled(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track subscription cancellation event"""
        try:
            start_time = time.time()
            
            # Prepare event properties
            properties = {
                'subscription_id': analytics_data.get('subscription_id'),
                'subscription_tier': analytics_data.get('subscription_tier'),
                'subscription_status': analytics_data.get('subscription_status'),
                'customer_id': analytics_data.get('customer_id'),
                'user_id': analytics_data.get('user_id'),
                'timestamp': analytics_data.get('timestamp'),
                'feature_changes': analytics_data.get('feature_changes', {}),
                'source': 'webhook'
            }
            
            # Track the event
            event_result = self._track_event(
                EventType.SUBSCRIPTION_CANCELLED,
                analytics_data.get('user_id'),
                analytics_data.get('customer_id'),
                properties
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, event_result['success'])
            
            return {
                'success': event_result['success'],
                'event_id': event_result['event_id'],
                'event_name': 'subscription_cancelled',
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error tracking subscription cancelled event: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_id': None,
                'event_name': 'subscription_cancelled'
            }
    
    def track_feature_access_granted(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track feature access granted event"""
        try:
            start_time = time.time()
            
            # Prepare event properties
            feature_changes = analytics_data.get('feature_changes', {})
            properties = {
                'subscription_id': analytics_data.get('subscription_id'),
                'subscription_tier': analytics_data.get('subscription_tier'),
                'customer_id': analytics_data.get('customer_id'),
                'user_id': analytics_data.get('user_id'),
                'timestamp': analytics_data.get('timestamp'),
                'features_granted': feature_changes.get('features_granted', []),
                'access_level': feature_changes.get('access_level'),
                'source': 'webhook'
            }
            
            # Track the event
            event_result = self._track_event(
                EventType.FEATURE_ACCESS_GRANTED,
                analytics_data.get('user_id'),
                analytics_data.get('customer_id'),
                properties
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, event_result['success'])
            
            return {
                'success': event_result['success'],
                'event_id': event_result['event_id'],
                'event_name': 'feature_access_granted',
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error tracking feature access granted event: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_id': None,
                'event_name': 'feature_access_granted'
            }
    
    def track_feature_access_changed(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track feature access changed event"""
        try:
            start_time = time.time()
            
            # Prepare event properties
            feature_changes = analytics_data.get('feature_changes', {})
            properties = {
                'subscription_id': analytics_data.get('subscription_id'),
                'subscription_tier': analytics_data.get('subscription_tier'),
                'customer_id': analytics_data.get('customer_id'),
                'user_id': analytics_data.get('user_id'),
                'timestamp': analytics_data.get('timestamp'),
                'features_granted': feature_changes.get('features_granted', []),
                'features_removed': feature_changes.get('features_removed', []),
                'access_level': feature_changes.get('access_level'),
                'source': 'webhook'
            }
            
            # Track the event
            event_result = self._track_event(
                EventType.FEATURE_ACCESS_CHANGED,
                analytics_data.get('user_id'),
                analytics_data.get('customer_id'),
                properties
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, event_result['success'])
            
            return {
                'success': event_result['success'],
                'event_id': event_result['event_id'],
                'event_name': 'feature_access_changed',
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error tracking feature access changed event: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_id': None,
                'event_name': 'feature_access_changed'
            }
    
    def track_conversion_event(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track conversion event"""
        try:
            start_time = time.time()
            
            # Prepare event properties
            properties = {
                'subscription_id': analytics_data.get('subscription_id'),
                'subscription_tier': analytics_data.get('subscription_tier'),
                'customer_id': analytics_data.get('customer_id'),
                'user_id': analytics_data.get('user_id'),
                'timestamp': analytics_data.get('timestamp'),
                'conversion_type': 'subscription_created',
                'funnel_stage': 'subscription',
                'source': 'webhook'
            }
            
            # Track the event
            event_result = self._track_event(
                EventType.CONVERSION,
                analytics_data.get('user_id'),
                analytics_data.get('customer_id'),
                properties
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, event_result['success'])
            
            return {
                'success': event_result['success'],
                'event_id': event_result['event_id'],
                'event_name': 'conversion',
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error tracking conversion event: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_id': None,
                'event_name': 'conversion'
            }
    
    def track_churn_event(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track churn event"""
        try:
            start_time = time.time()
            
            # Prepare event properties
            properties = {
                'subscription_id': analytics_data.get('subscription_id'),
                'subscription_tier': analytics_data.get('subscription_tier'),
                'customer_id': analytics_data.get('customer_id'),
                'user_id': analytics_data.get('user_id'),
                'timestamp': analytics_data.get('timestamp'),
                'churn_type': 'subscription_cancelled',
                'source': 'webhook'
            }
            
            # Track the event
            event_result = self._track_event(
                EventType.CHURN,
                analytics_data.get('user_id'),
                analytics_data.get('customer_id'),
                properties
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, event_result['success'])
            
            return {
                'success': event_result['success'],
                'event_id': event_result['event_id'],
                'event_name': 'churn',
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error tracking churn event: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_id': None,
                'event_name': 'churn'
            }
    
    def track_trial_ending(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track trial ending event"""
        try:
            start_time = time.time()
            
            # Prepare event properties
            properties = {
                'subscription_id': analytics_data.get('subscription_id'),
                'subscription_tier': analytics_data.get('subscription_tier'),
                'customer_id': analytics_data.get('customer_id'),
                'user_id': analytics_data.get('user_id'),
                'timestamp': analytics_data.get('timestamp'),
                'feature_changes': analytics_data.get('feature_changes', {}),
                'source': 'webhook'
            }
            
            # Track the event
            event_result = self._track_event(
                EventType.TRIAL_ENDING,
                analytics_data.get('user_id'),
                analytics_data.get('customer_id'),
                properties
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, event_result['success'])
            
            return {
                'success': event_result['success'],
                'event_id': event_result['event_id'],
                'event_name': 'trial_ending',
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error tracking trial ending event: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_id': None,
                'event_name': 'trial_ending'
            }
    
    def track_trial_conversion_opportunity(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track trial conversion opportunity event"""
        try:
            start_time = time.time()
            
            # Prepare event properties
            properties = {
                'subscription_id': analytics_data.get('subscription_id'),
                'subscription_tier': analytics_data.get('subscription_tier'),
                'customer_id': analytics_data.get('customer_id'),
                'user_id': analytics_data.get('user_id'),
                'timestamp': analytics_data.get('timestamp'),
                'opportunity_type': 'trial_ending',
                'conversion_potential': 'high',
                'source': 'webhook'
            }
            
            # Track the event
            event_result = self._track_event(
                EventType.TRIAL_CONVERSION_OPPORTUNITY,
                analytics_data.get('user_id'),
                analytics_data.get('customer_id'),
                properties
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, event_result['success'])
            
            return {
                'success': event_result['success'],
                'event_id': event_result['event_id'],
                'event_name': 'trial_conversion_opportunity',
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error tracking trial conversion opportunity event: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_id': None,
                'event_name': 'trial_conversion_opportunity'
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    # Private methods
    
    def _track_event(
        self,
        event_type: EventType,
        user_id: str,
        customer_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track an analytics event"""
        try:
            # Generate event ID
            event_id = str(uuid.uuid4())
            
            # Get event definition
            event_definition = self.event_definitions.get(event_type, {})
            
            # Create event data
            event_data = EventData(
                event_id=event_id,
                event_type=event_type,
                event_category=event_definition.get('category', EventCategory.BUSINESS),
                user_id=user_id,
                customer_id=customer_id,
                timestamp=datetime.now(timezone.utc),
                properties=properties
            )
            
            # Store event in database
            self._store_event(event_data)
            
            # Update real-time metrics if enabled
            if self.tracking_config['real_time_tracking']:
                self._update_real_time_metrics(event_data)
                self.performance_metrics['real_time_events'] += 1
            
            return {
                'success': True,
                'event_id': event_id
            }
            
        except Exception as e:
            logger.error(f"Error tracking event {event_type.value}: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_id': None
            }
    
    def _store_event(self, event_data: EventData):
        """Store event in database"""
        try:
            # Create analytics event record
            analytics_event = AnalyticsEvent(
                id=event_data.event_id,
                event_type=event_data.event_type.value,
                event_category=event_data.event_category.value,
                user_id=event_data.user_id,
                customer_id=event_data.customer_id,
                timestamp=event_data.timestamp,
                properties=event_data.properties,
                session_id=event_data.session_id,
                source=event_data.source,
                version=event_data.version
            )
            
            self.db.add(analytics_event)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing event: {e}")
            self.db.rollback()
            raise
    
    def _update_real_time_metrics(self, event_data: EventData):
        """Update real-time metrics"""
        try:
            # This would update real-time metrics in cache/database
            # For now, just log the event
            logger.info(f"Real-time metric update for event: {event_data.event_type.value}")
            
        except Exception as e:
            logger.error(f"Error updating real-time metrics: {e}")
    
    def _update_performance_metrics(self, processing_time: float, success: bool):
        """Update performance metrics"""
        try:
            if success:
                self.performance_metrics['events_tracked'] += 1
            else:
                self.performance_metrics['events_failed'] += 1
            
            # Update average processing time
            total_events = (
                self.performance_metrics['events_tracked'] + 
                self.performance_metrics['events_failed']
            )
            
            if total_events > 0:
                current_avg = self.performance_metrics['average_tracking_time_ms']
                new_avg = ((current_avg * (total_events - 1)) + processing_time) / total_events
                self.performance_metrics['average_tracking_time_ms'] = new_avg
            else:
                self.performance_metrics['average_tracking_time_ms'] = processing_time
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}") 