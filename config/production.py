"""
Production Configuration for Ultra-Budget Deployment
Optimized settings for performance, scalability, and cost-effectiveness
"""

import os
from datetime import timedelta
from .base import Config
from .secure_config import get_secure_config

class ProductionConfig(Config):
    """Production configuration using secure configuration management"""
    
    def __init__(self):
        """Initialize production configuration with secure config manager"""
        super().__init__()
        self._load_production_config()
    
    def _load_production_config(self):
        """Load production-specific configuration"""
        # Production-specific overrides
        self.DEBUG = False
        self.TESTING = False
        
        # Database Configuration
        self.DATABASE_URL = self.secure_config.get('DATABASE_URL')
        self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': int(self.secure_config.get('DB_POOL_SIZE', '10')),
            'pool_recycle': int(self.secure_config.get('DB_POOL_RECYCLE', '3600')),
            'pool_pre_ping': True,
            'max_overflow': int(self.secure_config.get('DB_MAX_OVERFLOW', '20'))
        }
        
        # Performance Configuration
        self.MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
        self.SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=30)  # Static file caching
        
        # Caching Configuration
        self.CACHE_TYPE = self.secure_config.get('CACHE_TYPE', 'simple')
        self.CACHE_DEFAULT_TIMEOUT = int(self.secure_config.get('CACHE_DEFAULT_TIMEOUT', '1800'))
        self.CACHE_KEY_PREFIX = self.secure_config.get('CACHE_KEY_PREFIX', 'mingus_')
        
        # Redis Configuration
        self.REDIS_URL = self.secure_config.get('REDIS_URL')
        self.REDIS_CACHE_TIMEOUT = 3600  # 1 hour
        
        # Rate Limiting Configuration
        self.RATELIMIT_ENABLED = self.secure_config.get('RATELIMIT_ENABLED', 'true').lower() == 'true'
        self.RATELIMIT_STORAGE_URL = self.secure_config.get('RATELIMIT_STORAGE_URL', 'memory://')  # Use memory storage for ultra-budget
        self.RATELIMIT_DEFAULT = self.secure_config.get('PROD_RATELIMIT_DEFAULT', '20 per minute')
        self.RATELIMIT_HEADERS_ENABLED = True
        
        # Supabase settings (use secure config manager)
        self.SUPABASE_URL = self.secure_config.get('SUPABASE_URL')
        self.SUPABASE_KEY = self.secure_config.get('SUPABASE_KEY')
        self.SUPABASE_SERVICE_ROLE_KEY = self.secure_config.get('SUPABASE_SERVICE_ROLE_KEY')
        self.SUPABASE_JWT_SECRET = self.secure_config.get('SUPABASE_JWT_SECRET')
        
        # Stripe settings for production
        self.STRIPE_ENVIRONMENT = self.secure_config.get('STRIPE_ENVIRONMENT', 'live')
        self.STRIPE_LIVE_SECRET_KEY = self.secure_config.get('STRIPE_LIVE_SECRET_KEY')
        self.STRIPE_LIVE_PUBLISHABLE_KEY = self.secure_config.get('STRIPE_LIVE_PUBLISHABLE_KEY')
        self.STRIPE_LIVE_WEBHOOK_SECRET = self.secure_config.get('STRIPE_LIVE_WEBHOOK_SECRET')
        
        # Plaid settings for production
        self.PLAID_ENVIRONMENT = self.secure_config.get('PLAID_ENVIRONMENT', 'production')
        self.PLAID_PRODUCTION_CLIENT_ID = self.secure_config.get('PLAID_PRODUCTION_CLIENT_ID')
        self.PLAID_PRODUCTION_SECRET = self.secure_config.get('PLAID_PRODUCTION_SECRET')
        self.PLAID_PRODUCTION_WEBHOOK_SECRET = self.secure_config.get('PLAID_PRODUCTION_WEBHOOK_SECRET')
        
        # Email settings for production
        self.EMAIL_PROVIDER = self.secure_config.get('EMAIL_PROVIDER', 'resend')
        self.RESEND_API_KEY = self.secure_config.get('RESEND_API_KEY')
        self.RESEND_FROM_EMAIL = self.secure_config.get('RESEND_FROM_EMAIL', 'noreply@mingusapp.com')
        self.RESEND_FROM_NAME = self.secure_config.get('RESEND_FROM_NAME', 'MINGUS Financial Wellness')
        
        # SMS settings for production
        self.TWILIO_ACCOUNT_SID = self.secure_config.get('TWILIO_ACCOUNT_SID')
        self.TWILIO_AUTH_TOKEN = self.secure_config.get('TWILIO_AUTH_TOKEN')
        self.TWILIO_PHONE_NUMBER = self.secure_config.get('TWILIO_PHONE_NUMBER')
        
        # Production security settings
        self.SECURE_SSL_REDIRECT = True
        self.SECURE_HSTS_SECONDS = 31536000
        self.SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        self.SECURE_HSTS_PRELOAD = True
        self.SECURE_CONTENT_TYPE_NOSNIFF = True
        self.SECURE_BROWSER_XSS_FILTER = True
        self.SECURE_FRAME_DENY = True
        
        # Content Security Policy (CSP) configuration for production
        self.CSP_DIRECTIVES = {
            'default-src': ["'self'"],
            'style-src': ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com"],
            'script-src': ["'self'", "'unsafe-inline'", "https://www.googletagmanager.com", "https://www.clarity.ms"],
            'font-src': ["'self'", "https://cdnjs.cloudflare.com", "https://fonts.gstatic.com"],
            'img-src': ["'self'", "data:", "https:"],
            'connect-src': ["'self'", "https://www.google-analytics.com", "https://www.clarity.ms"],
            'frame-src': ["'none'"],
            'object-src': ["'none'"],
            'base-uri': ["'self'"],
            'form-action': ["'self'"],
            'upgrade-insecure-requests': []
        }
        
        # Session security for production
        self.SESSION_COOKIE_SECURE = True
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = self.secure_config.get('PROD_SESSION_COOKIE_SAMESITE', 'Strict')
        self.PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
        
        # CORS settings for production
        cors_origins = self.secure_config.get('CORS_ORIGINS', 'https://mingusapp.com,https://www.mingusapp.com')
        self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(',')]
        
        # Logging configuration for production
        self.LOG_LEVEL = self.secure_config.get('PROD_LOG_LEVEL', 'INFO')
        self.LOG_FORMAT = self.secure_config.get('PROD_LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.LOG_FILE = self.secure_config.get('PROD_LOG_FILE', 'logs/mingus_production.log')
        self.LOG_ROTATION = self.secure_config.get('PROD_LOG_ROTATION', '1 day')
        self.LOG_RETENTION = self.secure_config.get('PROD_LOG_RETENTION', '30 days')
        
        # Static files configuration
        self.STATIC_FOLDER = self.secure_config.get('PROD_STATIC_FOLDER', 'static')
        self.STATIC_URL_PATH = self.secure_config.get('PROD_STATIC_URL_PATH', '/static')
        
        # Template configuration
        self.TEMPLATE_FOLDER = self.secure_config.get('PROD_TEMPLATE_FOLDER', 'templates')
        
        # File upload configuration
        self.MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
        self.UPLOAD_FOLDER = self.secure_config.get('PROD_UPLOAD_FOLDER', 'uploads/production')
        
        # API configuration for production
        self.API_TITLE = self.secure_config.get('PROD_API_TITLE', 'Mingus Personal Finance API (Production)')
        self.API_VERSION = self.secure_config.get('PROD_API_VERSION', 'v1')
        self.API_DESCRIPTION = self.secure_config.get('PROD_API_DESCRIPTION', 'Production API for Mingus personal finance application')
        
        # Rate limiting for production
        self.RATELIMIT_ENABLED = True
        self.RATELIMIT_DEFAULT = self.secure_config.get('PROD_RATELIMIT_DEFAULT', '20 per minute')
        self.RATELIMIT_STRATEGY = self.secure_config.get('PROD_RATELIMIT_STRATEGY', 'fixed-window')
        
        # Performance monitoring for production
        self.ENABLE_PERFORMANCE_MONITORING = True
        self.ENABLE_ERROR_TRACKING = True
        self.ENABLE_USAGE_ANALYTICS = True
        
        # Backup configuration for production
        self.BACKUP_CONFIG = {
            'enabled': self.secure_config.get('BACKUP_ENABLED', 'true').lower() == 'true',
            'schedule': self.secure_config.get('PROD_BACKUP_SCHEDULE', '0 2 * * *'),  # Daily at 2 AM
            'retention_days': int(self.secure_config.get('PROD_BACKUP_RETENTION_DAYS', '30')),
            'location': self.secure_config.get('PROD_BACKUP_LOCATION', 'backups/production/'),
            'compression': True,
            'encryption': True,
        }
        
        # Monitoring configuration for production
        self.MONITORING_CONFIG = {
            'enable_health_checks': True,
            'enable_performance_metrics': True,
            'enable_error_tracking': True,
            'enable_usage_analytics': True,
            'metrics_retention_days': int(self.secure_config.get('PROD_METRICS_RETENTION_DAYS', '90')),
            'alert_thresholds': {
                'response_time_ms': int(self.secure_config.get('PROD_RESPONSE_TIME_THRESHOLD', '2000')),
                'error_rate_percent': float(self.secure_config.get('PROD_ERROR_RATE_THRESHOLD', '1.0')),
                'memory_usage_percent': float(self.secure_config.get('PROD_MEMORY_USAGE_THRESHOLD', '80.0')),
                'cpu_usage_percent': float(self.secure_config.get('PROD_CPU_USAGE_THRESHOLD', '80.0')),
            }
        }
        
        # Error handling configuration for production
        self.ERROR_HANDLING_CONFIG = {
            'enable_error_pages': True,
            'log_errors': True,
            'email_errors': True,
            'error_reporting_url': self.secure_config.get('ERROR_REPORTING_URL'),
            'sentry_dsn': self.secure_config.get('SENTRY_DSN'),
        }
        
        # API configuration for production
        self.API_CONFIG = {
            'enable_rate_limiting': True,
            'enable_request_logging': True,
            'enable_response_caching': True,
            'max_request_size': 16 * 1024 * 1024,  # 16MB for production
            'timeout_seconds': 30,  # Shorter timeout for production
            'enable_compression': True,
            'enable_cors': True,
        }
        
        # Deployment configuration for production
        self.DEPLOYMENT_CONFIG = {
            'environment': 'production',
            'host': self.secure_config.get('PROD_HOST', '0.0.0.0'),
            'port': int(self.secure_config.get('PROD_PORT', '5000')),
            'workers': int(self.secure_config.get('PROD_WORKERS', '4')),
            'threads': int(self.secure_config.get('PROD_THREADS', '2')),
            'max_requests': int(self.secure_config.get('PROD_MAX_REQUESTS', '1000')),
            'max_requests_jitter': int(self.secure_config.get('PROD_MAX_REQUESTS_JITTER', '100')),
            'preload_app': True,
            'worker_class': self.secure_config.get('PROD_WORKER_CLASS', 'gthread'),
        }
        
        # Cost optimization configuration for production
        self.COST_OPTIMIZATION_CONFIG = {
            'use_free_tier_services': False,  # Use paid services in production
            'minimize_api_calls': True,  # Minimize API calls in production
            'use_in_memory_caching': False,  # Use Redis in production
            'disable_expensive_features': False,  # Enable all features in production
            'optimize_database_queries': True,  # Optimize in production
            'use_compression': True,  # Enable compression for production
            'minimize_external_dependencies': True,  # Minimize dependencies in production
        }
        
        # Feature flags for production
        self.FEATURE_FLAGS_CONFIG = {
            'income_comparison_enabled': True,
            'advanced_analytics_enabled': True,  # Enable in production
            'user_profiles_enabled': True,
            'job_recommendations_enabled': True,
            'email_notifications_enabled': True,
            'social_sharing_enabled': False,  # Disable in production for security
            'export_functionality_enabled': True,
        }
        
        # External services configuration for production
        self.EXTERNAL_SERVICES_CONFIG = {
            'census_api_enabled': True,  # Enable in production
            'email_service_enabled': True,
            'analytics_service_enabled': True,
            'monitoring_service_enabled': True,
            'cdn_enabled': True,  # Enable CDN for production
        }
        
        # Memory management configuration for production
        self.MEMORY_MANAGEMENT_CONFIG = {
            'max_cache_size_mb': int(self.secure_config.get('PROD_MAX_CACHE_SIZE_MB', '500')),
            'cache_cleanup_interval_seconds': int(self.secure_config.get('PROD_CACHE_CLEANUP_INTERVAL', '3600')),
            'max_concurrent_analyses': int(self.secure_config.get('PROD_MAX_CONCURRENT_ANALYSES', '10')),
            'memory_monitoring_enabled': True,
            'auto_cleanup_enabled': True,
        }
        
        # Performance monitoring configuration for production
        self.PERFORMANCE_MONITORING_CONFIG = {
            'enable_request_timing': True,
            'enable_memory_monitoring': True,
            'enable_cache_monitoring': True,
            'enable_error_monitoring': True,
            'metrics_export_interval_seconds': int(self.secure_config.get('PROD_METRICS_EXPORT_INTERVAL', '300')),
            'performance_thresholds': {
                'max_response_time_ms': int(self.secure_config.get('PROD_MAX_RESPONSE_TIME_MS', '2000')),
                'max_memory_usage_mb': int(self.secure_config.get('PROD_MAX_MEMORY_USAGE_MB', '1000')),
                'max_cpu_usage_percent': float(self.secure_config.get('PROD_MAX_CPU_USAGE_PERCENT', '80.0')),
            }
        }
    
    @classmethod
    def init_app(cls, app):
        """Initialize the Flask application with production configuration"""
        
        # Configure logging
        import logging
        from logging.handlers import RotatingFileHandler
        import os
        
        if not app.debug and not app.testing:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            file_handler = RotatingFileHandler(
                app.config.get('LOG_FILE', 'logs/mingus_production.log'),
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                app.config.get('LOG_FORMAT', '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Mingus startup')
        
        # Add security headers
        @app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response
        
        # Error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            return {'error': 'Not found'}, 404
        
        @app.errorhandler(500)
        def internal_error(error):
            return {'error': 'Internal server error'}, 500
        
        # Request logging
        @app.before_request
        def before_request():
            pass
        
        @app.after_request
        def after_request(response):
            return response
        
        # Memory monitoring
        def memory_monitor():
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            app.logger.info(f'Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB')
        
        # Schedule memory monitoring
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=memory_monitor, trigger="interval", minutes=30)
        scheduler.start()


class HerokuConfig(ProductionConfig):
    """Heroku-specific production configuration"""
    
    def __init__(self):
        super().__init__()
        self._load_heroku_config()
    
    def _load_heroku_config(self):
        """Load Heroku-specific configuration"""
        # Heroku-specific settings
        self.DATABASE_URL = self.secure_config.get('DATABASE_URL')  # Heroku sets this automatically
        self.REDIS_URL = self.secure_config.get('REDIS_URL')  # Heroku Redis addon
        self.PORT = int(self.secure_config.get('PORT', '5000'))  # Heroku sets PORT
        
        # Heroku-specific deployment settings
        self.DEPLOYMENT_CONFIG.update({
            'host': '0.0.0.0',
            'port': self.PORT,
            'workers': 1,  # Heroku dynos are single-threaded
            'threads': 1,
        })


class RailwayConfig(ProductionConfig):
    """Railway-specific production configuration"""
    
    def __init__(self):
        super().__init__()
        self._load_railway_config()
    
    def _load_railway_config(self):
        """Load Railway-specific configuration"""
        # Railway-specific settings
        self.DATABASE_URL = self.secure_config.get('DATABASE_URL')  # Railway sets this automatically
        self.REDIS_URL = self.secure_config.get('REDIS_URL')  # Railway Redis service
        self.PORT = int(self.secure_config.get('PORT', '5000'))  # Railway sets PORT
        
        # Railway-specific deployment settings
        self.DEPLOYMENT_CONFIG.update({
            'host': '0.0.0.0',
            'port': self.PORT,
            'workers': 1,  # Railway containers are single-threaded
            'threads': 1,
        })


class RenderConfig(ProductionConfig):
    """Render-specific production configuration"""
    
    def __init__(self):
        super().__init__()
        self._load_render_config()
    
    def _load_render_config(self):
        """Load Render-specific configuration"""
        # Render-specific settings
        self.DATABASE_URL = self.secure_config.get('DATABASE_URL')  # Render sets this automatically
        self.REDIS_URL = self.secure_config.get('REDIS_URL')  # Render Redis service
        self.PORT = int(self.secure_config.get('PORT', '10000'))  # Render sets PORT
        
        # Render-specific deployment settings
        self.DEPLOYMENT_CONFIG.update({
            'host': '0.0.0.0',
            'port': self.PORT,
            'workers': 1,  # Render services are single-threaded
            'threads': 1,
        })


class VercelConfig(ProductionConfig):
    """Vercel-specific production configuration"""
    
    def __init__(self):
        super().__init__()
        self._load_vercel_config()
    
    def _load_vercel_config(self):
        """Load Vercel-specific configuration"""
        # Vercel-specific settings
        self.DATABASE_URL = self.secure_config.get('DATABASE_URL')  # Vercel sets this automatically
        self.REDIS_URL = self.secure_config.get('REDIS_URL')  # Vercel Redis service
        self.PORT = int(self.secure_config.get('PORT', '3000'))  # Vercel sets PORT
        
        # Vercel-specific deployment settings
        self.DEPLOYMENT_CONFIG.update({
            'host': '0.0.0.0',
            'port': self.PORT,
            'workers': 1,  # Vercel functions are single-threaded
            'threads': 1,
        })


def get_config():
    """Get the appropriate configuration based on environment"""
    config_name = os.environ.get('FLASK_CONFIG', 'production')
    
    if config_name == 'production':
        return ProductionConfig()
    elif config_name == 'testing':
        return TestingConfig()
    elif config_name == 'development':
        return DevelopmentConfig()
    elif config_name == 'heroku':
        return HerokuConfig()
    elif config_name == 'railway':
        return RailwayConfig()
    elif config_name == 'render':
        return RenderConfig()
    elif config_name == 'vercel':
        return VercelConfig()
    else:
        return ProductionConfig() 