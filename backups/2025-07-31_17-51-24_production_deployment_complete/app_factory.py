# Test Edit: Attempting to modify a file in the backend directory.
"""
Flask Application Factory
Initializes and configures the Flask application with services
"""

from flask import Flask
from flask_cors import CORS
from loguru import logger
import os
from typing import Optional

from backend.services.user_service import UserService
from backend.services.onboarding_service import OnboardingService
from backend.services.audit_logging import AuditService
from backend.services.verification_service import VerificationService
from backend.middleware.security_middleware import SecurityMiddleware
from backend.models import Base  # Import shared Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.development import DevelopmentConfig

# Import new models
from backend.models.reminder_schedule import ReminderSchedule
from backend.models.user_preferences import UserPreferences

# Import new routes
from backend.routes.onboarding_completion import onboarding_completion_bp

# Import Flask-Celery integration
from backend.integration.flask_celery_integration import (
    init_flask_celery_integration,
    get_flask_celery_integration
)

# Import communication orchestrator
from backend.routes.communication_api import communication_api_bp

def create_app(config_name: str = None) -> Flask:
    """
    Application factory function
    
    Args:
        config_name: Configuration name (development, production, testing)
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(DevelopmentConfig)
    
    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize security middleware
    security_middleware = SecurityMiddleware()
    security_middleware.init_app(app)
    
    # Initialize request logging using Flask hooks
    from backend.middleware.request_logger import setup_request_logging
    setup_request_logging(app)
    
    # Initialize database
    init_database(app)  # Re-enabled with fixed version
    
    # Initialize services
    init_services(app)  # Re-enabled services
    
    # Initialize Flask-Celery integration
    init_flask_celery_integration(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register comprehensive communication API blueprint
    app.register_blueprint(communication_api_bp)
    
    # Register root routes
    register_root_routes(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register Celery health check endpoint
    register_celery_health_check(app)
    
    logger.info(f"Flask app initialized with config: {config_name}")
    return app

def init_database(app: Flask) -> None:
    """
    Initialize database connection and create tables - FIXED VERSION
    """
    try:
        database_url = app.config.get('DATABASE_URL')
        if not database_url:
            logger.warning("DATABASE_URL not configured, skipping database setup")
            return
        
        # Create engine
        engine = create_engine(
            database_url,
            pool_size=app.config.get('DB_POOL_SIZE', 10),
            max_overflow=app.config.get('DB_MAX_OVERFLOW', 20),
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Store in app config for access
        app.config['DATABASE_ENGINE'] = engine
        app.config['DATABASE_SESSION'] = SessionLocal
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def init_services(app: Flask) -> None:
    """
    Initialize application services
    """
    try:
        # Initialize user service
        user_service = UserService()
        app.config['USER_SERVICE'] = user_service
        
        # Initialize onboarding service
        onboarding_service = OnboardingService()
        app.config['ONBOARDING_SERVICE'] = onboarding_service
        
        # Initialize audit service
        audit_service = AuditService()
        app.config['AUDIT_SERVICE'] = audit_service
        
        # Initialize verification service
        verification_service = VerificationService()
        app.config['VERIFICATION_SERVICE'] = verification_service
        
        logger.info("Services initialized successfully")
        
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise

def register_blueprints(app: Flask) -> None:
    """
    Register Flask blueprints
    
    Args:
        app: Flask application instance
    """
    try:
        from backend.routes.auth import auth_bp
        from backend.routes.health import health_bp
        from backend.routes.onboarding import onboarding_bp
        from backend.routes.secure_financial import secure_financial_bp
        from backend.routes.financial_questionnaire import financial_questionnaire_bp
        from backend.monitoring.dashboard import dashboard_bp
        from backend.routes.insights import insights_bp
        from backend.routes.tour import tour_bp
        from backend.routes.checklist import checklist_bp
        from backend.routes.resume_analysis import resume_analysis_bp
        from backend.routes.intelligent_job_matching import intelligent_job_matching_bp
        from backend.routes.career_advancement import career_advancement_bp
        from backend.routes.job_recommendation_engine import job_recommendation_engine_bp
        from backend.routes.enhanced_job_recommendations import enhanced_job_recommendations_bp
        from backend.routes.income_analysis import income_analysis_bp
        from backend.routes.budget_tier import budget_tier_bp
        from backend.routes.budget_tier_insights import budget_insights_bp
        from backend.routes.bank_connection_flow import bank_connection_flow_bp
        from backend.routes.budget_tier_dashboard import budget_tier_dashboard_bp
        from backend.routes.communication_preferences import communication_preferences_bp
        from backend.routes.admin_communication import admin_communication_bp
        from backend.routes.behavioral_triggers import behavioral_triggers_bp
        from backend.routes.communication_analytics import communication_analytics_bp
        from backend.routes.webhook_handlers import webhook_handlers_bp
        from backend.routes.reporting_api import reporting_api_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(health_bp, url_prefix='/api/health')
        app.register_blueprint(onboarding_bp, url_prefix='/api/onboarding')
        app.register_blueprint(secure_financial_bp, url_prefix='/api/secure')
        app.register_blueprint(financial_questionnaire_bp, url_prefix='/api/questionnaire')
        app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
        app.register_blueprint(insights_bp, url_prefix='/api/insights')
        app.register_blueprint(tour_bp, url_prefix='/api/tour')
        app.register_blueprint(checklist_bp, url_prefix='/api/checklist')
        app.register_blueprint(resume_analysis_bp, url_prefix='/api/resume')
        app.register_blueprint(intelligent_job_matching_bp, url_prefix='/api/job-matching')
        app.register_blueprint(career_advancement_bp, url_prefix='/api/career-advancement')
        app.register_blueprint(job_recommendation_engine_bp, url_prefix='/api/job-recommendations')
        app.register_blueprint(enhanced_job_recommendations_bp, url_prefix='/api/enhanced-recommendations')
        app.register_blueprint(income_analysis_bp, url_prefix='/api/income-analysis')
        app.register_blueprint(budget_tier_bp, url_prefix='/api/budget-tier')
        app.register_blueprint(budget_insights_bp, url_prefix='/api/budget-insights')
        app.register_blueprint(bank_connection_flow_bp, url_prefix='/api/bank-connection')
        app.register_blueprint(budget_tier_dashboard_bp, url_prefix='/api/budget-tier/dashboard')
        app.register_blueprint(communication_preferences_bp)
        app.register_blueprint(admin_communication_bp)
        app.register_blueprint(behavioral_triggers_bp)
        app.register_blueprint(communication_analytics_bp, url_prefix='/api/analytics')
        app.register_blueprint(webhook_handlers_bp)
        app.register_blueprint(reporting_api_bp)
        
        logger.info("All blueprints registered successfully")
        
    except Exception as e:
        logger.error(f"Blueprint registration failed: {str(e)}")
        raise

def register_root_routes(app: Flask) -> None:
    """
    Register root routes
    
    Args:
        app: Flask application instance
    """
    @app.route('/')
    def root():
        return {
            'message': 'MINGUS API is running',
            'version': '1.0.0',
            'status': 'healthy'
        }

def register_celery_health_check(app: Flask) -> None:
    """
    Register Celery health check endpoint
    
    Args:
        app: Flask application instance
    """
    @app.route('/api/celery/health')
    def celery_health_check():
        """Health check endpoint for Celery integration"""
        try:
            integration = get_flask_celery_integration()
            if integration:
                health_status = integration.health_check()
                return health_status, 200
            else:
                return {
                    'error': 'Flask-Celery integration not initialized',
                    'status': 'unhealthy'
                }, 500
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {
                'error': 'Health check failed',
                'status': 'unhealthy',
                'details': str(e)
            }, 500

def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request'}, 400

    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized'}, 401

    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden'}, 403

    @app.errorhandler(429)
    def too_many_requests(error):
        return {'error': 'Too many requests'}, 429

def get_user_service() -> Optional[UserService]:
    """Get user service instance"""
    from flask import current_app
    return current_app.config.get('USER_SERVICE')

def get_onboarding_service() -> Optional[OnboardingService]:
    """Get onboarding service instance"""
    from flask import current_app
    return current_app.config.get('ONBOARDING_SERVICE')

def get_audit_service() -> Optional[AuditService]:
    """Get audit service instance"""
    from flask import current_app
    return current_app.config.get('AUDIT_SERVICE')

def get_verification_service() -> Optional[VerificationService]:
    """Get verification service instance"""
    from flask import current_app
    return current_app.config.get('VERIFICATION_SERVICE')

def get_db_session():
    """Get database session"""
    from flask import current_app
    SessionLocal = current_app.config.get('DATABASE_SESSION')
    if SessionLocal:
        return SessionLocal()
    return None 