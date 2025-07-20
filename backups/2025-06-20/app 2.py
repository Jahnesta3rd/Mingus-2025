"""
Main Flask application entry point
"""

import os
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

def main():
    """Main application entry point"""
    try:
        # Create Flask app using factory pattern
        app = create_app()
        
        # Get port from environment or config
        port = int(os.environ.get('PORT', 5003))
        app.config['PORT'] = port
        
        # Get host from environment
        host = os.environ.get('HOST', '0.0.0.0')
        
        # Log startup information
        logger.info(f"Starting Flask application on {host}:{port}")
        logger.info(f"Environment: {app.config.get('ENV', 'development')}")
        logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
        
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