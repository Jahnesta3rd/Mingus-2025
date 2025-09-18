#!/usr/bin/env python3
"""
Risk Analytics Tracker for Career Protection System

This module provides comprehensive tracking and analysis of user risk assessments,
interventions, and career protection outcomes to measure the effectiveness of
risk-based career protection strategies.

Features:
- User risk assessment tracking and analysis
- Risk intervention management and effectiveness measurement
- Career protection outcome tracking
- Risk trend analysis and pattern detection
- Success story tracking for risk-based interventions
- Real-time risk analytics and alerting
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class InterventionType(Enum):
    """Types of risk interventions"""
    EARLY_WARNING = "early_warning"
    JOB_SEARCH_ACCELERATION = "job_search_acceleration"
    SKILL_DEVELOPMENT = "skill_development"
    NETWORK_EXPANSION = "network_expansion"
    EMERGENCY_UNLOCK = "emergency_unlock"
    CAREER_COACHING = "career_coaching"
    RESUME_OPTIMIZATION = "resume_optimization"
    INTERVIEW_PREP = "interview_prep"

class OutcomeType(Enum):
    """Types of career protection outcomes"""
    SUCCESSFUL_TRANSITION = "successful_transition"
    UNEMPLOYMENT_PREVENTED = "unemployment_prevented"
    SALARY_INCREASED = "salary_increased"
    JOB_SECURITY_IMPROVED = "job_security_improved"
    CAREER_ADVANCEMENT = "career_advancement"
    SKILL_DEVELOPMENT = "skill_development"
    NETWORK_EXPANSION = "network_expansion"
    EARLY_WARNING_SUCCESS = "early_warning_success"
    INTERVENTION_SUCCESS = "intervention_success"

@dataclass
class RiskAssessment:
    """Data class for user risk assessment"""
    user_id: str
    assessment_date: datetime
    risk_level: str
    risk_score: float
    risk_factors: Dict[str, Any]
    industry_risk_score: Optional[float] = None
    company_risk_score: Optional[float] = None
    role_risk_score: Optional[float] = None
    market_risk_score: Optional[float] = None
    personal_risk_score: Optional[float] = None
    assessment_confidence: Optional[float] = None
    next_assessment_date: Optional[datetime] = None
    intervention_triggered: bool = False
    intervention_date: Optional[datetime] = None

@dataclass
class RiskIntervention:
    """Data class for risk intervention"""
    user_id: str
    risk_assessment_id: int
    intervention_type: str
    intervention_date: datetime
    intervention_status: str
    intervention_data: Dict[str, Any]
    success_metrics: Dict[str, Any]
    completion_date: Optional[datetime] = None
    effectiveness_score: Optional[float] = None
    user_response: Optional[Dict[str, Any]] = None

@dataclass
class CareerProtectionOutcome:
    """Data class for career protection outcome"""
    user_id: str
    risk_assessment_id: int
    intervention_id: Optional[int]
    outcome_type: str
    outcome_date: datetime
    outcome_details: Dict[str, Any]
    salary_change: Optional[float] = None
    job_security_improvement: Optional[float] = None
    time_to_new_role: Optional[int] = None
    satisfaction_score: Optional[int] = None
    would_recommend: Optional[bool] = None
    success_factors: Optional[Dict[str, Any]] = None
    verification_status: str = "unverified"
    verified_date: Optional[datetime] = None

class RiskAnalyticsTracker:
    """
    Comprehensive risk analytics tracker for career protection system.
    
    Tracks user risk assessments, interventions, and outcomes to measure
    the effectiveness of risk-based career protection strategies.
    """
    
    def __init__(self, db_path: str = "backend/analytics/recommendation_analytics.db"):
        """Initialize the risk analytics tracker"""
        self.db_path = db_path
        self._init_database()
        logger.info("RiskAnalyticsTracker initialized successfully")
    
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
            logger.info("Risk analytics database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing risk analytics database: {e}")
            raise
    
    def assess_user_risk(
        self,
        user_id: str,
        risk_factors: Dict[str, Any],
        industry_risk_score: Optional[float] = None,
        company_risk_score: Optional[float] = None,
        role_risk_score: Optional[float] = None,
        market_risk_score: Optional[float] = None,
        personal_risk_score: Optional[float] = None,
        assessment_confidence: Optional[float] = None
    ) -> int:
        """
        Assess user career risk and create risk assessment record
        
        Args:
            user_id: User identifier
            risk_factors: Dictionary of identified risk factors
            industry_risk_score: Industry-specific risk score (0-100)
            company_risk_score: Company-specific risk score (0-100)
            role_risk_score: Role-specific risk score (0-100)
            market_risk_score: Market-specific risk score (0-100)
            personal_risk_score: Personal risk score (0-100)
            assessment_confidence: Confidence in assessment (0-1)
            
        Returns:
            int: Risk assessment ID
        """
        try:
            # Calculate overall risk score
            risk_scores = [score for score in [
                industry_risk_score, company_risk_score, role_risk_score,
                market_risk_score, personal_risk_score
            ] if score is not None]
            
            if risk_scores:
                overall_risk_score = np.mean(risk_scores)
            else:
                # Fallback calculation based on risk factors
                overall_risk_score = self._calculate_risk_score_from_factors(risk_factors)
            
            # Determine risk level
            if overall_risk_score >= 80:
                risk_level = RiskLevel.CRITICAL.value
            elif overall_risk_score >= 60:
                risk_level = RiskLevel.HIGH.value
            elif overall_risk_score >= 40:
                risk_level = RiskLevel.MEDIUM.value
            else:
                risk_level = RiskLevel.LOW.value
            
            # Calculate next assessment date
            next_assessment_date = datetime.now() + timedelta(days=self._get_assessment_interval(risk_level))
            
            assessment = RiskAssessment(
                user_id=user_id,
                assessment_date=datetime.now(),
                risk_level=risk_level,
                risk_score=overall_risk_score,
                risk_factors=risk_factors,
                industry_risk_score=industry_risk_score,
                company_risk_score=company_risk_score,
                role_risk_score=role_risk_score,
                market_risk_score=market_risk_score,
                personal_risk_score=personal_risk_score,
                assessment_confidence=assessment_confidence,
                next_assessment_date=next_assessment_date
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_risk_assessments (
                    user_id, assessment_date, risk_level, risk_score, risk_factors,
                    industry_risk_score, company_risk_score, role_risk_score,
                    market_risk_score, personal_risk_score, assessment_confidence,
                    next_assessment_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                assessment.user_id, assessment.assessment_date, assessment.risk_level,
                assessment.risk_score, json.dumps(assessment.risk_factors),
                assessment.industry_risk_score, assessment.company_risk_score,
                assessment.role_risk_score, assessment.market_risk_score,
                assessment.personal_risk_score, assessment.assessment_confidence,
                assessment.next_assessment_date
            ))
            
            assessment_id = cursor.lastrowid
            
            # Trigger intervention if high risk
            if risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]:
                self._trigger_risk_intervention(assessment_id, user_id, risk_level)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Risk assessment created for user {user_id}: {risk_level} ({overall_risk_score:.1f})")
            return assessment_id
            
        except Exception as e:
            logger.error(f"Error assessing user risk: {e}")
            raise
    
    def trigger_intervention(
        self,
        user_id: str,
        risk_assessment_id: int,
        intervention_type: str,
        intervention_data: Dict[str, Any]
    ) -> int:
        """
        Trigger a risk intervention for a user
        
        Args:
            user_id: User identifier
            risk_assessment_id: Associated risk assessment ID
            intervention_type: Type of intervention
            intervention_data: Intervention-specific data
            
        Returns:
            int: Intervention ID
        """
        try:
            intervention = RiskIntervention(
                user_id=user_id,
                risk_assessment_id=risk_assessment_id,
                intervention_type=intervention_type,
                intervention_date=datetime.now(),
                intervention_status="triggered",
                intervention_data=intervention_data,
                success_metrics={}
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO risk_interventions (
                    user_id, risk_assessment_id, intervention_type, intervention_date,
                    intervention_status, intervention_data, success_metrics
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                intervention.user_id, intervention.risk_assessment_id,
                intervention.intervention_type, intervention.intervention_date,
                intervention.intervention_status, json.dumps(intervention.intervention_data),
                json.dumps(intervention.success_metrics)
            ))
            
            intervention_id = cursor.lastrowid
            
            # Update risk assessment to mark intervention triggered
            cursor.execute('''
                UPDATE user_risk_assessments 
                SET intervention_triggered = TRUE, intervention_date = ?
                WHERE id = ?
            ''', (intervention.intervention_date, risk_assessment_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Intervention triggered for user {user_id}: {intervention_type}")
            return intervention_id
            
        except Exception as e:
            logger.error(f"Error triggering intervention: {e}")
            raise
    
    def update_intervention_status(
        self,
        intervention_id: int,
        status: str,
        effectiveness_score: Optional[float] = None,
        user_response: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update intervention status and effectiveness
        
        Args:
            intervention_id: Intervention ID
            status: New intervention status
            effectiveness_score: Effectiveness score (0-10)
            user_response: User feedback on intervention
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            completion_date = datetime.now() if status == "completed" else None
            
            cursor.execute('''
                UPDATE risk_interventions 
                SET intervention_status = ?, effectiveness_score = ?, 
                    user_response = ?, completion_date = ?
                WHERE id = ?
            ''', (
                status, effectiveness_score, 
                json.dumps(user_response) if user_response else None,
                completion_date, intervention_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Intervention {intervention_id} status updated to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating intervention status: {e}")
            return False
    
    def track_career_protection_outcome(
        self,
        user_id: str,
        risk_assessment_id: int,
        outcome_type: str,
        outcome_details: Dict[str, Any],
        intervention_id: Optional[int] = None,
        salary_change: Optional[float] = None,
        job_security_improvement: Optional[float] = None,
        time_to_new_role: Optional[int] = None,
        satisfaction_score: Optional[int] = None,
        would_recommend: Optional[bool] = None,
        success_factors: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Track career protection outcome
        
        Args:
            user_id: User identifier
            risk_assessment_id: Associated risk assessment ID
            outcome_type: Type of outcome achieved
            outcome_details: Detailed outcome information
            intervention_id: Associated intervention ID (optional)
            salary_change: Salary change amount
            job_security_improvement: Job security improvement score
            time_to_new_role: Days to find new role
            satisfaction_score: User satisfaction (1-5)
            would_recommend: Would recommend to others
            success_factors: Factors that contributed to success
            
        Returns:
            int: Outcome ID
        """
        try:
            outcome = CareerProtectionOutcome(
                user_id=user_id,
                risk_assessment_id=risk_assessment_id,
                intervention_id=intervention_id,
                outcome_type=outcome_type,
                outcome_date=datetime.now(),
                outcome_details=outcome_details,
                salary_change=salary_change,
                job_security_improvement=job_security_improvement,
                time_to_new_role=time_to_new_role,
                satisfaction_score=satisfaction_score,
                would_recommend=would_recommend,
                success_factors=success_factors
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO career_protection_outcomes (
                    user_id, risk_assessment_id, intervention_id, outcome_type,
                    outcome_date, outcome_details, salary_change, job_security_improvement,
                    time_to_new_role, satisfaction_score, would_recommend, success_factors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                outcome.user_id, outcome.risk_assessment_id, outcome.intervention_id,
                outcome.outcome_type, outcome.outcome_date, json.dumps(outcome.outcome_details),
                outcome.salary_change, outcome.job_security_improvement,
                outcome.time_to_new_role, outcome.satisfaction_score,
                outcome.would_recommend, json.dumps(outcome.success_factors) if outcome.success_factors else None
            ))
            
            outcome_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Career protection outcome tracked for user {user_id}: {outcome_type}")
            return outcome_id
            
        except Exception as e:
            logger.error(f"Error tracking career protection outcome: {e}")
            raise
    
    def log_success_story(
        self,
        user_id: str,
        story_type: str,
        story_title: str,
        story_description: str,
        original_risk_factors: Dict[str, Any],
        intervention_timeline: Dict[str, Any],
        outcome_details: Dict[str, Any],
        user_satisfaction: Optional[int] = None,
        would_recommend: Optional[bool] = None,
        testimonial_text: Optional[str] = None
    ) -> int:
        """
        Log a risk-based success story
        
        Args:
            user_id: User identifier
            story_type: Type of success story
            story_title: Story title
            story_description: Story description
            original_risk_factors: Original risk factors faced
            intervention_timeline: Timeline of interventions
            outcome_details: Details of successful outcome
            user_satisfaction: User satisfaction score (1-5)
            would_recommend: Would recommend to others
            testimonial_text: User testimonial
            
        Returns:
            int: Success story ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO risk_success_stories (
                    user_id, story_type, story_title, story_description,
                    original_risk_factors, intervention_timeline, outcome_details,
                    user_satisfaction, would_recommend, testimonial_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, story_type, story_title, story_description,
                json.dumps(original_risk_factors), json.dumps(intervention_timeline),
                json.dumps(outcome_details), user_satisfaction, would_recommend, testimonial_text
            ))
            
            story_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Success story logged for user {user_id}: {story_type}")
            return story_id
            
        except Exception as e:
            logger.error(f"Error logging success story: {e}")
            raise
    
    def get_career_protection_metrics(
        self,
        time_period: str = 'last_30_days'
    ) -> Dict[str, Any]:
        """
        Get comprehensive career protection metrics
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            Dict containing career protection metrics
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
            
            # Get high-risk users count
            cursor.execute('''
                SELECT COUNT(*) as high_risk_users
                FROM user_risk_assessments 
                WHERE assessment_date >= ? AND risk_level IN ('high', 'critical')
            ''', (start_date,))
            high_risk_users = cursor.fetchone()[0]
            
            # Get successful transitions
            cursor.execute('''
                SELECT COUNT(*) as successful_transitions
                FROM career_protection_outcomes 
                WHERE outcome_date >= ? AND outcome_type = 'successful_transition'
            ''', (start_date,))
            successful_transitions = cursor.fetchone()[0]
            
            # Get unemployment prevented
            cursor.execute('''
                SELECT COUNT(*) as unemployment_prevented
                FROM career_protection_outcomes 
                WHERE outcome_date >= ? AND outcome_type = 'unemployment_prevented'
            ''', (start_date,))
            unemployment_prevented = cursor.fetchone()[0]
            
            # Get average advance warning time
            cursor.execute('''
                SELECT AVG(julianday(cpo.outcome_date) - julianday(ura.assessment_date)) as avg_warning_days
                FROM user_risk_assessments ura
                JOIN career_protection_outcomes cpo ON ura.id = cpo.risk_assessment_id
                WHERE ura.assessment_date >= ? AND cpo.outcome_type = 'successful_transition'
            ''', (start_date,))
            avg_warning_days = cursor.fetchone()[0] or 0
            
            # Get income protection rate
            cursor.execute('''
                SELECT 
                    COUNT(CASE WHEN salary_change >= 0 THEN 1 END) * 100.0 / COUNT(*) as income_protection_rate
                FROM career_protection_outcomes 
                WHERE outcome_date >= ? AND salary_change IS NOT NULL
            ''', (start_date,))
            income_protection_rate = cursor.fetchone()[0] or 0
            
            # Calculate overall success rate
            overall_success_rate = (successful_transitions / high_risk_users * 100) if high_risk_users > 0 else 0
            
            conn.close()
            
            return {
                'time_period': time_period,
                'users_at_high_risk': high_risk_users,
                'successful_transitions': successful_transitions,
                'unemployment_prevented': unemployment_prevented,
                'average_advance_warning_days': round(avg_warning_days, 1),
                'income_protection_rate': round(income_protection_rate, 2),
                'overall_success_rate': round(overall_success_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting career protection metrics: {e}")
            return {}
    
    def get_risk_success_stories(self, limit: int = 10, story_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves approved risk success stories.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = '''
            SELECT user_id, story_type, story_title, story_description,
                   original_risk_factors, intervention_timeline, outcome_details,
                   user_satisfaction, would_recommend, testimonial_text,
                   created_date
            FROM risk_success_stories
            WHERE approval_status = 'approved'
        '''
        params = []
        if story_type:
            query += ' AND story_type = ?'
            params.append(story_type)

        query += ' ORDER BY created_date DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)

        stories = []
        for row in cursor.fetchall():
            stories.append({
                'user_id': row[0],
                'story_type': row[1],
                'story_title': row[2],
                'story_description': row[3],
                'original_risk_factors': json.loads(row[4]),
                'intervention_timeline': json.loads(row[5]),
                'outcome_details': json.loads(row[6]),
                'user_satisfaction': row[7],
                'would_recommend': bool(row[8]),
                'testimonial_text': row[9],
                'created_date': row[10]
            })
        conn.close()
        return stories
    
    def get_intervention_effectiveness(
        self,
        time_period: str = 'last_30_days'
    ) -> Dict[str, Any]:
        """
        Get intervention effectiveness metrics
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            Dict containing intervention effectiveness metrics
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
            
            # Get intervention effectiveness by type
            cursor.execute('''
                SELECT 
                    intervention_type,
                    COUNT(*) as total_interventions,
                    COUNT(CASE WHEN intervention_status = 'completed' THEN 1 END) as completed_interventions,
                    AVG(effectiveness_score) as avg_effectiveness_score,
                    COUNT(CASE WHEN intervention_status = 'completed' AND effectiveness_score >= 7 THEN 1 END) as effective_interventions
                FROM risk_interventions 
                WHERE intervention_date >= ?
                GROUP BY intervention_type
                ORDER BY avg_effectiveness_score DESC
            ''', (start_date,))
            
            intervention_metrics = {}
            for row in cursor.fetchall():
                intervention_metrics[row[0]] = {
                    'total_interventions': row[1],
                    'completed_interventions': row[2],
                    'avg_effectiveness_score': round(row[3] or 0, 2),
                    'effective_interventions': row[4],
                    'completion_rate': round((row[2] / row[1] * 100) if row[1] > 0 else 0, 2),
                    'effectiveness_rate': round((row[4] / row[2] * 100) if row[2] > 0 else 0, 2)
                }
            
            conn.close()
            
            return {
                'time_period': time_period,
                'intervention_metrics': intervention_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting intervention effectiveness: {e}")
            return {}
    
    def get_risk_trend_analysis(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get risk trend analysis
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing risk trend analysis
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get daily risk level distribution
            cursor.execute('''
                SELECT 
                    DATE(assessment_date) as assessment_date,
                    risk_level,
                    COUNT(*) as count
                FROM user_risk_assessments 
                WHERE assessment_date >= ?
                GROUP BY DATE(assessment_date), risk_level
                ORDER BY assessment_date DESC, risk_level
            ''', (start_date,))
            
            risk_trends = {}
            for row in cursor.fetchall():
                date_str = row[0]
                if date_str not in risk_trends:
                    risk_trends[date_str] = {}
                risk_trends[date_str][row[1]] = row[2]
            
            # Get risk factor frequency
            cursor.execute('''
                SELECT 
                    json_extract(risk_factors, '$.primary_factor') as primary_factor,
                    COUNT(*) as frequency
                FROM user_risk_assessments 
                WHERE assessment_date >= ? AND risk_level IN ('high', 'critical')
                GROUP BY primary_factor
                ORDER BY frequency DESC
                LIMIT 10
            ''', (start_date,))
            
            top_risk_factors = {}
            for row in cursor.fetchall():
                if row[0]:
                    top_risk_factors[row[0]] = row[1]
            
            conn.close()
            
            return {
                'analysis_period_days': days,
                'risk_trends': risk_trends,
                'top_risk_factors': top_risk_factors
            }
            
        except Exception as e:
            logger.error(f"Error getting risk trend analysis: {e}")
            return {}
    
    def _calculate_risk_score_from_factors(self, risk_factors: Dict[str, Any]) -> float:
        """Calculate risk score from risk factors"""
        # Simple scoring based on common risk factors
        score = 0
        
        # Industry risk factors
        if risk_factors.get('industry_volatility', False):
            score += 20
        if risk_factors.get('industry_downsizing', False):
            score += 25
        
        # Company risk factors
        if risk_factors.get('company_financial_trouble', False):
            score += 30
        if risk_factors.get('company_layoffs', False):
            score += 25
        if risk_factors.get('company_merger', False):
            score += 15
        
        # Role risk factors
        if risk_factors.get('role_redundancy', False):
            score += 20
        if risk_factors.get('role_automation_risk', False):
            score += 15
        if risk_factors.get('role_outsourcing_risk', False):
            score += 20
        
        # Personal risk factors
        if risk_factors.get('limited_skills', False):
            score += 15
        if risk_factors.get('age_discrimination_risk', False):
            score += 10
        if risk_factors.get('location_risk', False):
            score += 10
        
        return min(score, 100)
    
    def _get_assessment_interval(self, risk_level: str) -> int:
        """Get assessment interval based on risk level"""
        intervals = {
            RiskLevel.LOW.value: 90,
            RiskLevel.MEDIUM.value: 60,
            RiskLevel.HIGH.value: 30,
            RiskLevel.CRITICAL.value: 14
        }
        return intervals.get(risk_level, 30)
    
    def _trigger_risk_intervention(self, assessment_id: int, user_id: str, risk_level: str):
        """Trigger automatic risk intervention for high-risk users"""
        try:
            # Determine intervention type based on risk level and factors
            intervention_type = "early_warning" if risk_level == RiskLevel.HIGH.value else "emergency_unlock"
            
            intervention_data = {
                'triggered_by': 'automatic_assessment',
                'risk_level': risk_level,
                'priority': 'high' if risk_level == RiskLevel.CRITICAL.value else 'medium'
            }
            
            self.trigger_intervention(
                user_id=user_id,
                risk_assessment_id=assessment_id,
                intervention_type=intervention_type,
                intervention_data=intervention_data
            )
            
        except Exception as e:
            logger.error(f"Error triggering automatic intervention: {e}")
