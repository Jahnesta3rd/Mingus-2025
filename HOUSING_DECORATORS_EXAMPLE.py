#!/usr/bin/env python3
"""
Housing Decorators Usage Examples

This file demonstrates how to use the new housing decorators for API endpoint protection:

1. @require_housing_feature('career_integration') - Requires specific housing feature access
2. @rate_limit_housing_searches() - Rate limits housing searches based on user tier

These decorators follow MINGUS security patterns and integrate with the existing
feature flag service and tier management system.
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from backend.auth.decorators import require_auth, require_housing_feature, rate_limit_housing_searches
from backend.models.database import db
from backend.models.housing_models import HousingSearch, HousingScenario
from backend.services.feature_flag_service import feature_flag_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create example blueprint
housing_examples_api = Blueprint('housing_examples_api', __name__, url_prefix='/api/housing-examples')

# ============================================================================
# EXAMPLE 1: Career Integration Analysis
# ============================================================================

@housing_examples_api.route('/analyze-career-scenarios', methods=['POST'])
@require_auth
@require_housing_feature('career_integration')
@cross_origin()
def analyze_career_scenarios():
    """
    Example endpoint using @require_housing_feature('career_integration')
    
    This endpoint:
    - Requires authentication (@require_auth)
    - Requires career_integration feature (Mid-tier and Professional only)
    - Automatically handles tier restrictions and upgrade prompts
    
    Usage:
    POST /api/housing-examples/analyze-career-scenarios
    Headers: Authorization: Bearer <token>, X-CSRF-Token: <token>
    Body: {"scenario_id": 123, "career_goals": ["remote_work", "promotion"]}
    """
    try:
        data = request.get_json()
        scenario_id = data.get('scenario_id')
        career_goals = data.get('career_goals', [])
        
        # Get current user (automatically available from @require_auth)
        from backend.auth.decorators import get_current_user_id
        user_id = get_current_user_id()
        
        # Business logic here - the decorator ensures user has career_integration access
        analysis_result = {
            'scenario_id': scenario_id,
            'career_goals': career_goals,
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
                }
            },
            'generated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Career scenario analysis completed for user {user_id}")
        
        return jsonify({
            'success': True,
            'data': analysis_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in career scenario analysis: {e}")
        return jsonify({
            'error': 'Analysis failed',
            'message': 'An error occurred while analyzing career scenarios'
        }), 500

# ============================================================================
# EXAMPLE 2: Housing Search with Rate Limiting
# ============================================================================

@housing_examples_api.route('/search-locations', methods=['POST'])
@require_auth
@rate_limit_housing_searches()
@cross_origin()
def search_locations():
    """
    Example endpoint using @rate_limit_housing_searches()
    
    This endpoint:
    - Requires authentication (@require_auth)
    - Rate limits based on user tier (Budget: 5/month, Mid-tier+: unlimited)
    - Automatically handles quota checking and upgrade prompts
    
    Usage:
    POST /api/housing-examples/search-locations
    Headers: Authorization: Bearer <token>, X-CSRF-Token: <token>
    Body: {"max_rent": 2000, "bedrooms": 2, "zip_code": "30309"}
    """
    try:
        data = request.get_json()
        search_criteria = {
            'max_rent': data.get('max_rent'),
            'bedrooms': data.get('bedrooms'),
            'zip_code': data.get('zip_code'),
            'housing_type': data.get('housing_type', 'apartment')
        }
        
        # Get current user (automatically available from @require_auth)
        from backend.auth.decorators import get_current_user_id
        user_id = get_current_user_id()
        
        # Create search record (rate limiting already checked by decorator)
        housing_search = HousingSearch(
            user_id=user_id,
            search_criteria=search_criteria,
            msa_area=search_criteria['zip_code'][:5],
            results_count=0
        )
        
        db.session.add(housing_search)
        db.session.commit()
        
        # Simulate search results
        search_results = {
            'search_id': housing_search.id,
            'criteria': search_criteria,
            'locations': [
                {
                    'id': 1,
                    'address': '123 Main St, Atlanta, GA 30309',
                    'rent': 1850,
                    'bedrooms': 2,
                    'commute_time': 25,
                    'affordability_score': 0.85
                }
            ],
            'total_results': 1
        }
        
        # Update search record
        housing_search.results_count = len(search_results['locations'])
        db.session.commit()
        
        logger.info(f"Housing search completed for user {user_id}, found {len(search_results['locations'])} locations")
        
        return jsonify({
            'success': True,
            'data': search_results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in housing search: {e}")
        return jsonify({
            'error': 'Search failed',
            'message': 'An error occurred while searching for locations'
        }), 500

# ============================================================================
# EXAMPLE 3: Combined Decorators
# ============================================================================

@housing_examples_api.route('/advanced-analysis', methods=['POST'])
@require_auth
@require_housing_feature('career_integration')
@rate_limit_housing_searches()
@cross_origin()
def advanced_analysis():
    """
    Example endpoint using both decorators together
    
    This endpoint:
    - Requires authentication (@require_auth)
    - Requires career_integration feature (Mid-tier and Professional only)
    - Rate limits based on user tier
    - Demonstrates how decorators can be stacked
    
    Usage:
    POST /api/housing-examples/advanced-analysis
    Headers: Authorization: Bearer <token>, X-CSRF-Token: <token>
    Body: {"scenario_id": 123, "search_criteria": {...}}
    """
    try:
        data = request.get_json()
        scenario_id = data.get('scenario_id')
        search_criteria = data.get('search_criteria', {})
        
        # Get current user
        from backend.auth.decorators import get_current_user_id
        user_id = get_current_user_id()
        
        # Both decorators have already validated:
        # 1. User has career_integration feature access
        # 2. User hasn't exceeded their search quota
        
        # Advanced analysis combining career and location data
        analysis_result = {
            'scenario_id': scenario_id,
            'search_criteria': search_criteria,
            'advanced_analysis': {
                'career_location_synergy': 0.78,
                'financial_optimization': 0.82,
                'lifestyle_compatibility': 0.75,
                'growth_potential': 0.88
            },
            'recommendations': [
                'Consider locations within 30 minutes of major business districts',
                'Prioritize areas with strong remote work infrastructure',
                'Evaluate long-term career growth potential'
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Advanced analysis completed for user {user_id}, scenario {scenario_id}")
        
        return jsonify({
            'success': True,
            'data': analysis_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in advanced analysis: {e}")
        return jsonify({
            'error': 'Analysis failed',
            'message': 'An error occurred during advanced analysis'
        }), 500

# ============================================================================
# EXAMPLE 4: Tier Information Endpoint
# ============================================================================

@housing_examples_api.route('/tier-status', methods=['GET'])
@require_auth
@cross_origin()
def get_tier_status():
    """
    Example endpoint showing current tier status and restrictions
    
    This endpoint:
    - Requires authentication (@require_auth)
    - Shows current tier and feature access
    - Provides upgrade information
    
    Usage:
    GET /api/housing-examples/tier-status
    Headers: Authorization: Bearer <token>
    """
    try:
        from backend.auth.decorators import get_current_user_id
        user_id = get_current_user_id()
        
        # Get current tier and features
        user_tier = feature_flag_service.get_user_tier(user_id)
        features = feature_flag_service.get_optimal_location_features(user_id)
        upgrade_options = feature_flag_service.get_tier_upgrade_options(user_id)
        
        # Get current usage
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        searches_this_month = HousingSearch.query.filter(
            HousingSearch.user_id == user_id,
            HousingSearch.created_at >= current_month
        ).count()
        
        scenarios_saved = HousingScenario.query.filter_by(user_id=user_id).count()
        
        tier_status = {
            'current_tier': user_tier.value,
            'tier_name': user_tier.value.replace('_', ' ').title(),
            'features': features,
            'current_usage': {
                'searches_this_month': searches_this_month,
                'scenarios_saved': scenarios_saved
            },
            'quota_status': {
                'searches': {
                    'used': searches_this_month,
                    'limit': features.get('housing_searches_per_month', 0),
                    'unlimited': features.get('housing_searches_per_month', 0) == -1,
                    'remaining': max(0, features.get('housing_searches_per_month', 0) - searches_this_month) 
                        if features.get('housing_searches_per_month', 0) != -1 else -1
                },
                'scenarios': {
                    'used': scenarios_saved,
                    'limit': features.get('scenarios_saved', 0),
                    'unlimited': features.get('scenarios_saved', 0) == -1,
                    'remaining': max(0, features.get('scenarios_saved', 0) - scenarios_saved)
                        if features.get('scenarios_saved', 0) != -1 else -1
                }
            },
            'upgrade_options': upgrade_options
        }
        
        return jsonify({
            'success': True,
            'data': tier_status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting tier status: {e}")
        return jsonify({
            'error': 'Failed to retrieve tier status',
            'message': 'An error occurred while retrieving tier status'
        }), 500

# ============================================================================
# DECORATOR USAGE PATTERNS
# ============================================================================

"""
DECORATOR USAGE PATTERNS:

1. BASIC AUTHENTICATION:
   @require_auth
   def my_endpoint():
       # User is authenticated, access via get_current_user_id()

2. FEATURE ACCESS CONTROL:
   @require_auth
   @require_housing_feature('career_integration')
   def career_endpoint():
       # User has career_integration feature access

3. RATE LIMITING:
   @require_auth
   @rate_limit_housing_searches()
   def search_endpoint():
       # User hasn't exceeded their search quota

4. COMBINED PROTECTION:
   @require_auth
   @require_housing_feature('career_integration')
   @rate_limit_housing_searches()
   def advanced_endpoint():
       # User is authenticated, has feature access, and within quota

5. ERROR RESPONSES:
   - 401: Authentication required
   - 403: Feature not available (with upgrade_required: true)
   - 429: Rate limit exceeded (with current_limit and searches_used)

6. FRONTEND INTEGRATION:
   - Use useTierRestrictions hook for client-side validation
   - Use TierGate component for conditional rendering
   - Handle upgrade prompts and tier information

SECURITY CONSIDERATIONS:
- All decorators require authentication first
- Feature access is checked against user's current tier
- Rate limiting is enforced per user, not per IP
- CSRF tokens are validated for state-changing operations
- All errors include appropriate upgrade prompts
- Logging is included for security monitoring
"""
