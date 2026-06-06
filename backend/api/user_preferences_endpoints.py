"""
User Preferences API endpoints for the React frontend
Provides endpoints for managing user meme preferences and settings
"""

import os
import psycopg2
import psycopg2.extras
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
user_preferences_api = Blueprint('user_preferences_api', __name__, url_prefix='/api')

def get_db_connection():
    """Get PostgreSQL database connection"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

def ensure_user_preferences_table():
    """Ensure the user_meme_preferences table exists"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create user_meme_preferences table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_meme_preferences (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE,
                preferences TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_meme_preferences_user_id 
            ON user_meme_preferences(user_id)
        ''')
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logger.error(f"Error ensuring user preferences table: {e}")
        raise InternalServerError("Database setup failed")

def get_user_meme_preferences(user_id):
    """
    Get meme preferences for a specific user
    """
    try:
        ensure_user_preferences_table()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT preferences FROM user_meme_preferences 
            WHERE user_id = %s
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result['preferences'])
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error fetching user preferences: {e}")
        raise InternalServerError("Failed to fetch preferences")

def save_user_meme_preferences(user_id, preferences):
    """
    Save meme preferences for a specific user
    """
    try:
        ensure_user_preferences_table()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Validate preferences structure
        validate_preferences(preferences)
        
        preferences_json = json.dumps(preferences)
        
        # Upsert preferences for both new and existing users
        cursor.execute('''
            INSERT INTO user_meme_preferences (user_id, preferences, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET
                preferences = EXCLUDED.preferences,
                updated_at = EXCLUDED.updated_at
        ''', (user_id, preferences_json))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Preferences saved for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error saving user preferences: {e}")
        raise InternalServerError("Failed to save preferences")

def validate_preferences(preferences):
    """
    Validate the structure of user preferences
    """
    if not isinstance(preferences, dict):
        raise BadRequest("Preferences must be a JSON object")
    
    # Check required fields
    required_fields = ['enabled', 'categories', 'frequency']
    for field in required_fields:
        if field not in preferences:
            raise BadRequest(f"Missing required field: {field}")
    
    # Validate enabled field
    if not isinstance(preferences['enabled'], bool):
        raise BadRequest("'enabled' must be a boolean")
    
    # Validate categories
    if not isinstance(preferences['categories'], dict):
        raise BadRequest("'categories' must be an object")
    
    valid_categories = ['faith', 'work_life', 'friendships', 'children', 'relationships', 'going_out']
    for category in valid_categories:
        if category not in preferences['categories']:
            raise BadRequest(f"Missing category: {category}")
        if not isinstance(preferences['categories'][category], bool):
            raise BadRequest(f"Category '{category}' must be a boolean")
    
    # Validate frequency
    valid_frequencies = ['every_login', 'once_per_day', 'weekly']
    if preferences['frequency'] not in valid_frequencies:
        raise BadRequest(f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}")

@user_preferences_api.route('/user-meme-preferences/<user_id>', methods=['GET'])
def get_user_meme_preferences_endpoint(user_id):
    """
    GET /api/user-meme-preferences/<user_id>
    Returns meme preferences for the specified user
    """
    try:
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            raise BadRequest("Valid user ID is required")
        
        # Get preferences
        preferences = get_user_meme_preferences(user_id)
        
        if preferences is None:
            return jsonify({
                'error': 'Preferences not found',
                'message': 'No preferences found for this user'
            }), 404
        
        return jsonify({
            'success': True,
            'preferences': preferences
        })
        
    except BadRequest as e:
        return jsonify({
            'error': 'Bad request',
            'message': str(e)
        }), 400
        
    except InternalServerError as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in get_user_meme_preferences_endpoint: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

@user_preferences_api.route('/user-meme-preferences/<user_id>', methods=['PUT'])
def save_user_meme_preferences_endpoint(user_id):
    """
    PUT /api/user-meme-preferences/<user_id>
    Saves meme preferences for the specified user
    """
    try:
        # Validate request
        if not request.is_json:
            raise BadRequest('Request must be JSON')
        
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            raise BadRequest("Valid user ID is required")
        
        data = request.get_json()
        
        # Validate required fields
        if 'preferences' not in data:
            raise BadRequest('Missing required field: preferences')
        
        preferences = data['preferences']
        
        # Save preferences
        save_user_meme_preferences(user_id, preferences)
        
        return jsonify({
            'success': True,
            'message': 'Preferences saved successfully',
            'preferences': preferences
        })
        
    except BadRequest as e:
        return jsonify({
            'error': 'Bad request',
            'message': str(e)
        }), 400
        
    except InternalServerError as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in save_user_meme_preferences_endpoint: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

@user_preferences_api.route('/user-meme-preferences/<user_id>', methods=['DELETE'])
def delete_user_meme_preferences_endpoint(user_id):
    """
    DELETE /api/user-meme-preferences/<user_id>
    Deletes meme preferences for the specified user (resets to defaults)
    """
    try:
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            raise BadRequest("Valid user ID is required")
        
        ensure_user_preferences_table()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete user preferences
        cursor.execute('''
            DELETE FROM user_meme_preferences WHERE user_id = %s
        ''', (user_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                'error': 'Preferences not found',
                'message': 'No preferences found for this user'
            }), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Preferences deleted successfully'
        })
        
    except BadRequest as e:
        return jsonify({
            'error': 'Bad request',
            'message': str(e)
        }), 400
        
    except InternalServerError as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in delete_user_meme_preferences_endpoint: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers
@user_preferences_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404

@user_preferences_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500
