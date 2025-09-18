#!/usr/bin/env python3
"""
Risk A/B Testing Examples and Configurations

This module provides example configurations and usage patterns for the
RiskABTestFramework, demonstrating how to set up and run various types
of risk-based A/B tests for career protection optimization.

Examples include:
- Risk threshold optimization tests
- Risk communication A/B tests
- Intervention timing optimization
- Success outcome measurement
- Continuous optimization patterns
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from .risk_ab_testing_framework import (
    RiskABTestFramework, 
    RiskTestType, 
    CommunicationTone, 
    TimingStrategy
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskABTestExamples:
    """Example configurations and usage patterns for risk A/B testing"""
    
    def __init__(self, db_path: str = "backend/analytics/recommendation_analytics.db"):
        """Initialize with risk A/B testing framework"""
        self.risk_ab_framework = RiskABTestFramework(db_path)
    
    async def create_risk_threshold_optimization_example(self) -> str:
        """Example: Create risk threshold optimization test"""
        try:
            # Define threshold variants to test
            threshold_variants = [0.4, 0.5, 0.6, 0.7, 0.8]
            
            # Define success criteria
            success_criteria = [
                'recommendation_click_rate',
                'application_generation_rate', 
                'user_engagement_score',
                'career_protection_success_rate'
            ]
            
            # Create the test
            test_id = await self.risk_ab_framework.create_risk_threshold_test(
                test_name="Conservative vs Aggressive Risk Thresholds",
                threshold_variants=threshold_variants,
                success_criteria=success_criteria,
                target_participants=1200,
                test_duration_days=45
            )
            
            logger.info(f"Created risk threshold optimization test: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating risk threshold optimization example: {e}")
            raise
    
    async def create_risk_communication_example(self) -> str:
        """Example: Create risk communication A/B test"""
        try:
            # Define communication variants to test
            communication_variants = [
                CommunicationTone.DIRECT,
                CommunicationTone.ENCOURAGING,
                CommunicationTone.DATA_DRIVEN,
                CommunicationTone.SUPPORTIVE,
                CommunicationTone.URGENT
            ]
            
            # Define success criteria
            success_criteria = [
                'message_open_rate',
                'user_understanding_score',
                'action_taken_rate',
                'user_satisfaction_score',
                'time_to_action_hours'
            ]
            
            # Create the test
            test_id = await self.risk_ab_framework.create_risk_communication_test(
                test_name="Risk Communication Tone Optimization",
                communication_variants=communication_variants,
                success_criteria=success_criteria,
                target_participants=900,
                test_duration_days=30
            )
            
            logger.info(f"Created risk communication test: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating risk communication example: {e}")
            raise
    
    async def create_intervention_timing_example(self) -> str:
        """Example: Create intervention timing optimization test"""
        try:
            # Define timing variants to test
            timing_variants = [
                TimingStrategy.IMMEDIATE,
                TimingStrategy.OPTIMIZED_TIMING,
                TimingStrategy.SCHEDULED_OUTREACH,
                TimingStrategy.GRADUAL_ESCALATION
            ]
            
            # Define success criteria
            success_criteria = [
                'response_rate',
                'conversion_time_hours',
                'user_engagement_score',
                'intervention_effectiveness'
            ]
            
            # Create the test
            test_id = await self.risk_ab_framework.create_intervention_timing_test(
                test_name="Optimal Intervention Timing",
                timing_variants=timing_variants,
                success_criteria=success_criteria,
                target_participants=600,
                test_duration_days=21
            )
            
            logger.info(f"Created intervention timing test: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating intervention timing example: {e}")
            raise
    
    async def run_comprehensive_risk_testing_suite(self) -> Dict[str, str]:
        """Example: Run a comprehensive suite of risk A/B tests"""
        try:
            test_results = {}
            
            # 1. Risk Threshold Optimization
            threshold_test_id = await self.create_risk_threshold_optimization_example()
            test_results['threshold_optimization'] = threshold_test_id
            
            # 2. Risk Communication Testing
            communication_test_id = await self.create_risk_communication_example()
            test_results['communication_testing'] = communication_test_id
            
            # 3. Intervention Timing Optimization
            timing_test_id = await self.create_intervention_timing_example()
            test_results['timing_optimization'] = timing_test_id
            
            logger.info("Created comprehensive risk testing suite")
            return test_results
            
        except Exception as e:
            logger.error(f"Error running comprehensive testing suite: {e}")
            raise
    
    async def demonstrate_risk_communication_experiment(self, user_id: str, risk_score: float) -> Dict[str, Any]:
        """Example: Demonstrate risk communication experiment"""
        try:
            # Run communication experiment
            response = await self.risk_ab_framework.run_risk_communication_experiment(
                user_id=user_id,
                risk_score=risk_score,
                experiment_group='encouraging'  # Test encouraging tone
            )
            
            logger.info(f"Demonstrated risk communication experiment for user {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error demonstrating risk communication experiment: {e}")
            raise
    
    async def demonstrate_intervention_timing_optimization(self, user_risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Example: Demonstrate intervention timing optimization"""
        try:
            # Run timing optimization
            intervention_plan = await self.risk_ab_framework.optimize_intervention_timing(
                user_risk_data=user_risk_data,
                timing_variant='optimized_timing'
            )
            
            logger.info(f"Demonstrated intervention timing optimization for user {user_risk_data['user_id']}")
            return intervention_plan
            
        except Exception as e:
            logger.error(f"Error demonstrating intervention timing optimization: {e}")
            raise
    
    async def demonstrate_success_measurement(self, test_id: str) -> Dict[str, Any]:
        """Example: Demonstrate success measurement across variants"""
        try:
            # Measure intervention success
            success_results = await self.risk_ab_framework.measure_intervention_success_by_variant(test_id)
            
            # Track long-term career outcomes
            long_term_results = await self.risk_ab_framework.track_long_term_career_outcomes(test_id, months=6)
            
            # Analyze user satisfaction
            satisfaction_results = await self.risk_ab_framework.analyze_user_satisfaction_by_variant(test_id)
            
            # Calculate ROI
            roi_results = await self.risk_ab_framework.calculate_roi_by_test_variant(test_id)
            
            combined_results = {
                'success_measurement': success_results,
                'long_term_outcomes': long_term_results,
                'user_satisfaction': satisfaction_results,
                'roi_analysis': roi_results
            }
            
            logger.info(f"Demonstrated success measurement for test {test_id}")
            return combined_results
            
        except Exception as e:
            logger.error(f"Error demonstrating success measurement: {e}")
            raise
    
    async def demonstrate_continuous_optimization(self, test_id: str) -> Dict[str, Any]:
        """Example: Demonstrate continuous optimization features"""
        try:
            # Auto-optimize risk thresholds
            threshold_optimization = await self.risk_ab_framework.auto_optimize_risk_thresholds(test_id)
            
            # Dynamic communication personalization
            personalization = await self.risk_ab_framework.dynamic_communication_personalization(
                user_id='example_user_123',
                risk_score=0.65
            )
            
            # Adaptive intervention timing
            timing_optimization = await self.risk_ab_framework.adaptive_intervention_timing(
                user_id='example_user_123',
                risk_score=0.65
            )
            
            # Iterative success improvement
            improvement_analysis = await self.risk_ab_framework.iterative_success_improvement(test_id)
            
            optimization_results = {
                'threshold_optimization': threshold_optimization,
                'communication_personalization': personalization,
                'timing_optimization': timing_optimization,
                'improvement_analysis': improvement_analysis
            }
            
            logger.info(f"Demonstrated continuous optimization for test {test_id}")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error demonstrating continuous optimization: {e}")
            raise

# Predefined test configurations
RISK_THRESHOLD_TESTS = {
    'conservative_vs_aggressive': {
        'variants': [0.4, 0.6, 0.8],  # Risk thresholds
        'success_metric': 'successful_job_transitions',
        'sample_size': 1200,
        'test_duration': 45
    },
    'graduated_response': {
        'variants': [0.3, 0.5, 0.7, 0.9],  # Multi-tier thresholds
        'success_metric': 'user_engagement_with_recommendations',
        'sample_size': 1500,
        'test_duration': 60
    },
    'emergency_unlock_optimization': {
        'variants': [0.6, 0.7, 0.8, 0.9],  # Emergency unlock thresholds
        'success_metric': 'emergency_unlock_effectiveness',
        'sample_size': 800,
        'test_duration': 30
    }
}

COMMUNICATION_TONE_TESTS = {
    'communication_tone': {
        'variants': ['urgent', 'supportive', 'analytical'],
        'success_metric': 'user_engagement_with_recommendations',
        'sample_size': 900,
        'test_duration': 30
    },
    'message_clarity': {
        'variants': ['simple', 'detailed', 'technical'],
        'success_metric': 'user_understanding_score',
        'sample_size': 600,
        'test_duration': 21
    },
    'urgency_communication': {
        'variants': ['immediate', 'gradual', 'escalating'],
        'success_metric': 'action_taken_rate',
        'sample_size': 750,
        'test_duration': 28
    }
}

INTERVENTION_TIMING_TESTS = {
    'intervention_timing': {
        'variants': ['immediate', '2_hour_delay', 'next_day'],
        'success_metric': 'recommendation_conversion_rate',
        'sample_size': 600,
        'test_duration': 21
    },
    'follow_up_sequences': {
        'variants': ['none', 'gradual', 'comprehensive', 'escalating'],
        'success_metric': 'user_response_rate',
        'sample_size': 800,
        'test_duration': 35
    },
    'notification_frequency': {
        'variants': ['daily', 'weekly', 'bi_weekly', 'monthly'],
        'success_metric': 'alert_fatigue_score',
        'sample_size': 1000,
        'test_duration': 42
    }
}

# Example usage patterns
async def example_usage():
    """Example usage of the Risk A/B Testing Framework"""
    try:
        # Initialize examples
        examples = RiskABTestExamples()
        
        # Create comprehensive testing suite
        test_suite = await examples.run_comprehensive_risk_testing_suite()
        
        # Demonstrate individual experiments
        user_risk_data = {
            'user_id': 'example_user_123',
            'risk_score': 0.65,
            'risk_factors': ['ai_automation', 'industry_volatility'],
            'timeline_urgency': '3_months'
        }
        
        # Risk communication experiment
        comm_response = await examples.demonstrate_risk_communication_experiment(
            user_id='example_user_123',
            risk_score=0.65
        )
        
        # Intervention timing optimization
        timing_plan = await examples.demonstrate_intervention_timing_optimization(user_risk_data)
        
        # Success measurement
        success_measurement = await examples.demonstrate_success_measurement(
            test_suite['threshold_optimization']
        )
        
        # Continuous optimization
        optimization = await examples.demonstrate_continuous_optimization(
            test_suite['threshold_optimization']
        )
        
        logger.info("Example usage completed successfully")
        return {
            'test_suite': test_suite,
            'communication_experiment': comm_response,
            'timing_optimization': timing_plan,
            'success_measurement': success_measurement,
            'continuous_optimization': optimization
        }
        
    except Exception as e:
        logger.error(f"Error in example usage: {e}")
        raise

if __name__ == "__main__":
    # Run example usage
    asyncio.run(example_usage())
