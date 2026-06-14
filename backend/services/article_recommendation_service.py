#!/usr/bin/env python3
"""Contextual article recommendations via Claude Haiku after checkup events."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import anthropic
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 50

_SYSTEM_PROMPT = (
    "You are a reading advisor for Mingus, a personal finance app "
    "for Black professionals. Select exactly 3 article IDs from the list "
    "below that are most relevant to the user's current situation. "
    "Return ONLY a JSON array of 3 integers — the article IDs. "
    "No preamble, no explanation."
)

_table_ready = False


def _get_db_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def _ensure_table() -> None:
    global _table_ready
    if _table_ready:
        return
    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS article_recommendations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                trigger VARCHAR(50) NOT NULL,
                domain VARCHAR(50) NOT NULL,
                article_ids INTEGER[] NOT NULL,
                context_snapshot JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_article_recs_user_created
            ON article_recommendations(user_id, created_at DESC)
            """
        )
        conn.commit()
        _table_ready = True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _parse_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(tag) for tag in raw]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(tag) for tag in parsed]
        except json.JSONDecodeError:
            pass
    return []


def _article_row_to_dict(row: dict) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "url": row["url"],
        "source": row["source"],
        "domain": row["domain"],
        "tags": _parse_tags(row.get("tags")),
        "read_time_minutes": row["read_time_minutes"],
    }


def _load_candidates(domain: str) -> list[dict]:
    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, title, url, source, domain,
                   COALESCE(summary, description, '') AS summary,
                   tags, read_time_minutes
            FROM articles
            WHERE is_active = TRUE AND domain = %s
            ORDER BY RANDOM()
            LIMIT 20
            """,
            (domain,),
        )
        rows = list(cur.fetchall())

        if len(rows) < 3:
            cur.execute(
                """
                SELECT id, title, url, source, domain,
                       COALESCE(summary, description, '') AS summary,
                       tags, read_time_minutes
                FROM articles
                WHERE is_active = TRUE
                ORDER BY RANDOM()
                LIMIT 20
                """
            )
            rows = list(cur.fetchall())
        return rows
    finally:
        conn.close()


def _build_user_prompt(
    trigger: str, context: dict | None, candidates: list[dict]
) -> str:
    lines = [
        f"Trigger: {trigger}",
        f"User context: {json.dumps(context or {})}",
        "",
        "Available articles:",
    ]
    for row in candidates:
        summary = (row.get("summary") or "")[:150]
        lines.append(f"ID: {row['id']} | Title: {row['title']} | Summary: {summary}")
    lines.append("")
    lines.append("Return the 3 most relevant article IDs as a JSON array.")
    return "\n".join(lines)


def _parse_id_array(raw: str) -> list[int] | None:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text.strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list) or len(data) != 3:
        return None
    ids: list[int] = []
    for item in data:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            return None
        ids.append(int(item))
    return ids


def _call_claude_for_ids(
    trigger: str, context: dict | None, candidates: list[dict]
) -> list[int] | None:
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": _build_user_prompt(trigger, context, candidates),
                }
            ],
        )
        block = response.content[0] if response.content else None
        text = (getattr(block, "text", None) or "").strip()
        if not text:
            return None
        return _parse_id_array(text)
    except Exception as exc:
        logger.warning("article_recommendation anthropic call failed: %s", exc)
        return None


def _select_article_ids(candidates: list[dict], trigger: str, context: dict | None) -> list[int]:
    candidate_ids = [int(row["id"]) for row in candidates]
    fallback = candidate_ids[:3]

    selected = _call_claude_for_ids(trigger, context, candidates)
    if selected is None:
        return fallback

    valid = {cid for cid in candidate_ids}
    filtered = [aid for aid in selected if aid in valid]
    if len(filtered) != 3:
        return fallback
    return filtered


def _fetch_articles_by_ids(article_ids: list[int]) -> list[dict]:
    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, title, url, source, domain, tags, read_time_minutes
            FROM articles
            WHERE id = ANY(%s) AND is_active = TRUE
            """,
            (article_ids,),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    by_id = {row["id"]: _article_row_to_dict(row) for row in rows}
    return [by_id[aid] for aid in article_ids if aid in by_id]


def _store_recommendation(
    user_id: int,
    trigger: str,
    domain: str,
    article_ids: list[int],
    context: dict | None,
) -> None:
    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO article_recommendations
                (user_id, trigger, domain, article_ids, context_snapshot)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                trigger,
                domain,
                article_ids,
                psycopg2.extras.Json(context or {}),
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def generate_contextual_recommendations(
    user_id: int,
    trigger: str,
    domain: str,
    context: dict | None = None,
) -> list[dict]:
    try:
        _ensure_table()
        candidates = _load_candidates(domain)
        if len(candidates) < 3:
            logger.warning(
                "article_recommendation: insufficient candidates for user_id=%s domain=%s",
                user_id,
                domain,
            )
            return []

        selected_ids = _select_article_ids(candidates, trigger, context)
        articles = _fetch_articles_by_ids(selected_ids)
        if len(articles) < 3:
            logger.warning(
                "article_recommendation: could not fetch 3 articles for user_id=%s",
                user_id,
            )
            return []

        _store_recommendation(user_id, trigger, domain, selected_ids, context)
        return articles
    except Exception as exc:
        logger.warning(
            "article_recommendation failed for user_id=%s trigger=%s: %s",
            user_id,
            trigger,
            exc,
        )
        return []


# Create table on first import.
try:
    _ensure_table()
except Exception as exc:
    logger.warning("article_recommendations table setup deferred: %s", exc)
