"""
Regression: build_forecast_for_user must accept JWT-style UUID strings (P8 / #28)
for user_id and resolve User via User.user_id.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime

import pytest
from flask import Flask
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.models.database import db, init_database
from backend.models.user_models import User
from backend.services.cash_forecast_service import build_forecast_for_user


def _database_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


@pytest.fixture
def cash_forecast_app():
    url = _database_url()
    if not url:
        pytest.skip(
            "DATABASE_URL or TEST_DATABASE_URL required "
            "(init_database does not support SQLite-only runs)."
        )

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "cash-forecast-service-test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    init_database(app)
    return app


class TestCashForecastService:
    def test_build_forecast_for_user_accepts_uuid_string(self, cash_forecast_app):
        """Completes without raising when user_id is User.user_id (UUID string)."""
        ext_user_id = str(uuid.uuid4())
        email = f"cash_fc_svc_{ext_user_id[:12]}@example.com"

        with cash_forecast_app.app_context():
            user = User(
                user_id=ext_user_id,
                email=email,
                password_hash="unused",
            )
            db.session.add(user)
            db.session.commit()

            try:
                daily, summaries, rel_bd = build_forecast_for_user(
                    user.user_id, days=90
                )
                assert isinstance(daily, list)
                assert isinstance(summaries, list)
                assert isinstance(rel_bd, list)
            finally:
                row = User.query.filter_by(user_id=ext_user_id).first()
                if row is not None:
                    db.session.delete(row)
                    db.session.commit()

    def test_build_forecast_for_user_surfaces_balance_set_state(self, cash_forecast_app):
        """NULL profile balance projects from $0 and explicit balance is preserved."""
        unset_user_id = str(uuid.uuid4())
        set_user_id = str(uuid.uuid4())
        unset_email = f"cash_fc_unset_{unset_user_id[:12]}@example.com"
        set_email = f"cash_fc_set_{set_user_id[:12]}@example.com"

        with cash_forecast_app.app_context():
            users = [
                User(
                    user_id=unset_user_id,
                    email=unset_email,
                    password_hash="unused",
                ),
                User(
                    user_id=set_user_id,
                    email=set_email,
                    password_hash="unused",
                ),
            ]
            db.session.add_all(users)
            db.session.flush()
            db.session.execute(
                text(
                    """
                    INSERT INTO user_profiles (
                        email, current_balance, balance_last_updated, important_dates
                    )
                    VALUES
                        (:unset_email, NULL, NULL, '{}'),
                        (:set_email, 2500.0, :updated_at, '{}')
                    """
                ),
                {
                    "unset_email": unset_email,
                    "set_email": set_email,
                    "updated_at": datetime.utcnow(),
                },
            )
            db.session.commit()

            try:
                unset_result = build_forecast_for_user(unset_user_id, days=90)
                unset_daily, unset_summaries, unset_rel_bd = unset_result
                assert unset_result.balance_set is False
                assert isinstance(unset_daily, list)
                assert isinstance(unset_summaries, list)
                assert isinstance(unset_rel_bd, list)
                assert unset_daily
                assert unset_daily[0]["opening_balance"] == 0.0

                set_result = build_forecast_for_user(set_user_id, days=90)
                set_daily, set_summaries, set_rel_bd = set_result
                assert set_result.balance_set is True
                assert isinstance(set_daily, list)
                assert isinstance(set_summaries, list)
                assert isinstance(set_rel_bd, list)
                assert set_daily
                assert set_daily[0]["opening_balance"] == 2500.0
            finally:
                db.session.execute(
                    text("DELETE FROM user_profiles WHERE email IN (:unset_email, :set_email)"),
                    {"unset_email": unset_email, "set_email": set_email},
                )
                User.query.filter(User.user_id.in_([unset_user_id, set_user_id])).delete(
                    synchronize_session=False
                )
                db.session.commit()
