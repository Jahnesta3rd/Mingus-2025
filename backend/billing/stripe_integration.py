"""
Lightweight shim for Stripe integration to satisfy tests expecting
`backend.billing.stripe_integration.StripeIntegration`.

It wraps the existing `backend.payment.stripe_integration.StripeService` and
re-exports common symbols used in tests.
"""

from typing import Any

try:
    from backend.payment.stripe_integration import (
        StripeService as _StripeService,
        SubscriptionTier,
    )
except Exception:  # pragma: no cover - fallback if payment module unavailable
    _StripeService = None  # type: ignore
    class SubscriptionTier:  # type: ignore
        BUDGET = "budget"
        MID_TIER = "mid_tier"
        PROFESSIONAL = "professional"


class StripeIntegration:
    """
    Thin wrapper around `StripeService` for backward-compat imports.
    Delegates all attribute access to the underlying service instance.
    """

    def __init__(self, api_key: str = None, webhook_secret: str = None, **kwargs: Any) -> None:
        if _StripeService is None:
            # Minimal no-op to avoid crashes in environments without payment module
            self._service = object()
        else:
            self._service = _StripeService(api_key=api_key, webhook_secret=webhook_secret)

    def __getattr__(self, name: str):
        return getattr(self._service, name)


__all__ = ["StripeIntegration", "SubscriptionTier"]












