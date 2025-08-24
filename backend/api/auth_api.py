"""
Authentication API
Comprehensive authentication and authorization endpoints with JWT tokens
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import logging
import re
from typing import Dict, Any, Optional

from ..middleware.rate_limiter import rate_limit
from ..middleware.validation import validate_request
from ..models.user import User
from ..services.auth_service import AuthService
from ..utils.response_utils import api_response, error_response

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Validation schemas
REGISTER_SCHEMA = {
    'email': {
        'required': True,
        'type': str,
        'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'max_length': 255
    },
    'password': {
        'required': True,
        'type': str,
        'min_length': 8,
        'max_length': 128,
        'pattern': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'
    },
    'full_name': {
        'required': True,
        'type': str,
        'min_length': 2,
        'max_length': 100
    },
    'phone_number': {
        'required': False,
        'type': str,
        'pattern': r'^\+?[\d\s\-\(\)]{10,}$'
    }
}

LOGIN_SCHEMA = {
    'email': {
        'required': True,
        'type': str,
        'max_length': 255
    },
    'password': {
        'required': True,
        'type': str,
        'max_length': 128
    },
    'remember_me': {
        'required': False,
        'type': bool
    }
}

PASSWORD_RESET_SCHEMA = {
    'email': {
        'required': True,
        'type': str,
        'max_length': 255
    }
}

PASSWORD_UPDATE_SCHEMA = {
    'current_password': {
        'required': True,
        'type': str,
        'max_length': 128
    },
    'new_password': {
        'required': True,
        'type': str,
        'min_length': 8,
        'max_length': 128,
        'pattern': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'
    }
}

@auth_bp.route('/register', methods=['POST'])
@rate_limit('register', max_requests=5, window=300)  # 5 requests per 5 minutes
@validate_request(REGISTER_SCHEMA)
def register():
    """
    Register a new user
    
    Request Body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe",
        "phone_number": "+1234567890"
    }
    """
    try:
        data = request.get_json()
        auth_service = AuthService()
        
        # Check if user already exists
        if auth_service.user_exists(data['email']):
            return error_response(
                'User already exists',
                'A user with this email address is already registered',
                409
            )
        
        # Create new user
        user = auth_service.create_user(
            email=data['email'],
            password=data['password'],
            full_name=data['full_name'],
            phone_number=data.get('phone_number')
        )
        
        # Generate tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        # Log successful registration
        logger.info(f"New user registered: {user.email}")
        
        return api_response(
            'User registered successfully',
            {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'created_at': user.created_at.isoformat()
                },
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires_in': 3600
                }
            },
            201
        )
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return error_response('Registration failed', str(e), 500)

@auth_bp.route('/login', methods=['POST'])
@rate_limit('login', max_requests=10, window=300)  # 10 requests per 5 minutes
@validate_request(LOGIN_SCHEMA)
def login():
    """
    Authenticate user and return JWT tokens
    
    Request Body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "remember_me": true
    }
    """
    try:
        data = request.get_json()
        auth_service = AuthService()
        
        # Authenticate user
        user = auth_service.authenticate_user(data['email'], data['password'])
        if not user:
            return error_response(
                'Authentication failed',
                'Invalid email or password',
                401
            )
        
        # Check if account is active
        if not user.is_active:
            return error_response(
                'Account disabled',
                'Your account has been disabled. Please contact support.',
                403
            )
        
        # Set token expiration based on remember_me
        access_expires = timedelta(hours=24 if data.get('remember_me') else 1)
        refresh_expires = timedelta(days=30 if data.get('remember_me') else 7)
        
        # Generate tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=access_expires
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=refresh_expires
        )
        
        # Update last login
        auth_service.update_last_login(user.id)
        
        # Log successful login
        logger.info(f"User logged in: {user.email}")
        
        return api_response(
            'Login successful',
            {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                },
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires_in': int(access_expires.total_seconds())
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return error_response('Login failed', str(e), 500)

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token
    """
    try:
        current_user_id = get_jwt_identity()
        auth_service = AuthService()
        
        # Verify user still exists and is active
        user = auth_service.get_user_by_id(current_user_id)
        if not user or not user.is_active:
            return error_response(
                'Invalid refresh token',
                'User not found or account disabled',
                401
            )
        
        # Generate new access token
        access_token = create_access_token(
            identity=current_user_id,
            expires_delta=timedelta(hours=1)
        )
        
        return api_response(
            'Token refreshed successfully',
            {
                'access_token': access_token,
                'expires_in': 3600
            }
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return error_response('Token refresh failed', str(e), 500)

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user and invalidate tokens
    """
    try:
        current_user_id = get_jwt_identity()
        jti = get_jwt()['jti']
        
        # Add token to blacklist
        auth_service = AuthService()
        auth_service.blacklist_token(jti)
        
        logger.info(f"User logged out: {current_user_id}")
        
        return api_response('Logout successful')
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return error_response('Logout failed', str(e), 500)

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get current user profile
    """
    try:
        current_user_id = get_jwt_identity()
        auth_service = AuthService()
        
        user = auth_service.get_user_by_id(current_user_id)
        if not user:
            return error_response('User not found', 'User profile not found', 404)
        
        return api_response(
            'Profile retrieved successfully',
            {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'phone_number': user.phone_number,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'preferences': user.preferences or {}
            }
        )
        
    except Exception as e:
        logger.error(f"Profile retrieval error: {str(e)}")
        return error_response('Profile retrieval failed', str(e), 500)

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
@validate_request({
    'full_name': {
        'required': False,
        'type': str,
        'min_length': 2,
        'max_length': 100
    },
    'phone_number': {
        'required': False,
        'type': str,
        'pattern': r'^\+?[\d\s\-\(\)]{10,}$'
    }
})
def update_profile():
    """
    Update current user profile
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        auth_service = AuthService()
        
        # Update user profile
        updated_user = auth_service.update_user_profile(
            user_id=current_user_id,
            full_name=data.get('full_name'),
            phone_number=data.get('phone_number')
        )
        
        if not updated_user:
            return error_response('User not found', 'User profile not found', 404)
        
        return api_response(
            'Profile updated successfully',
            {
                'id': updated_user.id,
                'email': updated_user.email,
                'full_name': updated_user.full_name,
                'phone_number': updated_user.phone_number,
                'updated_at': updated_user.updated_at.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return error_response('Profile update failed', str(e), 500)

@auth_bp.route('/password/reset', methods=['POST'])
@rate_limit('password_reset', max_requests=3, window=3600)  # 3 requests per hour
@validate_request(PASSWORD_RESET_SCHEMA)
def request_password_reset():
    """
    Request password reset email
    """
    try:
        data = request.get_json()
        auth_service = AuthService()
        
        # Send password reset email
        success = auth_service.send_password_reset_email(data['email'])
        
        # Always return success to prevent email enumeration
        return api_response(
            'Password reset email sent',
            'If an account with this email exists, a password reset link has been sent.'
        )
        
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return error_response('Password reset request failed', str(e), 500)

@auth_bp.route('/password/update', methods=['POST'])
@jwt_required()
@validate_request(PASSWORD_UPDATE_SCHEMA)
def update_password():
    """
    Update user password
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        auth_service = AuthService()
        
        # Verify current password and update
        success = auth_service.update_user_password(
            user_id=current_user_id,
            current_password=data['current_password'],
            new_password=data['new_password']
        )
        
        if not success:
            return error_response(
                'Password update failed',
                'Current password is incorrect',
                400
            )
        
        return api_response('Password updated successfully')
        
    except Exception as e:
        logger.error(f"Password update error: {str(e)}")
        return error_response('Password update failed', str(e), 500)

@auth_bp.route('/verify-email', methods=['POST'])
@jwt_required()
def verify_email():
    """
    Verify user email address
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('verification_token'):
            return error_response('Verification token required', 'Please provide verification token', 400)
        
        auth_service = AuthService()
        success = auth_service.verify_email(current_user_id, data['verification_token'])
        
        if not success:
            return error_response('Email verification failed', 'Invalid or expired verification token', 400)
        
        return api_response('Email verified successfully')
        
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return error_response('Email verification failed', str(e), 500)

@auth_bp.route('/check-auth', methods=['GET'])
@jwt_required()
def check_auth():
    """
    Check if current token is valid
    """
    try:
        current_user_id = get_jwt_identity()
        auth_service = AuthService()
        
        user = auth_service.get_user_by_id(current_user_id)
        if not user or not user.is_active:
            return error_response('Authentication failed', 'User not found or account disabled', 401)
        
        return api_response(
            'Authentication valid',
            {
                'user_id': user.id,
                'email': user.email,
                'is_active': user.is_active
            }
        )
        
    except Exception as e:
        logger.error(f"Auth check error: {str(e)}")
        return error_response('Authentication check failed', str(e), 500) 