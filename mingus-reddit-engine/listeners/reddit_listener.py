"""Reddit community listener — fetches posts for pain signal matching."""

import logging
import os
import zoneinfo
from datetime import datetime, timezone

import requests

from storage import db

logger = logging.getLogger(__name__)

APIFY_ACTOR_URL = (
    "https://api.apify.com/v2/acts/trudax~reddit-scraper-lite/"
    "run-sync-get-dataset-items"
)
SCAN_DEPTH_BY_TIER = {
    "high": 50,
    "medium": 25,
    "low": 10,
}
_seen_post_ids: set[str] = set()


def _log_timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _in_peak_window(current_hour, peak_hour_et, window=2):
    diff = abs(current_hour - peak_hour_et)
    diff = min(diff, 24 - diff)
    return diff <= window


def _normalize_post_id(raw_id):
    if not raw_id:
        return ""
    post_id = str(raw_id)
    if post_id.startswith("t3_"):
        return post_id[3:]
    return post_id


def _map_apify_item(raw_item, community_name):
    """Map an Apify dataset item to the standard listener item dict."""
    try:
        created_at = datetime.fromisoformat(
            raw_item["createdAt"].replace("Z", "+00:00")
        )
    except (KeyError, ValueError):
        created_at = datetime.now(timezone.utc)

    return {
        "post_id": _normalize_post_id(
            raw_item.get("id") or raw_item.get("parsedId")
        ),
        "title": raw_item.get("title", ""),
        "body": raw_item.get("body", "") or raw_item.get("text", ""),
        "url": raw_item.get("url", ""),
        "author": raw_item.get("author", "") or raw_item.get("username", ""),
        "created_at": created_at,
        "subreddit": community_name,
    }


def _log_community_scan(community_name, tier, post_count, peak_scan):
    logger.info(
        "[%s] community: %s | tier: %s | posts: %s | peak scan: %s",
        _log_timestamp(),
        community_name,
        tier,
        post_count,
        peak_scan,
    )


def fetch_community_content(community_row):
    """
    Fetch recent posts from a Reddit community via Apify.

    Returns a list of item dicts:
      post_id, title, body, url, author, created_at, subreddit
    """
    community_name = community_row["name"]
    tier = community_row.get("priority_tier") or "low"
    scan_depth = SCAN_DEPTH_BY_TIER.get(tier, 10)

    peak_hour_et = community_row.get("peak_hour_et")
    peak_scan = "no"
    if peak_hour_et is not None:
        et_now = datetime.now(zoneinfo.ZoneInfo("America/New_York"))
        current_hour = et_now.hour
        if _in_peak_window(current_hour, peak_hour_et):
            scan_depth *= 2
            peak_scan = "yes"

    items = []
    token = os.environ.get("APIFY_API_TOKEN", "").strip()
    if not token:
        logger.error(
            "APIFY_API_TOKEN not set — skipping r/%s",
            community_name,
        )
        _log_community_scan(community_name, tier, 0, peak_scan)
        return []

    payload = {
        "startUrls": [
            {"url": f"https://www.reddit.com/r/{community_name}/new/"}
        ],
        "maxItems": scan_depth,
        "type": "posts",
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            APIFY_ACTOR_URL,
            json=payload,
            headers=headers,
            timeout=300,
        )
    except requests.RequestException:
        logger.exception(
            "Apify request failed for r/%s",
            community_name,
        )
        _log_community_scan(community_name, tier, 0, peak_scan)
        return []

    if not response.ok:
        logger.error(
            "Apify returned %s for r/%s: %s",
            response.status_code,
            community_name,
            response.text[:500],
        )
        _log_community_scan(community_name, tier, 0, peak_scan)
        return []

    try:
        dataset = response.json()
    except ValueError:
        logger.error(
            "Apify returned non-JSON response for r/%s",
            community_name,
        )
        _log_community_scan(community_name, tier, 0, peak_scan)
        return []

    if not isinstance(dataset, list):
        logger.error(
            "Apify returned unexpected payload type for r/%s: %s",
            community_name,
            type(dataset).__name__,
        )
        _log_community_scan(community_name, tier, 0, peak_scan)
        return []

    if not dataset:
        logger.warning(
            "Apify returned empty dataset for r/%s",
            community_name,
        )
        _log_community_scan(community_name, tier, 0, peak_scan)
        return []

    for raw_item in dataset:
        if not isinstance(raw_item, dict):
            continue
        # Skip items that are not real posts
        if not raw_item.get("parsedId") or not raw_item.get("title", "").strip():
            continue
        item = _map_apify_item(raw_item, community_name)
        post_id = item["post_id"]
        if not post_id:
            continue
        if post_id in _seen_post_ids:
            continue
        if db.get_lead_by_post_id(post_id):
            continue
        _seen_post_ids.add(post_id)
        items.append(item)

    _log_community_scan(community_name, tier, len(items), peak_scan)

    if not items:
        logger.warning(
            "Apify returned no usable posts for r/%s",
            community_name,
        )

    return items


def run_listener() -> dict:
    """Fetch and deduplicate posts from all ranked communities."""
    from intelligence.heat_map import get_ranked_communities

    communities = get_ranked_communities()
    all_items = []
    new_items = 0

    for community in communities:
        items = fetch_community_content(community)
        for item in items:
            all_items.append(item)
            new_items += 1

    timestamp = _log_timestamp()
    logger.info(
        "[%s] RUN COMPLETE | communities: %s | "
        "items fetched: %s | new items: %s",
        timestamp,
        len(communities),
        len(all_items),
        new_items,
    )

    return {
        "communities_scanned": len(communities),
        "total_items": len(all_items),
        "new_items": new_items,
        "items": all_items,
    }


# PRAW VERSION — restore when Reddit API approved
#
# import praw
#
#
# def _get_reddit():
#     return praw.Reddit(
#         client_id=os.environ["REDDIT_CLIENT_ID"],
#         client_secret=os.environ["REDDIT_CLIENT_SECRET"],
#         user_agent=os.environ.get("REDDIT_USER_AGENT", "mingus-listener/1.0"),
#     )
#
#
# def fetch_community_content(community_row):
#     """Fetch recent posts from a Reddit community via PRAW."""
#     subreddit_name = community_row["name"]
#     reddit = _get_reddit()
#     subreddit = reddit.subreddit(subreddit_name)
#     items = []
#
#     for post in subreddit.new(limit=SCAN_DEPTH):
#         author = str(post.author) if post.author else "[deleted]"
#         items.append(
#             {
#                 "post_id": post.id,
#                 "title": post.title or "",
#                 "body": post.selftext or "",
#                 "url": f"https://www.reddit.com{post.permalink}",
#                 "author": author,
#                 "created_at": datetime.fromtimestamp(
#                     post.created_utc,
#                     tz=timezone.utc,
#                 ),
#                 "subreddit": subreddit_name,
#             }
#         )
#
#     return items
