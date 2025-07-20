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
    
    # Register blueprints
    register_blueprints(app)
    
    # Register root routes
    register_root_routes(app)
    
    # Register error handlers
    register_error_handlers(app)
    
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
        
        # Store in app config
        app.config['DATABASE_ENGINE'] = engine
        app.config['DATABASE_SESSION'] = SessionLocal
        
        # FIXED: Import all models to register them with the shared Base
        from backend.models import (
            User, UserProfile, OnboardingProgress, 
            UserHealthCheckin, HealthSpendingCorrelation
        )
        
        # Import encrypted models
        from backend.models.encrypted_financial_models import (
            EncryptedFinancialProfile, EncryptedIncomeSource, 
            EncryptedDebtAccount, FinancialAuditLog
        )
        
        # Create all tables using the shared Base - MUCH SIMPLER!
        if app.config.get('CREATE_TABLES', True):
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created/verified using shared Base")
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        logger.warning("Continuing without database setup")

def init_services(app: Flask) -> None:
    """
    Initialize and register services with Flask app context
    
    Args:
        app: Flask application instance
    """
    try:
        database_url = app.config.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not configured")
        
        # Initialize UserService
        user_service = UserService(app.config['DATABASE_SESSION'])
        app.user_service = user_service
        
        # Initialize OnboardingService
        onboarding_service = OnboardingService(app.config['DATABASE_SESSION'])
        app.onboarding_service = onboarding_service
        
        # Initialize AuditService
        audit_service = AuditService(app.config['DATABASE_SESSION'])
        app.audit_service = audit_service
        
        # Initialize VerificationService
        verification_service = VerificationService(app.config['DATABASE_SESSION'])
        app.verification_service = verification_service
        
        logger.info("Services initialized successfully")
        
    except Exception as e:
        logger.error(f"Service initialization failed: {str(e)}")
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
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(health_bp, url_prefix='/api/health')
        app.register_blueprint(onboarding_bp, url_prefix='/api/onboarding')
        app.register_blueprint(secure_financial_bp, url_prefix='/api/secure')
        app.register_blueprint(financial_questionnaire_bp, url_prefix='/api/questionnaire')
        app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
        app.register_blueprint(insights_bp, url_prefix='/api/insights')
        app.register_blueprint(tour_bp, url_prefix='/api/tour')
        app.register_blueprint(checklist_bp, url_prefix='/api/checklist')
        
        # Register new onboarding completion blueprint
        app.register_blueprint(onboarding_completion_bp, url_prefix='/api/onboarding/completion')
        
        logger.info("All blueprints registered successfully")
        
    except Exception as e:
        logger.error(f"Error registering blueprints: {str(e)}")
        raise

def register_root_routes(app: Flask) -> None:
    """
    Register root-level routes
    
    Args:
        app: Flask application instance
    """
    @app.route('/')
    def root():
        from flask import redirect
        return redirect('/api/auth/login')
    
    logger.info("Root routes registered successfully")

def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
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
        return {'error': 'Rate limit exceeded'}, 429

# Service getters for use in routes
def get_user_service() -> Optional[UserService]:
    """Get UserService instance"""
    from flask import current_app
    return getattr(current_app, 'user_service', None)

def get_onboarding_service() -> Optional[OnboardingService]:
    """Get OnboardingService instance"""
    from flask import current_app
    return getattr(current_app, 'onboarding_service', None)

def get_audit_service() -> Optional[AuditService]:
    """Get AuditService instance"""
    from flask import current_app
    return getattr(current_app, 'audit_service', None)

def get_verification_service() -> Optional[VerificationService]:
    """Get VerificationService instance"""
    from flask import current_app
    return getattr(current_app, 'verification_service', None)

def get_db_session():
    """Get database session"""
    from flask import current_app
    return current_app.config.get('DATABASE_SESSION')() 