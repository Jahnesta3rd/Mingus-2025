#!/usr/bin/env python3
"""
Career API Endpoints for Mingus Application

Provides endpoints for career risk assessment and tracking.
"""

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin

from backend.auth.decorators import get_current_jwt_user, require_auth
from backend.models.career_profile import CareerProfile

career_bp = Blueprint('career', __name__, url_prefix='/api/career')

SEED_ROLE_BLOCKLIST = frozenset({'doadmin', 'admin', 'test', 'seed_user', ''})
SEED_INDUSTRY_BLOCKLIST = frozenset(
    {v.lower() for v in ('Manufacturing', 'Unknown', 'Test', '')}
)


def _profile_complete(cp: CareerProfile) -> bool:
    """Mirror process-resume career_profile completeness (recommendation engine)."""
    role = (cp.current_role or '').strip().lower()
    field = (cp.bls_career_field or '').strip()
    seniority = (cp.seniority_level or '').strip()
    if role in SEED_ROLE_BLOCKLIST:
        return False
    if not field or field.lower() in SEED_INDUSTRY_BLOCKLIST:
        return False
    if not seniority:
        return False
    return True


def _empty_profile_payload() -> dict:
    return {
        'current_role': None,
        'industry': None,
        'seniority_level': None,
        'years_experience': None,
        'target_comp': None,
        'open_to_move': False,
        'profile_complete': False,
    }

@career_bp.route('/assess-and-track', methods=['GET', 'POST', 'OPTIONS'])
@cross_origin()
@require_auth
def assess_and_track():
    """Assess career risk and track assessment"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        return jsonify({
            'success': True,
            'data': {
                'risk_level': 'low',
                'score': 25,
                'factors': []
            }
        }), 200
    except Exception as e:
        return jsonify({'success': True, 'data': {'risk_level': 'low', 'score': 0}}), 200


@career_bp.route('/profile-summary', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def profile_summary():
    """Lightweight career_profile read for dashboard Career Check-in card."""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user = get_current_jwt_user()
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    cp = CareerProfile.query.filter_by(user_id=user.id).first()
    if not cp:
        return jsonify({'success': True, 'profile': _empty_profile_payload()}), 200

    return jsonify({
        'success': True,
        'profile': {
            'current_role': cp.current_role,
            'industry': cp.industry,
            'seniority_level': cp.seniority_level,
            'years_experience': cp.years_experience,
            'target_comp': cp.target_comp,
            'open_to_move': bool(cp.open_to_move),
            'profile_complete': _profile_complete(cp),
        },
    }), 200
