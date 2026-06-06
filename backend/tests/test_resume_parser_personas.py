"""
Legacy demo-persona resume/recommendation checks (Maya Johnson, Marcus Thompson,
Dr. Jasmine Williams).

These exercise the standalone mock recommender in test_resume_parser_job_recommendations.py
at the repo root — not the production MingusJobRecommendationEngine. Excluded from
default CI via pytest.ini: -m "not legacy_persona".
"""
from __future__ import annotations

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from test_resume_parser_job_recommendations import (  # noqa: E402
    RESUME_DATA,
    generate_job_recommendations,
    parse_resume_basic,
)

pytestmark = pytest.mark.legacy_persona


@pytest.mark.parametrize(
    "persona_key,expected_titles",
    [
        (
            "maya_johnson",
            {"Senior Marketing Coordinator", "Digital Marketing Specialist", "Marketing Manager"},
        ),
        (
            "marcus_thompson",
            {"Senior Software Developer", "Full-Stack Engineer", "Lead Developer"},
        ),
        (
            "dr_jasmine_williams",
            {
                "Deputy Director, Policy & Programs",
                "Senior Vice President, Policy",
                "Executive Director",
            },
        ),
    ],
)
def test_legacy_persona_mock_recommendations(persona_key, expected_titles):
    """Persona-name branches in generate_job_recommendations (lines 466–605)."""
    persona = RESUME_DATA[persona_key]
    parsed = parse_resume_basic(persona["resume_text"])
    recs = generate_job_recommendations(parsed, persona["name"])
    titles = {job["title"] for job in recs["recommended_jobs"]}
    assert titles == expected_titles
    assert recs["persona"] == persona["name"]
