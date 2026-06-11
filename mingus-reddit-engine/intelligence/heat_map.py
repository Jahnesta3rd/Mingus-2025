"""Heat map intelligence — discover, score, and rank Reddit communities for Mingus."""

import json
import logging
import os
from pathlib import Path

# PRAW VERSION — restore when Reddit API approved
try:
    import praw

    PRAW_INSTALLED = True
except ImportError:
    praw = None  # type: ignore[assignment,misc]
    PRAW_INSTALLED = False

PRAW_AVAILABLE = (
    PRAW_INSTALLED
    and bool(os.getenv("REDDIT_CLIENT_ID"))
    and bool(os.getenv("REDDIT_CLIENT_SECRET"))
)

from storage.db import (
    get_all_communities,
    get_communities,
    insert_community,
    set_community_active,
    update_community_heat,
)

logger = logging.getLogger(__name__)

DOMAIN_FRAGMENTS = {
    "budgeting": {
        "primary": [
            "personalfinance",
            "povertyfinance",
            "frugal",
            "financialindependence",
        ],
        "secondary": ["leanfire", "fire", "money", "economics"],
    },
    "debt": {
        "primary": ["creditcards", "studentloans", "debtfree", "loans"],
        "secondary": ["personalfinance", "povertyfinance", "bankruptcy"],
    },
    "housing": {
        "primary": [
            "renters",
            "firsttimehomebuyer",
            "landlord",
            "housing",
            "homeowners",
        ],
        "secondary": ["realestate", "personalfinance", "povertyfinance"],
    },
    "vehicle": {
        "primary": [
            "whatcarshouldibuy",
            "cars",
            "cartalk",
            "askcarsales",
            "mechanicadvice",
        ],
        "secondary": ["personalfinance", "povertyfinance"],
    },
    "work_life": {
        "primary": ["jobs", "careerguidance", "unemployment", "work"],
        "secondary": ["antiwork", "cscareerquestions", "personalfinance"],
    },
    "relationships": {
        "primary": ["relationships", "marriage", "dating", "datingoverthirty"],
        "secondary": ["personalfinance", "povertyfinance", "wedding"],
    },
    "family": {
        "primary": ["parenting", "daddit", "mommit", "beyondthebump"],
        "secondary": ["personalfinance", "povertyfinance", "relationships"],
    },
    "mood": {
        "primary": [
            "mentalhealth",
            "blackmentalhealth",
            "blackladies",
            "anxiety",
            "decidingtobebetter",
            "offmychest",
        ],
        "secondary": ["personalfinance", "povertyfinance", "selfimprovement"],
    },
    "body": {
        "primary": ["loseit", "fitness", "healthinsurance", "health"],
        "secondary": ["personalfinance", "povertyfinance"],
    },
}

def _get_reddit():
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ.get("REDDIT_USER_AGENT", "mingus-listener/1.0"),
    )


def _normalize_subreddit_name(name):
    return name.lower().removeprefix("r/").strip()


def _relevance_bonus(subreddit_name, primary_domain):
    """Return 2.0 (primary), 1.0 (secondary), or 0.0 (no match)."""
    name = _normalize_subreddit_name(subreddit_name)

    if primary_domain and primary_domain in DOMAIN_FRAGMENTS:
        fragments = DOMAIN_FRAGMENTS[primary_domain]
        for fragment in fragments.get("primary", []):
            if name == fragment.lower() or fragment.lower() in name:
                return 2.0
        for fragment in fragments.get("secondary", []):
            if name == fragment.lower() or fragment.lower() in name:
                return 1.0

    for domain_id, fragments in DOMAIN_FRAGMENTS.items():
        if domain_id == primary_domain:
            continue
        for fragment in fragments.get("primary", []):
            if name == fragment.lower() or fragment.lower() in name:
                return 1.0

    return 0.0


def _priority_tier(heat_score):
    if heat_score >= 7.5:
        return "high"
    if heat_score >= 5.0:
        return "medium"
    return "low"


_ZEROED_STATS = {"members": 0, "posts_per_day": 0, "growth_rate_3mo": 0}


def fetch_subreddit_stats(subreddit_name):
    """Fetch community activity stats via PRAW."""
    if not PRAW_AVAILABLE:
        logger.warning(
            "PRAW unavailable — returning zeroed stats for r/%s",
            subreddit_name,
        )
        return dict(_ZEROED_STATS)

    try:
        reddit = _get_reddit()
        subreddit = reddit.subreddit(subreddit_name)

        members = subreddit.subscribers or 0
        accounts_active = subreddit.accounts_active or 0

        posts = list(subreddit.new(limit=100))
        if len(posts) >= 2:
            timestamps = [post.created_utc for post in posts]
            span_days = (max(timestamps) - min(timestamps)) / 86400.0
            posts_per_day = len(posts) / max(span_days, 1.0)
        elif len(posts) == 1:
            posts_per_day = 1.0
        else:
            posts_per_day = 0.0

        growth_rate_3mo = float(accounts_active)

        return {
            "members": members,
            "posts_per_day": round(posts_per_day, 2),
            "growth_rate_3mo": growth_rate_3mo,
        }
    except Exception:
        logger.exception(
            "PRAW stats fetch failed for r/%s — returning zeroed stats",
            subreddit_name,
        )
        return dict(_ZEROED_STATS)


def compute_heat_score(stats_dict, primary_domain):
    """Compute heat score (0–10) from activity, growth, scale, and relevance."""
    posts_per_day = stats_dict.get("posts_per_day") or 0.0
    growth_rate_3mo = stats_dict.get("growth_rate_3mo") or 0.0
    members = min(stats_dict.get("members") or 0, 500_000)
    subreddit_name = stats_dict.get("name", "")

    activity = min((posts_per_day / 50.0) * 3.5, 3.5)
    growth = min((growth_rate_3mo / 20.0) * 2.5, 2.5)
    scale = min((members / 500_000.0) * 2.0, 2.0)
    relevance_bonus = _relevance_bonus(subreddit_name, primary_domain)

    score = activity + growth + scale + (relevance_bonus * 2.0)
    return round(max(0.0, min(10.0, score)), 2)


def run_heat_check():
    """Refresh stats and heat scores for all active communities."""
    communities = get_communities()
    updated = []

    for community in communities:
        name = community["name"]
        try:
            stats = fetch_subreddit_stats(name)
            heat_score = compute_heat_score(
                {**stats, "name": name},
                community.get("primary_domain"),
            )
            row = update_community_heat(
                community["id"],
                {
                    **stats,
                    "heat_score": heat_score,
                    "priority_tier": _priority_tier(heat_score),
                },
            )
            updated.append(row)
            logger.info(
                "Heat check: r/%s score=%.2f tier=%s",
                name,
                heat_score,
                _priority_tier(heat_score),
            )
        except Exception:
            logger.exception("Heat check failed for r/%s", name)

    return updated


def get_ranked_communities(min_tier=None):
    """Return active communities at or above min_tier, sorted by heat_score DESC."""
    if min_tier is None:
        min_tier = "low" if not PRAW_AVAILABLE else "medium"
    communities = get_communities(min_tier=min_tier)
    return sorted(
        communities,
        key=lambda c: (c.get("heat_score") or 0),
        reverse=True,
    )


def add_community(name, platform, primary_domain):
    """Insert a community and immediately fetch its stats and heat score."""
    normalized = _normalize_subreddit_name(name)
    row = insert_community(
        {
            "platform": platform,
            "name": normalized,
            "url": f"https://reddit.com/r/{normalized}",
            "primary_domain": primary_domain,
            "active": True,
        }
    )

    stats = fetch_subreddit_stats(normalized)
    heat_score = compute_heat_score(
        {**stats, "name": normalized},
        primary_domain,
    )
    return update_community_heat(
        row["id"],
        {
            **stats,
            "heat_score": heat_score,
            "priority_tier": _priority_tier(heat_score),
        },
    )


def seed_communities():
    """Load seed communities from config/subreddits.json.

    Adds new communities, reactivates previously deactivated seed entries,
    and sets active=false for DB communities no longer in the JSON.
    """
    config_path = Path(__file__).parent.parent / "config" / "subreddits.json"
    data = json.loads(config_path.read_text())
    incoming = {
        _normalize_subreddit_name(entry["name"]): entry
        for entry in data.get("communities", [])
    }

    all_communities = get_all_communities()
    by_name = {
        _normalize_subreddit_name(community["name"]): community
        for community in all_communities
    }

    deactivated = []
    for community in all_communities:
        name = _normalize_subreddit_name(community["name"])
        if name not in incoming and community.get("active"):
            row = set_community_active(community["id"], False)
            deactivated.append(row)
            logger.info("Deactivated r/%s (removed from seed list)", name)

    seeded = []
    for name, entry in incoming.items():
        if name in by_name:
            if not by_name[name].get("active"):
                set_community_active(by_name[name]["id"], True)
                logger.info("Reactivated r/%s", name)
            continue
        row = add_community(name, "reddit", entry["primary_domain"])
        seeded.append(row)
        logger.info("Seeded r/%s", name)

    return {"seeded": seeded, "deactivated": deactivated}
