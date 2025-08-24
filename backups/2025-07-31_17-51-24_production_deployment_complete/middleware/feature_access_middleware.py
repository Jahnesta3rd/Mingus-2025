"""
Feature Access Middleware

This middleware provides automatic feature access control with:
- Subscription gating for all protected features
- Graceful feature degradation with clear messaging
- Automatic upgrade prompts and trial offers
- Educational content and alternative suggestions
"""

import logging
import json
from functools import wraps
from flask import request, jsonify, current_app, session
from typing import Dict, Any, Optional
from backend.services.enhanced_feature_access_service import EnhancedFeatureAccessService, AccessResult

logger = logging.getLogger(__name__)

class FeatureAccessMiddleware:
    """Middleware for automatic feature access control"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with the Flask app"""
        self.app = app
        
        # Register before_request handler
        app.before_request(self.before_request)
        
        # Register after_request handler
        app.after_request(self.after_request)
        
        # Register error handlers
        app.register_error_handler(403, self.handle_feature_access_denied)
        app.register_error_handler(402, self.handle_payment_required)
    
    def before_request(self):
        """Handle requests before they reach the route"""
        # Check if this is a feature-protected route
        if self._is_feature_protected_route(request.endpoint):
            self._check_feature_access()
    
    def after_request(self, response):
        """Handle responses after they're generated"""
        # Add feature access headers if needed
        if hasattr(request, 'feature_access_result'):
            self._add_feature_access_headers(response, request.feature_access_result)
        
        return response
    
    def _is_feature_protected_route(self, endpoint: str) -> bool:
        """Check if the route requires feature access control"""
        if not endpoint:
            return False
        
        # Define protected route patterns
        protected_patterns = [
            'health.checkin',
            'health.analytics',
            'health.dashboard',
            'financial.reports',
            'financial.forecasting',
            'ai.insights',
            'ai.analytics',
            'career.risk',
            'career.management',
            'data.export',
            'api.access',
            'support.priority'
        ]
        
        return any(pattern in endpoint for pattern in protected_patterns)
    
    def _check_feature_access(self):
        """Check feature access for the current request"""
        try:
            # Get user ID from session
            user_id = session.get('user_id')
            if not user_id:
                return  # Let auth middleware handle this
            
            # Get feature ID from route
            feature_id = self._extract_feature_id_from_route(request.endpoint)
            if not feature_id:
                return  # Not a feature-specific route
            
            # Get feature access service
            feature_service = self._get_feature_service()
            if not feature_service:
                return
            
            # Check feature access
            access_result = feature_service.check_feature_access(
                user_id=str(user_id),
                feature_id=feature_id,
                context={'endpoint': request.endpoint, 'method': request.method}
            )
            
            # Store result for after_request
            request.feature_access_result = access_result
            
            # Handle access denied
            if not access_result.has_access:
                self._handle_access_denied(access_result)
            
            # Track usage if access granted
            elif access_result.reason == 'access_granted':
                feature_service.track_feature_usage(
                    user_id=str(user_id),
                    feature_id=feature_id,
                    context={'endpoint': request.endpoint, 'method': request.method}
                )
                
        except Exception as e:
            logger.error(f"Error in feature access middleware: {e}")
    
    def _extract_feature_id_from_route(self, endpoint: str) -> Optional[str]:
        """Extract feature ID from route endpoint"""
        if not endpoint:
            return None
        
        # Map endpoints to feature IDs
        endpoint_to_feature = {
            'health.checkin': 'health_checkin',
            'health.analytics': 'health_analytics',
            'health.dashboard': 'health_checkin',
            'financial.reports': 'financial_reports',
            'financial.forecasting': 'cash_flow_forecasting',
            'ai.insights': 'ai_insights',
            'ai.analytics': 'ai_insights',
            'career.risk': 'career_risk_management',
            'career.management': 'career_risk_management',
            'data.export': 'data_export',
            'api.access': 'api_access',
            'support.priority': 'priority_support'
        }
        
        # Find matching endpoint
        for pattern, feature_id in endpoint_to_feature.items():
            if pattern in endpoint:
                return feature_id
        
        return None
    
    def _get_feature_service(self) -> Optional[EnhancedFeatureAccessService]:
        """Get the feature access service"""
        try:
            if hasattr(current_app, 'feature_access_service'):
                return current_app.feature_access_service
            
            # Create service if not exists
            from backend.config import Config
            config = Config()
            
            service = EnhancedFeatureAccessService(
                db_session=current_app.db.session,
                config=config.FEATURE_ACCESS_CONFIG
            )
            
            current_app.feature_access_service = service
            return service
            
        except Exception as e:
            logger.error(f"Error getting feature service: {e}")
            return None
    
    def _handle_access_denied(self, access_result: AccessResult):
        """Handle feature access denied"""
        try:
            # Create response based on access result
            if access_result.reason == 'no_subscription':
                self._create_subscription_required_response(access_result)
            elif access_result.reason == 'upgrade_required':
                self._create_upgrade_required_response(access_result)
            elif access_result.reason == 'usage_limit_exceeded':
                self._create_usage_limit_response(access_result)
            else:
                self._create_generic_access_denied_response(access_result)
                
        except Exception as e:
            logger.error(f"Error handling access denied: {e}")
            self._create_generic_access_denied_response(access_result)
    
    def _create_subscription_required_response(self, access_result: AccessResult):
        """Create response for users without subscription"""
        response_data = {
            'success': False,
            'error': 'subscription_required',
            'message': 'A subscription is required to access this feature',
            'current_tier': access_result.current_tier,
            'required_tier': access_result.required_tier,
            'upgrade_required': True,
            'educational_content': access_result.educational_content,
            'alternative_suggestions': access_result.alternative_suggestions,
            'upgrade_benefits': access_result.upgrade_benefits,
            'trial_offer': access_result.trial_offer,
            'grace_period_remaining': access_result.grace_period_remaining
        }
        
        # Set response
        request.feature_access_response = jsonify(response_data), 402
    
    def _create_upgrade_required_response(self, access_result: AccessResult):
        """Create response for users who need to upgrade"""
        response_data = {
            'success': False,
            'error': 'upgrade_required',
            'message': f'This feature requires {access_result.required_tier} tier or higher',
            'current_tier': access_result.current_tier,
            'required_tier': access_result.required_tier,
            'upgrade_required': True,
            'educational_content': access_result.educational_content,
            'alternative_suggestions': access_result.alternative_suggestions,
            'upgrade_benefits': access_result.upgrade_benefits,
            'trial_offer': access_result.trial_offer,
            'grace_period_remaining': access_result.grace_period_remaining
        }
        
        # Set response
        request.feature_access_response = jsonify(response_data), 402
    
    def _create_usage_limit_response(self, access_result: AccessResult):
        """Create response for users who exceeded usage limits"""
        response_data = {
            'success': False,
            'error': 'usage_limit_exceeded',
            'message': 'You have reached your monthly usage limit for this feature',
            'current_tier': access_result.current_tier,
            'required_tier': access_result.required_tier,
            'current_usage': access_result.current_usage,
            'usage_limits': access_result.usage_limits,
            'upgrade_required': True,
            'educational_content': access_result.educational_content,
            'alternative_suggestions': access_result.alternative_suggestions,
            'upgrade_benefits': access_result.upgrade_benefits,
            'trial_offer': access_result.trial_offer,
            'grace_period_remaining': access_result.grace_period_remaining
        }
        
        # Set response
        request.feature_access_response = jsonify(response_data), 402
    
    def _create_generic_access_denied_response(self, access_result: AccessResult):
        """Create generic access denied response"""
        response_data = {
            'success': False,
            'error': 'access_denied',
            'message': 'Access to this feature is not available',
            'current_tier': access_result.current_tier,
            'required_tier': access_result.required_tier,
            'upgrade_required': access_result.upgrade_required,
            'educational_content': access_result.educational_content,
            'alternative_suggestions': access_result.alternative_suggestions,
            'upgrade_benefits': access_result.upgrade_benefits,
            'trial_offer': access_result.trial_offer
        }
        
        # Set response
        request.feature_access_response = jsonify(response_data), 403
    
    def _add_feature_access_headers(self, response, access_result: AccessResult):
        """Add feature access headers to response"""
        try:
            response.headers['X-Feature-Access'] = 'granted' if access_result.has_access else 'denied'
            response.headers['X-Current-Tier'] = access_result.current_tier
            response.headers['X-Required-Tier'] = access_result.required_tier
            
            if access_result.upgrade_required:
                response.headers['X-Upgrade-Required'] = 'true'
            
            if access_result.trial_available:
                response.headers['X-Trial-Available'] = 'true'
                
        except Exception as e:
            logger.error(f"Error adding feature access headers: {e}")
    
    def handle_feature_access_denied(self, error):
        """Handle 403 feature access denied errors"""
        if hasattr(request, 'feature_access_response'):
            return request.feature_access_response
        
        return jsonify({
            'success': False,
            'error': 'access_denied',
            'message': 'Access to this feature is not available'
        }), 403
    
    def handle_payment_required(self, error):
        """Handle 402 payment required errors"""
        if hasattr(request, 'feature_access_response'):
            return request.feature_access_response
        
        return jsonify({
            'success': False,
            'error': 'payment_required',
            'message': 'A subscription is required to access this feature'
        }), 402

def require_feature_access(feature_id: str):
    """Decorator to require specific feature access"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Get user ID from session
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
                
                if not access_result.has_access:
                    # Create appropriate response based on reason
                    if access_result.reason == 'no_subscription':
                        return jsonify({
                            'success': False,
                            'error': 'subscription_required',
                            'message': 'A subscription is required to access this feature',
                            'current_tier': access_result.current_tier,
                            'required_tier': access_result.required_tier,
                            'upgrade_required': True,
                            'educational_content': access_result.educational_content,
                            'alternative_suggestions': access_result.alternative_suggestions,
                            'upgrade_benefits': access_result.upgrade_benefits,
                            'trial_offer': access_result.trial_offer
                        }), 402
                    
                    elif access_result.reason == 'upgrade_required':
                        return jsonify({
                            'success': False,
                            'error': 'upgrade_required',
                            'message': f'This feature requires {access_result.required_tier} tier or higher',
                            'current_tier': access_result.current_tier,
                            'required_tier': access_result.required_tier,
                            'upgrade_required': True,
                            'educational_content': access_result.educational_content,
                            'alternative_suggestions': access_result.alternative_suggestions,
                            'upgrade_benefits': access_result.upgrade_benefits,
                            'trial_offer': access_result.trial_offer
                        }), 402
                    
                    elif access_result.reason == 'usage_limit_exceeded':
                        return jsonify({
                            'success': False,
                            'error': 'usage_limit_exceeded',
                            'message': 'You have reached your monthly usage limit for this feature',
                            'current_tier': access_result.current_tier,
                            'required_tier': access_result.required_tier,
                            'current_usage': access_result.current_usage,
                            'usage_limits': access_result.usage_limits,
                            'upgrade_required': True,
                            'educational_content': access_result.educational_content,
                            'alternative_suggestions': access_result.alternative_suggestions,
                            'upgrade_benefits': access_result.upgrade_benefits,
                            'trial_offer': access_result.trial_offer
                        }), 402
                    
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'access_denied',
                            'message': 'Access to this feature is not available',
                            'current_tier': access_result.current_tier,
                            'required_tier': access_result.required_tier,
                            'upgrade_required': access_result.upgrade_required,
                            'educational_content': access_result.educational_content,
                            'alternative_suggestions': access_result.alternative_suggestions,
                            'upgrade_benefits': access_result.upgrade_benefits,
                            'trial_offer': access_result.trial_offer
                        }), 403
                
                # Track usage
                feature_service.track_feature_usage(
                    user_id=str(user_id),
                    feature_id=feature_id,
                    context={'endpoint': request.endpoint, 'method': request.method}
                )
                
                # Call the original function
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in feature access decorator: {e}")
                return jsonify({
                    'success': False,
                    'error': 'internal_error',
                    'message': 'Internal server error'
                }), 500
        
        return wrapper
    return decorator

def require_subscription_tier(minimum_tier: str):
    """Decorator to require minimum subscription tier"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Get user ID from session
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({
                        'success': False,
                        'error': 'authentication_required',
                        'message': 'Authentication required'
                    }), 401
                
                # Get user subscription
                feature_service = current_app.feature_access_service
                if not feature_service:
                    return jsonify({
                        'success': False,
                        'error': 'service_unavailable',
                        'message': 'Feature access service unavailable'
                    }), 503
                
                subscription = feature_service._get_user_subscription(str(user_id))
                if not subscription:
                    return jsonify({
                        'success': False,
                        'error': 'subscription_required',
                        'message': 'A subscription is required to access this feature'
                    }), 402
                
                # Check tier level
                tier_hierarchy = {
                    'budget': 1,
                    'mid_tier': 2,
                    'professional': 3
                }
                
                current_tier_level = tier_hierarchy.get(subscription.get('tier', 'budget'), 0)
                required_tier_level = tier_hierarchy.get(minimum_tier, 0)
                
                if current_tier_level < required_tier_level:
                    return jsonify({
                        'success': False,
                        'error': 'upgrade_required',
                        'message': f'This feature requires {minimum_tier} tier or higher',
                        'current_tier': subscription.get('tier', 'budget'),
                        'required_tier': minimum_tier,
                        'upgrade_required': True
                    }), 402
                
                # Call the original function
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in subscription tier decorator: {e}")
                return jsonify({
                    'success': False,
                    'error': 'internal_error',
                    'message': 'Internal server error'
                }), 500
        
        return wrapper
    return decorator

# Initialize middleware
feature_access_middleware = FeatureAccessMiddleware() 