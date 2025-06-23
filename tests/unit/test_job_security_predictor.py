"""
Unit tests for JobSecurityPredictor
Tests individual prediction models and scoring algorithms
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backend.ml.job_security_predictor import JobSecurityPredictor
from backend.ml.models.company_predictor import CompanyPredictor
from backend.ml.models.industry_predictor import IndustryPredictor
from backend.ml.models.geographic_predictor import GeographicPredictor
from backend.ml.models.personal_risk_predictor import PersonalRiskPredictor


class TestJobSecurityPredictor(unittest.TestCase):
    """Test cases for JobSecurityPredictor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.predictor = JobSecurityPredictor()
        
        # Mock data for testing
        self.mock_user_data = {
            'id': 1,
            'age': 35,
            'years_experience': 8,
            'education_level': 'bachelor',
            'skills': ['python', 'data_analysis', 'project_management'],
            'current_salary': 75000,
            'tenure_months': 24,
            'performance_rating': 4.2,
            'department': 'engineering',
            'role_level': 'senior'
        }
        
        self.mock_company_data = {
            'company_id': 'COMP001',
            'company_name': 'Test Corp',
            'industry': 'technology',
            'size': 'medium',
            'location': 'San Francisco, CA',
            'financial_health': 'stable',
            'revenue_growth': 0.15,
            'profit_margin': 0.12,
            'employee_count': 500,
            'founded_year': 2010,
            'funding_rounds': 3,
            'last_funding_date': '2023-01-15'
        }
        
        self.mock_market_data = {
            'industry_growth_rate': 0.08,
            'unemployment_rate': 0.04,
            'job_market_health': 'strong',
            'skill_demand': {
                'python': 'high',
                'data_analysis': 'high',
                'project_management': 'medium'
            },
            'geographic_economic_health': 'strong'
        }
    
    def test_predictor_initialization(self):
        """Test that predictor initializes correctly"""
        self.assertIsNotNone(self.predictor)
        self.assertIsInstance(self.predictor.company_predictor, CompanyPredictor)
        self.assertIsInstance(self.predictor.industry_predictor, IndustryPredictor)
        self.assertIsInstance(self.predictor.geographic_predictor, GeographicPredictor)
        self.assertIsInstance(self.predictor.personal_risk_predictor, PersonalRiskPredictor)
    
    @patch('backend.ml.models.company_predictor.CompanyPredictor.predict')
    @patch('backend.ml.models.industry_predictor.IndustryPredictor.predict')
    @patch('backend.ml.models.geographic_predictor.GeographicPredictor.predict')
    @patch('backend.ml.models.personal_risk_predictor.PersonalRiskPredictor.predict')
    def test_comprehensive_prediction(self, mock_personal, mock_geo, mock_industry, mock_company):
        """Test comprehensive prediction with all models"""
        # Mock return values
        mock_company.return_value = {
            'risk_score': 0.3,
            'confidence': 0.85,
            'risk_factors': ['stable_financials', 'good_growth']
        }
        
        mock_industry.return_value = {
            'risk_score': 0.2,
            'confidence': 0.9,
            'growth_outlook': 'positive'
        }
        
        mock_geo.return_value = {
            'risk_score': 0.1,
            'confidence': 0.8,
            'economic_health': 'strong'
        }
        
        mock_personal.return_value = {
            'risk_score': 0.25,
            'confidence': 0.75,
            'risk_factors': ['good_performance', 'valuable_skills']
        }
        
        # Test comprehensive prediction
        result = self.predictor.predict_comprehensive(
            self.mock_user_data,
            self.mock_company_data,
            self.mock_market_data
        )
        
        # Verify all models were called
        mock_company.assert_called_once_with(self.mock_company_data)
        mock_industry.assert_called_once_with(self.mock_company_data.get('industry'))
        mock_geo.assert_called_once_with(self.mock_company_data.get('location'))
        mock_personal.assert_called_once_with(self.mock_user_data, self.mock_company_data)
        
        # Verify result structure
        self.assertIn('overall_risk_score', result)
        self.assertIn('risk_level', result)
        self.assertIn('confidence', result)
        self.assertIn('risk_factors', result)
        self.assertIn('recommendations', result)
        
        # Verify risk level categorization
        self.assertIn(result['risk_level'], ['low', 'medium', 'high', 'very_high'])
    
    def test_risk_level_categorization(self):
        """Test risk level categorization logic"""
        test_cases = [
            (0.1, 'low'),
            (0.3, 'low'),
            (0.4, 'medium'),
            (0.6, 'medium'),
            (0.7, 'high'),
            (0.8, 'high'),
            (0.9, 'very_high'),
            (1.0, 'very_high')
        ]
        
        for score, expected_level in test_cases:
            with self.subTest(score=score):
                level = self.predictor._categorize_risk_level(score)
                self.assertEqual(level, expected_level)
    
    def test_confidence_calculation(self):
        """Test confidence calculation from multiple models"""
        confidences = [0.8, 0.9, 0.7, 0.85]
        expected_confidence = min(confidences)  # Should use minimum confidence
        
        calculated_confidence = self.predictor._calculate_overall_confidence(confidences)
        self.assertEqual(calculated_confidence, expected_confidence)
    
    def test_risk_factor_aggregation(self):
        """Test aggregation of risk factors from multiple models"""
        risk_factors = [
            ['financial_instability', 'high_debt'],
            ['industry_decline', 'automation_risk'],
            ['economic_recession'],
            ['poor_performance', 'skill_gap']
        ]
        
        aggregated = self.predictor._aggregate_risk_factors(risk_factors)
        
        # Should combine all unique factors
        expected_factors = set([
            'financial_instability', 'high_debt', 'industry_decline',
            'automation_risk', 'economic_recession', 'poor_performance', 'skill_gap'
        ])
        
        self.assertEqual(set(aggregated), expected_factors)
    
    def test_recommendation_generation(self):
        """Test recommendation generation based on risk level"""
        test_cases = [
            ('low', ['maintain_current_practices']),
            ('medium', ['monitor_industry_trends', 'build_emergency_fund']),
            ('high', ['accelerate_skill_development', 'network_actively', 'build_emergency_fund']),
            ('very_high', ['immediate_job_search', 'maximize_savings', 'obtain_insurance'])
        ]
        
        for risk_level, expected_recommendations in test_cases:
            with self.subTest(risk_level=risk_level):
                recommendations = self.predictor._generate_recommendations(risk_level)
                
                # Should contain expected recommendations
                for expected_rec in expected_recommendations:
                    self.assertIn(expected_rec, recommendations)
    
    def test_invalid_input_handling(self):
        """Test handling of invalid or missing input data"""
        # Test with missing user data
        with self.assertRaises(ValueError):
            self.predictor.predict_comprehensive({}, self.mock_company_data, self.mock_market_data)
        
        # Test with missing company data
        with self.assertRaises(ValueError):
            self.predictor.predict_comprehensive(self.mock_user_data, {}, self.mock_market_data)
        
        # Test with None values
        with self.assertRaises(ValueError):
            self.predictor.predict_comprehensive(None, self.mock_company_data, self.mock_market_data)
    
    def test_edge_case_risk_scores(self):
        """Test edge cases for risk scores"""
        # Test boundary values
        self.assertEqual(self.predictor._categorize_risk_level(0.0), 'low')
        self.assertEqual(self.predictor._categorize_risk_level(0.39), 'low')
        self.assertEqual(self.predictor._categorize_risk_level(0.4), 'medium')
        self.assertEqual(self.predictor._categorize_risk_level(0.69), 'medium')
        self.assertEqual(self.predictor._categorize_risk_level(0.7), 'high')
        self.assertEqual(self.predictor._categorize_risk_level(0.79), 'high')
        self.assertEqual(self.predictor._categorize_risk_level(0.8), 'very_high')
        self.assertEqual(self.predictor._categorize_risk_level(1.0), 'very_high')
    
    @patch('backend.ml.models.company_predictor.CompanyPredictor.predict')
    def test_company_predictor_integration(self, mock_company_predict):
        """Test integration with company predictor"""
        mock_company_predict.return_value = {
            'risk_score': 0.4,
            'confidence': 0.8,
            'risk_factors': ['moderate_growth', 'stable_financials']
        }
        
        result = self.predictor.company_predictor.predict(self.mock_company_data)
        
        mock_company_predict.assert_called_once_with(self.mock_company_data)
        self.assertEqual(result['risk_score'], 0.4)
        self.assertEqual(result['confidence'], 0.8)
    
    @patch('backend.ml.models.industry_predictor.IndustryPredictor.predict')
    def test_industry_predictor_integration(self, mock_industry_predict):
        """Test integration with industry predictor"""
        mock_industry_predict.return_value = {
            'risk_score': 0.2,
            'confidence': 0.9,
            'growth_outlook': 'positive'
        }
        
        result = self.predictor.industry_predictor.predict('technology')
        
        mock_industry_predict.assert_called_once_with('technology')
        self.assertEqual(result['risk_score'], 0.2)
        self.assertEqual(result['confidence'], 0.9)
    
    def test_data_validation(self):
        """Test data validation for required fields"""
        # Test valid data
        self.assertTrue(self.predictor._validate_user_data(self.mock_user_data))
        self.assertTrue(self.predictor._validate_company_data(self.mock_company_data))
        
        # Test invalid user data
        invalid_user_data = self.mock_user_data.copy()
        del invalid_user_data['current_salary']
        self.assertFalse(self.predictor._validate_user_data(invalid_user_data))
        
        # Test invalid company data
        invalid_company_data = self.mock_company_data.copy()
        del invalid_company_data['industry']
        self.assertFalse(self.predictor._validate_company_data(invalid_company_data))
    
    def test_performance_benchmark(self):
        """Test prediction performance with timing"""
        import time
        
        start_time = time.time()
        
        # Mock all predictors to return quickly
        with patch.object(self.predictor.company_predictor, 'predict') as mock_company, \
             patch.object(self.predictor.industry_predictor, 'predict') as mock_industry, \
             patch.object(self.predictor.geographic_predictor, 'predict') as mock_geo, \
             patch.object(self.predictor.personal_risk_predictor, 'predict') as mock_personal:
            
            mock_company.return_value = {'risk_score': 0.3, 'confidence': 0.8}
            mock_industry.return_value = {'risk_score': 0.2, 'confidence': 0.9}
            mock_geo.return_value = {'risk_score': 0.1, 'confidence': 0.8}
            mock_personal.return_value = {'risk_score': 0.25, 'confidence': 0.75}
            
            result = self.predictor.predict_comprehensive(
                self.mock_user_data,
                self.mock_company_data,
                self.mock_market_data
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(execution_time, 1.0)  # 1 second threshold
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main() 