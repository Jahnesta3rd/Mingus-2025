#!/usr/bin/env python3
"""Career commitment classification from onboarding / check-in signals."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.models.career_commitment_profile import CareerCommitmentProfile

_SKILL_FREQ_POINTS: dict[int, int] = {
    1: 0,
    2: 10,
    3: 20,
    4: 35,
    5: 40,
}

_CLASSIFICATION_RATIONALE: dict[str, str] = {
    "type_3": "Real-world income or project signal detected — strong commitment.",
    "type_2": "Consistent practice and active research indicate serious intent.",
    "type_1": "Irregular practice without research signals a hobby-stage commitment.",
    "unclassified": "Not enough answers to classify — revisit after check-in.",
}


def get_classification_rationale(commitment_type: str | None) -> str | None:
    if not commitment_type or commitment_type == "unclassified":
        return None
    return _CLASSIFICATION_RATIONALE.get(commitment_type)


def _clamp_score(score: int) -> int:
    return max(0, min(100, score))


def _compute_score(
    skill_development_frequency: int | None,
    field_research_done: bool | None,
    real_world_signal: bool | None,
) -> tuple[int, bool]:
    """Return commitment_score (0-100) and whether inputs were incomplete."""
    score = 0
    partial_data = False

    if skill_development_frequency is None:
        partial_data = True
    else:
        score += _SKILL_FREQ_POINTS.get(skill_development_frequency, 0)

    if field_research_done is None:
        partial_data = True
    elif field_research_done:
        score += 30

    if real_world_signal:
        score += 30

    return _clamp_score(score), partial_data


def _classify_commitment_type(
    commitment_score: int,
    skill_development_frequency: int | None,
    field_research_done: bool | None,
    real_world_signal: bool | None,
    partial_data: bool,
) -> str:
    if partial_data and commitment_score == 0:
        return "unclassified"
    if real_world_signal is True or commitment_score >= 70:
        return "type_3"
    if (
        skill_development_frequency is not None
        and skill_development_frequency >= 3
        and field_research_done is True
        and commitment_score >= 30
    ):
        return "type_2"
    return "type_1"


def compute_commitment_type(user_id: int, db_session) -> dict[str, Any]:
    """Classify career commitment for a user and persist the result."""
    profile = (
        db_session.query(CareerCommitmentProfile)
        .filter_by(user_id=user_id)
        .first()
    )

    skill_development_frequency = (
        profile.skill_development_frequency if profile else None
    )
    field_research_done = profile.field_research_done if profile else None
    real_world_signal = profile.real_world_signal if profile else None

    commitment_score, partial_data = _compute_score(
        skill_development_frequency,
        field_research_done,
        real_world_signal,
    )
    commitment_type = _classify_commitment_type(
        commitment_score,
        skill_development_frequency,
        field_research_done,
        real_world_signal,
        partial_data,
    )

    now = datetime.utcnow()
    if profile:
        profile.commitment_type = commitment_type
        profile.commitment_score = commitment_score
        profile.last_reviewed_at = now
    else:
        profile = CareerCommitmentProfile(
            user_id=user_id,
            commitment_type=commitment_type,
            commitment_score=commitment_score,
            classified_at=now,
            last_reviewed_at=now,
            review_stage="initial",
        )
        db_session.add(profile)

    db_session.commit()

    return {
        "commitment_type": commitment_type,
        "commitment_score": commitment_score,
        "partial_data": partial_data,
        "classification_rationale": _CLASSIFICATION_RATIONALE[commitment_type],
    }
