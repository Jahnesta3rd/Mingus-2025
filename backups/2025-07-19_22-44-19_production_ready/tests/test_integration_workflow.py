"""
Integration Tests for Job Recommendation Engine Workflow
Tests complete user journeys, API endpoints, and system integration
"""

import unittest
import pytest
import time
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import Flask app and components
from backend.app import create_app
from backend.ml.models.mingus_job_recommendation_engine import MingusJobRecommendationEngine
from backend.services.intelligent_job_matching_service import IntelligentJobMatchingService
from backend.services.career_advancement_service import CareerAdvancementService
from backend.services.resume_analysis_service import ResumeAnalysisService


class TestIntegrationWorkflow(unittest.TestCase):
    """Integration tests for complete workflow scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Sample test data
        self.sample_resume = """
        SENIOR DATA ANALYST
        TechCorp Inc. | Atlanta, GA | 2020-2023
        - Led data analysis initiatives using Python, SQL, and Tableau
        - Managed team of 3 analysts and delivered insights to executive leadership
        - Increased revenue by 15% through predictive analytics implementation
        - Collaborated with cross-functional teams on data-driven decision making
        
        DATA ANALYST
        DataFlow Solutions | Atlanta, GA | 2018-2020
        - Performed statistical analysis and created automated reporting systems
        - Developed SQL queries and maintained data warehouse integrity
        - Created interactive dashboards using Power BI and Tableau
        - Supported marketing and sales teams with data insights
        
        EDUCATION
        Georgia Institute of Technology
        Bachelor of Science in Industrial Engineering
        GPA: 3.8/4.0
        
        SKILLS
        Technical: Python, SQL, R, Tableau, Power BI, Excel, Machine Learning
        Business: Project Management, Stakeholder Communication, Strategic Analysis
        Soft Skills: Leadership, Team Management, Problem Solving, Communication
        """
        
        # Mock authentication
        self.auth_headers = {
            'Authorization': 'Bearer test_token',
            'Content-Type': 'application/json'
        }

    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()

    def test_complete_user_journey(self):
        """Test complete user journey from resume upload to job recommendations"""
        # Step 1: Resume upload and analysis
        resume_data = {
            'resume_text': self.sample_resume,
            'current_salary': 75000,
            'target_locations': ['Atlanta', 'Houston'],
            'risk_preference': 'balanced'
        }
        
        response = self.client.post(
            '/api/job-recommendation/process-resume',
            json=resume_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        
        # Step 2: Verify profile analysis
        self.assertIn('user_profile', result['data'])
        profile = result['data']['user_profile']
        self.assertEqual(profile['field_expertise']['primary_field'], 'Data Analysis')
        self.assertEqual(profile['experience_level'], 'Senior')
        
        # Step 3: Verify financial analysis
        self.assertIn('financial_impact', result['data'])
        financial = result['data']['financial_impact']
        self.assertEqual(financial['current_salary'], 75000)
        self.assertGreater(financial['recommended_salary_ranges']['optimal']['target'], 75000)
        
        # Step 4: Verify career strategy
        self.assertIn('career_strategy', result['data'])
        strategy = result['data']['career_strategy']
        self.assertIn('conservative_opportunity', strategy)
        self.assertIn('optimal_opportunity', strategy)
        self.assertIn('stretch_opportunity', strategy)
        
        # Step 5: Verify action plan
        self.assertIn('action_plan', result['data'])
        action_plan = result['data']['action_plan']
        self.assertIn('immediate_actions', action_plan)
        self.assertIn('short_term_goals', action_plan)
        self.assertIn('long_term_strategy', action_plan)

    def test_api_endpoint_responses(self):
        """Test all API endpoints return appropriate responses"""
        endpoints = [
            {
                'url': '/api/job-recommendation/process-resume',
                'method': 'POST',
                'data': {
                    'resume_text': self.sample_resume,
                    'current_salary': 70000,
                    'target_locations': ['Atlanta']
                }
            },
            {
                'url': '/api/resume/analyze',
                'method': 'POST',
                'data': {
                    'resume_text': self.sample_resume
                }
            },
            {
                'url': '/api/job-matching/find-opportunities',
                'method': 'POST',
                'data': {
                    'user_id': 1,
                    'resume_text': self.sample_resume,
                    'current_salary': 70000,
                    'target_locations': ['Atlanta']
                }
            },
            {
                'url': '/api/career-advancement/strategy',
                'method': 'POST',
                'data': {
                    'user_id': 1,
                    'resume_text': self.sample_resume,
                    'target_locations': ['Atlanta'],
                    'risk_preference': 'balanced'
                }
            }
        ]
        
        for endpoint in endpoints:
            if endpoint['method'] == 'POST':
                response = self.client.post(
                    endpoint['url'],
                    json=endpoint['data'],
                    headers=self.auth_headers
                )
            else:
                response = self.client.get(
                    endpoint['url'],
                    headers=self.auth_headers
                )
            
            # Verify response structure
            self.assertIn(response.status_code, [200, 201, 400, 401, 500])
            
            if response.status_code in [200, 201]:
                result = json.loads(response.data)
                self.assertIn('success', result)
                self.assertIn('data', result)

    def test_session_management(self):
        """Test session management and progress tracking"""
        # Start a new session
        session_data = {
            'resume_text': self.sample_resume,
            'current_salary': 75000,
            'target_locations': ['Atlanta'],
            'risk_preference': 'balanced'
        }
        
        # Create session
        response = self.client.post(
            '/api/enhanced-job-recommendations/start-session',
            json=session_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        
        session_id = result['data']['session_id']
        progress_id = result['data']['progress_id']
        
        # Check progress
        response = self.client.get(
            f'/api/enhanced-job-recommendations/progress/{progress_id}',
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        progress = json.loads(response.data)
        self.assertIn('steps', progress['data'])
        
        # Wait for completion and get results
        max_wait = 30  # 30 seconds max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = self.client.get(
                f'/api/enhanced-job-recommendations/results/{session_id}',
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                result = json.loads(response.data)
                if result['success'] and result['data']['status'] == 'completed':
                    break
            
            time.sleep(1)
        
        # Verify final results
        self.assertEqual(response.status_code, 200)
        final_result = json.loads(response.data)
        self.assertTrue(final_result['success'])
        self.assertEqual(final_result['data']['status'], 'completed')
        self.assertIn('career_strategy', final_result['data'])

    def test_concurrent_user_requests(self):
        """Test system handles concurrent user requests"""
        def make_request(user_id):
            data = {
                'resume_text': self.sample_resume,
                'current_salary': 70000 + user_id * 1000,
                'target_locations': ['Atlanta'],
                'risk_preference': 'balanced'
            }
            
            response = self.client.post(
                '/api/job-recommendation/process-resume',
                json=data,
                headers=self.auth_headers
            )
            
            return {
                'user_id': user_id,
                'status_code': response.status_code,
                'success': response.status_code == 200
            }
        
        # Test concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # Verify all requests completed
        self.assertEqual(len(results), 10)
        
        # Verify success rate
        successful_requests = sum(1 for r in results if r['success'])
        success_rate = successful_requests / len(results)
        self.assertGreater(success_rate, 0.8)  # 80% success rate minimum

    def test_error_scenarios(self):
        """Test error handling in integration scenarios"""
        # Test invalid resume
        invalid_data = {
            'resume_text': 'Invalid resume',
            'current_salary': 50000
        }
        
        response = self.client.post(
            '/api/job-recommendation/process-resume',
            json=invalid_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.data)
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
        # Test missing authentication
        response = self.client.post(
            '/api/job-recommendation/process-resume',
            json={'resume_text': self.sample_resume, 'current_salary': 50000}
        )
        
        self.assertEqual(response.status_code, 401)
        
        # Test invalid salary
        invalid_salary_data = {
            'resume_text': self.sample_resume,
            'current_salary': -1000
        }
        
        response = self.client.post(
            '/api/job-recommendation/process-resume',
            json=invalid_salary_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.data)
        self.assertFalse(result['success'])

    def test_data_persistence(self):
        """Test data persistence across requests"""
        # First request
        data = {
            'resume_text': self.sample_resume,
            'current_salary': 75000,
            'target_locations': ['Atlanta'],
            'risk_preference': 'balanced'
        }
        
        response1 = self.client.post(
            '/api/job-recommendation/process-resume',
            json=data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response1.status_code, 200)
        result1 = json.loads(response1.data)
        user_id = result1['data']['user_profile']['user_id']
        
        # Second request with same user
        response2 = self.client.post(
            '/api/job-recommendation/process-resume',
            json=data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response2.status_code, 200)
        result2 = json.loads(response2.data)
        
        # Verify user consistency
        self.assertEqual(result2['data']['user_profile']['user_id'], user_id)
        
        # Verify cached results are faster
        self.assertLess(
            result2['processing_metrics']['total_processing_time'],
            result1['processing_metrics']['total_processing_time']
        )

    def test_performance_under_load(self):
        """Test performance under load"""
        start_time = time.time()
        
        # Make multiple requests
        responses = []
        for i in range(20):
            data = {
                'resume_text': self.sample_resume,
                'current_salary': 70000 + i * 1000,
                'target_locations': ['Atlanta'],
                'risk_preference': 'balanced'
            }
            
            response = self.client.post(
                '/api/job-recommendation/process-resume',
                json=data,
                headers=self.auth_headers
            )
            
            responses.append({
                'status_code': response.status_code,
                'response_time': time.time() - start_time
            })
        
        total_time = time.time() - start_time
        
        # Verify performance metrics
        successful_responses = [r for r in responses if r['status_code'] == 200]
        self.assertGreater(len(successful_responses), 15)  # 75% success rate
        
        # Average response time should be reasonable
        avg_response_time = total_time / len(responses)
        self.assertLess(avg_response_time, 5.0)  # Under 5 seconds average

    def test_service_integration(self):
        """Test integration between different services"""
        # Test resume analysis service integration
        with patch('backend.services.resume_analysis_service.Session') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            service = ResumeAnalysisService(mock_db)
            
            # Mock database response
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                id=1,
                current_salary=75000,
                preferred_locations=['Atlanta']
            )
            
            result = service.analyze_resume(
                user_id=1,
                resume_text=self.sample_resume
            )
            
            self.assertNotIn('error', result)
        
        # Test job matching service integration
        with patch('backend.services.intelligent_job_matching_service.Session') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            service = IntelligentJobMatchingService(mock_db)
            
            # Mock database response
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                id=1,
                current_salary=75000,
                preferred_locations=['Atlanta']
            )
            
            result = service.find_income_advancement_opportunities(
                user_id=1,
                resume_text=self.sample_resume,
                current_salary=75000,
                target_locations=['Atlanta']
            )
            
            self.assertNotIn('error', result)
        
        # Test career advancement service integration
        with patch('backend.services.career_advancement_service.Session') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            service = CareerAdvancementService(mock_db)
            
            # Mock database response
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                id=1,
                current_salary=75000,
                preferred_locations=['Atlanta']
            )
            
            result = service.generate_career_advancement_strategy(
                user_id=1,
                resume_text=self.sample_resume,
                target_locations=['Atlanta'],
                risk_preference='balanced'
            )
            
            self.assertNotIn('error', result)

    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        # Make rapid requests
        for i in range(10):
            data = {
                'resume_text': self.sample_resume,
                'current_salary': 70000,
                'target_locations': ['Atlanta']
            }
            
            response = self.client.post(
                '/api/job-recommendation/process-resume',
                json=data,
                headers=self.auth_headers
            )
            
            # Should not be rate limited for reasonable requests
            self.assertNotEqual(response.status_code, 429)
        
        # Test rate limiting on enhanced endpoint
        for i in range(10):
            data = {
                'resume_text': self.sample_resume,
                'current_salary': 70000,
                'target_locations': ['Atlanta']
            }
            
            response = self.client.post(
                '/api/enhanced-job-recommendations/start-session',
                json=data,
                headers=self.auth_headers
            )
            
            # Should not be rate limited for reasonable requests
            self.assertNotEqual(response.status_code, 429)

    def test_data_validation_integration(self):
        """Test data validation in integration context"""
        # Test various invalid inputs
        invalid_inputs = [
            {
                'resume_text': '',  # Empty resume
                'current_salary': 50000
            },
            {
                'resume_text': self.sample_resume,
                'current_salary': -1000  # Negative salary
            },
            {
                'resume_text': self.sample_resume,
                'current_salary': 50000,
                'risk_preference': 'invalid'  # Invalid risk preference
            },
            {
                'resume_text': self.sample_resume,
                'current_salary': 50000,
                'target_locations': ['Invalid City']  # Invalid location
            }
        ]
        
        for invalid_input in invalid_inputs:
            response = self.client.post(
                '/api/job-recommendation/process-resume',
                json=invalid_input,
                headers=self.auth_headers
            )
            
            # Should return validation error
            self.assertEqual(response.status_code, 400)
            result = json.loads(response.data)
            self.assertFalse(result['success'])
            self.assertIn('error', result)

    def test_monitoring_and_logging(self):
        """Test monitoring and logging in integration"""
        # Make a request and check for logging
        data = {
            'resume_text': self.sample_resume,
            'current_salary': 75000,
            'target_locations': ['Atlanta'],
            'risk_preference': 'balanced'
        }
        
        response = self.client.post(
            '/api/job-recommendation/process-resume',
            json=data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        
        # Verify monitoring data is included
        self.assertIn('processing_metrics', result)
        metrics = result['processing_metrics']
        
        self.assertGreater(metrics['total_processing_time'], 0)
        self.assertGreaterEqual(metrics['cache_hits'], 0)
        self.assertGreaterEqual(metrics['cache_misses'], 0)
        self.assertIsInstance(metrics['errors_encountered'], list)

    def test_user_journey_scenarios(self):
        """Test realistic user journey scenarios"""
        scenarios = [
            {
                'name': 'Entry Level Professional',
                'resume': """
                JUNIOR DATA ANALYST
                StartupCorp | Atlanta, GA | 2022-2023
                - Assisted with data analysis using Excel and basic SQL
                - Created reports and dashboards for team leads
                - Supported marketing campaigns with data insights
                
                EDUCATION
                Spelman College
                Bachelor of Science in Mathematics
                GPA: 3.6/4.0
                
                SKILLS
                Technical: Excel, SQL, Python (basic), Tableau
                Business: Data Analysis, Reporting, Communication
                """,
                'salary': 55000,
                'locations': ['Atlanta'],
                'risk_preference': 'conservative'
            },
            {
                'name': 'Mid-Level Professional',
                'resume': """
                SENIOR MARKETING SPECIALIST
                BrandCorp | Houston, TX | 2020-2023
                - Led digital marketing campaigns with $200K budget
                - Managed team of 2 specialists and achieved 20% growth
                - Developed customer acquisition strategies
                
                MARKETING COORDINATOR
                GrowthCorp | Houston, TX | 2018-2020
                - Executed social media campaigns and email marketing
                - Analyzed campaign performance and optimized ROI
                
                EDUCATION
                Texas Southern University
                Bachelor of Business Administration in Marketing
                GPA: 3.5/4.0
                
                SKILLS
                Technical: Google Analytics, Facebook Ads, Email Marketing, CRM
                Business: Campaign Management, Budget Management, Team Leadership
                """,
                'salary': 75000,
                'locations': ['Houston', 'Atlanta'],
                'risk_preference': 'balanced'
            }
        ]
        
        for scenario in scenarios:
            data = {
                'resume_text': scenario['resume'],
                'current_salary': scenario['salary'],
                'target_locations': scenario['locations'],
                'risk_preference': scenario['risk_preference']
            }
            
            response = self.client.post(
                '/api/job-recommendation/process-resume',
                json=data,
                headers=self.auth_headers
            )
            
            self.assertEqual(response.status_code, 200)
            result = json.loads(response.data)
            self.assertTrue(result['success'])
            
            # Verify scenario-specific expectations
            profile = result['data']['user_profile']
            strategy = result['data']['career_strategy']
            
            if scenario['name'] == 'Entry Level Professional':
                self.assertEqual(profile['experience_level'], 'Entry')
                # Conservative recommendations for entry level
                conservative = strategy['conservative_opportunity']
                salary_increase = conservative['income_impact']['salary_increase_percentage']
                self.assertLessEqual(salary_increase, 0.25)  # Max 25% for entry level
            
            elif scenario['name'] == 'Mid-Level Professional':
                self.assertEqual(profile['field_expertise']['primary_field'], 'Marketing')
                # Balanced recommendations for mid level
                optimal = strategy['optimal_opportunity']
                salary_increase = optimal['income_impact']['salary_increase_percentage']
                self.assertGreaterEqual(salary_increase, 0.20)  # Min 20% for mid level


if __name__ == '__main__':
    unittest.main() 