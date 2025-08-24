"""
Business Metrics Tracking for Job Recommendation Engine
Monitors conversion rates, user satisfaction, revenue impact, and cost optimization
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, Counter

from backend.services.cache_service import CacheService
from backend.analytics.analytics_service import AnalyticsService, EventType

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of business metrics"""
    CONVERSION = "conversion"
    ENGAGEMENT = "engagement"
    SATISFACTION = "satisfaction"
    REVENUE = "revenue"
    COST = "cost"
    RETENTION = "retention"
    REFERRAL = "referral"

class ConversionStage(Enum):
    """Conversion funnel stages"""
    RESUME_UPLOAD = "resume_upload"
    RECOMMENDATION_VIEW = "recommendation_view"
    RECOMMENDATION_INTERACTION = "recommendation_interaction"
    JOB_APPLICATION = "job_application"
    APPLICATION_SUCCESS = "application_success"
    SALARY_INCREASE = "salary_increase"
    PREMIUM_CONVERSION = "premium_conversion"

@dataclass
class ConversionMetrics:
    """Conversion funnel metrics"""
    stage: ConversionStage
    total_users: int
    converted_users: int
    conversion_rate: float
    drop_off_rate: float
    avg_time_to_convert: float
    revenue_per_conversion: float

@dataclass
class UserSatisfactionMetrics:
    """User satisfaction metrics"""
    user_id: str
    session_id: str
    satisfaction_score: float
    feedback_text: Optional[str] = None
    feature_ratings: Dict[str, float] = None
    nps_score: Optional[int] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class RevenueMetrics:
    """Revenue impact metrics"""
    user_id: str
    original_salary: float
    new_salary: float
    salary_increase: float
    salary_increase_percentage: float
    estimated_lifetime_value: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class CostMetrics:
    """Cost optimization metrics"""
    api_calls: int
    api_cost: float
    hosting_cost: float
    database_cost: float
    cdn_cost: float
    total_cost: float
    cost_per_user: float
    cost_per_conversion: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class BusinessMetricsService:
    """Business metrics tracking and analysis service"""
    
    def __init__(self, cache_service: CacheService, analytics_service: AnalyticsService):
        """Initialize business metrics service"""
        self.cache_service = cache_service
        self.analytics_service = analytics_service
        
        # Cost tracking
        self.api_costs = {
            'resume_parsing': 0.01,  # $0.01 per resume
            'job_search': 0.05,      # $0.05 per search
            'income_comparison': 0.02, # $0.02 per comparison
            'recommendation_generation': 0.03  # $0.03 per recommendation
        }
        
        self.hosting_costs = {
            'compute': 0.10,  # $0.10 per hour
            'memory': 0.05,   # $0.05 per GB-hour
            'storage': 0.02   # $0.02 per GB-month
        }
    
    def track_conversion_funnel(self, user_id: str, session_id: str, stage: ConversionStage) -> None:
        """Track user progression through conversion funnel"""
        funnel_data = {
            'user_id': user_id,
            'session_id': session_id,
            'stage': stage.value,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in cache
        cache_key = f"conversion_funnel:{session_id}"
        funnel_cache = self.cache_service.get(cache_key) or []
        funnel_cache.append(funnel_data)
        self.cache_service.set(cache_key, funnel_cache, ttl=86400)  # 24 hours
        
        # Track as analytics event
        self.analytics_service.track_event(
            user_id=user_id,
            session_id=session_id,
            event_type=EventType.CONVERSION_EVENT,
            metadata={'conversion_stage': stage.value}
        )
        
        # Update conversion metrics
        self.update_conversion_metrics(stage)
    
    def track_user_satisfaction(self, 
                              user_id: str,
                              session_id: str,
                              satisfaction_score: float,
                              feedback_text: Optional[str] = None,
                              feature_ratings: Optional[Dict[str, float]] = None,
                              nps_score: Optional[int] = None) -> None:
        """Track user satisfaction metrics"""
        satisfaction = UserSatisfactionMetrics(
            user_id=user_id,
            session_id=session_id,
            satisfaction_score=satisfaction_score,
            feedback_text=feedback_text,
            feature_ratings=feature_ratings or {},
            nps_score=nps_score
        )
        
        # Store in cache
        cache_key = f"user_satisfaction:{user_id}:{session_id}"
        self.cache_service.set(cache_key, asdict(satisfaction), ttl=86400)  # 24 hours
        
        # Track as analytics event
        self.analytics_service.track_event(
            user_id=user_id,
            session_id=session_id,
            event_type=EventType.FEEDBACK_SUBMIT,
            metadata={
                'satisfaction_score': satisfaction_score,
                'nps_score': nps_score,
                'feature_ratings': feature_ratings
            }
        )
        
        # Update satisfaction metrics
        self.update_satisfaction_metrics(satisfaction)
    
    def track_salary_increase(self,
                            user_id: str,
                            original_salary: float,
                            new_salary: float,
                            job_title: str,
                            company: str) -> None:
        """Track salary increase and revenue impact"""
        salary_increase = new_salary - original_salary
        salary_increase_percentage = (salary_increase / original_salary) * 100 if original_salary > 0 else 0
        
        # Estimate lifetime value (simplified calculation)
        estimated_lifetime_value = salary_increase * 5  # 5 years of increased salary
        
        revenue_metrics = RevenueMetrics(
            user_id=user_id,
            original_salary=original_salary,
            new_salary=new_salary,
            salary_increase=salary_increase,
            salary_increase_percentage=salary_increase_percentage,
            estimated_lifetime_value=estimated_lifetime_value
        )
        
        # Store in cache
        cache_key = f"revenue_metrics:{user_id}"
        self.cache_service.set(cache_key, asdict(revenue_metrics), ttl=2592000)  # 30 days
        
        # Track as analytics event
        self.analytics_service.track_event(
            user_id=user_id,
            session_id='',
            event_type=EventType.CONVERSION_EVENT,
            metadata={
                'salary_increase': salary_increase,
                'salary_increase_percentage': salary_increase_percentage,
                'job_title': job_title,
                'company': company,
                'estimated_lifetime_value': estimated_lifetime_value
            }
        )
        
        # Update revenue metrics
        self.update_revenue_metrics(revenue_metrics)
    
    def track_api_usage(self, api_type: str, calls: int = 1) -> None:
        """Track API usage and costs"""
        # Get current API usage from cache
        usage_key = f"api_usage:{datetime.now().strftime('%Y%m%d')}"
        api_usage = self.cache_service.get(usage_key) or defaultdict(int)
        
        api_usage[api_type] += calls
        
        # Calculate cost
        cost = api_usage[api_type] * self.api_costs.get(api_type, 0.01)
        api_usage[f"{api_type}_cost"] = cost
        
        self.cache_service.set(usage_key, dict(api_usage), ttl=86400)  # 24 hours
        
        logger.info(f"API usage tracked: {api_type} - {calls} calls, cost: ${cost:.4f}")
    
    def track_hosting_costs(self, compute_hours: float, memory_gb_hours: float, storage_gb: float) -> None:
        """Track hosting costs"""
        compute_cost = compute_hours * self.hosting_costs['compute']
        memory_cost = memory_gb_hours * self.hosting_costs['memory']
        storage_cost = storage_gb * self.hosting_costs['storage']
        total_cost = compute_cost + memory_cost + storage_cost
        
        cost_metrics = CostMetrics(
            api_calls=0,
            api_cost=0.0,
            hosting_cost=total_cost,
            database_cost=0.0,
            cdn_cost=0.0,
            total_cost=total_cost,
            cost_per_user=0.0,
            cost_per_conversion=0.0
        )
        
        # Store in cache
        cost_key = f"hosting_costs:{datetime.now().strftime('%Y%m%d')}"
        self.cache_service.set(cost_key, asdict(cost_metrics), ttl=86400)  # 24 hours
        
        logger.info(f"Hosting costs tracked: ${total_cost:.4f}")
    
    def get_conversion_funnel_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get conversion funnel analysis"""
        # Get conversion data from cache/database
        conversion_data = self.get_conversion_data(days)
        
        # Calculate funnel metrics
        funnel_stages = list(ConversionStage)
        funnel_metrics = {}
        
        for i, stage in enumerate(funnel_stages):
            stage_users = sum(1 for data in conversion_data if data.get('stage') == stage.value)
            
            if i == 0:
                # First stage - all users who started
                total_users = stage_users
                converted_users = stage_users
                drop_off_rate = 0.0
            else:
                # Subsequent stages
                converted_users = stage_users
                drop_off_rate = ((total_users - converted_users) / total_users) * 100 if total_users > 0 else 0
            
            conversion_rate = (converted_users / total_users) * 100 if total_users > 0 else 0
            
            funnel_metrics[stage.value] = ConversionMetrics(
                stage=stage,
                total_users=total_users,
                converted_users=converted_users,
                conversion_rate=conversion_rate,
                drop_off_rate=drop_off_rate,
                avg_time_to_convert=0.0,  # Would calculate from actual data
                revenue_per_conversion=0.0  # Would calculate from actual data
            )
        
        return {
            'funnel_metrics': {stage: asdict(metrics) for stage, metrics in funnel_metrics.items()},
            'total_conversions': sum(metrics.converted_users for metrics in funnel_metrics.values()),
            'overall_conversion_rate': funnel_metrics[ConversionStage.SALARY_INCREASE.value].conversion_rate if ConversionStage.SALARY_INCREASE.value in funnel_metrics else 0.0,
            'period_days': days
        }
    
    def get_user_satisfaction_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get user satisfaction analysis"""
        # Get satisfaction data from cache/database
        satisfaction_data = self.get_satisfaction_data(days)
        
        if not satisfaction_data:
            return {
                'avg_satisfaction_score': 0.0,
                'nps_score': 0,
                'feedback_analysis': {},
                'feature_ratings': {},
                'total_feedback': 0
            }
        
        # Calculate average satisfaction score
        satisfaction_scores = [data.get('satisfaction_score', 0.0) for data in satisfaction_data]
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0.0
        
        # Calculate NPS score
        nps_scores = [data.get('nps_score', 0) for data in satisfaction_data if data.get('nps_score') is not None]
        promoters = sum(1 for score in nps_scores if score >= 9)
        detractors = sum(1 for score in nps_scores if score <= 6)
        nps_score = ((promoters - detractors) / len(nps_scores)) * 100 if nps_scores else 0
        
        # Analyze feature ratings
        feature_ratings = defaultdict(list)
        for data in satisfaction_data:
            ratings = data.get('feature_ratings', {})
            for feature, rating in ratings.items():
                feature_ratings[feature].append(rating)
        
        avg_feature_ratings = {}
        for feature, ratings in feature_ratings.items():
            avg_feature_ratings[feature] = sum(ratings) / len(ratings)
        
        # Analyze feedback text (simplified)
        feedback_texts = [data.get('feedback_text', '') for data in satisfaction_data if data.get('feedback_text')]
        feedback_analysis = self.analyze_feedback_sentiment(feedback_texts)
        
        return {
            'avg_satisfaction_score': avg_satisfaction,
            'nps_score': nps_score,
            'feedback_analysis': feedback_analysis,
            'feature_ratings': avg_feature_ratings,
            'total_feedback': len(satisfaction_data),
            'satisfaction_distribution': self.get_satisfaction_distribution(satisfaction_scores)
        }
    
    def get_revenue_impact_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue impact analysis"""
        # Get revenue data from cache/database
        revenue_data = self.get_revenue_data(days)
        
        if not revenue_data:
            return {
                'total_salary_increases': 0,
                'avg_salary_increase': 0.0,
                'total_revenue_impact': 0.0,
                'avg_lifetime_value': 0.0,
                'revenue_by_demographic': {},
                'revenue_by_industry': {}
            }
        
        # Calculate revenue metrics
        total_salary_increases = len(revenue_data)
        total_salary_increase_amount = sum(data.get('salary_increase', 0.0) for data in revenue_data)
        avg_salary_increase = total_salary_increase_amount / total_salary_increases if total_salary_increases > 0 else 0.0
        
        total_lifetime_value = sum(data.get('estimated_lifetime_value', 0.0) for data in revenue_data)
        avg_lifetime_value = total_lifetime_value / total_salary_increases if total_salary_increases > 0 else 0.0
        
        # Analyze by demographic (would need demographic data)
        revenue_by_demographic = self.analyze_revenue_by_demographic(revenue_data)
        revenue_by_industry = self.analyze_revenue_by_industry(revenue_data)
        
        return {
            'total_salary_increases': total_salary_increases,
            'total_salary_increase_amount': total_salary_increase_amount,
            'avg_salary_increase': avg_salary_increase,
            'total_revenue_impact': total_lifetime_value,
            'avg_lifetime_value': avg_lifetime_value,
            'revenue_by_demographic': revenue_by_demographic,
            'revenue_by_industry': revenue_by_industry,
            'salary_increase_distribution': self.get_salary_increase_distribution(revenue_data)
        }
    
    def get_cost_optimization_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get cost optimization analysis"""
        # Get cost data from cache/database
        cost_data = self.get_cost_data(days)
        
        if not cost_data:
            return {
                'total_cost': 0.0,
                'cost_breakdown': {},
                'cost_per_user': 0.0,
                'cost_per_conversion': 0.0,
                'optimization_recommendations': []
            }
        
        # Calculate cost metrics
        total_cost = sum(data.get('total_cost', 0.0) for data in cost_data)
        
        # Get user and conversion counts
        total_users = self.get_total_users(days)
        total_conversions = self.get_total_conversions(days)
        
        cost_per_user = total_cost / total_users if total_users > 0 else 0.0
        cost_per_conversion = total_cost / total_conversions if total_conversions > 0 else 0.0
        
        # Cost breakdown
        cost_breakdown = {
            'api_costs': sum(data.get('api_cost', 0.0) for data in cost_data),
            'hosting_costs': sum(data.get('hosting_cost', 0.0) for data in cost_data),
            'database_costs': sum(data.get('database_cost', 0.0) for data in cost_data),
            'cdn_costs': sum(data.get('cdn_cost', 0.0) for data in cost_data)
        }
        
        # Generate optimization recommendations
        optimization_recommendations = self.generate_cost_optimization_recommendations(
            cost_breakdown, cost_per_user, cost_per_conversion
        )
        
        return {
            'total_cost': total_cost,
            'cost_breakdown': cost_breakdown,
            'cost_per_user': cost_per_user,
            'cost_per_conversion': cost_per_conversion,
            'optimization_recommendations': optimization_recommendations,
            'cost_trends': self.get_cost_trends(cost_data)
        }
    
    def update_conversion_metrics(self, stage: ConversionStage) -> None:
        """Update conversion metrics in cache"""
        metrics_key = f"conversion_metrics:{stage.value}"
        metrics = self.cache_service.get(metrics_key) or {
            'total_users': 0,
            'converted_users': 0,
            'last_updated': datetime.now().isoformat()
        }
        
        metrics['total_users'] += 1
        if stage in [ConversionStage.JOB_APPLICATION, ConversionStage.APPLICATION_SUCCESS, ConversionStage.SALARY_INCREASE]:
            metrics['converted_users'] += 1
        
        metrics['last_updated'] = datetime.now().isoformat()
        self.cache_service.set(metrics_key, metrics, ttl=86400)  # 24 hours
    
    def update_satisfaction_metrics(self, satisfaction: UserSatisfactionMetrics) -> None:
        """Update satisfaction metrics in cache"""
        metrics_key = f"satisfaction_metrics:{datetime.now().strftime('%Y%m%d')}"
        metrics = self.cache_service.get(metrics_key) or {
            'total_feedback': 0,
            'total_score': 0.0,
            'nps_scores': [],
            'feature_ratings': defaultdict(list)
        }
        
        metrics['total_feedback'] += 1
        metrics['total_score'] += satisfaction.satisfaction_score
        
        if satisfaction.nps_score is not None:
            metrics['nps_scores'].append(satisfaction.nps_score)
        
        for feature, rating in satisfaction.feature_ratings.items():
            metrics['feature_ratings'][feature].append(rating)
        
        self.cache_service.set(metrics_key, dict(metrics), ttl=86400)  # 24 hours
    
    def update_revenue_metrics(self, revenue: RevenueMetrics) -> None:
        """Update revenue metrics in cache"""
        metrics_key = f"revenue_metrics:{datetime.now().strftime('%Y%m%d')}"
        metrics = self.cache_service.get(metrics_key) or {
            'total_salary_increases': 0,
            'total_increase_amount': 0.0,
            'total_lifetime_value': 0.0
        }
        
        metrics['total_salary_increases'] += 1
        metrics['total_increase_amount'] += revenue.salary_increase
        metrics['total_lifetime_value'] += revenue.estimated_lifetime_value
        
        self.cache_service.set(metrics_key, metrics, ttl=86400)  # 24 hours
    
    def analyze_feedback_sentiment(self, feedback_texts: List[str]) -> Dict[str, Any]:
        """Analyze feedback sentiment (simplified implementation)"""
        # This would typically use NLP/sentiment analysis
        # For now, return placeholder analysis
        return {
            'positive_feedback': len([text for text in feedback_texts if 'good' in text.lower() or 'great' in text.lower()]),
            'negative_feedback': len([text for text in feedback_texts if 'bad' in text.lower() or 'poor' in text.lower()]),
            'neutral_feedback': len([text for text in feedback_texts if text and 'good' not in text.lower() and 'bad' not in text.lower()]),
            'total_feedback': len(feedback_texts)
        }
    
    def get_satisfaction_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Get satisfaction score distribution"""
        distribution = {
            'excellent': 0,
            'good': 0,
            'average': 0,
            'poor': 0
        }
        
        for score in scores:
            if score >= 4.5:
                distribution['excellent'] += 1
            elif score >= 3.5:
                distribution['good'] += 1
            elif score >= 2.5:
                distribution['average'] += 1
            else:
                distribution['poor'] += 1
        
        return distribution
    
    def analyze_revenue_by_demographic(self, revenue_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze revenue impact by demographic (placeholder)"""
        # This would analyze revenue by age, education, industry, etc.
        return {
            'age_ranges': {'25-29': 0.0, '30-34': 0.0, '35-39': 0.0},
            'education_levels': {'bachelor': 0.0, 'master': 0.0, 'doctorate': 0.0},
            'industries': {'technology': 0.0, 'finance': 0.0, 'marketing': 0.0}
        }
    
    def analyze_revenue_by_industry(self, revenue_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze revenue impact by industry (placeholder)"""
        # This would analyze revenue by industry
        return {
            'technology': 0.0,
            'finance': 0.0,
            'marketing': 0.0,
            'consulting': 0.0
        }
    
    def get_salary_increase_distribution(self, revenue_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get salary increase distribution"""
        distribution = {
            '0-10%': 0,
            '10-20%': 0,
            '20-30%': 0,
            '30-50%': 0,
            '50%+': 0
        }
        
        for data in revenue_data:
            percentage = data.get('salary_increase_percentage', 0.0)
            if percentage <= 10:
                distribution['0-10%'] += 1
            elif percentage <= 20:
                distribution['10-20%'] += 1
            elif percentage <= 30:
                distribution['20-30%'] += 1
            elif percentage <= 50:
                distribution['30-50%'] += 1
            else:
                distribution['50%+'] += 1
        
        return distribution
    
    def generate_cost_optimization_recommendations(self, 
                                                 cost_breakdown: Dict[str, float],
                                                 cost_per_user: float,
                                                 cost_per_conversion: float) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # API cost optimization
        if cost_breakdown.get('api_costs', 0) > cost_breakdown.get('hosting_costs', 0):
            recommendations.append("Consider implementing caching to reduce API calls")
            recommendations.append("Optimize API usage patterns to stay within free tiers")
        
        # Hosting cost optimization
        if cost_breakdown.get('hosting_costs', 0) > 0.5:  # More than 50% of total cost
            recommendations.append("Review hosting resource allocation and scaling policies")
            recommendations.append("Consider serverless options for variable workloads")
        
        # Cost per user optimization
        if cost_per_user > 0.10:  # More than $0.10 per user
            recommendations.append("Optimize resource usage to reduce cost per user")
            recommendations.append("Implement user-based resource limits")
        
        # Cost per conversion optimization
        if cost_per_conversion > 5.0:  # More than $5 per conversion
            recommendations.append("Focus on improving conversion rates to reduce cost per conversion")
            recommendations.append("Optimize recommendation quality to increase success rates")
        
        return recommendations
    
    def get_cost_trends(self, cost_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Get cost trends over time"""
        # This would analyze cost trends over the specified period
        return {
            'daily_costs': [0.0] * 30,  # Placeholder
            'api_costs': [0.0] * 30,
            'hosting_costs': [0.0] * 30
        }
    
    # Placeholder methods for data retrieval
    def get_conversion_data(self, days: int) -> List[Dict[str, Any]]:
        """Get conversion data from cache/database (placeholder)"""
        return []
    
    def get_satisfaction_data(self, days: int) -> List[Dict[str, Any]]:
        """Get satisfaction data from cache/database (placeholder)"""
        return []
    
    def get_revenue_data(self, days: int) -> List[Dict[str, Any]]:
        """Get revenue data from cache/database (placeholder)"""
        return []
    
    def get_cost_data(self, days: int) -> List[Dict[str, Any]]:
        """Get cost data from cache/database (placeholder)"""
        return []
    
    def get_total_users(self, days: int) -> int:
        """Get total users for period (placeholder)"""
        return 1000
    
    def get_total_conversions(self, days: int) -> int:
        """Get total conversions for period (placeholder)"""
        return 100 