"""
Test suite for Enhanced Income Comparison Calculator
Tests API integration, ML predictions, lead capture flow, and cultural content
"""

import pytest
import requests
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache

from backend.models import (
    SalaryBenchmark, PredictionCache, LeadEngagementScore,
    SalaryPrediction, CareerPathRecommendation, LeadCaptureEvent,
    GamificationBadge, UserBadge, EmailSequence, EmailSend
)
from backend.services.salary_prediction_service import SalaryPredictionService
from backend.services.lead_scoring_service import LeadScoringService
from backend.services.cultural_content_service import CulturalContentService
from backend.services.api_integration_service import (
    BLSAPIService, CensusAPIService, FREDAPIService, BEAAPIService
)


class TestIncomeComparison(TestCase):
    """Comprehensive test suite for income comparison calculator"""

    def setUp(self):
        """Set up test data and mock services"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test data
        self.sample_salary_data = {
            'current_salary': 75000,
            'location': 'atlanta',
            'industry': 'technology',
            'experience_level': 'mid',
            'education_level': 'bachelor',
            'skills': ['Leadership', 'Data Analysis'],
            'target_salary': 100000
        }
        
        # Mock external services
        self.mock_bls_service = Mock()
        self.mock_census_service = Mock()
        self.mock_fred_service = Mock()
        self.mock_bea_service = Mock()

    def tearDown(self):
        """Clean up after tests"""
        cache.clear()
        super().tearDown()

    # =============================================================================
    # API INTEGRATION TESTS
    # =============================================================================

    def test_bls_api_integration(self):
        """Test Bureau of Labor Statistics API integration"""
        with patch('backend.services.api_integration_service.BLSAPIService') as mock_bls:
            # Mock successful API response
            mock_bls.return_value.get_salary_data.return_value = {
                'status': 'success',
                'data': {
                    'atlanta': {
                        'technology': {
                            'mid': {
                                'mean_salary': 85000,
                                'percentile_25': 70000,
                                'percentile_75': 110000,
                                'sample_size': 1250
                            }
                        }
                    }
                }
            }
            
            service = BLSAPIService()
            result = service.get_salary_data('atlanta', 'technology', 'mid')
            
            self.assertEqual(result['status'], 'success')
            self.assertIn('atlanta', result['data'])
            self.assertIn('technology', result['data']['atlanta'])
            
            # Test error handling
            mock_bls.return_value.get_salary_data.side_effect = requests.RequestException("API Error")
            with self.assertRaises(requests.RequestException):
                service.get_salary_data('invalid_location', 'invalid_industry', 'invalid_level')

    def test_census_api_integration(self):
        """Test US Census Bureau API integration"""
        with patch('backend.services.api_integration_service.CensusAPIService') as mock_census:
            # Mock demographic data response
            mock_census.return_value.get_demographic_data.return_value = {
                'status': 'success',
                'data': {
                    'atlanta': {
                        'african_american_population': 450000,
                        'median_household_income': 65000,
                        'education_attainment': {
                            'bachelor_degree': 0.35,
                            'graduate_degree': 0.15
                        }
                    }
                }
            }
            
            service = CensusAPIService()
            result = service.get_demographic_data('atlanta')
            
            self.assertEqual(result['status'], 'success')
            self.assertIn('atlanta', result['data'])
            self.assertIn('african_american_population', result['data']['atlanta'])

    def test_fred_api_integration(self):
        """Test Federal Reserve Economic Data API integration"""
        with patch('backend.services.api_integration_service.FREDAPIService') as mock_fred:
            # Mock economic indicators response
            mock_fred.return_value.get_economic_indicators.return_value = {
                'status': 'success',
                'data': {
                    'inflation_rate': 2.5,
                    'unemployment_rate': 3.8,
                    'gdp_growth': 2.1,
                    'wage_growth': 3.2
                }
            }
            
            service = FREDAPIService()
            result = service.get_economic_indicators()
            
            self.assertEqual(result['status'], 'success')
            self.assertIn('inflation_rate', result['data'])
            self.assertIn('wage_growth', result['data'])

    def test_bea_api_integration(self):
        """Test Bureau of Economic Analysis API integration"""
        with patch('backend.services.api_integration_service.BEAAPIService') as mock_bea:
            # Mock regional economic data response
            mock_bea.return_value.get_regional_data.return_value = {
                'status': 'success',
                'data': {
                    'atlanta': {
                        'gdp_per_capita': 65000,
                        'employment_growth': 2.5,
                        'industry_mix': {
                            'technology': 0.25,
                            'healthcare': 0.20,
                            'finance': 0.15
                        }
                    }
                }
            }
            
            service = BEAAPIService()
            result = service.get_regional_data('atlanta')
            
            self.assertEqual(result['status'], 'success')
            self.assertIn('atlanta', result['data'])
            self.assertIn('gdp_per_capita', result['data']['atlanta'])

    def test_api_rate_limiting(self):
        """Test API rate limiting and error handling"""
        with patch('requests.get') as mock_get:
            # Mock rate limit response
            mock_get.return_value.status_code = 429
            mock_get.return_value.json.return_value = {
                'error': 'Rate limit exceeded',
                'retry_after': 60
            }
            
            service = BLSAPIService()
            
            # Test rate limit handling
            with self.assertRaises(Exception):
                service.get_salary_data('atlanta', 'technology', 'mid')

    # =============================================================================
    # ML PREDICTIONS TESTS
    # =============================================================================

    def test_salary_prediction_accuracy(self):
        """Test ML prediction accuracy and validation"""
        prediction_service = SalaryPredictionService()
        
        # Test prediction with valid data
        prediction = prediction_service.predict_salary(self.sample_salary_data)
        
        self.assertIsNotNone(prediction)
        self.assertIn('predicted_salary_1yr', prediction)
        self.assertIn('predicted_salary_3yr', prediction)
        self.assertIn('predicted_salary_5yr', prediction)
        self.assertIn('confidence_score', prediction)
        self.assertIn('percentile_rank', prediction)
        
        # Validate prediction ranges
        self.assertGreater(prediction['predicted_salary_1yr'], 0)
        self.assertGreater(prediction['predicted_salary_3yr'], prediction['predicted_salary_1yr'])
        self.assertGreater(prediction['predicted_salary_5yr'], prediction['predicted_salary_3yr'])
        self.assertGreaterEqual(prediction['confidence_score'], 0.0)
        self.assertLessEqual(prediction['confidence_score'], 1.0)
        self.assertGreaterEqual(prediction['percentile_rank'], 1)
        self.assertLessEqual(prediction['percentile_rank'], 100)

    def test_prediction_cache_functionality(self):
        """Test prediction caching and retrieval"""
        prediction_service = SalaryPredictionService()
        
        # Generate prediction
        prediction1 = prediction_service.predict_salary(self.sample_salary_data)
        
        # Generate same prediction again (should use cache)
        prediction2 = prediction_service.predict_salary(self.sample_salary_data)
        
        # Predictions should be identical
        self.assertEqual(prediction1['predicted_salary_1yr'], prediction2['predicted_salary_1yr'])
        self.assertEqual(prediction1['confidence_score'], prediction2['confidence_score'])
        
        # Test cache expiration
        cache_key = prediction_service._generate_cache_key(self.sample_salary_data)
        cache.delete(cache_key)
        
        # Should generate new prediction
        prediction3 = prediction_service.predict_salary(self.sample_salary_data)
        self.assertNotEqual(prediction1['predicted_salary_1yr'], prediction3['predicted_salary_1yr'])

    def test_career_path_recommendations(self):
        """Test career path recommendation generation"""
        prediction_service = SalaryPredictionService()
        
        # Generate career path recommendations
        recommendations = prediction_service.generate_career_paths(self.sample_salary_data)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        for recommendation in recommendations:
            self.assertIn('path_name', recommendation)
            self.assertIn('estimated_timeline_months', recommendation)
            self.assertIn('required_investment', recommendation)
            self.assertIn('projected_return', recommendation)
            self.assertIn('roi_percentage', recommendation)
            self.assertIn('risk_level', recommendation)
            
            # Validate recommendation data
            self.assertGreater(recommendation['estimated_timeline_months'], 0)
            self.assertGreaterEqual(recommendation['required_investment'], 0)
            self.assertGreater(recommendation['projected_return'], 0)
            self.assertGreater(recommendation['roi_percentage'], 0)
            self.assertIn(recommendation['risk_level'], ['low', 'medium', 'high'])

    def test_prediction_confidence_threshold(self):
        """Test prediction confidence threshold validation"""
        prediction_service = SalaryPredictionService()
        
        # Test with low confidence data
        low_confidence_data = {
            'current_salary': 75000,
            'location': 'unknown_location',
            'industry': 'unknown_industry',
            'experience_level': 'unknown',
            'education_level': 'unknown',
            'skills': []
        }
        
        prediction = prediction_service.predict_salary(low_confidence_data)
        
        # Should have lower confidence score
        self.assertLess(prediction['confidence_score'], 0.7)
        
        # Test with high confidence data
        high_confidence_data = {
            'current_salary': 75000,
            'location': 'atlanta',
            'industry': 'technology',
            'experience_level': 'mid',
            'education_level': 'bachelor',
            'skills': ['Leadership', 'Data Analysis', 'Project Management']
        }
        
        prediction = prediction_service.predict_salary(high_confidence_data)
        
        # Should have higher confidence score
        self.assertGreater(prediction['confidence_score'], 0.7)

    # =============================================================================
    # LEAD CAPTURE FLOW TESTS
    # =============================================================================

    def test_progressive_lead_capture_flow(self):
        """Test end-to-end progressive lead capture flow"""
        # Step 1: Basic info collection
        basic_info_data = {
            'email': 'test@example.com',
            'current_salary': 75000,
            'location': 'atlanta',
            'firstName': 'John',
            'lastName': 'Doe'
        }
        
        response = self.client.post(reverse('api:lead-capture-basic'), basic_info_data)
        self.assertEqual(response.status_code, 200)
        
        session_id = response.json()['session_id']
        
        # Step 2: Detailed profile collection
        detailed_profile_data = {
            'session_id': session_id,
            'industry': 'technology',
            'role': 'Software Engineer',
            'education': 'bachelor',
            'yearsOfExperience': 5,
            'companySize': '201-500'
        }
        
        response = self.client.post(reverse('api:lead-capture-detailed'), detailed_profile_data)
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Career goals collection
        career_goals_data = {
            'session_id': session_id,
            'targetSalary': 100000,
            'careerGoals': ['Increase salary by 20%+', 'Move into leadership role'],
            'skills': ['Leadership', 'Data Analysis'],
            'preferredLocation': 'atlanta'
        }
        
        response = self.client.post(reverse('api:lead-capture-goals'), career_goals_data)
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Preferences collection
        preferences_data = {
            'session_id': session_id,
            'contactMethod': 'email',
            'urgency': 'medium',
            'newsletter': True
        }
        
        response = self.client.post(reverse('api:lead-capture-preferences'), preferences_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify lead was created
        lead = LeadEngagementScore.objects.filter(email='test@example.com').first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.engagement_score, 1.0)  # Complete flow
        self.assertEqual(lead.lead_stage, 'qualified')

    def test_lead_scoring_algorithm(self):
        """Test lead scoring algorithm accuracy"""
        scoring_service = LeadScoringService()
        
        # Test high-value lead
        high_value_lead_data = {
            'email': 'highvalue@example.com',
            'current_salary': 120000,
            'target_salary': 150000,
            'industry': 'technology',
            'location': 'san-francisco',
            'education': 'master',
            'skills': ['Leadership', 'Strategic Planning', 'Data Analysis'],
            'urgency': 'high',
            'interaction_count': 10
        }
        
        score = scoring_service.calculate_lead_score(high_value_lead_data)
        self.assertGreater(score, 0.8)  # High-value lead should score > 80%
        
        # Test low-value lead
        low_value_lead_data = {
            'email': 'lowvalue@example.com',
            'current_salary': 30000,
            'target_salary': 35000,
            'industry': 'retail',
            'location': 'small-town',
            'education': 'high-school',
            'skills': [],
            'urgency': 'low',
            'interaction_count': 1
        }
        
        score = scoring_service.calculate_lead_score(low_value_lead_data)
        self.assertLess(score, 0.5)  # Low-value lead should score < 50%

    def test_gamification_badge_unlocking(self):
        """Test gamification badge unlocking system"""
        # Create test badges
        badge1 = GamificationBadge.objects.create(
            badge_name='Getting Started',
            badge_description='Completed first step',
            badge_icon='🚀',
            badge_color='#3B82F6',
            unlock_criteria={'step_completed': 1}
        )
        
        badge2 = GamificationBadge.objects.create(
            badge_name='Salary Insight',
            badge_description='Unlocked detailed analysis',
            badge_icon='💰',
            badge_color='#10B981',
            unlock_criteria={'step_completed': 2}
        )
        
        # Test badge unlocking
        session_id = 'test-session-123'
        
        # Complete step 1
        UserBadge.objects.create(
            session_id=session_id,
            badge=badge1,
            unlocked_at=datetime.now(),
            unlock_context={'step_completed': 1}
        )
        
        # Complete step 2
        UserBadge.objects.create(
            session_id=session_id,
            badge=badge2,
            unlocked_at=datetime.now(),
            unlock_context={'step_completed': 2}
        )
        
        # Verify badges were unlocked
        user_badges = UserBadge.objects.filter(session_id=session_id)
        self.assertEqual(user_badges.count(), 2)
        
        badge_names = [ub.badge.badge_name for ub in user_badges]
        self.assertIn('Getting Started', badge_names)
        self.assertIn('Salary Insight', badge_names)

    def test_email_sequence_triggering(self):
        """Test email sequence automation"""
        # Create email sequence
        sequence = EmailSequence.objects.create(
            sequence_name='Welcome Series',
            sequence_description='Welcome new leads',
            trigger_event='lead_captured',
            delay_hours=0,
            email_template='welcome_email'
        )
        
        # Create lead
        lead = LeadEngagementScore.objects.create(
            email='test@example.com',
            engagement_score=1.0,
            conversion_probability=0.8,
            lead_stage='qualified'
        )
        
        # Trigger email sequence
        email_send = EmailSend.objects.create(
            lead=lead,
            sequence=sequence,
            email_address='test@example.com',
            email_subject='Welcome to Mingus',
            email_content='Welcome to our platform!',
            scheduled_at=datetime.now(),
            status='scheduled'
        )
        
        # Verify email was scheduled
        self.assertEqual(email_send.status, 'scheduled')
        self.assertEqual(email_send.lead.email, 'test@example.com')

    # =============================================================================
    # CULTURAL CONTENT TESTS
    # =============================================================================

    def test_cultural_content_generation(self):
        """Test culturally-aware content generation"""
        content_service = CulturalContentService()
        
        # Test African American demographic content
        content = content_service.generate_cultural_content(
            location='atlanta',
            industry='technology',
            demographic='african_american'
        )
        
        self.assertIsNotNone(content)
        self.assertIn('salary_gap_analysis', content)
        self.assertIn('representation_premium', content)
        self.assertIn('community_context', content)
        self.assertIn('systemic_barriers', content)
        
        # Validate content relevance
        self.assertIn('Atlanta', content['community_context'])
        self.assertIn('technology', content['salary_gap_analysis'])
        self.assertIn('African American', content['representation_premium'])

    def test_salary_gap_analysis(self):
        """Test salary gap analysis for different demographics"""
        content_service = CulturalContentService()
        
        # Test salary gap calculation
        gap_analysis = content_service.analyze_salary_gaps(
            location='atlanta',
            industry='technology',
            experience_level='mid'
        )
        
        self.assertIn('overall_gap', gap_analysis)
        self.assertIn('demographic_gaps', gap_analysis)
        self.assertIn('african_american_gap', gap_analysis['demographic_gaps'])
        self.assertIn('recommendations', gap_analysis)
        
        # Validate gap analysis data
        self.assertIsInstance(gap_analysis['overall_gap'], (int, float))
        self.assertIsInstance(gap_analysis['demographic_gaps']['african_american_gap'], (int, float))

    def test_representation_premium_calculation(self):
        """Test representation premium calculation"""
        content_service = CulturalContentService()
        
        # Test representation premium
        premium_data = content_service.calculate_representation_premium(
            location='atlanta',
            industry='technology'
        )
        
        self.assertIn('leadership_premium', premium_data)
        self.assertIn('diversity_bonus', premium_data)
        self.assertIn('company_benefits', premium_data)
        
        # Validate premium calculations
        self.assertGreaterEqual(premium_data['leadership_premium'], 0)
        self.assertGreaterEqual(premium_data['diversity_bonus'], 0)

    def test_community_wealth_building_context(self):
        """Test community wealth building context generation"""
        content_service = CulturalContentService()
        
        # Test community context
        community_context = content_service.generate_community_context(
            location='atlanta',
            demographic='african_american'
        )
        
        self.assertIn('historical_context', community_context)
        self.assertIn('economic_opportunities', community_context)
        self.assertIn('networking_opportunities', community_context)
        self.assertIn('success_stories', community_context)
        
        # Validate context relevance
        self.assertIn('Atlanta', community_context['historical_context'])
        self.assertIn('African American', community_context['economic_opportunities'])

    def test_culturally_aware_recommendations(self):
        """Test culturally-aware career recommendations"""
        content_service = CulturalContentService()
        
        # Test recommendations
        recommendations = content_service.generate_cultural_recommendations(
            location='atlanta',
            industry='technology',
            experience_level='mid',
            demographic='african_american'
        )
        
        self.assertIn('skill_recommendations', recommendations)
        self.assertIn('networking_recommendations', recommendations)
        self.assertIn('mentorship_opportunities', recommendations)
        self.assertIn('community_resources', recommendations)
        
        # Validate recommendation relevance
        self.assertGreater(len(recommendations['skill_recommendations']), 0)
        self.assertGreater(len(recommendations['networking_recommendations']), 0)

    # =============================================================================
    # INTEGRATION TESTS
    # =============================================================================

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # 1. User starts lead capture
        response = self.client.post(reverse('api:lead-capture-start'), {
            'email': 'test@example.com',
            'current_salary': 75000,
            'location': 'atlanta'
        })
        self.assertEqual(response.status_code, 200)
        
        session_id = response.json()['session_id']
        
        # 2. Complete progressive disclosure
        steps = [
            ('basic', {'firstName': 'John', 'lastName': 'Doe'}),
            ('detailed', {'industry': 'technology', 'role': 'Engineer'}),
            ('goals', {'targetSalary': 100000, 'careerGoals': ['Leadership']}),
            ('preferences', {'contactMethod': 'email', 'urgency': 'medium'})
        ]
        
        for step_name, step_data in steps:
            step_data['session_id'] = session_id
            response = self.client.post(
                reverse(f'api:lead-capture-{step_name}'),
                step_data
            )
            self.assertEqual(response.status_code, 200)
        
        # 3. Generate salary prediction
        prediction_response = self.client.post(reverse('api:salary-predict'), {
            'session_id': session_id,
            'current_salary': 75000,
            'location': 'atlanta',
            'industry': 'technology'
        })
        self.assertEqual(prediction_response.status_code, 200)
        
        # 4. Generate cultural content
        cultural_response = self.client.post(reverse('api:cultural-content'), {
            'session_id': session_id,
            'location': 'atlanta',
            'industry': 'technology'
        })
        self.assertEqual(cultural_response.status_code, 200)
        
        # 5. Verify lead was created and scored
        lead = LeadEngagementScore.objects.filter(email='test@example.com').first()
        self.assertIsNotNone(lead)
        self.assertGreater(lead.engagement_score, 0.8)
        self.assertEqual(lead.lead_stage, 'qualified')

    def test_performance_under_load(self):
        """Test system performance under load"""
        import time
        
        # Test concurrent API requests
        start_time = time.time()
        
        # Simulate 10 concurrent users
        responses = []
        for i in range(10):
            response = self.client.post(reverse('api:salary-predict'), {
                'current_salary': 75000 + (i * 1000),
                'location': 'atlanta',
                'industry': 'technology',
                'experience_level': 'mid'
            })
            responses.append(response)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)
        
        # Performance should be reasonable (under 5 seconds for 10 requests)
        self.assertLess(total_time, 5.0)

    def test_error_handling_and_recovery(self):
        """Test error handling and system recovery"""
        # Test with invalid data
        response = self.client.post(reverse('api:salary-predict'), {
            'current_salary': 'invalid',
            'location': 'invalid_location',
            'industry': 'invalid_industry'
        })
        
        # Should return error but not crash
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        
        # Test with missing required fields
        response = self.client.post(reverse('api:salary-predict'), {})
        self.assertEqual(response.status_code, 400)
        
        # Test system recovery after errors
        response = self.client.post(reverse('api:salary-predict'), {
            'current_salary': 75000,
            'location': 'atlanta',
            'industry': 'technology'
        })
        self.assertEqual(response.status_code, 200)


class TestIncomeComparisonAPIs(TestCase):
    """Test API endpoints for income comparison calculator"""

    def setUp(self):
        self.client = Client()
        self.api_base = '/api/v1/income-comparison/'

    def test_salary_benchmark_endpoint(self):
        """Test salary benchmark API endpoint"""
        response = self.client.get(f'{self.api_base}benchmark/', {
            'location': 'atlanta',
            'industry': 'technology',
            'experience_level': 'mid'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('benchmark_data', data)
        self.assertIn('percentile_rank', data)
        self.assertIn('confidence_interval', data)

    def test_salary_prediction_endpoint(self):
        """Test salary prediction API endpoint"""
        response = self.client.post(f'{self.api_base}predict/', {
            'current_salary': 75000,
            'location': 'atlanta',
            'industry': 'technology',
            'experience_level': 'mid',
            'education_level': 'bachelor'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('predictions', data)
        self.assertIn('career_paths', data)
        self.assertIn('confidence_score', data)

    def test_lead_capture_endpoint(self):
        """Test lead capture API endpoint"""
        response = self.client.post(f'{self.api_base}lead-capture/', {
            'email': 'test@example.com',
            'current_salary': 75000,
            'location': 'atlanta',
            'step': 'basic'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('session_id', data)
        self.assertIn('next_step', data)
        self.assertIn('progress', data)

    def test_cultural_content_endpoint(self):
        """Test cultural content API endpoint"""
        response = self.client.get(f'{self.api_base}cultural-content/', {
            'location': 'atlanta',
            'industry': 'technology',
            'demographic': 'african_american'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('salary_gap_analysis', data)
        self.assertIn('representation_premium', data)
        self.assertIn('community_context', data)


if __name__ == '__main__':
    pytest.main([__file__]) 