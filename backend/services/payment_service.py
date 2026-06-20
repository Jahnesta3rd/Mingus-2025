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

    session_metadata = {
        'module': module,
        'user_db_id': str(user.id),
        'user_external_id': user.user_id,
        'user_email': user.email or '',
    }
    return stripe.checkout.Session.create(
        mode='subscription',
        line_items=[{'price': price_id, 'quantity': 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=session_metadata,
        subscription_data={'metadata': session_metadata},
        client_reference_id=str(user.id),
    )


def _session_to_dict(session: Any) -> dict[str, Any]:
    if isinstance(session, dict):
        return session
    to_dict = getattr(session, 'to_dict', None)
    if callable(to_dict):
        return to_dict()
    return dict(session)


def resolve_checkout_session_from_payment_intent(intent: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve Checkout Session for a PaymentIntent (payment or subscription checkout)."""
    pi_id = intent.get('id')
    if not pi_id:
        return None

    try:
        sessions = stripe.checkout.Session.list(payment_intent=pi_id, limit=1)
        if sessions.data:
            return _session_to_dict(sessions.data[0])
    except stripe.error.StripeError as exc:
        logger.warning(
            'Could not list checkout sessions for payment_intent=%s: %s',
            pi_id,
            exc,
        )

    invoice_id = intent.get('invoice')
    if not invoice_id:
        return None

    try:
        invoice = stripe.Invoice.retrieve(invoice_id)
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return None
        sessions = stripe.checkout.Session.list(subscription=subscription_id, limit=1)
        if sessions.data:
            return _session_to_dict(sessions.data[0])
    except stripe.error.StripeError as exc:
        logger.warning(
            'Could not resolve checkout session from invoice for payment_intent=%s: %s',
            pi_id,
            exc,
        )

    return None


def handle_payment_intent_succeeded_for_module(intent: dict[str, Any]) -> bool:
    """
    Grant a module add-on when payment_intent.succeeded fires without target_tier.

    Stripe endpoints often subscribe only to payment_intent.succeeded; module metadata
    lives on the Checkout Session (or subscription), not the PaymentIntent.
    """
    metadata = intent.get('metadata') or {}
    module = (metadata.get('module') or '').strip()
    if module and module in MODULE_IDS:
        handle_checkout_session_completed({
            'id': intent.get('id'),
            'metadata': metadata,
        })
        return True

    session = resolve_checkout_session_from_payment_intent(intent)
    if session is None:
        return False

    session_module = (session.get('metadata') or {}).get('module')
    if not session_module and session.get('subscription'):
        try:
            subscription = stripe.Subscription.retrieve(session.get('subscription'))
            session_module = (subscription.get('metadata') or {}).get('module')
        except stripe.error.StripeError as exc:
            logger.warning(
                'Could not load subscription metadata for payment_intent=%s: %s',
                intent.get('id'),
                exc,
            )
    if session_module:
        handle_checkout_session_completed(session)
        return True

    return False


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
