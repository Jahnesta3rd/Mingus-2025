#!/usr/bin/env python3
"""
Test suite for commute cost calculator API endpoints
"""

import json
import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the modules to test
import sys
sys.path.append('backend')
from api.commute_endpoints import commute_bp, init_commute_database, get_route_distance, calculate_commute_costs
from api.geocoding_endpoints import geocoding_bp, get_google_maps_api_key

class TestCommuteEndpoints:
    """Test cases for commute API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(commute_bp)
        app.register_blueprint(geocoding_bp)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        # Initialize database
        init_commute_database()
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_get_scenarios_empty(self, client):
        """Test getting scenarios when none exist"""
        response = client.get('/api/commute/scenarios')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['scenarios'] == []
    
    def test_save_scenario(self, client):
        """Test saving a commute scenario"""
        scenario_data = {
            'id': 'test_scenario_1',
            'name': 'Test Job - Honda Civic',
            'job_location': {
                'address': '123 Tech Street, San Francisco, CA',
                'coordinates': {'lat': 37.7749, 'lng': -122.4194}
            },
            'home_location': {
                'address': '456 Home Avenue, Oakland, CA',
                'coordinates': {'lat': 37.8044, 'lng': -122.2712}
            },
            'vehicle': {
                'id': 'vehicle_1',
                'make': 'Honda',
                'model': 'Civic',
                'year': 2020,
                'mpg': 32,
                'fuel_type': 'gasoline'
            },
            'commute_details': {
                'distance': 15.5,
                'duration': 25,
                'frequency': 'daily',
                'days_per_week': 5
            },
            'costs': {
                'fuel': 45.50,
                'maintenance': 12.30,
                'depreciation': 8.75,
                'insurance': 15.00,
                'parking': 75.00,
                'tolls': 5.25,
                'total': 161.80
            }
        }
        
        response = client.post('/api/commute/scenarios', 
                             data=json.dumps(scenario_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['scenario_id'] == 'test_scenario_1'
    
    def test_save_scenario_missing_fields(self, client):
        """Test saving scenario with missing required fields"""
        incomplete_data = {
            'id': 'test_scenario_1',
            'name': 'Test Job'
            # Missing required fields
        }
        
        response = client.post('/api/commute/scenarios',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Missing required field' in data['error']
    
    def test_get_scenarios_after_save(self, client):
        """Test retrieving scenarios after saving one"""
        # First save a scenario
        scenario_data = {
            'id': 'test_scenario_1',
            'name': 'Test Job - Honda Civic',
            'job_location': {'address': '123 Tech Street'},
            'home_location': {'address': '456 Home Avenue'},
            'vehicle': {'id': 'vehicle_1', 'make': 'Honda', 'model': 'Civic', 'year': 2020, 'mpg': 32, 'fuel_type': 'gasoline'},
            'commute_details': {'distance': 15.5, 'duration': 25, 'frequency': 'daily', 'days_per_week': 5},
            'costs': {'fuel': 45.50, 'maintenance': 12.30, 'depreciation': 8.75, 'insurance': 15.00, 'parking': 75.00, 'tolls': 5.25, 'total': 161.80}
        }
        
        save_response = client.post('/api/commute/scenarios',
                                  data=json.dumps(scenario_data),
                                  content_type='application/json')
        assert save_response.status_code == 200
        
        # Then retrieve scenarios
        response = client.get('/api/commute/scenarios')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['scenarios']) == 1
        assert data['scenarios'][0]['id'] == 'test_scenario_1'
        assert data['scenarios'][0]['name'] == 'Test Job - Honda Civic'
    
    def test_delete_scenario(self, client):
        """Test deleting a commute scenario"""
        # First save a scenario
        scenario_data = {
            'id': 'test_scenario_1',
            'name': 'Test Job - Honda Civic',
            'job_location': {'address': '123 Tech Street'},
            'home_location': {'address': '456 Home Avenue'},
            'vehicle': {'id': 'vehicle_1', 'make': 'Honda', 'model': 'Civic', 'year': 2020, 'mpg': 32, 'fuel_type': 'gasoline'},
            'commute_details': {'distance': 15.5, 'duration': 25, 'frequency': 'daily', 'days_per_week': 5},
            'costs': {'fuel': 45.50, 'maintenance': 12.30, 'depreciation': 8.75, 'insurance': 15.00, 'parking': 75.00, 'tolls': 5.25, 'total': 161.80}
        }
        
        save_response = client.post('/api/commute/scenarios',
                                  data=json.dumps(scenario_data),
                                  content_type='application/json')
        assert save_response.status_code == 200
        
        # Then delete it
        response = client.delete('/api/commute/scenarios/test_scenario_1')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Verify it's deleted
        get_response = client.get('/api/commute/scenarios')
        scenarios_data = json.loads(get_response.data)
        assert len(scenarios_data['scenarios']) == 0
    
    def test_delete_nonexistent_scenario(self, client):
        """Test deleting a scenario that doesn't exist"""
        response = client.delete('/api/commute/scenarios/nonexistent_id')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Scenario not found' in data['error']
    
    def test_get_vehicles(self, client):
        """Test getting user vehicles"""
        response = client.get('/api/commute/vehicles')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'vehicles' in data
    
    @patch('api.commute_endpoints.get_route_distance')
    def test_calculate_commute(self, mock_get_distance, client):
        """Test calculating commute costs"""
        mock_get_distance.return_value = {'distance': 15.5, 'duration': 25}
        
        calculation_data = {
            'origin': {'lat': 37.7749, 'lng': -122.4194},
            'destination': {'lat': 37.8044, 'lng': -122.2712},
            'vehicle': {
                'id': 'vehicle_1',
                'make': 'Honda',
                'model': 'Civic',
                'year': 2020,
                'mpg': 32,
                'fuel_type': 'gasoline'
            },
            'days_per_week': 5
        }
        
        response = client.post('/api/commute/calculate',
                             data=json.dumps(calculation_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'calculation' in data
        assert 'distance' in data['calculation']
        assert 'costs' in data['calculation']
    
    def test_calculate_commute_missing_fields(self, client):
        """Test calculating commute with missing required fields"""
        incomplete_data = {
            'origin': {'lat': 37.7749, 'lng': -122.4194}
            # Missing destination and vehicle
        }
        
        response = client.post('/api/commute/calculate',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Missing required field' in data['error']


class TestGeocodingEndpoints:
    """Test cases for geocoding API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(geocoding_bp)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_address_autocomplete(self, client):
        """Test address autocomplete functionality"""
        autocomplete_data = {'query': '123 Main Street'}
        
        response = client.post('/api/geocoding/autocomplete',
                             data=json.dumps(autocomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'suggestions' in data
    
    def test_address_autocomplete_short_query(self, client):
        """Test address autocomplete with query too short"""
        autocomplete_data = {'query': '12'}
        
        response = client.post('/api/geocoding/autocomplete',
                             data=json.dumps(autocomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['suggestions'] == []
    
    def test_address_autocomplete_missing_query(self, client):
        """Test address autocomplete without query parameter"""
        response = client.post('/api/geocoding/autocomplete',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Query parameter is required' in data['error']
    
    def test_geocode_address(self, client):
        """Test geocoding an address"""
        geocode_data = {'address': '123 Main Street, New York, NY'}
        
        response = client.post('/api/geocoding/geocode',
                             data=json.dumps(geocode_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'coordinates' in data
        assert 'lat' in data['coordinates']
        assert 'lng' in data['coordinates']
    
    def test_geocode_address_missing_address(self, client):
        """Test geocoding without address parameter"""
        response = client.post('/api/geocoding/geocode',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Address parameter is required' in data['error']
    
    def test_calculate_distance(self, client):
        """Test calculating distance between two points"""
        distance_data = {
            'origin': {'lat': 40.7128, 'lng': -74.0060},
            'destination': {'lat': 40.7589, 'lng': -73.9851}
        }
        
        response = client.post('/api/geocoding/distance',
                             data=json.dumps(distance_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'distance' in data
        assert 'duration' in data
    
    def test_calculate_distance_missing_coordinates(self, client):
        """Test calculating distance with missing coordinates"""
        incomplete_data = {'origin': {'lat': 40.7128, 'lng': -74.0060}}
        
        response = client.post('/api/geocoding/distance',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Origin and destination coordinates are required' in data['error']
    
    def test_reverse_geocode(self, client):
        """Test reverse geocoding coordinates to address"""
        reverse_geocode_data = {'lat': 40.7128, 'lng': -74.0060}
        
        response = client.post('/api/geocoding/reverse-geocode',
                             data=json.dumps(reverse_geocode_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'address' in data
    
    def test_reverse_geocode_missing_coordinates(self, client):
        """Test reverse geocoding with missing coordinates"""
        response = client.post('/api/geocoding/reverse-geocode',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Latitude and longitude are required' in data['error']


class TestCommuteCalculations:
    """Test cases for commute cost calculations"""
    
    def test_calculate_commute_costs_new_vehicle(self):
        """Test cost calculation for a new vehicle"""
        vehicle = {
            'id': 'vehicle_1',
            'make': 'Honda',
            'model': 'Civic',
            'year': 2023,  # New vehicle
            'mpg': 32,
            'fuel_type': 'gasoline'
        }
        
        distance = 15.5
        days_per_week = 5
        
        costs = calculate_commute_costs(distance, vehicle, days_per_week=days_per_week)
        
        assert 'fuel_cost' in costs
        assert 'maintenance_cost' in costs
        assert 'depreciation_cost' in costs
        assert 'total_cost' in costs
        assert 'annual_cost' in costs
        
        # New vehicle should have higher depreciation rate
        assert costs['depreciation_cost'] > 0
        assert costs['maintenance_cost'] > 0
        assert costs['fuel_cost'] > 0
    
    def test_calculate_commute_costs_old_vehicle(self):
        """Test cost calculation for an older vehicle"""
        vehicle = {
            'id': 'vehicle_2',
            'make': 'Toyota',
            'model': 'Camry',
            'year': 2010,  # Old vehicle
            'mpg': 25,
            'fuel_type': 'gasoline'
        }
        
        distance = 15.5
        days_per_week = 5
        
        costs = calculate_commute_costs(distance, vehicle, days_per_week=days_per_week)
        
        assert 'fuel_cost' in costs
        assert 'maintenance_cost' in costs
        assert 'depreciation_cost' in costs
        assert 'total_cost' in costs
        
        # Old vehicle should have higher maintenance rate
        assert costs['maintenance_cost'] > 0
        assert costs['fuel_cost'] > 0
    
    def test_calculate_commute_costs_hybrid_vehicle(self):
        """Test cost calculation for a hybrid vehicle"""
        vehicle = {
            'id': 'vehicle_3',
            'make': 'Toyota',
            'model': 'Prius',
            'year': 2020,
            'mpg': 50,  # High MPG
            'fuel_type': 'hybrid'
        }
        
        distance = 15.5
        days_per_week = 5
        
        costs = calculate_commute_costs(distance, vehicle, days_per_week=days_per_week)
        
        # Hybrid should have lower fuel costs due to higher MPG
        assert costs['fuel_cost'] > 0
        assert costs['total_cost'] > 0
    
    def test_calculate_commute_costs_different_days_per_week(self):
        """Test cost calculation with different work schedules"""
        vehicle = {
            'id': 'vehicle_1',
            'make': 'Honda',
            'model': 'Civic',
            'year': 2020,
            'mpg': 32,
            'fuel_type': 'gasoline'
        }
        
        distance = 15.5
        
        # 5 days per week
        costs_5_days = calculate_commute_costs(distance, vehicle, days_per_week=5)
        
        # 3 days per week (hybrid work)
        costs_3_days = calculate_commute_costs(distance, vehicle, days_per_week=3)
        
        # 3 days should cost less than 5 days
        assert costs_3_days['total_cost'] < costs_5_days['total_cost']
        assert costs_3_days['annual_cost'] < costs_5_days['annual_cost']
    
    def test_calculate_commute_costs_zero_distance(self):
        """Test cost calculation with zero distance (remote work)"""
        vehicle = {
            'id': 'vehicle_1',
            'make': 'Honda',
            'model': 'Civic',
            'year': 2020,
            'mpg': 32,
            'fuel_type': 'gasoline'
        }
        
        distance = 0
        days_per_week = 5
        
        costs = calculate_commute_costs(distance, vehicle, days_per_week=days_per_week)
        
        # Zero distance should result in minimal costs
        assert costs['fuel_cost'] == 0
        assert costs['maintenance_cost'] == 0
        assert costs['depreciation_cost'] == 0
        assert costs['total_cost'] == 0


class TestDatabaseOperations:
    """Test cases for database operations"""
    
    def test_init_database(self):
        """Test database initialization"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            # This should not raise an exception
            init_commute_database()
            
            # Verify tables were created
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'commute_scenarios' in tables
            assert 'user_vehicles' in tables
            
            conn.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
