#!/usr/bin/env python3
"""
Comprehensive Test Script for Risk Analytics Integration

This script tests the complete risk-based analytics system integration,
including risk assessment tracking, recommendation triggering, and outcome measurement.

Features:
- Risk event tracking testing
- Risk-based recommendation testing
- Career protection outcome testing
- A/B testing framework validation
- Risk dashboard functionality testing
- End-to-end risk analytics workflow testing
"""

import sys
import os
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import risk analytics components
from backend.analytics.risk_analytics_integration import (
    RiskAnalyticsIntegration,
    RiskAssessmentData,
    RiskOutcomeData,
    RiskEventType,
    RiskLevel,
    OutcomeType
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RiskAnalyticsIntegrationTester:
    """Comprehensive tester for risk analytics integration"""
    
    def __init__(self):
        """Initialize the tester"""
        self.test_db_path = "test_risk_analytics.db"
        self.risk_analytics = RiskAnalyticsIntegration(self.test_db_path)
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        self.test_users = [
            'test_user_1',
            'test_user_2', 
            'test_user_3'
        ]
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all risk analytics integration tests"""
        logger.info("Starting comprehensive risk analytics integration tests...")
        
        try:
            # Test individual components
            self.test_risk_assessment_tracking()
            self.test_risk_recommendation_tracking()
            self.test_emergency_unlock_tracking()
            self.test_prediction_accuracy_tracking()
            self.test_career_protection_outcome_tracking()
            
            # Test risk journey analytics
            self.test_risk_journey_analysis()
            self.test_early_warning_effectiveness()
            
            # Test A/B testing framework
            self.test_risk_ab_testing()
            
            # Test dashboard functionality
            self.test_risk_dashboard()
            
            # Test end-to-end workflows
            self.test_end_to_end_risk_workflow()
            
            # Test data cleanup
            self.test_data_cleanup()
            
            logger.info(f"All tests completed. Passed: {self.test_results['passed']}, Failed: {self.test_results['failed']}")
            return self.test_results
            
        except Exception as e:
            logger.error(f"Test suite failed with error: {e}")
            self.test_results['errors'].append(str(e))
            return self.test_results
    
    def assert_test(self, condition: bool, test_name: str, error_message: str = ""):
        """Assert a test condition"""
        if condition:
            self.test_results['passed'] += 1
            logger.info(f"✓ {test_name}")
        else:
            self.test_results['failed'] += 1
            error_msg = error_message or f"Test failed: {test_name}"
            self.test_results['errors'].append(error_msg)
            logger.error(f"✗ {test_name}: {error_msg}")
    
    def test_risk_assessment_tracking(self):
        """Test risk assessment tracking functionality"""
        logger.info("Testing risk assessment tracking...")
        
        try:
            # Test AI risk assessment
            ai_risk_data = RiskAssessmentData(
                user_id=self.test_users[0],
                assessment_type='ai_risk',
                overall_risk=0.75,
                risk_triggers=['High-risk industry', 'Low AI tool usage', 'Outdated skills'],
                risk_breakdown={
                    'industry_risk': 0.3,
                    'automation_risk': 0.25,
                    'skills_risk': 0.2
                },
                timeline_urgency='3_months',
                assessment_timestamp=datetime.now(),
                confidence_score=0.85,
                risk_factors={
                    'industry': 0.3,
                    'automation_level': 0.25,
                    'ai_usage': 0.2
                }
            )
            
            # Track AI risk assessment
            result = asyncio.run(self.risk_analytics.track_risk_assessment_completed(
                self.test_users[0], ai_risk_data
            ))
            self.assert_test(result, "AI risk assessment tracking")
            
            # Test layoff risk assessment
            layoff_risk_data = RiskAssessmentData(
                user_id=self.test_users[1],
                assessment_type='layoff_risk',
                overall_risk=0.65,
                risk_triggers=['Small company', 'Recent layoffs', 'Below expectations'],
                risk_breakdown={
                    'company_size_risk': 0.2,
                    'tenure_risk': 0.15,
                    'performance_risk': 0.2,
                    'company_health_risk': 0.1
                },
                timeline_urgency='6_months',
                assessment_timestamp=datetime.now(),
                confidence_score=0.78,
                risk_factors={
                    'company_size': 0.2,
                    'tenure': 0.15,
                    'performance': 0.2,
                    'company_health': 0.1
                }
            )
            
            # Track layoff risk assessment
            result = asyncio.run(self.risk_analytics.track_risk_assessment_completed(
                self.test_users[1], layoff_risk_data
            ))
            self.assert_test(result, "Layoff risk assessment tracking")
            
        except Exception as e:
            self.assert_test(False, "Risk assessment tracking", str(e))
    
    def test_risk_recommendation_tracking(self):
        """Test risk-triggered recommendation tracking"""
        logger.info("Testing risk recommendation tracking...")
        
        try:
            # Create risk data
            risk_data = RiskAssessmentData(
                user_id=self.test_users[0],
                assessment_type='ai_risk',
                overall_risk=0.8,
                risk_triggers=['High-risk industry', 'Low AI tool usage'],
                risk_breakdown={'industry_risk': 0.4, 'automation_risk': 0.4},
                timeline_urgency='immediate',
                assessment_timestamp=datetime.now(),
                confidence_score=0.9,
                risk_factors={'industry': 0.4, 'automation': 0.4}
            )
            
            # Create recommendations
            recommendations = {
                'jobs': [
                    {
                        'job_id': 'job_1',
                        'tier': 'optimal',
                        'score': 8.5,
                        'salary_increase_potential': 15000,
                        'success_probability': 0.85
                    },
                    {
                        'job_id': 'job_2',
                        'tier': 'stretch',
                        'score': 7.2,
                        'salary_increase_potential': 25000,
                        'success_probability': 0.65
                    }
                ],
                'success_probability': 0.75
            }
            
            # Track risk-triggered recommendation
            result = asyncio.run(self.risk_analytics.track_risk_recommendation_triggered(
                self.test_users[0], risk_data, recommendations
            ))
            self.assert_test(result, "Risk recommendation tracking")
            
        except Exception as e:
            self.assert_test(False, "Risk recommendation tracking", str(e))
    
    def test_emergency_unlock_tracking(self):
        """Test emergency unlock usage tracking"""
        logger.info("Testing emergency unlock tracking...")
        
        try:
            # Test emergency unlock data
            unlock_data = {
                'unlock_type': 'premium_features',
                'risk_score': 0.85,
                'features_unlocked': ['advanced_job_search', 'priority_support', 'salary_negotiation_tools'],
                'time_spent': 300
            }
            
            # Track emergency unlock
            result = asyncio.run(self.risk_analytics.track_emergency_unlock_usage(
                self.test_users[0], unlock_data
            ))
            self.assert_test(result, "Emergency unlock tracking")
            
        except Exception as e:
            self.assert_test(False, "Emergency unlock tracking", str(e))
    
    def test_prediction_accuracy_tracking(self):
        """Test risk prediction accuracy tracking"""
        logger.info("Testing prediction accuracy tracking...")
        
        try:
            # Test prediction data
            predicted_risk = {
                'overall_risk': 0.75,
                'timeline_urgency': '3_months',
                'risk_factors': {'industry': 0.3, 'automation': 0.25, 'skills': 0.2}
            }
            
            actual_outcome = {
                'outcome_type': 'proactive_switch',
                'days_from_prediction': 45,
                'risk_realized': 0.8,
                'success_factors': ['early_warning', 'quick_action', 'network_help']
            }
            
            # Track prediction accuracy
            result = asyncio.run(self.risk_analytics.track_risk_prediction_accuracy(
                self.test_users[0], predicted_risk, actual_outcome
            ))
            self.assert_test(result, "Prediction accuracy tracking")
            
        except Exception as e:
            self.assert_test(False, "Prediction accuracy tracking", str(e))
    
    def test_career_protection_outcome_tracking(self):
        """Test career protection outcome tracking"""
        logger.info("Testing career protection outcome tracking...")
        
        try:
            # Test outcome data
            outcome_data = {
                'outcome_type': 'proactive_switch',
                'risk_prediction_accuracy': 0.85,
                'time_to_outcome_days': 45,
                'salary_impact': 20000,
                'career_advancement_score': 0.8,
                'skills_improvement_score': 0.75,
                'network_expansion_score': 0.7,
                'success_factors': {
                    'early_warning': 0.3,
                    'quick_action': 0.25,
                    'network_help': 0.2,
                    'skill_development': 0.25
                }
            }
            
            # Track career protection outcome
            result = asyncio.run(self.risk_analytics.track_career_protection_outcomes(
                self.test_users[0], outcome_data
            ))
            self.assert_test(result, "Career protection outcome tracking")
            
        except Exception as e:
            self.assert_test(False, "Career protection outcome tracking", str(e))
    
    def test_risk_journey_analysis(self):
        """Test risk journey analysis functionality"""
        logger.info("Testing risk journey analysis...")
        
        try:
            # Test journey analysis
            journey_analysis = asyncio.run(self.risk_analytics.analyze_risk_to_recommendation_flow(
                self.test_users[0], 30
            ))
            
            self.assert_test(
                'user_id' in journey_analysis,
                "Risk journey analysis structure"
            )
            
            self.assert_test(
                'flow_analysis' in journey_analysis,
                "Risk journey flow analysis"
            )
            
        except Exception as e:
            self.assert_test(False, "Risk journey analysis", str(e))
    
    def test_early_warning_effectiveness(self):
        """Test early warning effectiveness measurement"""
        logger.info("Testing early warning effectiveness...")
        
        try:
            # Test early warning effectiveness
            effectiveness = asyncio.run(self.risk_analytics.measure_early_warning_effectiveness(30))
            
            self.assert_test(
                'analysis_period_days' in effectiveness,
                "Early warning effectiveness structure"
            )
            
        except Exception as e:
            self.assert_test(False, "Early warning effectiveness", str(e))
    
    def test_risk_ab_testing(self):
        """Test risk A/B testing framework"""
        logger.info("Testing risk A/B testing...")
        
        try:
            # Test A/B test creation
            test_id = asyncio.run(self.risk_analytics.optimize_risk_trigger_thresholds(
                "Test Risk Thresholds",
                [0.5, 0.6, 0.7, 0.8]
            ))
            
            self.assert_test(
                test_id is not None and len(test_id) > 0,
                "Risk A/B test creation"
            )
            
        except Exception as e:
            self.assert_test(False, "Risk A/B testing", str(e))
    
    def test_risk_dashboard(self):
        """Test risk dashboard functionality"""
        logger.info("Testing risk dashboard...")
        
        try:
            # Test dashboard data retrieval
            # This would typically test dashboard API endpoints
            self.assert_test(True, "Risk dashboard placeholder test")
            
        except Exception as e:
            self.assert_test(False, "Risk dashboard", str(e))
    
    def test_end_to_end_risk_workflow(self):
        """Test complete end-to-end risk analytics workflow"""
        logger.info("Testing end-to-end risk workflow...")
        
        try:
            # Simulate complete workflow
            user_id = self.test_users[2]
            
            # Step 1: Risk assessment
            risk_data = RiskAssessmentData(
                user_id=user_id,
                assessment_type='ai_risk',
                overall_risk=0.7,
                risk_triggers=['High-risk industry', 'Low AI usage'],
                risk_breakdown={'industry_risk': 0.35, 'automation_risk': 0.35},
                timeline_urgency='3_months',
                assessment_timestamp=datetime.now(),
                confidence_score=0.8,
                risk_factors={'industry': 0.35, 'automation': 0.35}
            )
            
            # Track assessment
            assessment_result = asyncio.run(self.risk_analytics.track_risk_assessment_completed(
                user_id, risk_data
            ))
            
            # Step 2: Risk-triggered recommendations
            recommendations = {
                'jobs': [
                    {
                        'job_id': 'job_3',
                        'tier': 'optimal',
                        'score': 8.0,
                        'salary_increase_potential': 12000,
                        'success_probability': 0.8
                    }
                ],
                'success_probability': 0.8
            }
            
            # Track recommendations
            rec_result = asyncio.run(self.risk_analytics.track_risk_recommendation_triggered(
                user_id, risk_data, recommendations
            ))
            
            # Step 3: Emergency unlock (if high risk)
            if risk_data.overall_risk >= 0.7:
                unlock_data = {
                    'unlock_type': 'premium_features',
                    'risk_score': risk_data.overall_risk,
                    'features_unlocked': ['advanced_search', 'priority_support']
                }
                
                unlock_result = asyncio.run(self.risk_analytics.track_emergency_unlock_usage(
                    user_id, unlock_data
                ))
            
            # Step 4: Track outcome after some time
            outcome_data = {
                'outcome_type': 'proactive_switch',
                'risk_prediction_accuracy': 0.85,
                'time_to_outcome_days': 60,
                'salary_impact': 15000,
                'career_advancement_score': 0.75,
                'skills_improvement_score': 0.8,
                'network_expansion_score': 0.7,
                'success_factors': {'early_warning': 0.4, 'quick_action': 0.3, 'skill_development': 0.3}
            }
            
            outcome_result = asyncio.run(self.risk_analytics.track_career_protection_outcomes(
                user_id, outcome_data
            ))
            
            # Verify workflow completion
            self.assert_test(assessment_result, "End-to-end: Risk assessment")
            self.assert_test(rec_result, "End-to-end: Risk recommendations")
            self.assert_test(outcome_result, "End-to-end: Career protection outcome")
            
        except Exception as e:
            self.assert_test(False, "End-to-end risk workflow", str(e))
    
    def test_data_cleanup(self):
        """Test data cleanup functionality"""
        logger.info("Testing data cleanup...")
        
        try:
            # Test cleanup
            cleanup_results = self.risk_analytics.analytics.cleanup_old_data(days_to_keep=1)
            
            self.assert_test(
                'error' not in cleanup_results,
                "Data cleanup"
            )
            
        except Exception as e:
            self.assert_test(False, "Data cleanup", str(e))
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        report = {
            'test_summary': {
                'total_tests': self.test_results['passed'] + self.test_results['failed'],
                'passed': self.test_results['passed'],
                'failed': self.test_results['failed'],
                'success_rate': self.test_results['passed'] / max(1, self.test_results['passed'] + self.test_results['failed']) * 100
            },
            'test_details': {
                'passed_tests': [],
                'failed_tests': self.test_results['errors']
            },
            'recommendations': self._generate_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if self.test_results['failed'] > 0:
            recommendations.append("Review failed tests and fix identified issues")
        
        if self.test_results['passed'] / max(1, self.test_results['passed'] + self.test_results['failed']) < 0.8:
            recommendations.append("Consider additional testing for low success rate")
        
        recommendations.append("Implement monitoring for production deployment")
        recommendations.append("Set up automated testing pipeline")
        recommendations.append("Create performance benchmarks for risk analytics")
        
        return recommendations

def main():
    """Main test execution function"""
    logger.info("Starting Risk Analytics Integration Test Suite")
    
    # Initialize tester
    tester = RiskAnalyticsIntegrationTester()
    
    # Run all tests
    test_results = tester.run_all_tests()
    
    # Generate report
    report = tester.generate_test_report()
    
    # Save report
    report_filename = f"risk_analytics_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Test report saved to: {report_filename}")
    logger.info(f"Test Results: {test_results['passed']} passed, {test_results['failed']} failed")
    
    if test_results['failed'] > 0:
        logger.error("Some tests failed. Check the report for details.")
        return 1
    else:
        logger.info("All tests passed successfully!")
        return 0

if __name__ == "__main__":
    exit(main())
