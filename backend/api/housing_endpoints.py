#!/usr/bin/env python3
"""
Housing API Endpoints for Mingus Application

Example endpoints demonstrating the use of housing feature decorators:
- @require_housing_feature('career_integration')
- @rate_limit_housing_searches()

These endpoints show how to protect housing-related functionality with proper
tier restrictions and rate limiting following MINGUS security patterns.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from backend.auth.decorators import require_auth, require_housing_feature, rate_limit_housing_searches
from backend.models.database import db
from backend.models.housing_models import HousingSearch, HousingScenario
from backend.services.feature_flag_service import feature_flag_service
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
housing_api = Blueprint('housing_api', __name__, url_prefix='/api/housing')

# ============================================================================
# EXAMPLE ENDPOINTS USING HOUSING DECORATORS
# ============================================================================

@housing_api.route('/analyze-career-scenarios', methods=['POST'])
@require_auth
@require_housing_feature('career_integration')
@cross_origin()
def analyze_career_scenarios():
    """
    POST /api/housing/analyze-career-scenarios
    
    Analyze career scenarios for housing decisions.
    Requires career_integration feature (Mid-tier and Professional only).
    
    Request body:
    {
        "scenario_id": 123,
        "career_goals": ["remote_work", "promotion"],
        "time_horizon": 12
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        scenario_id = data.get('scenario_id')
        career_goals = data.get('career_goals', [])
        time_horizon = data.get('time_horizon', 12)
        
        # Get current user
        from backend.auth.decorators import get_current_user_id
        user_id = get_current_user_id()
        
        # Get scenario
        scenario = HousingScenario.query.filter_by(
            id=scenario_id, 
            user_id=user_id
        ).first()
        
        if not scenario:
            return jsonify({'error': 'Scenario not found'}), 404
        
        # Simulate career analysis
        analysis_result = {
            'scenario_id': scenario_id,
            'career_goals': career_goals,
            'time_horizon_months': time_horizon,
            'analysis': {
                'job_opportunities': {
                    'remote_work_compatibility': 0.85,
                    'promotion_potential': 0.72,
                    'salary_growth_projection': 0.15
                },
                'location_impact': {
                    'commute_optimization': 0.68,
                    'networking_opportunities': 0.91,
                    'cost_of_living_impact': 0.23
                },
                'recommendations': [
                    'Consider locations within 30 minutes of major business districts',
                    'Prioritize areas with strong remote work infrastructure',
                    'Evaluate long-term career growth potential'
                ]
            },
            'generated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Career scenario analysis completed for user {user_id}, scenario {scenario_id}")
        
        return jsonify({
            'success': True,
            'data': analysis_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing career scenarios: {e}")
        return jsonify({
            'error': 'Analysis failed',
            'message': 'An error occurred while analyzing career scenarios'
        }), 500

@housing_api.route('/search-locations', methods=['POST'])
@require_auth
@rate_limit_housing_searches()
@cross_origin()
def search_locations():
    """
    POST /api/housing/search-locations
    
    Search for housing locations with rate limiting based on user tier.
    Budget tier: 5 searches/month, Mid-tier+: unlimited
    
    Request body:
    {
        "max_rent": 2000,
        "bedrooms": 2,
        "commute_time": 30,
        "zip_code": "30309",
        "housing_type": "apartment"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['max_rent', 'bedrooms', 'zip_code']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get current user
        from backend.auth.decorators import get_current_user_id
        user_id = get_current_user_id()
        
        # Create search record
        search_criteria = {
            'max_rent': data.get('max_rent'),
            'bedrooms': data.get('bedrooms'),
            'commute_time': data.get('commute_time', 30),
            'zip_code': data.get('zip_code'),
            'housing_type': data.get('housing_type', 'apartment'),
            'min_bathrooms': data.get('min_bathrooms', 1),
            'max_distance_from_work': data.get('max_distance_from_work', 15)
        }
        
        # Create housing search record
        housing_search = HousingSearch(
            user_id=user_id,
            search_criteria=search_criteria,
            msa_area=data.get('zip_code', '')[:5],  # Use first 5 digits as MSA
            lease_end_date=data.get('lease_end_date'),
            results_count=0  # Will be updated after search
        )
        
        db.session.add(housing_search)
        db.session.commit()
        
        # Simulate location search
        search_results = {
            'search_id': housing_search.id,
            'criteria': search_criteria,
            'locations': [
                {
                    'id': 1,
                    'address': '123 Main St, Atlanta, GA 30309',
                    'rent': 1850,
                    'bedrooms': 2,
                    'bathrooms': 2,
                    'commute_time': 25,
                    'walk_score': 78,
                    'transit_score': 65,
                    'bike_score': 72,
                    'affordability_score': 0.85
                },
                {
                    'id': 2,
                    'address': '456 Oak Ave, Atlanta, GA 30309',
                    'rent': 1950,
                    'bedrooms': 2,
                    'bathrooms': 2,
                    'commute_time': 20,
                    'walk_score': 82,
                    'transit_score': 71,
                    'bike_score': 68,
                    'affordability_score': 0.78
                }
            ],
            'total_results': 2,
            'search_metadata': {
                'search_time_ms': 1250,
                'api_calls_made': 3,
                'cache_hits': 1
            }
        }
        
        # Update search record with results count
        housing_search.results_count = len(search_results['locations'])
        db.session.commit()
        
        # Get user's remaining searches for the month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        searches_this_month = HousingSearch.query.filter(
            HousingSearch.user_id == user_id,
            HousingSearch.created_at >= current_month
        ).count()
        
        features = feature_flag_service.get_optimal_location_features(user_id)
        search_limit = features.get('housing_searches_per_month', 0)
        
        search_results['rate_limit_info'] = {
            'searches_used': searches_this_month,
            'search_limit': search_limit,
            'unlimited': search_limit == -1,
            'remaining_searches': max(0, search_limit - searches_this_month) if search_limit != -1 else -1
        }
        
        logger.info(f"Housing search completed for user {user_id}, found {len(search_results['locations'])} locations")
        
        return jsonify({
            'success': True,
            'data': search_results
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching locations: {e}")
        return jsonify({
            'error': 'Search failed',
            'message': 'An error occurred while searching for locations'
        }), 500

@housing_api.route('/scenarios', methods=['GET'])
@require_auth
@cross_origin()
def get_housing_scenarios():
    """
    GET /api/housing/scenarios
    
    Get user's saved housing scenarios with tier-based limits.
    Budget tier: 3 scenarios, Mid-tier: 10, Professional: unlimited
    """
    try:
        from backend.auth.decorators import get_current_user_id
        user_id = get_current_user_id()
        
        # Get user's scenarios
        scenarios = HousingScenario.query.filter_by(user_id=user_id).order_by(
            HousingScenario.created_at.desc()
        ).all()
        
        # Get tier limits
        features = feature_flag_service.get_optimal_location_features(user_id)
        scenario_limit = features.get('scenarios_saved', 0)
        
        scenarios_data = []
        for scenario in scenarios:
            scenarios_data.append({
                'id': scenario.id,
                'name': scenario.scenario_name,
                'housing_data': scenario.housing_data,
                'commute_data': scenario.commute_data,
                'financial_impact': scenario.financial_impact,
                'career_data': scenario.career_data,
                'is_favorite': scenario.is_favorite,
                'created_at': scenario.created_at.isoformat()
            })
        
        response_data = {
            'scenarios': scenarios_data,
            'total_count': len(scenarios_data),
            'tier_limits': {
                'max_scenarios': scenario_limit,
                'unlimited': scenario_limit == -1,
                'remaining_slots': max(0, scenario_limit - len(scenarios_data)) if scenario_limit != -1 else -1
            }
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting housing scenarios: {e}")
        return jsonify({
            'error': 'Failed to retrieve scenarios',
            'message': 'An error occurred while retrieving housing scenarios'
        }), 500

@housing_api.route('/tier-info', methods=['GET'])
@require_auth
@cross_origin()
def get_housing_tier_info():
    """
    GET /api/housing/tier-info
    
    Get user's current tier information and housing feature access.
    """
    try:
        from backend.auth.decorators import get_current_user_id
        user_id = get_current_user_id()
        
        # Get user's current tier
        user_tier = feature_flag_service.get_user_tier(user_id)
        features = feature_flag_service.get_optimal_location_features(user_id)
        
        # Get upgrade options
        upgrade_options = feature_flag_service.get_tier_upgrade_options(user_id)
        
        tier_info = {
            'current_tier': user_tier.value,
            'tier_name': user_tier.value.replace('_', ' ').title(),
            'features': features,
            'has_optimal_location': feature_flag_service.has_feature_access(
                user_id, 
                feature_flag_service.FeatureFlag.OPTIMAL_LOCATION
            ),
            'upgrade_options': upgrade_options
        }
        
        return jsonify({
            'success': True,
            'data': tier_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting tier info: {e}")
        return jsonify({
            'error': 'Failed to retrieve tier information',
            'message': 'An error occurred while retrieving tier information'
        }), 500

@housing_api.route('/recent-searches', methods=['GET'])
@require_auth
@cross_origin()
def get_recent_searches():
    """
    GET /api/housing/recent-searches
    
    Get user's recent housing searches for dashboard display.
    """
    try:
        from backend.auth.decorators import get_current_user_id
        user_id = get_current_user_id()
        
        # Get recent searches (last 10)
        recent_searches = HousingSearch.query.filter_by(user_id=user_id).order_by(
            HousingSearch.created_at.desc()
        ).limit(10).all()
        
        searches_data = []
        for search in recent_searches:
            searches_data.append({
                'id': search.id,
                'search_criteria': search.search_criteria,
                'results_count': search.results_count,
                'created_at': search.created_at.isoformat(),
                'msa_area': search.msa_area,
                'lease_end_date': search.lease_end_date.isoformat() if search.lease_end_date else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'searches': searches_data,
                'total_count': len(searches_data)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recent searches: {e}")
        return jsonify({
            'error': 'Failed to retrieve recent searches',
            'message': 'An error occurred while retrieving recent searches'
        }), 500
