"""
AI Job Impact Assessment API Routes
Handles AI job impact calculator submissions and email delivery
"""

import logging
import re
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest

from backend.services.resend_email_service import ResendEmailService
from backend.utils.validation import validate_email_format
from backend.utils.rate_limiting import limiter
from backend.utils.response_helpers import create_response
from backend.services.email_automation_service import EmailAutomationService
from backend.services.behavioral_triggers import BehavioralTriggersService

logger = logging.getLogger(__name__)

ai_job_assessment_bp = Blueprint('ai_job_assessment', __name__, url_prefix='/api')

# Initialize email service
resend_email_service = ResendEmailService()

# Initialize email automation services
email_automation_service = EmailAutomationService()
behavioral_triggers_service = BehavioralTriggersService()

@ai_job_assessment_bp.route('/ai-job-assessment', methods=['POST'])
@limiter.limit('5 per minute')
def submit_ai_job_assessment():
    """
    Submit AI job impact assessment with email automation trigger
    
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
        "automation_score": integer,
        "augmentation_score": integer,
        "overall_risk_level": "string",
        "assessment_type": "string"
    }
    
    Response:
    {
        "success": true,
        "message": "Assessment submitted successfully",
        "assessment_id": "uuid",
        "email_automation_triggered": true
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
            'tech_skills_level', 'concerns_array', 'first_name', 'email',
            'automation_score', 'augmentation_score', 'overall_risk_level'
        ]
        
        for field in required_fields:
            if field not in data or data[field] is None:
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
        
        # Validate scores
        automation_score = int(data['automation_score'])
        augmentation_score = int(data['augmentation_score'])
        
        if not (0 <= automation_score <= 100) or not (0 <= augmentation_score <= 100):
            return create_response(
                success=False,
                error='invalid_scores',
                message='Scores must be between 0 and 100'
            ), 400
        
        # Validate risk level
        valid_risk_levels = ['low', 'medium', 'high']
        if data['overall_risk_level'] not in valid_risk_levels:
            return create_response(
                success=False,
                error='invalid_risk_level',
                message='Invalid risk level'
            ), 400
        
        # Store assessment in database
        assessment_id = store_assessment(data)
        
        # Generate personalized recommendations
        recommendations = generate_ai_job_recommendations(data)
        
        # Send email with results
        email_sent = send_ai_job_results_email(
            email=email,
            first_name=data['first_name'],
            job_title=data['job_title'],
            automation_score=automation_score,
            augmentation_score=augmentation_score,
            risk_level=data['overall_risk_level'],
            recommendations=recommendations,
            assessment_data=data
        )
        
        # Track conversion if user signs up
        track_conversion(assessment_id, 'email_signup', 25.00)
        
        # Trigger email automation welcome series
        email_automation_triggered = False
        try:
            email_automation_triggered = email_automation_service.trigger_welcome_series(assessment_id)
            logger.info(f"Email automation triggered for assessment {assessment_id}: {email_automation_triggered}")
        except Exception as e:
            logger.error(f"Error triggering email automation: {e}")
        
        # Send immediate results email
        immediate_email_sent = send_ai_job_results_email(
            email=email,
            first_name=data['first_name'],
            job_title=data['job_title'],
            automation_score=automation_score,
            augmentation_score=augmentation_score,
            risk_level=data['overall_risk_level'],
            recommendations=recommendations,
            assessment_data=data
        )
        
        response_data = {
            'success': True,
            'message': 'AI job impact assessment submitted successfully',
            'assessment_id': assessment_id,
            'email_automation_triggered': email_automation_triggered,
            'immediate_email_sent': immediate_email_sent,
            'risk_level': data['overall_risk_level'],
            'automation_score': automation_score,
            'augmentation_score': augmentation_score
        }
        
        if not email_sent:
            response_data['email_message'] = 'Email service temporarily unavailable. Your results have been saved.'
        
        logger.info(f"AI job assessment submitted successfully for {email}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error submitting AI job assessment: {str(e)}")
        return create_response(
            success=False,
            error='submission_failed',
            message='Failed to submit assessment'
        ), 500

def store_assessment(data: Dict[str, Any]) -> str:
    """
    Store AI job assessment in database
    
    Args:
        data: Assessment data
        
    Returns:
        Assessment ID
    """
    try:
        # Get database session
        db = current_app.db_session
        
        # Create assessment record
        assessment_data = {
            'id': str(uuid.uuid4()),
            'job_title': data['job_title'],
            'industry': data['industry'],
            'experience_level': data['experience_level'],
            'tasks_array': json.dumps(data['tasks_array']),
            'remote_work_frequency': data['remote_work_frequency'],
            'ai_usage_frequency': data['ai_usage_frequency'],
            'team_size': data['team_size'],
            'tech_skills_level': data['tech_skills_level'],
            'concerns_array': json.dumps(data['concerns_array']),
            'first_name': data['first_name'],
            'email': data['email'],
            'location': data.get('location', ''),
            'automation_score': data['automation_score'],
            'augmentation_score': data['augmentation_score'],
            'overall_risk_level': data['overall_risk_level'],
            'assessment_type': data.get('assessment_type', 'ai_job_risk'),
            'completed_at': datetime.now(timezone.utc),
            'created_at': datetime.now(timezone.utc),
            
            # Lead generation fields
            'lead_source': 'ai_job_calculator',
            'utm_source': data.get('utm_source'),
            'utm_medium': data.get('utm_medium'),
            'utm_campaign': data.get('utm_campaign'),
            'utm_term': data.get('utm_term'),
            'utm_content': data.get('utm_content'),
            
            # Assessment metadata
            'questions_answered': 15,  # Total questions in the assessment
            'total_questions': 15,
            'completion_percentage': 100.0,
            
            # Risk analysis details
            'risk_factors': json.dumps(analyze_risk_factors(data)),
            'mitigation_strategies': json.dumps(generate_mitigation_strategies(data)),
            'recommended_skills': json.dumps(generate_recommended_skills(data)),
            'career_advice': json.dumps(generate_career_advice(data))
        }
        
        # Insert into database using raw SQL
        insert_query = """
        INSERT INTO ai_job_assessments (
            id, job_title, industry, experience_level, tasks_array,
            remote_work_frequency, ai_usage_frequency, team_size, tech_skills_level,
            concerns_array, first_name, email, location, automation_score,
            augmentation_score, overall_risk_level, assessment_type, completed_at,
            created_at, lead_source, utm_source, utm_medium, utm_campaign,
            utm_term, utm_content, questions_answered, total_questions,
            completion_percentage, risk_factors, mitigation_strategies,
            recommended_skills, career_advice
        ) VALUES (
            %(id)s, %(job_title)s, %(industry)s, %(experience_level)s, %(tasks_array)s,
            %(remote_work_frequency)s, %(ai_usage_frequency)s, %(team_size)s, %(tech_skills_level)s,
            %(concerns_array)s, %(first_name)s, %(email)s, %(location)s, %(automation_score)s,
            %(augmentation_score)s, %(overall_risk_level)s, %(assessment_type)s, %(completed_at)s,
            %(created_at)s, %(lead_source)s, %(utm_source)s, %(utm_medium)s, %(utm_campaign)s,
            %(utm_term)s, %(utm_content)s, %(questions_answered)s, %(total_questions)s,
            %(completion_percentage)s, %(risk_factors)s, %(mitigation_strategies)s,
            %(recommended_skills)s, %(career_advice)s
        )
        """
        
        db.execute(insert_query, assessment_data)
        db.commit()
        
        logger.info(f"AI job assessment stored in database: {assessment_data['id']}")
        return assessment_data['id']
        
    except SQLAlchemyError as e:
        logger.error(f"Database error storing AI job assessment: {str(e)}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error storing AI job assessment: {str(e)}")
        raise

def generate_ai_job_recommendations(data: Dict[str, Any]) -> List[str]:
    """
    Generate personalized recommendations based on assessment data
    
    Args:
        data: Assessment data
        
    Returns:
        List of recommendations
    """
    recommendations = []
    risk_level = data['overall_risk_level']
    automation_score = data['automation_score']
    augmentation_score = data['augmentation_score']
    industry = data['industry']
    job_title = data['job_title'].lower()
    
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
    if industry == 'technology':
        recommendations.append("Focus on emerging technologies like machine learning and data science")
    elif industry == 'finance':
        recommendations.append("Develop expertise in fintech and algorithmic trading")
    elif industry == 'healthcare':
        recommendations.append("Learn about AI applications in medical diagnosis and patient care")
    elif industry == 'marketing':
        recommendations.append("Master AI-powered marketing tools and analytics platforms")
    
    # Job-specific recommendations
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

def analyze_risk_factors(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze risk factors for the job
    
    Args:
        data: Assessment data
        
    Returns:
        Risk factors analysis
    """
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

def generate_mitigation_strategies(data: Dict[str, Any]) -> List[str]:
    """
    Generate mitigation strategies based on risk factors
    
    Args:
        data: Assessment data
        
    Returns:
        List of mitigation strategies
    """
    strategies = []
    risk_level = data['overall_risk_level']
    
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
    """
    Generate recommended skills based on assessment
    
    Args:
        data: Assessment data
        
    Returns:
        List of recommended skills
    """
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

def generate_career_advice(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate personalized career advice
    
    Args:
        data: Assessment data
        
    Returns:
        Career advice object
    """
    advice = {
        'short_term': [],
        'medium_term': [],
        'long_term': [],
        'immediate_actions': []
    }
    
    risk_level = data['overall_risk_level']
    
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

def send_ai_job_results_email(
    email: str,
    first_name: str,
    job_title: str,
    automation_score: int,
    augmentation_score: int,
    risk_level: str,
    recommendations: List[str],
    assessment_data: Dict[str, Any]
) -> bool:
    """
    Send AI job impact results email
    
    Args:
        email: Recipient email
        first_name: Recipient first name
        job_title: Job title
        automation_score: Automation risk score
        augmentation_score: AI augmentation potential score
        risk_level: Overall risk level
        recommendations: List of recommendations
        assessment_data: Full assessment data
        
    Returns:
        Success status
    """
    try:
        # Create HTML email content
        html_content = create_ai_job_results_email(
            first_name=first_name,
            job_title=job_title,
            automation_score=automation_score,
            augmentation_score=augmentation_score,
            risk_level=risk_level,
            recommendations=recommendations,
            assessment_data=assessment_data
        )
        
        # Send email via Resend
        result = resend_email_service.send_email(
            to_email=email,
            subject=f"Your AI Job Impact Analysis: {risk_level.title()} Risk Level",
            html_content=html_content
        )
        
        if result['success']:
            logger.info(f"AI job results email sent successfully to: {email}")
            return True
        else:
            logger.warning(f"Failed to send AI job results email to {email}: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.warning(f"Failed to send AI job results email: {e}")
        return False

def create_ai_job_results_email(
    first_name: str,
    job_title: str,
    automation_score: int,
    augmentation_score: int,
    risk_level: str,
    recommendations: List[str],
    assessment_data: Dict[str, Any]
) -> str:
    """
    Create HTML email content for AI job results
    
    Args:
        first_name: Recipient first name
        job_title: Job title
        automation_score: Automation risk score
        augmentation_score: AI augmentation potential score
        risk_level: Overall risk level
        recommendations: List of recommendations
        assessment_data: Full assessment data
        
    Returns:
        HTML email content
    """
    risk_color = {
        'low': '#10b981',
        'medium': '#f59e0b', 
        'high': '#ef4444'
    }.get(risk_level, '#6b7280')
    
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
                <p>Hi {first_name}, here's your personalized assessment for {job_title}</p>
            </div>
            
            <div class="content">
                <h2>Your Risk Level: <span class="risk-badge">{risk_level.upper()}</span></h2>
                
                <div class="score-card">
                    <h3>Automation Risk</h3>
                    <h2 style="color: #ef4444; font-size: 2em;">{automation_score}%</h2>
                    <p>This represents how likely your current tasks could be automated by AI</p>
                </div>
                
                <div class="score-card">
                    <h3>AI Augmentation Potential</h3>
                    <h2 style="color: #10b981; font-size: 2em;">{augmentation_score}%</h2>
                    <p>This shows how much AI could enhance your productivity and capabilities</p>
                </div>
                
                <h3>🎯 Personalized Recommendations</h3>
                {''.join([f'<div class="recommendation"><strong>•</strong> {rec}</div>' for rec in recommendations])}
                
                <div style="text-align: center;">
                    <a href="https://mingusapp.com/dashboard" class="cta-button">Access Your Full Report</a>
                </div>
                
                <h3>📊 Key Insights</h3>
                <ul>
                    <li><strong>Industry:</strong> {assessment_data.get('industry', 'N/A').title()}</li>
                    <li><strong>Experience Level:</strong> {assessment_data.get('experience_level', 'N/A').title()}</li>
                    <li><strong>Team Size:</strong> {assessment_data.get('team_size', 'N/A')}</li>
                    <li><strong>AI Usage:</strong> {assessment_data.get('ai_usage_frequency', 'N/A').title()}</li>
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

def track_conversion(assessment_id: str, conversion_type: str, value: float) -> None:
    """
    Track conversion for analytics
    
    Args:
        assessment_id: Assessment ID
        conversion_type: Type of conversion
        value: Conversion value
    """
    try:
        db = current_app.db_session
        
        conversion_data = {
            'id': str(uuid.uuid4()),
            'assessment_id': assessment_id,
            'conversion_type': conversion_type,
            'conversion_value': value,
            'converted_at': datetime.now(timezone.utc),
            'created_at': datetime.now(timezone.utc)
        }
        
        insert_query = """
        INSERT INTO ai_calculator_conversions (
            id, assessment_id, conversion_type, conversion_value, 
            converted_at, created_at
        ) VALUES (
            %(id)s, %(assessment_id)s, %(conversion_type)s, %(conversion_value)s,
            %(converted_at)s, %(created_at)s
        )
        """
        
        db.execute(insert_query, conversion_data)
        db.commit()
        
        logger.info(f"Conversion tracked: {conversion_type} for assessment {assessment_id}")
        
    except Exception as e:
        logger.error(f"Error tracking conversion: {str(e)}")
        # Don't raise exception as this is not critical

# Import uuid at the top of the file
import uuid
