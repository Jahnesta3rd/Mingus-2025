"""Life alerts on /api/life-ready-score — career domain only; score unchanged."""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from flask import Flask
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.career_profile import CareerProfile
from backend.models.database import db, init_database
from backend.models.employer import Employer, EmployerHealthSnapshot, LayoffEvent
from backend.models.life_ledger import LifeLedgerProfile
from backend.models.user_models import User
from backend.models.wellness import WeeklyCheckin
from backend.services import life_ready_score_service as lrss
from backend.services.life_ready_score_service import compute_life_ready_score


def _database_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


@pytest.fixture
def life_alerts_app():
    url = _database_url()
    if not url:
        pytest.skip(
            "DATABASE_URL or TEST_DATABASE_URL required "
            "(init_database does not support SQLite-only runs)."
        )

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "life-alerts-test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    init_database(app)
    return app


def _layoff_event(
    employer_id: int,
    *,
    filing_date: date,
    review_state: str = "auto",
) -> LayoffEvent:
    return LayoffEvent(
        employer_id=employer_id,
        filing_date=filing_date,
        accession_number=f"000{employer_id:07d}-26-000001",
        confidence=Decimal("0.950"),
        review_state=review_state,
    )


def _seed_sufficient_user(app, *, email_prefix: str = "life_alert"):
    ext_id = str(uuid.uuid4())
    email = f"{email_prefix}_{ext_id[:12]}@example.com"
    fin_json = json.dumps({"monthlyTakehome": 10000, "monthlyExpenses": {}})

    user = User(user_id=ext_id, email=email, password_hash="unused")
    db.session.add(user)
    db.session.flush()
    db.session.execute(
        text(
            """
            INSERT INTO user_profiles (email, important_dates, financial_info)
            VALUES (:email, '{}', :financial_info)
            """
        ),
        {"email": email, "financial_info": fin_json},
    )
    db.session.add(LifeLedgerProfile(user_id=user.id, roof_score=70))
    db.session.add(
        WeeklyCheckin(
            user_id=user.id,
            week_ending_date=date(2026, 5, 10),
            overall_mood=8,
        )
    )
    db.session.commit()
    return user, ext_id, email


class TestGetLifeAlerts:
    def test_active_layoff_event_high_alert(self, life_alerts_app):
        cik = f"{uuid.uuid4().int % 10000000000:010d}"

        with life_alerts_app.app_context():
            user, _, _ = _seed_sufficient_user(life_alerts_app, email_prefix="layoff_hi")
            employer = Employer(cik=cik, name="Layoff Corp")
            db.session.add(employer)
            db.session.flush()
            db.session.add(
                CareerProfile(user_id=user.id, employer_cik=cik, satisfaction=3)
            )
            db.session.add(
                _layoff_event(
                    employer.id,
                    filing_date=date.today() - timedelta(days=10),
                )
            )
            db.session.commit()

            try:
                alerts = lrss._get_life_alerts(user.id)
            finally:
                db.session.query(LayoffEvent).filter_by(employer_id=employer.id).delete()
                db.session.query(CareerProfile).filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.delete(employer)
                db.session.commit()

        assert len(alerts) == 1
        assert alerts[0].severity == "high"
        assert alerts[0].domain == "career"
        assert alerts[0].action_target == "career_risk"

    def test_layoff_event_older_than_90_days_no_alert(self, life_alerts_app):
        cik = f"{uuid.uuid4().int % 10000000000:010d}"

        with life_alerts_app.app_context():
            user, _, _ = _seed_sufficient_user(life_alerts_app, email_prefix="layoff_old")
            employer = Employer(cik=cik, name="Old Layoff Corp")
            db.session.add(employer)
            db.session.flush()
            db.session.add(
                CareerProfile(user_id=user.id, employer_cik=cik, satisfaction=3)
            )
            db.session.add(
                _layoff_event(
                    employer.id,
                    filing_date=date.today() - timedelta(days=100),
                )
            )
            db.session.commit()

            try:
                alerts = lrss._get_life_alerts(user.id)
            finally:
                db.session.query(LayoffEvent).filter_by(employer_id=employer.id).delete()
                db.session.query(CareerProfile).filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.delete(employer)
                db.session.commit()

        assert alerts == []

    def test_layoff_event_needs_review_no_high_alert(self, life_alerts_app):
        cik = f"{uuid.uuid4().int % 10000000000:010d}"

        with life_alerts_app.app_context():
            user, _, _ = _seed_sufficient_user(life_alerts_app, email_prefix="layoff_rev")
            employer = Employer(cik=cik, name="Review Layoff Corp")
            db.session.add(employer)
            db.session.flush()
            db.session.add(
                CareerProfile(user_id=user.id, employer_cik=cik, satisfaction=3)
            )
            db.session.add(
                _layoff_event(
                    employer.id,
                    filing_date=date.today() - timedelta(days=5),
                    review_state="needs_review",
                )
            )
            db.session.commit()

            try:
                alerts = lrss._get_life_alerts(user.id)
            finally:
                db.session.query(LayoffEvent).filter_by(employer_id=employer.id).delete()
                db.session.query(CareerProfile).filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.delete(employer)
                db.session.commit()

        assert not any(a.severity == "high" for a in alerts)

    def test_stressed_employer_health_moderate_alert(self, life_alerts_app):
        cik = f"{uuid.uuid4().int % 10000000000:010d}"

        with life_alerts_app.app_context():
            user, _, _ = _seed_sufficient_user(life_alerts_app, email_prefix="stress_mod")
            employer = Employer(cik=cik, name="Stressed Corp")
            db.session.add(employer)
            db.session.flush()
            db.session.add(
                CareerProfile(user_id=user.id, employer_cik=cik, satisfaction=3)
            )
            db.session.add(
                EmployerHealthSnapshot(
                    employer_id=employer.id,
                    score=Decimal("28.00"),
                    refreshed_at=datetime.utcnow(),
                    fiscal_period_end=date(2026, 3, 31),
                )
            )
            db.session.commit()

            try:
                alerts = lrss._get_life_alerts(user.id)
            finally:
                db.session.query(EmployerHealthSnapshot).filter_by(
                    employer_id=employer.id
                ).delete()
                db.session.query(CareerProfile).filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.delete(employer)
                db.session.commit()

        assert len(alerts) == 1
        assert alerts[0].severity == "moderate"
        assert alerts[0].domain == "career"

    def test_layoff_suppresses_moderate_alert(self, life_alerts_app):
        cik = f"{uuid.uuid4().int % 10000000000:010d}"

        with life_alerts_app.app_context():
            user, _, _ = _seed_sufficient_user(life_alerts_app, email_prefix="layoff_mod")
            employer = Employer(cik=cik, name="Both Corp")
            db.session.add(employer)
            db.session.flush()
            db.session.add(
                CareerProfile(user_id=user.id, employer_cik=cik, satisfaction=3)
            )
            db.session.add(
                EmployerHealthSnapshot(
                    employer_id=employer.id,
                    score=Decimal("28.00"),
                    refreshed_at=datetime.utcnow(),
                    fiscal_period_end=date(2026, 3, 31),
                )
            )
            db.session.add(
                _layoff_event(
                    employer.id,
                    filing_date=date.today() - timedelta(days=7),
                )
            )
            db.session.commit()

            try:
                alerts = lrss._get_life_alerts(user.id)
            finally:
                db.session.query(LayoffEvent).filter_by(employer_id=employer.id).delete()
                db.session.query(EmployerHealthSnapshot).filter_by(
                    employer_id=employer.id
                ).delete()
                db.session.query(CareerProfile).filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.delete(employer)
                db.session.commit()

        assert len(alerts) == 1
        assert alerts[0].severity == "high"

    def test_income_percentile_watch_alert(self, life_alerts_app, monkeypatch):
        cp = SimpleNamespace(employer_cik="", income_percentile=18)
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = cp
        monkeypatch.setattr(lrss.CareerProfile, "query", mock_query)

        with life_alerts_app.app_context():
            alerts = lrss._get_life_alerts(999)

        assert len(alerts) == 1
        assert alerts[0].severity == "watch"
        assert alerts[0].domain == "career"
        assert "18th percentile" in alerts[0].detail

    def test_no_career_profile_empty_alerts(self, life_alerts_app):
        with life_alerts_app.app_context():
            user, _, _ = _seed_sufficient_user(life_alerts_app, email_prefix="no_cp")
            try:
                alerts = lrss._get_life_alerts(user.id)
            finally:
                db.session.delete(user)
                db.session.commit()

        assert alerts == []

    def test_all_clear_no_alerts(self, life_alerts_app):
        cik = f"{uuid.uuid4().int % 10000000000:010d}"

        with life_alerts_app.app_context():
            user, _, _ = _seed_sufficient_user(life_alerts_app, email_prefix="all_clear")
            employer = Employer(cik=cik, name="Healthy Corp")
            db.session.add(employer)
            db.session.flush()
            db.session.add(
                CareerProfile(user_id=user.id, employer_cik=cik, satisfaction=4)
            )
            db.session.add(
                EmployerHealthSnapshot(
                    employer_id=employer.id,
                    score=Decimal("72.00"),
                    refreshed_at=datetime.utcnow(),
                    fiscal_period_end=date(2026, 3, 31),
                )
            )
            db.session.commit()

            try:
                alerts = lrss._get_life_alerts(user.id)
            finally:
                db.session.query(EmployerHealthSnapshot).filter_by(
                    employer_id=employer.id
                ).delete()
                db.session.query(CareerProfile).filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.delete(employer)
                db.session.commit()

        assert alerts == []


class TestLifeAlertsResponse:
    def test_life_alerts_always_present_on_response(self, life_alerts_app):
        with life_alerts_app.app_context():
            user, ext_id, email = _seed_sufficient_user(
                life_alerts_app, email_prefix="resp_present"
            )
            try:
                out = compute_life_ready_score(ext_id)
            finally:
                db.session.execute(
                    text("DELETE FROM user_profiles WHERE email = :email"),
                    {"email": email},
                )
                db.session.delete(user)
                db.session.commit()

        assert "life_alerts" in out
        assert out["life_alerts"] == []

    def test_score_unchanged_when_alerts_present(self, life_alerts_app):
        cik = f"{uuid.uuid4().int % 10000000000:010d}"

        with life_alerts_app.app_context():
            user, ext_id, email = _seed_sufficient_user(
                life_alerts_app, email_prefix="score_same"
            )
            try:
                before = compute_life_ready_score(ext_id)
                score_before = before["life_ready_score"]

                employer = Employer(cik=cik, name="Alert Corp")
                db.session.add(employer)
                db.session.flush()
                db.session.add(
                    CareerProfile(user_id=user.id, employer_cik=cik, satisfaction=3)
                )
                db.session.add(
                    _layoff_event(
                        employer.id,
                        filing_date=date.today() - timedelta(days=3),
                    )
                )
                db.session.commit()

                after = compute_life_ready_score(ext_id)
            finally:
                db.session.query(LayoffEvent).filter_by(employer_id=employer.id).delete()
                db.session.query(CareerProfile).filter_by(user_id=user.id).delete()
                db.session.delete(employer)
                db.session.execute(
                    text("DELETE FROM user_profiles WHERE email = :email"),
                    {"email": email},
                )
                db.session.delete(user)
                db.session.commit()

        assert len(after["life_alerts"]) == 1
        assert after["life_alerts"][0]["severity"] == "high"
        assert after["life_ready_score"] == score_before
