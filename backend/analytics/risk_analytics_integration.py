#!/usr/bin/env python3
"""
Risk-Based Analytics Integration for Career Protection

This module extends the existing AnalyticsIntegration to provide comprehensive
risk-based career protection analytics, including risk assessment tracking,
recommendation triggering, and outcome measurement.

Features:
- Risk event analytics tracking
- Risk-based user journey analytics
- Risk threshold optimization with A/B testing
- Career protection outcome measurement
- Risk prediction accuracy validation
- Emergency unlock usage tracking
- Risk communication effectiveness analysis
"""

import asyncio
import logging
import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import existing analytics components
from .analytics_integration import AnalyticsIntegration
from .user_behavior_analytics import UserBehaviorAnalytics
from .recommendation_effectiveness import RecommendationEffectiveness
from .success_metrics import SuccessMetrics
from .ab_testing_framework import ABTestFramework
from .risk_ab_testing_framework import RiskABTestFramework

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskEventType(Enum):
    """Types of risk-related events to track"""
    RISK_ASSESSMENT_COMPLETED = "risk_assessment_completed"
    RISK_RECOMMENDATION_TRIGGERED = "risk_recommendation_triggered"
    EMERGENCY_UNLOCK_USAGE = "emergency_unlock_usage"
    RISK_PREDICTION_ACCURACY = "risk_prediction_accuracy"
    CAREER_PROTECTION_OUTCOME = "career_protection_outcome"
    RISK_ALERT_SENT = "risk_alert_sent"
    RISK_ALERT_ACKNOWLEDGED = "risk_alert_acknowledged"
    PROACTIVE_ACTION_TAKEN = "proactive_action_taken"

class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class OutcomeType(Enum):
    """Career protection outcome types"""
    LAID_OFF = "laid_off"
    JOB_SAVED = "job_saved"
    PROACTIVE_SWITCH = "proactive_switch"
    PROMOTION_RECEIVED = "promotion_received"
    SKILLS_UPGRADED = "skills_upgraded"
    NETWORK_EXPANDED = "network_expanded"

@dataclass
class RiskAssessmentData:
    """Data structure for risk assessment information"""
    user_id: str
    assessment_type: str  # 'ai_risk', 'layoff_risk', 'income_risk'
    overall_risk: float
    risk_triggers: List[str]
    risk_breakdown: Dict[str, Any]
    timeline_urgency: str  # 'immediate', '3_months', '6_months', '1_year'
    assessment_timestamp: datetime
    confidence_score: float
    risk_factors: Dict[str, float]

@dataclass
class RiskRecommendationData:
    """Data structure for risk-triggered recommendations"""
    user_id: str
    trigger_type: str
    risk_score: float
    recommendations_generated: int
    recommendation_tiers: List[str]
    emergency_unlock_granted: bool
    timeline_urgency: str
    intervention_timestamp: datetime
    success_probability: float

@dataclass
class RiskOutcomeData:
    """Data structure for risk prediction outcomes"""
    user_id: str
    predicted_risk_score: float
    predicted_timeline: str
    actual_outcome: str
    outcome_timeline_days: int
    prediction_accuracy: float
    outcome_timestamp: datetime
    outcome_details: Dict[str, Any]

class RiskAnalyticsTracker:
    """Specialized tracker for risk-related analytics events"""
    
    def __init__(self, db_path: str):
        """Initialize the risk analytics tracker"""
        self.db_path = db_path
        self._init_risk_tables()
    
    def _init_risk_tables(self):
        """Initialize risk-specific database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Risk assessments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    assessment_type TEXT NOT NULL,
                    overall_risk REAL NOT NULL,
                    risk_triggers TEXT NOT NULL,
                    risk_breakdown TEXT NOT NULL,
                    timeline_urgency TEXT NOT NULL,
                    assessment_timestamp DATETIME NOT NULL,
                    confidence_score REAL NOT NULL,
                    risk_factors TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Risk recommendations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    recommendations_generated INTEGER NOT NULL,
                    recommendation_tiers TEXT NOT NULL,
                    emergency_unlock_granted BOOLEAN NOT NULL,
                    timeline_urgency TEXT NOT NULL,
                    intervention_timestamp DATETIME NOT NULL,
                    success_probability REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Risk outcomes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    predicted_risk_score REAL NOT NULL,
                    predicted_timeline TEXT NOT NULL,
                    actual_outcome TEXT NOT NULL,
                    outcome_timeline_days INTEGER NOT NULL,
                    prediction_accuracy REAL NOT NULL,
                    outcome_timestamp DATETIME NOT NULL,
                    outcome_details TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Risk journey flow table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_journey_flow (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    flow_step TEXT NOT NULL,
                    step_timestamp DATETIME NOT NULL,
                    step_data TEXT NOT NULL,
                    time_to_next_step INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Risk A/B test results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_ab_test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    variant_id TEXT NOT NULL,
                    risk_threshold REAL NOT NULL,
                    recommendation_timing TEXT NOT NULL,
                    user_response TEXT NOT NULL,
                    outcome_achieved TEXT,
                    test_timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    async def log_risk_intervention(self, user_id: str, risk_data: RiskAssessmentData, recommendations: Dict[str, Any]) -> str:
        """Log a risk intervention event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Log risk assessment
                cursor.execute('''
                    INSERT INTO risk_assessments 
                    (user_id, assessment_type, overall_risk, risk_triggers, risk_breakdown,
                     timeline_urgency, assessment_timestamp, confidence_score, risk_factors)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    risk_data.assessment_type,
                    risk_data.overall_risk,
                    json.dumps(risk_data.risk_triggers),
                    json.dumps(risk_data.risk_breakdown),
                    risk_data.timeline_urgency,
                    risk_data.assessment_timestamp,
                    risk_data.confidence_score,
                    json.dumps(risk_data.risk_factors)
                ))
                
                assessment_id = cursor.lastrowid
                
                # Log risk recommendation
                cursor.execute('''
                    INSERT INTO risk_recommendations 
                    (user_id, trigger_type, risk_score, recommendations_generated, 
                     recommendation_tiers, emergency_unlock_granted, timeline_urgency,
                     intervention_timestamp, success_probability)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    'risk_assessment',
                    risk_data.overall_risk,
                    len(recommendations.get('jobs', [])),
                    json.dumps([r.get('tier', 'optimal') for r in recommendations.get('jobs', [])]),
                    risk_data.overall_risk >= 0.7,
                    risk_data.timeline_urgency,
                    datetime.now(),
                    recommendations.get('success_probability', 0.0)
                ))
                
                conn.commit()
                logger.info(f"Logged risk intervention for user {user_id}")
                return str(assessment_id)
                
        except Exception as e:
            logger.error(f"Error logging risk intervention: {e}")
            raise
    
    async def log_prediction_accuracy(self, accuracy_data: RiskOutcomeData) -> bool:
        """Log risk prediction accuracy data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO risk_outcomes 
                    (user_id, predicted_risk_score, predicted_timeline, actual_outcome,
                     outcome_timeline_days, prediction_accuracy, outcome_timestamp, outcome_details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    accuracy_data.user_id,
                    accuracy_data.predicted_risk_score,
                    accuracy_data.predicted_timeline,
                    accuracy_data.actual_outcome,
                    accuracy_data.outcome_timeline_days,
                    accuracy_data.prediction_accuracy,
                    accuracy_data.outcome_timestamp,
                    json.dumps(accuracy_data.outcome_details)
                ))
                
                conn.commit()
                logger.info(f"Logged prediction accuracy for user {accuracy_data.user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error logging prediction accuracy: {e}")
            return False
    
    async def track_risk_journey_step(self, user_id: str, session_id: str, flow_step: str, step_data: Dict[str, Any], time_to_next: Optional[int] = None) -> bool:
        """Track a step in the risk-based user journey"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO risk_journey_flow 
                    (user_id, session_id, flow_step, step_timestamp, step_data, time_to_next_step)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    session_id,
                    flow_step,
                    datetime.now(),
                    json.dumps(step_data),
                    time_to_next
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error tracking risk journey step: {e}")
            return False

class RiskBasedSuccessMetrics:
    """Success metrics specifically for risk-based career protection outcomes"""
    
    def __init__(self, db_path: str):
        """Initialize risk-based success metrics"""
        self.db_path = db_path
        self._init_risk_success_tables()
    
    def _init_risk_success_tables(self):
        """Initialize risk-specific success metrics tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Career protection outcomes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS career_protection_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    outcome_type TEXT NOT NULL,
                    risk_prediction_accuracy REAL NOT NULL,
                    time_to_outcome_days INTEGER NOT NULL,
                    salary_impact REAL,
                    career_advancement_score REAL,
                    skills_improvement_score REAL,
                    network_expansion_score REAL,
                    outcome_timestamp DATETIME NOT NULL,
                    success_factors TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Early warning effectiveness table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS early_warning_effectiveness (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    warning_timestamp DATETIME NOT NULL,
                    warning_accuracy REAL NOT NULL,
                    advance_notice_days INTEGER NOT NULL,
                    user_response_time_hours INTEGER,
                    proactive_action_taken BOOLEAN NOT NULL,
                    outcome_improvement REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Risk communication effectiveness table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_communication_effectiveness (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    communication_type TEXT NOT NULL,
                    message_clarity_score REAL NOT NULL,
                    user_understanding_score REAL NOT NULL,
                    action_taken BOOLEAN NOT NULL,
                    time_to_action_hours INTEGER,
                    communication_timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    async def track_career_protection_outcome(self, user_id: str, outcome_type: str, outcome_data: Dict[str, Any]) -> bool:
        """Track career protection outcomes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO career_protection_outcomes 
                    (user_id, outcome_type, risk_prediction_accuracy, time_to_outcome_days,
                     salary_impact, career_advancement_score, skills_improvement_score,
                     network_expansion_score, outcome_timestamp, success_factors)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    outcome_type,
                    outcome_data.get('risk_prediction_accuracy', 0.0),
                    outcome_data.get('time_to_outcome_days', 0),
                    outcome_data.get('salary_impact', 0.0),
                    outcome_data.get('career_advancement_score', 0.0),
                    outcome_data.get('skills_improvement_score', 0.0),
                    outcome_data.get('network_expansion_score', 0.0),
                    datetime.now(),
                    json.dumps(outcome_data.get('success_factors', {}))
                ))
                
                conn.commit()
                logger.info(f"Tracked career protection outcome for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error tracking career protection outcome: {e}")
            return False

class RiskABTestFramework:
    """A/B testing framework for risk thresholds and recommendation timing"""
    
    def __init__(self, db_path: str):
        """Initialize risk A/B testing framework"""
        self.db_path = db_path
        self._init_risk_ab_tables()
    
    def _init_risk_ab_tables(self):
        """Initialize risk A/B testing tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Risk A/B tests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_ab_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT UNIQUE NOT NULL,
                    test_name TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    hypothesis TEXT NOT NULL,
                    risk_threshold_variants TEXT NOT NULL,
                    recommendation_timing_variants TEXT NOT NULL,
                    success_metrics TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_date DATETIME NOT NULL,
                    end_date DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    async def create_risk_threshold_test(self, test_name: str, threshold_variants: List[float], success_metrics: List[str]) -> str:
        """Create an A/B test for risk thresholds"""
        try:
            test_id = f"risk_threshold_{int(time.time())}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO risk_ab_tests 
                    (test_id, test_name, test_type, description, hypothesis,
                     risk_threshold_variants, recommendation_timing_variants, 
                     success_metrics, status, start_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    test_name,
                    'risk_threshold',
                    f'A/B test for risk threshold optimization: {test_name}',
                    'Different risk thresholds will optimize recommendation timing and user outcomes',
                    json.dumps(threshold_variants),
                    json.dumps(['immediate', 'delayed_24h', 'delayed_48h']),
                    json.dumps(success_metrics),
                    'active',
                    datetime.now()
                ))
                
                conn.commit()
                logger.info(f"Created risk threshold A/B test: {test_id}")
                return test_id
                
        except Exception as e:
            logger.error(f"Error creating risk threshold test: {e}")
            raise
    
    async def record_risk_threshold_test(self, user_id: str, risk_score: float, test_id: str, variant: str) -> bool:
        """Record a user's participation in a risk threshold test"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO risk_ab_test_results 
                    (test_id, user_id, variant_id, risk_threshold, recommendation_timing,
                     user_response, test_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    user_id,
                    variant,
                    risk_score,
                    'immediate',  # Default timing
                    'pending',
                    datetime.now()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error recording risk threshold test: {e}")
            return False

class RiskAnalyticsIntegration:
    """
    Comprehensive risk-based analytics integration for career protection.
    
    Extends the existing AnalyticsIntegration to provide specialized
    risk assessment, recommendation triggering, and outcome tracking.
    """
    
    def __init__(self, db_path: str = "backend/analytics/risk_analytics.db"):
        """Initialize the risk analytics integration system"""
        self.db_path = db_path
        
        # Initialize base analytics
        self.analytics = AnalyticsIntegration(db_path)
        
        # Initialize risk-specific components
        self.risk_tracker = RiskAnalyticsTracker(db_path)
        self.risk_success_metrics = RiskBasedSuccessMetrics(db_path)
        self.risk_ab_testing = RiskABTestFramework(db_path)
        
        logger.info("RiskAnalyticsIntegration initialized successfully")
    
    async def track_risk_assessment_completed(self, user_id: str, risk_data: RiskAssessmentData) -> bool:
        """Track when a risk assessment is completed"""
        try:
            # Track in existing analytics system
            self.analytics.user_behavior.track_feature_usage(
                user_id=user_id,
                feature_name='risk_assessment',
                time_spent=0,
                success=True
            )
            
            # Track risk-specific event
            event_data = {
                'user_id': user_id,
                'assessment_type': risk_data.assessment_type,
                'overall_risk': risk_data.overall_risk,
                'risk_level': self._determine_risk_level(risk_data.overall_risk),
                'timeline_urgency': risk_data.timeline_urgency,
                'confidence_score': risk_data.confidence_score
            }
            
            self.analytics.user_behavior.track_user_interaction(
                session_id=f"risk_assessment_{user_id}_{int(time.time())}",
                user_id=user_id,
                interaction_type='risk_assessment_completed',
                page_url='/risk-assessment',
                element_id='assessment_complete',
                element_text=f"Risk Assessment: {risk_data.assessment_type}",
                interaction_data=event_data
            )
            
            logger.info(f"Tracked risk assessment completion for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking risk assessment completion: {e}")
            return False
    
    async def track_risk_recommendation_triggered(self, user_id: str, risk_data: RiskAssessmentData, recommendations: Dict[str, Any]) -> bool:
        """Track when job recommendations are triggered by risk assessment"""
        try:
            event_data = {
                'user_id': user_id,
                'trigger_type': 'risk_assessment',
                'risk_score': risk_data.overall_risk,
                'risk_factors': risk_data.risk_triggers,
                'recommendations_generated': len(recommendations.get('jobs', [])),
                'recommendation_tiers': [r.get('tier', 'optimal') for r in recommendations.get('jobs', [])],
                'emergency_unlock_granted': risk_data.overall_risk >= 0.7,
                'timeline_urgency': risk_data.timeline_urgency
            }
            
            # Track in existing analytics system
            self.analytics.track_recommendation_workflow(
                user_id=user_id,
                session_id=f"risk_recommendation_{user_id}_{int(time.time())}",
                workflow_data={
                    'recommendations': recommendations.get('jobs', []),
                    'processing_time': 0,
                    'trigger_type': 'risk_assessment',
                    'risk_data': asdict(risk_data)
                }
            )
            
            # Specialized risk tracking
            await self.risk_tracker.log_risk_intervention(user_id, risk_data, recommendations)
            
            # Update A/B test data
            await self.risk_ab_testing.record_risk_threshold_test(
                user_id=user_id,
                risk_score=risk_data.overall_risk,
                test_id='default_risk_test',
                variant='control'
            )
            
            logger.info(f"Tracked risk-triggered recommendation for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking risk recommendation: {e}")
            return False
    
    async def track_emergency_unlock_usage(self, user_id: str, unlock_data: Dict[str, Any]) -> bool:
        """Track emergency feature unlock usage"""
        try:
            event_data = {
                'user_id': user_id,
                'unlock_type': unlock_data.get('unlock_type', 'premium_features'),
                'risk_score': unlock_data.get('risk_score', 0.0),
                'features_unlocked': unlock_data.get('features_unlocked', []),
                'unlock_timestamp': datetime.now().isoformat()
            }
            
            self.analytics.user_behavior.track_feature_usage(
                user_id=user_id,
                feature_name='emergency_unlock',
                time_spent=unlock_data.get('time_spent', 0),
                success=True
            )
            
            self.analytics.user_behavior.track_user_interaction(
                session_id=f"emergency_unlock_{user_id}_{int(time.time())}",
                user_id=user_id,
                interaction_type='emergency_unlock_usage',
                page_url='/emergency-unlock',
                element_id='unlock_activated',
                element_text='Emergency Unlock Activated',
                interaction_data=event_data
            )
            
            logger.info(f"Tracked emergency unlock usage for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking emergency unlock usage: {e}")
            return False
    
    async def track_risk_prediction_accuracy(self, user_id: str, predicted_risk: Dict[str, Any], actual_outcome: Dict[str, Any]) -> bool:
        """Measure how accurate risk predictions are"""
        try:
            # Calculate prediction accuracy
            prediction_accuracy = self._calculate_prediction_accuracy(predicted_risk, actual_outcome)
            
            accuracy_data = RiskOutcomeData(
                user_id=user_id,
                predicted_risk_score=predicted_risk.get('overall_risk', 0.0),
                predicted_timeline=predicted_risk.get('timeline_urgency', 'unknown'),
                actual_outcome=actual_outcome.get('outcome_type', 'unknown'),
                outcome_timeline_days=actual_outcome.get('days_from_prediction', 0),
                prediction_accuracy=prediction_accuracy,
                outcome_timestamp=datetime.now(),
                outcome_details=actual_outcome
            )
            
            # Log prediction accuracy
            await self.risk_tracker.log_prediction_accuracy(accuracy_data)
            
            # Track in success metrics
            await self.risk_success_metrics.track_career_protection_outcome(
                user_id=user_id,
                outcome_type=actual_outcome.get('outcome_type', 'unknown'),
                outcome_data={
                    'risk_prediction_accuracy': prediction_accuracy,
                    'time_to_outcome_days': actual_outcome.get('days_from_prediction', 0),
                    'success_factors': actual_outcome.get('success_factors', {})
                }
            )
            
            # Update risk model if accuracy is low
            if prediction_accuracy < 0.7:
                await self._trigger_risk_model_retraining(user_id, accuracy_data)
            
            logger.info(f"Tracked risk prediction accuracy for user {user_id}: {prediction_accuracy:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking risk prediction accuracy: {e}")
            return False
    
    async def track_career_protection_outcomes(self, user_id: str, outcome_data: Dict[str, Any]) -> bool:
        """Measure successful job transitions before layoffs"""
        try:
            await self.risk_success_metrics.track_career_protection_outcome(
                user_id=user_id,
                outcome_type=outcome_data.get('outcome_type', 'unknown'),
                outcome_data=outcome_data
            )
            
            # Track in base success metrics
            self.analytics.track_success_outcome(
                user_id=user_id,
                outcome_type='career_protection',
                outcome_data=outcome_data
            )
            
            logger.info(f"Tracked career protection outcome for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking career protection outcome: {e}")
            return False
    
    async def analyze_risk_to_recommendation_flow(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze complete user journey from risk detection to job placement"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get risk journey flow data
                cursor.execute('''
                    SELECT flow_step, step_timestamp, step_data, time_to_next_step
                    FROM risk_journey_flow 
                    WHERE user_id = ? AND step_timestamp >= datetime('now', '-{} days')
                    ORDER BY step_timestamp
                '''.format(days), (user_id,))
                
                flow_data = cursor.fetchall()
                
                # Analyze flow patterns
                flow_analysis = self._analyze_flow_patterns(flow_data)
                
                return {
                    'user_id': user_id,
                    'analysis_period_days': days,
                    'flow_steps': len(flow_data),
                    'flow_analysis': flow_analysis,
                    'average_time_between_steps': self._calculate_average_step_time(flow_data),
                    'completion_rate': self._calculate_flow_completion_rate(flow_data)
                }
                
        except Exception as e:
            logger.error(f"Error analyzing risk to recommendation flow: {e}")
            return {'error': str(e)}
    
    async def measure_early_warning_effectiveness(self, days: int = 30) -> Dict[str, Any]:
        """Calculate advance notice accuracy (3-6 months)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get early warning data
                cursor.execute('''
                    SELECT warning_accuracy, advance_notice_days, proactive_action_taken, outcome_improvement
                    FROM early_warning_effectiveness 
                    WHERE warning_timestamp >= datetime('now', '-{} days')
                '''.format(days))
                
                warning_data = cursor.fetchall()
                
                if not warning_data:
                    return {'error': 'No early warning data available'}
                
                # Calculate effectiveness metrics
                total_warnings = len(warning_data)
                accurate_warnings = sum(1 for w in warning_data if w[0] >= 0.7)
                proactive_actions = sum(1 for w in warning_data if w[2])
                avg_advance_notice = sum(w[1] for w in warning_data) / total_warnings
                avg_improvement = sum(w[3] for w in warning_data if w[3] is not None) / max(1, sum(1 for w in warning_data if w[3] is not None))
                
                return {
                    'analysis_period_days': days,
                    'total_warnings': total_warnings,
                    'accuracy_rate': accurate_warnings / total_warnings,
                    'proactive_action_rate': proactive_actions / total_warnings,
                    'average_advance_notice_days': avg_advance_notice,
                    'average_outcome_improvement': avg_improvement,
                    'early_warning_effectiveness_score': (accurate_warnings / total_warnings) * (proactive_actions / total_warnings) * 100
                }
                
        except Exception as e:
            logger.error(f"Error measuring early warning effectiveness: {e}")
            return {'error': str(e)}
    
    async def optimize_risk_trigger_thresholds(self, test_name: str, threshold_variants: List[float]) -> str:
        """A/B test different risk scores for recommendation activation"""
        try:
            test_id = await self.risk_ab_testing.create_risk_threshold_test(
                test_name=test_name,
                threshold_variants=threshold_variants,
                success_metrics=['conversion_rate', 'user_satisfaction', 'outcome_improvement']
            )
            
            logger.info(f"Created risk threshold optimization test: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating risk threshold optimization test: {e}")
            raise
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL.value
        elif risk_score >= 0.6:
            return RiskLevel.HIGH.value
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM.value
        else:
            return RiskLevel.LOW.value
    
    def _calculate_prediction_accuracy(self, predicted_risk: Dict[str, Any], actual_outcome: Dict[str, Any]) -> float:
        """Calculate prediction accuracy score"""
        # Simple accuracy calculation - can be enhanced with more sophisticated algorithms
        predicted_score = predicted_risk.get('overall_risk', 0.0)
        actual_score = actual_outcome.get('risk_realized', 0.0)
        
        # Calculate accuracy based on how close prediction was to actual outcome
        accuracy = 1.0 - abs(predicted_score - actual_score)
        return max(0.0, min(1.0, accuracy))
    
    def _analyze_flow_patterns(self, flow_data: List[Tuple]) -> Dict[str, Any]:
        """Analyze user flow patterns from risk detection to recommendation"""
        if not flow_data:
            return {'error': 'No flow data available'}
        
        steps = [row[0] for row in flow_data]
        step_counts = {}
        for step in steps:
            step_counts[step] = step_counts.get(step, 0) + 1
        
        return {
            'total_steps': len(flow_data),
            'unique_steps': len(set(steps)),
            'step_frequency': step_counts,
            'most_common_step': max(step_counts, key=step_counts.get) if step_counts else None
        }
    
    def _calculate_average_step_time(self, flow_data: List[Tuple]) -> float:
        """Calculate average time between flow steps"""
        if len(flow_data) < 2:
            return 0.0
        
        total_time = sum(row[3] for row in flow_data if row[3] is not None)
        return total_time / max(1, len([row for row in flow_data if row[3] is not None]))
    
    def _calculate_flow_completion_rate(self, flow_data: List[Tuple]) -> float:
        """Calculate flow completion rate"""
        if not flow_data:
            return 0.0
        
        # Define completion criteria
        completion_steps = ['recommendation_generated', 'application_started', 'outcome_achieved']
        completed_steps = sum(1 for row in flow_data if row[0] in completion_steps)
        
        return completed_steps / len(flow_data)
    
    async def _trigger_risk_model_retraining(self, user_id: str, accuracy_data: RiskOutcomeData) -> bool:
        """Trigger risk model retraining when accuracy is low"""
        try:
            # Log retraining trigger
            logger.warning(f"Risk model retraining triggered for user {user_id} due to low accuracy: {accuracy_data.prediction_accuracy}")
            
            # In a production system, this would trigger actual model retraining
            # For now, we'll just log the event
            await self.analytics.user_behavior.track_feature_usage(
                user_id=user_id,
                feature_name='risk_model_retraining_triggered',
                time_spent=0,
                success=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error triggering risk model retraining: {e}")
            return False
    
    # Risk A/B Testing Integration Methods
    async def create_risk_threshold_optimization_test(
        self, 
        test_name: str, 
        threshold_variants: List[float], 
        success_criteria: List[str]
    ) -> str:
        """Create and manage risk threshold optimization A/B test"""
        try:
            test_id = await self.risk_ab_testing.create_risk_threshold_test(
                test_name=test_name,
                threshold_variants=threshold_variants,
                success_criteria=success_criteria
            )
            
            logger.info(f"Created risk threshold optimization test: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating risk threshold optimization test: {e}")
            raise
    
    async def create_risk_communication_test(
        self,
        test_name: str,
        communication_variants: List[str],
        success_criteria: List[str]
    ) -> str:
        """Create and manage risk communication A/B test"""
        try:
            from .risk_ab_testing_framework import CommunicationTone
            
            # Convert string variants to enum
            tone_variants = [CommunicationTone(variant) for variant in communication_variants]
            
            test_id = await self.risk_ab_testing.create_risk_communication_test(
                test_name=test_name,
                communication_variants=tone_variants,
                success_criteria=success_criteria
            )
            
            logger.info(f"Created risk communication test: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating risk communication test: {e}")
            raise
    
    async def create_intervention_timing_test(
        self,
        test_name: str,
        timing_variants: List[str],
        success_criteria: List[str]
    ) -> str:
        """Create and manage intervention timing A/B test"""
        try:
            from .risk_ab_testing_framework import TimingStrategy
            
            # Convert string variants to enum
            strategy_variants = [TimingStrategy(variant) for variant in timing_variants]
            
            test_id = await self.risk_ab_testing.create_intervention_timing_test(
                test_name=test_name,
                timing_variants=strategy_variants,
                success_criteria=success_criteria
            )
            
            logger.info(f"Created intervention timing test: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating intervention timing test: {e}")
            raise
    
    async def assign_user_to_risk_test(
        self, 
        test_id: str, 
        user_id: str, 
        risk_score: float
    ) -> Optional[str]:
        """Assign user to risk A/B test and track assignment"""
        try:
            # Assign user to test
            variant_id = await self.risk_ab_testing.assign_user_to_risk_test(
                test_id=test_id,
                user_id=user_id,
                risk_score=risk_score
            )
            
            if variant_id:
                # Track assignment in base analytics
                self.analytics.user_behavior.track_feature_usage(
                    user_id=user_id,
                    feature_name='risk_ab_test_assignment',
                    time_spent=0,
                    success=True
                )
                
                logger.info(f"Assigned user {user_id} to risk test {test_id} variant {variant_id}")
            
            return variant_id
            
        except Exception as e:
            logger.error(f"Error assigning user to risk test: {e}")
            return None
    
    async def track_risk_test_conversion(
        self,
        test_id: str,
        user_id: str,
        conversion_event: str,
        value: float = 1.0,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Track conversion event for risk A/B test"""
        try:
            # Track in risk A/B testing framework
            success = await self.risk_ab_testing.track_risk_test_conversion(
                test_id=test_id,
                user_id=user_id,
                conversion_event=conversion_event,
                value=value,
                metadata=metadata
            )
            
            if success:
                # Also track in base analytics
                self.analytics.track_conversion(
                    user_id=user_id,
                    conversion_event=f"risk_test_{conversion_event}",
                    value=value,
                    metadata=metadata
                )
                
                logger.debug(f"Tracked risk test conversion: {conversion_event} for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error tracking risk test conversion: {e}")
            return False
    
    async def get_risk_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get comprehensive results for a risk A/B test"""
        try:
            # Get success measurement
            success_results = await self.risk_ab_testing.measure_intervention_success_by_variant(test_id)
            
            # Get long-term outcomes
            long_term_results = await self.risk_ab_testing.track_long_term_career_outcomes(test_id)
            
            # Get user satisfaction
            satisfaction_results = await self.risk_ab_testing.analyze_user_satisfaction_by_variant(test_id)
            
            # Get ROI analysis
            roi_results = await self.risk_ab_testing.calculate_roi_by_test_variant(test_id)
            
            return {
                'test_id': test_id,
                'success_measurement': success_results,
                'long_term_outcomes': long_term_results,
                'user_satisfaction': satisfaction_results,
                'roi_analysis': roi_results,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting risk test results: {e}")
            return {'error': str(e)}
    
    async def auto_optimize_risk_system(self, test_id: str) -> Dict[str, Any]:
        """Automatically optimize risk system based on A/B test results"""
        try:
            # Auto-optimize thresholds
            threshold_optimization = await self.risk_ab_testing.auto_optimize_risk_thresholds(test_id)
            
            # Get test results for analysis
            test_results = await self.get_risk_test_results(test_id)
            
            # Determine if optimization was successful
            optimization_successful = threshold_optimization.get('optimization_applied', False)
            
            if optimization_successful:
                # Track optimization success
                await self.track_career_protection_outcomes(
                    user_id='system',
                    outcome_data={
                        'outcome_type': 'system_optimization',
                        'risk_prediction_accuracy': threshold_optimization.get('confidence_level', 0),
                        'time_to_outcome_days': 0,
                        'success_factors': {
                            'optimization_type': 'risk_threshold',
                            'improvement_percentage': threshold_optimization.get('improvement_percentage', 0)
                        }
                    }
                )
            
            return {
                'optimization_applied': optimization_successful,
                'threshold_optimization': threshold_optimization,
                'test_results': test_results
            }
            
        except Exception as e:
            logger.error(f"Error in auto-optimizing risk system: {e}")
            return {'error': str(e)}
