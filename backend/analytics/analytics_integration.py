#!/usr/bin/env python3
"""
Analytics Integration Module for Job Recommendation Engine

This module provides seamless integration between the analytics system
and the existing Mingus job recommendation engine, ensuring all
user interactions and system events are properly tracked.

Features:
- Automatic integration with recommendation engine
- Session management integration
- Performance monitoring integration
- Real-time metrics collection
- Error tracking and alerting
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

# Import analytics components
from .user_behavior_analytics import UserBehaviorAnalytics
from .recommendation_effectiveness import RecommendationEffectiveness
from .performance_monitor import PerformanceMonitor
from .success_metrics import SuccessMetrics
from .ab_testing_framework import ABTestFramework
from .admin_dashboard import AdminDashboard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsIntegration:
    """
    Comprehensive analytics integration for the job recommendation engine.
    
    Provides seamless integration between analytics tracking and the
    existing Mingus system components.
    """
    
    def __init__(self, db_path: str = "backend/analytics/recommendation_analytics.db"):
        """Initialize the analytics integration system"""
        self.db_path = db_path
        
        # Initialize analytics components
        self.user_behavior = UserBehaviorAnalytics(db_path)
        self.recommendation_effectiveness = RecommendationEffectiveness(db_path)
        self.performance_monitor = PerformanceMonitor(db_path)
        self.success_metrics = SuccessMetrics(db_path)
        self.ab_testing = ABTestFramework(db_path)
        self.admin_dashboard = AdminDashboard(db_path)
        
        # Start performance monitoring
        self.performance_monitor.start_system_monitoring(interval=60)
        
        logger.info("AnalyticsIntegration initialized successfully")
    
    def track_recommendation_workflow(
        self,
        user_id: str,
        session_id: str,
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track a complete recommendation workflow
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            workflow_data: Workflow data including recommendations
            
        Returns:
            Dict containing tracking results
        """
        try:
            tracking_results = {
                'recommendations_tracked': 0,
                'engagements_tracked': 0,
                'errors': []
            }
            
            # Track recommendations
            if 'recommendations' in workflow_data:
                for recommendation in workflow_data['recommendations']:
                    try:
                        rec_id = self.recommendation_effectiveness.track_recommendation(
                            session_id=session_id,
                            user_id=user_id,
                            job_id=recommendation.get('job_id', ''),
                            tier=recommendation.get('tier', 'optimal'),
                            recommendation_score=recommendation.get('score', 0.0),
                            salary_increase_potential=recommendation.get('salary_increase_potential', 0.0),
                            success_probability=recommendation.get('success_probability', 0.0),
                            skills_gap_score=recommendation.get('skills_gap_score', 0.0),
                            company_culture_fit=recommendation.get('company_culture_fit', 0.0),
                            career_advancement_potential=recommendation.get('career_advancement_potential', 0.0)
                        )
                        tracking_results['recommendations_tracked'] += 1
                        
                        # Track initial view engagement
                        self.recommendation_effectiveness.track_engagement(
                            recommendation_id=rec_id,
                            user_id=user_id,
                            engagement_type='viewed',
                            engagement_time=0.0
                        )
                        tracking_results['engagements_tracked'] += 1
                        
                    except Exception as e:
                        tracking_results['errors'].append(f"Error tracking recommendation: {str(e)}")
                        logger.error(f"Error tracking recommendation: {e}")
            
            # Track feature usage
            self.user_behavior.track_feature_usage(
                user_id=user_id,
                feature_name='job_recommendation_workflow',
                time_spent=workflow_data.get('processing_time', 0),
                success=True
            )
            
            return tracking_results
            
        except Exception as e:
            logger.error(f"Error tracking recommendation workflow: {e}")
            return {'error': str(e)}
    
    def track_user_journey(
        self,
        user_id: str,
        session_id: str,
        journey_events: List[Dict[str, Any]]
    ) -> bool:
        """
        Track user journey events
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            journey_events: List of journey events
            
        Returns:
            bool: Success status
        """
        try:
            for event in journey_events:
                # Track user interaction
                self.user_behavior.track_user_interaction(
                    session_id=session_id,
                    user_id=user_id,
                    interaction_type=event.get('type', 'page_view'),
                    page_url=event.get('page_url', ''),
                    element_id=event.get('element_id', ''),
                    element_text=event.get('element_text', ''),
                    interaction_data=event.get('data', {})
                )
                
                # Track feature usage if applicable
                if 'feature_name' in event:
                    self.user_behavior.track_feature_usage(
                        user_id=user_id,
                        feature_name=event['feature_name'],
                        time_spent=event.get('time_spent', 0),
                        success=event.get('success', True)
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking user journey: {e}")
            return False
    
    @contextmanager
    def track_performance(self, process_name: str, session_id: str = None):
        """
        Context manager for tracking performance metrics
        
        Args:
            process_name: Name of the process being tracked
            session_id: Session identifier (optional)
            
        Yields:
            Performance tracking context
        """
        with self.performance_monitor.track_processing_time(
            session_id=session_id or 'system',
            process_name=process_name
        ) as metrics:
            try:
                yield metrics
            except Exception as e:
                # Log error
                self.performance_monitor.log_error(
                    error_type='processing_error',
                    error_message=str(e),
                    stack_trace=str(e),
                    session_id=session_id,
                    endpoint=process_name,
                    severity='medium'
                )
                raise
    
    def track_success_outcome(
        self,
        user_id: str,
        outcome_type: str,
        outcome_data: Dict[str, Any]
    ) -> bool:
        """
        Track user success outcomes
        
        Args:
            user_id: User identifier
            outcome_type: Type of success outcome
            outcome_data: Outcome data
            
        Returns:
            bool: Success status
        """
        try:
            if outcome_type == 'income_increase':
                self.success_metrics.track_income_change(
                    user_id=user_id,
                    current_salary=outcome_data.get('current_salary', 0),
                    previous_salary=outcome_data.get('previous_salary'),
                    target_salary=outcome_data.get('target_salary'),
                    source=outcome_data.get('source', 'self_reported'),
                    verified=outcome_data.get('verified', False)
                )
                
            elif outcome_type == 'career_advancement':
                self.success_metrics.track_career_advancement(
                    user_id=user_id,
                    advancement_type=outcome_data.get('advancement_type', 'promotion'),
                    previous_role=outcome_data.get('previous_role', ''),
                    new_role=outcome_data.get('new_role', ''),
                    salary_change=outcome_data.get('salary_change', 0.0),
                    skill_improvements=outcome_data.get('skill_improvements', {}),
                    recommendation_correlation=outcome_data.get('recommendation_correlation', {}),
                    success_factors=outcome_data.get('success_factors', {})
                )
                
            elif outcome_type == 'goal_achievement':
                self.success_metrics.track_goal_achievement(
                    user_id=user_id,
                    goal_type=outcome_data.get('goal_type', 'salary_increase'),
                    goal_value=outcome_data.get('goal_value', ''),
                    target_date=outcome_data.get('target_date'),
                    achieved_date=outcome_data.get('achieved_date'),
                    achievement_percentage=outcome_data.get('achievement_percentage', 0.0),
                    recommendation_contribution=outcome_data.get('recommendation_contribution', 0.0),
                    success_factors=outcome_data.get('success_factors', {})
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking success outcome: {e}")
            return False
    
    def get_user_analytics_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics summary for a user
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict containing user analytics summary
        """
        try:
            # Get behavior metrics
            behavior_metrics = self.user_behavior.get_user_behavior_metrics(user_id, days)
            
            # Get recommendation performance
            recommendation_performance = self.recommendation_effectiveness.get_user_recommendation_performance(user_id, days)
            
            # Get success metrics
            success_metrics = self.success_metrics.get_user_success_metrics(user_id, days)
            
            # Calculate engagement score
            engagement_score = self.user_behavior.calculate_engagement_score(user_id, days)
            
            return {
                'user_id': user_id,
                'analysis_period_days': days,
                'engagement_score': engagement_score,
                'behavior_metrics': behavior_metrics,
                'recommendation_performance': recommendation_performance,
                'success_metrics': success_metrics,
                'summary_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics summary: {e}")
            return {'error': str(e)}
    
    def get_system_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get comprehensive system analytics summary
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing system analytics summary
        """
        try:
            # Get system behavior metrics
            behavior_metrics = self.user_behavior.get_system_behavior_metrics(days)
            
            # Get recommendation effectiveness
            recommendation_effectiveness = self.recommendation_effectiveness.get_recommendation_effectiveness_by_tier(days)
            
            # Get performance summary
            performance_summary = self.performance_monitor.get_performance_summary(days * 24)
            
            # Get success metrics
            success_metrics = self.success_metrics.get_system_success_metrics(days)
            
            # Get dashboard overview
            dashboard_overview = self.admin_dashboard.get_dashboard_overview()
            
            return {
                'analysis_period_days': days,
                'behavior_metrics': behavior_metrics,
                'recommendation_effectiveness': recommendation_effectiveness,
                'performance_summary': performance_summary,
                'success_metrics': success_metrics,
                'dashboard_overview': dashboard_overview,
                'summary_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system analytics summary: {e}")
            return {'error': str(e)}
    
    def create_ab_test_for_recommendations(
        self,
        test_name: str,
        description: str,
        hypothesis: str,
        variants: List[Dict[str, Any]]
    ) -> str:
        """
        Create an A/B test for recommendation optimization
        
        Args:
            test_name: Name of the test
            description: Test description
            hypothesis: Test hypothesis
            variants: List of test variants
            
        Returns:
            test_id: Created test identifier
        """
        try:
            # Create test
            test_id = self.ab_testing.create_test(
                test_name=test_name,
                description=description,
                hypothesis=hypothesis,
                target_metric='conversion_rate',
                success_threshold=10.0,  # 10% improvement
                minimum_sample_size=1000,
                duration_days=14,
                created_by='analytics_integration'
            )
            
            # Add variants
            for i, variant in enumerate(variants):
                self.ab_testing.add_variant(
                    test_id=test_id,
                    variant_name=variant.get('name', f'Variant {i+1}'),
                    variant_description=variant.get('description', ''),
                    configuration=variant.get('configuration', {}),
                    traffic_percentage=variant.get('traffic_percentage', 50.0),
                    is_control=variant.get('is_control', i == 0)
                )
            
            # Start test
            self.ab_testing.start_test(test_id)
            
            logger.info(f"Created A/B test for recommendations: {test_id}")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            raise
    
    def get_recommendation_variant_for_user(
        self,
        user_id: str,
        test_id: str
    ) -> Optional[str]:
        """
        Get recommendation variant for a user in an A/B test
        
        Args:
            user_id: User identifier
            test_id: Test identifier
            
        Returns:
            variant_id: Assigned variant identifier or None
        """
        try:
            return self.ab_testing.assign_user_to_test(test_id, user_id)
        except Exception as e:
            logger.error(f"Error getting recommendation variant: {e}")
            return None
    
    def track_ab_test_conversion(
        self,
        test_id: str,
        user_id: str,
        conversion_event: str,
        value: float = 1.0
    ) -> bool:
        """
        Track A/B test conversion
        
        Args:
            test_id: Test identifier
            user_id: User identifier
            conversion_event: Conversion event name
            value: Conversion value
            
        Returns:
            bool: Success status
        """
        try:
            return self.ab_testing.track_conversion(
                test_id=test_id,
                user_id=user_id,
                conversion_event=conversion_event,
                value=value
            )
        except Exception as e:
            logger.error(f"Error tracking A/B test conversion: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up old analytics data to manage database size
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Dict containing cleanup results
        """
        try:
            import sqlite3
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cleanup_results = {}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean up old user sessions
            cursor.execute('''
                DELETE FROM user_sessions 
                WHERE session_start < ?
            ''', (cutoff_date,))
            cleanup_results['user_sessions'] = cursor.rowcount
            
            # Clean up old API performance data
            cursor.execute('''
                DELETE FROM api_performance 
                WHERE timestamp < ?
            ''', (cutoff_date,))
            cleanup_results['api_performance'] = cursor.rowcount
            
            # Clean up old processing metrics
            cursor.execute('''
                DELETE FROM processing_metrics 
                WHERE start_time < ?
            ''', (cutoff_date,))
            cleanup_results['processing_metrics'] = cursor.rowcount
            
            # Clean up old system resources (keep more recent data)
            recent_cutoff = datetime.now() - timedelta(days=30)
            cursor.execute('''
                DELETE FROM system_resources 
                WHERE timestamp < ?
            ''', (recent_cutoff,))
            cleanup_results['system_resources'] = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up old analytics data: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return {'error': str(e)}
    
    def stop_monitoring(self):
        """Stop all monitoring processes"""
        try:
            self.performance_monitor.stop_system_monitoring()
            logger.info("Analytics monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
