"""
Focused regression: compute_life_ready_score must accept JWT-style UUID strings
(P8 / #28) and resolve User via User.user_id, not integer PK on db.session.get.

Eight nominal components active including Career (employer health / satisfaction / neutral).
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.career_profile import CareerProfile
from backend.models.database import db, init_database
from backend.models.employer import Employer, EmployerHealthSnapshot
from backend.models.financial_setup import RecurringExpense
from backend.models.life_ledger import LifeLedgerProfile
from backend.models.transaction_schedule import IncomeStream
from backend.models.user_models import User
from backend.models.wellness import WeeklyCheckin
from backend.services import life_ready_score_service as lrss
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


_EXPECTED_COMPONENT_KEYS = (
    "financial",
    "roof",
    "career",
    "vibe",
    "vehicle",
    "body",
    "wellness",
    "stability",
)


class TestLifeReadyScoreWeights:
    """Pure unit tests (no database)."""

    def test_nominal_weights_sum_to_one(self):
        assert lrss._ACTIVE_WEIGHT_SUM == 1.0
        assert "career" in lrss._ACTIVE_COMPONENT_KEYS
        assert sum(lrss._NOMINAL_WEIGHTS[k] for k in lrss._ACTIVE_COMPONENT_KEYS) == 1.0

    def test_weighted_total_eight_active_equal_scores(self):
        """All eight active components equal → score equals input."""
        score = lrss._weighted_total(
            financial=80,
            roof=80,
            career=80,
            vibe=80,
            vehicle=80,
            body=80,
            wellness=80,
            stability=80,
        )
        assert score == 80

    def test_weighted_total_matches_manual_blend(self):
        vals = dict(
            financial=100,
            roof=70,
            career=50,
            vibe=50,
            vehicle=50,
            body=50,
            wellness=80,
            stability=10,
        )
        raw = sum(
            lrss._NOMINAL_WEIGHTS[k] * vals[k] for k in lrss._ACTIVE_COMPONENT_KEYS
        ) / float(lrss._ACTIVE_WEIGHT_SUM)
        assert lrss._weighted_total(**vals) == int(max(0, min(100, round(raw))))

    def test_pillar_one_meaningful_with_roof_only(self):
        p = SimpleNamespace(
            vibe_score=None,
            body_score=None,
            roof_score=60,
            vehicle_score=None,
        )
        assert lrss._vibe_body_pillar_meaningful(p, None) is True

    def test_pillar_one_meaningful_with_vehicle_only(self):
        p = SimpleNamespace(
            vibe_score=None,
            body_score=None,
            roof_score=None,
            vehicle_score=40,
        )
        assert lrss._vibe_body_pillar_meaningful(p, None) is True

    def test_satisfaction_to_career_score_mapping(self):
        for sat, expected in lrss._SATISFACTION_TO_CAREER_SCORE.items():
            cp = SimpleNamespace(employer_cik=None, satisfaction=sat)
            assert lrss._SATISFACTION_TO_CAREER_SCORE[int(cp.satisfaction)] == expected


class TestCareerComponentScorePaths:
    """Database-backed tests for _get_career_component_score paths."""

    def test_career_score_from_employer_health_snapshot(self, life_ready_app):
        ext_id = str(uuid.uuid4())
        email = f"life_ready_cik_{ext_id[:12]}@example.com"
        cik = f"{uuid.uuid4().int % 10000000000:010d}"

        with life_ready_app.app_context():
            user = User(user_id=ext_id, email=email, password_hash="unused")
            db.session.add(user)
            db.session.flush()

            employer = Employer(cik=cik, name="Test Employer Inc")
            db.session.add(employer)
            db.session.flush()
            db.session.add(
                EmployerHealthSnapshot(
                    employer_id=employer.id,
                    score=Decimal("72.50"),
                    refreshed_at=datetime.utcnow(),
                )
            )
            db.session.add(
                CareerProfile(user_id=user.id, employer_cik=cik, satisfaction=3)
            )
            db.session.commit()

            try:
                score = lrss._get_career_component_score(user.id)
            finally:
                cp = CareerProfile.query.filter_by(user_id=user.id).first()
                if cp is not None:
                    db.session.delete(cp)
                db.session.delete(user)
                db.session.flush()
                db.session.query(EmployerHealthSnapshot).filter_by(
                    employer_id=employer.id
                ).delete()
                db.session.delete(employer)
                db.session.commit()

        assert score == 72.5

    def test_career_score_self_report_satisfaction(self, life_ready_app):
        ext_id = str(uuid.uuid4())
        email = f"life_ready_sat_{ext_id[:12]}@example.com"

        with life_ready_app.app_context():
            user = User(user_id=ext_id, email=email, password_hash="unused")
            db.session.add(user)
            db.session.flush()
            db.session.add(
                CareerProfile(user_id=user.id, satisfaction=4, employer_cik=None)
            )
            db.session.commit()

            try:
                score = lrss._get_career_component_score(user.id)
            finally:
                cp = CareerProfile.query.filter_by(user_id=user.id).first()
                if cp is not None:
                    db.session.delete(cp)
                db.session.delete(user)
                db.session.commit()

        assert score == 65.0

    def test_career_score_neutral_fallback(self, life_ready_app):
        ext_id = str(uuid.uuid4())
        email = f"life_ready_neutral_{ext_id[:12]}@example.com"

        with life_ready_app.app_context():
            user = User(user_id=ext_id, email=email, password_hash="unused")
            db.session.add(user)
            db.session.flush()
            db.session.add(CareerProfile(user_id=user.id))
            db.session.commit()

            try:
                score = lrss._get_career_component_score(user.id)
            finally:
                cp = CareerProfile.query.filter_by(user_id=user.id).first()
                if cp is not None:
                    db.session.delete(cp)
                db.session.delete(user)
                db.session.commit()

        assert score == 50.0

    def test_career_score_neutral_no_career_profile_row(self, life_ready_app):
        ext_id = str(uuid.uuid4())
        email = f"life_ready_no_cp_{ext_id[:12]}@example.com"

        with life_ready_app.app_context():
            user = User(user_id=ext_id, email=email, password_hash="unused")
            db.session.add(user)
            db.session.commit()

            try:
                score = lrss._get_career_component_score(user.id)
            finally:
                db.session.delete(user)
                db.session.commit()

        assert score == 50.0


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
        assert tuple(comps.keys()) == _EXPECTED_COMPONENT_KEYS
        for key in _EXPECTED_COMPONENT_KEYS:
            assert "score" in comps[key]
            assert "weight" in comps[key]
            assert "active" in comps[key]
            assert comps[key]["weight"] == lrss._NOMINAL_WEIGHTS[key]
            assert comps[key]["active"] is True
        assert comps["career"]["score"] == 50

    def test_compute_life_ready_score_unknown_user_insufficient(self, life_ready_app):
        missing = str(uuid.uuid4())
        with life_ready_app.app_context():
            out = compute_life_ready_score(missing)
        assert out["has_sufficient_data"] is False
        assert out["life_ready_score"] is None
        assert out["pillars_complete"] == 0

    def test_three_pillars_roof_ledger_wellness_financial_real_score(
        self, life_ready_app
    ):
        """Pillar 1 from roof only + wellness + financial → sufficient data; career neutral 50."""
        ext_id = str(uuid.uuid4())
        email = f"life_ready_roof_{ext_id[:12]}@example.com"
        fin_json = json.dumps({"monthlyTakehome": 10000, "monthlyExpenses": {}})

        with life_ready_app.app_context():
            user = User(
                user_id=ext_id,
                email=email,
                password_hash="unused",
            )
            db.session.add(user)
            db.session.flush()
            db.session.execute(
                text(
                    """
                    INSERT INTO user_profiles (
                        email, important_dates, financial_info
                    )
                    VALUES (:email, '{}', :financial_info)
                    """
                ),
                {"email": email, "financial_info": fin_json},
            )
            db.session.add(
                LifeLedgerProfile(
                    user_id=user.id,
                    roof_score=70,
                )
            )
            db.session.add(
                WeeklyCheckin(
                    user_id=user.id,
                    week_ending_date=date(2026, 5, 10),
                    overall_mood=8,
                )
            )
            db.session.commit()

            try:
                out = compute_life_ready_score(ext_id)
            finally:
                db.session.execute(
                    text("DELETE FROM user_profiles WHERE email = :email"),
                    {"email": email},
                )
                u = User.query.filter_by(user_id=ext_id).first()
                if u is not None:
                    db.session.delete(u)
                    db.session.commit()

        assert out["has_sufficient_data"] is True
        assert out["pillars_complete"] == 3
        comps = out["components"]
        assert comps["roof"]["score"] == 70
        assert comps["vehicle"]["score"] == 50
        assert comps["career"]["active"] is True
        assert comps["career"]["score"] == 50

        expected = lrss._weighted_total(
            financial=100.0,
            roof=70.0,
            career=50.0,
            vibe=50.0,
            vehicle=50.0,
            body=50.0,
            wellness=80.0,
            stability=10.0,
        )
        assert out["life_ready_score"] == expected

    def test_career_included_in_eight_way_blend(self, life_ready_app):
        """Career is active; headline score matches all eight nominal-weight slots."""
        ext_id = str(uuid.uuid4())
        email = f"life_ready_career_blend_{ext_id[:12]}@example.com"
        fin_json = json.dumps(
            {"monthlyTakehome": 10000, "monthlyExpenses": {"rent": 2000}}
        )
        week = date(2026, 5, 3)

        with life_ready_app.app_context():
            user = User(
                user_id=ext_id,
                email=email,
                password_hash="unused",
            )
            db.session.add(user)
            db.session.flush()
            db.session.execute(
                text(
                    """
                    INSERT INTO user_profiles (
                        email, important_dates, financial_info
                    )
                    VALUES (:email, '{}', :financial_info)
                    """
                ),
                {"email": email, "financial_info": fin_json},
            )
            db.session.add(
                LifeLedgerProfile(
                    user_id=user.id,
                    vibe_score=72,
                    body_score=68,
                    roof_score=74,
                    vehicle_score=70,
                )
            )
            db.session.add(
                WeeklyCheckin(
                    user_id=user.id,
                    week_ending_date=week,
                    overall_mood=7,
                )
            )
            db.session.add(
                IncomeStream(
                    user_id=user.id,
                    label="job",
                    amount=3000,
                    frequency="monthly",
                    next_date=date(2026, 5, 15),
                    income_type="earned",
                    is_active=True,
                )
            )
            db.session.add(
                RecurringExpense(
                    user_id=user.id,
                    name="rent",
                    amount=1000,
                    category="housing",
                    frequency="monthly",
                    is_active=True,
                )
            )
            db.session.commit()

            try:
                out = compute_life_ready_score(ext_id)
            finally:
                db.session.execute(
                    text("DELETE FROM user_profiles WHERE email = :email"),
                    {"email": email},
                )
                u = User.query.filter_by(user_id=ext_id).first()
                if u is not None:
                    db.session.delete(u)
                    db.session.commit()

        assert out["has_sufficient_data"] is True
        comps = out["components"]
        assert comps["career"]["active"] is True
        assert comps["career"]["score"] == 50
        assert "career" in lrss._ACTIVE_COMPONENT_KEYS

        active_weighted = sum(
            lrss._NOMINAL_WEIGHTS[k] * comps[k]["score"]
            for k in lrss._ACTIVE_COMPONENT_KEYS
        )
        expected = lrss._clamp_0_100(active_weighted / lrss._ACTIVE_WEIGHT_SUM)
        assert out["life_ready_score"] == expected
