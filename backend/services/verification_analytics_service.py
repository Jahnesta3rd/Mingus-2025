"""
Verification Analytics Service
Tracks and analyzes phone verification patterns for insights and optimization
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import json

class VerificationAnalyticsService:
    """Service for tracking and analyzing verification patterns"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def track_event(self, user_id: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Track a verification event
        
        Args:
            user_id: User ID
            event_type: Type of event (send_code, verify_success, verify_failed, change_phone, resend_request)
            event_data: Event-specific data
            
        Returns:
            bool: Success status
        """
        try:
            query = text("""
                INSERT INTO verification_analytics 
                (user_id, event_type, event_data, created_at)
                VALUES (:user_id, :event_type, :event_data, NOW())
            """)
            
            self.db_session.execute(query, {
                'user_id': user_id,
                'event_type': event_type,
                'event_data': json.dumps(event_data)
            })
            self.db_session.commit()
            
            logger.info(f"Tracked verification event: {event_type} for user {user_id}")
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to track verification event: {str(e)}")
            return False
    
    def get_user_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics for a specific user
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            Dict with user analytics
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get event counts by type
            event_counts_query = text("""
                SELECT event_type, COUNT(*) as count
                FROM verification_analytics 
                WHERE user_id = :user_id AND created_at >= :since_date
                GROUP BY event_type
            """)
            
            event_counts = self.db_session.execute(event_counts_query, {
                'user_id': user_id,
                'since_date': since_date
            }).fetchall()
            
            # Get resend patterns
            resend_patterns_query = text("""
                SELECT 
                    phone_number,
                    MAX(resend_count) as max_resends,
                    AVG(resend_count) as avg_resends,
                    COUNT(*) as total_attempts,
                    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_verifications
                FROM phone_verification 
                WHERE user_id = :user_id AND created_at >= :since_date
                GROUP BY phone_number
            """)
            
            resend_patterns = self.db_session.execute(resend_patterns_query, {
                'user_id': user_id,
                'since_date': since_date
            }).fetchall()
            
            # Get recent events
            recent_events_query = text("""
                SELECT event_type, event_data, created_at
                FROM verification_analytics 
                WHERE user_id = :user_id AND created_at >= :since_date
                ORDER BY created_at DESC 
                LIMIT 20
            """)
            
            recent_events = self.db_session.execute(recent_events_query, {
                'user_id': user_id,
                'since_date': since_date
            }).fetchall()
            
            return {
                'user_id': user_id,
                'period_days': days,
                'event_counts': {row.event_type: row.count for row in event_counts},
                'resend_patterns': [
                    {
                        'phone_number': row.phone_number,
                        'max_resends': row.max_resends,
                        'avg_resends': float(row.avg_resends) if row.avg_resends else 0,
                        'total_attempts': row.total_attempts,
                        'successful_verifications': row.successful_verifications
                    }
                    for row in resend_patterns
                ],
                'recent_events': [
                    {
                        'event_type': row.event_type,
                        'event_data': json.loads(row.event_data) if row.event_data else {},
                        'created_at': row.created_at.isoformat()
                    }
                    for row in recent_events
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            return {}
    
    def get_global_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get global analytics across all users
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict with global analytics
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Overall statistics
            overall_stats_query = text("""
                SELECT 
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(*) as total_events,
                    COUNT(CASE WHEN event_type = 'send_code' THEN 1 END) as total_sends,
                    COUNT(CASE WHEN event_type = 'verify_success' THEN 1 END) as total_successes,
                    COUNT(CASE WHEN event_type = 'verify_failed' THEN 1 END) as total_failures,
                    COUNT(CASE WHEN event_type = 'change_phone' THEN 1 END) as total_phone_changes
                FROM verification_analytics 
                WHERE created_at >= :since_date
            """)
            
            overall_stats = self.db_session.execute(overall_stats_query, {
                'since_date': since_date
            }).fetchone()
            
            # Daily trends
            daily_trends_query = text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total_events,
                    COUNT(CASE WHEN event_type = 'send_code' THEN 1 END) as sends,
                    COUNT(CASE WHEN event_type = 'verify_success' THEN 1 END) as successes,
                    COUNT(CASE WHEN event_type = 'verify_failed' THEN 1 END) as failures
                FROM verification_analytics 
                WHERE created_at >= :since_date
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            daily_trends = self.db_session.execute(daily_trends_query, {
                'since_date': since_date
            }).fetchall()
            
            # Resend pattern analysis
            resend_analysis_query = text("""
                SELECT 
                    resend_count,
                    COUNT(*) as frequency,
                    AVG(attempts) as avg_attempts,
                    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_count
                FROM phone_verification 
                WHERE created_at >= :since_date
                GROUP BY resend_count
                ORDER BY resend_count
            """)
            
            resend_analysis = self.db_session.execute(resend_analysis_query, {
                'since_date': since_date
            }).fetchall()
            
            # Phone number patterns
            phone_patterns_query = text("""
                SELECT 
                    phone_number,
                    COUNT(*) as verification_attempts,
                    MAX(resend_count) as max_resends,
                    AVG(resend_count) as avg_resends,
                    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_verifications
                FROM phone_verification 
                WHERE created_at >= :since_date
                GROUP BY phone_number
                HAVING COUNT(*) > 1
                ORDER BY verification_attempts DESC
                LIMIT 20
            """)
            
            phone_patterns = self.db_session.execute(phone_patterns_query, {
                'since_date': since_date
            }).fetchall()
            
            return {
                'period_days': days,
                'overall_stats': {
                    'unique_users': overall_stats.unique_users,
                    'total_events': overall_stats.total_events,
                    'total_sends': overall_stats.total_sends,
                    'total_successes': overall_stats.total_successes,
                    'total_failures': overall_stats.total_failures,
                    'total_phone_changes': overall_stats.total_phone_changes,
                    'success_rate': (overall_stats.total_successes / overall_stats.total_sends * 100) if overall_stats.total_sends > 0 else 0
                },
                'daily_trends': [
                    {
                        'date': row.date.isoformat(),
                        'total_events': row.total_events,
                        'sends': row.sends,
                        'successes': row.successes,
                        'failures': row.failures
                    }
                    for row in daily_trends
                ],
                'resend_analysis': [
                    {
                        'resend_count': row.resend_count,
                        'frequency': row.frequency,
                        'avg_attempts': float(row.avg_attempts) if row.avg_attempts else 0,
                        'successful_count': row.successful_count,
                        'success_rate': (row.successful_count / row.frequency * 100) if row.frequency > 0 else 0
                    }
                    for row in resend_analysis
                ],
                'phone_patterns': [
                    {
                        'phone_number': row.phone_number,
                        'verification_attempts': row.verification_attempts,
                        'max_resends': row.max_resends,
                        'avg_resends': float(row.avg_resends) if row.avg_resends else 0,
                        'successful_verifications': row.successful_verifications
                    }
                    for row in phone_patterns
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting global analytics: {str(e)}")
            return {}
    
    def get_resend_insights(self, days: int = 30) -> Dict[str, Any]:
        """
        Get insights about resend patterns and optimization opportunities
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with resend insights
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Resend delay effectiveness
            delay_effectiveness_query = text("""
                SELECT 
                    CASE 
                        WHEN resend_count = 1 THEN '60s'
                        WHEN resend_count = 2 THEN '120s'
                        WHEN resend_count >= 3 THEN '300s+'
                    END as delay_category,
                    COUNT(*) as total_attempts,
                    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_verifications,
                    AVG(attempts) as avg_attempts_needed
                FROM phone_verification 
                WHERE created_at >= :since_date AND resend_count > 0
                GROUP BY 
                    CASE 
                        WHEN resend_count = 1 THEN '60s'
                        WHEN resend_count = 2 THEN '120s'
                        WHEN resend_count >= 3 THEN '300s+'
                    END
                ORDER BY delay_category
            """)
            
            delay_effectiveness = self.db_session.execute(delay_effectiveness_query, {
                'since_date': since_date
            }).fetchall()
            
            # User behavior patterns
            user_behavior_query = text("""
                SELECT 
                    user_id,
                    COUNT(*) as total_verifications,
                    MAX(resend_count) as max_resends_used,
                    AVG(resend_count) as avg_resends_per_verification,
                    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_verifications,
                    COUNT(DISTINCT phone_number) as unique_phone_numbers
                FROM phone_verification 
                WHERE created_at >= :since_date
                GROUP BY user_id
                HAVING COUNT(*) > 1
                ORDER BY total_verifications DESC
                LIMIT 50
            """)
            
            user_behavior = self.db_session.execute(user_behavior_query, {
                'since_date': since_date
            }).fetchall()
            
            # Time-based patterns
            time_patterns_query = text("""
                SELECT 
                    EXTRACT(HOUR FROM created_at) as hour_of_day,
                    COUNT(*) as total_verifications,
                    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_verifications,
                    AVG(resend_count) as avg_resends
                FROM phone_verification 
                WHERE created_at >= :since_date
                GROUP BY EXTRACT(HOUR FROM created_at)
                ORDER BY hour_of_day
            """)
            
            time_patterns = self.db_session.execute(time_patterns_query, {
                'since_date': since_date
            }).fetchall()
            
            return {
                'period_days': days,
                'delay_effectiveness': [
                    {
                        'delay_category': row.delay_category,
                        'total_attempts': row.total_attempts,
                        'successful_verifications': row.successful_verifications,
                        'success_rate': (row.successful_verifications / row.total_attempts * 100) if row.total_attempts > 0 else 0,
                        'avg_attempts_needed': float(row.avg_attempts_needed) if row.avg_attempts_needed else 0
                    }
                    for row in delay_effectiveness
                ],
                'user_behavior': [
                    {
                        'user_id': row.user_id,
                        'total_verifications': row.total_verifications,
                        'max_resends_used': row.max_resends_used,
                        'avg_resends_per_verification': float(row.avg_resends_per_verification) if row.avg_resends_per_verification else 0,
                        'successful_verifications': row.successful_verifications,
                        'unique_phone_numbers': row.unique_phone_numbers
                    }
                    for row in user_behavior
                ],
                'time_patterns': [
                    {
                        'hour_of_day': int(row.hour_of_day),
                        'total_verifications': row.total_verifications,
                        'successful_verifications': row.successful_verifications,
                        'success_rate': (row.successful_verifications / row.total_verifications * 100) if row.total_verifications > 0 else 0,
                        'avg_resends': float(row.avg_resends) if row.avg_resends else 0
                    }
                    for row in time_patterns
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting resend insights: {str(e)}")
            return {}
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get recommendations for optimizing the verification process
        
        Returns:
            List of optimization recommendations
        """
        try:
            recommendations = []
            
            # Analyze success rates by resend count
            success_rate_query = text("""
                SELECT 
                    resend_count,
                    COUNT(*) as total_attempts,
                    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_verifications,
                    (COUNT(CASE WHEN status = 'verified' THEN 1 END) * 100.0 / COUNT(*)) as success_rate
                FROM phone_verification 
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY resend_count
                ORDER BY resend_count
            """)
            
            success_rates = self.db_session.execute(success_rate_query).fetchall()
            
            # Check if 60s delay is too short
            if success_rates and len(success_rates) > 1:
                first_resend_success = success_rates[1].success_rate if len(success_rates) > 1 else 0
                if first_resend_success < 70:  # Less than 70% success rate
                    recommendations.append({
                        'type': 'delay_optimization',
                        'priority': 'high',
                        'title': 'Consider Increasing Initial Resend Delay',
                        'description': f'First resend success rate is {first_resend_success:.1f}%. Consider increasing the 60s delay to 90s or 120s.',
                        'impact': 'medium',
                        'implementation': 'Update resend_delays configuration in VerificationService'
                    })
            
            # Check for high resend usage
            high_resend_query = text("""
                SELECT COUNT(*) as high_resend_users
                FROM (
                    SELECT user_id, MAX(resend_count) as max_resends
                    FROM phone_verification 
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY user_id
                    HAVING MAX(resend_count) >= 3
                ) as high_resend
            """)
            
            high_resend_result = self.db_session.execute(high_resend_query).fetchone()
            if high_resend_result and high_resend_result.high_resend_users > 10:
                recommendations.append({
                    'type': 'user_experience',
                    'priority': 'medium',
                    'title': 'High Resend Usage Detected',
                    'description': f'{high_resend_result.high_resend_users} users are hitting the maximum resend limit. Consider offering alternative verification methods earlier.',
                    'impact': 'high',
                    'implementation': 'Show alternative contact options after 2 resends instead of 3'
                })
            
            # Check for time-based patterns
            time_pattern_query = text("""
                SELECT 
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as attempts,
                    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successes
                FROM phone_verification 
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY EXTRACT(HOUR FROM created_at)
                HAVING COUNT(*) > 100
                ORDER BY (COUNT(CASE WHEN status = 'verified' THEN 1 END) * 100.0 / COUNT(*)) ASC
                LIMIT 3
            """)
            
            low_success_hours = self.db_session.execute(time_pattern_query).fetchall()
            if low_success_hours:
                hours = [int(row.hour) for row in low_success_hours]
                recommendations.append({
                    'type': 'timing_optimization',
                    'priority': 'low',
                    'title': 'Low Success Rate During Certain Hours',
                    'description': f'Lower verification success rates observed during hours {hours}. Consider adjusting delays during these periods.',
                    'impact': 'low',
                    'implementation': 'Implement time-based delay adjustments'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting optimization recommendations: {str(e)}")
            return []
    
    def cleanup_old_analytics(self, days: int = 90) -> int:
        """
        Clean up old analytics data
        
        Args:
            days: Keep data newer than this many days
            
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            delete_query = text("""
                DELETE FROM verification_analytics 
                WHERE created_at < :cutoff_date
            """)
            
            result = self.db_session.execute(delete_query, {
                'cutoff_date': cutoff_date
            })
            
            self.db_session.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Cleaned up {deleted_count} old analytics records")
            
            return deleted_count
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error cleaning up old analytics: {str(e)}")
            return 0 