#!/usr/bin/env python3
"""
Comprehensive Test Script for Analytics Integration

This script tests the complete analytics system integration,
including all components, API endpoints, and data flow.

Features:
- End-to-end analytics workflow testing
- API endpoint validation
- Database schema verification
- Performance monitoring testing
- A/B testing framework validation
- Admin dashboard functionality testing
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import analytics components
from backend.analytics.analytics_integration import AnalyticsIntegration
from backend.analytics.user_behavior_analytics import UserBehaviorAnalytics
from backend.analytics.recommendation_effectiveness import RecommendationEffectiveness
from backend.analytics.performance_monitor import PerformanceMonitor
from backend.analytics.success_metrics import SuccessMetrics
from backend.analytics.ab_testing_framework import ABTestFramework
from backend.analytics.admin_dashboard import AdminDashboard

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalyticsIntegrationTester:
    """Comprehensive tester for analytics integration"""
    
    def __init__(self):
        """Initialize the tester"""
        self.test_db_path = "test_analytics.db"
        self.analytics = AnalyticsIntegration(self.test_db_path)
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all analytics integration tests"""
        logger.info("Starting comprehensive analytics integration tests...")
        
        try:
            # Test individual components
            self.test_user_behavior_analytics()
            self.test_recommendation_effectiveness()
            self.test_performance_monitoring()
            self.test_success_metrics()
            self.test_ab_testing_framework()
            self.test_admin_dashboard()
            
            # Test integration workflows
            self.test_recommendation_workflow()
            self.test_user_journey_tracking()
            self.test_success_outcome_tracking()
            self.test_ab_test_workflow()
            
            # Test system summaries
            self.test_user_analytics_summary()
            self.test_system_analytics_summary()
            
            # Test data cleanup
            self.test_data_cleanup()
            
            logger.info(f"All tests completed. Passed: {self.test_results['passed']}, Failed: {self.test_results['failed']}")
            return self.test_results
            
        except Exception as e:
            logger.error(f"Test suite failed with error: {e}")
            self.test_results['errors'].append(str(e))
            return self.test_results
    
    def assert_test(self, condition: bool, test_name: str, error_message: str = ""):
        """Assert test condition and record result"""
        if condition:
            self.test_results['passed'] += 1
            logger.info(f"✓ {test_name}")
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {error_message}")
            logger.error(f"✗ {test_name}: {error_message}")
    
    def test_user_behavior_analytics(self):
        """Test user behavior analytics component"""
        logger.info("Testing User Behavior Analytics...")
        
        try:
            # Test session management
            session_id = self.analytics.user_behavior.start_user_session(
                user_id="test_user_1",
                device_type="desktop",
                browser="Chrome",
                os="Windows"
            )
            self.assert_test(session_id is not None, "Session creation", "Failed to create session")
            
            # Test interaction tracking
            success = self.analytics.user_behavior.track_user_interaction(
                session_id=session_id,
                user_id="test_user_1",
                interaction_type="page_view",
                page_url="/recommendations",
                element_id="recommendation_card_1"
            )
            self.assert_test(success, "Interaction tracking", "Failed to track interaction")
            
            # Test resume event tracking
            success = self.analytics.user_behavior.track_resume_event(
                session_id=session_id,
                user_id="test_user_1",
                event_type="upload_completed",
                file_name="test_resume.pdf",
                file_size=1024000,
                processing_time=2.5,
                success_rate=95.0,
                confidence_score=8.5
            )
            self.assert_test(success, "Resume event tracking", "Failed to track resume event")
            
            # Test feature usage tracking
            success = self.analytics.user_behavior.track_feature_usage(
                user_id="test_user_1",
                feature_name="job_recommendations",
                time_spent=120,
                success=True,
                satisfaction_score=4
            )
            self.assert_test(success, "Feature usage tracking", "Failed to track feature usage")
            
            # Test session ending
            success = self.analytics.user_behavior.end_user_session(
                session_id=session_id,
                exit_page="/dashboard",
                conversion_events=2
            )
            self.assert_test(success, "Session ending", "Failed to end session")
            
            # Test metrics retrieval
            metrics = self.analytics.user_behavior.get_user_behavior_metrics("test_user_1", 30)
            self.assert_test(len(metrics) > 0, "Metrics retrieval", "Failed to retrieve user metrics")
            
        except Exception as e:
            self.assert_test(False, "User Behavior Analytics", f"Exception: {str(e)}")
    
    def test_recommendation_effectiveness(self):
        """Test recommendation effectiveness component"""
        logger.info("Testing Recommendation Effectiveness...")
        
        try:
            # Test recommendation tracking
            rec_id = self.analytics.recommendation_effectiveness.track_recommendation(
                session_id="test_session_1",
                user_id="test_user_1",
                job_id="job_123",
                tier="optimal",
                recommendation_score=8.5,
                salary_increase_potential=15000,
                success_probability=0.75,
                skills_gap_score=0.8,
                company_culture_fit=0.9,
                career_advancement_potential=0.85
            )
            self.assert_test(rec_id is not None, "Recommendation tracking", "Failed to track recommendation")
            
            # Test engagement tracking
            success = self.analytics.recommendation_effectiveness.track_engagement(
                recommendation_id=rec_id,
                user_id="test_user_1",
                engagement_type="viewed",
                engagement_time=15.5
            )
            self.assert_test(success, "Engagement tracking", "Failed to track engagement")
            
            # Test application outcome tracking
            success = self.analytics.recommendation_effectiveness.track_application_outcome(
                recommendation_id=rec_id,
                user_id="test_user_1",
                application_id="app_456",
                application_status="offer_received",
                application_date=datetime.now(),
                outcome_date=datetime.now() + timedelta(days=7),
                salary_offered=75000,
                final_salary=78000,
                interview_rounds=3,
                feedback_received="Excellent technical skills",
                success_factors={"technical_interview": "strong", "cultural_fit": "excellent"}
            )
            self.assert_test(success, "Application outcome tracking", "Failed to track application outcome")
            
            # Test user feedback tracking
            success = self.analytics.recommendation_effectiveness.track_user_feedback(
                user_id="test_user_1",
                feedback_type="recommendation_quality",
                rating=5,
                feedback_text="Great recommendations!",
                recommendation_id=rec_id
            )
            self.assert_test(success, "User feedback tracking", "Failed to track user feedback")
            
            # Test effectiveness metrics
            metrics = self.analytics.recommendation_effectiveness.get_recommendation_effectiveness_by_tier(30)
            self.assert_test('analysis_period_days' in metrics, "Effectiveness metrics", "Failed to retrieve effectiveness metrics")
            
        except Exception as e:
            self.assert_test(False, "Recommendation Effectiveness", f"Exception: {str(e)}")
    
    def test_performance_monitoring(self):
        """Test performance monitoring component"""
        logger.info("Testing Performance Monitoring...")
        
        try:
            # Test API performance tracking
            success = self.analytics.performance_monitor.track_api_performance(
                endpoint="/api/recommendations",
                method="POST",
                response_time=1250.5,
                status_code=200,
                request_size=2048,
                response_size=8192,
                user_id="test_user_1"
            )
            self.assert_test(success, "API performance tracking", "Failed to track API performance")
            
            # Test error logging
            success = self.analytics.performance_monitor.log_error(
                error_type="validation_error",
                error_message="Invalid resume format",
                user_id="test_user_1",
                session_id="test_session_1",
                severity="medium"
            )
            self.assert_test(success, "Error logging", "Failed to log error")
            
            # Test processing time tracking
            with self.analytics.performance_monitor.track_processing_time(
                session_id="test_session_1",
                process_name="resume_parsing"
            ) as metrics:
                time.sleep(0.1)  # Simulate processing
                metrics.success = True
            
            # Test performance summary
            summary = self.analytics.performance_monitor.get_performance_summary(24)
            self.assert_test(len(summary) > 0, "Performance summary", "Failed to retrieve performance summary")
            
            # Test real-time metrics
            realtime_metrics = self.analytics.performance_monitor.get_real_time_metrics()
            self.assert_test(len(realtime_metrics) > 0, "Real-time metrics", "Failed to retrieve real-time metrics")
            
        except Exception as e:
            self.assert_test(False, "Performance Monitoring", f"Exception: {str(e)}")
    
    def test_success_metrics(self):
        """Test success metrics component"""
        logger.info("Testing Success Metrics...")
        
        try:
            # Test income tracking
            success = self.analytics.success_metrics.track_income_change(
                user_id="test_user_1",
                current_salary=75000,
                previous_salary=65000,
                target_salary=80000,
                source="application_outcome",
                verified=True
            )
            self.assert_test(success, "Income tracking", "Failed to track income change")
            
            # Test career advancement tracking
            success = self.analytics.success_metrics.track_career_advancement(
                user_id="test_user_1",
                advancement_type="promotion",
                previous_role="Software Engineer",
                new_role="Senior Software Engineer",
                salary_change=10000,
                skill_improvements={"leadership": "developed", "architecture": "improved"},
                recommendation_correlation={"recommendation_id": "rec_123", "contribution": "high"},
                success_factors={"technical_skills": "strong", "communication": "excellent"}
            )
            self.assert_test(success, "Career advancement tracking", "Failed to track career advancement")
            
            # Test goal achievement tracking
            success = self.analytics.success_metrics.track_goal_achievement(
                user_id="test_user_1",
                goal_type="salary_increase",
                goal_value="Increase salary by 15%",
                target_date=datetime.now() + timedelta(days=90),
                achieved_date=datetime.now(),
                achievement_percentage=100.0,
                recommendation_contribution=80.0,
                success_factors={"recommendations": "helped identify opportunities", "preparation": "thorough"}
            )
            self.assert_test(success, "Goal achievement tracking", "Failed to track goal achievement")
            
            # Test user retention update
            success = self.analytics.success_metrics.update_user_retention(
                user_id="test_user_1",
                registration_date=datetime.now() - timedelta(days=30),
                last_activity=datetime.now(),
                total_sessions=15,
                total_time_spent=3600,
                recommendations_received=25,
                applications_submitted=8,
                successful_outcomes=3,
                satisfaction_avg=4.2
            )
            self.assert_test(success, "User retention update", "Failed to update user retention")
            
            # Test user success metrics
            metrics = self.analytics.success_metrics.get_user_success_metrics("test_user_1", 30)
            self.assert_test(len(metrics) > 0, "User success metrics", "Failed to retrieve user success metrics")
            
            # Test system success metrics
            system_metrics = self.analytics.success_metrics.get_system_success_metrics(30)
            self.assert_test(len(system_metrics) > 0, "System success metrics", "Failed to retrieve system success metrics")
            
        except Exception as e:
            self.assert_test(False, "Success Metrics", f"Exception: {str(e)}")
    
    def test_ab_testing_framework(self):
        """Test A/B testing framework"""
        logger.info("Testing A/B Testing Framework...")
        
        try:
            # Test test creation
            test_id = self.analytics.ab_testing.create_test(
                test_name="Recommendation Algorithm Test",
                description="Test different recommendation algorithms",
                hypothesis="New algorithm will increase conversion by 15%",
                target_metric="conversion_rate",
                success_threshold=15.0,
                minimum_sample_size=500,
                duration_days=14,
                created_by="test_user"
            )
            self.assert_test(test_id is not None, "Test creation", "Failed to create A/B test")
            
            # Test variant addition
            control_variant_id = self.analytics.ab_testing.add_variant(
                test_id=test_id,
                variant_name="Control",
                variant_description="Current recommendation algorithm",
                configuration={"algorithm": "current", "parameters": {"weight": 1.0}},
                traffic_percentage=50.0,
                is_control=True
            )
            self.assert_test(control_variant_id is not None, "Control variant addition", "Failed to add control variant")
            
            test_variant_id = self.analytics.ab_testing.add_variant(
                test_id=test_id,
                variant_name="Test",
                variant_description="New recommendation algorithm",
                configuration={"algorithm": "new", "parameters": {"weight": 1.2}},
                traffic_percentage=50.0,
                is_control=False
            )
            self.assert_test(test_variant_id is not None, "Test variant addition", "Failed to add test variant")
            
            # Test test starting
            success = self.analytics.ab_testing.start_test(test_id)
            self.assert_test(success, "Test starting", "Failed to start A/B test")
            
            # Test user assignment
            assigned_variant = self.analytics.ab_testing.assign_user_to_test(test_id, "test_user_1")
            self.assert_test(assigned_variant is not None, "User assignment", "Failed to assign user to test")
            
            # Test conversion tracking
            success = self.analytics.ab_testing.track_conversion(
                test_id=test_id,
                user_id="test_user_1",
                conversion_event="recommendation_clicked",
                value=1.0
            )
            self.assert_test(success, "Conversion tracking", "Failed to track conversion")
            
            # Test results retrieval
            results = self.analytics.ab_testing.get_test_results(test_id)
            self.assert_test(len(results) > 0, "Results retrieval", "Failed to retrieve test results")
            
            # Test active tests
            active_tests = self.analytics.ab_testing.get_active_tests()
            self.assert_test(len(active_tests) > 0, "Active tests retrieval", "Failed to retrieve active tests")
            
        except Exception as e:
            self.assert_test(False, "A/B Testing Framework", f"Exception: {str(e)}")
    
    def test_admin_dashboard(self):
        """Test admin dashboard component"""
        logger.info("Testing Admin Dashboard...")
        
        try:
            # Test dashboard overview
            overview = self.analytics.admin_dashboard.get_dashboard_overview()
            self.assert_test(len(overview) > 0, "Dashboard overview", "Failed to retrieve dashboard overview")
            
            # Test success stories
            stories = self.analytics.admin_dashboard.get_user_success_stories(5)
            self.assert_test(isinstance(stories, list), "Success stories", "Failed to retrieve success stories")
            
            # Test quality report
            quality_report = self.analytics.admin_dashboard.get_recommendation_quality_report(30)
            self.assert_test(len(quality_report) > 0, "Quality report", "Failed to retrieve quality report")
            
            # Test A/B test dashboard
            ab_dashboard = self.analytics.admin_dashboard.get_ab_test_dashboard()
            self.assert_test(len(ab_dashboard) > 0, "A/B test dashboard", "Failed to retrieve A/B test dashboard")
            
            # Test data export
            export_data = self.analytics.admin_dashboard.export_analytics_data(
                data_type="user_behavior",
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now(),
                format="json"
            )
            self.assert_test(len(export_data) > 0, "Data export", "Failed to export analytics data")
            
        except Exception as e:
            self.assert_test(False, "Admin Dashboard", f"Exception: {str(e)}")
    
    def test_recommendation_workflow(self):
        """Test complete recommendation workflow tracking"""
        logger.info("Testing Recommendation Workflow...")
        
        try:
            # Create test workflow data
            workflow_data = {
                'recommendations': [
                    {
                        'job_id': 'job_1',
                        'tier': 'conservative',
                        'score': 7.5,
                        'salary_increase_potential': 10000,
                        'success_probability': 0.8
                    },
                    {
                        'job_id': 'job_2',
                        'tier': 'optimal',
                        'score': 8.5,
                        'salary_increase_potential': 15000,
                        'success_probability': 0.75
                    }
                ],
                'processing_time': 3.2
            }
            
            # Test workflow tracking
            results = self.analytics.track_recommendation_workflow(
                user_id="test_user_2",
                session_id="test_session_2",
                workflow_data=workflow_data
            )
            
            self.assert_test(
                results.get('recommendations_tracked', 0) > 0,
                "Workflow tracking",
                "Failed to track recommendation workflow"
            )
            
        except Exception as e:
            self.assert_test(False, "Recommendation Workflow", f"Exception: {str(e)}")
    
    def test_user_journey_tracking(self):
        """Test user journey tracking"""
        logger.info("Testing User Journey Tracking...")
        
        try:
            # Create test journey events
            journey_events = [
                {
                    'type': 'page_view',
                    'page_url': '/dashboard',
                    'element_id': 'main_content'
                },
                {
                    'type': 'button_click',
                    'page_url': '/recommendations',
                    'element_id': 'get_recommendations_btn',
                    'feature_name': 'job_recommendations',
                    'time_spent': 30
                },
                {
                    'type': 'recommendation_view',
                    'page_url': '/recommendations',
                    'element_id': 'recommendation_card_1'
                }
            ]
            
            # Test journey tracking
            success = self.analytics.track_user_journey(
                user_id="test_user_3",
                session_id="test_session_3",
                journey_events=journey_events
            )
            
            self.assert_test(success, "User journey tracking", "Failed to track user journey")
            
        except Exception as e:
            self.assert_test(False, "User Journey Tracking", f"Exception: {str(e)}")
    
    def test_success_outcome_tracking(self):
        """Test success outcome tracking"""
        logger.info("Testing Success Outcome Tracking...")
        
        try:
            # Test income increase tracking
            success = self.analytics.track_success_outcome(
                user_id="test_user_4",
                outcome_type="income_increase",
                outcome_data={
                    'current_salary': 80000,
                    'previous_salary': 70000,
                    'source': 'application_outcome',
                    'verified': True
                }
            )
            self.assert_test(success, "Income increase tracking", "Failed to track income increase")
            
            # Test career advancement tracking
            success = self.analytics.track_success_outcome(
                user_id="test_user_4",
                outcome_type="career_advancement",
                outcome_data={
                    'advancement_type': 'promotion',
                    'previous_role': 'Developer',
                    'new_role': 'Senior Developer',
                    'salary_change': 12000,
                    'skill_improvements': {'leadership': 'developed'},
                    'recommendation_correlation': {'contribution': 'high'}
                }
            )
            self.assert_test(success, "Career advancement tracking", "Failed to track career advancement")
            
        except Exception as e:
            self.assert_test(False, "Success Outcome Tracking", f"Exception: {str(e)}")
    
    def test_ab_test_workflow(self):
        """Test A/B test workflow"""
        logger.info("Testing A/B Test Workflow...")
        
        try:
            # Create A/B test
            test_id = self.analytics.create_ab_test_for_recommendations(
                test_name="UI Layout Test",
                description="Test different UI layouts for recommendations",
                hypothesis="New layout will increase engagement by 20%",
                variants=[
                    {
                        'name': 'Control',
                        'description': 'Current layout',
                        'configuration': {'layout': 'current'},
                        'traffic_percentage': 50.0,
                        'is_control': True
                    },
                    {
                        'name': 'Test',
                        'description': 'New layout',
                        'configuration': {'layout': 'new'},
                        'traffic_percentage': 50.0,
                        'is_control': False
                    }
                ]
            )
            
            self.assert_test(test_id is not None, "A/B test creation", "Failed to create A/B test")
            
            # Test user assignment
            variant_id = self.analytics.get_recommendation_variant_for_user("test_user_5", test_id)
            self.assert_test(variant_id is not None, "User assignment", "Failed to assign user to variant")
            
            # Test conversion tracking
            success = self.analytics.track_ab_test_conversion(
                test_id=test_id,
                user_id="test_user_5",
                conversion_event="recommendation_clicked",
                value=1.0
            )
            self.assert_test(success, "Conversion tracking", "Failed to track conversion")
            
        except Exception as e:
            self.assert_test(False, "A/B Test Workflow", f"Exception: {str(e)}")
    
    def test_user_analytics_summary(self):
        """Test user analytics summary"""
        logger.info("Testing User Analytics Summary...")
        
        try:
            summary = self.analytics.get_user_analytics_summary("test_user_1", 30)
            
            self.assert_test(
                len(summary) > 0 and 'error' not in summary,
                "User analytics summary",
                "Failed to retrieve user analytics summary"
            )
            
        except Exception as e:
            self.assert_test(False, "User Analytics Summary", f"Exception: {str(e)}")
    
    def test_system_analytics_summary(self):
        """Test system analytics summary"""
        logger.info("Testing System Analytics Summary...")
        
        try:
            summary = self.analytics.get_system_analytics_summary(7)
            
            self.assert_test(
                len(summary) > 0 and 'error' not in summary,
                "System analytics summary",
                "Failed to retrieve system analytics summary"
            )
            
        except Exception as e:
            self.assert_test(False, "System Analytics Summary", f"Exception: {str(e)}")
    
    def test_data_cleanup(self):
        """Test data cleanup functionality"""
        logger.info("Testing Data Cleanup...")
        
        try:
            cleanup_results = self.analytics.cleanup_old_data(days_to_keep=1)
            
            self.assert_test(
                len(cleanup_results) > 0 and 'error' not in cleanup_results,
                "Data cleanup",
                "Failed to cleanup old data"
            )
            
        except Exception as e:
            self.assert_test(False, "Data Cleanup", f"Exception: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            import os
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
                logger.info("Test database cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up test data: {e}")

def main():
    """Main test execution"""
    tester = AnalyticsIntegrationTester()
    
    try:
        # Run all tests
        results = tester.run_all_tests()
        
        # Print summary
        print("\n" + "="*60)
        print("ANALYTICS INTEGRATION TEST SUMMARY")
        print("="*60)
        print(f"Tests Passed: {results['passed']}")
        print(f"Tests Failed: {results['failed']}")
        print(f"Total Tests: {results['passed'] + results['failed']}")
        print(f"Success Rate: {(results['passed'] / (results['passed'] + results['failed']) * 100):.1f}%")
        
        if results['errors']:
            print("\nErrors:")
            for error in results['errors']:
                print(f"  - {error}")
        
        print("="*60)
        
        # Clean up
        tester.cleanup_test_data()
        
        # Return success/failure
        return results['failed'] == 0
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        tester.cleanup_test_data()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
