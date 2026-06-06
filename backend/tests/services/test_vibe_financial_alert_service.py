"""
Regression: check_for_alerts must accept JWT-style UUID strings (P8 / #28) for user_id.
Service is tested directly (no Celery).
"""
from __future__ import annotations

import os
import sys
import uuid

import pytest
from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.alerts import UserAlert
from backend.models.database import db, init_database
from backend.models.user_models import User
from backend.models.vibe_tracker import VibeTrackedPerson
from backend.services.vibe_financial_alert_service import check_for_alerts


def _database_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


@pytest.fixture
def vibe_alert_app():
    url = _database_url()
    if not url:
        pytest.skip(
            "DATABASE_URL or TEST_DATABASE_URL required "
            "(init_database does not support SQLite-only runs)."
        )

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "vibe-financial-alert-test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    init_database(app)
    return app


class TestVibeFinancialAlertService:
    def test_check_for_alerts_accepts_uuid_string_user_id(self, vibe_alert_app):
        """Completes without raising when user_id is User.user_id (UUID string)."""
        ext_user_id = str(uuid.uuid4())
        person_id = uuid.uuid4()
        email = f"vibe_alert_svc_{ext_user_id[:12]}@example.com"

        with vibe_alert_app.app_context():
            user = User(
                user_id=ext_user_id,
                email=email,
                password_hash="unused",
            )
            db.session.add(user)
            db.session.flush()

            person = VibeTrackedPerson(
                id=person_id,
                user_id=user.id,
                nickname=f"p{uuid.uuid4().hex[:8]}",
            )
            db.session.add(person)
            db.session.commit()

            uid = user.id
            try:
                out = check_for_alerts(user.user_id, person_id)
                assert isinstance(out, list)
            finally:
                UserAlert.query.filter_by(user_id=uid).delete(
                    synchronize_session=False
                )
                p = db.session.get(VibeTrackedPerson, person_id)
                if p is not None:
                    db.session.delete(p)
                u = User.query.filter_by(user_id=ext_user_id).first()
                if u is not None:
                    db.session.delete(u)
                db.session.commit()
