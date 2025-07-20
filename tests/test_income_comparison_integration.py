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
from backend.data.income_data_manager import IncomeDataManager
from backend.ml.models.income_comparator import IncomeComparator

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
                'income': 65000,
                'age': 28,
                'race': 'african_american',
                'education': 'bachelors',
                'location': 'Atlanta'
            },
            'mid_career_african_american_manager': {
                'income': 85000,
                'age': 38,
                'race': 'african_american',
                'education': 'masters',
                'location': 'Washington DC'
            },
            'entry_level_african_american_worker': {
                'income': 45000,
                'age': 25,
                'race': 'african_american',
                'education': 'high_school',
                'location': 'Houston'
            },
            'senior_african_american_executive': {
                'income': 120000,
                'age': 42,
                'race': 'african_american',
                'education': 'masters',
                'location': 'New York City'
            },
            'white_professional_comparison': {
                'income': 75000,
                'age': 30,
                'race': 'white',
                'education': 'bachelors',
                'location': 'Chicago'
            },
            'hispanic_professional_comparison': {
                'income': 60000,
                'age': 32,
                'race': 'hispanic_latino',
                'education': 'bachelors',
                'location': 'Miami'
            }
        }
    
    def test_form_submission_workflow(self):
        """Test complete form submission workflow"""
        user = self.test_users['young_african_american_professional']
        
        # Test form submission
        form_data = {
            'income': user['income'],
            'age': user['age'],
            'race': user['race'],
            'education': user['education'],
            'location': user['location']
        }
        
        response = self.client.post('/api/income-analysis/analyze', 
                                  data=json.dumps(form_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('comparison_results', data)
        self.assertIn('summary', data)
        self.assertIn('recommendations', data)
    
    def test_demographic_analysis_accuracy(self):
        """Test demographic analysis accuracy across different profiles"""
        for profile_name, user in self.test_users.items():
            with self.subTest(profile=profile_name):
                # Create comparison
                comparator = IncomeComparator(IncomeDataManager())
                result = comparator.comprehensive_comparison(
                    user['income'], user['race'], user['age'],
                    user['education'], user['location']
                )
                
                # Verify all comparison types are present
                self.assertIn('national', result)
                self.assertIn('age_group', result)
                self.assertIn('education_level', result)
                self.assertIn('location', result)
                
                # Verify data quality
                for comparison_type, comparison in result.items():
                    if comparison_type != 'summary':
                        self.assertGreater(comparison['median_income'], 0)
                        self.assertGreaterEqual(comparison['percentile_rank'], 1)
                        self.assertLessEqual(comparison['percentile_rank'], 100)
    
    def test_geographic_variations(self):
        """Test geographic variations across target metro areas"""
        metro_areas = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City',
                      'Philadelphia', 'Chicago', 'Charlotte', 'Miami', 'Baltimore']
        
        base_user = {
            'income': 65000,
            'age': 30,
            'race': 'african_american',
            'education': 'bachelors'
        }
        
        comparator = IncomeComparator(IncomeDataManager())
        
        for metro in metro_areas:
            with self.subTest(metro=metro):
                result = comparator.compare_income_by_location(
                    base_user['income'], base_user['race'], metro
                )
                
                self.assertIsNotNone(result)
                self.assertGreater(result['median_income'], 0)
                self.assertEqual(result['location'], metro)
                
                # Verify percentile is reasonable
                self.assertGreaterEqual(result['percentile_rank'], 1)
                self.assertLessEqual(result['percentile_rank'], 100)
    
    def test_education_level_impact(self):
        """Test education level impact on income comparisons"""
        education_levels = ['high_school', 'bachelors', 'masters']
        
        base_user = {
            'income': 65000,
            'age': 30,
            'race': 'african_american'
        }
        
        comparator = IncomeComparator(IncomeDataManager())
        
        for education in education_levels:
            with self.subTest(education=education):
                result = comparator.compare_income_by_education(
                    base_user['income'], base_user['race'], education
                )
                
                self.assertIsNotNone(result)
                self.assertGreater(result['median_income'], 0)
                self.assertEqual(result['education_level'], education)
                
                # Verify education impact on percentile
                self.assertGreaterEqual(result['percentile_rank'], 1)
                self.assertLessEqual(result['percentile_rank'], 100)
    
    def test_age_group_transitions(self):
        """Test age group transitions and income expectations"""
        age_groups = [
            {'age': 25, 'expected_group': '25-34'},
            {'age': 30, 'expected_group': '25-34'},
            {'age': 35, 'expected_group': '35-44'},
            {'age': 40, 'expected_group': '35-44'}
        ]
        
        base_user = {
            'income': 65000,
            'race': 'african_american',
            'education': 'bachelors'
        }
        
        comparator = IncomeComparator(IncomeDataManager())
        
        for age_data in age_groups:
            with self.subTest(age=age_data['age']):
                result = comparator.compare_income_by_age(
                    base_user['income'], base_user['race'], age_data['age']
                )
                
                self.assertIsNotNone(result)
                self.assertEqual(result['age_group'], age_data['expected_group'])
                self.assertGreater(result['median_income'], 0)
    
    def test_api_integration_failure_scenarios(self):
        """Test API integration failure scenarios"""
        # Mock API failure
        with patch('backend.data.income_data_manager.IncomeDataManager._get_api_data') as mock_api:
            mock_api.return_value = None
            
            user = self.test_users['young_african_american_professional']
            comparator = IncomeComparator(IncomeDataManager())
            
            # Should fall back to fallback data
            result = comparator.comprehensive_comparison(
                user['income'], user['race'], user['age'],
                user['education'], user['location']
            )
            
            self.assertIsNotNone(result)
            self.assertIn('national', result)
            self.assertIn('age_group', result)
            self.assertIn('education_level', result)
            self.assertIn('location', result)
    
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
                    user = {'income': 60000, 'race': 'invalid_race', 'age': 30, 
                           'education': 'bachelors', 'location': 'invalid_location'}
                
                # Test form rendering
                response = self.client.get('/api/income-analysis/form')
                self.assertEqual(response.status_code, 200)
                
                # Test results rendering
                if scenario != 'missing_data_graceful_handling':
                    form_data = {
                        'income': user['income'],
                        'age': user['age'],
                        'race': user['race'],
                        'education': user['education'],
                        'location': user['location']
                    }
                    
                    response = self.client.post('/api/income-analysis/analyze',
                                              data=json.dumps(form_data),
                                              content_type='application/json')
                    self.assertEqual(response.status_code, 200)
    
    def test_performance_comparison_calculations(self):
        """Test performance of comparison calculations"""
        import time
        
        user = self.test_users['young_african_american_professional']
        comparator = IncomeComparator(IncomeDataManager())
        
        # Test single comparison performance
        start_time = time.time()
        result = comparator.comprehensive_comparison(
            user['income'], user['race'], user['age'],
            user['education'], user['location']
        )
        single_time = time.time() - start_time
        
        # Should complete within reasonable time (100ms)
        self.assertLess(single_time, 0.1)
        
        # Test multiple comparisons performance
        start_time = time.time()
        for _ in range(10):
            comparator.comprehensive_comparison(
                user['income'], user['race'], user['age'],
                user['education'], user['location']
            )
        multiple_time = time.time() - start_time
        
        # Should handle multiple requests efficiently
        self.assertLess(multiple_time, 1.0)
    
    def test_error_handling_edge_cases(self):
        """Test error handling for edge cases"""
        edge_cases = [
            {'income': -1000, 'race': 'african_american', 'age': 30, 'education': 'bachelors', 'location': 'Atlanta'},
            {'income': 0, 'race': 'african_american', 'age': 30, 'education': 'bachelors', 'location': 'Atlanta'},
            {'income': 1000000, 'race': 'african_american', 'age': 30, 'education': 'bachelors', 'location': 'Atlanta'},
            {'income': 60000, 'race': 'invalid_race', 'age': 30, 'education': 'bachelors', 'location': 'Atlanta'},
            {'income': 60000, 'race': 'african_american', 'age': 15, 'education': 'bachelors', 'location': 'Atlanta'},
            {'income': 60000, 'race': 'african_american', 'age': 30, 'education': 'invalid_education', 'location': 'Atlanta'},
            {'income': 60000, 'race': 'african_american', 'age': 30, 'education': 'bachelors', 'location': 'invalid_location'},
        ]
        
        comparator = IncomeComparator(IncomeDataManager())
        
        for i, edge_case in enumerate(edge_cases):
            with self.subTest(edge_case=i):
                try:
                    result = comparator.comprehensive_comparison(
                        edge_case['income'], edge_case['race'], edge_case['age'],
                        edge_case['education'], edge_case['location']
                    )
                    
                    # Should handle gracefully and return some result
                    self.assertIsNotNone(result)
                    self.assertIn('national', result)
                    
                except Exception as e:
                    # Should not crash, but may log errors
                    self.fail(f"Edge case {i} caused unexpected exception: {str(e)}")
    
    def test_motivational_messaging_appropriateness(self):
        """Test that motivational messaging is appropriate for different income levels"""
        test_cases = [
            {'income': 45000, 'expected_tone': 'encouraging'},
            {'income': 65000, 'expected_tone': 'balanced'},
            {'income': 85000, 'expected_tone': 'positive'},
            {'income': 120000, 'expected_tone': 'celebratory'}
        ]
        
        base_user = {
            'race': 'african_american',
            'age': 30,
            'education': 'bachelors',
            'location': 'Atlanta'
        }
        
        comparator = IncomeComparator(IncomeDataManager())
        
        for test_case in test_cases:
            with self.subTest(income=test_case['income']):
                result = comparator.comprehensive_comparison(
                    test_case['income'], base_user['race'], base_user['age'],
                    base_user['education'], base_user['location']
                )
                
                # Verify summary contains appropriate messaging
                self.assertIn('summary', result)
                summary = result['summary']
                
                # Should not be discouraging
                self.assertNotIn('failure', summary.lower())
                self.assertNotIn('hopeless', summary.lower())
                self.assertNotIn('impossible', summary.lower())
                
                # Should be encouraging
                encouraging_words = ['opportunity', 'potential', 'growth', 'advancement', 'improvement']
                has_encouraging_content = any(word in summary.lower() for word in encouraging_words)
                self.assertTrue(has_encouraging_content, f"Summary should contain encouraging content: {summary}")

if __name__ == '__main__':
    unittest.main() 