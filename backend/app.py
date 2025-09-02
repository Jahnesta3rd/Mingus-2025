from flask import Flask, jsonify, request, send_from_directory
import sys
import os
import traceback
from dotenv import load_dotenv

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

# Now we can import our module
from src.utils.cashflow_calculator import calculate_daily_cashflow

# Import article models to ensure SQLAlchemy knows about them
from backend.models.articles import (
    Article, UserArticleRead, UserArticleBookmark, UserArticleRating,
    ArticleRecommendation, ArticleAnalytics
)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Basic Flask configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Flask extensions
try:
    from extensions import init_extensions
    init_extensions(app)
    print("✅ Flask extensions initialized")
except Exception as e:
    print(f"⚠️  Flask extensions initialization failed: {e}")

# SSL Configuration - only import and initialize in production
if os.getenv('FLASK_ENV') == 'production':
    # Import SSL security middleware only in production
    try:
        from middleware.ssl_middleware import init_ssl_middleware
        from config.ssl_config import SSLSecurity
        
        # Production SSL settings
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
        app.config['SESSION_COOKIE_MAX_AGE'] = 1800  # 30 minutes for financial app
        
        # Initialize SSL middleware
        ssl_middleware = init_ssl_middleware(app)
        ssl_security = SSLSecurity(app)
        print("🔒 SSL Security middleware initialized for production")
    except Exception as e:
        print(f"⚠️  SSL middleware initialization failed: {e}")
        print("🔓 Continuing without SSL middleware")
else:
    # Development settings
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_MAX_AGE'] = 3600
    
    print("🔓 Development mode - SSL disabled")

# Initialize comprehensive performance monitoring
try:
    from monitoring.setup_monitoring import setup_monitoring_for_app
    print("📊 Setting up comprehensive performance monitoring...")
    monitor = setup_monitoring_for_app(app)
    print("✅ Performance monitoring initialized successfully")
except Exception as e:
    print(f"⚠️  Monitoring setup failed: {e}")
    print("🔓 Continuing without monitoring")
    monitor = None

@app.route('/')
def index():
    """Serve the main accessibility demo page"""
    return send_from_directory('..', 'accessibility_demo.html')

@app.route('/forms')
def forms():
    """Serve the financial forms accessibility examples"""
    return send_from_directory('..', 'financial_form_accessibility_examples.html')

@app.route('/calculator')
def calculator():
    """Serve the AI job impact calculator"""
    return send_from_directory('..', 'ai-job-impact-calculator.html')

@app.route('/landing')
def landing():
    """Serve the landing page"""
    return send_from_directory('..', 'landing.html')

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/forecast', methods=['POST'])
def generate_forecast():
    """Generate cashflow forecast for a user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'user_id' not in data or 'initial_balance' not in data:
            return jsonify({
                "error": "Missing required fields. Please provide user_id and initial_balance"
            }), 400
        
        # Extract parameters
        user_id = data['user_id']
        initial_balance = float(data['initial_balance'])
        start_date = data.get('start_date')  # Optional parameter
        
        # Generate forecast
        forecast_results = calculate_daily_cashflow(
            user_id=user_id,
            initial_balance=initial_balance,
            start_date=start_date
        )
        
        return jsonify({
            "status": "success",
            "data": forecast_results
        }), 200
        
    except ValueError as ve:
        print(f"ValueError: {str(ve)}")
        return jsonify({
            "error": "Invalid input data",
            "details": str(ve)
        }), 400
        
    except Exception as e:
        # Print the full error traceback
        print("Error in generate_forecast:")
        print(traceback.format_exc())
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # Print environment check
    print("\nEnvironment variables:")
    print(f"SUPABASE_URL: {'Set' if os.getenv('SUPABASE_URL') else 'Not set'}")
    print(f"SUPABASE_ANON_KEY: {'Set' if os.getenv('SUPABASE_URL') else 'Not set'}")
    print(f"PORT: {port}")
    print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")
    print(f"SSL_ENABLED: {'Yes' if os.getenv('FLASK_ENV') == 'production' else 'No'}")
    print(f"FORCE_HTTPS: {'Yes' if os.getenv('FLASK_ENV') == 'production' else 'No'}")
    print()
    
    app.run(host='0.0.0.0', port=port, debug=debug) 


def create_app(config_name: str = None) -> Flask:
    """
    Minimal application factory to satisfy tests expecting backend.app.create_app.
    Reuses the already-configured module-level Flask app.
    """
    return app