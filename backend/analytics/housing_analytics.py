#!/usr/bin/env python3
"""
MINGUS Optimal Living Location - Analytics Integration

Analytics tracking and monitoring for the housing location feature including:
- Feature usage tracking
- Performance monitoring
- Error tracking
- User engagement metrics
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
from sqlalchemy import func, and_, desc
from backend.models.database import db
from backend.models.housing_models import HousingSearch, HousingScenario
from backend.models.user_models import User

# Configure logging
logger = logging.getLogger(__name__)

class AnalyticsEventType(Enum):
    """Types of analytics events for housing feature"""
    HOUSING_SEARCH = "housing_search"
    SCENARIO_CREATED = "scenario_created"
    SCENARIO_VIEWED = "scenario_viewed"
    SCENARIO_DELETED = "scenario_deleted"
    PREFERENCES_UPDATED = "preferences_updated"
    COMMUTE_CALCULATED = "commute_calculated"
    API_ERROR = "api_error"
    FEATURE_ACCESS_DENIED = "feature_access_denied"

@dataclass
class HousingAnalyticsEvent:
    """Housing analytics event data structure"""
    event_type: AnalyticsEventType
    user_id: int
    timestamp: datetime
    data: Dict[str, Any]
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class HousingAnalyticsTracker:
    """Analytics tracker for housing location feature"""
    
    def __init__(self):
        self.events_buffer = []
        self.buffer_size = 100
        self.flush_interval = 300  # 5 minutes
    
    def track_event(self, event: HousingAnalyticsEvent):
        """Track a housing analytics event"""
        try:
            self.events_buffer.append(event)
            
            # Flush buffer if it's full
            if len(self.events_buffer) >= self.buffer_size:
                self._flush_events()
            
            logger.debug(f"Tracked housing event: {event.event_type.value}")
            
        except Exception as e:
            logger.error(f"Error tracking housing event: {e}")
    
    def track_housing_search(self, user_id: int, search_criteria: Dict[str, Any], 
                           results_count: int, response_time_ms: int, 
                           session_id: str = None, ip_address: str = None):
        """Track housing search event"""
        event = HousingAnalyticsEvent(
            event_type=AnalyticsEventType.HOUSING_SEARCH,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            data={
                'search_criteria': search_criteria,
                'results_count': results_count,
                'response_time_ms': response_time_ms,
                'msa_area': search_criteria.get('zip_code', '')[:5]
            },
            session_id=session_id,
            ip_address=ip_address
        )
        self.track_event(event)
    
    def track_scenario_created(self, user_id: int, scenario_id: int, 
                             scenario_name: str, include_career_analysis: bool,
                             session_id: str = None):
        """Track scenario creation event"""
        event = HousingAnalyticsEvent(
            event_type=AnalyticsEventType.SCENARIO_CREATED,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            data={
                'scenario_id': scenario_id,
                'scenario_name': scenario_name,
                'include_career_analysis': include_career_analysis
            },
            session_id=session_id
        )
        self.track_event(event)
    
    def track_api_error(self, user_id: int, api_name: str, error_message: str,
                       endpoint: str, status_code: int, session_id: str = None):
        """Track API error event"""
        event = HousingAnalyticsEvent(
            event_type=AnalyticsEventType.API_ERROR,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            data={
                'api_name': api_name,
                'error_message': error_message,
                'endpoint': endpoint,
                'status_code': status_code
            },
            session_id=session_id
        )
        self.track_event(event)
    
    def track_feature_access_denied(self, user_id: int, feature_name: str, 
                                  required_tier: str, current_tier: str,
                                  session_id: str = None):
        """Track feature access denied event"""
        event = HousingAnalyticsEvent(
            event_type=AnalyticsEventType.FEATURE_ACCESS_DENIED,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            data={
                'feature_name': feature_name,
                'required_tier': required_tier,
                'current_tier': current_tier
            },
            session_id=session_id
        )
        self.track_event(event)
    
    def _flush_events(self):
        """Flush events buffer to database"""
        if not self.events_buffer:
            return
        
        try:
            # Store events in database (simplified - in production use proper analytics DB)
            for event in self.events_buffer:
                self._store_event_in_db(event)
            
            self.events_buffer.clear()
            logger.info(f"Flushed {len(self.events_buffer)} housing analytics events")
            
        except Exception as e:
            logger.error(f"Error flushing housing analytics events: {e}")
    
    def _store_event_in_db(self, event: HousingAnalyticsEvent):
        """Store event in database"""
        # In production, this would store in a dedicated analytics table
        # For now, we'll log the event
        logger.info(f"Housing Analytics Event: {event.event_type.value} - User {event.user_id}")

class HousingPerformanceMonitor:
    """Performance monitoring for housing feature"""
    
    def __init__(self):
        self.metrics = {}
        self.alert_thresholds = {
            'search_response_time_ms': 5000,  # 5 seconds
            'api_error_rate': 0.05,  # 5%
            'database_query_time_ms': 1000,  # 1 second
            'cache_hit_rate': 0.8  # 80%
        }
    
    def record_search_performance(self, response_time_ms: int, api_calls: int, 
                                cache_hits: int, results_count: int):
        """Record search performance metrics"""
        self.metrics['search_response_time_ms'] = response_time_ms
        self.metrics['api_calls_per_search'] = api_calls
        self.metrics['cache_hits_per_search'] = cache_hits
        self.metrics['results_per_search'] = results_count
        
        # Check for performance alerts
        if response_time_ms > self.alert_thresholds['search_response_time_ms']:
            self._trigger_performance_alert('search_response_time', response_time_ms)
    
    def record_api_performance(self, api_name: str, response_time_ms: int, 
                             status_code: int, success: bool):
        """Record API performance metrics"""
        key = f"{api_name}_response_time_ms"
        self.metrics[key] = response_time_ms
        
        if not success:
            self._record_api_error(api_name, status_code)
    
    def record_database_performance(self, query_name: str, execution_time_ms: int):
        """Record database performance metrics"""
        key = f"db_{query_name}_time_ms"
        self.metrics[key] = execution_time_ms
        
        if execution_time_ms > self.alert_thresholds['database_query_time_ms']:
            self._trigger_performance_alert('database_query_time', execution_time_ms)
    
    def _record_api_error(self, api_name: str, status_code: int):
        """Record API error"""
        error_key = f"{api_name}_errors"
        if error_key not in self.metrics:
            self.metrics[error_key] = 0
        self.metrics[error_key] += 1
        
        # Calculate error rate
        total_key = f"{api_name}_total_requests"
        if total_key in self.metrics:
            error_rate = self.metrics[error_key] / self.metrics[total_key]
            if error_rate > self.alert_thresholds['api_error_rate']:
                self._trigger_performance_alert('api_error_rate', error_rate)
    
    def _trigger_performance_alert(self, metric_name: str, value: float):
        """Trigger performance alert"""
        logger.warning(f"Performance alert: {metric_name} = {value}")
        # In production, this would send alerts to monitoring system
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        return {
            'metrics': self.metrics,
            'alert_thresholds': self.alert_thresholds,
            'timestamp': datetime.utcnow().isoformat()
        }

class HousingEngagementAnalyzer:
    """Analyze user engagement with housing feature"""
    
    def get_user_engagement_metrics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get user engagement metrics for housing feature"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get search count
            search_count = HousingSearch.query.filter(
                and_(
                    HousingSearch.user_id == user_id,
                    HousingSearch.created_at >= start_date
                )
            ).count()
            
            # Get scenario count
            scenario_count = HousingScenario.query.filter(
                and_(
                    HousingScenario.user_id == user_id,
                    HousingScenario.created_at >= start_date
                )
            ).count()
            
            # Get favorite scenarios count
            favorite_count = HousingScenario.query.filter(
                and_(
                    HousingScenario.user_id == user_id,
                    HousingScenario.is_favorite == True,
                    HousingScenario.created_at >= start_date
                )
            ).count()
            
            # Calculate engagement score
            engagement_score = self._calculate_engagement_score(
                search_count, scenario_count, favorite_count, days
            )
            
            return {
                'user_id': user_id,
                'period_days': days,
                'search_count': search_count,
                'scenario_count': scenario_count,
                'favorite_count': favorite_count,
                'engagement_score': engagement_score,
                'engagement_level': self._get_engagement_level(engagement_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {e}")
            return {}
    
    def get_feature_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get overall feature usage statistics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total searches
            total_searches = HousingSearch.query.filter(
                HousingSearch.created_at >= start_date
            ).count()
            
            # Total scenarios
            total_scenarios = HousingScenario.query.filter(
                HousingScenario.created_at >= start_date
            ).count()
            
            # Unique users
            unique_users = db.session.query(HousingSearch.user_id).filter(
                HousingSearch.created_at >= start_date
            ).distinct().count()
            
            # Average searches per user
            avg_searches_per_user = total_searches / unique_users if unique_users > 0 else 0
            
            # Average scenarios per user
            avg_scenarios_per_user = total_scenarios / unique_users if unique_users > 0 else 0
            
            return {
                'period_days': days,
                'total_searches': total_searches,
                'total_scenarios': total_scenarios,
                'unique_users': unique_users,
                'avg_searches_per_user': round(avg_searches_per_user, 2),
                'avg_scenarios_per_user': round(avg_scenarios_per_user, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating feature usage stats: {e}")
            return {}
    
    def _calculate_engagement_score(self, search_count: int, scenario_count: int, 
                                  favorite_count: int, days: int) -> float:
        """Calculate user engagement score"""
        # Weighted scoring system
        search_weight = 0.4
        scenario_weight = 0.4
        favorite_weight = 0.2
        
        # Normalize by time period
        search_score = min(search_count / (days * 0.1), 1.0)  # Max 1 search per 10 days
        scenario_score = min(scenario_count / (days * 0.05), 1.0)  # Max 1 scenario per 20 days
        favorite_score = min(favorite_count / (days * 0.02), 1.0)  # Max 1 favorite per 50 days
        
        return (search_score * search_weight + 
                scenario_score * scenario_weight + 
                favorite_score * favorite_weight) * 100
    
    def _get_engagement_level(self, score: float) -> str:
        """Get engagement level based on score"""
        if score >= 80:
            return 'high'
        elif score >= 50:
            return 'medium'
        elif score >= 20:
            return 'low'
        else:
            return 'minimal'

class HousingErrorMonitor:
    """Monitor errors in housing feature"""
    
    def __init__(self):
        self.error_counts = {}
        self.error_thresholds = {
            'api_errors_per_hour': 10,
            'database_errors_per_hour': 5,
            'validation_errors_per_hour': 20
        }
    
    def record_error(self, error_type: str, error_message: str, 
                    user_id: int = None, context: Dict[str, Any] = None):
        """Record an error"""
        timestamp = datetime.utcnow()
        
        if error_type not in self.error_counts:
            self.error_counts[error_type] = []
        
        self.error_counts[error_type].append({
            'timestamp': timestamp,
            'error_message': error_message,
            'user_id': user_id,
            'context': context or {}
        })
        
        # Check error thresholds
        self._check_error_thresholds(error_type)
        
        logger.error(f"Housing error recorded: {error_type} - {error_message}")
    
    def _check_error_thresholds(self, error_type: str):
        """Check if error thresholds are exceeded"""
        if error_type not in self.error_counts:
            return
        
        # Count errors in last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_errors = [
            error for error in self.error_counts[error_type]
            if error['timestamp'] > one_hour_ago
        ]
        
        error_count = len(recent_errors)
        threshold_key = f"{error_type}_per_hour"
        
        if threshold_key in self.error_thresholds:
            threshold = self.error_thresholds[threshold_key]
            if error_count >= threshold:
                self._trigger_error_alert(error_type, error_count, threshold)
    
    def _trigger_error_alert(self, error_type: str, count: int, threshold: int):
        """Trigger error alert"""
        logger.critical(f"Error threshold exceeded: {error_type} = {count} (threshold: {threshold})")
        # In production, this would send alerts to monitoring system
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        summary = {}
        for error_type, errors in self.error_counts.items():
            recent_errors = [e for e in errors if e['timestamp'] > cutoff_time]
            summary[error_type] = {
                'count': len(recent_errors),
                'unique_users': len(set(e['user_id'] for e in recent_errors if e['user_id']))
            }
        
        return summary

# Global instances
housing_analytics_tracker = HousingAnalyticsTracker()
housing_performance_monitor = HousingPerformanceMonitor()
housing_engagement_analyzer = HousingEngagementAnalyzer()
housing_error_monitor = HousingErrorMonitor()

# Export analytics components
__all__ = [
    'housing_analytics_tracker',
    'housing_performance_monitor', 
    'housing_engagement_analyzer',
    'housing_error_monitor',
    'AnalyticsEventType',
    'HousingAnalyticsEvent'
]
