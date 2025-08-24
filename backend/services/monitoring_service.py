"""
Monitoring Service for Income Comparison Calculator
Collects and exports metrics for Prometheus monitoring
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from contextlib import contextmanager

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, generate_latest,
    CONTENT_TYPE_LATEST, REGISTRY
)
from django.conf import settings
from django.core.cache import cache
from django.db import connection

logger = logging.getLogger(__name__)


@dataclass
class MonitoringMetrics:
    """Centralized metrics collection for the income comparison calculator"""
    
    # API Metrics
    api_requests_total = Counter(
        'mingus_api_requests_total',
        'Total API requests',
        ['endpoint', 'method', 'status']
    )
    
    api_response_time_seconds = Histogram(
        'mingus_api_response_time_seconds',
        'API response time in seconds',
        ['endpoint', 'method'],
        buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
    )
    
    api_errors_total = Counter(
        'mingus_api_errors_total',
        'Total API errors',
        ['endpoint', 'error_type']
    )
    
    # External API Health
    external_api_health = Gauge(
        'mingus_external_api_health',
        'External API health status',
        ['api']
    )
    
    # Lead Generation Metrics
    lead_capture_attempts_total = Counter(
        'mingus_lead_capture_attempts_total',
        'Total lead capture attempts',
        ['step', 'location', 'industry']
    )
    
    lead_capture_total = Counter(
        'mingus_lead_capture_total',
        'Total successful lead captures',
        ['step', 'location', 'industry', 'demographic']
    )
    
    lead_engagement_score = Histogram(
        'mingus_lead_engagement_score',
        'Lead engagement scores',
        ['location', 'industry'],
        buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    )
    
    # Salary Prediction Metrics
    salary_predictions_total = Counter(
        'mingus_salary_predictions_total',
        'Total salary predictions generated',
        ['location', 'industry', 'experience_level']
    )
    
    salary_prediction_accuracy = Gauge(
        'mingus_salary_prediction_accuracy',
        'Salary prediction accuracy score',
        ['model_version']
    )
    
    # Cultural Content Metrics
    cultural_content_generated_total = Counter(
        'mingus_cultural_content_generated_total',
        'Total cultural content pieces generated',
        ['content_type', 'demographic', 'location']
    )
    
    cultural_content_failures_total = Counter(
        'mingus_cultural_content_failures_total',
        'Total cultural content generation failures',
        ['content_type', 'error_type']
    )
    
    # Gamification Metrics
    badges_unlocked_total = Counter(
        'mingus_badges_unlocked_total',
        'Total badges unlocked',
        ['badge_type', 'demographic']
    )
    
    # Email Metrics
    emails_sent_total = Counter(
        'mingus_emails_sent_total',
        'Total emails sent',
        ['sequence', 'template']
    )
    
    emails_opened_total = Counter(
        'mingus_emails_opened_total',
        'Total emails opened',
        ['sequence', 'template']
    )
    
    emails_clicked_total = Counter(
        'mingus_emails_clicked_total',
        'Total emails clicked',
        ['sequence', 'template']
    )
    
    emails_failed_total = Counter(
        'mingus_emails_failed_total',
        'Total email delivery failures',
        ['sequence', 'error_type']
    )
    
    # Database Metrics
    database_connections_active = Gauge(
        'mingus_database_connections_active',
        'Number of active database connections'
    )
    
    database_query_duration_seconds = Histogram(
        'mingus_database_query_duration_seconds',
        'Database query duration in seconds',
        ['query_type'],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
    )
    
    # Redis Metrics
    redis_memory_usage_bytes = Gauge(
        'mingus_redis_memory_usage_bytes',
        'Redis memory usage in bytes'
    )
    
    redis_cache_hits_total = Counter(
        'mingus_redis_cache_hits_total',
        'Total Redis cache hits'
    )
    
    redis_cache_misses_total = Counter(
        'mingus_redis_cache_misses_total',
        'Total Redis cache misses'
    )
    
    # Celery Metrics
    celery_tasks_total = Counter(
        'mingus_celery_tasks_total',
        'Total Celery tasks',
        ['task_type', 'status']
    )
    
    celery_tasks_completed_total = Counter(
        'mingus_celery_tasks_completed_total',
        'Total completed Celery tasks',
        ['task_type']
    )
    
    celery_tasks_failed_total = Counter(
        'mingus_celery_tasks_failed_total',
        'Total failed Celery tasks',
        ['task_type', 'error_type']
    )
    
    celery_workers_active = Gauge(
        'mingus_celery_workers_active',
        'Number of active Celery workers'
    )
    
    celery_queue_length = Gauge(
        'mingus_celery_queue_length',
        'Number of tasks in Celery queue',
        ['queue_name']
    )
    
    # Business Metrics
    high_value_lead_started_total = Counter(
        'mingus_high_value_lead_started_total',
        'Total high-value leads started',
        ['location', 'industry']
    )
    
    high_value_lead_dropoff_total = Counter(
        'mingus_high_value_lead_dropoff_total',
        'Total high-value leads that dropped off',
        ['step', 'location', 'industry']
    )
    
    salary_gap_analysis_failures_total = Counter(
        'mingus_salary_gap_analysis_failures_total',
        'Total salary gap analysis failures',
        ['location', 'industry']
    )
    
    representation_premium_errors_total = Counter(
        'mingus_representation_premium_errors_total',
        'Total representation premium calculation errors',
        ['location', 'industry']
    )
    
    # Security Metrics
    rate_limit_violations_total = Counter(
        'mingus_rate_limit_violations_total',
        'Total rate limit violations',
        ['ip_address', 'endpoint']
    )
    
    # Deployment Metrics
    deployment_version = Gauge(
        'mingus_deployment_version',
        'Current deployment version',
        ['version', 'environment']
    )
    
    deployment_rollback = Gauge(
        'mingus_deployment_rollback',
        'Deployment rollback status',
        ['version']
    )
    
    # Error Metrics
    errors_total = Counter(
        'mingus_errors_total',
        'Total errors',
        ['error_type', 'component']
    )
    
    requests_total = Counter(
        'mingus_requests_total',
        'Total requests',
        ['method', 'endpoint', 'status']
    )


class MonitoringService:
    """Service for collecting and managing monitoring metrics"""
    
    def __init__(self):
        self.metrics = MonitoringMetrics()
        self.start_time = time.time()
        
    def record_api_request(self, endpoint: str, method: str, status: int, duration: float):
        """Record API request metrics"""
        self.metrics.api_requests_total.labels(
            endpoint=endpoint,
            method=method,
            status=status
        ).inc()
        
        self.metrics.api_response_time_seconds.labels(
            endpoint=endpoint,
            method=method
        ).observe(duration)
        
        self.metrics.requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        if status >= 400:
            self.metrics.api_errors_total.labels(
                endpoint=endpoint,
                error_type=f"http_{status}"
            ).inc()
            
            self.metrics.errors_total.labels(
                error_type=f"http_{status}",
                component="api"
            ).inc()
    
    def record_external_api_health(self, api_name: str, is_healthy: bool):
        """Record external API health status"""
        self.metrics.external_api_health.labels(api=api_name).set(1 if is_healthy else 0)
    
    def record_lead_capture_attempt(self, step: str, location: str, industry: str):
        """Record lead capture attempt"""
        self.metrics.lead_capture_attempts_total.labels(
            step=step,
            location=location,
            industry=industry
        ).inc()
    
    def record_lead_capture_success(self, step: str, location: str, industry: str, demographic: str = "unknown"):
        """Record successful lead capture"""
        self.metrics.lead_capture_total.labels(
            step=step,
            location=location,
            industry=industry,
            demographic=demographic
        ).inc()
    
    def record_lead_engagement_score(self, score: float, location: str, industry: str):
        """Record lead engagement score"""
        self.metrics.lead_engagement_score.labels(
            location=location,
            industry=industry
        ).observe(score)
    
    def record_salary_prediction(self, location: str, industry: str, experience_level: str):
        """Record salary prediction generation"""
        self.metrics.salary_predictions_total.labels(
            location=location,
            industry=industry,
            experience_level=experience_level
        ).inc()
    
    def update_salary_prediction_accuracy(self, accuracy: float, model_version: str = "v1"):
        """Update salary prediction accuracy"""
        self.metrics.salary_prediction_accuracy.labels(model_version=model_version).set(accuracy)
    
    def record_cultural_content_generation(self, content_type: str, demographic: str, location: str):
        """Record cultural content generation"""
        self.metrics.cultural_content_generated_total.labels(
            content_type=content_type,
            demographic=demographic,
            location=location
        ).inc()
    
    def record_cultural_content_failure(self, content_type: str, error_type: str):
        """Record cultural content generation failure"""
        self.metrics.cultural_content_failures_total.labels(
            content_type=content_type,
            error_type=error_type
        ).inc()
    
    def record_badge_unlock(self, badge_type: str, demographic: str = "unknown"):
        """Record badge unlock"""
        self.metrics.badges_unlocked_total.labels(
            badge_type=badge_type,
            demographic=demographic
        ).inc()
    
    def record_email_sent(self, sequence: str, template: str):
        """Record email sent"""
        self.metrics.emails_sent_total.labels(
            sequence=sequence,
            template=template
        ).inc()
    
    def record_email_opened(self, sequence: str, template: str):
        """Record email opened"""
        self.metrics.emails_opened_total.labels(
            sequence=sequence,
            template=template
        ).inc()
    
    def record_email_clicked(self, sequence: str, template: str):
        """Record email clicked"""
        self.metrics.emails_clicked_total.labels(
            sequence=sequence,
            template=template
        ).inc()
    
    def record_email_failure(self, sequence: str, error_type: str):
        """Record email delivery failure"""
        self.metrics.emails_failed_total.labels(
            sequence=sequence,
            error_type=error_type
        ).inc()
    
    def update_database_connections(self, count: int):
        """Update active database connections count"""
        self.metrics.database_connections_active.set(count)
    
    def record_database_query(self, query_type: str, duration: float):
        """Record database query duration"""
        self.metrics.database_query_duration_seconds.labels(
            query_type=query_type
        ).observe(duration)
    
    def update_redis_memory_usage(self, bytes_used: int):
        """Update Redis memory usage"""
        self.metrics.redis_memory_usage_bytes.set(bytes_used)
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.metrics.redis_cache_hits_total.inc()
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.metrics.redis_cache_misses_total.inc()
    
    def record_celery_task(self, task_type: str, status: str):
        """Record Celery task"""
        self.metrics.celery_tasks_total.labels(
            task_type=task_type,
            status=status
        ).inc()
        
        if status == "completed":
            self.metrics.celery_tasks_completed_total.labels(task_type=task_type).inc()
        elif status == "failed":
            self.metrics.celery_tasks_failed_total.labels(
                task_type=task_type,
                error_type="unknown"
            ).inc()
    
    def update_celery_workers(self, count: int):
        """Update active Celery workers count"""
        self.metrics.celery_workers_active.set(count)
    
    def update_celery_queue_length(self, queue_name: str, length: int):
        """Update Celery queue length"""
        self.metrics.celery_queue_length.labels(queue_name=queue_name).set(length)
    
    def record_high_value_lead_started(self, location: str, industry: str):
        """Record high-value lead started"""
        self.metrics.high_value_lead_started_total.labels(
            location=location,
            industry=industry
        ).inc()
    
    def record_high_value_lead_dropoff(self, step: str, location: str, industry: str):
        """Record high-value lead dropoff"""
        self.metrics.high_value_lead_dropoff_total.labels(
            step=step,
            location=location,
            industry=industry
        ).inc()
    
    def record_salary_gap_analysis_failure(self, location: str, industry: str):
        """Record salary gap analysis failure"""
        self.metrics.salary_gap_analysis_failures_total.labels(
            location=location,
            industry=industry
        ).inc()
    
    def record_representation_premium_error(self, location: str, industry: str):
        """Record representation premium calculation error"""
        self.metrics.representation_premium_errors_total.labels(
            location=location,
            industry=industry
        ).inc()
    
    def record_rate_limit_violation(self, ip_address: str, endpoint: str):
        """Record rate limit violation"""
        self.metrics.rate_limit_violations_total.labels(
            ip_address=ip_address,
            endpoint=endpoint
        ).inc()
    
    def update_deployment_version(self, version: str, environment: str):
        """Update deployment version"""
        self.metrics.deployment_version.labels(
            version=version,
            environment=environment
        ).set(1)
    
    def record_deployment_rollback(self, version: str):
        """Record deployment rollback"""
        self.metrics.deployment_rollback.labels(version=version).set(1)
    
    def record_error(self, error_type: str, component: str):
        """Record general error"""
        self.metrics.errors_total.labels(
            error_type=error_type,
            component=component
        ).inc()
    
    @contextmanager
    def api_request_timer(self, endpoint: str, method: str):
        """Context manager for timing API requests"""
        start_time = time.time()
        try:
            yield
            status = 200
        except Exception as e:
            status = 500
            self.record_error(str(type(e).__name__), "api")
            raise
        finally:
            duration = time.time() - start_time
            self.record_api_request(endpoint, method, status, duration)
    
    @contextmanager
    def database_query_timer(self, query_type: str):
        """Context manager for timing database queries"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_database_query(query_type, duration)
    
    def collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            # Database connections
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
                active_connections = cursor.fetchone()[0]
                self.update_database_connections(active_connections)
            
            # Redis memory usage
            redis_info = cache.client.info()
            if 'used_memory' in redis_info:
                self.update_redis_memory_usage(redis_info['used_memory'])
            
            # Cache hit/miss ratio
            cache_stats = cache.client.info('stats')
            if 'keyspace_hits' in cache_stats and 'keyspace_misses' in cache_stats:
                hits = int(cache_stats['keyspace_hits'])
                misses = int(cache_stats['keyspace_misses'])
                # Note: This is a simplified approach. In production, you'd want to track this over time
                
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            self.record_error("system_metrics_collection", "monitoring")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics"""
        return {
            'uptime_seconds': time.time() - self.start_time,
            'total_api_requests': self.metrics.api_requests_total._value.sum(),
            'total_lead_captures': self.metrics.lead_capture_total._value.sum(),
            'total_salary_predictions': self.metrics.salary_predictions_total._value.sum(),
            'total_errors': self.metrics.errors_total._value.sum(),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'lead_conversion_rate': self._calculate_lead_conversion_rate(),
            'api_error_rate': self._calculate_api_error_rate()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        hits = self.metrics.redis_cache_hits_total._value.sum()
        misses = self.metrics.redis_cache_misses_total._value.sum()
        total = hits + misses
        return hits / total if total > 0 else 0.0
    
    def _calculate_lead_conversion_rate(self) -> float:
        """Calculate lead conversion rate"""
        attempts = self.metrics.lead_capture_attempts_total._value.sum()
        captures = self.metrics.lead_capture_total._value.sum()
        return captures / attempts if attempts > 0 else 0.0
    
    def _calculate_api_error_rate(self) -> float:
        """Calculate API error rate"""
        requests = self.metrics.api_requests_total._value.sum()
        errors = self.metrics.api_errors_total._value.sum()
        return errors / requests if requests > 0 else 0.0
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        return generate_latest(REGISTRY)


# Global monitoring service instance
monitoring_service = MonitoringService()


# Decorators for easy metric collection
def monitor_api_request(endpoint: str, method: str = "GET"):
    """Decorator to monitor API requests"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with monitoring_service.api_request_timer(endpoint, method):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def monitor_database_query(query_type: str):
    """Decorator to monitor database queries"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with monitoring_service.database_query_timer(query_type):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def monitor_celery_task(task_type: str):
    """Decorator to monitor Celery tasks"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                monitoring_service.record_celery_task(task_type, "started")
                result = func(*args, **kwargs)
                monitoring_service.record_celery_task(task_type, "completed")
                return result
            except Exception as e:
                monitoring_service.record_celery_task(task_type, "failed")
                monitoring_service.record_error(str(type(e).__name__), "celery")
                raise
        return wrapper
    return decorator


# Middleware for automatic request monitoring
class MonitoringMiddleware:
    """Django middleware for automatic request monitoring"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Record request start
        monitoring_service.record_api_request(
            endpoint=request.path,
            method=request.method,
            status=200,  # Will be updated after response
            duration=0
        )
        
        response = self.get_response(request)
        
        # Record request completion
        duration = time.time() - start_time
        monitoring_service.record_api_request(
            endpoint=request.path,
            method=request.method,
            status=response.status_code,
            duration=duration
        )
        
        return response 