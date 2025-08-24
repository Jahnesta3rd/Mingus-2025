"""
Analytics Service for Job Recommendation Engine
Tracks user behavior, recommendation effectiveness, and system performance
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, Counter

from backend.models.base import Base
from backend.services.cache_service import CacheService
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Analytics event types"""
    RESUME_UPLOAD = "resume_upload"
    RECOMMENDATION_VIEW = "recommendation_view"
    RECOMMENDATION_CLICK = "recommendation_click"
    JOB_APPLY = "job_apply"
    RECOMMENDATION_SAVE = "recommendation_save"
    PROGRESS_UPDATE = "progress_update"
    FEEDBACK_SUBMIT = "feedback_submit"
    ERROR_OCCURRED = "error_occurred"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    FEATURE_USAGE = "feature_usage"
    CONVERSION_EVENT = "conversion_event"

class UserJourneyStage(Enum):
    """User journey stages for funnel analysis"""
    RESUME_UPLOAD = "resume_upload"
    PROCESSING = "processing"
    RECOMMENDATION_VIEW = "recommendation_view"
    RECOMMENDATION_INTERACTION = "recommendation_interaction"
    APPLICATION_ACTION = "application_action"
    FEEDBACK = "feedback"
    COMPLETION = "completion"

@dataclass
class AnalyticsEvent:
    """Analytics event data structure"""
    event_id: str
    user_id: Optional[str]
    session_id: str
    event_type: EventType
    timestamp: datetime
    page_url: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class UserBehaviorMetrics:
    """User behavior metrics for analysis"""
    user_id: str
    session_count: int
    total_time_spent: float
    recommendation_views: int
    recommendation_clicks: int
    applications_submitted: int
    recommendations_saved: int
    feedback_submitted: int
    last_activity: datetime
    conversion_rate: float
    engagement_score: float

@dataclass
class RecommendationMetrics:
    """Recommendation effectiveness metrics"""
    recommendation_id: str
    user_id: str
    job_title: str
    company: str
    location: str
    salary_range: Dict[str, int]
    tier_type: str  # conservative, optimal, stretch
    skills_match_percentage: float
    success_probability: float
    click_count: int
    application_count: int
    save_count: int
    feedback_rating: Optional[float] = None
    actual_salary_increase: Optional[float] = None
    application_success: Optional[bool] = None

@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    timestamp: datetime
    response_time: float
    memory_usage: float
    cpu_usage: float
    database_query_time: float
    cache_hit_rate: float
    error_rate: float
    concurrent_users: int
    api_calls_per_minute: int

class AnalyticsService:
    """Comprehensive analytics service for job recommendation engine"""
    
    def __init__(self, cache_service: CacheService):
        """Initialize analytics service"""
        self.cache_service = cache_service
        self.event_buffer = []
        self.buffer_size = 100
        self.flush_interval = 300  # 5 minutes
        
    def track_event(self, 
                   user_id: Optional[str],
                   session_id: str,
                   event_type: EventType,
                   metadata: Optional[Dict[str, Any]] = None,
                   request_info: Optional[Dict[str, Any]] = None) -> str:
        """Track an analytics event"""
        event_id = str(uuid.uuid4())
        
        event = AnalyticsEvent(
            event_id=event_id,
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            timestamp=datetime.now(),
            page_url=request_info.get('page_url') if request_info else None,
            user_agent=request_info.get('user_agent') if request_info else None,
            ip_address=request_info.get('ip_address') if request_info else None,
            metadata=metadata or {}
        )
        
        # Add to buffer for batch processing
        self.event_buffer.append(event)
        
        # Flush buffer if it's full
        if len(self.event_buffer) >= self.buffer_size:
            self.flush_events()
        
        return event_id
    
    def track_user_journey(self, 
                          user_id: str,
                          session_id: str,
                          stage: UserJourneyStage,
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """Track user journey progression"""
        journey_data = {
            'stage': stage.value,
            'journey_timestamp': datetime.now().isoformat(),
            'stage_metadata': metadata or {}
        }
        
        # Store journey data in cache for real-time analysis
        cache_key = f"user_journey:{session_id}"
        journey_cache = self.cache_service.get(cache_key) or {}
        journey_cache[stage.value] = journey_data
        self.cache_service.set(cache_key, journey_cache, ttl=3600)
        
        # Track as analytics event
        self.track_event(
            user_id=user_id,
            session_id=session_id,
            event_type=EventType.FEATURE_USAGE,
            metadata=journey_data
        )
    
    def track_recommendation_interaction(self,
                                       user_id: str,
                                       session_id: str,
                                       recommendation_id: str,
                                       interaction_type: str,
                                       recommendation_data: Dict[str, Any]) -> None:
        """Track recommendation interactions"""
        metadata = {
            'recommendation_id': recommendation_id,
            'interaction_type': interaction_type,
            'job_title': recommendation_data.get('job_title'),
            'company': recommendation_data.get('company'),
            'location': recommendation_data.get('location'),
            'tier_type': recommendation_data.get('tier_type'),
            'skills_match': recommendation_data.get('skills_match_percentage'),
            'success_probability': recommendation_data.get('success_probability')
        }
        
        event_type = EventType.RECOMMENDATION_CLICK if interaction_type == 'click' else EventType.FEATURE_USAGE
        
        self.track_event(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            metadata=metadata
        )
        
        # Update recommendation metrics
        self.update_recommendation_metrics(recommendation_id, interaction_type)
    
    def track_application_action(self,
                               user_id: str,
                               session_id: str,
                               recommendation_id: str,
                               action_type: str,
                               application_data: Dict[str, Any]) -> None:
        """Track job application actions"""
        metadata = {
            'recommendation_id': recommendation_id,
            'action_type': action_type,
            'job_title': application_data.get('job_title'),
            'company': application_data.get('company'),
            'salary_range': application_data.get('salary_range'),
            'application_method': application_data.get('application_method')
        }
        
        self.track_event(
            user_id=user_id,
            session_id=session_id,
            event_type=EventType.JOB_APPLY,
            metadata=metadata
        )
        
        # Update recommendation metrics
        self.update_recommendation_metrics(recommendation_id, 'application')
    
    def track_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Track system performance metrics"""
        # Store in cache for real-time monitoring
        cache_key = f"performance_metrics:{datetime.now().strftime('%Y%m%d_%H')}"
        performance_cache = self.cache_service.get(cache_key) or []
        performance_cache.append(asdict(metrics))
        
        # Keep only last 60 minutes of data
        if len(performance_cache) > 60:
            performance_cache = performance_cache[-60:]
        
        self.cache_service.set(cache_key, performance_cache, ttl=7200)
        
        # Check for performance alerts
        self.check_performance_alerts(metrics)
    
    def track_recommendation_quality(self,
                                   recommendation_id: str,
                                   user_id: str,
                                   quality_metrics: Dict[str, Any]) -> None:
        """Track recommendation quality metrics"""
        cache_key = f"recommendation_quality:{recommendation_id}"
        
        quality_data = {
            'recommendation_id': recommendation_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'skills_match_percentage': quality_metrics.get('skills_match_percentage'),
            'salary_increase_percentage': quality_metrics.get('salary_increase_percentage'),
            'success_probability': quality_metrics.get('success_probability'),
            'geographic_relevance': quality_metrics.get('geographic_relevance'),
            'industry_alignment': quality_metrics.get('industry_alignment')
        }
        
        self.cache_service.set(cache_key, quality_data, ttl=86400)  # 24 hours
        
        # Track as analytics event
        self.track_event(
            user_id=user_id,
            session_id=quality_metrics.get('session_id', ''),
            event_type=EventType.FEATURE_USAGE,
            metadata={'quality_metrics': quality_data}
        )
    
    def get_user_behavior_metrics(self, user_id: str, days: int = 30) -> UserBehaviorMetrics:
        """Get user behavior metrics for analysis"""
        # Get user events from cache/database
        user_events = self.get_user_events(user_id, days)
        
        # Calculate metrics
        session_count = len(set(event.get('session_id') for event in user_events))
        recommendation_views = sum(1 for event in user_events if event.get('event_type') == EventType.RECOMMENDATION_VIEW.value)
        recommendation_clicks = sum(1 for event in user_events if event.get('event_type') == EventType.RECOMMENDATION_CLICK.value)
        applications_submitted = sum(1 for event in user_events if event.get('event_type') == EventType.JOB_APPLY.value)
        recommendations_saved = sum(1 for event in user_events if event.get('event_type') == EventType.RECOMMENDATION_SAVE.value)
        feedback_submitted = sum(1 for event in user_events if event.get('event_type') == EventType.FEEDBACK_SUBMIT.value)
        
        # Calculate engagement score
        total_actions = recommendation_views + recommendation_clicks + applications_submitted + recommendations_saved
        engagement_score = min(total_actions / max(session_count, 1), 10.0)  # Scale to 0-10
        
        # Calculate conversion rate
        conversion_rate = applications_submitted / max(recommendation_views, 1)
        
        return UserBehaviorMetrics(
            user_id=user_id,
            session_count=session_count,
            total_time_spent=0.0,  # Would need session duration tracking
            recommendation_views=recommendation_views,
            recommendation_clicks=recommendation_clicks,
            applications_submitted=applications_submitted,
            recommendations_saved=recommendations_saved,
            feedback_submitted=feedback_submitted,
            last_activity=datetime.now(),  # Would get from actual data
            conversion_rate=conversion_rate,
            engagement_score=engagement_score
        )
    
    def get_recommendation_effectiveness(self, days: int = 30) -> List[RecommendationMetrics]:
        """Get recommendation effectiveness metrics"""
        # Get recommendation events from cache/database
        recommendation_events = self.get_recommendation_events(days)
        
        # Group by recommendation ID
        recommendation_stats = defaultdict(lambda: {
            'click_count': 0,
            'application_count': 0,
            'save_count': 0,
            'feedback_ratings': []
        })
        
        for event in recommendation_events:
            rec_id = event.get('metadata', {}).get('recommendation_id')
            if rec_id:
                if event.get('event_type') == EventType.RECOMMENDATION_CLICK.value:
                    recommendation_stats[rec_id]['click_count'] += 1
                elif event.get('event_type') == EventType.JOB_APPLY.value:
                    recommendation_stats[rec_id]['application_count'] += 1
                elif event.get('event_type') == EventType.RECOMMENDATION_SAVE.value:
                    recommendation_stats[rec_id]['save_count'] += 1
                elif event.get('event_type') == EventType.FEEDBACK_SUBMIT.value:
                    rating = event.get('metadata', {}).get('rating')
                    if rating:
                        recommendation_stats[rec_id]['feedback_ratings'].append(rating)
        
        # Convert to RecommendationMetrics objects
        metrics = []
        for rec_id, stats in recommendation_stats.items():
            # Get recommendation details from cache/database
            rec_details = self.get_recommendation_details(rec_id)
            
            metrics.append(RecommendationMetrics(
                recommendation_id=rec_id,
                user_id=rec_details.get('user_id', ''),
                job_title=rec_details.get('job_title', ''),
                company=rec_details.get('company', ''),
                location=rec_details.get('location', ''),
                salary_range=rec_details.get('salary_range', {}),
                tier_type=rec_details.get('tier_type', ''),
                skills_match_percentage=rec_details.get('skills_match_percentage', 0.0),
                success_probability=rec_details.get('success_probability', 0.0),
                click_count=stats['click_count'],
                application_count=stats['application_count'],
                save_count=stats['save_count'],
                feedback_rating=sum(stats['feedback_ratings']) / len(stats['feedback_ratings']) if stats['feedback_ratings'] else None
            ))
        
        return metrics
    
    def get_performance_metrics(self, hours: int = 24) -> List[PerformanceMetrics]:
        """Get system performance metrics"""
        performance_data = []
        
        # Get performance data from cache
        for hour in range(hours):
            cache_key = f"performance_metrics:{datetime.now().strftime('%Y%m%d_%H')}"
            hour_data = self.cache_service.get(cache_key) or []
            performance_data.extend(hour_data)
        
        # Convert to PerformanceMetrics objects
        metrics = []
        for data in performance_data:
            metrics.append(PerformanceMetrics(
                timestamp=datetime.fromisoformat(data['timestamp']),
                response_time=data['response_time'],
                memory_usage=data['memory_usage'],
                cpu_usage=data['cpu_usage'],
                database_query_time=data['database_query_time'],
                cache_hit_rate=data['cache_hit_rate'],
                error_rate=data['error_rate'],
                concurrent_users=data['concurrent_users'],
                api_calls_per_minute=data['api_calls_per_minute']
            ))
        
        return metrics
    
    def get_funnel_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get user funnel analysis"""
        # Get user journey data from cache/database
        journey_data = self.get_user_journey_data(days)
        
        # Calculate funnel stages
        funnel_stages = {
            UserJourneyStage.RESUME_UPLOAD.value: 0,
            UserJourneyStage.PROCESSING.value: 0,
            UserJourneyStage.RECOMMENDATION_VIEW.value: 0,
            UserJourneyStage.RECOMMENDATION_INTERACTION.value: 0,
            UserJourneyStage.APPLICATION_ACTION.value: 0,
            UserJourneyStage.FEEDBACK.value: 0,
            UserJourneyStage.COMPLETION.value: 0
        }
        
        for journey in journey_data:
            for stage in journey.get('stages', []):
                stage_name = stage.get('stage')
                if stage_name in funnel_stages:
                    funnel_stages[stage_name] += 1
        
        # Calculate conversion rates
        total_users = funnel_stages[UserJourneyStage.RESUME_UPLOAD.value]
        conversion_rates = {}
        
        for stage, count in funnel_stages.items():
            if total_users > 0:
                conversion_rates[stage] = (count / total_users) * 100
            else:
                conversion_rates[stage] = 0
        
        return {
            'funnel_stages': funnel_stages,
            'conversion_rates': conversion_rates,
            'total_users': total_users,
            'period_days': days
        }
    
    def get_demographic_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get demographic correlation analysis"""
        # Get user events with demographic data
        user_events = self.get_user_events_with_demographics(days)
        
        # Group by demographic factors
        demographic_stats = defaultdict(lambda: {
            'total_users': 0,
            'recommendation_views': 0,
            'applications_submitted': 0,
            'conversion_rate': 0.0,
            'avg_salary_increase': 0.0
        })
        
        for event in user_events:
            demographics = event.get('demographics', {})
            age_range = demographics.get('age_range', 'unknown')
            education = demographics.get('education_level', 'unknown')
            industry = demographics.get('industry', 'unknown')
            
            # Update stats for each demographic factor
            for factor, value in [('age', age_range), ('education', education), ('industry', industry)]:
                if event.get('event_type') == EventType.RECOMMENDATION_VIEW.value:
                    demographic_stats[f"{factor}_{value}"]['recommendation_views'] += 1
                elif event.get('event_type') == EventType.JOB_APPLY.value:
                    demographic_stats[f"{factor}_{value}"]['applications_submitted'] += 1
                
                demographic_stats[f"{factor}_{value}"]['total_users'] += 1
        
        # Calculate conversion rates and averages
        for factor, stats in demographic_stats.items():
            if stats['recommendation_views'] > 0:
                stats['conversion_rate'] = (stats['applications_submitted'] / stats['recommendation_views']) * 100
        
        return {
            'demographic_stats': dict(demographic_stats),
            'period_days': days
        }
    
    def update_recommendation_metrics(self, recommendation_id: str, interaction_type: str) -> None:
        """Update recommendation metrics in cache"""
        cache_key = f"recommendation_metrics:{recommendation_id}"
        metrics = self.cache_service.get(cache_key) or {
            'click_count': 0,
            'application_count': 0,
            'save_count': 0,
            'view_count': 0
        }
        
        if interaction_type == 'click':
            metrics['click_count'] += 1
        elif interaction_type == 'application':
            metrics['application_count'] += 1
        elif interaction_type == 'save':
            metrics['save_count'] += 1
        elif interaction_type == 'view':
            metrics['view_count'] += 1
        
        self.cache_service.set(cache_key, metrics, ttl=86400)  # 24 hours
    
    def check_performance_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for performance alerts and trigger notifications"""
        alerts = []
        
        # Response time alert
        if metrics.response_time > 8.0:  # 8 seconds threshold
            alerts.append({
                'type': 'high_response_time',
                'severity': 'warning',
                'message': f'Response time exceeded threshold: {metrics.response_time:.2f}s',
                'timestamp': datetime.now().isoformat()
            })
        
        # Error rate alert
        if metrics.error_rate > 0.05:  # 5% error rate threshold
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'critical',
                'message': f'Error rate exceeded threshold: {metrics.error_rate:.2%}',
                'timestamp': datetime.now().isoformat()
            })
        
        # Memory usage alert
        if metrics.memory_usage > 1000:  # 1GB memory threshold
            alerts.append({
                'type': 'high_memory_usage',
                'severity': 'warning',
                'message': f'Memory usage exceeded threshold: {metrics.memory_usage:.2f}MB',
                'timestamp': datetime.now().isoformat()
            })
        
        # Store alerts in cache for monitoring dashboard
        if alerts:
            alert_cache = self.cache_service.get('performance_alerts') or []
            alert_cache.extend(alerts)
            
            # Keep only last 100 alerts
            if len(alert_cache) > 100:
                alert_cache = alert_cache[-100:]
            
            self.cache_service.set('performance_alerts', alert_cache, ttl=86400)
    
    def flush_events(self) -> None:
        """Flush buffered events to storage"""
        if not self.event_buffer:
            return
        
        # Store events in cache for batch processing
        batch_id = str(uuid.uuid4())
        batch_key = f"analytics_batch:{batch_id}"
        
        events_data = [event.to_dict() for event in self.event_buffer]
        self.cache_service.set(batch_key, events_data, ttl=3600)  # 1 hour TTL
        
        # Clear buffer
        self.event_buffer.clear()
        
        logger.info(f"Flushed {len(events_data)} analytics events to batch {batch_id}")
    
    def get_user_events(self, user_id: str, days: int) -> List[Dict[str, Any]]:
        """Get user events from cache/database (placeholder implementation)"""
        # This would typically query a database or cache
        # For now, return empty list
        return []
    
    def get_recommendation_events(self, days: int) -> List[Dict[str, Any]]:
        """Get recommendation events from cache/database (placeholder implementation)"""
        # This would typically query a database or cache
        # For now, return empty list
        return []
    
    def get_recommendation_details(self, recommendation_id: str) -> Dict[str, Any]:
        """Get recommendation details from cache/database (placeholder implementation)"""
        # This would typically query a database or cache
        # For now, return empty dict
        return {}
    
    def get_user_journey_data(self, days: int) -> List[Dict[str, Any]]:
        """Get user journey data from cache/database (placeholder implementation)"""
        # This would typically query a database or cache
        # For now, return empty list
        return []
    
    def get_user_events_with_demographics(self, days: int) -> List[Dict[str, Any]]:
        """Get user events with demographic data (placeholder implementation)"""
        # This would typically query a database or cache
        # For now, return empty list
        return [] 