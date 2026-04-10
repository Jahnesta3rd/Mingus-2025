#!/usr/bin/env python3
"""
User API Endpoints for Mingus Application

Provides endpoints for user profile and setup status.
"""

import logging

from flask import Blueprint, jsonify, request, g
from flask_cors import cross_origin
from backend.auth.decorators import require_auth
from backend.api.profile_endpoints import get_db_connection

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/profile', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_user_profile():
    """Get user profile information"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        user_id = g.get('user_id') or g.get('current_user_id')
        user_email = getattr(g, 'current_user_email', None) or ''

        current_balance = None
        balance_last_updated = None
        if user_email:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    SELECT current_balance, balance_last_updated
                    FROM user_profiles WHERE email = %s
                    ''',
                    (user_email,),
                )
                row = cursor.fetchone()
                conn.close()
                if row:
                    if row.get('current_balance') is not None:
                        current_balance = float(row['current_balance'])
                    ts = row.get('balance_last_updated')
                    if ts is not None:
                        balance_last_updated = ts.isoformat()
            except Exception as e:
                logger.debug(f"Profile balance fields not loaded: {e}")

        return jsonify({
            'success': True,
            'profile': {
                'id': user_id or '',
                'email': user_email,
                'name': '',
                'tier': 'budget',
                'current_address': None,
                'vehicle_info': None,
                'preferences': None,
                'current_balance': current_balance,
                'balance_last_updated': balance_last_updated,
            }
        }), 200
    except Exception as e:
        return jsonify({'success': True, 'profile': {}}), 200

@user_bp.route('/balance', methods=['PATCH', 'OPTIONS'])
@cross_origin()
@require_auth
def patch_user_balance():
    """Update self-reported cash balance for the authenticated user."""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_email = getattr(g, 'current_user_email', None)
    if not user_email:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Request body must be JSON.'}), 400
    if 'current_balance' not in data:
        return jsonify({'error': 'current_balance is required.'}), 400

    raw = data['current_balance']
    try:
        if isinstance(raw, bool):
            raise ValueError('boolean')
        balance = float(raw)
    except (TypeError, ValueError):
        return jsonify({'error': 'current_balance must be a number.'}), 400

    if balance < -1_000_000 or balance > 100_000_000:
        return jsonify({
            'error': 'Balance must be between -$1,000,000 and $100,000,000.'
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            UPDATE user_profiles
            SET current_balance = %s, balance_last_updated = CURRENT_TIMESTAMP
            WHERE email = %s
            RETURNING current_balance, balance_last_updated
            ''',
            (balance, user_email),
        )
        row = cursor.fetchone()
        conn.commit()
        conn.close()
        if not row:
            return jsonify({'error': 'Profile not found.'}), 404

        ts = row['balance_last_updated']
        return jsonify({
            'success': True,
            'current_balance': float(row['current_balance']),
            'balance_last_updated': ts.isoformat() if ts else None,
        }), 200
    except Exception as e:
        logger.error(f"patch_user_balance failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/setup-status', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_setup_status():
    """Get user setup completion status"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        return jsonify({
            'success': True,
            'setupCompleted': True,
            'data': {
                'is_complete': True,
                'steps_completed': ['profile', 'preferences'],
                'current_step': None
            }
        }), 200
    except Exception as e:
        return jsonify({'success': True, 'setupCompleted': True, 'data': {'is_complete': True}}), 200

@user_bp.route('/tier', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_user_tier():
    """Get user subscription tier"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        return jsonify({
            'success': True,
            'data': {
                'tier': 'budget',
                'name': 'Budget',
                'price': 15
            }
        }), 200
    except Exception as e:
        return jsonify({'success': True, 'data': {'tier': 'budget', 'name': 'Budget', 'price': 15}}), 200
