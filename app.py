#!/usr/bin/env python3
"""
Mingus Personal Finance App - Main Application
Integrated Flask application with all API endpoints and security features
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import API blueprints
from backend.api.assessment_endpoints import assessment_api
from backend.api.meme_endpoints import meme_api
from backend.api.user_preferences_endpoints import user_preferences_api
from backend.api.profile_endpoints import profile_api
from backend.api.resume_endpoints import resume_api
from backend.api.job_matching_endpoints import job_matching_api
from backend.api.three_tier_endpoints import three_tier_api
from backend.api.recommendation_engine_endpoints import recommendation_engine_api
from backend.api.referral_gated_endpoints import referral_gated_api
from backend.api.unified_risk_analytics_api import risk_analytics_api
from backend.api.vehicle_endpoints import vehicle_api
from backend.api.vehicle_management_api import vehicle_management_api
from backend.api.vehicle_setup_endpoints import vehicle_setup_api

# Import security middleware
from backend.middleware.security import SecurityMiddleware

# Import SQLAlchemy models and database
from backend.models.database import init_database

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration from environment variables
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'your-secret-key-change-this'),
    CSRF_SECRET_KEY=os.environ.get('CSRF_SECRET_KEY', 'your-csrf-secret-key'),
    ENCRYPTION_KEY=os.environ.get('ENCRYPTION_KEY', 'your-encryption-key'),
    RATE_LIMIT_PER_MINUTE=int(os.environ.get('RATE_LIMIT_PER_MINUTE', '100')),
    DB_ENCRYPTION_ENABLED=os.environ.get('DB_ENCRYPTION_ENABLED', 'true').lower() == 'true',
    LOG_SENSITIVE_DATA=os.environ.get('LOG_SENSITIVE_DATA', 'false').lower() == 'true'
)

# Configure CORS for all endpoints including new assessment endpoints
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000').split(',')
CORS_METHODS = os.environ.get('CORS_METHODS', 'GET,POST,PUT,DELETE,OPTIONS').split(',')
CORS_HEADERS = os.environ.get('CORS_HEADERS', 'Content-Type,Authorization,X-CSRF-Token,X-Requested-With').split(',')

CORS(app, 
     origins=CORS_ORIGINS,
     methods=CORS_METHODS,
     allow_headers=CORS_HEADERS,
     supports_credentials=True,
     expose_headers=['X-CSRF-Token'])

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{app.config['RATE_LIMIT_PER_MINUTE']} per minute"],
    storage_uri=os.environ.get('RATE_LIMIT_STORAGE_URL', 'memory://')
)

# Register API blueprints
app.register_blueprint(assessment_api)
app.register_blueprint(meme_api)
app.register_blueprint(user_preferences_api)
app.register_blueprint(profile_api)
app.register_blueprint(resume_api)
app.register_blueprint(job_matching_api)
app.register_blueprint(three_tier_api)
app.register_blueprint(recommendation_engine_api)
app.register_blueprint(referral_gated_api)
app.register_blueprint(risk_analytics_api)
app.register_blueprint(vehicle_api)
app.register_blueprint(vehicle_management_api)
app.register_blueprint(vehicle_setup_api)

# Import and register gas price API
from backend.api.gas_price_endpoints import gas_price_api
app.register_blueprint(gas_price_api)

# Initialize SQLAlchemy database
init_database(app)

# Initialize security middleware
security_middleware = SecurityMiddleware(app)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': os.environ.get('TIMESTAMP', 'unknown'),
        'version': '1.0.0',
        'services': {
            'database': 'connected',
            'sqlalchemy_models': 'active',
            'vehicle_management': 'active',
            'vehicle_management_api': 'active',
            'assessment_api': 'active',
            'meme_api': 'active',
            'user_preferences_api': 'active',
            'job_matching_api': 'active',
            'three_tier_api': 'active',
            'recommendation_engine_api': 'active',
            'risk_analytics_api': 'active'
        }
    })

# API status endpoint
@app.route('/api/status', methods=['GET'])
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'operational',
        'endpoints': {
            'assessments': {
                'submit': '/api/assessments',
                'results': '/api/assessments/<id>/results',
                'analytics': '/api/assessments/analytics'
            },
            'memes': {
                'get_meme': '/api/user-meme',
                'analytics': '/api/meme-analytics',
                'stats': '/api/meme-stats'
            },
            'user_preferences': {
                'get': '/api/user-preferences',
                'update': '/api/user-preferences'
            },
            'job_matching': {
                'search': '/api/job-matching/search',
                'msa_targeting': '/api/job-matching/msa-targeting',
                'remote_detection': '/api/job-matching/remote-detection'
            },
            'three_tier_recommendations': {
                'recommendations': '/api/three-tier/recommendations',
                'tier_specific': '/api/three-tier/tier/{tier_name}',
                'job_analysis': '/api/three-tier/job/{job_id}/analysis',
                'tiers_summary': '/api/three-tier/tiers/summary',
                'skills_gap': '/api/three-tier/skills/gap-analysis'
            },
            'recommendation_engine': {
                'process_resume': '/api/recommendations/process-resume',
                'status': '/api/recommendations/status/{session_id}',
                'analytics': '/api/recommendations/analytics',
                'performance': '/api/recommendations/performance',
                'health': '/api/recommendations/health',
                'cache_clear': '/api/recommendations/cache/clear',
                'session_results': '/api/recommendations/sessions/{session_id}/results'
            },
            'referral_gated': {
                'career_preview': '/career-preview',
                'refer_friend': '/refer-friend',
                'referral_status': '/referral-status/{referral_code}',
                'career_advancement': '/career-advancement',
                'feature_access': '/api/feature-access/job-recommendations',
                'upload_resume': '/upload-resume',
                'location_preferences': '/set-location-preferences',
                'process_recommendations': '/process-recommendations',
                'referral_progress': '/referral-progress',
                'validate_zipcode': '/validate-zipcode',
                'location_recommendations': '/location-recommendations'
            },
            'risk_analytics': {
                'assess_and_track': '/api/risk/assess-and-track',
                'dashboard': '/api/risk/dashboard/{user_id}',
                'trigger_recommendations': '/api/risk/trigger-recommendations',
                'effectiveness': '/api/risk/analytics/effectiveness',
                'track_outcome': '/api/risk/outcome/track',
                'monitor_status': '/api/risk/monitor/status',
                'trigger_alert': '/api/risk/alert/trigger',
                'live_trends': '/api/risk/trends/live',
                'active_predictions': '/api/risk/predictions/active',
                'active_experiments': '/api/risk/experiments/active',
                'assign_experiment': '/api/risk/experiments/assign',
                'track_experiment_outcome': '/api/risk/experiments/outcome',
                'admin_analytics': '/api/risk/analytics/admin/comprehensive',
                'health': '/api/risk/health'
            },
            'vehicle_management': {
                'create_vehicle': '/api/vehicle',
                'get_vehicles': '/api/vehicle',
                'get_vehicle': '/api/vehicle/{id}',
                'update_vehicle': '/api/vehicle/{id}',
                'delete_vehicle': '/api/vehicle/{id}',
                'maintenance_predictions': '/api/vehicle/{id}/maintenance-predictions',
                'commute_analysis': '/api/vehicle/{id}/commute-analysis',
                'forecast_impact': '/api/vehicle/{id}/forecast-impact',
                'vin_lookup': '/api/vehicle/vin-lookup',
                'health': '/api/vehicle/health'
            }
        },
        'security': {
            'csrf_protection': 'enabled',
            'rate_limiting': 'enabled',
            'input_validation': 'enabled',
            'data_encryption': app.config['DB_ENCRYPTION_ENABLED']
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status_code': 404
    }), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit exceeded errors"""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'status_code': 429
    }), 429

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    }), 500

# Application startup
def initialize_app():
    """Initialize application on first request"""
    logger.info("Initializing Mingus Personal Finance App...")
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('database_backups', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    
    # Initialize assessment database
    try:
        from backend.api.assessment_endpoints import init_assessment_db
        init_assessment_db()
        logger.info("Assessment database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize assessment database: {e}")
    
    logger.info("Application initialization complete")

if __name__ == '__main__':
    # Initialize application
    initialize_app()
    
    # Get configuration from environment
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', '5000'))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting Mingus Personal Finance App on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"CORS origins: {CORS_ORIGINS}")
    logger.info(f"Rate limit: {app.config['RATE_LIMIT_PER_MINUTE']} per minute")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )
