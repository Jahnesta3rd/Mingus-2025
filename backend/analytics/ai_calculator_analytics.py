"""
AI Job Impact Calculator Analytics Service
Comprehensive analytics implementation for tracking calculator performance, user behavior, and business metrics.
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
from enum import Enum

import requests
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import Session
import statsd
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Metric, Dimension, Filter, FilterExpression
)

from backend.database import get_db_session
from backend.models.user import User
from backend.models.assessment import Assessment, AssessmentStep
from backend.models.analytics import AnalyticsEvent, ConversionEvent
from backend.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize StatsD client
statsd_client = statsd.StatsClient(
    host=settings.STATSD_HOST,
    port=settings.STATSD_PORT,
    prefix='mingus.ai_calculator'
)

# Initialize Google Analytics client
ga_client = BetaAnalyticsDataClient()

class EventType(Enum):
    """Analytics event types for AI calculator"""
    CALCULATOR_OPENED = "ai_calculator_opened"
    STEP_COMPLETED = "calculator_step_completed"
    ASSESSMENT_SUBMITTED = "assessment_submitted"
    CONVERSION_OFFER_VIEWED = "conversion_offer_viewed"
    PAID_UPGRADE_CLICKED = "paid_upgrade_clicked"
    CALCULATOR_ERROR = "calculator_error"
    PERFORMANCE_METRIC = "performance_metric"

class RiskLevel(Enum):
    """AI job risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class CalculatorEvent:
    """Data structure for calculator events"""
    event_type: EventType
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    source: Optional[str] = None
    medium: Optional[str] = None
    campaign: Optional[str] = None
    step_number: Optional[int] = None
    time_on_step: Optional[float] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    assessment_completion_time: Optional[float] = None
    error_message: Optional[str] = None
    performance_metric: Optional[str] = None
    metric_value: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class AICalculatorAnalytics:
    """Main analytics service for AI Job Impact Calculator"""
    
    def __init__(self):
        self.db_session = get_db_session()
        self.session_timers = {}
        self.step_timers = {}
    
    def track_calculator_opened(self, user_id: Optional[str] = None, 
                              session_id: Optional[str] = None,
                              source: str = "direct",
                              medium: str = "none",
                              campaign: str = "none") -> None:
        """Track when calculator is opened"""
        event = CalculatorEvent(
            event_type=EventType.CALCULATOR_OPENED,
            user_id=user_id,
            session_id=session_id or str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            source=source,
            medium=medium,
            campaign=campaign
        )
        
        self._send_ga4_event(event)
        self._send_statsd_event(event)
        self._store_event(event)
        
        # Start session timer
        if session_id:
            self.session_timers[session_id] = time.time()
    
    def track_step_completed(self, session_id: str, step_number: int, 
                           time_on_step: float, user_id: Optional[str] = None) -> None:
        """Track when a calculator step is completed"""
        event = CalculatorEvent(
            event_type=EventType.STEP_COMPLETED,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            step_number=step_number,
            time_on_step=time_on_step
        )
        
        self._send_ga4_event(event)
        self._send_statsd_event(event)
        self._store_event(event)
        
        # Track funnel progression
        statsd_client.incr(f'funnel.step_{step_number}_completed')
    
    def track_assessment_submitted(self, session_id: str, job_title: str, 
                                 industry: str, risk_level: RiskLevel,
                                 assessment_completion_time: float,
                                 user_id: Optional[str] = None) -> None:
        """Track when assessment is submitted"""
        event = CalculatorEvent(
            event_type=EventType.ASSESSMENT_SUBMITTED,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            job_title=job_title,
            industry=industry,
            risk_level=risk_level,
            assessment_completion_time=assessment_completion_time
        )
        
        self._send_ga4_event(event)
        self._send_statsd_event(event)
        self._store_event(event)
        
        # Track conversion
        statsd_client.incr('conversion.assessment_submitted')
        statsd_client.gauge(f'risk_level.{risk_level.value}', 1)
        
        # Store assessment data for BI
        self._store_assessment_data(event)
    
    def track_conversion_offer_viewed(self, session_id: str, risk_level: RiskLevel,
                                    time_to_view: float, user_id: Optional[str] = None) -> None:
        """Track when conversion offer is viewed"""
        event = CalculatorEvent(
            event_type=EventType.CONVERSION_OFFER_VIEWED,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            risk_level=risk_level,
            time_to_view=time_to_view
        )
        
        self._send_ga4_event(event)
        self._send_statsd_event(event)
        self._store_event(event)
    
    def track_paid_upgrade_clicked(self, session_id: str, risk_level: RiskLevel,
                                 assessment_completion_time: float,
                                 user_id: Optional[str] = None) -> None:
        """Track when paid upgrade is clicked"""
        event = CalculatorEvent(
            event_type=EventType.PAID_UPGRADE_CLICKED,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            risk_level=risk_level,
            assessment_completion_time=assessment_completion_time
        )
        
        self._send_ga4_event(event)
        self._send_statsd_event(event)
        self._store_event(event)
        
        # Track revenue event
        statsd_client.incr('revenue.upgrade_clicked')
    
    def track_performance_metric(self, metric_name: str, metric_value: float,
                               session_id: Optional[str] = None) -> None:
        """Track performance metrics"""
        event = CalculatorEvent(
            event_type=EventType.PERFORMANCE_METRIC,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            performance_metric=metric_name,
            metric_value=metric_value
        )
        
        self._send_statsd_event(event)
        self._store_event(event)
    
    def track_error(self, error_message: str, session_id: Optional[str] = None,
                   user_id: Optional[str] = None) -> None:
        """Track calculator errors"""
        event = CalculatorEvent(
            event_type=EventType.CALCULATOR_ERROR,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            error_message=error_message
        )
        
        self._send_statsd_event(event)
        self._store_event(event)
        
        # Track error rate
        statsd_client.incr('errors.calculator')
    
    def _send_ga4_event(self, event: CalculatorEvent) -> None:
        """Send event to Google Analytics 4"""
        try:
            # Prepare GA4 event data
            event_data = {
                'event_name': event.event_type.value,
                'timestamp_micros': int(event.timestamp.timestamp() * 1000000),
                'user_pseudo_id': event.session_id,
                'user_id': event.user_id,
                'event_parameters': []
            }
            
            # Add event-specific parameters
            if event.source:
                event_data['event_parameters'].append({
                    'key': 'source',
                    'value': {'string_value': event.source}
                })
            
            if event.medium:
                event_data['event_parameters'].append({
                    'key': 'medium',
                    'value': {'string_value': event.medium}
                })
            
            if event.campaign:
                event_data['event_parameters'].append({
                    'key': 'campaign',
                    'value': {'string_value': event.campaign}
                })
            
            if event.step_number:
                event_data['event_parameters'].append({
                    'key': 'step_number',
                    'value': {'int_value': event.step_number}
                })
            
            if event.time_on_step:
                event_data['event_parameters'].append({
                    'key': 'time_on_step',
                    'value': {'double_value': event.time_on_step}
                })
            
            if event.job_title:
                event_data['event_parameters'].append({
                    'key': 'job_title',
                    'value': {'string_value': event.job_title}
                })
            
            if event.industry:
                event_data['event_parameters'].append({
                    'key': 'industry',
                    'value': {'string_value': event.industry}
                })
            
            if event.risk_level:
                event_data['event_parameters'].append({
                    'key': 'risk_level',
                    'value': {'string_value': event.risk_level.value}
                })
            
            if event.assessment_completion_time:
                event_data['event_parameters'].append({
                    'key': 'assessment_completion_time',
                    'value': {'double_value': event.assessment_completion_time}
                })
            
            # Send to GA4 (implementation depends on GA4 API setup)
            logger.info(f"GA4 Event: {event_data}")
            
        except Exception as e:
            logger.error(f"Failed to send GA4 event: {e}")
    
    def _send_statsd_event(self, event: CalculatorEvent) -> None:
        """Send event to StatsD"""
        try:
            # Increment event counter
            statsd_client.incr(f'events.{event.event_type.value}')
            
            # Track timing for relevant events
            if event.time_on_step:
                statsd_client.timing(f'timing.step_{event.step_number}', event.time_on_step * 1000)
            
            if event.assessment_completion_time:
                statsd_client.timing('timing.assessment_completion', event.assessment_completion_time * 1000)
            
            # Track performance metrics
            if event.performance_metric and event.metric_value:
                statsd_client.gauge(f'performance.{event.performance_metric}', event.metric_value)
                
        except Exception as e:
            logger.error(f"Failed to send StatsD event: {e}")
    
    def _store_event(self, event: CalculatorEvent) -> None:
        """Store event in database"""
        try:
            analytics_event = AnalyticsEvent(
                event_type=event.event_type.value,
                user_id=event.user_id,
                session_id=event.session_id,
                timestamp=event.timestamp,
                event_data=asdict(event)
            )
            
            self.db_session.add(analytics_event)
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Failed to store analytics event: {e}")
            self.db_session.rollback()
    
    def _store_assessment_data(self, event: CalculatorEvent) -> None:
        """Store assessment data for business intelligence"""
        try:
            # Store in assessment table
            assessment = Assessment(
                user_id=event.user_id,
                session_id=event.session_id,
                job_title=event.job_title,
                industry=event.industry,
                risk_level=event.risk_level.value,
                completion_time=event.assessment_completion_time,
                created_at=event.timestamp
            )
            
            self.db_session.add(assessment)
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Failed to store assessment data: {e}")
            self.db_session.rollback()

# Global analytics instance
ai_calculator_analytics = AICalculatorAnalytics()
