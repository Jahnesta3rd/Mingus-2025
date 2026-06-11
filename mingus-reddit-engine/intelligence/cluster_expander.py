"""Community discovery — find subreddits adjacent to high-heat communities."""

import argparse
import json
import logging
from collections import Counter
from pathlib import Path

from intelligence.heat_map import (
    DOMAIN_FRAGMENTS,
    PRAW_AVAILABLE,
    _get_reddit,
    _normalize_subreddit_name,
    _relevance_bonus,
    add_community,
    compute_heat_score,
    fetch_subreddit_stats,
    get_ranked_communities,
)

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent / "config"
CANDIDATES_PATH = CONFIG_DIR / "expansion_candidates.json"
SUBREDDITS_PATH = CONFIG_DIR / "subreddits.json"

RECOMMENDATIONS_PER_COMMUNITY = 10
CROSSPOST_TOP_LIMIT = 50
CROSSPOST_MIN_COUNT = 3


def _suggest_domain(subreddit_name):
    """Pick the best DOMAIN_FRAGMENTS match for a candidate subreddit."""
    for domain_id in DOMAIN_FRAGMENTS:
        if _relevance_bonus(subreddit_name, domain_id) == 2.0:
            return domain_id
    for domain_id in DOMAIN_FRAGMENTS:
        if _relevance_bonus(subreddit_name, domain_id) == 1.0:
            return domain_id
    return ""


def _existing_community_names():
    from storage.db import get_all_communities

    return {
        _normalize_subreddit_name(community["name"])
        for community in get_all_communities()
    }


def _load_candidates_file():
    if not CANDIDATES_PATH.exists():
        return []
    data = json.loads(CANDIDATES_PATH.read_text())
    if isinstance(data, list):
        return data
    return data.get("candidates", [])


def _save_candidates_file(candidates):
    CANDIDATES_PATH.write_text(
        json.dumps({"candidates": candidates}, indent=2) + "\n"
    )


def _load_review_decisions():
    return {
        _normalize_subreddit_name(candidate["name"]): candidate.get("add_to_system")
        for candidate in _load_candidates_file()
    }


def _discover_recommended(reddit, high_tier_communities, existing_names):
    """Method 1 — Reddit recommended subreddits via PRAW."""
    discovered = {}

    for community in high_tier_communities:
        source_name = community["name"]
        try:
            recommendations = reddit.subreddits.recommended([source_name])[
                :RECOMMENDATIONS_PER_COMMUNITY
            ]
        except Exception:
            logger.exception(
                "Recommended subreddit fetch failed for r/%s",
                source_name,
            )
            continue

        for subreddit in recommendations:
            candidate_name = _normalize_subreddit_name(subreddit.display_name)
            if candidate_name in existing_names or candidate_name in discovered:
                continue
            discovered[candidate_name] = {
                "name": subreddit.display_name,
                "discovery_method": "recommended",
                "found_via": source_name,
            }

    return discovered


def _extract_crosspost_source(reddit, post, source_community_name):
    crosspost_parent = getattr(post, "crosspost_parent", None)
    if not crosspost_parent:
        return None

    try:
        parent_id = str(crosspost_parent)
        if parent_id.startswith("t3_"):
            parent_id = parent_id[3:]
        parent = reddit.submission(id=parent_id)
        candidate_name = _normalize_subreddit_name(parent.subreddit.display_name)
    except Exception:
        logger.debug("Failed to resolve crosspost parent for post %s", post.id)
        return None

    if candidate_name == _normalize_subreddit_name(source_community_name):
        return None

    return candidate_name


def _discover_crosspost(reddit, high_tier_communities, existing_names):
    """Method 2 — cross-post frequency from high-tier communities."""
    counts = Counter()
    found_via = {}

    for community in high_tier_communities:
        source_name = community["name"]
        try:
            subreddit = reddit.subreddit(source_name)
            posts = subreddit.top(time_filter="month", limit=CROSSPOST_TOP_LIMIT)
        except Exception:
            logger.exception(
                "Crosspost discovery failed for r/%s",
                source_name,
            )
            continue

        for post in posts:
            candidate_name = _extract_crosspost_source(reddit, post, source_name)
            if not candidate_name or candidate_name in existing_names:
                continue
            counts[candidate_name] += 1
            found_via.setdefault(candidate_name, set()).add(source_name)

    discovered = {}
    for candidate_name, count in counts.items():
        if count < CROSSPOST_MIN_COUNT:
            continue
        discovered[candidate_name] = {
            "name": candidate_name,
            "discovery_method": "crosspost",
            "found_via": ", ".join(sorted(found_via[candidate_name])),
        }

    return discovered


def _merge_discoveries(recommended, crosspost):
    merged = dict(recommended)
    for name, candidate in crosspost.items():
        if name in merged:
            merged[name]["discovery_method"] = "crosspost"
            merged[name]["found_via"] = (
                f"{merged[name]['found_via']}, {candidate['found_via']}"
            )
        else:
            merged[name] = candidate
    return merged


def _score_candidate(raw_candidate, prior_decisions):
    name = raw_candidate["name"]
    suggested_domain = _suggest_domain(name)
    stats = fetch_subreddit_stats(name)
    heat_score = compute_heat_score(
        {**stats, "name": name},
        suggested_domain or None,
    )
    normalized = _normalize_subreddit_name(name)
    prior = prior_decisions.get(normalized)

    return {
        "name": name,
        "heat_score": heat_score,
        "discovery_method": raw_candidate["discovery_method"],
        "found_via": raw_candidate["found_via"],
        "suggested_domain": suggested_domain,
        "members": int(stats.get("members") or 0),
        "posts_per_day": float(stats.get("posts_per_day") or 0),
        "add_to_system": prior if prior is not None else None,
    }


def _append_to_subreddits(name, primary_domain):
    data = json.loads(SUBREDDITS_PATH.read_text())
    communities = data.setdefault("communities", [])
    normalized = _normalize_subreddit_name(name)
    existing = {
        _normalize_subreddit_name(entry["name"]) for entry in communities
    }
    if normalized in existing:
        return
    communities.append({"name": name, "primary_domain": primary_domain})
    SUBREDDITS_PATH.write_text(json.dumps(data, indent=2) + "\n")


def run_expansion():
    """Discover adjacent communities, score them, and write review JSON."""
    if not PRAW_AVAILABLE:
        logger.warning("PRAW unavailable — cluster expansion skipped")
        return 0

    try:
        reddit = _get_reddit()
    except Exception:
        logger.exception("PRAW unavailable — cluster expansion skipped")
        return 0

    high_tier = get_ranked_communities(min_tier="high")
    if not high_tier:
        logger.info("No high-tier communities found — cluster expansion skipped")
        return 0

    existing_names = _existing_community_names()
    prior_decisions = _load_review_decisions()

    try:
        recommended = _discover_recommended(reddit, high_tier, existing_names)
        crosspost = _discover_crosspost(reddit, high_tier, existing_names)
    except Exception:
        logger.exception("PRAW unavailable — cluster expansion skipped")
        return 0

    merged = _merge_discoveries(recommended, crosspost)
    candidates = [
        _score_candidate(raw_candidate, prior_decisions)
        for raw_candidate in merged.values()
    ]
    candidates.sort(key=lambda c: c["heat_score"], reverse=True)

    _save_candidates_file(candidates)
    logger.info("Cluster expansion found %s candidate(s)", len(candidates))
    return len(candidates)


def review_candidates():
    """CLI review loop for expansion_candidates.json."""
    candidates = _load_candidates_file()
    if not candidates:
        print("No expansion candidates found. Run run_expansion() first.")
        return

    pending = [c for c in candidates if c.get("add_to_system") is None]
    if not pending:
        print("No pending candidates to review.")
        return

    for candidate in pending:
        print()
        print(f"Candidate: r/{candidate['name']}")
        print(f"  heat_score       : {candidate.get('heat_score')}")
        print(f"  discovery_method : {candidate.get('discovery_method')}")
        print(f"  found_via        : {candidate.get('found_via')}")
        print(f"  suggested_domain : {candidate.get('suggested_domain')}")
        print(f"  members          : {candidate.get('members')}")
        print(f"  posts_per_day    : {candidate.get('posts_per_day')}")

        choice = input(
            f"Add [{candidate['name']}] to system? (y/n/skip): "
        ).strip().lower()

        if choice == "y":
            domain = candidate.get("suggested_domain") or "budgeting"
            add_community(candidate["name"], "reddit", domain)
            _append_to_subreddits(candidate["name"], domain)
            candidate["add_to_system"] = True
            print(f"Added r/{candidate['name']} to system.")
        elif choice == "n":
            candidate["add_to_system"] = False
            print(f"Marked r/{candidate['name']} as rejected.")
        else:
            print(f"Skipped r/{candidate['name']}.")

    _save_candidates_file(candidates)


def main():
    parser = argparse.ArgumentParser(description="Mingus cluster expansion")
    parser.add_argument(
        "--review",
        action="store_true",
        help="Review expansion candidates interactively",
    )
    args = parser.parse_args()

    if args.review:
        review_candidates()
    else:
        count = run_expansion()
        print(f"Expansion complete: {count} candidate(s) written.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
