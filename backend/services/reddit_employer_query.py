#!/usr/bin/env python3
"""Reddit employer sentiment query via Apify search and Claude analysis (CS3 layer 3)."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

APIFY_ACTOR_URL = (
    "https://api.apify.com/v2/acts/trudax~reddit-scraper-lite/"
    "run-sync-get-dataset-items"
)
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
REQUEST_TIMEOUT = 30
LLM_MODEL = "claude-sonnet-4-6"
LLM_MAX_TOKENS = 600
JSON_RETRY_APPEND = (
    "\n\nIMPORTANT: Return only raw JSON. No backticks, no markdown, no prose."
)

SENTIMENT_SYSTEM_PROMPT = """
You are an employment analyst reviewing Reddit discussions about a company.
You identify patterns in employee and candidate sentiment.
Return ONLY valid JSON. No preamble. No markdown fences. No explanation.
Be factual and neutral — these are observations, not verdicts.
"""


class EmployerQueryRunner:
    """Fetch Reddit posts about an employer via Apify and score sentiment via LLM."""

    def __init__(self, requests_session: requests.Session | None = None) -> None:
        """Injectable session for testability, matching JargonScorer pattern."""
        self.session = requests_session or requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.apify_token = os.environ.get("APIFY_API_TOKEN", "").strip()

    @staticmethod
    def _build_queries(employer_name: str) -> list[str]:
        """Returns 3 search queries for the employer."""
        return [
            f'"{employer_name}"',
            f"working at {employer_name}",
            (
                f"{employer_name} layoffs OR {employer_name} culture OR "
                f"{employer_name} management"
            ),
        ]

    def _fetch_via_apify(self, query: str, max_posts: int = 10) -> list[dict]:
        """
        Calls Apify trudax~reddit-scraper-lite actor synchronously.
        Returns list of normalized post dicts. Never raises — returns [] on any error.
        """
        if not self.apify_token:
            logger.warning(
                "APIFY_API_TOKEN not set — reddit_employer_query will return no posts"
            )
            return []

        payload = {
            "searches": [query],
            "type": "posts",
            "sort": "relevance",
            "maxPostsPerQuery": max_posts,
            "maxComments": 5,
            "maxCommentsDepth": 1,
        }

        try:
            resp = self.session.post(
                APIFY_ACTOR_URL,
                headers={"Authorization": f"Bearer {self.apify_token}"},
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            raw_items = resp.json()
        except Exception as exc:
            logger.warning("Apify fetch failed for query %r: %s", query, exc)
            return []

        if not isinstance(raw_items, list):
            logger.warning(
                "Apify returned unexpected payload type for query %r: %s",
                query,
                type(raw_items).__name__,
            )
            return []

        posts: list[dict] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue

            post_id = (
                item.get("id")
                or item.get("post_id")
                or item.get("dataId")
                or item.get("parsedId")
                or ""
            )
            title = item.get("title", "")
            body = (
                item.get("body")
                or item.get("text")
                or item.get("selftext")
                or ""
            )[:500]
            url = item.get("url") or item.get("postUrl") or item.get("permalink", "")
            sub = (
                item.get("community")
                or item.get("subreddit")
                or item.get("communityName")
                or ""
            )
            score = int(item.get("score") or item.get("upVotes") or 0)
            n_comm = int(
                item.get("numberOfComments") or item.get("num_comments") or 0
            )

            top_comments: list[str] = []
            for comment in (item.get("comments") or [])[:5]:
                if not isinstance(comment, dict):
                    continue
                text = comment.get("body") or comment.get("text") or ""
                if len(text) > 20:
                    top_comments.append(text[:300])

            if not post_id:
                continue

            posts.append(
                {
                    "post_id": str(post_id),
                    "title": title,
                    "body": body,
                    "url": url,
                    "subreddit": str(sub),
                    "score": score,
                    "num_comments": n_comm,
                    "top_comments": top_comments,
                }
            )

        return posts

    def fetch_employer_posts(
        self,
        employer_name: str,
        max_posts_per_query: int = 10,
    ) -> list[dict]:
        """
        Runs all 3 queries via Apify, deduplicates by post_id, caps at 30 total.
        Never raises.
        """
        queries = self._build_queries(employer_name)
        seen_ids: set[str] = set()
        all_posts: list[dict] = []

        for query in queries:
            posts = self._fetch_via_apify(query, max_posts_per_query)
            for post in posts:
                if post["post_id"] not in seen_ids:
                    seen_ids.add(post["post_id"])
                    all_posts.append(post)
            if len(all_posts) >= 30:
                break

        return all_posts[:30]

    def _score_sentiment_with_llm(
        self,
        posts: list[dict],
        employer_name: str,
    ) -> dict[str, Any]:
        """
        Calls Anthropic API. Identical call pattern to jargon_scorer.score_with_llm.
        Never raises.
        """
        prompt_posts = [
            {
                "title": post["title"][:120],
                "body": post["body"][:250],
                "subreddit": post["subreddit"],
                "score": post["score"],
                "top_comment": (
                    post["top_comments"][0][:150] if post["top_comments"] else None
                ),
            }
            for post in posts[:15]
        ]

        user_content = f"""
Company: {employer_name}
Reddit posts found: {len(posts)} total (showing {len(prompt_posts)} below)

{json.dumps(prompt_posts, indent=2)}

Analyze these posts and return this exact JSON:
{{
  "sentiment_band": "<positive|mixed|negative>",
  "confidence": "<high|medium|low>",
  "red_flags": [<up to 3 specific, concrete concerns drawn from the posts. [] if none.>],
  "positive_signals": [<up to 3 specific positive observations. [] if none.>],
  "sentiment_summary": "<one neutral factual sentence summarizing what the posts say about working here>"
}}

Scoring guidance:
- sentiment_band='positive': majority of posts reflect good experiences
- sentiment_band='mixed': meaningful split between positive and negative
- sentiment_band='negative': majority reflect problems or concerns
- confidence='high': 10+ posts with a clear pattern
- confidence='medium': 5–9 posts or mixed signals
- confidence='low': fewer than 5 meaningful posts
- red_flags and positive_signals must be grounded in the actual post text.
  Do not invent signals not present in the data.
"""

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {
                "sentiment_band": None,
                "llm_status": "unavailable",
                "error": "ANTHROPIC_API_KEY not configured",
                "red_flags": [],
                "positive_signals": [],
                "sentiment_summary": None,
            }

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body = {
            "model": LLM_MODEL,
            "max_tokens": LLM_MAX_TOKENS,
            "system": SENTIMENT_SYSTEM_PROMPT.strip(),
            "messages": [{"role": "user", "content": user_content}],
        }

        def _attempt(content: str) -> dict | None:
            body["messages"] = [{"role": "user", "content": content}]
            try:
                resp = requests.post(
                    ANTHROPIC_MESSAGES_URL,
                    headers=headers,
                    json=body,
                    timeout=30,
                )
                resp.raise_for_status()
                raw = resp.json()["content"][0]["text"]
                raw = (
                    raw.strip()
                    .removeprefix("```json")
                    .removeprefix("```")
                    .removesuffix("```")
                    .strip()
                )
                return json.loads(raw)
            except json.JSONDecodeError:
                return None
            except Exception:
                raise

        try:
            parsed = _attempt(user_content)
            if parsed is None:
                parsed = _attempt(user_content + JSON_RETRY_APPEND)
            if parsed is None:
                logger.warning(
                    "reddit_employer_query: LLM returned unparseable JSON for %s",
                    employer_name,
                )
                return {
                    "sentiment_band": None,
                    "llm_status": "parse_error",
                    "red_flags": [],
                    "positive_signals": [],
                    "sentiment_summary": None,
                }
            return parsed
        except Exception as exc:
            logger.warning("reddit_employer_query: Anthropic call failed: %s", exc)
            return {
                "sentiment_band": None,
                "llm_status": "unavailable",
                "error": str(exc),
                "red_flags": [],
                "positive_signals": [],
                "sentiment_summary": None,
            }

    @staticmethod
    def _select_sample_threads(posts: list[dict], n: int = 3) -> list[dict]:
        """Returns up to n highest-scored posts with body length > 50 chars."""
        candidates = [post for post in posts if len(post["body"]) > 50]
        candidates.sort(key=lambda post: post["score"], reverse=True)
        return [
            {
                "title": post["title"],
                "url": post["url"],
                "subreddit": post["subreddit"],
                "score": post["score"],
            }
            for post in candidates[:n]
        ]

    def run_employer_query(self, employer_name: str) -> dict[str, Any]:
        """
        Main entry point. Called by CompanyScreenService (CS4).
        Never raises. Always returns layer3_band, layer3_status, post_count,
        query_timestamp at minimum.
        """
        from datetime import datetime, timezone

        posts = self.fetch_employer_posts(employer_name)
        post_count = len(posts)
        timestamp = datetime.now(timezone.utc).isoformat()

        if post_count < 5:
            return {
                "layer3_band": "insufficient_data",
                "layer3_status": "insufficient_data",
                "confidence": None,
                "red_flags": [],
                "positive_signals": [],
                "sentiment_summary": None,
                "sample_threads": self._select_sample_threads(posts),
                "post_count": post_count,
                "query_timestamp": timestamp,
            }

        llm_result = self._score_sentiment_with_llm(posts, employer_name)

        if llm_result.get("sentiment_band") is None:
            return {
                "layer3_band": "insufficient_data",
                "layer3_status": llm_result.get("llm_status", "unavailable"),
                "confidence": None,
                "red_flags": [],
                "positive_signals": [],
                "sentiment_summary": None,
                "sample_threads": self._select_sample_threads(posts),
                "post_count": post_count,
                "query_timestamp": timestamp,
            }

        return {
            "layer3_band": llm_result["sentiment_band"],
            "layer3_status": "complete",
            "confidence": llm_result.get("confidence"),
            "red_flags": llm_result.get("red_flags", []),
            "positive_signals": llm_result.get("positive_signals", []),
            "sentiment_summary": llm_result.get("sentiment_summary"),
            "sample_threads": self._select_sample_threads(posts),
            "post_count": post_count,
            "query_timestamp": timestamp,
        }
