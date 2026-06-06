#!/usr/bin/env python3
"""Legal audit trail: recorded user agreement acceptances."""

from datetime import datetime

from .database import db


class AgreementAcceptance(db.Model):
    __tablename__ = "agreement_acceptances"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    agreement_version = db.Column(db.String(100), nullable=False, index=True)
    accepted_at = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    agreement_hash = db.Column(db.String(128), nullable=True)

    user = db.relationship("User", backref=db.backref("agreement_acceptances", lazy="dynamic"))
