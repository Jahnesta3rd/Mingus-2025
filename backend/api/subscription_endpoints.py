#!/usr/bin/env python3
"""
Subscription API Endpoints for Mingus Application

Provides endpoints for subscription tier information and management.
"""

from flask import Blueprint, jsonify, request, g
from flask_cors import cross_origin
from backend.auth.decorators import require_auth

subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/subscription')

@subscription_bp.route('/tier-info', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_tier_info():
    """Get user's subscription tier information"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    # Return default tier info
    # In production, this would fetch actual tier from database
    return jsonify({
        'success': True,
        'data': {
            'tier': 'budget',
            'name': 'Budget',
            'price': 15,
            'features': ['Basic budgeting', 'Expense tracking', 'Monthly reports']
        }
    }), 200
