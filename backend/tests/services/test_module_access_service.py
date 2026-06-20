"""Tests for subscription module access (module_access_service)."""
from __future__ import annotations

import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.database import db, init_database
from backend.models.user_models import User
from backend.services.module_access_service import get_user_modules, has_module
from flask import Flask


def _postgres_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


def _require_postgres() -> str:
    url = _postgres_url()
    if not url or not url.startswith(("postgresql", "postgres")):
        pytest.skip(
            "Module access tests require PostgreSQL. Set DATABASE_URL or TEST_DATABASE_URL."
        )
    return url


@pytest.fixture
def module_access_app(monkeypatch):
    url = _require_postgres()
    monkeypatch.setenv("DATABASE_URL", url)

    app = Flask(__name__)
    app.config["TESTING"] = True
    init_database(app)
    return app


def _cleanup_user(user: User | None) -> None:
    if user is not None:
        db.session.delete(user)
        db.session.commit()


def _create_user(*, tier: str = "budget", purchased_modules: list[str] | None = None) -> User:
    ext_id = str(uuid.uuid4())
    email = f"mod_access_{ext_id[:12]}@example.com"
    user = User(
        user_id=ext_id,
        email=email,
        password_hash="unused",
        tier=tier,
        purchased_modules=list(purchased_modules or []),
    )
    db.session.add(user)
    db.session.commit()
    return user


class TestHasModule:
    def test_unknown_module_returns_false(self, module_access_app):
        with module_access_app.app_context():
            user = _create_user()
            try:
                assert has_module(user.id, "not_a_module") is False
            finally:
                _cleanup_user(user)

    def test_base_plan_user_has_no_family_addon(self, module_access_app):
        with module_access_app.app_context():
            user = _create_user(tier="budget")
            try:
                assert has_module(user.id, "family_addon") is False
                assert has_module(user.id, "vehicle_module") is False
            finally:
                _cleanup_user(user)

    def test_family_life_stage_grants_family_addon(self, module_access_app):
        with module_access_app.app_context():
            user = _create_user(tier="family_life_stage")
            try:
                assert has_module(user.id, "family_addon") is True
                assert has_module(user.id, "vehicle_module") is True
                assert has_module(user.id, "housing_module") is True
                assert has_module(user.id, "career_pro") is True
            finally:
                _cleanup_user(user)

    def test_purchased_family_addon_on_base_plan(self, module_access_app):
        with module_access_app.app_context():
            user = _create_user(tier="budget", purchased_modules=["family_addon"])
            try:
                assert has_module(user.id, "family_addon") is True
                assert has_module(user.id, "vehicle_module") is False
            finally:
                _cleanup_user(user)

    def test_get_user_modules_shape(self, module_access_app):
        with module_access_app.app_context():
            user = _create_user(tier="budget", purchased_modules=["career_pro"])
            try:
                modules = get_user_modules(user.id)
                assert set(modules.keys()) == {
                    "vehicle_module",
                    "housing_module",
                    "career_pro",
                    "family_addon",
                }
                assert modules["career_pro"] is True
                assert modules["family_addon"] is False
            finally:
                _cleanup_user(user)
