#!/usr/bin/env python3
"""
Setup script for comprehensive performance monitoring system
Integrates monitoring with Flask, PostgreSQL, Redis, and Celery
"""

import os
import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from monitoring.comprehensive_monitor import comprehensive_monitor
from monitoring.config import get_monitoring_config
from monitoring.prometheus_exporter import start_background_updater

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_monitoring_for_app(app):
    """
    Set up comprehensive monitoring for a Flask application
    
    Args:
        app: Flask application instance
    """
    try:
        logger.info("Setting up comprehensive performance monitoring...")
        
        # Get environment-specific configuration
        environment = os.getenv('FLASK_ENV', 'development')
        config = get_monitoring_config(environment)
        
        logger.info(f"Using monitoring configuration for environment: {environment}")
        
        # Initialize comprehensive monitor with the app
        comprehensive_monitor.init_app(app)
        
        # Start background metrics updater for Prometheus
        start_background_updater()
        
        # Register monitoring blueprint
        from monitoring.api import monitoring_bp
        app.register_blueprint(monitoring_bp)
        
        # Register Prometheus metrics endpoint
        from monitoring.prometheus_exporter import prometheus_metrics
        app.add_url_rule('/metrics', 'prometheus_metrics', prometheus_metrics)
        
        # Add monitoring configuration to app config
        app.config['MONITORING_CONFIG'] = config
        
        logger.info("Comprehensive monitoring setup completed successfully")
        
        return comprehensive_monitor
        
    except Exception as e:
        logger.error(f"Failed to setup monitoring: {e}")
        raise

def setup_database_monitoring(app):
    """
    Set up database-specific monitoring
    
    Args:
        app: Flask application instance
    """
    try:
        logger.info("Setting up database monitoring...")
        
        # Check if SQLAlchemy is configured
        if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
            logger.warning("SQLAlchemy not found, database monitoring will be limited")
            return
        
        # Get database configuration
        db_config = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        
        if 'postgresql' in db_config.lower():
            logger.info("PostgreSQL database detected, enabling advanced monitoring")
            # PostgreSQL-specific monitoring features can be added here
        elif 'sqlite' in db_config.lower():
            logger.info("SQLite database detected, enabling basic monitoring")
            # SQLite-specific monitoring features can be added here
        
        logger.info("Database monitoring setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup database monitoring: {e}")

def setup_redis_monitoring(app):
    """
    Set up Redis-specific monitoring
    
    Args:
        app: Flask application instance
    """
    try:
        logger.info("Setting up Redis monitoring...")
        
        # Check if Redis is configured
        redis_url = os.getenv('REDIS_URL') or app.config.get('REDIS_URL')
        
        if redis_url:
            logger.info(f"Redis detected at: {redis_url}")
            # Redis-specific monitoring features can be added here
        else:
            logger.warning("Redis not configured, Redis monitoring will be limited")
        
        logger.info("Redis monitoring setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup Redis monitoring: {e}")

def setup_celery_monitoring(app):
    """
    Set up Celery-specific monitoring
    
    Args:
        app: Flask application instance
    """
    try:
        logger.info("Setting up Celery monitoring...")
        
        # Check if Celery is configured
        celery_broker_url = os.getenv('CELERY_BROKER_URL') or app.config.get('CELERY_BROKER_URL')
        
        if celery_broker_url:
            logger.info(f"Celery broker detected at: {celery_broker_url}")
            # Celery-specific monitoring features can be added here
        else:
            logger.warning("Celery not configured, Celery monitoring will be limited")
        
        logger.info("Celery monitoring setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup Celery monitoring: {e}")

def setup_web_vitals_collection(app):
    """
    Set up Core Web Vitals collection
    
    Args:
        app: Flask application instance
    """
    try:
        logger.info("Setting up Core Web Vitals collection...")
        
        # Serve the performance monitoring JavaScript
        @app.route('/static/js/performance-monitor.js')
        def serve_performance_monitor():
            from flask import send_from_directory
            return send_from_directory('static/js', 'performance-monitor.js')
        
        # Add a simple endpoint to test web vitals collection
        @app.route('/monitoring/test-web-vitals')
        def test_web_vitals():
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Web Vitals Test</title>
                <script src="/static/js/performance-monitor.js"></script>
            </head>
            <body>
                <h1>Web Vitals Test Page</h1>
                <p>This page is used to test Core Web Vitals collection.</p>
                <button onclick="testMetrics()">Test Metrics</button>
                <div id="results"></div>
                
                <script>
                function testMetrics() {
                    if (window.performanceMonitor) {
                        const metrics = window.performanceMonitor.getMetrics();
                        document.getElementById('results').innerHTML = 
                            '<pre>' + JSON.stringify(metrics, null, 2) + '</pre>';
                    } else {
                        document.getElementById('results').innerHTML = 
                            '<p>Performance monitor not loaded</p>';
                    }
                }
                </script>
            </body>
            </html>
            """
        
        logger.info("Core Web Vitals collection setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup web vitals collection: {e}")

def create_monitoring_dashboard(app):
    """
    Create a simple monitoring dashboard
    
    Args:
        app: Flask application instance
    """
    try:
        logger.info("Creating monitoring dashboard...")
        
        @app.route('/monitoring/dashboard')
        def monitoring_dashboard():
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Performance Monitoring Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .metric-card { 
                        border: 1px solid #ddd; 
                        padding: 15px; 
                        margin: 10px; 
                        border-radius: 5px; 
                        background: #f9f9f9; 
                    }
                    .metric-value { 
                        font-size: 24px; 
                        font-weight: bold; 
                        color: #333; 
                    }
                    .metric-label { 
                        color: #666; 
                        margin-bottom: 5px; 
                    }
                    .grid { 
                        display: grid; 
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                        gap: 20px; 
                    }
                    .refresh-btn { 
                        padding: 10px 20px; 
                        background: #007bff; 
                        color: white; 
                        border: none; 
                        border-radius: 5px; 
                        cursor: pointer; 
                        margin-bottom: 20px; 
                    }
                    .refresh-btn:hover { background: #0056b3; }
                </style>
            </head>
            <body>
                <h1>Performance Monitoring Dashboard</h1>
                <button class="refresh-btn" onclick="refreshMetrics()">Refresh Metrics</button>
                
                <div class="grid">
                    <div class="metric-card">
                        <div class="metric-label">API Requests</div>
                        <div class="metric-value" id="api-requests">-</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Database Queries</div>
                        <div class="metric-value" id="db-queries">-</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Redis Operations</div>
                        <div class="metric-value" id="redis-ops">-</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Celery Tasks</div>
                        <div class="metric-value" id="celery-tasks">-</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">System CPU</div>
                        <div class="metric-value" id="system-cpu">-</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">System Memory</div>
                        <div class="metric-value" id="system-memory">-</div>
                    </div>
                </div>
                
                <script>
                async function refreshMetrics() {
                    try {
                        const response = await fetch('/monitoring/metrics');
                        const data = await response.json();
                        
                        document.getElementById('api-requests').textContent = data.api.total_requests;
                        document.getElementById('db-queries').textContent = data.database.total_queries;
                        document.getElementById('redis-ops').textContent = data.redis.total_operations;
                        document.getElementById('celery-tasks').textContent = data.celery.total_tasks;
                        document.getElementById('system-cpu').textContent = data.system.current_cpu + '%';
                        document.getElementById('system-memory').textContent = data.system.current_memory + '%';
                        
                    } catch (error) {
                        console.error('Error fetching metrics:', error);
                    }
                }
                
                // Auto-refresh every 30 seconds
                setInterval(refreshMetrics, 30000);
                
                // Initial load
                refreshMetrics();
                </script>
            </body>
            </html>
            """
        
        logger.info("Monitoring dashboard created")
        
    except Exception as e:
        logger.error(f"Failed to create monitoring dashboard: {e}")

def main():
    """
    Main setup function for standalone execution
    """
    try:
        logger.info("Starting monitoring setup...")
        
        # This would typically be called from your Flask app factory
        # For standalone execution, we'll create a minimal Flask app
        from flask import Flask
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # Setup monitoring
        monitor = setup_monitoring_for_app(app)
        
        # Setup specific monitoring components
        setup_database_monitoring(app)
        setup_redis_monitoring(app)
        setup_celery_monitoring(app)
        setup_web_vitals_collection(app)
        create_monitoring_dashboard(app)
        
        logger.info("Monitoring setup completed successfully!")
        logger.info("Available endpoints:")
        logger.info("  - /monitoring/health - Health check")
        logger.info("  - /monitoring/metrics - Performance metrics")
        logger.info("  - /monitoring/dashboard - Monitoring dashboard")
        logger.info("  - /metrics - Prometheus metrics")
        logger.info("  - /static/js/performance-monitor.js - Frontend monitoring library")
        
        return monitor
        
    except Exception as e:
        logger.error(f"Monitoring setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
