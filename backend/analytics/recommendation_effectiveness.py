#!/usr/bin/env python3
"""
Recommendation Effectiveness Analytics System

This module provides comprehensive tracking and analysis of job recommendation
effectiveness, including engagement metrics, application outcomes, and success
rate analysis across different recommendation tiers.

Features:
- Job recommendation tracking and scoring
- Engagement and interaction analysis
- Application outcome tracking
- Success rate calculation by tier
- User satisfaction and feedback analysis
- Recommendation quality metrics
- A/B testing support for recommendation improvements
"""

import sqlite3
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobTier(Enum):
    """Job recommendation tiers"""
    CONSERVATIVE = "conservative"
    OPTIMAL = "optimal"
    STRETCH = "stretch"

class EngagementType(Enum):
    """Types of recommendation engagement"""
    VIEWED = "viewed"
    CLICKED = "clicked"
    APPLIED = "applied"
    SAVED = "saved"
    SHARED = "shared"
    DISMISSED = "dismissed"

class ApplicationStatus(Enum):
    """Application outcome statuses"""
    STARTED = "started"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFER_RECEIVED = "offer_received"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_DECLINED = "offer_declined"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

@dataclass
class JobRecommendation:
    """Data class for job recommendations"""
    recommendation_id: str
    session_id: str
    user_id: str
    job_id: str
    tier: str
    recommendation_score: float
    salary_increase_potential: float
    success_probability: float
    skills_gap_score: float
    company_culture_fit: float
    career_advancement_potential: float

@dataclass
class RecommendationEngagement:
    """Data class for recommendation engagement events"""
    recommendation_id: str
    user_id: str
    engagement_type: str
    engagement_time: float = 0.0

@dataclass
class ApplicationOutcome:
    """Data class for application outcomes"""
    recommendation_id: str
    user_id: str
    application_id: str
    application_status: str
    application_date: datetime
    outcome_date: Optional[datetime] = None
    salary_offered: Optional[float] = None
    salary_negotiated: Optional[float] = None
    final_salary: Optional[float] = None
    interview_rounds: int = 0
    feedback_received: str = ""
    success_factors: str = ""

@dataclass
class UserFeedback:
    """Data class for user feedback"""
    user_id: str
    session_id: Optional[str]
    feedback_type: str
    rating: Optional[int] = None
    feedback_text: str = ""
    recommendation_id: Optional[str] = None

class RecommendationEffectiveness:
    """
    Comprehensive recommendation effectiveness analytics system.
    
    Tracks job recommendations, user engagement, application outcomes,
    and success rates to measure and improve recommendation quality.
    """
    
    def __init__(self, db_path: str = "backend/analytics/recommendation_analytics.db"):
        """Initialize the recommendation effectiveness system"""
        self.db_path = db_path
        self._init_database()
        logger.info("RecommendationEffectiveness initialized successfully")
    
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
            logger.info("Recommendation effectiveness database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing recommendation effectiveness database: {e}")
            raise
    
    def track_recommendation(
        self,
        session_id: str,
        user_id: str,
        job_id: str,
        tier: str,
        recommendation_score: float,
        salary_increase_potential: float = 0.0,
        success_probability: float = 0.0,
        skills_gap_score: float = 0.0,
        company_culture_fit: float = 0.0,
        career_advancement_potential: float = 0.0
    ) -> str:
        """
        Track a new job recommendation
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            job_id: Job opportunity identifier
            tier: Recommendation tier (conservative, optimal, stretch)
            recommendation_score: Overall recommendation score
            salary_increase_potential: Potential salary increase
            success_probability: Probability of success
            skills_gap_score: Skills gap analysis score
            company_culture_fit: Company culture fit score
            career_advancement_potential: Career advancement potential
            
        Returns:
            recommendation_id: Unique recommendation identifier
        """
        try:
            recommendation_id = str(uuid.uuid4())
            recommendation = JobRecommendation(
                recommendation_id=recommendation_id,
                session_id=session_id,
                user_id=user_id,
                job_id=job_id,
                tier=tier,
                recommendation_score=recommendation_score,
                salary_increase_potential=salary_increase_potential,
                success_probability=success_probability,
                skills_gap_score=skills_gap_score,
                company_culture_fit=company_culture_fit,
                career_advancement_potential=career_advancement_potential
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO job_recommendations (
                    recommendation_id, session_id, user_id, job_id, tier,
                    recommendation_score, salary_increase_potential, success_probability,
                    skills_gap_score, company_culture_fit, career_advancement_potential
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recommendation.recommendation_id, recommendation.session_id,
                recommendation.user_id, recommendation.job_id, recommendation.tier,
                recommendation.recommendation_score, recommendation.salary_increase_potential,
                recommendation.success_probability, recommendation.skills_gap_score,
                recommendation.company_culture_fit, recommendation.career_advancement_potential
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Tracked recommendation {recommendation_id} for user {user_id}")
            return recommendation_id
            
        except Exception as e:
            logger.error(f"Error tracking recommendation: {e}")
            raise
    
    def track_engagement(
        self,
        recommendation_id: str,
        user_id: str,
        engagement_type: str,
        engagement_time: float = 0.0
    ) -> bool:
        """
        Track user engagement with a recommendation
        
        Args:
            recommendation_id: Recommendation identifier
            user_id: User identifier
            engagement_type: Type of engagement
            engagement_time: Time spent engaging in seconds
            
        Returns:
            bool: Success status
        """
        try:
            engagement = RecommendationEngagement(
                recommendation_id=recommendation_id,
                user_id=user_id,
                engagement_type=engagement_type,
                engagement_time=engagement_time
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO recommendation_engagement (
                    recommendation_id, user_id, engagement_type, engagement_time
                ) VALUES (?, ?, ?, ?)
            ''', (
                engagement.recommendation_id, engagement.user_id,
                engagement.engagement_type, engagement.engagement_time
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Tracked engagement: {engagement_type} for recommendation {recommendation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking engagement: {e}")
            return False
    
    def track_application_outcome(
        self,
        recommendation_id: str,
        user_id: str,
        application_id: str,
        application_status: str,
        application_date: Optional[datetime] = None,
        outcome_date: Optional[datetime] = None,
        salary_offered: Optional[float] = None,
        salary_negotiated: Optional[float] = None,
        final_salary: Optional[float] = None,
        interview_rounds: int = 0,
        feedback_received: str = "",
        success_factors: Dict[str, Any] = None
    ) -> bool:
        """
        Track application outcomes and results
        
        Args:
            recommendation_id: Recommendation identifier
            user_id: User identifier
            application_id: Application identifier
            application_status: Current application status
            application_date: Date application was submitted
            outcome_date: Date of final outcome
            salary_offered: Salary offered by employer
            salary_negotiated: Negotiated salary
            final_salary: Final accepted salary
            interview_rounds: Number of interview rounds
            feedback_received: Feedback from employer
            success_factors: Factors that contributed to success
            
        Returns:
            bool: Success status
        """
        try:
            if application_date is None:
                application_date = datetime.now()
            
            outcome = ApplicationOutcome(
                recommendation_id=recommendation_id,
                user_id=user_id,
                application_id=application_id,
                application_status=application_status,
                application_date=application_date,
                outcome_date=outcome_date,
                salary_offered=salary_offered,
                salary_negotiated=salary_negotiated,
                final_salary=final_salary,
                interview_rounds=interview_rounds,
                feedback_received=feedback_received,
                success_factors=json.dumps(success_factors or {})
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO application_outcomes (
                    recommendation_id, user_id, application_id, application_status,
                    application_date, outcome_date, salary_offered, salary_negotiated,
                    final_salary, interview_rounds, feedback_received, success_factors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                outcome.recommendation_id, outcome.user_id, outcome.application_id,
                outcome.application_status, outcome.application_date, outcome.outcome_date,
                outcome.salary_offered, outcome.salary_negotiated, outcome.final_salary,
                outcome.interview_rounds, outcome.feedback_received, outcome.success_factors
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Tracked application outcome: {application_status} for recommendation {recommendation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking application outcome: {e}")
            return False
    
    def track_user_feedback(
        self,
        user_id: str,
        feedback_type: str,
        rating: Optional[int] = None,
        feedback_text: str = "",
        session_id: Optional[str] = None,
        recommendation_id: Optional[str] = None
    ) -> bool:
        """
        Track user feedback and satisfaction
        
        Args:
            user_id: User identifier
            feedback_type: Type of feedback
            rating: User rating (1-5)
            feedback_text: Text feedback
            session_id: Session identifier
            recommendation_id: Recommendation identifier
            
        Returns:
            bool: Success status
        """
        try:
            feedback = UserFeedback(
                user_id=user_id,
                session_id=session_id,
                feedback_type=feedback_type,
                rating=rating,
                feedback_text=feedback_text,
                recommendation_id=recommendation_id
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_feedback (
                    user_id, session_id, feedback_type, rating, feedback_text, recommendation_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                feedback.user_id, feedback.session_id, feedback.feedback_type,
                feedback.rating, feedback.feedback_text, feedback.recommendation_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Tracked user feedback: {feedback_type} from user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking user feedback: {e}")
            return False
    
    def get_recommendation_effectiveness_by_tier(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get recommendation effectiveness metrics by tier
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing effectiveness metrics by tier
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get effectiveness metrics by tier
            cursor.execute('''
                SELECT 
                    jr.tier,
                    COUNT(*) as total_recommendations,
                    COUNT(DISTINCT jr.user_id) as unique_users,
                    AVG(jr.recommendation_score) as avg_recommendation_score,
                    AVG(jr.salary_increase_potential) as avg_salary_potential,
                    AVG(jr.success_probability) as avg_success_probability,
                    COUNT(re.recommendation_id) as total_engagements,
                    COUNT(DISTINCT re.recommendation_id) as engaged_recommendations,
                    COUNT(ao.application_id) as applications_started,
                    COUNT(CASE WHEN ao.application_status IN ('offer_received', 'offer_accepted') THEN 1 END) as successful_applications,
                    COUNT(CASE WHEN ao.application_status = 'offer_accepted' THEN 1 END) as offers_accepted,
                    AVG(ao.final_salary) as avg_final_salary,
                    AVG(ao.interview_rounds) as avg_interview_rounds
                FROM job_recommendations jr
                LEFT JOIN recommendation_engagement re ON jr.recommendation_id = re.recommendation_id
                LEFT JOIN application_outcomes ao ON jr.recommendation_id = ao.recommendation_id
                WHERE jr.created_at >= ?
                GROUP BY jr.tier
                ORDER BY jr.tier
            ''', (start_date,))
            
            tier_metrics = {}
            rows = cursor.fetchall()
            
            for row in rows:
                if len(row) < 13:
                    logger.error(f"Row has only {len(row)} columns, expected 13: {row}")
                    continue
                    
                tier = row[0]
                total_recommendations = row[1]
                unique_users = row[2]
                avg_recommendation_score = row[3] or 0
                avg_salary_potential = row[4] or 0
                avg_success_probability = row[5] or 0
                total_engagements = row[6] or 0
                engaged_recommendations = row[7] or 0
                applications_started = row[8] or 0
                successful_applications = row[9] or 0
                offers_accepted = row[10] or 0
                avg_final_salary = row[11] or 0
                avg_interview_rounds = row[12] or 0
                
                # Calculate rates
                engagement_rate = (engaged_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0
                application_rate = (applications_started / total_recommendations * 100) if total_recommendations > 0 else 0
                success_rate = (successful_applications / applications_started * 100) if applications_started > 0 else 0
                offer_acceptance_rate = (offers_accepted / successful_applications * 100) if successful_applications > 0 else 0
                
                tier_metrics[tier] = {
                    'total_recommendations': total_recommendations,
                    'unique_users': unique_users,
                    'avg_recommendation_score': round(avg_recommendation_score, 2),
                    'avg_salary_potential': round(avg_salary_potential, 2),
                    'avg_success_probability': round(avg_success_probability, 2),
                    'total_engagements': total_engagements,
                    'engagement_rate': round(engagement_rate, 2),
                    'application_rate': round(application_rate, 2),
                    'success_rate': round(success_rate, 2),
                    'offer_acceptance_rate': round(offer_acceptance_rate, 2),
                    'avg_final_salary': round(avg_final_salary, 2),
                    'avg_interview_rounds': round(avg_interview_rounds, 1)
                }
            
            conn.close()
            
            return {
                'analysis_period_days': days,
                'tier_metrics': tier_metrics,
                'overall_metrics': self._calculate_overall_metrics(tier_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendation effectiveness by tier: {e}")
            return {}
    
    def _calculate_overall_metrics(self, tier_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall effectiveness metrics"""
        if not tier_metrics:
            return {}
        
        total_recommendations = sum(tier.get('total_recommendations', 0) for tier in tier_metrics.values())
        total_engagements = sum(tier.get('total_engagements', 0) for tier in tier_metrics.values())
        total_applications = sum(tier.get('applications_started', 0) for tier in tier_metrics.values())
        total_successful = sum(tier.get('successful_applications', 0) for tier in tier_metrics.values())
        
        return {
            'total_recommendations': total_recommendations,
            'overall_engagement_rate': round((total_engagements / total_recommendations * 100) if total_recommendations > 0 else 0, 2),
            'overall_application_rate': round((total_applications / total_recommendations * 100) if total_recommendations > 0 else 0, 2),
            'overall_success_rate': round((total_successful / total_applications * 100) if total_applications > 0 else 0, 2)
        }
    
    def get_user_recommendation_performance(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get recommendation performance metrics for a specific user
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict containing user performance metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get user's recommendation metrics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_recommendations,
                    COUNT(DISTINCT jr.tier) as tiers_used,
                    AVG(jr.recommendation_score) as avg_recommendation_score,
                    COUNT(re.recommendation_id) as total_engagements,
                    COUNT(ao.application_id) as applications_started,
                    COUNT(CASE WHEN ao.application_status IN ('offer_received', 'offer_accepted') THEN 1 END) as successful_applications,
                    COUNT(CASE WHEN ao.application_status = 'offer_accepted' THEN 1 END) as offers_accepted,
                    AVG(ao.final_salary) as avg_final_salary
                FROM job_recommendations jr
                LEFT JOIN recommendation_engagement re ON jr.recommendation_id = re.recommendation_id
                LEFT JOIN application_outcomes ao ON jr.recommendation_id = ao.recommendation_id
                WHERE jr.user_id = ? AND jr.created_at >= ?
            ''', (user_id, start_date))
            
            result = cursor.fetchone()
            if not result:
                return {'user_id': user_id, 'message': 'No recommendations found'}
            
            total_recommendations, tiers_used, avg_recommendation_score, total_engagements, applications_started, successful_applications, offers_accepted, avg_final_salary = result
            
            # Get user feedback
            cursor.execute('''
                SELECT 
                    AVG(rating) as avg_rating,
                    COUNT(*) as feedback_count
                FROM user_feedback 
                WHERE user_id = ? AND timestamp >= ?
            ''', (user_id, start_date))
            
            feedback_result = cursor.fetchone()
            avg_rating = feedback_result[0] if feedback_result[0] else 0
            feedback_count = feedback_result[1] if feedback_result[1] else 0
            
            # Calculate rates
            engagement_rate = (total_engagements / total_recommendations * 100) if total_recommendations > 0 else 0
            application_rate = (applications_started / total_recommendations * 100) if total_recommendations > 0 else 0
            success_rate = (successful_applications / applications_started * 100) if applications_started > 0 else 0
            offer_acceptance_rate = (offers_accepted / successful_applications * 100) if successful_applications > 0 else 0
            
            conn.close()
            
            return {
                'user_id': user_id,
                'analysis_period_days': days,
                'total_recommendations': total_recommendations,
                'tiers_used': tiers_used,
                'avg_recommendation_score': round(avg_recommendation_score or 0, 2),
                'engagement_rate': round(engagement_rate, 2),
                'application_rate': round(application_rate, 2),
                'success_rate': round(success_rate, 2),
                'offer_acceptance_rate': round(offer_acceptance_rate, 2),
                'avg_final_salary': round(avg_final_salary or 0, 2),
                'avg_rating': round(avg_rating, 2),
                'feedback_count': feedback_count
            }
            
        except Exception as e:
            logger.error(f"Error getting user recommendation performance: {e}")
            return {}
    
    def get_recommendation_quality_metrics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get recommendation quality metrics and insights
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing quality metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get quality metrics
            cursor.execute('''
                SELECT 
                    AVG(jr.recommendation_score) as avg_score,
                    MIN(jr.recommendation_score) as min_score,
                    MAX(jr.recommendation_score) as max_score,
                    AVG(jr.salary_increase_potential) as avg_salary_potential,
                    AVG(jr.success_probability) as avg_success_probability,
                    AVG(jr.skills_gap_score) as avg_skills_gap,
                    AVG(jr.company_culture_fit) as avg_culture_fit,
                    AVG(jr.career_advancement_potential) as avg_advancement_potential,
                    COUNT(*) as total_recommendations,
                    COUNT(CASE WHEN jr.recommendation_score >= 8.0 THEN 1 END) as high_quality_recommendations,
                    COUNT(CASE WHEN jr.recommendation_score < 5.0 THEN 1 END) as low_quality_recommendations
                FROM job_recommendations jr
                WHERE jr.created_at >= ?
            ''', (start_date,))
            
            quality_result = cursor.fetchone()
            
            # Get engagement correlation
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
                ORDER BY jr.recommendation_score
            ''', (start_date,))
            
            score_engagement_data = cursor.fetchall()
            
            # Calculate correlation between score and engagement
            scores = [row[0] for row in score_engagement_data]
            engagements = [row[1] for row in score_engagement_data]
            applications = [row[2] for row in score_engagement_data]
            
            score_engagement_correlation = self._calculate_correlation(scores, engagements)
            score_application_correlation = self._calculate_correlation(scores, applications)
            
            conn.close()
            
            if quality_result:
                total_recommendations = quality_result[8]
                high_quality = quality_result[9]
                low_quality = quality_result[10]
                
                return {
                    'analysis_period_days': days,
                    'score_metrics': {
                        'avg_score': round(quality_result[0] or 0, 2),
                        'min_score': round(quality_result[1] or 0, 2),
                        'max_score': round(quality_result[2] or 0, 2),
                        'high_quality_percentage': round((high_quality / total_recommendations * 100) if total_recommendations > 0 else 0, 2),
                        'low_quality_percentage': round((low_quality / total_recommendations * 100) if total_recommendations > 0 else 0, 2)
                    },
                    'potential_metrics': {
                        'avg_salary_potential': round(quality_result[3] or 0, 2),
                        'avg_success_probability': round(quality_result[4] or 0, 2),
                        'avg_skills_gap': round(quality_result[5] or 0, 2),
                        'avg_culture_fit': round(quality_result[6] or 0, 2),
                        'avg_advancement_potential': round(quality_result[7] or 0, 2)
                    },
                    'correlation_metrics': {
                        'score_engagement_correlation': round(score_engagement_correlation, 3),
                        'score_application_correlation': round(score_application_correlation, 3)
                    }
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting recommendation quality metrics: {e}")
            return {}
    
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
    
    def get_top_performing_recommendations(
        self,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top performing recommendations based on engagement and success
        
        Args:
            days: Number of days to analyze
            limit: Maximum number of recommendations to return
            
        Returns:
            List of top performing recommendations
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT 
                    jr.recommendation_id,
                    jr.job_id,
                    jr.tier,
                    jr.recommendation_score,
                    jr.salary_increase_potential,
                    COUNT(re.recommendation_id) as engagement_count,
                    COUNT(ao.application_id) as application_count,
                    COUNT(CASE WHEN ao.application_status = 'offer_accepted' THEN 1 END) as success_count,
                    AVG(ao.final_salary) as avg_final_salary
                FROM job_recommendations jr
                LEFT JOIN recommendation_engagement re ON jr.recommendation_id = re.recommendation_id
                LEFT JOIN application_outcomes ao ON jr.recommendation_id = ao.recommendation_id
                WHERE jr.created_at >= ?
                GROUP BY jr.recommendation_id
                ORDER BY 
                    (COUNT(re.recommendation_id) * 0.3 + 
                     COUNT(ao.application_id) * 0.4 + 
                     COUNT(CASE WHEN ao.application_status = 'offer_accepted' THEN 1 END) * 0.3) DESC,
                    jr.recommendation_score DESC
                LIMIT ?
            ''', (start_date, limit))
            
            top_recommendations = []
            for row in cursor.fetchall():
                top_recommendations.append({
                    'recommendation_id': row[0],
                    'job_id': row[1],
                    'tier': row[2],
                    'recommendation_score': round(row[3], 2),
                    'salary_increase_potential': round(row[4], 2),
                    'engagement_count': row[5],
                    'application_count': row[6],
                    'success_count': row[7],
                    'avg_final_salary': round(row[8] or 0, 2)
                })
            
            conn.close()
            return top_recommendations
            
        except Exception as e:
            logger.error(f"Error getting top performing recommendations: {e}")
            return []
