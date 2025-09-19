#!/usr/bin/env python3
"""
MINGUS External API Endpoints

REST API endpoints for external API integrations used by the Optimal Living Location feature.
Provides endpoints for Rentals.com, Zillow, and Google Maps Distance Matrix API integration.

Endpoints:
- GET /api/external/rentals/{zip_code} - Get rental listings
- GET /api/external/homes/{zip_code} - Get home listings  
- POST /api/external/route/distance - Calculate route distance
- GET /api/external/route/cached - Get cached route data
- GET /api/external/status - Get service status
- POST /api/external/cache/clear - Clear API cache
"""

import os
import sys
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from werkzeug.exceptions import BadRequest, NotFound

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.external_api_service import external_api_service

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
external_api = Blueprint('external_api', __name__)

# ============================================================================
# RENTAL LISTINGS ENDPOINTS
# ============================================================================

@external_api.route('/api/external/rentals/<zip_code>', methods=['GET'])
@cross_origin()
def get_rental_listings(zip_code):
    """
    Get rental listings for a specific zipcode from Rentals.com.
    
    Args:
        zip_code: 5-digit US zipcode
        
    Query Parameters:
        limit: int (optional) - Maximum number of listings to return (default: 50)
        offset: int (optional) - Number of listings to skip (default: 0)
        price_min: float (optional) - Minimum rent price
        price_max: float (optional) - Maximum rent price
        bedrooms: int (optional) - Number of bedrooms
        bathrooms: float (optional) - Number of bathrooms
        property_type: str (optional) - Type of property (apartment, house, condo, etc.)
        pet_friendly: bool (optional) - Pet-friendly properties only
        furnished: bool (optional) - Furnished properties only
        parking: bool (optional) - Parking available
        laundry: bool (optional) - Laundry facilities
        air_conditioning: bool (optional) - Air conditioning
        dishwasher: bool (optional) - Dishwasher
        pool: bool (optional) - Swimming pool
        gym: bool (optional) - Gym/fitness center
        
    Returns:
        JSON response with rental listings
    """
    try:
        # Validate zipcode format
        if not zip_code or not zip_code.isdigit() or len(zip_code) != 5:
            return jsonify({
                'success': False,
                'error': 'Invalid zipcode format. Must be 5 digits.',
                'zip_code': zip_code
            }), 400
        
        # Get query parameters
        filters = {}
        for param in request.args:
            value = request.args.get(param)
            
            # Convert numeric parameters
            if param in ['limit', 'offset', 'bedrooms']:
                try:
                    filters[param] = int(value)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'error': f'Invalid {param} value. Must be an integer.',
                        'zip_code': zip_code
                    }), 400
            
            # Convert float parameters
            elif param in ['bathrooms', 'price_min', 'price_max']:
                try:
                    filters[param] = float(value)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'error': f'Invalid {param} value. Must be a number.',
                        'zip_code': zip_code
                    }), 400
            
            # Convert boolean parameters
            elif param in ['pet_friendly', 'furnished', 'parking', 'laundry', 
                          'air_conditioning', 'dishwasher', 'pool', 'gym']:
                if value.lower() in ['true', '1', 'yes']:
                    filters[param] = True
                elif value.lower() in ['false', '0', 'no']:
                    filters[param] = False
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid {param} value. Must be true/false.',
                        'zip_code': zip_code
                    }), 400
            
            # String parameters
            else:
                filters[param] = value
        
        # Get rental listings
        result = external_api_service.get_rental_listings(zip_code, filters)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 500 if 'rate_limit' in result.get('error', '') else 400
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f"Error getting rental listings for zipcode {zip_code}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'zip_code': zip_code
        }), 500

# ============================================================================
# HOME LISTINGS ENDPOINTS
# ============================================================================

@external_api.route('/api/external/homes/<zip_code>', methods=['GET'])
@cross_origin()
def get_home_listings(zip_code):
    """
    Get home listings for a specific zipcode from Zillow.
    
    Args:
        zip_code: 5-digit US zipcode
        
    Query Parameters:
        limit: int (optional) - Maximum number of listings to return (default: 50)
        offset: int (optional) - Number of listings to skip (default: 0)
        price_min: float (optional) - Minimum home price
        price_max: float (optional) - Maximum home price
        bedrooms: int (optional) - Number of bedrooms
        bathrooms: float (optional) - Number of bathrooms
        home_type: str (optional) - Type of home (house, condo, townhouse, etc.)
        square_feet_min: int (optional) - Minimum square footage
        square_feet_max: int (optional) - Maximum square footage
        year_built_min: int (optional) - Minimum year built
        year_built_max: int (optional) - Maximum year built
        lot_size_min: float (optional) - Minimum lot size
        lot_size_max: float (optional) - Maximum lot size
        has_pool: bool (optional) - Has swimming pool
        has_garage: bool (optional) - Has garage
        new_construction: bool (optional) - New construction only
        
    Returns:
        JSON response with home listings
    """
    try:
        # Validate zipcode format
        if not zip_code or not zip_code.isdigit() or len(zip_code) != 5:
            return jsonify({
                'success': False,
                'error': 'Invalid zipcode format. Must be 5 digits.',
                'zip_code': zip_code
            }), 400
        
        # Get query parameters
        filters = {}
        for param in request.args:
            value = request.args.get(param)
            
            # Convert numeric parameters
            if param in ['limit', 'offset', 'bedrooms', 'square_feet_min', 'square_feet_max',
                        'year_built_min', 'year_built_max']:
                try:
                    filters[param] = int(value)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'error': f'Invalid {param} value. Must be an integer.',
                        'zip_code': zip_code
                    }), 400
            
            # Convert float parameters
            elif param in ['bathrooms', 'price_min', 'price_max', 'lot_size_min', 'lot_size_max']:
                try:
                    filters[param] = float(value)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'error': f'Invalid {param} value. Must be a number.',
                        'zip_code': zip_code
                    }), 400
            
            # Convert boolean parameters
            elif param in ['has_pool', 'has_garage', 'new_construction']:
                if value.lower() in ['true', '1', 'yes']:
                    filters[param] = True
                elif value.lower() in ['false', '0', 'no']:
                    filters[param] = False
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid {param} value. Must be true/false.',
                        'zip_code': zip_code
                    }), 400
            
            # String parameters
            else:
                filters[param] = value
        
        # Get home listings
        result = external_api_service.get_home_listings(zip_code, filters)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 500 if 'rate_limit' in result.get('error', '') else 400
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f"Error getting home listings for zipcode {zip_code}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'zip_code': zip_code
        }), 500

# ============================================================================
# ROUTE DISTANCE ENDPOINTS
# ============================================================================

@external_api.route('/api/external/route/distance', methods=['POST'])
@cross_origin()
def calculate_route_distance():
    """
    Calculate route distance between two locations using Google Maps.
    
    Body:
        origin: str - Origin address or coordinates
        destination: str - Destination address or coordinates
        mode: str (optional) - Travel mode (driving, walking, bicycling, transit)
        avoid: list (optional) - List of things to avoid (tolls, highways, ferries, indoor)
        
    Returns:
        JSON response with route distance information
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        # Validate required fields
        if 'origin' not in data or 'destination' not in data:
            return jsonify({
                'success': False,
                'error': 'Origin and destination are required'
            }), 400
        
        origin = data['origin']
        destination = data['destination']
        mode = data.get('mode', 'driving')
        avoid = data.get('avoid', [])
        
        # Validate mode
        valid_modes = ['driving', 'walking', 'bicycling', 'transit']
        if mode not in valid_modes:
            return jsonify({
                'success': False,
                'error': f'Invalid mode. Must be one of: {", ".join(valid_modes)}'
            }), 400
        
        # Validate avoid options
        valid_avoid = ['tolls', 'highways', 'ferries', 'indoor']
        if avoid and not all(item in valid_avoid for item in avoid):
            return jsonify({
                'success': False,
                'error': f'Invalid avoid options. Must be one or more of: {", ".join(valid_avoid)}'
            }), 400
        
        # Calculate route distance
        result = external_api_service.calculate_route_distance(origin, destination, mode, avoid)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 500 if 'rate_limit' in result.get('error', '') else 400
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f"Error calculating route distance: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@external_api.route('/api/external/route/cached', methods=['GET'])
@cross_origin()
def get_cached_route():
    """
    Get cached route data if available.
    
    Query Parameters:
        origin_zip: str - Origin zipcode
    dest_zip: str - Destination zipcode
    mode: str (optional) - Travel mode (default: driving)
        
    Returns:
        JSON response with cached route data or not found message
    """
    try:
        origin_zip = request.args.get('origin_zip')
        dest_zip = request.args.get('dest_zip')
        mode = request.args.get('mode', 'driving')
        
        if not origin_zip or not dest_zip:
            return jsonify({
                'success': False,
                'error': 'origin_zip and dest_zip are required'
            }), 400
        
        # Validate zipcodes
        if not origin_zip.isdigit() or len(origin_zip) != 5:
            return jsonify({
                'success': False,
                'error': 'Invalid origin_zip format. Must be 5 digits.'
            }), 400
        
        if not dest_zip.isdigit() or len(dest_zip) != 5:
            return jsonify({
                'success': False,
                'error': 'Invalid dest_zip format. Must be 5 digits.'
            }), 400
        
        # Get cached route
        cached_route = external_api_service.get_cached_route(origin_zip, dest_zip, mode)
        
        if cached_route:
            return jsonify({
                'success': True,
                'data': cached_route,
                'cached': True,
                'origin_zip': origin_zip,
                'dest_zip': dest_zip,
                'mode': mode
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No cached route data found',
                'origin_zip': origin_zip,
                'dest_zip': dest_zip,
                'mode': mode
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting cached route: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# ============================================================================
# SERVICE STATUS ENDPOINTS
# ============================================================================

@external_api.route('/api/external/status', methods=['GET'])
@cross_origin()
def get_external_api_status():
    """
    Get external API service status and health information.
    
    Returns:
        JSON response with service status
    """
    try:
        status = external_api_service.get_service_status()
        
        return jsonify({
            'success': True,
            'data': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting external API status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get service status'
        }), 500

@external_api.route('/api/external/cache/clear', methods=['POST'])
@cross_origin()
def clear_external_api_cache():
    """
    Clear external API cache.
    
    Body:
        cache_type: str (optional) - Type of cache to clear (all, routes)
        
    Returns:
        JSON response with cache clear results
    """
    try:
        data = request.get_json() or {}
        cache_type = data.get('cache_type', 'all')
        
        result = external_api_service.clear_cache(cache_type)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error clearing external API cache: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear cache'
        }), 500

@external_api.route('/api/external/cache/stats', methods=['GET'])
@cross_origin()
def get_cache_stats():
    """
    Get external API cache statistics.
    
    Returns:
        JSON response with cache statistics
    """
    try:
        stats = external_api_service.get_cache_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get cache statistics'
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@external_api.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors"""
    return jsonify({
        'success': False,
        'error': 'Bad Request',
        'message': 'Invalid request parameters',
        'status_code': 400
    }), 400

@external_api.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    return jsonify({
        'success': False,
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status_code': 404
    }), 404

@external_api.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle 429 Rate Limit Exceeded errors"""
    return jsonify({
        'success': False,
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'status_code': 429
    }), 429

@external_api.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error"""
    logger.error(f"External API internal error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    }), 500
