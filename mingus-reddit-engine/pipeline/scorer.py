"""Semantic lead scoring via Anthropic API."""

import json
import logging
import os

import anthropic

from storage import db

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are a market research specialist for Mingus, a personal
finance and wellness app for African American professionals
ages 28-45. Mingus solves problems across 7 domains: career
& income, housing, financial habits, mental health & money,
physical wellness, relationships & money, and mental models.

Community: {community_name}
Community focus: {primary_domain}
Community heat score: {heat_score}/10

Score the post on:
- pain_score (1-10): Real, felt problem — not a question or
  opinion, but lived pain?
- readiness_score (1-10): Open to a tool or solution now?

Also identify:
- primary_domain: which of the 7 Mingus domains
- secondary_domain: if any (null if none)
- city_signal: any US city mentioned or implied (null if none)
- lead_magnet_match: which Mingus free assessment fits best:
  'ai_replacement_risk' | 'income_comparison' | 'layoff_risk' |
  'cuffing_season_score' | 'vibe_check' | null

Return ONLY valid JSON — no preamble, no explanation:
{{
  "pain_score": int,
  "readiness_score": int,
  "primary_domain": str,
  "secondary_domain": str or null,
  "city_signal": str or null,
  "lead_magnet_match": str or null,
  "summary": "one sentence",
  "suggested_reply_angle": "one sentence"
}}"""


def _parse_model_json(raw_text: str) -> dict | None:
    cleaned = raw_text.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error("Scorer returned invalid JSON: %s", cleaned[:300])
        return None


def semantic_score(match: dict) -> dict | None:
    """
    Score a keyword match via Anthropic and return a scored lead dict.
    """
    item = match["item"]
    community = db.get_community_by_name(item.get("subreddit", ""))

    community_name = item.get("subreddit", "unknown")
    primary_domain = community.get("primary_domain") if community else "unknown"
    heat_score = community.get("heat_score") if community else 0

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        community_name=community_name,
        primary_domain=primary_domain,
        heat_score=heat_score,
    )
    user_message = f"{item.get('title', '')}\n\n{item.get('body', '')}"

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set — skipping semantic score")
        return None

    model = os.getenv("SCORER_MODEL", "claude-haiku-3")
    composite_threshold = float(os.getenv("COMPOSITE_THRESHOLD", "6.5"))
    hot_lead_threshold = float(os.getenv("HOT_LEAD_THRESHOLD", "9.0"))

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = message.content[0].text
        result = _parse_model_json(raw)
        if not result:
            return None
    except Exception:
        logger.exception("Anthropic API error during semantic scoring")
        return None

    try:
        pain_score = int(result["pain_score"])
        readiness_score = int(result["readiness_score"])
    except (KeyError, TypeError, ValueError):
        logger.error("Scorer response missing valid pain/readiness scores")
        return None

    base = (pain_score * 0.6) + (readiness_score * 0.4)
    composite = base + match["domain_match_boost"] + match["heat_boost"]
    composite = min(round(composite, 2), 10.0)

    if composite < composite_threshold:
        return None

    community_id = community["id"] if community else None

    return {
        "post_id": item.get("post_id"),
        "community_id": community_id,
        "platform": "reddit",
        "author": item.get("author", ""),
        "title": item.get("title", ""),
        "body": item.get("body", ""),
        "url": item.get("url", ""),
        "created_at": item.get("created_at"),
        "domain_id": result.get("primary_domain") or match["domain_id"],
        "matched_keywords": match["matched_keywords"],
        "pain_score": pain_score,
        "readiness_score": readiness_score,
        "composite_score": composite,
        "ai_summary": result.get("summary", ""),
        "suggested_reply_angle": result.get("suggested_reply_angle", ""),
        "city_signal": result.get("city_signal"),
        "lead_magnet_match": result.get("lead_magnet_match"),
        "is_hot_lead": composite >= hot_lead_threshold,
    }
