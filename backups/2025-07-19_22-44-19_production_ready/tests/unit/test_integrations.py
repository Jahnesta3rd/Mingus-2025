"""
Unit tests for job security integrations
Tests financial planning, goal setting, and recommendations integrations
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta

from backend.integrations.financial_planning_integration import FinancialPlanningIntegration
from backend.integrations.goal_setting_integration import GoalSettingIntegration
from backend.integrations.recommendations_integration import RecommendationsIntegration


class TestFinancialPlanningIntegration(unittest.TestCase):
    """Test cases for FinancialPlanningIntegration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.integration = FinancialPlanningIntegration()
        
        self.mock_user_data = {
            'id': 1,
            'current_salary': 75000,
            'monthly_expenses': 4000,
            'current_savings': 12000,
            'investment_risk_tolerance': 0.7,
            'debt_payments': 800,
            'investment_assets': 25000
        }
        
        self.mock_company_data = {
            'company_id': 'COMP001',
            'industry': 'technology',
            'financial_health': 'stable',
            'revenue_growth': 0.15,
            'employee_count': 500
        }
    
    @patch('backend.ml.job_security_predictor.JobSecurityPredictor')
    def test_get_job_security_adjusted_financial_plan(self, mock_predictor_class):
        """Test financial plan generation with job security adjustments"""
        # Mock predictor
        mock_predictor = Mock()
        mock_predictor.personal_risk_predictor.predict.return_value = {
            'risk_score': 0.3, 'confidence': 0.8
        }
        mock_predictor.company_predictor.predict.return_value = {
            'risk_score': 0.4, 'confidence': 0.85
        }
        mock_predictor.industry_predictor.predict.return_value = {
            'risk_score': 0.2, 'confidence': 0.9
        }
        mock_predictor_class.return_value = mock_predictor
        
        # Mock cash flow service
        with patch.object(self.integration, 'cash_flow_service') as mock_cash_flow:
            mock_cash_flow.get_user_cash_flow.return_value = {
                'monthly_income': 6250,
                'monthly_expenses': 4000,
                'current_savings': 12000,
                'monthly_savings_rate': 0.2,
                'monthly_debt_payments': 800,
                'investment_assets': 25000
            }
            
            result = self.integration.get_job_security_adjusted_financial_plan(
                1, self.mock_user_data, self.mock_company_data
            )
        
        # Verify result structure
        self.assertIn('job_security_assessment', result)
        self.assertIn('current_financials', result)
        self.assertIn('adjusted_recommendations', result)
        self.assertIn('scenario_planning', result)
        self.assertIn('action_plan', result)
        
        # Verify emergency fund recommendations
        emergency_fund = result['adjusted_recommendations']['emergency_fund']
        self.assertIn('current_months', emergency_fund)
        self.assertIn('recommended_months', emergency_fund)
        self.assertIn('gap', emergency_fund)
    
    def test_emergency_fund_calculations(self):
        """Test emergency fund calculations for different risk levels"""
        test_cases = [
            ('low', 3, 12000),      # 3 months * 4000
            ('medium', 6, 24000),   # 6 months * 4000
            ('high', 9, 36000),     # 9 months * 4000
            ('very_high', 12, 48000) # 12 months * 4000
        ]
        
        for risk_level, expected_months, expected_amount in test_cases:
            with self.subTest(risk_level=risk_level):
                multiplier = self.integration.emergency_fund_multipliers[risk_level]
                self.assertEqual(multiplier, expected_months)
                
                recommended_amount = self.mock_user_data['monthly_expenses'] * multiplier
                self.assertEqual(recommended_amount, expected_amount)
    
    def test_investment_risk_adjustments(self):
        """Test investment risk tolerance adjustments"""
        base_risk_tolerance = 0.7
        
        test_cases = [
            ('low', 0.7),      # No change
            ('medium', 0.56),  # 0.7 * 0.8
            ('high', 0.42),    # 0.7 * 0.6
            ('very_high', 0.28) # 0.7 * 0.4
        ]
        
        for risk_level, expected_adjusted in test_cases:
            with self.subTest(risk_level=risk_level):
                adjustment = self.integration.risk_adjustments[risk_level]
                adjusted_risk = base_risk_tolerance * adjustment
                self.assertAlmostEqual(adjusted_risk, expected_adjusted, places=2)
    
    def test_debt_recommendations(self):
        """Test debt management recommendations"""
        current_financials = {
            'monthly_income': 6250,
            'debt_payments': 2500,  # 40% debt-to-income
            'monthly_expenses': 4000
        }
        
        # Test high risk level
        recommendations = self.integration._get_debt_recommendations(
            current_financials, 'high'
        )
        
        self.assertEqual(recommendations['debt_to_income_ratio'], 0.4)
        self.assertIn('Prioritize debt reduction', recommendations['recommendations'])
        self.assertEqual(recommendations['priority'], 'high')
    
    def test_insurance_recommendations(self):
        """Test insurance recommendations"""
        user_data = {
            'current_salary': 75000,
            'disability_insurance': False,
            'life_insurance': False
        }
        
        recommendations = self.integration._get_insurance_recommendations(
            user_data, 'high'
        )
        
        self.assertIn('disability_insurance', recommendations['recommendations'])
        self.assertIn('life_insurance', recommendations['recommendations'])
        self.assertGreater(recommendations['total_monthly_cost'], 0)


class TestGoalSettingIntegration(unittest.TestCase):
    """Test cases for GoalSettingIntegration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.integration = GoalSettingIntegration()
        
        self.mock_user_data = {
            'id': 1,
            'current_role': 'software_engineer',
            'skills': ['python', 'javascript'],
            'current_salary': 75000,
            'monthly_expenses': 4000
        }
        
        self.mock_company_data = {
            'company_id': 'COMP001',
            'industry': 'technology',
            'location': 'San Francisco, CA'
        }
    
    @patch('backend.ml.job_security_predictor.JobSecurityPredictor')
    def test_create_job_security_aware_goals(self, mock_predictor_class):
        """Test goal creation with job security considerations"""
        # Mock predictor
        mock_predictor = Mock()
        mock_predictor.personal_risk_predictor.predict.return_value = {
            'risk_score': 0.6, 'confidence': 0.8
        }
        mock_predictor.company_predictor.predict.return_value = {
            'risk_score': 0.5, 'confidence': 0.85
        }
        mock_predictor.industry_predictor.predict.return_value = {
            'risk_score': 0.4, 'confidence': 0.9
        }
        mock_predictor_class.return_value = mock_predictor
        
        result = self.integration.create_job_security_aware_goals(
            1, self.mock_user_data, self.mock_company_data
        )
        
        # Verify result structure
        self.assertIn('job_security_assessment', result)
        self.assertIn('goal_analysis', result)
        self.assertIn('new_goals', result)
        self.assertIn('updated_goals', result)
        self.assertIn('career_planning', result)
    
    def test_goal_priority_calculations(self):
        """Test goal priority calculations based on risk level"""
        skill = {
            'name': 'Data Analysis',
            'importance': 'high',
            'demand_trend': 'increasing'
        }
        
        test_cases = [
            ('low', 0.5),      # 1.0 * 0.5
            ('medium', 1.0),   # 1.0 * 1.0
            ('high', 1.5),     # 1.0 * 1.5
            ('very_high', 2.0) # 1.0 * 2.0
        ]
        
        for risk_level, expected_priority in test_cases:
            with self.subTest(risk_level=risk_level):
                priority = self.integration._calculate_skill_priority(skill, risk_level)
                self.assertEqual(priority, expected_priority)
    
    def test_career_transition_timeline(self):
        """Test career transition timeline calculations"""
        test_cases = [
            ('low', 12, 3),      # 12 months prep, 3 months search
            ('medium', 8, 2),    # 8 months prep, 2 months search
            ('high', 6, 2),      # 6 months prep, 2 months search
            ('very_high', 3, 1)  # 3 months prep, 1 month search
        ]
        
        for risk_level, expected_prep, expected_search in test_cases:
            with self.subTest(risk_level=risk_level):
                timeline = self.integration._get_transition_timeline(risk_level)
                self.assertEqual(timeline['preparation_months'], expected_prep)
                self.assertEqual(timeline['active_search_months'], expected_search)
    
    def test_skill_gap_identification(self):
        """Test skill gap identification"""
        user_data = {
            'skills': ['python', 'javascript']
        }
        
        company_data = {
            'industry': 'technology'
        }
        
        skill_gaps = self.integration._identify_skill_gaps(user_data, company_data)
        
        # Should identify missing skills
        self.assertIsInstance(skill_gaps, list)
        for gap in skill_gaps:
            self.assertIn('skill_name', gap)
            self.assertIn('importance', gap)
            self.assertIn('priority', gap)


class TestRecommendationsIntegration(unittest.TestCase):
    """Test cases for RecommendationsIntegration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.integration = RecommendationsIntegration()
        
        self.mock_user_data = {
            'id': 1,
            'current_role': 'software_engineer',
            'skills': ['python', 'javascript'],
            'current_salary': 75000,
            'monthly_expenses': 4000,
            'emergency_fund': 8000
        }
        
        self.mock_company_data = {
            'company_id': 'COMP001',
            'industry': 'technology',
            'location': 'San Francisco, CA'
        }
    
    @patch('backend.ml.job_security_predictor.JobSecurityPredictor')
    def test_get_personalized_recommendations(self, mock_predictor_class):
        """Test personalized recommendations generation"""
        # Mock predictor
        mock_predictor = Mock()
        mock_predictor.personal_risk_predictor.predict.return_value = {
            'risk_score': 0.5, 'confidence': 0.8
        }
        mock_predictor.company_predictor.predict.return_value = {
            'risk_score': 0.4, 'confidence': 0.85
        }
        mock_predictor.industry_predictor.predict.return_value = {
            'risk_score': 0.3, 'confidence': 0.9
        }
        mock_predictor_class.return_value = mock_predictor
        
        result = self.integration.get_personalized_recommendations(
            1, self.mock_user_data, self.mock_company_data
        )
        
        # Verify result structure
        self.assertIn('job_security_assessment', result)
        self.assertIn('skills_recommendations', result)
        self.assertIn('networking_recommendations', result)
        self.assertIn('financial_recommendations', result)
        self.assertIn('career_recommendations', result)
        self.assertIn('action_plan', result)
    
    def test_skills_recommendations(self):
        """Test skills development recommendations"""
        user_data = {
            'skills': ['python']
        }
        
        company_data = {
            'industry': 'technology'
        }
        
        job_security_assessment = {
            'overall_risk': {'risk_level': 'medium'}
        }
        
        recommendations = self.integration._get_skills_recommendations(
            user_data, company_data, job_security_assessment
        )
        
        self.assertIn('skill_gaps', recommendations)
        self.assertIn('learning_resources', recommendations)
        self.assertIn('priority_skills', recommendations)
        
        # Should identify missing skills
        self.assertGreater(len(recommendations['skill_gaps']), 0)
    
    def test_networking_recommendations(self):
        """Test networking recommendations"""
        company_data = {
            'industry': 'technology',
            'location': 'San Francisco, CA'
        }
        
        job_security_assessment = {
            'overall_risk': {'risk_level': 'medium'}
        }
        
        recommendations = self.integration._get_networking_recommendations(
            self.mock_user_data, company_data, job_security_assessment
        )
        
        self.assertIn('networking_plan', recommendations)
        self.assertIn('activities', recommendations)
        self.assertIn('opportunities', recommendations)
        
        # Should have networking plan
        plan = recommendations['networking_plan']
        self.assertIn('monthly_events', plan)
        self.assertIn('online_activities', plan)
    
    def test_financial_recommendations(self):
        """Test financial product recommendations"""
        user_data = {
            'current_salary': 75000,
            'monthly_expenses': 4000,
            'emergency_fund': 8000,
            'disability_insurance': False,
            'life_insurance': False
        }
        
        company_data = {
            'industry': 'technology'
        }
        
        job_security_assessment = {
            'overall_risk': {'risk_level': 'medium'}
        }
        
        recommendations = self.integration._get_financial_recommendations(
            user_data, company_data, job_security_assessment
        )
        
        self.assertIn('recommendations', recommendations)
        self.assertIn('providers', recommendations)
        self.assertIn('priority_products', recommendations)
        
        # Should have emergency fund recommendations
        emergency_fund = recommendations['recommendations']['emergency_fund']
        self.assertIn('current_amount', emergency_fund)
        self.assertIn('recommended_amount', emergency_fund)
    
    def test_priority_recommendations(self):
        """Test priority recommendations based on risk level"""
        test_cases = [
            ('very_high', 'Immediately build emergency fund'),
            ('high', 'Build emergency fund to 9 months'),
            ('medium', 'Build emergency fund to 6 months'),
            ('low', 'Maintain current emergency fund')
        ]
        
        for risk_level, expected_recommendation in test_cases:
            with self.subTest(risk_level=risk_level):
                assessment = {
                    'overall_risk': {'risk_level': risk_level}
                }
                
                recommendations = self.integration._get_priority_recommendations(assessment)
                
                # Should contain expected recommendation
                found = any(expected_recommendation in rec for rec in recommendations)
                self.assertTrue(found, f"Expected recommendation not found for {risk_level}")


if __name__ == '__main__':
    unittest.main() 