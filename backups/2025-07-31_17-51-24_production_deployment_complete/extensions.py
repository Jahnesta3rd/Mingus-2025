"""
Flask extensions for MINGUS application
Initializes all extensions used throughout the application
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from flask_talisman import Talisman
from flask_caching import Cache

# Database
db = SQLAlchemy()

# Migrations
migrate = Migrate()

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Compression
compress = Compress()

# Security headers
talisman = Talisman()

# Caching
cache = Cache()

# Celery (will be initialized in celery_app.py)
celery = None

def init_extensions(app):
    """Initialize all Flask extensions"""
    # Database
    db.init_app(app)
    
    # Migrations
    migrate.init_app(app, db)
    
    # Rate limiting
    limiter.init_app(app)
    
    # Compression
    compress.init_app(app)
    
    # Security headers
    talisman.init_app(app)
    
    # Caching
    cache.init_app(app)
    
    # Initialize Celery
    init_celery(app)

def init_celery(app):
    """Initialize Celery with Flask app context"""
    from celery import Celery
    
    celery_app = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND'),
        broker=app.config.get('CELERY_BROKER_URL')
    )
    
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,
        task_soft_time_limit=25 * 60,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        broker_connection_retry_on_startup=True,
        result_expires=3600,
        task_ignore_result=False,
        task_eager_propagates=True,
    )
    
    # Set Flask app context
    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery_app.Task = ContextTask
    
    # Store celery instance globally
    global celery
    celery = celery_app
    
    return celery_app 