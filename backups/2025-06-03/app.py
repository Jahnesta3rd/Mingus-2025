from flask import Flask
from flask_cors import CORS
from config import config
import os
from loguru import logger
from tests.mock_supabase import MockSupabaseClient
from backend.services.important_dates_service import ImportantDatesService
from backend.services.onboarding_service import OnboardingService
from backend.services.user_service import UserService
import asyncio
from functools import wraps

def async_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        except RuntimeError:
            # If we're already in an event loop (e.g., during testing),
            # create a new one just for this request
            new_loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(new_loop)
                return new_loop.run_until_complete(f(*args, **kwargs))
            finally:
                new_loop.close()
                asyncio.set_event_loop(loop)
    return wrapper

def create_app(config_name=None):
    """Create Flask application."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name]())
    
    # Enable CORS
    CORS(app)
    
    # Initialize services
    if config_name == 'testing':
        app.supabase_client = MockSupabaseClient()
    else:
        app.supabase_client = app.config.get('supabase_client')
    
    app.important_dates_service = ImportantDatesService(app.supabase_client)
    app.onboarding_service = OnboardingService(app.supabase_client)
    app.user_service = UserService(app.supabase_client)
    
    # Register blueprint
    with app.app_context():
        from routes import api
        app.register_blueprint(api)
    
    # Log configuration
    logger.info(f"Environment: {config_name}")
    logger.info(f"Supabase URL: {app.config['SUPABASE_URL']}")
    logger.info(f"Port: {app.config['PORT']}")
    
    return app

# Create app instance for production/development
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=True)