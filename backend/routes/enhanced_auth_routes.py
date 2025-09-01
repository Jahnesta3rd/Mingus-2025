#!/usr/bin/env python3
"""
Enhanced Authentication Routes for MINGUS
Complete authentication system with email verification and password reset
"""

from flask import Blueprint, request, jsonify, current_app, g
from flask_csrf import csrf_protected
from backend.middleware.unified_auth import (
    require_auth, get_current_user_id, create_auth_response
)
from backend.middleware.rate_limiter import AdvancedRateLimiter
from backend.services.auth_service import AuthService
from backend.services.resend_email_service import resend_email_service
import logging
import re
from datetime import datetime
import secrets

logger = logging.getLogger(__name__)

enhanced_auth_bp = Blueprint('enhanced_auth', __name__, url_prefix='/auth')

# Initialize rate limiter
rate_limiter = AdvancedRateLimiter()

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is valid"

def get_client_info():
    """Get client information for security tracking"""
    return {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'timestamp': datetime.utcnow()
    }

@enhanced_auth_bp.route('/verify-email', methods=['POST'])
@csrf_protected
def verify_email():
    """
    Verify user email with token
    
    POST /auth/verify-email
    Body: {"token": "verification_token"}
    """
    try:
        # Rate limiting
        client_id = rate_limiter.get_identifier(request)
        rate_check = rate_limiter.is_rate_limited(client_id, 'auth')
        if rate_check['limited']:
            return jsonify({
                'error': 'Rate limited',
                'message': 'Too many verification attempts. Please try again later.',
                'retry_after': rate_check['window_remaining']
            }), 429
        
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({
                'error': 'Missing token',
                'message': 'Verification token is required'
            }), 400
        
        token = data['token'].strip()
        if not token:
            return jsonify({
                'error': 'Invalid token',
                'message': 'Verification token cannot be empty'
            }), 400
        
        # Get auth service
        auth_service = current_app.auth_service
        
        # Verify email
        success, message, user_id = auth_service.verify_email(token)
        
        if success:
            logger.info(f"Email verified successfully for user {user_id}")
            return jsonify({
                'success': True,
                'message': message,
                'user_id': user_id
            })
        else:
            logger.warning(f"Email verification failed: {message}")
            return jsonify({
                'error': 'Verification failed',
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Verification failed due to server error'
        }), 500

@enhanced_auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email_get(token):
    """
    Verify user email with token (GET method for email links)
    
    GET /auth/verify-email/<token>
    """
    try:
        if not token:
            return jsonify({
                'error': 'Missing token',
                'message': 'Verification token is required'
            }), 400
        
        # Get auth service
        auth_service = current_app.auth_service
        
        # Verify email
        success, message, user_id = auth_service.verify_email(token)
        
        if success:
            logger.info(f"Email verified successfully for user {user_id} via GET")
            return jsonify({
                'success': True,
                'message': message,
                'user_id': user_id,
                'redirect_url': f"{current_app.config.get('FRONTEND_URL', '/')}/dashboard"
            })
        else:
            logger.warning(f"Email verification failed via GET: {message}")
            return jsonify({
                'error': 'Verification failed',
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"Email verification GET error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Verification failed due to server error'
        }), 500

@enhanced_auth_bp.route('/resend-verification', methods=['POST'])
@csrf_protected
def resend_verification():
    """
    Resend email verification
    
    POST /auth/resend-verification
    Body: {"email": "user@example.com"}
    """
    try:
        # Rate limiting
        client_id = rate_limiter.get_identifier(request)
        rate_check = rate_limiter.is_rate_limited(client_id, 'auth')
        if rate_check['limited']:
            return jsonify({
                'error': 'Rate limited',
                'message': 'Too many resend attempts. Please try again later.',
                'retry_after': rate_check['window_remaining']
            }), 429
        
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Missing email',
                'message': 'Email address is required'
            }), 400
        
        email = data['email'].strip().lower()
        if not email or not validate_email(email):
            return jsonify({
                'error': 'Invalid email',
                'message': 'Please provide a valid email address'
            }), 400
        
        # Get client info for security tracking
        client_info = get_client_info()
        
        # Get auth service
        auth_service = current_app.auth_service
        
        # Resend verification email
        success, message = auth_service.resend_verification_email(
            email, 
            client_info['ip_address'], 
            client_info['user_agent']
        )
        
        if success:
            logger.info(f"Verification email resent to {email}")
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            logger.warning(f"Failed to resend verification to {email}: {message}")
            return jsonify({
                'error': 'Resend failed',
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"Resend verification error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to resend verification email'
        }), 500

@enhanced_auth_bp.route('/forgot-password', methods=['POST'])
@csrf_protected
def forgot_password():
    """
    Request password reset
    
    POST /auth/forgot-password
    Body: {"email": "user@example.com"}
    """
    try:
        # Rate limiting
        client_id = rate_limiter.get_identifier(request)
        rate_check = rate_limiter.is_rate_limited(client_id, 'password_reset')
        if rate_check['limited']:
            return jsonify({
                'error': 'Rate limited',
                'message': 'Too many password reset requests. Please try again later.',
                'retry_after': rate_check['window_remaining']
            }), 429
        
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Missing email',
                'message': 'Email address is required'
            }), 400
        
        email = data['email'].strip().lower()
        if not email or not validate_email(email):
            return jsonify({
                'error': 'Invalid email',
                'message': 'Please provide a valid email address'
            }), 400
        
        # Get client info for security tracking
        client_info = get_client_info()
        
        # Get auth service
        auth_service = current_app.auth_service
        
        # Create password reset token
        success, message, token = auth_service.create_password_reset_token(
            email, 
            client_info['ip_address'], 
            client_info['user_agent']
        )
        
        if success and token:
            # Send password reset email
            email_result = resend_email_service.send_password_reset_email(email, token)
            
            if email_result['success']:
                logger.info(f"Password reset email sent to {email}")
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                logger.error(f"Failed to send password reset email: {email_result.get('error')}")
                return jsonify({
                    'error': 'Email delivery failed',
                    'message': 'Password reset email could not be sent. Please try again later.'
                }), 500
        else:
            logger.warning(f"Password reset request failed for {email}: {message}")
            return jsonify({
                'error': 'Reset request failed',
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Password reset request failed due to server error'
        }), 500

@enhanced_auth_bp.route('/reset-password/<token>', methods=['GET'])
def reset_password_get(token):
    """
    Validate password reset token (GET method for email links)
    
    GET /auth/reset-password/<token>
    """
    try:
        if not token:
            return jsonify({
                'error': 'Missing token',
                'message': 'Reset token is required'
            }), 400
        
        # Get auth service
        auth_service = current_app.auth_service
        
        # Validate reset token
        success, message, user_id = auth_service.validate_password_reset_token(token)
        
        if success:
            logger.info(f"Password reset token validated for user {user_id}")
            return jsonify({
                'success': True,
                'message': message,
                'user_id': user_id,
                'token_valid': True
            })
        else:
            logger.warning(f"Password reset token validation failed: {message}")
            return jsonify({
                'error': 'Invalid token',
                'message': message,
                'token_valid': False
            }), 400
            
    except Exception as e:
        logger.error(f"Password reset token validation error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Token validation failed due to server error'
        }), 500

@enhanced_auth_bp.route('/reset-password', methods=['POST'])
@csrf_protected
def reset_password():
    """
    Reset password with token
    
    POST /auth/reset-password
    Body: {"token": "reset_token", "new_password": "new_password"}
    """
    try:
        # Rate limiting
        client_id = rate_limiter.get_identifier(request)
        rate_check = rate_limiter.is_rate_limited(client_id, 'auth')
        if rate_check['limited']:
            return jsonify({
                'error': 'Rate limited',
                'message': 'Too many password reset attempts. Please try again later.',
                'retry_after': rate_check['window_remaining']
            }), 429
        
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Missing data',
                'message': 'Reset token and new password are required'
            }), 400
        
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')
        
        if not token:
            return jsonify({
                'error': 'Missing token',
                'message': 'Reset token is required'
            }), 400
        
        if not new_password:
            return jsonify({
                'error': 'Missing password',
                'message': 'New password is required'
            }), 400
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({
                'error': 'Invalid password',
                'message': message
            }), 400
        
        # Get auth service
        auth_service = current_app.auth_service
        
        # Reset password
        success, message = auth_service.reset_password(token, new_password)
        
        if success:
            logger.info("Password reset successfully")
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            logger.warning(f"Password reset failed: {message}")
            return jsonify({
                'error': 'Password reset failed',
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Password reset failed due to server error'
        }), 500

@enhanced_auth_bp.route('/verification-status', methods=['GET'])
@require_auth
def get_verification_status():
    """
    Get current user's email verification status
    
    GET /auth/verification-status
    Requires: Authentication
    """
    try:
        user_id = get_current_user_id()
        
        # Get auth service
        auth_service = current_app.auth_service
        
        # Get verification status
        status = auth_service.get_user_verification_status(user_id)
        
        if 'error' in status:
            return jsonify({
                'error': 'Failed to get status',
                'message': status['error']
            }), 500
        
        return jsonify({
            'success': True,
            'verification_status': status
        })
        
    except Exception as e:
        logger.error(f"Get verification status error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to get verification status'
        }), 500

@enhanced_auth_bp.route('/request-verification', methods=['POST'])
@require_auth
def request_verification():
    """
    Request email verification for authenticated user
    
    POST /auth/request-verification
    Requires: Authentication
    """
    try:
        user_id = get_current_user_id()
        
        # Get user info
        user = current_app.user_service.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'error': 'User not found',
                'message': 'User account not found'
            }), 404
        
        # Check if already verified
        if user.get('email_verified', False):
            return jsonify({
                'error': 'Already verified',
                'message': 'Email is already verified'
            }), 400
        
        # Get client info for security tracking
        client_info = get_client_info()
        
        # Get auth service
        auth_service = current_app.auth_service
        
        # Create email verification
        success, message, token = auth_service.create_email_verification(
            user_id, 
            user['email'], 
            client_info['ip_address'], 
            client_info['user_agent']
        )
        
        if success and token:
            # Send verification email
            email_result = resend_email_service.send_verification_email(user['email'], token)
            
            if email_result['success']:
                logger.info(f"Verification email sent to user {user_id}")
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                logger.error(f"Failed to send verification email: {email_result.get('error')}")
                return jsonify({
                    'error': 'Email delivery failed',
                    'message': 'Verification email could not be sent. Please try again later.'
                }), 500
        else:
            logger.warning(f"Failed to create verification for user {user_id}: {message}")
            return jsonify({
                'error': 'Verification creation failed',
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"Request verification error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to request verification'
        }), 500

@enhanced_auth_bp.route('/cleanup-tokens', methods=['POST'])
@require_auth
def cleanup_tokens():
    """
    Clean up expired tokens (admin/maintenance endpoint)
    
    POST /auth/cleanup-tokens
    Requires: Authentication
    """
    try:
        user_id = get_current_user_id()
        
        # Check if user has admin privileges (implement as needed)
        # For now, allow any authenticated user to trigger cleanup
        
        # Get auth service
        auth_service = current_app.auth_service
        
        # Clean up expired tokens
        cleaned_count = auth_service.cleanup_expired_tokens()
        
        logger.info(f"Token cleanup completed by user {user_id}, cleaned {cleaned_count} tokens")
        
        return jsonify({
            'success': True,
            'message': f'Cleanup completed successfully',
            'tokens_cleaned': cleaned_count
        })
        
    except Exception as e:
        logger.error(f"Token cleanup error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Token cleanup failed'
        }), 500
