from flask import Blueprint, request, jsonify, g
import psycopg2
import psycopg2.extras
from datetime import datetime
import os
from loguru import logger

from backend.auth.decorators import require_auth

quick_setup_api = Blueprint('quick_setup_api', __name__)


@quick_setup_api.route('/api/profile/quick-setup', methods=['POST'])
@require_auth
def quick_setup():
    """Handle quick profile setup with minimal required fields."""
    conn = None
    try:
        user_id = getattr(g, 'current_user_id', None)
        email = getattr(g, 'current_user_email', None) or ''
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        income_range = (
            data.get('income_range')
            or data.get('incomeRange')
            or ''
        )
        if isinstance(income_range, str):
            income_range = income_range.strip()
        else:
            income_range = str(income_range).strip()

        primary_goal = (
            data.get('primary_goal')
            or data.get('primaryGoal')
            or ''
        )
        if isinstance(primary_goal, str):
            primary_goal = primary_goal.strip()
        else:
            primary_goal = str(primary_goal).strip()

        loc = data.get('location')
        if loc is None:
            location = ''
        elif isinstance(loc, str):
            location = loc.strip()
        else:
            location = str(loc).strip()

        if not income_range or not primary_goal:
            return jsonify({'error': 'income range and primary goal are required'}), 400

        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return jsonify({'error': 'Database not configured'}), 500
        conn = psycopg2.connect(db_url)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        cursor = conn.cursor()

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

        cursor.execute('SELECT id FROM user_profiles WHERE user_id = %s', (str(user_id),))
        existing = cursor.fetchone()

        if existing:
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
                str(user_id),
            ))
        else:
            cursor.execute('''
                INSERT INTO user_profiles
                (user_id, email, income_range, location, primary_goal, setup_completed, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                str(user_id),
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
        conn = None

        logger.info('Quick setup completed for user: {}', user_id)

        return jsonify({
            'success': True,
            'message': 'Profile setup completed'
        }), 200

    except psycopg2.Error as e:
        if conn is not None:
            conn.rollback()
            conn.close()
        logger.error('Database error in quick_setup: {}', e)
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        if conn is not None:
            conn.rollback()
            conn.close()
        logger.error('Error in quick_setup: {}', e, exc_info=True)
        return jsonify({'error': str(e)}), 500
