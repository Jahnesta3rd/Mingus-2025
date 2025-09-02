"""
Email Verification Routes for MINGUS Flask Application
Comprehensive endpoints for email verification with security and cultural awareness
"""

from flask import Blueprint, request, jsonify, current_app, g
from flask_cors import cross_origin
from loguru import logger
import os
from datetime import datetime
from typing import Dict, Any, Optional

from ..services.email_verification_service import EmailVerificationService
from ..middleware.rate_limit_decorators import rate_limit, rate_limit_by_user
from ..middleware.enhanced_auth import login_required
from ..utils.validation import validate_email_format
from ..utils.security import sanitize_input, validate_csrf_token

# Initialize blueprint
email_verification_bp = Blueprint('email_verification', __name__, url_prefix='/api/email-verification')

# Initialize service
email_verification_service = EmailVerificationService()

@email_verification_bp.route('/send', methods=['POST'])
@cross_origin()
@rate_limit('email_verification', {'requests': '5', 'window': '3600'})  # 5 requests per hour
def send_verification_email():
    """
    Send verification email to user
    
    Rate limited to prevent abuse
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        verification_type = data.get('verification_type', 'signup')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Validate email format
        if not validate_email_format(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate verification type
        allowed_types = ['signup', 'email_change', 'password_reset']
        if verification_type not in allowed_types:
            return jsonify({'error': 'Invalid verification type'}), 400
        
        # Get user by email
        user = current_app.user_service.get_user_by_email(email)
        if not user:
            # Don't reveal if user exists (security best practice)
            return jsonify({'message': 'If an account exists, a verification email has been sent'}), 200
        
        # Check if user is already verified
        if user.get('email_verified') and verification_type == 'signup':
            return jsonify({'message': 'Email is already verified'}), 200
        
        # Get client information for security
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Create verification record
        verification, token = email_verification_service.create_verification(
            user_id=user['id'],
            email=email,
            verification_type=verification_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Send verification email asynchronously
        from ..tasks.email_verification_tasks import send_verification_email
        send_verification_email.delay(
            user_id=user['id'],
            email=email,
            verification_type=verification_type
        )
        
        # Log the request
        logger.info(f"Verification email requested for user {user['id']} at {email}")
        
        return jsonify({
            'message': 'Verification email sent successfully',
            'verification_type': verification_type,
            'expires_at': verification.expires_at.isoformat() if verification.expires_at else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        return jsonify({'error': 'Failed to send verification email'}), 500

@email_verification_bp.route('/verify', methods=['POST'])
@cross_origin()
@rate_limit('email_verification', {'requests': '10', 'window': '3600'})  # 10 attempts per hour
def verify_email():
    """
    Verify email using token
    
    Rate limited to prevent brute force attacks
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        token = data.get('token', '').strip()
        user_id = data.get('user_id')  # Optional for additional validation
        
        if not token:
            return jsonify({'error': 'Verification token is required'}), 400
        
        # Sanitize and validate input
        token = sanitize_input(token)
        if len(token) < 10:  # Basic token length validation
            return jsonify({'error': 'Invalid token format'}), 400
        
        # Get client information for security
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Verify the email
        success, message, user_data = email_verification_service.verify_email(token, user_id)
        
        if success:
            logger.info(f"Email verified successfully for user {user_data['id'] if user_data else 'unknown'}")
            return jsonify({
                'message': message,
                'verified': True,
                'user': user_data
            }), 200
        else:
            logger.warning(f"Email verification failed: {message}")
            return jsonify({
                'error': message,
                'verified': False
            }), 400
        
    except Exception as e:
        logger.error(f"Error during email verification: {e}")
        return jsonify({'error': 'Verification failed'}), 500

@email_verification_bp.route('/resend', methods=['POST'])
@cross_origin()
@login_required
@rate_limit_by_user('email_verification_resend', {'requests': '3', 'window': '3600'})  # 3 resends per hour per user
def resend_verification():
    """
    Resend verification email to authenticated user
    
    Rate limited per user to prevent abuse
    """
    try:
        # Get authenticated user
        user_id = g.user_id
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        
        # Get user details
        user = current_app.user_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if already verified
        if user.get('email_verified'):
            return jsonify({'message': 'Email is already verified'}), 200
        
        # Resend verification
        success, message = email_verification_service.resend_verification(user_id, email)
        
        if success:
            logger.info(f"Verification email resent to user {user_id}")
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 400
        
    except Exception as e:
        logger.error(f"Error resending verification email: {e}")
        return jsonify({'error': 'Failed to resend verification email'}), 500

@email_verification_bp.route('/change-email', methods=['POST'])
@cross_origin()
@login_required
@rate_limit_by_user('email_change', {'requests': '2', 'window': '86400'})  # 2 email changes per day per user
def initiate_email_change():
    """
    Initiate email change verification process
    
    Rate limited to prevent abuse
    """
    try:
        # Get authenticated user
        user_id = g.user_id
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        new_email = data.get('new_email', '').strip().lower()
        current_password = data.get('current_password', '')
        
        if not new_email:
            return jsonify({'error': 'New email is required'}), 400
        
        if not current_password:
            return jsonify({'error': 'Current password is required'}), 400
        
        # Validate email format
        if not validate_email_format(new_email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Sanitize input
        new_email = sanitize_input(new_email)
        
        # Initiate email change verification
        success, message = email_verification_service.change_email_verification(
            user_id, new_email, current_password
        )
        
        if success:
            logger.info(f"Email change verification initiated for user {user_id}")
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 400
        
    except Exception as e:
        logger.error(f"Error initiating email change: {e}")
        return jsonify({'error': 'Failed to initiate email change'}), 500

@email_verification_bp.route('/complete-email-change', methods=['POST'])
@cross_origin()
@login_required
@rate_limit_by_user('email_change_complete', {'requests': '5', 'window': '3600'})  # 5 attempts per hour per user
def complete_email_change():
    """
    Complete email change after verification
    
    Rate limited to prevent abuse
    """
    try:
        # Get authenticated user
        user_id = g.user_id
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'error': 'Verification token is required'}), 400
        
        # Sanitize input
        token = sanitize_input(token)
        
        # Complete email change
        success, message = email_verification_service.complete_email_change(token, user_id)
        
        if success:
            logger.info(f"Email change completed for user {user_id}")
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 400
        
    except Exception as e:
        logger.error(f"Error completing email change: {e}")
        return jsonify({'error': 'Failed to complete email change'}), 500

@email_verification_bp.route('/status', methods=['GET'])
@cross_origin()
@login_required
@rate_limit_by_user('verification_status', {'requests': '10', 'window': '3600'})  # 10 checks per hour per user
def get_verification_status():
    """
    Get current verification status for authenticated user
    """
    try:
        # Get authenticated user
        user_id = g.user_id
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get verification status
        status = email_verification_service.get_verification_status(user_id)
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting verification status: {e}")
        return jsonify({'error': 'Failed to get verification status'}), 500

@email_verification_bp.route('/health', methods=['GET'])
@cross_origin()
def verification_health_check():
    """
    Health check endpoint for email verification system
    """
    try:
        # Basic health check
        health_status = {
            'status': 'healthy',
            'service': 'email_verification',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'email_verification',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@email_verification_bp.route('/admin/cleanup', methods=['POST'])
@cross_origin()
@login_required
@rate_limit('admin_cleanup', {'requests': '1', 'window': '3600'})  # 1 cleanup per hour
def admin_cleanup_expired():
    """
    Admin endpoint to manually trigger cleanup of expired verifications
    
    Requires authentication and is rate limited
    """
    try:
        # Get authenticated user
        user_id = g.user_id
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has admin privileges (you'll need to implement this)
        # if not current_app.user_service.is_admin(user_id):
        #     return jsonify({'error': 'Admin privileges required'}), 403
        
        # Perform cleanup
        cleaned_count = email_verification_service.cleanup_expired_verifications()
        
        logger.info(f"Admin cleanup triggered by user {user_id}, cleaned {cleaned_count} records")
        
        return jsonify({
            'message': 'Cleanup completed successfully',
            'records_cleaned': cleaned_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error during admin cleanup: {e}")
        return jsonify({'error': 'Cleanup failed'}), 500

@email_verification_bp.route('/admin/analytics', methods=['GET'])
@cross_origin()
@login_required
@rate_limit('admin_analytics', {'requests': '5', 'window': '3600'})  # 5 requests per hour
def admin_verification_analytics():
    """
    Admin endpoint to get verification analytics
    
    Requires authentication and is rate limited
    """
    try:
        # Get authenticated user
        user_id = g.user_id
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has admin privileges (you'll need to implement this)
        # if not current_app.user_service.is_admin(user_id):
        #     return jsonify({'error': 'Admin privileges required'}), 403
        
        # Trigger analytics processing
        from ..tasks.email_verification_tasks import process_verification_analytics
        task = process_verification_analytics.delay()
        
        return jsonify({
            'message': 'Analytics processing started',
            'task_id': task.id
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting analytics processing: {e}")
        return jsonify({'error': 'Failed to start analytics processing'}), 500

# Error handlers for the blueprint
@email_verification_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        'error': 'Bad request',
        'message': 'Invalid request data'
    }), 400

@email_verification_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Authentication required'
    }), 401

@email_verification_bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden errors"""
    return jsonify({
        'error': 'Forbidden',
        'message': 'Insufficient privileges'
    }), 403

@email_verification_bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'Resource not found'
    }), 404

@email_verification_bp.errorhandler(429)
def too_many_requests(error):
    """Handle rate limit errors"""
    return jsonify({
        'error': 'Too many requests',
        'message': 'Rate limit exceeded. Please try again later.'
    }), 429

@email_verification_bp.errorhandler(500)
def internal_server_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error in email verification: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500
