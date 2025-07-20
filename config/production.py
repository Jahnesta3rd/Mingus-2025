"""
Production Configuration for Ultra-Budget Deployment
Optimized settings for performance, scalability, and cost-effectiveness
"""

import os
from datetime import timedelta

class ProductionConfig:
    """Production configuration for income comparison feature"""
    
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Database Configuration (if needed for user demographics)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mingus_production.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # Performance Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=30)  # Static file caching
    
    # Caching Configuration
    CACHE_TYPE = 'simple'  # Use simple in-memory cache for ultra-budget
    CACHE_DEFAULT_TIMEOUT = 1800  # 30 minutes default TTL
    CACHE_KEY_PREFIX = 'mingus_'
    
    # Redis Configuration (optional, for advanced caching)
    REDIS_URL = os.environ.get('REDIS_URL')
    REDIS_CACHE_TIMEOUT = 3600  # 1 hour
    
    # Rate Limiting Configuration
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'  # Use memory storage for ultra-budget
    RATELIMIT_DEFAULT = '20 per minute'
    RATELIMIT_HEADERS_ENABLED = True
    
    # Income Comparison Feature Configuration
    INCOME_COMPARISON = {
        # Performance targets
        'max_analysis_time_ms': 500,
        'max_total_response_time_ms': 3000,
        'max_memory_usage_mb': 100,
        
        # Caching settings
        'response_cache_size': 500,
        'response_cache_ttl_seconds': 1800,  # 30 minutes
        'percentile_cache_size': 1000,
        'location_cache_size': 100,
        
        # Rate limiting
        'max_requests_per_minute': 20,
        'max_requests_per_hour': 100,
        'max_requests_per_day': 1000,
        
        # Data validation
        'max_salary_value': 1000000,
        'min_salary_value': 10000,
        'allowed_age_ranges': ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
        'allowed_education_levels': ['high_school', 'some_college', 'bachelors', 'masters', 'doctorate'],
        'allowed_locations': [
            'atlanta', 'chicago', 'dallas', 'houston', 'los_angeles', 
            'miami', 'new_york', 'philadelphia', 'washington_dc'
        ],
        
        # Monitoring
        'enable_performance_monitoring': True,
        'enable_error_tracking': True,
        'enable_usage_analytics': True,
        
        # Security
        'enable_input_validation': True,
        'enable_rate_limiting': True,
        'enable_csrf_protection': True,
        'enable_https_redirect': True,
        
        # Privacy
        'data_retention_days': 30,
        'anonymize_user_data': True,
        'encrypt_stored_data': False,  # Ultra-budget: no encryption overhead
    }
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/mingus_production.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Monitoring Configuration
    MONITORING = {
        'enable_health_checks': True,
        'health_check_interval_seconds': 300,  # 5 minutes
        'enable_performance_metrics': True,
        'enable_error_tracking': True,
        'enable_usage_analytics': True,
        'metrics_retention_days': 7,
    }
    
    # Security Configuration
    SECURITY = {
        'enable_https': True,
        'enable_cors': True,
        'cors_origins': ['https://yourdomain.com', 'https://www.yourdomain.com'],
        'enable_csrf': True,
        'session_cookie_secure': True,
        'session_cookie_httponly': True,
        'session_cookie_samesite': 'Lax',
        'max_session_age_hours': 24,
    }
    
    # Static File Configuration
    STATIC_FOLDER = 'static'
    STATIC_URL_PATH = '/static'
    STATIC_CACHE_TIMEOUT = 31536000  # 1 year for static assets
    
    # Template Configuration
    TEMPLATE_FOLDER = 'templates'
    TEMPLATE_CACHE_SIZE = 100
    
    # Error Handling
    ERROR_HANDLING = {
        'enable_error_pages': True,
        'log_errors': True,
        'email_errors': False,  # Ultra-budget: no email service
        'error_reporting_url': None,
    }
    
    # API Configuration
    API = {
        'enable_rate_limiting': True,
        'enable_request_logging': True,
        'enable_response_caching': True,
        'max_request_size': 1024 * 1024,  # 1MB
        'timeout_seconds': 30,
    }
    
    # Deployment Configuration
    DEPLOYMENT = {
        'environment': 'production',
        'host': '0.0.0.0',
        'port': int(os.environ.get('PORT', 5000)),
        'workers': int(os.environ.get('WORKERS', 1)),  # Ultra-budget: single worker
        'threads': int(os.environ.get('THREADS', 4)),
        'max_requests': 1000,
        'max_requests_jitter': 100,
        'preload_app': True,
        'worker_class': 'sync',  # Ultra-budget: sync workers
    }
    
    # Cost Optimization
    COST_OPTIMIZATION = {
        'use_free_tier_services': True,
        'minimize_api_calls': True,
        'use_in_memory_caching': True,
        'disable_expensive_features': True,
        'optimize_database_queries': True,
        'use_compression': True,
        'minimize_external_dependencies': True,
    }
    
    # Feature Flags
    FEATURE_FLAGS = {
        'income_comparison_enabled': True,
        'advanced_analytics_enabled': False,  # Ultra-budget: disable expensive features
        'user_profiles_enabled': False,
        'job_recommendations_enabled': True,
        'email_notifications_enabled': False,
        'social_sharing_enabled': False,
        'export_functionality_enabled': False,
    }
    
    # External Services (minimal for ultra-budget)
    EXTERNAL_SERVICES = {
        'census_api_enabled': False,  # Use fallback data
        'email_service_enabled': False,
        'analytics_service_enabled': False,
        'monitoring_service_enabled': False,
        'cdn_enabled': False,  # Serve static files directly
    }
    
    # Memory Management
    MEMORY_MANAGEMENT = {
        'max_cache_size_mb': 50,
        'cache_cleanup_interval_seconds': 3600,  # 1 hour
        'max_concurrent_analyses': 10,
        'memory_monitoring_enabled': True,
        'auto_cleanup_enabled': True,
    }
    
    # Performance Monitoring
    PERFORMANCE_MONITORING = {
        'enable_request_timing': True,
        'enable_memory_monitoring': True,
        'enable_cache_monitoring': True,
        'enable_error_monitoring': True,
        'metrics_export_interval_seconds': 300,  # 5 minutes
        'performance_thresholds': {
            'max_response_time_ms': 3000,
            'max_memory_usage_mb': 100,
            'max_cpu_usage_percent': 80,
        }
    }
    
    # Backup and Recovery
    BACKUP = {
        'enable_automatic_backups': False,  # Ultra-budget: manual backups
        'backup_interval_hours': 24,
        'backup_retention_days': 7,
        'backup_location': 'backups/',
    }
    
    # Development vs Production
    @classmethod
    def init_app(cls, app):
        """Initialize application with production settings"""
        
        # Set production-specific configurations
        app.config['PROPAGATE_EXCEPTIONS'] = True
        
        # Configure logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            # File handler
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            file_handler = RotatingFileHandler(
                cls.LOG_FILE,
                maxBytes=cls.LOG_MAX_SIZE,
                backupCount=cls.LOG_BACKUP_COUNT
            )
            file_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
            file_handler.setLevel(getattr(logging, cls.LOG_LEVEL))
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(getattr(logging, cls.LOG_LEVEL))
            app.logger.info('Mingus startup in production mode')
        
        # Configure CORS
        if cls.SECURITY['enable_cors']:
            from flask_cors import CORS
            CORS(app, origins=cls.SECURITY['cors_origins'])
        
        # Configure rate limiting
        if cls.API['enable_rate_limiting']:
            from flask_limiter import Limiter
            from flask_limiter.util import get_remote_address
            
            limiter = Limiter(
                app,
                key_func=get_remote_address,
                default_limits=[cls.RATELIMIT_DEFAULT],
                storage_uri=cls.RATELIMIT_STORAGE_URL
            )
        
        # Configure caching
        if cls.CACHE_TYPE == 'simple':
            from flask_caching import Cache
            cache = Cache(app)
        
        # Configure session
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=cls.SECURITY['max_session_age_hours'])
        app.config['SESSION_COOKIE_SECURE'] = cls.SECURITY['session_cookie_secure']
        app.config['SESSION_COOKIE_HTTPONLY'] = cls.SECURITY['session_cookie_httponly']
        app.config['SESSION_COOKIE_SAMESITE'] = cls.SECURITY['session_cookie_samesite']
        
        # Configure static files
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=cls.STATIC_CACHE_TIMEOUT)
        
        # Register error handlers
        if cls.ERROR_HANDLING['enable_error_pages']:
            @app.errorhandler(404)
            def not_found_error(error):
                return render_template('errors/404.html'), 404
            
            @app.errorhandler(500)
            def internal_error(error):
                return render_template('errors/500.html'), 500
        
        # Configure performance monitoring
        if cls.PERFORMANCE_MONITORING['enable_request_timing']:
            @app.before_request
            def before_request():
                g.start_time = time.time()
            
            @app.after_request
            def after_request(response):
                if hasattr(g, 'start_time'):
                    duration = time.time() - g.start_time
                    app.logger.info(f'Request completed in {duration:.3f}s')
                return response
        
        # Configure memory monitoring
        if cls.MEMORY_MANAGEMENT['memory_monitoring_enabled']:
            import psutil
            import threading
            
            def memory_monitor():
                while True:
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    if memory_mb > cls.MEMORY_MANAGEMENT['max_cache_size_mb']:
                        app.logger.warning(f'High memory usage: {memory_mb:.1f}MB')
                        # Trigger cache cleanup
                        if hasattr(app, 'cache'):
                            app.cache.clear()
                    time.sleep(300)  # Check every 5 minutes
            
            memory_thread = threading.Thread(target=memory_monitor, daemon=True)
            memory_thread.start()
        
        app.logger.info('Production configuration initialized successfully')

# Environment-specific overrides
class HerokuConfig(ProductionConfig):
    """Heroku-specific configuration"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    REDIS_URL = os.environ.get('REDIS_URL')
    DEPLOYMENT = {
        **ProductionConfig.DEPLOYMENT,
        'host': '0.0.0.0',
        'port': int(os.environ.get('PORT', 5000)),
    }

class RailwayConfig(ProductionConfig):
    """Railway-specific configuration"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    REDIS_URL = os.environ.get('REDIS_URL')
    DEPLOYMENT = {
        **ProductionConfig.DEPLOYMENT,
        'host': '0.0.0.0',
        'port': int(os.environ.get('PORT', 5000)),
    }

class RenderConfig(ProductionConfig):
    """Render-specific configuration"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    REDIS_URL = os.environ.get('REDIS_URL')
    DEPLOYMENT = {
        **ProductionConfig.DEPLOYMENT,
        'host': '0.0.0.0',
        'port': int(os.environ.get('PORT', 5000)),
    }

class VercelConfig(ProductionConfig):
    """Vercel-specific configuration"""
    DEPLOYMENT = {
        **ProductionConfig.DEPLOYMENT,
        'workers': 1,
        'threads': 1,
    }

# Configuration mapping
config_map = {
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'railway': RailwayConfig,
    'render': RenderConfig,
    'vercel': VercelConfig,
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'production')
    return config_map.get(env, ProductionConfig) 