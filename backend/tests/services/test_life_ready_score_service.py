"""
Focused regression: compute_life_ready_score must accept JWT-style UUID strings
(P8 / #28) and resolve User via User.user_id, not integer PK on db.session.get.
"""
from __future__ import annotations

import os
import sys
import uuid

import pytest
from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.database import db, init_database
from backend.models.user_models import User
from backend.services.life_ready_score_service import compute_life_ready_score


def _database_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


@pytest.fixture
def life_ready_app():
    url = _database_url()
    if not url:
        pytest.skip(
            "DATABASE_URL or TEST_DATABASE_URL required "
            "(init_database does not support SQLite-only runs)."
        )

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "life-ready-score-test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    init_database(app)
    return app


class TestLifeReadyScoreService:
    def test_compute_life_ready_score_accepts_uuid_string(self, life_ready_app):
        """Fails if User is still loaded with db.session.get(User, uuid_string)."""
        ext_id = str(uuid.uuid4())
        email = f"life_ready_svc_{ext_id[:12]}@example.com"

        with life_ready_app.app_context():
            user = User(
                user_id=ext_id,
                email=email,
                password_hash="unused",
            )
            db.session.add(user)
            db.session.commit()

            try:
                out = compute_life_ready_score(user.user_id)
            finally:
                row = User.query.filter_by(user_id=ext_id).first()
                if row is not None:
                    db.session.delete(row)
                    db.session.commit()

        assert isinstance(out, dict)
        assert out.get("has_sufficient_data") is False
        assert out.get("life_ready_score") is None
        assert out.get("pillars_complete") == 0
        assert out.get("pillars_total") == 4
        assert out.get("trend") is None
        assert out.get("headline") is None
        comps = out.get("components")
        assert isinstance(comps, dict)
        for key in ("vibe", "body", "wellness", "financial", "stability"):
            assert key in comps
            assert "score" in comps[key]
            assert "weight" in comps[key]

    def test_compute_life_ready_score_unknown_user_insufficient(self, life_ready_app):
        missing = str(uuid.uuid4())
        with life_ready_app.app_context():
            out = compute_life_ready_score(missing)
        assert out["has_sufficient_data"] is False
        assert out["life_ready_score"] is None
        assert out["pillars_complete"] == 0
