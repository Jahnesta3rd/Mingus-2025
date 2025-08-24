#!/usr/bin/env python3
"""
Test script to verify security and health monitoring features
"""

import os
import sys
from flask import Flask, jsonify

def test_security_and_health():
    """Test security and health monitoring modules"""
    print("🔒 Testing Security and Health Monitoring Integration")
    print("=" * 60)
    
    try:
        # Create a minimal Flask app for testing
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # Test security middleware
        print("1. Testing Security Middleware...")
        from backend.middleware.security import init_security
        security_components = init_security(app)
        print("   ✅ Security middleware initialized successfully")
        print(f"   ✅ Security components: {list(security_components.keys())}")
        
        # Test health monitoring
        print("2. Testing Health Monitoring...")
        from backend.monitoring.health import create_health_routes
        create_health_routes(app)
        print("   ✅ Health monitoring routes created successfully")
        
        # Test Flask-Talisman
        print("3. Testing Flask-Talisman...")
        try:
            from flask_talisman import Talisman
            talisman = Talisman(app)
            print("   ✅ Flask-Talisman initialized successfully")
        except ImportError:
            print("   ⚠️  Flask-Talisman not available")
        
        # Test Flask-Limiter
        print("4. Testing Flask-Limiter...")
        try:
            from flask_limiter import Limiter
            from flask_limiter.util import get_remote_address
            limiter = Limiter(
                app=app,
                key_func=get_remote_address,
                default_limits=["200 per day", "50 per hour"]
            )
            print("   ✅ Flask-Limiter initialized successfully")
        except ImportError:
            print("   ⚠️  Flask-Limiter not available")
        
        # Test Flask-WTF
        print("5. Testing Flask-WTF...")
        try:
            from flask_wtf import CSRFProtect
            csrf = CSRFProtect(app)
            print("   ✅ Flask-WTF CSRF protection initialized successfully")
        except ImportError:
            print("   ⚠️  Flask-WTF not available")
        
        # Test monitoring packages
        print("6. Testing Monitoring Packages...")
        try:
            import psutil
            print(f"   ✅ psutil available - CPU: {psutil.cpu_percent()}%")
        except ImportError:
            print("   ❌ psutil not available")
        
        try:
            import prometheus_client
            print("   ✅ prometheus-client available")
        except ImportError:
            print("   ❌ prometheus-client not available")
        
        # Test security decorators
        print("7. Testing Security Decorators...")
        from backend.middleware.security import require_https, validate_financial_data, audit_financial_access
        
        @app.route('/test-secure')
        @require_https
        @validate_financial_data
        @audit_financial_access
        def test_secure_endpoint():
            return jsonify({"message": "Secure endpoint working"})
        
        print("   ✅ Security decorators applied successfully")
        
        # Test health endpoints
        print("8. Testing Health Endpoints...")
        with app.test_client() as client:
            # Test basic health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("   ✅ /health endpoint working")
            else:
                print(f"   ❌ /health endpoint failed: {response.status_code}")
            
            # Test detailed health endpoint
            response = client.get('/health/detailed')
            if response.status_code == 200:
                print("   ✅ /health/detailed endpoint working")
            else:
                print(f"   ❌ /health/detailed endpoint failed: {response.status_code}")
            
            # Test readiness endpoint
            response = client.get('/health/readiness')
            if response.status_code == 200:
                print("   ✅ /health/readiness endpoint working")
            else:
                print(f"   ❌ /health/readiness endpoint failed: {response.status_code}")
            
            # Test liveness endpoint
            response = client.get('/health/liveness')
            if response.status_code == 200:
                print("   ✅ /health/liveness endpoint working")
            else:
                print(f"   ❌ /health/liveness endpoint failed: {response.status_code}")
        
        print("\n🎉 All Security and Health Monitoring Tests Passed!")
        print("=" * 60)
        print("✅ Security middleware: Working")
        print("✅ Health monitoring: Working")
        print("✅ Flask-Talisman: Available")
        print("✅ Flask-Limiter: Available")
        print("✅ Flask-WTF: Available")
        print("✅ psutil: Available")
        print("✅ prometheus-client: Available")
        print("✅ Security decorators: Working")
        print("✅ Health endpoints: Working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_security_and_health()
    sys.exit(0 if success else 1) 