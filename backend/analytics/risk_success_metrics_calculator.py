#!/usr/bin/env python3
"""
Risk-Based Success Metrics Calculator

This module provides comprehensive calculation of success metrics for risk-based
career protection recommendations, including career protection success rates,
early warning effectiveness, and conversion tracking.

Key Metrics:
- career_protection_success_rate: % of high-risk users who successfully transition before layoffs
- early_warning_effectiveness: Average advance notice accuracy (target: 3-6 months)
- risk_recommendation_conversion: % of risk-triggered recommendations that lead to job applications
- emergency_unlock_utilization: Usage patterns for emergency feature unlocks
- proactive_vs_reactive_outcomes: Career outcome comparison based on risk response timing
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskSuccessMetricType(Enum):
    """Types of risk-based success metrics"""
    CAREER_PROTECTION_SUCCESS_RATE = "career_protection_success_rate"
    EARLY_WARNING_EFFECTIVENESS = "early_warning_effectiveness"
    RISK_RECOMMENDATION_CONVERSION = "risk_recommendation_conversion"
    EMERGENCY_UNLOCK_UTILIZATION = "emergency_unlock_utilization"
    PROACTIVE_VS_REACTIVE_OUTCOMES = "proactive_vs_reactive_outcomes"

@dataclass
class RiskSuccessMetrics:
    """Comprehensive risk-based success metrics"""
    career_protection_success_rate: float
    early_warning_effectiveness: float
    risk_recommendation_conversion: float
    emergency_unlock_utilization: Dict[str, Any]
    proactive_vs_reactive_outcomes: Dict[str, Any]
    calculation_timestamp: datetime
    analysis_period_days: int

@dataclass
class CareerProtectionOutcome:
    """Individual career protection outcome data"""
    user_id: str
    risk_assessment_id: int
    outcome_type: str
    transition_success: bool
    salary_protection_amount: float
    time_to_transition_days: int
    advance_notice_days: int
    risk_mitigation_effectiveness: float
    outcome_timestamp: datetime

class RiskSuccessMetricsCalculator:
    """Calculator for risk-based success metrics"""
    
    def __init__(self, db_path: str):
        """Initialize the success metrics calculator"""
        self.db_path = db_path
    
    async def calculate_all_metrics(self, days: int = 30) -> RiskSuccessMetrics:
        """Calculate all risk-based success metrics"""
        try:
            # Calculate individual metrics
            career_protection_rate = await self.calculate_career_protection_success_rate(days)
            early_warning_effectiveness = await self.calculate_early_warning_effectiveness(days)
            recommendation_conversion = await self.calculate_risk_recommendation_conversion(days)
            emergency_unlock_util = await self.calculate_emergency_unlock_utilization(days)
            proactive_vs_reactive = await self.calculate_proactive_vs_reactive_outcomes(days)
            
            return RiskSuccessMetrics(
                career_protection_success_rate=career_protection_rate,
                early_warning_effectiveness=early_warning_effectiveness,
                risk_recommendation_conversion=recommendation_conversion,
                emergency_unlock_utilization=emergency_unlock_util,
                proactive_vs_reactive_outcomes=proactive_vs_reactive,
                calculation_timestamp=datetime.now(),
                analysis_period_days=days
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk success metrics: {e}")
            raise
    
    async def calculate_career_protection_success_rate(self, days: int) -> float:
        """
        Calculate % of high-risk users who successfully transition before layoffs
        
        Target: 70%+ successful transitions
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get high-risk users (risk score >= 0.6) from the analysis period
                cursor.execute('''
                    SELECT COUNT(DISTINCT ra.user_id) as high_risk_users
                    FROM risk_assessments ra
                    WHERE ra.overall_risk >= 0.6
                    AND ra.assessment_timestamp >= datetime('now', '-{} days')
                '''.format(days))
                
                high_risk_users = cursor.fetchone()[0]
                
                if high_risk_users == 0:
                    return 0.0
                
                # Get successful career protection outcomes
                cursor.execute('''
                    SELECT COUNT(DISTINCT cpo.user_id) as successful_transitions
                    FROM career_protection_outcomes cpo
                    JOIN risk_assessments ra ON cpo.risk_assessment_id = ra.id
                    WHERE cpo.transition_success = 1
                    AND cpo.outcome_type IN ('proactive_switch', 'job_saved', 'promotion')
                    AND ra.overall_risk >= 0.6
                    AND cpo.outcome_timestamp >= datetime('now', '-{} days')
                '''.format(days))
                
                successful_transitions = cursor.fetchone()[0]
                
                success_rate = successful_transitions / high_risk_users
                
                logger.info(f"Career protection success rate: {success_rate:.2%} ({successful_transitions}/{high_risk_users})")
                return success_rate
                
        except Exception as e:
            logger.error(f"Error calculating career protection success rate: {e}")
            return 0.0
    
    async def calculate_early_warning_effectiveness(self, days: int) -> float:
        """
        Calculate average advance notice accuracy (target: 3-6 months)
        
        Target: 75%+ accuracy with 3-6 month advance notice
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get early warning data with advance notice
                cursor.execute('''
                    SELECT 
                        AVG(ewe.warning_accuracy) as avg_accuracy,
                        AVG(ewe.advance_notice_days) as avg_advance_notice,
                        COUNT(*) as total_warnings
                    FROM early_warning_effectiveness ewe
                    WHERE ewe.warning_timestamp >= datetime('now', '-{} days')
                    AND ewe.advance_notice_days >= 90  -- At least 3 months
                    AND ewe.advance_notice_days <= 180  -- At most 6 months
                '''.format(days))
                
                result = cursor.fetchone()
                avg_accuracy = result[0] or 0.0
                avg_advance_notice = result[1] or 0.0
                total_warnings = result[2] or 0
                
                # Calculate effectiveness score (accuracy weighted by advance notice quality)
                if total_warnings == 0:
                    return 0.0
                
                # Weight accuracy by how close advance notice is to optimal range (120-150 days)
                optimal_range_center = 135  # 4.5 months
                advance_notice_quality = max(0, 1 - abs(avg_advance_notice - optimal_range_center) / optimal_range_center)
                
                effectiveness = avg_accuracy * advance_notice_quality
                
                logger.info(f"Early warning effectiveness: {effectiveness:.2%} (accuracy: {avg_accuracy:.2%}, advance notice: {avg_advance_notice:.0f} days)")
                return effectiveness
                
        except Exception as e:
            logger.error(f"Error calculating early warning effectiveness: {e}")
            return 0.0
    
    async def calculate_risk_recommendation_conversion(self, days: int) -> float:
        """
        Calculate % of risk-triggered recommendations that lead to job applications
        
        Target: 40%+ conversion rate
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total risk-triggered recommendations
                cursor.execute('''
                    SELECT COUNT(*) as total_recommendations
                    FROM risk_triggered_recommendations rtr
                    WHERE rtr.trigger_timestamp >= datetime('now', '-{} days')
                '''.format(days))
                
                total_recommendations = cursor.fetchone()[0]
                
                if total_recommendations == 0:
                    return 0.0
                
                # Get recommendations that led to applications
                cursor.execute('''
                    SELECT COUNT(*) as applications_generated
                    FROM risk_triggered_recommendations rtr
                    WHERE rtr.application_generated = 1
                    AND rtr.trigger_timestamp >= datetime('now', '-{} days')
                '''.format(days))
                
                applications_generated = cursor.fetchone()[0]
                
                conversion_rate = applications_generated / total_recommendations
                
                logger.info(f"Risk recommendation conversion: {conversion_rate:.2%} ({applications_generated}/{total_recommendations})")
                return conversion_rate
                
        except Exception as e:
            logger.error(f"Error calculating risk recommendation conversion: {e}")
            return 0.0
    
    async def calculate_emergency_unlock_utilization(self, days: int) -> Dict[str, Any]:
        """
        Calculate usage patterns for emergency feature unlocks
        
        Returns detailed utilization metrics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get emergency unlock usage data
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_unlocks,
                        COUNT(DISTINCT user_id) as unique_users,
                        AVG(time_spent) as avg_time_spent,
                        COUNT(CASE WHEN unlock_type = 'premium_features' THEN 1 END) as premium_unlocks,
                        COUNT(CASE WHEN unlock_type = 'priority_support' THEN 1 END) as support_unlocks
                    FROM risk_recommendations rr
                    WHERE rr.emergency_unlock_granted = 1
                    AND rr.intervention_timestamp >= datetime('now', '-{} days')
                '''.format(days))
                
                result = cursor.fetchone()
                total_unlocks = result[0] or 0
                unique_users = result[1] or 0
                avg_time_spent = result[2] or 0
                premium_unlocks = result[3] or 0
                support_unlocks = result[4] or 0
                
                # Calculate utilization metrics
                utilization_metrics = {
                    'total_unlocks': total_unlocks,
                    'unique_users': unique_users,
                    'avg_time_spent_minutes': round(avg_time_spent / 60, 2) if avg_time_spent else 0,
                    'premium_unlock_rate': premium_unlocks / max(1, total_unlocks),
                    'support_unlock_rate': support_unlocks / max(1, total_unlocks),
                    'unlocks_per_user': total_unlocks / max(1, unique_users),
                    'utilization_score': min(1.0, total_unlocks / max(1, unique_users) * 0.1)  # Normalized score
                }
                
                logger.info(f"Emergency unlock utilization: {utilization_metrics['utilization_score']:.2%}")
                return utilization_metrics
                
        except Exception as e:
            logger.error(f"Error calculating emergency unlock utilization: {e}")
            return {}
    
    async def calculate_proactive_vs_reactive_outcomes(self, days: int) -> Dict[str, Any]:
        """
        Calculate career outcome comparison based on risk response timing
        
        Compares outcomes for users who act on early warnings vs those who don't
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get proactive outcomes (users who acted on early warnings)
                cursor.execute('''
                    SELECT 
                        COUNT(*) as proactive_count,
                        AVG(cpo.salary_improvement_percentage) as avg_salary_improvement,
                        AVG(cpo.risk_mitigation_effectiveness) as avg_mitigation_effectiveness,
                        AVG(cpo.time_to_transition_days) as avg_transition_time
                    FROM career_protection_outcomes cpo
                    JOIN early_warning_effectiveness ewe ON cpo.user_id = ewe.user_id
                    WHERE cpo.outcome_type = 'proactive_switch'
                    AND ewe.proactive_action_taken = 1
                    AND cpo.outcome_timestamp >= datetime('now', '-{} days')
                '''.format(days))
                
                proactive_result = cursor.fetchone()
                proactive_count = proactive_result[0] or 0
                proactive_salary_improvement = proactive_result[1] or 0
                proactive_mitigation_effectiveness = proactive_result[2] or 0
                proactive_transition_time = proactive_result[3] or 0
                
                # Get reactive outcomes (users who didn't act on early warnings)
                cursor.execute('''
                    SELECT 
                        COUNT(*) as reactive_count,
                        AVG(cpo.salary_improvement_percentage) as avg_salary_improvement,
                        AVG(cpo.risk_mitigation_effectiveness) as avg_mitigation_effectiveness,
                        AVG(cpo.time_to_transition_days) as avg_transition_time
                    FROM career_protection_outcomes cpo
                    JOIN early_warning_effectiveness ewe ON cpo.user_id = ewe.user_id
                    WHERE cpo.outcome_type IN ('job_saved', 'laid_off')
                    AND ewe.proactive_action_taken = 0
                    AND cpo.outcome_timestamp >= datetime('now', '-{} days')
                '''.format(days))
                
                reactive_result = cursor.fetchone()
                reactive_count = reactive_result[0] or 0
                reactive_salary_improvement = reactive_result[1] or 0
                reactive_mitigation_effectiveness = reactive_result[2] or 0
                reactive_transition_time = reactive_result[3] or 0
                
                # Calculate comparison metrics
                comparison_metrics = {
                    'proactive_outcomes': {
                        'count': proactive_count,
                        'avg_salary_improvement': round(proactive_salary_improvement, 2),
                        'avg_mitigation_effectiveness': round(proactive_mitigation_effectiveness, 3),
                        'avg_transition_time_days': round(proactive_transition_time, 1)
                    },
                    'reactive_outcomes': {
                        'count': reactive_count,
                        'avg_salary_improvement': round(reactive_salary_improvement, 2),
                        'avg_mitigation_effectiveness': round(reactive_mitigation_effectiveness, 3),
                        'avg_transition_time_days': round(reactive_transition_time, 1)
                    },
                    'comparison': {
                        'salary_improvement_advantage': round(proactive_salary_improvement - reactive_salary_improvement, 2),
                        'mitigation_effectiveness_advantage': round(proactive_mitigation_effectiveness - reactive_mitigation_effectiveness, 3),
                        'transition_time_advantage_days': round(reactive_transition_time - proactive_transition_time, 1),
                        'proactive_success_rate': proactive_count / max(1, proactive_count + reactive_count)
                    }
                }
                
                logger.info(f"Proactive vs reactive outcomes calculated: {comparison_metrics['comparison']['proactive_success_rate']:.2%} proactive success rate")
                return comparison_metrics
                
        except Exception as e:
            logger.error(f"Error calculating proactive vs reactive outcomes: {e}")
            return {}
    
    async def get_risk_metrics_dashboard_data(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive dashboard data for risk metrics"""
        try:
            # Calculate all metrics
            metrics = await self.calculate_all_metrics(days)
            
            # Get additional dashboard data
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get risk assessment trends
                cursor.execute('''
                    SELECT 
                        assessment_type,
                        AVG(overall_risk) as avg_risk,
                        COUNT(*) as count
                    FROM risk_assessments
                    WHERE assessment_timestamp >= datetime('now', '-{} days')
                    GROUP BY assessment_type
                '''.format(days))
                
                risk_trends = {}
                for row in cursor.fetchall():
                    risk_trends[row[0]] = {
                        'avg_risk': round(row[1], 3),
                        'count': row[2]
                    }
                
                # Get user segment distribution
                cursor.execute('''
                    SELECT 
                        segment_name,
                        COUNT(*) as count
                    FROM risk_user_segments
                    WHERE segment_timestamp >= datetime('now', '-{} days')
                    GROUP BY segment_name
                '''.format(days))
                
                user_segments = {}
                for row in cursor.fetchall():
                    user_segments[row[0]] = row[1]
                
                # Get A/B test performance
                cursor.execute('''
                    SELECT 
                        test_id,
                        variant_id,
                        AVG(CASE WHEN outcome_achieved = 'success' THEN 1.0 ELSE 0.0 END) as success_rate,
                        COUNT(*) as participants
                    FROM risk_ab_test_results
                    WHERE test_timestamp >= datetime('now', '-{} days')
                    GROUP BY test_id, variant_id
                '''.format(days))
                
                ab_test_performance = {}
                for row in cursor.fetchall():
                    test_id = row[0]
                    if test_id not in ab_test_performance:
                        ab_test_performance[test_id] = {}
                    ab_test_performance[test_id][row[1]] = {
                        'success_rate': round(row[2], 3),
                        'participants': row[3]
                    }
            
            return {
                'metrics': {
                    'career_protection_success_rate': metrics.career_protection_success_rate,
                    'early_warning_effectiveness': metrics.early_warning_effectiveness,
                    'risk_recommendation_conversion': metrics.risk_recommendation_conversion,
                    'emergency_unlock_utilization': metrics.emergency_unlock_utilization,
                    'proactive_vs_reactive_outcomes': metrics.proactive_vs_reactive_outcomes
                },
                'risk_trends': risk_trends,
                'user_segments': user_segments,
                'ab_test_performance': ab_test_performance,
                'analysis_period_days': days,
                'calculation_timestamp': metrics.calculation_timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting risk metrics dashboard data: {e}")
            return {}
    
    async def track_risk_triggered_recommendation(self, 
                                                risk_assessment_id: int, 
                                                recommendation_id: int, 
                                                trigger_risk_score: float,
                                                recommendation_tier: str,
                                                success_probability: float) -> int:
        """Track a risk-triggered recommendation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO risk_triggered_recommendations 
                    (risk_assessment_id, recommendation_id, trigger_risk_score, 
                     trigger_timestamp, recommendation_tier, success_probability)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    risk_assessment_id,
                    recommendation_id,
                    trigger_risk_score,
                    datetime.now(),
                    recommendation_tier,
                    success_probability
                ))
                
                recommendation_tracking_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Tracked risk-triggered recommendation: {recommendation_tracking_id}")
                return recommendation_tracking_id
                
        except Exception as e:
            logger.error(f"Error tracking risk-triggered recommendation: {e}")
            raise
    
    async def update_recommendation_outcome(self, 
                                          recommendation_tracking_id: int, 
                                          application_generated: bool = False,
                                          outcome_achieved: str = None) -> bool:
        """Update recommendation outcome when user takes action"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                update_fields = []
                update_values = []
                
                if application_generated:
                    update_fields.append("application_generated = ?")
                    update_values.append(True)
                    update_fields.append("application_timestamp = ?")
                    update_values.append(datetime.now())
                
                if outcome_achieved:
                    update_fields.append("outcome_achieved = ?")
                    update_values.append(outcome_achieved)
                    update_fields.append("outcome_timestamp = ?")
                    update_values.append(datetime.now())
                
                if update_fields:
                    update_values.append(recommendation_tracking_id)
                    
                    cursor.execute(f'''
                        UPDATE risk_triggered_recommendations 
                        SET {', '.join(update_fields)}
                        WHERE id = ?
                    ''', update_values)
                    
                    conn.commit()
                
                logger.info(f"Updated recommendation outcome: {recommendation_tracking_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating recommendation outcome: {e}")
            return False
