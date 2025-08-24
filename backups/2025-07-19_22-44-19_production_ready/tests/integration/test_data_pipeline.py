"""
Integration tests for complete data pipeline
Tests data ingestion, processing, scoring, and storage
"""

import unittest
import tempfile
import os
import json
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from backend.ml.job_security_predictor import JobSecurityPredictor
from backend.ml.utils.feature_engineering import FeatureEngineer
from backend.integrations.financial_planning_integration import FinancialPlanningIntegration
from backend.integrations.goal_setting_integration import GoalSettingIntegration
from backend.integrations.recommendations_integration import RecommendationsIntegration


class TestDataPipelineIntegration(unittest.TestCase):
    """Test complete data pipeline integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.predictor = JobSecurityPredictor()
        self.feature_engineer = FeatureEngineer()
        self.financial_integration = FinancialPlanningIntegration()
        self.goal_integration = GoalSettingIntegration()
        self.recommendations_integration = RecommendationsIntegration()
        
        # Create test data
        self.test_user_data = self._create_test_user_data()
        self.test_company_data = self._create_test_company_data()
        self.test_market_data = self._create_test_market_data()
        
        # Create temporary database
        self.temp_db_path = tempfile.mktemp(suffix='.db')
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)
    
    def _create_test_user_data(self):
        """Create comprehensive test user data"""
        return {
            'id': 1,
            'age': 32,
            'years_experience': 8,
            'education_level': 'bachelor',
            'skills': ['python', 'data_analysis', 'project_management', 'machine_learning'],
            'current_salary': 85000,
            'tenure_months': 36,
            'performance_rating': 4.5,
            'department': 'engineering',
            'role_level': 'senior',
            'certifications': ['AWS', 'PMP'],
            'languages': ['English', 'Spanish'],
            'remote_work_capability': True,
            'willingness_to_relocate': True,
            'industry_experience': 6,
            'management_experience': 2,
            'publications': 3,
            'patents': 1,
            'awards': ['Employee of the Year 2023'],
            'volunteer_work': True,
            'professional_memberships': ['IEEE', 'ACM'],
            'github_contributions': 150,
            'linkedin_connections': 500,
            'blog_posts': 12,
            'conference_presentations': 5
        }
    
    def _create_test_company_data(self):
        """Create comprehensive test company data"""
        return {
            'company_id': 'COMP001',
            'company_name': 'TechInnovate Inc',
            'industry': 'technology',
            'sub_industry': 'software_development',
            'size': 'medium',
            'location': 'San Francisco, CA',
            'financial_health': 'strong',
            'revenue_growth': 0.25,
            'profit_margin': 0.18,
            'employee_count': 750,
            'founded_year': 2015,
            'funding_rounds': 4,
            'last_funding_date': '2023-06-15',
            'funding_amount': 50000000,
            'valuation': 500000000,
            'ipo_status': 'private',
            'acquisition_target': False,
            'layoff_history': {
                '2020': 0,
                '2021': 0,
                '2022': 0,
                '2023': 0
            },
            'hiring_trends': {
                '2020': 50,
                '2021': 75,
                '2022': 100,
                '2023': 125
            },
            'employee_satisfaction': 4.2,
            'glassdoor_rating': 4.3,
            'customer_satisfaction': 4.5,
            'market_share': 0.15,
            'competitors': ['TechCorp', 'InnovateSoft', 'DevSolutions'],
            'technology_stack': ['Python', 'React', 'AWS', 'Kubernetes'],
            'business_model': 'SaaS',
            'customer_base': 10000,
            'revenue_per_employee': 200000,
            'debt_to_equity_ratio': 0.3,
            'cash_reserves': 25000000,
            'burn_rate': 2000000,
            'runway_months': 12
        }
    
    def _create_test_market_data(self):
        """Create comprehensive test market data"""
        return {
            'industry_growth_rate': 0.12,
            'unemployment_rate': 0.035,
            'job_market_health': 'strong',
            'skill_demand': {
                'python': 'very_high',
                'data_analysis': 'very_high',
                'project_management': 'high',
                'machine_learning': 'very_high',
                'cloud_computing': 'high',
                'devops': 'high'
            },
            'geographic_economic_health': 'strong',
            'salary_trends': {
                'software_engineer': 0.08,
                'data_scientist': 0.12,
                'product_manager': 0.10
            },
            'remote_work_adoption': 0.75,
            'automation_risk': {
                'software_development': 0.15,
                'data_analysis': 0.25,
                'project_management': 0.10
            },
            'industry_disruption_risk': 0.20,
            'regulatory_environment': 'stable',
            'economic_outlook': 'positive',
            'venture_capital_activity': 'high',
            'merger_acquisition_activity': 'moderate',
            'global_economic_indicators': {
                'gdp_growth': 0.025,
                'inflation_rate': 0.03,
                'interest_rates': 0.05
            }
        }
    
    def test_complete_data_pipeline(self):
        """Test complete data pipeline from raw data to final recommendations"""
        # Step 1: Feature engineering
        features = self.feature_engineer.engineer_features(
            self.test_user_data,
            self.test_company_data,
            self.test_market_data
        )
        
        self.assertIsInstance(features, dict)
        self.assertIn('user_features', features)
        self.assertIn('company_features', features)
        self.assertIn('market_features', features)
        self.assertIn('interaction_features', features)
        
        # Step 2: Job security prediction
        prediction = self.predictor.predict_comprehensive(
            self.test_user_data,
            self.test_company_data,
            self.test_market_data
        )
        
        self.assertIn('overall_risk_score', prediction)
        self.assertIn('risk_level', prediction)
        self.assertIn('confidence', prediction)
        self.assertIn('risk_factors', prediction)
        
        # Step 3: Financial planning integration
        financial_plan = self.financial_integration.get_job_security_adjusted_financial_plan(
            1, self.test_user_data, self.test_company_data
        )
        
        self.assertIn('job_security_assessment', financial_plan)
        self.assertIn('adjusted_recommendations', financial_plan)
        self.assertIn('scenario_planning', financial_plan)
        
        # Step 4: Goal setting integration
        goals = self.goal_integration.create_job_security_aware_goals(
            1, self.test_user_data, self.test_company_data
        )
        
        self.assertIn('new_goals', goals)
        self.assertIn('career_planning', goals)
        self.assertIn('industry_scenarios', goals)
        
        # Step 5: Recommendations integration
        recommendations = self.recommendations_integration.get_personalized_recommendations(
            1, self.test_user_data, self.test_company_data
        )
        
        self.assertIn('skills_recommendations', recommendations)
        self.assertIn('networking_recommendations', recommendations)
        self.assertIn('financial_recommendations', recommendations)
        self.assertIn('action_plan', recommendations)
        
        # Step 6: Verify data consistency across pipeline
        self._verify_pipeline_consistency(prediction, financial_plan, goals, recommendations)
    
    def _verify_pipeline_consistency(self, prediction, financial_plan, goals, recommendations):
        """Verify data consistency across the pipeline"""
        # Check that risk levels are consistent
        prediction_risk = prediction['risk_level']
        financial_risk = financial_plan['job_security_assessment']['overall_risk']['risk_level']
        goals_risk = goals['job_security_assessment']['overall_risk']['risk_level']
        
        self.assertEqual(prediction_risk, financial_risk)
        self.assertEqual(prediction_risk, goals_risk)
        
        # Check that risk scores are consistent
        prediction_score = prediction['overall_risk_score']
        financial_score = financial_plan['job_security_assessment']['overall_risk']['risk_score']
        goals_score = goals['job_security_assessment']['overall_risk']['risk_score']
        
        self.assertAlmostEqual(prediction_score, financial_score, places=3)
        self.assertAlmostEqual(prediction_score, goals_score, places=3)
    
    def test_data_validation_pipeline(self):
        """Test data validation throughout the pipeline"""
        # Test with invalid user data
        invalid_user_data = self.test_user_data.copy()
        del invalid_user_data['current_salary']
        
        with self.assertRaises(ValueError):
            self.predictor.predict_comprehensive(
                invalid_user_data,
                self.test_company_data,
                self.test_market_data
            )
        
        # Test with invalid company data
        invalid_company_data = self.test_company_data.copy()
        del invalid_company_data['industry']
        
        with self.assertRaises(ValueError):
            self.predictor.predict_comprehensive(
                self.test_user_data,
                invalid_company_data,
                self.test_market_data
            )
    
    def test_performance_pipeline(self):
        """Test pipeline performance with timing"""
        import time
        
        # Test single prediction performance
        start_time = time.time()
        
        prediction = self.predictor.predict_comprehensive(
            self.test_user_data,
            self.test_company_data,
            self.test_market_data
        )
        
        single_prediction_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(single_prediction_time, 2.0)  # 2 seconds threshold
        
        # Test batch processing performance
        batch_size = 10
        batch_data = []
        
        for i in range(batch_size):
            user_data = self.test_user_data.copy()
            user_data['id'] = i + 1
            user_data['current_salary'] = 75000 + (i * 5000)
            
            company_data = self.test_company_data.copy()
            company_data['company_id'] = f'COMP{i:03d}'
            
            batch_data.append((user_data, company_data, self.test_market_data))
        
        start_time = time.time()
        
        batch_results = []
        for user_data, company_data, market_data in batch_data:
            result = self.predictor.predict_comprehensive(user_data, company_data, market_data)
            batch_results.append(result)
        
        batch_processing_time = time.time() - start_time
        
        # Should process batch efficiently
        self.assertLess(batch_processing_time, 10.0)  # 10 seconds for 10 predictions
        self.assertEqual(len(batch_results), batch_size)
    
    def test_error_handling_pipeline(self):
        """Test error handling throughout the pipeline"""
        # Test with missing ML models
        with patch.object(self.predictor, 'company_predictor') as mock_company:
            mock_company.predict.side_effect = Exception("Model error")
            
            # Should handle gracefully and return fallback values
            result = self.predictor.predict_comprehensive(
                self.test_user_data,
                self.test_company_data,
                self.test_market_data
            )
            
            self.assertIn('overall_risk_score', result)
            self.assertIn('risk_level', result)
    
    def test_data_persistence_pipeline(self):
        """Test data persistence throughout the pipeline"""
        # This would test database operations
        # For now, test that results can be serialized
        prediction = self.predictor.predict_comprehensive(
            self.test_user_data,
            self.test_company_data,
            self.test_market_data
        )
        
        # Test JSON serialization
        try:
            json_str = json.dumps(prediction, default=str)
            deserialized = json.loads(json_str)
            self.assertIsInstance(deserialized, dict)
        except Exception as e:
            self.fail(f"Failed to serialize prediction result: {e}")
    
    def test_rate_limiting_integration(self):
        """Test rate limiting and retry logic"""
        # Mock rate limiting
        with patch('time.sleep') as mock_sleep:
            # Simulate rate limiting
            with patch.object(self.predictor, 'company_predictor') as mock_company:
                mock_company.predict.side_effect = [
                    Exception("Rate limit exceeded"),
                    {'risk_score': 0.3, 'confidence': 0.8}
                ]
                
                # Should retry and succeed
                result = self.predictor.predict_comprehensive(
                    self.test_user_data,
                    self.test_company_data,
                    self.test_market_data
                )
                
                self.assertIn('overall_risk_score', result)
                mock_sleep.assert_called()  # Should have slept between retries
    
    def test_large_dataset_performance(self):
        """Test performance with large datasets"""
        # Create large dataset
        large_user_data = []
        large_company_data = []
        
        for i in range(100):
            user_data = self.test_user_data.copy()
            user_data['id'] = i + 1
            user_data['current_salary'] = 75000 + (i * 1000)
            large_user_data.append(user_data)
            
            company_data = self.test_company_data.copy()
            company_data['company_id'] = f'COMP{i:03d}'
            large_company_data.append(company_data)
        
        # Test batch processing
        import time
        start_time = time.time()
        
        results = []
        for i in range(10):  # Test with subset for performance
            result = self.predictor.predict_comprehensive(
                large_user_data[i],
                large_company_data[i],
                self.test_market_data
            )
            results.append(result)
        
        processing_time = time.time() - start_time
        
        # Should process efficiently
        self.assertLess(processing_time, 20.0)  # 20 seconds for 10 predictions
        self.assertEqual(len(results), 10)
    
    def test_data_integrity_pipeline(self):
        """Test data integrity throughout the pipeline"""
        # Test that input data is not modified
        original_user_data = self.test_user_data.copy()
        original_company_data = self.test_company_data.copy()
        original_market_data = self.test_market_data.copy()
        
        # Run pipeline
        self.predictor.predict_comprehensive(
            self.test_user_data,
            self.test_company_data,
            self.test_market_data
        )
        
        # Verify input data unchanged
        self.assertEqual(self.test_user_data, original_user_data)
        self.assertEqual(self.test_company_data, original_company_data)
        self.assertEqual(self.test_market_data, original_market_data)
    
    def test_memory_usage_pipeline(self):
        """Test memory usage optimization"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Run pipeline multiple times
        for _ in range(10):
            self.predictor.predict_comprehensive(
                self.test_user_data,
                self.test_company_data,
                self.test_market_data
            )
        
        # Get final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)  # 100MB threshold


if __name__ == '__main__':
    unittest.main() 