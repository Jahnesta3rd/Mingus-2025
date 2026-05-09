#!/usr/bin/env python3
"""Smoke tests for daily_outlook_public_bp under /api/daily-outlook."""

from __future__ import annotations

import json
import os
import uuid
from datetime import date, datetime, timedelta

import jwt
import pytest
from flask import Flask
from sqlalchemy import text

from backend.auth.decorators import JWT_ALGORITHM, JWT_SECRET_KEY
from backend.models.database import db, init_database
from backend.routes.daily_outlook_routes import daily_outlook_public_bp


def _ensure_user_sql(app: Flask, user_id: str) -> int:
    """Insert test user without ORM; return internal numeric users.id."""
    with app.app_context():
        row = db.session.execute(
            text("SELECT id FROM users WHERE user_id = :u LIMIT 1"),
            {"u": user_id},
        ).first()
        if row:
            return int(row[0])
        now = datetime.utcnow()
        email = f"{user_id}@smoke.test"
        db.session.execute(
            text(
                """
                INSERT INTO users (
                    user_id, email, password_hash, tier, is_beta, is_admin,
                    referral_count, successful_referrals, feature_unlocked,
                    last_activity, created_at, updated_at
                ) VALUES (
                    :user_id, :email, :ph, 'budget', false, false,
                    0, 0, false,
                    :now, :now, :now
                )
                """
            ),
            {
                "user_id": user_id,
                "email": email,
                "ph": "smoke-test-no-login",
                "now": now,
            },
        )
        db.session.commit()
        row2 = db.session.execute(
            text("SELECT id FROM users WHERE user_id = :u"),
            {"u": user_id},
        ).first()
        return int(row2[0])


@pytest.fixture
def smoke_app():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for daily outlook smoke tests")
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_database(app)
    app.register_blueprint(daily_outlook_public_bp)

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
        "email": "do@m.test",
        "exp": int((datetime.utcnow() + timedelta(hours=2)).timestamp()),
    }
    raw = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return raw if isinstance(raw, str) else raw.decode("ascii")


def test_daily_outlook_public_smoke_401_and_200_shapes(smoke_app, smoke_client):
    """
    Single test: 401s first, then authenticated GET defaults, tomorrow, and mutating
    POSTs (after inserting today's outlook row via SQL).
    """
    for path, method, kwargs in (
        ("/api/daily-outlook/", "get", {}),
        ("/api/daily-outlook", "get", {}),
        ("/api/daily-outlook/tomorrow", "get", {}),
        ("/api/daily-outlook/actions", "post", {"json": {"action_id": "a", "completed": True}}),
        ("/api/daily-outlook/rating", "post", {"json": {"rating": 4, "timestamp": "x"}}),
    ):
        if method == "get":
            r = smoke_client.get(path)
        else:
            r = smoke_client.post(path, **kwargs)
        assert r.status_code == 401, (path, r.get_data(as_text=True))

    uid = f"do{uuid.uuid4().hex[:30]}"
    internal_id = _ensure_user_sql(smoke_app, uid)
    tok = _make_token(uid)
    headers = {"Authorization": f"Bearer {tok}"}

    r_root = smoke_client.get("/api/daily-outlook", headers=headers)
    assert r_root.status_code == 200, r_root.get_data(as_text=True)
    body = r_root.get_json()
    assert body.get("user_name")
    assert body.get("current_time")
    assert body.get("balance_score", {}).get("value") == 0
    assert body.get("primary_insight", {}).get("title")
    assert body.get("quick_actions") == []
    assert body.get("tomorrow_teaser") is None
    assert body.get("user_tier") in (
        "budget",
        "budget_career_vehicle",
        "mid_tier",
        "professional",
    )

    r_tom = smoke_client.get("/api/daily-outlook/tomorrow", headers=headers)
    assert r_tom.status_code == 200, r_tom.get_data(as_text=True)
    tom = r_tom.get_json()
    tt = tom.get("tomorrow_teaser") or {}
    assert "title" in tt and "description" in tt and "excitement_level" in tt

    today = date.today().isoformat()
    qa = [{"id": "smoke_action", "action": "Smoke action", "description": "d", "difficulty": "easy"}]
    now = datetime.utcnow()
    with smoke_app.app_context():
        db.session.execute(
            text(
                """
                INSERT INTO daily_outlooks (
                    user_id, date, balance_score,
                    financial_weight, wellness_weight, relationship_weight, career_weight,
                    primary_insight, quick_actions, encouragement_message, surprise_element,
                    streak_count, created_at
                ) VALUES (
                    :uid, :d, 55,
                    25, 25, 25, 25,
                    'Insight text', CAST(:qa AS JSON), 'Keep going!', NULL,
                    1, :now
                )
                ON CONFLICT (user_id, date) DO UPDATE SET
                    balance_score = EXCLUDED.balance_score,
                    quick_actions = EXCLUDED.quick_actions
                """
            ),
            {
                "uid": internal_id,
                "d": today,
                "qa": json.dumps(qa),
                "now": now,
            },
        )
        db.session.commit()

    r_act = smoke_client.post(
        "/api/daily-outlook/actions",
        headers=headers,
        json={"action_id": "smoke_action", "completed": True},
    )
    assert r_act.status_code == 200, r_act.get_data(as_text=True)
    act_j = r_act.get_json()
    assert act_j.get("id") == "smoke_action"
    assert act_j.get("completed") is True

    r_rate = smoke_client.post(
        "/api/daily-outlook/rating",
        headers=headers,
        json={"rating": 5, "timestamp": datetime.utcnow().isoformat()},
    )
    assert r_rate.status_code == 200, r_rate.get_data(as_text=True)
    rate_j = r_rate.get_json()
    assert rate_j.get("success") is True
    assert rate_j.get("rating") == 5
