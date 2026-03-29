"""
Integration Tests for Assessment Flow

Tests include:
- End-to-end assessment flow
- Payment processing integration
- Email automation triggers
- Analytics event tracking
- API endpoint integration
- Database persistence
- Service orchestration
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
import json
import requests

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app import create_app
from backend.database import get_db_session, init_database_session_factory
from backend.models.user import User
from backend.models.assessment_models import Assessment
from backend.models.assessment_analytics_models import AssessmentAnalyticsEvent
from backend.models.payment import MINGUSPaymentIntent
from backend.services.assessment_scoring_service import AssessmentScoringService
from backend.services.ai_calculator_payment_service import AICalculatorPaymentService
from backend.services.email_automation_service import EmailAutomationService
from backend.services.ai_calculator_analytics_service import AICalculatorAnalyticsService

class TestAssessmentFlowIntegration(unittest.TestCase):
    """Integration test suite for assessment flow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Mock database session
        self.mock_session = Mock()
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None
        self.mock_session.add.return_value = None
        self.mock_session.commit.return_value = None
        self.mock_session.rollback.return_value = None
        self.mock_session.close.return_value = None
        
        # Patch database session
        self.db_patcher = patch('backend.database.get_db_session', return_value=self.mock_session)
        self.db_patcher.start()
        
        # Initialize services with mocked session
        self.scoring_service = AssessmentScoringService(self.mock_session, self.app.config)
        self.payment_service = AICalculatorPaymentService(self.app.config)
        self.email_service = EmailAutomationService(self.app.config)
        self.analytics_service = AICalculatorAnalyticsService(self.app.config)
        
        # Test data
        self.test_user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpassword123'
        }
        
        self.test_assessment_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'experience_level': 'mid',
            'company_size': 'large',
            'location': 'urban',
            'industry': 'technology',
            'skills': ['python', 'javascript', 'react'],
            'required_skills': ['python', 'javascript', 'react', 'node.js']
        }
        
        self.test_payment_data = {
            'amount': 29.99,
            'currency': 'usd',
            'payment_method': 'card',
            'card_token': 'tok_test_123'
        }
    
    def tearDown(self):
        """Clean up after tests"""
        self.db_patcher.stop()
        self.app_context.pop()
    
    def test_complete_assessment_flow(self):
        """Test complete assessment flow from start to finish"""
        # Step 1: User registration
        with patch('backend.services.email_automation_service.EmailAutomationService.send_welcome_email') as mock_welcome:
            mock_welcome.return_value = True
            
            response = self.client.post('/api/auth/register', 
                                      json=self.test_user_data)
            
            self.assertEqual(response.status_code, 201)
            user_data = response.get_json()
            user_id = user_data['user']['id']
            
            # Verify user was created
            user = User.query.get(user_id)
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'test@example.com')
            
            # Verify welcome email was sent
            mock_welcome.assert_called_once()
        
        # Step 2: User authentication
        auth_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        response = self.client.post('/api/auth/login', json=auth_data)
        self.assertEqual(response.status_code, 200)
        
        auth_response = response.get_json()
        access_token = auth_response['access_token']
        
        # Set up authenticated headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Step 3: Start assessment
        with patch('backend.services.ai_calculator_analytics_service.AICalculatorAnalyticsService.track_assessment_started') as mock_started:
            mock_started.return_value = True
            
            response = self.client.post('/api/assessments/start',
                                      json={'assessment_type': 'job_risk'},
                                      headers=headers)
            
            self.assertEqual(response.status_code, 201)
            assessment_data = response.get_json()
            assessment_id = assessment_data['assessment']['id']
            
            # Verify assessment was created
            assessment = Assessment.query.get(assessment_id)
            self.assertIsNotNone(assessment)
            self.assertEqual(assessment.status, 'in_progress')
            
            # Verify analytics event was tracked
            mock_started.assert_called_once()
        
        # Step 4: Submit assessment
        with patch('backend.services.assessment_scoring_service.AssessmentScoringService._calculate_ai_job_risk') as mock_calculate, \
             patch('backend.services.ai_calculator_analytics_service.AICalculatorAnalyticsService.track_assessment_completion') as mock_completion, \
             patch('backend.services.email_automation_service.EmailAutomationService.send_assessment_email') as mock_email:
            
            # Mock scoring calculation
            mock_calculate.return_value = Mock(
                overall_score=0.65,
                final_risk_level='medium',
                field_multiplier=1.2,
                confidence_interval=(0.60, 0.70),
                recommendations=['Learn AI skills', 'Network more'],
                risk_factors=['Automation risk', 'Skill gaps']
            )
            mock_completion.return_value = True
            mock_email.return_value = True
            
            response = self.client.post(f'/api/assessments/{assessment_id}/submit',
                                      json={'assessment_data': self.test_assessment_data},
                                      headers=headers)
            
            self.assertEqual(response.status_code, 200)
            result_data = response.get_json()
            
            # Verify assessment was completed
            assessment = Assessment.query.get(assessment_id)
            self.assertEqual(assessment.status, 'completed')
            self.assertIsNotNone(assessment.data)
            
            # Verify scoring was calculated
            mock_calculate.assert_called_once()
            
            # Verify analytics event was tracked
            mock_completion.assert_called_once()
            
            # Verify email was sent
            mock_email.assert_called_once()
            
            # Verify response contains expected data
            self.assertIn('overall_score', result_data['data'])
            self.assertIn('final_risk_level', result_data['data'])
            self.assertIn('recommendations', result_data['data'])
        
        # Step 5: Process payment
        with patch('stripe.PaymentIntent.create') as mock_stripe_create, \
             patch('backend.services.ai_calculator_analytics_service.AICalculatorAnalyticsService.track_payment_event') as mock_payment_track, \
             patch('backend.services.email_automation_service.EmailAutomationService.send_payment_confirmation') as mock_payment_email:
            
            # Mock Stripe payment
            mock_payment_intent = Mock(
                id='pi_test_123',
                status='succeeded',
                amount=2999,
                currency='usd'
            )
            mock_stripe_create.return_value = mock_payment_intent
            mock_payment_track.return_value = True
            mock_payment_email.return_value = True
            
            response = self.client.post('/api/payments/process',
                                      json=self.test_payment_data,
                                      headers=headers)
            
            self.assertEqual(response.status_code, 200)
            payment_data = response.get_json()
            
            # Verify payment was processed
            self.assertIn('transaction_id', payment_data['data'])
            self.assertEqual(payment_data['data']['status'], 'succeeded')
            
            # Verify payment was saved to database
            payment = MINGUSPaymentIntent.query.filter_by(transaction_id='pi_test_123').first()
            self.assertIsNotNone(payment)
            self.assertEqual(payment.amount, 29.99)
            
            # Verify analytics event was tracked
            mock_payment_track.assert_called_once()
            
            # Verify payment confirmation email was sent
            mock_payment_email.assert_called_once()
    
    def test_assessment_scoring_integration(self):
        """Test assessment scoring service integration"""
        # Create test user and assessment
        user = User(**self.test_user_data)
        self.mock_session.add(user)
        self.mock_session.commit()
        
        assessment = Assessment(
            user_id=user.id,
            assessment_type='job_risk',
            status='in_progress'
        )
        self.mock_session.add(assessment)
        self.mock_session.commit()
        
        # Test scoring calculation
        with patch('backend.services.assessment_scoring_service.AssessmentScoringService._calculate_ai_job_risk') as mock_calculate:
            mock_calculate.return_value = Mock(
                overall_score=0.75,
                final_risk_level='medium',
                field_multiplier=1.2,
                confidence_interval=(0.70, 0.80),
                recommendations=['Test recommendation'],
                risk_factors=['Test risk factor']
            )
            
            result = self.scoring_service.calculate_assessment_score(
                assessment.id,
                self.test_assessment_data
            )
            
            self.assertIsNotNone(result)
            self.assertEqual(result['overall_score'], 0.75)
            self.assertEqual(result['final_risk_level'], 'medium')
            
            # Verify assessment was updated
            assessment = Assessment.query.get(assessment.id)
            self.assertEqual(assessment.status, 'completed')
            self.assertIsNotNone(assessment.results)
    
    def test_payment_processing_integration(self):
        """Test payment processing service integration"""
        # Create test user
        user = User(**self.test_user_data)
        self.mock_session.add(user)
        self.mock_session.commit()
        
        # Test payment processing
        with patch('stripe.PaymentIntent.create') as mock_stripe_create, \
             patch('stripe.Customer.create') as mock_stripe_customer:
            
            # Mock Stripe responses
            mock_customer = Mock(
                id='cus_test_123',
                email='test@example.com'
            )
            mock_stripe_customer.return_value = mock_customer
            
            mock_payment_intent = Mock(
                id='pi_test_123',
                status='succeeded',
                amount=2999,
                currency='usd'
            )
            mock_stripe_create.return_value = mock_payment_intent
            
            result = self.payment_service.process_payment(
                user.id,
                self.test_payment_data
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['transaction_id'], 'pi_test_123')
            self.assertEqual(result['amount'], 29.99)
            
            # Verify payment was saved
            payment = MINGUSPaymentIntent.query.filter_by(transaction_id='pi_test_123').first()
            self.assertIsNotNone(payment)
            self.assertEqual(payment.user_id, user.id)
            self.assertEqual(payment.amount, 29.99)
    
    def test_email_automation_integration(self):
        """Test email automation service integration"""
        # Create test user and assessment
        user = User(**self.test_user_data)
        self.mock_session.add(user)
        self.mock_session.commit()
        
        assessment = Assessment(
            user_id=user.id,
            assessment_type='job_risk',
            status='completed',
            data=self.test_assessment_data,
            results={
                'overall_score': 0.75,
                'risk_level': 'medium',
                'recommendations': ['Test recommendation']
            }
        )
        self.mock_session.add(assessment)
        self.mock_session.commit()
        
        # Test email automation
        with patch('backend.services.email_automation_service.Mail') as mock_mail:
            mock_mail_instance = Mock()
            mock_mail.return_value = mock_mail_instance
            mock_mail_instance.send.return_value = True
            
            result = self.email_service.send_assessment_email(
                user.__dict__,
                assessment.__dict__
            )
            
            self.assertTrue(result)
            mock_mail_instance.send.assert_called_once()
    
    def test_analytics_tracking_integration(self):
        """Test analytics tracking service integration"""
        # Create test user and assessment
        user = User(**self.test_user_data)
        self.mock_session.add(user)
        self.mock_session.commit()
        
        assessment = Assessment(
            user_id=user.id,
            assessment_type='job_risk',
            status='completed'
        )
        self.mock_session.add(assessment)
        self.mock_session.commit()
        
        # Test analytics tracking
        event_data = {
            'completion_time': 120,
            'score': 0.75,
            'risk_level': 'medium'
        }
        
        result = self.analytics_service.track_assessment_completion(
            user.id,
            assessment.id,
            event_data
        )
        
        self.assertTrue(result)
        
        # Verify analytics event was saved
        analytics = AssessmentAnalyticsEvent.query.filter_by(
            user_id=user.id,
            assessment_id=assessment.id
        ).first()
        
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.event_type, 'assessment_completed')
        self.assertEqual(analytics.event_data['score'], 0.75)
    
    def test_api_error_handling(self):
        """Test API error handling"""
        # Test invalid assessment data
        response = self.client.post('/api/assessments/job-risk',
                                  json={'invalid': 'data'})
        
        self.assertEqual(response.status_code, 400)
        
        # Test invalid payment data
        response = self.client.post('/api/payments/process',
                                  json={'invalid': 'payment'})
        
        self.assertEqual(response.status_code, 400)
        
        # Test unauthorized access
        response = self.client.get('/api/assessments/history')
        self.assertEqual(response.status_code, 401)
    
    def test_database_transaction_rollback(self):
        """Test database transaction rollback on errors"""
        # Create test user
        user = User(**self.test_user_data)
        self.mock_session.add(user)
        self.mock_session.commit()
        
        # Test transaction rollback on payment failure
        with patch('stripe.PaymentIntent.create') as mock_stripe_create:
            mock_stripe_create.side_effect = Exception("Payment failed")
            
            try:
                self.payment_service.process_payment(
                    user.id,
                    self.test_payment_data
                )
            except Exception:
                pass
            
            # Verify no payment was saved
            payment = MINGUSPaymentIntent.query.filter_by(user_id=user.id).first()
            self.assertIsNone(payment)
    
    def test_concurrent_assessment_processing(self):
        """Test concurrent assessment processing"""
        import threading
        import queue
        
        # Create test user
        user = User(**self.test_user_data)
        self.mock_session.add(user)
        self.mock_session.commit()
        
        results = queue.Queue()
        
        def process_assessment(thread_id):
            try:
                assessment = Assessment(
                    user_id=user.id,
                    assessment_type='job_risk',
                    status='in_progress'
                )
                self.mock_session.add(assessment)
                self.mock_session.commit()
                
                with patch('backend.services.assessment_scoring_service.AssessmentScoringService._calculate_ai_job_risk') as mock_calculate:
                    mock_calculate.return_value = Mock(
                        overall_score=0.75,
                        final_risk_level='medium',
                        field_multiplier=1.2,
                        confidence_interval=(0.70, 0.80),
                        recommendations=['Test'],
                        risk_factors=['Test']
                    )
                    
                    result = self.scoring_service.calculate_assessment_score(
                        assessment.id,
                        self.test_assessment_data
                    )
                    
                    results.put((thread_id, True, result))
            except Exception as e:
                results.put((thread_id, False, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_assessment, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results.empty():
            thread_id, success, result = results.get()
            if success:
                success_count += 1
                self.assertIsNotNone(result)
        
        # All assessments should succeed
        self.assertEqual(success_count, 5)
    
    def test_assessment_data_persistence(self):
        """Test assessment data persistence and retrieval"""
        # Create test user
        user = User(**self.test_user_data)
        self.mock_session.add(user)
        self.mock_session.commit()
        
        # Create assessment with data
        assessment = Assessment(
            user_id=user.id,
            assessment_type='job_risk',
            status='completed',
            data=self.test_assessment_data,
            results={
                'overall_score': 0.75,
                'risk_level': 'medium',
                'recommendations': ['Test recommendation']
            }
        )
        self.mock_session.add(assessment)
        self.mock_session.commit()
        
        # Retrieve and verify data
        retrieved_assessment = Assessment.query.get(assessment.id)
        self.assertEqual(retrieved_assessment.data['current_salary'], 75000)
        self.assertEqual(retrieved_assessment.data['field'], 'software_development')
        self.assertEqual(retrieved_assessment.results['overall_score'], 0.75)
        self.assertEqual(retrieved_assessment.results['risk_level'], 'medium')
    
    def test_user_assessment_history(self):
        """Test user assessment history retrieval"""
        # Create test user
        user = User(**self.test_user_data)
        self.mock_session.add(user)
        self.mock_session.commit()
        
        # Create multiple assessments
        for i in range(3):
            assessment = Assessment(
                user_id=user.id,
                assessment_type='job_risk',
                status='completed',
                data=self.test_assessment_data,
                results={'overall_score': 0.7 + (i * 0.1)}
            )
            self.mock_session.add(assessment)
        
        self.mock_session.commit()
        
        # Retrieve assessment history
        history = Assessment.query.filter_by(user_id=user.id).all()
        self.assertEqual(len(history), 3)
        
        # Verify assessments are ordered by creation time
        for i in range(len(history) - 1):
            self.assertLessEqual(history[i].created_at, history[i + 1].created_at)

if __name__ == '__main__':
    unittest.main()
