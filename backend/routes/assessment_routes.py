"""
Mingus Assessment System API Routes

This module provides comprehensive API endpoints for the assessment system,
integrating with existing authentication, database, and calculation services.
"""

from flask import Blueprint, request, jsonify, current_app, session, g
from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from datetime import datetime, timedelta, timezone
import uuid
import logging
import time
from typing import Dict, Any, List, Optional
import json

# Import existing services and models
from backend.middleware.auth import require_auth, get_current_user_id
from backend.services.calculator_integration_service import CalculatorIntegrationService
from backend.services.calculator_database_service import CalculatorDatabaseService
from backend.services.payment_processor import PaymentProcessor
from backend.models.subscription_models import Subscription, Customer
from backend.models.user import User

# Import assessment models (these will be created)
from backend.models.assessment_models import Assessment, UserAssessment, AssessmentResult

# Import security components
from backend.security.assessment_security import (
    validate_assessment_input, 
    SecurityValidator, 
    SecureAssessmentDB,
    rate_limit_assessment,
    add_assessment_security_headers
)

# Import new comprehensive security components
from backend.security.assessment_security_integration import (
    secure_assessment_endpoint,
    secure_assessment_submission,
    init_assessment_security
)
from backend.security.csrf_protection import require_csrf_token

logger = logging.getLogger(__name__)

# Create blueprint
assessment_bp = Blueprint('assessment', __name__, url_prefix='/api/assessments')

# =====================================================
# AUTHENTICATION DECORATORS
# =====================================================

def optional_auth(f):
    """Decorator for optional authentication - allows both authenticated and anonymous users"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if user_id:
            # User is authenticated
            request.user = {
                'id': user_id,
                'email': session.get('email'),
                'authenticated': True
            }
        else:
            # Anonymous user
            request.user = {
                'id': None,
                'email': None,
                'authenticated': False
            }
        return f(*args, **kwargs)
    return decorated

def get_db_session() -> Session:
    """Get database session from current app"""
    return current_app.db.session

def rate_limit_anonymous(limit: int = 10, window: int = 3600):
    """Rate limiting decorator for anonymous users"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not request.user.get('authenticated'):
                # Check rate limit for anonymous users
                ip = request.remote_addr
                cache_key = f"rate_limit:anonymous:{ip}:{f.__name__}"
                
                # Simple in-memory rate limiting (in production, use Redis)
                current_count = getattr(current_app, '_rate_limit_cache', {}).get(cache_key, 0)
                if current_count >= limit:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {limit} requests per {window//3600} hour(s) for anonymous users',
                        'retry_after': window
                    }), 429
                
                # Increment counter
                if not hasattr(current_app, '_rate_limit_cache'):
                    current_app._rate_limit_cache = {}
                current_app._rate_limit_cache[cache_key] = current_count + 1
                
            return f(*args, **kwargs)
        return decorated
    return decorator

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def validate_assessment_responses(responses: Dict[str, Any], assessment_type: str) -> Dict[str, Any]:
    """Validate assessment responses against schema"""
    try:
        # Get assessment template from database
        db_session = get_db_session()
        assessment = db_session.query(Assessment).filter(
            Assessment.type == assessment_type,
            Assessment.is_active == True
        ).first()
        
        if not assessment:
            return {'valid': False, 'error': 'Assessment not found or inactive'}
        
        # Validate responses against questions schema
        questions = assessment.questions_json
        required_questions = [q['id'] for q in questions if q.get('required', True)]
        
        # Check required questions
        for question_id in required_questions:
            if question_id not in responses:
                return {'valid': False, 'error': f'Missing required question: {question_id}'}
        
        # Validate response types
        for question in questions:
            question_id = question['id']
            if question_id in responses:
                response = responses[question_id]
                question_type = question['type']
                
                if question_type == 'radio':
                    if not isinstance(response, str):
                        return {'valid': False, 'error': f'Invalid response type for {question_id}'}
                    valid_options = [opt['value'] for opt in question.get('options', [])]
                    if response not in valid_options:
                        return {'valid': False, 'error': f'Invalid option for {question_id}'}
                
                elif question_type == 'checkbox':
                    if not isinstance(response, list):
                        return {'valid': False, 'error': f'Invalid response type for {question_id}'}
                    valid_options = [opt['value'] for opt in question.get('options', [])]
                    if not all(opt in valid_options for opt in response):
                        return {'valid': False, 'error': f'Invalid option for {question_id}'}
                
                elif question_type == 'rating':
                    if not isinstance(response, (int, float)) or response < 1 or response > 5:
                        return {'valid': False, 'error': f'Invalid rating for {question_id}'}
        
        return {'valid': True, 'assessment': assessment}
        
    except Exception as e:
        logger.error(f"Error validating assessment responses: {e}")
        return {'valid': False, 'error': 'Validation error'}

def calculate_assessment_score(responses: Dict[str, Any], assessment: Assessment) -> Dict[str, Any]:
    """Calculate assessment score using exact calculation logic"""
    try:
        # Initialize calculator service
        db_session = get_db_session()
        calculator_service = CalculatorIntegrationService(db_session, current_app.config)
        
        # Calculate score using exact formulas from assessment service
        score_result = calculator_service._calculate_assessment_score(responses)
        
        # Determine risk level based on score
        score = score_result.get('score', 0)
        risk_level = 'low'
        
        if score >= 70:
            risk_level = 'low'
        elif score >= 40:
            risk_level = 'medium'
        elif score >= 20:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        return {
            'score': score,
            'risk_level': risk_level,
            'segment': score_result.get('segment', 'stress-free'),
            'product_tier': score_result.get('product_tier', 'Budget ($10)'),
            'insights': score_result.get('insights', []),
            'recommendations': score_result.get('recommendations', [])
        }
        
    except Exception as e:
        logger.error(f"Error calculating assessment score: {e}")
        return {
            'score': 0,
            'risk_level': 'unknown',
            'segment': 'unknown',
            'product_tier': 'Budget ($10)',
            'insights': ['Unable to calculate insights at this time'],
            'recommendations': ['Please try again later or contact support']
        }

def create_lead_record(email: str, first_name: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create lead record for anonymous assessment users"""
    try:
        db_session = get_db_session()
        
        # Generate lead ID
        lead_id = str(uuid.uuid4())
        
        # Calculate lead score based on assessment data
        lead_score = 50  # Base score
        if assessment_data.get('score', 0) > 70:
            lead_score += 20
        elif assessment_data.get('score', 0) > 50:
            lead_score += 10
        
        # Create lead record
        lead_data = {
            'id': lead_id,
            'email': email,
            'first_name': first_name,
            'lead_score': lead_score,
            'assessment_data': assessment_data,
            'created_at': datetime.utcnow(),
            'status': 'new'
        }
        
        # In a real implementation, you would save this to a leads table
        # For now, we'll just return the lead data
        logger.info(f"Lead created: {lead_id} for email: {email}")
        
        return {
            'success': True,
            'lead_id': lead_id,
            'lead_score': lead_score
        }
        
    except Exception as e:
        logger.error(f"Error creating lead record: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# =====================================================
# API ENDPOINTS
# =====================================================

@assessment_bp.route('/available', methods=['GET'])
@optional_auth
@secure_assessment_endpoint
@rate_limit_assessment(limit=20, window=3600)
def get_available_assessments():
    """
    GET /api/assessments/available
    
    Returns list of active assessments with metadata.
    Different data for authenticated vs anonymous users.
    """
    try:
        db_session = get_db_session()
        user = request.user
        
        # Get active assessments
        assessments_query = db_session.query(Assessment).filter(
            Assessment.is_active == True
        )
        
        if not user.get('authenticated'):
            # Anonymous users only see assessments that allow anonymous access
            assessments_query = assessments_query.filter(Assessment.allow_anonymous == True)
        
        assessments = assessments_query.all()
        
        # Get completion statistics
        stats_query = db_session.query(
            Assessment.id,
            func.count(UserAssessment.id).label('total_attempts'),
            func.count(UserAssessment.id).filter(UserAssessment.is_complete == True).label('completed_attempts'),
            func.avg(UserAssessment.score).label('average_score'),
            func.avg(UserAssessment.time_spent_seconds).label('average_time_seconds')
        ).outerjoin(UserAssessment).group_by(Assessment.id)
        
        stats = {row.id: {
            'total_attempts': row.total_attempts or 0,
            'completed_attempts': row.completed_attempts or 0,
            'completion_rate': round((row.completed_attempts or 0) * 100.0 / (row.total_attempts or 1), 2),
            'average_score': round(row.average_score or 0, 1),
            'average_time_minutes': round((row.average_time_seconds or 0) / 60, 1)
        } for row in stats_query.all()}
        
        # Format response
        assessment_list = []
        for assessment in assessments:
            assessment_data = {
                'id': str(assessment.id),
                'type': assessment.type,
                'title': assessment.title,
                'description': assessment.description,
                'estimated_duration_minutes': assessment.estimated_duration_minutes,
                'version': assessment.version,
                'requires_authentication': assessment.requires_authentication,
                'allow_anonymous': assessment.allow_anonymous,
                'max_attempts_per_user': assessment.max_attempts_per_user,
                'stats': stats.get(assessment.id, {})
            }
            
            # Add user-specific data for authenticated users
            if user.get('authenticated'):
                # Check if user has already taken this assessment
                user_assessment = db_session.query(UserAssessment).filter(
                    UserAssessment.user_id == user['id'],
                    UserAssessment.assessment_id == assessment.id,
                    UserAssessment.is_complete == True
                ).first()
                
                if user_assessment:
                    assessment_data['user_completed'] = True
                    assessment_data['user_score'] = user_assessment.score
                    assessment_data['user_risk_level'] = user_assessment.risk_level
                    assessment_data['completed_at'] = user_assessment.completed_at.isoformat()
                else:
                    assessment_data['user_completed'] = False
                    assessment_data['attempts_remaining'] = assessment.max_attempts_per_user
            
            assessment_list.append(assessment_data)
        
        return jsonify({
            'success': True,
            'assessments': assessment_list,
            'user_authenticated': user.get('authenticated', False),
            'total_assessments': len(assessment_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available assessments: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve assessments',
            'message': str(e)
        }), 500

@assessment_bp.route('/<assessment_type>/submit', methods=['POST'])
@optional_auth
@secure_assessment_submission
@validate_assessment_input
@rate_limit_assessment(limit=5, window=3600)
def submit_assessment(assessment_type):
    """
    POST /api/assessments/<assessment_type>/submit
    
    Submit assessment responses and get results.
    Supports both authenticated and anonymous users.
    """
    try:
        db_session = get_db_session()
        user = request.user
        
        # Validate assessment type
        valid_assessment_types = [
            'income-comparison',
            'relationship-money', 
            'tax-impact',
            'job-matching'
        ]
        
        if assessment_type not in valid_assessment_types:
            return jsonify({
                'success': False,
                'error': 'Invalid assessment type',
                'message': f'Assessment type "{assessment_type}" is not supported'
            }), 400
        
        # Get assessment data from request
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'message': 'Assessment data is required'
            }), 400
        
        # Validate responses
        responses = data.get('responses', {})
        if not responses:
            return jsonify({
                'success': False,
                'error': 'No responses provided',
                'message': 'Assessment responses are required'
            }), 400
        
        # Get assessment from database
        assessment = db_session.query(Assessment).filter(
            Assessment.type == assessment_type,
            Assessment.is_active == True
        ).first()
        
        if not assessment:
            return jsonify({
                'success': False,
                'error': 'Assessment not found',
                'message': f'Assessment type "{assessment_type}" is not available'
            }), 404
        
        # Check if assessment allows anonymous access
        if not user.get('authenticated') and not assessment.allow_anonymous:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'This assessment requires authentication'
            }), 403
        
        # Validate responses against assessment schema
        validation_result = validate_assessment_responses(responses, assessment_type)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid responses',
                'message': validation_result['error']
            }), 400
        
        # Calculate assessment score
        score_result = calculate_assessment_score(responses, assessment)
        
        # Create user assessment record
        user_assessment_id = str(uuid.uuid4())
        user_assessment = UserAssessment(
            id=user_assessment_id,
            user_id=user.get('id'),
            assessment_id=assessment.id,
            responses_json=responses,
            score=score_result['score'],
            risk_level=score_result['risk_level'],
            segment=score_result['segment'],
            product_tier=score_result['product_tier'],
            insights_json=score_result['insights'],
            recommendations_json=score_result['recommendations'],
            is_complete=True,
            completed_at=datetime.utcnow()
        )
        
        db_session.add(user_assessment)
        db_session.commit()
        
        # Return results
        return jsonify({
            'success': True,
            'assessment_id': user_assessment_id,
            'assessment_type': assessment_type,
            'score': score_result['score'],
            'risk_level': score_result['risk_level'],
            'segment': score_result['segment'],
            'product_tier': score_result['product_tier'],
            'insights': score_result['insights'],
            'recommendations': score_result['recommendations'],
            'completed_at': user_assessment.completed_at.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error submitting assessment {assessment_type}: {e}")
        db_session.rollback()
        return jsonify({
            'success': False,
            'error': 'Assessment submission failed',
            'message': 'An error occurred while processing your assessment'
        }), 500

@assessment_bp.route('/<user_assessment_id>/results', methods=['GET'])
@require_auth
@secure_assessment_endpoint
def get_assessment_results(user_assessment_id: str):
    """
    GET /api/assessments/{user_assessment_id}/results
    
    Return detailed assessment results for specific assessment.
    Check user authorization (own results only).
    Include personalized insights based on subscription tier.
    """
    try:
        db_session = get_db_session()
        user = request.user
        
        # Get user assessment
        user_assessment = db_session.query(UserAssessment).filter(
            UserAssessment.id == user_assessment_id
        ).first()
        
        if not user_assessment:
            return jsonify({
                'success': False,
                'error': 'Assessment not found'
            }), 404
        
        # Check authorization - users can only see their own results
        if user_assessment.user_id != user['id']:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to assessment results'
            }), 403
        
        # Get assessment details
        assessment = db_session.query(Assessment).filter(
            Assessment.id == user_assessment.assessment_id
        ).first()
        
        # Get assessment results
        assessment_result = db_session.query(AssessmentResult).filter(
            AssessmentResult.user_assessment_id == user_assessment_id
        ).first()
        
        # Get user subscription tier
        user_subscription = db_session.query(Subscription).filter(
            Subscription.user_id == user['id'],
            Subscription.status.in_(['active', 'trialing'])
        ).first()
        
        subscription_tier = user_subscription.tier if user_subscription else 'free'
        
        # Prepare base response
        response_data = {
            'success': True,
            'assessment': {
                'id': str(user_assessment.id),
                'type': assessment.type,
                'title': assessment.title,
                'version': user_assessment.assessment_version,
                'completed_at': user_assessment.completed_at.isoformat(),
                'time_spent_minutes': round(user_assessment.time_spent_seconds / 60, 1)
            },
            'results': {
                'score': user_assessment.score,
                'risk_level': user_assessment.risk_level,
                'segment': assessment_result.insights_json.get('segment') if assessment_result else None,
                'product_tier': assessment_result.insights_json.get('product_tier') if assessment_result else None
            }
        }
        
        # Add insights and recommendations based on subscription tier
        if subscription_tier == 'free':
            # Free tier: limited insights
            if assessment_result:
                response_data['insights'] = assessment_result.insights_json.get('insights', [])[:3]
                response_data['recommendations'] = assessment_result.recommendations_json.get('action_items', [])[:2]
                response_data['upgrade_message'] = 'Upgrade to see all insights and detailed recommendations'
        else:
            # Paid tiers: full insights
            if assessment_result:
                response_data['insights'] = assessment_result.insights_json.get('insights', [])
                response_data['recommendations'] = assessment_result.recommendations_json.get('action_items', [])
                response_data['detailed_analysis'] = assessment_result.insights_json
                response_data['next_steps'] = assessment_result.recommendations_json.get('next_steps', [])
                
                # Add assessment-specific detailed data
                if assessment.type == 'ai_job_risk':
                    response_data['ai_analysis'] = {
                        'automation_score': assessment_result.automation_score,
                        'augmentation_score': assessment_result.augmentation_score,
                        'risk_factors': assessment_result.risk_factors or [],
                        'mitigation_strategies': assessment_result.mitigation_strategies or []
                    }
                elif assessment.type == 'tax_impact':
                    response_data['tax_analysis'] = {
                        'tax_efficiency_score': assessment_result.tax_efficiency_score,
                        'potential_savings': float(assessment_result.potential_savings) if assessment_result.potential_savings else 0,
                        'optimization_opportunities': assessment_result.tax_optimization_opportunities or []
                    }
                elif assessment.type == 'income_comparison':
                    response_data['market_analysis'] = {
                        'market_position_score': assessment_result.market_position_score,
                        'salary_benchmark_data': assessment_result.salary_benchmark_data or {},
                        'negotiation_leverage_points': assessment_result.negotiation_leverage_points or []
                    }
        
        response_data['subscription_tier'] = subscription_tier
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error getting assessment results: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve assessment results',
            'message': str(e)
        }), 500

@assessment_bp.route('/convert/<user_assessment_id>', methods=['POST'])
@optional_auth
@secure_assessment_submission
def convert_assessment_to_subscription(user_assessment_id: str):
    """
    POST /api/assessments/convert/{user_assessment_id}
    
    Handle conversion from free assessment to paid subscription.
    Integrate with existing Stripe payment processing.
    Update user profile with assessment insights.
    """
    try:
        data = request.get_json() or {}
        user = request.user
        
        db_session = get_db_session()
        
        # Get user assessment
        user_assessment = db_session.query(UserAssessment).filter(
            UserAssessment.id == user_assessment_id
        ).first()
        
        if not user_assessment:
            return jsonify({
                'success': False,
                'error': 'Assessment not found'
            }), 404
        
        # Check if user owns this assessment or is anonymous with matching email
        if user.get('authenticated'):
            if user_assessment.user_id != user['id']:
                return jsonify({
                    'success': False,
                    'error': 'Unauthorized access to assessment'
                }), 403
        else:
            # Anonymous user - check email match
            if user_assessment.email != data.get('email'):
                return jsonify({
                    'success': False,
                    'error': 'Email does not match assessment'
                }), 403
        
        # Get assessment results
        assessment_result = db_session.query(AssessmentResult).filter(
            AssessmentResult.user_assessment_id == user_assessment_id
        ).first()
        
        if not assessment_result:
            return jsonify({
                'success': False,
                'error': 'Assessment results not found'
            }), 404
        
        # Initialize payment processor
        payment_processor = PaymentProcessor(db_session, current_app.config)
        
        # Create or get customer
        if user.get('authenticated'):
            # Authenticated user - create customer if doesn't exist
            existing_customer = db_session.query(Customer).filter(
                Customer.user_id == user['id']
            ).first()
            
            if not existing_customer:
                customer = payment_processor.create_customer(
                    user_id=user['id'],
                    email=user['email'],
                    name=data.get('full_name')
                )
            else:
                customer = existing_customer
        else:
            # Anonymous user - create customer with assessment data
            customer = payment_processor.create_customer(
                user_id=None,  # Will be updated when user signs up
                email=user_assessment.email,
                name=f"{user_assessment.first_name} {user_assessment.last_name}".strip()
            )
        
        # Determine subscription tier based on assessment results
        segment = assessment_result.insights_json.get('segment', 'stress-free')
        product_tier = assessment_result.insights_json.get('product_tier', 'Budget ($10)')
        
        # Map product tier to pricing tier ID
        tier_mapping = {
            'Budget ($10)': 1,  # Assuming tier ID 1 is budget
            'Mid-tier ($20)': 2,  # Assuming tier ID 2 is mid-tier
            'Professional ($50)': 3  # Assuming tier ID 3 is professional
        }
        
        pricing_tier_id = tier_mapping.get(product_tier, 1)
        
        # Create subscription with trial
        subscription = payment_processor.create_subscription(
            customer_id=customer.id,
            pricing_tier_id=pricing_tier_id,
            billing_cycle='monthly',
            trial_days=7
        )
        
        # Update user assessment with conversion data
        user_assessment.conversion_data = {
            'converted_at': datetime.now(timezone.utc).isoformat(),
            'subscription_id': subscription.id,
            'customer_id': customer.id,
            'pricing_tier_id': pricing_tier_id,
            'trial_days': 7
        }
        
        db_session.commit()
        
        # Prepare conversion response
        conversion_data = {
            'success': True,
            'subscription_id': subscription.id,
            'customer_id': customer.id,
            'trial_days': 7,
            'tier': product_tier,
            'segment': segment,
            'next_steps': [
                'Complete your profile setup',
                'Explore premium features',
                'Schedule your first consultation'
            ]
        }
        
        # Add payment intent data if payment method provided
        if data.get('payment_method_id'):
            try:
                # Attach payment method to customer
                payment_processor.stripe.PaymentMethod.attach(
                    data['payment_method_id'],
                    customer=customer.stripe_customer_id
                )
                
                # Set as default payment method
                payment_processor.stripe.Customer.modify(
                    customer.stripe_customer_id,
                    invoice_settings={
                        'default_payment_method': data['payment_method_id']
                    }
                )
                
                conversion_data['payment_method_attached'] = True
                
            except Exception as e:
                logger.error(f"Error attaching payment method: {e}")
                conversion_data['payment_method_attached'] = False
                conversion_data['payment_warning'] = 'Payment method could not be attached. You can add it later.'
        
        logger.info(f"Assessment converted to subscription: {user_assessment_id} -> {subscription.id}")
        
        return jsonify(conversion_data), 200
        
    except Exception as e:
        logger.error(f"Error converting assessment to subscription: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to convert assessment',
            'message': str(e)
        }), 500

@assessment_bp.route('/stats', methods=['GET'])
@secure_assessment_endpoint
@rate_limit_anonymous(limit=30, window=3600)
def get_assessment_stats():
    """
    GET /api/assessments/stats
    
    Return real-time statistics for social proof.
    Anonymous aggregated data only.
    """
    try:
        db_session = get_db_session()
        
        # Get today's date
        today = datetime.now(timezone.utc).date()
        week_ago = today - timedelta(days=7)
        
        # Calculate statistics
        today_stats = db_session.query(
            func.count(UserAssessment.id).label('total'),
            func.count(UserAssessment.id).filter(UserAssessment.is_complete == True).label('completed'),
            func.avg(UserAssessment.score).label('average_score')
        ).filter(
            func.date(UserAssessment.created_at) == today
        ).first()
        
        week_stats = db_session.query(
            func.count(UserAssessment.id).label('total'),
            func.count(UserAssessment.id).filter(UserAssessment.is_complete == True).label('completed'),
            func.avg(UserAssessment.score).label('average_score')
        ).filter(
            func.date(UserAssessment.created_at) >= week_ago
        ).first()
        
        # Get assessment type breakdown
        type_stats = db_session.query(
            Assessment.type,
            func.count(UserAssessment.id).label('total_attempts'),
            func.avg(UserAssessment.score).label('average_score')
        ).join(UserAssessment).filter(
            UserAssessment.is_complete == True
        ).group_by(Assessment.type).all()
        
        # Get risk level distribution
        risk_stats = db_session.query(
            UserAssessment.risk_level,
            func.count(UserAssessment.id).label('count')
        ).filter(
            UserAssessment.is_complete == True
        ).group_by(UserAssessment.risk_level).all()
        
        # Format response
        stats_data = {
            'success': True,
            'today': {
                'total_assessments': today_stats.total or 0,
                'completed_assessments': today_stats.completed or 0,
                'completion_rate': round((today_stats.completed or 0) * 100.0 / (today_stats.total or 1), 1),
                'average_score': round(today_stats.average_score or 0, 1)
            },
            'this_week': {
                'total_assessments': week_stats.total or 0,
                'completed_assessments': week_stats.completed or 0,
                'completion_rate': round((week_stats.completed or 0) * 100.0 / (week_stats.total or 1), 1),
                'average_score': round(week_stats.average_score or 0, 1)
            },
            'by_assessment_type': {
                stat.type: {
                    'total_attempts': stat.total_attempts,
                    'average_score': round(stat.average_score or 0, 1)
                } for stat in type_stats
            },
            'risk_distribution': {
                stat.risk_level: stat.count for stat in risk_stats
            },
            'total_users_helped': db_session.query(UserAssessment).filter(
                UserAssessment.is_complete == True
            ).count()
        }
        
        return jsonify(stats_data), 200
        
    except Exception as e:
        logger.error(f"Error getting assessment stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve statistics',
            'message': str(e)
        }), 500

# =====================================================
# ERROR HANDLERS
# =====================================================

@assessment_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'Invalid request data'
    }), 400

@assessment_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication required'
    }), 401

@assessment_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 'Forbidden',
        'message': 'Access denied'
    }), 403

@assessment_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not found',
        'message': 'Resource not found'
    }), 404

@assessment_bp.errorhandler(429)
def rate_limited(error):
    return jsonify({
        'success': False,
        'error': 'Rate limited',
        'message': 'Too many requests'
    }), 429

@assessment_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500
