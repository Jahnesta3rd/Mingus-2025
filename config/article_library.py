"""
Article Library Configuration for MINGUS Application
Dedicated configuration class for article library feature integration
"""

import os
from typing import Dict, Any, Optional
from config.base import Config


class ArticleLibraryConfig(Config):
    """Configuration class for article library feature"""
    
    def __init__(self):
        """Initialize article library configuration"""
        super().__init__()
        self._load_article_library_config()
    
    def _load_article_library_config(self):
        """Load article library specific configuration"""
        
        # OpenAI API Configuration
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '500'))
        self.OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.1'))
        
        # Email Processing Configuration
        self.MAC_EMAIL_ADDRESS = os.getenv('MAC_EMAIL_ADDRESS')
        self.MAC_EMAIL_APP_PASSWORD = os.getenv('MAC_EMAIL_APP_PASSWORD')
        self.EMAIL_PROCESSING_RATE_LIMIT = int(os.getenv('EMAIL_PROCESSING_RATE_LIMIT', '2'))
        self.EMAIL_BATCH_SIZE = int(os.getenv('EMAIL_BATCH_SIZE', '50'))
        
        # Article Processing Configuration
        self.ARTICLE_SCRAPING_DELAY = int(os.getenv('ARTICLE_SCRAPING_DELAY', '2'))
        self.ARTICLE_CONTENT_MAX_SIZE = int(os.getenv('ARTICLE_CONTENT_MAX_SIZE', '50000'))
        self.ARTICLE_QUALITY_THRESHOLD = float(os.getenv('ARTICLE_QUALITY_THRESHOLD', '0.7'))
        self.CULTURAL_RELEVANCE_THRESHOLD = float(os.getenv('CULTURAL_RELEVANCE_THRESHOLD', '6.0'))
        
        # Search Configuration
        self.SEARCH_RESULTS_PER_PAGE = int(os.getenv('SEARCH_RESULTS_PER_PAGE', '20'))
        self.SEARCH_CACHE_TIMEOUT = int(os.getenv('SEARCH_CACHE_TIMEOUT', '3600'))
        self.ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
        
        # Assessment Configuration
        self.ASSESSMENT_CACHE_DURATION = int(os.getenv('ASSESSMENT_CACHE_DURATION', '7200'))
        self.BE_INTERMEDIATE_THRESHOLD = int(os.getenv('BE_INTERMEDIATE_THRESHOLD', '60'))
        self.DO_INTERMEDIATE_THRESHOLD = int(os.getenv('DO_INTERMEDIATE_THRESHOLD', '60'))
        self.HAVE_INTERMEDIATE_THRESHOLD = int(os.getenv('HAVE_INTERMEDIATE_THRESHOLD', '60'))
        self.BE_ADVANCED_THRESHOLD = int(os.getenv('BE_ADVANCED_THRESHOLD', '80'))
        self.DO_ADVANCED_THRESHOLD = int(os.getenv('DO_ADVANCED_THRESHOLD', '80'))
        self.HAVE_ADVANCED_THRESHOLD = int(os.getenv('HAVE_ADVANCED_THRESHOLD', '80'))
        
        # Background Tasks Configuration
        self.CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        self.CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
        self.CELERY_TASK_ROUTES = eval(os.getenv('CELERY_TASK_ROUTES', '{}'))
        
        # Monitoring and Analytics
        self.ENABLE_ARTICLE_ANALYTICS = os.getenv('ENABLE_ARTICLE_ANALYTICS', 'true').lower() == 'true'
        self.ANALYTICS_RETENTION_DAYS = int(os.getenv('ANALYTICS_RETENTION_DAYS', '90'))
        self.SENTRY_DSN = os.getenv('SENTRY_DSN')
        
        # Performance Configuration
        self.CACHE_TYPE = os.getenv('CACHE_TYPE', 'redis')
        self.CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))
        self.CACHE_KEY_PREFIX = os.getenv('CACHE_KEY_PREFIX', 'mingus_articles')
        
        # Security Configuration
        self.RATE_LIMIT_STORAGE_URL = os.getenv('RATE_LIMIT_STORAGE_URL', 'redis://localhost:6379/1')
        self.DEFAULT_RATE_LIMIT = os.getenv('DEFAULT_RATE_LIMIT', '100/hour')
        self.SEARCH_RATE_LIMIT = os.getenv('SEARCH_RATE_LIMIT', '30/minute')
        self.API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '1000/hour')
        
        # Feature Flags
        self.ENABLE_AI_RECOMMENDATIONS = os.getenv('ENABLE_AI_RECOMMENDATIONS', 'true').lower() == 'true'
        self.ENABLE_CULTURAL_PERSONALIZATION = os.getenv('ENABLE_CULTURAL_PERSONALIZATION', 'true').lower() == 'true'
        self.ENABLE_ADVANCED_SEARCH = os.getenv('ENABLE_ADVANCED_SEARCH', 'true').lower() == 'true'
        self.ENABLE_SOCIAL_SHARING = os.getenv('ENABLE_SOCIAL_SHARING', 'true').lower() == 'true'
        self.ENABLE_OFFLINE_READING = os.getenv('ENABLE_OFFLINE_READING', 'false').lower() == 'true'
        
        # Article Library Database Tables
        self.ARTICLE_TABLES = [
            'articles',
            'user_article_reads',
            'user_article_bookmarks',
            'user_article_ratings',
            'user_article_progress',
            'user_assessment_scores',
            'article_recommendations',
            'article_analytics'
        ]
        
        # Article Library API Endpoints
        self.ARTICLE_API_ENDPOINTS = [
            '/api/articles',
            '/api/articles/search',
            '/api/articles/recommendations',
            '/api/articles/trending',
            '/api/articles/recent',
            '/api/articles/featured',
            '/api/articles/popular',
            '/api/articles/topics',
            '/api/articles/filters'
        ]
    
    def validate_article_library_config(self) -> Dict[str, Any]:
        """Validate article library configuration"""
        errors = []
        warnings = []
        
        # Validate OpenAI Configuration
        if not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required for article classification")
        
        # Validate Email Configuration
        if not self.MAC_EMAIL_ADDRESS:
            warnings.append("MAC_EMAIL_ADDRESS not set - email processing disabled")
        if not self.MAC_EMAIL_APP_PASSWORD:
            warnings.append("MAC_EMAIL_APP_PASSWORD not set - email processing disabled")
        
        # Validate Redis Configuration
        if not self.CELERY_BROKER_URL:
            errors.append("CELERY_BROKER_URL is required for background tasks")
        
        # Validate Thresholds
        if not (0 <= self.ARTICLE_QUALITY_THRESHOLD <= 1):
            errors.append("ARTICLE_QUALITY_THRESHOLD must be between 0 and 1")
        
        if not (0 <= self.CULTURAL_RELEVANCE_THRESHOLD <= 10):
            errors.append("CULTURAL_RELEVANCE_THRESHOLD must be between 0 and 10")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'valid': len(errors) == 0
        }
    
    def get_article_library_settings(self) -> Dict[str, Any]:
        """Get all article library settings as dictionary"""
        return {
            'openai': {
                'api_key': self.OPENAI_API_KEY,
                'model': self.OPENAI_MODEL,
                'max_tokens': self.OPENAI_MAX_TOKENS,
                'temperature': self.OPENAI_TEMPERATURE
            },
            'email_processing': {
                'mac_email_address': self.MAC_EMAIL_ADDRESS,
                'rate_limit': self.EMAIL_PROCESSING_RATE_LIMIT,
                'batch_size': self.EMAIL_BATCH_SIZE
            },
            'article_processing': {
                'scraping_delay': self.ARTICLE_SCRAPING_DELAY,
                'content_max_size': self.ARTICLE_CONTENT_MAX_SIZE,
                'quality_threshold': self.ARTICLE_QUALITY_THRESHOLD,
                'cultural_relevance_threshold': self.CULTURAL_RELEVANCE_THRESHOLD
            },
            'search': {
                'results_per_page': self.SEARCH_RESULTS_PER_PAGE,
                'cache_timeout': self.SEARCH_CACHE_TIMEOUT,
                'elasticsearch_url': self.ELASTICSEARCH_URL
            },
            'assessment': {
                'cache_duration': self.ASSESSMENT_CACHE_DURATION,
                'be_intermediate_threshold': self.BE_INTERMEDIATE_THRESHOLD,
                'do_intermediate_threshold': self.DO_INTERMEDIATE_THRESHOLD,
                'have_intermediate_threshold': self.HAVE_INTERMEDIATE_THRESHOLD,
                'be_advanced_threshold': self.BE_ADVANCED_THRESHOLD,
                'do_advanced_threshold': self.DO_ADVANCED_THRESHOLD,
                'have_advanced_threshold': self.HAVE_ADVANCED_THRESHOLD
            },
            'celery': {
                'broker_url': self.CELERY_BROKER_URL,
                'result_backend': self.CELERY_RESULT_BACKEND,
                'task_routes': self.CELERY_TASK_ROUTES
            },
            'analytics': {
                'enabled': self.ENABLE_ARTICLE_ANALYTICS,
                'retention_days': self.ANALYTICS_RETENTION_DAYS,
                'sentry_dsn': self.SENTRY_DSN
            },
            'cache': {
                'type': self.CACHE_TYPE,
                'default_timeout': self.CACHE_DEFAULT_TIMEOUT,
                'key_prefix': self.CACHE_KEY_PREFIX
            },
            'security': {
                'rate_limit_storage_url': self.RATE_LIMIT_STORAGE_URL,
                'default_rate_limit': self.DEFAULT_RATE_LIMIT,
                'search_rate_limit': self.SEARCH_RATE_LIMIT,
                'api_rate_limit': self.API_RATE_LIMIT
            },
            'features': {
                'ai_recommendations': self.ENABLE_AI_RECOMMENDATIONS,
                'cultural_personalization': self.ENABLE_CULTURAL_PERSONALIZATION,
                'advanced_search': self.ENABLE_ADVANCED_SEARCH,
                'social_sharing': self.ENABLE_SOCIAL_SHARING,
                'offline_reading': self.ENABLE_OFFLINE_READING
            }
        }
