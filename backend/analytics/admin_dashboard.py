#!/usr/bin/env python3
"""
Admin Dashboard for Job Recommendation Analytics

This module provides a comprehensive admin dashboard for real-time monitoring
and analysis of the job recommendation system, including system health,
user success metrics, recommendation effectiveness, and A/B test results.

Features:
- Real-time system health monitoring
- User success story tracking
- Recommendation quality reports
- Performance optimization insights
- A/B test monitoring and results
- Alert system for critical issues
- Export capabilities for reports
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DashboardMetrics:
    """Data class for dashboard metrics"""
    timestamp: datetime
    system_health: str
    active_users: int
    total_recommendations: int
    success_rate: float
    avg_response_time: float
    error_rate: float
    cpu_usage: float
    memory_usage: float

@dataclass
class Alert:
    """Data class for system alerts"""
    alert_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class AdminDashboard:
    """
    Comprehensive admin dashboard for job recommendation analytics.
    
    Provides real-time monitoring, system health tracking, user success
    metrics, and comprehensive reporting capabilities for administrators.
    """
    
    def __init__(self, db_path: str = "backend/analytics/recommendation_analytics.db"):
        """Initialize the admin dashboard"""
        self.db_path = db_path
        self._init_database()
        self._dashboard_cache = {}
        self._cache_ttl = 60  # 1 minute cache TTL
        self._last_cache_update = 0
        logger.info("AdminDashboard initialized successfully")
    
    def _init_database(self):
        """Initialize the analytics database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Read and execute the schema
            with open('backend/analytics/recommendation_analytics_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            cursor.executescript(schema_sql)
            conn.commit()
            conn.close()
            logger.info("Admin dashboard database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing admin dashboard database: {e}")
            raise
    
    def get_dashboard_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard overview
        
        Returns:
            Dict containing dashboard overview metrics
        """
        try:
            # Check cache first
            current_time = time.time()
            if (current_time - self._last_cache_update) < self._cache_ttl and 'overview' in self._dashboard_cache:
                return self._dashboard_cache['overview']
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # System health metrics
            health_metrics = self._get_system_health_metrics(cursor)
            
            # User metrics
            user_metrics = self._get_user_metrics(cursor)
            
            # Recommendation metrics
            recommendation_metrics = self._get_recommendation_metrics(cursor)
            
            # Performance metrics
            performance_metrics = self._get_performance_metrics(cursor)
            
            # Recent activity
            recent_activity = self._get_recent_activity(cursor)
            
            # Active alerts
            active_alerts = self._get_active_alerts(cursor)
            
            conn.close()
            
            overview = {
                'timestamp': datetime.now().isoformat(),
                'system_health': health_metrics,
                'user_metrics': user_metrics,
                'recommendation_metrics': recommendation_metrics,
                'performance_metrics': performance_metrics,
                'recent_activity': recent_activity,
                'active_alerts': active_alerts
            }
            
            # Update cache
            self._dashboard_cache['overview'] = overview
            self._last_cache_update = current_time
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            return {'error': str(e)}
    
    def _get_system_health_metrics(self, cursor) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            # Get recent system resources
            cursor.execute('''
                SELECT 
                    cpu_usage, memory_usage, error_rate, response_time_avg
                FROM system_resources 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            
            resource_data = cursor.fetchone()
            
            # Get recent API performance
            cursor.execute('''
                SELECT 
                    AVG(response_time) as avg_response_time,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) * 100.0 / COUNT(*) as error_rate
                FROM api_performance 
                WHERE timestamp >= datetime('now', '-1 hour')
            ''')
            
            api_data = cursor.fetchone()
            
            # Determine overall health
            cpu_usage = resource_data[0] if resource_data else 0
            memory_usage = resource_data[1] if resource_data else 0
            error_rate = api_data[1] if api_data and api_data[1] else 0
            response_time = api_data[0] if api_data and api_data[0] else 0
            
            if cpu_usage > 90 or memory_usage > 95 or error_rate > 10:
                health_status = "critical"
            elif cpu_usage > 80 or memory_usage > 85 or error_rate > 5:
                health_status = "warning"
            elif cpu_usage > 70 or memory_usage > 75 or error_rate > 2:
                health_status = "degraded"
            else:
                health_status = "healthy"
            
            return {
                'status': health_status,
                'cpu_usage': round(cpu_usage, 2),
                'memory_usage': round(memory_usage, 2),
                'error_rate': round(error_rate, 2),
                'avg_response_time': round(response_time, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting system health metrics: {e}")
            return {'status': 'unknown', 'cpu_usage': 0, 'memory_usage': 0, 'error_rate': 0, 'avg_response_time': 0}
    
    def _get_user_metrics(self, cursor) -> Dict[str, Any]:
        """Get user-related metrics"""
        try:
            # Active users (last 24 hours)
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) as active_users
                FROM user_sessions 
                WHERE session_start >= datetime('now', '-24 hours')
            ''')
            
            active_users = cursor.fetchone()[0] or 0
            
            # New users (last 24 hours)
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) as new_users
                FROM user_sessions 
                WHERE session_start >= datetime('now', '-24 hours')
                AND user_id NOT IN (
                    SELECT DISTINCT user_id FROM user_sessions 
                    WHERE session_start < datetime('now', '-24 hours')
                )
            ''')
            
            new_users = cursor.fetchone()[0] or 0
            
            # Total users
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) as total_users
                FROM user_sessions
            ''')
            
            total_users = cursor.fetchone()[0] or 0
            
            # User engagement score
            cursor.execute('''
                SELECT AVG(engagement_score) as avg_engagement
                FROM user_retention
            ''')
            
            avg_engagement = cursor.fetchone()[0] or 0
            
            return {
                'active_users_24h': active_users,
                'new_users_24h': new_users,
                'total_users': total_users,
                'avg_engagement_score': round(avg_engagement, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting user metrics: {e}")
            return {'active_users_24h': 0, 'new_users_24h': 0, 'total_users': 0, 'avg_engagement_score': 0}
    
    def _get_recommendation_metrics(self, cursor) -> Dict[str, Any]:
        """Get recommendation-related metrics"""
        try:
            # Recommendations generated (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) as recommendations_24h
                FROM job_recommendations 
                WHERE created_at >= datetime('now', '-24 hours')
            ''')
            
            recommendations_24h = cursor.fetchone()[0] or 0
            
            # Total recommendations
            cursor.execute('''
                SELECT COUNT(*) as total_recommendations
                FROM job_recommendations
            ''')
            
            total_recommendations = cursor.fetchone()[0] or 0
            
            # Success rate (applications to offers)
            cursor.execute('''
                SELECT 
                    COUNT(ao.application_id) as total_applications,
                    COUNT(CASE WHEN ao.application_status = 'offer_accepted' THEN 1 END) as successful_applications
                FROM application_outcomes ao
                WHERE ao.application_date >= datetime('now', '-30 days')
            ''')
            
            app_data = cursor.fetchone()
            total_applications = app_data[0] or 0
            successful_applications = app_data[1] or 0
            success_rate = (successful_applications / total_applications * 100) if total_applications > 0 else 0
            
            # Average recommendation score
            cursor.execute('''
                SELECT AVG(recommendation_score) as avg_score
                FROM job_recommendations 
                WHERE created_at >= datetime('now', '-7 days')
            ''')
            
            avg_score = cursor.fetchone()[0] or 0
            
            return {
                'recommendations_24h': recommendations_24h,
                'total_recommendations': total_recommendations,
                'success_rate': round(success_rate, 2),
                'avg_recommendation_score': round(avg_score, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendation metrics: {e}")
            return {'recommendations_24h': 0, 'total_recommendations': 0, 'success_rate': 0, 'avg_recommendation_score': 0}
    
    def _get_performance_metrics(self, cursor) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            # API performance (last hour)
            cursor.execute('''
                SELECT 
                    AVG(response_time) as avg_response_time,
                    MAX(response_time) as max_response_time,
                    COUNT(*) as total_requests
                FROM api_performance 
                WHERE timestamp >= datetime('now', '-1 hour')
            ''')
            
            api_data = cursor.fetchone()
            
            # Processing time metrics
            cursor.execute('''
                SELECT 
                    process_name,
                    AVG(duration) as avg_duration,
                    COUNT(*) as total_processes
                FROM processing_metrics 
                WHERE start_time >= datetime('now', '-24 hours')
                GROUP BY process_name
                ORDER BY avg_duration DESC
            ''')
            
            processing_data = cursor.fetchall()
            
            return {
                'avg_response_time': round(api_data[0] or 0, 2),
                'max_response_time': round(api_data[1] or 0, 2),
                'total_requests_1h': api_data[2] or 0,
                'processing_metrics': [
                    {
                        'process_name': row[0],
                        'avg_duration': round(row[1], 2),
                        'total_processes': row[2]
                    }
                    for row in processing_data
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'avg_response_time': 0, 'max_response_time': 0, 'total_requests_1h': 0, 'processing_metrics': []}
    
    def _get_recent_activity(self, cursor) -> List[Dict[str, Any]]:
        """Get recent system activity"""
        try:
            activities = []
            
            # Recent user sessions
            cursor.execute('''
                SELECT 
                    user_id, session_start, device_type, session_duration
                FROM user_sessions 
                ORDER BY session_start DESC 
                LIMIT 5
            ''')
            
            for row in cursor.fetchall():
                activities.append({
                    'type': 'user_session',
                    'user_id': row[0],
                    'timestamp': row[1],
                    'description': f"User session on {row[2]} ({row[3]}s)",
                    'icon': 'user'
                })
            
            # Recent recommendations
            cursor.execute('''
                SELECT 
                    user_id, tier, recommendation_score, created_at
                FROM job_recommendations 
                ORDER BY created_at DESC 
                LIMIT 5
            ''')
            
            for row in cursor.fetchall():
                activities.append({
                    'type': 'recommendation',
                    'user_id': row[0],
                    'timestamp': row[3],
                    'description': f"{row[1].title()} tier recommendation (score: {row[2]:.1f})",
                    'icon': 'recommendation'
                })
            
            # Recent applications
            cursor.execute('''
                SELECT 
                    user_id, application_status, application_date
                FROM application_outcomes 
                ORDER BY application_date DESC 
                LIMIT 5
            ''')
            
            for row in cursor.fetchall():
                activities.append({
                    'type': 'application',
                    'user_id': row[0],
                    'timestamp': row[2],
                    'description': f"Application status: {row[1].replace('_', ' ').title()}",
                    'icon': 'application'
                })
            
            # Sort by timestamp and return most recent
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            return activities[:10]
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
    
    def _get_active_alerts(self, cursor) -> List[Dict[str, Any]]:
        """Get active system alerts"""
        try:
            cursor.execute('''
                SELECT 
                    alert_id, alert_name, severity, triggered_at, metric_value, threshold_value
                FROM alert_history ah
                JOIN alert_definitions ad ON ah.alert_id = ad.alert_id
                WHERE ah.resolved_at IS NULL
                ORDER BY ah.triggered_at DESC
                LIMIT 10
            ''')
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'alert_id': row[0],
                    'alert_name': row[1],
                    'severity': row[2],
                    'triggered_at': row[3],
                    'current_value': row[4],
                    'threshold_value': row[5],
                    'message': f"{row[1]}: {row[4]} (threshold: {row[5]})"
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def get_user_success_stories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user success stories for the dashboard
        
        Args:
            limit: Maximum number of stories to return
            
        Returns:
            List of success stories
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    ur.user_id,
                    ur.successful_outcomes,
                    ur.satisfaction_avg,
                    ur.engagement_score,
                    it.current_salary,
                    it.salary_increase,
                    it.increase_percentage,
                    ca.advancement_type,
                    ca.new_role,
                    ca.salary_change
                FROM user_retention ur
                LEFT JOIN (
                    SELECT user_id, current_salary, salary_increase, increase_percentage,
                           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY tracking_date DESC) as rn
                    FROM income_tracking
                ) it ON ur.user_id = it.user_id AND it.rn = 1
                LEFT JOIN (
                    SELECT user_id, advancement_type, new_role, salary_change,
                           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY advancement_date DESC) as rn
                    FROM career_advancement
                ) ca ON ur.user_id = ca.user_id AND ca.rn = 1
                WHERE ur.successful_outcomes > 0
                ORDER BY ur.successful_outcomes DESC, it.increase_percentage DESC
                LIMIT ?
            ''', (limit,))
            
            success_stories = []
            for row in cursor.fetchall():
                user_id, successful_outcomes, satisfaction_avg, engagement_score, current_salary, salary_increase, increase_percentage, advancement_type, new_role, salary_change = row
                
                story = {
                    'user_id': user_id,
                    'successful_outcomes': successful_outcomes,
                    'satisfaction_avg': round(satisfaction_avg or 0, 2),
                    'engagement_score': round(engagement_score or 0, 2),
                    'current_salary': current_salary or 0,
                    'salary_increase': salary_increase or 0,
                    'increase_percentage': round(increase_percentage or 0, 2),
                    'advancement_type': advancement_type,
                    'new_role': new_role,
                    'salary_change': salary_change or 0
                }
                
                # Generate success story description
                story['description'] = self._generate_success_story_description(story)
                success_stories.append(story)
            
            conn.close()
            return success_stories
            
        except Exception as e:
            logger.error(f"Error getting user success stories: {e}")
            return []
    
    def _generate_success_story_description(self, story: Dict[str, Any]) -> str:
        """Generate a human-readable success story description"""
        parts = []
        
        if story['successful_outcomes'] > 0:
            parts.append(f"achieved {story['successful_outcomes']} successful job outcomes")
        
        if story['increase_percentage'] > 0:
            parts.append(f"increased salary by {story['increase_percentage']:.1f}%")
        
        if story['advancement_type'] and story['new_role']:
            parts.append(f"advanced to {story['new_role']}")
        
        if story['satisfaction_avg'] > 0:
            parts.append(f"rated satisfaction {story['satisfaction_avg']:.1f}/5")
        
        if parts:
            return "User " + ", ".join(parts) + "."
        else:
            return "User achieved career success through our recommendations."
    
    def get_recommendation_quality_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive recommendation quality report
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing quality report
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Quality metrics by tier
            cursor.execute('''
                SELECT 
                    tier,
                    COUNT(*) as total_recommendations,
                    AVG(recommendation_score) as avg_score,
                    COUNT(CASE WHEN recommendation_score >= 8.0 THEN 1 END) as high_quality,
                    COUNT(CASE WHEN recommendation_score < 5.0 THEN 1 END) as low_quality,
                    AVG(salary_increase_potential) as avg_salary_potential,
                    AVG(success_probability) as avg_success_probability
                FROM job_recommendations 
                WHERE created_at >= ?
                GROUP BY tier
                ORDER BY tier
            ''', (start_date,))
            
            tier_quality = {}
            for row in cursor.fetchall():
                tier, total, avg_score, high_quality, low_quality, avg_salary_potential, avg_success_probability = row
                
                tier_quality[tier] = {
                    'total_recommendations': total,
                    'avg_score': round(avg_score, 2),
                    'high_quality_count': high_quality,
                    'high_quality_percentage': round((high_quality / total * 100) if total > 0 else 0, 2),
                    'low_quality_count': low_quality,
                    'low_quality_percentage': round((low_quality / total * 100) if total > 0 else 0, 2),
                    'avg_salary_potential': round(avg_salary_potential, 2),
                    'avg_success_probability': round(avg_success_probability, 2)
                }
            
            # Engagement correlation
            cursor.execute('''
                SELECT 
                    jr.recommendation_score,
                    COUNT(re.recommendation_id) as engagement_count,
                    COUNT(ao.application_id) as application_count
                FROM job_recommendations jr
                LEFT JOIN recommendation_engagement re ON jr.recommendation_id = re.recommendation_id
                LEFT JOIN application_outcomes ao ON jr.recommendation_id = ao.recommendation_id
                WHERE jr.created_at >= ?
                GROUP BY jr.recommendation_id
            ''', (start_date,))
            
            score_engagement_data = cursor.fetchall()
            
            # Calculate correlation
            scores = [row[0] for row in score_engagement_data]
            engagements = [row[1] for row in score_engagement_data]
            applications = [row[2] for row in score_engagement_data]
            
            score_engagement_correlation = self._calculate_correlation(scores, engagements)
            score_application_correlation = self._calculate_correlation(scores, applications)
            
            conn.close()
            
            return {
                'analysis_period_days': days,
                'tier_quality': tier_quality,
                'correlation_metrics': {
                    'score_engagement_correlation': round(score_engagement_correlation, 3),
                    'score_application_correlation': round(score_application_correlation, 3)
                },
                'overall_quality_score': self._calculate_overall_quality_score(tier_quality)
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendation quality report: {e}")
            return {'error': str(e)}
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        try:
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            sum_y2 = sum(y[i] ** 2 for i in range(n))
            
            numerator = n * sum_xy - sum_x * sum_y
            denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
            
            if denominator == 0:
                return 0.0
            
            return numerator / denominator
            
        except Exception:
            return 0.0
    
    def _calculate_overall_quality_score(self, tier_quality: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        if not tier_quality:
            return 0.0
        
        total_recommendations = sum(tier['total_recommendations'] for tier in tier_quality.values())
        if total_recommendations == 0:
            return 0.0
        
        weighted_score = 0
        for tier_data in tier_quality.values():
            weight = tier_data['total_recommendations'] / total_recommendations
            weighted_score += tier_data['avg_score'] * weight
        
        return round(weighted_score, 2)
    
    def get_ab_test_dashboard(self) -> Dict[str, Any]:
        """Get A/B test dashboard data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Active tests
            cursor.execute('''
                SELECT 
                    t.test_id, t.test_name, t.target_metric, t.start_date,
                    COUNT(a.user_id) as assigned_users,
                    COUNT(DISTINCT v.variant_id) as variant_count
                FROM ab_tests t
                LEFT JOIN ab_test_assignments a ON t.test_id = a.test_id
                LEFT JOIN ab_test_variants v ON t.test_id = v.test_id
                WHERE t.status = 'active'
                GROUP BY t.test_id
                ORDER BY t.start_date DESC
            ''')
            
            active_tests = []
            for row in cursor.fetchall():
                active_tests.append({
                    'test_id': row[0],
                    'test_name': row[1],
                    'target_metric': row[2],
                    'start_date': row[3],
                    'assigned_users': row[4],
                    'variant_count': row[5]
                })
            
            # Recent test results
            cursor.execute('''
                SELECT 
                    t.test_id, t.test_name, t.status, t.end_date,
                    COUNT(a.user_id) as total_users
                FROM ab_tests t
                LEFT JOIN ab_test_assignments a ON t.test_id = a.test_id
                WHERE t.status IN ('completed', 'cancelled')
                GROUP BY t.test_id
                ORDER BY t.end_date DESC
                LIMIT 5
            ''')
            
            recent_tests = []
            for row in cursor.fetchall():
                recent_tests.append({
                    'test_id': row[0],
                    'test_name': row[1],
                    'status': row[2],
                    'end_date': row[3],
                    'total_users': row[4]
                })
            
            conn.close()
            
            return {
                'active_tests': active_tests,
                'recent_tests': recent_tests,
                'total_active_tests': len(active_tests)
            }
            
        except Exception as e:
            logger.error(f"Error getting A/B test dashboard: {e}")
            return {'active_tests': [], 'recent_tests': [], 'total_active_tests': 0}
    
    def export_analytics_data(
        self,
        data_type: str,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export analytics data for external analysis
        
        Args:
            data_type: Type of data to export
            start_date: Start date for export
            end_date: End date for export
            format: Export format (json, csv)
            
        Returns:
            Dict containing exported data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if data_type == "user_behavior":
                cursor.execute('''
                    SELECT * FROM user_sessions 
                    WHERE session_start >= ? AND session_start <= ?
                    ORDER BY session_start DESC
                ''', (start_date, end_date))
                
                data = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
            elif data_type == "recommendations":
                cursor.execute('''
                    SELECT * FROM job_recommendations 
                    WHERE created_at >= ? AND created_at <= ?
                    ORDER BY created_at DESC
                ''', (start_date, end_date))
                
                data = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
            elif data_type == "performance":
                cursor.execute('''
                    SELECT * FROM api_performance 
                    WHERE timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp DESC
                ''', (start_date, end_date))
                
                data = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
            else:
                return {'error': 'Invalid data type'}
            
            conn.close()
            
            # Convert to requested format
            if format == "json":
                export_data = [
                    dict(zip(columns, row)) for row in data
                ]
            else:  # CSV
                export_data = {
                    'columns': columns,
                    'rows': data
                }
            
            return {
                'data_type': data_type,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'format': format,
                'record_count': len(data),
                'data': export_data
            }
            
        except Exception as e:
            logger.error(f"Error exporting analytics data: {e}")
            return {'error': str(e)}
    
    def clear_cache(self):
        """Clear dashboard cache"""
        self._dashboard_cache = {}
        self._last_cache_update = 0
        logger.info("Dashboard cache cleared")
