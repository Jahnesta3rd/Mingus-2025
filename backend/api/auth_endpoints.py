#!/usr/bin/env python3
"""
Authentication API Endpoints
Handles user registration, login, and token verification
"""

import os
import secrets
import uuid
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import logging

from backend.models.database import db
from backend.models.user_models import User
from backend.utils.password import hash_password, check_password, verify_password_strength

# Simple rate limiting (in-memory)
_rate_limit_store = {}
_rate_limit_max = 100  # requests per minute
_rate_limit_window = 60  # seconds

def check_rate_limit(client_ip: str) -> bool:
    """Simple rate limiting check"""
    import time
    current_time = time.time()
    
    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []
    
    # Clean old requests
    _rate_limit_store[client_ip] = [
        req_time for req_time in _rate_limit_store[client_ip]
        if current_time - req_time < _rate_limit_window
    ]
    
    # Check limit
    if len(_rate_limit_store[client_ip]) >= _rate_limit_max:
        return False
    
    # Add current request
    _rate_limit_store[client_ip].append(current_time)
    return True

def validate_csrf_token(token: str) -> bool:
    """Simple CSRF token validation - for auth endpoints, we'll be lenient"""
    # For registration/login, we can be more lenient
    # In production, implement proper CSRF token validation
    if not token:
        return False
    # Basic check - token should exist and not be empty
    return len(token) > 0

logger = logging.getLogger(__name__)

# Create blueprint
auth_api = Blueprint('auth_api', __name__, url_prefix='/api/auth')

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-jwt-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))  # 24 hours


def generate_jwt_token(user_id: str, email: str) -> str:
    """Generate JWT token for authenticated user"""
    expiration = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': expiration,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


@auth_api.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    """
    try:
        # Rate limiting check
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        
        # Get JSON data - handle both application/json and form data
        if request.is_json:
            data = request.get_json()
        else:
            # Try to parse as JSON from raw data
            try:
                import json
                data = json.loads(request.data.decode('utf-8'))
            except:
                data = request.form.to_dict()
        
        if not data:
            logger.warning("No data provided in registration request")
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        if not password:
            return jsonify({'success': False, 'error': 'Password is required'}), 400
        
        if not first_name:
            return jsonify({'success': False, 'error': 'First name is required'}), 400
        
        # Validate email format
        if '@' not in email or '.' not in email.split('@')[1]:
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate password strength (relaxed - just check length)
        if len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters long'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'error': 'User with this email already exists'}), 409
        
        # Generate unique user_id
        user_id = str(uuid.uuid4())
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create new user
        new_user = User(
            user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name if last_name else None,
            password_hash=password_hash,  # Store hashed password
            tier='budget',  # Default tier
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate JWT token
        token = generate_jwt_token(user_id, email)
        
        logger.info(f"User registered successfully: {email}")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'email': email,
            'name': first_name,
            'token': token,
            'message': 'Registration successful'
        }), 201
        
    except ValueError as e:
        logger.error(f"Registration validation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        db.session.rollback()
        # Return more detailed error in development, generic in production
        error_msg = str(e) if os.environ.get('FLASK_ENV') == 'development' else 'Registration failed. Please try again.'
        return jsonify({'success': False, 'error': error_msg}), 500


@auth_api.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token
    """
    try:
        # Rate limiting check
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        
        data = request.get_json()
        
        if not data:
            raise BadRequest("No data provided")
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Check password
        if not user.password_hash:
            logger.warning(f"User {email} has no password hash")
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        if not check_password(password, user.password_hash):
            logger.warning(f"Invalid password attempt for: {email}")
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Update last activity
        user.last_activity = datetime.utcnow()
        db.session.commit()
        
        # Generate JWT token
        token = generate_jwt_token(user.user_id, user.email)
        
        logger.info(f"User logged in successfully: {email}")
        
        return jsonify({
            'success': True,
            'user_id': user.user_id,
            'email': user.email,
            'name': user.first_name or user.email,
            'token': token,
            'message': 'Login successful'
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'error': 'Login failed. Please try again.'}), 500


@auth_api.route('/verify', methods=['GET'])
def verify_token():
    """
    Verify JWT token and return user information
    """
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Missing or invalid Authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get('user_id')
            email = payload.get('email')
            
            # Verify user still exists
            user = User.query.filter_by(user_id=user_id, email=email).first()
            
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            return jsonify({
                'success': True,
                'user_id': user.user_id,
                'email': user.email,
                'name': user.first_name or user.email
            }), 200
            
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
            
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({'success': False, 'error': 'Token verification failed'}), 500
