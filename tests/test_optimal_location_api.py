#!/usr/bin/env python3
"""
Mingus Personal Finance App - Optimal Location API Tests
Comprehensive unit tests for the Optimal Location API endpoints following MINGUS testing patterns
"""

import unittest
import sqlite3
import tempfile
import os
import sys
import json
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

class TestOptimalLocationAPI(unittest.TestCase):
    """Unit tests for the Optimal Location API endpoints"""
    
    def setUp(self):
        """Set up test Flask app and database"""
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
        """Clean up test database"""
        with self.app.app_context():
            db.drop_all()
    
    def _setup_test_data(self):
        """Set up test data"""
        # Create test users
        self.budget_user = User(
            id=1,
            email='budget@example.com',
            first_name='Budget',
            last_name='User',
            tier='budget'
        )
        
        self.midtier_user = User(
            id=2,
            email='midtier@example.com',
            first_name='Mid',
            last_name='Tier',
            tier='mid_tier'
        )
        
        self.professional_user = User(
            id=3,
            email='professional@example.com',
            first_name='Professional',
            last_name='User',
            tier='professional'
        )
        
        db.session.add_all([self.budget_user, self.midtier_user, self.professional_user])
        db.session.commit()
    
    def _get_auth_headers(self, user_id=2):
        """Get authentication headers for testing"""
        return {
            'Authorization': f'Bearer test_token_{user_id}',
            'X-CSRF-Token': 'test_csrf_token_12345',
            'Content-Type': 'application/json'
        }
    
    @patch('backend.api.optimal_location_api.get_current_user_id')
    @patch('backend.api.optimal_location_api.check_optimal_location_feature_access')
    @patch('backend.api.optimal_location_api.check_search_limit')
    def test_housing_search_endpoint_authenticated(self, mock_search_limit, mock_feature_access, mock_user_id):
        """Test housing search endpoint with authenticated user"""
        # Setup mocks
        mock_user_id.return_value = 2
        mock_feature_access.return_value = True
        mock_search_limit.return_value = True
        
        # Mock external services
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
                            'address': '123 Main St',
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
                
                # Test data
                search_data = {
                    'max_rent': 3000,
                    'bedrooms': 2,
                    'commute_time': 30,
                    'zip_code': '10001',
                    'housing_type': 'apartment',
                    'min_bathrooms': 1,
                    'max_distance_from_work': 15
                }
                
                response = self.client.post(
                    '/api/housing/search',
                    data=json.dumps(search_data),
                    headers=self._get_auth_headers()
                )
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                
                self.assertTrue(data['success'])
                self.assertIn('search_id', data)
                self.assertIn('listings', data)
                self.assertIn('total_results', data)
                self.assertIn('search_criteria', data)
                self.assertIn('location', data)
    
    @patch('backend.api.optimal_location_api.get_current_user_id')
    def test_housing_search_rate_limiting(self, mock_user_id):
        """Test housing search rate limiting"""
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
    
    @patch('backend.api.optimal_location_api.get_current_user_id')
    @patch('backend.api.optimal_location_api.check_optimal_location_feature_access')
    @patch('backend.api.optimal_location_api.check_scenario_save_limit')
    def test_scenario_creation_with_career_analysis(self, mock_scenario_limit, mock_feature_access, mock_user_id):
        """Test scenario creation with career analysis"""
        # Setup mocks
        mock_user_id.return_value = 3
        mock_feature_access.return_value = True
        mock_scenario_limit.return_value = True
        
        with patch('backend.api.optimal_location_api.check_optimal_location_subfeature') as mock_subfeature:
            mock_subfeature.return_value = True  # Career analysis allowed
            
            with patch('backend.api.optimal_location_api.calculate_commute_data') as mock_commute:
                mock_commute.return_value = {
                    'estimated_commute_time': 25,
                    'estimated_distance': 12.5,
                    'traffic_factor': 1.1,
                    'commute_cost_per_month': 180.0
                }
                
                with patch('backend.api.optimal_location_api.calculate_financial_impact') as mock_financial:
                    mock_financial.return_value = {
                        'monthly_rent': 3000,
                        'annual_rent': 36000,
                        'affordability_score': 85.0,
                        'recommended_max_rent': 4000,
                        'rent_to_income_ratio': 0.25,
                        'total_monthly_housing_cost': 3180.0
                    }
                    
                    with patch('backend.api.optimal_location_api.calculate_career_analysis') as mock_career:
                        mock_career.return_value = {
                            'nearby_job_opportunities': 25,
                            'average_salary_in_area': 85000,
                            'career_growth_potential': 'High',
                            'networking_opportunities': 'Excellent',
                            'commute_to_job_centers': {
                                'downtown': 20,
                                'tech_corridor': 30,
                                'airport': 40
                            }
                        }
                        
                        # Test data
                        scenario_data = {
                            'housing_data': {
                                'address': '456 Career Ave',
                                'city': 'New York',
                                'state': 'NY',
                                'zip_code': '10001',
                                'rent': 3000,
                                'bedrooms': 2,
                                'bathrooms': 2
                            },
                            'include_career_analysis': True,
                            'scenario_name': 'Career-Focused Apartment'
                        }
                        
                        response = self.client.post(
                            '/api/housing/scenario',
                            data=json.dumps(scenario_data),
                            headers=self._get_auth_headers(3)
                        )
                        
                        self.assertEqual(response.status_code, 200)
                        data = json.loads(response.data)
                        
                        self.assertTrue(data['success'])
                        self.assertIn('scenario_id', data)
                        self.assertIn('scenario_name', data)
                        self.assertIn('housing_data', data)
                        self.assertIn('commute_data', data)
                        self.assertIn('financial_impact', data)
                        self.assertIn('career_data', data)
                        self.assertIn('created_at', data)
    
    @patch('backend.api.optimal_location_api.get_current_user_id')
    def test_tier_based_feature_restrictions(self, mock_user_id):
        """Test tier-based feature restrictions"""
        # Test budget user (no access)
        mock_user_id.return_value = 1
        
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
            
            self.assertIn('error', data)
            self.assertIn('Feature not available', data['error'])
            self.assertIn('upgrade_required', data)
            self.assertTrue(data['upgrade_required'])
            self.assertEqual(data['required_tier'], 'mid_tier')
    
    def test_invalid_input_validation(self):
        """Test invalid input validation"""
        # Test missing required fields
        invalid_data = {
            'max_rent': 3000
            # Missing required fields: bedrooms, commute_time, zip_code
        }
        
        response = self.client.post(
            '/api/housing/search',
            data=json.dumps(invalid_data),
            headers=self._get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('Validation failed', data['error'])
        self.assertIn('details', data)
    
    def test_commute_cost_calculation(self):
        """Test commute cost calculation endpoint"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 2
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.external_api_service') as mock_external:
                    mock_external.calculate_route_distance.return_value = {
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
                        
                        # Test data
                        commute_data = {
                            'origin_zip': '10001',
                            'destination_zip': '10005',
                            'vehicle_id': 1
                        }
                        
                        response = self.client.post(
                            '/api/housing/commute-cost',
                            data=json.dumps(commute_data),
                            headers=self._get_auth_headers()
                        )
                        
                        self.assertEqual(response.status_code, 200)
                        data = json.loads(response.data)
                        
                        self.assertTrue(data['success'])
                        self.assertIn('commute_analysis', data)
                        self.assertIn('route_data', data)
                        
                        # Verify commute analysis structure
                        commute_analysis = data['commute_analysis']
                        self.assertIn('monthly_fuel_cost', commute_analysis)
                        self.assertIn('total_monthly_cost', commute_analysis)
                        self.assertIn('cost_per_mile', commute_analysis)
    
    @patch('backend.api.optimal_location_api.get_current_user_id')
    @patch('backend.api.optimal_location_api.check_optimal_location_feature_access')
    def test_get_user_scenarios(self, mock_feature_access, mock_user_id):
        """Test getting user scenarios"""
        # Setup mocks
        mock_user_id.return_value = 2
        mock_feature_access.return_value = True
        
        # Create test scenarios
        with self.app.app_context():
            scenario1 = HousingScenario(
                user_id=2,
                scenario_name='Test Scenario 1',
                housing_data={'address': '123 Test St', 'rent': 2000},
                commute_data={'commute_time': 25},
                financial_impact={'affordability_score': 85},
                career_data={'opportunities': 10}
            )
            
            scenario2 = HousingScenario(
                user_id=2,
                scenario_name='Test Scenario 2',
                housing_data={'address': '456 Test Ave', 'rent': 2500},
                commute_data={'commute_time': 30},
                financial_impact={'affordability_score': 75},
                career_data={'opportunities': 15}
            )
            
            db.session.add_all([scenario1, scenario2])
            db.session.commit()
        
        response = self.client.get(
            '/api/housing/scenarios/2',
            headers=self._get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('scenarios', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['scenarios']), 2)
        
        # Verify scenario structure
        scenario = data['scenarios'][0]
        self.assertIn('id', scenario)
        self.assertIn('scenario_name', scenario)
        self.assertIn('housing_data', scenario)
        self.assertIn('financial_impact', scenario)
        self.assertIn('is_favorite', scenario)
        self.assertIn('created_at', scenario)
    
    @patch('backend.api.optimal_location_api.get_current_user_id')
    @patch('backend.api.optimal_location_api.check_optimal_location_feature_access')
    def test_update_housing_preferences(self, mock_feature_access, mock_user_id):
        """Test updating housing preferences"""
        # Setup mocks
        mock_user_id.return_value = 2
        mock_feature_access.return_value = True
        
        # Test data
        preferences_data = {
            'max_commute_time': 45,
            'housing_type': 'apartment',
            'min_bedrooms': 2,
            'max_bedrooms': 3,
            'max_rent_percentage': 30.0,
            'preferred_neighborhoods': ['downtown', 'suburbs']
        }
        
        response = self.client.put(
            '/api/housing/preferences',
            data=json.dumps(preferences_data),
            headers=self._get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('preferences', data)
        
        # Verify preferences structure
        preferences = data['preferences']
        self.assertIn('max_commute_time', preferences)
        self.assertIn('preferred_housing_type', preferences)
        self.assertIn('min_bedrooms', preferences)
        self.assertIn('max_bedrooms', preferences)
        self.assertIn('max_rent_percentage', preferences)
        self.assertIn('preferred_neighborhoods', preferences)
        self.assertIn('updated_at', preferences)
    
    @patch('backend.api.optimal_location_api.get_current_user_id')
    @patch('backend.api.optimal_location_api.check_optimal_location_feature_access')
    def test_delete_housing_scenario(self, mock_feature_access, mock_user_id):
        """Test deleting housing scenario"""
        # Setup mocks
        mock_user_id.return_value = 2
        mock_feature_access.return_value = True
        
        # Create test scenario
        with self.app.app_context():
            scenario = HousingScenario(
                user_id=2,
                scenario_name='Test Scenario to Delete',
                housing_data={'address': '789 Delete St', 'rent': 1800},
                commute_data={'commute_time': 20},
                financial_impact={'affordability_score': 90},
                career_data={'opportunities': 5}
            )
            db.session.add(scenario)
            db.session.commit()
            scenario_id = scenario.id
        
        response = self.client.delete(
            f'/api/housing/scenario/{scenario_id}',
            headers=self._get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('scenario_id', data)
        self.assertEqual(data['scenario_id'], scenario_id)
    
    def test_unauthorized_access(self):
        """Test unauthorized access without authentication"""
        search_data = {
            'max_rent': 3000,
            'bedrooms': 2,
            'commute_time': 30,
            'zip_code': '10001'
        }
        
        response = self.client.post(
            '/api/housing/search',
            data=json.dumps(search_data)
            # No authentication headers
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('User authentication required', data['error'])
    
    def test_invalid_csrf_token(self):
        """Test invalid CSRF token"""
        search_data = {
            'max_rent': 3000,
            'bedrooms': 2,
            'commute_time': 30,
            'zip_code': '10001'
        }
        
        headers = self._get_auth_headers()
        headers['X-CSRF-Token'] = 'invalid_token'  # Invalid CSRF token
        
        response = self.client.post(
            '/api/housing/search',
            data=json.dumps(search_data),
            headers=headers
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('Invalid CSRF token', data['error'])
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        with patch('backend.api.optimal_location_api.check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = False  # Rate limit exceeded
            
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
            self.assertIn('Rate limit exceeded', data['error'])
    
    def test_commute_cost_calculation_with_cached_route(self):
        """Test commute cost calculation with cached route"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 2
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                # Create cached route
                with self.app.app_context():
                    cached_route = CommuteRouteCache(
                        origin_zip='10001',
                        destination_zip='10005',
                        distance_miles=15.5,
                        drive_time_minutes=30,
                        traffic_factor=1.2
                    )
                    db.session.add(cached_route)
                    db.session.commit()
                
                with patch('backend.api.optimal_location_api.vehicle_analytics_service') as mock_vehicle:
                    mock_vehicle.calculate_commute_costs.return_value = {
                        'monthly_fuel_cost': 120.0,
                        'total_monthly_cost': 245.0
                    }
                    
                    commute_data = {
                        'origin_zip': '10001',
                        'destination_zip': '10005',
                        'vehicle_id': 1
                    }
                    
                    response = self.client.post(
                        '/api/housing/commute-cost',
                        data=json.dumps(commute_data),
                        headers=self._get_auth_headers()
                    )
                    
                    self.assertEqual(response.status_code, 200)
                    data = json.loads(response.data)
                    
                    self.assertTrue(data['success'])
                    self.assertIn('commute_analysis', data)
                    self.assertIn('route_data', data)
    
    def test_scenario_creation_without_career_analysis(self):
        """Test scenario creation without career analysis"""
        with patch('backend.api.optimal_location_api.get_current_user_id') as mock_user_id:
            mock_user_id.return_value = 2
            
            with patch('backend.api.optimal_location_api.check_optimal_location_feature_access') as mock_feature:
                mock_feature.return_value = True
                
                with patch('backend.api.optimal_location_api.check_scenario_save_limit') as mock_limit:
                    mock_limit.return_value = True
                    
                    with patch('backend.api.optimal_location_api.calculate_commute_data') as mock_commute:
                        mock_commute.return_value = {
                            'estimated_commute_time': 25,
                            'estimated_distance': 12.5,
                            'traffic_factor': 1.1,
                            'commute_cost_per_month': 180.0
                        }
                        
                        with patch('backend.api.optimal_location_api.calculate_financial_impact') as mock_financial:
                            mock_financial.return_value = {
                                'monthly_rent': 2500,
                                'affordability_score': 80.0
                            }
                            
                            scenario_data = {
                                'housing_data': {
                                    'address': '123 Simple St',
                                    'city': 'New York',
                                    'state': 'NY',
                                    'zip_code': '10001',
                                    'rent': 2500,
                                    'bedrooms': 2,
                                    'bathrooms': 1
                                },
                                'include_career_analysis': False,
                                'scenario_name': 'Simple Apartment'
                            }
                            
                            response = self.client.post(
                                '/api/housing/scenario',
                                data=json.dumps(scenario_data),
                                headers=self._get_auth_headers()
                            )
                            
                            self.assertEqual(response.status_code, 200)
                            data = json.loads(response.data)
                            
                            self.assertTrue(data['success'])
                            self.assertIn('scenario_id', data)
                            self.assertIn('housing_data', data)
                            self.assertIn('commute_data', data)
                            self.assertIn('financial_impact', data)
                            # Career data should be empty since not requested
                            self.assertIn('career_data', data)


class TestOptimalLocationAPIIntegration(unittest.TestCase):
    """Integration tests for the Optimal Location API"""
    
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
            self._setup_integration_test_data()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up integration test database"""
        with self.app.app_context():
            db.drop_all()
    
    def _setup_integration_test_data(self):
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
                housing_data={'address': '123 Main St', 'rent': 3000, 'bedrooms': 2},
                commute_data={'commute_time': 20, 'distance': 8.5},
                financial_impact={'affordability_score': 85, 'monthly_cost': 3200},
                career_data={'opportunities': 25, 'avg_salary': 85000}
            ),
            HousingScenario(
                user_id=2,
                scenario_name='Suburban House',
                housing_data={'address': '456 Oak Ave', 'rent': 2200, 'bedrooms': 3},
                commute_data={'commute_time': 35, 'distance': 15.2},
                financial_impact={'affordability_score': 75, 'monthly_cost': 2400},
                career_data={'opportunities': 15, 'avg_salary': 75000}
            ),
            HousingScenario(
                user_id=3,
                scenario_name='Luxury Condo',
                housing_data={'address': '789 Park Ave', 'rent': 5000, 'bedrooms': 2},
                commute_data={'commute_time': 15, 'distance': 5.0},
                financial_impact={'affordability_score': 90, 'monthly_cost': 5200},
                career_data={'opportunities': 50, 'avg_salary': 120000}
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
    
    def test_end_to_end_housing_search_and_scenario_creation(self):
        """Test complete end-to-end flow from search to scenario creation"""
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
                                        
                                        # Step 3: Verify scenario was created
                                        scenarios_response = self.client.get(
                                            '/api/housing/scenarios/2',
                                            headers=self._get_auth_headers()
                                        )
                                        
                                        self.assertEqual(scenarios_response.status_code, 200)
                                        scenarios_result = json.loads(scenarios_response.data)
                                        self.assertTrue(scenarios_result['success'])
                                        self.assertGreaterEqual(len(scenarios_result['scenarios']), 1)
    
    def test_tier_upgrade_flow_testing(self):
        """Test tier upgrade flow"""
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
    
    def test_database_transaction_testing(self):
        """Test database transaction handling"""
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
    
    def test_external_api_integration_testing(self):
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


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add unit tests
    test_suite.addTest(unittest.makeSuite(TestOptimalLocationAPI))
    
    # Add integration tests
    test_suite.addTest(unittest.makeSuite(TestOptimalLocationAPIIntegration))
    
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
