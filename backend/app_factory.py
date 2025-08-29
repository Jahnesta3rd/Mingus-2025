# Test Edit: Attempting to modify a file in the backend directory.
"""
Flask Application Factory
Initializes and configures the Flask application with services
"""

from flask import Flask, current_app
from flask_cors import CORS
from loguru import logger
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from backend.services.user_service import UserService
from backend.services.onboarding_service import OnboardingService
from backend.services.audit_logging import AuditService
from backend.services.verification_service import VerificationService
from backend.middleware.security_middleware import SecurityMiddleware
from backend.middleware.security import init_security

# Import new assessment security integration
from backend.security.assessment_security_integration import init_assessment_security
from backend.models import Base  # Import shared Base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config.development import DevelopmentConfig

# Import metrics
from .metrics import create_metrics_endpoint, health_check_timer, record_health_check_failure, record_health_check_success, update_system_metrics, update_database_metrics, update_redis_metrics

# Import health monitoring
from backend.monitoring.health import create_health_routes

# Import new models
from backend.models.reminder_schedule import ReminderSchedule
from backend.models.user_preferences import UserPreferences

# Import new routes
from backend.routes.onboarding_completion import onboarding_completion_bp

# Import article library components
from backend.integrations.article_library_integration import integrate_article_library
from config.article_library import ArticleLibraryConfig

def create_app(config_name: str = None) -> Flask:
    """
    Application factory function
    
    Args:
        config_name: Configuration name (development, production, testing)
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__, template_folder='../templates')
    
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
    
    # Initialize security middleware (NEW)
    security_components = init_security(app)
    
    # Initialize assessment security integration
    assessment_security = init_assessment_security(app)
    
    # Initialize request logging using Flask hooks
    from backend.middleware.request_logger import setup_request_logging
    setup_request_logging(app)
    
    # Set DATABASE_URL directly from environment if not in config
    if not app.config.get('DATABASE_URL') and os.getenv('DATABASE_URL'):
        app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
        logger.info(f"Loaded DATABASE_URL from environment: {app.config['DATABASE_URL']}")
    
    # Initialize database
    init_database(app)  # Re-enabled with fixed version
    
    # Initialize services (skip in testing if DATABASE_URL not set)
    if app.config.get('DATABASE_URL'):
        init_services(app)
    else:
        logger.warning("Skipping database-dependent service initialization: DATABASE_URL not set")
    
    # Initialize email service (independent of database)
    init_email_service(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register root routes
    register_root_routes(app)
    
    # Add health check routes (NEW) if not already present
    try:
        if 'health_check' not in app.view_functions:
            create_health_routes(app)
    except Exception:
        logger.warning("Skipping create_health_routes (optional dependencies missing)")
    
    # Integrate article library if enabled
    if app.config.get('ENABLE_ARTICLE_LIBRARY', True):
        try:
            integration = integrate_article_library(app)
            app.article_library_integration = integration
            logger.info("Article library integration completed successfully")
        except Exception as e:
            logger.error(f"Article library integration failed: {str(e)}")
            # Don't fail the entire app if article library integration fails
    else:
        logger.info("Article library integration disabled")
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register metrics endpoint
    create_metrics_endpoint(app)
    
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
        
        # Initialize the global database session factory
        from backend.database import init_database_session_factory
        init_database_session_factory(database_url)
        
        # Skip model imports to avoid conflicts - create tables directly
        
        # Create only the tables we need
        if app.config.get('CREATE_TABLES', True):
            # Create tables manually to avoid model conflicts
            with engine.connect() as conn:
                # Create users table if it doesn't exist
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        email VARCHAR(255) UNIQUE NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))
                
                # Create questionnaire_submissions table if it doesn't exist
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS questionnaire_submissions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        email VARCHAR(255) NOT NULL,
                        answers JSONB NOT NULL,
                        total_score INTEGER NOT NULL,
                        wellness_level VARCHAR(100) NOT NULL,
                        wellness_description TEXT,
                        has_signed_up BOOLEAN DEFAULT FALSE,
                        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                        source VARCHAR(100) DEFAULT 'financial_questionnaire',
                        utm_source VARCHAR(100),
                        utm_medium VARCHAR(100),
                        utm_campaign VARCHAR(100),
                        submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        signed_up_at TIMESTAMP WITH TIME ZONE,
                        CONSTRAINT questionnaire_submissions_email_unique UNIQUE (email)
                    )
                """))
                
                # Create relationship_questionnaire_submissions table if it doesn't exist
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS relationship_questionnaire_submissions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        email VARCHAR(255) NOT NULL,
                        answers JSONB NOT NULL,
                        total_score INTEGER NOT NULL,
                        connection_level VARCHAR(100) NOT NULL,
                        connection_description TEXT,
                        has_signed_up BOOLEAN DEFAULT FALSE,
                        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                        source VARCHAR(100) DEFAULT 'relationship_questionnaire',
                        utm_source VARCHAR(100),
                        utm_medium VARCHAR(100),
                        utm_campaign VARCHAR(100),
                        submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        signed_up_at TIMESTAMP WITH TIME ZONE,
                        CONSTRAINT relationship_questionnaire_submissions_email_unique UNIQUE (email)
                    )
                """))
                
                conn.commit()
            
            logger.info("Questionnaire tables created/verified successfully")
        
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

def init_email_service(app: Flask) -> None:
    """
    Initialize email service (independent of database)
    
    Args:
        app: Flask application instance
    """
    try:
        # Initialize Resend Email Service
        from backend.services.resend_email_service import resend_email_service
        app.resend_email_service = resend_email_service
        logger.info("Resend email service initialized")
        
    except Exception as e:
        logger.error(f"Email service initialization failed: {str(e)}")
        logger.warning("Continuing without email service")

def register_blueprints(app: Flask) -> None:
    """
    Register Flask blueprints
    
    Args:
        app: Flask application instance
    """
    try:
        from backend.routes.auth import auth_bp
        from backend.routes.health import health_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(health_bp, url_prefix='/api/health')

        # Optional blueprints guarded for missing optional deps in test env
        try:
            from backend.routes.system_health import system_health_bp
            app.register_blueprint(system_health_bp, url_prefix='/api/system/health')
        except Exception:
            logger.warning("Skipping system_health blueprint (optional dependency missing)")

        for bp_import, prefix in [
            ("backend.routes.onboarding:onboarding_bp", "/api/onboarding"),
            ("backend.routes.secure_financial:secure_financial_bp", "/api/secure"),
            ("backend.routes.financial_questionnaire:financial_questionnaire_bp", "/api/questionnaire"),
            ("backend.monitoring.dashboard:dashboard_bp", "/api/dashboard"),
            ("backend.routes.insights:insights_bp", "/api/insights"),
            ("backend.routes.tour:tour_bp", "/api/tour"),
            ("backend.routes.checklist:checklist_bp", "/api/checklist"),
            ("backend.routes.resume_analysis:resume_analysis_bp", "/api/resume"),
            ("backend.routes.intelligent_job_matching:intelligent_job_matching_bp", "/api/job-matching"),
            ("backend.routes.career_advancement:career_advancement_bp", "/api/career-advancement"),
            ("backend.routes.job_recommendation_engine:job_recommendation_engine_bp", "/api/job-recommendations"),
            ("backend.routes.enhanced_job_recommendations:enhanced_job_recommendations_bp", "/api/enhanced-recommendations"),
            ("backend.routes.income_analysis:income_analysis_bp", "/api/income-analysis"),
            ("backend.routes.articles:articles_bp", "/api/articles"),
            ("backend.routes.memes:memes_bp", "/api/memes"),
            ("backend.routes.meme_admin:meme_admin_bp", "/admin/memes"),
            ("backend.routes.calculator_routes:calculator_bp", "/api/v1/calculator"),
            # ("backend.routes.assessment_routes:assessment_bp", "/api/assessments"),  # Temporarily disabled due to import issues
        ]:
            try:
                module_name, attr_name = bp_import.split(":")
                mod = __import__(module_name, fromlist=[attr_name])
                bp = getattr(mod, attr_name)
                app.register_blueprint(bp, url_prefix=prefix)
            except Exception:
                logger.warning(f"Skipping optional blueprint {bp_import}")

        logger.info("Blueprints registered (core + available optional)")

    except Exception as e:
        logger.error(f"Blueprint registration failed: {str(e)}")
        raise

def register_root_routes(app: Flask) -> None:
    """
    Register minimal root-level routes for testing and health checks.
    This implementation intentionally avoids optional dependencies to be test-friendly.
    """
    from datetime import datetime

    @app.route('/')
    def root():
        """Serve the main landing page at root"""
        import os
        # Get the absolute path to the landing.html file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        landing_path = os.path.join(project_root, 'landing.html')
        
        if os.path.exists(landing_path):
            with open(landing_path, 'r', encoding='utf-8') as f:
                return f.read(), 200, {'Content-Type': 'text/html'}
        else:
            return {
                'message': 'Mingus API is running',
                'version': '1.0.0',
                'status': 'healthy',
                'landing_path_checked': landing_path
            }

    @app.route('/landing')
    def landing_page():
        """Serve the landing page"""
        import os
        # Get the absolute path to the landing.html file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        landing_path = os.path.join(project_root, 'landing.html')
        
        if os.path.exists(landing_path):
            with open(landing_path, 'r', encoding='utf-8') as f:
                return f.read(), 200, {'Content-Type': 'text/html'}
        else:
            return {'error': 'Landing page not found', 'landing_path_checked': landing_path}, 404

    @app.route('/health')
    def health_check():
        """Enhanced health check with article library status"""
        try:
            # Check database connection using our raw SQLAlchemy setup
            db_status = "not_configured"
            article_count = 0
            
            # Check if we have database configuration
            if current_app.config.get('DATABASE_URL') and current_app.config.get('DATABASE_ENGINE'):
                try:
                    from sqlalchemy import text
                    engine = current_app.config.get('DATABASE_ENGINE')
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    
                    db_status = "healthy"
                    
                    # Check article library tables if available
                    try:
                        from backend.models.articles import Article
                        article_count = Article.query.count()
                    except Exception:
                        # Article tables might not exist yet
                        pass
                except Exception as e:
                    db_status = f"unhealthy: {str(e)}"
            
            # Get article library status
            article_library_status = "not_integrated"
            if hasattr(current_app, 'article_library_integration'):
                try:
                    status = current_app.article_library_integration.get_integration_status()
                    article_library_status = "active" if status['configuration_valid'] else "inactive"
                except Exception:
                    article_library_status = "error"
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': db_status,
                'article_library': {
                    'status': article_library_status,
                    'article_count': article_count
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }, 500
    
    @app.route('/health/database')
    def database_health_check():
        """Dedicated database health check endpoint"""
        from datetime import datetime
        import time
        from sqlalchemy import text
        from sqlalchemy.exc import SQLAlchemyError
        
        try:
            start_time = time.time()
            
            # Get database extension
            db = current_app.extensions.get('sqlalchemy')
            if not db:
                return {
                    'status': 'unhealthy',
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': 'Database extension not found',
                    'message': 'SQLAlchemy extension is not properly configured'
                }, 503
            
            # Test SQLAlchemy connection
            connection_status = "healthy"
            connection_error = None
            try:
                # Test basic connection
                result = db.session.execute(text("SELECT 1 as test"))
                result.fetchone()
            except SQLAlchemyError as e:
                connection_status = "unhealthy"
                connection_error = str(e)
            
            # Verify database responsiveness with more complex query
            responsiveness_status = "healthy"
            responsiveness_error = None
            table_count = None
            try:
                # Check if we can query system tables
                result = db.session.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
                table_count = result.fetchone()[0]
            except SQLAlchemyError as e:
                responsiveness_status = "unhealthy"
                responsiveness_error = str(e)
            
            # Check connection pool status
            pool_status = "healthy"
            pool_error = None
            pool_info = {}
            try:
                engine = db.engine
                pool_info = {
                    'pool_size': engine.pool.size(),
                    'checked_in': engine.pool.checkedin(),
                    'checked_out': engine.pool.checkedout(),
                    'overflow': engine.pool.overflow(),
                    'invalid': engine.pool.invalid()
                }
                
                # Check for connection pool issues
                if pool_info['invalid'] > 0:
                    pool_status = "warning"
                    pool_error = f"Found {pool_info['invalid']} invalid connections in pool"
                elif pool_info['checked_out'] > pool_info['pool_size'] * 0.8:
                    pool_status = "warning"
                    pool_error = f"High connection usage: {pool_info['checked_out']}/{pool_info['pool_size']}"
                    
            except Exception as e:
                pool_status = "unhealthy"
                pool_error = str(e)
            
            # Calculate response time
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # Determine overall database health
            overall_status = "healthy"
            if connection_status == "unhealthy" or responsiveness_status == "unhealthy":
                overall_status = "unhealthy"
            elif pool_status == "warning":
                overall_status = "warning"
            
            health_data = {
                'status': overall_status,
                'timestamp': datetime.utcnow().isoformat(),
                'response_time_ms': response_time,
                'connection': {
                    'status': connection_status,
                    'error': connection_error
                },
                'responsiveness': {
                    'status': responsiveness_status,
                    'error': responsiveness_error,
                    'table_count': table_count
                },
                'connection_pool': {
                    'status': pool_status,
                    'error': pool_error,
                    'info': pool_info
                }
            }
            
            # Return appropriate status code
            if overall_status == "healthy":
                return health_data, 200
            elif overall_status == "warning":
                return health_data, 200  # Still healthy but with warnings
            else:
                return health_data, 503
                
        except Exception as e:
            return {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'message': 'Failed to perform database health check'
            }, 500
    
    @app.route('/health/redis')
    def redis_health_check():
        """Dedicated Redis health check endpoint"""
        from datetime import datetime
        import time
        import os
        
        try:
            start_time = time.time()
            
            # Get Redis configuration
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            redis_db = int(os.getenv('REDIS_DB', '0'))
            redis_password = os.getenv('REDIS_PASSWORD')
            
            # Test Redis connectivity
            connectivity_status = "healthy"
            connectivity_error = None
            connectivity_time = None
            
            try:
                import redis
                redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    decode_responses=True
                )
                
                # Test basic connectivity
                conn_start = time.time()
                redis_client.ping()
                connectivity_time = round((time.time() - conn_start) * 1000, 2)
                
            except Exception as e:
                connectivity_status = "unhealthy"
                connectivity_error = str(e)
            
            # Verify cache operations
            cache_status = "healthy"
            cache_error = None
            cache_test_time = None
            
            if connectivity_status == "healthy":
                try:
                    # Test write operation
                    cache_start = time.time()
                    test_key = f"health_check_{int(time.time())}"
                    test_value = "health_check_value"
                    
                    # Write test
                    redis_client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
                    
                    # Read test
                    retrieved_value = redis_client.get(test_key)
                    
                    # Delete test
                    redis_client.delete(test_key)
                    
                    cache_test_time = round((time.time() - cache_start) * 1000, 2)
                    
                    # Verify the operation was successful
                    if retrieved_value != test_value:
                        cache_status = "unhealthy"
                        cache_error = "Cache read/write verification failed"
                        
                except Exception as e:
                    cache_status = "unhealthy"
                    cache_error = str(e)
            else:
                cache_status = "unhealthy"
                cache_error = "Cannot test cache operations - connectivity failed"
            
            # Check Redis memory usage
            memory_status = "healthy"
            memory_error = None
            memory_info = {}
            
            if connectivity_status == "healthy":
                try:
                    # Get Redis info
                    info = redis_client.info()
                    
                    memory_info = {
                        'used_memory_human': info.get('used_memory_human', 'N/A'),
                        'used_memory_peak_human': info.get('used_memory_peak_human', 'N/A'),
                        'used_memory_rss_human': info.get('used_memory_rss_human', 'N/A'),
                        'used_memory_lua_human': info.get('used_memory_lua_human', 'N/A'),
                        'mem_fragmentation_ratio': round(info.get('mem_fragmentation_ratio', 0), 2),
                        'total_connections_received': info.get('total_connections_received', 0),
                        'total_commands_processed': info.get('total_commands_processed', 0),
                        'keyspace_hits': info.get('keyspace_hits', 0),
                        'keyspace_misses': info.get('keyspace_misses', 0),
                        'uptime_in_seconds': info.get('uptime_in_seconds', 0),
                        'connected_clients': info.get('connected_clients', 0)
                    }
                    
                    # Check memory usage thresholds
                    used_memory = info.get('used_memory', 0)
                    max_memory = info.get('maxmemory', 0)
                    
                    if max_memory > 0:
                        memory_usage_percent = (used_memory / max_memory) * 100
                        memory_info['memory_usage_percent'] = round(memory_usage_percent, 2)
                        
                        if memory_usage_percent > 90:
                            memory_status = "warning"
                            memory_error = f"High memory usage: {memory_usage_percent:.1f}%"
                        elif memory_usage_percent > 95:
                            memory_status = "unhealthy"
                            memory_error = f"Critical memory usage: {memory_usage_percent:.1f}%"
                    
                    # Check fragmentation ratio
                    frag_ratio = info.get('mem_fragmentation_ratio', 0)
                    if frag_ratio > 1.5:
                        memory_status = "warning"
                        memory_error = f"High memory fragmentation: {frag_ratio:.2f}"
                        
                except Exception as e:
                    memory_status = "unhealthy"
                    memory_error = str(e)
            else:
                memory_status = "unhealthy"
                memory_error = "Cannot check memory usage - connectivity failed"
            
            # Calculate total response time
            total_response_time = round((time.time() - start_time) * 1000, 2)
            
            # Determine overall Redis health
            overall_status = "healthy"
            if connectivity_status == "unhealthy":
                overall_status = "unhealthy"
            elif cache_status == "unhealthy":
                overall_status = "unhealthy"
            elif memory_status == "unhealthy":
                overall_status = "unhealthy"
            elif memory_status == "warning":
                overall_status = "warning"
            
            health_data = {
                'status': overall_status,
                'timestamp': datetime.utcnow().isoformat(),
                'response_time_ms': total_response_time,
                'connectivity': {
                    'status': connectivity_status,
                    'error': connectivity_error,
                    'response_time_ms': connectivity_time,
                    'host': redis_host,
                    'port': redis_port,
                    'db': redis_db
                },
                'cache_operations': {
                    'status': cache_status,
                    'error': cache_error,
                    'response_time_ms': cache_test_time
                },
                'memory_usage': {
                    'status': memory_status,
                    'error': memory_error,
                    'info': memory_info
                }
            }
            
            # Return appropriate status code
            if overall_status == "healthy":
                return health_data, 200
            elif overall_status == "warning":
                return health_data, 200  # Still healthy but with warnings
            else:
                return health_data, 503
                
        except Exception as e:
            return {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'message': 'Failed to perform Redis health check'
            }, 500
    
    # Only register external health once
    if 'external_services_health_check' not in app.view_functions:
        @app.route('/health/external')
        def external_services_health_check():
            """Dedicated external services health check endpoint"""
        from datetime import datetime
        import time
        import os
        import requests
        
        try:
            start_time = time.time()
            
            external_services = {}
            
            # Check Supabase API connectivity
            supabase_status = "healthy"
            supabase_error = None
            supabase_response_time = None
            
            try:
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_ANON_KEY')
                
                if supabase_url and supabase_key:
                    # Test Supabase health endpoint or basic connectivity
                    supabase_start = time.time()
                    headers = {
                        'apikey': supabase_key,
                        'Authorization': f'Bearer {supabase_key}'
                    }
                    
                    # Try to access a simple endpoint (health check or basic query)
                    response = requests.get(
                        f"{supabase_url}/rest/v1/", 
                        headers=headers, 
                        timeout=10
                    )
                    supabase_response_time = round((time.time() - supabase_start) * 1000, 2)
                    
                    if response.status_code not in [200, 401]:  # 401 is expected for health check
                        supabase_status = "unhealthy"
                        supabase_error = f"HTTP {response.status_code}"
                else:
                    supabase_status = "not_configured"
                    supabase_error = "Supabase credentials not configured"
                    
            except Exception as e:
                supabase_status = "unhealthy"
                supabase_error = str(e)
            
            external_services['supabase_api'] = {
                'status': supabase_status,
                'response_time_ms': supabase_response_time,
                'error': supabase_error
            }
            
            # Check Stripe API status
            stripe_status = "healthy"
            stripe_error = None
            stripe_response_time = None
            
            try:
                stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
                
                if stripe_secret_key:
                    import stripe
                    stripe.api_key = stripe_secret_key
                    
                    # Test Stripe API connectivity
                    stripe_start = time.time()
                    try:
                        # Get account information (lightweight operation)
                        account = stripe.Account.retrieve()
                        stripe_response_time = round((time.time() - stripe_start) * 1000, 2)
                    except stripe.error.AuthenticationError:
                        # Authentication error is expected for health check
                        stripe_response_time = round((time.time() - stripe_start) * 1000, 2)
                    except Exception as e:
                        stripe_status = "unhealthy"
                        stripe_error = str(e)
                else:
                    stripe_status = "not_configured"
                    stripe_error = "Stripe API key not configured"
                    
            except Exception as e:
                stripe_status = "unhealthy"
                stripe_error = str(e)
            
            external_services['stripe_api'] = {
                'status': stripe_status,
                'response_time_ms': stripe_response_time,
                'error': stripe_error
            }
            
            # Check Email service (Resend) status
            resend_status = "healthy"
            resend_error = None
            resend_response_time = None
            
            try:
                resend_api_key = os.getenv('RESEND_API_KEY')
                
                if resend_api_key:
                    # Test Resend API connectivity
                    resend_start = time.time()
                    headers = {
                        'Authorization': f'Bearer {resend_api_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    # Try to get domains (lightweight operation)
                    response = requests.get(
                        'https://api.resend.com/domains',
                        headers=headers,
                        timeout=10
                    )
                    resend_response_time = round((time.time() - resend_start) * 1000, 2)
                    
                    if response.status_code not in [200, 401, 403]:  # Expected responses
                        resend_status = "unhealthy"
                        resend_error = f"HTTP {response.status_code}"
                else:
                    resend_status = "not_configured"
                    resend_error = "Resend API key not configured"
                    
            except Exception as e:
                resend_status = "unhealthy"
                resend_error = str(e)
            
            external_services['email_service_resend'] = {
                'status': resend_status,
                'response_time_ms': resend_response_time,
                'error': resend_error
            }
            
            # Check SMS service (Twilio) status
            twilio_status = "healthy"
            twilio_error = None
            twilio_response_time = None
            
            try:
                twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
                twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
                
                if twilio_account_sid and twilio_auth_token:
                    # Test Twilio API connectivity
                    twilio_start = time.time()
                    import base64
                    
                    # Create basic auth header
                    auth_string = f"{twilio_account_sid}:{twilio_auth_token}"
                    auth_bytes = auth_string.encode('ascii')
                    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
                    
                    headers = {
                        'Authorization': f'Basic {auth_b64}',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                    
                    # Try to get account information (lightweight operation)
                    response = requests.get(
                        f'https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}.json',
                        headers=headers,
                        timeout=10
                    )
                    twilio_response_time = round((time.time() - twilio_start) * 1000, 2)
                    
                    if response.status_code not in [200, 401]:  # Expected responses
                        twilio_status = "unhealthy"
                        twilio_error = f"HTTP {response.status_code}"
                else:
                    twilio_status = "not_configured"
                    twilio_error = "Twilio credentials not configured"
                    
            except Exception as e:
                twilio_status = "unhealthy"
                twilio_error = str(e)
            
            external_services['sms_service_twilio'] = {
                'status': twilio_status,
                'response_time_ms': twilio_response_time,
                'error': twilio_error
            }
            
            # Calculate total response time
            total_response_time = round((time.time() - start_time) * 1000, 2)
            
            # Determine overall external services health
            unhealthy_services = []
            not_configured_services = []
            
            for service_name, service_data in external_services.items():
                if service_data['status'] == 'unhealthy':
                    unhealthy_services.append(service_name)
                elif service_data['status'] == 'not_configured':
                    not_configured_services.append(service_name)
            
            # Determine overall status
            if unhealthy_services:
                overall_status = "unhealthy"
            elif not_configured_services and len(not_configured_services) == len(external_services):
                overall_status = "not_configured"
            else:
                overall_status = "healthy"
            
            health_data = {
                'status': overall_status,
                'timestamp': datetime.utcnow().isoformat(),
                'response_time_ms': total_response_time,
                'services': external_services,
                'unhealthy_services': unhealthy_services,
                'not_configured_services': not_configured_services,
                'summary': {
                    'total_services': len(external_services),
                    'healthy_services': len([s for s in external_services.values() if s['status'] == 'healthy']),
                    'unhealthy_services': len(unhealthy_services),
                    'not_configured_services': len(not_configured_services)
                }
            }
            
            # Return appropriate status code
            if overall_status == "healthy":
                return health_data, 200
            elif overall_status == "not_configured":
                return health_data, 200  # Still healthy but not configured
            else:
                return health_data, 503
                
        except Exception as e:
            return {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'message': 'Failed to perform external services health check'
            }, 500
    
    @app.route('/health/external')
    def external_services_health_check():
        """Dedicated external services health check endpoint"""
        from datetime import datetime
        import time
        import os
        import requests
        
        try:
            start_time = time.time()
            
            # Initialize services status
            services_status = {}
            
            # Check Supabase API connectivity
            supabase_status = "healthy"
            supabase_error = None
            supabase_response_time = None
            
            try:
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_ANON_KEY')
                
                if supabase_url and supabase_key:
                    supabase_start = time.time()
                    
                    # Test Supabase health endpoint or basic connectivity
                    headers = {
                        'apikey': supabase_key,
                        'Authorization': f'Bearer {supabase_key}'
                    }
                    
                    # Try to access a simple endpoint
                    response = requests.get(
                        f"{supabase_url}/rest/v1/",
                        headers=headers,
                        timeout=10
                    )
                    
                    supabase_response_time = round((time.time() - supabase_start) * 1000, 2)
                    
                    if response.status_code in [200, 401]:  # 401 is expected without proper auth
                        supabase_status = "healthy"
                    else:
                        supabase_status = "unhealthy"
                        supabase_error = f"HTTP {response.status_code}"
                        
                else:
                    supabase_status = "not_configured"
                    supabase_error = "Supabase URL or key not configured"
                    
            except Exception as e:
                supabase_status = "unhealthy"
                supabase_error = str(e)
            
            services_status['supabase'] = {
                'status': supabase_status,
                'error': supabase_error,
                'response_time_ms': supabase_response_time
            }
            
            # Check Stripe API status
            stripe_status = "healthy"
            stripe_error = None
            stripe_response_time = None
            
            try:
                stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
                
                if stripe_secret_key:
                    stripe_start = time.time()
                    
                    # Test Stripe API connectivity
                    headers = {
                        'Authorization': f'Bearer {stripe_secret_key}',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                    
                    # Try to get account information (lightweight operation)
                    response = requests.get(
                        'https://api.stripe.com/v1/account',
                        headers=headers,
                        timeout=10
                    )
                    
                    stripe_response_time = round((time.time() - stripe_start) * 1000, 2)
                    
                    if response.status_code == 200:
                        stripe_status = "healthy"
                    else:
                        stripe_status = "unhealthy"
                        stripe_error = f"HTTP {response.status_code}: {response.text[:100]}"
                        
                else:
                    stripe_status = "not_configured"
                    stripe_error = "Stripe secret key not configured"
                    
            except Exception as e:
                stripe_status = "unhealthy"
                stripe_error = str(e)
            
            services_status['stripe'] = {
                'status': stripe_status,
                'error': stripe_error,
                'response_time_ms': stripe_response_time
            }
            
            # Check Email service (Resend) status
            resend_status = "healthy"
            resend_error = None
            resend_response_time = None
            
            try:
                resend_api_key = os.getenv('RESEND_API_KEY')
                
                if resend_api_key:
                    resend_start = time.time()
                    
                    # Test Resend API connectivity
                    headers = {
                        'Authorization': f'Bearer {resend_api_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    # Try to get domains (lightweight operation)
                    response = requests.get(
                        'https://api.resend.com/domains',
                        headers=headers,
                        timeout=10
                    )
                    
                    resend_response_time = round((time.time() - resend_start) * 1000, 2)
                    
                    if response.status_code in [200, 401]:  # 401 is expected without proper setup
                        resend_status = "healthy"
                    else:
                        resend_status = "unhealthy"
                        resend_error = f"HTTP {response.status_code}: {response.text[:100]}"
                        
                else:
                    resend_status = "not_configured"
                    resend_error = "Resend API key not configured"
                    
            except Exception as e:
                resend_status = "unhealthy"
                resend_error = str(e)
            
            services_status['resend'] = {
                'status': resend_status,
                'error': resend_error,
                'response_time_ms': resend_response_time
            }
            
            # Check SMS service (Twilio) status
            twilio_status = "healthy"
            twilio_error = None
            twilio_response_time = None
            
            try:
                twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
                twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
                
                if twilio_account_sid and twilio_auth_token:
                    twilio_start = time.time()
                    
                    # Test Twilio API connectivity
                    import base64
                    auth_string = f"{twilio_account_sid}:{twilio_auth_token}"
                    auth_bytes = auth_string.encode('ascii')
                    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
                    
                    headers = {
                        'Authorization': f'Basic {auth_b64}',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                    
                    # Try to get account information (lightweight operation)
                    response = requests.get(
                        f'https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}.json',
                        headers=headers,
                        timeout=10
                    )
                    
                    twilio_response_time = round((time.time() - twilio_start) * 1000, 2)
                    
                    if response.status_code == 200:
                        twilio_status = "healthy"
                    else:
                        twilio_status = "unhealthy"
                        twilio_error = f"HTTP {response.status_code}: {response.text[:100]}"
                        
                else:
                    twilio_status = "not_configured"
                    twilio_error = "Twilio credentials not configured"
                    
            except Exception as e:
                twilio_status = "unhealthy"
                twilio_error = str(e)
            
            services_status['twilio'] = {
                'status': twilio_status,
                'error': twilio_error,
                'response_time_ms': twilio_response_time
            }
            
            # Calculate total response time
            total_response_time = round((time.time() - start_time) * 1000, 2)
            
            # Determine overall external services health
            critical_services = ['supabase', 'stripe']  # Define critical services
            unhealthy_services = []
            warning_services = []
            
            for service_name, service_data in services_status.items():
                if service_data['status'] == 'unhealthy':
                    unhealthy_services.append(service_name)
                elif service_data['status'] == 'not_configured':
                    warning_services.append(service_name)
            
            # Check if any critical services are unhealthy
            critical_failures = [service for service in unhealthy_services if service in critical_services]
            
            if critical_failures:
                overall_status = "unhealthy"
            elif unhealthy_services:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            health_data = {
                'status': overall_status,
                'timestamp': datetime.utcnow().isoformat(),
                'response_time_ms': total_response_time,
                'services': services_status,
                'unhealthy_services': unhealthy_services,
                'warning_services': warning_services,
                'critical_services_failing': len(critical_failures) > 0
            }
            
            # Return appropriate status code
            if overall_status == "healthy":
                return health_data, 200
            elif overall_status == "warning":
                return health_data, 200  # Still healthy but with warnings
            else:
                return health_data, 503
                
        except Exception as e:
            return {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'message': 'Failed to perform external services health check'
            }, 500
    
    if 'standard_health_check' not in app.view_functions:
        @app.route('/health/standard')
        @health_check_timer('standard', 'overall')
        def standard_health_check():
            """Standardized health check endpoint with consistent response format"""
        from datetime import datetime
        import time
        import os
        import requests
        
        try:
            start_time = time.time()
            
            # Initialize checks
            checks = {}
            
            # Check database
            db_status = "healthy"
            db_response_time = None
            try:
                from sqlalchemy import text
                db = current_app.extensions.get('sqlalchemy')
                if db:
                    db_start = time.time()
                    result = db.session.execute(text("SELECT 1 as test"))
                    result.fetchone()
                    db_response_time = round((time.time() - db_start) * 1000, 2)
                    record_health_check_success('standard', 'database')
                    # Update database metrics
                    update_database_metrics(db)
                else:
                    db_status = "unhealthy"
                    record_health_check_failure('standard', 'database', 'NoDatabaseConnection')
            except Exception as e:
                db_status = "unhealthy"
                record_health_check_failure('standard', 'database', type(e).__name__)
            
            checks['database'] = {
                "status": db_status,
                "response_time": db_response_time
            }
            
            # Check Redis
            redis_status = "healthy"
            redis_response_time = None
            try:
                import redis
                redis_host = os.getenv('REDIS_HOST', 'localhost')
                redis_port = int(os.getenv('REDIS_PORT', '6379'))
                redis_client = redis.Redis(host=redis_host, port=redis_port, socket_connect_timeout=2)
                redis_start = time.time()
                redis_client.ping()
                redis_response_time = round((time.time() - redis_start) * 1000, 2)
                record_health_check_success('standard', 'redis')
                # Update Redis metrics
                update_redis_metrics(redis_client)
            except Exception as e:
                redis_status = "unhealthy"
                record_health_check_failure('standard', 'redis', type(e).__name__)
            
            checks['redis'] = {
                "status": redis_status,
                "response_time": redis_response_time
            }
            
            # Check external APIs
            external_apis = {}
            
            # Check Supabase
            supabase_status = "healthy"
            try:
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_ANON_KEY')
                
                if supabase_url and supabase_key:
                    headers = {
                        'apikey': supabase_key,
                        'Authorization': f'Bearer {supabase_key}'
                    }
                    response = requests.get(
                        f"{supabase_url}/rest/v1/",
                        headers=headers,
                        timeout=5
                    )
                    if response.status_code not in [200, 401]:
                        supabase_status = "unhealthy"
                        record_health_check_failure('standard', 'supabase', f'HTTP{response.status_code}')
                    else:
                        record_health_check_success('standard', 'supabase')
                else:
                    supabase_status = "unhealthy"
                    record_health_check_failure('standard', 'supabase', 'MissingCredentials')
            except Exception as e:
                supabase_status = "unhealthy"
                record_health_check_failure('standard', 'supabase', type(e).__name__)
            
            external_apis['supabase'] = {"status": supabase_status}
            
            # Check Stripe
            stripe_status = "healthy"
            try:
                stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
                
                if stripe_secret_key:
                    headers = {
                        'Authorization': f'Bearer {stripe_secret_key}',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                    response = requests.get(
                        'https://api.stripe.com/v1/alerting_rules',
                        headers=headers,
                        timeout=5
                    )
                    if response.status_code != 200:
                        stripe_status = "unhealthy"
                        record_health_check_failure('standard', 'stripe', f'HTTP{response.status_code}')
                    else:
                        record_health_check_success('standard', 'stripe')
                else:
                    stripe_status = "unhealthy"
                    record_health_check_failure('standard', 'stripe', 'MissingCredentials')
            except Exception as e:
                stripe_status = "unhealthy"
                record_health_check_failure('standard', 'stripe', type(e).__name__)
            
            external_apis['stripe'] = {"status": stripe_status}
            
            checks['external_apis'] = external_apis
            
            # Update system metrics
            update_system_metrics()
            
            # Determine overall status
            all_checks = [db_status, redis_status, supabase_status, stripe_status]
            
            if all(status == "healthy" for status in all_checks):
                overall_status = "healthy"
            elif any(status == "unhealthy" for status in all_checks):
                overall_status = "unhealthy"
            else:
                overall_status = "degraded"
            
            # Get application version
            version = getattr(current_app, 'version', '1.0.0')
            
            response_data = {
                "status": overall_status,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "version": version,
                "checks": checks
            }
            
            # Return appropriate status code
            if overall_status == "healthy":
                return response_data, 200
            elif overall_status == "degraded":
                return response_data, 200  # Still healthy but with warnings
            else:
                return response_data, 503
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "version": getattr(current_app, 'version', '1.0.0'),
                "checks": {},
                "error": str(e)
            }, 500
    
    if 'metrics_health_check' not in app.view_functions:
        @app.route('/health/metrics')
        def metrics_health_check():
            """Health check endpoint with comprehensive Prometheus metrics"""
        from datetime import datetime
        import time
        import os
        import requests
        
        try:
            start_time = time.time()
            
            # Initialize metrics data
            metrics_data = {
                "status": "healthy",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "version": getattr(current_app, 'version', '1.0.0'),
                "response_time_ms": 0,
                "checks": {},
                "metrics": {
                    "health_check_duration_seconds": {},
                    "health_check_failures_total": {},
                    "health_check_status": {},
                    "system_metrics": {},
                    "database_metrics": {},
                    "redis_metrics": {}
                }
            }
            
            # Database check with metrics
            db_start = time.time()
            try:
                from sqlalchemy import text
                db = current_app.extensions.get('sqlalchemy')
                if db:
                    result = db.session.execute(text("SELECT 1 as test"))
                    result.fetchone()
                    db_duration = time.time() - db_start
                    record_health_check_success('metrics', 'database')
                    update_database_metrics(db)
                    
                    metrics_data['checks']['database'] = {
                        "status": "healthy",
                        "response_time_ms": round(db_duration * 1000, 2)
                    }
                    metrics_data['metrics']['database_metrics'] = {
                        "connection_pool_size": getattr(db.engine.pool, 'size', 0),
                        "connections_checked_out": getattr(db.engine.pool, 'checkedout', 0)
                    }
                else:
                    record_health_check_failure('metrics', 'database', 'NoDatabaseConnection')
                    metrics_data['checks']['database'] = {"status": "unhealthy"}
            except Exception as e:
                record_health_check_failure('metrics', 'database', type(e).__name__)
                metrics_data['checks']['database'] = {"status": "unhealthy", "error": str(e)}
            
            # Redis check with metrics
            redis_start = time.time()
            try:
                import redis
                redis_host = os.getenv('REDIS_HOST', 'localhost')
                redis_port = int(os.getenv('REDIS_PORT', '6379'))
                redis_client = redis.Redis(host=redis_host, port=redis_port, socket_connect_timeout=2)
                redis_client.ping()
                redis_duration = time.time() - redis_start
                record_health_check_success('metrics', 'redis')
                
                # Get Redis info
                redis_info = redis_client.info()
                update_redis_metrics(redis_client)
                
                metrics_data['checks']['redis'] = {
                    "status": "healthy",
                    "response_time_ms": round(redis_duration * 1000, 2)
                }
                metrics_data['metrics']['redis_metrics'] = {
                    "memory_usage_bytes": redis_info.get('used_memory', 0),
                    "connected_clients": redis_info.get('connected_clients', 0),
                    "total_commands_processed": redis_info.get('total_commands_processed', 0)
                }
            except Exception as e:
                record_health_check_failure('metrics', 'redis', type(e).__name__)
                metrics_data['checks']['redis'] = {"status": "unhealthy", "error": str(e)}
            
            # External APIs check with metrics
            external_apis = {}
            
            # Supabase check
            supabase_start = time.time()
            try:
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_ANON_KEY')
                
                if supabase_url and supabase_key:
                    headers = {
                        'apikey': supabase_key,
                        'Authorization': f'Bearer {supabase_key}'
                    }
                    response = requests.get(
                        f"{supabase_url}/rest/v1/",
                        headers=headers,
                        timeout=5
                    )
                    supabase_duration = time.time() - supabase_start
                    
                    if response.status_code in [200, 401]:
                        record_health_check_success('metrics', 'supabase')
                        external_apis['supabase'] = {
                            "status": "healthy",
                            "response_time_ms": round(supabase_duration * 1000, 2)
                        }
                    else:
                        record_health_check_failure('metrics', 'supabase', f'HTTP{response.status_code}')
                        external_apis['supabase'] = {"status": "unhealthy"}
                else:
                    record_health_check_failure('metrics', 'supabase', 'MissingCredentials')
                    external_apis['supabase'] = {"status": "unhealthy"}
            except Exception as e:
                record_health_check_failure('metrics', 'supabase', type(e).__name__)
                external_apis['supabase'] = {"status": "unhealthy", "error": str(e)}
            
            # Stripe check
            stripe_start = time.time()
            try:
                stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
                
                if stripe_secret_key:
                    headers = {
                        'Authorization': f'Bearer {stripe_secret_key}',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                    response = requests.get(
                        'https://api.stripe.com/v1/alerting_rules',
                        headers=headers,
                        timeout=5
                    )
                    stripe_duration = time.time() - stripe_start
                    
                    if response.status_code == 200:
                        record_health_check_success('metrics', 'stripe')
                        external_apis['stripe'] = {
                            "status": "healthy",
                            "response_time_ms": round(stripe_duration * 1000, 2)
                        }
                    else:
                        record_health_check_failure('metrics', 'stripe', f'HTTP{response.status_code}')
                        external_apis['stripe'] = {"status": "unhealthy"}
                else:
                    record_health_check_failure('metrics', 'stripe', 'MissingCredentials')
                    external_apis['stripe'] = {"status": "unhealthy"}
            except Exception as e:
                record_health_check_failure('metrics', 'stripe', type(e).__name__)
                external_apis['stripe'] = {"status": "unhealthy", "error": str(e)}
            
            metrics_data['checks']['external_apis'] = external_apis
            
            # System metrics
            try:
                import psutil
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=0.1)
                disk = psutil.disk_usage('/')
                
                update_system_metrics()
                
                metrics_data['metrics']['system_metrics'] = {
                    "memory_total_bytes": memory.total,
                    "memory_available_bytes": memory.available,
                    "memory_used_bytes": memory.used,
                    "memory_percent": memory.percent,
                    "cpu_percent": cpu_percent,
                    "disk_used_bytes": disk.used,
                    "disk_total_bytes": disk.total,
                    "disk_percent": (disk.used / disk.total) * 100
                }
            except Exception as e:
                metrics_data['metrics']['system_metrics'] = {"error": str(e)}
            
            # Calculate overall response time
            total_duration = time.time() - start_time
            metrics_data['response_time_ms'] = round(total_duration * 1000, 2)
            
            # Determine overall status
            all_checks = []
            for check_group in metrics_data['checks'].values():
                if isinstance(check_group, dict):
                    if 'status' in check_group:
                        all_checks.append(check_group['status'])
                    else:
                        for service in check_group.values():
                            if isinstance(service, dict) and 'status' in service:
                                all_checks.append(service['status'])
            
            if all(status == "healthy" for status in all_checks):
                metrics_data['status'] = "healthy"
                return metrics_data, 200
            elif any(status == "unhealthy" for status in all_checks):
                metrics_data['status'] = "unhealthy"
                return metrics_data, 503
            else:
                metrics_data['status'] = "degraded"
                return metrics_data, 200
                
        except Exception as e:
            record_health_check_failure('metrics', 'overall', type(e).__name__)
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "version": getattr(current_app, 'version', '1.0.0'),
                "checks": {},
                "metrics": {},
                "error": str(e)
            }, 500

def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers
    
    Args:
        app: Flask application instance
    """
    
    # Add rate limiting error handler for article library
    @app.errorhandler(429)
    def rate_limit_handler(e):
        return {
            'error': 'Rate limit exceeded',
            'message': str(e.description) if hasattr(e, 'description') else 'Too many requests',
            'retry_after': getattr(e, 'retry_after', None)
        }, 429
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
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
    """Get UserService instance"""
    return None

def get_onboarding_service() -> Optional[OnboardingService]:
    """Get OnboardingService instance"""
    return None

def get_audit_service() -> Optional[AuditService]:
    """Get AuditService instance"""
    return None

def get_verification_service() -> Optional[VerificationService]:
    """Get VerificationService instance"""
    return None

def get_db_session():
    """Get database session"""
    return None 