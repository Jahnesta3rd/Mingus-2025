#!/usr/bin/env python3
"""Log rows for batched beta invitation emails (queued → sent | failed)."""

from datetime import datetime

from .database import db


class BetaInviteLog(db.Model):
    __tablename__ = "beta_invite_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    first_name = db.Column(db.String(120), nullable=True)
    code = db.Column(db.String(20), nullable=False)
    wave_label = db.Column(db.String(64), nullable=False, index=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="queued")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
