#!/usr/bin/env python3
"""Signed tokens for public lead-magnet assessment result links."""

import secrets
from datetime import datetime, timedelta

from .database import db


class AssessmentToken(db.Model):
    __tablename__ = "assessment_tokens"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    assessment_id = db.Column(db.Integer, nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email_hash = db.Column(db.String(255), nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    redeemed_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )

    def __init__(self, assessment_id, email_hash):
        self.assessment_id = assessment_id
        self.email_hash = email_hash
        self.token = self._generate_token()
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(days=7)

    @staticmethod
    def _generate_token() -> str:
        """Generate a secure random token (raw token, not JWT)."""
        return secrets.token_urlsafe(32)

    def is_valid(self) -> bool:
        """Check if token is not expired and not used."""
        return not self.is_used and datetime.utcnow() < self.expires_at
