"""
Authentication routes blueprint
"""

from flask import Blueprint, request, jsonify, session, current_app, render_template, redirect
from loguru import logger
from werkzeug.security import generate_password_hash
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> tuple[bool, str]:
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

@auth_bp.route('/login', methods=['GET'])
def login_form():
    """Show login form"""
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET']) 
def register_form():
    """Show registration form"""
    return render_template('register.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        # Track performance metrics
        from backend.monitoring.performance_monitoring import performance_monitor
        from backend.optimization.cache_manager import cache_manager
        
        with performance_monitor.api_timer('/api/auth/register', 'POST'):
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate required fields
            required_fields = ['email', 'password', 'first_name', 'last_name']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'{field} is required'}), 400
            
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            phone_number = data.get('phone_number', '').strip()
            
            # Combine first and last name for full_name
            full_name = f"{first_name} {last_name}".strip()
            
            # Validate email format
            if not validate_email(email):
                return jsonify({'error': 'Invalid email format'}), 400
            
            # Validate password strength
            password_valid, password_message = validate_password_strength(password)
            if not password_valid:
                return jsonify({'error': password_message}), 400
            
            # Check if user already exists
            existing_user = current_app.user_service.get_user_by_email(email)
            if existing_user:
                return jsonify({'error': 'User with this email already exists'}), 409
            
            # Create user
            user_data = {
                'email': email,
                'password': password,
                'full_name': full_name,
                'phone_number': phone_number
            }
            
            user = current_app.user_service.create_user(user_data)
            
            if user:
                # Store user in session to persist login state
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                session['user_name'] = user['full_name']

                # Track user registration
                from backend.analytics.business_intelligence import business_intelligence
                business_intelligence.track_user_metric(
                    user['id'], 
                    'registration', 
                    1.0,
                    {'email': email, 'full_name': full_name}
                )
                
                # After user completes registration, redirect to onboarding
                if not current_app.onboarding_service.is_onboarding_complete(user['id']):
                    return redirect('/api/onboarding/choice')
                else:
                    return redirect('/dashboard')
            else:
                return jsonify({'error': 'Failed to create user account'}), 500
                
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Authenticate user
        user = current_app.user_service.authenticate_user(email, password)
        
        if user:
            # Store user in session
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_name'] = user['full_name']
            
            # Get onboarding progress
            onboarding_progress = current_app.onboarding_service.get_onboarding_progress(user['id'])
            if not onboarding_progress or not onboarding_progress.get('is_complete', False):
                return redirect('/api/onboarding/choice')
            user_profile = current_app.onboarding_service.get_user_profile(user['id'])
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'phone_number': user['phone_number']
                },
                'onboarding_progress': onboarding_progress,
                'profile': user_profile
            }), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        # Clear session
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get current user profile"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get user data
        user = current_app.user_service.get_user_by_id(user_id)
        profile = current_app.onboarding_service.get_user_profile(user_id)
        onboarding_progress = current_app.onboarding_service.get_onboarding_progress(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': user,
            'profile': profile,
            'onboarding_progress': onboarding_progress
        }), 200
        
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update current user profile"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update user profile
        updated_profile = current_app.onboarding_service.update_user_profile(user_id, data)
        
        if updated_profile:
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'profile': updated_profile
            }), 200
        else:
            return jsonify({'error': 'Failed to update profile'}), 500
            
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'authenticated': False}), 200
        
        # Get user data
        user = current_app.user_service.get_user_by_id(user_id)
        
        if not user:
            session.clear()
            return jsonify({'authenticated': False}), 200
        
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Check auth error: {str(e)}")
        return jsonify({'authenticated': False}), 200 