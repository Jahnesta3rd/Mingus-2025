"""
Regression tests for atomic POST /api/auth/register (P2.1).

Verifies that signup creates exactly one row in users, user_profiles, and
onboarding_progress in a single transaction, with rollback on failure.
Requires PostgreSQL with migrated schema (same as production): SQLite cannot
execute sqlalchemy.dialects.postgresql.insert with ON CONFLICT used by the handler.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from unittest import mock

import pytest
from flask import Flask
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.api import register_all_apis
from backend.api.auth_endpoints import auth_api
from backend.middleware.security import SecurityMiddleware
from backend.models.database import db, init_database
from backend.models.onboarding_progress import OnboardingProgress
from backend.models.user_models import User


def _postgres_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


def _require_postgres() -> str:
    url = _postgres_url()
    if not url or not url.startswith(("postgresql", "postgres")):
        pytest.skip(
            "Atomic register tests require PostgreSQL with migrated schema "
            "(tables users, user_profiles, onboarding_progress). "
            "Set DATABASE_URL or TEST_DATABASE_URL. "
            "The /register handler uses pg_insert + ON CONFLICT (not SQLite-compatible)."
        )
    return url


@pytest.fixture
def auth_app(monkeypatch):
    """Flask app with DB init + API blueprints including auth (matches production app.py)."""
    url = _require_postgres()
    monkeypatch.setenv("DATABASE_URL", url)

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key-register-atomic"
    app.config["WTF_CSRF_ENABLED"] = False

    init_database(app)
    register_all_apis(app)
    app.register_blueprint(auth_api)
    SecurityMiddleware().init_app(app)
    return app


@pytest.fixture
def auth_client(auth_app):
    return auth_app.test_client()


@pytest.fixture(autouse=True)
def _patch_rate_limit(monkeypatch):
    monkeypatch.setattr("backend.api.auth_endpoints.check_rate_limit", lambda _ip: True)


def _payload(email: str, first_name: str = "Mingus") -> dict:
    return {
        "email": email,
        "password": "longpass12",
        "firstName": first_name,
    }


def _cleanup_email(email: str) -> None:
    normalized = email.strip().lower()
    user = User.query.filter_by(email=normalized).first()
    if not user:
        return
    uid = user.id
    db.session.execute(
        text("DELETE FROM onboarding_progress WHERE user_id = :uid"), {"uid": uid}
    )
    db.session.execute(
        text("DELETE FROM user_profiles WHERE email = :e"), {"e": normalized}
    )
    db.session.delete(user)
    db.session.commit()


def _count_users(email: str) -> int:
    return (
        db.session.execute(
            text("SELECT COUNT(*) FROM users WHERE email = :e"),
            {"e": email.lower()},
        ).scalar()
        or 0
    )


def _count_profiles(email: str) -> int:
    return (
        db.session.execute(
            text("SELECT COUNT(*) FROM user_profiles WHERE email = :e"),
            {"e": email.lower()},
        ).scalar()
        or 0
    )


def _count_onboarding_for_user(user_id: int) -> int:
    return (
        db.session.execute(
            text("SELECT COUNT(*) FROM onboarding_progress WHERE user_id = :uid"),
            {"uid": user_id},
        ).scalar()
        or 0
    )


def test_register_creates_all_three_rows_atomically(auth_app, auth_client, caplog):
    email = f"atomic.reg.{uuid.uuid4().hex}@example.com"
    first_name = "Casey"

    with auth_app.app_context():
        _cleanup_email(email)

    caplog.set_level(logging.INFO, "backend.api.auth_endpoints")

    resp = auth_client.post(
        "/api/auth/register",
        json=_payload(email, first_name=first_name),
        content_type="application/json",
    )

    assert resp.status_code in (200, 201)
    body = resp.get_json()
    assert body is not None
    assert body.get("success") is True

    with auth_app.app_context():
        assert _count_users(email) == 1
        assert _count_profiles(email) == 1

        row = db.session.execute(
            text(
                "SELECT first_name, personal_info, financial_info, monthly_expenses, "
                "important_dates, health_wellness, goals FROM user_profiles "
                "WHERE email = :e"
            ),
            {"e": email.lower()},
        ).mappings().first()
        assert row is not None
        assert row["first_name"] == first_name
        for col in (
            "financial_info",
            "monthly_expenses",
            "important_dates",
            "health_wellness",
            "goals",
        ):
            assert row[col] == "{}"

        personal = json.loads(row["personal_info"])
        expected_keys = {
            "firstName",
            "lastName",
            "dateOfBirth",
            "employmentStatus",
            "occupation",
            "city",
            "state",
            "zip",
            "phone",
        }
        assert set(personal.keys()) == expected_keys

        u = User.query.filter_by(email=email.lower()).one()
        assert _count_onboarding_for_user(u.id) == 1

        ob = OnboardingProgress.query.filter_by(user_id=u.id).one()
        assert ob.current_module == "income"
        assert list(ob.completed_modules or []) == []
        assert list(ob.skipped_modules or []) == []

        _cleanup_email(email)

    assert any("signup_complete" in (r.getMessage() or "") for r in caplog.records)


def test_register_rolls_back_on_user_profiles_insert_failure(
    auth_app, auth_client, caplog
):
    email = f"rollback.profile.{uuid.uuid4().hex}@example.com"
    caplog.set_level(logging.ERROR, "backend.api.auth_endpoints")

    with auth_app.app_context():
        _cleanup_email(email)

    orig_execute = db.session.execute
    call_n = [0]

    def execute_fail_profile(stmt, *args, **kwargs):
        # First db.session.execute in register() is user_profiles INSERT.
        call_n[0] += 1
        if call_n[0] == 1:
            raise RuntimeError("simulated user_profiles insert failure")
        return orig_execute(stmt, *args, **kwargs)

    with mock.patch.object(db.session, "execute", side_effect=execute_fail_profile):
        resp = auth_client.post(
            "/api/auth/register",
            json=_payload(email),
            content_type="application/json",
        )

    assert resp.status_code == 500

    with auth_app.app_context():
        assert _count_users(email) == 0
        assert _count_profiles(email) == 0
        assert (
            db.session.execute(
                text(
                    "SELECT COUNT(*) FROM onboarding_progress op "
                    "JOIN users u ON u.id = op.user_id WHERE u.email = :e"
                ),
                {"e": email.lower()},
            ).scalar()
            == 0
        )

    assert any(
        "signup_transaction_failed" in (r.getMessage() or "") for r in caplog.records
    )


def test_register_rolls_back_on_onboarding_progress_insert_failure(
    auth_app, auth_client, caplog
):
    email = f"rollback.onboarding.{uuid.uuid4().hex}@example.com"
    caplog.set_level(logging.ERROR, "backend.api.auth_endpoints")

    with auth_app.app_context():
        _cleanup_email(email)

    orig_execute = db.session.execute
    call_n = [0]

    def execute_fail_onboarding(stmt, *args, **kwargs):
        call_n[0] += 1
        if call_n[0] == 2:
            raise RuntimeError("simulated onboarding_progress insert failure")
        return orig_execute(stmt, *args, **kwargs)

    with mock.patch.object(db.session, "execute", side_effect=execute_fail_onboarding):
        resp = auth_client.post(
            "/api/auth/register",
            json=_payload(email),
            content_type="application/json",
        )

    assert resp.status_code == 500

    with auth_app.app_context():
        assert _count_users(email) == 0
        assert _count_profiles(email) == 0
        assert (
            db.session.execute(
                text(
                    "SELECT COUNT(*) FROM onboarding_progress op "
                    "JOIN users u ON u.id = op.user_id WHERE u.email = :e"
                ),
                {"e": email.lower()},
            ).scalar()
            == 0
        )

    assert any(
        "signup_transaction_failed" in (r.getMessage() or "") for r in caplog.records
    )


def test_register_duplicate_email_does_not_create_orphaned_data(
    auth_app, auth_client
):
    email = f"dup.reg.{uuid.uuid4().hex}@example.com"

    with auth_app.app_context():
        _cleanup_email(email)

    r1 = auth_client.post(
        "/api/auth/register",
        json=_payload(email, first_name="First"),
        content_type="application/json",
    )
    assert r1.status_code in (200, 201)

    r2 = auth_client.post(
        "/api/auth/register",
        json=_payload(email, first_name="Second"),
        content_type="application/json",
    )
    assert r2.status_code == 409

    with auth_app.app_context():
        assert _count_users(email) == 1
        assert _count_profiles(email) == 1
        u = User.query.filter_by(email=email.lower()).one()
        assert _count_onboarding_for_user(u.id) == 1

        row = db.session.execute(
            text("SELECT first_name FROM user_profiles WHERE email = :e"),
            {"e": email.lower()},
        ).first()
        assert row is not None
        assert row[0] == "First"

        _cleanup_email(email)
