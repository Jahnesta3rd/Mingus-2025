"""
Weekly Check-in API endpoints for the React frontend
Provides endpoints for submitting and retrieving weekly check-in data
"""

import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, InternalServerError

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
weekly_checkin_api = Blueprint('weekly_checkin_api', __name__, url_prefix='/api')

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'mingus_memes.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_week_start_date(check_in_date):
    """Get the start of the week (Monday) for a given date"""
    date_obj = datetime.strptime(check_in_date, '%Y-%m-%d')
    # Get Monday of the week
    monday = date_obj - timedelta(days=date_obj.weekday())
    return monday.strftime('%Y-%m-%d')

@weekly_checkin_api.route('/weekly-checkin', methods=['POST'])
def submit_weekly_checkin():
    """
    POST /api/weekly-checkin
    Submit weekly check-in data including health and vehicle information
    """
    try:
        # Validate request
        if not request.is_json:
            raise BadRequest('Request must be JSON')
        
        data = request.get_json()
        
        # Get user identification
        user_id = request.headers.get('X-User-ID')
        session_id = request.headers.get('X-Session-ID')
        
        if not user_id:
            raise BadRequest('User ID is required')
        
        # Validate required fields
        required_fields = ['check_in_date']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f'Missing required field: {field}')
        
        # Get week start date
        week_start_date = get_week_start_date(data['check_in_date'])
        
        # Extract health and wellness data
        health_data = data.get('healthWellness', {})
        vehicle_data = data.get('vehicleWellness', {})
        
        # Validate health data
        physical_activity = health_data.get('physicalActivity', 0)
        relationship_satisfaction = health_data.get('relationshipSatisfaction', 0)
        meditation_minutes = health_data.get('meditationMinutes', 0)
        stress_spending = health_data.get('stressSpending', 0.0)
        
        # Validate vehicle data
        vehicle_expenses = vehicle_data.get('vehicleExpenses', 0.0)
        transportation_stress = vehicle_data.get('transportationStress', 0)
        commute_satisfaction = vehicle_data.get('commuteSatisfaction', 0)
        vehicle_decisions = vehicle_data.get('vehicleDecisions', '')
        
        # Validate ranges
        if not (0 <= physical_activity <= 20):
            raise BadRequest('Physical activity must be between 0 and 20')
        if not (1 <= relationship_satisfaction <= 10):
            raise BadRequest('Relationship satisfaction must be between 1 and 10')
        if not (0 <= meditation_minutes <= 1000):
            raise BadRequest('Meditation minutes must be between 0 and 1000')
        if not (0 <= stress_spending <= 10000):
            raise BadRequest('Stress spending must be between 0 and 10000')
        if not (0 <= vehicle_expenses <= 10000):
            raise BadRequest('Vehicle expenses must be between 0 and 10000')
        if not (1 <= transportation_stress <= 5):
            raise BadRequest('Transportation stress must be between 1 and 5')
        if not (1 <= commute_satisfaction <= 5):
            raise BadRequest('Commute satisfaction must be between 1 and 5')
        
        # Store check-in data
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create weekly_checkins table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT,
                check_in_date DATE NOT NULL,
                week_start_date DATE NOT NULL,
                physical_activity INTEGER DEFAULT 0,
                relationship_satisfaction INTEGER,
                meditation_minutes INTEGER DEFAULT 0,
                stress_spending DECIMAL(10,2) DEFAULT 0.0,
                vehicle_expenses DECIMAL(10,2) DEFAULT 0.0,
                transportation_stress INTEGER,
                commute_satisfaction INTEGER,
                vehicle_decisions TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, week_start_date)
            )
        ''')
        
        # Insert or update check-in data
        cursor.execute('''
            INSERT OR REPLACE INTO weekly_checkins 
            (user_id, session_id, check_in_date, week_start_date, 
             physical_activity, relationship_satisfaction, meditation_minutes, stress_spending,
             vehicle_expenses, transportation_stress, commute_satisfaction, vehicle_decisions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            session_id,
            data['check_in_date'],
            week_start_date,
            physical_activity,
            relationship_satisfaction,
            meditation_minutes,
            stress_spending,
            vehicle_expenses,
            transportation_stress,
            commute_satisfaction,
            vehicle_decisions
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Weekly check-in submitted: user_id={user_id}, week_start={week_start_date}")
        
        return jsonify({
            'success': True,
            'message': 'Weekly check-in submitted successfully',
            'week_start_date': week_start_date
        })
        
    except BadRequest as e:
        return jsonify({
            'error': 'Bad request',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error submitting weekly check-in: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to submit weekly check-in'
        }), 500

@weekly_checkin_api.route('/weekly-checkin/latest', methods=['GET'])
def get_latest_checkin():
    """
    GET /api/weekly-checkin/latest
    Get the latest weekly check-in for the user
    """
    try:
        user_id = request.headers.get('X-User-ID')
        
        if not user_id:
            return jsonify({
                'error': 'Bad request',
                'message': 'User ID is required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest check-in
        cursor.execute('''
            SELECT * FROM weekly_checkins 
            WHERE user_id = ? 
            ORDER BY check_in_date DESC 
            LIMIT 1
        ''', (user_id,))
        
        checkin = cursor.fetchone()
        conn.close()
        
        if not checkin:
            return jsonify({
                'error': 'Not found',
                'message': 'No check-in data found'
            }), 404
        
        # Format response
        checkin_data = dict(checkin)
        
        return jsonify({
            'success': True,
            'checkin': checkin_data
        })
        
    except Exception as e:
        logger.error(f"Error getting latest check-in: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to get latest check-in'
        }), 500

@weekly_checkin_api.route('/weekly-checkin/history', methods=['GET'])
def get_checkin_history():
    """
    GET /api/weekly-checkin/history
    Get check-in history for analytics
    """
    try:
        user_id = request.headers.get('X-User-ID')
        weeks = request.args.get('weeks', 12, type=int)  # Default to 12 weeks
        
        if not user_id:
            return jsonify({
                'error': 'Bad request',
                'message': 'User ID is required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get check-in history
        cursor.execute('''
            SELECT * FROM weekly_checkins 
            WHERE user_id = ? 
            ORDER BY check_in_date DESC 
            LIMIT ?
        ''', (user_id, weeks))
        
        checkins = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'checkins': checkins,
            'count': len(checkins)
        })
        
    except Exception as e:
        logger.error(f"Error getting check-in history: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to get check-in history'
        }), 500

@weekly_checkin_api.route('/weekly-checkin/analytics', methods=['GET'])
def get_checkin_analytics():
    """
    GET /api/weekly-checkin/analytics
    Get analytics and insights from check-in data
    """
    try:
        user_id = request.headers.get('X-User-ID')
        weeks = request.args.get('weeks', 12, type=int)
        
        if not user_id:
            return jsonify({
                'error': 'Bad request',
                'message': 'User ID is required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get check-in data for analysis
        cursor.execute('''
            SELECT * FROM weekly_checkins 
            WHERE user_id = ? 
            ORDER BY check_in_date DESC 
            LIMIT ?
        ''', (user_id, weeks))
        
        checkins = [dict(row) for row in cursor.fetchall()]
        
        if not checkins:
            return jsonify({
                'success': True,
                'analytics': {
                    'message': 'No data available for analysis',
                    'recommendations': []
                }
            })
        
        # Calculate analytics
        analytics = calculate_checkin_analytics(checkins)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting check-in analytics: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to get check-in analytics'
        }), 500

def calculate_checkin_analytics(checkins):
    """
    Calculate analytics and insights from check-in data
    """
    if not checkins:
        return {'message': 'No data available'}
    
    # Calculate averages
    total_checkins = len(checkins)
    
    # Health metrics
    avg_physical_activity = sum(c.get('physical_activity', 0) for c in checkins) / total_checkins
    avg_relationship_satisfaction = sum(c.get('relationship_satisfaction', 0) for c in checkins) / total_checkins
    avg_meditation_minutes = sum(c.get('meditation_minutes', 0) for c in checkins) / total_checkins
    avg_stress_spending = sum(c.get('stress_spending', 0) for c in checkins) / total_checkins
    
    # Vehicle metrics
    avg_vehicle_expenses = sum(c.get('vehicle_expenses', 0) for c in checkins) / total_checkins
    avg_transportation_stress = sum(c.get('transportation_stress', 0) for c in checkins) / total_checkins
    avg_commute_satisfaction = sum(c.get('commute_satisfaction', 0) for c in checkins) / total_checkins
    
    # Calculate trends
    health_trend = calculate_health_trend(checkins)
    vehicle_trend = calculate_vehicle_trend(checkins)
    
    # Generate recommendations
    recommendations = generate_recommendations(checkins, {
        'avg_physical_activity': avg_physical_activity,
        'avg_relationship_satisfaction': avg_relationship_satisfaction,
        'avg_meditation_minutes': avg_meditation_minutes,
        'avg_stress_spending': avg_stress_spending,
        'avg_vehicle_expenses': avg_vehicle_expenses,
        'avg_transportation_stress': avg_transportation_stress,
        'avg_commute_satisfaction': avg_commute_satisfaction
    })
    
    return {
        'summary': {
            'total_checkins': total_checkins,
            'date_range': {
                'start': checkins[-1]['check_in_date'],
                'end': checkins[0]['check_in_date']
            }
        },
        'health_metrics': {
            'avg_physical_activity': round(avg_physical_activity, 1),
            'avg_relationship_satisfaction': round(avg_relationship_satisfaction, 1),
            'avg_meditation_minutes': round(avg_meditation_minutes, 1),
            'avg_stress_spending': round(avg_stress_spending, 2),
            'trend': health_trend
        },
        'vehicle_metrics': {
            'avg_vehicle_expenses': round(avg_vehicle_expenses, 2),
            'avg_transportation_stress': round(avg_transportation_stress, 1),
            'avg_commute_satisfaction': round(avg_commute_satisfaction, 1),
            'trend': vehicle_trend
        },
        'recommendations': recommendations
    }

def calculate_health_trend(checkins):
    """Calculate health trend over time"""
    if len(checkins) < 2:
        return 'insufficient_data'
    
    # Simple trend calculation based on recent vs older data
    recent = checkins[:len(checkins)//2]
    older = checkins[len(checkins)//2:]
    
    recent_avg = sum(c.get('physical_activity', 0) for c in recent) / len(recent)
    older_avg = sum(c.get('physical_activity', 0) for c in older) / len(older)
    
    if recent_avg > older_avg * 1.1:
        return 'improving'
    elif recent_avg < older_avg * 0.9:
        return 'declining'
    else:
        return 'stable'

def calculate_vehicle_trend(checkins):
    """Calculate vehicle expense trend over time"""
    if len(checkins) < 2:
        return 'insufficient_data'
    
    recent = checkins[:len(checkins)//2]
    older = checkins[len(checkins)//2:]
    
    recent_avg = sum(c.get('vehicle_expenses', 0) for c in recent) / len(recent)
    older_avg = sum(c.get('vehicle_expenses', 0) for c in older) / len(older)
    
    if recent_avg > older_avg * 1.2:
        return 'increasing'
    elif recent_avg < older_avg * 0.8:
        return 'decreasing'
    else:
        return 'stable'

def generate_recommendations(checkins, metrics):
    """Generate personalized recommendations based on check-in data"""
    recommendations = []
    
    # Health recommendations
    if metrics['avg_physical_activity'] < 3:
        recommendations.append({
            'category': 'health',
            'priority': 'medium',
            'message': 'Consider increasing your physical activity to improve overall wellness',
            'action': 'Try to fit in at least 3 workouts per week'
        })
    
    if metrics['avg_relationship_satisfaction'] < 6:
        recommendations.append({
            'category': 'relationships',
            'priority': 'high',
            'message': 'Your relationship satisfaction seems low',
            'action': 'Consider having an open conversation with your partner or seeking support'
        })
    
    if metrics['avg_stress_spending'] > 100:
        recommendations.append({
            'category': 'financial',
            'priority': 'high',
            'message': 'High stress spending detected',
            'action': 'Try stress management techniques before making purchases'
        })
    
    # Vehicle recommendations
    if metrics['avg_vehicle_expenses'] > 200:
        recommendations.append({
            'category': 'vehicle',
            'priority': 'medium',
            'message': 'High vehicle expenses this month',
            'action': 'Consider setting up a vehicle maintenance fund'
        })
    
    if metrics['avg_transportation_stress'] > 3:
        recommendations.append({
            'category': 'transportation',
            'priority': 'medium',
            'message': 'High transportation stress detected',
            'action': 'Consider alternative routes or transportation methods'
        })
    
    if metrics['avg_commute_satisfaction'] < 3:
        recommendations.append({
            'category': 'commute',
            'priority': 'low',
            'message': 'Low commute satisfaction',
            'action': 'Consider carpooling, public transit, or remote work options'
        })
    
    return recommendations

# Error handlers
@weekly_checkin_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404

@weekly_checkin_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500
