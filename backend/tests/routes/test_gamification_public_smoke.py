#!/usr/bin/env python3
"""Smoke tests for gamification_public_bp GET /api/gamification/milestones."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta

import jwt
import pytest
from flask import Flask
from sqlalchemy import text

from backend.auth.decorators import JWT_ALGORITHM, JWT_SECRET_KEY
from backend.models.database import db, init_database
from backend.routes.gamification_routes import gamification_public_bp


def _ensure_user_sql(app: Flask, user_id: str) -> None:
    """Insert test user without ORM User.query (mapper breaks after gamification_api import)."""
    with app.app_context():
        exists = db.session.execute(
            text("SELECT 1 FROM users WHERE user_id = :u LIMIT 1"),
            {"u": user_id},
        ).scalar()
        if exists:
            return
        now = datetime.utcnow()
        email = f"{user_id}@smoke.test"
        db.session.execute(
            text(
                """
                INSERT INTO users (
                    user_id, email, tier, is_beta, is_admin,
                    referral_count, successful_referrals, feature_unlocked,
                    last_activity, created_at, updated_at
                ) VALUES (
                    :user_id, :email, 'budget', false, false,
                    0, 0, false,
                    :now, :now, :now
                )
                """
            ),
            {"user_id": user_id, "email": email, "now": now},
        )
        db.session.commit()


@pytest.fixture
def smoke_app():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for gamification smoke tests")
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_database(app)
    app.register_blueprint(gamification_public_bp)

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
        "email": "g@m.test",
        "exp": int((datetime.utcnow() + timedelta(hours=2)).timestamp()),
    }
    raw = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return raw if isinstance(raw, str) else raw.decode("ascii")


def test_gamification_milestones_smoke_401_403_and_shape(smoke_app, smoke_client):
    """
    One test function so User ORM stays usable for 403 checks before lazy-importing
    gamification_api (which leaves User mapper inconsistent in this minimal app).
    """
    r401 = smoke_client.get("/api/gamification/milestones")
    assert r401.status_code == 401

    uid_a = f"ga{uuid.uuid4().hex[:30]}"
    uid_b = f"gb{uuid.uuid4().hex[:30]}"
    _ensure_user_sql(smoke_app, uid_a)
    _ensure_user_sql(smoke_app, uid_b)
    tok_a = _make_token(uid_a)
    headers_a = {"Authorization": f"Bearer {tok_a}"}

    # 403: wrong userId — must run before any request that imports gamification_api.
    r403 = smoke_client.get(
        f"/api/gamification/milestones?userId={uid_b}",
        headers=headers_a,
    )
    assert r403.status_code == 403
    err = r403.get_json()
    assert err.get("error") == "forbidden"

    # 200 + MilestonesResponse shape (first call that lazy-imports gamification_api).
    r200 = smoke_client.get("/api/gamification/milestones", headers=headers_a)
    assert r200.status_code == 200, r200.get_data(as_text=True)
    data = r200.get_json()
    assert isinstance(data, dict)
    for k in ("current_streak", "next_milestone", "milestones", "achievements"):
        assert k in data
    assert isinstance(data["milestones"], list)
    assert isinstance(data["achievements"], list)
    for item in data["milestones"]:
        assert "days" in item and "achieved" in item and "achieved_date" in item
