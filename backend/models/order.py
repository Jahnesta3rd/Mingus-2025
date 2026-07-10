#!/usr/bin/env python3
"""BTS purchase order model (BTS9 checkout)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from .database import db


class Order(db.Model):
    """Tier checkout order persisted after successful Stripe payment."""

    __tablename__ = "bts_purchase_orders"

    order_id = db.Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    session_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("back_to_school_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(db.String(255), nullable=False, index=True)
    tier = db.Column(db.Integer, nullable=False)

    cart_items = db.Column(JSONB, nullable=False)
    items_count = db.Column(db.Integer, nullable=False, default=0, server_default="0")

    shipping_address = db.Column(JSONB, nullable=False)

    stripe_payment_intent_id = db.Column(db.String(255), nullable=True)
    coupon_code = db.Column(db.String(100), nullable=True)
    coupon_discount = db.Column(
        db.Numeric(10, 2), nullable=False, default=0, server_default="0"
    )

    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(10, 2), nullable=False, default=0, server_default="0")
    tax = db.Column(db.Numeric(10, 2), nullable=False, default=0, server_default="0")
    total = db.Column(db.Numeric(10, 2), nullable=False)

    status = db.Column(
        db.String(50), nullable=False, default="pending", server_default="pending"
    )
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.text("NOW()"),
    )
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "orderId": str(self.order_id),
            "sessionId": str(self.session_id),
            "userId": self.user_id,
            "tier": self.tier,
            "status": self.status,
            "subtotal": float(self.subtotal) if self.subtotal is not None else 0.0,
            "discount": float(self.discount) if self.discount is not None else 0.0,
            "tax": float(self.tax) if self.tax is not None else 0.0,
            "total": float(self.total) if self.total is not None else 0.0,
            "couponCode": self.coupon_code,
            "cartItems": self.cart_items,
            "shippingAddress": self.shipping_address,
            "itemsCount": self.items_count,
            "stripePaymentIntentId": self.stripe_payment_intent_id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
        }
