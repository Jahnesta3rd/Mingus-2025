#!/usr/bin/env python3
"""Subscription module access checks (base plan + purchased add-ons + tier bundles)."""

from __future__ import annotations

import logging
from typing import FrozenSet

from backend.models.database import db
from backend.models.user_models import User

logger = logging.getLogger(__name__)

MODULE_IDS: FrozenSet[str] = frozenset({
    'vehicle_module',
    'housing_module',
    'career_pro',
    'family_addon',
})

# Tiers that include every billable module without individual add-on purchase.
TIER_ALL_MODULES: FrozenSet[str] = frozenset({'family_life_stage'})


def _normalize_module(module: str) -> str | None:
    if not module or not isinstance(module, str):
        return None
    key = module.strip()
    if key not in MODULE_IDS:
        return None
    return key


def _purchased_modules(user: User | None) -> set[str]:
    if user is None:
        return set()
    raw = getattr(user, 'purchased_modules', None) or []
    if not isinstance(raw, list):
        return set()
    return {m for m in raw if isinstance(m, str) and m in MODULE_IDS}


def has_module(user_id: int, module: str) -> bool:
    """
    Return True when the user may access a subscription module.

    Access is granted when:
    - the module was explicitly purchased (users.purchased_modules JSON), or
    - the user's tier includes all modules (e.g. family_life_stage).
    """
    module_key = _normalize_module(module)
    if module_key is None:
        return False

    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if user is None:
            return False

        tier = (user.tier or '').strip().lower()
        if tier in TIER_ALL_MODULES:
            return True

        return module_key in _purchased_modules(user)
    except Exception as exc:
        logger.error(
            "Error checking module access for user_id=%s module=%s: %s",
            user_id,
            module,
            exc,
        )
        return False


def get_user_modules(user_id: int) -> dict[str, bool]:
    """Return access flags for every known module (for profile API responses)."""
    return {module: has_module(user_id, module) for module in sorted(MODULE_IDS)}


def grant_module(user_id: int, module: str) -> bool:
    """
    Grant a subscription module to a user (append to purchased_modules).

    No-op when the user already has access via tier bundle or prior purchase.
    """
    module_key = _normalize_module(module)
    if module_key is None:
        return False

    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if user is None:
            return False

        if has_module(user_id, module_key):
            return True

        purchased = list(user.purchased_modules or [])
        if module_key not in purchased:
            purchased.append(module_key)
            user.purchased_modules = purchased
            db.session.commit()
        return True
    except Exception as exc:
        logger.error(
            "Error granting module for user_id=%s module=%s: %s",
            user_id,
            module,
            exc,
        )
        db.session.rollback()
        return False
