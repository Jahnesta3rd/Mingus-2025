<<<<<<< HEAD
from flask import Blueprint, request, jsonify, render_template, current_app, session, redirect, url_for, flash
from backend.models.onboarding import (
    AnonymousOnboardingCreate,
    AnonymousOnboardingResponse,
    OnboardingStatus
)
from backend.models.important_dates import ImportantDateCreate, ImportantDateUpdate
from backend.middleware.auth import require_auth
from datetime import datetime, timedelta
import uuid
from loguru import logger
import jwt
from functools import wraps
from config import config
import os
import re
import hashlib
import secrets

api = Blueprint('api', __name__)

def hash_password(password):
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}${hash_obj.hexdigest()}"

def verify_password(password, hashed_password):
    """Verify password against hashed password"""
    try:
        salt, hash_value = hashed_password.split('$')
        hash_obj = hashlib.sha256((password + salt).encode())
        return hash_obj.hexdigest() == hash_value
    except:
        return False

def validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Password validation - minimum 8 characters, at least one letter and one number"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@api.route('/')
def index():
    return render_template('index.html')

@api.route('/login', methods=['GET'])
def login():
    return render_template('login orig.html')

@api.route('/login', methods=['POST'])
def login_submit():
    try:
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Basic validation
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login orig.html', error='Email and password are required')
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('login orig.html', error='Please enter a valid email address')
        
        # Here you would typically authenticate against your database
        # For now, we'll use a simple check against Supabase or your user service
        try:
            # Attempt to authenticate with Supabase
            # This is a placeholder - you'll need to implement actual authentication
            # based on your Supabase setup
            auth_result = current_app.user_service.authenticate_user(email, password)
            
            if auth_result.get('success'):
                # Store user session
                session['user_id'] = auth_result.get('user_id')
                session['email'] = email
                session['authenticated'] = True
                
                flash('Login successful!', 'success')
                return redirect(url_for('api.dashboard'))
            else:
                flash('Invalid email or password', 'error')
                return render_template('login orig.html', error='Invalid email or password')
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            flash('Authentication service error. Please try again.', 'error')
            return render_template('login orig.html', error='Authentication service error. Please try again.')
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        flash('An error occurred during login. Please try again.', 'error')
        return render_template('login orig.html', error='An error occurred during login. Please try again.')

@api.route('/register', methods=['GET'])
def register():
    return render_template('register.html')

@api.route('/register', methods=['POST'])
def register_submit():
    try:
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        
        # Basic validation
        if not email or not password or not confirm_password or not full_name:
            flash('All fields are required', 'error')
            return render_template('register.html', error='All fields are required')
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('register.html', error='Please enter a valid email address')
        
        password_valid, password_message = validate_password(password)
        if not password_valid:
            flash(password_message, 'error')
            return render_template('register.html', error=password_message)
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html', error='Passwords do not match')
        
        # Check if user already exists
        try:
            existing_user = current_app.user_service.get_user_by_email(email)
            if existing_user:
                flash('User with this email already exists', 'error')
                return render_template('register.html', error='User with this email already exists')
        except Exception as e:
            logger.error(f"Error checking existing user: {str(e)}")
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create new user
        try:
            user_data = {
                'email': email,
                'password': hashed_password,
                'full_name': full_name,
                'phone_number': phone_number,
                'created_at': datetime.utcnow()
            }
            
            # Create user in database
            new_user = current_app.user_service.create_user(user_data)
            
            if new_user:
                # Create user profile
                profile_data = {
                    'user_id': new_user.get('id'),
                    'full_name': full_name,
                    'phone_number': phone_number,
                    'onboarding_completed': False
                }
                
                current_app.onboarding_service.create_user_profile(profile_data)
                
                # Create onboarding record
                onboarding_data = {
                    'user_id': new_user.get('id'),
                    'step': 'profile',
                    'completed': False
                }
                
                current_app.onboarding_service.create_onboarding_record(onboarding_data)
                
                # Set session
                session['user_id'] = new_user.get('id')
                session['email'] = email
                session['authenticated'] = True
                
                flash('Registration successful! Welcome to Mingus!', 'success')
                return redirect(url_for('api.dashboard'))
            else:
                flash('Failed to create user account', 'error')
                return render_template('register.html', error='Failed to create user account')
                
        except Exception as e:
            logger.error(f"User creation error: {str(e)}")
            flash('Failed to create user account. Please try again.', 'error')
            return render_template('register.html', error='Failed to create user account. Please try again.')
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        flash('An error occurred during registration. Please try again.', 'error')
        return render_template('register.html', error='An error occurred during registration. Please try again.')

@api.route('/dashboard')
@require_auth
def dashboard():
    return render_template('dashboard.html')

@api.route('/onboarding')
@require_auth
def onboarding():
    return render_template('onboarding.html')

@api.route('/auth/callback')
def auth_callback():
    return render_template('auth_callback.html')

@api.route('/reset-password')
def reset_password():
    return render_template('reset_password.html')

@api.route('/api/important-dates', methods=['GET'])
@require_auth
async def get_important_dates():
    try:
        dates = await current_app.important_dates_service.get_important_dates()
        return jsonify(dates)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/onboarding/status', methods=['GET'])
@require_auth
async def get_onboarding_status():
    try:
        status = await current_app.onboarding_service.get_onboarding_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/onboarding/update', methods=['POST'])
@require_auth
async def update_onboarding():
    try:
        data = request.json
        result = await current_app.onboarding_service.update_onboarding_profile(request.user_id, data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
from flask import Blueprint, request, jsonify, render_template, current_app, session
from backend.models.onboarding import (
    AnonymousOnboardingCreate,
    OnboardingCreate,
    OnboardingUpdate
)
from backend.models.important_dates import ImportantDateCreate, ImportantDateUpdate
from backend.middleware.auth import require_auth
from datetime import datetime
import uuid
from loguru import logger
from pydantic import ValidationError
import asyncio
from app import async_route
import jwt
from functools import wraps

api = Blueprint('api', __name__)

def get_client_info():
    """Get client information from the request."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        request_data = request.get_json()
        if isinstance(request_data, dict):
            session_id = request_data.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())

    return {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'referrer': request.referrer,
        'session_id': session_id
    }

@api.route('/')
def root():
    return render_template('login.html')

@api.route('/app')
@require_auth
def main_app():
    return render_template('main_app.html')

@api.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
                
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({"error": "Email and password are required"}), 400
                
            # Here you would typically verify credentials with your auth service
            # For now, we'll just return a success response
            return jsonify({"message": "Login successful"}), 200
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return jsonify({"error": "Login failed"}), 500
            
    return render_template('login.html')
>>>>>>> 18b195ffe700f2ac1a508d162ad042b3b768c7ae

@api.route('/welcome')
def welcome():
    return render_template('welcome.html')

<<<<<<< HEAD
@api.route('/signup')
def signup_page():
    return render_template('signup.html')

@api.route('/api/onboarding/anonymous', methods=['POST'])
async def create_anonymous_onboarding():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Create anonymous onboarding record with required fields
        onboarding_data = AnonymousOnboardingCreate(
            session_id=str(uuid.uuid4()),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            financial_challenge=data.get('financial_challenge'),
            stress_handling=data.get('stress_handling', []),
            motivation=data.get('motivation', []),
            monthly_income=data.get('monthly_income', 0),
            monthly_expenses=data.get('monthly_expenses', 0),
            savings_goal=data.get('savings_goal', 0),
            risk_tolerance=data.get('risk_tolerance', 5),
            financial_knowledge=data.get('financial_knowledge', 5),
            preferred_contact_method=data.get('preferred_contact_method', 'email'),
            contact_info=data.get('contact_info')
        )
        
        result = await current_app.onboarding_service.create_anonymous_onboarding(onboarding_data)
        return jsonify(result.model_dump())
        
=======
@api.route('/onboarding')
def onboarding():
    return render_template('onboarding.html')

@api.route('/signup')
def signup_page():
    """Render the signup form."""
    session_id = request.cookies.get('session_id', str(uuid.uuid4()))
    return render_template('signup.html', session_id=session_id)

@api.route('/api/onboarding/anonymous', methods=['POST'])
@async_route
async def create_anonymous_onboarding():
    """Create an anonymous onboarding response."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Empty request body"}), 400
            
        # Get and validate client info
        client_info = get_client_info()
        
        # Combine data with client info
        complete_data = {**data, **client_info}
        
        # Create anonymous onboarding
        validated_data = AnonymousOnboardingCreate(**complete_data)
        result = await current_app.onboarding_service.create_anonymous_onboarding(validated_data)
        
        response = jsonify(result.model_dump())
        
        # Set session cookie if not already set
        if not request.cookies.get('session_id'):
            response.set_cookie(
                'session_id',
                client_info['session_id'],
                max_age=30*24*60*60,  # 30 days
                httponly=True,
                secure=True,
                samesite='Strict'
            )
        
        return response, 201
        
    except ValidationError as e:
        return jsonify({
            "error": "Validation error",
            "details": e.errors()
        }), 400
>>>>>>> 18b195ffe700f2ac1a508d162ad042b3b768c7ae
    except Exception as e:
        logger.error(f"Error creating anonymous onboarding: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

<<<<<<< HEAD
@api.route('/api/onboarding/stats', methods=['GET'])
@require_auth
async def get_onboarding_stats():
    try:
        stats = await current_app.onboarding_service.get_onboarding_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting onboarding stats: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/validate-token', methods=['POST'])
def validate_token():
    try:
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({"error": "No token provided"}), 400
            
        token = data['token']
        jwt_secret = current_app.config.get('SUPABASE_JWT_SECRET')
        
        if not jwt_secret:
            return jsonify({"error": "Server configuration error"}), 500
            
        try:
            decoded = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            session['user_id'] = decoded.get('sub')
            session['email'] = decoded.get('email')
            return jsonify({"valid": True})
        except jwt.InvalidTokenError:
            return jsonify({"valid": False, "error": "Invalid token"}), 401
            
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/auth', methods=['GET'])
@require_auth
def get_auth_status():
    return jsonify({"authenticated": True})

@api.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('api.login')) 
=======
@api.route('/api/onboarding/anonymous/<session_id>', methods=['GET'])
@async_route
async def get_anonymous_onboarding(session_id: str):
    """Get anonymous onboarding responses for a session."""
    try:
        result = await current_app.onboarding_service.get_anonymous_onboarding(session_id)
        if not result:
            return jsonify({"error": "No onboarding responses found"}), 404
        return jsonify([response.model_dump() for response in result])
    except Exception as e:
        logger.error(f"Error fetching anonymous onboarding: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/anonymous/convert', methods=['POST'])
@require_auth
@async_route
async def convert_anonymous_to_user():
    """Convert anonymous responses to user responses after signup."""
    try:
        data = request.get_json()
        if not data or 'session_id' not in data:
            return jsonify({"error": "session_id is required"}), 400
            
        result = await current_app.onboarding_service.convert_anonymous_to_user(
            session_id=data['session_id'],
            user_id=request.user_id
        )
        return jsonify(result.model_dump())
    except Exception as e:
        logger.error(f"Error converting anonymous onboarding: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/anonymous/stats', methods=['GET'])
@async_route
async def get_anonymous_onboarding_stats():
    """Get statistics about anonymous onboarding responses."""
    try:
        result = await current_app.onboarding_service.get_anonymous_onboarding_stats()
        return jsonify(result.model_dump())
    except Exception as e:
        logger.error(f"Error fetching anonymous onboarding stats: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/profile', methods=['POST'])
@require_auth
@async_route
async def create_onboarding():
    try:
        data = request.get_json()
        onboarding_data = OnboardingCreate(**data)
        result = await current_app.onboarding_service.create_onboarding_profile(
            request.user_id,
            onboarding_data
        )
        return jsonify(result.model_dump()), 201
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"Error creating onboarding profile: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/profile', methods=['GET'])
@require_auth
@async_route
async def get_onboarding():
    try:
        result = await current_app.onboarding_service.get_onboarding_profile(request.user_id)
        if not result:
            return jsonify({"error": "Onboarding profile not found"}), 404
        return jsonify(result.model_dump())
    except Exception as e:
        logger.error(f"Error fetching onboarding profile: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/profile', methods=['PUT'])
@require_auth
@async_route
async def update_onboarding():
    try:
        data = request.get_json()
        update_data = OnboardingUpdate(**data)
        result = await current_app.onboarding_service.update_onboarding_profile(
            request.user_id,
            update_data
        )
        return jsonify(result.model_dump())
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"Error updating onboarding profile: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/status', methods=['GET'])
@require_auth
@async_route
async def check_onboarding_status():
    try:
        result = await current_app.onboarding_service.check_onboarding_status(request.user_id)
        return jsonify(result.model_dump())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error checking onboarding status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/stats', methods=['GET'])
@require_auth
@async_route
async def get_onboarding_stats():
    try:
        result = await current_app.onboarding_service.get_onboarding_stats()
        return jsonify(result.model_dump())
    except Exception as e:
        logger.error(f"Error fetching onboarding stats: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/reset-password')
def reset_password():
    return render_template('reset_password.html')

@api.route('/reset-password-confirm')
def reset_password_confirm():
    return render_template('reset_password_confirm.html')

@api.route('/validate-token', methods=['POST'])
def validate_token():
    token = request.json.get('token')
    if not token:
        return jsonify({"error": "No token provided"}), 400
        
    try:
        # In development, just verify token format
        if current_app.config['ENV'] == 'development':
            jwt.decode(token, options={"verify_signature": False})
            return jsonify({"valid": True}), 200
            
        # In production, verify with Supabase secret
        jwt_secret = current_app.config.get('SUPABASE_JWT_SECRET')
        if not jwt_secret:
            return jsonify({"error": "Server configuration error"}), 500
            
        decoded = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        return jsonify({
            "valid": True,
            "user": {
                "id": decoded.get('sub'),
                "email": decoded.get('email')
            }
        }), 200
        
    except jwt.InvalidTokenError as e:
        return jsonify({"error": str(e)}), 401

@api.route('/set-auth-cookie', methods=['POST'])
def set_auth_cookie():
    token = request.json.get('token')
    if not token:
        return jsonify({"error": "No token provided"}), 400
        
    try:
        # Validate token first
        jwt_secret = current_app.config.get('SUPABASE_JWT_SECRET')
        if not jwt_secret:
            return jsonify({"error": "Server configuration error"}), 500
            
        decoded = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        
        # Set session data
        session['user_id'] = decoded.get('sub')
        session['email'] = decoded.get('email')
        
        return jsonify({"success": True}), 200
        
    except jwt.InvalidTokenError as e:
        return jsonify({"error": str(e)}), 401

@api.route('/set-session', methods=['POST'])
def set_session():
    data = request.json
    if not data or not data.get('token') or not data.get('user'):
        return jsonify({"error": "Invalid request data"}), 400
        
    try:
        # In development, just verify token format
        if current_app.config['ENV'] == 'development':
            jwt.decode(data['token'], options={"verify_signature": False})
        else:
            # In production, verify with Supabase secret
            jwt_secret = current_app.config.get('SUPABASE_JWT_SECRET')
            if not jwt_secret:
                return jsonify({"error": "Server configuration error"}), 500
            jwt.decode(data['token'], jwt_secret, algorithms=['HS256'])
        
        # Set session data
        session['user_id'] = data['user'].get('id')
        session['email'] = data['user'].get('email')
        
        return jsonify({"success": True}), 200
        
    except jwt.InvalidTokenError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": "Failed to set session"}), 500 
>>>>>>> 18b195ffe700f2ac1a508d162ad042b3b768c7ae
