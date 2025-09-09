"""
Meme API endpoints for the React frontend
Provides endpoints for fetching user memes and tracking analytics
"""

import os
import sqlite3
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, InternalServerError

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
meme_api = Blueprint('meme_api', __name__, url_prefix='/api')

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'mingus_memes.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_meme(user_id=None, session_id=None):
    """
    Get a random meme for the user
    Can be personalized based on user preferences in the future
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # For now, get a random active meme
        # In the future, this could be personalized based on:
        # - User preferences
        # - Time of day
        # - User demographics
        # - Previous meme interactions
        
        cursor.execute('''
            SELECT * FROM memes 
            WHERE is_active = 1 
            ORDER BY RANDOM() 
            LIMIT 1
        ''')
        
        meme = cursor.fetchone()
        conn.close()
        
        if not meme:
            return None
            
        return dict(meme)
        
    except Exception as e:
        logger.error(f"Error fetching user meme: {e}")
        raise InternalServerError("Failed to fetch meme")

def track_meme_analytics(meme_id, action, user_id=None, session_id=None):
    """
    Track meme interaction analytics
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create analytics table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meme_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meme_id INTEGER NOT NULL,
                action TEXT NOT NULL CHECK (action IN ('view', 'continue', 'skip', 'auto_advance')),
                user_id TEXT,
                session_id TEXT,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (meme_id) REFERENCES memes (id)
            )
        ''')
        
        # Insert analytics record
        cursor.execute('''
            INSERT INTO meme_analytics (meme_id, action, user_id, session_id, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            meme_id,
            action,
            user_id,
            session_id,
            request.remote_addr,
            request.headers.get('User-Agent', '')
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Analytics tracked: meme_id={meme_id}, action={action}, user_id={user_id}")
        
    except Exception as e:
        logger.error(f"Error tracking analytics: {e}")
        # Don't raise - analytics failure shouldn't break the user experience

@meme_api.route('/user-meme', methods=['GET'])
def get_user_meme_endpoint():
    """
    GET /api/user-meme
    Returns a random meme for the current user
    """
    try:
        # Get user identification from headers
        user_id = request.headers.get('X-User-ID')
        session_id = request.headers.get('X-Session-ID')
        
        # Get meme
        meme = get_user_meme(user_id, session_id)
        
        if not meme:
            return jsonify({
                'error': 'No memes available',
                'message': 'No active memes found in the database'
            }), 404
        
        # Track view analytics
        track_meme_analytics(meme['id'], 'view', user_id, session_id)
        
        return jsonify(meme)
        
    except InternalServerError as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in get_user_meme_endpoint: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

@meme_api.route('/meme-analytics', methods=['POST'])
def track_meme_analytics_endpoint():
    """
    POST /api/meme-analytics
    Tracks user interactions with memes
    """
    try:
        # Validate request
        if not request.is_json:
            raise BadRequest('Request must be JSON')
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['meme_id', 'action']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f'Missing required field: {field}')
        
        # Validate action
        valid_actions = ['view', 'continue', 'skip', 'auto_advance']
        if data['action'] not in valid_actions:
            raise BadRequest(f'Invalid action. Must be one of: {", ".join(valid_actions)}')
        
        # Validate meme_id
        try:
            meme_id = int(data['meme_id'])
        except (ValueError, TypeError):
            raise BadRequest('meme_id must be an integer')
        
        # Get optional fields
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        # Track analytics
        track_meme_analytics(meme_id, data['action'], user_id, session_id)
        
        return jsonify({
            'success': True,
            'message': 'Analytics tracked successfully'
        })
        
    except BadRequest as e:
        return jsonify({
            'error': 'Bad request',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in track_meme_analytics_endpoint: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

@meme_api.route('/meme-stats', methods=['GET'])
def get_meme_stats():
    """
    GET /api/meme-stats
    Returns statistics about meme usage (for admin purposes)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total memes
        cursor.execute('SELECT COUNT(*) as total FROM memes WHERE is_active = 1')
        total_memes = cursor.fetchone()['total']
        
        # Get analytics summary
        cursor.execute('''
            SELECT 
                action,
                COUNT(*) as count,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT session_id) as unique_sessions
            FROM meme_analytics 
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY action
        ''')
        
        analytics = [dict(row) for row in cursor.fetchall()]
        
        # Get most popular memes
        cursor.execute('''
            SELECT 
                m.id,
                m.caption,
                m.category,
                COUNT(a.id) as view_count
            FROM memes m
            LEFT JOIN meme_analytics a ON m.id = a.meme_id AND a.action = 'view'
            WHERE m.is_active = 1
            GROUP BY m.id
            ORDER BY view_count DESC
            LIMIT 10
        ''')
        
        popular_memes = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'total_memes': total_memes,
            'analytics_last_7_days': analytics,
            'popular_memes': popular_memes
        })
        
    except Exception as e:
        logger.error(f"Error getting meme stats: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to fetch statistics'
        }), 500

# Error handlers
@meme_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404

@meme_api.route('/meme-mood', methods=['POST'])
def track_meme_mood():
    """
    POST /api/meme-mood
    Tracks user mood response to memes
    """
    try:
        # Validate request
        if not request.is_json:
            raise BadRequest('Request must be JSON')
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['meme_id', 'mood_score', 'mood_label']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f'Missing required field: {field}')
        
        # Validate mood score
        mood_score = int(data['mood_score'])
        if not (1 <= mood_score <= 5):
            raise BadRequest('Mood score must be between 1 and 5')
        
        # Validate mood label
        valid_moods = ['excited', 'happy', 'neutral', 'sad', 'angry']
        if data['mood_label'] not in valid_moods:
            raise BadRequest(f'Invalid mood label. Must be one of: {", ".join(valid_moods)}')
        
        # Get user identification
        user_id = request.headers.get('X-User-ID')
        session_id = request.headers.get('X-Session-ID')
        
        if not user_id:
            raise BadRequest('User ID is required')
        
        # Store mood data
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_mood_data 
            (user_id, session_id, meme_id, mood_score, mood_label, meme_category, spending_context)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            session_id,
            data['meme_id'],
            mood_score,
            data['mood_label'],
            data.get('meme_category', 'unknown'),
            data.get('spending_context', 'before_budget_check')
        ))
        
        conn.commit()
        conn.close()
        
        # Calculate mood-spending correlation if user has spending data
        correlation = calculate_mood_spending_correlation(user_id)
        
        logger.info(f"Mood tracked: user_id={user_id}, meme_id={data['meme_id']}, mood={data['mood_label']}")
        
        return jsonify({
            'success': True,
            'message': 'Mood tracked successfully',
            'correlation': correlation
        })
        
    except BadRequest as e:
        return jsonify({
            'error': 'Bad request',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error tracking mood: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to track mood'
        }), 500

@meme_api.route('/mood-analytics', methods=['GET'])
def get_mood_analytics():
    """
    GET /api/mood-analytics
    Returns mood analytics and spending correlations
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
        
        # Get mood statistics
        cursor.execute("""
            SELECT 
                mood_label,
                COUNT(*) as count,
                AVG(mood_score) as avg_score
            FROM user_mood_data 
            WHERE user_id = ?
            GROUP BY mood_label
            ORDER BY count DESC
        """, (user_id,))
        
        mood_stats = [dict(row) for row in cursor.fetchall()]
        
        # Get spending correlation
        correlation = calculate_mood_spending_correlation(user_id)
        
        # Get mood trends (last 30 days)
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                AVG(mood_score) as avg_mood,
                COUNT(*) as mood_count
            FROM user_mood_data 
            WHERE user_id = ?
            AND timestamp >= datetime('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (user_id,))
        
        mood_trends = [dict(row) for row in cursor.fetchall()]
        
        # Get recent mood insights
        insights = generate_mood_insights(user_id)
        
        conn.close()
        
        return jsonify({
            'mood_statistics': mood_stats,
            'spending_correlation': correlation,
            'mood_trends': mood_trends,
            'insights': insights
        })
        
    except Exception as e:
        logger.error(f"Error getting mood analytics: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to fetch mood analytics'
        }), 500

def calculate_mood_spending_correlation(user_id):
    """
    Calculate correlation between mood and spending behavior
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get mood data for the last 30 days
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                AVG(mood_score) as avg_mood,
                COUNT(*) as mood_count
            FROM user_mood_data 
            WHERE user_id = ? 
            AND timestamp >= datetime('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (user_id,))
        
        mood_data = cursor.fetchall()
        
        # For now, return a mock correlation since we don't have spending data
        # In a real implementation, you would query the spending/transaction data
        if len(mood_data) < 2:
            return {
                'correlation_coefficient': 0.0,
                'pattern': 'insufficient_data',
                'data_points': len(mood_data),
                'confidence': 'low'
            }
        
        # Mock correlation calculation (replace with real spending data)
        avg_mood = sum(row['avg_mood'] for row in mood_data) / len(mood_data)
        
        # Simple pattern detection based on mood trends
        if avg_mood > 4.0:
            pattern = {
                'type': 'high_mood',
                'description': 'Generally positive mood detected',
                'risk_level': 'medium',
                'recommendation': 'monitor_for_impulse_spending'
            }
        elif avg_mood < 2.5:
            pattern = {
                'type': 'low_mood',
                'description': 'Generally negative mood detected',
                'risk_level': 'high',
                'recommendation': 'provide_emotional_support'
            }
        else:
            pattern = {
                'type': 'stable_mood',
                'description': 'Stable mood patterns',
                'risk_level': 'low',
                'recommendation': 'continue_monitoring'
            }
        
        conn.close()
        
        return {
            'correlation_coefficient': 0.0,  # Mock value
            'pattern': pattern,
            'data_points': len(mood_data),
            'confidence': 'medium' if len(mood_data) >= 7 else 'low'
        }
        
    except Exception as e:
        logger.error(f"Error calculating mood-spending correlation: {e}")
        return {
            'correlation_coefficient': 0.0,
            'pattern': 'error',
            'data_points': 0,
            'confidence': 'low'
        }

def generate_mood_insights(user_id):
    """
    Generate personalized mood insights
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get recent mood data
        cursor.execute("""
            SELECT mood_label, mood_score, timestamp, meme_category
            FROM user_mood_data 
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (user_id,))
        
        recent_moods = cursor.fetchall()
        
        if not recent_moods:
            return []
        
        insights = []
        
        # Analyze mood patterns
        mood_counts = {}
        for mood in recent_moods:
            label = mood['mood_label']
            mood_counts[label] = mood_counts.get(label, 0) + 1
        
        # Most common mood
        most_common = max(mood_counts.items(), key=lambda x: x[1])
        if most_common[1] >= 3:
            insights.append({
                'type': 'mood_pattern',
                'message': f'You\'ve been feeling {most_common[0]} frequently lately',
                'recommendation': get_mood_recommendation(most_common[0])
            })
        
        # Recent mood trend
        if len(recent_moods) >= 3:
            recent_scores = [m['mood_score'] for m in recent_moods[:3]]
            if all(score >= 4 for score in recent_scores):
                insights.append({
                    'type': 'positive_trend',
                    'message': 'You\'ve been in a great mood recently!',
                    'recommendation': 'Consider setting a spending reminder to avoid impulse purchases'
                })
            elif all(score <= 2 for score in recent_scores):
                insights.append({
                    'type': 'negative_trend',
                    'message': 'You\'ve been feeling down lately',
                    'recommendation': 'Take care of yourself and avoid emotional spending'
                })
        
        conn.close()
        return insights
        
    except Exception as e:
        logger.error(f"Error generating mood insights: {e}")
        return []

def get_mood_recommendation(mood):
    """
    Get recommendation based on mood
    """
    recommendations = {
        'excited': 'Consider setting a budget reminder to avoid impulse purchases',
        'happy': 'Great mood! Perfect time to review your financial goals',
        'neutral': 'Steady mood. Your budget is on track!',
        'sad': 'Remember, retail therapy can hurt your budget. Take care of yourself',
        'angry': 'Take a deep breath. Impulse spending won\'t solve the problem'
    }
    return recommendations.get(mood, 'Continue monitoring your mood and spending patterns')

@meme_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500
