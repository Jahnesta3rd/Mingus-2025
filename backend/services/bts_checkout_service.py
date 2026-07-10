#!/usr/bin/env python3
"""BTS9 Tier-1 checkout: Stripe payment intent + order persistence."""

from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import stripe

from backend.models.database import db
from backend.models.order import Order
from backend.models.bts import BackToSchoolSession

logger = logging.getLogger(__name__)

_MVP_COUPONS: dict[str, Decimal] = {
    "MINGUS10": Decimal("0.10"),
    "SCHOOL20": Decimal("0.20"),
    "WELCOME5": Decimal("0.05"),
}

_REQUIRED_ADDRESS_FIELDS = (
    "firstName",
    "lastName",
    "address",
    "city",
    "state",
    "zip",
    "phone",
)


def _money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class BTSCheckoutService:
    """Create payment intents, validate coupons/addresses, persist orders."""

    def __init__(self) -> None:
        key = os.getenv("STRIPE_SECRET_KEY")
        if key:
            stripe.api_key = key

    def create_payment_intent(
        self,
        total: float | Decimal,
        *,
        session_id: str | None = None,
        user_id: str | None = None,
        tier: int | None = None,
    ) -> dict[str, str]:
        if not stripe.api_key:
            raise ValueError("Stripe is not configured (STRIPE_SECRET_KEY missing)")

        amount = _money(total)
        if amount <= 0:
            raise ValueError("Invalid total")

        amount_cents = int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))
        metadata: dict[str, str] = {"source": "bts_checkout"}
        if session_id:
            metadata["sessionId"] = str(session_id)
        if user_id:
            metadata["userId"] = str(user_id)
        if tier is not None:
            metadata["tier"] = str(tier)

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                payment_method_types=["card"],
                metadata=metadata,
                description=f"Mingus BTS Tier {tier or 1} checkout",
            )
        except stripe.error.StripeError as exc:
            logger.exception("Stripe PaymentIntent create failed: %s", exc)
            raise ValueError(f"Stripe error: {exc}") from exc

        return {
            "clientSecret": intent.client_secret,
            "paymentIntentId": intent.id,
        }

    def validate_shipping_address(self, address: dict | None) -> bool:
        if not isinstance(address, dict):
            raise ValueError("shippingAddress is required")

        for field in _REQUIRED_ADDRESS_FIELDS:
            value = address.get(field)
            if value is None or not str(value).strip():
                raise ValueError(f"Missing or empty: {field}")

        state = str(address.get("state", "")).strip().upper()
        if len(state) != 2 or not state.isalpha():
            raise ValueError("State must be a 2-character code")

        zip_code = re.sub(r"[^0-9]", "", str(address.get("zip", "")))
        if len(zip_code) < 5:
            raise ValueError("Invalid ZIP code")

        phone = re.sub(r"[^0-9]", "", str(address.get("phone", "")))
        if len(phone) < 10:
            raise ValueError("Invalid phone number")

        return True

    def validate_coupon(self, coupon_code: str | None) -> dict[str, Any]:
        if not coupon_code or not str(coupon_code).strip():
            raise ValueError("Coupon code required")

        code = str(coupon_code).strip().upper()
        discount_percent = _MVP_COUPONS.get(code)
        if discount_percent is None:
            raise ValueError(f"Coupon '{coupon_code}' not found")

        return {
            "code": code,
            "discountPercent": float(discount_percent),
        }

    def _verify_payment_intent(self, payment_intent_id: str, expected_total: Decimal) -> None:
        if not payment_intent_id:
            raise ValueError("paymentIntentId is required")
        if not stripe.api_key:
            raise ValueError("Stripe is not configured (STRIPE_SECRET_KEY missing)")

        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as exc:
            raise ValueError(f"Could not verify payment: {exc}") from exc

        if intent.status != "succeeded":
            raise ValueError(
                f"Payment not completed (status: {intent.status}). Complete payment first."
            )

        expected_cents = int(
            (expected_total * 100).to_integral_value(rounding=ROUND_HALF_UP)
        )
        if int(intent.amount) != expected_cents:
            raise ValueError("Payment amount does not match order total")

    def create_order(
        self,
        *,
        session_id: str,
        user_id: str,
        tier: int,
        cart_items: dict,
        shipping_address: dict,
        payment_intent_id: str,
        subtotal: float | Decimal,
        coupon_code: str | None = None,
    ) -> dict:
        # MVP: Tier 1 only
        try:
            tier_int = int(tier)
        except (TypeError, ValueError) as exc:
            raise ValueError("tier must be an integer") from exc
        if tier_int != 1:
            raise ValueError("Only Tier 1 checkout is supported in this release")

        if not session_id:
            raise ValueError("sessionId is required")
        if not user_id:
            raise ValueError("userId is required")
        if not isinstance(cart_items, dict) or not cart_items:
            raise ValueError("cartItems is required")

        self.validate_shipping_address(shipping_address)

        subtotal_dec = _money(subtotal)
        if subtotal_dec <= 0:
            raise ValueError("Invalid subtotal")

        discount = Decimal("0.00")
        applied_code = None
        if coupon_code:
            coupon = self.validate_coupon(coupon_code)
            applied_code = coupon["code"]
            discount = _money(subtotal_dec * Decimal(str(coupon["discountPercent"])))

        total = _money(subtotal_dec - discount)
        if total < 0:
            total = Decimal("0.00")

        self._verify_payment_intent(payment_intent_id, total)

        # Idempotent: same payment intent → return existing order
        existing = Order.query.filter_by(
            stripe_payment_intent_id=payment_intent_id
        ).first()
        if existing:
            return existing.to_dict()

        items_count = 0
        for items in cart_items.values():
            if isinstance(items, list):
                items_count += len(items)

        try:
            session_uuid = uuid.UUID(str(session_id))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid sessionId") from exc

        # Normalize address state/zip
        address = {
            **shipping_address,
            "state": str(shipping_address.get("state", "")).strip().upper(),
            "zip": str(shipping_address.get("zip", "")).strip(),
            "phone": str(shipping_address.get("phone", "")).strip(),
        }

        order = Order(
            session_id=session_uuid,
            user_id=str(user_id),
            tier=tier_int,
            cart_items=cart_items,
            items_count=items_count,
            shipping_address=address,
            stripe_payment_intent_id=payment_intent_id,
            coupon_code=applied_code,
            coupon_discount=discount,
            subtotal=subtotal_dec,
            discount=discount,
            tax=Decimal("0.00"),
            total=total,
            status="completed",
            completed_at=datetime.utcnow(),
        )

        try:
            db.session.add(order)

            # BTS8: stamp Tier 1 purchase time for reminder scheduling
            if tier_int == 1:
                session = BackToSchoolSession.query.filter_by(
                    session_id=session_uuid
                ).first()
                if session and session.user_id == str(user_id):
                    if not session.tier1_purchased_at:
                        session.tier1_purchased_at = datetime.utcnow()

            db.session.commit()
            return order.to_dict()
        except Exception as exc:
            db.session.rollback()
            logger.exception("Failed to create BTS order: %s", exc)
            raise ValueError(f"Failed to create order: {exc}") from exc

    def get_order(self, order_id: str, user_id: str | None = None) -> dict:
        try:
            order_uuid = uuid.UUID(str(order_id))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid orderId") from exc

        order = Order.query.filter_by(order_id=order_uuid).first()
        if not order:
            raise ValueError("Order not found")
        if user_id and order.user_id != str(user_id):
            raise ValueError("Order not found")
        return order.to_dict()


bts_checkout_service = BTSCheckoutService()
