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
            
            # Create user with email_verified=False initially
            user_data = {
                'email': email,
                'password': password,
                'full_name': full_name,
                'phone_number': phone_number,
                'email_verified': False  # New users start unverified
            }
            
            user = current_app.user_service.create_user(user_data)
            
            if user:
                # Store user in session to persist login state
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                session['user_name'] = user['full_name']
                
                # Send email verification
                try:
                    from backend.services.email_verification_service import EmailVerificationService
                    verification_service = EmailVerificationService()
                    
                    # Get client information for security
                    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                    user_agent = request.headers.get('User-Agent', '')
                    
                    # Create verification record
                    verification, token = verification_service.create_verification(
                        user_id=user['id'],
                        email=email,
                        verification_type='signup',
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    
                    # Send verification email asynchronously
                    from backend.tasks.email_verification_tasks import send_verification_email
                    send_verification_email.delay(
                        user_id=user['id'],
                        email=email,
                        verification_type='signup'
                    )
                    
                    logger.info(f"Verification email sent for new user {user['id']} at {email}")
                    
                except Exception as e:
                    logger.error(f"Failed to send verification email for user {user['id']}: {e}")
                    # Continue with registration even if verification fails
                
                # Return success response with verification notice
                return jsonify({
                    'success': True,
                    'message': 'Registration successful. Please check your email to verify your account.',
                    'user': {
                        'id': user['id'],
                        'email': user['email'],
                        'full_name': user['full_name'],
                        'email_verified': user.get('email_verified', False)
                    },
                    'verification_required': True,
                    'verification_sent': True
                }), 201
            else:
                return jsonify({'error': 'Failed to create user'}), 500
                
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
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
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Get user by email
        user = current_app.user_service.get_user_by_email(email)
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Verify password
        if not current_app.user_service.verify_password(user['id'], password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if user is active
        if user.get('is_active') == False:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Store user in session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = user['full_name']
        
        # Check email verification status
        email_verified = user.get('email_verified', False)
        
        # Return user data with verification status
        response_data = {
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'email_verified': email_verified
            }
        }
        
        # Add verification notice if email is not verified
        if not email_verified:
            response_data['verification_required'] = True
            response_data['message'] = 'Login successful. Please verify your email to access all features.'
            
            # Check if verification email was recently sent
            try:
                from backend.services.email_verification_service import EmailVerificationService
                verification_service = EmailVerificationService()
                pending_verification = verification_service.get_pending_verification(user['id'])
                
                if pending_verification:
                    response_data['verification_pending'] = True
                    response_data['verification_expires_at'] = pending_verification.expires_at.isoformat() if pending_verification.expires_at else None
                else:
                    # Offer to resend verification
                    response_data['verification_resend_available'] = True
                    
            except Exception as e:
                logger.warning(f"Could not check verification status: {e}")
        
        return jsonify(response_data), 200
        
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
        
        # Add verification status to profile
        profile_data = {
            'success': True,
            'user': user,
            'profile': profile,
            'onboarding_progress': onboarding_progress,
            'email_verification': {
                'verified': user.get('email_verified', False),
                'required': not user.get('email_verified', False)
            }
        }
        
        # Add verification details if not verified
        if not user.get('email_verified', False):
            try:
                from backend.services.email_verification_service import EmailVerificationService
                verification_service = EmailVerificationService()
                pending_verification = verification_service.get_pending_verification(user_id)
                
                if pending_verification:
                    profile_data['email_verification']['pending'] = True
                    profile_data['email_verification']['expires_at'] = pending_verification.expires_at.isoformat() if pending_verification.expires_at else None
                    profile_data['email_verification']['verification_type'] = pending_verification.verification_type
                else:
                    profile_data['email_verification']['resend_available'] = True
                    
            except Exception as e:
                logger.warning(f"Could not get verification details: {e}")
        
        return jsonify(profile_data), 200
        
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
        
        # Return authentication status with verification info
        auth_data = {
            'authenticated': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'email_verified': user.get('email_verified', False)
            }
        }
        
        # Add verification status
        if not user.get('email_verified', False):
            auth_data['verification_required'] = True
            
            # Check pending verification
            try:
                from backend.services.email_verification_service import EmailVerificationService
                verification_service = EmailVerificationService()
                pending_verification = verification_service.get_pending_verification(user_id)
                
                if pending_verification:
                    auth_data['verification_pending'] = True
                    auth_data['verification_expires_at'] = pending_verification.expires_at.isoformat() if pending_verification.expires_at else None
                    
            except Exception as e:
                logger.warning(f"Could not check verification status: {e}")
        
        return jsonify(auth_data), 200
        
    except Exception as e:
        logger.error(f"Check auth error: {str(e)}")
        return jsonify({'authenticated': False}), 200

@auth_bp.route('/verification-status', methods=['GET'])
def get_verification_status():
    """Get email verification status for current user"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get user data
        user = current_app.user_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get verification status
        verification_status = {
            'verified': user.get('email_verified', False),
            'email': user['email']
        }
        
        # If not verified, get pending verification details
        if not verification_status['verified']:
            try:
                from backend.services.email_verification_service import EmailVerificationService
                verification_service = EmailVerificationService()
                pending_verification = verification_service.get_pending_verification(user_id)
                
                if pending_verification:
                    verification_status['pending'] = True
                    verification_status['expires_at'] = pending_verification.expires_at.isoformat() if pending_verification.expires_at else None
                    verification_status['verification_type'] = pending_verification.verification_type
                    verification_status['resend_available'] = verification_service.can_resend_verification(user_id)
                else:
                    verification_status['resend_available'] = True
                    
            except Exception as e:
                logger.error(f"Error getting verification status: {e}")
                verification_status['error'] = 'Could not retrieve verification details'
        
        return jsonify({
            'success': True,
            'verification': verification_status
        }), 200
        
    except Exception as e:
        logger.error(f"Get verification status error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500 