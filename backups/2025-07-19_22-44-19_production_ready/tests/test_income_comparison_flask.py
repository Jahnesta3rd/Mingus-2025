"""
Flask Integration Tests for Income Comparison Feature
Tests complete web application workflow and API endpoints
"""

import unittest
import sys
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from flask import Flask
from backend.routes.income_analysis import income_analysis_bp
from backend.data.income_data_manager import IncomeDataManager

class TestIncomeComparisonFlask(unittest.TestCase):
    """Flask integration tests for income comparison feature"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.app = Flask(__name__)
        self.app.register_blueprint(income_analysis_bp, url_prefix='/api/income-analysis')
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Sample user profiles for testing
        self.test_users = {
            'young_professional': {
                'income': 65000,
                'age': 28,
                'race': 'african_american',
                'education': 'bachelors',
                'location': 'Atlanta'
            },
            'mid_career_manager': {
                'income': 85000,
                'age': 38,
                'race': 'african_american',
                'education': 'masters',
                'location': 'Washington DC'
            },
            'entry_level_worker': {
                'income': 45000,
                'age': 25,
                'race': 'african_american',
                'education': 'high_school',
                'location': 'Houston'
            },
            'senior_executive': {
                'income': 120000,
                'age': 42,
                'race': 'african_american',
                'education': 'masters',
                'location': 'New York City'
            }
        }
    
    def test_form_endpoint_availability(self):
        """Test that form endpoint is available and returns HTML"""
        response = self.client.get('/api/income-analysis/form')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.content_type)
        
        # Should contain form elements
        html_content = response.data.decode('utf-8')
        self.assertIn('income_analysis_form', html_content)
        self.assertIn('salary', html_content)
        self.assertIn('age', html_content)
        self.assertIn('race', html_content)
        self.assertIn('education', html_content)
        self.assertIn('location', html_content)
    
    def test_results_endpoint_availability(self):
        """Test that results endpoint is available"""
        response = self.client.get('/api/income-analysis/results')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.content_type)
        
        # Should contain results template
        html_content = response.data.decode('utf-8')
        self.assertIn('income_analysis_results', html_content)
    
    def test_dashboard_endpoint_availability(self):
        """Test that dashboard endpoint is available"""
        response = self.client.get('/api/income-analysis/dashboard')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.content_type)
        
        # Should contain dashboard template
        html_content = response.data.decode('utf-8')
        self.assertIn('comprehensive_career_dashboard', html_content)
    
    def test_analyze_endpoint_functionality(self):
        """Test analyze endpoint with valid data"""
        user = self.test_users['young_professional']
        
        response = self.client.post('/api/income-analysis/analyze',
                                  data=json.dumps(user),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response.content_type)
        
        data = json.loads(response.data)
        self.assertIn('comparison_results', data)
        self.assertIn('summary', data)
        self.assertIn('recommendations', data)
        self.assertIn('success', data)
        
        # Verify comparison results structure
        comparison_results = data['comparison_results']
        self.assertIn('national', comparison_results)
        self.assertIn('age_group', comparison_results)
        self.assertIn('education_level', comparison_results)
        self.assertIn('location', comparison_results)
        
        # Verify data quality
        for comparison_type, comparison in comparison_results.items():
            self.assertIn('median_income', comparison)
            self.assertIn('percentile_rank', comparison)
            self.assertIn('income_gap', comparison)
            self.assertGreater(comparison['median_income'], 0)
            self.assertGreaterEqual(comparison['percentile_rank'], 1)
            self.assertLessEqual(comparison['percentile_rank'], 100)
    
    def test_analyze_endpoint_invalid_data(self):
        """Test analyze endpoint with invalid data"""
        invalid_data_cases = [
            {},  # Empty data
            {'income': 'invalid'},  # Invalid income
            {'income': -1000},  # Negative income
            {'income': 60000, 'race': 'invalid_race'},  # Invalid race
            {'income': 60000, 'age': 'invalid_age'},  # Invalid age
            {'income': 60000, 'education': 'invalid_education'},  # Invalid education
            {'income': 60000, 'location': 'invalid_location'},  # Invalid location
        ]
        
        for i, invalid_data in enumerate(invalid_data_cases):
            with self.subTest(invalid_case=i):
                response = self.client.post('/api/income-analysis/analyze',
                                          data=json.dumps(invalid_data),
                                          content_type='application/json')
                
                # Should handle gracefully (not crash)
                self.assertIn(response.status_code, [200, 400, 422])
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    self.assertIn('success', data)
                    # Should return some result even with invalid data
                    if 'comparison_results' in data:
                        self.assertIsNotNone(data['comparison_results'])
    
    def test_demo_endpoint_functionality(self):
        """Test demo endpoint returns sample data"""
        response = self.client.get('/api/income-analysis/demo')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response.content_type)
        
        data = json.loads(response.data)
        self.assertIn('comparison_results', data)
        self.assertIn('summary', data)
        self.assertIn('recommendations', data)
        
        # Verify demo data structure
        comparison_results = data['comparison_results']
        self.assertIn('national', comparison_results)
        self.assertIn('age_group', comparison_results)
        self.assertIn('education_level', comparison_results)
        self.assertIn('location', comparison_results)
    
    def test_health_endpoint_functionality(self):
        """Test health endpoint returns service status"""
        response = self.client.get('/api/income-analysis/health')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response.content_type)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('service', data)
        
        self.assertEqual(data['service'], 'income_analysis')
        self.assertEqual(data['status'], 'healthy')
    
    def test_complete_user_journey(self):
        """Test complete user journey from form to results"""
        user = self.test_users['mid_career_manager']
        
        # Step 1: Access form
        response = self.client.get('/api/income-analysis/form')
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Submit form data
        response = self.client.post('/api/income-analysis/analyze',
                                  data=json.dumps(user),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Step 3: Access results
        response = self.client.get('/api/income-analysis/results')
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Access dashboard
        response = self.client.get('/api/income-analysis/dashboard')
        self.assertEqual(response.status_code, 200)
    
    def test_multiple_user_scenarios(self):
        """Test multiple user scenarios"""
        for profile_name, user in self.test_users.items():
            with self.subTest(profile=profile_name):
                response = self.client.post('/api/income-analysis/analyze',
                                          data=json.dumps(user),
                                          content_type='application/json')
                
                self.assertEqual(response.status_code, 200)
                
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                
                # Verify comparison results
                comparison_results = data['comparison_results']
                self.assertIn('national', comparison_results)
                self.assertIn('age_group', comparison_results)
                self.assertIn('education_level', comparison_results)
                self.assertIn('location', comparison_results)
                
                # Verify data quality
                for comparison_type, comparison in comparison_results.items():
                    self.assertGreater(comparison['median_income'], 0)
                    self.assertGreaterEqual(comparison['percentile_rank'], 1)
                    self.assertLessEqual(comparison['percentile_rank'], 100)
    
    def test_error_handling_scenarios(self):
        """Test error handling scenarios"""
        error_scenarios = [
            # Missing required fields
            {'income': 60000},
            {'race': 'african_american'},
            
            # Invalid data types
            {'income': 'not_a_number', 'race': 'african_american', 'age': 30},
            {'income': 60000, 'race': 'african_american', 'age': 'not_a_number'},
            
            # Out of range values
            {'income': -1000, 'race': 'african_american', 'age': 30},
            {'income': 60000, 'race': 'african_american', 'age': 150},
            
            # Invalid combinations
            {'income': 60000, 'race': 'african_american', 'age': 15, 'education': 'masters'},
        ]
        
        for i, error_data in enumerate(error_scenarios):
            with self.subTest(error_scenario=i):
                response = self.client.post('/api/income-analysis/analyze',
                                          data=json.dumps(error_data),
                                          content_type='application/json')
                
                # Should not crash
                self.assertIn(response.status_code, [200, 400, 422])
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    # Should handle gracefully and return some result
                    self.assertIsNotNone(data)
    
    def test_performance_under_load(self):
        """Test performance under load"""
        user = self.test_users['young_professional']
        
        # Test multiple concurrent requests
        start_time = time.time()
        
        responses = []
        for _ in range(10):
            response = self.client.post('/api/income-analysis/analyze',
                                      data=json.dumps(user),
                                      content_type='application/json')
            responses.append(response)
        
        total_time = time.time() - start_time
        avg_time = total_time / 10
        
        # Should handle load efficiently
        self.assertLess(avg_time, 0.1, f"Average response time: {avg_time:.3f}s")
        
        # All responses should be successful
        for i, response in enumerate(responses):
            self.assertEqual(response.status_code, 200, f"Response {i} failed")
            
            data = json.loads(response.data)
            self.assertTrue(data['success'], f"Response {i} not successful")
    
    def test_template_rendering_quality(self):
        """Test template rendering quality"""
        # Test form template
        response = self.client.get('/api/income-analysis/form')
        html_content = response.data.decode('utf-8')
        
        # Should contain professional elements
        self.assertIn('Bootstrap', html_content)  # Professional styling
        self.assertIn('Font Awesome', html_content)  # Icons
        self.assertIn('income analysis', html_content.lower())  # Content
        
        # Test results template
        response = self.client.get('/api/income-analysis/results')
        html_content = response.data.decode('utf-8')
        
        # Should contain results elements
        self.assertIn('comparison', html_content.lower())
        self.assertIn('percentile', html_content.lower())
        self.assertIn('income gap', html_content.lower())
        
        # Test dashboard template
        response = self.client.get('/api/income-analysis/dashboard')
        html_content = response.data.decode('utf-8')
        
        # Should contain dashboard elements
        self.assertIn('dashboard', html_content.lower())
        self.assertIn('career', html_content.lower())
        self.assertIn('job matches', html_content.lower())
    
    def test_api_response_format(self):
        """Test API response format consistency"""
        user = self.test_users['senior_executive']
        
        response = self.client.post('/api/income-analysis/analyze',
                                  data=json.dumps(user),
                                  content_type='application/json')
        
        data = json.loads(response.data)
        
        # Verify response structure
        required_fields = ['success', 'comparison_results', 'summary', 'recommendations']
        for field in required_fields:
            self.assertIn(field, data)
        
        # Verify comparison results structure
        comparison_results = data['comparison_results']
        required_comparisons = ['national', 'age_group', 'education_level', 'location']
        for comparison in required_comparisons:
            self.assertIn(comparison, comparison_results)
            
            comparison_data = comparison_results[comparison]
            required_comparison_fields = ['median_income', 'percentile_rank', 'income_gap', 'income_gap_percentage']
            for field in required_comparison_fields:
                self.assertIn(field, comparison_data)
        
        # Verify data types
        self.assertIsInstance(data['success'], bool)
        self.assertIsInstance(data['summary'], str)
        self.assertIsInstance(data['recommendations'], list)
        
        for comparison in comparison_results.values():
            self.assertIsInstance(comparison['median_income'], (int, float))
            self.assertIsInstance(comparison['percentile_rank'], (int, float))
            self.assertIsInstance(comparison['income_gap'], (int, float))
            self.assertIsInstance(comparison['income_gap_percentage'], (int, float))
    
    def test_motivational_messaging_consistency(self):
        """Test that motivational messaging is consistent and appropriate"""
        for profile_name, user in self.test_users.items():
            with self.subTest(profile=profile_name):
                response = self.client.post('/api/income-analysis/analyze',
                                          data=json.dumps(user),
                                          content_type='application/json')
                
                data = json.loads(response.data)
                summary = data['summary']
                recommendations = data['recommendations']
                
                # Summary should be encouraging
                discouraging_words = ['failure', 'hopeless', 'impossible', 'never', 'can\'t']
                for word in discouraging_words:
                    self.assertNotIn(word, summary.lower(), 
                                   f"Summary contains discouraging word '{word}' for {profile_name}")
                
                # Should contain encouraging content
                encouraging_words = ['opportunity', 'potential', 'growth', 'advancement', 'improvement']
                has_encouraging_content = any(word in summary.lower() for word in encouraging_words)
                self.assertTrue(has_encouraging_content, 
                              f"Summary should contain encouraging content for {profile_name}")
                
                # Recommendations should be actionable
                self.assertIsInstance(recommendations, list)
                self.assertGreater(len(recommendations), 0)
                
                for recommendation in recommendations:
                    self.assertIsInstance(recommendation, str)
                    self.assertGreater(len(recommendation), 10)
    
    def test_data_accuracy_across_endpoints(self):
        """Test data accuracy across different endpoints"""
        user = self.test_users['young_professional']
        
        # Test analyze endpoint
        response = self.client.post('/api/income-analysis/analyze',
                                  data=json.dumps(user),
                                  content_type='application/json')
        
        analyze_data = json.loads(response.data)
        
        # Test demo endpoint
        response = self.client.get('/api/income-analysis/demo')
        demo_data = json.loads(response.data)
        
        # Both should have same structure
        for endpoint_data in [analyze_data, demo_data]:
            self.assertIn('comparison_results', endpoint_data)
            self.assertIn('summary', endpoint_data)
            self.assertIn('recommendations', endpoint_data)
            
            comparison_results = endpoint_data['comparison_results']
            for comparison_type in ['national', 'age_group', 'education_level', 'location']:
                self.assertIn(comparison_type, comparison_results)
                
                comparison = comparison_results[comparison_type]
                self.assertIn('median_income', comparison)
                self.assertIn('percentile_rank', comparison)
                self.assertIn('income_gap', comparison)
                self.assertIn('income_gap_percentage', comparison)
                
                # Verify data quality
                self.assertGreater(comparison['median_income'], 0)
                self.assertGreaterEqual(comparison['percentile_rank'], 1)
                self.assertLessEqual(comparison['percentile_rank'], 100)

if __name__ == '__main__':
    unittest.main() 