"""
Secure AI Calculator API Routes

Comprehensive API endpoints for the AI Job Impact Calculator with enhanced security and privacy measures:
- PII encryption
- Rate limiting (5 assessments per hour per IP)
- CSRF protection
- Input validation and sanitization
- GDPR compliance with explicit consent
- Anonymous assessment option
- Data export and deletion for GDPR compliance
- Comprehensive audit logging
- CCPA compliance
"""

import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify, current_app, g, session
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.security.ai_calculator_security import (
    AICalculatorSecurityService,
    secure_ai_calculator_endpoint,
    require_gdpr_consent,
    encrypt_pii_data,
    require_ai_calculator_csrf,
    generate_ai_calculator_csrf_token,
    export_user_data,
    delete_user_data,
    get_ai_calculator_privacy_policy,
    create_ai_calculator_consent_record,
    AICalculatorSecurityLevel
)
from backend.middleware.auth import require_auth, optional_auth
from backend.services.email_service import EmailService
from backend.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

# Create blueprint
ai_calculator_secure_bp = Blueprint('ai_calculator_secure', __name__, url_prefix='/api/ai-calculator/secure')

# Initialize services
email_service = EmailService()
analytics_service = AnalyticsService()


def get_db_session() -> Session:
    """Get database session from current app"""
    return current_app.db.session


# =====================================================
# CORE ASSESSMENT ENDPOINTS
# =====================================================

@ai_calculator_secure_bp.route('/assess', methods=['POST'])
@secure_ai_calculator_endpoint(security_level=AICalculatorSecurityLevel.PUBLIC)
@encrypt_pii_data()
@require_ai_calculator_csrf()
def submit_secure_assessment():
    """
    POST /api/ai-calculator/secure/assess
    
    Submit AI job impact assessment with comprehensive security measures:
    - Rate limiting: 5 assessments per hour per IP
    - PII encryption before database storage
    - CSRF protection
    - Input validation and sanitization
    - GDPR consent verification
    - Audit logging
    - Suspicious behavior detection
    """
    try:
        # Get security service
        security_service = AICalculatorSecurityService(get_db_session())
        
        # Get validated and encrypted data
        data = request.get_json()
        user_id = getattr(g, 'user_id', None)
        ip_address = request.remote_addr or 'unknown'
        
        # Check GDPR consent if email is provided
        if data.get('email') and not security_service.check_gdpr_consent(user_id, data['email']):
            return jsonify({
                'success': False,
                'error': 'gdpr_consent_required',
                'message': 'GDPR consent is required for data processing',
                'consent_required': True,
                'privacy_policy': get_ai_calculator_privacy_policy()
            }), 403
        
        # Calculate assessment scores
        automation_score, augmentation_score = calculate_job_scores(data)
        risk_level = determine_risk_level(automation_score, augmentation_score)
        recommendations = generate_recommendations(data, automation_score, augmentation_score, risk_level)
        
        # Create assessment record with encrypted PII
        assessment_id = str(uuid.uuid4())
        
        # Insert assessment with parameterized query to prevent SQL injection
        result = get_db_session().execute(text("""
            INSERT INTO ai_job_assessments (
                id, user_id, job_title, industry, experience_level, tasks_array,
                remote_work_frequency, ai_usage_frequency, team_size, tech_skills_level,
                concerns_array, first_name, email, location, automation_score,
                augmentation_score, overall_risk_level, assessment_type, completed_at,
                created_at, lead_source, utm_source, utm_medium, utm_campaign,
                utm_term, utm_content, risk_factors, mitigation_strategies,
                recommended_skills, career_advice
            ) VALUES (
                :id, :user_id, :job_title, :industry, :experience_level, :tasks_array,
                :remote_work_frequency, :ai_usage_frequency, :team_size, :tech_skills_level,
                :concerns_array, :first_name, :email, :location, :automation_score,
                :augmentation_score, :overall_risk_level, :assessment_type, :completed_at,
                :created_at, :lead_source, :utm_source, :utm_medium, :utm_campaign,
                :utm_term, :utm_content, :risk_factors, :mitigation_strategies,
                :recommended_skills, :career_advice
            )
        """), {
            'id': assessment_id,
            'user_id': user_id,
            'job_title': data['job_title'],
            'industry': data['industry'],
            'experience_level': data['experience_level'],
            'tasks_array': json.dumps(data['tasks_array']),
            'remote_work_frequency': data['remote_work_frequency'],
            'ai_usage_frequency': data['ai_usage_frequency'],
            'team_size': data['team_size'],
            'tech_skills_level': data['tech_skills_level'],
            'concerns_array': json.dumps(data['concerns_array']),
            'first_name': data.get('first_name', ''),
            'email': data.get('email', ''),
            'location': data.get('location', ''),
            'automation_score': automation_score,
            'augmentation_score': augmentation_score,
            'overall_risk_level': risk_level,
            'assessment_type': 'ai_job_risk',
            'completed_at': datetime.now(timezone.utc),
            'created_at': datetime.now(timezone.utc),
            'lead_source': 'ai_job_calculator',
            'utm_source': data.get('utm_source', ''),
            'utm_medium': data.get('utm_medium', ''),
            'utm_campaign': data.get('utm_campaign', ''),
            'utm_term': data.get('utm_term', ''),
            'utm_content': data.get('utm_content', ''),
            'risk_factors': json.dumps(recommendations.get('risk_factors', {})),
            'mitigation_strategies': json.dumps(recommendations.get('mitigation_strategies', [])),
            'recommended_skills': json.dumps(recommendations.get('recommended_skills', [])),
            'career_advice': json.dumps(recommendations.get('career_advice', {}))
        })
        
        get_db_session().commit()
        
        # Send welcome email if email provided and consent given
        email_sent = False
        if data.get('email') and security_service.check_gdpr_consent(user_id, data['email']):
            try:
                email_service.send_ai_calculator_welcome_email(
                    email=data['email'],
                    first_name=data.get('first_name', 'User'),
                    assessment_id=assessment_id,
                    automation_score=automation_score,
                    augmentation_score=augmentation_score,
                    risk_level=risk_level
                )
                email_sent = True
            except Exception as e:
                logger.error(f"Failed to send welcome email: {e}")
        
        # Track analytics
        analytics_service.track_assessment_completion(
            assessment_id=assessment_id,
            user_id=user_id,
            automation_score=automation_score,
            augmentation_score=augmentation_score,
            risk_level=risk_level,
            ip_address=ip_address
        )
        
        # Log successful assessment
        security_service.log_assessment_event(
            'assessment_submitted', user_id, data, ip_address
        )
        
        return jsonify({
            'success': True,
            'assessment_id': assessment_id,
            'automation_score': automation_score,
            'augmentation_score': augmentation_score,
            'risk_level': risk_level,
            'recommendations': recommendations,
            'email_sent': email_sent,
            'privacy_notice': {
                'data_retention': '2 years',
                'data_usage': 'Assessment analysis and personalized recommendations',
                'rights': ['access', 'rectification', 'erasure', 'portability']
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Secure assessment submission error: {e}")
        get_db_session().rollback()
        return jsonify({
            'success': False,
            'error': 'assessment_submission_failed',
            'message': 'An error occurred while processing your assessment'
        }), 500


@ai_calculator_secure_bp.route('/assess/anonymous', methods=['POST'])
@secure_ai_calculator_endpoint(security_level=AICalculatorSecurityLevel.PUBLIC)
@encrypt_pii_data()
@require_ai_calculator_csrf()
def submit_anonymous_assessment():
    """
    POST /api/ai-calculator/secure/assess/anonymous
    
    Submit anonymous AI job impact assessment (no email required):
    - No PII collection
    - Rate limiting: 3 assessments per hour per IP
    - Results not stored permanently
    - No email communication
    """
    try:
        # Get security service
        security_service = AICalculatorSecurityService(get_db_session())
        
        # Get validated data (no email required)
        data = request.get_json()
        ip_address = request.remote_addr or 'unknown'
        
        # Remove PII fields for anonymous assessment
        data.pop('email', None)
        data.pop('first_name', None)
        data.pop('location', None)
        
        # Calculate assessment scores
        automation_score, augmentation_score = calculate_job_scores(data)
        risk_level = determine_risk_level(automation_score, augmentation_score)
        recommendations = generate_recommendations(data, automation_score, augmentation_score, risk_level)
        
        # Generate temporary assessment ID
        assessment_id = f"anon_{str(uuid.uuid4())[:8]}"
        
        # Track analytics (no PII)
        analytics_service.track_anonymous_assessment(
            assessment_id=assessment_id,
            automation_score=automation_score,
            augmentation_score=augmentation_score,
            risk_level=risk_level,
            ip_address=ip_address
        )
        
        # Log anonymous assessment
        security_service.log_assessment_event(
            'anonymous_assessment_submitted', None, data, ip_address
        )
        
        return jsonify({
            'success': True,
            'assessment_id': assessment_id,
            'automation_score': automation_score,
            'augmentation_score': augmentation_score,
            'risk_level': risk_level,
            'recommendations': recommendations,
            'anonymous': True,
            'privacy_notice': {
                'data_collection': 'No personal data collected',
                'data_retention': 'Temporary (session only)',
                'data_usage': 'Assessment analysis only'
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Anonymous assessment submission error: {e}")
        return jsonify({
            'success': False,
            'error': 'anonymous_assessment_failed',
            'message': 'An error occurred while processing your assessment'
        }), 500


# =====================================================
# GDPR COMPLIANCE ENDPOINTS
# =====================================================

@ai_calculator_secure_bp.route('/gdpr/consent', methods=['POST'])
@secure_ai_calculator_endpoint(security_level=AICalculatorSecurityLevel.PUBLIC)
@require_ai_calculator_csrf()
def submit_gdpr_consent():
    """
    POST /api/ai-calculator/secure/gdpr/consent
    
    Submit GDPR consent for data processing:
    - Marketing communications
    - Analytics and improvement
    - Personalized recommendations
    """
    try:
        data = request.get_json()
        user_id = getattr(g, 'user_id', None)
        email = data.get('email')
        consent_types = data.get('consent_types', [])
        ip_address = request.remote_addr or 'unknown'
        
        if not email or not consent_types:
            return jsonify({
                'success': False,
                'error': 'missing_required_fields',
                'message': 'Email and consent types are required'
            }), 400
        
        # Create consent records
        success = create_ai_calculator_consent_record(
            user_id=user_id,
            email=email,
            consent_types=consent_types,
            ip_address=ip_address
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Consent recorded successfully',
                'consent_types': consent_types,
                'privacy_policy': get_ai_calculator_privacy_policy()
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'consent_recording_failed',
                'message': 'Failed to record consent'
            }), 500
        
    except Exception as e:
        logger.error(f"GDPR consent submission error: {e}")
        return jsonify({
            'success': False,
            'error': 'consent_submission_failed',
            'message': 'An error occurred while recording consent'
        }), 500


@ai_calculator_secure_bp.route('/gdpr/privacy-policy', methods=['GET'])
def get_privacy_policy():
    """
    GET /api/ai-calculator/secure/gdpr/privacy-policy
    
    Get AI Calculator privacy policy
    """
    try:
        return jsonify({
            'success': True,
            'privacy_policy': get_ai_calculator_privacy_policy()
        }), 200
        
    except Exception as e:
        logger.error(f"Privacy policy retrieval error: {e}")
        return jsonify({
            'success': False,
            'error': 'privacy_policy_retrieval_failed',
            'message': 'Failed to retrieve privacy policy'
        }), 500


@ai_calculator_secure_bp.route('/gdpr/export', methods=['POST'])
@require_auth
@secure_ai_calculator_endpoint(security_level=AICalculatorSecurityLevel.AUTHENTICATED)
@require_ai_calculator_csrf()
def export_user_data_endpoint():
    """
    POST /api/ai-calculator/secure/gdpr/export
    
    Export user data for GDPR compliance:
    - All assessment data
    - Conversion data
    - Decrypted PII data
    """
    try:
        user_id = g.user_id
        ip_address = request.remote_addr or 'unknown'
        
        # Export user data
        export_data = export_user_data(user_id)
        
        if 'error' in export_data:
            return jsonify({
                'success': False,
                'error': 'export_failed',
                'message': export_data['error']
            }), 500
        
        # Log the export request
        security_service = AICalculatorSecurityService(get_db_session())
        security_service.log_assessment_event(
            'data_export_requested', user_id, {}, ip_address
        )
        
        return jsonify({
            'success': True,
            'export_data': export_data,
            'message': 'Data export completed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Data export error: {e}")
        return jsonify({
            'success': False,
            'error': 'export_failed',
            'message': 'An error occurred while exporting data'
        }), 500


@ai_calculator_secure_bp.route('/gdpr/delete', methods=['POST'])
@require_auth
@secure_ai_calculator_endpoint(security_level=AICalculatorSecurityLevel.AUTHENTICATED)
@require_ai_calculator_csrf()
def delete_user_data_endpoint():
    """
    POST /api/ai-calculator/secure/gdpr/delete
    
    Delete user data for GDPR compliance:
    - All assessment data
    - Conversion data
    - Complete data erasure
    """
    try:
        user_id = g.user_id
        ip_address = request.remote_addr or 'unknown'
        
        # Delete user data
        deletion_result = delete_user_data(user_id)
        
        if 'error' in deletion_result:
            return jsonify({
                'success': False,
                'error': 'deletion_failed',
                'message': deletion_result['error']
            }), 500
        
        # Log the deletion request
        security_service = AICalculatorSecurityService(get_db_session())
        security_service.log_assessment_event(
            'data_deletion_requested', user_id, {}, ip_address
        )
        
        return jsonify({
            'success': True,
            'deletion_result': deletion_result,
            'message': 'Data deletion completed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Data deletion error: {e}")
        return jsonify({
            'success': False,
            'error': 'deletion_failed',
            'message': 'An error occurred while deleting data'
        }), 500


# =====================================================
# CSRF TOKEN ENDPOINTS
# =====================================================

@ai_calculator_secure_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    """
    GET /api/ai-calculator/secure/csrf-token
    
    Get CSRF token for form submission
    """
    try:
        token = generate_ai_calculator_csrf_token()
        return jsonify({
            'success': True,
            'csrf_token': token
        }), 200
        
    except Exception as e:
        logger.error(f"CSRF token generation error: {e}")
        return jsonify({
            'success': False,
            'error': 'csrf_token_generation_failed',
            'message': 'Failed to generate CSRF token'
        }), 500


# =====================================================
# ASSESSMENT RETRIEVAL ENDPOINTS
# =====================================================

@ai_calculator_secure_bp.route('/assessment/<assessment_id>', methods=['GET'])
@optional_auth
@secure_ai_calculator_endpoint(security_level=AICalculatorSecurityLevel.AUTHENTICATED)
def get_assessment_result(assessment_id: str):
    """
    GET /api/ai-calculator/secure/assessment/<assessment_id>
    
    Get assessment result with proper authorization:
    - Users can only access their own assessments
    - Anonymous assessments require special handling
    """
    try:
        user_id = getattr(g, 'user_id', None)
        ip_address = request.remote_addr or 'unknown'
        
        # Get assessment from database
        result = get_db_session().execute(text("""
            SELECT * FROM ai_job_assessments 
            WHERE id = :assessment_id
        """), {'assessment_id': assessment_id}).fetchone()
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'assessment_not_found',
                'message': 'Assessment not found'
            }), 404
        
        assessment_data = dict(result._mapping)
        
        # Check authorization
        if assessment_data['user_id'] and assessment_data['user_id'] != user_id:
            return jsonify({
                'success': False,
                'error': 'unauthorized_access',
                'message': 'Access denied'
            }), 403
        
        # Decrypt PII data if user is authorized
        security_service = AICalculatorSecurityService(get_db_session())
        if assessment_data['user_id'] == user_id:
            for field in ['first_name', 'email', 'location']:
                if assessment_data.get(field):
                    assessment_data[field] = security_service.decrypt_pii(assessment_data[field])
        
        # Log access
        security_service.log_assessment_event(
            'assessment_accessed', user_id, {'assessment_id': assessment_id}, ip_address
        )
        
        return jsonify({
            'success': True,
            'assessment': assessment_data
        }), 200
        
    except Exception as e:
        logger.error(f"Assessment retrieval error: {e}")
        return jsonify({
            'success': False,
            'error': 'assessment_retrieval_failed',
            'message': 'An error occurred while retrieving assessment'
        }), 500


# =====================================================
# ADMIN ENDPOINTS
# =====================================================

@ai_calculator_secure_bp.route('/admin/data-retention', methods=['POST'])
@require_auth
@secure_ai_calculator_endpoint(security_level=AICalculatorSecurityLevel.ADMIN)
def enforce_data_retention():
    """
    POST /api/ai-calculator/secure/admin/data-retention
    
    Admin endpoint to enforce data retention policies:
    - Delete old assessment data (2+ years)
    - Delete old conversion data
    - Log cleanup activities
    """
    try:
        # Check admin permissions
        if not hasattr(g, 'user_role') or g.user_role != 'admin':
            return jsonify({
                'success': False,
                'error': 'insufficient_permissions',
                'message': 'Admin access required'
            }), 403
        
        security_service = AICalculatorSecurityService(get_db_session())
        cleanup_result = security_service.enforce_data_retention()
        
        if 'error' in cleanup_result:
            return jsonify({
                'success': False,
                'error': 'retention_enforcement_failed',
                'message': cleanup_result['error']
            }), 500
        
        return jsonify({
            'success': True,
            'cleanup_result': cleanup_result,
            'message': 'Data retention policies enforced successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Data retention enforcement error: {e}")
        return jsonify({
            'success': False,
            'error': 'retention_enforcement_failed',
            'message': 'An error occurred while enforcing data retention'
        }), 500


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def calculate_job_scores(data: Dict[str, Any]) -> tuple[int, int]:
    """Calculate automation and augmentation scores"""
    # Base scores from job risk data
    base_automation = 50
    base_augmentation = 50
    
    # Industry modifiers
    industry_modifiers = {
        'technology': {'automation': -10, 'augmentation': 15},
        'healthcare': {'automation': 5, 'augmentation': 20},
        'finance': {'automation': 10, 'augmentation': 10},
        'manufacturing': {'automation': 20, 'augmentation': 5},
        'retail': {'automation': 15, 'augmentation': 8},
        'marketing': {'automation': 8, 'augmentation': 12},
        'education': {'automation': 5, 'augmentation': 15},
        'legal': {'automation': 3, 'augmentation': 18},
        'consulting': {'automation': 5, 'augmentation': 15}
    }
    
    industry = data.get('industry', 'other')
    if industry in industry_modifiers:
        base_automation += industry_modifiers[industry]['automation']
        base_augmentation += industry_modifiers[industry]['augmentation']
    
    # Experience level modifiers
    experience_modifiers = {
        'entry': {'automation': 5, 'augmentation': -5},
        'mid': {'automation': 0, 'augmentation': 0},
        'senior': {'automation': -5, 'augmentation': 10},
        'executive': {'automation': -10, 'augmentation': 15}
    }
    
    experience = data.get('experience_level', 'mid')
    if experience in experience_modifiers:
        base_automation += experience_modifiers[experience]['automation']
        base_augmentation += experience_modifiers[experience]['augmentation']
    
    # Tech skills modifiers
    tech_modifiers = {
        'basic': {'automation': 10, 'augmentation': -10},
        'intermediate': {'automation': 0, 'augmentation': 0},
        'advanced': {'automation': -5, 'augmentation': 10},
        'expert': {'automation': -10, 'augmentation': 15}
    }
    
    tech_skills = data.get('tech_skills_level', 'intermediate')
    if tech_skills in tech_modifiers:
        base_automation += tech_modifiers[tech_skills]['automation']
        base_augmentation += tech_modifiers[tech_skills]['augmentation']
    
    # Ensure scores are within bounds
    automation_score = max(0, min(100, base_automation))
    augmentation_score = max(0, min(100, base_augmentation))
    
    return automation_score, augmentation_score


def determine_risk_level(automation_score: int, augmentation_score: int) -> str:
    """Determine overall risk level based on scores"""
    if automation_score >= 70:
        return 'high'
    elif automation_score >= 40:
        return 'medium'
    else:
        return 'low'


def generate_recommendations(data: Dict[str, Any], automation_score: int, 
                           augmentation_score: int, risk_level: str) -> Dict[str, Any]:
    """Generate personalized recommendations"""
    recommendations = {
        'risk_factors': {},
        'mitigation_strategies': [],
        'recommended_skills': [],
        'career_advice': {}
    }
    
    # Risk factors
    if automation_score > 60:
        recommendations['risk_factors']['automation_risk'] = 'High automation potential'
    if augmentation_score < 30:
        recommendations['risk_factors']['skill_gap'] = 'Limited AI augmentation skills'
    
    # Mitigation strategies
    if risk_level == 'high':
        recommendations['mitigation_strategies'].extend([
            'Develop AI-resistant skills',
            'Focus on creative and strategic work',
            'Build human-centric expertise'
        ])
    elif risk_level == 'medium':
        recommendations['mitigation_strategies'].extend([
            'Learn AI collaboration tools',
            'Develop hybrid human-AI workflows',
            'Stay updated with industry trends'
        ])
    else:
        recommendations['mitigation_strategies'].extend([
            'Leverage AI for productivity gains',
            'Focus on AI-augmented decision making',
            'Develop AI leadership skills'
        ])
    
    # Recommended skills
    if automation_score > 50:
        recommendations['recommended_skills'].extend([
            'Strategic thinking',
            'Creative problem solving',
            'Human-AI collaboration'
        ])
    
    if augmentation_score < 50:
        recommendations['recommended_skills'].extend([
            'AI tool proficiency',
            'Data analysis',
            'Process optimization'
        ])
    
    # Career advice
    recommendations['career_advice'] = {
        'short_term': 'Focus on developing AI collaboration skills',
        'medium_term': 'Build expertise in areas where human judgment is critical',
        'long_term': 'Position yourself as an AI-human interface specialist'
    }
    
    return recommendations
