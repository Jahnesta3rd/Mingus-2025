"""Tests for PATCH /api/user/me relationship_status."""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta

import jwt
import pytest
from flask import Flask
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.api import register_all_apis
from backend.auth.decorators import JWT_ALGORITHM, JWT_SECRET_KEY
from backend.models.database import db, init_database
from backend.models.user_models import User
from backend.routes import user_api  # noqa: F401 — registers PATCH /api/user/me
from backend.routes.user import user_bp as user_agreement_bp


def _postgres_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


def _require_postgres() -> str:
    url = _postgres_url()
    if not url or not url.startswith(("postgresql", "postgres")):
        pytest.skip(
            "PATCH /api/user/me tests require PostgreSQL. "
            "Set DATABASE_URL or TEST_DATABASE_URL."
        )
    return url


@pytest.fixture
def me_app(monkeypatch):
    url = _require_postgres()
    monkeypatch.setenv("DATABASE_URL", url)

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key-user-me"
    app.config["WTF_CSRF_ENABLED"] = False
    init_database(app)
    register_all_apis(app)
    app.register_blueprint(user_agreement_bp)
    return app


@pytest.fixture
def me_client(me_app):
    return me_app.test_client()


def _make_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": int((datetime.utcnow() + timedelta(hours=2)).timestamp()),
    }
    raw = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return raw if isinstance(raw, str) else raw.decode("ascii")


def _cleanup(email: str) -> None:
    normalized = email.strip().lower()
    user = User.query.filter_by(email=normalized).first()
    if user:
        db.session.delete(user)
    db.session.commit()


def _ensure_user(email: str, ext_user_id: str) -> User:
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(user_id=ext_user_id, email=email, tier="budget")
        db.session.add(user)
        db.session.commit()
    return user


def test_patch_me_relationship_status_single(me_app, me_client):
    ext_user_id = str(uuid.uuid4())
    email = f"me_single_{ext_user_id[:12]}@example.com"
    try:
        with me_app.app_context():
            user = _ensure_user(email, ext_user_id)
            user_pk = user.id

        token = _make_token(ext_user_id, email)
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Test-User-Id": ext_user_id,
            "X-Test-User-Email": email,
            "Content-Type": "application/json",
        }
        resp = me_client.patch(
            "/api/user/me",
            headers=headers,
            json={"relationship_status": "single"},
        )
        assert resp.status_code == 200, resp.get_data(as_text=True)
        assert resp.get_json() == {"success": True}

        with me_app.app_context():
            row = db.session.execute(
                text("SELECT relationship_status FROM users WHERE id = :id"),
                {"id": user_pk},
            ).first()
            assert row[0] == "single"
    finally:
        with me_app.app_context():
            _cleanup(email)


def test_patch_me_relationship_status_rejects_invalid(me_app, me_client):
    ext_user_id = str(uuid.uuid4())
    email = f"me_invalid_{ext_user_id[:12]}@example.com"
    try:
        with me_app.app_context():
            _ensure_user(email, ext_user_id)

        token = _make_token(ext_user_id, email)
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Test-User-Id": ext_user_id,
            "X-Test-User-Email": email,
            "Content-Type": "application/json",
        }
        resp = me_client.patch(
            "/api/user/me",
            headers=headers,
            json={"relationship_status": "not_a_status"},
        )
        assert resp.status_code == 400
    finally:
        with me_app.app_context():
            _cleanup(email)


def test_get_profile_includes_relationship_status(me_app, me_client):
    ext_user_id = str(uuid.uuid4())
    email = f"me_get_{ext_user_id[:12]}@example.com"
    try:
        with me_app.app_context():
            user = _ensure_user(email, ext_user_id)
            db.session.execute(
                text("UPDATE users SET relationship_status = :val WHERE id = :id"),
                {"val": "married", "id": user.id},
            )
            db.session.commit()

        token = _make_token(ext_user_id, email)
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Test-User-Id": ext_user_id,
            "X-Test-User-Email": email,
        }
        resp = me_client.get("/api/user/profile", headers=headers)
        assert resp.status_code == 200, resp.get_data(as_text=True)
        body = resp.get_json()
        assert body["profile"]["relationship_status"] == "married"
    finally:
        with me_app.app_context():
            _cleanup(email)
