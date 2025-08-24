"""
End-to-end tests for user workflows
Tests complete user journeys from registration to job security insights
"""

import unittest
import json
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Import Flask test client
from backend.app_factory import create_app
from backend.models.user import User
from backend.services.user_service import UserService
from backend.services.onboarding_service import OnboardingService


class TestUserWorkflows(unittest.TestCase):
    """Test complete user workflows"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        # Create test database
        with self.app.app_context():
            from backend.models.base import Base
            from backend.app_factory import engine
            Base.metadata.create_all(engine)
            
            # Initialize services
            self.user_service = UserService()
            self.onboarding_service = OnboardingService()
    
    def tearDown(self):
        """Clean up test fixtures"""
        with self.app.app_context():
            from backend.models.base import Base
            from backend.app_factory import engine
            Base.metadata.drop_all(engine)
    
    def test_complete_user_registration_workflow(self):
        """Test complete user registration workflow"""
        # Step 1: User visits registration page
        response = self.client.get('/api/auth/register')
        self.assertEqual(response.status_code, 200)
        
        # Step 2: User submits registration form
        registration_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '1234567890'
        }
        
        response = self.client.post('/api/auth/register',
                                  data=json.dumps(registration_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 3: User is redirected to onboarding
        response = self.client.get('/api/health/onboarding')
        self.assertEqual(response.status_code, 200)
    
    def test_job_security_onboarding_workflow(self):
        """Test job security onboarding workflow"""
        # First register and login user
        self._register_and_login_user()
        
        # Step 1: User starts job security onboarding
        response = self.client.get('/api/job-security/onboarding')
        self.assertEqual(response.status_code, 200)
        
        # Step 2: User provides employment information
        employment_data = {
            'current_company': 'TechCorp',
            'industry': 'technology',
            'job_title': 'Software Engineer',
            'years_experience': 5,
            'current_salary': 80000,
            'tenure_months': 24,
            'department': 'engineering',
            'role_level': 'senior'
        }
        
        response = self.client.post('/api/job-security/employment-info',
                                  data=json.dumps(employment_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 3: User provides skills information
        skills_data = {
            'technical_skills': ['python', 'javascript', 'react'],
            'soft_skills': ['leadership', 'communication'],
            'certifications': ['AWS', 'PMP'],
            'languages': ['English', 'Spanish'],
            'willingness_to_relocate': True,
            'remote_work_preference': True
        }
        
        response = self.client.post('/api/job-security/skills-info',
                                  data=json.dumps(skills_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 4: User provides financial information
        financial_data = {
            'current_savings': 15000,
            'monthly_expenses': 4000,
            'debt_payments': 800,
            'emergency_fund': 8000,
            'investment_assets': 25000,
            'insurance_coverage': {
                'health': True,
                'disability': False,
                'life': False
            }
        }
        
        response = self.client.post('/api/job-security/financial-info',
                                  data=json.dumps(financial_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 5: User completes onboarding
        response = self.client.post('/api/job-security/complete-onboarding')
        self.assertEqual(response.status_code, 200)
        
        # Step 6: Verify onboarding completion
        response = self.client.get('/api/job-security/onboarding-status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['completed'])
    
    def test_job_security_dashboard_workflow(self):
        """Test job security dashboard workflow"""
        # Setup user with complete profile
        user_id = self._setup_complete_user_profile()
        
        # Step 1: User accesses dashboard
        response = self.client.get('/api/job-security/dashboard')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('risk_assessment', data)
        self.assertIn('recommendations', data)
        self.assertIn('financial_plan', data)
        self.assertIn('goals', data)
        
        # Step 2: User views detailed risk assessment
        response = self.client.get('/api/job-security/risk-assessment')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('overall_risk_score', data)
        self.assertIn('risk_level', data)
        self.assertIn('risk_factors', data)
        self.assertIn('confidence', data)
        
        # Step 3: User views personalized recommendations
        response = self.client.get('/api/job-security/recommendations')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('skills_recommendations', data)
        self.assertIn('networking_recommendations', data)
        self.assertIn('financial_recommendations', data)
        self.assertIn('career_recommendations', data)
        
        # Step 4: User views financial planning
        response = self.client.get('/api/job-security/financial-plan')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('emergency_fund', data)
        self.assertIn('investment_strategy', data)
        self.assertIn('insurance_recommendations', data)
    
    def test_goal_setting_workflow(self):
        """Test goal setting workflow"""
        # Setup user with complete profile
        user_id = self._setup_complete_user_profile()
        
        # Step 1: User views current goals
        response = self.client.get('/api/job-security/goals')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('current_goals', data)
        self.assertIn('recommended_goals', data)
        
        # Step 2: User creates new goal
        goal_data = {
            'type': 'skill_development',
            'name': 'Learn Machine Learning',
            'description': 'Complete ML certification to improve job security',
            'target_amount': 2000,
            'timeline_months': 6,
            'priority': 'high'
        }
        
        response = self.client.post('/api/job-security/goals',
                                  data=json.dumps(goal_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 3: User updates goal progress
        progress_data = {
            'goal_id': 1,
            'progress_percentage': 25,
            'notes': 'Completed first course module'
        }
        
        response = self.client.put('/api/job-security/goals/1/progress',
                                 data=json.dumps(progress_data),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 4: User views goal progress
        response = self.client.get('/api/job-security/goals/1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['progress_percentage'], 25)
    
    def test_notification_workflow(self):
        """Test notification workflow"""
        # Setup user with complete profile
        user_id = self._setup_complete_user_profile()
        
        # Step 1: User sets notification preferences
        notification_prefs = {
            'risk_alerts': True,
            'recommendation_updates': True,
            'goal_reminders': True,
            'market_updates': False,
            'frequency': 'weekly'
        }
        
        response = self.client.post('/api/job-security/notifications/preferences',
                                  data=json.dumps(notification_prefs),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 2: User views notifications
        response = self.client.get('/api/job-security/notifications')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('notifications', data)
        
        # Step 3: User marks notification as read
        response = self.client.put('/api/job-security/notifications/1/read')
        self.assertEqual(response.status_code, 200)
    
    def test_career_transition_workflow(self):
        """Test career transition planning workflow"""
        # Setup user with complete profile
        user_id = self._setup_complete_user_profile()
        
        # Step 1: User starts career transition planning
        response = self.client.get('/api/job-security/career-transition')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('transition_timeline', data)
        self.assertIn('target_industries', data)
        self.assertIn('skill_gaps', data)
        
        # Step 2: User explores target industries
        response = self.client.get('/api/job-security/career-transition/industries')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('industries', data)
        
        # Step 3: User creates transition plan
        transition_plan = {
            'target_industry': 'healthcare',
            'target_role': 'Healthcare Data Analyst',
            'timeline_months': 12,
            'required_skills': ['healthcare_analytics', 'sql', 'python'],
            'estimated_cost': 5000,
            'action_items': [
                'Complete healthcare analytics certification',
                'Network with healthcare professionals',
                'Build healthcare data portfolio'
            ]
        }
        
        response = self.client.post('/api/job-security/career-transition/plan',
                                  data=json.dumps(transition_plan),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Step 4: User tracks transition progress
        response = self.client.get('/api/job-security/career-transition/progress')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('plan', data)
        self.assertIn('progress', data)
    
    def test_data_export_workflow(self):
        """Test data export workflow"""
        # Setup user with complete profile
        user_id = self._setup_complete_user_profile()
        
        # Step 1: User requests data export
        export_request = {
            'format': 'pdf',
            'include_sections': ['risk_assessment', 'recommendations', 'financial_plan']
        }
        
        response = self.client.post('/api/job-security/export',
                                  data=json.dumps(export_request),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('export_id', data)
        self.assertIn('status', data)
        
        # Step 2: User checks export status
        export_id = data['export_id']
        response = self.client.get(f'/api/job-security/export/{export_id}')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('download_url', data)
    
    def test_accessibility_workflow(self):
        """Test accessibility features"""
        # Setup user with complete profile
        user_id = self._setup_complete_user_profile()
        
        # Step 1: Test keyboard navigation
        response = self.client.get('/api/job-security/dashboard')
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Test screen reader compatibility
        response = self.client.get('/api/job-security/dashboard?accessibility=screen_reader')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('aria_labels', data)
        self.assertIn('alt_text', data)
        
        # Step 3: Test high contrast mode
        response = self.client.get('/api/job-security/dashboard?theme=high_contrast')
        self.assertEqual(response.status_code, 200)
    
    def _register_and_login_user(self):
        """Helper method to register and login a user"""
        # Register user
        registration_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '1234567890'
        }
        
        self.client.post('/api/auth/register',
                        data=json.dumps(registration_data),
                        content_type='application/json')
        
        # Login user
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post('/api/auth/login',
                                  data=json.dumps(login_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Store session
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_email'] = 'test@example.com'
    
    def _setup_complete_user_profile(self):
        """Helper method to setup a user with complete profile"""
        # Register and login user
        self._register_and_login_user()
        
        # Complete job security onboarding
        employment_data = {
            'current_company': 'TechCorp',
            'industry': 'technology',
            'job_title': 'Software Engineer',
            'years_experience': 5,
            'current_salary': 80000,
            'tenure_months': 24
        }
        
        self.client.post('/api/job-security/employment-info',
                        data=json.dumps(employment_data),
                        content_type='application/json')
        
        skills_data = {
            'technical_skills': ['python', 'javascript'],
            'soft_skills': ['leadership', 'communication']
        }
        
        self.client.post('/api/job-security/skills-info',
                        data=json.dumps(skills_data),
                        content_type='application/json')
        
        financial_data = {
            'current_savings': 15000,
            'monthly_expenses': 4000
        }
        
        self.client.post('/api/job-security/financial-info',
                        data=json.dumps(financial_data),
                        content_type='application/json')
        
        self.client.post('/api/job-security/complete-onboarding')
        
        return 1  # Return user ID


if __name__ == '__main__':
    unittest.main() 