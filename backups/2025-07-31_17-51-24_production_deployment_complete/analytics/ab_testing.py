"""
A/B Testing Framework for Job Recommendation Engine
Tests recommendation algorithms, UI variations, and targeting strategies
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, Counter

from backend.services.cache_service import CacheService
from backend.analytics.analytics_service import AnalyticsService, EventType

logger = logging.getLogger(__name__)

class ExperimentType(Enum):
    """Types of A/B experiments"""
    RECOMMENDATION_ALGORITHM = "recommendation_algorithm"
    USER_INTERFACE = "user_interface"
    DEMOGRAPHIC_TARGETING = "demographic_targeting"
    INCOME_TARGETING = "income_targeting"
    SKILLS_MATCHING = "skills_matching"
    APPLICATION_STRATEGY = "application_strategy"
    MESSAGING = "messaging"

class ExperimentStatus(Enum):
    """Experiment status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

@dataclass
class ExperimentVariant:
    """Experiment variant configuration"""
    variant_id: str
    name: str
    description: str
    traffic_percentage: float
    configuration: Dict[str, Any]
    is_control: bool = False

@dataclass
class Experiment:
    """A/B experiment configuration"""
    experiment_id: str
    name: str
    description: str
    experiment_type: ExperimentType
    status: ExperimentStatus
    variants: List[ExperimentVariant]
    start_date: datetime
    end_date: Optional[datetime] = None
    target_audience: Dict[str, Any] = None
    success_metrics: List[str] = None
    minimum_sample_size: int = 1000
    confidence_level: float = 0.95
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class ExperimentResult:
    """Experiment result data"""
    experiment_id: str
    variant_id: str
    user_id: str
    session_id: str
    timestamp: datetime
    metrics: Dict[str, Any]
    conversion: bool = False
    conversion_value: float = 0.0

class ABTestingService:
    """A/B testing service for recommendation engine optimization"""
    
    def __init__(self, cache_service: CacheService, analytics_service: AnalyticsService):
        """Initialize A/B testing service"""
        self.cache_service = cache_service
        self.analytics_service = analytics_service
        self.experiments: Dict[str, Experiment] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = {}  # user_id -> {experiment_id: variant_id}
        
        # Load active experiments
        self.load_active_experiments()
    
    def create_experiment(self, 
                         name: str,
                         description: str,
                         experiment_type: ExperimentType,
                         variants: List[Dict[str, Any]],
                         target_audience: Optional[Dict[str, Any]] = None,
                         success_metrics: Optional[List[str]] = None,
                         minimum_sample_size: int = 1000,
                         confidence_level: float = 0.95) -> str:
        """Create a new A/B experiment"""
        experiment_id = str(uuid.uuid4())
        
        # Create experiment variants
        experiment_variants = []
        total_traffic = sum(variant.get('traffic_percentage', 0) for variant in variants)
        
        for i, variant_data in enumerate(variants):
            variant = ExperimentVariant(
                variant_id=str(uuid.uuid4()),
                name=variant_data['name'],
                description=variant_data.get('description', ''),
                traffic_percentage=variant_data.get('traffic_percentage', 100.0 / len(variants)),
                configuration=variant_data.get('configuration', {}),
                is_control=i == 0  # First variant is control
            )
            experiment_variants.append(variant)
        
        # Validate traffic percentages
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError("Traffic percentages must sum to 100%")
        
        # Create experiment
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            experiment_type=experiment_type,
            status=ExperimentStatus.DRAFT,
            variants=experiment_variants,
            start_date=datetime.now(),
            target_audience=target_audience or {},
            success_metrics=success_metrics or ['conversion_rate', 'engagement_score'],
            minimum_sample_size=minimum_sample_size,
            confidence_level=confidence_level
        )
        
        # Store experiment
        self.experiments[experiment_id] = experiment
        self.save_experiment(experiment)
        
        logger.info(f"Created experiment: {name} (ID: {experiment_id})")
        return experiment_id
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment"""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.ACTIVE
        experiment.updated_at = datetime.now()
        
        self.save_experiment(experiment)
        
        logger.info(f"Started experiment: {experiment.name}")
        return True
    
    def pause_experiment(self, experiment_id: str) -> bool:
        """Pause an experiment"""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.PAUSED
        experiment.updated_at = datetime.now()
        
        self.save_experiment(experiment)
        
        logger.info(f"Paused experiment: {experiment.name}")
        return True
    
    def complete_experiment(self, experiment_id: str) -> bool:
        """Complete an experiment"""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_date = datetime.now()
        experiment.updated_at = datetime.now()
        
        self.save_experiment(experiment)
        
        logger.info(f"Completed experiment: {experiment.name}")
        return True
    
    def get_user_variant(self, user_id: str, experiment_id: str) -> Optional[str]:
        """Get the variant assigned to a user for an experiment"""
        # Check if user is already assigned
        if user_id in self.user_assignments and experiment_id in self.user_assignments[user_id]:
            return self.user_assignments[user_id][experiment_id]
        
        # Check if experiment is active
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        if experiment.status != ExperimentStatus.ACTIVE:
            return None
        
        # Check if user meets target audience criteria
        if not self.user_matches_target_audience(user_id, experiment.target_audience):
            return None
        
        # Assign variant based on traffic percentages
        variant_id = self.assign_variant(user_id, experiment)
        
        # Store assignment
        if user_id not in self.user_assignments:
            self.user_assignments[user_id] = {}
        self.user_assignments[user_id][experiment_id] = variant_id
        
        # Track assignment
        self.track_experiment_assignment(user_id, experiment_id, variant_id)
        
        return variant_id
    
    def assign_variant(self, user_id: str, experiment: Experiment) -> str:
        """Assign a variant to a user based on traffic percentages"""
        # Use user ID hash for consistent assignment
        user_hash = hash(user_id) % 10000
        cumulative_percentage = 0
        
        for variant in experiment.variants:
            cumulative_percentage += variant.traffic_percentage
            if user_hash < cumulative_percentage:
                return variant.variant_id
        
        # Fallback to first variant
        return experiment.variants[0].variant_id
    
    def user_matches_target_audience(self, user_id: str, target_audience: Dict[str, Any]) -> bool:
        """Check if user matches target audience criteria"""
        if not target_audience:
            return True
        
        # Get user demographics from cache/database
        user_demographics = self.get_user_demographics(user_id)
        if not user_demographics:
            return True  # Default to include if no demographics available
        
        # Check age range
        if 'age_range' in target_audience:
            user_age_range = user_demographics.get('age_range')
            if user_age_range not in target_audience['age_range']:
                return False
        
        # Check education level
        if 'education_level' in target_audience:
            user_education = user_demographics.get('education_level')
            if user_education not in target_audience['education_level']:
                return False
        
        # Check industry
        if 'industry' in target_audience:
            user_industry = user_demographics.get('industry')
            if user_industry not in target_audience['industry']:
                return False
        
        # Check location
        if 'location' in target_audience:
            user_location = user_demographics.get('location')
            if user_location not in target_audience['location']:
                return False
        
        return True
    
    def track_experiment_result(self, 
                              user_id: str,
                              experiment_id: str,
                              variant_id: str,
                              session_id: str,
                              metrics: Dict[str, Any],
                              conversion: bool = False,
                              conversion_value: float = 0.0) -> None:
        """Track experiment result for a user"""
        result = ExperimentResult(
            experiment_id=experiment_id,
            variant_id=variant_id,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.now(),
            metrics=metrics,
            conversion=conversion,
            conversion_value=conversion_value
        )
        
        # Store result in cache
        cache_key = f"experiment_result:{experiment_id}:{user_id}"
        self.cache_service.set(cache_key, asdict(result), ttl=86400)  # 24 hours
        
        # Track as analytics event
        self.analytics_service.track_event(
            user_id=user_id,
            session_id=session_id,
            event_type=EventType.FEATURE_USAGE,
            metadata={
                'experiment_id': experiment_id,
                'variant_id': variant_id,
                'metrics': metrics,
                'conversion': conversion,
                'conversion_value': conversion_value
            }
        )
    
    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment results and statistical analysis"""
        if experiment_id not in self.experiments:
            return {}
        
        experiment = self.experiments[experiment_id]
        
        # Get all results for this experiment
        results = self.get_experiment_results_data(experiment_id)
        
        if not results:
            return {
                'experiment_id': experiment_id,
                'status': experiment.status.value,
                'total_participants': 0,
                'variants': {}
            }
        
        # Group results by variant
        variant_results = defaultdict(list)
        for result in results:
            variant_results[result['variant_id']].append(result)
        
        # Calculate metrics for each variant
        variant_metrics = {}
        for variant in experiment.variants:
            variant_data = variant_results.get(variant.variant_id, [])
            
            if variant_data:
                metrics = self.calculate_variant_metrics(variant_data, experiment.success_metrics)
                variant_metrics[variant.variant_id] = {
                    'variant_name': variant.name,
                    'is_control': variant.is_control,
                    'participant_count': len(variant_data),
                    'metrics': metrics
                }
        
        # Perform statistical analysis
        statistical_analysis = self.perform_statistical_analysis(variant_metrics, experiment)
        
        return {
            'experiment_id': experiment_id,
            'experiment_name': experiment.name,
            'status': experiment.status.value,
            'total_participants': len(results),
            'variants': variant_metrics,
            'statistical_analysis': statistical_analysis,
            'recommendations': self.generate_experiment_recommendations(variant_metrics, experiment)
        }
    
    def calculate_variant_metrics(self, variant_data: List[Dict[str, Any]], success_metrics: List[str]) -> Dict[str, Any]:
        """Calculate metrics for a variant"""
        metrics = {}
        
        # Conversion rate
        conversions = sum(1 for result in variant_data if result.get('conversion', False))
        conversion_rate = conversions / len(variant_data) if variant_data else 0.0
        metrics['conversion_rate'] = conversion_rate
        
        # Average conversion value
        conversion_values = [result.get('conversion_value', 0.0) for result in variant_data if result.get('conversion', False)]
        avg_conversion_value = sum(conversion_values) / len(conversion_values) if conversion_values else 0.0
        metrics['avg_conversion_value'] = avg_conversion_value
        
        # Engagement score (custom metric)
        engagement_scores = [result.get('metrics', {}).get('engagement_score', 0.0) for result in variant_data]
        avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.0
        metrics['avg_engagement_score'] = avg_engagement
        
        # Response time (if available)
        response_times = [result.get('metrics', {}).get('response_time', 0.0) for result in variant_data]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        metrics['avg_response_time'] = avg_response_time
        
        # Custom metrics
        for metric_name in success_metrics:
            if metric_name not in metrics:
                metric_values = [result.get('metrics', {}).get(metric_name, 0.0) for result in variant_data]
                avg_metric = sum(metric_values) / len(metric_values) if metric_values else 0.0
                metrics[f'avg_{metric_name}'] = avg_metric
        
        return metrics
    
    def perform_statistical_analysis(self, variant_metrics: Dict[str, Any], experiment: Experiment) -> Dict[str, Any]:
        """Perform statistical analysis on experiment results"""
        analysis = {
            'confidence_level': experiment.confidence_level,
            'statistical_significance': {},
            'effect_size': {},
            'recommendations': []
        }
        
        # Find control variant
        control_variant = None
        for variant_id, metrics in variant_metrics.items():
            if metrics.get('is_control', False):
                control_variant = variant_id
                break
        
        if not control_variant:
            return analysis
        
        control_metrics = variant_metrics[control_variant]['metrics']
        
        # Compare each variant to control
        for variant_id, variant_data in variant_metrics.items():
            if variant_id == control_variant:
                continue
            
            variant_metrics_data = variant_data['metrics']
            
            # Calculate statistical significance for conversion rate
            significance = self.calculate_statistical_significance(
                control_metrics['conversion_rate'],
                variant_metrics_data['conversion_rate'],
                variant_metrics[control_variant]['participant_count'],
                variant_data['participant_count']
            )
            
            analysis['statistical_significance'][variant_id] = {
                'conversion_rate_significant': significance,
                'p_value': self.calculate_p_value(significance)
            }
            
            # Calculate effect size
            effect_size = self.calculate_effect_size(
                control_metrics['conversion_rate'],
                variant_metrics_data['conversion_rate']
            )
            
            analysis['effect_size'][variant_id] = effect_size
            
            # Generate recommendations
            if significance and effect_size > 0.1:  # Medium effect size
                analysis['recommendations'].append({
                    'variant_id': variant_id,
                    'variant_name': variant_data['variant_name'],
                    'recommendation': 'Consider implementing this variant',
                    'confidence': 'high' if effect_size > 0.3 else 'medium'
                })
        
        return analysis
    
    def calculate_statistical_significance(self, control_rate: float, variant_rate: float, 
                                         control_n: int, variant_n: int) -> bool:
        """Calculate statistical significance using chi-square test"""
        # Simplified chi-square test for conversion rates
        if control_n == 0 or variant_n == 0:
            return False
        
        # Calculate pooled proportion
        pooled_p = (control_rate * control_n + variant_rate * variant_n) / (control_n + variant_n)
        
        # Calculate standard error
        se = (pooled_p * (1 - pooled_p) * (1/control_n + 1/variant_n)) ** 0.5
        
        # Calculate z-score
        z_score = abs(variant_rate - control_rate) / se
        
        # Check significance at 95% confidence level
        return z_score > 1.96
    
    def calculate_p_value(self, significance: bool) -> float:
        """Calculate p-value (simplified)"""
        return 0.01 if significance else 0.5
    
    def calculate_effect_size(self, control_rate: float, variant_rate: float) -> float:
        """Calculate Cohen's h effect size for proportions"""
        import math
        h = 2 * (math.asin(math.sqrt(variant_rate)) - math.asin(math.sqrt(control_rate)))
        return abs(h)
    
    def generate_experiment_recommendations(self, variant_metrics: Dict[str, Any], experiment: Experiment) -> List[str]:
        """Generate recommendations based on experiment results"""
        recommendations = []
        
        # Check sample size
        total_participants = sum(metrics['participant_count'] for metrics in variant_metrics.values())
        if total_participants < experiment.minimum_sample_size:
            recommendations.append(f"Insufficient sample size. Need {experiment.minimum_sample_size} participants, got {total_participants}")
        
        # Find best performing variant
        best_variant = None
        best_conversion_rate = 0.0
        
        for variant_id, metrics in variant_metrics.items():
            conversion_rate = metrics['metrics'].get('conversion_rate', 0.0)
            if conversion_rate > best_conversion_rate:
                best_conversion_rate = conversion_rate
                best_variant = variant_id
        
        if best_variant:
            best_variant_name = variant_metrics[best_variant]['variant_name']
            recommendations.append(f"Best performing variant: {best_variant_name} (conversion rate: {best_conversion_rate:.2%})")
        
        # Check for significant improvements
        control_variant = None
        for variant_id, metrics in variant_metrics.items():
            if metrics.get('is_control', False):
                control_variant = variant_id
                break
        
        if control_variant:
            control_rate = variant_metrics[control_variant]['metrics'].get('conversion_rate', 0.0)
            for variant_id, metrics in variant_metrics.items():
                if variant_id != control_variant:
                    variant_rate = metrics['metrics'].get('conversion_rate', 0.0)
                    improvement = (variant_rate - control_rate) / control_rate if control_rate > 0 else 0
                    
                    if improvement > 0.1:  # 10% improvement
                        recommendations.append(f"{metrics['variant_name']} shows {improvement:.1%} improvement over control")
        
        return recommendations
    
    def get_user_demographics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user demographics from cache/database"""
        # This would typically query user data
        # For now, return placeholder data
        return {
            'age_range': '30-34',
            'education_level': 'bachelor',
            'industry': 'technology',
            'location': 'Atlanta, GA'
        }
    
    def get_experiment_results_data(self, experiment_id: str) -> List[Dict[str, Any]]:
        """Get experiment results data from cache/database"""
        # This would typically query stored results
        # For now, return empty list
        return []
    
    def save_experiment(self, experiment: Experiment) -> None:
        """Save experiment to cache/database"""
        cache_key = f"experiment:{experiment.experiment_id}"
        self.cache_service.set(cache_key, asdict(experiment), ttl=86400)  # 24 hours
    
    def load_active_experiments(self) -> None:
        """Load active experiments from cache/database"""
        # This would typically load from persistent storage
        # For now, create some example experiments
        self.create_example_experiments()
    
    def create_example_experiments(self) -> None:
        """Create example experiments for testing"""
        # Recommendation algorithm experiment
        self.create_experiment(
            name="Recommendation Algorithm Optimization",
            description="Test different recommendation algorithms for better job matching",
            experiment_type=ExperimentType.RECOMMENDATION_ALGORITHM,
            variants=[
                {
                    'name': 'Control (Current Algorithm)',
                    'description': 'Current recommendation algorithm',
                    'traffic_percentage': 50.0,
                    'configuration': {'algorithm': 'current'}
                },
                {
                    'name': 'Enhanced Skills Matching',
                    'description': 'Improved skills matching algorithm',
                    'traffic_percentage': 25.0,
                    'configuration': {'algorithm': 'enhanced_skills', 'skills_weight': 0.8}
                },
                {
                    'name': 'Salary-Focused Matching',
                    'description': 'Algorithm optimized for salary improvements',
                    'traffic_percentage': 25.0,
                    'configuration': {'algorithm': 'salary_focused', 'salary_weight': 0.7}
                }
            ],
            target_audience={
                'age_range': ['25-29', '30-34', '35-39'],
                'education_level': ['bachelor', 'master'],
                'industry': ['technology', 'finance', 'marketing']
            },
            success_metrics=['conversion_rate', 'engagement_score', 'salary_increase']
        )
        
        # UI experiment
        self.create_experiment(
            name="User Interface Optimization",
            description="Test different UI layouts for better user engagement",
            experiment_type=ExperimentType.USER_INTERFACE,
            variants=[
                {
                    'name': 'Control (Current Layout)',
                    'description': 'Current user interface layout',
                    'traffic_percentage': 50.0,
                    'configuration': {'layout': 'current'}
                },
                {
                    'name': 'Card-Based Layout',
                    'description': 'Modern card-based recommendation display',
                    'traffic_percentage': 25.0,
                    'configuration': {'layout': 'card_based', 'show_salary_first': True}
                },
                {
                    'name': 'List-Based Layout',
                    'description': 'Traditional list-based recommendation display',
                    'traffic_percentage': 25.0,
                    'configuration': {'layout': 'list_based', 'compact_view': True}
                }
            ],
            success_metrics=['engagement_score', 'time_on_page', 'recommendation_clicks']
        )
        
        # Start the experiments
        for experiment_id in self.experiments.keys():
            self.start_experiment(experiment_id)
    
    def get_experiment_configuration(self, user_id: str, experiment_type: ExperimentType) -> Dict[str, Any]:
        """Get experiment configuration for a user"""
        # Find active experiments of the specified type
        for experiment in self.experiments.values():
            if (experiment.experiment_type == experiment_type and 
                experiment.status == ExperimentStatus.ACTIVE):
                
                variant_id = self.get_user_variant(user_id, experiment.experiment_id)
                if variant_id:
                    # Find variant configuration
                    for variant in experiment.variants:
                        if variant.variant_id == variant_id:
                            return variant.configuration
        
        return {}  # Default configuration if no experiment
    
    def track_experiment_assignment(self, user_id: str, experiment_id: str, variant_id: str) -> None:
        """Track experiment assignment for analytics"""
        assignment_data = {
            'user_id': user_id,
            'experiment_id': experiment_id,
            'variant_id': variant_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store assignment in cache
        assignment_key = f"experiment_assignment:{user_id}:{experiment_id}"
        self.cache_service.set(assignment_key, assignment_data, ttl=86400)  # 24 hours
        
        # Track as analytics event
        self.analytics_service.track_event(
            user_id=user_id,
            session_id='',  # No session for assignment
            event_type=EventType.FEATURE_USAGE,
            metadata={
                'experiment_assignment': assignment_data
            }
        ) 