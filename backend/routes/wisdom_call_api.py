#!/usr/bin/env python3
"""Compatibility shim — wisdom routes live in ``backend.api.wisdom_routes``."""

from backend.api.wisdom_routes import (  # noqa: F401
    get_wisdom_call,
    get_wisdom_call_stats,
    mark_wisdom_call_read,
    store_wisdom_batch_result,
    wisdom_bp,
    wisdom_call_bp,
)

__all__ = [
    "wisdom_bp",
    "wisdom_call_bp",
    "get_wisdom_call",
    "get_wisdom_call_stats",
    "mark_wisdom_call_read",
    "store_wisdom_batch_result",
]
