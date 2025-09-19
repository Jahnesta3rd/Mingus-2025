#!/usr/bin/env python3
"""
Geocoding API Endpoints
Provides endpoints for address geocoding, autocomplete, and distance calculations.
"""

import json
import logging
import requests
import os
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
geocoding_bp = Blueprint('geocoding', __name__, url_prefix='/api/geocoding')

def get_google_maps_api_key():
    """Get Google Maps API key from environment"""
    return os.getenv('GOOGLE_MAPS_API_KEY', '')

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In a real implementation, you would verify JWT tokens here
        return f(*args, **kwargs)
    return decorated_function

@geocoding_bp.route('/autocomplete', methods=['POST'])
@cross_origin()
@require_auth
def address_autocomplete():
    """Get address autocomplete suggestions"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query parameter is required'
            }), 400
        
        query = data['query']
        if len(query) < 3:
            return jsonify({
                'success': True,
                'suggestions': []
            })
        
        api_key = get_google_maps_api_key()
        if not api_key:
            # Return mock data for development
            mock_suggestions = [
                {
                    'description': f"{query} Street, New York, NY, USA",
                    'place_id': f"mock_place_{hash(query)}_1",
                    'formatted_address': f"{query} Street, New York, NY, USA"
                },
                {
                    'description': f"{query} Avenue, Los Angeles, CA, USA",
                    'place_id': f"mock_place_{hash(query)}_2",
                    'formatted_address': f"{query} Avenue, Los Angeles, CA, USA"
                },
                {
                    'description': f"{query} Boulevard, Chicago, IL, USA",
                    'place_id': f"mock_place_{hash(query)}_3",
                    'formatted_address': f"{query} Boulevard, Chicago, IL, USA"
                }
            ]
            
            return jsonify({
                'success': True,
                'suggestions': mock_suggestions
            })
        
        # Use Google Places API for autocomplete
        url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
        params = {
            'input': query,
            'key': api_key,
            'types': 'address'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK':
            suggestions = []
            for prediction in data['predictions']:
                suggestions.append({
                    'description': prediction['description'],
                    'place_id': prediction['place_id'],
                    'formatted_address': prediction['description']
                })
            
            return jsonify({
                'success': True,
                'suggestions': suggestions
            })
        else:
            logger.error(f"Google Places API error: {data}")
            return jsonify({
                'success': False,
                'error': 'Address autocomplete failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to get address autocomplete: {e}")
        return jsonify({
            'success': False,
            'error': 'Address autocomplete service unavailable'
        }), 500

@geocoding_bp.route('/geocode', methods=['POST'])
@cross_origin()
@require_auth
def geocode_address():
    """Geocode an address to get coordinates"""
    try:
        data = request.get_json()
        
        if not data or 'address' not in data:
            return jsonify({
                'success': False,
                'error': 'Address parameter is required'
            }), 400
        
        address = data['address']
        
        api_key = get_google_maps_api_key()
        if not api_key:
            # Return mock coordinates for development
            mock_coordinates = {
                'lat': 40.7128 + (hash(address) % 100) / 1000,
                'lng': -74.0060 + (hash(address) % 100) / 1000
            }
            
            return jsonify({
                'success': True,
                'coordinates': mock_coordinates,
                'formatted_address': address
            })
        
        # Use Google Geocoding API
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': api_key
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            coordinates = {
                'lat': result['geometry']['location']['lat'],
                'lng': result['geometry']['location']['lng']
            }
            
            return jsonify({
                'success': True,
                'coordinates': coordinates,
                'formatted_address': result['formatted_address']
            })
        else:
            logger.error(f"Google Geocoding API error: {data}")
            return jsonify({
                'success': False,
                'error': 'Could not geocode address'
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to geocode address: {e}")
        return jsonify({
            'success': False,
            'error': 'Geocoding service unavailable'
        }), 500

@geocoding_bp.route('/distance', methods=['POST'])
@cross_origin()
@require_auth
def calculate_distance():
    """Calculate distance and duration between two points"""
    try:
        data = request.get_json()
        
        if not data or 'origin' not in data or 'destination' not in data:
            return jsonify({
                'success': False,
                'error': 'Origin and destination coordinates are required'
            }), 400
        
        origin = data['origin']
        destination = data['destination']
        
        api_key = get_google_maps_api_key()
        if not api_key:
            # Return mock distance for development
            import math
            
            # Calculate straight-line distance
            lat_diff = destination['lat'] - origin['lat']
            lng_diff = destination['lng'] - origin['lng']
            distance = math.sqrt(lat_diff**2 + lng_diff**2) * 69  # Rough miles per degree
            
            return jsonify({
                'success': True,
                'distance': max(distance, 0.1),  # Minimum 0.1 miles
                'duration': max(distance * 2, 1)  # Rough estimate: 2 minutes per mile
            })
        
        # Use Google Distance Matrix API
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
            return jsonify({
                'success': True,
                'distance': element['distance']['value'] / 1609.34,  # Convert meters to miles
                'duration': element['duration']['value'] / 60  # Convert seconds to minutes
            })
        else:
            logger.error(f"Google Distance Matrix API error: {data}")
            return jsonify({
                'success': False,
                'error': 'Could not calculate distance'
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to calculate distance: {e}")
        return jsonify({
            'success': False,
            'error': 'Distance calculation service unavailable'
        }), 500

@geocoding_bp.route('/reverse-geocode', methods=['POST'])
@cross_origin()
@require_auth
def reverse_geocode():
    """Reverse geocode coordinates to get address"""
    try:
        data = request.get_json()
        
        if not data or 'lat' not in data or 'lng' not in data:
            return jsonify({
                'success': False,
                'error': 'Latitude and longitude are required'
            }), 400
        
        lat = data['lat']
        lng = data['lng']
        
        api_key = get_google_maps_api_key()
        if not api_key:
            # Return mock address for development
            mock_address = f"Mock Address at {lat:.4f}, {lng:.4f}"
            
            return jsonify({
                'success': True,
                'address': mock_address,
                'formatted_address': mock_address
            })
        
        # Use Google Reverse Geocoding API
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'latlng': f"{lat},{lng}",
            'key': api_key
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            return jsonify({
                'success': True,
                'address': result['formatted_address'],
                'formatted_address': result['formatted_address']
            })
        else:
            logger.error(f"Google Reverse Geocoding API error: {data}")
            return jsonify({
                'success': False,
                'error': 'Could not reverse geocode coordinates'
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to reverse geocode: {e}")
        return jsonify({
            'success': False,
            'error': 'Reverse geocoding service unavailable'
        }), 500
