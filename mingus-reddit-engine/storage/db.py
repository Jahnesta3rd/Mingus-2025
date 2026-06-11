"""PostgreSQL access layer for the Mingus Reddit Engine."""

import os
from pathlib import Path

from psycopg2 import pool
from psycopg2.extras import Json, RealDictCursor

PGHOST = os.environ.get("PGHOST", "")
PGPORT = os.environ.get("PGPORT", "5432")
PGDATABASE = os.environ.get("PGDATABASE", "")
PGUSER = os.environ.get("PGUSER", "")
PGPASSWORD = os.environ.get("PGPASSWORD", "")
PGSSLMODE = os.environ.get("PGSSLMODE", "require")

connection_pool = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=(
        f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/"
        f"{PGDATABASE}?sslmode={PGSSLMODE}"
    ),
)

_TIER_ORDER = {"high": 0, "medium": 1, "low": 2}


def get_connection():
    return connection_pool.getconn()


def release_connection(conn):
    connection_pool.putconn(conn)


def init_db():
    schema_path = Path(__file__).parent / "schema.sql"
    sql = schema_path.read_text()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    finally:
        release_connection(conn)


def insert_community(d):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO communities (
                    platform, name, url, members, posts_per_day,
                    growth_rate_3mo, peak_day, peak_hour_et, heat_score,
                    priority_tier, primary_domain, active
                ) VALUES (
                    %(platform)s, %(name)s, %(url)s, %(members)s,
                    %(posts_per_day)s, %(growth_rate_3mo)s, %(peak_day)s,
                    %(peak_hour_et)s, %(heat_score)s, %(priority_tier)s,
                    %(primary_domain)s, %(active)s
                )
                RETURNING *
                """,
                {
                    "platform": d.get("platform"),
                    "name": d.get("name"),
                    "url": d.get("url"),
                    "members": d.get("members"),
                    "posts_per_day": d.get("posts_per_day"),
                    "growth_rate_3mo": d.get("growth_rate_3mo"),
                    "peak_day": d.get("peak_day"),
                    "peak_hour_et": d.get("peak_hour_et"),
                    "heat_score": d.get("heat_score"),
                    "priority_tier": d.get("priority_tier"),
                    "primary_domain": d.get("primary_domain"),
                    "active": d.get("active", True),
                },
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        release_connection(conn)


def get_all_communities():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM communities
                ORDER BY name
                """
            )
            return cur.fetchall()
    finally:
        release_connection(conn)


def set_community_active(community_id, active):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE communities SET active = %s
                WHERE id = %s
                RETURNING *
                """,
                (active, community_id),
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        release_connection(conn)


def get_community_by_name(name):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM communities
                WHERE LOWER(name) = LOWER(%s)
                LIMIT 1
                """,
                (name,),
            )
            return cur.fetchone()
    finally:
        release_connection(conn)


def get_communities(min_tier=None):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if min_tier is None:
                cur.execute(
                    """
                    SELECT * FROM communities
                    WHERE active = TRUE
                    ORDER BY heat_score DESC NULLS LAST
                    """
                )
            else:
                allowed = [
                    tier
                    for tier, rank in _TIER_ORDER.items()
                    if rank <= _TIER_ORDER.get(min_tier, 2)
                ]
                cur.execute(
                    """
                    SELECT * FROM communities
                    WHERE active = TRUE AND priority_tier = ANY(%s)
                    ORDER BY heat_score DESC NULLS LAST
                    """,
                    (allowed,),
                )
            return cur.fetchall()
    finally:
        release_connection(conn)


def update_community_heat(community_id, stats_dict):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE communities SET
                    members = COALESCE(%(members)s, members),
                    posts_per_day = COALESCE(%(posts_per_day)s, posts_per_day),
                    growth_rate_3mo = COALESCE(%(growth_rate_3mo)s, growth_rate_3mo),
                    peak_day = COALESCE(%(peak_day)s, peak_day),
                    peak_hour_et = COALESCE(%(peak_hour_et)s, peak_hour_et),
                    heat_score = COALESCE(%(heat_score)s, heat_score),
                    priority_tier = COALESCE(%(priority_tier)s, priority_tier),
                    last_heat_check = NOW()
                WHERE id = %(community_id)s
                RETURNING *
                """,
                {
                    "community_id": community_id,
                    "members": stats_dict.get("members"),
                    "posts_per_day": stats_dict.get("posts_per_day"),
                    "growth_rate_3mo": stats_dict.get("growth_rate_3mo"),
                    "peak_day": stats_dict.get("peak_day"),
                    "peak_hour_et": stats_dict.get("peak_hour_et"),
                    "heat_score": stats_dict.get("heat_score"),
                    "priority_tier": stats_dict.get("priority_tier"),
                },
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        release_connection(conn)


def get_lead_by_post_id(post_id):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id FROM leads
                WHERE post_id = %s
                LIMIT 1
                """,
                (post_id,),
            )
            return cur.fetchone()
    finally:
        release_connection(conn)


def insert_lead(d):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO leads (
                    platform, post_id, community_id, author, title, body, url,
                    created_at, domain_id, matched_keywords, pain_score,
                    readiness_score, composite_score, ai_summary,
                    suggested_reply_angle, drafted_reply
                ) VALUES (
                    %(platform)s, %(post_id)s, %(community_id)s, %(author)s,
                    %(title)s, %(body)s, %(url)s, %(created_at)s, %(domain_id)s,
                    %(matched_keywords)s, %(pain_score)s, %(readiness_score)s,
                    %(composite_score)s, %(ai_summary)s,
                    %(suggested_reply_angle)s, %(drafted_reply)s
                )
                ON CONFLICT (post_id) DO NOTHING
                RETURNING *
                """,
                {
                    "platform": d.get("platform"),
                    "post_id": d.get("post_id"),
                    "community_id": d.get("community_id"),
                    "author": d.get("author"),
                    "title": d.get("title"),
                    "body": d.get("body"),
                    "url": d.get("url"),
                    "created_at": d.get("created_at"),
                    "domain_id": d.get("domain_id"),
                    "matched_keywords": Json(d.get("matched_keywords")),
                    "pain_score": d.get("pain_score"),
                    "readiness_score": d.get("readiness_score"),
                    "composite_score": d.get("composite_score"),
                    "ai_summary": d.get("ai_summary"),
                    "suggested_reply_angle": d.get("suggested_reply_angle"),
                    "drafted_reply": d.get("drafted_reply"),
                },
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        release_connection(conn)


def get_unnotified_leads(min_score=6.5):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM leads
                WHERE notified = FALSE AND composite_score >= %s
                ORDER BY composite_score DESC
                """,
                (min_score,),
            )
            return cur.fetchall()
    finally:
        release_connection(conn)


def get_leads_for_brief(lookback_days=14, min_score=6.5):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM leads
                WHERE ingested_at >= NOW() - (%s || ' days')::INTERVAL
                  AND composite_score >= %s
                ORDER BY composite_score DESC
                """,
                (lookback_days, min_score),
            )
            return cur.fetchall()
    finally:
        release_connection(conn)


def mark_notified(lead_ids):
    if not lead_ids:
        return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads SET notified = TRUE
                WHERE id = ANY(%s::uuid[])
                """,
                (lead_ids,),
            )
        conn.commit()
    finally:
        release_connection(conn)


def mark_responded(lead_id, upvotes, got_dm):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE leads SET
                    responded = TRUE,
                    response_upvotes = %s,
                    response_got_dm = %s
                WHERE id = %s
                RETURNING *
                """,
                (upvotes, got_dm, lead_id),
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        release_connection(conn)


def update_quality_rating(lead_id, rating):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE leads SET lead_quality_rating = %s
                WHERE id = %s
                RETURNING *
                """,
                (rating, lead_id),
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        release_connection(conn)


def update_drafted_reply(lead_id, reply_text):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE leads SET drafted_reply = %s
                WHERE id = %s
                RETURNING *
                """,
                (reply_text, lead_id),
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        release_connection(conn)


def insert_ad_brief(d):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO ad_briefs (
                    period_start, period_end, top_communities, top_keywords,
                    top_domains, suggested_copy_angles, geo_targets,
                    budget_allocation, status
                ) VALUES (
                    %(period_start)s, %(period_end)s, %(top_communities)s,
                    %(top_keywords)s, %(top_domains)s, %(suggested_copy_angles)s,
                    %(geo_targets)s, %(budget_allocation)s, %(status)s
                )
                RETURNING *
                """,
                {
                    "period_start": d.get("period_start"),
                    "period_end": d.get("period_end"),
                    "top_communities": Json(d.get("top_communities")),
                    "top_keywords": Json(d.get("top_keywords")),
                    "top_domains": Json(d.get("top_domains")),
                    "suggested_copy_angles": Json(d.get("suggested_copy_angles")),
                    "geo_targets": Json(d.get("geo_targets")),
                    "budget_allocation": Json(d.get("budget_allocation")),
                    "status": d.get("status", "draft"),
                },
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        release_connection(conn)


def get_ad_brief_by_id(brief_id):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM ad_briefs
                WHERE id = %s
                """,
                (brief_id,),
            )
            return cur.fetchone()
    finally:
        release_connection(conn)


def get_latest_ad_brief():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM ad_briefs
                ORDER BY generated_at DESC
                LIMIT 1
                """
            )
            return cur.fetchone()
    finally:
        release_connection(conn)


def mark_brief_ready(brief_id):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE ad_briefs SET status = 'ready'
                WHERE id = %s
                RETURNING *
                """,
                (brief_id,),
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        release_connection(conn)


def insert_ad_performance(d):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO ad_performance (
                    brief_id, campaign_type, targeting_value, impressions,
                    clicks, ctr, assessment_starts, cost_per_lead, date_recorded
                ) VALUES (
                    %(brief_id)s, %(campaign_type)s, %(targeting_value)s,
                    %(impressions)s, %(clicks)s, %(ctr)s,
                    %(assessment_starts)s, %(cost_per_lead)s, %(date_recorded)s
                )
                RETURNING *
                """,
                {
                    "brief_id": d.get("brief_id"),
                    "campaign_type": d.get("campaign_type"),
                    "targeting_value": d.get("targeting_value"),
                    "impressions": d.get("impressions"),
                    "clicks": d.get("clicks"),
                    "ctr": d.get("ctr"),
                    "assessment_starts": d.get("assessment_starts"),
                    "cost_per_lead": d.get("cost_per_lead"),
                    "date_recorded": d.get("date_recorded"),
                },
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        release_connection(conn)


def get_ad_performance(brief_id, lookback_days):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM ad_performance
                WHERE brief_id = %s
                  AND date_recorded >= CURRENT_DATE - (%s || ' days')::INTERVAL
                ORDER BY date_recorded DESC
                """,
                (brief_id, lookback_days),
            )
            return cur.fetchall()
    finally:
        release_connection(conn)


def log_signal_update(domain_id, added, removed, reason, source):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO signal_library_updates (
                    domain_id, keyword_added, keyword_removed, reason, source
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (domain_id, added, removed, reason, source),
            )
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        release_connection(conn)
