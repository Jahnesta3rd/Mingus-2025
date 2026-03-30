#!/usr/bin/env python3
"""In-app feedback: per-feature ratings and NPS survey (beta)."""

from datetime import datetime

from .database import db


class FeatureRating(db.Model):
    __tablename__ = "feature_ratings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    feature_name = db.Column(db.String(100), nullable=False, index=True)
    rating = db.Column(db.String(4), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_tier = db.Column(db.String(20), nullable=False)

    user = db.relationship("User", backref=db.backref("feature_ratings", lazy="dynamic"))


class NPSSurvey(db.Model):
    __tablename__ = "nps_surveys"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    score = db.Column(db.Integer, nullable=False)
    most_valuable_feature = db.Column(db.String(100), nullable=True)
    least_valuable_feature = db.Column(db.String(100), nullable=True)
    would_pay = db.Column(db.String(10), nullable=True)
    price_willing = db.Column(db.Integer, nullable=True)
    additional_comments = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("nps_survey", uselist=False))
