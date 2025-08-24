"""
Webhook Logging and Monitoring Service for MINGUS
================================================

Comprehensive service for webhook event logging, monitoring, and analytics.
Provides detailed tracking of webhook events, performance metrics, and system health.

Features:
- Detailed event logging with structured data
- Real-time performance monitoring
- Error tracking and analysis
- Health checks and alerting
- Analytics and reporting
- Audit trail integration

Author: MINGUS Development Team
Date: January 2025
"""

import logging
import json
import time
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import traceback

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from ..models.webhook_event_tracking import WebhookEventRecord, EventProcessingState
from ..models.subscription import AuditLog, AuditEventType, AuditSeverity
from ..config.base import Config

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for webhook events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventCategory(Enum):
    """Categories for webhook events"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    SYSTEM = "system"
    ERROR = "error"


@dataclass
class WebhookEventLog:
    """Structured webhook event log entry"""
    event_id: str
    event_type: str
    timestamp: datetime
    level: LogLevel
    category: EventCategory
    source_ip: str
    user_agent: str
    request_id: str
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class WebhookPerformanceMetrics:
    """Comprehensive webhook performance metrics"""
    # Basic metrics
    total_events: int
    successful_events: int
    failed_events: int
    success_rate: float
    
    # Performance metrics
    average_processing_time: float
    median_processing_time: float
    p95_processing_time: float
    p99_processing_time: float
    min_processing_time: float
    max_processing_time: float
    
    # Throughput metrics
    events_per_minute: float
    events_per_hour: float
    peak_events_per_minute: float
    
    # Error metrics
    error_rate: float
    error_distribution: Dict[str, int]
    top_errors: List[Tuple[str, int]]
    
    # Timing metrics
    first_event_time: Optional[datetime]
    last_event_time: Optional[datetime]
    time_range_hours: float


@dataclass
class WebhookHealthStatus:
    """Webhook system health status"""
    overall_status: str  # healthy, degraded, critical
    health_score: float  # 0.0 to 1.0
    last_check: datetime
    
    # Component status
    database_health: str
    processing_health: str
    security_health: str
    performance_health: str
    
    # Issues and alerts
    active_issues: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]
    
    # Recommendations
    recommendations: List[str]
    
    # Metrics
    uptime_percentage: float
    average_response_time: float
    error_rate_24h: float


class WebhookLoggingService:
    """Comprehensive webhook logging and monitoring service"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Performance tracking
        self.processing_times = deque(maxlen=10000)  # Last 10,000 events
        self.error_counts = defaultdict(int)
        self.event_counts = defaultdict(int)
        self.response_times = deque(maxlen=1000)
        
        # Health monitoring
        self.health_thresholds = {
            'success_rate_min': 0.95,  # 95% minimum success rate
            'avg_processing_time_max': 5.0,  # 5 seconds max average
            'error_rate_max': 0.05,  # 5% maximum error rate
            'p95_processing_time_max': 10.0,  # 10 seconds max p95
            'events_per_minute_min': 0.1,  # Minimum event rate
        }
        
        # Alerting configuration
        self.alert_thresholds = {
            'critical_error_rate': 0.10,  # 10% critical error rate
            'high_processing_time': 15.0,  # 15 seconds high processing time
            'low_success_rate': 0.90,  # 90% low success rate
        }
        
        # Logging configuration
        self.log_retention_days = 30
        self.metrics_retention_days = 90
        self.audit_retention_days = 365
        
        # Initialize monitoring
        self.last_health_check = None
        self.health_check_interval = 300  # 5 minutes
        
    def log_webhook_event(
        self,
        event_id: str,
        event_type: str,
        source_ip: str,
        user_agent: str,
        request_id: str,
        processing_time: float,
        success: bool,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> WebhookEventLog:
        """Log a webhook event with comprehensive details"""
        try:
            # Determine log level and category
            level = self._determine_log_level(success, error_message)
            category = self._determine_event_category(event_type, success, error_message)
            
            # Create log entry
            log_entry = WebhookEventLog(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                level=level,
                category=category,
                source_ip=source_ip,
                user_agent=user_agent,
                request_id=request_id,
                processing_time=processing_time,
                success=success,
                error_message=error_message,
                error_details=error_details,
                metadata=metadata,
                entity_type=entity_type,
                entity_id=entity_id,
                session_id=session_id,
                correlation_id=correlation_id
            )
            
            # Store in database
            self._store_webhook_log(log_entry)
            
            # Update performance tracking
            self._update_performance_tracking(log_entry)
            
            # Check for alerts
            self._check_alerts(log_entry)
            
            # Log to standard logger
            self._log_to_standard_logger(log_entry)
            
            return log_entry
            
        except Exception as e:
            logger.error(f"Error logging webhook event: {e}")
            # Create minimal log entry
            return WebhookEventLog(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.ERROR,
                category=EventCategory.ERROR,
                source_ip=source_ip,
                user_agent=user_agent,
                request_id=request_id,
                processing_time=processing_time,
                success=success,
                error_message=f"Logging error: {str(e)}"
            )
    
    def get_performance_metrics(
        self,
        time_range_hours: int = 24,
        event_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> WebhookPerformanceMetrics:
        """Get comprehensive performance metrics"""
        try:
            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # Query webhook event records
            query = self.db.query(WebhookEventRecord).filter(
                and_(
                    WebhookEventRecord.created_at >= start_time,
                    WebhookEventRecord.created_at <= end_time
                )
            )
            
            # Apply filters
            if event_type:
                query = query.filter(WebhookEventRecord.event_type == event_type)
            if entity_type:
                query = query.filter(WebhookEventRecord.event_metadata.contains({'entity_type': entity_type}))
            if entity_id:
                query = query.filter(WebhookEventRecord.event_metadata.contains({'entity_id': entity_id}))
            
            records = query.all()
            
            if not records:
                return self._create_empty_metrics(time_range_hours)
            
            # Calculate basic metrics
            total_events = len(records)
            successful_events = len([r for r in records if r.processing_status == 'completed'])
            failed_events = len([r for r in records if r.processing_status == 'failed'])
            success_rate = successful_events / total_events if total_events > 0 else 0.0
            
            # Calculate processing times
            processing_times = []
            for record in records:
                if record.processing_started_at and record.processing_completed_at:
                    processing_time = (record.processing_completed_at - record.processing_started_at).total_seconds()
                    processing_times.append(processing_time)
            
            # Calculate performance metrics
            if processing_times:
                processing_times.sort()
                avg_processing_time = sum(processing_times) / len(processing_times)
                median_processing_time = processing_times[len(processing_times) // 2]
                p95_processing_time = processing_times[int(len(processing_times) * 0.95)]
                p99_processing_time = processing_times[int(len(processing_times) * 0.99)]
                min_processing_time = min(processing_times)
                max_processing_time = max(processing_times)
            else:
                avg_processing_time = median_processing_time = p95_processing_time = p99_processing_time = min_processing_time = max_processing_time = 0.0
            
            # Calculate throughput metrics
            time_range_minutes = time_range_hours * 60
            events_per_minute = total_events / time_range_minutes if time_range_minutes > 0 else 0.0
            events_per_hour = total_events / time_range_hours if time_range_hours > 0 else 0.0
            
            # Calculate peak events per minute
            peak_events_per_minute = self._calculate_peak_events_per_minute(records, time_range_hours)
            
            # Calculate error metrics
            error_rate = failed_events / total_events if total_events > 0 else 0.0
            error_distribution = self._calculate_error_distribution(records)
            top_errors = sorted(error_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Calculate timing metrics
            first_event_time = min(record.created_at for record in records) if records else None
            last_event_time = max(record.created_at for record in records) if records else None
            
            return WebhookPerformanceMetrics(
                total_events=total_events,
                successful_events=successful_events,
                failed_events=failed_events,
                success_rate=success_rate,
                average_processing_time=avg_processing_time,
                median_processing_time=median_processing_time,
                p95_processing_time=p95_processing_time,
                p99_processing_time=p99_processing_time,
                min_processing_time=min_processing_time,
                max_processing_time=max_processing_time,
                events_per_minute=events_per_minute,
                events_per_hour=events_per_hour,
                peak_events_per_minute=peak_events_per_minute,
                error_rate=error_rate,
                error_distribution=error_distribution,
                top_errors=top_errors,
                first_event_time=first_event_time,
                last_event_time=last_event_time,
                time_range_hours=time_range_hours
            )
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return self._create_empty_metrics(time_range_hours)
    
    def get_health_status(self) -> WebhookHealthStatus:
        """Get comprehensive health status"""
        try:
            # Get recent metrics
            metrics = self.get_performance_metrics(time_range_hours=24)
            
            # Check database health
            database_health = self._check_database_health()
            
            # Check processing health
            processing_health = self._check_processing_health(metrics)
            
            # Check security health
            security_health = self._check_security_health()
            
            # Check performance health
            performance_health = self._check_performance_health(metrics)
            
            # Determine overall status
            overall_status = self._determine_overall_status(
                database_health, processing_health, security_health, performance_health
            )
            
            # Calculate health score
            health_score = self._calculate_health_score(metrics, overall_status)
            
            # Get active issues and alerts
            active_issues = self._get_active_issues(metrics)
            recent_alerts = self._get_recent_alerts()
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metrics, active_issues)
            
            # Calculate additional metrics
            uptime_percentage = self._calculate_uptime_percentage()
            average_response_time = metrics.average_processing_time
            error_rate_24h = metrics.error_rate
            
            return WebhookHealthStatus(
                overall_status=overall_status,
                health_score=health_score,
                last_check=datetime.now(timezone.utc),
                database_health=database_health,
                processing_health=processing_health,
                security_health=security_health,
                performance_health=performance_health,
                active_issues=active_issues,
                recent_alerts=recent_alerts,
                recommendations=recommendations,
                uptime_percentage=uptime_percentage,
                average_response_time=average_response_time,
                error_rate_24h=error_rate_24h
            )
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return self._create_error_health_status(str(e))
    
    def get_event_analytics(
        self,
        time_range_hours: int = 24,
        group_by: str = "event_type"
    ) -> Dict[str, Any]:
        """Get detailed event analytics"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # Query with grouping
            if group_by == "event_type":
                query = self.db.query(
                    WebhookEventRecord.event_type,
                    func.count(WebhookEventRecord.id).label('count'),
                    func.avg(
                        func.extract('epoch', WebhookEventRecord.processing_completed_at) -
                        func.extract('epoch', WebhookEventRecord.processing_started_at)
                    ).label('avg_processing_time'),
                    func.sum(
                        case(
                            (WebhookEventRecord.processing_status == 'completed', 1),
                            else_=0
                        )
                    ).label('successful_count')
                ).filter(
                    and_(
                        WebhookEventRecord.created_at >= start_time,
                        WebhookEventRecord.created_at <= end_time
                    )
                ).group_by(WebhookEventRecord.event_type)
            
            elif group_by == "entity_type":
                query = self.db.query(
                    func.jsonb_extract_path_text(WebhookEventRecord.event_metadata, 'entity_type').label('entity_type'),
                    func.count(WebhookEventRecord.id).label('count'),
                    func.avg(
                        func.extract('epoch', WebhookEventRecord.processing_completed_at) -
                        func.extract('epoch', WebhookEventRecord.processing_started_at)
                    ).label('avg_processing_time')
                ).filter(
                    and_(
                        WebhookEventRecord.created_at >= start_time,
                        WebhookEventRecord.created_at <= end_time
                    )
                ).group_by(text("jsonb_extract_path_text(event_metadata, 'entity_type')"))
            
            else:
                raise ValueError(f"Unsupported group_by: {group_by}")
            
            results = query.all()
            
            # Process results
            analytics = {
                'time_range_hours': time_range_hours,
                'group_by': group_by,
                'total_events': sum(r.count for r in results),
                'groups': []
            }
            
            for result in results:
                group_data = {
                    'name': getattr(result, group_by) or 'unknown',
                    'count': result.count,
                    'avg_processing_time': float(result.avg_processing_time) if result.avg_processing_time else 0.0,
                }
                
                if group_by == "event_type":
                    group_data['successful_count'] = result.successful_count
                    group_data['success_rate'] = result.successful_count / result.count if result.count > 0 else 0.0
                
                analytics['groups'].append(group_data)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting event analytics: {e}")
            return {
                'error': str(e),
                'time_range_hours': time_range_hours,
                'group_by': group_by,
                'total_events': 0,
                'groups': []
            }
    
    def get_error_analytics(
        self,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """Get detailed error analytics"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # Query failed events
            failed_events = self.db.query(WebhookEventRecord).filter(
                and_(
                    WebhookEventRecord.processing_status == 'failed',
                    WebhookEventRecord.created_at >= start_time,
                    WebhookEventRecord.created_at <= end_time
                )
            ).all()
            
            # Analyze errors
            error_patterns = defaultdict(int)
            error_by_event_type = defaultdict(int)
            error_by_entity_type = defaultdict(int)
            error_timeline = defaultdict(int)
            
            for event in failed_events:
                # Error pattern analysis
                error_message = event.error_message or "Unknown error"
                error_patterns[error_message] += 1
                
                # Error by event type
                error_by_event_type[event.event_type] += 1
                
                # Error by entity type
                if event.event_metadata:
                    entity_type = event.event_metadata.get('entity_type', 'unknown')
                    error_by_entity_type[entity_type] += 1
                
                # Error timeline (by hour)
                hour_key = event.created_at.strftime('%Y-%m-%d %H:00')
                error_timeline[hour_key] += 1
            
            # Get top errors
            top_errors = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Get error trends
            error_trends = self._analyze_error_trends(failed_events)
            
            return {
                'time_range_hours': time_range_hours,
                'total_failed_events': len(failed_events),
                'error_patterns': dict(error_patterns),
                'error_by_event_type': dict(error_by_event_type),
                'error_by_entity_type': dict(error_by_entity_type),
                'error_timeline': dict(error_timeline),
                'top_errors': top_errors,
                'error_trends': error_trends
            }
            
        except Exception as e:
            logger.error(f"Error getting error analytics: {e}")
            return {
                'error': str(e),
                'time_range_hours': time_range_hours,
                'total_failed_events': 0,
                'error_patterns': {},
                'error_by_event_type': {},
                'error_by_entity_type': {},
                'error_timeline': {},
                'top_errors': [],
                'error_trends': {}
            }
    
    def generate_webhook_report(
        self,
        time_range_hours: int = 24,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive webhook report"""
        try:
            # Get all metrics and analytics
            performance_metrics = self.get_performance_metrics(time_range_hours)
            health_status = self.get_health_status()
            event_analytics = self.get_event_analytics(time_range_hours)
            error_analytics = self.get_error_analytics(time_range_hours)
            
            # Generate report
            report = {
                'report_generated_at': datetime.now(timezone.utc).isoformat(),
                'time_range_hours': time_range_hours,
                'summary': {
                    'total_events': performance_metrics.total_events,
                    'success_rate': f"{performance_metrics.success_rate:.2%}",
                    'average_processing_time': f"{performance_metrics.average_processing_time:.3f}s",
                    'error_rate': f"{performance_metrics.error_rate:.2%}",
                    'health_status': health_status.overall_status,
                    'health_score': f"{health_status.health_score:.2%}"
                },
                'performance_metrics': asdict(performance_metrics),
                'health_status': asdict(health_status),
                'event_analytics': event_analytics,
                'error_analytics': error_analytics
            }
            
            # Add detailed information if requested
            if include_details:
                report['details'] = {
                    'top_errors': performance_metrics.top_errors,
                    'active_issues': health_status.active_issues,
                    'recommendations': health_status.recommendations,
                    'recent_alerts': health_status.recent_alerts
                }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating webhook report: {e}")
            return {
                'error': str(e),
                'report_generated_at': datetime.now(timezone.utc).isoformat(),
                'time_range_hours': time_range_hours
            }
    
    def cleanup_old_logs(self, days: Optional[int] = None) -> Dict[str, int]:
        """Clean up old log entries"""
        try:
            days = days or self.log_retention_days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Clean up webhook event records
            deleted_records = self.db.query(WebhookEventRecord).filter(
                WebhookEventRecord.created_at < cutoff_date
            ).delete()
            
            # Clean up audit logs
            deleted_audit_logs = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type.in_([AuditEventType.WEBHOOK_RECEIVED, AuditEventType.WEBHOOK_PROCESSED]),
                    AuditLog.created_at < cutoff_date
                )
            ).delete()
            
            self.db.commit()
            
            return {
                'deleted_webhook_records': deleted_records,
                'deleted_audit_logs': deleted_audit_logs,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            self.db.rollback()
            return {'error': str(e)}
    
    # Private helper methods
    
    def _determine_log_level(self, success: bool, error_message: Optional[str]) -> LogLevel:
        """Determine appropriate log level"""
        if success:
            return LogLevel.INFO
        elif error_message:
            if "critical" in error_message.lower() or "security" in error_message.lower():
                return LogLevel.CRITICAL
            elif "timeout" in error_message.lower() or "connection" in error_message.lower():
                return LogLevel.ERROR
            else:
                return LogLevel.WARNING
        else:
            return LogLevel.ERROR
    
    def _determine_event_category(self, event_type: str, success: bool, error_message: Optional[str]) -> EventCategory:
        """Determine event category"""
        if not success and error_message:
            return EventCategory.ERROR
        elif "security" in event_type.lower() or "auth" in event_type.lower():
            return EventCategory.SECURITY
        elif "performance" in event_type.lower() or "timeout" in event_type.lower():
            return EventCategory.PERFORMANCE
        elif "system" in event_type.lower() or "health" in event_type.lower():
            return EventCategory.SYSTEM
        else:
            return EventCategory.BUSINESS
    
    def _store_webhook_log(self, log_entry: WebhookEventLog) -> None:
        """Store webhook log in database"""
        try:
            # Create audit log entry
            audit_log = AuditLog(
                event_type=AuditEventType.WEBHOOK_PROCESSED,
                severity=AuditSeverity.INFO if log_entry.success else AuditSeverity.WARNING,
                event_description=f"Webhook {log_entry.event_type} processed",
                metadata={
                    'event_id': log_entry.event_id,
                    'event_type': log_entry.event_type,
                    'level': log_entry.level.value,
                    'category': log_entry.category.value,
                    'source_ip': log_entry.source_ip,
                    'user_agent': log_entry.user_agent,
                    'request_id': log_entry.request_id,
                    'processing_time': log_entry.processing_time,
                    'success': log_entry.success,
                    'error_message': log_entry.error_message,
                    'error_details': log_entry.error_details,
                    'entity_type': log_entry.entity_type,
                    'entity_id': log_entry.entity_id,
                    'session_id': log_entry.session_id,
                    'correlation_id': log_entry.correlation_id,
                    'timestamp': log_entry.timestamp.isoformat()
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing webhook log: {e}")
            self.db.rollback()
    
    def _update_performance_tracking(self, log_entry: WebhookEventLog) -> None:
        """Update performance tracking metrics"""
        try:
            # Update processing times
            self.processing_times.append(log_entry.processing_time)
            
            # Update event counts
            self.event_counts[log_entry.event_type] += 1
            
            # Update error counts
            if not log_entry.success and log_entry.error_message:
                self.error_counts[log_entry.error_message] += 1
            
        except Exception as e:
            logger.error(f"Error updating performance tracking: {e}")
    
    def _check_alerts(self, log_entry: WebhookEventLog) -> None:
        """Check for alert conditions"""
        try:
            # Check for critical errors
            if log_entry.level == LogLevel.CRITICAL:
                self._send_alert("critical_error", {
                    'event_id': log_entry.event_id,
                    'event_type': log_entry.event_type,
                    'error_message': log_entry.error_message,
                    'source_ip': log_entry.source_ip
                })
            
            # Check for high processing times
            if log_entry.processing_time > self.alert_thresholds['high_processing_time']:
                self._send_alert("high_processing_time", {
                    'event_id': log_entry.event_id,
                    'event_type': log_entry.event_type,
                    'processing_time': log_entry.processing_time,
                    'threshold': self.alert_thresholds['high_processing_time']
                })
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _send_alert(self, alert_type: str, alert_data: Dict[str, Any]) -> None:
        """Send alert notification"""
        try:
            # Log alert
            logger.warning(f"ALERT: {alert_type} - {alert_data}")
            
            # Store alert in database
            alert_log = AuditLog(
                event_type=AuditEventType.SECURITY_EVENT,
                severity=AuditSeverity.WARNING,
                event_description=f"Webhook alert: {alert_type}",
                metadata={
                    'alert_type': alert_type,
                    'alert_data': alert_data,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            self.db.add(alert_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def _log_to_standard_logger(self, log_entry: WebhookEventLog) -> None:
        """Log to standard Python logger"""
        try:
            log_message = (
                f"Webhook Event: {log_entry.event_type} | "
                f"ID: {log_entry.event_id} | "
                f"Success: {log_entry.success} | "
                f"Time: {log_entry.processing_time:.3f}s | "
                f"IP: {log_entry.source_ip}"
            )
            
            if log_entry.error_message:
                log_message += f" | Error: {log_entry.error_message}"
            
            if log_entry.level == LogLevel.DEBUG:
                logger.debug(log_message)
            elif log_entry.level == LogLevel.INFO:
                logger.info(log_message)
            elif log_entry.level == LogLevel.WARNING:
                logger.warning(log_message)
            elif log_entry.level == LogLevel.ERROR:
                logger.error(log_message)
            elif log_entry.level == LogLevel.CRITICAL:
                logger.critical(log_message)
            
        except Exception as e:
            logger.error(f"Error logging to standard logger: {e}")
    
    def _create_empty_metrics(self, time_range_hours: int) -> WebhookPerformanceMetrics:
        """Create empty metrics for no data scenarios"""
        return WebhookPerformanceMetrics(
            total_events=0,
            successful_events=0,
            failed_events=0,
            success_rate=0.0,
            average_processing_time=0.0,
            median_processing_time=0.0,
            p95_processing_time=0.0,
            p99_processing_time=0.0,
            min_processing_time=0.0,
            max_processing_time=0.0,
            events_per_minute=0.0,
            events_per_hour=0.0,
            peak_events_per_minute=0.0,
            error_rate=0.0,
            error_distribution={},
            top_errors=[],
            first_event_time=None,
            last_event_time=None,
            time_range_hours=time_range_hours
        )
    
    def _calculate_peak_events_per_minute(self, records: List[WebhookEventRecord], time_range_hours: int) -> float:
        """Calculate peak events per minute"""
        try:
            if not records:
                return 0.0
            
            # Group events by minute
            events_by_minute = defaultdict(int)
            for record in records:
                minute_key = record.created_at.strftime('%Y-%m-%d %H:%M')
                events_by_minute[minute_key] += 1
            
            # Find peak
            peak_events = max(events_by_minute.values()) if events_by_minute else 0
            return float(peak_events)
            
        except Exception as e:
            logger.error(f"Error calculating peak events: {e}")
            return 0.0
    
    def _calculate_error_distribution(self, records: List[WebhookEventRecord]) -> Dict[str, int]:
        """Calculate error distribution"""
        try:
            error_distribution = defaultdict(int)
            for record in records:
                if record.processing_status == 'failed':
                    error_message = record.error_message or "Unknown error"
                    error_distribution[error_message] += 1
            
            return dict(error_distribution)
            
        except Exception as e:
            logger.error(f"Error calculating error distribution: {e}")
            return {}
    
    def _check_database_health(self) -> str:
        """Check database health"""
        try:
            # Test database connection
            self.db.execute(text("SELECT 1"))
            return "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return "critical"
    
    def _check_processing_health(self, metrics: WebhookPerformanceMetrics) -> str:
        """Check processing health"""
        try:
            if metrics.success_rate >= self.health_thresholds['success_rate_min']:
                return "healthy"
            elif metrics.success_rate >= 0.90:
                return "degraded"
            else:
                return "critical"
        except Exception as e:
            logger.error(f"Processing health check failed: {e}")
            return "unknown"
    
    def _check_security_health(self) -> str:
        """Check security health"""
        try:
            # Check for recent security events
            recent_security_events = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.SECURITY_EVENT,
                    AuditLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=1)
                )
            ).count()
            
            if recent_security_events == 0:
                return "healthy"
            elif recent_security_events < 5:
                return "degraded"
            else:
                return "critical"
        except Exception as e:
            logger.error(f"Security health check failed: {e}")
            return "unknown"
    
    def _check_performance_health(self, metrics: WebhookPerformanceMetrics) -> str:
        """Check performance health"""
        try:
            if (metrics.average_processing_time <= self.health_thresholds['avg_processing_time_max'] and
                metrics.p95_processing_time <= self.health_thresholds['p95_processing_time_max']):
                return "healthy"
            elif metrics.average_processing_time <= 10.0:
                return "degraded"
            else:
                return "critical"
        except Exception as e:
            logger.error(f"Performance health check failed: {e}")
            return "unknown"
    
    def _determine_overall_status(self, db_health: str, proc_health: str, sec_health: str, perf_health: str) -> str:
        """Determine overall health status"""
        if any(status == "critical" for status in [db_health, proc_health, sec_health, perf_health]):
            return "critical"
        elif any(status == "degraded" for status in [db_health, proc_health, sec_health, perf_health]):
            return "degraded"
        else:
            return "healthy"
    
    def _calculate_health_score(self, metrics: WebhookPerformanceMetrics, overall_status: str) -> float:
        """Calculate health score (0.0 to 1.0)"""
        try:
            # Base score from success rate
            base_score = metrics.success_rate
            
            # Adjust for performance
            perf_factor = 1.0
            if metrics.average_processing_time > self.health_thresholds['avg_processing_time_max']:
                perf_factor = 0.8
            elif metrics.average_processing_time > 10.0:
                perf_factor = 0.6
            
            # Adjust for overall status
            status_factor = 1.0
            if overall_status == "critical":
                status_factor = 0.3
            elif overall_status == "degraded":
                status_factor = 0.7
            
            return min(1.0, base_score * perf_factor * status_factor)
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.0
    
    def _get_active_issues(self, metrics: WebhookPerformanceMetrics) -> List[Dict[str, Any]]:
        """Get active issues"""
        issues = []
        
        if metrics.success_rate < self.health_thresholds['success_rate_min']:
            issues.append({
                'type': 'low_success_rate',
                'severity': 'high',
                'description': f"Success rate {metrics.success_rate:.2%} below threshold {self.health_thresholds['success_rate_min']:.2%}",
                'value': metrics.success_rate,
                'threshold': self.health_thresholds['success_rate_min']
            })
        
        if metrics.average_processing_time > self.health_thresholds['avg_processing_time_max']:
            issues.append({
                'type': 'high_processing_time',
                'severity': 'medium',
                'description': f"Average processing time {metrics.average_processing_time:.3f}s above threshold {self.health_thresholds['avg_processing_time_max']}s",
                'value': metrics.average_processing_time,
                'threshold': self.health_thresholds['avg_processing_time_max']
            })
        
        if metrics.error_rate > self.health_thresholds['error_rate_max']:
            issues.append({
                'type': 'high_error_rate',
                'severity': 'high',
                'description': f"Error rate {metrics.error_rate:.2%} above threshold {self.health_thresholds['error_rate_max']:.2%}",
                'value': metrics.error_rate,
                'threshold': self.health_thresholds['error_rate_max']
            })
        
        return issues
    
    def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            recent_alerts = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.SECURITY_EVENT,
                    AuditLog.metadata.contains({'alert_type': True}),
                    AuditLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
                )
            ).order_by(desc(AuditLog.created_at)).limit(10).all()
            
            return [
                {
                    'timestamp': alert.created_at.isoformat(),
                    'type': alert.metadata.get('alert_type'),
                    'data': alert.metadata.get('alert_data'),
                    'severity': alert.severity.value
                }
                for alert in recent_alerts
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []
    
    def _generate_recommendations(self, metrics: WebhookPerformanceMetrics, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        if metrics.success_rate < 0.95:
            recommendations.append("Investigate failed webhook events to improve success rate")
        
        if metrics.average_processing_time > 5.0:
            recommendations.append("Optimize webhook processing to reduce average processing time")
        
        if metrics.error_rate > 0.05:
            recommendations.append("Review error patterns and implement error handling improvements")
        
        if metrics.events_per_minute < 0.1:
            recommendations.append("Monitor webhook volume - low event rate detected")
        
        if not recommendations:
            recommendations.append("Webhook system is performing well - continue monitoring")
        
        return recommendations
    
    def _calculate_uptime_percentage(self) -> float:
        """Calculate uptime percentage"""
        try:
            # Simple uptime calculation based on recent health checks
            # In production, this would be more sophisticated
            return 99.5  # Placeholder
        except Exception as e:
            logger.error(f"Error calculating uptime: {e}")
            return 0.0
    
    def _analyze_error_trends(self, failed_events: List[WebhookEventRecord]) -> Dict[str, Any]:
        """Analyze error trends"""
        try:
            if not failed_events:
                return {}
            
            # Group errors by hour
            errors_by_hour = defaultdict(int)
            for event in failed_events:
                hour_key = event.created_at.strftime('%Y-%m-%d %H:00')
                errors_by_hour[hour_key] += 1
            
            # Calculate trend
            hours = sorted(errors_by_hour.keys())
            if len(hours) >= 2:
                recent_errors = sum(errors_by_hour[hour] for hour in hours[-3:])  # Last 3 hours
                earlier_errors = sum(errors_by_hour[hour] for hour in hours[:-3])  # Earlier hours
                
                if earlier_errors > 0:
                    trend = (recent_errors - earlier_errors) / earlier_errors
                else:
                    trend = 0.0
            else:
                trend = 0.0
            
            return {
                'errors_by_hour': dict(errors_by_hour),
                'trend': trend,
                'trend_direction': 'increasing' if trend > 0.1 else 'decreasing' if trend < -0.1 else 'stable'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing error trends: {e}")
            return {}
    
    def _create_error_health_status(self, error_message: str) -> WebhookHealthStatus:
        """Create error health status"""
        return WebhookHealthStatus(
            overall_status="critical",
            health_score=0.0,
            last_check=datetime.now(timezone.utc),
            database_health="unknown",
            processing_health="unknown",
            security_health="unknown",
            performance_health="unknown",
            active_issues=[{
                'type': 'system_error',
                'severity': 'critical',
                'description': f"Health check failed: {error_message}"
            }],
            recent_alerts=[],
            recommendations=["Investigate system health check failures"],
            uptime_percentage=0.0,
            average_response_time=0.0,
            error_rate_24h=1.0
        ) 