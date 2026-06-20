#!/usr/bin/env python3
"""Stripe module add-on checkout routes."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from backend.auth.decorators import get_current_jwt_user, require_auth
from backend.services.module_access_service import MODULE_IDS, has_module
from backend.services.payment_service import (
    create_module_checkout_session,
    get_module_price_id,
    _frontend_base_url,
)

logger = logging.getLogger(__name__)

payment_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


@payment_bp.route('/create-checkout-session', methods=['POST', 'OPTIONS'])
@require_auth
def create_checkout_session():
    """Create a Stripe Checkout Session for a subscription module add-on."""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    module = (data.get('module') or '').strip()

    if module not in MODULE_IDS:
        return jsonify({'success': False, 'error': 'Invalid or missing module.'}), 400

    if not get_module_price_id(module):
        return jsonify({
            'success': False,
            'error': f'Stripe price is not configured for module: {module}',
        }), 503

    user = get_current_jwt_user()
    if user is None:
        return jsonify({'success': False, 'error': 'User not found.'}), 404

    if has_module(user.id, module):
        return jsonify({
            'success': False,
            'error': 'Module already active for this account.',
        }), 400

    base = _frontend_base_url(request.host_url)
    from_param = (data.get('from') or '').strip()
    from_suffix = f'&from={from_param}' if from_param else ''
    success_url = f'{base}/dashboard/tools?checkout=success&module={module}{from_suffix}'
    cancel_url = f'{base}/dashboard/upgrade?module={module}'
    if from_param:
        cancel_url = f'{cancel_url}&from={from_param}'

    try:
        session = create_module_checkout_session(
            user,
            module,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return jsonify({
            'success': True,
            'url': session.url,
            'sessionId': session.id,
        }), 200
    except Exception as exc:
        logger.error('create-checkout-session failed for module=%s: %s', module, exc)
        return jsonify({
            'success': False,
            'error': 'Failed to create checkout session.',
        }), 500
