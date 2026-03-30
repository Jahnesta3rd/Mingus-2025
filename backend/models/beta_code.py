#!/usr/bin/env python3
"""Beta invite codes for pre-registration validation and post-signup redemption."""
import secrets
from datetime import datetime

from .database import db


class BetaCode(db.Model):
    __tablename__ = "beta_codes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    status = db.Column(db.String(10), nullable=False, default="available")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    redeemed_at = db.Column(db.DateTime, nullable=True)
    redeemed_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    batch = db.Column(db.String(30), nullable=True)

    @classmethod
    def generate_bulk(cls, n, batch_label):
        """Create n unique codes MINGUS-BETA-XXXXXXXX (hex from token_hex, uppercase)."""
        batch_label = batch_label or None
        to_add = []
        seen_local = set()
        while len(to_add) < n:
            suffix = secrets.token_hex(4).upper()
            code_str = f"MINGUS-BETA-{suffix}"
            if code_str in seen_local:
                continue
            if cls.query.filter_by(code=code_str).first():
                continue
            seen_local.add(code_str)
            to_add.append(
                cls(code=code_str, batch=batch_label, status="available")
            )
        db.session.add_all(to_add)
        db.session.commit()
        return to_add
