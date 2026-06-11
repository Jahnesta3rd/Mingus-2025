"""Peak posting hour analysis for Reddit communities."""

import logging
from collections import Counter
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from intelligence.heat_map import PRAW_AVAILABLE, _get_reddit
from storage.db import get_community_by_name, update_community_heat

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")

_SKIPPED_RESULT = {
    "peak_hours": [],
    "peak_day": None,
    "hour_frequency": {},
}


def analyze_peak_hours(subreddit_name):
    """
    Analyze the last 100 posts for peak posting hours (ET) and day of week.

    Returns top 3 peak hours, peak day, and hour frequency dict.
    Updates the communities row with peak_day and peak_hour_et.
    """
    if not PRAW_AVAILABLE:
        logger.warning("Peak hours analysis skipped — PRAW unavailable")
        return dict(_SKIPPED_RESULT)

    try:
        reddit = _get_reddit()
        subreddit = reddit.subreddit(subreddit_name)
        posts = list(subreddit.new(limit=100))

        hour_counts = Counter()
        day_counts = Counter()

        for post in posts:
            dt_et = datetime.fromtimestamp(
                post.created_utc, tz=timezone.utc
            ).astimezone(ET)
            hour_counts[dt_et.hour] += 1
            day_counts[dt_et.strftime("%A")] += 1

        top_hours = [hour for hour, _ in hour_counts.most_common(3)]
        peak_day = day_counts.most_common(1)[0][0] if day_counts else None
        peak_hour_et = top_hours[0] if top_hours else None

        community = get_community_by_name(subreddit_name)
        if community:
            update_community_heat(
                community["id"],
                {
                    "peak_day": peak_day,
                    "peak_hour_et": peak_hour_et,
                },
            )
        else:
            logger.warning("No community row found for r/%s", subreddit_name)

        return {
            "peak_hours": top_hours,
            "peak_day": peak_day,
            "hour_frequency": dict(sorted(hour_counts.items())),
        }
    except Exception:
        logger.exception(
            "Peak hours analysis failed for r/%s — skipping DB update",
            subreddit_name,
        )
        return dict(_SKIPPED_RESULT)
