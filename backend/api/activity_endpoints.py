#!/usr/bin/env python3
"""
Activity API Endpoints for Mingus Application

Provides endpoints for retrieving user activity and recent actions.
"""

from flask import Blueprint, jsonify, request, g
from flask_cors import cross_origin
from backend.auth.decorators import require_auth

activity_bp = Blueprint('activity', __name__, url_prefix='/api/activity')

@activity_bp.route('/recent', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_recent_activity():
    """Get recent user activity"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    # Return empty activities list
    # In production, this would fetch actual activity from database
    return jsonify({
        'success': True,
        'data': {
            'activities': []
        }
    }), 200
