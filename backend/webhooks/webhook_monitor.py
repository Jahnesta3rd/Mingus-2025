"""
Webhook Monitoring and Analytics System for MINGUS
Tracks webhook performance, success rates, and provides insights
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
import json

from ..models.subscription import AuditLog, AuditEventType, AuditSeverity
from ..config.base import Config

logger = logging.getLogger(__name__)

@dataclass
class WebhookMetrics:
    """Webhook performance metrics"""
    total_events: int
    successful_events: int
    failed_events: int
    success_rate: float
    average_processing_time: float
    total_processing_time: float
    events_per_minute: float
    last_event_time: Optional[datetime]
    error_distribution: Dict[str, int]

@dataclass
class WebhookHealth:
    """Webhook health status"""
    is_healthy: bool
    status: str
    issues: List[str]
    recommendations: List[str]
    last_check: datetime

class WebhookMonitor:
    """Comprehensive webhook monitoring and analytics system"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Performance tracking
        self.processing_times = deque(maxlen=1000)  # Last 1000 events
        self.error_counts = defaultdict(int)
        self.event_counts = defaultdict(int)
        
        # Health thresholds
        self.success_rate_threshold = 0.95  # 95% success rate
        self.avg_processing_time_threshold = 5.0  # 5 seconds
        self.max_error_rate = 0.05  # 5% error rate
        
        # Monitoring intervals
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = None
    
    def track_webhook_event(
        self,
        event_type: str,
        processing_time: float,
        success: bool,
        error: str = None
    ) -> None:
        """Track webhook event performance"""
        try:
            # Record processing time
            self.processing_times.append(processing_time)
            
            # Update event counts
            self.event_counts[event_type] += 1
            
            # Update error counts
            if not success and error:
                self.error_counts[error] += 1
            
            # Log to database
            self._log_webhook_metric(event_type, processing_time, success, error)
            
        except Exception as e:
            logger.error(f"Error tracking webhook event: {e}")
    
    def get_webhook_metrics(
        self,
        event_type: str = None,
        time_range: str = "24h"
    ) -> WebhookMetrics:
        """Get webhook performance metrics"""
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            if time_range == "1h":
                start_time = end_time - timedelta(hours=1)
            elif time_range == "6h":
                start_time = end_time - timedelta(hours=6)
            elif time_range == "24h":
                start_time = end_time - timedelta(days=1)
            elif time_range == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_range == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(days=1)
            
            # Query database for metrics
            query = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type.in_([AuditEventType.WEBHOOK_RECEIVED, AuditEventType.WEBHOOK_PROCESSED]),
                    AuditLog.created_at >= start_time,
                    AuditLog.created_at <= end_time
                )
            )
            
            if event_type:
                query = query.filter(AuditLog.metadata.contains({'event_type': event_type}))
            
            logs = query.all()
            
            # Calculate metrics
            total_events = len([log for log in logs if log.event_type == AuditEventType.WEBHOOK_RECEIVED])
            successful_events = len([log for log in logs if log.event_type == AuditEventType.WEBHOOK_PROCESSED and 
                                   log.metadata.get('success', False)])
            failed_events = len([log for log in logs if log.event_type == AuditEventType.WEBHOOK_PROCESSED and 
                               not log.metadata.get('success', False)])
            
            success_rate = successful_events / total_events if total_events > 0 else 0.0
            
            # Calculate processing times
            processing_times = []
            for log in logs:
                if log.event_type == AuditEventType.WEBHOOK_PROCESSED:
                    # Extract processing time from metadata or calculate from timestamps
                    processing_time = log.metadata.get('processing_time', 0)
                    if processing_time:
                        processing_times.append(processing_time)
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
            total_processing_time = sum(processing_times)
            
            # Calculate events per minute
            time_diff = (end_time - start_time).total_seconds() / 60
            events_per_minute = total_events / time_diff if time_diff > 0 else 0.0
            
            # Get last event time
            last_event = query.order_by(desc(AuditLog.created_at)).first()
            last_event_time = last_event.created_at if last_event else None
            
            # Get error distribution
            error_distribution = defaultdict(int)
            for log in logs:
                if log.event_type == AuditEventType.WEBHOOK_PROCESSED and not log.metadata.get('success', False):
                    error = log.metadata.get('error', 'Unknown error')
                    error_distribution[error] += 1
            
            return WebhookMetrics(
                total_events=total_events,
                successful_events=successful_events,
                failed_events=failed_events,
                success_rate=success_rate,
                average_processing_time=avg_processing_time,
                total_processing_time=total_processing_time,
                events_per_minute=events_per_minute,
                last_event_time=last_event_time,
                error_distribution=dict(error_distribution)
            )
            
        except Exception as e:
            logger.error(f"Error getting webhook metrics: {e}")
            return WebhookMetrics(
                total_events=0,
                successful_events=0,
                failed_events=0,
                success_rate=0.0,
                average_processing_time=0.0,
                total_processing_time=0.0,
                events_per_minute=0.0,
                last_event_time=None,
                error_distribution={}
            )
    
    def get_webhook_health(self) -> WebhookHealth:
        """Get webhook health status"""
        try:
            # Check if we need to update health status
            if (self.last_health_check and 
                (datetime.utcnow() - self.last_health_check).total_seconds() < self.health_check_interval):
                return self._cached_health_status
            
            # Get recent metrics
            metrics = self.get_webhook_metrics(time_range="1h")
            
            issues = []
            recommendations = []
            
            # Check success rate
            if metrics.success_rate < self.success_rate_threshold:
                issues.append(f"Low success rate: {metrics.success_rate:.2%} (threshold: {self.success_rate_threshold:.2%})")
                recommendations.append("Review error logs and check webhook handlers")
            
            # Check processing time
            if metrics.average_processing_time > self.avg_processing_time_threshold:
                issues.append(f"High processing time: {metrics.average_processing_time:.2f}s (threshold: {self.avg_processing_time_threshold}s)")
                recommendations.append("Optimize webhook processing logic")
            
            # Check error rate
            error_rate = metrics.failed_events / metrics.total_events if metrics.total_events > 0 else 0
            if error_rate > self.max_error_rate:
                issues.append(f"High error rate: {error_rate:.2%} (threshold: {self.max_error_rate:.2%})")
                recommendations.append("Investigate and fix webhook errors")
            
            # Check if no events received
            if metrics.total_events == 0:
                issues.append("No webhook events received in the last hour")
                recommendations.append("Check webhook endpoint configuration and Stripe webhook settings")
            
            # Check last event time
            if metrics.last_event_time:
                time_since_last = (datetime.utcnow() - metrics.last_event_time).total_seconds()
                if time_since_last > 3600:  # 1 hour
                    issues.append(f"No webhook events in {time_since_last/3600:.1f} hours")
                    recommendations.append("Verify webhook endpoint is accessible and properly configured")
            
            # Determine overall health
            is_healthy = len(issues) == 0
            status = "healthy" if is_healthy else "unhealthy"
            
            # Create health status
            health = WebhookHealth(
                is_healthy=is_healthy,
                status=status,
                issues=issues,
                recommendations=recommendations,
                last_check=datetime.utcnow()
            )
            
            # Cache health status
            self._cached_health_status = health
            self.last_health_check = datetime.utcnow()
            
            return health
            
        except Exception as e:
            logger.error(f"Error getting webhook health: {e}")
            return WebhookHealth(
                is_healthy=False,
                status="error",
                issues=[f"Error checking health: {str(e)}"],
                recommendations=["Check webhook monitoring system"],
                last_check=datetime.utcnow()
            )
    
    def get_event_type_analytics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Get analytics by event type"""
        try:
            metrics = self.get_webhook_metrics(time_range=time_range)
            
            # Query for event type breakdown
            query = self.db.query(
                AuditLog.metadata['event_type'].label('event_type'),
                func.count(AuditLog.id).label('count')
            ).filter(
                and_(
                    AuditLog.event_type == AuditEventType.WEBHOOK_RECEIVED,
                    AuditLog.created_at >= datetime.utcnow() - timedelta(days=1)
                )
            ).group_by('event_type')
            
            event_type_counts = {row.event_type: row.count for row in query.all()}
            
            # Get processing time by event type
            processing_times_by_type = {}
            for event_type in event_type_counts.keys():
                event_metrics = self.get_webhook_metrics(event_type=event_type, time_range=time_range)
                processing_times_by_type[event_type] = {
                    'avg_processing_time': event_metrics.average_processing_time,
                    'success_rate': event_metrics.success_rate,
                    'total_events': event_metrics.total_events
                }
            
            return {
                'event_type_counts': event_type_counts,
                'processing_times_by_type': processing_times_by_type,
                'overall_metrics': {
                    'total_events': metrics.total_events,
                    'success_rate': metrics.success_rate,
                    'avg_processing_time': metrics.average_processing_time,
                    'events_per_minute': metrics.events_per_minute
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting event type analytics: {e}")
            return {}
    
    def get_error_analytics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Get error analytics and patterns"""
        try:
            # Query for error logs
            query = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.WEBHOOK_PROCESSED,
                    AuditLog.metadata.contains({'success': False}),
                    AuditLog.created_at >= datetime.utcnow() - timedelta(days=1)
                )
            )
            
            error_logs = query.all()
            
            # Analyze error patterns
            error_patterns = defaultdict(int)
            error_timestamps = []
            
            for log in error_logs:
                error = log.metadata.get('error', 'Unknown error')
                error_patterns[error] += 1
                error_timestamps.append(log.created_at)
            
            # Find most common errors
            most_common_errors = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Analyze error timing patterns
            error_timing = self._analyze_error_timing(error_timestamps)
            
            return {
                'total_errors': len(error_logs),
                'error_patterns': dict(error_patterns),
                'most_common_errors': most_common_errors,
                'error_timing': error_timing,
                'error_rate': len(error_logs) / max(1, self.get_webhook_metrics(time_range=time_range).total_events)
            }
            
        except Exception as e:
            logger.error(f"Error getting error analytics: {e}")
            return {}
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over time"""
        try:
            trends = {
                'success_rate_trend': [],
                'processing_time_trend': [],
                'events_per_hour_trend': [],
                'error_rate_trend': []
            }
            
            # Get hourly metrics for the specified period
            for hour in range(hours):
                end_time = datetime.utcnow() - timedelta(hours=hour)
                start_time = end_time - timedelta(hours=1)
                
                # Query for hourly metrics
                query = self.db.query(AuditLog).filter(
                    and_(
                        AuditLog.event_type.in_([AuditEventType.WEBHOOK_RECEIVED, AuditEventType.WEBHOOK_PROCESSED]),
                        AuditLog.created_at >= start_time,
                        AuditLog.created_at <= end_time
                    )
                )
                
                logs = query.all()
                
                # Calculate hourly metrics
                total_events = len([log for log in logs if log.event_type == AuditEventType.WEBHOOK_RECEIVED])
                successful_events = len([log for log in logs if log.event_type == AuditEventType.WEBHOOK_PROCESSED and 
                                       log.metadata.get('success', False)])
                failed_events = len([log for log in logs if log.event_type == AuditEventType.WEBHOOK_PROCESSED and 
                                   not log.metadata.get('success', False)])
                
                success_rate = successful_events / total_events if total_events > 0 else 0.0
                error_rate = failed_events / total_events if total_events > 0 else 0.0
                
                # Calculate average processing time
                processing_times = []
                for log in logs:
                    if log.event_type == AuditEventType.WEBHOOK_PROCESSED:
                        processing_time = log.metadata.get('processing_time', 0)
                        if processing_time:
                            processing_times.append(processing_time)
                
                avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
                
                # Add to trends
                trends['success_rate_trend'].append({
                    'timestamp': end_time.isoformat(),
                    'value': success_rate
                })
                trends['processing_time_trend'].append({
                    'timestamp': end_time.isoformat(),
                    'value': avg_processing_time
                })
                trends['events_per_hour_trend'].append({
                    'timestamp': end_time.isoformat(),
                    'value': total_events
                })
                trends['error_rate_trend'].append({
                    'timestamp': end_time.isoformat(),
                    'value': error_rate
                })
            
            # Reverse to get chronological order
            for key in trends:
                trends[key].reverse()
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {}
    
    def _log_webhook_metric(
        self,
        event_type: str,
        processing_time: float,
        success: bool,
        error: str = None
    ) -> None:
        """Log webhook metric to database"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.WEBHOOK_METRIC,
                event_description=f"Webhook metric: {event_type}",
                severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
                metadata={
                    'event_type': event_type,
                    'processing_time': processing_time,
                    'success': success,
                    'error': error,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging webhook metric: {e}")
    
    def _analyze_error_timing(self, error_timestamps: List[datetime]) -> Dict[str, Any]:
        """Analyze error timing patterns"""
        if not error_timestamps:
            return {}
        
        # Group errors by hour
        hourly_errors = defaultdict(int)
        for timestamp in error_timestamps:
            hour = timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_errors[hour] += 1
        
        # Find peak error hours
        peak_hours = sorted(hourly_errors.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Calculate error intervals
        intervals = []
        sorted_timestamps = sorted(error_timestamps)
        for i in range(1, len(sorted_timestamps)):
            interval = (sorted_timestamps[i] - sorted_timestamps[i-1]).total_seconds()
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        return {
            'hourly_distribution': dict(hourly_errors),
            'peak_error_hours': peak_hours,
            'average_error_interval_seconds': avg_interval,
            'total_errors': len(error_timestamps)
        }
    
    def generate_webhook_report(self, time_range: str = "24h") -> Dict[str, Any]:
        """Generate comprehensive webhook report"""
        try:
            metrics = self.get_webhook_metrics(time_range=time_range)
            health = self.get_webhook_health()
            event_analytics = self.get_event_type_analytics(time_range=time_range)
            error_analytics = self.get_error_analytics(time_range=time_range)
            trends = self.get_performance_trends(hours=24 if time_range == "24h" else 1)
            
            return {
                'report_generated_at': datetime.utcnow().isoformat(),
                'time_range': time_range,
                'summary': {
                    'total_events': metrics.total_events,
                    'success_rate': metrics.success_rate,
                    'avg_processing_time': metrics.average_processing_time,
                    'events_per_minute': metrics.events_per_minute,
                    'is_healthy': health.is_healthy,
                    'status': health.status
                },
                'health': {
                    'is_healthy': health.is_healthy,
                    'status': health.status,
                    'issues': health.issues,
                    'recommendations': health.recommendations
                },
                'metrics': {
                    'total_events': metrics.total_events,
                    'successful_events': metrics.successful_events,
                    'failed_events': metrics.failed_events,
                    'success_rate': metrics.success_rate,
                    'average_processing_time': metrics.average_processing_time,
                    'total_processing_time': metrics.total_processing_time,
                    'events_per_minute': metrics.events_per_minute,
                    'last_event_time': metrics.last_event_time.isoformat() if metrics.last_event_time else None,
                    'error_distribution': metrics.error_distribution
                },
                'event_analytics': event_analytics,
                'error_analytics': error_analytics,
                'trends': trends
            }
            
        except Exception as e:
            logger.error(f"Error generating webhook report: {e}")
            return {
                'error': str(e),
                'report_generated_at': datetime.utcnow().isoformat()
            } 