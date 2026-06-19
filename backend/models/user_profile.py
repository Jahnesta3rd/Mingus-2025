#!/usr/bin/env python3
"""user_profiles row — demographic and profile fields keyed by email."""

from datetime import datetime

from .database import db


class UserProfile(db.Model):
    """Profile data stored in user_profiles (email-keyed)."""

    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.Text, nullable=False, unique=True, index=True)
    first_name = db.Column(db.Text, nullable=True)
    personal_info = db.Column(db.Text, nullable=True)
    financial_info = db.Column(db.Text, nullable=True)
    monthly_expenses = db.Column(db.Text, nullable=True)
    important_dates = db.Column(db.Text, nullable=True)
    health_wellness = db.Column(db.Text, nullable=True)
    goals = db.Column(db.Text, nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    def __repr__(self) -> str:
        return f"<UserProfile email={self.email!r} zip_code={self.zip_code!r}>"
