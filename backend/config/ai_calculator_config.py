"""
AI Job Impact Calculator Configuration
Configuration settings for the AI Calculator API endpoints
"""

import os
from typing import Dict, Any

# Scoring Configuration
SCORING_CONFIG = {
    'automation_bounds': (5, 80),
    'augmentation_bounds': (10, 85),
    
    # Industry modifiers for scoring
    'industry_modifiers': {
        'technology': {'automation': 10, 'augmentation': 15},
        'healthcare': {'automation': -10, 'augmentation': 5},
        'finance': {'automation': 5, 'augmentation': 10},
        'manufacturing': {'automation': 15, 'augmentation': -5},
        'retail': {'automation': 10, 'augmentation': 0},
        'marketing': {'automation': 0, 'augmentation': 10},
        'education': {'automation': -5, 'augmentation': 5},
        'legal': {'automation': -10, 'augmentation': 0},
        'consulting': {'automation': -5, 'augmentation': 10},
        'other': {'automation': 0, 'augmentation': 0}
    },
    
    # Task-based modifiers
    'task_modifiers': {
        'coding': {'automation': 5, 'augmentation': 10},
        'writing': {'automation': 5, 'augmentation': 8},
        'analysis': {'automation': 5, 'augmentation': 12},
        'data_entry': {'automation': 15, 'augmentation': -5},
        'customer_service': {'automation': 10, 'augmentation': 0},
        'project_management': {'automation': -5, 'augmentation': 8},
        'creative_design': {'automation': -8, 'augmentation': 5},
        'sales': {'automation': 0, 'augmentation': 10},
        'reporting': {'automation': 8, 'augmentation': 3},
        'content_creation': {'automation': 3, 'augmentation': 8}
    },
    
    # Experience level modifiers
    'experience_modifiers': {
        'entry': {'automation': 0, 'augmentation': 0},
        'mid': {'automation': -2, 'augmentation': 5},
        'senior': {'automation': -5, 'augmentation': 10},
        'executive': {'automation': -8, 'augmentation': 15}
    },
    
    # AI usage frequency modifiers
    'ai_usage_modifiers': {
        'never': {'automation': 0, 'augmentation': 0},
        'rarely': {'automation': 0, 'augmentation': 2},
        'sometimes': {'automation': -2, 'augmentation': 5},
        'often': {'automation': -5, 'augmentation': 10},
        'always': {'automation': -10, 'augmentation': 15}
    },
    
    # Technical skills modifiers
    'tech_skills_modifiers': {
        'basic': {'automation': 0, 'augmentation': 0},
        'intermediate': {'automation': -3, 'augmentation': 5},
        'advanced': {'automation': -5, 'augmentation': 8},
        'expert': {'automation': -8, 'augmentation': 12}
    }
}

# Risk Level Thresholds
RISK_THRESHOLDS = {
    'high': 50,      # Total impact score >= 50
    'medium': 30,    # Total impact score 30-49
    'low': 0         # Total impact score < 30
}

# Job Search Configuration
JOB_SEARCH_CONFIG = {
    'min_similarity_threshold': 0.3,
    'max_results': 10,
    'high_similarity_threshold': 0.6
}

# Email Configuration
EMAIL_CONFIG = {
    'welcome_subject_template': 'Your AI Job Impact Analysis: {risk_level} Risk Level',
    'from_name': 'MINGUS AI Career Insights',
    'from_email': 'ai-insights@mingusapp.com',
    'reply_to': 'support@mingusapp.com'
}

# Conversion Configuration
CONVERSION_CONFIG = {
    'valid_types': [
        'email_signup',
        'paid_upgrade', 
        'consultation_booking',
        'course_enrollment'
    ],
    'default_values': {
        'email_signup': 25.00,
        'paid_upgrade': 99.00,
        'consultation_booking': 199.00,
        'course_enrollment': 299.00
    }
}

# Stripe Configuration
STRIPE_CONFIG = {
    'currency': 'usd',
    'payment_methods': ['card'],
    'success_url_template': '{frontend_url}/success?session_id={{CHECKOUT_SESSION_ID}}',
    'cancel_url_template': '{frontend_url}/cancel',
    'products': {
        'paid_upgrade': {
            'name': 'MINGUS Premium Subscription',
            'description': 'Premium access to MINGUS financial wellness platform'
        },
        'consultation_booking': {
            'name': 'AI Career Consultation',
            'description': '1-hour consultation with AI career expert'
        },
        'course_enrollment': {
            'name': 'AI Career Mastery Course',
            'description': 'Comprehensive course on AI career adaptation'
        }
    }
}

# Rate Limiting Configuration
RATE_LIMIT_CONFIG = {
    'assessment_submission': '5 per minute',
    'job_search': '10 per minute',
    'conversion_tracking': '10 per minute'
}

# Validation Configuration
VALIDATION_CONFIG = {
    'required_fields': [
        'job_title', 'industry', 'experience_level', 'tasks_array',
        'remote_work_frequency', 'ai_usage_frequency', 'team_size',
        'tech_skills_level', 'concerns_array', 'first_name', 'email'
    ],
    'valid_experience_levels': ['entry', 'mid', 'senior', 'executive'],
    'valid_remote_frequencies': ['never', 'rarely', 'sometimes', 'often', 'always'],
    'valid_ai_usage_frequencies': ['never', 'rarely', 'sometimes', 'often', 'always'],
    'valid_team_sizes': ['1-5', '6-10', '11-25', '26-50', '50+'],
    'valid_tech_skill_levels': ['basic', 'intermediate', 'advanced', 'expert'],
    'valid_risk_levels': ['low', 'medium', 'high']
}

# Database Configuration
DATABASE_CONFIG = {
    'table_names': {
        'assessments': 'ai_job_assessments',
        'risk_data': 'ai_job_risk_data',
        'conversions': 'ai_calculator_conversions'
    },
    'indexes': [
        'idx_ai_job_assessments_email',
        'idx_ai_job_assessments_risk_level',
        'idx_ai_job_assessments_created_at',
        'idx_ai_job_risk_data_job_keyword',
        'idx_ai_calculator_conversions_assessment_id'
    ]
}

# Analytics Configuration
ANALYTICS_CONFIG = {
    'tracking_events': [
        'assessment_started',
        'assessment_completed',
        'email_signup',
        'paid_conversion',
        'job_search'
    ],
    'conversion_funnel_stages': [
        'awareness',
        'interest',
        'consideration',
        'intent',
        'purchase'
    ]
}

# Security Configuration
SECURITY_CONFIG = {
    'csrf_protection': True,
    'rate_limiting': True,
    'input_validation': True,
    'sql_injection_protection': True,
    'xss_protection': True
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'handlers': ['file', 'console'],
    'log_file': 'logs/ai_calculator.log'
}

def get_config() -> Dict[str, Any]:
    """Get complete configuration dictionary"""
    return {
        'scoring': SCORING_CONFIG,
        'risk_thresholds': RISK_THRESHOLDS,
        'job_search': JOB_SEARCH_CONFIG,
        'email': EMAIL_CONFIG,
        'conversion': CONVERSION_CONFIG,
        'stripe': STRIPE_CONFIG,
        'rate_limit': RATE_LIMIT_CONFIG,
        'validation': VALIDATION_CONFIG,
        'database': DATABASE_CONFIG,
        'analytics': ANALYTICS_CONFIG,
        'security': SECURITY_CONFIG,
        'logging': LOGGING_CONFIG
    }

def get_environment_config() -> Dict[str, Any]:
    """Get configuration from environment variables"""
    return {
        'stripe_secret_key': os.getenv('STRIPE_SECRET_KEY'),
        'stripe_publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY'),
        'resend_api_key': os.getenv('RESEND_API_KEY'),
        'resend_from_email': os.getenv('RESEND_FROM_EMAIL', 'ai-insights@mingusapp.com'),
        'resend_from_name': os.getenv('RESEND_FROM_NAME', 'MINGUS AI Career Insights'),
        'frontend_url': os.getenv('FRONTEND_URL', 'https://mingusapp.com'),
        'database_url': os.getenv('DATABASE_URL'),
        'environment': os.getenv('FLASK_ENV', 'development'),
        'debug': os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    }
