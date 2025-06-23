"""
Health-Spending Correlation Analysis Service

This service analyzes the correlation between user health metrics and spending patterns
to provide insights for financial wellness optimization.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import statistics
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
import numpy as np
from scipy import stats
from backend.models import UserHealthCheckin, HealthSpendingCorrelation, User
from backend.models.base import Base

logger = logging.getLogger(__name__)

@dataclass
class CorrelationResult:
    """Data class for correlation analysis results"""
    metric: str
    correlation_coefficient: float
    p_value: float
    significance: str
    sample_size: int
    trend_direction: str
    strength: str
    confidence_interval: Tuple[float, float]

@dataclass
class SpendingPattern:
    """Data class for spending pattern analysis"""
    category: str
    average_amount: float
    frequency: int
    correlation_with_stress: float
    correlation_with_mood: float
    trend: str
    risk_level: str

@dataclass
class HealthInsight:
    """Data class for health-based insights"""
    insight_type: str
    title: str
    description: str
    impact_score: float
    recommendations: List[str]
    data_points: Dict[str, Any]

class HealthCorrelationService:
    """
    Service for analyzing correlations between health metrics and spending patterns
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    def analyze_health_spending_patterns(self, user_id: int, weeks: int = 12) -> Dict[str, Any]:
        """
        Main correlation analysis method
        
        Args:
            user_id: User ID to analyze
            weeks: Number of weeks to analyze (default: 12)
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        try:
            # Calculate date range
            end_date = date.today()
            start_date = end_date - timedelta(weeks=weeks)
            
            # Get health and spending data
            health_data = self._get_health_data(user_id, start_date, end_date)
            spending_data = self._get_spending_data(user_id, start_date, end_date)
            
            if not health_data or not spending_data:
                return {
                    'error': 'Insufficient data for analysis',
                    'health_records': len(health_data) if health_data else 0,
                    'spending_records': len(spending_data) if spending_data else 0
                }
            
            # Perform correlation analyses
            correlations = self._calculate_correlations(health_data, spending_data)
            patterns = self._analyze_spending_patterns(health_data, spending_data)
            insights = self._generate_insights(correlations, patterns, health_data, spending_data)
            trends = self._analyze_trends(health_data, spending_data)
            
            return {
                'user_id': user_id,
                'analysis_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'weeks': weeks
                },
                'data_summary': {
                    'health_records': len(health_data),
                    'spending_records': len(spending_data),
                    'total_spending': sum(record['amount'] for record in spending_data),
                    'average_weekly_spending': sum(record['amount'] for record in spending_data) / weeks
                },
                'correlations': correlations,
                'spending_patterns': patterns,
                'insights': insights,
                'trends': trends,
                'risk_assessment': self._assess_financial_risk(correlations, patterns),
                'recommendations': self._generate_recommendations(correlations, patterns, insights)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing health-spending patterns for user {user_id}: {str(e)}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def correlate_stress_to_spending(self, health_data: List[Dict], spending_data: List[Dict]) -> CorrelationResult:
        """
        Analyze correlation between stress levels and spending behavior
        
        Args:
            health_data: List of health check-in records
            spending_data: List of spending records
            
        Returns:
            CorrelationResult with analysis details
        """
        try:
            # Align health and spending data by date
            aligned_data = self._align_data_by_date(health_data, spending_data)
            
            if len(aligned_data) < 3:
                return CorrelationResult(
                    metric="stress_spending",
                    correlation_coefficient=0.0,
                    p_value=1.0,
                    significance="insufficient_data",
                    sample_size=len(aligned_data),
                    trend_direction="unknown",
                    strength="none",
                    confidence_interval=(0.0, 0.0)
                )
            
            # Extract stress levels and spending amounts
            stress_levels = [record['stress_level'] for record in aligned_data]
            spending_amounts = [record['spending_amount'] for record in aligned_data]
            
            # Calculate correlation
            correlation, p_value = stats.pearsonr(stress_levels, spending_amounts)
            
            # Determine significance and strength
            significance = "significant" if p_value < 0.05 else "not_significant"
            strength = self._get_correlation_strength(abs(correlation))
            trend_direction = "positive" if correlation > 0 else "negative"
            
            # Calculate confidence interval (simplified)
            confidence_interval = self._calculate_confidence_interval(correlation, len(aligned_data))
            
            return CorrelationResult(
                metric="stress_spending",
                correlation_coefficient=correlation,
                p_value=p_value,
                significance=significance,
                sample_size=len(aligned_data),
                trend_direction=trend_direction,
                strength=strength,
                confidence_interval=confidence_interval
            )
            
        except Exception as e:
            self.logger.error(f"Error correlating stress to spending: {str(e)}")
            return CorrelationResult(
                metric="stress_spending",
                correlation_coefficient=0.0,
                p_value=1.0,
                significance="error",
                sample_size=0,
                trend_direction="unknown",
                strength="none",
                confidence_interval=(0.0, 0.0)
            )
    
    def analyze_mood_spending_relationship(self, health_data: List[Dict], spending_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze the relationship between mood and spending patterns
        
        Args:
            health_data: List of health check-in records
            spending_data: List of spending records
            
        Returns:
            Dictionary with mood-spending analysis
        """
        try:
            aligned_data = self._align_data_by_date(health_data, spending_data)
            
            if len(aligned_data) < 3:
                return {'error': 'Insufficient data for mood-spending analysis'}
            
            # Group spending by mood levels
            mood_spending = {}
            for record in aligned_data:
                mood = record['mood_rating']
                if mood not in mood_spending:
                    mood_spending[mood] = []
                mood_spending[mood].append(record['spending_amount'])
            
            # Calculate statistics for each mood level
            mood_analysis = {}
            for mood, amounts in mood_spending.items():
                mood_analysis[mood] = {
                    'average_spending': statistics.mean(amounts),
                    'median_spending': statistics.median(amounts),
                    'spending_count': len(amounts),
                    'spending_std': statistics.stdev(amounts) if len(amounts) > 1 else 0
                }
            
            # Find mood levels with highest/lowest spending
            avg_by_mood = {mood: data['average_spending'] for mood, data in mood_analysis.items()}
            highest_spending_mood = max(avg_by_mood, key=avg_by_mood.get)
            lowest_spending_mood = min(avg_by_mood, key=avg_by_mood.get)
            
            return {
                'mood_spending_analysis': mood_analysis,
                'highest_spending_mood': {
                    'mood_level': highest_spending_mood,
                    'average_spending': avg_by_mood[highest_spending_mood]
                },
                'lowest_spending_mood': {
                    'mood_level': lowest_spending_mood,
                    'average_spending': avg_by_mood[lowest_spending_mood]
                },
                'correlation': self.correlate_stress_to_spending(health_data, spending_data),
                'insights': self._generate_mood_insights(mood_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing mood-spending relationship: {str(e)}")
            return {'error': f'Mood-spending analysis failed: {str(e)}'}
    
    def identify_impulse_spending_triggers(self, health_data: List[Dict], spending_data: List[Dict]) -> List[Dict]:
        """
        Identify health-related triggers for impulse spending
        
        Args:
            health_data: List of health check-in records
            spending_data: List of spending records
            
        Returns:
            List of identified triggers with confidence scores
        """
        try:
            triggers = []
            aligned_data = self._align_data_by_date(health_data, spending_data)
            
            if len(aligned_data) < 5:
                return [{'error': 'Insufficient data for trigger analysis'}]
            
            # Analyze spending spikes
            spending_amounts = [record['spending_amount'] for record in aligned_data]
            mean_spending = statistics.mean(spending_amounts)
            std_spending = statistics.stdev(spending_amounts) if len(spending_amounts) > 1 else 0
            
            # Identify spending spikes (2+ standard deviations above mean)
            spike_threshold = mean_spending + (2 * std_spending)
            
            for record in aligned_data:
                if record['spending_amount'] > spike_threshold:
                    trigger = self._analyze_spending_spike(record)
                    if trigger:
                        triggers.append(trigger)
            
            # Group and rank triggers
            trigger_summary = self._summarize_triggers(triggers)
            
            return trigger_summary
            
        except Exception as e:
            self.logger.error(f"Error identifying impulse spending triggers: {str(e)}")
            return [{'error': f'Trigger analysis failed: {str(e)}'}]
    
    def generate_health_based_budget_recommendations(self, user_id: int, weeks: int = 8) -> Dict[str, Any]:
        """
        Generate budget recommendations based on health patterns
        
        Args:
            user_id: User ID
            weeks: Analysis period in weeks
            
        Returns:
            Dictionary with personalized budget recommendations
        """
        try:
            # Get recent analysis
            analysis = self.analyze_health_spending_patterns(user_id, weeks)
            
            if 'error' in analysis:
                return {'error': analysis['error']}
            
            recommendations = {
                'user_id': user_id,
                'analysis_period_weeks': weeks,
                'budget_adjustments': [],
                'spending_alerts': [],
                'wellness_incentives': [],
                'risk_mitigation': []
            }
            
            # Generate budget adjustments based on correlations
            correlations = analysis.get('correlations', {})
            
            # Stress-based adjustments
            if 'stress_spending' in correlations:
                stress_corr = correlations['stress_spending']
                if stress_corr.correlation_coefficient > 0.3 and stress_corr.significance == "significant":
                    recommendations['budget_adjustments'].append({
                        'type': 'stress_management_budget',
                        'description': 'Allocate budget for stress-reduction activities',
                        'amount': self._calculate_stress_budget(analysis),
                        'priority': 'high' if stress_corr.correlation_coefficient > 0.5 else 'medium'
                    })
            
            # Mood-based adjustments
            if 'mood_spending' in correlations:
                mood_corr = correlations['mood_spending']
                if mood_corr.correlation_coefficient < -0.3 and mood_corr.significance == "significant":
                    recommendations['budget_adjustments'].append({
                        'type': 'mood_improvement_budget',
                        'description': 'Budget for mood-enhancing activities',
                        'amount': self._calculate_mood_budget(analysis),
                        'priority': 'high' if abs(mood_corr.correlation_coefficient) > 0.5 else 'medium'
                    })
            
            # Generate spending alerts
            patterns = analysis.get('spending_patterns', [])
            for pattern in patterns:
                if pattern.risk_level == "high":
                    recommendations['spending_alerts'].append({
                        'category': pattern.category,
                        'trigger': f"High correlation with {pattern.correlation_with_stress:.2f} stress level",
                        'recommendation': 'Monitor spending in this category during high-stress periods'
                    })
            
            # Wellness incentives
            health_data = self._get_health_data(user_id, date.today() - timedelta(weeks=weeks), date.today())
            if health_data:
                avg_stress = statistics.mean([record['stress_level'] for record in health_data])
                if avg_stress > 6:
                    recommendations['wellness_incentives'].append({
                        'type': 'stress_reduction_bonus',
                        'description': 'Budget bonus for stress-reduction activities',
                        'amount': 50.0,
                        'conditions': ['Complete weekly stress-reduction activities', 'Maintain stress level below 5']
                    })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating budget recommendations for user {user_id}: {str(e)}")
            return {'error': f'Budget recommendations failed: {str(e)}'}
    
    def _get_health_data(self, user_id: int, start_date: date, end_date: date) -> List[Dict]:
        """Retrieve health check-in data for analysis"""
        try:
            health_records = self.db.query(UserHealthCheckin).filter(
                and_(
                    UserHealthCheckin.user_id == user_id,
                    UserHealthCheckin.checkin_date >= start_date,
                    UserHealthCheckin.checkin_date <= end_date
                )
            ).order_by(UserHealthCheckin.checkin_date).all()
            
            return [
                {
                    'id': record.id,
                    'checkin_date': record.checkin_date,
                    'stress_level': record.stress_level,
                    'mood_rating': record.mood_rating,
                    'energy_level': record.energy_level,
                    'relationships_rating': record.relationships_rating,
                    'physical_activity_minutes': record.physical_activity_minutes or 0,
                    'mindfulness_minutes': record.mindfulness_minutes or 0
                }
                for record in health_records
            ]
        except Exception as e:
            self.logger.error(f"Error retrieving health data: {str(e)}")
            return []
    
    def _get_spending_data(self, user_id: int, start_date: date, end_date: date) -> List[Dict]:
        """Retrieve spending data for analysis (mock implementation)"""
        # This would typically query a spending/transactions table
        # For now, we'll create mock data based on health patterns
        try:
            health_data = self._get_health_data(user_id, start_date, end_date)
            
            # Generate mock spending data correlated with health metrics
            spending_data = []
            for health_record in health_data:
                # Base spending amount
                base_spending = 100.0
                
                # Adjust based on stress level (higher stress = more spending)
                stress_multiplier = 1 + (health_record['stress_level'] - 5) * 0.2
                
                # Adjust based on mood (lower mood = more spending)
                mood_multiplier = 1 + (5 - health_record['mood_rating']) * 0.15
                
                # Add some randomness
                random_factor = np.random.uniform(0.8, 1.2)
                
                spending_amount = base_spending * stress_multiplier * mood_multiplier * random_factor
                
                spending_data.append({
                    'id': len(spending_data) + 1,
                    'date': health_record['checkin_date'],
                    'amount': round(spending_amount, 2),
                    'category': self._get_spending_category(health_record),
                    'description': f"Spending on {self._get_spending_category(health_record)}"
                })
            
            return spending_data
            
        except Exception as e:
            self.logger.error(f"Error retrieving spending data: {str(e)}")
            return []
    
    def _get_spending_category(self, health_record: Dict) -> str:
        """Determine spending category based on health metrics"""
        stress = health_record['stress_level']
        mood = health_record['mood_rating']
        
        if stress > 7:
            return "comfort_food" if mood < 5 else "entertainment"
        elif mood < 4:
            return "retail_therapy"
        elif health_record['energy_level'] < 4:
            return "convenience_services"
        else:
            return "regular_expenses"
    
    def _align_data_by_date(self, health_data: List[Dict], spending_data: List[Dict]) -> List[Dict]:
        """Align health and spending data by date for correlation analysis"""
        try:
            # Create date mapping for health data
            health_by_date = {record['checkin_date']: record for record in health_data}
            
            aligned_data = []
            for spending_record in spending_data:
                spending_date = spending_record['date']
                
                # Find closest health record (within 3 days)
                closest_health = None
                min_days_diff = float('inf')
                
                for health_date, health_record in health_by_date.items():
                    days_diff = abs((spending_date - health_date).days)
                    if days_diff <= 3 and days_diff < min_days_diff:
                        closest_health = health_record
                        min_days_diff = days_diff
                
                if closest_health:
                    aligned_data.append({
                        'date': spending_date,
                        'stress_level': closest_health['stress_level'],
                        'mood_rating': closest_health['mood_rating'],
                        'energy_level': closest_health['energy_level'],
                        'spending_amount': spending_record['amount'],
                        'spending_category': spending_record['category']
                    })
            
            return aligned_data
            
        except Exception as e:
            self.logger.error(f"Error aligning data by date: {str(e)}")
            return []
    
    def _calculate_correlations(self, health_data: List[Dict], spending_data: List[Dict]) -> Dict[str, CorrelationResult]:
        """Calculate correlations between health metrics and spending"""
        try:
            aligned_data = self._align_data_by_date(health_data, spending_data)
            
            if len(aligned_data) < 3:
                return {}
            
            correlations = {}
            
            # Stress-spending correlation
            correlations['stress_spending'] = self.correlate_stress_to_spending(health_data, spending_data)
            
            # Mood-spending correlation
            mood_levels = [record['mood_rating'] for record in aligned_data]
            spending_amounts = [record['spending_amount'] for record in aligned_data]
            
            if len(mood_levels) >= 3:
                mood_corr, mood_p = stats.pearsonr(mood_levels, spending_amounts)
                correlations['mood_spending'] = CorrelationResult(
                    metric="mood_spending",
                    correlation_coefficient=mood_corr,
                    p_value=mood_p,
                    significance="significant" if mood_p < 0.05 else "not_significant",
                    sample_size=len(aligned_data),
                    trend_direction="positive" if mood_corr > 0 else "negative",
                    strength=self._get_correlation_strength(abs(mood_corr)),
                    confidence_interval=self._calculate_confidence_interval(mood_corr, len(aligned_data))
                )
            
            return correlations
            
        except Exception as e:
            self.logger.error(f"Error calculating correlations: {str(e)}")
            return {}
    
    def _analyze_spending_patterns(self, health_data: List[Dict], spending_data: List[Dict]) -> List[SpendingPattern]:
        """Analyze spending patterns in relation to health metrics"""
        try:
            patterns = []
            aligned_data = self._align_data_by_date(health_data, spending_data)
            
            if not aligned_data:
                return patterns
            
            # Group by spending category
            category_data = {}
            for record in aligned_data:
                category = record['spending_category']
                if category not in category_data:
                    category_data[category] = []
                category_data[category].append(record)
            
            # Analyze each category
            for category, records in category_data.items():
                if len(records) < 2:
                    continue
                
                amounts = [record['spending_amount'] for record in records]
                stress_levels = [record['stress_level'] for record in records]
                mood_levels = [record['mood_rating'] for record in records]
                
                # Calculate correlations
                stress_corr = stats.pearsonr(stress_levels, amounts)[0] if len(stress_levels) > 1 else 0
                mood_corr = stats.pearsonr(mood_levels, amounts)[0] if len(mood_levels) > 1 else 0
                
                # Determine trend
                trend = "increasing" if stress_corr > 0.3 else "decreasing" if stress_corr < -0.3 else "stable"
                
                # Assess risk level
                risk_level = "high" if abs(stress_corr) > 0.5 else "medium" if abs(stress_corr) > 0.3 else "low"
                
                patterns.append(SpendingPattern(
                    category=category,
                    average_amount=statistics.mean(amounts),
                    frequency=len(records),
                    correlation_with_stress=stress_corr,
                    correlation_with_mood=mood_corr,
                    trend=trend,
                    risk_level=risk_level
                ))
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing spending patterns: {str(e)}")
            return []
    
    def _generate_insights(self, correlations: Dict, patterns: List[SpendingPattern], 
                          health_data: List[Dict], spending_data: List[Dict]) -> List[HealthInsight]:
        """Generate actionable insights from the analysis"""
        try:
            insights = []
            
            # Stress-spending insight
            if 'stress_spending' in correlations:
                stress_corr = correlations['stress_spending']
                if stress_corr.correlation_coefficient > 0.4 and stress_corr.significance == "significant":
                    insights.append(HealthInsight(
                        insight_type="stress_spending",
                        title="High Stress Leads to Increased Spending",
                        description=f"Your spending increases by {abs(stress_corr.correlation_coefficient):.1%} when stress levels are high",
                        impact_score=stress_corr.correlation_coefficient,
                        recommendations=[
                            "Practice stress-reduction techniques before making purchases",
                            "Set spending limits during high-stress periods",
                            "Consider stress management activities as alternatives to shopping"
                        ],
                        data_points={
                            'correlation': stress_corr.correlation_coefficient,
                            'confidence': stress_corr.confidence_interval,
                            'sample_size': stress_corr.sample_size
                        }
                    ))
            
            # Mood-spending insight
            if 'mood_spending' in correlations:
                mood_corr = correlations['mood_spending']
                if mood_corr.correlation_coefficient < -0.3 and mood_corr.significance == "significant":
                    insights.append(HealthInsight(
                        insight_type="mood_spending",
                        title="Low Mood Triggers Impulse Spending",
                        description=f"Spending increases by {abs(mood_corr.correlation_coefficient):.1%} when mood is low",
                        impact_score=abs(mood_corr.correlation_coefficient),
                        recommendations=[
                            "Identify mood-boosting activities that don't involve spending",
                            "Create a 'mood improvement' budget separate from regular expenses",
                            "Practice mindfulness before making purchases during low moods"
                        ],
                        data_points={
                            'correlation': mood_corr.correlation_coefficient,
                            'confidence': mood_corr.confidence_interval,
                            'sample_size': mood_corr.sample_size
                        }
                    ))
            
            # High-risk spending patterns
            high_risk_patterns = [p for p in patterns if p.risk_level == "high"]
            if high_risk_patterns:
                insights.append(HealthInsight(
                    insight_type="high_risk_patterns",
                    title="High-Risk Spending Categories Identified",
                    description=f"Found {len(high_risk_patterns)} spending categories strongly influenced by health factors",
                    impact_score=0.8,
                    recommendations=[
                        f"Monitor spending in {', '.join([p.category for p in high_risk_patterns])}",
                        "Set up spending alerts for these categories",
                        "Create alternative coping strategies for these spending triggers"
                    ],
                    data_points={
                        'high_risk_categories': [p.category for p in high_risk_patterns],
                        'correlations': {p.category: p.correlation_with_stress for p in high_risk_patterns}
                    }
                ))
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            return []
    
    def _analyze_trends(self, health_data: List[Dict], spending_data: List[Dict]) -> Dict[str, Any]:
        """Analyze trends over time"""
        try:
            if len(health_data) < 4 or len(spending_data) < 4:
                return {'error': 'Insufficient data for trend analysis'}
            
            # Sort data by date
            health_data.sort(key=lambda x: x['checkin_date'])
            spending_data.sort(key=lambda x: x['date'])
            
            # Calculate trends
            stress_trend = self._calculate_trend([record['stress_level'] for record in health_data])
            mood_trend = self._calculate_trend([record['mood_rating'] for record in health_data])
            spending_trend = self._calculate_trend([record['amount'] for record in spending_data])
            
            return {
                'stress_trend': stress_trend,
                'mood_trend': mood_trend,
                'spending_trend': spending_trend,
                'trend_correlation': {
                    'stress_spending_trend': stats.pearsonr(stress_trend['values'], spending_trend['values'])[0] if len(stress_trend['values']) > 1 else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {str(e)}")
            return {'error': f'Trend analysis failed: {str(e)}'}
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend for a series of values"""
        try:
            if len(values) < 2:
                return {'direction': 'stable', 'slope': 0, 'values': values}
            
            x = list(range(len(values)))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            direction = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
            
            return {
                'direction': direction,
                'slope': slope,
                'r_squared': r_value ** 2,
                'p_value': p_value,
                'values': values
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating trend: {str(e)}")
            return {'direction': 'error', 'slope': 0, 'values': values}
    
    def _assess_financial_risk(self, correlations: Dict, patterns: List[SpendingPattern]) -> Dict[str, Any]:
        """Assess overall financial risk based on health-spending correlations"""
        try:
            risk_score = 0.0
            risk_factors = []
            
            # Stress correlation risk
            if 'stress_spending' in correlations:
                stress_corr = correlations['stress_spending']
                if stress_corr.correlation_coefficient > 0.5:
                    risk_score += 0.4
                    risk_factors.append("High stress-spending correlation")
                elif stress_corr.correlation_coefficient > 0.3:
                    risk_score += 0.2
                    risk_factors.append("Moderate stress-spending correlation")
            
            # High-risk patterns
            high_risk_count = len([p for p in patterns if p.risk_level == "high"])
            if high_risk_count > 0:
                risk_score += min(high_risk_count * 0.2, 0.4)
                risk_factors.append(f"{high_risk_count} high-risk spending categories")
            
            # Determine risk level
            if risk_score >= 0.7:
                risk_level = "high"
            elif risk_score >= 0.4:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'recommendations': self._get_risk_recommendations(risk_level, risk_factors)
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing financial risk: {str(e)}")
            return {'error': f'Risk assessment failed: {str(e)}'}
    
    def _get_risk_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Get recommendations based on risk level"""
        recommendations = []
        
        if risk_level == "high":
            recommendations.extend([
                "Consider professional financial counseling",
                "Implement strict spending controls during high-stress periods",
                "Develop comprehensive stress management strategies",
                "Set up automatic savings transfers before payday"
            ])
        elif risk_level == "medium":
            recommendations.extend([
                "Monitor spending patterns more closely",
                "Create emergency fund for impulse spending",
                "Practice mindfulness before purchases",
                "Set weekly spending limits"
            ])
        else:
            recommendations.extend([
                "Continue monitoring health-spending patterns",
                "Maintain current financial habits",
                "Consider preventive stress management"
            ])
        
        return recommendations
    
    def _generate_recommendations(self, correlations: Dict, patterns: List[SpendingPattern], 
                                insights: List[HealthInsight]) -> List[Dict]:
        """Generate actionable recommendations"""
        try:
            recommendations = []
            
            # Stress management recommendations
            if 'stress_spending' in correlations and correlations['stress_spending'].correlation_coefficient > 0.3:
                recommendations.append({
                    'category': 'stress_management',
                    'priority': 'high',
                    'title': 'Implement Stress-Reduction Strategies',
                    'description': 'Your spending increases significantly during high-stress periods',
                    'actions': [
                        'Practice daily meditation or deep breathing',
                        'Schedule regular exercise sessions',
                        'Create a stress-relief budget for healthy activities',
                        'Set up spending alerts during high-stress periods'
                    ]
                })
            
            # Budget optimization recommendations
            high_risk_patterns = [p for p in patterns if p.risk_level == "high"]
            if high_risk_patterns:
                recommendations.append({
                    'category': 'budget_optimization',
                    'priority': 'high',
                    'title': 'Optimize Budget for Health-Influenced Spending',
                    'description': f'Found {len(high_risk_patterns)} categories strongly affected by health factors',
                    'actions': [
                        f'Set lower limits for {", ".join([p.category for p in high_risk_patterns])}',
                        'Create separate budgets for health-related spending',
                        'Implement 24-hour waiting period for purchases in these categories',
                        'Track spending triggers and patterns'
                    ]
                })
            
            # Wellness investment recommendations
            if insights:
                recommendations.append({
                    'category': 'wellness_investment',
                    'priority': 'medium',
                    'title': 'Invest in Wellness Activities',
                    'description': 'Preventive wellness spending can reduce impulse purchases',
                    'actions': [
                        'Allocate budget for gym memberships or fitness classes',
                        'Invest in mindfulness apps or meditation courses',
                        'Schedule regular wellness check-ins',
                        'Create a wellness rewards system'
                    ]
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def _get_correlation_strength(self, correlation_value: float) -> str:
        """Determine correlation strength based on value"""
        abs_value = abs(correlation_value)
        if abs_value >= 0.7:
            return "strong"
        elif abs_value >= 0.5:
            return "moderate"
        elif abs_value >= 0.3:
            return "weak"
        else:
            return "very_weak"
    
    def _calculate_confidence_interval(self, correlation: float, sample_size: int) -> Tuple[float, float]:
        """Calculate confidence interval for correlation coefficient"""
        try:
            if sample_size < 3:
                return (0.0, 0.0)
            
            # Simplified confidence interval calculation
            z_score = 1.96  # 95% confidence level
            se = np.sqrt((1 - correlation**2) / (sample_size - 2))
            
            lower = correlation - z_score * se
            upper = correlation + z_score * se
            
            return (max(-1.0, lower), min(1.0, upper))
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence interval: {str(e)}")
            return (0.0, 0.0)
    
    def _analyze_spending_spike(self, record: Dict) -> Optional[Dict]:
        """Analyze a spending spike for potential triggers"""
        try:
            triggers = []
            
            if record['stress_level'] > 7:
                triggers.append('high_stress')
            if record['mood_rating'] < 4:
                triggers.append('low_mood')
            if record['energy_level'] < 4:
                triggers.append('low_energy')
            
            if triggers:
                return {
                    'date': record['date'],
                    'spending_amount': record['spending_amount'],
                    'triggers': triggers,
                    'confidence': len(triggers) / 3.0  # Simple confidence score
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing spending spike: {str(e)}")
            return None
    
    def _summarize_triggers(self, triggers: List[Dict]) -> List[Dict]:
        """Summarize and rank spending triggers"""
        try:
            if not triggers:
                return []
            
            # Count trigger occurrences
            trigger_counts = {}
            for trigger in triggers:
                for trigger_type in trigger.get('triggers', []):
                    trigger_counts[trigger_type] = trigger_counts.get(trigger_type, 0) + 1
            
            # Create summary
            summary = []
            total_spikes = len(triggers)
            
            for trigger_type, count in trigger_counts.items():
                summary.append({
                    'trigger_type': trigger_type,
                    'frequency': count,
                    'percentage': (count / total_spikes) * 100,
                    'average_spending': statistics.mean([
                        t['spending_amount'] for t in triggers 
                        if trigger_type in t.get('triggers', [])
                    ]),
                    'risk_level': 'high' if count > total_spikes * 0.5 else 'medium'
                })
            
            return sorted(summary, key=lambda x: x['frequency'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error summarizing triggers: {str(e)}")
            return []
    
    def _generate_mood_insights(self, mood_analysis: Dict) -> List[str]:
        """Generate insights from mood-spending analysis"""
        try:
            insights = []
            
            # Find mood with highest spending
            if mood_analysis:
                highest_spending_mood = max(mood_analysis.keys(), 
                                          key=lambda x: mood_analysis[x]['average_spending'])
                lowest_spending_mood = min(mood_analysis.keys(), 
                                         key=lambda x: mood_analysis[x]['average_spending'])
                
                insights.append(f"Highest spending occurs during mood level {highest_spending_mood}")
                insights.append(f"Lowest spending occurs during mood level {lowest_spending_mood}")
                
                # Check for significant differences
                high_spending = mood_analysis[highest_spending_mood]['average_spending']
                low_spending = mood_analysis[lowest_spending_mood]['average_spending']
                
                if high_spending > low_spending * 1.5:
                    insights.append("Significant spending variation based on mood levels")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating mood insights: {str(e)}")
            return []
    
    def _calculate_stress_budget(self, analysis: Dict) -> float:
        """Calculate recommended stress management budget"""
        try:
            data_summary = analysis.get('data_summary', {})
            avg_weekly_spending = data_summary.get('average_weekly_spending', 100.0)
            
            # Recommend 10-20% of average weekly spending for stress management
            return round(avg_weekly_spending * 0.15, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating stress budget: {str(e)}")
            return 50.0
    
    def _calculate_mood_budget(self, analysis: Dict) -> float:
        """Calculate recommended mood improvement budget"""
        try:
            data_summary = analysis.get('data_summary', {})
            avg_weekly_spending = data_summary.get('average_weekly_spending', 100.0)
            
            # Recommend 5-15% of average weekly spending for mood improvement
            return round(avg_weekly_spending * 0.10, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating mood budget: {str(e)}")
            return 30.0 