"""
AI Calculator Integration Routes
API endpoints for integrating AI calculator with existing Mingus application
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify, current_app
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_

from backend.models.ai_job_models import AIJobAssessment, AICalculatorConversion
from backend.models.ai_user_profile_extension import AIUserProfileExtension, AIOnboardingProgress
from backend.models.user import User
from backend.services.ai_calculator_email_service import AICalculatorEmailService
from backend.services.ai_calculator_analytics_service import AICalculatorAnalyticsService
from backend.services.ai_calculator_payment_service import AICalculatorPaymentService
from backend.utils.validation import validate_email_format
from backend.utils.rate_limiting import limiter
from backend.utils.response_helpers import create_response

logger = logging.getLogger(__name__)

ai_integration_bp = Blueprint('ai_integration', __name__, url_prefix='/api/ai-integration')

# Initialize services
email_service = AICalculatorEmailService()
analytics_service = AICalculatorAnalyticsService()
payment_service = AICalculatorPaymentService()
csrf = CSRFProtect()


@ai_integration_bp.route('/user-profile/update', methods=['POST'])
@limiter.limit('10 per minute')
def update_user_profile_with_ai_data():
    """Update existing user profile with AI assessment data"""
    try:
        data = request.get_json()
        
        if not data:
            return create_response(False, "No data provided", 400)
        
        user_id = data.get('user_id')
        assessment_id = data.get('assessment_id')
        
        if not user_id or not assessment_id:
            return create_response(False, "User ID and assessment ID required", 400)
        
        # Get database session
        db = current_app.config['db_session']
        
        # Get user and assessment
        user = db.query(User).filter(User.id == user_id).first()
        assessment = db.query(AIJobAssessment).filter(AIJobAssessment.id == assessment_id).first()
        
        if not user or not assessment:
            return create_response(False, "User or assessment not found", 404)
        
        # Link assessment to user
        assessment.user_id = user_id
        
        # Create or update AI profile extension
        profile_extension = db.query(AIUserProfileExtension).filter(
            AIUserProfileExtension.user_id == user_id
        ).first()
        
        if not profile_extension:
            profile_extension = AIUserProfileExtension(
                user_id=user_id,
                latest_ai_assessment_id=assessment_id,
                overall_risk_level=assessment.overall_risk_level,
                automation_score=assessment.automation_score,
                augmentation_score=assessment.augmentation_score,
                ai_assessment_completed=True,
                ai_assessment_completion_date=assessment.completed_at,
                ai_onboarding_step='completed',
                ai_career_insights_enabled=True,
                ai_assessment_count=1,
                last_ai_assessment_date=assessment.completed_at
            )
            db.add(profile_extension)
        else:
            profile_extension.latest_ai_assessment_id = assessment_id
            profile_extension.overall_risk_level = assessment.overall_risk_level
            profile_extension.automation_score = assessment.automation_score
            profile_extension.augmentation_score = assessment.augmentation_score
            profile_extension.ai_assessment_completed = True
            profile_extension.ai_assessment_completion_date = assessment.completed_at
            profile_extension.ai_onboarding_step = 'completed'
            profile_extension.ai_career_insights_enabled = True
            profile_extension.ai_assessment_count += 1
            profile_extension.last_ai_assessment_date = assessment.completed_at
        
        # Create or update onboarding progress
        onboarding_progress = db.query(AIOnboardingProgress).filter(
            AIOnboardingProgress.user_id == user_id
        ).first()
        
        if not onboarding_progress:
            onboarding_progress = AIOnboardingProgress(
                user_id=user_id,
                ai_assessment_introduced=True,
                ai_assessment_started=True,
                ai_assessment_completed=True,
                introduction_date=datetime.now(timezone.utc),
                started_date=assessment.created_at,
                completed_date=assessment.completed_at,
                user_opted_in=True
            )
            db.add(onboarding_progress)
        else:
            onboarding_progress.ai_assessment_completed = True
            onboarding_progress.completed_date = assessment.completed_at
            onboarding_progress.user_opted_in = True
        
        # Schedule email sequence
        email_service.schedule_email_sequence(assessment, db)
        
        # Track analytics
        analytics_service.track_calculator_completion(assessment, db)
        
        db.commit()
        
        return create_response(True, "User profile updated successfully", 200, {
            'profile_extension': profile_extension.to_dict(),
            'onboarding_progress': onboarding_progress.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        db.rollback()
        return create_response(False, f"Error updating profile: {str(e)}", 500)


@ai_integration_bp.route('/user-profile/<user_id>', methods=['GET'])
@limiter.limit('20 per minute')
def get_user_ai_profile(user_id):
    """Get user's AI profile extension data"""
    try:
        db = current_app.config['db_session']
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return create_response(False, "User not found", 404)
        
        # Get AI profile extension
        profile_extension = db.query(AIUserProfileExtension).filter(
            AIUserProfileExtension.user_id == user_id
        ).first()
        
        # Get onboarding progress
        onboarding_progress = db.query(AIOnboardingProgress).filter(
            AIOnboardingProgress.user_id == user_id
        ).first()
        
        # Get latest assessment
        latest_assessment = None
        if profile_extension and profile_extension.latest_ai_assessment_id:
            latest_assessment = db.query(AIJobAssessment).filter(
                AIJobAssessment.id == profile_extension.latest_ai_assessment_id
            ).first()
        
        response_data = {
            'user': user.to_dict(),
            'ai_profile': profile_extension.to_dict() if profile_extension else None,
            'onboarding_progress': onboarding_progress.to_dict() if onboarding_progress else None,
            'latest_assessment': latest_assessment.to_dict() if latest_assessment else None
        }
        
        return create_response(True, "AI profile retrieved successfully", 200, response_data)
        
    except Exception as e:
        logger.error(f"Error getting AI profile: {e}")
        return create_response(False, f"Error retrieving profile: {str(e)}", 500)


@ai_integration_bp.route('/email/send-welcome', methods=['POST'])
@limiter.limit('5 per minute')
def send_welcome_email():
    """Send welcome email for AI calculator assessment"""
    try:
        data = request.get_json()
        assessment_id = data.get('assessment_id')
        
        if not assessment_id:
            return create_response(False, "Assessment ID required", 400)
        
        db = current_app.config['db_session']
        
        assessment = db.query(AIJobAssessment).filter(AIJobAssessment.id == assessment_id).first()
        if not assessment:
            return create_response(False, "Assessment not found", 404)
        
        success = email_service.send_welcome_email(assessment, db)
        
        if success:
            return create_response(True, "Welcome email sent successfully", 200)
        else:
            return create_response(False, "Failed to send welcome email", 500)
            
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
        return create_response(False, f"Error sending email: {str(e)}", 500)


@ai_integration_bp.route('/email/send-risk-followup', methods=['POST'])
@limiter.limit('5 per minute')
def send_risk_followup_email():
    """Send risk-based follow-up email"""
    try:
        data = request.get_json()
        assessment_id = data.get('assessment_id')
        
        if not assessment_id:
            return create_response(False, "Assessment ID required", 400)
        
        db = current_app.config['db_session']
        
        assessment = db.query(AIJobAssessment).filter(AIJobAssessment.id == assessment_id).first()
        if not assessment:
            return create_response(False, "Assessment not found", 404)
        
        success = email_service.send_risk_based_followup(assessment, db)
        
        if success:
            return create_response(True, "Risk follow-up email sent successfully", 200)
        else:
            return create_response(False, "Failed to send follow-up email", 500)
            
    except Exception as e:
        logger.error(f"Error sending risk follow-up email: {e}")
        return create_response(False, f"Error sending email: {str(e)}", 500)


@ai_integration_bp.route('/analytics/performance', methods=['GET'])
@limiter.limit('10 per minute')
def get_calculator_performance():
    """Get AI calculator performance metrics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        db = current_app.config['db_session']
        
        metrics = analytics_service.get_calculator_performance_metrics(db, days)
        
        return create_response(True, "Performance metrics retrieved successfully", 200, metrics)
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return create_response(False, f"Error retrieving metrics: {str(e)}", 500)


@ai_integration_bp.route('/analytics/demographics', methods=['GET'])
@limiter.limit('10 per minute')
def get_demographic_analysis():
    """Get demographic analysis of calculator users"""
    try:
        days = request.args.get('days', 30, type=int)
        
        db = current_app.config['db_session']
        
        demographics = analytics_service.get_demographic_analysis(db, days)
        
        return create_response(True, "Demographic analysis retrieved successfully", 200, demographics)
        
    except Exception as e:
        logger.error(f"Error getting demographic analysis: {e}")
        return create_response(False, f"Error retrieving demographics: {str(e)}", 500)


@ai_integration_bp.route('/analytics/ab-testing', methods=['GET'])
@limiter.limit('10 per minute')
def get_ab_testing_results():
    """Get A/B testing results"""
    try:
        test_name = request.args.get('test_name', 'calculator_positioning')
        days = request.args.get('days', 30, type=int)
        
        db = current_app.config['db_session']
        
        results = analytics_service.get_ab_testing_results(db, test_name, days)
        
        return create_response(True, "A/B testing results retrieved successfully", 200, results)
        
    except Exception as e:
        logger.error(f"Error getting A/B testing results: {e}")
        return create_response(False, f"Error retrieving A/B testing results: {str(e)}", 500)


@ai_integration_bp.route('/analytics/export-report', methods=['GET'])
@limiter.limit('5 per minute')
def export_analytics_report():
    """Export comprehensive analytics report"""
    try:
        days = request.args.get('days', 30, type=int)
        format_type = request.args.get('format', 'json')
        
        db = current_app.config['db_session']
        
        report = analytics_service.export_analytics_report(db, days, format_type)
        
        return create_response(True, "Analytics report exported successfully", 200, report)
        
    except Exception as e:
        logger.error(f"Error exporting analytics report: {e}")
        return create_response(False, f"Error exporting report: {str(e)}", 500)


@ai_integration_bp.route('/payment/create-checkout', methods=['POST'])
@limiter.limit('10 per minute')
def create_career_plan_checkout():
    """Create Stripe checkout session for AI Career Plan"""
    try:
        data = request.get_json()
        assessment_id = data.get('assessment_id')
        
        if not assessment_id:
            return create_response(False, "Assessment ID required", 400)
        
        db = current_app.config['db_session']
        
        assessment = db.query(AIJobAssessment).filter(AIJobAssessment.id == assessment_id).first()
        if not assessment:
            return create_response(False, "Assessment not found", 404)
        
        checkout_result = payment_service.create_career_plan_checkout_session(assessment, db)
        
        if checkout_result['success']:
            return create_response(True, "Checkout session created successfully", 200, checkout_result)
        else:
            return create_response(False, checkout_result['error'], 500)
            
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return create_response(False, f"Error creating checkout: {str(e)}", 500)


@ai_integration_bp.route('/payment/success', methods=['GET'])
@limiter.limit('20 per minute')
def handle_payment_success():
    """Handle successful payment"""
    try:
        session_id = request.args.get('session_id')
        assessment_id = request.args.get('assessment_id')
        
        if not session_id or not assessment_id:
            return create_response(False, "Session ID and assessment ID required", 400)
        
        db = current_app.config['db_session']
        
        result = payment_service.process_payment_success(session_id, assessment_id, db)
        
        if result['success']:
            return create_response(True, "Payment processed successfully", 200, result)
        else:
            return create_response(False, result['error'], 500)
            
    except Exception as e:
        logger.error(f"Error processing payment success: {e}")
        return create_response(False, f"Error processing payment: {str(e)}", 500)


@ai_integration_bp.route('/payment/analytics', methods=['GET'])
@limiter.limit('10 per minute')
def get_payment_analytics():
    """Get payment and revenue analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        db = current_app.config['db_session']
        
        analytics = payment_service.get_payment_analytics(db, days)
        
        return create_response(True, "Payment analytics retrieved successfully", 200, analytics)
        
    except Exception as e:
        logger.error(f"Error getting payment analytics: {e}")
        return create_response(False, f"Error retrieving payment analytics: {str(e)}", 500)


@ai_integration_bp.route('/subscription/upgrade-offer', methods=['POST'])
@limiter.limit('10 per minute')
def create_subscription_upgrade_offer():
    """Create upgrade offer for existing subscribers"""
    try:
        data = request.get_json()
        assessment_id = data.get('assessment_id')
        
        if not assessment_id:
            return create_response(False, "Assessment ID required", 400)
        
        db = current_app.config['db_session']
        
        assessment = db.query(AIJobAssessment).filter(AIJobAssessment.id == assessment_id).first()
        if not assessment:
            return create_response(False, "Assessment not found", 404)
        
        offer_result = payment_service.create_subscription_upgrade_offer(assessment, db)
        
        if offer_result['success']:
            return create_response(True, "Upgrade offer created successfully", 200, offer_result)
        else:
            return create_response(False, offer_result['error'], 500)
            
    except Exception as e:
        logger.error(f"Error creating upgrade offer: {e}")
        return create_response(False, f"Error creating offer: {str(e)}", 500)


@ai_integration_bp.route('/tracking/calculator-start', methods=['POST'])
@limiter.limit('20 per minute')
def track_calculator_start():
    """Track when user starts the AI calculator"""
    try:
        data = request.get_json()
        assessment_id = data.get('assessment_id')
        user_data = data.get('user_data', {})
        
        if not assessment_id:
            return create_response(False, "Assessment ID required", 400)
        
        db = current_app.config['db_session']
        
        success = analytics_service.track_calculator_start(assessment_id, user_data, db)
        
        if success:
            return create_response(True, "Calculator start tracked successfully", 200)
        else:
            return create_response(False, "Failed to track calculator start", 500)
            
    except Exception as e:
        logger.error(f"Error tracking calculator start: {e}")
        return create_response(False, f"Error tracking start: {str(e)}", 500)


@ai_integration_bp.route('/tracking/conversion-funnel', methods=['POST'])
@limiter.limit('20 per minute')
def track_conversion_funnel():
    """Track conversion funnel progression"""
    try:
        data = request.get_json()
        assessment_id = data.get('assessment_id')
        funnel_step = data.get('funnel_step')
        step_data = data.get('step_data', {})
        
        if not assessment_id or not funnel_step:
            return create_response(False, "Assessment ID and funnel step required", 400)
        
        db = current_app.config['db_session']
        
        success = analytics_service.track_conversion_funnel(assessment_id, funnel_step, step_data, db)
        
        if success:
            return create_response(True, "Conversion funnel tracked successfully", 200)
        else:
            return create_response(False, "Failed to track conversion funnel", 500)
            
    except Exception as e:
        logger.error(f"Error tracking conversion funnel: {e}")
        return create_response(False, f"Error tracking funnel: {str(e)}", 500)
