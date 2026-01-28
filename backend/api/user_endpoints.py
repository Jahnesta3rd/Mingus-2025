#!/usr/bin/env python3
"""
User API Endpoints for Mingus Application

Provides endpoints for user profile and setup status.
"""

from flask import Blueprint, jsonify, request, g
from flask_cors import cross_origin
from backend.auth.decorators import require_auth

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/profile', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_user_profile():
    """Get user profile information"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        user_id = g.get('user_id')
        return jsonify({
            'success': True,
            'profile': {
                'id': user_id or '',
                'email': '',
                'name': '',
                'tier': 'budget',
                'current_address': None,
                'vehicle_info': None,
                'preferences': None
            }
        }), 200
    except Exception as e:
        return jsonify({'success': True, 'profile': {}}), 200

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
