"""Unit tests for HPRS commitment pipeline credit."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from backend.services.hprs_career_risk_service import apply_pipeline_credit


def _mock_commitment_profile(*, commitment_type=None, skill_development_frequency=0):
    profile = MagicMock()
    profile.commitment_type = commitment_type
    profile.skill_development_frequency = skill_development_frequency
    return profile


def _mock_db_session(profile):
    db_session = MagicMock()
    db_session.query.return_value.filter_by.return_value.first.return_value = profile
    return db_session


def _base_result(score: int) -> dict:
    return {
        "career_risk_score": score,
        "career_risk_band": "MODERATE",
        "career_modifier": -3,
        "active_layoff": False,
        "data_source": "sec_edgar",
        "employer_health_score": 55,
    }


def test_pipeline_credit_applied():
    profile = _mock_commitment_profile(
        commitment_type="type_2",
        skill_development_frequency=4,
    )
    db_session = _mock_db_session(profile)

    result = apply_pipeline_credit(_base_result(30), 1, db_session)

    assert result["career_risk_score"] == 26
    assert result["pipeline_credit"] == 4
    assert result["commitment_type"] == "type_2"
    assert result["career_risk_band"] == "MODERATE"


def test_pipeline_credit_not_applied_low_skill():
    profile = _mock_commitment_profile(
        commitment_type="type_2",
        skill_development_frequency=3,
    )
    db_session = _mock_db_session(profile)

    result = apply_pipeline_credit(_base_result(30), 1, db_session)

    assert result["pipeline_credit"] == 0
    assert result["career_risk_score"] == 30
    assert result["career_risk_band"] == "MODERATE"


def test_pipeline_credit_not_applied_type_1():
    profile = _mock_commitment_profile(
        commitment_type="type_1",
        skill_development_frequency=5,
    )
    db_session = _mock_db_session(profile)

    result = apply_pipeline_credit(_base_result(30), 1, db_session)

    assert result["pipeline_credit"] == 0
    assert result["career_risk_score"] == 30


def test_credit_does_not_go_below_zero():
    profile = _mock_commitment_profile(
        commitment_type="type_3",
        skill_development_frequency=5,
    )
    db_session = _mock_db_session(profile)

    result = apply_pipeline_credit(_base_result(2), 1, db_session)

    assert result["career_risk_score"] == 0
    assert result["pipeline_credit"] == 4
    assert result["career_risk_band"] == "LOW"
