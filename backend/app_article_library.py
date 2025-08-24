"""
MINGUS Flask Application with Article Library Integration
Simplified entry point demonstrating article library integration
"""

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import existing Mingus components
from config.development import DevelopmentConfig
from backend.extensions import db, migrate

# Import new article library components
from backend.routes.articles import articles_bp
from backend.models.articles import Article, UserArticleProgress, UserAssessmentScores
from backend.integrations.article_library_integration import integrate_article_library
from config.article_library import ArticleLibraryConfig

def create_app(config_class=DevelopmentConfig):
    """Create and configure Flask application with article library integration"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize existing extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize new extensions for article library
    cache = Cache(app)
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["1000 per hour"]
    )
    
    # Configure CORS for frontend integration
    CORS(app, origins=[
        "http://localhost:3000",  # Development
        "http://localhost:5173",  # Vite development
        "https://your-mingus-domain.com"  # Production
    ])

    # Register existing blueprints (if available)
    try:
        from backend.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
    except ImportError:
        pass
    
    try:
        from backend.routes.users import users_bp
        app.register_blueprint(users_bp, url_prefix='/api/users')
    except ImportError:
        pass
    
    try:
        from backend.routes.forecasts import forecasts_bp
        app.register_blueprint(forecasts_bp, url_prefix='/api/forecasts')
    except ImportError:
        pass
    
    # Register new article library blueprint
    app.register_blueprint(articles_bp, url_prefix='/api/articles')
    
    # Integrate article library
    if app.config.get('ENABLE_ARTICLE_LIBRARY', True):
        try:
            integration = integrate_article_library(app)
            app.article_library_integration = integration
            print("✅ Article library integration completed successfully")
        except Exception as e:
            print(f"❌ Article library integration failed: {str(e)}")
            # Don't fail the entire app if article library integration fails
    else:
        print("ℹ️ Article library integration disabled")
    
    # Add article library specific error handlers
    @app.errorhandler(429)
    def rate_limit_handler(e):
        return jsonify({
            'error': 'Rate limit exceeded', 
            'message': str(e.description) if hasattr(e, 'description') else 'Too many requests'
        }), 429
    
    # Add health check endpoint with article library status
    @app.route('/api/health')
    def health_check():
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            
            # Check article library tables
            article_count = 0
            try:
                article_count = Article.query.count()
            except Exception:
                # Article tables might not exist yet
                pass
            
            # Get article library integration status
            article_library_status = "not_integrated"
            if hasattr(app, 'article_library_integration'):
                try:
                    status = app.article_library_integration.get_integration_status()
                    article_library_status = "active" if status['configuration_valid'] else "inactive"
                except Exception:
                    article_library_status = "error"
            
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'article_library': {
                    'status': article_library_status,
                    'article_count': article_count
                },
                'features': {
                    'ai_recommendations': app.config.get('ENABLE_AI_RECOMMENDATIONS', False),
                    'cultural_personalization': app.config.get('ENABLE_CULTURAL_PERSONALIZATION', False),
                    'advanced_search': app.config.get('ENABLE_ADVANCED_SEARCH', False),
                    'social_sharing': app.config.get('ENABLE_SOCIAL_SHARING', False)
                }
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500
    
    # Add article library status endpoint
    @app.route('/api/articles/status')
    def article_library_status():
        """Get detailed article library status"""
        try:
            if hasattr(app, 'article_library_integration'):
                status = app.article_library_integration.get_integration_status()
                return jsonify({
                    'status': 'success',
                    'article_library': status
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Article library not integrated'
                }), 404
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # Add configuration endpoint
    @app.route('/api/articles/config')
    def article_library_config():
        """Get article library configuration (non-sensitive)"""
        try:
            config = ArticleLibraryConfig()
            settings = config.get_article_library_settings()
            
            # Remove sensitive information
            if 'openai' in settings:
                settings['openai']['api_key'] = '***' if settings['openai']['api_key'] else None
            
            if 'email_processing' in settings:
                settings['email_processing']['mac_email_address'] = '***' if settings['email_processing']['mac_email_address'] else None
                settings['email_processing']['mac_email_app_password'] = '***' if settings['email_processing'].get('mac_email_app_password') else None
            
            return jsonify({
                'status': 'success',
                'config': settings
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    return app

# Create application instance
app = create_app()

if __name__ == '__main__':
    print("🚀 Starting MINGUS Flask Application with Article Library Integration")
    print("📚 Article Library Features:")
    print("   - AI-powered article classification")
    print("   - Cultural personalization")
    print("   - Advanced search capabilities")
    print("   - User progress tracking")
    print("   - Assessment-based access control")
    print("   - Background task processing")
    print("   - Redis caching and rate limiting")
    print("")
    print("🌐 Available endpoints:")
    print("   - Health check: http://localhost:5000/api/health")
    print("   - Article library: http://localhost:5000/api/articles")
    print("   - Article status: http://localhost:5000/api/articles/status")
    print("   - Article config: http://localhost:5000/api/articles/config")
    print("")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config.get('FLASK_DEBUG', True)
    )
