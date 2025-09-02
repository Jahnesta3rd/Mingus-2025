"""
Email Verification Middleware
Integrates with existing security middleware for email verification endpoints
"""

from functools import wraps
from flask import request, g, current_app, jsonify
from loguru import logger
from typing import Optional, Dict, Any
import time

class EmailVerificationMiddleware:
    """Middleware for email verification security and monitoring"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize email verification middleware with Flask app"""
        # Register before_request handler
        app.before_request(self.before_request)
        
        # Register after_request handler
        app.after_request(self.after_request)
        
        # Register error handlers
        app.errorhandler(429)(self.handle_rate_limit_exceeded)
        app.errorhandler(403)(self.handle_verification_required)
        
        logger.info("Email verification middleware initialized")
    
    def before_request(self):
        """Process requests before handling"""
        # Check if this is an email verification endpoint
        if self.is_email_verification_endpoint():
            # Add request context for email verification
            g.email_verification_request = True
            g.request_start_time = time.time()
            
            # Log email verification requests
            self.log_verification_request()
            
            # Check for suspicious patterns
            self.detect_suspicious_activity()
    
    def after_request(self, response):
        """Process responses after handling"""
        # Check if this was an email verification request
        if getattr(g, 'email_verification_request', False):
            # Add email verification headers
            self.add_verification_headers(response)
            
            # Log response details
            self.log_verification_response(response)
            
            # Track metrics
            self.track_verification_metrics(response)
        
        return response
    
    def is_email_verification_endpoint(self) -> bool:
        """Check if current request is for email verification"""
        return request.endpoint and 'email_verification' in request.endpoint
    
    def log_verification_request(self):
        """Log email verification request details"""
        try:
            user_id = g.get('user_id')
            email = request.json.get('email') if request.is_json else None
            verification_type = request.json.get('verification_type') if request.is_json else None
            
            log_data = {
                'endpoint': request.endpoint,
                'method': request.method,
                'ip_address': request.headers.get('X-Forwarded-For', request.remote_addr),
                'user_agent': request.headers.get('User-Agent', ''),
                'timestamp': time.time()
            }
            
            if user_id:
                log_data['user_id'] = user_id
            
            if email:
                log_data['email'] = email
            
            if verification_type:
                log_data['verification_type'] = verification_type
            
            logger.info(f"Email verification request: {log_data}")
            
        except Exception as e:
            logger.warning(f"Could not log verification request: {e}")
    
    def log_verification_response(self, response):
        """Log email verification response details"""
        try:
            response_time = time.time() - g.get('request_start_time', time.time())
            
            log_data = {
                'endpoint': request.endpoint,
                'status_code': response.status_code,
                'response_time': response_time,
                'timestamp': time.time()
            }
            
            if hasattr(g, 'user_id'):
                log_data['user_id'] = g.user_id
            
            logger.info(f"Email verification response: {log_data}")
            
        except Exception as e:
            logger.warning(f"Could not log verification response: {e}")
    
    def detect_suspicious_activity(self):
        """Detect suspicious email verification activity"""
        try:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            email = request.json.get('email') if request.is_json else None
            
            if not email:
                return
            
            # Check for rapid-fire requests from same IP
            from ..services.rate_limit_service import RateLimitService
            rate_limit_service = RateLimitService()
            
            # Check IP-based rate limiting
            if not rate_limit_service.check_ip_limit(ip_address, 'email_verification'):
                logger.warning(f"Suspicious activity detected: IP {ip_address} exceeded rate limits")
                g.suspicious_activity = True
            
            # Check for email enumeration attempts
            if self.detect_email_enumeration(ip_address, email):
                logger.warning(f"Potential email enumeration attempt from IP {ip_address}")
                g.suspicious_activity = True
                
        except Exception as e:
            logger.warning(f"Could not detect suspicious activity: {e}")
    
    def detect_email_enumeration(self, ip_address: str, email: str) -> bool:
        """Detect potential email enumeration attempts"""
        try:
            # This is a simplified check - you might want to implement more sophisticated detection
            from ..services.rate_limit_service import RateLimitService
            rate_limit_service = RateLimitService()
            
            # Check if this IP has been requesting many different emails
            recent_emails = rate_limit_service.get_recent_emails_for_ip(ip_address, window_minutes=60)
            
            if len(recent_emails) > 10:  # More than 10 different emails in 1 hour
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Could not check for email enumeration: {e}")
            return False
    
    def add_verification_headers(self, response):
        """Add email verification specific headers"""
        try:
            # Add verification-related headers
            response.headers['X-Email-Verification-Endpoint'] = 'true'
            
            # Add rate limit information if available
            if hasattr(g, 'rate_limit_info'):
                response.headers['X-RateLimit-Limit'] = str(g.rate_limit_info.get('limit', ''))
                response.headers['X-RateLimit-Remaining'] = str(g.rate_limit_info.get('remaining', ''))
                response.headers['X-RateLimit-Reset'] = str(g.rate_limit_info.get('reset', ''))
            
            # Add verification status if available
            if hasattr(g, 'verification_status'):
                response.headers['X-Verification-Status'] = g.verification_status
            
        except Exception as e:
            logger.warning(f"Could not add verification headers: {e}")
    
    def track_verification_metrics(self, response):
        """Track email verification metrics"""
        try:
            # Track success/failure rates
            if response.status_code == 200:
                self.record_verification_success()
            elif response.status_code >= 400:
                self.record_verification_failure(response.status_code)
            
            # Track response times
            response_time = time.time() - g.get('request_start_time', time.time())
            self.record_response_time(response_time)
            
        except Exception as e:
            logger.warning(f"Could not track verification metrics: {e}")
    
    def record_verification_success(self):
        """Record successful verification"""
        try:
            # This would integrate with your existing metrics system
            from ..metrics import record_verification_success
            record_verification_success()
        except ImportError:
            # Metrics system not available
            pass
        except Exception as e:
            logger.warning(f"Could not record verification success: {e}")
    
    def record_verification_failure(self, status_code: int):
        """Record verification failure"""
        try:
            # This would integrate with your existing metrics system
            from ..metrics import record_verification_failure
            record_verification_failure(status_code)
        except ImportError:
            # Metrics system not available
            pass
        except Exception as e:
            logger.warning(f"Could not record verification failure: {e}")
    
    def record_response_time(self, response_time: float):
        """Record response time for verification requests"""
        try:
            # This would integrate with your existing metrics system
            from ..metrics import record_verification_response_time
            record_verification_response_time(response_time)
        except ImportError:
            # Metrics system not available
            pass
        except Exception as e:
            logger.warning(f"Could not record response time: {e}")
    
    def handle_rate_limit_exceeded(self, error):
        """Handle rate limit exceeded errors for email verification"""
        try:
            if self.is_email_verification_endpoint():
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'message': 'Too many verification requests. Please try again later.',
                    'retry_after': 3600  # 1 hour
                }), 429
            
            # Let other error handlers deal with it
            return error
            
        except Exception as e:
            logger.error(f"Error handling rate limit exceeded: {e}")
            return error
    
    def handle_verification_required(self, error):
        """Handle verification required errors"""
        try:
            if self.is_email_verification_endpoint():
                return jsonify({
                    'error': 'Email verification required',
                    'code': 'EMAIL_VERIFICATION_REQUIRED',
                    'message': 'Please verify your email address to access this feature'
                }), 403
            
            # Let other error handlers deal with it
            return error
            
        except Exception as e:
            logger.error(f"Error handling verification required: {e}")
            return error

def init_email_verification_middleware(app):
    """Initialize email verification middleware"""
    middleware = EmailVerificationMiddleware()
    middleware.init_app(app)
    return middleware

# Decorator for email verification endpoints
def email_verification_endpoint(f):
    """Decorator to mark endpoints as email verification endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Mark this request as email verification
        g.email_verification_request = True
        g.request_start_time = time.time()
        
        return f(*args, **kwargs)
    
    return decorated_function

# Utility functions for email verification middleware
def get_verification_context() -> Dict[str, Any]:
    """Get email verification context from Flask g"""
    context = {}
    
    if hasattr(g, 'email_verification_request'):
        context['is_verification_request'] = g.email_verification_request
    
    if hasattr(g, 'suspicious_activity'):
        context['suspicious_activity'] = g.suspicious_activity
    
    if hasattr(g, 'rate_limit_info'):
        context['rate_limit_info'] = g.rate_limit_info
    
    if hasattr(g, 'verification_status'):
        context['verification_status'] = g.verification_status
    
    return context

def is_suspicious_activity_detected() -> bool:
    """Check if suspicious activity was detected"""
    return getattr(g, 'suspicious_activity', False)

def get_rate_limit_info() -> Optional[Dict[str, Any]]:
    """Get rate limit information"""
    return getattr(g, 'rate_limit_info', None)
