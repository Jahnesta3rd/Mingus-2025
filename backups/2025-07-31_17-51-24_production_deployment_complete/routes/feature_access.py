"""
Feature Access Routes

This module provides routes for:
- Feature access checking and management
- Trial offer activation
- Subscription upgrade flows
- Educational content delivery
- Graceful feature degradation
"""

import logging
from flask import Blueprint, request, jsonify, session, current_app
from functools import wraps
from typing import Dict, Any
from backend.middleware.auth import require_auth
from backend.middleware.feature_access_middleware import require_feature_access, require_subscription_tier
from backend.services.enhanced_feature_access_service import EnhancedFeatureAccessService

logger = logging.getLogger(__name__)

# Create blueprint
feature_access_bp = Blueprint('feature_access', __name__, url_prefix='/api/features')

def handle_api_errors(f):
    """Decorator to handle API errors consistently"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': 'internal_error',
                'message': 'Internal server error'
            }), 500
    return decorated_function

@feature_access_bp.route('/check-access/<feature_id>', methods=['GET'])
@require_auth
@handle_api_errors
def check_feature_access(feature_id: str):
    """Check if user has access to a specific feature"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'authentication_required',
                'message': 'Authentication required'
            }), 401
        
        # Get feature access service
        feature_service = current_app.feature_access_service
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'service_unavailable',
                'message': 'Feature access service unavailable'
            }), 503
        
        # Check feature access
        access_result = feature_service.check_feature_access(
            user_id=str(user_id),
            feature_id=feature_id,
            context={'endpoint': request.endpoint, 'method': request.method}
        )
        
        # Return comprehensive access result
        return jsonify({
            'success': True,
            'feature_id': feature_id,
            'has_access': access_result.has_access,
            'reason': access_result.reason,
            'current_tier': access_result.current_tier,
            'required_tier': access_result.required_tier,
            'current_usage': access_result.current_usage,
            'usage_limits': access_result.usage_limits,
            'upgrade_required': access_result.upgrade_required,
            'trial_available': access_result.trial_available,
            'educational_content': access_result.educational_content,
            'alternative_suggestions': access_result.alternative_suggestions,
            'upgrade_benefits': access_result.upgrade_benefits,
            'trial_offer': access_result.trial_offer,
            'grace_period_remaining': access_result.grace_period_remaining
        })
        
    except Exception as e:
        logger.error(f"Error checking feature access: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500

@feature_access_bp.route('/summary', methods=['GET'])
@require_auth
@handle_api_errors
def get_feature_summary():
    """Get comprehensive feature summary for user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'authentication_required',
                'message': 'Authentication required'
            }), 401
        
        # Get feature access service
        feature_service = current_app.feature_access_service
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'service_unavailable',
                'message': 'Feature access service unavailable'
            }), 503
        
        # Get feature summary
        summary = feature_service.get_user_feature_summary(str(user_id))
        
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting feature summary: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500

@feature_access_bp.route('/trial/start/<feature_id>', methods=['POST'])
@require_auth
@handle_api_errors
def start_feature_trial(feature_id: str):
    """Start a trial for a premium feature"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'authentication_required',
                'message': 'Authentication required'
            }), 401
        
        # Get feature access service
        feature_service = current_app.feature_access_service
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'service_unavailable',
                'message': 'Feature access service unavailable'
            }), 503
        
        # Start trial
        result = feature_service.start_feature_trial(str(user_id), feature_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting feature trial: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500

@feature_access_bp.route('/trial/status/<feature_id>', methods=['GET'])
@require_auth
@handle_api_errors
def get_trial_status(feature_id: str):
    """Get trial status for a feature"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'authentication_required',
                'message': 'Authentication required'
            }), 401
        
        # Get feature access service
        feature_service = current_app.feature_access_service
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'service_unavailable',
                'message': 'Feature access service unavailable'
            }), 503
        
        # Check trial status
        trial_status = feature_service._check_trial_status(str(user_id), feature_id)
        
        return jsonify({
            'success': True,
            'feature_id': feature_id,
            'has_used_trial': trial_status['has_used_trial'],
            'trial_start': trial_status['trial_start'],
            'trial_end': trial_status['trial_end']
        })
        
    except Exception as e:
        logger.error(f"Error getting trial status: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500

@feature_access_bp.route('/upgrade/pricing', methods=['GET'])
@require_auth
@handle_api_errors
def get_upgrade_pricing():
    """Get upgrade pricing information"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'authentication_required',
                'message': 'Authentication required'
            }), 401
        
        # Get feature access service
        feature_service = current_app.feature_access_service
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'service_unavailable',
                'message': 'Feature access service unavailable'
            }), 503
        
        # Get user subscription
        subscription = feature_service._get_user_subscription(str(user_id))
        if not subscription:
            return jsonify({
                'success': False,
                'error': 'no_subscription',
                'message': 'No active subscription found'
            }), 404
        
        current_tier = subscription.get('tier', 'budget')
        tier_config = feature_service.tier_configs.get(current_tier, {})
        
        return jsonify({
            'success': True,
            'current_tier': current_tier,
            'current_tier_name': tier_config.get('name', 'Unknown'),
            'current_price': tier_config.get('price', 0),
            'upgrade_path': tier_config.get('upgrade_path'),
            'upgrade_price': tier_config.get('upgrade_price'),
            'all_tiers': feature_service.tier_configs
        })
        
    except Exception as e:
        logger.error(f"Error getting upgrade pricing: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500

@feature_access_bp.route('/educational-content/<category>', methods=['GET'])
@require_auth
@handle_api_errors
def get_educational_content(category: str):
    """Get educational content for a feature category"""
    try:
        # Get feature access service
        feature_service = current_app.feature_access_service
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'service_unavailable',
                'message': 'Feature access service unavailable'
            }), 503
        
        # Get educational content
        content = feature_service._get_educational_content(category)
        
        return jsonify({
            'success': True,
            'category': category,
            'content': content
        })
        
    except Exception as e:
        logger.error(f"Error getting educational content: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500

@feature_access_bp.route('/usage/<feature_id>', methods=['GET'])
@require_auth
@handle_api_errors
def get_feature_usage(feature_id: str):
    """Get current usage for a feature"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'authentication_required',
                'message': 'Authentication required'
            }), 401
        
        # Get feature access service
        feature_service = current_app.feature_access_service
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'service_unavailable',
                'message': 'Feature access service unavailable'
            }), 503
        
        # Get user subscription
        subscription = feature_service._get_user_subscription(str(user_id))
        if not subscription:
            return jsonify({
                'success': False,
                'error': 'no_subscription',
                'message': 'No active subscription found'
            }), 404
        
        current_tier = subscription.get('tier', 'budget')
        
        # Get usage information
        usage_check = feature_service._check_usage_limits(str(user_id), feature_id, current_tier)
        
        return jsonify({
            'success': True,
            'feature_id': feature_id,
            'current_tier': current_tier,
            'current_usage': usage_check['current_usage'],
            'usage_limits': usage_check['usage_limits'],
            'within_limits': usage_check['within_limits'],
            'exceeded_limits': usage_check['exceeded_limits']
        })
        
    except Exception as e:
        logger.error(f"Error getting feature usage: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500

@feature_access_bp.route('/graceful-degradation/<feature_id>', methods=['GET'])
@require_auth
@handle_api_errors
def get_graceful_degradation_info(feature_id: str):
    """Get graceful degradation information for a feature"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'authentication_required',
                'message': 'Authentication required'
            }), 401
        
        # Get feature access service
        feature_service = current_app.feature_access_service
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'service_unavailable',
                'message': 'Feature access service unavailable'
            }), 503
        
        # Check feature access
        access_result = feature_service.check_feature_access(
            user_id=str(user_id),
            feature_id=feature_id,
            context={'endpoint': request.endpoint, 'method': request.method}
        )
        
        # Create graceful degradation response
        degradation_info = {
            'success': True,
            'feature_id': feature_id,
            'has_access': access_result.has_access,
            'reason': access_result.reason,
            'current_tier': access_result.current_tier,
            'required_tier': access_result.required_tier,
            'upgrade_required': access_result.upgrade_required,
            'trial_available': access_result.trial_available,
            'educational_content': access_result.educational_content,
            'alternative_suggestions': access_result.alternative_suggestions,
            'upgrade_benefits': access_result.upgrade_benefits,
            'trial_offer': access_result.trial_offer,
            'grace_period_remaining': access_result.grace_period_remaining,
            'degradation_message': _create_degradation_message(access_result),
            'alternative_features': _get_alternative_features(feature_id, access_result.current_tier),
            'upgrade_path': _get_upgrade_path(access_result.current_tier)
        }
        
        return jsonify(degradation_info)
        
    except Exception as e:
        logger.error(f"Error getting graceful degradation info: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500

def _create_degradation_message(access_result) -> str:
    """Create a user-friendly degradation message"""
    if access_result.reason == 'no_subscription':
        return "This feature requires a subscription. Start your journey with MINGUS today!"
    
    elif access_result.reason == 'upgrade_required':
        return f"This feature is available with {access_result.required_tier} tier or higher. Upgrade to unlock premium features!"
    
    elif access_result.reason == 'usage_limit_exceeded':
        return "You've reached your monthly limit for this feature. Upgrade for unlimited access!"
    
    else:
        return "This feature is not available with your current plan. Consider upgrading for more features!"

def _get_alternative_features(feature_id: str, current_tier: str) -> list:
    """Get alternative features available to the user"""
    alternatives = {
        'health_analytics': ['health_checkin', 'basic_health_tracking'],
        'ai_insights': ['basic_calculators', 'educational_content'],
        'custom_reports': ['standard_reports', 'report_templates'],
        'data_export': ['data_backup', 'manual_export'],
        'api_access': ['web_interface', 'integration_templates']
    }
    
    return alternatives.get(feature_id, [])

def _get_upgrade_path(current_tier: str) -> dict:
    """Get upgrade path information"""
    upgrade_paths = {
        'budget': {
            'next_tier': 'mid_tier',
            'price': 35.00,
            'benefits': [
                'Unlimited health check-ins',
                'Advanced AI insights',
                'Career risk management',
                'Priority support'
            ]
        },
        'mid_tier': {
            'next_tier': 'professional',
            'price': 75.00,
            'benefits': [
                'Unlimited access to all features',
                'API access',
                'Dedicated account manager',
                'Team management'
            ]
        }
    }
    
    return upgrade_paths.get(current_tier, {})

# Example protected routes with feature access control

@feature_access_bp.route('/health/checkin', methods=['POST'])
@require_auth
@require_feature_access('health_checkin')
@handle_api_errors
def submit_health_checkin():
    """Submit health check-in (requires health_checkin feature access)"""
    try:
        # This route is protected by the require_feature_access decorator
        # If access is denied, the decorator will return an appropriate response
        
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Process health check-in
        # ... implementation here ...
        
        return jsonify({
            'success': True,
            'message': 'Health check-in submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error submitting health check-in: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500

@feature_access_bp.route('/ai/insights', methods=['POST'])
@require_auth
@require_feature_access('ai_insights')
@handle_api_errors
def generate_ai_insights():
    """Generate AI insights (requires ai_insights feature access)"""
    try:
        # This route is protected by the require_feature_access decorator
        # If access is denied, the decorator will return an appropriate response
        
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Generate AI insights
        # ... implementation here ...
        
        return jsonify({
            'success': True,
            'message': 'AI insights generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating AI insights: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500

@feature_access_bp.route('/financial/reports', methods=['POST'])
@require_auth
@require_feature_access('financial_reports')
@handle_api_errors
def generate_financial_report():
    """Generate financial report (requires financial_reports feature access)"""
    try:
        # This route is protected by the require_feature_access decorator
        # If access is denied, the decorator will return an appropriate response
        
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Generate financial report
        # ... implementation here ...
        
        return jsonify({
            'success': True,
            'message': 'Financial report generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating financial report: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500

@feature_access_bp.route('/career/risk-assessment', methods=['POST'])
@require_auth
@require_subscription_tier('mid_tier')
@handle_api_errors
def perform_career_risk_assessment():
    """Perform career risk assessment (requires mid_tier or higher)"""
    try:
        # This route is protected by the require_subscription_tier decorator
        # If tier is insufficient, the decorator will return an appropriate response
        
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Perform career risk assessment
        # ... implementation here ...
        
        return jsonify({
            'success': True,
            'message': 'Career risk assessment completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error performing career risk assessment: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500 