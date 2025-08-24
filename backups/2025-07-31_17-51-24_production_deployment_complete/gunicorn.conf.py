"""
Gunicorn Configuration for MINGUS Production Deployment
Optimized for high-performance Flask application with proper worker management
"""

import os
import multiprocessing
from datetime import datetime

# =====================================================
# SERVER SOCKET CONFIGURATION
# =====================================================

# Server socket
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:5002')
backlog = int(os.getenv('GUNICORN_BACKLOG', 2048))

# =====================================================
# WORKER PROCESSES CONFIGURATION
# =====================================================

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'gevent')
worker_connections = int(os.getenv('GUNICORN_WORKER_CONNECTIONS', 1000))

# Worker lifecycle
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', 1000))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', 100))
worker_tmp_dir = os.getenv('GUNICORN_WORKER_TMP_DIR', '/dev/shm')

# Worker timeout settings
timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', 2))
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', 30))

# =====================================================
# PERFORMANCE OPTIMIZATION
# =====================================================

# Preload application for better performance
preload_app = True

# Worker process naming
worker_tmp_dir = '/dev/shm'
worker_exit_on_app_exit = False

# Memory management
max_requests_jitter = 100
worker_abort_on_exit = False

# =====================================================
# LOGGING CONFIGURATION
# =====================================================

# Access log
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '/app/logs/gunicorn_access.log')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Error log
errorlog = os.getenv('GUNICORN_ERROR_LOG', '/app/logs/gunicorn_error.log')
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# Log rotation
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s %(L)s'

# =====================================================
# SECURITY CONFIGURATION
# =====================================================

# User and group
user = os.getenv('GUNICORN_USER', 'mingus')
group = os.getenv('GUNICORN_GROUP', 'mingus')

# Process naming
proc_name = 'mingus-gunicorn'

# =====================================================
# SSL/TLS CONFIGURATION (if using SSL)
# =====================================================

# SSL configuration (uncomment if using SSL)
# keyfile = os.getenv('SSL_KEYFILE', '/app/ssl/private.key')
# certfile = os.getenv('SSL_CERTFILE', '/app/ssl/certificate.crt')
# ca_certs = os.getenv('SSL_CA_CERTS', '/app/ssl/ca_bundle.crt')

# =====================================================
# APPLICATION HOOKS
# =====================================================

def when_ready(server):
    """Called just after the server is started"""
    server.log.info(f"Server is ready. Spawning {workers} workers")

def on_starting(server):
    """Called just before the master process is initialized"""
    server.log.info("Starting MINGUS Gunicorn server")

def on_reload(server):
    """Called to reload the server"""
    server.log.info("Reloading MINGUS Gunicorn server")

def worker_int(worker):
    """Called just after a worker has been initialized"""
    worker.log.info(f"Worker {worker.pid} initialized")

def pre_fork(server, worker):
    """Called just before a worker has been forked"""
    server.log.info(f"Worker {worker.pid} will be spawned")

def post_fork(server, worker):
    """Called just after a worker has been forked"""
    server.log.info(f"Worker {worker.pid} spawned")

def post_worker_init(worker):
    """Called just after a worker has initialized the application"""
    worker.log.info(f"Worker {worker.pid} initialized application")

def worker_abort(worker):
    """Called when a worker received SIGABRT signal"""
    worker.log.info(f"Worker {worker.pid} received SIGABRT")

def pre_exec(server):
    """Called just before a new master process is forked"""
    server.log.info("New master process will be forked")

def child_exit(server, worker):
    """Called when a worker has been exited"""
    server.log.info(f"Worker {worker.pid} exited")

def worker_exit(server, worker):
    """Called when a worker has been exited, in callable worker"""
    server.log.info(f"Worker {worker.pid} exited")

def nworkers_changed(server, new_value, old_value):
    """Called when the number of workers has been changed"""
    server.log.info(f"Number of workers changed from {old_value} to {new_value}")

def on_exit(server):
    """Called just before exiting Gunicorn"""
    server.log.info("MINGUS Gunicorn server shutting down")

# =====================================================
# CUSTOM SETTINGS FOR MINGUS
# =====================================================

# Health check endpoint
def health_check(environ, start_response):
    """Custom health check for MINGUS application"""
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [b'OK']

# Request ID tracking
def add_request_id(environ, start_response):
    """Add request ID to environment"""
    import uuid
    environ['HTTP_X_REQUEST_ID'] = str(uuid.uuid4())
    return None

# =====================================================
# ENVIRONMENT-SPECIFIC OVERRIDES
# =====================================================

# Production-specific settings
if os.getenv('FLASK_ENV') == 'production':
    # Increase workers for production
    workers = max(workers, 4)
    
    # Enable more detailed logging
    loglevel = 'info'
    
    # Increase timeout for complex operations
    timeout = 180
    
    # Enable request tracking
    enable_stdio_inheritance = True

# Development-specific settings
elif os.getenv('FLASK_ENV') == 'development':
    # Reduce workers for development
    workers = 2
    
    # More verbose logging
    loglevel = 'debug'
    
    # Shorter timeout for faster development cycle
    timeout = 60

# =====================================================
# MONITORING AND METRICS
# =====================================================

# Enable statsd for metrics (if available)
statsd_host = os.getenv('STATSD_HOST')
statsd_port = int(os.getenv('STATSD_PORT', 8125))
statsd_prefix = os.getenv('STATSD_PREFIX', 'mingus.gunicorn')

# =====================================================
# FINAL CONFIGURATION VALIDATION
# =====================================================

# Validate configuration
if workers < 1:
    workers = 1

if timeout < 30:
    timeout = 30

if max_requests < 1:
    max_requests = 1000

# Log final configuration
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"MINGUS Gunicorn Configuration:")
logger.info(f"  Workers: {workers}")
logger.info(f"  Worker Class: {worker_class}")
logger.info(f"  Bind: {bind}")
logger.info(f"  Timeout: {timeout}")
logger.info(f"  Max Requests: {max_requests}")
logger.info(f"  Preload App: {preload_app}") 