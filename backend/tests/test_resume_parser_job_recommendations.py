"""
Job recommendation engine regression tests (#113 Phase C1).

Uses neutral career-profile fixtures (not demo personas). Requires PostgreSQL
with seeded job_postings (see backend/scripts/seed_job_postings.py).
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta
from statistics import variance

import jwt
import pytest
from flask import Flask
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.api import register_all_apis
from backend.auth.decorators import JWT_ALGORITHM, JWT_SECRET_KEY
from backend.models.career_profile import CareerProfile
from backend.models.database import db, init_database
from backend.models.user_models import User
from backend.services.career_title_classifier import classify_career_title
from backend.utils.mingus_job_recommendation_engine import (
    MingusJobRecommendationEngine,
    TRANSITION_AFFINITY,
    get_pg_connection,
)

FIXTURE_TECH_NYC = {
    "bls_career_field": "Technology",
    "seniority_level": "mid",
    "msa": "35620",
    "target_comp": 130000,
    "current_role": "Software Engineer",
}

FIXTURE_HEALTHCARE_ATLANTA = {
    "bls_career_field": "Healthcare (Clinical)",
    "seniority_level": "mid",
    "msa": "12060",
    "target_comp": 95000,
    "current_role": "Registered Nurse",
}

FIXTURE_MARKETING_CHICAGO = {
    "bls_career_field": "Marketing & Communications",
    "seniority_level": "mid",
    "msa": "16980",
    "target_comp": 90000,
    "current_role": "Marketing Coordinator",
}

TECH_AFFINITY_FIELDS = frozenset(TRANSITION_AFFINITY["Technology"])
CREATIVE_ALLOWED_FIELDS = frozenset(
    {
        "Creative & Design",
        "Marketing & Communications",
        "Technology",
        "Media & Journalism",
    }
)
CREATIVE_UNRELATED_FIELDS = frozenset(
    {
        "Healthcare (Clinical)",
        "Construction & Trades",
        "Hospitality & Food Service",
    }
)


def _postgres_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


def _require_postgres() -> str:
    url = _postgres_url()
    if not url or not url.startswith(("postgresql", "postgres")):
        pytest.skip(
            "Job recommendation tests require PostgreSQL with job_postings seed. "
            "Set DATABASE_URL or TEST_DATABASE_URL."
        )
    return url


def _require_job_postings_seed() -> None:
    _require_postgres()
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM job_postings WHERE is_active = true")
        count = cur.fetchone()["c"]
        conn.close()
    except Exception as exc:
        pytest.skip(f"job_postings table unavailable: {exc}")
    if not count:
        pytest.skip("job_postings seed empty — run backend/scripts/seed_job_postings.py")


@pytest.fixture(scope="module")
def recommendation_engine():
    _require_job_postings_seed()
    return MingusJobRecommendationEngine()


def _tier_lists(result: dict) -> list[list]:
    return [
        result[key]
        for key in ("same_level", "reach", "conservative")
        if isinstance(result.get(key), list)
    ]


def _tier_job_count(result: dict) -> int:
    return sum(len(tier) for tier in _tier_lists(result))


def _has_nonempty_tier(result: dict) -> bool:
    return any(result.get(t) for t in ("same_level", "reach", "conservative"))


def _job_titles(result: dict) -> set[str]:
    titles: set[str] = set()
    for tier in _tier_lists(result):
        for job in tier:
            title = job.get("title")
            if title:
                titles.add(title)
    return titles


def _career_fields_in_tiers(result: dict, tier_names: tuple[str, ...]) -> set[str]:
    fields: set[str] = set()
    for name in tier_names:
        for job in result.get(name) or []:
            field = job.get("career_field")
            if field:
                fields.add(field)
    return fields


def _all_scores(result: dict) -> list[float]:
    scores: list[float] = []
    for tier in _tier_lists(result):
        for job in tier:
            score = job.get("overall_score")
            if score is not None:
                scores.append(float(score))
    return scores


def _top_scored_job(result: dict) -> dict | None:
    best: dict | None = None
    best_score = -1.0
    for tier in _tier_lists(result):
        for job in tier:
            score = float(job.get("overall_score") or 0)
            if score > best_score:
                best_score = score
                best = job
    return best


class TestProcessRecommendationsFixtures:
    """Tasks 3–4: profile-driven engine output (no persona names)."""

    def test_technology_nyc_mid_returns_nonempty_tiers(self, recommendation_engine):
        result = recommendation_engine.process_recommendations("test-user-1", FIXTURE_TECH_NYC)
        assert _has_nonempty_tier(result), result
        assert _tier_job_count(result) > 0

    def test_healthcare_atlanta_mid_returns_nonempty_tiers(self, recommendation_engine):
        result = recommendation_engine.process_recommendations(
            "test-user-2", FIXTURE_HEALTHCARE_ATLANTA
        )
        assert _has_nonempty_tier(result), result
        assert (
            result.get("same_level")
            or result.get("reach")
            or result.get("conservative")
        )

    def test_different_profiles_return_different_job_titles(self, recommendation_engine):
        result_tech = recommendation_engine.process_recommendations(
            "test-user-1", FIXTURE_TECH_NYC
        )
        result_health = recommendation_engine.process_recommendations(
            "test-user-2", FIXTURE_HEALTHCARE_ATLANTA
        )
        tech_titles = _job_titles(result_tech)
        health_titles = _job_titles(result_health)
        assert tech_titles, "Technology/NYC returned no jobs"
        assert health_titles, "Healthcare/Atlanta returned no jobs"
        assert tech_titles != health_titles, (
            "Engine returning same jobs for different fields"
        )

    def test_multi_dimensional_scoring_produces_differentiated_results(
        self, recommendation_engine
    ):
        result_tech = recommendation_engine.process_recommendations(
            "score-user-tech", FIXTURE_TECH_NYC
        )
        result_mkt = recommendation_engine.process_recommendations(
            "score-user-mkt", FIXTURE_MARKETING_CHICAGO
        )
        top_tech = _top_scored_job(result_tech)
        top_mkt = _top_scored_job(result_mkt)
        assert top_tech and top_mkt, "Expected scored jobs in both profiles"
        assert top_tech.get("title") != top_mkt.get("title"), (
            "Top-scored job should differ across career fields"
        )

        scores = _all_scores(result_tech) + _all_scores(result_mkt)
        assert len(scores) >= 2, "Need multiple scored jobs to assess variance"
        assert variance(scores) > 0, "Scores must not be flat (all identical)"


class TestTransitionAffinityConservativePath:
    """Task 7: affinity conservative tier when same-field MSA jobs are removed."""

    def test_conservative_uses_technology_affinity_when_local_tech_removed(
        self, recommendation_engine
    ):
        conn = get_pg_connection()
        conn.autocommit = False
        try:
            cur = conn.cursor()
            cur.execute(
                """
                DELETE FROM job_postings
                WHERE career_field = %s
                  AND msa_code = %s
                  AND seniority_level = %s
                """,
                ("Technology", "35620", "mid"),
            )
            result = recommendation_engine.process_recommendations(
                "affinity-user", FIXTURE_TECH_NYC
            )
            conservative_fields = _career_fields_in_tiers(result, ("conservative",))
            assert conservative_fields, (
                "Expected conservative tier jobs via transition affinity"
            )
            assert conservative_fields & TECH_AFFINITY_FIELDS, (
                f"Conservative tier should include Technology affinity fields; "
                f"got {conservative_fields}"
            )
            assert not (
                conservative_fields & {"Hospitality & Food Service", "Retail & Consumer"}
            ), (
                f"Conservative tier must not include unrelated fields; "
                f"got {conservative_fields}"
            )
        finally:
            conn.rollback()
            conn.close()


@pytest.fixture
def recommendations_app(monkeypatch):
    url = _require_postgres()
    monkeypatch.setenv("DATABASE_URL", url)
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "recommendations-endpoint-test"
    app.config["WTF_CSRF_ENABLED"] = False
    init_database(app)
    register_all_apis(app)
    return app


def _make_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": int((datetime.utcnow() + timedelta(hours=2)).timestamp()),
    }
    raw = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return raw if isinstance(raw, str) else raw.decode("ascii")


class TestProcessResumeEndpointGuards:
    """Task 5: block seed/placeholder roles and industries on process-resume."""

    def test_seed_industry_returns_422(self, recommendations_app):
        email = f"rec-industry-{uuid.uuid4().hex[:8]}@example.com"
        ext_id = str(uuid.uuid4())
        with recommendations_app.app_context():
            user = User(user_id=ext_id, email=email, tier="budget")
            db.session.add(user)
            db.session.flush()
            cp = CareerProfile(
                user_id=user.id,
                current_role="Software Engineer",
                bls_career_field="Unknown",
                seniority_level="mid",
            )
            db.session.add(cp)
            db.session.commit()
            token = _make_token(ext_id, email)

        resp = recommendations_app.test_client().post(
            "/api/recommendations/process-resume",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
        assert resp.get_json().get("error") == "career_profile_incomplete"

        with recommendations_app.app_context():
            row = User.query.filter_by(email=email).first()
            if row:
                db.session.execute(
                    text("DELETE FROM career_profile WHERE user_id = :uid"),
                    {"uid": row.id},
                )
                db.session.delete(row)
            db.session.commit()

    def test_seed_role_returns_422(self, recommendations_app):
        email = f"rec-seed-{uuid.uuid4().hex[:8]}@example.com"
        ext_id = str(uuid.uuid4())
        internal_user_id = None
        with recommendations_app.app_context():
            user = User(user_id=ext_id, email=email, tier="budget")
            db.session.add(user)
            db.session.flush()
            internal_user_id = user.id
            cp = CareerProfile(
                user_id=internal_user_id,
                current_role="test",
                bls_career_field="Technology",
                seniority_level="mid",
                target_comp=100000.0,
            )
            db.session.add(cp)
            db.session.commit()
            token = _make_token(ext_id, email)

        client = recommendations_app.test_client()
        resp = client.post(
            "/api/recommendations/process-resume",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
        body = resp.get_json()
        assert body.get("error") == "career_profile_incomplete"

        with recommendations_app.app_context():
            db.session.execute(
                text("DELETE FROM career_profile WHERE user_id = :uid"),
                {"uid": internal_user_id},
            )
            row = User.query.filter_by(email=email).first()
            if row:
                db.session.delete(row)
            db.session.commit()


class TestCareerClassificationRecommendations:
    """Task 6: title classification + recommendations stay in-field / affinity."""

    def test_senior_product_designer_classification_and_recommendations(
        self, recommendation_engine, recommendations_app
    ):
        email = f"designer-{uuid.uuid4().hex[:8]}@example.com"
        ext_id = str(uuid.uuid4())
        with recommendations_app.app_context():
            user = User(user_id=ext_id, email=email, tier="budget")
            db.session.add(user)
            db.session.flush()
            cp = CareerProfile(
                user_id=user.id,
                current_role="Senior Product Designer",
                industry=None,
            )
            db.session.add(cp)
            db.session.commit()

            result = classify_career_title(
                raw_title="Senior Product Designer",
                raw_industry=None,
                user_id=user.id,
                db_session=db.session,
            )
            if result.get("confidence", 0) >= 0.5:
                cp.bls_career_field = result["career_field"]
                cp.seniority_level = result["seniority_level"]
                cp.is_management = result.get("is_management")
                cp.title_normalization_source = result.get("source", "llm")
                db.session.commit()

            db.session.refresh(cp)
            assert cp.bls_career_field == "Creative & Design"
            assert cp.seniority_level == "senior"
            assert cp.title_normalization_source in (
                "llm",
                "rule",
                "fallback_on_error",
            )

            profile_dict = {
                "bls_career_field": cp.bls_career_field,
                "seniority_level": cp.seniority_level,
                "msa": "35620",
                "target_comp": 120000,
                "current_role": cp.current_role,
            }

        recs = recommendation_engine.process_recommendations(ext_id, profile_dict)
        relevant = _career_fields_in_tiers(recs, ("conservative", "same_level"))
        assert relevant, "Expected jobs in conservative or same_level tier"
        assert relevant.issubset(CREATIVE_ALLOWED_FIELDS), (
            f"Recommendations should be Creative & Design or affinity fields; got {relevant}"
        )
        assert not (relevant & CREATIVE_UNRELATED_FIELDS), (
            f"Unexpected unrelated fields in tiers: {relevant}"
        )

        with recommendations_app.app_context():
            u = User.query.filter_by(email=email).first()
            if u:
                db.session.execute(
                    text("DELETE FROM career_profile WHERE user_id = :uid"),
                    {"uid": u.id},
                )
                db.session.delete(u)
                db.session.commit()
