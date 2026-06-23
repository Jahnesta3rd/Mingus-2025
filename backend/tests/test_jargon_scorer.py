"""Unit tests for JargonScorer — no real HTTP calls."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from backend.services.jargon_scorer import JargonScorer


@pytest.fixture
def scorer() -> JargonScorer:
    return JargonScorer()


def _rich_text_bundle(total_chars: int = 500) -> dict:
    filler = "x" * total_chars
    return {
        "careers_text": filler,
        "job_posting_text": "",
        "about_text": "",
        "fetch_errors": [],
        "total_chars": total_chars,
    }


def test_score_employer_cache_hit(scorer: JargonScorer):
    cached_row = MagicMock()
    cached_row.jargon_score = 72
    cached_row.jargon_density_pct = 0.15
    cached_row.top_jargon_phrases = ["synergy"]

    db_session = MagicMock()

    with patch.object(
        scorer,
        "fetch_company_text",
        return_value=_rich_text_bundle(),
    ), patch.object(
        scorer,
        "get_cached_score",
        return_value=cached_row,
    ) as mock_cache, patch.object(
        scorer,
        "score_with_llm",
    ) as mock_llm, patch("backend.services.jargon_scorer.time.sleep"):
        result = scorer.score_employer(
            "Microsoft",
            employer_cik="0000789019",
            db_session=db_session,
        )

    assert result["layer2_score"] == 72
    assert result["from_cache"] is True
    assert result["layer2_status"] == "complete"
    mock_cache.assert_called_once()
    mock_llm.assert_not_called()


def test_score_employer_insufficient_text(scorer: JargonScorer):
    with patch.object(
        scorer,
        "fetch_company_text",
        return_value=_rich_text_bundle(total_chars=50),
    ):
        result = scorer.score_employer("TinyCo")

    assert result["layer2_status"] == "insufficient_text"
    assert result["layer2_score"] is None


def test_score_with_llm_happy_path(scorer: JargonScorer):
    llm_payload = {
        "jargon_density_score": 80,
        "role_clarity_score": 70,
        "values_authenticity_score": 65,
        "leadership_transparency_score": 60,
        "composite_layer2_score": 72,
        "top_jargon_phrases": ["move the needle"],
        "scoring_notes": "Mostly clear with some buzzwords.",
    }
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "content": [{"text": json.dumps(llm_payload)}],
    }

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}), patch(
        "backend.services.jargon_scorer.requests.post",
        return_value=mock_response,
    ) as mock_post:
        result = scorer.score_with_llm(_rich_text_bundle(), "Microsoft")

    assert isinstance(result["composite_layer2_score"], int)
    assert result["composite_layer2_score"] == 72
    assert isinstance(result["top_jargon_phrases"], list)
    mock_post.assert_called_once()


def test_score_with_llm_json_decode_error_retry(scorer: JargonScorer):
    bad_response = MagicMock()
    bad_response.raise_for_status = MagicMock()
    bad_response.json.return_value = {"content": [{"text": "not valid json {{{"}]}

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}), patch(
        "backend.services.jargon_scorer.requests.post",
        return_value=bad_response,
    ) as mock_post:
        result = scorer.score_with_llm(_rich_text_bundle(), "Microsoft")

    assert result["layer2_status"] == "parse_error"
    assert result["layer2_score"] is None
    assert mock_post.call_count == 2


def test_score_with_llm_missing_api_key(scorer: JargonScorer):
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)

    with patch.dict(os.environ, env, clear=True), patch(
        "backend.services.jargon_scorer.requests.post",
    ) as mock_post:
        result = scorer.score_with_llm(_rich_text_bundle(), "Microsoft")

    assert result["layer2_status"] == "unavailable"
    mock_post.assert_not_called()


def test_score_employer_llm_happy_path(scorer: JargonScorer):
    llm_payload = {
        "jargon_density_score": 80,
        "role_clarity_score": 70,
        "values_authenticity_score": 65,
        "leadership_transparency_score": 60,
        "composite_layer2_score": 72,
        "top_jargon_phrases": ["synergy"],
        "scoring_notes": "Clear overall.",
    }

    with patch.object(
        scorer,
        "fetch_company_text",
        return_value=_rich_text_bundle(),
    ), patch.object(
        scorer,
        "get_cached_score",
        return_value=None,
    ), patch.object(
        scorer,
        "score_with_llm",
        return_value=llm_payload,
    ), patch.object(
        scorer,
        "save_to_cache",
    ), patch("backend.services.jargon_scorer.time.sleep"):
        result = scorer.score_employer("Microsoft", db_session=MagicMock())

    assert result["layer2_score"] == 72
    assert isinstance(result["layer2_score"], int)
    assert result["layer2_status"] == "complete"
    assert result["from_cache"] is False


def test_fetch_company_text_does_not_raise_on_network_failure(scorer: JargonScorer):
    with patch.object(
        scorer,
        "_google_search_urls",
        side_effect=Exception("network down"),
    ):
        result = scorer.fetch_company_text("Acme Corp")

    assert result["careers_text"] == ""
    assert result["job_posting_text"] == ""
    assert result["about_text"] == ""
    assert result["fetch_errors"]
    assert result["total_chars"] == 0


def test_save_to_cache_rollback_on_collision(scorer: JargonScorer):
    db_session = MagicMock()
    db_session.commit.side_effect = Exception("unique constraint violated")

    llm_result = {
        "composite_layer2_score": 72,
        "jargon_density_score": 80,
        "top_jargon_phrases": [],
    }
    text_bundle = _rich_text_bundle()

    row = scorer.save_to_cache(
        "Microsoft",
        "0000789019",
        text_bundle,
        llm_result,
        db_session,
    )

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.rollback.assert_called_once()
    assert row is not None
