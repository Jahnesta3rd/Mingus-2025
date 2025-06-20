"""
Simple Flask application with UserService and OnboardingService integration
"""

from flask import Flask, request, jsonify, session, current_app
from flask_cors import CORS
from backend.services.user_service import UserService
from backend.services.onboarding_service import OnboardingService
from backend.models.user import Base as UserBase
from backend.models.user_profile import Base as ProfileBase
from backend.models.onboarding_progress import Base as ProgressBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from loguru import logger

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5002"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://mingus_user:mingus_password@localhost/mingus_dev')

# Initialize database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist
UserBase.metadata.create_all(bind=engine)
ProfileBase.metadata.create_all(bind=engine)
ProgressBase.metadata.create_all(bind=engine)

# Initialize services
user_service = UserService(DATABASE_URL)
onboarding_service = OnboardingService(None, DATABASE_URL)

# Make services available globally
app.user_service = user_service
app.onboarding_service = onboarding_service

# Simple authentication check
def require_auth(f):
    """Simple decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/')
def index():
    return jsonify({'message': 'Mingus API is running'})

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        phone_number = data.get('phone_number', '').strip()
        
        if not email or not password or not full_name:
            return jsonify({'error': 'Email, password, and full_name are required'}), 400
        
        # Create user
        user_data = {
            'email': email,
            'password': password,
            'full_name': full_name,
            'phone_number': phone_number
        }
        
        user = user_service.create_user(user_data)
        
        if user:
            # Start onboarding process
            onboarding_record = onboarding_service.create_onboarding_record({
                'user_id': user['id'],
                'current_step': 'welcome'
            })
            
            # Create initial profile
            profile = onboarding_service.create_user_profile({
                'user_id': user['id']
            })
            
            return jsonify({
                'success': True,
                'message': 'User registered successfully',
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'full_name': user['full_name']
                }
            }), 201
        else:
            return jsonify({'error': 'Failed to create user account'}), 500
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Authenticate user
        user = user_service.authenticate_user(email, password)
        
        if user:
            # Store user in session
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_name'] = user['full_name']
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'full_name': user['full_name']
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logout successful'})

@app.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile"""
    try:
        user_id = session.get('user_id')
        
        profile = onboarding_service.get_user_profile(user_id)
        onboarding_progress = onboarding_service.get_onboarding_progress(user_id)
        
        return jsonify({
            'success': True,
            'profile': profile,
            'onboarding_progress': onboarding_progress
        }), 200
        
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        updated_profile = onboarding_service.update_user_profile(user_id, data)
        
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

@app.route('/api/onboarding/start', methods=['POST'])
@require_auth
def start_onboarding():
    """Start onboarding process"""
    try:
        user_id = session.get('user_id')
        
        onboarding_record = onboarding_service.create_onboarding_record({
            'user_id': user_id,
            'current_step': 'welcome'
        })
        
        if onboarding_record:
            return jsonify({
                'success': True,
                'message': 'Onboarding started successfully',
                'onboarding_record': onboarding_record
            }), 201
        else:
            return jsonify({'error': 'Failed to start onboarding'}), 500
            
    except Exception as e:
        logger.error(f"Start onboarding error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/onboarding/step/<step_name>', methods=['POST'])
@require_auth
def update_onboarding_step(step_name):
    """Update onboarding step"""
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        
        updated_progress = onboarding_service.update_onboarding_progress(
            user_id=user_id,
            step_name=step_name,
            is_completed=data.get('completed', True),
            responses=data.get('responses', {})
        )
        
        if updated_progress:
            return jsonify({
                'success': True,
                'message': f'Step {step_name} updated successfully',
                'progress': updated_progress
            }), 200
        else:
            return jsonify({'error': 'Failed to update step'}), 500
            
    except Exception as e:
        logger.error(f"Update step error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/onboarding/progress', methods=['GET'])
@require_auth
def get_onboarding_progress():
    """Get onboarding progress"""
    try:
        user_id = session.get('user_id')
        
        progress = onboarding_service.get_onboarding_progress(user_id)
        profile = onboarding_service.get_user_profile(user_id)
        
        if progress:
            return jsonify({
                'success': True,
                'progress': progress,
                'profile': profile
            }), 200
        else:
            return jsonify({'error': 'Onboarding progress not found'}), 404
            
    except Exception as e:
        logger.error(f"Get onboarding progress error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'authenticated': False}), 200
    
    user = user_service.get_user_by_id(user_id)
    
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

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    logger.info(f"Starting simple Flask app on port {port}")
    logger.info(f"Database URL: {DATABASE_URL}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 