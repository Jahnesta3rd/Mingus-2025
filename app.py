"""
Main Flask application entry point with centralized security configuration
"""

import os
import sys
from loguru import logger
from backend.app_factory import create_app

# Configure logging
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)

def initialize_security_systems():
    """Initialize all security systems and validate configuration"""
    try:
        logger.info("Initializing security configuration systems...")
        
        # Import and initialize security configuration
        from config.security_config import init_security_config, get_security_config
        
        # Get environment from environment variable
        environment = os.environ.get('FLASK_ENV', 'development')
        logger.info(f"Initializing security configuration for environment: {environment}")
        
        # Initialize security configuration
        security_config = init_security_config(environment)
        
        # Validate security configuration
        logger.info("Validating security configuration...")
        try:
            # This will raise ConfigValidationError if validation fails
            security_config._validate_configuration()
            logger.info("Security configuration validation passed")
        except Exception as e:
            logger.error(f"Security configuration validation failed: {str(e)}")
            if environment == 'production':
                logger.critical("CRITICAL: Security validation failed in production environment")
                sys.exit(1)
            else:
                logger.warning("Security validation failed, continuing with warnings")
        
        # Log security configuration summary
        security_summary = security_config.get_security_summary()
        logger.info(f"Security configuration summary: {security_summary}")
        
        # Check for critical security warnings
        if environment == 'production':
            critical_warnings = []
            if not security_config.get('SESSION_COOKIE_SECURE', False):
                critical_warnings.append("Secure cookies disabled in production")
            if not security_config.get('AUDIT_LOGGING_ENABLED', False):
                critical_warnings.append("Audit logging disabled in production")
            if security_config.get('DEBUG', False):
                critical_warnings.append("DEBUG mode enabled in production")
            
            if critical_warnings:
                logger.critical("CRITICAL SECURITY WARNINGS in production:")
                for warning in critical_warnings:
                    logger.critical(f"  - {warning}")
                logger.critical("Application startup blocked due to critical security issues")
                sys.exit(1)
        
        logger.info("Security systems initialization completed successfully")
        return security_config
        
    except Exception as e:
        logger.error(f"Failed to initialize security systems: {str(e)}")
        if environment == 'production':
            logger.critical("CRITICAL: Security initialization failed in production")
            sys.exit(1)
        else:
            logger.warning("Security initialization failed, continuing with warnings")
            return None

def main():
    """Main application entry point with security initialization"""
    try:
        # Initialize security systems first
        security_config = initialize_security_systems()
        
        # Create Flask app using factory pattern
        app = create_app()
        
        # Apply security configuration to Flask app
        if security_config:
            try:
                # Update Flask app config with security settings
                security_settings = security_config.get_all()
                for key, value in security_settings.items():
                    if key not in app.config:
                        app.config[key] = value
                
                # Apply security headers
                if security_config.get('SECURITY_HEADERS_ENABLED', False):
                    from backend.middleware.security_headers import SecurityHeadersMiddleware
                    app.wsgi_app = SecurityHeadersMiddleware(app.wsgi_app, security_config)
                    logger.info("Security headers middleware initialized")
                
                # Apply rate limiting
                if security_config.get('RATE_LIMIT_ENABLED', False):
                    from backend.middleware.rate_limiting import RateLimitingMiddleware
                    app.wsgi_app = RateLimitingMiddleware(app.wsgi_app, security_config)
                    logger.info("Rate limiting middleware initialized")
                
                # Apply CSRF protection
                if security_config.get('CSRF_ENABLED', False):
                    from backend.middleware.csrf_protection import CSRFProtectionMiddleware
                    app.wsgi_app = CSRFProtectionMiddleware(app.wsgi_app, security_config)
                    logger.info("CSRF protection middleware initialized")
                
                logger.info("Security configuration applied to Flask application")
                
            except Exception as e:
                logger.error(f"Failed to apply security configuration to Flask app: {str(e)}")
                if os.environ.get('FLASK_ENV') == 'production':
                    logger.critical("CRITICAL: Security configuration application failed in production")
                    sys.exit(1)
        
        # Get port from environment or config
        port = int(os.environ.get('PORT', 5003))
        app.config['PORT'] = port
        
        # Get host from environment
        host = os.environ.get('HOST', '0.0.0.0')
        
        # Log startup information
        logger.info(f"Starting Flask application on {host}:{port}")
        logger.info(f"Environment: {app.config.get('ENV', 'development')}")
        logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
        
        # Final security check before startup
        if security_config:
            try:
                # Validate final configuration
                security_config._validate_configuration()
                logger.info("Final security validation passed")
            except Exception as e:
                logger.error(f"Final security validation failed: {str(e)}")
                if os.environ.get('FLASK_ENV') == 'production':
                    logger.critical("CRITICAL: Final security validation failed in production")
                    sys.exit(1)
        
        # Run the application
        app.run(
            host=host,
            port=app.config.get('PORT'),
            debug=app.config.get('DEBUG', False),
            use_reloader=app.config.get('DEBUG', False)
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

if __name__ == '__main__':
    main()