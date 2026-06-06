#!/usr/bin/env python3
"""Smoke tests for user_activity_public_bp GET /api/user/activity/recent."""

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
from backend.routes.user_activity_routes import user_activity_public_bp


@pytest.fixture
def smoke_app():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for user activity smoke tests")
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_database(app)
    app.register_blueprint(user_activity_public_bp)

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
        "email": "ua@m.test",
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


def test_user_activity_recent_unauthenticated_returns_401(smoke_client):
    r = smoke_client.get("/api/user/activity/recent")
    assert r.status_code == 401


def test_user_activity_recent_authenticated_empty_shape(smoke_app, smoke_client):
    uid = f"ua{uuid.uuid4().hex[:30]}"
    _ensure_user(smoke_app, uid)
    tok = _make_token(uid)
    headers = {"Authorization": f"Bearer {tok}"}

    r = smoke_client.get("/api/user/activity/recent", headers=headers)
    assert r.status_code == 200, r.get_data(as_text=True)
    data = r.get_json()
    assert isinstance(data, dict)
    assert data == {"activities": []}
