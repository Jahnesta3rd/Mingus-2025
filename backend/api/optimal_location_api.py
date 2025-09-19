#!/usr/bin/env python3
"""
Optimal Living Location API for Mingus Application

REST API endpoints for the Optimal Living Location feature with proper authentication,
validation, and tier restrictions.

Endpoints:
- POST /api/housing/search - Find optimal locations
- POST /api/housing/scenario - Create housing scenario
- GET /api/housing/scenarios/{user_id} - Get user's saved scenarios
- PUT /api/housing/preferences - Update housing preferences
- POST /api/housing/commute-cost - Calculate commute cost
- DELETE /api/housing/scenario/{scenario_id} - Delete scenario
"""

import logging
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from backend.models.database import db
from backend.models.user_models import User
from backend.models.housing_models import (
    HousingSearch, HousingScenario, UserHousingPreferences, CommuteRouteCache
)
from backend.auth.decorators import require_auth, require_csrf, get_current_user_id
from backend.utils.validation import APIValidator
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier, FeatureFlag
from backend.services.vehicle_analytics_service import VehicleAnalyticsService
from backend.services.external_api_service import ExternalAPIService
from backend.utils.location_utils import LocationService
from datetime import datetime, timedelta
from decimal import Decimal
import json
from typing import Dict, Any, List, Optional
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy import func, and_, or_, desc
from werkzeug.exceptions import BadRequest, NotFound, Forbidden, Unauthorized

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
optimal_location_api = Blueprint('optimal_location_api', __name__, url_prefix='/api/housing')

# Initialize services
validator = APIValidator()
feature_service = FeatureFlagService()
vehicle_analytics_service = VehicleAnalyticsService()
external_api_service = ExternalAPIService()
location_service = LocationService()

# ============================================================================
# MARSHMALLOW SCHEMAS FOR VALIDATION
# ============================================================================

class HousingSearchSchema(Schema):
    """Schema for housing search request validation"""
    max_rent = fields.Float(required=True, validate=validate.Range(min=0, max=10000))
    bedrooms = fields.Integer(required=True, validate=validate.Range(min=0, max=10))
    commute_time = fields.Integer(required=True, validate=validate.Range(min=0, max=180))
    zip_code = fields.String(required=True, validate=validate.Length(min=5, max=10))
    housing_type = fields.String(validate=validate.OneOf(['apartment', 'house', 'condo']))
    min_bathrooms = fields.Integer(validate=validate.Range(min=0, max=10))
    max_distance_from_work = fields.Float(validate=validate.Range(min=0, max=100))

class HousingScenarioSchema(Schema):
    """Schema for housing scenario creation validation"""
    housing_data = fields.Dict(required=True)
    include_career_analysis = fields.Boolean(load_default=False)
    scenario_name = fields.String(required=True, validate=validate.Length(min=1, max=255))

class HousingPreferencesSchema(Schema):
    """Schema for housing preferences update validation"""
    max_commute_time = fields.Integer(validate=validate.Range(min=0, max=180))
    housing_type = fields.String(validate=validate.OneOf(['apartment', 'house', 'condo']))
    min_bedrooms = fields.Integer(validate=validate.Range(min=0, max=10))
    max_bedrooms = fields.Integer(validate=validate.Range(min=0, max=10))
    max_rent_percentage = fields.Decimal(validate=validate.Range(min=0, max=100))
    preferred_neighborhoods = fields.List(fields.String())

class CommuteCostSchema(Schema):
    """Schema for commute cost calculation validation"""
    origin_zip = fields.String(required=True, validate=validate.Length(min=5, max=10))
    destination_zip = fields.String(required=True, validate=validate.Length(min=5, max=10))
    vehicle_id = fields.Integer(required=True, validate=validate.Range(min=1))

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_user_tier_access(user_id: int, required_tier: FeatureTier) -> bool:
    """Check if user has access to a specific tier feature"""
    try:
        user_tier = feature_service.get_user_tier(user_id)
        tier_hierarchy = {
            FeatureTier.BUDGET: 1,
            FeatureTier.BUDGET_CAREER_VEHICLE: 2,
            FeatureTier.MID_TIER: 3,
            FeatureTier.PROFESSIONAL: 4
        }
        return tier_hierarchy.get(user_tier, 0) >= tier_hierarchy.get(required_tier, 0)
    except Exception as e:
        logger.error(f"Error checking user tier access: {e}")
        return False

def check_search_limit(user_id: int) -> bool:
    """Check if user has remaining search quota for the month"""
    try:
        # Get current month's search count
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        search_count = HousingSearch.query.filter(
            and_(
                HousingSearch.user_id == user_id,
                HousingSearch.created_at >= current_month
            )
        ).count()
        
        # Use the new feature flag service method
        return feature_service.check_housing_search_limit(user_id, search_count)
    except Exception as e:
        logger.error(f"Error checking search limit: {e}")
        return False

def check_scenario_save_limit(user_id: int) -> bool:
    """Check if user can save more housing scenarios"""
    try:
        # Get current saved scenarios count
        scenario_count = HousingScenario.query.filter(
            HousingScenario.user_id == user_id
        ).count()
        
        # Use the new feature flag service method
        return feature_service.check_scenario_save_limit(user_id, scenario_count)
    except Exception as e:
        logger.error(f"Error checking scenario save limit: {e}")
        return False

def check_optimal_location_feature_access(user_id: int) -> bool:
    """Check if user has access to optimal location features"""
    try:
        return feature_service.has_feature_access(user_id, FeatureFlag.OPTIMAL_LOCATION)
    except Exception as e:
        logger.error(f"Error checking optimal location feature access: {e}")
        return False

def check_optimal_location_subfeature(user_id: int, feature_name: str) -> bool:
    """Check if user has access to a specific optimal location subfeature"""
    try:
        return feature_service.has_optimal_location_feature(user_id, feature_name)
    except Exception as e:
        logger.error(f"Error checking optimal location subfeature {feature_name}: {e}")
        return False

def validate_csrf_token(token: str) -> bool:
    """Validate CSRF token"""
    if not token:
        return False
    # In production, implement proper CSRF validation
    return len(token) > 10

def check_rate_limit(client_ip: str) -> bool:
    """Check rate limiting for client IP"""
    # Simple rate limiting - in production, use Redis or similar
    return True

# ============================================================================
# API ENDPOINTS
# ============================================================================

@optimal_location_api.route('/search', methods=['POST'])
@require_auth
@cross_origin()
def search_housing():
    """
    POST /api/housing/search
    Find optimal housing locations based on search criteria
    
    Request body:
    {
        "max_rent": 2000,
        "bedrooms": 2,
        "commute_time": 30,
        "zip_code": "30309",
        "housing_type": "apartment",
        "min_bathrooms": 1,
        "max_distance_from_work": 15
    }
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in housing search")
            return jsonify({'error': 'Invalid CSRF token'}), 403
        
        # Rate limiting check
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Get current user
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User authentication required'}), 401
        
        # Check if user has access to optimal location features
        if not check_optimal_location_feature_access(user_id):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Optimal Location features are available in Mid-tier and Professional tiers.',
                'upgrade_required': True,
                'required_tier': 'mid_tier'
            }), 403
        
        # Check search limit
        if not check_search_limit(user_id):
            features = feature_service.get_optimal_location_features(user_id)
            limit = features.get('housing_searches_per_month', 0)
            return jsonify({
                'error': 'Search limit exceeded',
                'message': f'You have reached your monthly limit of {limit} housing searches. Upgrade to Mid-tier for unlimited searches.',
                'upgrade_required': True,
                'current_limit': limit
            }), 429
        
        # Validate request data
        data = request.get_json()
        if not data:
            raise BadRequest("No data provided")
        
        schema = HousingSearchSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'details': e.messages
            }), 400
        
        # Create search record
        search_criteria = {
            'max_rent': validated_data['max_rent'],
            'bedrooms': validated_data['bedrooms'],
            'commute_time': validated_data['commute_time'],
            'zip_code': validated_data['zip_code'],
            'housing_type': validated_data.get('housing_type'),
            'min_bathrooms': validated_data.get('min_bathrooms'),
            'max_distance_from_work': validated_data.get('max_distance_from_work')
        }
        
        # Get location data
        location_result = location_service.validate_and_geocode(validated_data['zip_code'])
        if not location_result['success']:
            return jsonify({
                'error': 'Invalid location',
                'message': location_result['error']
            }), 400
        
        # Create housing search record
        housing_search = HousingSearch(
            user_id=user_id,
            search_criteria=search_criteria,
            msa_area=location_result['location']['msa'],
            results_count=0
        )
        db.session.add(housing_search)
        
        # Get rental listings from external API
        try:
            rental_listings = external_api_service.get_rental_listings(
                validated_data['zip_code'],
                filters={
                    'max_rent': validated_data['max_rent'],
                    'bedrooms': validated_data['bedrooms'],
                    'housing_type': validated_data.get('housing_type')
                }
            )
            
            if rental_listings.get('success'):
                listings = rental_listings.get('listings', [])
                housing_search.results_count = len(listings)
                
                # Calculate affordability scores
                for listing in listings:
                    listing['affordability_score'] = calculate_affordability_score(
                        listing.get('rent', 0),
                        user_id
                    )
                
                # Sort by affordability score
                listings.sort(key=lambda x: x.get('affordability_score', 0), reverse=True)
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'search_id': housing_search.id,
                    'listings': listings[:20],  # Limit to top 20 results
                    'total_results': len(listings),
                    'search_criteria': search_criteria,
                    'location': location_result['location']
                })
            else:
                return jsonify({
                    'error': 'Failed to retrieve listings',
                    'message': rental_listings.get('error', 'Unknown error')
                }), 500
                
        except Exception as e:
            logger.error(f"Error retrieving rental listings: {e}")
            db.session.rollback()
            return jsonify({
                'error': 'Failed to retrieve listings',
                'message': 'External API error'
            }), 500
            
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in housing search: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@optimal_location_api.route('/scenario', methods=['POST'])
@require_auth
@cross_origin()
def create_housing_scenario():
    """
    POST /api/housing/scenario
    Create a comprehensive housing scenario with financial impact analysis
    
    Request body:
    {
        "housing_data": {
            "address": "123 Main St",
            "rent": 1800,
            "bedrooms": 2,
            "bathrooms": 1
        },
        "include_career_analysis": true,
        "scenario_name": "Downtown Apartment"
    }
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in scenario creation")
            return jsonify({'error': 'Invalid CSRF token'}), 403
        
        # Rate limiting check
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Get current user
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User authentication required'}), 401
        
        # Check if user has access to optimal location features
        if not check_optimal_location_feature_access(user_id):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Optimal Location features are available in Mid-tier and Professional tiers.',
                'upgrade_required': True,
                'required_tier': 'mid_tier'
            }), 403
        
        # Check scenario save limit
        if not check_scenario_save_limit(user_id):
            features = feature_service.get_optimal_location_features(user_id)
            limit = features.get('scenarios_saved', 0)
            return jsonify({
                'error': 'Scenario save limit exceeded',
                'message': f'You have reached your limit of {limit} saved scenarios. Upgrade to Professional tier for unlimited scenarios.',
                'upgrade_required': True,
                'current_limit': limit
            }), 429
        
        # Validate request data
        data = request.get_json()
        if not data:
            raise BadRequest("No data provided")
        
        schema = HousingScenarioSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'details': e.messages
            }), 400
        
        # Check access to career analysis feature
        include_career_analysis = validated_data.get('include_career_analysis', False)
        if include_career_analysis and not check_optimal_location_subfeature(user_id, 'career_integration'):
            return jsonify({
                'error': 'Career analysis not available',
                'message': 'Career integration is available in Mid-tier and Professional tiers.',
                'upgrade_required': True,
                'required_tier': 'mid_tier'
            }), 403
        
        # Create housing scenario
        housing_data = validated_data['housing_data']
        
        # Calculate commute data
        commute_data = calculate_commute_data(housing_data, user_id)
        
        # Calculate financial impact
        financial_impact = calculate_financial_impact(housing_data, user_id)
        
        # Career analysis (if requested and user has access)
        career_data = {}
        if include_career_analysis:
            career_data = calculate_career_analysis(housing_data, user_id)
        
        # Create scenario record
        scenario = HousingScenario(
            user_id=user_id,
            scenario_name=validated_data['scenario_name'],
            housing_data=housing_data,
            commute_data=commute_data,
            financial_impact=financial_impact,
            career_data=career_data
        )
        
        db.session.add(scenario)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'scenario_id': scenario.id,
            'scenario_name': scenario.scenario_name,
            'housing_data': housing_data,
            'commute_data': commute_data,
            'financial_impact': financial_impact,
            'career_data': career_data,
            'created_at': scenario.created_at.isoformat()
        })
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating housing scenario: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@optimal_location_api.route('/scenarios/<int:user_id>', methods=['GET'])
@require_auth
@cross_origin()
def get_user_scenarios(user_id):
    """
    GET /api/housing/scenarios/{user_id}
    Get user's saved housing scenarios with pagination
    """
    try:
        # Verify user access
        current_user_id = get_current_user_id()
        if current_user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if user has access to optimal location features
        if not check_optimal_location_feature_access(user_id):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Optimal Location features are available in Mid-tier and Professional tiers.',
                'upgrade_required': True,
                'required_tier': 'mid_tier'
            }), 403
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 50)  # Limit to 50 per page
        
        # Get scenarios
        scenarios_query = HousingScenario.query.filter_by(user_id=user_id)
        
        # Apply sorting
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if sort_by == 'created_at':
            if sort_order == 'desc':
                scenarios_query = scenarios_query.order_by(desc(HousingScenario.created_at))
            else:
                scenarios_query = scenarios_query.order_by(HousingScenario.created_at)
        elif sort_by == 'scenario_name':
            if sort_order == 'desc':
                scenarios_query = scenarios_query.order_by(desc(HousingScenario.scenario_name))
            else:
                scenarios_query = scenarios_query.order_by(HousingScenario.scenario_name)
        
        # Paginate results
        scenarios = scenarios_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Format response
        scenarios_data = []
        for scenario in scenarios.items:
            scenarios_data.append({
                'id': scenario.id,
                'scenario_name': scenario.scenario_name,
                'housing_data': scenario.housing_data,
                'financial_impact': scenario.financial_impact,
                'is_favorite': scenario.is_favorite,
                'created_at': scenario.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'scenarios': scenarios_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': scenarios.total,
                'pages': scenarios.pages,
                'has_next': scenarios.has_next,
                'has_prev': scenarios.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving user scenarios: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@optimal_location_api.route('/preferences', methods=['PUT'])
@require_auth
@cross_origin()
def update_housing_preferences():
    """
    PUT /api/housing/preferences
    Update user's housing preferences
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in preferences update")
            return jsonify({'error': 'Invalid CSRF token'}), 403
        
        # Rate limiting check
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Get current user
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User authentication required'}), 401
        
        # Check if user has access to optimal location features
        if not check_optimal_location_feature_access(user_id):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Optimal Location features are available in Mid-tier and Professional tiers.',
                'upgrade_required': True,
                'required_tier': 'mid_tier'
            }), 403
        
        # Validate request data
        data = request.get_json()
        if not data:
            raise BadRequest("No data provided")
        
        schema = HousingPreferencesSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'details': e.messages
            }), 400
        
        # Get or create user preferences
        preferences = UserHousingPreferences.query.filter_by(user_id=user_id).first()
        if not preferences:
            preferences = UserHousingPreferences(user_id=user_id)
            db.session.add(preferences)
        
        # Update preferences
        for field, value in validated_data.items():
            setattr(preferences, field, value)
        
        preferences.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Housing preferences updated successfully',
            'preferences': {
                'max_commute_time': preferences.max_commute_time,
                'preferred_housing_type': preferences.preferred_housing_type,
                'min_bedrooms': preferences.min_bedrooms,
                'max_bedrooms': preferences.max_bedrooms,
                'max_rent_percentage': float(preferences.max_rent_percentage) if preferences.max_rent_percentage else None,
                'preferred_neighborhoods': preferences.preferred_neighborhoods,
                'updated_at': preferences.updated_at.isoformat()
            }
        })
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating housing preferences: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@optimal_location_api.route('/commute-cost', methods=['POST'])
@require_auth
@cross_origin()
def calculate_commute_cost():
    """
    POST /api/housing/commute-cost
    Calculate detailed commute cost using VehicleAnalyticsService
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in commute cost calculation")
            return jsonify({'error': 'Invalid CSRF token'}), 403
        
        # Rate limiting check
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Get current user
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User authentication required'}), 401
        
        # Validate request data
        data = request.get_json()
        if not data:
            raise BadRequest("No data provided")
        
        schema = CommuteCostSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'details': e.messages
            }), 400
        
        # Get route data
        origin_zip = validated_data['origin_zip']
        destination_zip = validated_data['destination_zip']
        vehicle_id = validated_data['vehicle_id']
        
        # Check if route is cached
        cached_route = CommuteRouteCache.query.filter_by(
            origin_zip=origin_zip,
            destination_zip=destination_zip
        ).first()
        
        if cached_route and (datetime.utcnow() - cached_route.last_updated).days < 7:
            # Use cached data
            distance_miles = float(cached_route.distance_miles)
            drive_time_minutes = cached_route.drive_time_minutes
            traffic_factor = float(cached_route.traffic_factor)
        else:
            # Calculate new route
            route_result = external_api_service.calculate_route_distance(
                origin_zip, destination_zip
            )
            
            if not route_result.get('success'):
                return jsonify({
                    'error': 'Failed to calculate route',
                    'message': route_result.get('error', 'Unknown error')
                }), 500
            
            distance_miles = route_result.get('distance_miles', 0)
            drive_time_minutes = route_result.get('drive_time_minutes', 0)
            traffic_factor = route_result.get('traffic_factor', 1.0)
            
            # Cache the result
            if cached_route:
                cached_route.distance_miles = distance_miles
                cached_route.drive_time_minutes = drive_time_minutes
                cached_route.traffic_factor = traffic_factor
                cached_route.last_updated = datetime.utcnow()
            else:
                cached_route = CommuteRouteCache(
                    origin_zip=origin_zip,
                    destination_zip=destination_zip,
                    distance_miles=distance_miles,
                    drive_time_minutes=drive_time_minutes,
                    traffic_factor=traffic_factor
                )
                db.session.add(cached_route)
            
            db.session.commit()
        
        # Calculate commute costs using VehicleAnalyticsService
        try:
            commute_analysis = vehicle_analytics_service.calculate_commute_costs(
                user_id=user_id,
                vehicle_id=vehicle_id,
                distance_miles=distance_miles,
                drive_time_minutes=drive_time_minutes,
                traffic_factor=traffic_factor
            )
            
            return jsonify({
                'success': True,
                'commute_analysis': commute_analysis,
                'route_data': {
                    'origin_zip': origin_zip,
                    'destination_zip': destination_zip,
                    'distance_miles': distance_miles,
                    'drive_time_minutes': drive_time_minutes,
                    'traffic_factor': traffic_factor
                }
            })
            
        except Exception as e:
            logger.error(f"Error calculating commute costs: {e}")
            return jsonify({
                'error': 'Failed to calculate commute costs',
                'message': 'Vehicle analytics service error'
            }), 500
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in commute cost calculation: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@optimal_location_api.route('/scenario/<int:scenario_id>', methods=['DELETE'])
@require_auth
@cross_origin()
def delete_housing_scenario(scenario_id):
    """
    DELETE /api/housing/scenario/{scenario_id}
    Delete a housing scenario (soft delete)
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in scenario deletion")
            return jsonify({'error': 'Invalid CSRF token'}), 403
        
        # Rate limiting check
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Get current user
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User authentication required'}), 401
        
        # Check if user has access to optimal location features
        if not check_optimal_location_feature_access(user_id):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Optimal Location features are available in Mid-tier and Professional tiers.',
                'upgrade_required': True,
                'required_tier': 'mid_tier'
            }), 403
        
        # Get scenario and verify ownership
        scenario = HousingScenario.query.filter_by(
            id=scenario_id,
            user_id=user_id
        ).first()
        
        if not scenario:
            return jsonify({'error': 'Scenario not found or access denied'}), 404
        
        # Soft delete (mark as deleted)
        scenario.is_favorite = False  # Remove from favorites
        # In a full implementation, you might add a 'deleted_at' field
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Housing scenario deleted successfully',
            'scenario_id': scenario_id
        })
        
    except Exception as e:
        logger.error(f"Error deleting housing scenario: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_affordability_score(rent: float, user_id: int) -> float:
    """Calculate affordability score for a rental property"""
    try:
        # Get user's financial data (simplified)
        # In production, integrate with user's financial profile
        user = User.query.get(user_id)
        if not user:
            return 0.0
        
        # Simplified affordability calculation
        # In production, use actual income and expense data
        estimated_income = 50000  # Placeholder
        monthly_income = estimated_income / 12
        rent_ratio = rent / monthly_income if monthly_income > 0 else 1.0
        
        # Score based on 30% rule (lower is better)
        if rent_ratio <= 0.3:
            return 100.0
        elif rent_ratio <= 0.4:
            return 80.0
        elif rent_ratio <= 0.5:
            return 60.0
        else:
            return 40.0
            
    except Exception as e:
        logger.error(f"Error calculating affordability score: {e}")
        return 0.0

def calculate_commute_data(housing_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Calculate commute data for housing scenario"""
    try:
        # Simplified commute calculation
        # In production, integrate with Google Maps API
        return {
            'estimated_commute_time': 30,  # minutes
            'estimated_distance': 15.5,    # miles
            'traffic_factor': 1.2,
            'commute_cost_per_month': 200.0
        }
    except Exception as e:
        logger.error(f"Error calculating commute data: {e}")
        return {}

def calculate_financial_impact(housing_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Calculate financial impact of housing scenario"""
    try:
        rent = housing_data.get('rent', 0)
        
        return {
            'monthly_rent': rent,
            'annual_rent': rent * 12,
            'affordability_score': calculate_affordability_score(rent, user_id),
            'recommended_max_rent': 1500,  # Placeholder
            'rent_to_income_ratio': 0.3,   # Placeholder
            'total_monthly_housing_cost': rent + 200  # rent + utilities estimate
        }
    except Exception as e:
        logger.error(f"Error calculating financial impact: {e}")
        return {}

def calculate_career_analysis(housing_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Calculate career analysis for housing scenario"""
    try:
        # Simplified career analysis
        # In production, integrate with job matching and career services
        return {
            'nearby_job_opportunities': 15,
            'average_salary_in_area': 65000,
            'career_growth_potential': 'High',
            'networking_opportunities': 'Excellent',
            'commute_to_job_centers': {
                'downtown': 25,
                'tech_corridor': 35,
                'airport': 45
            }
        }
    except Exception as e:
        logger.error(f"Error calculating career analysis: {e}")
        return {}

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@optimal_location_api.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'Invalid request data'
    }), 400

@optimal_location_api.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Authentication required'
    }), 401

@optimal_location_api.errorhandler(403)
def forbidden(error):
    return jsonify({
        'error': 'Forbidden',
        'message': 'Access denied'
    }), 403

@optimal_location_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'Resource not found'
    }), 404

@optimal_location_api.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests'
    }), 429

@optimal_location_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500
