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
from backend.models import Base  # Import shared Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.development import DevelopmentConfig

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
    # Import blueprints here to avoid circular imports
    from backend.routes.auth import auth_bp
    from backend.routes.onboarding import onboarding_bp
    from backend.routes.user import user_bp
    from backend.routes.health import health_bp
    from backend.routes.health_insights import health_insights_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(onboarding_bp, url_prefix='/api/onboarding')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(health_bp, url_prefix='/api/health')
    app.register_blueprint(health_insights_bp)
    
    logger.info("Blueprints registered successfully")

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
    
    logger.info("Error handlers registered successfully")

def get_user_service() -> Optional[UserService]:
    """
    Get UserService from Flask app context
    
    Returns:
        UserService instance or None if not available
    """
    from flask import current_app
    return getattr(current_app, 'user_service', None)

def get_onboarding_service() -> Optional[OnboardingService]:
    """
    Get OnboardingService from Flask app context
    
    Returns:
        OnboardingService instance or None if not available
    """
    from flask import current_app
    return getattr(current_app, 'onboarding_service', None)

def get_db_session():
    """
    Get database session from Flask app context
    
    Returns:
        Database session or None if not available
    """
    from flask import current_app
    SessionLocal = current_app.config.get('DATABASE_SESSION')
    if SessionLocal:
        return SessionLocal()
    return None 