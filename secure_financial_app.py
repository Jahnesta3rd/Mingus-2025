from flask import Flask, request, session, redirect, url_for, flash, render_template, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import hashlib
import json
import redis
import uuid
from functools import wraps
import logging
from typing import Dict, List, Optional
import ipaddress
import geoip2.database
import geoip2.errors

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security Configuration
app.config.update(
    SECRET_KEY=secrets.token_urlsafe(32),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=20),  # 20 minutes for financial app
    SESSION_REFRESH_EACH_REQUEST=True,
    SQLALCHEMY_DATABASE_URI='sqlite:///financial_app.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    REDIS_URL='redis://localhost:6379/0'
)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'

# Initialize CSP middleware
from csp_policy_manager import CSPMiddleware, CSPViolationHandler
csp_middleware = CSPMiddleware(app, environment=os.getenv('FLASK_ENV', 'development'))
violation_handler = CSPViolationHandler(app)

# Redis connection for session storage
try:
    redis_client = redis.from_url(app.config['REDIS_URL'])
    redis_client.ping()
except redis.ConnectionError:
    logger.warning("Redis not available, using in-memory storage")
    redis_client = None

# GeoIP database for location tracking
try:
    geoip_reader = geoip2.database.Reader('GeoLite2-City.mmdb')
except FileNotFoundError:
    logger.warning("GeoIP database not found, location tracking disabled")
    geoip_reader = None

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    security_level = db.Column(db.String(20), default='standard')  # standard, enhanced, maximum
    
    # Relationships
    sessions = db.relationship('UserSession', backref='user', lazy=True, cascade='all, delete-orphan')
    login_attempts = db.relationship('LoginAttempt', backref='user', lazy=True, cascade='all, delete-orphan')

class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    device_info = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    location = db.Column(db.Text, nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=False)

class LoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text, nullable=True)
    success = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.Text, nullable=True)

# Session Management Class
class SecureSessionManager:
    def __init__(self, app):
        self.app = app
        self.max_concurrent_sessions = 3
        self.session_timeout = timedelta(minutes=20)
        self.rate_limit_window = timedelta(minutes=15)
        self.max_login_attempts = 5
        
    def generate_secure_session_id(self) -> str:
        """Generate a cryptographically secure session ID"""
        return secrets.token_urlsafe(32)
    
    def create_session(self, user_id: int, request) -> str:
        """Create a new secure session"""
        session_id = self.generate_secure_session_id()
        
        # Get device and location info
        device_info = self._get_device_info(request)
        ip_address = self._get_client_ip(request)
        location = self._get_location_info(ip_address)
        
        # Check concurrent sessions limit
        active_sessions = UserSession.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).count()
        
        if active_sessions >= self.max_concurrent_sessions:
            # Remove oldest session
            oldest_session = UserSession.query.filter_by(
                user_id=user_id, 
                is_active=True
            ).order_by(UserSession.created_at.asc()).first()
            if oldest_session:
                self.invalidate_session(oldest_session.session_id)
        
        # Create new session
        new_session = UserSession(
            user_id=user_id,
            session_id=session_id,
            device_info=device_info,
            ip_address=ip_address,
            location=location,
            user_agent=request.headers.get('User-Agent'),
            expires_at=datetime.utcnow() + self.session_timeout
        )
        
        db.session.add(new_session)
        db.session.commit()
        
        # Store in Redis for fast access
        if redis_client:
            session_data = {
                'user_id': user_id,
                'created_at': new_session.created_at.isoformat(),
                'expires_at': new_session.expires_at.isoformat(),
                'device_info': device_info,
                'ip_address': ip_address,
                'location': location
            }
            redis_client.setex(
                f"session:{session_id}",
                int(self.session_timeout.total_seconds()),
                json.dumps(session_data)
            )
        
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validate a session and return session data"""
        if not session_id:
            return None
        
        # Check Redis first
        if redis_client:
            session_data = redis_client.get(f"session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                if datetime.fromisoformat(data['expires_at']) > datetime.utcnow():
                    # Update last activity
                    self._update_session_activity(session_id)
                    return data
        
        # Fallback to database
        db_session = UserSession.query.filter_by(
            session_id=session_id,
            is_active=True
        ).first()
        
        if db_session and db_session.expires_at > datetime.utcnow():
            self._update_session_activity(session_id)
            return {
                'user_id': db_session.user_id,
                'created_at': db_session.created_at.isoformat(),
                'expires_at': db_session.expires_at.isoformat(),
                'device_info': db_session.device_info,
                'ip_address': db_session.ip_address,
                'location': db_session.location
            }
        
        return None
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        # Remove from Redis
        if redis_client:
            redis_client.delete(f"session:{session_id}")
        
        # Update database
        db_session = UserSession.query.filter_by(session_id=session_id).first()
        if db_session:
            db_session.is_active = False
            db.session.commit()
    
    def invalidate_all_user_sessions(self, user_id: int):
        """Invalidate all sessions for a user"""
        # Remove from Redis
        if redis_client:
            sessions = UserSession.query.filter_by(user_id=user_id, is_active=True).all()
            for session in sessions:
                redis_client.delete(f"session:{session.session_id}")
        
        # Update database
        UserSession.query.filter_by(user_id=user_id, is_active=True).update({'is_active': False})
        db.session.commit()
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        expired_sessions = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow(),
            UserSession.is_active == True
        ).all()
        
        for session in expired_sessions:
            if redis_client:
                redis_client.delete(f"session:{session.session_id}")
            session.is_active = False
        
        db.session.commit()
    
    def _get_device_info(self, request) -> str:
        """Extract device information from request"""
        user_agent = request.headers.get('User-Agent', '')
        # Simple device detection - in production, use a proper user agent parser
        if 'Mobile' in user_agent:
            return 'Mobile Device'
        elif 'Tablet' in user_agent:
            return 'Tablet'
        else:
            return 'Desktop'
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return request.remote_addr
    
    def _get_location_info(self, ip_address: str) -> Optional[str]:
        """Get location information from IP address"""
        if not geoip_reader or not ip_address:
            return None
        
        try:
            # Skip private IPs
            if ipaddress.ip_address(ip_address).is_private:
                return "Private Network"
            
            response = geoip_reader.city(ip_address)
            return f"{response.city.name}, {response.country.name}"
        except (geoip2.errors.AddressNotFoundError, ValueError):
            return "Unknown Location"
    
    def _update_session_activity(self, session_id: str):
        """Update session last activity"""
        if redis_client:
            # Extend session in Redis
            redis_client.expire(f"session:{session_id}", int(self.session_timeout.total_seconds()))
        
        # Update database
        db_session = UserSession.query.filter_by(session_id=session_id).first()
        if db_session:
            db_session.last_activity = datetime.utcnow()
            db.session.commit()

# Initialize session manager
session_manager = SecureSessionManager(app)

# Rate limiting decorator
def rate_limit(max_attempts: int, window: timedelta):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip_address = request.remote_addr
            key = f"rate_limit:{ip_address}:{f.__name__}"
            
            if redis_client:
                attempts = redis_client.get(key)
                if attempts and int(attempts) >= max_attempts:
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                
                pipe = redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, int(window.total_seconds()))
                pipe.execute()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Security decorators
def require_enhanced_security(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        if current_user.security_level != 'enhanced':
            flash('Enhanced security level required for this action', 'warning')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def check_session_security(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        # Check if session is still valid
        session_id = session.get('session_id')
        if not session_manager.validate_session(session_id):
            logout_user()
            flash('Session expired. Please login again.', 'warning')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(max_attempts=5, window=timedelta(minutes=15))
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user is locked
        user = User.query.filter_by(username=username).first()
        if user and user.locked_until and user.locked_until > datetime.utcnow():
            flash('Account temporarily locked. Please try again later.', 'error')
            return render_template('login.html')
        
        if user and check_password_hash(user.password_hash, password):
            # Reset failed attempts
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Create secure session
            session_id = session_manager.create_session(user.id, request)
            session['session_id'] = session_id
            
            # Log successful login
            login_attempt = LoginAttempt(
                user_id=user.id,
                username=username,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                success=True,
                location=session_manager._get_location_info(request.remote_addr)
            )
            db.session.add(login_attempt)
            db.session.commit()
            
            login_user(user, remember=False)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Increment failed attempts
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                db.session.commit()
            
            # Log failed attempt
            login_attempt = LoginAttempt(
                username=username,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                success=False,
                location=session_manager._get_location_info(request.remote_addr)
            )
            db.session.add(login_attempt)
            db.session.commit()
            
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Invalidate current session
    session_id = session.get('session_id')
    if session_id:
        session_manager.invalidate_session(session_id)
    
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/logout_all_devices')
@login_required
@check_session_security
def logout_all_devices():
    session_manager.invalidate_all_user_sessions(current_user.id)
    logout_user()
    session.clear()
    flash('You have been logged out from all devices.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
@check_session_security
def dashboard():
    # Get user's active sessions
    active_sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserSession.last_activity.desc()).all()
    
    return render_template('dashboard.html', sessions=active_sessions)

@app.route('/sessions')
@login_required
@check_session_security
def view_sessions():
    sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserSession.last_activity.desc()).all()
    
    return render_template('sessions.html', sessions=sessions)

@app.route('/security_settings')
@login_required
@check_session_security
def security_settings():
    return render_template('security_settings.html', now=datetime.utcnow())

@app.route('/api/sessions')
@login_required
@check_session_security
def api_sessions():
    sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserSession.last_activity.desc()).all()
    
    session_data = []
    for sess in sessions:
        session_data.append({
            'id': sess.id,
            'device_info': sess.device_info,
            'ip_address': sess.ip_address,
            'location': sess.location,
            'created_at': sess.created_at.isoformat(),
            'last_activity': sess.last_activity.isoformat(),
            'is_current': sess.session_id == session.get('session_id')
        })
    
    return jsonify(session_data)

@app.route('/api/terminate_session/<int:session_id>', methods=['POST'])
@login_required
@check_session_security
def terminate_session(session_id):
    user_session = UserSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first()
    
    if user_session:
        session_manager.invalidate_session(user_session.session_id)
        return jsonify({'success': True})
    
    return jsonify({'error': 'Session not found'}), 404

@app.route('/api/login_attempts')
@login_required
@check_session_security
def api_login_attempts():
    """Get recent login attempts for the current user"""
    attempts = LoginAttempt.query.filter_by(
        user_id=current_user.id
    ).order_by(LoginAttempt.timestamp.desc()).limit(20).all()
    
    attempts_data = []
    for attempt in attempts:
        attempts_data.append({
            'id': attempt.id,
            'username': attempt.username,
            'ip_address': attempt.ip_address,
            'location': attempt.location,
            'success': attempt.success,
            'timestamp': attempt.timestamp.isoformat(),
            'user_agent': attempt.user_agent
        })
    
    return jsonify(attempts_data)

# Background task for session cleanup
@app.before_request
def cleanup_sessions():
    """Clean up expired sessions before each request"""
    session_manager.cleanup_expired_sessions()

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Create a test user for demonstration
def create_test_user():
    with app.app_context():
        # Check if test user exists
        test_user = User.query.filter_by(username='demo').first()
        if not test_user:
            test_user = User(
                username='demo',
                email='demo@example.com',
                password_hash=generate_password_hash('SecurePass123!'),
                is_verified=True,
                security_level='enhanced'
            )
            db.session.add(test_user)
            db.session.commit()
            logger.info("Test user 'demo' created with password 'SecurePass123!'")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_test_user()
    app.run(debug=False, host='0.0.0.0', port=5000)
