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
from backend.auth.decorators import (
    get_current_jwt_user,
    require_auth,
    require_housing_feature,
    rate_limit_housing_searches,
)
from backend.models.database import db
from backend.models.housing_models import HousingSearch, HousingScenario
from backend.models.housing_profile import HousingProfile
from backend.data.zip_to_msa import ZIP_TO_MSA
from backend.services.external_api_service import external_api_service
from backend.services.feature_flag_service import feature_flag_service, FeatureFlag
from backend.utils.user_profile_context import extract_zip_from_text, resolve_search_zip
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)

EMPTY_LISTINGS_MESSAGE = (
    'No listings found for this location yet. '
    'Try a nearby zip code or check back soon.'
)

# Retired by HRA-03 completion (June 2026). Live listings via ExternalAPIService.


def resolve_msa_code_for_zip(zip_code: str) -> str:
    """Resolve CBSA msa_code from a zip string."""
    digits = extract_zip_from_text(zip_code) or (zip_code[:5] if zip_code else '')
    if not digits:
        return ''
    return ZIP_TO_MSA.get(digits, '') or ''


def _extract_listings_from_api_payload(data: Any) -> List[Any]:
    """Pull listing rows from Rentals.com API payload shapes."""
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ('listings', 'results', 'properties', 'data'):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def _normalize_rental_listing(
    raw: Dict[str, Any],
    resolved_zip: str,
    msa_code: str,
    index: int,
) -> Dict[str, Any]:
    """Map external API listing fields to housing search response shape."""
    city = raw.get('city') or raw.get('City') or ''
    state = raw.get('state') or raw.get('State') or ''
    zip_code = raw.get('zip_code') or raw.get('zip') or raw.get('postal_code') or resolved_zip
    street = raw.get('address') or raw.get('street_address') or raw.get('street') or ''
    address = raw.get('full_address') or raw.get('location')
    if not address and street:
        address = f'{street}, {city}, {state} {zip_code}'.strip(', ')
    price = raw.get('price') or raw.get('rent') or raw.get('monthly_rent') or 0
    listing_id = str(raw.get('id') or raw.get('listing_id') or f'{resolved_zip}-{index + 1}')
    listing_url = raw.get('listing_url') or raw.get('url') or raw.get('link')
    title = raw.get('title') or raw.get('name')
    if not title:
        title = f'{city} Residences #{index + 1}' if city else f'Listing #{index + 1}'

    return {
        'id': listing_id,
        'title': title,
        'address': address or street,
        'location': address or street,
        'city': city,
        'state': state,
        'zip_code': zip_code,
        'price': price,
        'bedrooms': raw.get('bedrooms'),
        'bathrooms': raw.get('bathrooms'),
        'listing_url': listing_url,
        'msa_code': msa_code,
    }

# Create blueprint
housing_api = Blueprint('housing_api', __name__, url_prefix='/api/housing')

# ============================================================================
# EXAMPLE ENDPOINTS USING HOUSING DECORATORS
# ============================================================================

def _housing_profile_complete(hp: HousingProfile) -> bool:
    return (
        hp.housing_type is not None
        and hp.monthly_cost is not None
        and hp.monthly_cost > 0
    )


def _empty_housing_profile_payload() -> Dict[str, Any]:
    return {
        'housing_type': None,
        'monthly_cost': None,
        'zip_or_city': None,
        'has_buy_goal': False,
        'target_price': None,
        'target_timeline_months': None,
        'profile_complete': False,
    }


@housing_api.route('/profile', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_housing_profile():
    """Housing profile read for Snapshot action-card down payment CTA."""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user = get_current_jwt_user()
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    hp = HousingProfile.query.filter_by(user_id=user.id).first()
    if not hp:
        return jsonify({
            'has_buy_goal': False,
            'target_price': None,
            'target_timeline_months': None,
            'down_payment_saved': 0,
        }), 200

    return jsonify({
        'has_buy_goal': bool(hp.has_buy_goal),
        'target_price': hp.target_price,
        'target_timeline_months': hp.target_timeline_months,
        'down_payment_saved': float(hp.down_payment_saved or 0),
    }), 200


@housing_api.route('/profile-summary', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def profile_summary():
    """Lightweight housing_profile read for dashboard Housing Check-in card."""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user = get_current_jwt_user()
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    hp = HousingProfile.query.filter_by(user_id=user.id).first()
    if not hp:
        return jsonify({'success': True, 'profile': _empty_housing_profile_payload()}), 200

    return jsonify({
        'success': True,
        'profile': {
            'housing_type': hp.housing_type,
            'monthly_cost': hp.monthly_cost,
            'zip_or_city': hp.zip_or_city,
            'has_buy_goal': bool(hp.has_buy_goal),
            'target_price': hp.target_price,
            'target_timeline_months': hp.target_timeline_months,
            'profile_complete': _housing_profile_complete(hp),
        },
    }), 200


@housing_api.route('/analyze-career-scenarios', methods=['POST', 'OPTIONS'])
@cross_origin()
@require_auth
@require_housing_feature('career_integration')
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
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        scenario_id = data.get('scenario_id')
        career_goals = data.get('career_goals', [])
        time_horizon = data.get('time_horizon', 12)
        
        # Get current user
        from backend.auth.decorators import get_current_user_id, get_current_user_db_id
        user_id = get_current_user_id()
        db_user_id = get_current_user_db_id()
        if db_user_id is None:
            return jsonify({'error': 'User not found'}), 404
        
        # Get scenario
        scenario = HousingScenario.query.filter_by(
            id=scenario_id, 
            user_id=db_user_id
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

@housing_api.route('/search-locations', methods=['POST', 'OPTIONS'])
@cross_origin()
@require_auth
@rate_limit_housing_searches()
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
        from backend.auth.decorators import get_current_user_id, get_current_user_db_id
        user_id = get_current_user_id()
        db_user_id = get_current_user_db_id()
        if db_user_id is None:
            return jsonify({'error': 'User not found'}), 404
        
        request_zip = data.get('zip_code')
        request_zip_stripped = (request_zip or '').strip()
        if request_zip_stripped and len(request_zip_stripped) < 5:
            return jsonify({'error': 'Please enter a valid 5-digit zip code.'}), 422

        zip_resolution = resolve_search_zip(db_user_id, request_zip, db.session)
        if zip_resolution is None:
            return jsonify({
                'error': (
                    'Location required. Add a zip code to your profile or enter one above.'
                ),
                'code': 'ZIP_REQUIRED',
            }), 400

        resolved_zip = zip_resolution.zip_code
        zip_source = zip_resolution.source
        msa_code = resolve_msa_code_for_zip(resolved_zip)
        logger.info(
            'housing_search zip=%s msa=%s source=%s',
            resolved_zip,
            msa_code,
            zip_source,
        )

        # Create search record
        search_criteria = {
            'max_rent': data.get('max_rent'),
            'bedrooms': data.get('bedrooms'),
            'commute_time': data.get('commute_time', 30),
            'zip_code': resolved_zip,
            'housing_type': data.get('housing_type', 'apartment'),
            'min_bathrooms': data.get('min_bathrooms', 1),
            'max_distance_from_work': data.get('max_distance_from_work', 15)
        }
        
        # Create housing search record
        housing_search = HousingSearch(
            user_id=db_user_id,
            search_criteria=search_criteria,
            msa_area=msa_code or resolved_zip[:5],
            lease_end_date=data.get('lease_end_date'),
            results_count=0  # Will be updated after search
        )
        
        db.session.add(housing_search)
        db.session.commit()

        rental_filters = {
            'price_max': search_criteria.get('max_rent'),
            'bedrooms': search_criteria.get('bedrooms'),
            'bathrooms': search_criteria.get('min_bathrooms'),
            'property_type': search_criteria.get('housing_type'),
            'limit': 20,
        }

        listings: List[Dict[str, Any]] = []
        try:
            api_result = external_api_service.get_rental_listings(
                resolved_zip,
                rental_filters,
            )
            if api_result.get('success'):
                raw_listings = _extract_listings_from_api_payload(api_result.get('data'))
                listings = [
                    _normalize_rental_listing(item, resolved_zip, msa_code, i)
                    for i, item in enumerate(raw_listings)
                    if isinstance(item, dict)
                ]
            else:
                logger.warning(
                    'ExternalAPIService.get_rental_listings returned no success: %s',
                    api_result.get('error'),
                )
        except Exception as e:
            logger.error('ExternalAPIService.get_rental_listings failed: %s', e)
            listings = []

        search_results = {
            'search_id': housing_search.id,
            'locations': listings,
            'results': listings,
            'total_results': len(listings),
            'search_criteria': search_criteria,
            'zip_resolved': resolved_zip,
            'msa_code': msa_code,
            'zip_source': zip_source,
        }

        if not listings:
            search_results['message'] = EMPTY_LISTINGS_MESSAGE
            search_results['beta_notice'] = True

        housing_search.results_count = len(listings)
        db.session.commit()
        
        # Get user's remaining searches for the month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        searches_this_month = HousingSearch.query.filter(
            HousingSearch.user_id == db_user_id,
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
        print(f"Error in search_locations: {e}")
        return jsonify({
            'success': True,
            'data': {
                'search_id': None,
                'criteria': {},
                'locations': [],
                'total_results': 0,
                'search_metadata': {},
                'rate_limit_info': {}
            }
        }), 200

@housing_api.route('/scenarios', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_housing_scenarios():
    """
    GET /api/housing/scenarios
    
    Get user's saved housing scenarios with tier-based limits.
    Budget tier: 3 scenarios, Mid-tier: 10, Professional: unlimited
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        from backend.auth.decorators import get_current_user_id, get_current_user_db_id
        user_id = get_current_user_id()
        db_user_id = get_current_user_db_id()
        if db_user_id is None:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's scenarios
        scenarios = HousingScenario.query.filter_by(user_id=db_user_id).order_by(
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
        print(f"Error in get_housing_scenarios: {e}")
        return jsonify({
            'success': True,
            'data': {
                'scenarios': [],
                'total_count': 0,
                'tier_limits': {
                    'max_scenarios': 0,
                    'unlimited': False,
                    'remaining_slots': 0
                }
            }
        }), 200

@housing_api.route('/tier-info', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_housing_tier_info():
    """
    GET /api/housing/tier-info
    
    Get user's current tier information and housing feature access.
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
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
                FeatureFlag.OPTIMAL_LOCATION
            ),
            'upgrade_options': upgrade_options
        }
        
        return jsonify({
            'success': True,
            'data': tier_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting tier info: {e}")
        print(f"Error in get_housing_tier_info: {e}")
        return jsonify({
            'success': True,
            'data': {
                'current_tier': 'budget',
                'tier_name': 'Budget',
                'features': {},
                'has_optimal_location': False,
                'upgrade_options': []
            }
        }), 200

@housing_api.route('/recent-searches', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_recent_searches():
    """
    GET /api/housing/recent-searches
    
    Get user's recent housing searches for dashboard display.
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        from backend.auth.decorators import get_current_user_id, get_current_user_db_id
        user_id = get_current_user_id()
        db_user_id = get_current_user_db_id()
        if db_user_id is None:
            return jsonify({'error': 'User not found'}), 404
        
        # Get recent searches (last 10)
        recent_searches = HousingSearch.query.filter_by(user_id=db_user_id).order_by(
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
        print(f"Error in get_recent_searches: {e}")
        return jsonify({
            'success': True,
            'data': {
                'searches': [],
                'total_count': 0
            }
        }), 200
