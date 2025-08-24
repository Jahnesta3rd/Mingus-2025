"""
Article Library Integration for MINGUS Flask Application
Integrates article library features with existing Mingus Flask app
"""

from flask import Flask, Blueprint
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from typing import Dict, Any, Optional

from backend.routes.articles import articles_bp
from backend.services.article_search import ArticleSearchService
from backend.services.article_classification import ArticleClassificationService
from backend.services.article_recommendations import ArticleRecommendationService
from config.article_library import ArticleLibraryConfig

logger = logging.getLogger(__name__)


class ArticleLibraryIntegration:
    """Article Library Integration Manager"""
    
    def __init__(self, app: Flask):
        """Initialize article library integration"""
        self.app = app
        self.config = ArticleLibraryConfig()
        self.cache = Cache()
        self.limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=self.config.RATE_LIMIT_STORAGE_URL,
            default_limits=[self.config.DEFAULT_RATE_LIMIT]
        )
        
    def initialize_services(self):
        """Initialize article library services"""
        try:
            # Initialize cache
            self.cache.init_app(self.app, config={
                'CACHE_TYPE': self.config.CACHE_TYPE,
                'CACHE_REDIS_URL': self.config.CELERY_BROKER_URL,
                'CACHE_DEFAULT_TIMEOUT': self.config.CACHE_DEFAULT_TIMEOUT,
                'CACHE_KEY_PREFIX': self.config.CACHE_KEY_PREFIX
            })
            
            # Initialize rate limiter
            self.limiter.init_app(self.app)
            
            # Initialize services
            self._initialize_article_services()
            
            logger.info("Article library services initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing article library services: {str(e)}")
            raise
    
    def _initialize_article_services(self):
        """Initialize article-related services"""
        # Initialize search service
        search_service = ArticleSearchService(
            cache=self.cache,
            config=self.config
        )
        
        # Initialize classification service
        classification_service = ArticleClassificationService(
            openai_api_key=self.config.OPENAI_API_KEY,
            model=self.config.OPENAI_MODEL,
            max_tokens=self.config.OPENAI_MAX_TOKENS,
            temperature=self.config.OPENAI_TEMPERATURE
        )
        
        # Initialize recommendation service
        recommendation_service = ArticleRecommendationService(
            cache=self.cache,
            config=self.config
        )
        
        # Register services with app context
        self.app.article_search_service = search_service
        self.app.article_classification_service = classification_service
        self.app.article_recommendation_service = recommendation_service
    
    def register_blueprints(self):
        """Register article library blueprints"""
        try:
            # Register main articles blueprint
            self.app.register_blueprint(articles_bp)
            
            # Apply rate limiting to article endpoints
            self._apply_rate_limiting()
            
            logger.info("Article library blueprints registered successfully")
            
        except Exception as e:
            logger.error(f"Error registering article library blueprints: {str(e)}")
            raise
    
    def _apply_rate_limiting(self):
        """Apply rate limiting to article endpoints"""
        # Apply specific rate limits to search endpoints
        self.limiter.limit(self.config.SEARCH_RATE_LIMIT)(
            self.app.view_functions.get('articles.search')
        )
        
        # Apply API rate limiting to all article endpoints
        for endpoint in self.config.ARTICLE_API_ENDPOINTS:
            if endpoint in self.app.view_functions:
                self.limiter.limit(self.config.API_RATE_LIMIT)(
                    self.app.view_functions[endpoint]
                )
    
    def configure_database(self):
        """Configure database for article library tables"""
        try:
            # Ensure article tables exist
            from backend.models.articles import Base as ArticleBase
            from backend.models import engine
            
            # Create article tables if they don't exist
            ArticleBase.metadata.create_all(bind=engine)
            
            logger.info("Article library database tables configured")
            
        except Exception as e:
            logger.error(f"Error configuring article library database: {str(e)}")
            raise
    
    def setup_celery_tasks(self):
        """Setup Celery tasks for article processing"""
        try:
            from backend.tasks.article_tasks import setup_article_tasks
            
            # Setup article processing tasks
            setup_article_tasks(self.app)
            
            logger.info("Article library Celery tasks configured")
            
        except Exception as e:
            logger.error(f"Error setting up article library Celery tasks: {str(e)}")
            raise
    
    def validate_integration(self) -> Dict[str, Any]:
        """Validate article library integration"""
        validation_result = self.config.validate_article_library_config()
        
        # Additional integration validations
        if not validation_result['valid']:
            return validation_result
        
        # Check if blueprints are registered
        if 'articles' not in self.app.blueprints:
            validation_result['errors'].append("Articles blueprint not registered")
        
        # Check if services are initialized
        if not hasattr(self.app, 'article_search_service'):
            validation_result['errors'].append("Article search service not initialized")
        
        if not hasattr(self.app, 'article_classification_service'):
            validation_result['errors'].append("Article classification service not initialized")
        
        validation_result['valid'] = len(validation_result['errors']) == 0
        return validation_result
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get article library integration status"""
        return {
            'blueprints_registered': 'articles' in self.app.blueprints,
            'services_initialized': all([
                hasattr(self.app, 'article_search_service'),
                hasattr(self.app, 'article_classification_service'),
                hasattr(self.app, 'article_recommendation_service')
            ]),
            'cache_configured': hasattr(self.app, 'cache'),
            'rate_limiting_configured': hasattr(self.app, 'limiter'),
            'celery_tasks_configured': True,  # Will be checked during setup
            'database_tables_configured': True,  # Will be checked during setup
            'configuration_valid': self.config.validate_article_library_config()['valid']
        }


def integrate_article_library(app: Flask) -> ArticleLibraryIntegration:
    """
    Integrate article library with existing Flask application
    
    Args:
        app: Flask application instance
        
    Returns:
        ArticleLibraryIntegration instance
    """
    integration = ArticleLibraryIntegration(app)
    
    # Initialize services
    integration.initialize_services()
    
    # Register blueprints
    integration.register_blueprints()
    
    # Configure database
    integration.configure_database()
    
    # Setup Celery tasks
    integration.setup_celery_tasks()
    
    # Validate integration
    validation_result = integration.validate_integration()
    if not validation_result['valid']:
        logger.error(f"Article library integration validation failed: {validation_result['errors']}")
        raise ValueError(f"Article library integration validation failed: {validation_result['errors']}")
    
    logger.info("Article library integration completed successfully")
    return integration


def get_article_library_config() -> ArticleLibraryConfig:
    """Get article library configuration"""
    return ArticleLibraryConfig()


def get_article_library_status(app: Flask) -> Dict[str, Any]:
    """Get article library status"""
    if hasattr(app, 'article_library_integration'):
        return app.article_library_integration.get_integration_status()
    else:
        return {
            'blueprints_registered': False,
            'services_initialized': False,
            'cache_configured': False,
            'rate_limiting_configured': False,
            'celery_tasks_configured': False,
            'database_tables_configured': False,
            'configuration_valid': False
        }
