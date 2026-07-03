#!/usr/bin/env python3
"""Log rows for lead magnet assessment result emails (queued → sent | failed)."""

from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB

from .database import db


class LeadMagnetEmailLog(db.Model):
    __tablename__ = "lead_magnet_email_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    assessment_type = db.Column(db.String(64), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="queued")
    sent_at = db.Column(db.DateTime, nullable=True)
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    last_error = db.Column(db.Text, nullable=True)
    results_data = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
