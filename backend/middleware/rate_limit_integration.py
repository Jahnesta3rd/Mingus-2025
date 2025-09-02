"""
Rate Limiting Integration for Flask Application
Examples and integration patterns for applying rate limiting to existing routes
"""

import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable
from flask import request, g, current_app, Response
from .rate_limit_decorators import (
    rate_limit,
    rate_limit_by_user,
    rate_limit_by_ip,
    rate_limit_financial,
    rate_limit_payment,
    rate_limit_auth,
    rate_limit_assessment,
    rate_limit_webhook,
    login_rate_limit,
    register_rate_limit,
    password_reset_rate_limit,
    financial_rate_limit,
    payment_rate_limit,
    assessment_submit_rate_limit,
    assessment_view_rate_limit,
    webhook_rate_limit
)
from .rate_limiter import get_rate_limiter, add_rate_limit_headers
from backend.monitoring.rate_limit_monitoring import record_rate_limit_event
import time

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    """Middleware for applying rate limiting to Flask routes"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with the Flask app"""
        self.app = app
        self.rate_limiter = get_rate_limiter()
        
        # Register before_request and after_request handlers
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        logger.info("RateLimitMiddleware initialized successfully")
    
    def before_request(self):
        """Handle rate limiting before each request"""
        try:
            # Get rate limit info for the current endpoint
            endpoint = request.endpoint
            if endpoint:
                # Apply rate limiting based on endpoint type
                self._apply_rate_limiting(endpoint)
        except Exception as e:
            logger.error(f"Error in rate limiting middleware: {e}")
            # Continue with request if rate limiting fails
    
    def after_request(self, response):
        """Add rate limit headers after each request"""
        try:
            if hasattr(g, 'rate_limit_info'):
                response = add_rate_limit_headers(response, g.rate_limit_info)
        except Exception as e:
            logger.error(f"Error adding rate limit headers: {e}")
        
        return response
    
    def _apply_rate_limiting(self, endpoint):
        """Apply rate limiting based on endpoint type"""
        # This is a simplified implementation
        # In production, you would check actual rate limits
        pass

class RateLimitIntegration:
    """Integration helper for applying rate limiting to existing routes"""
    
    def __init__(self):
        self.rate_limiter = get_rate_limiter()
    
    def apply_to_blueprint(self, blueprint, config: Dict[str, str]):
        """
        Apply rate limiting to all routes in a blueprint
        
        Args:
            blueprint: Flask blueprint
            config: Dictionary mapping route names to rate limit types
        """
        for route_name, endpoint_type in config.items():
            if hasattr(blueprint, route_name):
                route_func = getattr(blueprint, route_name)
                decorated_func = self._apply_rate_limit(route_func, endpoint_type)
                setattr(blueprint, route_name, decorated_func)
    
    def _apply_rate_limit(self, func: Callable, endpoint_type: str) -> Callable:
        """Apply appropriate rate limiting to a function"""
        if endpoint_type in ['login', 'register', 'password_reset']:
            return rate_limit_auth(endpoint_type)(func)
        elif endpoint_type in ['financial_api', 'financial_hourly']:
            return rate_limit_financial(endpoint_type)(func)
        elif endpoint_type in ['payment', 'stripe_webhook']:
            return rate_limit_payment(endpoint_type)(func)
        elif endpoint_type in ['assessment_submit', 'assessment_view']:
            return rate_limit_assessment(endpoint_type)(func)
        elif endpoint_type == 'webhook':
            return rate_limit_webhook(endpoint_type)(func)
        else:
            return rate_limit(endpoint_type)(func)

# Example route integrations
def integrate_auth_routes(app):
    """Integrate rate limiting with authentication routes"""
    
    @app.route('/api/auth/login', methods=['POST'])
    @login_rate_limit
    def login():
        """User login endpoint with rate limiting"""
        # Your existing login logic here
        return {'message': 'Login endpoint'}, 200
    
    @app.route('/api/auth/register', methods=['POST'])
    @register_rate_limit
    def register():
        """User registration endpoint with rate limiting"""
        # Your existing registration logic here
        return {'message': 'Register endpoint'}, 200
    
    @app.route('/api/auth/password-reset', methods=['POST'])
    @password_reset_rate_limit
    def password_reset():
        """Password reset endpoint with rate limiting"""
        # Your existing password reset logic here
        return {'message': 'Password reset endpoint'}, 200
    
    @app.route('/api/auth/refresh', methods=['POST'])
    @rate_limit_auth('refresh')
    def refresh_token():
        """Token refresh endpoint with rate limiting"""
        # Your existing refresh logic here
        return {'message': 'Token refresh endpoint'}, 200

def integrate_financial_routes(app):
    """Integrate rate limiting with financial data routes"""
    
    @app.route('/api/financial/planning', methods=['GET'])
    @financial_rate_limit
    def get_financial_planning():
        """Financial planning endpoint with rate limiting"""
        # Your existing financial planning logic here
        return {'message': 'Financial planning data'}, 200
    
    @app.route('/api/financial/education', methods=['GET'])
    @rate_limit_financial('financial_education')
    def get_financial_education():
        """Financial education endpoint with rate limiting"""
        # Your existing financial education logic here
        return {'message': 'Financial education content'}, 200
    
    @app.route('/api/financial/tools', methods=['GET'])
    @rate_limit_financial('financial_planning')
    def get_financial_tools():
        """Financial tools endpoint with rate limiting"""
        # Your existing financial tools logic here
        return {'message': 'Financial tools'}, 200
    
    @app.route('/api/financial/analytics', methods=['GET'])
    @rate_limit_by_user('analytics', {'requests': 30, 'window': 3600})
    def get_financial_analytics():
        """Financial analytics endpoint with custom rate limiting"""
        # Your existing analytics logic here
        return {'message': 'Financial analytics'}, 200

def integrate_payment_routes(app):
    """Integrate rate limiting with payment routes"""
    
    @app.route('/api/payment/stripe/create-payment-intent', methods=['POST'])
    @payment_rate_limit
    def create_payment_intent():
        """Stripe payment intent creation with rate limiting"""
        # Your existing payment logic here
        return {'message': 'Payment intent created'}, 200
    
    @app.route('/api/payment/stripe/confirm-payment', methods=['POST'])
    @payment_rate_limit
    def confirm_payment():
        """Stripe payment confirmation with rate limiting"""
        # Your existing payment confirmation logic here
        return {'message': 'Payment confirmed'}, 200
    
    @app.route('/api/webhooks/stripe', methods=['POST'])
    @webhook_rate_limit
    def stripe_webhook():
        """Stripe webhook endpoint with rate limiting"""
        # Your existing webhook logic here
        return {'message': 'Webhook processed'}, 200
    
    @app.route('/api/payment/plaid/link-account', methods=['POST'])
    @rate_limit_payment('plaid')
    def plaid_link_account():
        """Plaid account linking with rate limiting"""
        # Your existing Plaid logic here
        return {'message': 'Account linked'}, 200

def integrate_assessment_routes(app):
    """Integrate rate limiting with assessment and onboarding routes"""
    
    @app.route('/api/assessment/submit', methods=['POST'])
    @assessment_submit_rate_limit
    def submit_assessment():
        """Assessment submission with rate limiting"""
        # Your existing assessment submission logic here
        return {'message': 'Assessment submitted'}, 200
    
    @app.route('/api/assessment/view/<assessment_id>', methods=['GET'])
    @assessment_view_rate_limit
    def view_assessment(assessment_id):
        """Assessment viewing with rate limiting"""
        # Your existing assessment viewing logic here
        return {'message': f'Assessment {assessment_id} data'}, 200
    
    @app.route('/api/onboarding/complete', methods=['POST'])
    @rate_limit_assessment('onboarding')
    def complete_onboarding():
        """Onboarding completion with rate limiting"""
        # Your existing onboarding logic here
        return {'message': 'Onboarding completed'}, 200
    
    @app.route('/api/career/advice', methods=['GET'])
    @rate_limit_assessment('career_advice')
    def get_career_advice():
        """Career advice endpoint with rate limiting"""
        # Your existing career advice logic here
        return {'message': 'Career advice content'}, 200

def integrate_general_api_routes(app):
    """Integrate rate limiting with general API routes"""
    
    @app.route('/api/general/health', methods=['GET'])
    @rate_limit_by_ip('health_check', {'requests': 100, 'window': 60})
    def health_check():
        """Health check endpoint with IP-based rate limiting"""
        # Your existing health check logic here
        return {'message': 'Service healthy'}, 200
    
    @app.route('/api/general/metrics', methods=['GET'])
    @rate_limit_by_user('metrics', {'requests': 50, 'window': 3600})
    def get_metrics():
        """Metrics endpoint with user-based rate limiting"""
        # Your existing metrics logic here
        return {'message': 'Metrics data'}, 200
    
    @app.route('/api/general/search', methods=['GET'])
    @rate_limit('search', {'requests': 200, 'window': 3600})
    def search():
        """Search endpoint with custom rate limiting"""
        # Your existing search logic here
        return {'message': 'Search results'}, 200

def integrate_mobile_api_routes(app):
    """Integrate rate limiting with mobile API routes"""
    
    @app.route('/api/mobile/sync', methods=['POST'])
    @rate_limit_by_user('mobile_sync', {'requests': 10, 'window': 300})
    def mobile_sync():
        """Mobile sync endpoint with rate limiting"""
        # Your existing mobile sync logic here
        return {'message': 'Sync completed'}, 200
    
    @app.route('/api/mobile/notifications', methods=['GET'])
    @rate_limit_by_user('mobile_notifications', {'requests': 20, 'window': 300})
    def get_mobile_notifications():
        """Mobile notifications endpoint with rate limiting"""
        # Your existing notifications logic here
        return {'message': 'Notifications data'}, 200
    
    @app.route('/api/mobile/offline-data', methods=['GET'])
    @rate_limit_by_user('mobile_offline', {'requests': 5, 'window': 3600})
    def get_mobile_offline_data():
        """Mobile offline data endpoint with rate limiting"""
        # Your existing offline data logic here
        return {'message': 'Offline data'}, 200

def integrate_admin_routes(app):
    """Integrate rate limiting with admin routes"""
    
    @app.route('/api/admin/users', methods=['GET'])
    @rate_limit_by_user('admin_users', {'requests': 100, 'window': 3600})
    def get_admin_users():
        """Admin users endpoint with rate limiting"""
        # Your existing admin logic here
        return {'message': 'Admin users data'}, 200
    
    @app.route('/api/admin/analytics', methods=['GET'])
    @rate_limit_by_user('admin_analytics', {'requests': 50, 'window': 3600})
    def get_admin_analytics():
        """Admin analytics endpoint with rate limiting"""
        # Your existing admin analytics logic here
        return {'message': 'Admin analytics'}, 200
    
    @app.route('/api/admin/system-status', methods=['GET'])
    @rate_limit_by_user('admin_system', {'requests': 200, 'window': 3600})
    def get_admin_system_status():
        """Admin system status endpoint with rate limiting"""
        # Your existing system status logic here
        return {'message': 'System status'}, 200

def integrate_webhook_routes(app):
    """Integrate rate limiting with webhook routes"""
    
    @app.route('/api/webhooks/plaid', methods=['POST'])
    @rate_limit_webhook('plaid_webhook')
    def plaid_webhook():
        """Plaid webhook endpoint with rate limiting"""
        # Your existing Plaid webhook logic here
        return {'message': 'Plaid webhook processed'}, 200
    
    @app.route('/api/webhooks/email-service', methods=['POST'])
    @rate_limit_webhook('email_webhook')
    def email_webhook():
        """Email service webhook endpoint with rate limiting"""
        # Your existing email webhook logic here
        return {'message': 'Email webhook processed'}, 200
    
    @app.route('/api/webhooks/third-party', methods=['POST'])
    @rate_limit_webhook('third_party_webhook')
    def third_party_webhook():
        """Third-party webhook endpoint with rate limiting"""
        # Your existing third-party webhook logic here
        return {'message': 'Third-party webhook processed'}, 200

def integrate_rate_limit_headers(app):
    """Integrate rate limit headers with all responses"""
    
    @app.after_request
    def add_rate_limit_headers(response):
        """Add rate limit headers to all responses"""
        try:
            if hasattr(g, 'rate_limit_info'):
                response = add_rate_limit_headers(response, g.rate_limit_info)
        except Exception as e:
            logger.error(f"Error adding rate limit headers: {e}")
        
        return response

def integrate_rate_limit_monitoring(app):
    """Integrate rate limit monitoring with the application"""
    
    @app.before_request
    def record_request_start():
        """Record request start for monitoring"""
        g.request_start_time = time.time()
    
    @app.after_request
    def record_request_completion(response):
        """Record request completion for monitoring"""
        try:
            if hasattr(g, 'rate_limit_info'):
                # Record rate limit event for monitoring
                event_data = {
                    'timestamp': g.request_start_time,
                    'identifier': g.rate_limit_info.get('identifier', 'unknown'),
                    'endpoint_type': g.rate_limit_info.get('endpoint_type', 'unknown'),
                    'requests_made': g.rate_limit_info.get('requests_made', 0),
                    'limit': g.rate_limit_info.get('limit', 0),
                    'limited': g.rate_limit_info.get('limited', False),
                    'ip_address': request.remote_addr,
                    'user_id': g.get('user_id'),
                    'user_agent': request.headers.get('User-Agent'),
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'path': request.path,
                    'cultural_context': {
                        'african_american_focused': 'assessment' in request.path.lower(),
                        'financial_professional': 'financial' in request.path.lower(),
                        'mobile_user': 'mobile' in request.headers.get('User-Agent', '').lower()
                    }
                }
                
                record_rate_limit_event(event_data)
                
        except Exception as e:
            logger.error(f"Error recording rate limit event: {e}")
        
        return response

def create_rate_limit_middleware(app):
    """Create and configure rate limiting middleware for the application"""
    
    # Initialize rate limiting integration
    integration = RateLimitIntegration()
    
    # Integrate with different route types
    integrate_auth_routes(app)
    integrate_financial_routes(app)
    integrate_payment_routes(app)
    integrate_assessment_routes(app)
    integrate_general_api_routes(app)
    integrate_mobile_api_routes(app)
    integrate_admin_routes(app)
    integrate_webhook_routes(app)
    
    # Integrate rate limit headers and monitoring
    integrate_rate_limit_headers(app)
    integrate_rate_limit_monitoring(app)
    
    logger.info("Rate limiting middleware integrated successfully")

# Example usage in existing routes
def apply_rate_limiting_to_existing_route(route_func: Callable, endpoint_type: str) -> Callable:
    """
    Apply rate limiting to an existing route function
    
    Args:
        route_func: Existing route function
        endpoint_type: Rate limit endpoint type
        
    Returns:
        Decorated function with rate limiting
    """
    if endpoint_type in ['login', 'register', 'password_reset']:
        return rate_limit_auth(endpoint_type)(route_func)
    elif endpoint_type in ['financial_api', 'financial_hourly']:
        return rate_limit_financial(endpoint_type)(route_func)
    elif endpoint_type in ['payment', 'stripe_webhook']:
        return rate_limit_payment(endpoint_type)(route_func)
    elif endpoint_type in ['assessment_submit', 'assessment_view']:
        return rate_limit_assessment(endpoint_type)(route_func)
    elif endpoint_type == 'webhook':
        return rate_limit_webhook(endpoint_type)(route_func)
    else:
        return rate_limit(endpoint_type)(route_func)

# Example of applying to existing blueprint routes
def integrate_with_existing_blueprint(blueprint, route_config: Dict[str, str]):
    """
    Integrate rate limiting with existing blueprint routes
    
    Args:
        blueprint: Flask blueprint
        route_config: Dictionary mapping route names to rate limit types
        
    Example:
        route_config = {
            'user_profile': 'api_general',
            'update_profile': 'api_general',
            'delete_account': 'critical_operation'
        }
    """
    integration = RateLimitIntegration()
    integration.apply_to_blueprint(blueprint, route_config)

# Example configuration for different route types
RATE_LIMIT_ROUTE_CONFIG = {
    'auth': {
        'login': 'login',
        'register': 'register',
        'password_reset': 'password_reset',
        'refresh_token': 'refresh'
    },
    'financial': {
        'get_planning': 'financial_api',
        'get_education': 'financial_education',
        'get_tools': 'financial_planning',
        'get_analytics': 'analytics'
    },
    'payment': {
        'create_payment': 'payment',
        'confirm_payment': 'payment',
        'stripe_webhook': 'stripe_webhook',
        'plaid_link': 'plaid'
    },
    'assessment': {
        'submit_assessment': 'assessment_submit',
        'view_assessment': 'assessment_view',
        'complete_onboarding': 'onboarding',
        'get_career_advice': 'career_advice'
    },
    'general': {
        'health_check': 'health_check',
        'get_metrics': 'metrics',
        'search': 'search'
    },
    'mobile': {
        'sync': 'mobile_sync',
        'notifications': 'mobile_notifications',
        'offline_data': 'mobile_offline'
    },
    'admin': {
        'users': 'admin_users',
        'analytics': 'admin_analytics',
        'system_status': 'admin_system'
    },
    'webhooks': {
        'plaid': 'plaid_webhook',
        'email': 'email_webhook',
        'third_party': 'third_party_webhook'
    }
}
