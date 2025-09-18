"""
Email configuration for Mingus Personal Finance
"""

import os

# Email Settings
EMAIL_CONFIG = {
    'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'SMTP_PORT': int(os.getenv('SMTP_PORT', '587')),
    'SMTP_USERNAME': os.getenv('SMTP_USERNAME', ''),
    'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD', ''),
    'FROM_EMAIL': os.getenv('FROM_EMAIL', 'noreply@mingus.com'),
    'FROM_NAME': os.getenv('FROM_NAME', 'Mingus Personal Finance'),
    'ENABLE_EMAIL': os.getenv('ENABLE_EMAIL', 'true').lower() == 'true'
}

# Email Templates
EMAIL_TEMPLATES = {
    'assessment_results': {
        'subject': '🎯 Your {assessment_title} Results Are Ready!',
        'template': 'assessment_results.html'
    },
    'welcome': {
        'subject': '🎉 Welcome to Mingus - Your Personal Finance Journey Starts Here!',
        'template': 'welcome.html'
    },
    'follow_up': {
        'subject': '💡 Ready to Take Your Next Step?',
        'template': 'follow_up.html'
    }
}

# Assessment-specific content
ASSESSMENT_CONTENT = {
    'ai-risk': {
        'title': 'AI Replacement Risk Assessment',
        'description': 'Determine your job security in the age of artificial intelligence',
        'cta_primary': 'Get AI-Ready Skills Training',
        'cta_secondary': 'Join AI Professionals Network',
        'cta_url_primary': 'https://mingus.com/ai-training',
        'cta_url_secondary': 'https://mingus.com/ai-network'
    },
    'income-comparison': {
        'title': 'Income Comparison Assessment',
        'description': 'See how your salary compares to industry standards',
        'cta_primary': 'Negotiate Your Salary',
        'cta_secondary': 'Career Advancement Plan',
        'cta_url_primary': 'https://mingus.com/salary-negotiation',
        'cta_url_secondary': 'https://mingus.com/career-planning'
    },
    'cuffing-season': {
        'title': 'Cuffing Season Score',
        'description': 'Find out if you\'re ready for meaningful connections',
        'cta_primary': 'Dating Success Workshop',
        'cta_secondary': 'Confidence Building Course',
        'cta_url_primary': 'https://mingus.com/dating-workshop',
        'cta_url_secondary': 'https://mingus.com/confidence-course'
    },
    'layoff-risk': {
        'title': 'Layoff Risk Assessment',
        'description': 'Assess your job security in today\'s market',
        'cta_primary': 'Job Security Action Plan',
        'cta_secondary': 'Skills Development Program',
        'cta_url_primary': 'https://mingus.com/job-security',
        'cta_url_secondary': 'https://mingus.com/skills-development'
    }
}

# Email tracking and analytics
EMAIL_ANALYTICS = {
    'track_opens': True,
    'track_clicks': True,
    'utm_source': 'email',
    'utm_medium': 'assessment_results',
    'utm_campaign': 'results_ready'
}
