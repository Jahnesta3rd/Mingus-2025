#!/usr/bin/env python3
"""
Commute Cost Calculator API Endpoints
Provides endpoints for commute cost calculations, scenario management, and geocoding services.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import requests
import os
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
commute_bp = Blueprint('commute', __name__, url_prefix='/api/commute')

# Database path
DB_PATH = "backend/mingus_commute.db"

@dataclass
class CommuteScenario:
    """Commute scenario data structure"""
    id: str
    name: str
    job_location: Dict[str, Any]
    home_location: Dict[str, Any]
    vehicle: Dict[str, Any]
    commute_details: Dict[str, Any]
    costs: Dict[str, float]
    created_at: str
    updated_at: str

@dataclass
class Vehicle:
    """Vehicle data structure"""
    id: str
    make: str
    model: str
    year: int
    mpg: float
    fuel_type: str
    current_mileage: int
    monthly_miles: int

def init_commute_database():
    """Initialize the commute scenarios database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create scenarios table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commute_scenarios (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT NOT NULL,
                job_location TEXT NOT NULL,
                home_location TEXT NOT NULL,
                vehicle TEXT NOT NULL,
                commute_details TEXT NOT NULL,
                costs TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create vehicles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_vehicles (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                mpg REAL NOT NULL,
                fuel_type TEXT NOT NULL,
                current_mileage INTEGER DEFAULT 0,
                monthly_miles INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Commute database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize commute database: {e}")
        raise

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In a real implementation, you would verify JWT tokens here
        # For now, we'll assume the user is authenticated
        return f(*args, **kwargs)
    return decorated_function

def get_google_maps_api_key():
    """Get Google Maps API key from environment"""
    return os.getenv('GOOGLE_MAPS_API_KEY', '')

@commute_bp.route('/scenarios', methods=['GET'])
@cross_origin()
@require_auth
def get_scenarios():
    """Get all saved commute scenarios for the user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # In a real implementation, you would filter by user_id
        cursor.execute('''
            SELECT id, name, job_location, home_location, vehicle, 
                   commute_details, costs, created_at, updated_at
            FROM commute_scenarios
            ORDER BY updated_at DESC
        ''')
        
        scenarios = []
        for row in cursor.fetchall():
            scenario = {
                'id': row[0],
                'name': row[1],
                'job_location': json.loads(row[2]),
                'home_location': json.loads(row[3]),
                'vehicle': json.loads(row[4]),
                'commute_details': json.loads(row[5]),
                'costs': json.loads(row[6]),
                'created_at': row[7],
                'updated_at': row[8]
            }
            scenarios.append(scenario)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'scenarios': scenarios
        })
        
    except Exception as e:
        logger.error(f"Failed to get scenarios: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve scenarios'
        }), 500

@commute_bp.route('/scenarios', methods=['POST'])
@cross_origin()
@require_auth
def save_scenario():
    """Save a new commute scenario"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['id', 'name', 'job_location', 'home_location', 'vehicle', 'commute_details', 'costs']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insert or update scenario
        cursor.execute('''
            INSERT OR REPLACE INTO commute_scenarios 
            (id, user_id, name, job_location, home_location, vehicle, 
             commute_details, costs, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['id'],
            'current_user',  # In real implementation, get from JWT token
            data['name'],
            json.dumps(data['job_location']),
            json.dumps(data['home_location']),
            json.dumps(data['vehicle']),
            json.dumps(data['commute_details']),
            json.dumps(data['costs']),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Scenario saved successfully',
            'scenario_id': data['id']
        })
        
    except Exception as e:
        logger.error(f"Failed to save scenario: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to save scenario'
        }), 500

@commute_bp.route('/scenarios/<scenario_id>', methods=['DELETE'])
@cross_origin()
@require_auth
def delete_scenario(scenario_id):
    """Delete a commute scenario"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM commute_scenarios WHERE id = ?', (scenario_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Scenario not found'
            }), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Scenario deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to delete scenario: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete scenario'
        }), 500

@commute_bp.route('/vehicles', methods=['GET'])
@cross_origin()
@require_auth
def get_vehicles():
    """Get user's vehicles"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # In a real implementation, you would filter by user_id
        cursor.execute('''
            SELECT id, make, model, year, mpg, fuel_type, 
                   current_mileage, monthly_miles, created_at, updated_at
            FROM user_vehicles
            ORDER BY created_at DESC
        ''')
        
        vehicles = []
        for row in cursor.fetchall():
            vehicle = {
                'id': row[0],
                'make': row[1],
                'model': row[2],
                'year': row[3],
                'mpg': row[4],
                'fuel_type': row[5],
                'current_mileage': row[6],
                'monthly_miles': row[7],
                'created_at': row[8],
                'updated_at': row[9]
            }
            vehicles.append(vehicle)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'vehicles': vehicles
        })
        
    except Exception as e:
        logger.error(f"Failed to get vehicles: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve vehicles'
        }), 500

@commute_bp.route('/calculate', methods=['POST'])
@cross_origin()
@require_auth
def calculate_commute():
    """Calculate commute costs between two locations"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['origin', 'destination', 'vehicle']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Get distance and duration from Google Maps API
        distance_data = get_route_distance(
            data['origin']['coordinates'],
            data['destination']['coordinates']
        )
        
        if not distance_data:
            return jsonify({
                'success': False,
                'error': 'Could not calculate route distance'
            }), 400
        
        # Calculate costs
        costs = calculate_commute_costs(
            distance_data['distance'],
            data['vehicle'],
            data.get('days_per_week', 5)
        )
        
        return jsonify({
            'success': True,
            'calculation': {
                'distance': distance_data['distance'],
                'duration': distance_data['duration'],
                'costs': costs
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to calculate commute: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to calculate commute costs'
        }), 500

def get_route_distance(origin: Dict[str, float], destination: Dict[str, float]) -> Optional[Dict[str, Any]]:
    """Get distance and duration between two points using Google Maps API"""
    try:
        api_key = get_google_maps_api_key()
        if not api_key:
            logger.warning("Google Maps API key not configured")
            # Return mock data for development
            return {
                'distance': 15.5,  # miles
                'duration': 25  # minutes
            }
        
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': f"{origin['lat']},{origin['lng']}",
            'destinations': f"{destination['lat']},{destination['lng']}",
            'units': 'imperial',
            'key': api_key
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['rows'][0]['elements'][0]['status'] == 'OK':
            element = data['rows'][0]['elements'][0]
            return {
                'distance': element['distance']['value'] / 1609.34,  # Convert meters to miles
                'duration': element['duration']['value'] / 60  # Convert seconds to minutes
            }
        else:
            logger.error(f"Google Maps API error: {data}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to get route distance: {e}")
        return None

def calculate_commute_costs(distance: float, vehicle: Dict[str, Any], days_per_week: int = 5) -> Dict[str, float]:
    """Calculate detailed commute costs"""
    try:
        weekly_distance = distance * 2 * days_per_week  # Round trip
        monthly_distance = weekly_distance * 4.33
        annual_distance = monthly_distance * 12
        
        # Fuel costs (assuming $3.50/gallon average)
        fuel_price = 3.50
        fuel_cost_per_mile = fuel_price / vehicle['mpg']
        fuel_cost = weekly_distance * fuel_cost_per_mile
        
        # Maintenance costs (based on vehicle age and mileage)
        vehicle_age = datetime.now().year - vehicle['year']
        if vehicle_age > 10:
            maintenance_rate = 0.15
        elif vehicle_age > 5:
            maintenance_rate = 0.10
        else:
            maintenance_rate = 0.08
        
        maintenance_cost = weekly_distance * maintenance_rate
        
        # Depreciation (simplified calculation)
        if vehicle_age > 10:
            depreciation_rate = 0.05
        elif vehicle_age > 5:
            depreciation_rate = 0.08
        else:
            depreciation_rate = 0.12
        
        depreciation_cost = weekly_distance * depreciation_rate
        
        # Insurance (prorated for commute)
        insurance_cost = (500 / 12) * (days_per_week / 7)  # $500/month insurance
        
        # Parking (estimated)
        parking_cost = days_per_week * 15  # $15/day parking
        
        # Tolls (estimated)
        tolls_cost = weekly_distance * 0.05  # $0.05/mile in tolls
        
        total_cost = fuel_cost + maintenance_cost + depreciation_cost + insurance_cost + parking_cost + tolls_cost
        cost_per_mile = total_cost / weekly_distance if weekly_distance > 0 else 0
        annual_cost = total_cost * 52
        
        return {
            'fuel_cost': fuel_cost,
            'maintenance_cost': maintenance_cost,
            'depreciation_cost': depreciation_cost,
            'insurance_cost': insurance_cost,
            'parking_cost': parking_cost,
            'tolls_cost': tolls_cost,
            'total_cost': total_cost,
            'cost_per_mile': cost_per_mile,
            'annual_cost': annual_cost,
            'weekly_distance': weekly_distance,
            'monthly_distance': monthly_distance,
            'annual_distance': annual_distance
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate commute costs: {e}")
        return {}

# Initialize database on module load
init_commute_database()
