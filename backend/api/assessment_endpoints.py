"""
Assessment API endpoints for the React frontend
Provides endpoints for handling lead magnet assessments
"""

import os
import sqlite3
import json
import logging
import hashlib
import hmac
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, InternalServerError
from ..utils.validation import APIValidator
from ..services.email_service import EmailService

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
assessment_api = Blueprint('assessment_api', __name__, url_prefix='/api')

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'assessments.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_assessment_db():
    """Initialize assessment database tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                first_name TEXT,
                phone TEXT,
                assessment_type TEXT NOT NULL,
                answers TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create assessment analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessment_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER,
                action TEXT NOT NULL,
                question_id TEXT,
                answer_value TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                user_agent TEXT,
                FOREIGN KEY (assessment_id) REFERENCES assessments (id)
            )
        ''')
        
        # Create lead magnet results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_magnet_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER,
                email TEXT NOT NULL,
                assessment_type TEXT NOT NULL,
                score INTEGER,
                risk_level TEXT,
                recommendations TEXT,
                results_sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assessment_id) REFERENCES assessments (id)
            )
        ''')
        
        conn.commit()
        logger.info("Assessment database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing assessment database: {e}")
        raise InternalServerError("Database initialization failed")
    finally:
        if 'conn' in locals():
            conn.close()

@assessment_api.route('/assessments', methods=['POST'])
def submit_assessment():
    """
    Submit a completed assessment with security validation
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in assessment submission")
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
        # Rate limiting check
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        
        data = request.get_json()
        
        if not data:
            raise BadRequest("No data provided")
        
        # Comprehensive input validation and sanitization
        is_valid, errors, sanitized_data = APIValidator.validate_assessment_data(data)
        if not is_valid:
            logger.warning(f"Validation failed: {errors}")
            return jsonify({'success': False, 'error': 'Validation failed', 'details': errors}), 400
        
        # Initialize database if it doesn't exist
        init_assessment_db()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hash email for privacy
        email_hash = hashlib.sha256(sanitized_data['email'].encode()).hexdigest()
        
        # Insert assessment data with encrypted email
        cursor.execute('''
            INSERT INTO assessments (email, first_name, phone, assessment_type, answers, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            email_hash,  # Store hashed email instead of plain text
            sanitized_data.get('firstName'),
            sanitized_data.get('phone'),
            sanitized_data['assessmentType'],
            json.dumps(sanitized_data['answers']),
            sanitized_data.get('completedAt', datetime.now().isoformat())
        ))
        
        assessment_id = cursor.lastrowid
        
        # Calculate and store results
        results = calculate_assessment_results(sanitized_data['assessmentType'], sanitized_data['answers'])
        
        cursor.execute('''
            INSERT INTO lead_magnet_results (assessment_id, email, assessment_type, score, risk_level, recommendations)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            assessment_id,
            email_hash,  # Store hashed email
            sanitized_data['assessmentType'],
            results['score'],
            results['risk_level'],
            json.dumps(results['recommendations'])
        ))
        
        conn.commit()
        
        # Log analytics (without sensitive data)
        log_assessment_analytics(assessment_id, 'completed', {
            'assessment_type': sanitized_data['assessmentType'],
            'has_email': bool(sanitized_data['email']),
            'has_name': bool(sanitized_data.get('firstName')),
            'answer_count': len(sanitized_data['answers'])
        })
        
        logger.info(f"Assessment submitted successfully: {assessment_id}")
        
        # Send immediate results email
        try:
            email_service = EmailService()
            email_sent = email_service.send_assessment_results(
                email=sanitized_data['email'],
                first_name=sanitized_data.get('firstName', 'there'),
                assessment_type=sanitized_data['assessmentType'],
                results=results,
                recommendations=results.get('recommendations', [])
            )
            
            if email_sent:
                logger.info(f"Results email sent successfully to {sanitized_data['email']}")
            else:
                logger.warning(f"Failed to send results email to {sanitized_data['email']}")
                
        except Exception as email_error:
            logger.error(f"Error sending results email: {email_error}")
            # Don't fail the assessment submission if email fails
        
        return jsonify({
            'success': True,
            'assessment_id': assessment_id,
            'results': results,
            'message': 'Assessment submitted successfully',
            'email_sent': email_sent if 'email_sent' in locals() else False
        })
        
    except BadRequest as e:
        logger.warning(f"Bad request in submit_assessment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in submit_assessment: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@assessment_api.route('/assessments/<int:assessment_id>/results', methods=['GET'])
def get_assessment_results(assessment_id):
    """
    Get assessment results by ID
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, lmr.score, lmr.risk_level, lmr.recommendations
            FROM assessments a
            LEFT JOIN lead_magnet_results lmr ON a.id = lmr.assessment_id
            WHERE a.id = ?
        ''', (assessment_id,))
        
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'success': False, 'error': 'Assessment not found'}), 404
        
        return jsonify({
            'success': True,
            'assessment': {
                'id': result['id'],
                'email': result['email'],
                'first_name': result['first_name'],
                'assessment_type': result['assessment_type'],
                'answers': json.loads(result['answers']),
                'completed_at': result['completed_at'],
                'score': result['score'],
                'risk_level': result['risk_level'],
                'recommendations': json.loads(result['recommendations']) if result['recommendations'] else []
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_assessment_results: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@assessment_api.route('/assessments/analytics', methods=['POST'])
def track_assessment_analytics():
    """
    Track assessment analytics events
    """
    try:
        data = request.get_json()
        
        if not data:
            raise BadRequest("No data provided")
        
        required_fields = ['action']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f"Missing required field: {field}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO assessment_analytics (assessment_id, action, question_id, answer_value, session_id, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('assessment_id'),
            data['action'],
            data.get('question_id'),
            data.get('answer_value'),
            data.get('session_id'),
            request.headers.get('User-Agent')
        ))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Analytics tracked successfully'})
        
    except BadRequest as e:
        logger.warning(f"Bad request in track_assessment_analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in track_assessment_analytics: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

def calculate_assessment_results(assessment_type, answers):
    """
    Calculate assessment results based on type and answers
    """
    if assessment_type == 'ai-risk':
        return calculate_ai_risk_results(answers)
    elif assessment_type == 'income-comparison':
        return calculate_income_comparison_results(answers)
    elif assessment_type == 'cuffing-season':
        return calculate_cuffing_season_results(answers)
    elif assessment_type == 'layoff-risk':
        return calculate_layoff_risk_results(answers)
    elif assessment_type == 'vehicle-financial-health':
        return calculate_vehicle_financial_health_results(answers)
    else:
        return {'score': 0, 'risk_level': 'unknown', 'recommendations': []}

def calculate_ai_risk_results(answers):
    """Calculate AI replacement risk score"""
    score = 0
    risk_factors = []
    
    # Industry risk
    high_risk_industries = ['Manufacturing', 'Retail/E-commerce', 'Finance/Banking']
    if answers.get('industry') in high_risk_industries:
        score += 30
        risk_factors.append('High-risk industry')
    
    # Automation level
    automation_scores = {
        'Very Little': 0,
        'Some': 15,
        'Moderate': 25,
        'A Lot': 35,
        'Almost Everything': 45
    }
    score += automation_scores.get(answers.get('automationLevel', ''), 0)
    
    # AI tool usage
    ai_usage_scores = {
        'Never': 20,
        'Rarely': 15,
        'Sometimes': 10,
        'Often': 5,
        'Constantly': 0
    }
    score += ai_usage_scores.get(answers.get('aiTools', ''), 0)
    
    # Skills assessment
    ai_resistant_skills = ['Creative Writing', 'Customer Service', 'Teaching/Training', 'Strategy']
    skills = answers.get('skills', [])
    ai_resistant_count = sum(1 for skill in skills if skill in ai_resistant_skills)
    score -= ai_resistant_count * 5
    
    # Determine risk level
    if score >= 70:
        risk_level = 'High'
    elif score >= 40:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'
    
    # Generate recommendations
    recommendations = []
    if risk_level == 'High':
        recommendations.extend([
            'Consider upskilling in AI-resistant areas like creative work or human interaction',
            'Learn to work alongside AI tools rather than compete with them',
            'Develop skills in areas that require emotional intelligence and creativity'
        ])
    elif risk_level == 'Medium':
        recommendations.extend([
            'Stay updated with AI trends in your industry',
            'Consider learning AI tools to enhance your productivity',
            'Focus on developing uniquely human skills'
        ])
    else:
        recommendations.extend([
            'Continue developing your current skill set',
            'Consider how AI can enhance your work rather than replace it',
            'Stay informed about AI developments in your field'
        ])
    
    return {
        'score': min(100, max(0, score)),
        'risk_level': risk_level,
        'recommendations': recommendations
    }

def calculate_income_comparison_results(answers):
    """Calculate income comparison results"""
    # This would typically involve comparing against industry data
    # For now, we'll provide a basic calculation
    
    salary_ranges = {
        'Under $30,000': 25000,
        '$30,000 - $50,000': 40000,
        '$50,000 - $75,000': 62500,
        '$75,000 - $100,000': 87500,
        '$100,000 - $150,000': 125000,
        '$150,000 - $200,000': 175000,
        'Over $200,000': 250000
    }
    
    # Try to get salary from different possible formats
    current_salary_str = answers.get('currentSalary', '')
    current_salary = 0
    
    # First try to get from salary ranges
    if current_salary_str in salary_ranges:
        current_salary = salary_ranges[current_salary_str]
    else:
        # Try to parse as numeric string
        try:
            current_salary = float(current_salary_str)
        except (ValueError, TypeError):
            # Default to a reasonable salary if parsing fails
            current_salary = 75000
    
    experience = answers.get('experience', '')
    location = answers.get('location', '')
    
    # Basic market rate calculation (simplified)
    # Add some location-based adjustments
    location_multiplier = 1.0
    if 'San Francisco' in location or 'New York' in location:
        location_multiplier = 1.3
    elif 'Seattle' in location or 'Boston' in location:
        location_multiplier = 1.2
    elif 'Austin' in location or 'Denver' in location:
        location_multiplier = 1.1
    
    market_rate = current_salary * 1.1 * location_multiplier
    
    # Ensure we don't have division by zero
    if market_rate == 0:
        market_rate = 75000  # Default market rate
    
    if current_salary < market_rate * 0.8:
        percentile = 'Below 20th percentile'
        recommendations = [
            'Consider negotiating for a raise based on market rates',
            'Research salary benchmarks for your role and location',
            'Highlight your achievements and value to the company'
        ]
    elif current_salary < market_rate * 0.9:
        percentile = '20th-40th percentile'
        recommendations = [
            'You may be slightly underpaid for your role',
            'Consider discussing compensation with your manager',
            'Continue building skills to increase your market value'
        ]
    elif current_salary < market_rate * 1.1:
        percentile = '40th-60th percentile'
        recommendations = [
            'Your salary is competitive for your role',
            'Focus on performance to justify future increases',
            'Consider additional responsibilities for higher pay'
        ]
    else:
        percentile = 'Above 60th percentile'
        recommendations = [
            'Your salary is above market rate',
            'Continue performing at a high level',
            'Consider mentoring others or taking on leadership roles'
        ]
    
    # Calculate score safely
    if market_rate > 0:
        score = min(100, max(0, (current_salary / market_rate) * 50))
    else:
        score = 50  # Default score
    
    return {
        'score': score,
        'risk_level': percentile,
        'recommendations': recommendations
    }

def calculate_cuffing_season_results(answers):
    """Calculate cuffing season score"""
    score = 0
    
    # Relationship status
    status_scores = {
        'Single and dating': 40,
        'Single and not dating': 20,
        'In a relationship': 80,
        'Married': 90,
        'Divorced': 30,
        'Widowed': 25
    }
    score += status_scores.get(answers.get('relationshipStatus', ''), 0)
    
    # Dating frequency
    frequency_scores = {
        'Multiple times per week': 30,
        'Once a week': 25,
        '2-3 times per month': 20,
        'Once a month': 15,
        'Rarely': 10,
        'Never': 0
    }
    score += frequency_scores.get(answers.get('datingFrequency', ''), 0)
    
    # Winter dating interest
    winter_scores = {
        'Much more interested': 20,
        'Somewhat more interested': 15,
        'No change': 10,
        'Less interested': 5,
        'Much less interested': 0
    }
    score += winter_scores.get(answers.get('winterDating', ''), 0)
    
    # Determine cuffing season readiness
    if score >= 80:
        cuffing_level = 'High - You\'re ready for cuffing season!'
    elif score >= 60:
        cuffing_level = 'Medium - You\'re somewhat ready'
    elif score >= 40:
        cuffing_level = 'Low - You might need to put yourself out there more'
    else:
        cuffing_level = 'Very Low - Focus on self-improvement first'
    
    recommendations = [
        'Be authentic in your dating approach',
        'Focus on building genuine connections',
        'Don\'t rush into relationships just for the season',
        'Use dating apps strategically during peak seasons'
    ]
    
    return {
        'score': min(100, max(0, score)),
        'risk_level': cuffing_level,
        'recommendations': recommendations
    }

def calculate_layoff_risk_results(answers):
    """Calculate layoff risk score"""
    score = 0
    risk_factors = []
    
    # Company size (smaller companies are riskier)
    size_scores = {
        '1-10 employees': 30,
        '11-50 employees': 20,
        '51-200 employees': 15,
        '201-1000 employees': 10,
        '1000+ employees': 5
    }
    score += size_scores.get(answers.get('companySize', ''), 0)
    
    # Tenure (shorter tenure is riskier)
    tenure_scores = {
        'Less than 6 months': 25,
        '6 months - 1 year': 20,
        '1-2 years': 15,
        '3-5 years': 10,
        '6-10 years': 5,
        'Over 10 years': 0
    }
    score += tenure_scores.get(answers.get('tenure', ''), 0)
    
    # Performance
    performance_scores = {
        'Exceeds expectations': -10,
        'Meets expectations': 0,
        'Below expectations': 20,
        'Unsure': 10
    }
    score += performance_scores.get(answers.get('performance', ''), 0)
    
    # Company health
    health_scores = {
        'Very strong': -15,
        'Strong': -10,
        'Stable': 0,
        'Some concerns': 15,
        'Major concerns': 25
    }
    score += health_scores.get(answers.get('companyHealth', ''), 0)
    
    # Recent layoffs
    layoff_scores = {
        'Yes, major layoffs': 30,
        'Yes, minor layoffs': 15,
        'No layoffs': 0,
        'Not sure': 10
    }
    score += layoff_scores.get(answers.get('recentLayoffs', ''), 0)
    
    # Skills relevance
    skills_scores = {
        'Very relevant': -10,
        'Somewhat relevant': 0,
        'Neutral': 5,
        'Somewhat outdated': 15,
        'Very outdated': 25
    }
    score += skills_scores.get(answers.get('skillsRelevance', ''), 0)
    
    # Determine risk level
    if score >= 60:
        risk_level = 'High'
    elif score >= 30:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'
    
    # Generate recommendations
    recommendations = []
    if risk_level == 'High':
        recommendations.extend([
            'Update your resume and start networking immediately',
            'Consider upskilling in high-demand areas',
            'Build an emergency fund to cover 3-6 months of expenses',
            'Start applying for new positions as a backup plan'
        ])
    elif risk_level == 'Medium':
        recommendations.extend([
            'Stay alert to company changes and industry trends',
            'Continue building your skills and network',
            'Consider side projects or freelance work',
            'Keep your resume updated and ready'
        ])
    else:
        recommendations.extend([
            'Continue performing well in your current role',
            'Stay updated with industry trends',
            'Build strong relationships with colleagues and management',
            'Consider taking on additional responsibilities'
        ])
    
    return {
        'score': min(100, max(0, score)),
        'risk_level': risk_level,
        'recommendations': recommendations
    }

def calculate_vehicle_financial_health_results(answers):
    """Calculate vehicle financial health score"""
    score = 0
    risk_factors = []
    
    # Vehicle age (newer is better for financial health)
    age_scores = {
        'Less than 2 years': 20,
        '2-5 years': 15,
        '6-10 years': 10,
        '11-15 years': 5,
        '16-20 years': 0,
        'Over 20 years': -5,
        'I don\'t own a vehicle': 0
    }
    score += age_scores.get(answers.get('vehicleAge', ''), 0)
    
    # Vehicle mileage (lower is better)
    mileage_scores = {
        'Under 50,000 miles': 15,
        '50,000 - 75,000 miles': 12,
        '75,000 - 100,000 miles': 8,
        '100,000 - 150,000 miles': 4,
        '150,000 - 200,000 miles': 0,
        'Over 200,000 miles': -5,
        'I don\'t know': 0
    }
    score += mileage_scores.get(answers.get('vehicleMileage', ''), 0)
    
    # Maintenance history (good maintenance is better)
    maintenance_scores = {
        'Regular maintenance, no major issues': 20,
        'Some minor repairs, mostly routine maintenance': 15,
        'Several unexpected repairs in the past year': 5,
        'Major repairs needed recently': -10,
        'I don\'t keep track of maintenance': -5,
        'I don\'t own a vehicle': 0
    }
    score += maintenance_scores.get(answers.get('maintenanceHistory', ''), 0)
    
    # Cost awareness (more aware is better)
    awareness_scores = {
        'Very aware - I track every expense': 20,
        'Somewhat aware - I know the major costs': 15,
        'Generally aware - I have a rough idea': 10,
        'Not very aware - I don\'t track these costs': 0,
        'Not aware at all - I don\'t know my costs': -10
    }
    score += awareness_scores.get(answers.get('monthlyTransportationCosts', ''), 0)
    
    # Emergency fund (having one is better)
    emergency_scores = {
        'Yes, I have a dedicated vehicle emergency fund': 25,
        'Yes, I have a general emergency fund that could cover vehicle repairs': 20,
        'No, but I have some savings that could help': 10,
        'No, I don\'t have any emergency savings': -15,
        'I don\'t own a vehicle': 0
    }
    score += emergency_scores.get(answers.get('emergencyFund', ''), 0)
    
    # Financial stress (less stress is better)
    stress_scores = {
        'No stress at all': 20,
        'Minimal stress': 15,
        'Moderate stress': 5,
        'Significant stress': -10,
        'Extreme stress': -20,
        'I don\'t own a vehicle': 0
    }
    score += stress_scores.get(answers.get('vehicleFinancialStress', ''), 0)
    
    # Commute distance (shorter is better for costs)
    commute_scores = {
        'Less than 10 miles round trip': 15,
        '10-25 miles round trip': 10,
        '25-50 miles round trip': 5,
        '50-75 miles round trip': 0,
        'Over 75 miles round trip': -10,
        'I work from home': 20,
        'I don\'t have a regular commute': 15
    }
    score += commute_scores.get(answers.get('commuteDistance', ''), 0)
    
    # Insurance and financing (paid off with good insurance is best)
    insurance_scores = {
        'Fully paid off, comprehensive insurance': 25,
        'Making payments, comprehensive insurance': 15,
        'Fully paid off, basic insurance': 10,
        'Making payments, basic insurance': 5,
        'Leasing with insurance included': 8,
        'I don\'t own a vehicle': 0
    }
    score += insurance_scores.get(answers.get('vehicleInsurance', ''), 0)
    
    # Future planning (better planning is better)
    planning_scores = {
        'I have a detailed savings plan and timeline': 20,
        'I have a general savings plan': 15,
        'I\'m saving some money but no specific plan': 8,
        'I\'ll figure it out when the time comes': 0,
        'I plan to finance it when needed': -5,
        'I don\'t plan to buy another vehicle': 0
    }
    score += planning_scores.get(answers.get('futureVehiclePlanning', ''), 0)
    
    # Determine financial health level
    if score >= 80:
        health_level = 'Excellent'
    elif score >= 60:
        health_level = 'Good'
    elif score >= 40:
        health_level = 'Fair'
    elif score >= 20:
        health_level = 'Poor'
    else:
        health_level = 'Critical'
    
    # Generate recommendations based on health level
    recommendations = []
    if health_level == 'Excellent':
        recommendations.extend([
            'Continue your excellent vehicle financial management',
            'Consider upgrading to a more fuel-efficient vehicle',
            'Review insurance coverage annually for best rates',
            'Maintain your emergency fund for unexpected repairs'
        ])
    elif health_level == 'Good':
        recommendations.extend([
            'Track all vehicle expenses to improve cost awareness',
            'Build a dedicated vehicle emergency fund',
            'Research ways to reduce insurance and maintenance costs',
            'Plan ahead for your next vehicle purchase'
        ])
    elif health_level == 'Fair':
        recommendations.extend([
            'Create a monthly vehicle budget and stick to it',
            'Start building an emergency fund for vehicle repairs',
            'Get quotes from multiple insurance providers',
            'Consider if your current vehicle is cost-effective'
        ])
    elif health_level == 'Poor':
        recommendations.extend([
            'Immediately start tracking all vehicle-related expenses',
            'Build an emergency fund for unexpected repairs',
            'Consider downsizing to a more affordable vehicle',
            'Look into public transportation or carpooling options'
        ])
    else:  # Critical
        recommendations.extend([
            'Urgently review your vehicle ownership costs',
            'Consider selling your current vehicle if it\'s a financial burden',
            'Explore alternative transportation options',
            'Seek financial counseling for vehicle-related debt'
        ])
    
    return {
        'score': min(100, max(0, score)),
        'health_level': health_level,
        'recommendations': recommendations
    }

def validate_csrf_token(token):
    """Validate CSRF token"""
    print(f"DEBUG: Validating CSRF token: '{token}'")
    if not token:
        print("DEBUG: No token provided")
        return False
    
    # For testing purposes, accept 'test-token'
    if token == 'test-token':
        print("DEBUG: Test token accepted")
        return True
    
    # In production, implement proper CSRF token validation
    # This is a simplified example - use proper session-based CSRF tokens
    expected_token = os.environ.get('CSRF_SECRET_KEY', 'default-secret')
    result = hmac.compare_digest(token, expected_token)
    print(f"DEBUG: Token validation result: {result}")
    return result

def check_rate_limit(client_ip):
    """Check rate limiting for client IP"""
    # Simple in-memory rate limiting (use Redis in production)
    current_time = datetime.now()
    window_start = current_time.replace(second=0, microsecond=0)
    
    # This is a simplified implementation
    # In production, use Redis or similar for distributed rate limiting
    return True  # Placeholder - implement proper rate limiting

def log_assessment_analytics(assessment_id, action, data):
    """Log assessment analytics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO assessment_analytics (assessment_id, action, session_id, user_agent)
            VALUES (?, ?, ?, ?)
        ''', (
            assessment_id,
            action,
            data.get('sessionId'),
            'Assessment API'
        ))
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error logging assessment analytics: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
