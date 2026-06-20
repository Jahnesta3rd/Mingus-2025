#!/usr/bin/env python3
"""Authenticated user self-service endpoints (PATCH /api/user/me)."""

from flask import jsonify, request
from flask_cors import cross_origin
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from backend.auth.decorators import get_current_jwt_user, jwt_required
from backend.models.database import db
from backend.routes.user import user_bp

VALID_USER_RELATIONSHIP_STATUSES = frozenset({
    'single',
    'partnered',
    'married',
    'separated',
    'divorced',
    'widowed',
    'complicated',
})


@user_bp.route('/me', methods=['PATCH', 'OPTIONS'])
@cross_origin()
@jwt_required
def patch_current_user():
    """Update fields on the authenticated user's row in ``users``."""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user = get_current_jwt_user()
    if user is None:
        return jsonify({'success': False, 'error': 'User not found'}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Request body must be JSON.'}), 400

    if 'relationship_status' not in data:
        return jsonify({'success': False, 'error': 'No supported fields to update.'}), 400

    raw = data['relationship_status']
    if raw is None:
        value = None
    elif not isinstance(raw, str):
        return jsonify({
            'success': False,
            'error': 'relationship_status must be a string or null.',
        }), 400
    else:
        value = raw.strip().lower()
        if value not in VALID_USER_RELATIONSHIP_STATUSES:
            return jsonify({
                'success': False,
                'error': 'relationship_status is invalid.',
            }), 400

    try:
        db.session.execute(
            db.text(
                'UPDATE users SET relationship_status = :val, updated_at = CURRENT_TIMESTAMP '
                'WHERE id = :user_id'
            ),
            {'val': value, 'user_id': user.id},
        )
        db.session.commit()
    except SQLAlchemyError:
        logger.exception('Failed to update relationship_status user_id={}', user.id)
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to save.'}), 500

    return jsonify({'success': True}), 200
