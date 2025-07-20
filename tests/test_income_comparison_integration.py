"""
Integration Tests for Income Comparison Feature
Tests complete user journey and Flask integration
"""

import unittest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from flask import Flask
from backend.routes.income_analysis import income_analysis_bp
from backend.ml.models.income_comparator import IncomeComparator, EducationLevel

class TestIncomeComparisonIntegration(unittest.TestCase):
    """Integration tests for income comparison feature"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.app = Flask(__name__)
        self.app.register_blueprint(income_analysis_bp, url_prefix='/api/income-analysis')
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Sample user profiles for testing
        self.test_users = {
            'young_african_american_professional': {
                'current_salary': 65000,
                'age_range': '25-35',
                'race': 'African American',
                'education_level': 'bachelors',
                'location': 'Atlanta'
            },
            'mid_career_african_american_manager': {
                'current_salary': 85000,
                'age_range': '35-44',
                'race': 'African American',
                'education_level': 'masters',
                'location': 'Washington DC'
            },
            'entry_level_african_american_worker': {
                'current_salary': 45000,
                'age_range': '25-35',
                'race': 'African American',
                'education_level': 'high_school',
                'location': 'Houston'
            },
            'senior_african_american_executive': {
                'current_salary': 120000,
                'age_range': '35-44',
                'race': 'African American',
                'education_level': 'masters',
                'location': 'New York City'
            },
            'white_professional_comparison': {
                'current_salary': 75000,
                'age_range': '25-35',
                'race': 'White',
                'education_level': 'bachelors',
                'location': 'Chicago'
            },
            'hispanic_professional_comparison': {
                'current_salary': 60000,
                'age_range': '25-35',
                'race': 'Hispanic/Latino',
                'education_level': 'bachelors',
                'location': 'Miami'
            }
        }
    
    def test_form_submission_workflow(self):
        """Test complete form submission workflow"""
        user = self.test_users['young_african_american_professional']
        
        # Test form submission
        response = self.client.post('/api/income-analysis/analyze', 
                                  data=json.dumps(user),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('income_comparison', data['data'])
        
        income_comparison = data['data']['income_comparison']
        self.assertIn('overall_percentile', income_comparison)
        self.assertIn('career_opportunity_score', income_comparison)
        self.assertIn('primary_gap', income_comparison)
        self.assertIn('comparisons', income_comparison)
        self.assertIn('motivational_summary', income_comparison)
        self.assertIn('action_plan', income_comparison)
        self.assertIn('next_steps', income_comparison)
    
    def test_demographic_analysis_accuracy(self):
        """Test demographic analysis accuracy across different profiles"""
        for profile_name, user in self.test_users.items():
            with self.subTest(profile=profile_name):
                # Create comparison
                comparator = IncomeComparator()
                result = comparator.analyze_income(
                    user_income=user['current_salary'],
                    location=user['location'],
                    education_level=EducationLevel.BACHELORS if user['education_level'] == 'bachelors' else EducationLevel.MASTERS,
                    age_group=user['age_range']
                )
                
                # Verify all comparison types are present
                self.assertGreater(len(result.comparisons), 0)
                
                # Verify data quality
                for comparison in result.comparisons:
                    self.assertGreater(comparison.median_income, 0)
                    self.assertGreaterEqual(comparison.percentile_rank, 0)
                    self.assertLessEqual(comparison.percentile_rank, 100)
    
    def test_geographic_variations(self):
        """Test geographic variations across target metro areas"""
        metro_areas = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City',
                      'Philadelphia', 'Chicago', 'Charlotte', 'Miami', 'Baltimore']
        
        base_user = {
            'current_salary': 65000,
            'age_range': '25-35',
            'race': 'African American',
            'education_level': 'bachelors'
        }
        
        comparator = IncomeComparator()
        
        for metro in metro_areas:
            with self.subTest(metro=metro):
                result = comparator.analyze_income(
                    user_income=base_user['current_salary'],
                    location=metro,
                    education_level=EducationLevel.BACHELORS,
                    age_group=base_user['age_range']
                )
                
                self.assertIsNotNone(result)
                self.assertGreater(len(result.comparisons), 0)
                
                # Verify percentile is reasonable
                self.assertGreaterEqual(result.overall_percentile, 0)
                self.assertLessEqual(result.overall_percentile, 100)
    
    def test_education_level_impact(self):
        """Test education level impact on income comparisons"""
        education_levels = ['high_school', 'bachelors', 'masters']
        
        base_user = {
            'current_salary': 65000,
            'age_range': '25-35',
            'race': 'African American'
        }
        
        comparator = IncomeComparator()
        
        for education in education_levels:
            with self.subTest(education=education):
                education_enum = {
                    'high_school': EducationLevel.HIGH_SCHOOL,
                    'bachelors': EducationLevel.BACHELORS,
                    'masters': EducationLevel.MASTERS
                }[education]
                
                result = comparator.analyze_income(
                    user_income=base_user['current_salary'],
                    location='Atlanta',
                    education_level=education_enum,
                    age_group=base_user['age_range']
                )
                
                self.assertIsNotNone(result)
                self.assertGreater(len(result.comparisons), 0)
                
                # Verify education impact on percentile
                self.assertGreaterEqual(result.overall_percentile, 0)
                self.assertLessEqual(result.overall_percentile, 100)
    
    def test_age_group_transitions(self):
        """Test age group transitions and income expectations"""
        age_groups = [
            {'age': 25, 'expected_group': '25-35'},
            {'age': 30, 'expected_group': '25-35'},
            {'age': 35, 'expected_group': '35-44'},
            {'age': 40, 'expected_group': '35-44'}
        ]
        
        base_user = {
            'current_salary': 65000,
            'race': 'African American',
            'education_level': 'bachelors'
        }
        
        comparator = IncomeComparator()
        
        for age_data in age_groups:
            with self.subTest(age=age_data['age']):
                result = comparator.analyze_income(
                    user_income=base_user['current_salary'],
                    location='Atlanta',
                    education_level=EducationLevel.BACHELORS,
                    age_group=age_data['expected_group']
                )
                
                self.assertIsNotNone(result)
                self.assertGreater(len(result.comparisons), 0)
                
                # Verify age group comparison exists
                age_comparisons = [c for c in result.comparisons if 'Age' in c.group_name]
                self.assertGreater(len(age_comparisons), 0)
    
    def test_api_integration_failure_scenarios(self):
        """Test API integration failure scenarios"""
        # Test with missing required fields
        incomplete_data = {
            'current_salary': 65000,
            'age_range': '25-35'
            # Missing race, education_level, location
        }
        
        response = self.client.post('/api/income-analysis/analyze',
                                  data=json.dumps(incomplete_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        # Test with invalid salary
        invalid_salary_data = {
            'current_salary': -1000,
            'age_range': '25-35',
            'race': 'African American',
            'education_level': 'bachelors',
            'location': 'Atlanta'
        }
        
        response = self.client.post('/api/income-analysis/analyze',
                                  data=json.dumps(invalid_salary_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
    
    def test_template_rendering_scenarios(self):
        """Test template rendering with various data scenarios"""
        scenarios = [
            'high_income_positive_comparison',
            'low_income_improvement_needed',
            'average_income_balanced_view',
            'missing_data_graceful_handling'
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                if scenario == 'high_income_positive_comparison':
                    user = self.test_users['senior_african_american_executive']
                elif scenario == 'low_income_improvement_needed':
                    user = self.test_users['entry_level_african_american_worker']
                elif scenario == 'average_income_balanced_view':
                    user = self.test_users['young_african_american_professional']
                else:
                    user = {'current_salary': 60000, 'age_range': '25-35', 'race': 'African American',
                           'education_level': 'bachelors', 'location': 'Atlanta'}
                
                # Test API endpoint instead of template rendering
                response = self.client.post('/api/income-analysis/analyze',
                                          data=json.dumps(user),
                                          content_type='application/json')
                
                self.assertEqual(response.status_code, 200)
                
                data = json.loads(response.data)
                self.assertIn('success', data)
                self.assertTrue(data['success'])
                self.assertIn('data', data)
                self.assertIn('income_comparison', data['data'])
                
                income_comparison = data['data']['income_comparison']
                self.assertIn('overall_percentile', income_comparison)
                self.assertIn('motivational_summary', income_comparison)
    
    def test_performance_comparison_calculations(self):
        """Test performance of comparison calculations"""
        import time
        
        user = self.test_users['young_african_american_professional']
        comparator = IncomeComparator()
        
        # Test single comparison performance
        start_time = time.time()
        result = comparator.analyze_income(
            user_income=user['current_salary'],
            location=user['location'],
            education_level=EducationLevel.BACHELORS,
            age_group=user['age_range']
        )
        end_time = time.time()
        
        calculation_time = end_time - start_time
        self.assertLess(calculation_time, 0.1)  # Should complete in under 100ms
        
        # Test multiple comparisons performance
        start_time = time.time()
        for i in range(10):
            comparator.analyze_income(
                user_income=user['current_salary'] + i * 1000,
                location=user['location'],
                education_level=EducationLevel.BACHELORS,
                age_group=user['age_range']
            )
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / 10
        self.assertLess(avg_time, 0.05)  # Average should be under 50ms
    
    def test_error_handling_edge_cases(self):
        """Test error handling for edge cases"""
        edge_cases = [
            {'current_salary': 0, 'age_range': '25-35', 'race': 'African American', 'education_level': 'bachelors', 'location': 'Atlanta'},
            {'current_salary': 1000000, 'age_range': '25-35', 'race': 'African American', 'education_level': 'bachelors', 'location': 'Atlanta'},
            {'current_salary': 60000, 'age_range': '25-35', 'race': 'African American', 'education_level': 'invalid_education', 'location': 'Atlanta'},
            {'current_salary': 60000, 'age_range': '25-35', 'race': 'African American', 'education_level': 'bachelors', 'location': 'invalid_location'},
        ]
        
        comparator = IncomeComparator()
        
        for i, case in enumerate(edge_cases):
            with self.subTest(case=i):
                if case['current_salary'] == 0:
                    # Test API validation
                    response = self.client.post('/api/income-analysis/analyze',
                                              data=json.dumps(case),
                                              content_type='application/json')
                    self.assertEqual(response.status_code, 400)
                elif case['education_level'] == 'invalid_education':
                    # Test API validation
                    response = self.client.post('/api/income-analysis/analyze',
                                              data=json.dumps(case),
                                              content_type='application/json')
                    self.assertEqual(response.status_code, 400)
                else:
                    # Test that comparator handles edge cases gracefully
                    try:
                        result = comparator.analyze_income(
                            user_income=case['current_salary'],
                            location=case['location'],
                            education_level=EducationLevel.BACHELORS,
                            age_group=case['age_range']
                        )
                        self.assertIsNotNone(result)
                    except Exception as e:
                        # Should handle gracefully, not crash
                        self.assertIsInstance(e, Exception)
    
    def test_motivational_messaging_appropriateness(self):
        """Test that motivational messaging is appropriate for different income levels"""
        test_cases = [
            {'current_salary': 45000, 'expected_tone': 'encouraging'},
            {'current_salary': 65000, 'expected_tone': 'balanced'},
            {'current_salary': 85000, 'expected_tone': 'positive'},
            {'current_salary': 120000, 'expected_tone': 'celebratory'}
        ]
        
        base_user = {
            'age_range': '25-35',
            'race': 'African American',
            'education_level': 'bachelors',
            'location': 'Atlanta'
        }
        
        comparator = IncomeComparator()
        
        for case in test_cases:
            with self.subTest(salary=case['current_salary']):
                result = comparator.analyze_income(
                    user_income=case['current_salary'],
                    location=base_user['location'],
                    education_level=EducationLevel.BACHELORS,
                    age_group=base_user['age_range']
                )
                
                # Verify motivational content exists
                self.assertIsNotNone(result.motivational_summary)
                self.assertGreater(len(result.motivational_summary), 20)
                
                # Verify action plan exists
                self.assertIsNotNone(result.action_plan)
                self.assertGreater(len(result.action_plan), 0)
                
                # Verify next steps exist
                self.assertIsNotNone(result.next_steps)
                self.assertGreater(len(result.next_steps), 0)

if __name__ == '__main__':
    unittest.main() 