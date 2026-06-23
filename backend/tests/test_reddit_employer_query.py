"""Unit tests for EmployerQueryRunner — no real HTTP or Apify calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from backend.services.reddit_employer_query import EmployerQueryRunner


@pytest.fixture
def runner() -> EmployerQueryRunner:
    return EmployerQueryRunner()


def _post(
    post_id: str,
    *,
    body: str | None = None,
    score: int = 10,
) -> dict:
    return {
        "post_id": post_id,
        "title": f"Title {post_id}",
        "body": body or ("x" * 60),
        "url": f"https://reddit.com/r/jobs/comments/{post_id}",
        "subreddit": "jobs",
        "score": score,
        "num_comments": 2,
        "top_comments": [],
    }


def test_run_employer_query_insufficient_posts(runner: EmployerQueryRunner):
    posts = [_post("1"), _post("2"), _post("3")]

    with patch.object(
        runner,
        "fetch_employer_posts",
        return_value=posts,
    ), patch.object(
        runner,
        "_score_sentiment_with_llm",
    ) as mock_llm:
        result = runner.run_employer_query("Acme Corp")

    assert result["layer3_band"] == "insufficient_data"
    assert result["layer3_status"] == "insufficient_data"
    assert mock_llm.call_count == 0


def test_run_employer_query_llm_unavailable(runner: EmployerQueryRunner):
    posts = [_post(str(i)) for i in range(10)]

    with patch.object(
        runner,
        "fetch_employer_posts",
        return_value=posts,
    ), patch.object(
        runner,
        "_score_sentiment_with_llm",
        return_value={"sentiment_band": None, "llm_status": "unavailable"},
    ):
        result = runner.run_employer_query("Acme Corp")

    assert result["layer3_band"] == "insufficient_data"
    assert result["layer3_status"] == "unavailable"
    assert result["post_count"] == 10


def test_run_employer_query_happy_path(runner: EmployerQueryRunner):
    posts = [_post(str(i), score=100 - i) for i in range(12)]

    with patch.object(
        runner,
        "fetch_employer_posts",
        return_value=posts,
    ), patch.object(
        runner,
        "_score_sentiment_with_llm",
        return_value={
            "sentiment_band": "mixed",
            "confidence": "medium",
            "red_flags": ["High turnover reported"],
            "positive_signals": ["Pay is competitive"],
            "sentiment_summary": (
                "Mixed reviews: pay praised, turnover frequently mentioned."
            ),
        },
    ):
        result = runner.run_employer_query("Acme Corp")

    assert result["layer3_band"] == "mixed"
    assert result["layer3_status"] == "complete"
    assert result["post_count"] == 12
    assert isinstance(result["sample_threads"], list)
    assert len(result["sample_threads"]) <= 3
    assert result["red_flags"] == ["High turnover reported"]


def test_fetch_employer_posts_deduplication(runner: EmployerQueryRunner):
    duplicate = _post("abc123")
    other = _post("def456")

    with patch.object(
        runner,
        "_fetch_via_apify",
        side_effect=[[duplicate], [duplicate, other], []],
    ):
        result = runner.fetch_employer_posts("Acme Corp")

    post_ids = [post["post_id"] for post in result]
    assert post_ids.count("abc123") == 1
    assert len(result) == len(set(post_ids))
    assert len(result) == 2


def test_fetch_via_apify_connection_error(runner: EmployerQueryRunner):
    runner.apify_token = "test-token"
    runner.session.post = MagicMock(
        side_effect=requests.exceptions.ConnectionError("network down")
    )

    result = runner._fetch_via_apify('"Acme Corp"')

    assert result == []


def test_score_sentiment_with_llm_json_decode_retry(runner: EmployerQueryRunner):
    bad_response = MagicMock()
    bad_response.raise_for_status = MagicMock()
    bad_response.json.return_value = {
        "content": [{"text": "not valid json {{{{"}],
    }

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}), patch(
        "backend.services.reddit_employer_query.requests.post",
        return_value=bad_response,
    ) as mock_post:
        result = runner._score_sentiment_with_llm(
            [_post("1") for _ in range(6)],
            "Acme Corp",
        )

    assert mock_post.call_count == 2
    assert result["sentiment_band"] is None
    assert result["llm_status"] == "parse_error"
