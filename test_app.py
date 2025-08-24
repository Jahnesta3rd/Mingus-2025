#!/usr/bin/env python3
"""
Test Flask application with security middleware and health endpoints
Simplified version for testing without database requirements
"""

import os
from flask import Flask, jsonify
from datetime import datetime
import time

# Import security and health modules
from backend.middleware.security import init_security
from backend.monitoring.health import create_health_routes

def create_test_app():
    """Create a test Flask application with security and health monitoring"""
    app = Flask(__name__)
    
    # Basic configuration
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': os.getenv('SECRET_KEY', 'test-secret-key-for-development'),
        'DEBUG': True,
        'ENV': 'development'
    })
    
    # Initialize security middleware
    print("🔒 Initializing security middleware...")
    security_components = init_security(app)
    print("✅ Security middleware initialized")
    
    # Add health check routes
    print("🏥 Adding health monitoring routes...")
    create_health_routes(app)
    print("✅ Health monitoring routes added")
    
    # Add a simple test route
    @app.route('/')
    def home():
        return jsonify({
            'message': 'Mingus Flask Application with Security & Health Monitoring',
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat(),
            'security': 'enabled',
            'health_monitoring': 'enabled'
        })
    
    @app.route('/test-secure')
    def test_secure():
        return jsonify({
            'message': 'Secure endpoint working',
            'security_headers': 'active',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    print("✅ Test Flask application created successfully")
    return app

def main():
    """Main function to run the test Flask application"""
    print("🚀 Starting Test Flask Application")
    print("=" * 50)
    
    try:
        # Create the test app
        app = create_test_app()
        
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 8000))
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"🌐 Starting server on {host}:{port}")
        print("📋 Available endpoints:")
        print("   - GET /                    - Home page")
        print("   - GET /health              - Basic health check")
        print("   - GET /health/detailed     - Detailed health check")
        print("   - GET /health/readiness    - Kubernetes readiness probe")
        print("   - GET /health/liveness     - Kubernetes liveness probe")
        print("   - GET /health/startup      - Kubernetes startup probe")
        print("   - GET /test-secure         - Test secure endpoint")
        print()
        print("🔒 Security features active:")
        print("   - Security headers")
        print("   - Request logging")
        print("   - Rate limiting")
        print("   - Input validation")
        print()
        print("🏥 Health monitoring active:")
        print("   - System resource monitoring")
        print("   - External service checks")
        print("   - Response time tracking")
        print()
        print("=" * 50)
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=True,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ Failed to start test application: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main()) 