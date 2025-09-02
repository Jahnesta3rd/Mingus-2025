#!/usr/bin/env python3
"""
Minimal Flask App to Test CORS Configuration
"""

from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from backend.config.unified_security_config import UnifiedSecurityConfig
    
    # Create Flask app
    app = Flask(__name__)
    
    # Get CORS configuration from unified security config
    security_config = UnifiedSecurityConfig()
    cors_origins = security_config.CORS_ORIGINS if security_config.CORS_ENABLED else ['http://localhost:3000']
    
    print(f"🔧 CORS Configuration:")
    print(f"   Enabled: {security_config.CORS_ENABLED}")
    print(f"   Origins: {cors_origins}")
    print(f"   Methods: {security_config.CORS_METHODS}")
    print(f"   Headers: {security_config.CORS_ALLOW_HEADERS}")
    
    # Initialize CORS with security best practices
    CORS(app, 
         origins=cors_origins,
         methods=security_config.CORS_METHODS,
         allow_headers=security_config.CORS_ALLOW_HEADERS,
         supports_credentials=security_config.CORS_SUPPORTS_CREDENTIALS,
         max_age=3600,
         vary_header=True,
         send_wildcard=False
    )
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'cors_enabled': True})
    
    @app.route('/api/test')
    def test():
        return jsonify({'message': 'CORS test endpoint', 'cors_origins': cors_origins})
    
    @app.route('/api/secure')
    def secure():
        return jsonify({'message': 'Secure endpoint', 'cors_methods': security_config.CORS_METHODS})
    
    @app.route('/api/financial/balance')
    def financial_balance():
        return jsonify({'balance': 1000, 'currency': 'USD'})
    
    if __name__ == '__main__':
        print(f"🚀 Starting Flask app with CORS configuration on port 5001")
        print(f"✅ CORS Origins: {cors_origins}")
        app.run(host='0.0.0.0', port=5001, debug=True)
        
except Exception as e:
    print(f"❌ Error setting up CORS app: {e}")
    import traceback
    traceback.print_exc()
