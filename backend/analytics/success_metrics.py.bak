#!/usr/bin/env python3
"""
Success Metrics System for Job Recommendation Engine

This module provides comprehensive tracking and analysis of user success outcomes,
including income improvements, career advancement, goal achievement, and business
impact metrics to measure the real-world effectiveness of job recommendations.

Features:
- Income tracking and salary improvement analysis
- Career advancement monitoring
- Goal achievement tracking
- User retention and engagement analysis
- Business impact measurement
- Success story tracking
- ROI analysis for recommendations
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

# Import risk analytics components
from .risk_analytics_tracker import RiskAnalyticsTracker
from .risk_predictive_analytics import RiskPredictiveAnalytics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancementType(Enum):
    """Types of career advancement"""
    PROMOTION = "promotion"
    SALARY_INCREASE = "salary_increase"
    ROLE_CHANGE = "role_change"
    SKILL_DEVELOPMENT = "skill_development"
    CERTIFICATION = "certification"
    EDUCATION = "education"
    NETWORKING = "networking"
    MENTORSHIP = "mentorship"

class GoalType(Enum):
    """Types of user goals"""
    SALARY_INCREASE = "salary_increase"
    CAREER_CHANGE = "career_change"
    SKILL_DEVELOPMENT = "skill_development"
    PROMOTION = "promotion"
    WORK_LIFE_BALANCE = "work_life_balance"
    JOB_SATISFACTION = "job_satisfaction"

@dataclass
class IncomeTracking:
    """Data class for income tracking"""
    user_id: str
    current_salary: float
    target_salary: Optional[float] = None
    salary_increase: float = 0.0
    increase_percentage: float = 0.0
    tracking_date: datetime = None
    source: str = "self_reported"
    verified: bool = False

@dataclass
class CareerAdvancement:
    """Data class for career advancement tracking"""
    user_id: str
    advancement_type: str
    advancement_date: datetime
    previous_role: str = ""
    new_role: str = ""
    salary_change: float = 0.0
    skill_improvements: str = ""
    recommendation_correlation: str = ""
    success_factors: str = ""

@dataclass
class UserRetention:
    """Data class for user retention metrics"""
    user_id: str
    registration_date: datetime
    last_activity: datetime
    total_sessions: int = 0
    total_time_spent: int = 0
    recommendations_received: int = 0
    applications_submitted: int = 0
    successful_outcomes: int = 0
    satisfaction_avg: float = 0.0
    churn_risk_score: float = 0.0
    engagement_score: float = 0.0
    lifetime_value: float = 0.0

@dataclass
class GoalAchievement:
    """Data class for goal achievement tracking"""
    user_id: str
    goal_type: str
    goal_value: str
    target_date: Optional[datetime] = None
    achieved_date: Optional[datetime] = None
    achievement_percentage: float = 0.0
    recommendation_contribution: float = 0.0
    success_factors: str = ""

class SuccessMetrics:
    """
    Comprehensive success metrics system for job recommendation engine.
    
    Tracks user outcomes, income improvements, career advancement, and goal
    achievement to measure the real-world impact of job recommendations.
    """
    
    def __init__(self, db_path: str = "backend/analytics/recommendation_analytics.db"):
        """Initialize the success metrics system"""
        self.db_path = db_path
        self._init_database()
        
        # Initialize risk analytics components
        self.risk_analytics = RiskAnalyticsTracker(db_path)
        self.predictive_analytics = RiskPredictiveAnalytics(db_path)
        
        logger.info("SuccessMetrics initialized successfully")
    
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
            logger.info("Success metrics database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing success metrics database: {e}")
            raise
    
    def track_income_change(
        self,
        user_id: str,
        current_salary: float,
        previous_salary: Optional[float] = None,
        target_salary: Optional[float] = None,
        source: str = "self_reported",
        verified: bool = False
    ) -> bool:
        """
        Track user income changes and improvements
        
        Args:
            user_id: User identifier
            current_salary: Current salary amount
            previous_salary: Previous salary for comparison
            target_salary: Target salary goal
            source: Source of income data
            verified: Whether the data is verified
            
        Returns:
            bool: Success status
        """
        try:
            # Calculate salary increase if previous salary provided
            salary_increase = 0.0
            increase_percentage = 0.0
            
            if previous_salary and previous_salary > 0:
                salary_increase = current_salary - previous_salary
                increase_percentage = (salary_increase / previous_salary) * 100
            
            income_tracking = IncomeTracking(
                user_id=user_id,
                current_salary=current_salary,
                target_salary=target_salary,
                salary_increase=salary_increase,
                increase_percentage=increase_percentage,
                tracking_date=datetime.now(),
                source=source,
                verified=verified
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO income_tracking (
                    user_id, current_salary, target_salary, salary_increase,
                    increase_percentage, tracking_date, source, verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                income_tracking.user_id, income_tracking.current_salary,
                income_tracking.target_salary, income_tracking.salary_increase,
                income_tracking.increase_percentage, income_tracking.tracking_date,
                income_tracking.source, income_tracking.verified
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Tracked income change for user {user_id}: {salary_increase:+.2f} ({increase_percentage:+.1f}%)")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking income change: {e}")
            return False
    
    def track_career_advancement(
        self,
        user_id: str,
        advancement_type: str,
        previous_role: str = "",
        new_role: str = "",
        salary_change: float = 0.0,
        skill_improvements: Dict[str, Any] = None,
        recommendation_correlation: Dict[str, Any] = None,
        success_factors: Dict[str, Any] = None
    ) -> bool:
        """
        Track career advancement events
        
        Args:
            user_id: User identifier
            advancement_type: Type of advancement
            previous_role: Previous role/title
            new_role: New role/title
            salary_change: Salary change amount
            skill_improvements: Skills developed
            recommendation_correlation: How recommendations contributed
            success_factors: Factors that led to success
            
        Returns:
            bool: Success status
        """
        try:
            advancement = CareerAdvancement(
                user_id=user_id,
                advancement_type=advancement_type,
                advancement_date=datetime.now(),
                previous_role=previous_role,
                new_role=new_role,
                salary_change=salary_change,
                skill_improvements=json.dumps(skill_improvements or {}),
                recommendation_correlation=json.dumps(recommendation_correlation or {}),
                success_factors=json.dumps(success_factors or {})
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO career_advancement (
                    user_id, advancement_type, advancement_date, previous_role,
                    new_role, salary_change, skill_improvements,
                    recommendation_correlation, success_factors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                advancement.user_id, advancement.advancement_type,
                advancement.advancement_date, advancement.previous_role,
                advancement.new_role, advancement.salary_change,
                advancement.skill_improvements, advancement.recommendation_correlation,
                advancement.success_factors
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Tracked career advancement: {advancement_type} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking career advancement: {e}")
            return False
    
    def track_goal_achievement(
        self,
        user_id: str,
        goal_type: str,
        goal_value: str,
        target_date: Optional[datetime] = None,
        achieved_date: Optional[datetime] = None,
        achievement_percentage: float = 0.0,
        recommendation_contribution: float = 0.0,
        success_factors: Dict[str, Any] = None
    ) -> bool:
        """
        Track goal achievement progress
        
        Args:
            user_id: User identifier
            goal_type: Type of goal
            goal_value: Specific goal description
            target_date: Target completion date
            achieved_date: Actual achievement date
            achievement_percentage: Percentage of goal achieved
            recommendation_contribution: How much recommendations helped
            success_factors: Factors that contributed to success
            
        Returns:
            bool: Success status
        """
        try:
            goal_achievement = GoalAchievement(
                user_id=user_id,
                goal_type=goal_type,
                goal_value=goal_value,
                target_date=target_date,
                achieved_date=achieved_date,
                achievement_percentage=achievement_percentage,
                recommendation_contribution=recommendation_contribution,
                success_factors=json.dumps(success_factors or {})
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO goal_achievement (
                    user_id, goal_type, goal_value, target_date, achieved_date,
                    achievement_percentage, recommendation_contribution, success_factors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                goal_achievement.user_id, goal_achievement.goal_type,
                goal_achievement.goal_value, goal_achievement.target_date,
                goal_achievement.achieved_date, goal_achievement.achievement_percentage,
                goal_achievement.recommendation_contribution, goal_achievement.success_factors
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Tracked goal achievement: {goal_type} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking goal achievement: {e}")
            return False
    
    def update_user_retention(
        self,
        user_id: str,
        registration_date: datetime,
        last_activity: datetime,
        total_sessions: int = 0,
        total_time_spent: int = 0,
        recommendations_received: int = 0,
        applications_submitted: int = 0,
        successful_outcomes: int = 0,
        satisfaction_avg: float = 0.0
    ) -> bool:
        """
        Update user retention metrics
        
        Args:
            user_id: User identifier
            registration_date: When user registered
            last_activity: Last activity timestamp
            total_sessions: Total number of sessions
            total_time_spent: Total time spent in seconds
            recommendations_received: Number of recommendations received
            applications_submitted: Number of applications submitted
            successful_outcomes: Number of successful outcomes
            satisfaction_avg: Average satisfaction score
            
        Returns:
            bool: Success status
        """
        try:
            # Calculate engagement and churn risk scores
            engagement_score = self._calculate_engagement_score(
                total_sessions, total_time_spent, recommendations_received,
                applications_submitted, successful_outcomes
            )
            
            churn_risk_score = self._calculate_churn_risk_score(
                last_activity, total_sessions, engagement_score
            )
            
            # Calculate lifetime value (simplified)
            lifetime_value = self._calculate_lifetime_value(
                successful_outcomes, satisfaction_avg, total_time_spent
            )
            
            retention = UserRetention(
                user_id=user_id,
                registration_date=registration_date,
                last_activity=last_activity,
                total_sessions=total_sessions,
                total_time_spent=total_time_spent,
                recommendations_received=recommendations_received,
                applications_submitted=applications_submitted,
                successful_outcomes=successful_outcomes,
                satisfaction_avg=satisfaction_avg,
                churn_risk_score=churn_risk_score,
                engagement_score=engagement_score,
                lifetime_value=lifetime_value
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_retention (
                    user_id, registration_date, last_activity, total_sessions,
                    total_time_spent, recommendations_received, applications_submitted,
                    successful_outcomes, satisfaction_avg, churn_risk_score,
                    engagement_score, lifetime_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                retention.user_id, retention.registration_date, retention.last_activity,
                retention.total_sessions, retention.total_time_spent,
                retention.recommendations_received, retention.applications_submitted,
                retention.successful_outcomes, retention.satisfaction_avg,
                retention.churn_risk_score, retention.engagement_score,
                retention.lifetime_value
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Updated retention metrics for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user retention: {e}")
            return False
    
    def _calculate_engagement_score(
        self,
        total_sessions: int,
        total_time_spent: int,
        recommendations_received: int,
        applications_submitted: int,
        successful_outcomes: int
    ) -> float:
        """Calculate user engagement score"""
        # Weighted scoring system
        session_score = min(total_sessions * 2, 40)  # Max 40 points
        time_score = min(total_time_spent / 3600 * 5, 30)  # Max 30 points (hours)
        recommendation_score = min(recommendations_received * 3, 20)  # Max 20 points
        application_score = min(applications_submitted * 5, 10)  # Max 10 points
        success_score = min(successful_outcomes * 10, 20)  # Max 20 points
        
        return min(session_score + time_score + recommendation_score + application_score + success_score, 100.0)
    
    def _calculate_churn_risk_score(
        self,
        last_activity: datetime,
        total_sessions: int,
        engagement_score: float
    ) -> float:
        """Calculate user churn risk score (0-100, higher = more risk)"""
        days_since_activity = (datetime.now() - last_activity).days
        
        # Base churn risk from inactivity
        if days_since_activity > 30:
            inactivity_risk = 80
        elif days_since_activity > 14:
            inactivity_risk = 60
        elif days_since_activity > 7:
            inactivity_risk = 40
        else:
            inactivity_risk = 0
        
        # Adjust based on engagement
        engagement_adjustment = (100 - engagement_score) * 0.3
        
        # Adjust based on session frequency
        if total_sessions > 0:
            avg_days_between_sessions = days_since_activity / max(total_sessions, 1)
            if avg_days_between_sessions > 7:
                frequency_risk = 30
            else:
                frequency_risk = 0
        else:
            frequency_risk = 50
        
        return min(inactivity_risk + engagement_adjustment + frequency_risk, 100.0)
    
    def _calculate_lifetime_value(
        self,
        successful_outcomes: int,
        satisfaction_avg: float,
        total_time_spent: int
    ) -> float:
        """Calculate user lifetime value (simplified)"""
        # Base value from successful outcomes
        outcome_value = successful_outcomes * 1000  # $1000 per successful outcome
        
        # Satisfaction multiplier
        satisfaction_multiplier = satisfaction_avg / 5.0 if satisfaction_avg > 0 else 1.0
        
        # Engagement bonus
        engagement_bonus = min(total_time_spent / 3600 * 10, 500)  # $10 per hour, max $500
        
        return (outcome_value + engagement_bonus) * satisfaction_multiplier
    
    def get_user_success_metrics(
        self,
        user_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Get comprehensive success metrics for a user
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict containing success metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get income metrics
            cursor.execute('''
                SELECT 
                    current_salary,
                    salary_increase,
                    increase_percentage,
                    tracking_date
                FROM income_tracking 
                WHERE user_id = ? AND tracking_date >= ?
                ORDER BY tracking_date DESC
            ''', (user_id, start_date))
            
            income_data = cursor.fetchall()
            
            # Get career advancement
            cursor.execute('''
                SELECT 
                    advancement_type,
                    COUNT(*) as count,
                    AVG(salary_change) as avg_salary_change
                FROM career_advancement 
                WHERE user_id = ? AND advancement_date >= ?
                GROUP BY advancement_type
            ''', (user_id, start_date))
            
            advancement_data = {}
            for row in cursor.fetchall():
                advancement_data[row[0]] = {
                    'count': row[1],
                    'avg_salary_change': row[2]
                }
            
            # Get goal achievement
            cursor.execute('''
                SELECT 
                    goal_type,
                    COUNT(*) as total_goals,
                    AVG(achievement_percentage) as avg_achievement,
                    COUNT(CASE WHEN achievement_percentage >= 100 THEN 1 END) as completed_goals
                FROM goal_achievement 
                WHERE user_id = ? AND created_at >= ?
                GROUP BY goal_type
            ''', (user_id, start_date))
            
            goal_data = {}
            for row in cursor.fetchall():
                goal_data[row[0]] = {
                    'total_goals': row[1],
                    'avg_achievement': round(row[2], 2),
                    'completed_goals': row[3]
                }
            
            # Get retention metrics
            cursor.execute('''
                SELECT 
                    registration_date, last_activity, total_sessions,
                    total_time_spent, recommendations_received, applications_submitted,
                    successful_outcomes, satisfaction_avg, churn_risk_score,
                    engagement_score, lifetime_value
                FROM user_retention 
                WHERE user_id = ?
            ''', (user_id,))
            
            retention_data = cursor.fetchone()
            
            conn.close()
            
            # Calculate income improvement
            income_improvement = 0
            if len(income_data) >= 2:
                latest_salary = income_data[0][0]
                previous_salary = income_data[1][0]
                income_improvement = latest_salary - previous_salary
            
            # Calculate success rate
            total_applications = retention_data[5] if retention_data else 0
            successful_outcomes = retention_data[6] if retention_data else 0
            success_rate = (successful_outcomes / total_applications * 100) if total_applications > 0 else 0
            
            return {
                'user_id': user_id,
                'analysis_period_days': days,
                'income_metrics': {
                    'current_salary': income_data[0][0] if income_data else 0,
                    'income_improvement': income_improvement,
                    'latest_increase_percentage': income_data[0][2] if income_data else 0,
                    'salary_tracking_entries': len(income_data)
                },
                'career_advancement': advancement_data,
                'goal_achievement': goal_data,
                'retention_metrics': {
                    'registration_date': retention_data[0] if retention_data else None,
                    'last_activity': retention_data[1] if retention_data else None,
                    'total_sessions': retention_data[2] if retention_data else 0,
                    'total_time_spent_hours': round((retention_data[3] or 0) / 3600, 2),
                    'recommendations_received': retention_data[4] if retention_data else 0,
                    'applications_submitted': total_applications,
                    'successful_outcomes': successful_outcomes,
                    'success_rate': round(success_rate, 2),
                    'satisfaction_avg': round(retention_data[7] or 0, 2),
                    'churn_risk_score': round(retention_data[8] or 0, 2),
                    'engagement_score': round(retention_data[9] or 0, 2),
                    'lifetime_value': round(retention_data[10] or 0, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user success metrics: {e}")
            return {}
    
    def get_system_success_metrics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get system-wide success metrics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing system success metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Overall income improvements
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_income_entries,
                    AVG(salary_increase) as avg_salary_increase,
                    AVG(increase_percentage) as avg_increase_percentage,
                    COUNT(CASE WHEN salary_increase > 0 THEN 1 END) as positive_changes
                FROM income_tracking 
                WHERE tracking_date >= ?
            ''', (start_date,))
            
            income_metrics = cursor.fetchone()
            
            # Career advancement summary
            cursor.execute('''
                SELECT 
                    advancement_type,
                    COUNT(*) as count
                FROM career_advancement 
                WHERE advancement_date >= ?
                GROUP BY advancement_type
                ORDER BY count DESC
            ''', (start_date,))
            
            advancement_summary = {}
            for row in cursor.fetchall():
                advancement_summary[row[0]] = row[1]
            
            # Goal achievement summary
            cursor.execute('''
                SELECT 
                    goal_type,
                    COUNT(*) as total_goals,
                    AVG(achievement_percentage) as avg_achievement,
                    COUNT(CASE WHEN achievement_percentage >= 100 THEN 1 END) as completed_goals
                FROM goal_achievement 
                WHERE created_at >= ?
                GROUP BY goal_type
            ''', (start_date,))
            
            goal_summary = {}
            for row in cursor.fetchall():
                goal_summary[row[0]] = {
                    'total_goals': row[1],
                    'avg_achievement': round(row[2], 2),
                    'completed_goals': row[3],
                    'completion_rate': round((row[3] / row[1] * 100) if row[1] > 0 else 0, 2)
                }
            
            # User retention summary
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_users,
                    AVG(engagement_score) as avg_engagement,
                    AVG(churn_risk_score) as avg_churn_risk,
                    AVG(lifetime_value) as avg_lifetime_value,
                    COUNT(CASE WHEN churn_risk_score > 70 THEN 1 END) as high_risk_users
                FROM user_retention
            ''')
            
            retention_summary = cursor.fetchone()
            
            # Success stories (users with significant improvements)
            cursor.execute('''
                SELECT 
                    ur.user_id,
                    ur.successful_outcomes,
                    ur.satisfaction_avg,
                    it.current_salary,
                    it.salary_increase,
                    it.increase_percentage
                FROM user_retention ur
                LEFT JOIN (
                    SELECT user_id, current_salary, salary_increase, increase_percentage,
                           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY tracking_date DESC) as rn
                    FROM income_tracking
                ) it ON ur.user_id = it.user_id AND it.rn = 1
                WHERE ur.successful_outcomes > 0
                ORDER BY ur.successful_outcomes DESC, it.increase_percentage DESC
                LIMIT 10
            ''')
            
            success_stories = []
            for row in cursor.fetchall():
                success_stories.append({
                    'user_id': row[0],
                    'successful_outcomes': row[1],
                    'satisfaction_avg': round(row[2] or 0, 2),
                    'current_salary': row[3] or 0,
                    'salary_increase': row[4] or 0,
                    'increase_percentage': round(row[5] or 0, 2)
                })
            
            conn.close()
            
            return {
                'analysis_period_days': days,
                'income_metrics': {
                    'total_income_entries': income_metrics[0] or 0,
                    'avg_salary_increase': round(income_metrics[1] or 0, 2),
                    'avg_increase_percentage': round(income_metrics[2] or 0, 2),
                    'positive_changes': income_metrics[3] or 0,
                    'positive_change_rate': round((income_metrics[3] or 0) / max(income_metrics[0] or 1, 1) * 100, 2)
                },
                'career_advancement': advancement_summary,
                'goal_achievement': goal_summary,
                'retention_metrics': {
                    'total_users': retention_summary[0] or 0,
                    'avg_engagement_score': round(retention_summary[1] or 0, 2),
                    'avg_churn_risk_score': round(retention_summary[2] or 0, 2),
                    'avg_lifetime_value': round(retention_summary[3] or 0, 2),
                    'high_risk_users': retention_summary[4] or 0,
                    'high_risk_percentage': round((retention_summary[4] or 0) / max(retention_summary[0] or 1, 1) * 100, 2)
                },
                'success_stories': success_stories
            }
            
        except Exception as e:
            logger.error(f"Error getting system success metrics: {e}")
            return {}
    
    def get_roi_analysis(
        self,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Get ROI analysis for the recommendation system
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing ROI analysis
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Calculate total salary increases
            cursor.execute('''
                SELECT 
                    SUM(salary_increase) as total_salary_increase,
                    COUNT(DISTINCT user_id) as users_with_increases,
                    AVG(salary_increase) as avg_salary_increase
                FROM income_tracking 
                WHERE tracking_date >= ? AND salary_increase > 0
            ''', (start_date,))
            
            salary_impact = cursor.fetchone()
            
            # Calculate system costs (simplified)
            cursor.execute('''
                SELECT 
                    SUM(duration) as total_processing_time,
                    COUNT(*) as total_recommendations
                FROM processing_metrics 
                WHERE start_time >= ?
            ''', (start_date,))
            
            cost_data = cursor.fetchone()
            
            # Estimate costs (would be actual cloud costs in production)
            total_processing_time = cost_data[0] or 0
            total_recommendations = cost_data[1] or 0
            estimated_cost = total_processing_time * 0.001  # $0.001 per second
            
            # Calculate ROI
            total_salary_increase = salary_impact[0] or 0
            roi_percentage = ((total_salary_increase - estimated_cost) / estimated_cost * 100) if estimated_cost > 0 else 0
            
            # Calculate cost per successful outcome
            cursor.execute('''
                SELECT COUNT(*) as successful_outcomes
                FROM user_retention 
                WHERE successful_outcomes > 0
            ''')
            
            successful_outcomes = cursor.fetchone()[0] or 0
            cost_per_success = estimated_cost / successful_outcomes if successful_outcomes > 0 else 0
            
            conn.close()
            
            return {
                'analysis_period_days': days,
                'financial_impact': {
                    'total_salary_increase': round(total_salary_increase, 2),
                    'users_with_increases': salary_impact[1] or 0,
                    'avg_salary_increase': round(salary_impact[2] or 0, 2)
                },
                'system_costs': {
                    'total_processing_time_hours': round(total_processing_time / 3600, 2),
                    'total_recommendations': total_recommendations,
                    'estimated_cost': round(estimated_cost, 2),
                    'cost_per_recommendation': round(estimated_cost / total_recommendations if total_recommendations > 0 else 0, 4)
                },
                'roi_metrics': {
                    'roi_percentage': round(roi_percentage, 2),
                    'successful_outcomes': successful_outcomes,
                    'cost_per_success': round(cost_per_success, 2),
                    'revenue_per_dollar_spent': round(total_salary_increase / estimated_cost if estimated_cost > 0 else 0, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting ROI analysis: {e}")
            return {}
    
    # =====================================================
    # RISK-BASED CAREER PROTECTION METRICS
    # =====================================================
    
    def career_protection_success_rate(self, time_period: str = 'last_30_days') -> float:
        """
        Calculate career protection success rate
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            float: Success rate percentage
        """
        try:
            protection_metrics = self.risk_analytics.get_career_protection_metrics(time_period)
            return protection_metrics.get('overall_success_rate', 0.0)
        except Exception as e:
            logger.error(f"Error calculating career protection success rate: {e}")
            return 0.0
    
    def early_warning_accuracy(self, time_period: str = 'last_30_days') -> float:
        """
        Calculate early warning accuracy rate
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            float: Accuracy percentage
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate date range
            if time_period == 'last_7_days':
                start_date = datetime.now() - timedelta(days=7)
            elif time_period == 'last_30_days':
                start_date = datetime.now() - timedelta(days=30)
            elif time_period == 'last_90_days':
                start_date = datetime.now() - timedelta(days=90)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            # Get forecasts with actual outcomes
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_forecasts,
                    COUNT(CASE WHEN accuracy_score >= 0.8 THEN 1 END) as accurate_forecasts
                FROM risk_forecasts 
                WHERE forecast_date >= ? AND actual_outcome IS NOT NULL
            ''', (start_date,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result[0] > 0:
                accuracy_rate = (result[1] / result[0]) * 100
                return round(accuracy_rate, 2)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating early warning accuracy: {e}")
            return 0.0
    
    def risk_intervention_effectiveness(self, time_period: str = 'last_30_days') -> float:
        """
        Calculate risk intervention effectiveness rate
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            float: Effectiveness percentage
        """
        try:
            intervention_metrics = self.risk_analytics.get_intervention_effectiveness(time_period)
            
            # Calculate overall effectiveness across all intervention types
            total_interventions = 0
            effective_interventions = 0
            
            for intervention_type, metrics in intervention_metrics.get('intervention_metrics', {}).items():
                total_interventions += metrics.get('total_interventions', 0)
                effective_interventions += metrics.get('effective_interventions', 0)
            
            if total_interventions > 0:
                effectiveness_rate = (effective_interventions / total_interventions) * 100
                return round(effectiveness_rate, 2)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating risk intervention effectiveness: {e}")
            return 0.0
    
    def income_protection_rate(self, time_period: str = 'last_30_days') -> float:
        """
        Calculate income protection rate during risk-triggered job changes
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            float: Income protection percentage
        """
        try:
            protection_metrics = self.risk_analytics.get_career_protection_metrics(time_period)
            return protection_metrics.get('income_protection_rate', 0.0)
        except Exception as e:
            logger.error(f"Error calculating income protection rate: {e}")
            return 0.0
    
    def unemployment_prevention_rate(self, time_period: str = 'last_30_days') -> float:
        """
        Calculate unemployment prevention rate for high-risk users
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            float: Unemployment prevention percentage
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate date range
            if time_period == 'last_7_days':
                start_date = datetime.now() - timedelta(days=7)
            elif time_period == 'last_30_days':
                start_date = datetime.now() - timedelta(days=30)
            elif time_period == 'last_90_days':
                start_date = datetime.now() - timedelta(days=90)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            # Get high-risk users and unemployment prevention outcomes
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT ura.user_id) as high_risk_users,
                    COUNT(CASE WHEN cpo.outcome_type = 'unemployment_prevented' THEN 1 END) as unemployment_prevented
                FROM user_risk_assessments ura
                LEFT JOIN career_protection_outcomes cpo ON ura.id = cpo.risk_assessment_id
                WHERE ura.assessment_date >= ? AND ura.risk_level IN ('high', 'critical')
            ''', (start_date,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result[0] > 0:
                prevention_rate = (result[1] / result[0]) * 100
                return round(prevention_rate, 2)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating unemployment prevention rate: {e}")
            return 0.0
    
    def risk_to_outcome_funnel(self, time_period: str = 'last_30_days') -> Dict[str, Any]:
        """
        Track user progression from risk detection to successful job placement
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            Dict containing funnel metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate date range
            if time_period == 'last_7_days':
                start_date = datetime.now() - timedelta(days=7)
            elif time_period == 'last_30_days':
                start_date = datetime.now() - timedelta(days=30)
            elif time_period == 'last_90_days':
                start_date = datetime.now() - timedelta(days=90)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            # Get funnel metrics
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT ura.user_id) as users_at_risk,
                    COUNT(DISTINCT CASE WHEN ri.id IS NOT NULL THEN ura.user_id END) as users_with_interventions,
                    COUNT(DISTINCT CASE WHEN cpo.outcome_type = 'successful_transition' THEN ura.user_id END) as users_with_successful_transitions,
                    COUNT(DISTINCT CASE WHEN cpo.outcome_type = 'salary_increased' THEN ura.user_id END) as users_with_salary_increases
                FROM user_risk_assessments ura
                LEFT JOIN risk_interventions ri ON ura.id = ri.risk_assessment_id
                LEFT JOIN career_protection_outcomes cpo ON ura.id = cpo.risk_assessment_id
                WHERE ura.assessment_date >= ? AND ura.risk_level IN ('high', 'critical')
            ''', (start_date,))
            
            result = cursor.fetchone()
            conn.close()
            
            users_at_risk = result[0] or 0
            users_with_interventions = result[1] or 0
            users_with_successful_transitions = result[2] or 0
            users_with_salary_increases = result[3] or 0
            
            return {
                'time_period': time_period,
                'funnel_steps': {
                    'users_at_risk': users_at_risk,
                    'users_with_interventions': users_with_interventions,
                    'users_with_successful_transitions': users_with_successful_transitions,
                    'users_with_salary_increases': users_with_salary_increases
                },
                'conversion_rates': {
                    'risk_to_intervention': round((users_with_interventions / users_at_risk * 100) if users_at_risk > 0 else 0, 2),
                    'intervention_to_transition': round((users_with_successful_transitions / users_with_interventions * 100) if users_with_interventions > 0 else 0, 2),
                    'transition_to_salary_increase': round((users_with_salary_increases / users_with_successful_transitions * 100) if users_with_successful_transitions > 0 else 0, 2),
                    'overall_success_rate': round((users_with_salary_increases / users_at_risk * 100) if users_at_risk > 0 else 0, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk to outcome funnel: {e}")
            return {}
    
    def proactive_vs_reactive_comparison(self, time_period: str = 'last_30_days') -> Dict[str, Any]:
        """
        Compare outcomes for users who act on early warnings vs reactive job searchers
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            Dict containing comparison metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate date range
            if time_period == 'last_7_days':
                start_date = datetime.now() - timedelta(days=7)
            elif time_period == 'last_30_days':
                start_date = datetime.now() - timedelta(days=30)
            elif time_period == 'last_90_days':
                start_date = datetime.now() - timedelta(days=90)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            # Get proactive users (those with early warning interventions)
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT ura.user_id) as proactive_users,
                    AVG(cpo.salary_change) as avg_salary_change_proactive,
                    AVG(cpo.time_to_new_role) as avg_time_to_role_proactive,
                    AVG(cpo.satisfaction_score) as avg_satisfaction_proactive
                FROM user_risk_assessments ura
                JOIN risk_interventions ri ON ura.id = ri.risk_assessment_id
                LEFT JOIN career_protection_outcomes cpo ON ura.id = cpo.risk_assessment_id
                WHERE ura.assessment_date >= ? 
                AND ri.intervention_type = 'early_warning'
                AND cpo.outcome_type = 'successful_transition'
            ''', (start_date,))
            
            proactive_result = cursor.fetchone()
            
            # Get reactive users (those without early warning interventions)
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT ura.user_id) as reactive_users,
                    AVG(cpo.salary_change) as avg_salary_change_reactive,
                    AVG(cpo.time_to_new_role) as avg_time_to_role_reactive,
                    AVG(cpo.satisfaction_score) as avg_satisfaction_reactive
                FROM user_risk_assessments ura
                LEFT JOIN risk_interventions ri ON ura.id = ri.risk_assessment_id
                LEFT JOIN career_protection_outcomes cpo ON ura.id = cpo.risk_assessment_id
                WHERE ura.assessment_date >= ? 
                AND (ri.id IS NULL OR ri.intervention_type != 'early_warning')
                AND cpo.outcome_type = 'successful_transition'
            ''', (start_date,))
            
            reactive_result = cursor.fetchone()
            conn.close()
            
            return {
                'time_period': time_period,
                'proactive_users': {
                    'count': proactive_result[0] or 0,
                    'avg_salary_change': round(proactive_result[1] or 0, 2),
                    'avg_time_to_role_days': round(proactive_result[2] or 0, 1),
                    'avg_satisfaction': round(proactive_result[3] or 0, 2)
                },
                'reactive_users': {
                    'count': reactive_result[0] or 0,
                    'avg_salary_change': round(reactive_result[1] or 0, 2),
                    'avg_time_to_role_days': round(reactive_result[2] or 0, 1),
                    'avg_satisfaction': round(reactive_result[3] or 0, 2)
                },
                'comparison': {
                    'salary_change_difference': round((proactive_result[1] or 0) - (reactive_result[1] or 0), 2),
                    'time_difference_days': round((reactive_result[2] or 0) - (proactive_result[2] or 0), 1),
                    'satisfaction_difference': round((proactive_result[3] or 0) - (reactive_result[3] or 0), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating proactive vs reactive comparison: {e}")
            return {}
    
    def risk_communication_effectiveness(self, time_period: str = 'last_30_days') -> Dict[str, Any]:
        """
        Measure how well users understand and respond to risk alerts
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            Dict containing communication effectiveness metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate date range
            if time_period == 'last_7_days':
                start_date = datetime.now() - timedelta(days=7)
            elif time_period == 'last_30_days':
                start_date = datetime.now() - timedelta(days=30)
            elif time_period == 'last_90_days':
                start_date = datetime.now() - timedelta(days=90)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            # Get communication effectiveness metrics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_interventions,
                    COUNT(CASE WHEN intervention_status = 'completed' THEN 1 END) as completed_interventions,
                    COUNT(CASE WHEN user_response IS NOT NULL THEN 1 END) as interventions_with_response,
                    AVG(CASE WHEN user_response IS NOT NULL THEN 
                        json_extract(user_response, '$.understanding_score') 
                    END) as avg_understanding_score,
                    AVG(CASE WHEN user_response IS NOT NULL THEN 
                        json_extract(user_response, '$.action_taken_score') 
                    END) as avg_action_taken_score
                FROM risk_interventions 
                WHERE intervention_date >= ? AND intervention_type = 'early_warning'
            ''', (start_date,))
            
            result = cursor.fetchone()
            conn.close()
            
            total_interventions = result[0] or 0
            completed_interventions = result[1] or 0
            interventions_with_response = result[2] or 0
            avg_understanding_score = result[3] or 0
            avg_action_taken_score = result[4] or 0
            
            return {
                'time_period': time_period,
                'communication_metrics': {
                    'total_interventions': total_interventions,
                    'completed_interventions': completed_interventions,
                    'interventions_with_response': interventions_with_response,
                    'response_rate': round((interventions_with_response / total_interventions * 100) if total_interventions > 0 else 0, 2),
                    'completion_rate': round((completed_interventions / total_interventions * 100) if total_interventions > 0 else 0, 2),
                    'avg_understanding_score': round(avg_understanding_score, 2),
                    'avg_action_taken_score': round(avg_action_taken_score, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk communication effectiveness: {e}")
            return {}
    
    def emergency_unlock_conversion(self, time_period: str = 'last_30_days') -> Dict[str, Any]:
        """
        Calculate success rates for users who receive emergency feature unlocks
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            Dict containing emergency unlock conversion metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate date range
            if time_period == 'last_7_days':
                start_date = datetime.now() - timedelta(days=7)
            elif time_period == 'last_30_days':
                start_date = datetime.now() - timedelta(days=30)
            elif time_period == 'last_90_days':
                start_date = datetime.now() - timedelta(days=90)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            # Get emergency unlock metrics
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT ri.user_id) as users_with_emergency_unlock,
                    COUNT(DISTINCT CASE WHEN cpo.outcome_type = 'successful_transition' THEN ri.user_id END) as successful_transitions,
                    COUNT(DISTINCT CASE WHEN cpo.outcome_type = 'salary_increased' THEN ri.user_id END) as salary_increases,
                    AVG(cpo.time_to_new_role) as avg_time_to_role,
                    AVG(cpo.satisfaction_score) as avg_satisfaction
                FROM risk_interventions ri
                LEFT JOIN career_protection_outcomes cpo ON ri.user_id = cpo.user_id
                WHERE ri.intervention_date >= ? 
                AND ri.intervention_type = 'emergency_unlock'
                AND (cpo.outcome_date >= ri.intervention_date OR cpo.outcome_date IS NULL)
            ''', (start_date,))
            
            result = cursor.fetchone()
            conn.close()
            
            users_with_emergency_unlock = result[0] or 0
            successful_transitions = result[1] or 0
            salary_increases = result[2] or 0
            avg_time_to_role = result[3] or 0
            avg_satisfaction = result[4] or 0
            
            return {
                'time_period': time_period,
                'emergency_unlock_metrics': {
                    'users_with_emergency_unlock': users_with_emergency_unlock,
                    'successful_transitions': successful_transitions,
                    'salary_increases': salary_increases,
                    'transition_rate': round((successful_transitions / users_with_emergency_unlock * 100) if users_with_emergency_unlock > 0 else 0, 2),
                    'salary_increase_rate': round((salary_increases / users_with_emergency_unlock * 100) if users_with_emergency_unlock > 0 else 0, 2),
                    'avg_time_to_role_days': round(avg_time_to_role, 1),
                    'avg_satisfaction': round(avg_satisfaction, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating emergency unlock conversion: {e}")
            return {}
    
    def get_risk_based_success_metrics(self, time_period: str = 'last_30_days') -> Dict[str, Any]:
        """
        Get comprehensive risk-based success metrics
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            Dict containing all risk-based success metrics
        """
        try:
            return {
                'time_period': time_period,
                'career_protection_metrics': {
                    'career_protection_success_rate': self.career_protection_success_rate(time_period),
                    'early_warning_accuracy': self.early_warning_accuracy(time_period),
                    'risk_intervention_effectiveness': self.risk_intervention_effectiveness(time_period),
                    'income_protection_rate': self.income_protection_rate(time_period),
                    'unemployment_prevention_rate': self.unemployment_prevention_rate(time_period)
                },
                'user_journey_analytics': {
                    'risk_to_outcome_funnel': self.risk_to_outcome_funnel(time_period),
                    'proactive_vs_reactive_comparison': self.proactive_vs_reactive_comparison(time_period),
                    'risk_communication_effectiveness': self.risk_communication_effectiveness(time_period),
                    'emergency_unlock_conversion': self.emergency_unlock_conversion(time_period)
                },
                'predictive_insights': self.predictive_analytics.get_forecast_accuracy_metrics(30),
                'risk_trend_analysis': self.risk_analytics.get_risk_trend_analysis(30)
            }
            
        except Exception as e:
            logger.error(f"Error getting risk-based success metrics: {e}")
            return {}
