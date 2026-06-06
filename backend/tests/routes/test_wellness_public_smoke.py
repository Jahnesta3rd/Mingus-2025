#!/usr/bin/env python3
"""Smoke tests for wellness_public_bp (/api/wellness) as registered from backend.app."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta

import jwt
import pytest
from flask import Flask

from backend.auth.decorators import JWT_ALGORITHM, JWT_SECRET_KEY
from backend.models.database import db, init_database
from backend.models.user_models import User
from backend.routes.wellness_routes import wellness_public_bp


@pytest.fixture
def smoke_app():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for wellness smoke tests")
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_database(app)
    app.register_blueprint(wellness_public_bp)

    @app.teardown_request
    def _rollback_on_error(exc):
        if exc is not None:
            db.session.rollback()

    with app.app_context():
        db.create_all()
    yield app


@pytest.fixture
def smoke_client(smoke_app):
    return smoke_app.test_client()


def _make_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "email": "smoke@example.com",
        "exp": int((datetime.utcnow() + timedelta(hours=2)).timestamp()),
    }
    raw = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return raw if isinstance(raw, str) else raw.decode("ascii")


def _ensure_user(app: Flask, user_id: str) -> None:
    with app.app_context():
        u = User.query.filter_by(user_id=user_id).first()
        if not u:
            db.session.add(User(user_id=user_id, email=f"{user_id}@smoke.test"))
            db.session.commit()


def test_wellness_unauthenticated_returns_401(smoke_client):
    r = smoke_client.get("/api/wellness/streak")
    assert r.status_code == 401


def test_wellness_authenticated_get_and_post_parseable(smoke_app, smoke_client):
    # users.user_id is varchar(36); keep sub short enough for JWT + DB.
    uid = f"ws{uuid.uuid4().hex[:30]}"
    _ensure_user(smoke_app, uid)
    tok = _make_token(uid)
    headers = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

    r_streak = smoke_client.get("/api/wellness/streak", headers=headers)
    assert r_streak.status_code == 200, r_streak.get_data(as_text=True)
    data_streak = r_streak.get_json()
    assert isinstance(data_streak, dict)
    assert set(data_streak.keys()) >= {
        "current_streak",
        "longest_streak",
        "last_checkin_date",
        "total_checkins",
    }

    r_scores = smoke_client.get("/api/wellness/scores/latest", headers=headers)
    assert r_scores.status_code == 200
    data_scores = r_scores.get_json()
    assert isinstance(data_scores, dict)
    assert "week_ending_date" in data_scores

    payload = {
        "exercise_days": 3,
        "sleep_quality": 6,
        "meditation_minutes": 15,
        "stress_level": 5,
        "overall_mood": 6,
        "relationship_satisfaction": 7,
        "social_interactions": 5,
        "financial_stress": 4,
        "spending_control": 6,
    }
    r_post = smoke_client.post("/api/wellness/checkin", json=payload, headers=headers)
    assert r_post.status_code in (200, 201), r_post.get_data(as_text=True)
    data_post = r_post.get_json()
    assert isinstance(data_post, dict)
    assert "checkin_id" in data_post or "wellness_scores" in data_post
