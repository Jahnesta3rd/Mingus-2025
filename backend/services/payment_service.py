#!/usr/bin/env python3
"""Stripe Checkout for subscription module add-ons."""

from __future__ import annotations

import logging
import os
from typing import Any

import stripe

from backend.models.user_models import User
from backend.services.module_access_service import MODULE_IDS, grant_module

logger = logging.getLogger(__name__)

MODULE_PRICE_ENV_KEYS: dict[str, str] = {
    'vehicle_module': 'STRIPE_VEHICLE_MODULE_PRICE_ID',
    'housing_module': 'STRIPE_HOUSING_MODULE_PRICE_ID',
    'career_pro': 'STRIPE_CAREER_PRO_PRICE_ID',
    'family_addon': 'STRIPE_FAMILY_ADDON_PRICE_ID',
}


def get_module_price_id(module: str) -> str | None:
    """Resolve Stripe Price ID for a module key from environment."""
    env_key = MODULE_PRICE_ENV_KEYS.get(module)
    if not env_key:
        return None
    value = (os.environ.get(env_key) or '').strip()
    return value or None


def _frontend_base_url(fallback: str) -> str:
    base = (os.environ.get('FRONTEND_BASE_URL') or '').strip().rstrip('/')
    if base:
        return base
    return fallback.rstrip('/')


def create_module_checkout_session(
    user: User,
    module: str,
    *,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:
    """Create a Stripe Checkout Session for a recurring module add-on."""
    if module not in MODULE_IDS:
        raise ValueError(f'Unsupported module: {module}')

    price_id = get_module_price_id(module)
    if not price_id:
        raise ValueError(f'No Stripe price configured for module: {module}')

    return stripe.checkout.Session.create(
        mode='subscription',
        line_items=[{'price': price_id, 'quantity': 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            'module': module,
            'user_db_id': str(user.id),
            'user_external_id': user.user_id,
            'user_email': user.email or '',
        },
        client_reference_id=str(user.id),
    )


def handle_checkout_session_completed(session: dict[str, Any]) -> None:
    """Grant module access when Stripe checkout.session.completed fires."""
    metadata = session.get('metadata') or {}
    module = (metadata.get('module') or '').strip()
    if not module or module not in MODULE_IDS:
        logger.info(
            'checkout.session.completed without module metadata; skipping grant (session=%s)',
            session.get('id'),
        )
        return

    user_db_id = metadata.get('user_db_id')
    user_external_id = metadata.get('user_external_id')

    resolved_id: int | None = None
    if user_db_id is not None:
        try:
            resolved_id = int(user_db_id)
        except (TypeError, ValueError):
            logger.warning('Invalid user_db_id in checkout metadata: %s', user_db_id)

    if resolved_id is None and user_external_id:
        from backend.models.database import db

        user = db.session.query(User).filter_by(user_id=str(user_external_id)).first()
        if user:
            resolved_id = user.id

    if resolved_id is None:
        logger.error(
            'checkout.session.completed could not resolve user for module=%s metadata=%s',
            module,
            metadata,
        )
        return

    if grant_module(resolved_id, module):
        logger.info(
            'Granted module %s to user_id=%s via checkout.session.completed',
            module,
            resolved_id,
        )
    else:
        logger.error(
            'Failed to grant module %s to user_id=%s via checkout.session.completed',
            module,
            resolved_id,
        )
