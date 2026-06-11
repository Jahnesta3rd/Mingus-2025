"""Keyword matching against Mingus domain signal libraries."""

import json
import logging
from pathlib import Path

from storage import db

logger = logging.getLogger(__name__)

DOMAIN_PRIORITY = [
    "career_income",
    "financial_habits",
    "housing",
    "mental_health_money",
    "relationships_money",
    "wellness_correlation",
    "mental_models",
]

PRIMARY_DOMAIN_TO_SIGNAL_DOMAIN = {
    "work_life": "career_income",
    "budgeting": "financial_habits",
    "debt": "financial_habits",
    "housing": "housing",
    "mood": "mental_health_money",
    "relationships": "relationships_money",
    "body": "wellness_correlation",
    "family": "relationships_money",
    "vehicle": "financial_habits",
}

_PRIORITY_RANK = {domain_id: idx for idx, domain_id in enumerate(DOMAIN_PRIORITY)}

_SIGNALS_PATH = Path(__file__).parent.parent / "config" / "domain_signals.json"
with _SIGNALS_PATH.open() as _signals_file:
    _SIGNAL_DATA = json.load(_signals_file)

DOMAIN_SIGNALS = _SIGNAL_DATA.get("domains", [])


def _pick_best_domain(domain_hits):
    """Choose domain with most hits; break ties via DOMAIN_PRIORITY."""
    max_hits = max(len(keywords) for keywords in domain_hits.values())
    candidates = [
        domain_id
        for domain_id, keywords in domain_hits.items()
        if len(keywords) == max_hits
    ]
    return min(candidates, key=lambda domain_id: _PRIORITY_RANK[domain_id])


def keyword_match(item: dict) -> dict | None:
    """
    Match listener item text against domain keyword libraries.

    Returns a match dict or None if no keywords hit.
    """
    title = item.get("title") or ""
    body = item.get("body") or ""
    combined_text = f"{title} {body}".lower()

    domain_hits = {}
    for domain in DOMAIN_SIGNALS:
        domain_id = domain["domain_id"]
        matched = []
        for keyword in domain.get("keywords", []):
            if keyword.lower() in combined_text:
                matched.append(keyword)
        if matched:
            domain_hits[domain_id] = matched

    if not domain_hits:
        return None

    best_domain = _pick_best_domain(domain_hits)
    matched_keywords = domain_hits[best_domain]

    community = db.get_community_by_name(item.get("subreddit", ""))
    primary_domain = community.get("primary_domain") if community else None
    heat_score = float(community.get("heat_score") or 0) if community else 0.0

    mapped_primary = PRIMARY_DOMAIN_TO_SIGNAL_DOMAIN.get(primary_domain)
    domain_match_boost = 0.5 if mapped_primary == best_domain else 0.0
    heat_boost = 0.3 if heat_score >= 8.0 else 0.0

    return {
        "item": item,
        "domain_id": best_domain,
        "matched_keywords": matched_keywords,
        "domain_match_boost": domain_match_boost,
        "heat_boost": heat_boost,
    }
