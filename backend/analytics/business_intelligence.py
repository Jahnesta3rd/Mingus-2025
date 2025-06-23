"""
Business Intelligence System
Tracks user adoption, engagement, feature usage, score accuracy, and ROI analysis
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from loguru import logger
import pandas as pd
import numpy as np
from scipy import stats

@dataclass
class UserMetric:
    """User-related metric"""
    user_id: str
    metric_type: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureUsage:
    """Feature usage tracking"""
    user_id: str
    feature_name: str
    usage_count: int
    total_time: float
    first_used: datetime
    last_used: datetime
    satisfaction_score: Optional[float] = None

@dataclass
class FunnelStep:
    """Funnel analysis step"""
    step_name: str
    user_count: int
    conversion_rate: float
    dropoff_rate: float
    avg_time_in_step: float

class BusinessIntelligence:
    """Main business intelligence class"""
    
    def __init__(self, db_path: str = "business_intelligence.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize business intelligence database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # User adoption and engagement
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        metric_type TEXT NOT NULL,
                        value REAL NOT NULL,
                        timestamp DATETIME NOT NULL,
                        metadata TEXT
                    )
                """)
                
                # Feature usage tracking
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS feature_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        feature_name TEXT NOT NULL,
                        usage_count INTEGER DEFAULT 1,
                        total_time REAL DEFAULT 0,
                        first_used DATETIME NOT NULL,
                        last_used DATETIME NOT NULL,
                        satisfaction_score REAL
                    )
                """)
                
                # User satisfaction and feedback
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        feedback_type TEXT NOT NULL,
                        rating INTEGER,
                        comment TEXT,
                        timestamp DATETIME NOT NULL,
                        feature_name TEXT
                    )
                """)
                
                # Score accuracy tracking
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS score_accuracy (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        score_type TEXT NOT NULL,
                        predicted_score REAL NOT NULL,
                        actual_outcome TEXT,
                        accuracy_rating REAL,
                        timestamp DATETIME NOT NULL
                    )
                """)
                
                # ROI analysis
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS roi_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data_source TEXT NOT NULL,
                        cost REAL NOT NULL,
                        value_generated REAL NOT NULL,
                        user_count INTEGER NOT NULL,
                        timestamp DATETIME NOT NULL
                    )
                """)
                
                # User journey tracking
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_journey (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        step_name TEXT NOT NULL,
                        step_order INTEGER NOT NULL,
                        time_spent REAL,
                        timestamp DATETIME NOT NULL
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_metrics_user ON user_metrics(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_metrics_type ON user_metrics(metric_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_feature_usage_user ON feature_usage(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_feedback_user ON user_feedback(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_score_accuracy_user ON score_accuracy(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_journey_user ON user_journey(user_id)")
                
        except Exception as e:
            logger.error(f"Failed to initialize business intelligence database: {e}")
    
    def track_user_metric(self, user_id: str, metric_type: str, value: float, 
                         metadata: Dict[str, Any] = None):
        """Track a user metric"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO user_metrics (user_id, metric_type, value, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, metric_type, value, datetime.now(), 
                     json.dumps(metadata) if metadata else None))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track user metric: {e}")
    
    def track_feature_usage(self, user_id: str, feature_name: str, usage_time: float = 0.0,
                           satisfaction_score: Optional[float] = None):
        """Track feature usage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if user has used this feature before
                cursor = conn.execute("""
                    SELECT usage_count, total_time, first_used, last_used
                    FROM feature_usage 
                    WHERE user_id = ? AND feature_name = ?
                """, (user_id, feature_name))
                
                existing = cursor.fetchone()
                now = datetime.now()
                
                if existing:
                    # Update existing record
                    new_count = existing[0] + 1
                    new_time = existing[1] + usage_time
                    new_satisfaction = satisfaction_score if satisfaction_score else existing[3]
                    
                    conn.execute("""
                        UPDATE feature_usage 
                        SET usage_count = ?, total_time = ?, last_used = ?, 
                            satisfaction_score = ?
                        WHERE user_id = ? AND feature_name = ?
                    """, (new_count, new_time, now, new_satisfaction, user_id, feature_name))
                else:
                    # Create new record
                    conn.execute("""
                        INSERT INTO feature_usage 
                        (user_id, feature_name, usage_count, total_time, first_used, last_used, satisfaction_score)
                        VALUES (?, ?, 1, ?, ?, ?, ?)
                    """, (user_id, feature_name, usage_time, now, now, satisfaction_score))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track feature usage: {e}")
    
    def track_user_feedback(self, user_id: str, feedback_type: str, rating: Optional[int] = None,
                           comment: Optional[str] = None, feature_name: Optional[str] = None):
        """Track user feedback and satisfaction"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO user_feedback 
                    (user_id, feedback_type, rating, comment, timestamp, feature_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, feedback_type, rating, comment, datetime.now(), feature_name))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track user feedback: {e}")
    
    def track_score_accuracy(self, user_id: str, score_type: str, predicted_score: float,
                           actual_outcome: Optional[str] = None, accuracy_rating: Optional[float] = None):
        """Track score prediction accuracy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO score_accuracy 
                    (user_id, score_type, predicted_score, actual_outcome, accuracy_rating, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, score_type, predicted_score, actual_outcome, accuracy_rating, datetime.now()))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track score accuracy: {e}")
    
    def track_roi_metric(self, data_source: str, cost: float, value_generated: float, user_count: int):
        """Track ROI metrics for data sources"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO roi_metrics 
                    (data_source, cost, value_generated, user_count, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (data_source, cost, value_generated, user_count, datetime.now()))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track ROI metric: {e}")
    
    def track_user_journey(self, user_id: str, session_id: str, step_name: str, 
                          step_order: int, time_spent: float = 0.0):
        """Track user journey through the application"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO user_journey 
                    (user_id, session_id, step_name, step_order, time_spent, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, session_id, step_name, step_order, time_spent, datetime.now()))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track user journey: {e}")
    
    def get_user_adoption_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get user adoption metrics for the last N days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # New user registrations
                cursor = conn.execute("""
                    SELECT DATE(timestamp) as date, COUNT(DISTINCT user_id) as new_users
                    FROM user_metrics 
                    WHERE metric_type = 'registration' AND timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (cutoff_date,))
                
                new_users_data = cursor.fetchall()
                
                # Active users (users with any activity)
                cursor = conn.execute("""
                    SELECT DATE(timestamp) as date, COUNT(DISTINCT user_id) as active_users
                    FROM user_metrics 
                    WHERE timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (cutoff_date,))
                
                active_users_data = cursor.fetchall()
                
                # User retention (users who returned after first use)
                cursor = conn.execute("""
                    SELECT 
                        COUNT(DISTINCT user_id) as total_users,
                        COUNT(DISTINCT CASE WHEN usage_count > 1 THEN user_id END) as returning_users
                    FROM feature_usage 
                    WHERE first_used >= ?
                """, (cutoff_date,))
                
                retention_data = cursor.fetchone()
                
                return {
                    'new_users': [
                        {'date': row[0], 'count': row[1]} for row in new_users_data
                    ],
                    'active_users': [
                        {'date': row[0], 'count': row[1]} for row in active_users_data
                    ],
                    'retention': {
                        'total_users': retention_data[0],
                        'returning_users': retention_data[1],
                        'retention_rate': retention_data[1] / retention_data[0] if retention_data[0] > 0 else 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get user adoption metrics: {e}")
            return {}
    
    def get_feature_usage_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get feature usage analytics for the last N days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Feature usage summary
                cursor = conn.execute("""
                    SELECT 
                        feature_name,
                        COUNT(DISTINCT user_id) as unique_users,
                        SUM(usage_count) as total_uses,
                        AVG(usage_count) as avg_uses_per_user,
                        AVG(total_time) as avg_time_per_use,
                        AVG(satisfaction_score) as avg_satisfaction
                    FROM feature_usage 
                    WHERE last_used >= ?
                    GROUP BY feature_name
                    ORDER BY total_uses DESC
                """, (cutoff_date,))
                
                feature_stats = cursor.fetchall()
                
                # Feature adoption over time
                cursor = conn.execute("""
                    SELECT 
                        feature_name,
                        DATE(first_used) as date,
                        COUNT(DISTINCT user_id) as new_adopters
                    FROM feature_usage 
                    WHERE first_used >= ?
                    GROUP BY feature_name, DATE(first_used)
                    ORDER BY feature_name, date
                """, (cutoff_date,))
                
                adoption_data = cursor.fetchall()
                
                return {
                    'feature_summary': [
                        {
                            'feature_name': row[0],
                            'unique_users': row[1],
                            'total_uses': row[2],
                            'avg_uses_per_user': row[3],
                            'avg_time_per_use': row[4],
                            'avg_satisfaction': row[5]
                        }
                        for row in feature_stats
                    ],
                    'adoption_timeline': [
                        {
                            'feature_name': row[0],
                            'date': row[1],
                            'new_adopters': row[2]
                        }
                        for row in adoption_data
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get feature usage analytics: {e}")
            return {}
    
    def get_funnel_analysis(self, funnel_steps: List[str], days: int = 30) -> List[FunnelStep]:
        """Analyze user funnel through specified steps"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                funnel_data = []
                
                for i, step in enumerate(funnel_steps):
                    # Count users who reached this step
                    cursor = conn.execute("""
                        SELECT COUNT(DISTINCT user_id) as user_count
                        FROM user_journey 
                        WHERE step_name = ? AND timestamp >= ?
                    """, (step, cutoff_date))
                    
                    user_count = cursor.fetchone()[0]
                    
                    # Calculate conversion rate from previous step
                    conversion_rate = 0.0
                    dropoff_rate = 0.0
                    
                    if i > 0 and funnel_data:
                        previous_count = funnel_data[i-1].user_count
                        if previous_count > 0:
                            conversion_rate = user_count / previous_count
                            dropoff_rate = 1 - conversion_rate
                    
                    # Calculate average time in step
                    cursor = conn.execute("""
                        SELECT AVG(time_spent) as avg_time
                        FROM user_journey 
                        WHERE step_name = ? AND timestamp >= ?
                    """, (step, cutoff_date))
                    
                    avg_time = cursor.fetchone()[0] or 0.0
                    
                    funnel_data.append(FunnelStep(
                        step_name=step,
                        user_count=user_count,
                        conversion_rate=conversion_rate,
                        dropoff_rate=dropoff_rate,
                        avg_time_in_step=avg_time
                    ))
                
                return funnel_data
                
        except Exception as e:
            logger.error(f"Failed to get funnel analysis: {e}")
            return []
    
    def get_score_accuracy_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze score prediction accuracy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Overall accuracy by score type
                cursor = conn.execute("""
                    SELECT 
                        score_type,
                        COUNT(*) as total_predictions,
                        AVG(accuracy_rating) as avg_accuracy,
                        COUNT(CASE WHEN accuracy_rating >= 0.8 THEN 1 END) as high_accuracy_count
                    FROM score_accuracy 
                    WHERE timestamp >= ? AND accuracy_rating IS NOT NULL
                    GROUP BY score_type
                """, (cutoff_date,))
                
                accuracy_stats = cursor.fetchall()
                
                # Accuracy trends over time
                cursor = conn.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        score_type,
                        AVG(accuracy_rating) as avg_accuracy
                    FROM score_accuracy 
                    WHERE timestamp >= ? AND accuracy_rating IS NOT NULL
                    GROUP BY DATE(timestamp), score_type
                    ORDER BY date, score_type
                """, (cutoff_date,))
                
                accuracy_trends = cursor.fetchall()
                
                return {
                    'accuracy_summary': [
                        {
                            'score_type': row[0],
                            'total_predictions': row[1],
                            'avg_accuracy': row[2],
                            'high_accuracy_rate': row[3] / row[1] if row[1] > 0 else 0
                        }
                        for row in accuracy_stats
                    ],
                    'accuracy_trends': [
                        {
                            'date': row[0],
                            'score_type': row[1],
                            'avg_accuracy': row[2]
                        }
                        for row in accuracy_trends
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get score accuracy analysis: {e}")
            return {}
    
    def get_user_satisfaction_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze user satisfaction and feedback"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Overall satisfaction metrics
                cursor = conn.execute("""
                    SELECT 
                        feedback_type,
                        COUNT(*) as total_feedback,
                        AVG(rating) as avg_rating,
                        COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_feedback
                    FROM user_feedback 
                    WHERE timestamp >= ? AND rating IS NOT NULL
                    GROUP BY feedback_type
                """, (cutoff_date,))
                
                satisfaction_stats = cursor.fetchall()
                
                # Feature-specific satisfaction
                cursor = conn.execute("""
                    SELECT 
                        feature_name,
                        COUNT(*) as total_feedback,
                        AVG(rating) as avg_rating
                    FROM user_feedback 
                    WHERE timestamp >= ? AND rating IS NOT NULL AND feature_name IS NOT NULL
                    GROUP BY feature_name
                    ORDER BY avg_rating DESC
                """, (cutoff_date,))
                
                feature_satisfaction = cursor.fetchall()
                
                # Sentiment analysis of comments
                cursor = conn.execute("""
                    SELECT comment, rating
                    FROM user_feedback 
                    WHERE timestamp >= ? AND comment IS NOT NULL
                """, (cutoff_date,))
                
                comments_data = cursor.fetchall()
                
                return {
                    'overall_satisfaction': [
                        {
                            'feedback_type': row[0],
                            'total_feedback': row[1],
                            'avg_rating': row[2],
                            'positive_rate': row[3] / row[1] if row[1] > 0 else 0
                        }
                        for row in satisfaction_stats
                    ],
                    'feature_satisfaction': [
                        {
                            'feature_name': row[0],
                            'total_feedback': row[1],
                            'avg_rating': row[2]
                        }
                        for row in feature_satisfaction
                    ],
                    'sentiment_analysis': self._analyze_sentiment(comments_data)
                }
                
        except Exception as e:
            logger.error(f"Failed to get user satisfaction analysis: {e}")
            return {}
    
    def get_roi_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze ROI for different data sources and features"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # ROI by data source
                cursor = conn.execute("""
                    SELECT 
                        data_source,
                        SUM(cost) as total_cost,
                        SUM(value_generated) as total_value,
                        SUM(user_count) as total_users,
                        (SUM(value_generated) - SUM(cost)) / SUM(cost) as roi_ratio
                    FROM roi_metrics 
                    WHERE timestamp >= ?
                    GROUP BY data_source
                    ORDER BY roi_ratio DESC
                """, (cutoff_date,))
                
                roi_stats = cursor.fetchall()
                
                # ROI trends over time
                cursor = conn.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        data_source,
                        SUM(cost) as daily_cost,
                        SUM(value_generated) as daily_value
                    FROM roi_metrics 
                    WHERE timestamp >= ?
                    GROUP BY DATE(timestamp), data_source
                    ORDER BY date, data_source
                """, (cutoff_date,))
                
                roi_trends = cursor.fetchall()
                
                return {
                    'roi_summary': [
                        {
                            'data_source': row[0],
                            'total_cost': row[1],
                            'total_value': row[2],
                            'total_users': row[3],
                            'roi_ratio': row[4]
                        }
                        for row in roi_stats
                    ],
                    'roi_trends': [
                        {
                            'date': row[0],
                            'data_source': row[1],
                            'daily_cost': row[2],
                            'daily_value': row[3],
                            'daily_roi': (row[3] - row[2]) / row[2] if row[2] > 0 else 0
                        }
                        for row in roi_trends
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get ROI analysis: {e}")
            return {}
    
    def _analyze_sentiment(self, comments_data: List[Tuple[str, float]]) -> Dict[str, Any]:
        """Analyze sentiment of user comments"""
        if not comments_data:
            return {}
        
        # Simple sentiment analysis based on rating correlation
        comments = [row[0] for row in comments_data]
        ratings = [row[1] for row in comments_data]
        
        # Basic sentiment indicators
        positive_words = ['good', 'great', 'excellent', 'love', 'amazing', 'perfect', 'awesome']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'useless', 'broken']
        
        positive_count = sum(1 for comment in comments 
                           if any(word in comment.lower() for word in positive_words))
        negative_count = sum(1 for comment in comments 
                           if any(word in comment.lower() for word in negative_words))
        
        total_comments = len(comments)
        
        return {
            'total_comments': total_comments,
            'positive_sentiment': positive_count / total_comments if total_comments > 0 else 0,
            'negative_sentiment': negative_count / total_comments if total_comments > 0 else 0,
            'neutral_sentiment': (total_comments - positive_count - negative_count) / total_comments if total_comments > 0 else 0,
            'avg_rating': np.mean(ratings) if ratings else 0
        }
    
    def generate_insights_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive insights report"""
        adoption_metrics = self.get_user_adoption_metrics(days)
        feature_analytics = self.get_feature_usage_analytics(days)
        satisfaction_analysis = self.get_user_satisfaction_analysis(days)
        roi_analysis = self.get_roi_analysis(days)
        
        # Generate insights
        insights = []
        
        # User adoption insights
        if adoption_metrics.get('retention'):
            retention_rate = adoption_metrics['retention']['retention_rate']
            if retention_rate < 0.3:
                insights.append({
                    'type': 'warning',
                    'category': 'user_retention',
                    'message': f'Low user retention rate: {retention_rate:.1%}. Consider improving onboarding experience.',
                    'priority': 'high'
                })
            elif retention_rate > 0.7:
                insights.append({
                    'type': 'success',
                    'category': 'user_retention',
                    'message': f'Excellent user retention rate: {retention_rate:.1%}',
                    'priority': 'low'
                })
        
        # Feature usage insights
        if feature_analytics.get('feature_summary'):
            most_used = max(feature_analytics['feature_summary'], 
                          key=lambda x: x['total_uses'])
            least_used = min(feature_analytics['feature_summary'], 
                           key=lambda x: x['total_uses'])
            
            insights.append({
                'type': 'info',
                'category': 'feature_usage',
                'message': f'Most used feature: {most_used["feature_name"]} ({most_used["total_uses"]} uses)',
                'priority': 'medium'
            })
            
            if least_used['total_uses'] < 10:
                insights.append({
                    'type': 'warning',
                    'category': 'feature_usage',
                    'message': f'Low usage feature: {least_used["feature_name"]} ({least_used["total_uses"]} uses). Consider promoting or improving.',
                    'priority': 'medium'
                })
        
        # Satisfaction insights
        if satisfaction_analysis.get('feature_satisfaction'):
            lowest_satisfaction = min(satisfaction_analysis['feature_satisfaction'], 
                                    key=lambda x: x['avg_rating'])
            
            if lowest_satisfaction['avg_rating'] < 3.0:
                insights.append({
                    'type': 'warning',
                    'category': 'user_satisfaction',
                    'message': f'Low satisfaction with {lowest_satisfaction["feature_name"]}: {lowest_satisfaction["avg_rating"]:.1f}/5.0',
                    'priority': 'high'
                })
        
        # ROI insights
        if roi_analysis.get('roi_summary'):
            negative_roi = [source for source in roi_analysis['roi_summary'] 
                          if source['roi_ratio'] < 0]
            
            if negative_roi:
                insights.append({
                    'type': 'warning',
                    'category': 'roi',
                    'message': f'Negative ROI detected for {len(negative_roi)} data sources. Review costs and value generation.',
                    'priority': 'high'
                })
        
        return {
            'summary': {
                'total_users': adoption_metrics.get('retention', {}).get('total_users', 0),
                'active_features': len(feature_analytics.get('feature_summary', [])),
                'avg_satisfaction': satisfaction_analysis.get('sentiment_analysis', {}).get('avg_rating', 0),
                'total_roi': sum(source['roi_ratio'] for source in roi_analysis.get('roi_summary', []))
            },
            'insights': insights,
            'metrics': {
                'adoption': adoption_metrics,
                'features': feature_analytics,
                'satisfaction': satisfaction_analysis,
                'roi': roi_analysis
            }
        }

# Global business intelligence instance
business_intelligence = BusinessIntelligence() 