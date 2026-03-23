from flask import Blueprint, request, jsonify, g
import psycopg2
import psycopg2.extras
from datetime import datetime
import os
import logging
import jwt

logger = logging.getLogger(__name__)

quick_setup_api = Blueprint('quick_setup_api', __name__)

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-jwt-secret-key')
JWT_ALGORITHM = 'HS256'

def get_user_from_token():
    """Extract user information from JWT token"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        return {
            'user_id': payload.get('user_id'),
            'email': payload.get('email')
        }
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token")
        return None
    except Exception as e:
        logger.error(f"Error extracting user from token: {e}")
        return None

@quick_setup_api.route('/api/profile/quick-setup', methods=['POST'])
def quick_setup():
    """Handle quick profile setup with minimal required fields"""
    try:
        # Authenticate user
        user_info = get_user_from_token()
        if not user_info:
            return jsonify({'error': 'Authentication required'}), 401
        
        user_id = user_info['user_id']
        email = user_info['email']
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        income_range = data.get('incomeRange', '')
        location = data.get('location', '').strip()
        primary_goal = data.get('primaryGoal', '')
        
        # Validate required fields
        if not all([income_range, location, primary_goal]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Get database connection
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return jsonify({'error': 'Database not configured'}), 500
        conn = psycopg2.connect(db_url)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                email TEXT,
                income_range TEXT,
                location TEXT,
                primary_goal TEXT,
                setup_completed INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(user_id)
            )
        ''')
        
        # Check if profile exists
        cursor.execute('SELECT id FROM user_profiles WHERE user_id = %s', (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing profile
            cursor.execute('''
                UPDATE user_profiles 
                SET income_range = %s, location = %s, primary_goal = %s, 
                    setup_completed = %s, updated_at = %s
                WHERE user_id = %s
            ''', (
                income_range,
                location,
                primary_goal,
                1,
                datetime.utcnow().isoformat(),
                user_id
            ))
        else:
            # Insert new profile
            cursor.execute('''
                INSERT INTO user_profiles 
                (user_id, email, income_range, location, primary_goal, setup_completed, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                email,
                income_range,
                location,
                primary_goal,
                1,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f'Quick setup completed for user: {user_id}')
        
        return jsonify({
            'success': True,
            'message': 'Profile setup completed'
        }), 200
        
    except psycopg2.Error as e:
        if 'conn' in locals():
            conn.rollback()
        logger.error(f'Database error in quick_setup: {e}')
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f'Error in quick_setup: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
