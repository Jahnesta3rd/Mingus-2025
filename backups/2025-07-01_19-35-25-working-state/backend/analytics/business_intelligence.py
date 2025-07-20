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
import uuid

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
                        time_spent REAL DEFAULT 0,
                        timestamp DATETIME NOT NULL
                    )
                """)
                
                conn.commit()
                logger.info("Business intelligence database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize business intelligence database: {str(e)}")
            raise

    def track_user_metric(self, user_id: str, metric_type: str, value: float, 
                         metadata: Dict[str, Any] = None):
        """Track a user metric"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO user_metrics (user_id, metric_type, value, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, metric_type, value, datetime.now(), json.dumps(metadata or {})))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track user metric: {str(e)}")

    def track_feature_usage(self, user_id: str, feature_name: str, usage_time: float = 0.0,
                           satisfaction_score: Optional[float] = None):
        """Track feature usage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                now = datetime.now()
                
                # Check if usage record exists
                cursor = conn.execute("""
                    SELECT id, usage_count, total_time, first_used
                    FROM feature_usage 
                    WHERE user_id = ? AND feature_name = ?
                """, (user_id, feature_name))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    conn.execute("""
                        UPDATE feature_usage 
                        SET usage_count = usage_count + 1,
                            total_time = total_time + ?,
                            last_used = ?,
                            satisfaction_score = COALESCE(?, satisfaction_score)
                        WHERE id = ?
                    """, (usage_time, now, satisfaction_score, existing[0]))
                else:
                    # Create new record
                    conn.execute("""
                        INSERT INTO feature_usage 
                        (user_id, feature_name, usage_count, total_time, first_used, last_used, satisfaction_score)
                        VALUES (?, ?, 1, ?, ?, ?, ?)
                    """, (user_id, feature_name, usage_time, now, now, satisfaction_score))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track feature usage: {str(e)}")

    def track_user_feedback(self, user_id: str, feedback_type: str, rating: Optional[int] = None,
                           comment: Optional[str] = None, feature_name: Optional[str] = None):
        """Track user feedback"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO user_feedback (user_id, feedback_type, rating, comment, timestamp, feature_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, feedback_type, rating, comment, datetime.now(), feature_name))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track user feedback: {str(e)}")

    def track_score_accuracy(self, user_id: str, score_type: str, predicted_score: float,
                           actual_outcome: Optional[str] = None, accuracy_rating: Optional[float] = None):
        """Track score accuracy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO score_accuracy (user_id, score_type, predicted_score, actual_outcome, accuracy_rating, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, score_type, predicted_score, actual_outcome, accuracy_rating, datetime.now()))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track score accuracy: {str(e)}")

    def track_roi_metric(self, data_source: str, cost: float, value_generated: float, user_count: int):
        """Track ROI metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO roi_metrics (data_source, cost, value_generated, user_count, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (data_source, cost, value_generated, user_count, datetime.now()))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track ROI metric: {str(e)}")

    def track_user_journey(self, user_id: str, session_id: str, step_name: str, 
                          step_order: int, time_spent: float = 0.0):
        """Track user journey steps"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO user_journey (user_id, session_id, step_name, step_order, time_spent, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, session_id, step_name, step_order, time_spent, datetime.now()))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track user journey: {str(e)}")

    def get_user_adoption_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get user adoption metrics for the last N days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Total users
                total_users = conn.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM user_metrics 
                    WHERE timestamp >= ?
                """, (cutoff_date,)).fetchone()[0]
                
                # Active users (users with activity in last 7 days)
                active_cutoff = datetime.now() - timedelta(days=7)
                active_users = conn.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM user_metrics 
                    WHERE timestamp >= ?
                """, (active_cutoff,)).fetchone()[0]
                
                # New users
                new_users = conn.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM user_metrics 
                    WHERE timestamp >= ? AND metric_type = 'registration'
                """, (cutoff_date,)).fetchone()[0]
                
                # Engagement rate
                engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0
                
                return {
                    'total_users': total_users,
                    'active_users': active_users,
                    'new_users': new_users,
                    'engagement_rate': round(engagement_rate, 2),
                    'period_days': days
                }
        except Exception as e:
            logger.error(f"Failed to get user adoption metrics: {str(e)}")
            return {}

    def get_feature_usage_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get feature usage analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Most used features
                feature_usage = conn.execute("""
                    SELECT feature_name, 
                           COUNT(*) as usage_count,
                           AVG(satisfaction_score) as avg_satisfaction
                    FROM feature_usage 
                    WHERE last_used >= ?
                    GROUP BY feature_name
                    ORDER BY usage_count DESC
                """, (cutoff_date,)).fetchall()
                
                # Feature adoption rate
                total_users = conn.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM user_metrics 
                    WHERE timestamp >= ?
                """, (cutoff_date,)).fetchone()[0]
                
                feature_adoption = {}
                for feature_name, usage_count, avg_satisfaction in feature_usage:
                    adoption_rate = (usage_count / total_users * 100) if total_users > 0 else 0
                    feature_adoption[feature_name] = {
                        'usage_count': usage_count,
                        'adoption_rate': round(adoption_rate, 2),
                        'avg_satisfaction': round(avg_satisfaction or 0, 2)
                    }
                
                return {
                    'feature_usage': feature_adoption,
                    'total_users': total_users,
                    'period_days': days
                }
        except Exception as e:
            logger.error(f"Failed to get feature usage analytics: {str(e)}")
            return {}

    def get_funnel_analysis(self, funnel_steps: List[str], days: int = 30) -> List[FunnelStep]:
        """Get funnel analysis for specified steps"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                funnel_data = []
                
                for i, step in enumerate(funnel_steps):
                    # Count users who reached this step
                    user_count = conn.execute("""
                        SELECT COUNT(DISTINCT user_id) FROM user_journey 
                        WHERE step_name = ? AND timestamp >= ?
                    """, (step, cutoff_date)).fetchone()[0]
                    
                    # Calculate conversion rate from previous step
                    conversion_rate = 0.0
                    if i > 0 and funnel_data:
                        prev_count = funnel_data[i-1].user_count
                        conversion_rate = (user_count / prev_count * 100) if prev_count > 0 else 0
                    
                    # Calculate dropoff rate
                    dropoff_rate = 0.0
                    if i > 0 and funnel_data:
                        prev_count = funnel_data[i-1].user_count
                        dropoff_rate = ((prev_count - user_count) / prev_count * 100) if prev_count > 0 else 0
                    
                    # Average time in step
                    avg_time = conn.execute("""
                        SELECT AVG(time_spent) FROM user_journey 
                        WHERE step_name = ? AND timestamp >= ?
                    """, (step, cutoff_date)).fetchone()[0] or 0.0
                    
                    funnel_data.append(FunnelStep(
                        step_name=step,
                        user_count=user_count,
                        conversion_rate=round(conversion_rate, 2),
                        dropoff_rate=round(dropoff_rate, 2),
                        avg_time_in_step=round(avg_time, 2)
                    ))
                
                return funnel_data
        except Exception as e:
            logger.error(f"Failed to get funnel analysis: {str(e)}")
            return []

    def get_score_accuracy_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get score accuracy analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Overall accuracy
                accuracy_data = conn.execute("""
                    SELECT score_type,
                           AVG(accuracy_rating) as avg_accuracy,
                           COUNT(*) as total_predictions
                    FROM score_accuracy 
                    WHERE timestamp >= ? AND accuracy_rating IS NOT NULL
                    GROUP BY score_type
                """, (cutoff_date,)).fetchall()
                
                # Score distribution
                score_distribution = conn.execute("""
                    SELECT score_type,
                           predicted_score,
                           COUNT(*) as count
                    FROM score_accuracy 
                    WHERE timestamp >= ?
                    GROUP BY score_type, predicted_score
                    ORDER BY score_type, predicted_score
                """, (cutoff_date,)).fetchall()
                
                return {
                    'accuracy_by_type': {row[0]: {'avg_accuracy': round(row[1] or 0, 2), 'total_predictions': row[2]} for row in accuracy_data},
                    'score_distribution': score_distribution,
                    'period_days': days
                }
        except Exception as e:
            logger.error(f"Failed to get score accuracy analysis: {str(e)}")
            return {}

    def get_user_satisfaction_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get user satisfaction analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Overall satisfaction
                overall_satisfaction = conn.execute("""
                    SELECT AVG(rating) as avg_rating,
                           COUNT(*) as total_feedback
                    FROM user_feedback 
                    WHERE timestamp >= ? AND rating IS NOT NULL
                """, (cutoff_date,)).fetchone()
                
                # Satisfaction by feature
                feature_satisfaction = conn.execute("""
                    SELECT feature_name,
                           AVG(rating) as avg_rating,
                           COUNT(*) as feedback_count
                    FROM user_feedback 
                    WHERE timestamp >= ? AND rating IS NOT NULL AND feature_name IS NOT NULL
                    GROUP BY feature_name
                    ORDER BY avg_rating DESC
                """, (cutoff_date,)).fetchall()
                
                # Feedback sentiment analysis
                comments_data = conn.execute("""
                    SELECT comment, rating FROM user_feedback 
                    WHERE timestamp >= ? AND comment IS NOT NULL
                """, (cutoff_date,)).fetchall()
                
                sentiment_analysis = self._analyze_sentiment(comments_data)
                
                return {
                    'overall_satisfaction': {
                        'avg_rating': round(overall_satisfaction[0] or 0, 2),
                        'total_feedback': overall_satisfaction[1]
                    },
                    'feature_satisfaction': {row[0]: {'avg_rating': round(row[1] or 0, 2), 'feedback_count': row[2]} for row in feature_satisfaction},
                    'sentiment_analysis': sentiment_analysis,
                    'period_days': days
                }
        except Exception as e:
            logger.error(f"Failed to get user satisfaction analysis: {str(e)}")
            return {}

    def get_roi_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get ROI analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Overall ROI
                roi_data = conn.execute("""
                    SELECT SUM(cost) as total_cost,
                           SUM(value_generated) as total_value,
                           SUM(user_count) as total_users
                    FROM roi_metrics 
                    WHERE timestamp >= ?
                """, (cutoff_date,)).fetchone()
                
                total_cost = roi_data[0] or 0
                total_value = roi_data[1] or 0
                total_users = roi_data[2] or 0
                
                overall_roi = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
                value_per_user = total_value / total_users if total_users > 0 else 0
                
                # ROI by data source
                source_roi = conn.execute("""
                    SELECT data_source,
                           SUM(cost) as total_cost,
                           SUM(value_generated) as total_value,
                           SUM(user_count) as total_users
                    FROM roi_metrics 
                    WHERE timestamp >= ?
                    GROUP BY data_source
                """, (cutoff_date,)).fetchall()
                
                source_analysis = {}
                for row in source_roi:
                    source_cost = row[1] or 0
                    source_value = row[2] or 0
                    source_users = row[3] or 0
                    source_roi_pct = ((source_value - source_cost) / source_cost * 100) if source_cost > 0 else 0
                    
                    source_analysis[row[0]] = {
                        'total_cost': source_cost,
                        'total_value': source_value,
                        'total_users': source_users,
                        'roi_percentage': round(source_roi_pct, 2),
                        'value_per_user': round(source_value / source_users, 2) if source_users > 0 else 0
                    }
                
                return {
                    'overall_roi': {
                        'total_cost': total_cost,
                        'total_value': total_value,
                        'total_users': total_users,
                        'roi_percentage': round(overall_roi, 2),
                        'value_per_user': round(value_per_user, 2)
                    },
                    'source_analysis': source_analysis,
                    'period_days': days
                }
        except Exception as e:
            logger.error(f"Failed to get ROI analysis: {str(e)}")
            return {}

    def _analyze_sentiment(self, comments_data: List[Tuple[str, float]]) -> Dict[str, Any]:
        """Analyze sentiment of user comments"""
        try:
            if not comments_data:
                return {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}
            
            sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
            
            for comment, rating in comments_data:
                if rating >= 4:
                    sentiment_counts['positive'] += 1
                elif rating <= 2:
                    sentiment_counts['negative'] += 1
                else:
                    sentiment_counts['neutral'] += 1
            
            total = len(comments_data)
            return {
                'positive': sentiment_counts['positive'],
                'neutral': sentiment_counts['neutral'],
                'negative': sentiment_counts['negative'],
                'total': total,
                'positive_percentage': round(sentiment_counts['positive'] / total * 100, 2) if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {str(e)}")
            return {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}

    def generate_insights_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive insights report"""
        try:
            return {
                'user_adoption': self.get_user_adoption_metrics(days),
                'feature_usage': self.get_feature_usage_analytics(days),
                'user_satisfaction': self.get_user_satisfaction_analysis(days),
                'score_accuracy': self.get_score_accuracy_analysis(days),
                'roi_analysis': self.get_roi_analysis(days),
                'generated_at': datetime.now().isoformat(),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Failed to generate insights report: {str(e)}")
            return {}

# Global instance
business_intelligence = BusinessIntelligence() 