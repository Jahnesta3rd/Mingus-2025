#!/usr/bin/env python3
"""
Test Flask Application with User Profile Integration
Demonstrates the complete user profile functionality
"""

from flask import Flask, jsonify, request, render_template_string
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
import json
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key-for-development'

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    """Simple user class for testing"""
    def __init__(self, user_id, email, first_name=None, last_name=None):
        self.id = user_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

@login_manager.user_loader
def load_user(user_id):
    """Load user from database"""
    try:
        conn = sqlite3.connect('instance/mingus.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, first_name, last_name FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(user_data[0], user_data[1], user_data[2], user_data[3])
        return None
    except Exception as e:
        logger.error(f"Error loading user: {e}")
        return None

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect('instance/mingus.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

# Import and register user profile blueprint
from backend.routes.user_profile import user_profile_bp
app.register_blueprint(user_profile_bp)

@app.route('/')
def index():
    """Home page"""
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mingus User Profile Test</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .card { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }
                .button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                .button:hover { background: #0056b3; }
                .success { color: green; }
                .error { color: red; }
                .profile-data { background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 10px 0; }
                pre { white-space: pre-wrap; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 Mingus User Profile Test Application</h1>
                
                {% if current_user.is_authenticated %}
                    <div class="card">
                        <h2>👤 Welcome, {{ current_user.first_name or current_user.email }}!</h2>
                        <p>You are logged in as: {{ current_user.email }}</p>
                        <button class="button" onclick="getProfile()">Get Profile</button>
                        <button class="button" onclick="showUpdateForm()">Update Profile</button>
                        <button class="button" onclick="getSubscription()">Get Subscription</button>
                        <button class="button" onclick="getFeatureUsage()">Get Feature Usage</button>
                        <a href="/logout" class="button">Logout</a>
                    </div>
                    
                    <div id="profile-display" class="card" style="display: none;">
                        <h3>📊 User Profile</h3>
                        <div id="profile-content"></div>
                    </div>
                    
                    <div id="update-form" class="card" style="display: none;">
                        <h3>✏️ Update Profile</h3>
                        <form id="profile-form">
                            <div>
                                <label>First Name:</label>
                                <input type="text" id="firstName" name="firstName" required>
                            </div>
                            <div>
                                <label>Last Name:</label>
                                <input type="text" id="lastName" name="lastName" required>
                            </div>
                            <div>
                                <label>ZIP Code:</label>
                                <input type="text" id="zipCode" name="zipCode" required>
                            </div>
                            <div>
                                <label>Dependents:</label>
                                <input type="number" id="dependentsCount" name="dependentsCount" min="0" max="20">
                            </div>
                            <div>
                                <label>Marital Status:</label>
                                <select id="maritalStatus" name="maritalStatus">
                                    <option value="">Select...</option>
                                    <option value="single">Single</option>
                                    <option value="married">Married</option>
                                    <option value="partnership">Partnership</option>
                                    <option value="divorced">Divorced</option>
                                    <option value="widowed">Widowed</option>
                                </select>
                            </div>
                            <div>
                                <label>Industry:</label>
                                <input type="text" id="industry" name="industry">
                            </div>
                            <div>
                                <label>Job Title:</label>
                                <input type="text" id="jobTitle" name="jobTitle">
                            </div>
                            <div>
                                <label>Monthly Income:</label>
                                <input type="number" id="monthlyIncome" name="monthlyIncome" min="0" step="0.01">
                            </div>
                            <div>
                                <label>Employment Status:</label>
                                <select id="employmentStatus" name="employmentStatus">
                                    <option value="">Select...</option>
                                    <option value="employed">Employed</option>
                                    <option value="unemployed">Unemployed</option>
                                    <option value="self-employed">Self-Employed</option>
                                    <option value="student">Student</option>
                                    <option value="retired">Retired</option>
                                </select>
                            </div>
                            <button type="submit" class="button">Update Profile</button>
                        </form>
                    </div>
                    
                    <div id="subscription-display" class="card" style="display: none;">
                        <h3>💳 Subscription Information</h3>
                        <div id="subscription-content"></div>
                    </div>
                    
                    <div id="usage-display" class="card" style="display: none;">
                        <h3>📈 Feature Usage</h3>
                        <div id="usage-content"></div>
                    </div>
                    
                {% else %}
                    <div class="card">
                        <h2>🔐 Login Required</h2>
                        <p>Please log in to test the user profile functionality.</p>
                        <a href="/login" class="button">Login</a>
                    </div>
                {% endif %}
                
                <div class="card">
                    <h3>📋 Test Instructions</h3>
                    <ol>
                        <li>Login with the test account (test@mingus.com)</li>
                        <li>Click "Get Profile" to see current profile data</li>
                        <li>Click "Update Profile" to modify profile information</li>
                        <li>Click "Get Subscription" to see subscription details</li>
                        <li>Click "Get Feature Usage" to see usage statistics</li>
                    </ol>
                </div>
            </div>
            
            <script>
                async function getProfile() {
                    try {
                        const response = await fetch('/api/user-profile/get');
                        const data = await response.json();
                        
                        if (data.success) {
                            document.getElementById('profile-content').innerHTML = 
                                '<pre>' + JSON.stringify(data.profile, null, 2) + '</pre>';
                            document.getElementById('profile-display').style.display = 'block';
                        } else {
                            alert('Error: ' + data.error);
                        }
                    } catch (error) {
                        alert('Error: ' + error.message);
                    }
                }
                
                async function getSubscription() {
                    try {
                        const response = await fetch('/api/user-profile/subscription');
                        const data = await response.json();
                        
                        if (data.success) {
                            document.getElementById('subscription-content').innerHTML = 
                                '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                            document.getElementById('subscription-display').style.display = 'block';
                        } else {
                            alert('Error: ' + data.error);
                        }
                    } catch (error) {
                        alert('Error: ' + error.message);
                    }
                }
                
                async function getFeatureUsage() {
                    try {
                        const response = await fetch('/api/user-profile/feature-usage');
                        const data = await response.json();
                        
                        if (data.success) {
                            document.getElementById('usage-content').innerHTML = 
                                '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                            document.getElementById('usage-display').style.display = 'block';
                        } else {
                            alert('Error: ' + data.error);
                        }
                    } catch (error) {
                        alert('Error: ' + error.message);
                    }
                }
                
                function showUpdateForm() {
                    document.getElementById('update-form').style.display = 'block';
                }
                
                document.getElementById('profile-form').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const formData = new FormData(e.target);
                    const data = {};
                    for (let [key, value] of formData.entries()) {
                        if (value) data[key] = value;
                    }
                    
                    try {
                        const response = await fetch('/api/user-profile/update', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(data)
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            alert('Profile updated successfully! Completion: ' + result.profile_completion_percentage + '%');
                            document.getElementById('update-form').style.display = 'none';
                        } else {
                            alert('Error: ' + (result.errors ? result.errors.join(', ') : result.error));
                        }
                    } catch (error) {
                        alert('Error: ' + error.message);
                    }
                });
            </script>
        </body>
        </html>
    ''')

@app.route('/login')
def login():
    """Login page"""
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Mingus Test</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 400px; margin: 0 auto; }
                .card { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
                .button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%; }
                input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔐 Login</h1>
                <div class="card">
                    <form method="POST" action="/login">
                        <div>
                            <label>Email:</label>
                            <input type="email" name="email" value="test@mingus.com" required>
                        </div>
                        <div>
                            <label>Password:</label>
                            <input type="password" name="password" value="test123" required>
                        </div>
                        <button type="submit" class="button">Login</button>
                    </form>
                    <p><small>Use test@mingus.com / test123 to login</small></p>
                </div>
            </div>
        </body>
        </html>
    ''')

@app.route('/login', methods=['POST'])
def login_post():
    """Handle login"""
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Simple authentication for testing
    if email == 'test@mingus.com' and password == 'test123':
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, email, first_name, last_name FROM users WHERE email = ?', (email,))
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                user = User(user_data[0], user_data[1], user_data[2], user_data[3])
                login_user(user)
                return jsonify({'success': True, 'redirect': '/'})
    
    return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return jsonify({'success': True, 'redirect': '/'})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if get_db_connection() else 'disconnected'
    })

@app.route('/api/test-profile')
def test_profile_api():
    """Test endpoint to verify API is working"""
    return jsonify({
        'success': True,
        'message': 'User Profile API is working!',
        'endpoints': [
            'GET /api/user-profile/get',
            'POST /api/user-profile/update',
            'GET /api/user-profile/onboarding-progress',
            'POST /api/user-profile/onboarding-progress',
            'GET /api/user-profile/subscription',
            'GET /api/user-profile/feature-usage'
        ]
    })

if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists('instance/mingus.db'):
        print("❌ Database not found! Please run the migration script first:")
        print("   python apply_user_profile_migrations.py")
        exit(1)
    
    print("🚀 Starting Mingus User Profile Test Application...")
    print("📊 Database: instance/mingus.db")
    print("🌐 Server: http://localhost:5001")
    print("👤 Test User: test@mingus.com / test123")
    print("📋 API Test: http://localhost:5001/api/test-profile")
    print("🏥 Health Check: http://localhost:5001/health")
    
    app.run(debug=True, host='0.0.0.0', port=5001) 