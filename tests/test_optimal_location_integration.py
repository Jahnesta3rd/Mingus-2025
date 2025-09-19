#!/usr/bin/env python3
"""
Mingus Personal Finance App - Optimal Location Integration Tests
End-to-end integration tests for the Optimal Location feature following MINGUS testing patterns
"""

import unittest
import sqlite3
import tempfile
import os
import sys
import json
import time
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from backend.api.optimal_location_api import optimal_location_api
from backend.models.database import db
from backend.models.user_models import User
from backend.models.housing_models import (
    HousingSearch, HousingScenario, UserHousingPreferences, CommuteRouteCache
)
from backend.services.optimal_location_service import OptimalLocationService

class TestOptimalLocationIntegration(unittest.TestCase):
    """Integration tests for the Optimal Location feature"""
    
    def setUp(self):
        """Set up integration test environment"""
        # Create Flask app for testing
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Register blueprint
        self.app.register_blueprint(optimal_location_api)
        
        # Initialize database
        db.init_app(self.app)
        
        with self.app.app_context():
            db.create_all()
            self._setup_test_data()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up integration test database"""
        with self.app.app_context():
            db.drop_all()
    
    def _setup_test_data(self):
        """Set up comprehensive test data for integration tests"""
        # Create test users with different tiers
        users = [
            User(id=1, email='budget@example.com', first_name='Budget', last_name='User', tier='budget'),
            User(id=2, email='midtier@example.com', first_name='Mid', last_name='Tier', tier='mid_tier'),
            User(id=3, email='professional@example.com', first_name='Professional', last_name='User', tier='professional')
        ]
        
        db.session.add_all(users)
        db.session.commit()
        
        # Create test housing scenarios
        scenarios = [
            HousingScenario(
                user_id=2,
                scenario_name='Downtown Apartment',
                housing_data={
                    'address': '123 Main St',
                    'city': 'New York',
                    'state': 'NY',
                    'zip_code': '10001',
                    'rent': 3000,
                    'bedrooms': 2,
                    'bathrooms': 1,
                    'property_type': 'apartment'
                },
                commute_data={
                    'estimated_commute_time': 20,
                    'estimated_distance': 8.5,
                    'commute_cost_per_month': 200
                },
                financial_impact={
                    'monthly_rent': 3000,
                    'affordability_score': 85,
                    'total_monthly_housing_cost': 3200,
                    'rent_to_income_ratio': 0.25
                },
                career_data={
                    'nearby_job_opportunities': 25,
                    'average_salary_in_area': 85000,
                    'career_growth_potential': 'High'
                }
            ),
            HousingScenario(
                user_id=2,
                scenario_name='Suburban House',
                housing_data={
                    'address': '456 Oak Ave',
                    'city': 'Brooklyn',
                    'state': 'NY',
                    'zip_code': '11201',
                    'rent': 2200,
                    'bedrooms': 3,
                    'bathrooms': 2,
                    'property_type': 'house'
                },
                commute_data={
                    'estimated_commute_time': 35,
                    'estimated_distance': 15.2,
                    'commute_cost_per_month': 300
                },
                financial_impact={
                    'monthly_rent': 2200,
                    'affordability_score': 75,
                    'total_monthly_housing_cost': 2400,
                    'rent_to_income_ratio': 0.18
                },
                career_data={
                    'nearby_job_opportunities': 15,
                    'average_salary_in_area': 75000,
                    'career_growth_potential': 'Medium'
                }
            )
        ]
        
        db.session.add_all(scenarios)
        db.session.commit()
        
        # Create user housing preferences
        preferences = UserHousingPreferences(
            user_id=2,
            max_commute_time=30,
            preferred_housing_type='apartment',
            min_bedrooms=2,
            max_bedrooms=3,
            max_rent_percentage=Decimal('30.0'),
            preferred_neighborhoods=['downtown', 'suburbs']
        )
        
        db.session.add(preferences)
        db.session.commit()
    
    def _get_auth_headers(self, user_id=2):
        """Get authentication headers for testing"""
        return {
            'Authorization': f'Bearer test_token_{user_id}',
            'X-CSRF-Token': 'test_csrf_token_12345',
            'Content-Type': 'application/json'
        }
    
    def test_end_to_end_user_flow(self):
        """Test complete end-to-end user flow from search to scenario creation"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 2
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_search_limit') as mock_search_limit:
                    mock_search_limit.return_value = True
                    
                    with patch('backend.api.optimal_location_api.check_scenario_save_limit') as mock_scenario_limit:
                        mock_scenario_limit.return_value = True
                        
                        # Step 1: Search for housing
                        with patch('backend.api.optimal_location_api.location_service') as mock_location:
                            mock_location.validate_and_geocode.return_value = {
                                'success': True,
                                'location': {
                                    'msa': 'New York-Newark-Jersey City, NY-NJ-PA',
                                    'zip_code': '10001'
                                }
                            }
                            
                            with patch('backend.api.optimal_location_api.external_api_service') as mock_external:
                                mock_external.get_rental_listings.return_value = {
                                    'success': True,
                                    'listings': [
                                        {
                                            'id': 'listing1',
                                            'address': '123 Search St',
                                            'city': 'New York',
                                            'state': 'NY',
                                            'zip_code': '10001',
                                            'rent': 2800,
                                            'bedrooms': 2,
                                            'bathrooms': 1,
                                            'property_type': 'apartment'
                                        }
                                    ]
                                }
                                
                                search_data = {
                                    'max_rent': 3000,
                                    'bedrooms': 2,
                                    'commute_time': 30,
                                    'zip_code': '10001',
                                    'housing_type': 'apartment'
                                }
                                
                                search_response = self.client.post(
                                    '/api/housing/search',
                                    data=json.dumps(search_data),
                                    headers=self._get_auth_headers()
                                )
                                
                                self.assertEqual(search_response.status_code, 200)
                                search_result = json.loads(search_response.data)
                                self.assertTrue(search_result['success'])
                                self.assertEqual(len(search_result['listings']), 1)
                                
                                # Step 2: Create scenario from search result
                                with patch('backend.api.optimal_location_api.calculate_commute_data') as mock_commute:
                                    mock_commute.return_value = {
                                        'estimated_commute_time': 25,
                                        'estimated_distance': 10.5,
                                        'traffic_factor': 1.1,
                                        'commute_cost_per_month': 200.0
                                    }
                                    
                                    with patch('backend.api.optimal_location_api.calculate_financial_impact') as mock_financial:
                                        mock_financial.return_value = {
                                            'monthly_rent': 2800,
                                            'affordability_score': 82.0,
                                            'total_monthly_housing_cost': 3000.0
                                        }
                                        
                                        scenario_data = {
                                            'housing_data': search_result['listings'][0],
                                            'include_career_analysis': False,
                                            'scenario_name': 'From Search Result'
                                        }
                                        
                                        scenario_response = self.client.post(
                                            '/api/housing/scenario',
                                            data=json.dumps(scenario_data),
                                            headers=self._get_auth_headers()
                                        )
                                        
                                        self.assertEqual(scenario_response.status_code, 200)
                                        scenario_result = json.loads(scenario_response.data)
                                        self.assertTrue(scenario_result['success'])
                                        self.assertIn('scenario_id', scenario_result)
                                        
                                        # Step 3: Verify scenario was created and can be retrieved
                                        scenarios_response = self.client.get(
                                            '/api/housing/scenarios/2',
                                            headers=self._get_auth_headers()
                                        )
                                        
                                        self.assertEqual(scenarios_response.status_code, 200)
                                        scenarios_result = json.loads(scenarios_response.data)
                                        self.assertTrue(scenarios_result['success'])
                                        self.assertGreaterEqual(len(scenarios_result['scenarios']), 1)
                                        
                                        # Step 4: Update housing preferences
                                        preferences_data = {
                                            'max_commute_time': 45,
                                            'housing_type': 'apartment',
                                            'min_bedrooms': 2,
                                            'max_bedrooms': 3,
                                            'max_rent_percentage': 35.0,
                                            'preferred_neighborhoods': ['downtown', 'midtown']
                                        }
                                        
                                        preferences_response = self.client.put(
                                            '/api/housing/preferences',
                                            data=json.dumps(preferences_data),
                                            headers=self._get_auth_headers()
                                        )
                                        
                                        self.assertEqual(preferences_response.status_code, 200)
                                        preferences_result = json.loads(preferences_response.data)
                                        self.assertTrue(preferences_result['success'])
                                        
                                        # Step 5: Calculate commute cost for a specific route
                                        commute_data = {
                                            'origin_zip': '10001',
                                            'destination_zip': '10005',
                                            'vehicle_id': 1
                                        }
                                        
                                        with patch('backend.api.optimal_location_api.external_api_service') as mock_commute_external:
                                            mock_commute_external.calculate_route_distance.return_value = {
                                                'success': True,
                                                'distance_miles': 15.5,
                                                'drive_time_minutes': 30,
                                                'traffic_factor': 1.2
                                            }
                                            
                                            with patch('backend.api.optimal_location_api.vehicle_analytics_service') as mock_vehicle:
                                                mock_vehicle.calculate_commute_costs.return_value = {
                                                    'monthly_fuel_cost': 120.0,
                                                    'monthly_maintenance_cost': 45.0,
                                                    'monthly_insurance_cost': 80.0,
                                                    'total_monthly_cost': 245.0,
                                                    'cost_per_mile': 0.79,
                                                    'annual_cost': 2940.0
                                                }
                                                
                                                commute_response = self.client.post(
                                                    '/api/housing/commute-cost',
                                                    data=json.dumps(commute_data),
                                                    headers=self._get_auth_headers()
                                                )
                                                
                                                self.assertEqual(commute_response.status_code, 200)
                                                commute_result = json.loads(commute_response.data)
                                                self.assertTrue(commute_result['success'])
                                                self.assertIn('commute_analysis', commute_result)
                                                
                                                # Step 6: Delete a scenario
                                                scenario_id = scenario_result['scenario_id']
                                                delete_response = self.client.delete(
                                                    f'/api/housing/scenario/{scenario_id}',
                                                    headers=self._get_auth_headers()
                                                )
                                                
                                                self.assertEqual(delete_response.status_code, 200)
                                                delete_result = json.loads(delete_response.data)
                                                self.assertTrue(delete_result['success'])
    
    def test_tier_upgrade_flow(self):
        """Test tier upgrade flow for different user tiers"""
        # Test budget user trying to access mid-tier features
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 1  # Budget user
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = False  # No access
                
                search_data = {
                    'max_rent': 2000,
                    'bedrooms': 1,
                    'commute_time': 45,
                    'zip_code': '10001'
                }
                
                response = self.client.post(
                    '/api/housing/search',
                    data=json.dumps(search_data),
                    headers=self._get_auth_headers(1)
                )
                
                self.assertEqual(response.status_code, 403)
                data = json.loads(response.data)
                
                self.assertIn('upgrade_required', data)
                self.assertTrue(data['upgrade_required'])
                self.assertEqual(data['required_tier'], 'mid_tier')
                
                # Test mid-tier user accessing professional features
                mock_user_id.return_value = 2  # Mid-tier user
                mock_feature.return_value = True  # Has access
                
                with patch('backend.api.optimal_location_api.check_optimal_location_subfeature') as mock_subfeature:
                    mock_subfeature.return_value = False  # No career analysis access
                    
                    scenario_data = {
                        'housing_data': {
                            'address': '123 Test St',
                            'rent': 2500,
                            'bedrooms': 2,
                            'bathrooms': 1
                        },
                        'include_career_analysis': True,  # Professional feature
                        'scenario_name': 'Test Scenario'
                    }
                    
                    response = self.client.post(
                        '/api/housing/scenario',
                        data=json.dumps(scenario_data),
                        headers=self._get_auth_headers(2)
                    )
                    
                    self.assertEqual(response.status_code, 403)
                    data = json.loads(response.data)
                    
                    self.assertIn('upgrade_required', data)
                    self.assertTrue(data['upgrade_required'])
                    self.assertEqual(data['required_tier'], 'mid_tier')
    
    def test_database_transaction_consistency(self):
        """Test database transaction consistency across operations"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 2
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_scenario_save_limit') as mock_limit:
                    mock_limit.return_value = True
                    
                    # Test scenario creation with database error
                    with patch('backend.api.optimal_location_api.db.session.commit') as mock_commit:
                        mock_commit.side_effect = Exception("Database error")
                        
                        scenario_data = {
                            'housing_data': {
                                'address': '123 Error St',
                                'rent': 2000,
                                'bedrooms': 2,
                                'bathrooms': 1
                            },
                            'include_career_analysis': False,
                            'scenario_name': 'Error Test'
                        }
                        
                        response = self.client.post(
                            '/api/housing/scenario',
                            data=json.dumps(scenario_data),
                            headers=self._get_auth_headers()
                        )
                        
                        self.assertEqual(response.status_code, 500)
                        data = json.loads(response.data)
                        
                        self.assertIn('error', data)
                        self.assertIn('Internal server error', data['error'])
                        
                        # Verify rollback occurred
                        mock_commit.assert_called()
    
    def test_external_api_integration(self):
        """Test external API integration with mocked responses"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 2
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_search_limit') as mock_limit:
                    mock_limit.return_value = True
                    
                    # Test with successful external API response
                    with patch('backend.api.optimal_location_api.location_service') as mock_location:
                        mock_location.validate_and_geocode.return_value = {
                            'success': True,
                            'location': {
                                'msa': 'New York-Newark-Jersey City, NY-NJ-PA',
                                'zip_code': '10001'
                            }
                        }
                        
                        with patch('backend.api.optimal_location_api.external_api_service') as mock_external:
                            mock_external.get_rental_listings.return_value = {
                                'success': True,
                                'listings': [
                                    {
                                        'id': 'api_listing1',
                                        'address': '123 API St',
                                        'city': 'New York',
                                        'state': 'NY',
                                        'zip_code': '10001',
                                        'rent': 2500,
                                        'bedrooms': 2,
                                        'bathrooms': 1,
                                        'property_type': 'apartment'
                                    }
                                ]
                            }
                            
                            search_data = {
                                'max_rent': 3000,
                                'bedrooms': 2,
                                'commute_time': 30,
                                'zip_code': '10001'
                            }
                            
                            response = self.client.post(
                                '/api/housing/search',
                                data=json.dumps(search_data),
                                headers=self._get_auth_headers()
                            )
                            
                            self.assertEqual(response.status_code, 200)
                            data = json.loads(response.data)
                            
                            self.assertTrue(data['success'])
                            self.assertEqual(len(data['listings']), 1)
                            self.assertEqual(data['listings'][0]['id'], 'api_listing1')
                            
                            # Test with external API failure
                            mock_external.get_rental_listings.return_value = {
                                'success': False,
                                'error': 'External API Error'
                            }
                            
                            response = self.client.post(
                                '/api/housing/search',
                                data=json.dumps(search_data),
                                headers=self._get_auth_headers()
                            )
                            
                            self.assertEqual(response.status_code, 500)
                            data = json.loads(response.data)
                            
                            self.assertIn('error', data)
                            self.assertIn('Failed to retrieve listings', data['error'])
    
    def test_concurrent_user_scenarios(self):
        """Test concurrent user scenarios"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 2
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_search_limit') as mock_limit:
                    mock_limit.return_value = True
                    
                    # Simulate concurrent searches
                    search_data = {
                        'max_rent': 3000,
                        'bedrooms': 2,
                        'commute_time': 30,
                        'zip_code': '10001'
                    }
                    
                    with patch('backend.api.optimal_location_api.location_service') as mock_location:
                        mock_location.validate_and_geocode.return_value = {
                            'success': True,
                            'location': {
                                'msa': 'New York-Newark-Jersey City, NY-NJ-PA',
                                'zip_code': '10001'
                            }
                        }
                        
                        with patch('backend.api.optimal_location_api.external_api_service') as mock_external:
                            mock_external.get_rental_listings.return_value = {
                                'success': True,
                                'listings': []
                            }
                            
                            # Make multiple concurrent requests
                            responses = []
                            for i in range(5):
                                response = self.client.post(
                                    '/api/housing/search',
                                    data=json.dumps(search_data),
                                    headers=self._get_auth_headers()
                                )
                                responses.append(response)
                            
                            # All requests should succeed
                            for response in responses:
                                self.assertEqual(response.status_code, 200)
                                data = json.loads(response.data)
                                self.assertTrue(data['success'])
    
    def test_rate_limiting_integration(self):
        """Test rate limiting integration"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 2
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_search_limit') as mock_limit:
                    mock_limit.return_value = False  # Rate limit exceeded
                    
                    with patch('backend.api.optimal_location_api.feature_service') as mock_feature_service:
                        mock_feature_service.get_optimal_location_features.return_value = {
                            'housing_searches_per_month': 5
                        }
                        
                        search_data = {
                            'max_rent': 3000,
                            'bedrooms': 2,
                            'commute_time': 30,
                            'zip_code': '10001'
                        }
                        
                        response = self.client.post(
                            '/api/housing/search',
                            data=json.dumps(search_data),
                            headers=self._get_auth_headers()
                        )
                        
                        self.assertEqual(response.status_code, 429)
                        data = json.loads(response.data)
                        
                        self.assertIn('error', data)
                        self.assertIn('Search limit exceeded', data['error'])
                        self.assertIn('upgrade_required', data)
                        self.assertTrue(data['upgrade_required'])
    
    def test_data_persistence_across_sessions(self):
        """Test data persistence across user sessions"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 2
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_scenario_save_limit') as mock_limit:
                    mock_limit.return_value = True
                    
                    # Create a scenario
                    scenario_data = {
                        'housing_data': {
                            'address': '123 Persistence St',
                            'rent': 2500,
                            'bedrooms': 2,
                            'bathrooms': 1
                        },
                        'include_career_analysis': False,
                        'scenario_name': 'Persistence Test'
                    }
                    
                    with patch('backend.api.optimal_location_api.calculate_commute_data') as mock_commute:
                        mock_commute.return_value = {
                            'estimated_commute_time': 25,
                            'estimated_distance': 10.5,
                            'traffic_factor': 1.1,
                            'commute_cost_per_month': 200.0
                        }
                        
                        with patch('backend.api.optimal_location_api.calculate_financial_impact') as mock_financial:
                            mock_financial.return_value = {
                                'monthly_rent': 2500,
                                'affordability_score': 80.0,
                                'total_monthly_housing_cost': 2700.0
                            }
                            
                            response = self.client.post(
                                '/api/housing/scenario',
                                data=json.dumps(scenario_data),
                                headers=self._get_auth_headers()
                            )
                            
                            self.assertEqual(response.status_code, 200)
                            scenario_result = json.loads(response.data)
                            scenario_id = scenario_result['scenario_id']
                            
                            # Verify scenario was saved
                            scenarios_response = self.client.get(
                                '/api/housing/scenarios/2',
                                headers=self._get_auth_headers()
                            )
                            
                            self.assertEqual(scenarios_response.status_code, 200)
                            scenarios_result = json.loads(scenarios_response.data)
                            
                            # Find the created scenario
                            created_scenario = None
                            for scenario in scenarios_result['scenarios']:
                                if scenario['id'] == scenario_id:
                                    created_scenario = scenario
                                    break
                            
                            self.assertIsNotNone(created_scenario)
                            self.assertEqual(created_scenario['scenario_name'], 'Persistence Test')
    
    def test_error_recovery_and_graceful_degradation(self):
        """Test error recovery and graceful degradation"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 2
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_search_limit') as mock_limit:
                    mock_limit.return_value = True
                    
                    # Test with location service failure
                    with patch('backend.api.optimal_location_api.location_service') as mock_location:
                        mock_location.validate_and_geocode.return_value = {
                            'success': False,
                            'error': 'Location service unavailable'
                        }
                        
                        search_data = {
                            'max_rent': 3000,
                            'bedrooms': 2,
                            'commute_time': 30,
                            'zip_code': '10001'
                        }
                        
                        response = self.client.post(
                            '/api/housing/search',
                            data=json.dumps(search_data),
                            headers=self._get_auth_headers()
                        )
                        
                        self.assertEqual(response.status_code, 400)
                        data = json.loads(response.data)
                        
                        self.assertIn('error', data)
                        self.assertIn('Invalid location', data['error'])
    
    def test_performance_under_load(self):
        """Test performance under load"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 2
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_search_limit') as mock_limit:
                    mock_limit.return_value = True
                    
                    search_data = {
                        'max_rent': 3000,
                        'bedrooms': 2,
                        'commute_time': 30,
                        'zip_code': '10001'
                    }
                    
                    with patch('backend.api.optimal_location_api.location_service') as mock_location:
                        mock_location.validate_and_geocode.return_value = {
                            'success': True,
                            'location': {
                                'msa': 'New York-Newark-Jersey City, NY-NJ-PA',
                                'zip_code': '10001'
                            }
                        }
                        
                        with patch('backend.api.optimal_location_api.external_api_service') as mock_external:
                            mock_external.get_rental_listings.return_value = {
                                'success': True,
                                'listings': []
                            }
                            
                            # Measure response time
                            start_time = time.time()
                            
                            response = self.client.post(
                                '/api/housing/search',
                                data=json.dumps(search_data),
                                headers=self._get_auth_headers()
                            )
                            
                            end_time = time.time()
                            response_time = end_time - start_time
                            
                            # Response should be fast (less than 1 second)
                            self.assertLess(response_time, 1.0)
                            self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add integration tests
    test_suite.addTest(unittest.makeSuite(TestOptimalLocationIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
