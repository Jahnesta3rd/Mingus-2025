#!/usr/bin/env python3
"""
Unified Authentication Routes for MINGUS Assessment System
Secure JWT-based authentication endpoints
"""

from flask import Blueprint, request, jsonify, current_app, g
from backend.middleware.unified_auth import (
    require_auth, require_subscription_tier, get_current_user_id, 
    get_current_user_tier, logout_user, create_auth_response, auth_middleware
)
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

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

def validate_auth_request(data: dict) -> dict:
    """Validate authentication request data"""
    errors = []
    
    if not data:
        return {'valid': False, 'errors': ['No data provided']}
    
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email:
        errors.append('Email is required')
    elif not validate_email(email):
        errors.append('Invalid email format')
    
    if not password:
        errors.append('Password is required')
    else:
        is_valid, message = validate_password(password)
        if not is_valid:
            errors.append(message)
    
    return {'valid': len(errors) == 0, 'errors': errors}

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate request data
        validation_result = validate_auth_request(data)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_result['errors']
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        # Check if user already exists
        existing_user = current_app.user_service.get_user_by_email(email)
        if existing_user:
            return jsonify({
                'error': 'User already exists',
                'message': 'An account with this email already exists'
            }), 409
        
        # Create new user
        user_data = {
            'email': email,
            'password': password,  # Will be hashed by user service
            'full_name': full_name,
            'subscription_tier': 'free',
            'created_at': datetime.utcnow(),
            'is_active': True
        }
        
        new_user = current_app.user_service.create_user(user_data)
        
        if new_user:
            # Create authentication response
            response_data = create_auth_response(
                new_user['id'], 
                new_user.get('subscription_tier', 'free')
            )
            
            # Add user info to response
            response_data['user'] = {
                'id': new_user['id'],
                'email': new_user['email'],
                'full_name': new_user['full_name'],
                'subscription_tier': new_user.get('subscription_tier', 'free')
            }
            
            logger.info(f"New user registered: {email}")
            return jsonify(response_data), 201
        else:
            return jsonify({
                'error': 'Registration failed',
                'message': 'Unable to create user account'
            }), 500
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Registration failed due to server error'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        # Validate request data
        validation_result = validate_auth_request(data)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_result['errors']
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        # Authenticate user
        user = current_app.user_service.authenticate_user(email, password)
        
        if not user:
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Invalid email or password'
            }), 401
        
        # Check if account is active
        if not user.get('is_active', True):
            return jsonify({
                'error': 'Account disabled',
                'message': 'Your account has been disabled. Please contact support.'
            }), 403
        
        # Create authentication response
        response_data = create_auth_response(
            user['id'], 
            user.get('subscription_tier', 'free'),
            remember_me
        )
        
        # Add user info to response
        response_data['user'] = {
            'id': user['id'],
            'email': user['email'],
            'full_name': user.get('full_name', ''),
            'subscription_tier': user.get('subscription_tier', 'free'),
            'phone_number': user.get('phone_number', '')
        }
        
        # Update last login
        current_app.user_service.update_last_login(user['id'])
        
        logger.info(f"User logged in: {email}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Login failed due to server error'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """User logout endpoint"""
    try:
        # Perform logout
        logout_user()
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Logout failed due to server error'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        refresh_token = data.get('refresh_token')
        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400
        
        # Refresh access token
        new_access_token = auth_middleware.refresh_access_token(refresh_token)
        
        if new_access_token:
            return jsonify({
                'success': True,
                'access_token': new_access_token,
                'token_type': 'Bearer',
                'expires_in': auth_middleware.access_token_expiry
            })
        else:
            return jsonify({
                'error': 'Invalid refresh token',
                'message': 'Refresh token is invalid or expired'
            }), 401
            
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Token refresh failed due to server error'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user profile"""
    try:
        user_id = get_current_user_id()
        
        # Get user data
        user = current_app.user_service.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'error': 'User not found',
                'message': 'User account not found'
            }), 404
        
        # Get additional profile data
        profile = current_app.onboarding_service.get_user_profile(user_id)
        onboarding_progress = current_app.onboarding_service.get_onboarding_progress(user_id)
        
        response_data = {
            'success': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'full_name': user.get('full_name', ''),
                'subscription_tier': user.get('subscription_tier', 'free'),
                'phone_number': user.get('phone_number', ''),
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login')
            },
            'profile': profile,
            'onboarding_progress': onboarding_progress
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve profile'
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update current user profile"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate email if provided
        if 'email' in data:
            email = data['email'].strip().lower()
            if not validate_email(email):
                return jsonify({
                    'error': 'Invalid email format'
                }), 400
            
            # Check if email is already taken
            existing_user = current_app.user_service.get_user_by_email(email)
            if existing_user and existing_user['id'] != user_id:
                return jsonify({
                    'error': 'Email already in use',
                    'message': 'This email is already registered to another account'
                }), 409
        
        # Update user profile
        updated_user = current_app.user_service.update_user(user_id, data)
        
        if updated_user:
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'user': {
                    'id': updated_user['id'],
                    'email': updated_user['email'],
                    'full_name': updated_user.get('full_name', ''),
                    'subscription_tier': updated_user.get('subscription_tier', 'free'),
                    'phone_number': updated_user.get('phone_number', '')
                }
            })
        else:
            return jsonify({
                'error': 'Update failed',
                'message': 'Unable to update profile'
            }), 500
            
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Profile update failed due to server error'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({
                'error': 'Current password and new password are required'
            }), 400
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Verify current password and change password
        success = current_app.user_service.change_password(
            user_id, current_password, new_password
        )
        
        if success:
            # Revoke all user sessions to force re-authentication
            auth_middleware.revoke_user_sessions(user_id)
            
            return jsonify({
                'success': True,
                'message': 'Password changed successfully. Please log in again.'
            })
        else:
            return jsonify({
                'error': 'Password change failed',
                'message': 'Current password is incorrect'
            }), 400
            
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Password change failed due to server error'
        }), 500

@auth_bp.route('/subscription', methods=['GET'])
@require_auth
def get_subscription():
    """Get current user subscription information"""
    try:
        user_id = get_current_user_id()
        current_tier = get_current_user_tier()
        
        # Get subscription details from service
        subscription_info = current_app.subscription_service.get_user_subscription(user_id)
        
        return jsonify({
            'success': True,
            'subscription': {
                'tier': current_tier,
                'details': subscription_info
            }
        })
        
    except Exception as e:
        logger.error(f"Get subscription error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve subscription information'
        }), 500

@auth_bp.route('/sessions', methods=['GET'])
@require_auth
def get_active_sessions():
    """Get user's active sessions"""
    try:
        user_id = get_current_user_id()
        
        # Get active sessions from middleware
        user_sessions = auth_middleware.user_sessions.get(user_id, {})
        
        sessions = []
        for session_id, last_activity in user_sessions.items():
            sessions.append({
                'session_id': session_id,
                'last_activity': datetime.fromtimestamp(last_activity).isoformat(),
                'active': True
            })
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'max_sessions': auth_middleware.max_concurrent_sessions
        })
        
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve session information'
        }), 500

@auth_bp.route('/sessions', methods=['DELETE'])
@require_auth
def revoke_all_sessions():
    """Revoke all user sessions except current"""
    try:
        user_id = get_current_user_id()
        
        # Revoke all sessions
        auth_middleware.revoke_user_sessions(user_id)
        
        return jsonify({
            'success': True,
            'message': 'All sessions revoked successfully'
        })
        
    except Exception as e:
        logger.error(f"Revoke sessions error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to revoke sessions'
        }), 500
