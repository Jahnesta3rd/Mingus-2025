#!/usr/bin/env python3
"""
Enhanced Authentication Routes for MINGUS Assessment System
Integrates secure JWT validation, brute force protection, and session security
"""

from flask import Blueprint, request, jsonify, current_app, g
from backend.middleware.enhanced_auth import (
    require_auth, require_secure_auth, get_current_user_id, 
    logout_user, create_auth_response, validate_auth_request,
    handle_auth_error
)
from backend.security.brute_force_protection import get_brute_force_protection
from backend.security.secure_jwt_manager import get_jwt_manager
from backend.security.secure_session_manager import get_session_manager
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Enhanced login endpoint with security features"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate request data
        validation_result = validate_auth_request(data)
        if not validation_result['valid']:
            return jsonify({
                "error": "Invalid request data",
                "details": validation_result['errors']
            }), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        captcha_token = data.get('captcha_token')
        
        # Get security components
        brute_force_protection = get_brute_force_protection()
        
        # Check if account is locked out
        if brute_force_protection.is_locked_out(email, 'login'):
            lockout_info = brute_force_protection.get_lockout_info(email, 'login')
            return jsonify(handle_auth_error('account_locked', {
                'lockout_until': lockout_info.get('lockout_until'),
                'remaining_lockout': lockout_info.get('remaining_lockout')
            })), 423
        
        # Check if captcha is required
        lockout_info = brute_force_protection.get_lockout_info(email, 'login')
        if lockout_info.get('attempts', 0) >= 3 and not captcha_token:
            return jsonify({
                "error": "Captcha required",
                "require_captcha": True,
                "attempts": lockout_info.get('attempts', 0)
            }), 400
        
        # Validate credentials (implement with your user service)
        user = validate_user_credentials(email, password)
        
        if user:
            # Record successful login
            brute_force_protection.record_successful_attempt(email, 'login')
            
            # Create authentication response
            response_data = create_auth_response(user['id'], remember_me)
            
            logger.info(f"Successful login for user {email}")
            return jsonify(response_data)
        else:
            # Record failed login attempt
            lockout_result = brute_force_protection.record_failed_attempt(email, 'login')
            
            response_data = handle_auth_error('invalid_credentials', {
                'attempts': lockout_result.get('attempts', 0),
                'remaining_attempts': lockout_result.get('remaining_attempts', 0)
            })
            
            if lockout_result.get('locked'):
                response_data.update({
                    'account_locked': True,
                    'lockout_until': lockout_result.get('lockout_until'),
                    'lockout_duration': lockout_result.get('lockout_duration')
                })
                return jsonify(response_data), 423
            
            if lockout_result.get('require_captcha'):
                response_data['require_captcha'] = True
            
            logger.warning(f"Failed login attempt for email {email}")
            return jsonify(response_data), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Enhanced logout endpoint with security cleanup"""
    try:
        # Perform enhanced logout
        logout_user()
        
        return jsonify({"success": True, "message": "Logged out successfully"})
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/refresh', methods=['POST'])
@require_auth
def refresh_token():
    """Refresh authentication token"""
    try:
        jwt_manager = get_jwt_manager()
        
        # Get current token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "No token provided"}), 401
        
        token = auth_header[7:]
        
        # Refresh token
        new_token = jwt_manager.refresh_token(token)
        
        if new_token:
            return jsonify({
                "success": True,
                "token": new_token
            })
        else:
            return jsonify({"error": "Token refresh failed"}), 401
            
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/validate', methods=['POST'])
def validate_token():
    """Validate authentication token"""
    try:
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({"error": "No token provided"}), 400
        
        token = data['token']
        jwt_manager = get_jwt_manager()
        
        # Validate token
        result = jwt_manager.validate_secure_token(token)
        
        if result.get('valid'):
            return jsonify({
                "valid": True,
                "user_id": result['payload'].get('sub'),
                "expires_at": result['payload'].get('exp')
            })
        else:
            return jsonify({
                "valid": False,
                "reason": result.get('reason', 'Invalid token')
            }), 401
            
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/status', methods=['GET'])
@require_auth
def get_auth_status():
    """Get current authentication status"""
    try:
        user_info = get_current_user_info()
        
        if user_info:
            return jsonify({
                "authenticated": True,
                "user_id": user_info.get('user_id'),
                "auth_method": user_info.get('auth_method'),
                "session_info": user_info.get('session_data')
            })
        else:
            return jsonify({"authenticated": False}), 401
            
    except Exception as e:
        logger.error(f"Auth status error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/sessions', methods=['GET'])
@require_auth
def get_user_sessions():
    """Get all active sessions for current user"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        session_manager = get_session_manager()
        sessions = session_manager.get_user_sessions(user_id)
        
        return jsonify({
            "sessions": sessions,
            "total_sessions": len(sessions)
        })
        
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/sessions/<session_id>', methods=['DELETE'])
@require_auth
def revoke_session(session_id):
    """Revoke a specific session"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        session_manager = get_session_manager()
        session_manager.revoke_session(session_id, user_id)
        
        return jsonify({"success": True, "message": "Session revoked"})
        
    except Exception as e:
        logger.error(f"Revoke session error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/sessions/all', methods=['DELETE'])
@require_auth
def revoke_all_sessions():
    """Revoke all sessions for current user"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        session_manager = get_session_manager()
        session_manager.revoke_all_user_sessions(user_id)
        
        return jsonify({"success": True, "message": "All sessions revoked"})
        
    except Exception as e:
        logger.error(f"Revoke all sessions error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/security/events', methods=['GET'])
@require_secure_auth
def get_security_events():
    """Get security events for current user"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        hours = request.args.get('hours', 24, type=int)
        
        # Get events from all security components
        jwt_manager = get_jwt_manager()
        brute_force_protection = get_brute_force_protection()
        session_manager = get_session_manager()
        
        jwt_events = jwt_manager.get_security_events(user_id=user_id, hours=hours)
        brute_force_events = brute_force_protection.get_security_events(user_id=user_id, hours=hours)
        session_events = session_manager.get_security_events(user_id=user_id, hours=hours)
        
        return jsonify({
            "jwt_events": [event.__dict__ for event in jwt_events],
            "brute_force_events": [event.__dict__ for event in brute_force_events],
            "session_events": [event.__dict__ for event in session_events],
            "total_events": len(jwt_events) + len(brute_force_events) + len(session_events)
        })
        
    except Exception as e:
        logger.error(f"Get security events error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/security/suspicious-activity', methods=['GET'])
@require_secure_auth
def get_suspicious_activity():
    """Get suspicious activity for current user"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        hours = request.args.get('hours', 24, type=int)
        
        brute_force_protection = get_brute_force_protection()
        suspicious_activity = brute_force_protection.get_suspicious_activity(hours)
        
        # Filter for current user
        user_suspicious = [event for event in suspicious_activity 
                         if event.get('identifier') == user_id]
        
        return jsonify({
            "suspicious_events": user_suspicious,
            "total_events": len(user_suspicious)
        })
        
    except Exception as e:
        logger.error(f"Get suspicious activity error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/security/lockout-info', methods=['GET'])
def get_lockout_info():
    """Get lockout information for an identifier"""
    try:
        identifier = request.args.get('identifier')
        action_type = request.args.get('action_type', 'login')
        
        if not identifier:
            return jsonify({"error": "Identifier required"}), 400
        
        brute_force_protection = get_brute_force_protection()
        lockout_info = brute_force_protection.get_lockout_info(identifier, action_type)
        
        return jsonify(lockout_info)
        
    except Exception as e:
        logger.error(f"Get lockout info error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def validate_user_credentials(email: str, password: str) -> dict:
    """Validate user credentials (implement with your user service)"""
    # This is a placeholder - implement with your actual user authentication
    # Example implementation:
    """
    from your_models import User
    from werkzeug.security import check_password_hash
    
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
    return None
    """
    
    # For demonstration purposes, accept any email/password combination
    # In production, implement proper user authentication
    if email and password:
        return {
            'id': f'user_{email.split("@")[0]}',
            'email': email,
            'first_name': 'Demo',
            'last_name': 'User'
        }
    return None
