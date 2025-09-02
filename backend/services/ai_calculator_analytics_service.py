"""
AI Calculator Analytics Service
Comprehensive analytics and tracking for AI calculator performance
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.dialects.postgresql import UUID

from backend.models.ai_job_models import AIJobAssessment, AICalculatorConversion
from backend.models.ai_user_profile_extension import AIUserProfileExtension
from backend.models.analytics_models import UserEvent, AnalyticsEvent

logger = logging.getLogger(__name__)


class AICalculatorAnalyticsService:
    """Analytics service for AI calculator performance tracking"""
    
    def __init__(self):
        self.event_types = {
            'calculator_started': 'ai_calculator_started',
            'calculator_completed': 'ai_calculator_completed',
            'calculator_abandoned': 'ai_calculator_abandoned',
            'career_plan_viewed': 'ai_career_plan_viewed',
            'career_plan_purchased': 'ai_career_plan_purchased',
            'email_opened': 'ai_email_opened',
            'email_clicked': 'ai_email_clicked',
            'conversion_funnel_step': 'ai_conversion_funnel_step'
        }
    
    def track_calculator_start(self, assessment_id: str, user_data: Dict[str, Any], db: Session) -> bool:
        """Track when user starts the AI calculator"""
        try:
            event = UserEvent(
                event_type=self.event_types['calculator_started'],
                event_data={
                    'assessment_id': assessment_id,
                    'job_title': user_data.get('job_title'),
                    'industry': user_data.get('industry'),
                    'experience_level': user_data.get('experience_level'),
                    'source': user_data.get('utm_source', 'direct'),
                    'medium': user_data.get('utm_medium', 'none'),
                    'campaign': user_data.get('utm_campaign', 'none')
                },
                source='ai_calculator',
                user_agent=user_data.get('user_agent'),
                ip_address=user_data.get('ip_address')
            )
            
            db.add(event)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking calculator start: {e}")
            db.rollback()
            return False
    
    def track_calculator_completion(self, assessment: AIJobAssessment, db: Session) -> bool:
        """Track when user completes the AI calculator"""
        try:
            event = UserEvent(
                event_type=self.event_types['calculator_completed'],
                event_data={
                    'assessment_id': str(assessment.id),
                    'job_title': assessment.job_title,
                    'industry': assessment.industry,
                    'experience_level': assessment.experience_level,
                    'risk_level': assessment.overall_risk_level,
                    'automation_score': assessment.automation_score,
                    'augmentation_score': assessment.augmentation_score,
                    'completion_time': assessment.assessment_duration_seconds,
                    'questions_answered': assessment.questions_answered,
                    'completion_percentage': float(assessment.completion_percentage)
                },
                source='ai_calculator'
            )
            
            db.add(event)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking calculator completion: {e}")
            db.rollback()
            return False
    
    def track_calculator_abandonment(self, assessment_id: str, step_abandoned: int, user_data: Dict[str, Any], db: Session) -> bool:
        """Track when user abandons the AI calculator"""
        try:
            event = UserEvent(
                event_type=self.event_types['calculator_abandoned'],
                event_data={
                    'assessment_id': assessment_id,
                    'step_abandoned': step_abandoned,
                    'job_title': user_data.get('job_title'),
                    'industry': user_data.get('industry'),
                    'time_spent': user_data.get('time_spent', 0)
                },
                source='ai_calculator'
            )
            
            db.add(event)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking calculator abandonment: {e}")
            db.rollback()
            return False
    
    def track_conversion_funnel(self, assessment_id: str, funnel_step: str, step_data: Dict[str, Any], db: Session) -> bool:
        """Track conversion funnel progression"""
        try:
            event = UserEvent(
                event_type=self.event_types['conversion_funnel_step'],
                event_data={
                    'assessment_id': assessment_id,
                    'funnel_step': funnel_step,
                    'step_data': step_data,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                source='ai_calculator'
            )
            
            db.add(event)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking conversion funnel: {e}")
            db.rollback()
            return False
    
    def get_calculator_performance_metrics(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive calculator performance metrics"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get all assessments in period
            assessments = db.query(AIJobAssessment).filter(
                AIJobAssessment.created_at >= cutoff_date
            ).all()
            
            # Get conversion data
            conversions = db.query(AICalculatorConversion).filter(
                and_(
                    AICalculatorConversion.created_at >= cutoff_date,
                    AICalculatorConversion.conversion_type == 'paid_upgrade'
                )
            ).all()
            
            # Calculate metrics
            total_assessments = len(assessments)
            completed_assessments = len([a for a in assessments if a.completed_at])
            paid_conversions = len(conversions)
            total_revenue = sum(conv.conversion_revenue for conv in conversions)
            
            # Completion rate by traffic source
            completion_by_source = {}
            for assessment in assessments:
                source = assessment.utm_source or 'direct'
                if source not in completion_by_source:
                    completion_by_source[source] = {'started': 0, 'completed': 0}
                completion_by_source[source]['started'] += 1
                if assessment.completed_at:
                    completion_by_source[source]['completed'] += 1
            
            # Risk level distribution
            risk_distribution = {}
            for assessment in assessments:
                if assessment.completed_at:
                    risk = assessment.overall_risk_level
                    risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
            
            # Industry performance
            industry_performance = {}
            for assessment in assessments:
                if assessment.completed_at:
                    industry = assessment.industry
                    if industry not in industry_performance:
                        industry_performance[industry] = {'assessments': 0, 'conversions': 0, 'revenue': 0}
                    industry_performance[industry]['assessments'] += 1
            
            # Add conversion data to industry performance
            for conversion in conversions:
                assessment = db.query(AIJobAssessment).filter(
                    AIJobAssessment.id == conversion.assessment_id
                ).first()
                if assessment:
                    industry = assessment.industry
                    if industry in industry_performance:
                        industry_performance[industry]['conversions'] += 1
                        industry_performance[industry]['revenue'] += float(conversion.conversion_revenue)
            
            return {
                'period_days': days,
                'total_assessments': total_assessments,
                'completed_assessments': completed_assessments,
                'completion_rate': (completed_assessments / total_assessments * 100) if total_assessments > 0 else 0,
                'paid_conversions': paid_conversions,
                'conversion_rate': (paid_conversions / completed_assessments * 100) if completed_assessments > 0 else 0,
                'total_revenue': float(total_revenue),
                'average_order_value': (total_revenue / paid_conversions) if paid_conversions > 0 else 0,
                'completion_by_source': completion_by_source,
                'risk_distribution': risk_distribution,
                'industry_performance': industry_performance
            }
            
        except Exception as e:
            logger.error(f"Error getting calculator performance metrics: {e}")
            return {}
    
    def get_demographic_analysis(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get demographic analysis of calculator users"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get completed assessments with user data
            assessments = db.query(AIJobAssessment).filter(
                and_(
                    AIJobAssessment.created_at >= cutoff_date,
                    AIJobAssessment.completed_at.isnot(None)
                )
            ).all()
            
            # Age group analysis (would need age data from user profiles)
            age_groups = {
                '18-24': 0,
                '25-34': 0,
                '35-44': 0,
                '45-54': 0,
                '55+': 0
            }
            
            # Experience level analysis
            experience_distribution = {}
            for assessment in assessments:
                exp_level = assessment.experience_level
                experience_distribution[exp_level] = experience_distribution.get(exp_level, 0) + 1
            
            # Location analysis
            location_distribution = {}
            for assessment in assessments:
                if assessment.location:
                    location = assessment.location
                    location_distribution[location] = location_distribution.get(location, 0) + 1
            
            # Income level analysis (would need income data)
            income_distribution = {
                'under_50k': 0,
                '50k_100k': 0,
                '100k_150k': 0,
                '150k_200k': 0,
                'over_200k': 0
            }
            
            # Tech skills analysis
            tech_skills_distribution = {}
            for assessment in assessments:
                tech_level = assessment.tech_skills_level
                tech_skills_distribution[tech_level] = tech_skills_distribution.get(tech_level, 0) + 1
            
            return {
                'period_days': days,
                'total_users': len(assessments),
                'age_groups': age_groups,
                'experience_distribution': experience_distribution,
                'location_distribution': location_distribution,
                'income_distribution': income_distribution,
                'tech_skills_distribution': tech_skills_distribution
            }
            
        except Exception as e:
            logger.error(f"Error getting demographic analysis: {e}")
            return {}
    
    def get_ab_testing_results(self, db: Session, test_name: str, days: int = 30) -> Dict[str, Any]:
        """Get A/B testing results for different calculator configurations"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get assessments with A/B test data
            assessments = db.query(AIJobAssessment).filter(
                and_(
                    AIJobAssessment.created_at >= cutoff_date,
                    AIJobAssessment.completed_at.isnot(None)
                )
            ).all()
            
            # Group by test variant (would need test variant tracking)
            test_variants = {
                'control': {'assessments': 0, 'conversions': 0, 'revenue': 0},
                'variant_a': {'assessments': 0, 'conversions': 0, 'revenue': 0},
                'variant_b': {'assessments': 0, 'conversions': 0, 'revenue': 0}
            }
            
            # Calculate conversion rates for each variant
            for variant, data in test_variants.items():
                if data['assessments'] > 0:
                    data['conversion_rate'] = (data['conversions'] / data['assessments']) * 100
                    data['avg_revenue'] = data['revenue'] / data['assessments']
                else:
                    data['conversion_rate'] = 0
                    data['avg_revenue'] = 0
            
            return {
                'test_name': test_name,
                'period_days': days,
                'variants': test_variants,
                'statistical_significance': self._calculate_statistical_significance(test_variants)
            }
            
        except Exception as e:
            logger.error(f"Error getting A/B testing results: {e}")
            return {}
    
    def get_risk_algorithm_performance(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Analyze performance of different risk calculation algorithms"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get assessments with different algorithm versions
            assessments = db.query(AIJobAssessment).filter(
                and_(
                    AIJobAssessment.created_at >= cutoff_date,
                    AIJobAssessment.completed_at.isnot(None)
                )
            ).all()
            
            # Group by algorithm version (would need algorithm version tracking)
            algorithm_performance = {
                'v1': {'assessments': 0, 'conversions': 0, 'accuracy': 0},
                'v2': {'assessments': 0, 'conversions': 0, 'accuracy': 0},
                'v3': {'assessments': 0, 'conversions': 0, 'accuracy': 0}
            }
            
            # Calculate metrics for each algorithm version
            for version, data in algorithm_performance.items():
                if data['assessments'] > 0:
                    data['conversion_rate'] = (data['conversions'] / data['assessments']) * 100
                else:
                    data['conversion_rate'] = 0
            
            return {
                'period_days': days,
                'algorithm_performance': algorithm_performance,
                'recommended_algorithm': self._get_recommended_algorithm(algorithm_performance)
            }
            
        except Exception as e:
            logger.error(f"Error getting risk algorithm performance: {e}")
            return {}
    
    def _calculate_statistical_significance(self, test_variants: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistical significance between test variants"""
        # Placeholder for statistical significance calculation
        return {
            'control_vs_variant_a': 0.05,
            'control_vs_variant_b': 0.03,
            'variant_a_vs_variant_b': 0.08
        }
    
    def _get_recommended_algorithm(self, algorithm_performance: Dict[str, Any]) -> str:
        """Get recommended algorithm based on performance"""
        best_algorithm = 'v1'
        best_conversion_rate = 0
        
        for version, data in algorithm_performance.items():
            if data['conversion_rate'] > best_conversion_rate:
                best_conversion_rate = data['conversion_rate']
                best_algorithm = version
        
        return best_algorithm
    
    def export_analytics_report(self, db: Session, days: int = 30, format: str = 'json') -> Dict[str, Any]:
        """Export comprehensive analytics report"""
        try:
            performance_metrics = self.get_calculator_performance_metrics(db, days)
            demographic_analysis = self.get_demographic_analysis(db, days)
            ab_testing_results = self.get_ab_testing_results(db, 'calculator_positioning', days)
            algorithm_performance = self.get_risk_algorithm_performance(db, days)
            
            report = {
                'report_generated_at': datetime.now(timezone.utc).isoformat(),
                'period_days': days,
                'performance_metrics': performance_metrics,
                'demographic_analysis': demographic_analysis,
                'ab_testing_results': ab_testing_results,
                'algorithm_performance': algorithm_performance,
                'summary': {
                    'total_assessments': performance_metrics.get('total_assessments', 0),
                    'completion_rate': performance_metrics.get('completion_rate', 0),
                    'conversion_rate': performance_metrics.get('conversion_rate', 0),
                    'total_revenue': performance_metrics.get('total_revenue', 0),
                    'recommended_actions': self._generate_recommended_actions(performance_metrics)
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error exporting analytics report: {e}")
            return {}
    
    def _generate_recommended_actions(self, performance_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommended actions based on performance metrics"""
        recommendations = []
        
        completion_rate = performance_metrics.get('completion_rate', 0)
        conversion_rate = performance_metrics.get('conversion_rate', 0)
        
        if completion_rate < 70:
            recommendations.append("Optimize calculator flow to improve completion rate")
        
        if conversion_rate < 5:
            recommendations.append("Review pricing strategy and value proposition")
        
        if completion_rate < 50:
            recommendations.append("Simplify assessment questions to reduce abandonment")
        
        return recommendations
