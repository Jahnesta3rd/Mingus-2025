"""
Secure Assessment Routes Example
Demonstrates implementation of comprehensive rate limiting and API security
"""

from flask import Blueprint, request, jsonify, current_app, session, g
from functools import wraps
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, Any, List, Optional

# Import comprehensive security middleware
from backend.middleware.security_integration import (
    secure_endpoint,
    secure_assessment_endpoint,
    secure_assessment_view_endpoint,
    secure_endpoint_with_config,
    SecurityMiddleware
)
from backend.middleware.rate_limiter import rate_limited, add_rate_limit_headers
from backend.middleware.api_validation import validate_api_request

# Import existing services and models
from backend.middleware.auth import require_auth, get_current_user_id
from backend.services.calculator_integration_service import CalculatorIntegrationService
from backend.models.assessment_models import Assessment, UserAssessment, AssessmentResult
from backend.models.user import User
from sqlalchemy import func

logger = logging.getLogger(__name__)

# Create blueprint
assessment_bp = Blueprint('assessment', __name__, url_prefix='/api/assessments')

# =====================================================
# SECURE ASSESSMENT ENDPOINTS
# =====================================================

@assessment_bp.route('/submit', methods=['POST'])
@secure_assessment_endpoint()  # Pre-configured security for assessment submission
@require_auth
def submit_assessment():
    """
    Submit assessment with comprehensive security:
    - Rate limiting: 3 requests per 5 minutes
    - Request size limit: 512KB
    - Content type validation: JSON only
    - Input sanitization and validation
    - Security event logging
    """
    try:
        data = request.get_json()
        
        # Data is already sanitized by security middleware
        assessment_data = {
            'user_id': g.user_id,
            'assessment_type': data.get('assessment_type'),
            'answers': data.get('answers', {}),
            'metadata': data.get('metadata', {})
        }
        
        # Process assessment
        calculator_service = CalculatorIntegrationService()
        result = calculator_service.process_assessment(assessment_data)
        
        return jsonify({
            'success': True,
            'assessment_id': result['assessment_id'],
            'score': result['score'],
            'recommendations': result['recommendations']
        }), 201
        
    except Exception as e:
        logger.error(f"Assessment submission error: {e}")
        return jsonify({
            'error': 'Assessment submission failed',
            'message': 'An error occurred while processing your assessment'
        }), 500

@assessment_bp.route('/view/<assessment_id>', methods=['GET'])
@secure_assessment_view_endpoint()  # Pre-configured security for assessment viewing
@require_auth
def view_assessment(assessment_id: str):
    """
    View assessment with comprehensive security:
    - Rate limiting: 20 requests per 5 minutes
    - Request size limit: 256KB
    - Content type validation: JSON only
    - Input sanitization and validation
    """
    try:
        # Get assessment from database
        db_session = current_app.db.session
        assessment = db_session.query(UserAssessment).filter(
            UserAssessment.id == assessment_id,
            UserAssessment.user_id == g.user_id
        ).first()
        
        if not assessment:
            return jsonify({
                'error': 'Assessment not found',
                'message': 'The requested assessment could not be found'
            }), 404
        
        return jsonify({
            'success': True,
            'assessment': {
                'id': assessment.id,
                'type': assessment.assessment_type,
                'score': assessment.score,
                'completed_at': assessment.completed_at.isoformat(),
                'answers': assessment.answers
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Assessment view error: {e}")
        return jsonify({
            'error': 'Assessment retrieval failed',
            'message': 'An error occurred while retrieving the assessment'
        }), 500

@assessment_bp.route('/list', methods=['GET'])
@secure_endpoint(
    endpoint_type='assessment_view',
    custom_rate_limits={'requests': 30, 'window': 300},  # 30 requests per 5 minutes
    max_request_size=256 * 1024,  # 256KB
    allowed_content_types=['application/json']
)
@require_auth
def list_assessments():
    """
    List user assessments with custom security configuration
    """
    try:
        # Get query parameters (already sanitized)
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)  # Max 50 per page
        
        db_session = current_app.db.session
        assessments = db_session.query(UserAssessment).filter(
            UserAssessment.user_id == g.user_id
        ).order_by(UserAssessment.completed_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'assessments': [{
                'id': a.id,
                'type': a.assessment_type,
                'score': a.score,
                'completed_at': a.completed_at.isoformat()
            } for a in assessments.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': assessments.total,
                'pages': assessments.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Assessment list error: {e}")
        return jsonify({
            'error': 'Assessment list retrieval failed',
            'message': 'An error occurred while retrieving assessments'
        }), 500

@assessment_bp.route('/analytics', methods=['GET'])
@secure_endpoint_with_config('assessment', 'analytics')  # Using configuration-based security
@require_auth
def get_assessment_analytics():
    """
    Get assessment analytics with configuration-based security
    """
    try:
        db_session = current_app.db.session
        
        # Get analytics data
        total_assessments = db_session.query(func.count(UserAssessment.id)).filter(
            UserAssessment.user_id == g.user_id
        ).scalar()
        
        avg_score = db_session.query(func.avg(UserAssessment.score)).filter(
            UserAssessment.user_id == g.user_id
        ).scalar()
        
        recent_assessments = db_session.query(UserAssessment).filter(
            UserAssessment.user_id == g.user_id,
            UserAssessment.completed_at >= datetime.now(timezone.utc) - timedelta(days=30)
        ).count()
        
        return jsonify({
            'success': True,
            'analytics': {
                'total_assessments': total_assessments,
                'average_score': float(avg_score) if avg_score else 0,
                'recent_assessments': recent_assessments
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Assessment analytics error: {e}")
        return jsonify({
            'error': 'Analytics retrieval failed',
            'message': 'An error occurred while retrieving analytics'
        }), 500

# =====================================================
# LEGACY COMPATIBILITY ENDPOINTS
# =====================================================

@assessment_bp.route('/legacy/submit', methods=['POST'])
@rate_limited('assessment_submit')  # Using legacy rate limiting
@validate_api_request  # Using legacy API validation
@require_auth
def legacy_submit_assessment():
    """
    Legacy assessment submission with separate security decorators
    """
    try:
        data = request.get_json()
        
        # Process assessment
        calculator_service = CalculatorIntegrationService()
        result = calculator_service.process_assessment({
            'user_id': g.user_id,
            'assessment_type': data.get('assessment_type'),
            'answers': data.get('answers', {}),
            'metadata': data.get('metadata', {})
        })
        
        response = jsonify({
            'success': True,
            'assessment_id': result['assessment_id'],
            'score': result['score'],
            'recommendations': result['recommendations']
        }), 201
        
        # Add rate limit headers manually
        return add_rate_limit_headers(response[0]), response[1]
        
    except Exception as e:
        logger.error(f"Legacy assessment submission error: {e}")
        return jsonify({
            'error': 'Assessment submission failed',
            'message': 'An error occurred while processing your assessment'
        }), 500

# =====================================================
# ADMIN ENDPOINTS WITH ELEVATED SECURITY
# =====================================================

@assessment_bp.route('/admin/all', methods=['GET'])
@secure_endpoint(
    endpoint_type='admin',
    custom_rate_limits={'requests': 100, 'window': 3600},  # 100 requests per hour
    max_request_size=1024 * 1024,  # 1MB
    allowed_content_types=['application/json'],
    required_headers=['User-Agent', 'Accept', 'Authorization']
)
@require_auth
def admin_list_all_assessments():
    """
    Admin endpoint to list all assessments with elevated security
    """
    try:
        # Check admin permissions
        user = current_app.db.session.query(User).filter(User.id == g.user_id).first()
        if not user or not user.is_admin:
            return jsonify({
                'error': 'Access denied',
                'message': 'Admin privileges required'
            }), 403
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # Max 100 per page
        
        db_session = current_app.db.session
        assessments = db_session.query(UserAssessment).order_by(
            UserAssessment.completed_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'assessments': [{
                'id': a.id,
                'user_id': a.user_id,
                'type': a.assessment_type,
                'score': a.score,
                'completed_at': a.completed_at.isoformat()
            } for a in assessments.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': assessments.total,
                'pages': assessments.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Admin assessment list error: {e}")
        return jsonify({
            'error': 'Admin assessment list retrieval failed',
            'message': 'An error occurred while retrieving assessments'
        }), 500

# =====================================================
# WEBHOOK ENDPOINTS WITH WEBHOOK-SPECIFIC SECURITY
# =====================================================

@assessment_bp.route('/webhook/result', methods=['POST'])
@secure_endpoint(
    endpoint_type='webhook',
    custom_rate_limits={'requests': 200, 'window': 3600},  # 200 requests per hour
    max_request_size=1024 * 1024,  # 1MB
    allowed_content_types=['application/json'],
    required_headers=['User-Agent', 'Accept', 'X-Webhook-Signature']
)
def webhook_assessment_result():
    """
    Webhook endpoint for assessment results with webhook-specific security
    """
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Webhook-Signature')
        if not signature:
            return jsonify({
                'error': 'Missing signature',
                'message': 'Webhook signature is required'
            }), 401
        
        # Verify signature (implement your signature verification logic)
        # verify_webhook_signature(request.data, signature)
        
        data = request.get_json()
        
        # Process webhook data
        assessment_id = data.get('assessment_id')
        result_data = data.get('result')
        
        # Update assessment with result
        db_session = current_app.db.session
        assessment = db_session.query(UserAssessment).filter(
            UserAssessment.id == assessment_id
        ).first()
        
        if assessment:
            assessment.result_data = result_data
            assessment.updated_at = datetime.now(timezone.utc)
            db_session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Webhook processed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Webhook assessment result error: {e}")
        return jsonify({
            'error': 'Webhook processing failed',
            'message': 'An error occurred while processing the webhook'
        }), 500

# =====================================================
# ERROR HANDLERS
# =====================================================

@assessment_bp.errorhandler(429)
def handle_rate_limit_exceeded(error):
    """Handle rate limit exceeded errors"""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.',
        'retry_after': request.headers.get('Retry-After', 60)
    }), 429

@assessment_bp.errorhandler(413)
def handle_request_too_large(error):
    """Handle request too large errors"""
    return jsonify({
        'error': 'Request too large',
        'message': 'The request size exceeds the allowed limit.'
    }), 413

@assessment_bp.errorhandler(415)
def handle_unsupported_media_type(error):
    """Handle unsupported media type errors"""
    return jsonify({
        'error': 'Unsupported media type',
        'message': 'The request content type is not supported.'
    }), 415

# =====================================================
# INITIALIZATION
# =====================================================

def init_assessment_routes(app):
    """Initialize assessment routes with security middleware"""
    # Register security middleware
    security_middleware = SecurityMiddleware()
    security_middleware.init_app(app)
    
    # Register blueprint
    app.register_blueprint(assessment_bp)
    
    logger.info("Secure assessment routes initialized with comprehensive security middleware")
