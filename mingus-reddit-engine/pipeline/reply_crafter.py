"""Draft authentic community replies for qualified leads via Anthropic API."""

import logging
import os

import anthropic

from storage import db

logger = logging.getLogger(__name__)

COMMUNITY_TONE = {
    "blackpersonalfinance": "direct, peer tone, culturally aware",
    "povertyfinance": "direct, no-fluff, peer tone",
    "personalfinance": "practical, evidence-backed",
    "financialindependence": "analytical, goal-oriented",
    "blackladies": "warm, validating, sisterhood tone",
    "blackmentalhealth": "warm, non-clinical, validating",
    "mentalhealth": "warm, non-clinical, validating",
    "careerguidance": "practical, evidence-backed",
    "cscareerquestions": "practical, data-driven",
    "antiwork": "empathetic, anti-corporate, peer tone",
    "selfimprovement": "aspirational, framework-oriented",
    "firsttimehomebuyer": "encouraging, step-by-step",
    "realestate": "analytical, market-aware",
    "relationships": "warm, non-judgmental",
    "dating_advice": "warm, non-judgmental",
    "studentloans": "practical, empathetic",
    "creditcards": "practical, direct",
}

BRIDGE_LANGUAGE = {
    "income_comparison": (
        "The market rate for your role is probably higher than "
        "you expect — do you know what percentile you're at?"
    ),
    "layoff_risk": (
        "There's a way to calculate your specific exposure based "
        "on your role and industry — want me to walk you through it?"
    ),
    "ai_replacement_risk": (
        "Your actual risk depends on which parts of your role are "
        "judgment-based vs repeatable — have you mapped that out?"
    ),
    "cuffing_season_score": (
        "Financial compatibility is one of the most underrated "
        "relationship factors — what does that look like for you?"
    ),
    "vibe_check": (
        "The stress-to-spending connection is real and measurable "
        "— are you tracking how your emotional state affects your "
        "financial decisions?"
    ),
}

_SYSTEM_PROMPT_TEMPLATE = """You are a community engagement specialist helping the founder
of Mingus respond authentically to people in online communities.

Community: {community_name}
Community tone: {community_tone}
Post domain: {domain_id}
Lead magnet match: {lead_magnet_match}
City signal: {city_signal}
Link safe: false
Suggested reply angle: {suggested_reply_angle}
Bridge language: {bridge_language}

Write a single reply that sounds like a knowledgeable friend
who has been in this community for months. Not a marketer.
Not a coach. A peer who happens to know more about this topic.

Rules:
- 3-6 sentences total
- Open with acknowledgment of their specific situation
- One concrete insight, not a list
- End with one question
- No product names, no links
- If city_signal is present, reference local context naturally
- If bridge_language is provided, weave it in naturally toward
  the end — never force it, never make it sound like an ad

Return only the reply text. No preamble. No explanation."""


def draft_reply(lead: dict) -> str | None:
    """Generate a community reply draft for a scored lead."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set — skipping reply draft")
        return None

    community_name = (lead.get("subreddit") or "").lower()
    community_tone = COMMUNITY_TONE.get(community_name, "genuine, peer tone")

    lead_magnet_match = lead.get("lead_magnet_match") or "null"
    bridge_language = BRIDGE_LANGUAGE.get(lead.get("lead_magnet_match") or "", "none")

    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        community_name=community_name,
        community_tone=community_tone,
        domain_id=lead.get("domain_id", ""),
        lead_magnet_match=lead_magnet_match,
        city_signal=lead.get("city_signal") or "none",
        suggested_reply_angle=lead.get("suggested_reply_angle", ""),
        bridge_language=bridge_language,
    )

    user_message = f"{lead.get('title', '')}\n\n{lead.get('body', '')}"
    model = os.getenv("SCORER_MODEL", "claude-haiku-3")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return message.content[0].text.strip()
    except Exception:
        logger.exception("Anthropic API error during reply drafting")
        return None


def save_draft(lead_id: str | None, reply_text: str) -> None:
    """Persist reply draft to the leads table."""
    if not lead_id:
        return
    db.update_drafted_reply(lead_id, reply_text)
    logger.info("Draft saved for lead %s", lead_id)


def process_lead(lead: dict) -> str | None:
    """Draft and save a reply for a scored lead."""
    reply_text = draft_reply(lead)
    if reply_text:
        save_draft(lead.get("id"), reply_text)
    return reply_text
