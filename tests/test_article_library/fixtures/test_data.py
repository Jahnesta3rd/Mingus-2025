"""
Test Data Fixtures for Article Library Testing Suite

This module provides comprehensive test data for all article library tests.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Sample Articles Data
SAMPLE_ARTICLES = [
    {
        'id': str(uuid.uuid4()),
        'url': 'https://nerdwallet.com/article/careers/salary-negotiation',
        'title': 'How to Negotiate Your Salary Like a Pro',
        'content': 'Comprehensive guide to salary negotiation strategies for professionals...',
        'content_preview': 'Learn proven techniques for negotiating higher salaries...',
        'meta_description': 'Master salary negotiation with these expert strategies',
        'author': 'Financial Expert',
        'publish_date': datetime(2024, 3, 15),
        'word_count': 2500,
        'reading_time_minutes': 10,
        'primary_phase': 'DO',
        'difficulty_level': 'Intermediate',
        'confidence_score': 0.92,
        'demographic_relevance': 9,
        'cultural_sensitivity': 8,
        'income_impact_potential': 9,
        'actionability_score': 9,
        'professional_development_value': 9,
        'key_topics': ['salary negotiation', 'career advancement', 'compensation'],
        'learning_objectives': ['Learn negotiation strategies', 'Understand market rates'],
        'prerequisites': ['Basic career knowledge'],
        'cultural_relevance_keywords': ['professional development', 'career growth'],
        'target_income_range': '$40K-$80K',
        'career_stage': 'Mid-career',
        'recommended_reading_order': 25,
        'domain': 'nerdwallet.com',
        'source_quality_score': 0.95,
        'is_active': True,
        'is_featured': True
    },
    {
        'id': str(uuid.uuid4()),
        'url': 'https://blackenterprise.com/wealth-building-strategies',
        'title': 'Building Generational Wealth: A Complete Guide',
        'content': 'Strategies for building and preserving wealth across generations...',
        'content_preview': 'Discover proven strategies for building lasting wealth...',
        'meta_description': 'Complete guide to generational wealth building',
        'author': 'Wealth Advisor',
        'publish_date': datetime(2024, 2, 20),
        'word_count': 3200,
        'reading_time_minutes': 13,
        'primary_phase': 'HAVE',
        'difficulty_level': 'Advanced',
        'confidence_score': 0.88,
        'demographic_relevance': 10,
        'cultural_sensitivity': 10,
        'income_impact_potential': 10,
        'actionability_score': 8,
        'professional_development_value': 9,
        'key_topics': ['generational wealth', 'investment strategies', 'estate planning'],
        'learning_objectives': ['Understand wealth building', 'Learn investment strategies'],
        'prerequisites': ['Basic financial knowledge', 'Investment experience'],
        'cultural_relevance_keywords': ['generational wealth', 'African American finance'],
        'target_income_range': '$80K+',
        'career_stage': 'Advanced career',
        'recommended_reading_order': 75,
        'domain': 'blackenterprise.com',
        'source_quality_score': 0.92,
        'is_active': True,
        'is_featured': True
    },
    {
        'id': str(uuid.uuid4()),
        'url': 'https://investopedia.com/mindset-wealth-building',
        'title': 'The Wealth Mindset: Think Like a Millionaire',
        'content': 'Developing the right mindset for building wealth and financial success...',
        'content_preview': 'Learn how successful people think about money and wealth...',
        'meta_description': 'Develop a wealth-building mindset',
        'author': 'Psychology Expert',
        'publish_date': datetime(2024, 1, 10),
        'word_count': 1800,
        'reading_time_minutes': 7,
        'primary_phase': 'BE',
        'difficulty_level': 'Beginner',
        'confidence_score': 0.85,
        'demographic_relevance': 8,
        'cultural_sensitivity': 7,
        'income_impact_potential': 7,
        'actionability_score': 6,
        'professional_development_value': 8,
        'key_topics': ['wealth mindset', 'financial psychology', 'success habits'],
        'learning_objectives': ['Develop wealth mindset', 'Understand success psychology'],
        'prerequisites': ['Open mind'],
        'cultural_relevance_keywords': ['success mindset', 'financial psychology'],
        'target_income_range': 'All ranges',
        'career_stage': 'All stages',
        'recommended_reading_order': 5,
        'domain': 'investopedia.com',
        'source_quality_score': 0.90,
        'is_active': True,
        'is_featured': False
    },
    {
        'id': str(uuid.uuid4()),
        'url': 'https://forbes.com/investment-strategies-2024',
        'title': 'Best Investment Strategies for 2024',
        'content': 'Top investment strategies and opportunities for the current year...',
        'content_preview': 'Discover the most promising investment opportunities...',
        'meta_description': 'Investment strategies for 2024',
        'author': 'Investment Analyst',
        'publish_date': datetime(2024, 1, 5),
        'word_count': 2800,
        'reading_time_minutes': 11,
        'primary_phase': 'DO',
        'difficulty_level': 'Intermediate',
        'confidence_score': 0.90,
        'demographic_relevance': 8,
        'cultural_sensitivity': 6,
        'income_impact_potential': 9,
        'actionability_score': 8,
        'professional_development_value': 7,
        'key_topics': ['investment strategies', 'market analysis', 'portfolio management'],
        'learning_objectives': ['Learn investment strategies', 'Understand market trends'],
        'prerequisites': ['Basic investment knowledge'],
        'cultural_relevance_keywords': ['investment opportunities', 'financial growth'],
        'target_income_range': '$60K+',
        'career_stage': 'Mid-career',
        'recommended_reading_order': 35,
        'domain': 'forbes.com',
        'source_quality_score': 0.94,
        'is_active': True,
        'is_featured': False
    },
    {
        'id': str(uuid.uuid4()),
        'url': 'https://essence.com/financial-independence-women',
        'title': 'Financial Independence for Black Women',
        'content': 'Empowering Black women to achieve financial independence...',
        'content_preview': 'Strategies for Black women to build financial independence...',
        'meta_description': 'Financial independence guide for Black women',
        'author': 'Financial Empowerment Coach',
        'publish_date': datetime(2024, 2, 28),
        'word_count': 2200,
        'reading_time_minutes': 9,
        'primary_phase': 'HAVE',
        'difficulty_level': 'Intermediate',
        'confidence_score': 0.87,
        'demographic_relevance': 10,
        'cultural_sensitivity': 10,
        'income_impact_potential': 9,
        'actionability_score': 8,
        'professional_development_value': 9,
        'key_topics': ['financial independence', 'women empowerment', 'wealth building'],
        'learning_objectives': ['Achieve financial independence', 'Build wealth'],
        'prerequisites': ['Basic financial knowledge'],
        'cultural_relevance_keywords': ['Black women', 'financial empowerment'],
        'target_income_range': '$40K-$80K',
        'career_stage': 'Mid-career',
        'recommended_reading_order': 45,
        'domain': 'essence.com',
        'source_quality_score': 0.89,
        'is_active': True,
        'is_featured': True
    }
]

# Sample Users Data
SAMPLE_USERS = [
    {
        'id': str(uuid.uuid4()),
        'email': 'test.user1@example.com',
        'full_name': 'Test User One',
        'subscription_tier': 'premium',
        'is_active': True,
        'created_at': datetime.now() - timedelta(days=30)
    },
    {
        'id': str(uuid.uuid4()),
        'email': 'test.user2@example.com',
        'full_name': 'Test User Two',
        'subscription_tier': 'free',
        'is_active': True,
        'created_at': datetime.now() - timedelta(days=15)
    },
    {
        'id': str(uuid.uuid4()),
        'email': 'test.user3@example.com',
        'full_name': 'Test User Three',
        'subscription_tier': 'enterprise',
        'is_active': True,
        'created_at': datetime.now() - timedelta(days=7)
    }
]

# Sample Assessment Scores Data
SAMPLE_ASSESSMENT_SCORES = [
    {
        'id': str(uuid.uuid4()),
        'user_id': SAMPLE_USERS[0]['id'],
        'be_score': 7,
        'do_score': 6,
        'have_score': 5,
        'assessment_date': datetime.now() - timedelta(days=5),
        'confidence_level': 0.85
    },
    {
        'id': str(uuid.uuid4()),
        'user_id': SAMPLE_USERS[1]['id'],
        'be_score': 3,
        'do_score': 2,
        'have_score': 1,
        'assessment_date': datetime.now() - timedelta(days=2),
        'confidence_level': 0.70
    },
    {
        'id': str(uuid.uuid4()),
        'user_id': SAMPLE_USERS[2]['id'],
        'be_score': 9,
        'do_score': 8,
        'have_score': 9,
        'assessment_date': datetime.now() - timedelta(days=1),
        'confidence_level': 0.95
    }
]

# Sample Email Data
SAMPLE_EMAIL_DATA = [
    {
        'subject': 'Weekly Financial Tips',
        'from': 'newsletter@nerdwallet.com',
        'date': '2024-03-15',
        'body': '''
        Check out these great articles:
        https://nerdwallet.com/article/careers/salary-negotiation
        https://blackenterprise.com/wealth-building-strategies
        https://investopedia.com/emergency-fund-guide
        '''
    },
    {
        'subject': 'Investment Opportunities',
        'from': 'alerts@forbes.com',
        'date': '2024-03-14',
        'body': '''
        Latest investment strategies:
        https://forbes.com/investment-strategies-2024
        https://blackenterprise.com/stock-market-guide
        '''
    }
]

# Sample Domain Data
SAMPLE_DOMAIN_DATA = [
    {
        'domain': 'nerdwallet.com',
        'url_count': 15,
        'quality_score': 0.95,
        'is_approved': True,
        'approval_date': datetime.now() - timedelta(days=10)
    },
    {
        'domain': 'blackenterprise.com',
        'url_count': 12,
        'quality_score': 0.92,
        'is_approved': True,
        'approval_date': datetime.now() - timedelta(days=8)
    },
    {
        'domain': 'investopedia.com',
        'url_count': 8,
        'quality_score': 0.90,
        'is_approved': True,
        'approval_date': datetime.now() - timedelta(days=5)
    },
    {
        'domain': 'forbes.com',
        'url_count': 6,
        'quality_score': 0.94,
        'is_approved': True,
        'approval_date': datetime.now() - timedelta(days=3)
    },
    {
        'domain': 'essence.com',
        'url_count': 4,
        'quality_score': 0.89,
        'is_approved': True,
        'approval_date': datetime.now() - timedelta(days=1)
    }
]

# Sample User Article Interactions
SAMPLE_USER_READS = [
    {
        'id': str(uuid.uuid4()),
        'user_id': SAMPLE_USERS[0]['id'],
        'article_id': SAMPLE_ARTICLES[0]['id'],
        'read_date': datetime.now() - timedelta(days=2),
        'read_duration_minutes': 8,
        'completion_percentage': 85
    },
    {
        'id': str(uuid.uuid4()),
        'user_id': SAMPLE_USERS[0]['id'],
        'article_id': SAMPLE_ARTICLES[1]['id'],
        'read_date': datetime.now() - timedelta(days=1),
        'read_duration_minutes': 12,
        'completion_percentage': 95
    }
]

SAMPLE_USER_BOOKMARKS = [
    {
        'id': str(uuid.uuid4()),
        'user_id': SAMPLE_USERS[0]['id'],
        'article_id': SAMPLE_ARTICLES[0]['id'],
        'bookmark_date': datetime.now() - timedelta(days=1),
        'notes': 'Great salary negotiation tips'
    }
]

SAMPLE_USER_RATINGS = [
    {
        'id': str(uuid.uuid4()),
        'user_id': SAMPLE_USERS[0]['id'],
        'article_id': SAMPLE_ARTICLES[0]['id'],
        'rating': 5,
        'rating_date': datetime.now() - timedelta(days=1),
        'feedback': 'Very helpful and actionable'
    }
]

# Sample Search Queries
SAMPLE_SEARCH_QUERIES = [
    'salary negotiation',
    'wealth building',
    'investment strategies',
    'financial independence',
    'career advancement',
    'mindset development',
    'generational wealth',
    'Black women finance'
]

# Sample API Request Data
SAMPLE_API_REQUESTS = {
    'search_articles': {
        'query': 'salary negotiation',
        'filters': {
            'primary_phase': 'DO',
            'difficulty_level': 'Intermediate',
            'demographic_relevance_min': 7
        },
        'page': 1,
        'per_page': 10
    },
    'get_recommendations': {
        'user_id': SAMPLE_USERS[0]['id'],
        'limit': 5,
        'include_read': False
    },
    'rate_article': {
        'article_id': SAMPLE_ARTICLES[0]['id'],
        'rating': 5,
        'feedback': 'Excellent article with practical tips'
    },
    'bookmark_article': {
        'article_id': SAMPLE_ARTICLES[1]['id'],
        'notes': 'Save for later reference'
    }
}

# Sample Error Responses
SAMPLE_ERROR_RESPONSES = {
    'authentication_required': {
        'error': 'Authentication required',
        'message': 'Please log in to access this resource'
    },
    'access_denied': {
        'error': 'Access denied',
        'message': 'Complete assessment to unlock this content'
    },
    'article_not_found': {
        'error': 'Article not found',
        'message': 'The requested article could not be found'
    },
    'invalid_input': {
        'error': 'Invalid input',
        'message': 'Please check your input and try again'
    }
}

# Performance Test Data
PERFORMANCE_TEST_DATA = {
    'large_search_query': 'finance OR money OR wealth OR investment OR career OR salary OR negotiation OR strategy OR planning OR management OR budget OR saving OR spending OR debt OR credit OR loan OR mortgage OR insurance OR retirement OR estate OR tax OR business OR entrepreneurship OR side hustle OR passive income OR real estate OR stocks OR bonds OR mutual funds OR ETFs OR cryptocurrency OR blockchain OR fintech OR digital banking OR mobile payments OR peer to peer lending OR crowdfunding OR angel investing OR venture capital OR private equity OR hedge funds OR commodities OR forex OR options OR futures OR derivatives OR structured products OR annuities OR life insurance OR health insurance OR disability insurance OR long term care insurance OR umbrella insurance OR professional liability insurance OR cyber insurance OR identity theft protection OR credit monitoring OR fraud protection OR financial planning OR retirement planning OR estate planning OR tax planning OR insurance planning OR investment planning OR debt management OR credit repair OR bankruptcy OR foreclosure OR short sale OR deed in lieu OR loan modification OR refinancing OR consolidation OR settlement OR negotiation OR mediation OR arbitration OR litigation OR legal advice OR financial advice OR investment advice OR tax advice OR legal services OR financial services OR investment services OR banking services OR credit services OR insurance services OR real estate services OR business services OR consulting services OR coaching services OR mentoring services OR networking services OR professional development OR continuing education OR certification OR licensing OR accreditation OR compliance OR regulation OR oversight OR governance OR risk management OR internal controls OR audit OR review OR assessment OR evaluation OR monitoring OR reporting OR disclosure OR transparency OR accountability OR responsibility OR ethics OR integrity OR trust OR confidence OR credibility OR reputation OR brand OR marketing OR advertising OR promotion OR publicity OR public relations OR media relations OR investor relations OR customer relations OR employee relations OR vendor relations OR partner relations OR stakeholder relations OR community relations OR government relations OR regulatory relations OR industry relations OR trade relations OR international relations OR diplomatic relations OR political relations OR economic relations OR social relations OR cultural relations OR environmental relations OR sustainability OR corporate social responsibility OR philanthropy OR charitable giving OR volunteering OR community service OR social impact OR social enterprise OR social innovation OR social entrepreneurship OR social finance OR impact investing OR sustainable investing OR responsible investing OR ethical investing OR green investing OR clean energy OR renewable energy OR energy efficiency OR energy conservation OR energy management OR energy policy OR energy regulation OR energy market OR energy trading OR energy finance OR energy investment OR energy technology OR energy innovation OR energy infrastructure OR energy security OR energy independence OR energy diversification OR energy transition OR energy transformation OR energy revolution OR energy evolution OR energy future OR energy outlook OR energy forecast OR energy projection OR energy scenario OR energy planning OR energy strategy OR energy policy OR energy regulation OR energy market OR energy trading OR energy finance OR energy investment OR energy technology OR energy innovation OR energy infrastructure OR energy security OR energy independence OR energy diversification OR energy transition OR energy transformation OR energy revolution OR energy evolution OR energy future OR energy outlook OR energy forecast OR energy projection OR energy scenario OR energy planning OR energy strategy',
    'multiple_filters': {
        'primary_phase': ['BE', 'DO', 'HAVE'],
        'difficulty_level': ['Beginner', 'Intermediate', 'Advanced'],
        'demographic_relevance_min': 5,
        'cultural_sensitivity_min': 6,
        'income_impact_potential_min': 7,
        'actionability_score_min': 6,
        'professional_development_value_min': 7,
        'target_income_range': ['$40K-$60K', '$60K-$80K', '$80K+'],
        'career_stage': ['Early career', 'Mid-career', 'Advanced career'],
        'domain': ['nerdwallet.com', 'blackenterprise.com', 'investopedia.com', 'forbes.com', 'essence.com']
    }
}

# Security Test Data
SECURITY_TEST_DATA = {
    'sql_injection_attempts': [
        "'; DROP TABLE articles; --",
        "' OR 1=1; --",
        "' UNION SELECT * FROM users; --",
        "'; INSERT INTO articles VALUES ('hack'); --"
    ],
    'xss_attempts': [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src=javascript:alert('XSS')></iframe>"
    ],
    'path_traversal_attempts': [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
    ],
    'authentication_bypass_attempts': [
        {"user_id": "admin"},
        {"user_id": "1 OR 1=1"},
        {"user_id": "'; DROP TABLE users; --"},
        {"user_id": "UNION SELECT * FROM users"}
    ]
}
