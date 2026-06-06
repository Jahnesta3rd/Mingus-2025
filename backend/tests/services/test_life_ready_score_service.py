"""
Focused regression: compute_life_ready_score must accept JWT-style UUID strings
(P8 / #28) and resolve User via User.user_id, not integer PK on db.session.get.

Phase 1A: eight nominal components, inactive Career (excluded + renormalized weights),
roof/vehicle active with neutral fill, pillar 1 includes roof/vehicle.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import date
from types import SimpleNamespace

import pytest
from flask import Flask
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.database import db, init_database
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

    def test_weighted_total_renormalizes_seven_active_only(self):
        """All active components equal → full score; inactive career must not pull toward 50."""
        score = lrss._weighted_total(
            financial=80,
            roof=80,
            vibe=80,
            vehicle=80,
            body=80,
            wellness=80,
            stability=80,
        )
        assert score == 80
        # Hypothetical mistake: treat career as 50 with full nominal weights summed to 1.0.
        phantom_blend = (
            sum(lrss._NOMINAL_WEIGHTS[k] * 80 for k in lrss._ACTIVE_COMPONENT_KEYS)
            + lrss._NOMINAL_WEIGHTS["career"] * 50
        )
        wrong_if_career_neutral_filled = int(
            max(0, min(100, round(phantom_blend / 1.0)))
        )
        assert wrong_if_career_neutral_filled != score

    def test_weighted_total_matches_manual_blend(self):
        vals = dict(
            financial=100,
            roof=70,
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
        assert comps["career"]["active"] is False
        assert comps["career"]["score"] is None
        for key in ("financial", "roof", "vibe", "vehicle", "body", "wellness", "stability"):
            assert comps[key]["active"] is True

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
        """Pillar 1 from roof only + wellness + financial → sufficient data; missing vehicle uses neutral 50."""
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
        assert out["life_ready_score"] == 66
        comps = out["components"]
        assert comps["roof"]["score"] == 70
        assert comps["vehicle"]["score"] == 50
        assert comps["career"]["active"] is False
        assert comps["career"]["score"] is None

    def test_career_socket_excluded_from_renormalized_blend(self, life_ready_app):
        """Career stays inactive (no score); the headline score matches only the 7 active slots."""
        ext_id = str(uuid.uuid4())
        email = f"life_ready_career_blend_{ext_id[:12]}@example.com"
        # 80% savings rate → financial component 80 (integer-friendly for payload vs blend).
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
        assert comps["career"]["active"] is False
        assert comps["career"]["score"] is None
        assert "career" not in lrss._ACTIVE_COMPONENT_KEYS

        active_weighted = sum(
            lrss._NOMINAL_WEIGHTS[k] * comps[k]["score"]
            for k in lrss._ACTIVE_COMPONENT_KEYS
        )
        expected = lrss._clamp_0_100(active_weighted / lrss._ACTIVE_WEIGHT_SUM)
        assert out["life_ready_score"] == expected

        # If career were incorrectly neutral-filled at 50 into an 8-way / 1.0 blend, the score would differ.
        phantom_numerator = active_weighted + lrss._NOMINAL_WEIGHTS["career"] * 50
        wrong_if_career_included = lrss._clamp_0_100(phantom_numerator / 1.0)
        assert wrong_if_career_included != out["life_ready_score"]
