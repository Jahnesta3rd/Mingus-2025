"""
AI Job Impact Calculator Flask API Endpoints
Comprehensive API for AI job impact assessment, job search, and conversion tracking
"""

import logging
import re
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher
from flask import Blueprint, request, jsonify, current_app
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from werkzeug.exceptions import BadRequest

from backend.models.ai_job_models import AIJobAssessment, AIJobRiskData, AICalculatorConversion
from backend.services.resend_email_service import ResendEmailService
from backend.utils.validation import validate_email_format
from backend.utils.rate_limiting import limiter
from backend.utils.response_helpers import create_response

logger = logging.getLogger(__name__)

ai_calculator_bp = Blueprint('ai_calculator', __name__, url_prefix='/api/ai-calculator')

# Initialize services
resend_email_service = ResendEmailService()
csrf = CSRFProtect()

# Scoring configuration
SCORING_CONFIG = {
    'automation_bounds': (5, 80),
    'augmentation_bounds': (10, 85),
    'industry_modifiers': {
        'technology': {'automation': 10, 'augmentation': 15},
        'healthcare': {'automation': -10, 'augmentation': 5},
        'finance': {'automation': 5, 'augmentation': 10},
        'manufacturing': {'automation': 15, 'augmentation': -5},
        'retail': {'automation': 10, 'augmentation': 0},
        'marketing': {'automation': 0, 'augmentation': 10},
        'education': {'automation': -5, 'augmentation': 5},
        'legal': {'automation': -10, 'augmentation': 0},
        'consulting': {'automation': -5, 'augmentation': 10}
    },
    'task_modifiers': {
        'coding': {'automation': 5, 'augmentation': 10},
        'writing': {'automation': 5, 'augmentation': 8},
        'analysis': {'automation': 5, 'augmentation': 12},
        'data_entry': {'automation': 15, 'augmentation': -5},
        'customer_service': {'automation': 10, 'augmentation': 0},
        'project_management': {'automation': -5, 'augmentation': 8},
        'creative_design': {'automation': -8, 'augmentation': 5},
        'sales': {'automation': 0, 'augmentation': 10}
    },
    'experience_modifiers': {
        'entry': {'automation': 0, 'augmentation': 0},
        'mid': {'automation': -2, 'augmentation': 5},
        'senior': {'automation': -5, 'augmentation': 10},
        'executive': {'automation': -8, 'augmentation': 15}
    },
    'ai_usage_modifiers': {
        'never': {'automation': 0, 'augmentation': 0},
        'rarely': {'automation': 0, 'augmentation': 2},
        'sometimes': {'automation': -2, 'augmentation': 5},
        'often': {'automation': -5, 'augmentation': 10},
        'always': {'automation': -10, 'augmentation': 15}
    },
    'tech_skills_modifiers': {
        'basic': {'automation': 0, 'augmentation': 0},
        'intermediate': {'automation': -3, 'augmentation': 5},
        'advanced': {'automation': -5, 'augmentation': 8},
        'expert': {'automation': -8, 'augmentation': 12}
    }
}

@ai_calculator_bp.route('/assess', methods=['POST'])
@limiter.limit('5 per minute')
def assess_job_impact():
    """
    POST /api/ai-calculator/assess
    Accept form data from 5-step assessment and calculate AI job impact scores
    
    Request Body:
    {
        "job_title": "string",
        "industry": "string",
        "experience_level": "string",
        "tasks_array": ["string"],
        "remote_work_frequency": "string",
        "ai_usage_frequency": "string",
        "team_size": "string",
        "tech_skills_level": "string",
        "concerns_array": ["string"],
        "first_name": "string",
        "email": "string",
        "location": "string",
        "utm_source": "string",
        "utm_medium": "string",
        "utm_campaign": "string",
        "utm_term": "string",
        "utm_content": "string"
    }
    
    Response:
    {
        "success": true,
        "assessment_id": "uuid",
        "automation_score": integer,
        "augmentation_score": integer,
        "risk_level": "string",
        "recommendations": ["string"],
        "email_sent": boolean
    }
    """
    try:
        data = request.get_json()
        if not data:
            return create_response(
                success=False,
                error='no_data',
                message='No data provided'
            ), 400
        
        # Validate required fields
        required_fields = [
            'job_title', 'industry', 'experience_level', 'tasks_array',
            'remote_work_frequency', 'ai_usage_frequency', 'team_size',
            'tech_skills_level', 'concerns_array', 'first_name', 'email'
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                return create_response(
                    success=False,
                    error='missing_field',
                    message=f'Missing required field: {field}'
                ), 400
        
        # Validate email format
        email = data['email'].strip().lower()
        if not validate_email_format(email):
            return create_response(
                success=False,
                error='invalid_email',
                message='Invalid email format'
            ), 400
        
        # Validate enum values
        validation_errors = validate_assessment_data(data)
        if validation_errors:
            return create_response(
                success=False,
                error='validation_error',
                message='Invalid data provided',
                details=validation_errors
            ), 400
        
        # Calculate scores
        automation_score, augmentation_score = calculate_job_scores(data)
        
        # Determine risk level
        risk_level = determine_risk_level(automation_score, augmentation_score)
        
        # Generate recommendations
        recommendations = generate_recommendations(data, automation_score, augmentation_score, risk_level)
        
        # Create assessment record
        assessment = create_assessment_record(data, automation_score, augmentation_score, risk_level, recommendations)
        
        # Send welcome email
        email_sent = send_assessment_results_email(assessment, recommendations)
        
        # Track conversion
        track_conversion(assessment.id, 'email_signup', 25.00)
        
        response_data = {
            'success': True,
            'assessment_id': str(assessment.id),
            'automation_score': automation_score,
            'augmentation_score': augmentation_score,
            'risk_level': risk_level,
            'recommendations': recommendations,
            'email_sent': email_sent,
            'message': 'Assessment completed successfully'
        }
        
        if not email_sent:
            response_data['email_message'] = 'Email service temporarily unavailable. Your results have been saved.'
        
        logger.info(f"AI job assessment completed for {email}: {risk_level} risk")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error in job impact assessment: {str(e)}")
        return create_response(
            success=False,
            error='assessment_failed',
            message='Failed to complete assessment'
        ), 500

@ai_calculator_bp.route('/job-search', methods=['GET'])
@limiter.limit('10 per minute')
def search_jobs():
    """
    GET /api/ai-calculator/job-search?job_title=string
    Fuzzy search for job titles in the risk data table
    
    Query Parameters:
    - job_title: string (required)
    
    Response:
    {
        "success": true,
        "results": [
            {
                "job_keyword": "string",
                "automation_base_score": integer,
                "augmentation_base_score": integer,
                "risk_category": "string",
                "similarity_score": float
            }
        ]
    }
    """
    try:
        job_title = request.args.get('job_title', '').strip()
        if not job_title:
            return create_response(
                success=False,
                error='missing_job_title',
                message='job_title parameter is required'
            ), 400
        
        # Get database session
        db = current_app.db_session
        
        # Get all job risk data
        risk_data = db.query(AIJobRiskData).all()
        
        # Calculate similarity scores
        search_results = []
        for job_data in risk_data:
            similarity = calculate_similarity(job_title.lower(), job_data.job_keyword.lower())
            if similarity > 0.3:  # Minimum similarity threshold
                search_results.append({
                    'job_keyword': job_data.job_keyword,
                    'automation_base_score': job_data.automation_base_score,
                    'augmentation_base_score': job_data.augmentation_base_score,
                    'risk_category': job_data.risk_category,
                    'similarity_score': round(similarity, 3)
                })
        
        # Sort by similarity score and limit to 10 results
        search_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        search_results = search_results[:10]
        
        response_data = {
            'success': True,
            'query': job_title,
            'results': search_results,
            'total_results': len(search_results)
        }
        
        logger.info(f"Job search completed for '{job_title}': {len(search_results)} results")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error in job search: {str(e)}")
        return create_response(
            success=False,
            error='search_failed',
            message='Failed to search jobs'
        ), 500

@ai_calculator_bp.route('/convert', methods=['POST'])
@limiter.limit('10 per minute')
def track_conversion_event():
    """
    POST /api/ai-calculator/convert
    Track conversion events and trigger Stripe checkout for paid conversions
    
    Request Body:
    {
        "assessment_id": "uuid",
        "conversion_type": "string",
        "conversion_value": float,
        "conversion_source": "string",
        "conversion_medium": "string",
        "conversion_campaign": "string"
    }
    
    Response:
    {
        "success": true,
        "conversion_id": "uuid",
        "stripe_session_id": "string" (for paid conversions)
    }
    """
    try:
        data = request.get_json()
        if not data:
            return create_response(
                success=False,
                error='no_data',
                message='No data provided'
            ), 400
        
        # Validate required fields
        required_fields = ['assessment_id', 'conversion_type', 'conversion_value']
        for field in required_fields:
            if field not in data:
                return create_response(
                    success=False,
                    error='missing_field',
                    message=f'Missing required field: {field}'
                ), 400
        
        # Validate conversion type
        valid_conversion_types = ['email_signup', 'paid_upgrade', 'consultation_booking', 'course_enrollment']
        if data['conversion_type'] not in valid_conversion_types:
            return create_response(
                success=False,
                error='invalid_conversion_type',
                message=f'Invalid conversion type. Must be one of: {", ".join(valid_conversion_types)}'
            ), 400
        
        # Validate assessment exists
        db = current_app.db_session
        assessment = db.query(AIJobAssessment).filter(AIJobAssessment.id == data['assessment_id']).first()
        if not assessment:
            return create_response(
                success=False,
                error='assessment_not_found',
                message='Assessment not found'
            ), 404
        
        # Create conversion record
        conversion = create_conversion_record(data, assessment)
        
        # Handle paid conversions
        stripe_session_id = None
        if data['conversion_type'] in ['paid_upgrade', 'consultation_booking', 'course_enrollment']:
            stripe_session_id = create_stripe_checkout_session(conversion, assessment)
        
        response_data = {
            'success': True,
            'conversion_id': str(conversion.id),
            'conversion_type': conversion.conversion_type,
            'conversion_value': float(conversion.conversion_value)
        }
        
        if stripe_session_id:
            response_data['stripe_session_id'] = stripe_session_id
        
        logger.info(f"Conversion tracked: {conversion.conversion_type} for assessment {assessment.id}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error tracking conversion: {str(e)}")
        return create_response(
            success=False,
            error='conversion_failed',
            message='Failed to track conversion'
        ), 500

# Helper Functions

def validate_assessment_data(data: Dict[str, Any]) -> List[str]:
    """Validate assessment data against allowed values"""
    errors = []
    
    # Validate experience level
    valid_experience = ['entry', 'mid', 'senior', 'executive']
    if data['experience_level'] not in valid_experience:
        errors.append(f"experience_level must be one of: {', '.join(valid_experience)}")
    
    # Validate remote work frequency
    valid_remote = ['never', 'rarely', 'sometimes', 'often', 'always']
    if data['remote_work_frequency'] not in valid_remote:
        errors.append(f"remote_work_frequency must be one of: {', '.join(valid_remote)}")
    
    # Validate AI usage frequency
    valid_ai_usage = ['never', 'rarely', 'sometimes', 'often', 'always']
    if data['ai_usage_frequency'] not in valid_ai_usage:
        errors.append(f"ai_usage_frequency must be one of: {', '.join(valid_ai_usage)}")
    
    # Validate team size
    valid_team_size = ['1-5', '6-10', '11-25', '26-50', '50+']
    if data['team_size'] not in valid_team_size:
        errors.append(f"team_size must be one of: {', '.join(valid_team_size)}")
    
    # Validate tech skills level
    valid_tech_skills = ['basic', 'intermediate', 'advanced', 'expert']
    if data['tech_skills_level'] not in valid_tech_skills:
        errors.append(f"tech_skills_level must be one of: {', '.join(valid_tech_skills)}")
    
    return errors

def calculate_job_scores(data: Dict[str, Any]) -> Tuple[int, int]:
    """Calculate automation and augmentation scores based on assessment data"""
    
    # Get base scores from job title matching
    base_automation, base_augmentation = get_base_scores_from_job_title(data['job_title'])
    
    # Apply industry modifiers
    industry_mod = SCORING_CONFIG['industry_modifiers'].get(data['industry'], {'automation': 0, 'augmentation': 0})
    base_automation += industry_mod['automation']
    base_augmentation += industry_mod['augmentation']
    
    # Apply task-based modifiers
    for task in data['tasks_array']:
        task_mod = SCORING_CONFIG['task_modifiers'].get(task, {'automation': 0, 'augmentation': 0})
        base_automation += task_mod['automation']
        base_augmentation += task_mod['augmentation']
    
    # Apply experience modifiers
    exp_mod = SCORING_CONFIG['experience_modifiers'].get(data['experience_level'], {'automation': 0, 'augmentation': 0})
    base_automation += exp_mod['automation']
    base_augmentation += exp_mod['augmentation']
    
    # Apply AI usage modifiers
    ai_mod = SCORING_CONFIG['ai_usage_modifiers'].get(data['ai_usage_frequency'], {'automation': 0, 'augmentation': 0})
    base_automation += ai_mod['automation']
    base_augmentation += ai_mod['augmentation']
    
    # Apply tech skills modifiers
    tech_mod = SCORING_CONFIG['tech_skills_modifiers'].get(data['tech_skills_level'], {'automation': 0, 'augmentation': 0})
    base_automation += tech_mod['automation']
    base_augmentation += tech_mod['augmentation']
    
    # Ensure scores stay within bounds
    automation_score = max(SCORING_CONFIG['automation_bounds'][0], 
                          min(SCORING_CONFIG['automation_bounds'][1], base_automation))
    augmentation_score = max(SCORING_CONFIG['augmentation_bounds'][0], 
                            min(SCORING_CONFIG['augmentation_bounds'][1], base_augmentation))
    
    return int(automation_score), int(augmentation_score)

def get_base_scores_from_job_title(job_title: str) -> Tuple[int, int]:
    """Get base scores from job title using fuzzy matching"""
    
    # Default scores
    default_automation = 50
    default_augmentation = 50
    
    try:
        db = current_app.db_session
        risk_data = db.query(AIJobRiskData).all()
        
        best_match = None
        best_similarity = 0
        
        for job_data in risk_data:
            similarity = calculate_similarity(job_title.lower(), job_data.job_keyword.lower())
            if similarity > best_similarity and similarity > 0.6:  # High similarity threshold
                best_similarity = similarity
                best_match = job_data
        
        if best_match:
            return best_match.automation_base_score, best_match.augmentation_base_score
        
        # If no good match, use keyword-based scoring
        job_title_lower = job_title.lower()
        
        # High automation risk keywords
        high_automation_keywords = ['data entry', 'bookkeeping', 'administrative', 'clerical', 'receptionist']
        for keyword in high_automation_keywords:
            if keyword in job_title_lower:
                return 75, 25
        
        # Low automation risk keywords
        low_automation_keywords = ['engineer', 'developer', 'manager', 'director', 'executive', 'creative', 'designer']
        for keyword in low_automation_keywords:
            if keyword in job_title_lower:
                return 20, 80
        
        # Medium automation risk keywords
        medium_automation_keywords = ['analyst', 'coordinator', 'specialist', 'consultant', 'representative']
        for keyword in medium_automation_keywords:
            if keyword in job_title_lower:
                return 45, 55
        
        return default_automation, default_augmentation
        
    except Exception as e:
        logger.warning(f"Error getting base scores for job title '{job_title}': {e}")
        return default_automation, default_augmentation

def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings using SequenceMatcher"""
    return SequenceMatcher(None, str1, str2).ratio()

def determine_risk_level(automation_score: int, augmentation_score: int) -> str:
    """Determine overall risk level based on scores"""
    total_impact = automation_score + (100 - augmentation_score)  # Higher augmentation = lower risk
    
    if total_impact >= 50:
        return 'high'
    elif total_impact >= 30:
        return 'medium'
    else:
        return 'low'

def generate_recommendations(data: Dict[str, Any], automation_score: int, augmentation_score: int, risk_level: str) -> List[str]:
    """Generate personalized recommendations based on assessment data"""
    recommendations = []
    
    # Base recommendations by risk level
    if risk_level == 'high':
        recommendations.extend([
            "Focus on developing skills that complement AI rather than compete with it",
            "Consider transitioning to roles that require human creativity and emotional intelligence",
            "Build expertise in AI tools to become more valuable in your field",
            "Develop strong interpersonal and communication skills",
            "Consider upskilling in areas that are difficult to automate"
        ])
    elif risk_level == 'medium':
        recommendations.extend([
            "Stay updated with AI trends in your industry",
            "Develop skills that enhance your ability to work alongside AI",
            "Consider how AI can augment your current role",
            "Build expertise in areas that require human judgment",
            "Focus on strategic thinking and problem-solving skills"
        ])
    else:  # low risk
        recommendations.extend([
            "Continue developing your technical and analytical skills",
            "Explore ways to leverage AI to increase your productivity",
            "Consider mentoring others in AI adoption",
            "Focus on leadership and innovation skills",
            "Stay ahead of the curve by learning emerging technologies"
        ])
    
    # Industry-specific recommendations
    industry = data['industry']
    if industry == 'technology':
        recommendations.append("Focus on emerging technologies like machine learning and data science")
    elif industry == 'finance':
        recommendations.append("Develop expertise in fintech and algorithmic trading")
    elif industry == 'healthcare':
        recommendations.append("Learn about AI applications in medical diagnosis and patient care")
    elif industry == 'marketing':
        recommendations.append("Master AI-powered marketing tools and analytics platforms")
    
    # Job-specific recommendations
    job_title = data['job_title'].lower()
    if 'manager' in job_title or 'director' in job_title:
        recommendations.append("Develop skills in AI strategy and team leadership")
    elif 'engineer' in job_title or 'developer' in job_title:
        recommendations.append("Focus on AI/ML development and system architecture")
    elif 'analyst' in job_title:
        recommendations.append("Learn advanced analytics and data visualization tools")
    
    # AI usage recommendations
    if data['ai_usage_frequency'] in ['never', 'rarely']:
        recommendations.append("Start experimenting with AI tools relevant to your field")
    
    return recommendations[:5]  # Return top 5 recommendations

def create_assessment_record(data: Dict[str, Any], automation_score: int, augmentation_score: int, risk_level: str, recommendations: List[str]) -> AIJobAssessment:
    """Create and save assessment record to database"""
    
    db = current_app.db_session
    
    assessment = AIJobAssessment(
        job_title=data['job_title'],
        industry=data['industry'],
        experience_level=data['experience_level'],
        tasks_array=data['tasks_array'],
        remote_work_frequency=data['remote_work_frequency'],
        ai_usage_frequency=data['ai_usage_frequency'],
        team_size=data['team_size'],
        tech_skills_level=data['tech_skills_level'],
        concerns_array=data['concerns_array'],
        first_name=data['first_name'],
        email=data['email'],
        location=data.get('location', ''),
        automation_score=automation_score,
        augmentation_score=augmentation_score,
        overall_risk_level=risk_level,
        utm_source=data.get('utm_source'),
        utm_medium=data.get('utm_medium'),
        utm_campaign=data.get('utm_campaign'),
        utm_term=data.get('utm_term'),
        utm_content=data.get('utm_content'),
        questions_answered=15,
        total_questions=15,
        completion_percentage=100.0,
        risk_factors=analyze_risk_factors(data),
        mitigation_strategies=generate_mitigation_strategies(data, risk_level),
        recommended_skills=generate_recommended_skills(data),
        career_advice=generate_career_advice(data, risk_level)
    )
    
    db.add(assessment)
    db.commit()
    
    return assessment

def analyze_risk_factors(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze risk factors for the job"""
    risk_factors = {
        'high_automation_tasks': [],
        'low_skill_requirements': False,
        'repetitive_work': False,
        'limited_creativity': False,
        'easily_measurable_output': False
    }
    
    # Analyze tasks for automation risk
    high_risk_tasks = ['data_entry', 'reporting', 'customer_service']
    for task in data['tasks_array']:
        if task in high_risk_tasks:
            risk_factors['high_automation_tasks'].append(task)
    
    # Analyze other factors
    if data['tech_skills_level'] == 'basic':
        risk_factors['low_skill_requirements'] = True
    
    if 'data_entry' in data['tasks_array'] or 'reporting' in data['tasks_array']:
        risk_factors['repetitive_work'] = True
    
    return risk_factors

def generate_mitigation_strategies(data: Dict[str, Any], risk_level: str) -> List[str]:
    """Generate mitigation strategies based on risk factors"""
    strategies = []
    
    if risk_level == 'high':
        strategies.extend([
            "Upskill in areas requiring human creativity and emotional intelligence",
            "Develop expertise in AI tools to become more valuable",
            "Consider transitioning to roles that are difficult to automate",
            "Build strong networking and relationship-building skills",
            "Focus on strategic thinking and decision-making"
        ])
    elif risk_level == 'medium':
        strategies.extend([
            "Stay updated with industry trends and emerging technologies",
            "Develop skills that complement AI capabilities",
            "Focus on areas requiring human judgment and creativity",
            "Build expertise in your domain knowledge",
            "Learn to work effectively with AI tools"
        ])
    else:
        strategies.extend([
            "Continue developing technical and analytical skills",
            "Explore ways to leverage AI for productivity gains",
            "Focus on innovation and strategic thinking",
            "Mentor others in AI adoption and best practices",
            "Stay ahead of emerging technologies"
        ])
    
    return strategies

def generate_recommended_skills(data: Dict[str, Any]) -> List[str]:
    """Generate recommended skills based on assessment"""
    skills = []
    industry = data['industry']
    job_title = data['job_title'].lower()
    
    # Core skills for all roles
    skills.extend([
        "Data Analysis",
        "Critical Thinking",
        "Problem Solving",
        "Communication",
        "Adaptability"
    ])
    
    # Industry-specific skills
    if industry == 'technology':
        skills.extend(["Machine Learning", "Python", "Data Science", "Cloud Computing"])
    elif industry == 'finance':
        skills.extend(["Financial Modeling", "Risk Management", "Fintech", "Blockchain"])
    elif industry == 'marketing':
        skills.extend(["Digital Marketing", "Analytics", "Content Strategy", "SEO/SEM"])
    elif industry == 'healthcare':
        skills.extend(["Healthcare Analytics", "Patient Care", "Medical Technology", "Regulatory Compliance"])
    
    # Role-specific skills
    if 'manager' in job_title:
        skills.extend(["Leadership", "Project Management", "Strategic Planning", "Team Building"])
    elif 'analyst' in job_title:
        skills.extend(["Statistical Analysis", "SQL", "Data Visualization", "Business Intelligence"])
    elif 'engineer' in job_title:
        skills.extend(["Software Development", "System Architecture", "DevOps", "API Design"])
    
    return skills[:8]  # Return top 8 skills

def generate_career_advice(data: Dict[str, Any], risk_level: str) -> Dict[str, Any]:
    """Generate personalized career advice"""
    advice = {
        'short_term': [],
        'medium_term': [],
        'long_term': [],
        'immediate_actions': []
    }
    
    if risk_level == 'high':
        advice['immediate_actions'].extend([
            "Start learning AI tools relevant to your field",
            "Identify transferable skills you can leverage",
            "Network with professionals in emerging roles",
            "Research alternative career paths in your industry"
        ])
        
        advice['short_term'].extend([
            "Enroll in online courses for in-demand skills",
            "Join professional groups focused on AI and automation",
            "Start a side project to build new skills",
            "Seek mentorship from industry leaders"
        ])
        
        advice['medium_term'].extend([
            "Consider transitioning to a more future-proof role",
            "Build a portfolio showcasing your new skills",
            "Develop expertise in areas requiring human creativity",
            "Explore entrepreneurship opportunities"
        ])
        
        advice['long_term'].extend([
            "Position yourself as an AI-human collaboration expert",
            "Consider consulting or advisory roles",
            "Build a personal brand around your unique value proposition",
            "Explore opportunities in emerging industries"
        ])
    
    elif risk_level == 'medium':
        advice['immediate_actions'].extend([
            "Stay updated with AI trends in your industry",
            "Identify how AI can augment your current role",
            "Start experimenting with AI tools",
            "Document your current skills and expertise"
        ])
        
        advice['short_term'].extend([
            "Learn to work effectively with AI tools",
            "Develop skills that complement AI capabilities",
            "Build relationships with AI teams in your organization",
            "Take on projects that involve AI integration"
        ])
        
        advice['medium_term'].extend([
            "Become an AI champion in your organization",
            "Develop expertise in AI strategy and implementation",
            "Build a reputation for innovation and adaptability",
            "Consider roles that bridge human and AI capabilities"
        ])
        
        advice['long_term'].extend([
            "Position yourself as a thought leader in AI adoption",
            "Explore opportunities in AI consulting or training",
            "Develop expertise in AI ethics and governance",
            "Consider leadership roles in AI-driven organizations"
        ])
    
    else:  # low risk
        advice['immediate_actions'].extend([
            "Continue developing your technical expertise",
            "Explore ways to leverage AI for productivity gains",
            "Mentor others in AI adoption",
            "Stay ahead of emerging technologies"
        ])
        
        advice['short_term'].extend([
            "Lead AI initiatives in your organization",
            "Develop AI strategy and implementation skills",
            "Build expertise in cutting-edge technologies",
            "Share your knowledge through speaking and writing"
        ])
        
        advice['medium_term'].extend([
            "Position yourself as an AI innovation leader",
            "Explore opportunities in AI research and development",
            "Build a network of AI professionals and thought leaders",
            "Consider advisory or consulting roles"
        ])
        
        advice['long_term'].extend([
            "Become a recognized expert in AI and its applications",
            "Explore opportunities in AI policy and governance",
            "Consider founding or leading AI-focused organizations",
            "Contribute to the development of AI standards and best practices"
        ])
    
    return advice

def send_assessment_results_email(assessment: AIJobAssessment, recommendations: List[str]) -> bool:
    """Send assessment results email via Resend"""
    try:
        html_content = create_assessment_results_email(assessment, recommendations)
        
        result = resend_email_service.send_email(
            to_email=assessment.email,
            subject=f"Your AI Job Impact Analysis: {assessment.overall_risk_level.title()} Risk Level",
            html_content=html_content
        )
        
        if result['success']:
            logger.info(f"Assessment results email sent successfully to: {assessment.email}")
            return True
        else:
            logger.warning(f"Failed to send assessment results email to {assessment.email}: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.warning(f"Failed to send assessment results email: {e}")
        return False

def create_assessment_results_email(assessment: AIJobAssessment, recommendations: List[str]) -> str:
    """Create HTML email content for assessment results"""
    risk_color = {
        'low': '#10b981',
        'medium': '#f59e0b', 
        'high': '#ef4444'
    }.get(assessment.overall_risk_level, '#6b7280')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your AI Job Impact Analysis</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #8A31FF 0%, #10b981 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 10px; margin: 20px 0; }}
            .score-card {{ background: white; padding: 20px; border-radius: 8px; margin: 15px 0; text-align: center; }}
            .risk-badge {{ display: inline-block; background: {risk_color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; }}
            .recommendation {{ background: white; padding: 15px; border-left: 4px solid #10b981; margin: 10px 0; }}
            .cta-button {{ display: inline-block; background: #8A31FF; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
            .footer {{ text-align: center; color: #666; font-size: 14px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Your AI Job Impact Analysis</h1>
                <p>Hi {assessment.first_name}, here's your personalized assessment for {assessment.job_title}</p>
            </div>
            
            <div class="content">
                <h2>Your Risk Level: <span class="risk-badge">{assessment.overall_risk_level.upper()}</span></h2>
                
                <div class="score-card">
                    <h3>Automation Risk</h3>
                    <h2 style="color: #ef4444; font-size: 2em;">{assessment.automation_score}%</h2>
                    <p>This represents how likely your current tasks could be automated by AI</p>
                </div>
                
                <div class="score-card">
                    <h3>AI Augmentation Potential</h3>
                    <h2 style="color: #10b981; font-size: 2em;">{assessment.augmentation_score}%</h2>
                    <p>This shows how much AI could enhance your productivity and capabilities</p>
                </div>
                
                <h3>🎯 Personalized Recommendations</h3>
                {''.join([f'<div class="recommendation"><strong>•</strong> {rec}</div>' for rec in recommendations])}
                
                <div style="text-align: center;">
                    <a href="https://mingusapp.com/dashboard" class="cta-button">Access Your Full Report</a>
                </div>
                
                <h3>📊 Key Insights</h3>
                <ul>
                    <li><strong>Industry:</strong> {assessment.industry.title()}</li>
                    <li><strong>Experience Level:</strong> {assessment.experience_level.title()}</li>
                    <li><strong>Team Size:</strong> {assessment.team_size}</li>
                    <li><strong>AI Usage:</strong> {assessment.ai_usage_frequency.title()}</li>
                </ul>
            </div>
            
            <div class="footer">
                <p>This analysis was generated based on your responses to our AI Job Impact Calculator.</p>
                <p>© 2024 MINGUS. All rights reserved.</p>
                <p><a href="mailto:support@mingusapp.com">support@mingusapp.com</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def create_conversion_record(data: Dict[str, Any], assessment: AIJobAssessment) -> AICalculatorConversion:
    """Create and save conversion record to database"""
    
    db = current_app.db_session
    
    conversion = AICalculatorConversion(
        assessment_id=assessment.id,
        conversion_type=data['conversion_type'],
        conversion_value=data['conversion_value'],
        conversion_source=data.get('conversion_source'),
        conversion_medium=data.get('conversion_medium'),
        conversion_campaign=data.get('conversion_campaign')
    )
    
    db.add(conversion)
    db.commit()
    
    return conversion

def create_stripe_checkout_session(conversion: AICalculatorConversion, assessment: AIJobAssessment) -> Optional[str]:
    """Create Stripe checkout session for paid conversions"""
    try:
        # Import Stripe here to avoid circular imports
        import stripe
        
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        
        if not stripe.api_key:
            logger.warning("Stripe API key not configured")
            return None
        
        # Create checkout session based on conversion type
        session_data = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': get_product_name(conversion.conversion_type),
                        'description': get_product_description(conversion.conversion_type)
                    },
                    'unit_amount': int(conversion.conversion_value * 100)  # Convert to cents
                },
                'quantity': 1
            }],
            'mode': 'payment',
            'success_url': f"{current_app.config.get('FRONTEND_URL', 'https://mingusapp.com')}/success?session_id={{CHECKOUT_SESSION_ID}}",
            'cancel_url': f"{current_app.config.get('FRONTEND_URL', 'https://mingusapp.com')}/cancel",
            'metadata': {
                'conversion_id': str(conversion.id),
                'assessment_id': str(assessment.id),
                'conversion_type': conversion.conversion_type
            }
        }
        
        session = stripe.checkout.Session.create(**session_data)
        
        logger.info(f"Stripe checkout session created: {session.id}")
        return session.id
        
    except Exception as e:
        logger.error(f"Error creating Stripe checkout session: {e}")
        return None

def get_product_name(conversion_type: str) -> str:
    """Get product name for Stripe checkout"""
    product_names = {
        'paid_upgrade': 'MINGUS Premium Subscription',
        'consultation_booking': 'AI Career Consultation',
        'course_enrollment': 'AI Career Mastery Course'
    }
    return product_names.get(conversion_type, 'MINGUS Service')

def get_product_description(conversion_type: str) -> str:
    """Get product description for Stripe checkout"""
    descriptions = {
        'paid_upgrade': 'Premium access to MINGUS financial wellness platform',
        'consultation_booking': '1-hour consultation with AI career expert',
        'course_enrollment': 'Comprehensive course on AI career adaptation'
    }
    return descriptions.get(conversion_type, 'MINGUS service')

def track_conversion(assessment_id: str, conversion_type: str, value: float) -> None:
    """Track conversion for analytics (non-critical)"""
    try:
        db = current_app.db_session
        
        conversion = AICalculatorConversion(
            assessment_id=assessment_id,
            conversion_type=conversion_type,
            conversion_value=value
        )
        
        db.add(conversion)
        db.commit()
        
        logger.info(f"Conversion tracked: {conversion_type} for assessment {assessment_id}")
        
    except Exception as e:
        logger.error(f"Error tracking conversion: {str(e)}")
        # Don't raise exception as this is not critical
