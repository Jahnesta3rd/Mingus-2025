#!/usr/bin/env python3
"""
Mock MINGUS Server for Penetration Testing Demonstration
This server simulates the MINGUS application with various security measures
"""

from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS
import time
import secrets
import hashlib
import hmac
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)
CORS(app)

# Mock user database
users = {
    'test@example.com': {
        'password_hash': 'hashed_password_123',
        'id': 'user_123',
        'subscription_tier': 'basic'
    }
}

# Rate limiting storage
rate_limit_store = {}
failed_login_attempts = {}

# CSRF tokens
csrf_tokens = {}

def require_auth(f):
    """Authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header[7:]
        if token not in ['valid_token_123', 'admin_token_456']:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated

def require_csrf(f):
    """CSRF protection decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'GET':
            return f(*args, **kwargs)
        
        token = request.headers.get('X-CSRFToken') or request.json.get('csrf_token')
        if not token or token not in csrf_tokens:
            return jsonify({'error': 'CSRF token required'}), 403
        
        return f(*args, **kwargs)
    return decorated

def rate_limit(max_attempts=5, window=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            identifier = request.remote_addr
            current_time = time.time()
            
            if identifier in rate_limit_store:
                attempts, last_attempt = rate_limit_store[identifier]
                if current_time - last_attempt < window:
                    if attempts >= max_attempts:
                        return jsonify({'error': 'Rate limit exceeded'}), 429
                    rate_limit_store[identifier] = (attempts + 1, current_time)
                else:
                    rate_limit_store[identifier] = (1, current_time)
            else:
                rate_limit_store[identifier] = (1, current_time)
            
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route('/')
def index():
    """Home page"""
    return jsonify({'message': 'MINGUS Financial Application'})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

@app.route('/api/auth/login', methods=['POST'])
@rate_limit(max_attempts=5, window=300)
def login():
    """Login endpoint with security measures"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Check for brute force attempts
    if email in failed_login_attempts:
        attempts, last_attempt = failed_login_attempts[email]
        if time.time() - last_attempt < 300 and attempts >= 5:
            return jsonify({'error': 'Account temporarily locked'}), 423
    
    if email in users and password == 'SecurePass123!':
        # Reset failed attempts
        if email in failed_login_attempts:
            del failed_login_attempts[email]
        
        return jsonify({
            'success': True,
            'token': 'valid_token_123',
            'user': {'id': users[email]['id'], 'email': email}
        })
    else:
        # Record failed attempt
        if email in failed_login_attempts:
            attempts, _ = failed_login_attempts[email]
            failed_login_attempts[email] = (attempts + 1, time.time())
        else:
            failed_login_attempts[email] = (1, time.time())
        
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/password-reset', methods=['POST'])
def password_reset():
    """Password reset endpoint"""
    data = request.get_json()
    email = data.get('email')
    
    # Generic response to prevent enumeration
    return jsonify({'message': 'If the email exists, a reset link has been sent'})

@app.route('/api/user/profile')
@require_auth
def user_profile():
    """Protected user profile endpoint"""
    return jsonify({'user': {'id': 'user_123', 'email': 'test@example.com'}})

@app.route('/api/financial/transactions', methods=['POST'])
@require_auth
@require_csrf
def create_transaction():
    """Financial transaction endpoint with CSRF protection"""
    data = request.get_json()
    
    # Input validation
    if not data.get('amount') or not isinstance(data.get('amount'), (int, float)):
        return jsonify({'error': 'Invalid amount'}), 400
    
    return jsonify({'success': True, 'transaction_id': 'txn_123'})

@app.route('/api/payment/subscriptions', methods=['POST'])
@require_auth
@require_csrf
def create_subscription():
    """Subscription endpoint with CSRF protection"""
    data = request.get_json()
    
    # Input validation
    valid_tiers = ['basic', 'premium', 'professional']
    if data.get('tier') not in valid_tiers:
        return jsonify({'error': 'Invalid subscription tier'}), 400
    
    return jsonify({'success': True, 'subscription_id': 'sub_123'})

@app.route('/api/premium/analytics')
@require_auth
def premium_analytics():
    """Premium feature endpoint"""
    # Check subscription tier
    auth_header = request.headers.get('Authorization')
    if auth_header and 'admin_token_456' in auth_header:
        return jsonify({'analytics': 'premium_data'})
    else:
        return jsonify({'error': 'Premium subscription required'}), 403

@app.route('/api/assessment/results')
@require_auth
def assessment_results():
    """Assessment results endpoint"""
    return jsonify({'results': 'assessment_data'})

@app.route('/api/financial/csrf-token', methods=['GET'])
def get_csrf_token():
    """Generate CSRF token"""
    token = secrets.token_urlsafe(32)
    csrf_tokens[token] = time.time()
    return jsonify({'csrf_token': token})

@app.route('/api/admin/users')
@require_auth
def admin_users():
    """Admin endpoint"""
    auth_header = request.headers.get('Authorization')
    if 'admin_token_456' in auth_header:
        return jsonify({'users': ['user1', 'user2']})
    else:
        return jsonify({'error': 'Admin access required'}), 403

@app.route('/.env')
def env_file():
    """Simulate exposed environment file"""
    return jsonify({'error': 'Environment file not found'}), 404

@app.route('/api/file/<path:filename>')
def file_access(filename):
    """File access endpoint"""
    # Simulate directory traversal protection
    if '..' in filename or 'etc' in filename:
        return jsonify({'error': 'Invalid file path'}), 400
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/user/profile', methods=['POST'])
@require_auth
def update_profile():
    """Profile update endpoint"""
    data = request.get_json()
    
    # Input validation
    if 'email' in data and '@' not in data['email']:
        return jsonify({'error': 'Invalid email format'}), 400
    
    return jsonify({'success': True})

@app.route('/api/financial/profile', methods=['POST'])
@require_auth
@require_csrf
def update_financial_profile():
    """Financial profile update endpoint"""
    data = request.get_json()
    
    # Input validation
    if 'monthly_income' in data:
        try:
            income = float(data['monthly_income'])
            if income < 0 or income > 1000000:
                return jsonify({'error': 'Invalid income amount'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid income format'}), 400
    
    return jsonify({'success': True})

@app.route('/api/goals/set', methods=['POST'])
@require_auth
@require_csrf
def set_goals():
    """Goal setting endpoint"""
    data = request.get_json()
    
    # Input validation
    if not data.get('goal_name') or len(data['goal_name']) > 100:
        return jsonify({'error': 'Invalid goal name'}), 400
    
    return jsonify({'success': True})

@app.route('/api/assessment/submit', methods=['POST'])
@require_auth
def submit_assessment():
    """Assessment submission endpoint"""
    data = request.get_json()
    
    # Input validation
    if not data.get('responses') or not isinstance(data['responses'], list):
        return jsonify({'error': 'Invalid responses format'}), 400
    
    return jsonify({'success': True, 'assessment_id': 'assess_123'})

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

if __name__ == '__main__':
    print("🚀 Starting Mock MINGUS Server for Penetration Testing")
    print("📍 Server will run on http://localhost:5001")
    print("🔒 Security features enabled:")
    print("   - Authentication required for protected endpoints")
    print("   - CSRF protection for financial operations")
    print("   - Rate limiting for login attempts")
    print("   - Input validation")
    print("   - Security headers")
    print("   - Brute force protection")
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=False)
