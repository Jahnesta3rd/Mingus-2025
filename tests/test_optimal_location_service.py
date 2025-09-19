#!/usr/bin/env python3
"""
Mingus Personal Finance App - Optimal Location Service Tests
Comprehensive unit tests for the Optimal Location Service following MINGUS testing patterns
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

from backend.services.optimal_location_service import (
    OptimalLocationService, HousingOption, SearchCriteria, 
    AffordabilityAnalysis, HousingScenario, AffordabilityTier
)

class TestOptimalLocationService(unittest.TestCase):
    """Unit tests for the Optimal Location Service"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary databases
        self.profile_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.vehicle_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.profile_db.close()
        self.vehicle_db.close()
        
        # Initialize service
        self.service = OptimalLocationService(
            profile_db_path=self.profile_db.name,
            vehicle_db_path=self.vehicle_db.name
        )
        
        # Set up test data
        self._setup_test_databases()
    
    def tearDown(self):
        """Clean up test databases"""
        if os.path.exists(self.profile_db.name):
            os.unlink(self.profile_db.name)
        if os.path.exists(self.vehicle_db.name):
            os.unlink(self.vehicle_db.name)
    
    def _setup_test_databases(self):
        """Set up test databases with sample data"""
        # Profile database
        with sqlite3.connect(self.profile_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    first_name TEXT,
                    personal_info TEXT,
                    financial_info TEXT,
                    monthly_expenses TEXT,
                    zip_code TEXT
                )
            ''')
            
            # Insert test user
            cursor.execute('''
                INSERT INTO user_profiles 
                (id, email, first_name, personal_info, financial_info, monthly_expenses, zip_code)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                1, 'test@example.com', 'Test User',
                json.dumps({'age': 30, 'occupation': 'Software Engineer'}),
                json.dumps({'monthly_income': 8000, 'emergency_fund': 10000}),
                json.dumps({'rent': 2000, 'utilities': 200, 'food': 500}),
                '10001'
            ))
            conn.commit()
        
        # Vehicle database
        with sqlite3.connect(self.vehicle_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    make TEXT,
                    model TEXT,
                    year INTEGER,
                    mpg REAL
                )
            ''')
            
            # Insert test vehicle
            cursor.execute('''
                INSERT INTO vehicles (id, user_id, make, model, year, mpg)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (1, 1, 'Toyota', 'Camry', 2020, 30.0))
            conn.commit()
    
    def test_find_optimal_locations_with_valid_data(self):
        """Test finding optimal locations with valid data"""
        search_criteria = SearchCriteria(
            max_price=2500,
            min_bedrooms=2,
            min_bathrooms=1,
            property_types=['apartment'],
            max_commute_time=30,
            preferred_areas=['downtown'],
            must_have_features=['parking'],
            nice_to_have_features=['gym']
        )
        
        with patch.object(self.service, '_get_housing_listings') as mock_listings:
            mock_listings.return_value = [
                {
                    'id': 'listing1',
                    'address': '123 Main St',
                    'city': 'New York',
                    'state': 'NY',
                    'zip_code': '10001',
                    'price': 2200,
                    'bedrooms': 2,
                    'bathrooms': 1,
                    'property_type': 'apartment',
                    'url': 'https://example.com/listing1'
                }
            ]
            
            with patch.object(self.service, 'get_msa_boundaries') as mock_msa:
                mock_msa.return_value = {
                    'success': True,
                    'msa_name': 'New York-Newark-Jersey City, NY-NJ-PA',
                    'msa_zip_codes': ['10001', '10002'],
                    'center_zip_code': '10001'
                }
                
                result = self.service.find_optimal_locations(1, search_criteria)
                
                self.assertTrue(result['success'])
                self.assertIn('top_options', result)
                self.assertIn('total_options', result)
                self.assertEqual(len(result['top_options']), 1)
    
    def test_affordability_score_calculation(self):
        """Test affordability score calculation"""
        user_profile = {
            'email': 'test@example.com',
            'financial_info': {'monthly_income': 8000},
            'monthly_expenses': {'rent': 2000, 'utilities': 200}
        }
        
        housing_option = {
            'price': 2200,
            'address': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001'
        }
        
        commute_analysis = {
            'distance_miles': 10,
            'time_minutes': 25,
            'monthly_cost': 200
        }
        
        with patch.object(self.service.cash_forecast_engine, 'generate_enhanced_cash_flow_forecast') as mock_forecast:
            mock_forecast.return_value = MagicMock(average_monthly_amount=8000)
            
            result = self.service.calculate_affordability_score(
                user_profile, housing_option, commute_analysis
            )
            
            self.assertIn('score', result)
            self.assertIn('tier', result)
            self.assertIn('percentage_of_income', result)
            self.assertIsInstance(result['score'], int)
            self.assertIsInstance(result['tier'], AffordabilityTier)
    
    def test_commute_cost_integration(self):
        """Test commute cost integration with VehicleAnalyticsService"""
        housing_option = {
            'address': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001'
        }
        
        user_profile = {'work_zip_code': '10005'}
        vehicles = [{'make': 'Toyota', 'model': 'Camry', 'mpg': 30.0}]
        
        with patch.object(self.service.external_api_service, 'get_route_info') as mock_route:
            mock_route.return_value = {
                'success': True,
                'data': {
                    'distance_miles': 15.5,
                    'duration_minutes': 30
                }
            }
            
            result = self.service._calculate_commute_costs(
                housing_option, user_profile, vehicles
            )
            
            self.assertIn('distance_miles', result)
            self.assertIn('time_minutes', result)
            self.assertIn('monthly_cost', result)
            self.assertEqual(result['distance_miles'], 15.5)
            self.assertEqual(result['time_minutes'], 30)
    
    def test_tier_restrictions_budget_user(self):
        """Test tier restrictions for budget tier user"""
        with patch.object(self.service.feature_flag_service, 'get_user_tier') as mock_tier:
            mock_tier.return_value = 'budget'
            
            # Budget users should have limited access
            search_criteria = SearchCriteria(
                max_price=1500,
                min_bedrooms=1,
                min_bathrooms=1,
                property_types=['apartment'],
                max_commute_time=45,
                preferred_areas=[],
                must_have_features=[],
                nice_to_have_features=[]
            )
            
            with patch.object(self.service, '_get_housing_listings') as mock_listings:
                mock_listings.return_value = []
                
                with patch.object(self.service, 'get_msa_boundaries') as mock_msa:
                    mock_msa.return_value = {'success': True, 'msa_zip_codes': ['10001']}
                    
                    result = self.service.find_optimal_locations(1, search_criteria)
                    
                    # Should still work but with limited features
                    self.assertTrue(result['success'])
    
    def test_tier_restrictions_midtier_user(self):
        """Test tier restrictions for mid-tier user"""
        with patch.object(self.service.feature_flag_service, 'get_user_tier') as mock_tier:
            mock_tier.return_value = 'mid_tier'
            
            # Mid-tier users should have more features
            search_criteria = SearchCriteria(
                max_price=3000,
                min_bedrooms=2,
                min_bathrooms=2,
                property_types=['apartment', 'condo'],
                max_commute_time=30,
                preferred_areas=['downtown', 'suburbs'],
                must_have_features=['parking', 'laundry'],
                nice_to_have_features=['gym', 'pool']
            )
            
            with patch.object(self.service, '_get_housing_listings') as mock_listings:
                mock_listings.return_value = []
                
                with patch.object(self.service, 'get_msa_boundaries') as mock_msa:
                    mock_msa.return_value = {'success': True, 'msa_zip_codes': ['10001']}
                    
                    result = self.service.find_optimal_locations(1, search_criteria)
                    
                    self.assertTrue(result['success'])
    
    def test_scenario_creation_and_retrieval(self):
        """Test housing scenario creation and retrieval"""
        housing_data = {
            'address': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001',
            'price': 2200,
            'bedrooms': 2,
            'bathrooms': 1
        }
        
        with patch.object(self.service, '_calculate_comprehensive_financial_impact') as mock_financial:
            mock_financial.return_value = {
                'current_monthly_expenses': 3000,
                'new_monthly_expenses': 3200,
                'expense_change': 200
            }
            
            with patch.object(self.service, '_generate_financial_projections') as mock_projections:
                mock_projections.return_value = {
                    'year_1': {'annual_income': 96000, 'annual_expenses': 38400}
                }
                
                result = self.service.create_housing_scenario(1, housing_data, include_career_options=True)
                
                self.assertTrue(result['success'])
                self.assertIn('scenario_id', result)
                self.assertIn('scenario', result)
    
    def test_msa_boundary_detection(self):
        """Test MSA boundary detection"""
        with patch.object(self.service.location_validator, 'geocode_zipcode') as mock_geocode:
            mock_geocode.return_value = MagicMock(
                msa='New York-Newark-Jersey City, NY-NJ-PA',
                latitude=40.7589,
                longitude=-73.9851,
                population=20000000,
                cost_of_living_index=150
            )
            
            with patch.object(self.service, '_get_zip_codes_in_msa') as mock_zip_codes:
                mock_zip_codes.return_value = ['10001', '10002', '10003']
                
                result = self.service.get_msa_boundaries('10001')
                
                self.assertTrue(result['success'])
                self.assertIn('msa_name', result)
                self.assertIn('msa_zip_codes', result)
                self.assertEqual(result['msa_name'], 'New York-Newark-Jersey City, NY-NJ-PA')
    
    def test_external_api_error_handling(self):
        """Test external API error handling"""
        search_criteria = SearchCriteria(
            max_price=2500,
            min_bedrooms=2,
            min_bathrooms=1,
            property_types=['apartment'],
            max_commute_time=30,
            preferred_areas=[],
            must_have_features=[],
            nice_to_have_features=[]
        )
        
        with patch.object(self.service.external_api_service, 'get_rental_listings') as mock_rental:
            mock_rental.side_effect = Exception("API Error")
            
            with patch.object(self.service, 'get_msa_boundaries') as mock_msa:
                mock_msa.return_value = {'success': True, 'msa_zip_codes': ['10001']}
                
                result = self.service.find_optimal_locations(1, search_criteria)
                
                # Should handle API errors gracefully
                self.assertTrue(result['success'])
                self.assertEqual(result['total_options'], 0)
    
    def test_emergency_fund_impact_calculation(self):
        """Test emergency fund impact calculation"""
        user_profile = {
            'financial_info': {'emergency_fund': 5000},
            'monthly_expenses': {'rent': 2000, 'utilities': 200, 'food': 500}
        }
        
        result = self.service._calculate_emergency_fund_impact(
            user_profile, 2500, 8000
        )
        
        self.assertIn('current_emergency_fund', result)
        self.assertIn('recommended_emergency_fund', result)
        self.assertIn('shortfall', result)
        self.assertIn('sufficient', result)
    
    def test_cash_flow_impact_calculation(self):
        """Test cash flow impact calculation"""
        mock_forecast = MagicMock()
        mock_forecast.average_monthly_amount = 8000
        
        result = self.service._calculate_cash_flow_impact(mock_forecast, 2500)
        
        self.assertIn('current_monthly_forecast', result)
        self.assertIn('new_monthly_forecast', result)
        self.assertIn('cash_flow_change', result)
        self.assertIn('percentage_change', result)
    
    def test_affordability_recommendations_generation(self):
        """Test affordability recommendations generation"""
        # Test excellent tier
        recommendations = self.service._generate_affordability_recommendations(
            20.0, 30.0, AffordabilityTier.EXCELLENT
        )
        self.assertIn("Excellent affordability", recommendations[0])
        
        # Test unaffordable tier
        recommendations = self.service._generate_affordability_recommendations(
            50.0, 30.0, AffordabilityTier.UNAFFORDABLE
        )
        self.assertIn("Not affordable", recommendations[0])
    
    def test_financial_projections_generation(self):
        """Test financial projections generation"""
        user_profile = {
            'financial_info': {'monthly_income': 8000},
            'monthly_expenses': {'rent': 2000, 'utilities': 200}
        }
        
        housing_data = {'price': 2500}
        
        result = self.service._generate_financial_projections(
            user_profile, housing_data, years=3
        )
        
        self.assertIn('year_1', result)
        self.assertIn('year_2', result)
        self.assertIn('year_3', result)
        
        for year_data in result.values():
            self.assertIn('annual_income', year_data)
            self.assertIn('annual_expenses', year_data)
            self.assertIn('annual_savings', year_data)
            self.assertIn('savings_rate', year_data)
    
    def test_career_opportunities_analysis(self):
        """Test career opportunities analysis"""
        user_profile = {'email': 'test@example.com'}
        housing_data = {'city': 'New York', 'state': 'NY'}
        
        result = self.service._analyze_career_opportunities(
            user_profile, housing_data
        )
        
        self.assertIsInstance(result, list)
        if result:  # If mock data is returned
            self.assertIn('title', result[0])
            self.assertIn('company', result[0])
            self.assertIn('salary_range', result[0])
    
    def test_database_initialization(self):
        """Test database initialization"""
        # Test that databases are properly initialized
        self.assertTrue(os.path.exists(self.profile_db.name))
        self.assertTrue(os.path.exists(self.vehicle_db.name))
        
        # Test that tables exist
        with sqlite3.connect(self.profile_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            self.assertIn('user_profiles', tables)
    
    def test_user_profile_retrieval(self):
        """Test user profile retrieval"""
        profile = self.service._get_user_profile(1)
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile['email'], 'test@example.com')
        self.assertEqual(profile['first_name'], 'Test User')
        self.assertIn('financial_info', profile)
        self.assertIn('monthly_expenses', profile)
    
    def test_user_vehicles_retrieval(self):
        """Test user vehicles retrieval"""
        vehicles = self.service._get_user_vehicles(1)
        
        self.assertIsInstance(vehicles, list)
        if vehicles:
            self.assertIn('make', vehicles[0])
            self.assertIn('model', vehicles[0])
            self.assertIn('mpg', vehicles[0])
    
    def test_housing_listings_retrieval(self):
        """Test housing listings retrieval"""
        msa_boundaries = {
            'msa_zip_codes': ['10001', '10002'],
            'success': True
        }
        
        search_criteria = SearchCriteria(
            max_price=2500,
            min_bedrooms=2,
            min_bathrooms=1,
            property_types=['apartment'],
            max_commute_time=30,
            preferred_areas=[],
            must_have_features=[],
            nice_to_have_features=[]
        )
        
        with patch.object(self.service.external_api_service, 'get_rental_listings') as mock_rental:
            mock_rental.return_value = {
                'success': True,
                'data': [{'id': '1', 'price': 2000, 'bedrooms': 2}]
            }
            
            with patch.object(self.service.external_api_service, 'get_home_listings') as mock_home:
                mock_home.return_value = {
                    'success': True,
                    'data': [{'id': '2', 'price': 3000, 'bedrooms': 3}]
                }
                
                result = self.service._get_housing_listings(msa_boundaries, search_criteria)
                
                self.assertIsInstance(result, list)
                self.assertEqual(len(result), 2)
    
    def test_monthly_commute_cost_calculation(self):
        """Test monthly commute cost calculation"""
        # Test with vehicles
        vehicles = [{'mpg': 25.0, 'make': 'Honda', 'model': 'Civic'}]
        result = self.service._calculate_monthly_commute_cost(20.0, 45, vehicles)
        
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)
        
        # Test without vehicles (fallback)
        result_no_vehicles = self.service._calculate_monthly_commute_cost(20.0, 45, [])
        self.assertIsInstance(result_no_vehicles, float)
        self.assertGreater(result_no_vehicles, 0)
    
    def test_distance_calculation(self):
        """Test distance calculation between coordinates"""
        # Test distance between NYC and LA (approximately 2445 miles)
        distance = self.service._calculate_distance(40.7589, -73.9851, 34.0522, -118.2437)
        
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 2000)  # Should be roughly 2445 miles
        self.assertLess(distance, 3000)     # But not too far off
    
    def test_msa_determination_from_coordinates(self):
        """Test MSA determination from coordinates"""
        # Test NYC coordinates
        msa = self.service._determine_msa_from_coordinates(40.7589, -73.9851)
        self.assertIn("New York", msa)
        
        # Test LA coordinates
        msa = self.service._determine_msa_from_coordinates(34.0522, -118.2437)
        self.assertIn("Los Angeles", msa)
        
        # Test unknown coordinates
        msa = self.service._determine_msa_from_coordinates(0.0, 0.0)
        self.assertEqual(msa, "Unknown MSA")
    
    def test_zip_codes_in_msa_retrieval(self):
        """Test zip codes in MSA retrieval"""
        # Test known MSA
        zip_codes = self.service._get_zip_codes_in_msa("New York-Newark-Jersey City, NY-NJ-PA")
        self.assertIsInstance(zip_codes, list)
        self.assertGreater(len(zip_codes), 0)
        
        # Test unknown MSA
        zip_codes = self.service._get_zip_codes_in_msa("Unknown MSA")
        self.assertEqual(zip_codes, ["10001"])  # Default fallback
    
    def test_housing_scenario_saving(self):
        """Test housing scenario saving to database"""
        scenario = HousingScenario(
            scenario_id="test_scenario_123",
            user_id=1,
            housing_option={'address': '123 Test St', 'price': 2000},
            financial_impact={'monthly_cost': 2000},
            career_opportunities=[],
            projections={'year_1': {'annual_income': 96000}},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Should not raise exception
        try:
            self.service._save_housing_scenario(scenario)
        except Exception as e:
            self.fail(f"_save_housing_scenario raised an exception: {e}")
        
        # Verify scenario was saved
        with sqlite3.connect(self.profile_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM housing_scenarios WHERE scenario_id = ?", ("test_scenario_123",))
            result = cursor.fetchone()
            self.assertIsNotNone(result)


class TestOptimalLocationServiceIntegration(unittest.TestCase):
    """Integration tests for the Optimal Location Service"""
    
    def setUp(self):
        """Set up integration test environment"""
        # Create temporary databases
        self.profile_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.vehicle_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.profile_db.close()
        self.vehicle_db.close()
        
        # Initialize service
        self.service = OptimalLocationService(
            profile_db_path=self.profile_db.name,
            vehicle_db_path=self.vehicle_db.name
        )
        
        # Set up comprehensive test data
        self._setup_integration_test_data()
    
    def tearDown(self):
        """Clean up integration test databases"""
        if os.path.exists(self.profile_db.name):
            os.unlink(self.profile_db.name)
        if os.path.exists(self.vehicle_db.name):
            os.unlink(self.vehicle_db.name)
    
    def _setup_integration_test_data(self):
        """Set up comprehensive test data for integration tests"""
        # Profile database with multiple users
        with sqlite3.connect(self.profile_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    first_name TEXT,
                    personal_info TEXT,
                    financial_info TEXT,
                    monthly_expenses TEXT,
                    zip_code TEXT
                )
            ''')
            
            # Insert multiple test users
            test_users = [
                (1, 'budget@example.com', 'Budget User', 
                 json.dumps({'age': 25, 'occupation': 'Entry Level'}),
                 json.dumps({'monthly_income': 4000, 'emergency_fund': 2000}),
                 json.dumps({'rent': 1200, 'utilities': 150, 'food': 300}),
                 '10001'),
                (2, 'midtier@example.com', 'Mid Tier User',
                 json.dumps({'age': 30, 'occupation': 'Mid Level'}),
                 json.dumps({'monthly_income': 8000, 'emergency_fund': 15000}),
                 json.dumps({'rent': 2500, 'utilities': 200, 'food': 500}),
                 '10001'),
                (3, 'professional@example.com', 'Professional User',
                 json.dumps({'age': 35, 'occupation': 'Senior Level'}),
                 json.dumps({'monthly_income': 15000, 'emergency_fund': 50000}),
                 json.dumps({'rent': 4000, 'utilities': 300, 'food': 800}),
                 '10001')
            ]
            
            cursor.executemany('''
                INSERT INTO user_profiles 
                (id, email, first_name, personal_info, financial_info, monthly_expenses, zip_code)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', test_users)
            conn.commit()
        
        # Vehicle database with multiple vehicles
        with sqlite3.connect(self.vehicle_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    make TEXT,
                    model TEXT,
                    year INTEGER,
                    mpg REAL
                )
            ''')
            
            # Insert vehicles for each user
            test_vehicles = [
                (1, 1, 'Honda', 'Civic', 2018, 35.0),
                (2, 2, 'Toyota', 'Camry', 2020, 30.0),
                (3, 3, 'BMW', 'X5', 2021, 25.0)
            ]
            
            cursor.executemany('''
                INSERT INTO vehicles (id, user_id, make, model, year, mpg)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', test_vehicles)
            conn.commit()
    
    def test_end_to_end_housing_search_flow(self):
        """Test complete end-to-end housing search flow"""
        search_criteria = SearchCriteria(
            max_price=3000,
            min_bedrooms=2,
            min_bathrooms=1,
            property_types=['apartment'],
            max_commute_time=30,
            preferred_areas=['downtown'],
            must_have_features=['parking'],
            nice_to_have_features=['gym']
        )
        
        # Mock external services
        with patch.object(self.service.external_api_service, 'get_rental_listings') as mock_rental:
            mock_rental.return_value = {
                'success': True,
                'data': [
                    {
                        'id': 'listing1',
                        'address': '123 Main St',
                        'city': 'New York',
                        'state': 'NY',
                        'zip_code': '10001',
                        'price': 2500,
                        'bedrooms': 2,
                        'bathrooms': 1,
                        'property_type': 'apartment',
                        'url': 'https://example.com/listing1'
                    }
                ]
            }
            
            with patch.object(self.service.external_api_service, 'get_route_info') as mock_route:
                mock_route.return_value = {
                    'success': True,
                    'data': {
                        'distance_miles': 10.5,
                        'duration_minutes': 25
                    }
                }
                
                with patch.object(self.service.cash_forecast_engine, 'generate_enhanced_cash_flow_forecast') as mock_forecast:
                    mock_forecast.return_value = MagicMock(average_monthly_amount=8000)
                    
                    # Test with mid-tier user
                    result = self.service.find_optimal_locations(2, search_criteria)
                    
                    self.assertTrue(result['success'])
                    self.assertIn('top_options', result)
                    self.assertGreater(len(result['top_options']), 0)
                    
                    # Verify housing option structure
                    option = result['top_options'][0]
                    self.assertIn('id', option)
                    self.assertIn('address', option)
                    self.assertIn('price', option)
                    self.assertIn('affordability_score', option)
                    self.assertIn('affordability_tier', option)
    
    def test_scenario_creation_with_career_analysis(self):
        """Test scenario creation with career analysis"""
        housing_data = {
            'address': '456 Career Ave',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001',
            'price': 3000,
            'bedrooms': 2,
            'bathrooms': 2
        }
        
        with patch.object(self.service, '_calculate_comprehensive_financial_impact') as mock_financial:
            mock_financial.return_value = {
                'current_monthly_expenses': 4000,
                'new_monthly_expenses': 4500,
                'expense_change': 500
            }
            
            with patch.object(self.service, '_generate_financial_projections') as mock_projections:
                mock_projections.return_value = {
                    'year_1': {'annual_income': 120000, 'annual_expenses': 54000, 'annual_savings': 66000}
                }
                
                with patch.object(self.service, '_analyze_career_opportunities') as mock_career:
                    mock_career.return_value = [
                        {
                            'title': 'Senior Software Engineer',
                            'company': 'Tech Corp',
                            'salary_range': '$120,000 - $150,000',
                            'location': 'New York',
                            'remote_friendly': True,
                            'growth_potential': 'High'
                        }
                    ]
                    
                    result = self.service.create_housing_scenario(
                        3, housing_data, include_career_options=True
                    )
                    
                    self.assertTrue(result['success'])
                    self.assertIn('scenario_id', result)
                    self.assertIn('scenario', result)
                    
                    # Verify career opportunities are included
                    scenario = result['scenario']
                    self.assertIn('career_opportunities', scenario)
                    self.assertGreater(len(scenario['career_opportunities']), 0)
    
    def test_multiple_user_tier_scenarios(self):
        """Test scenarios for different user tiers"""
        search_criteria = SearchCriteria(
            max_price=2000,
            min_bedrooms=1,
            min_bathrooms=1,
            property_types=['apartment'],
            max_commute_time=45,
            preferred_areas=[],
            must_have_features=[],
            nice_to_have_features=[]
        )
        
        # Test budget user (limited features)
        with patch.object(self.service.feature_flag_service, 'get_user_tier') as mock_tier:
            mock_tier.return_value = 'budget'
            
            with patch.object(self.service, '_get_housing_listings') as mock_listings:
                mock_listings.return_value = []
                
                with patch.object(self.service, 'get_msa_boundaries') as mock_msa:
                    mock_msa.return_value = {'success': True, 'msa_zip_codes': ['10001']}
                    
                    result = self.service.find_optimal_locations(1, search_criteria)
                    self.assertTrue(result['success'])
        
        # Test professional user (full features)
        with patch.object(self.service.feature_flag_service, 'get_user_tier') as mock_tier:
            mock_tier.return_value = 'professional'
            
            with patch.object(self.service, '_get_housing_listings') as mock_listings:
                mock_listings.return_value = []
                
                with patch.object(self.service, 'get_msa_boundaries') as mock_msa:
                    mock_msa.return_value = {'success': True, 'msa_zip_codes': ['10001']}
                    
                    result = self.service.find_optimal_locations(3, search_criteria)
                    self.assertTrue(result['success'])
    
    def test_error_recovery_and_graceful_degradation(self):
        """Test error recovery and graceful degradation"""
        search_criteria = SearchCriteria(
            max_price=2500,
            min_bedrooms=2,
            min_bathrooms=1,
            property_types=['apartment'],
            max_commute_time=30,
            preferred_areas=[],
            must_have_features=[],
            nice_to_have_features=[]
        )
        
        # Test with external API failure
        with patch.object(self.service.external_api_service, 'get_rental_listings') as mock_rental:
            mock_rental.side_effect = Exception("External API Error")
            
            with patch.object(self.service, 'get_msa_boundaries') as mock_msa:
                mock_msa.return_value = {'success': True, 'msa_zip_codes': ['10001']}
                
                result = self.service.find_optimal_locations(2, search_criteria)
                
                # Should handle error gracefully
                self.assertTrue(result['success'])
                self.assertEqual(result['total_options'], 0)
        
        # Test with database error
        with patch.object(self.service, '_get_user_profile') as mock_profile:
            mock_profile.side_effect = Exception("Database Error")
            
            result = self.service.find_optimal_locations(999, search_criteria)
            
            # Should handle error gracefully
            self.assertFalse(result['success'])
            self.assertIn('error', result)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add unit tests
    test_suite.addTest(unittest.makeSuite(TestOptimalLocationService))
    
    # Add integration tests
    test_suite.addTest(unittest.makeSuite(TestOptimalLocationServiceIntegration))
    
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
