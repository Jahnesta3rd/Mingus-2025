"""Tests for PATCH /api/user/profile important_dates upsert and merge."""
from __future__ import annotations

import json
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


def _postgres_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


def _require_postgres() -> str:
    url = _postgres_url()
    if not url or not url.startswith(("postgresql", "postgres")):
        pytest.skip(
            "PATCH profile tests require PostgreSQL (user_profiles.email UNIQUE). "
            "Set DATABASE_URL or TEST_DATABASE_URL."
        )
    return url


@pytest.fixture
def profile_app(monkeypatch):
    url = _require_postgres()
    monkeypatch.setenv("DATABASE_URL", url)

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key-profile-patch"
    app.config["WTF_CSRF_ENABLED"] = False
    init_database(app)
    register_all_apis(app)
    return app


@pytest.fixture
def profile_client(profile_app):
    return profile_app.test_client()


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
    db.session.execute(
        text("DELETE FROM user_profiles WHERE email = :e"), {"e": normalized}
    )
    user = User.query.filter_by(email=normalized).first()
    if user:
        db.session.delete(user)
    db.session.commit()


def _ensure_user(email: str, ext_user_id: str) -> None:
    user = User.query.filter_by(email=email).first()
    if not user:
        db.session.add(
            User(user_id=ext_user_id, email=email, password_hash="unused")
        )
        db.session.commit()


def test_patch_important_dates_upserts_when_profile_missing(profile_app, profile_client):
    ext_user_id = str(uuid.uuid4())
    email = f"patch_up_{ext_user_id[:12]}@example.com"

    with profile_app.app_context():
        _cleanup(email)
        _ensure_user(email, ext_user_id)

    token = _make_token(ext_user_id, email)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    events = [
        {
            "name": "Graduation",
            "date": "2027-06-01",
            "cost": 500,
            "recurring": False,
            "type": "graduation",
        }
    ]

    try:
        resp = profile_client.patch(
            "/api/user/profile",
            headers=headers,
            json={"important_dates": {"custom_events": events}},
        )
        assert resp.status_code == 200, resp.get_data(as_text=True)
        body = resp.get_json()
        assert body["success"] is True
        assert body["profile"]["important_dates"]["custom_events"] == events

        with profile_app.app_context():
            row = db.session.execute(
                text("SELECT important_dates FROM user_profiles WHERE email = :e"),
                {"e": email},
            ).first()
            assert row is not None
            stored = json.loads(row[0])
            assert stored["custom_events"] == events
            assert "customEvents" not in stored
    finally:
        with profile_app.app_context():
            _cleanup(email)


def test_patch_important_dates_merges_without_clobbering_other_keys(
    profile_app, profile_client
):
    ext_user_id = str(uuid.uuid4())
    email = f"patch_merge_{ext_user_id[:12]}@example.com"
    existing = {
        "birthday": "1990-03-15",
        "custom_events": [
            {"name": "Trip", "date": "2027-01-01", "cost": 100, "recurring": False}
        ],
    }

    with profile_app.app_context():
        _cleanup(email)
        _ensure_user(email, ext_user_id)
        db.session.execute(
            text(
                "INSERT INTO user_profiles (email, personal_info, financial_info, "
                "monthly_expenses, important_dates, health_wellness, goals) "
                "VALUES (:e, '{}', '{}', '{}', :imp, '{}', '{}')"
            ),
            {"e": email, "imp": json.dumps(existing)},
        )
        db.session.commit()

    token = _make_token(ext_user_id, email)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    updated_events = existing["custom_events"] + [
        {"name": "Wedding", "date": "2028-05-20", "cost": 2000, "recurring": False}
    ]

    try:
        resp = profile_client.patch(
            "/api/user/profile",
            headers=headers,
            json={"important_dates": {"custom_events": updated_events}},
        )
        assert resp.status_code == 200, resp.get_data(as_text=True)

        with profile_app.app_context():
            row = db.session.execute(
                text("SELECT important_dates FROM user_profiles WHERE email = :e"),
                {"e": email},
            ).first()
            stored = json.loads(row[0])
            assert stored["birthday"] == "1990-03-15"
            assert len(stored["custom_events"]) == 2
            assert stored["custom_events"][1]["name"] == "Wedding"
    finally:
        with profile_app.app_context():
            _cleanup(email)
