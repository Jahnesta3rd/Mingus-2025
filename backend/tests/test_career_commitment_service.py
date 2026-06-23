"""Unit tests for career commitment classification service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from backend.services.career_commitment_service import compute_commitment_type


def _mock_profile(
    *,
    skill_development_frequency=None,
    field_research_done=None,
    real_world_signal=None,
    review_stage="initial",
):
    profile = MagicMock()
    profile.skill_development_frequency = skill_development_frequency
    profile.field_research_done = field_research_done
    profile.real_world_signal = real_world_signal
    profile.review_stage = review_stage
    return profile


def _mock_db_session(profile):
    db_session = MagicMock()
    db_session.query.return_value.filter_by.return_value.first.return_value = profile
    return db_session


def test_type_3_via_real_world_signal():
    profile = _mock_profile(
        skill_development_frequency=2,
        field_research_done=False,
        real_world_signal=True,
    )
    db_session = _mock_db_session(profile)

    result = compute_commitment_type(1, db_session)

    assert result["commitment_type"] == "type_3"
    assert result["commitment_score"] == 40
    assert result["partial_data"] is False
    assert "Real-world income or project signal" in result["classification_rationale"]
    assert profile.commitment_type == "type_3"
    assert profile.commitment_score == 40
    db_session.commit.assert_called_once()


def test_type_3_via_high_score():
    profile = _mock_profile(
        skill_development_frequency=5,
        field_research_done=True,
        real_world_signal=False,
    )
    db_session = _mock_db_session(profile)

    result = compute_commitment_type(2, db_session)

    assert result["commitment_type"] == "type_3"
    assert result["commitment_score"] == 70
    assert result["partial_data"] is False
    assert "Real-world income or project signal" in result["classification_rationale"]


def test_type_2():
    profile = _mock_profile(
        skill_development_frequency=4,
        field_research_done=True,
        real_world_signal=False,
    )
    db_session = _mock_db_session(profile)

    result = compute_commitment_type(3, db_session)

    assert result["commitment_type"] == "type_2"
    assert result["commitment_score"] == 65
    assert result["partial_data"] is False
    assert "Consistent practice and active research" in result["classification_rationale"]


def test_type_1():
    profile = _mock_profile(
        skill_development_frequency=2,
        field_research_done=False,
        real_world_signal=False,
    )
    db_session = _mock_db_session(profile)

    result = compute_commitment_type(4, db_session)

    assert result["commitment_type"] == "type_1"
    assert result["commitment_score"] == 10
    assert result["partial_data"] is False
    assert "hobby-stage commitment" in result["classification_rationale"]


def test_unclassified():
    db_session = _mock_db_session(None)

    result = compute_commitment_type(5, db_session)

    assert result["commitment_type"] == "unclassified"
    assert result["commitment_score"] == 0
    assert result["partial_data"] is True
    assert "Not enough answers to classify" in result["classification_rationale"]
    db_session.add.assert_called_once()
    added_profile = db_session.add.call_args[0][0]
    assert added_profile.user_id == 5
    assert added_profile.commitment_type == "unclassified"
    assert added_profile.review_stage == "initial"
    assert added_profile.classified_at is not None
    db_session.commit.assert_called_once()
