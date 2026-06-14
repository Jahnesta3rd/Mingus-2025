#!/usr/bin/env python3
"""Article library API: browse, search, domain filters, recommendations, bookmarks."""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime

import psycopg2
import psycopg2.extras
from flask import Blueprint, jsonify, request
from sqlalchemy import desc

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.models.housing_profile import HousingProfile
from backend.models.life_ledger import LifeLedgerModuleAnswer, LifeLedgerProfile

logger = logging.getLogger(__name__)

articles_bp = Blueprint("articles", __name__, url_prefix="/api/articles")

DOMAIN_LABELS: dict[str, str] = {
    "career_income": "Career & Income",
    "housing": "Housing",
    "financial_habits": "Financial Habits",
    "mental_health_money": "Mental Health & Money",
    "physical_wellness": "Physical Wellness",
    "relationships_money": "Relationships & Money",
    "mental_models": "Free Game",
}

_MODULE_TO_DOMAIN: dict[str, str] = {
    "body": "physical_wellness",
    "roof": "housing",
    "vehicle": "career_income",
    "vibe": "mental_health_money",
}

_CHECKUP_FIELD_DOMAINS: tuple[tuple[str, str], ...] = (
    ("body_energy_rating", "physical_wellness"),
    ("housing_stability_rating", "housing"),
    ("mood_stress_triggered_purchase", "mental_health_money"),
    ("spending_intentionality_rating", "financial_habits"),
    ("relationship_friction_type", "relationships_money"),
    ("practice_had_moments", "mental_health_money"),
    ("vehicle_satisfaction_rating", "career_income"),
)

_bookmarks_table_ready = False


def _get_db_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def _ensure_bookmarks_table() -> None:
    global _bookmarks_table_ready
    if _bookmarks_table_ready:
        return
    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS article_bookmarks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE(user_id, article_id)
            )
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_article_bookmarks_user_id
            ON article_bookmarks(user_id)
            """
        )
        conn.commit()
        _bookmarks_table_ready = True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _parse_tags(raw) -> list[str]:
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


def _row_to_article(row: dict) -> dict:
    return {
        "id": row["id"],
        "url": row["url"],
        "title": row["title"],
        "description": row["description"],
        "source": row["source"],
        "domain": row["domain"],
        "tags": _parse_tags(row.get("tags")),
        "read_time_minutes": row["read_time_minutes"],
    }


def _resolve_user_mingus_domain(user_id: int) -> str:
    """Pick article domain from the user's most recent checkup activity."""
    candidates: list[tuple[datetime, str]] = []

    module_row = (
        LifeLedgerModuleAnswer.query.filter_by(user_id=user_id)
        .order_by(desc(LifeLedgerModuleAnswer.completed_at))
        .first()
    )
    if module_row and module_row.module in _MODULE_TO_DOMAIN:
        candidates.append(
            (module_row.completed_at, _MODULE_TO_DOMAIN[module_row.module])
        )

    housing = HousingProfile.query.get(user_id)
    if housing is not None:
        candidates.append((housing.updated_at, "housing"))

    profile = LifeLedgerProfile.query.filter_by(user_id=user_id).first()
    if profile is not None:
        for field, domain in _CHECKUP_FIELD_DOMAINS:
            if getattr(profile, field, None) is not None:
                candidates.append((profile.updated_at, domain))

    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]
    return "career_income"


@articles_bp.route("", methods=["GET"])
@articles_bp.route("/", methods=["GET"])
def list_articles():
    domain = (request.args.get("domain") or "").strip() or None
    query_text = (request.args.get("q") or "").strip() or None

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1

    try:
        per_page = int(request.args.get("per_page", 20))
    except (TypeError, ValueError):
        per_page = 20
    per_page = max(1, min(per_page, 50))

    offset = (page - 1) * per_page
    conditions = ["is_active = TRUE"]
    params: list = []

    if domain:
        conditions.append("domain = %s")
        params.append(domain)

    where_clause = " AND ".join(conditions)

    conn = _get_db_connection()
    try:
        cur = conn.cursor()

        if query_text:
            count_sql = f"""
                SELECT COUNT(*) AS total
                FROM articles
                WHERE {where_clause}
                  AND search_vector @@ plainto_tsquery('english', %s)
            """
            cur.execute(count_sql, params + [query_text])
            total = int(cur.fetchone()["total"])

            list_sql = f"""
                SELECT id, url, title, description, source, domain, tags, read_time_minutes
                FROM articles
                WHERE {where_clause}
                  AND search_vector @@ plainto_tsquery('english', %s)
                ORDER BY ts_rank(search_vector, plainto_tsquery('english', %s)) DESC
                LIMIT %s OFFSET %s
            """
            cur.execute(list_sql, params + [query_text, query_text, per_page, offset])
        else:
            count_sql = f"""
                SELECT COUNT(*) AS total
                FROM articles
                WHERE {where_clause}
            """
            cur.execute(count_sql, params)
            total = int(cur.fetchone()["total"])

            list_sql = f"""
                SELECT id, url, title, description, source, domain, tags, read_time_minutes
                FROM articles
                WHERE {where_clause}
                ORDER BY classified_at DESC
                LIMIT %s OFFSET %s
            """
            cur.execute(list_sql, params + [per_page, offset])

        rows = cur.fetchall()
    finally:
        conn.close()

    pages = math.ceil(total / per_page) if total else 0
    return jsonify(
        {
            "articles": [_row_to_article(row) for row in rows],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }
    )


@articles_bp.route("/domains", methods=["GET"])
def list_domains():
    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT domain, COUNT(*) AS count
            FROM articles
            WHERE is_active = TRUE
            GROUP BY domain
            ORDER BY domain
            """
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    domains = [
        {
            "domain": row["domain"],
            "count": int(row["count"]),
            "label": DOMAIN_LABELS.get(row["domain"], row["domain"]),
        }
        for row in rows
    ]
    return jsonify({"domains": domains})


@articles_bp.route("/recommended", methods=["GET"])
@require_auth
def recommended_articles():
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "User not found"}), 404

    domain = _resolve_user_mingus_domain(user_id)

    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, url, title, description, source, domain, tags, read_time_minutes
            FROM articles
            WHERE is_active = TRUE AND domain = %s
            ORDER BY RANDOM()
            LIMIT 5
            """,
            (domain,),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    return jsonify({"articles": [_row_to_article(row) for row in rows]})


@articles_bp.route("/<int:article_id>/bookmark", methods=["POST"])
@require_auth
def toggle_bookmark(article_id: int):
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "User not found"}), 404

    _ensure_bookmarks_table()

    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM articles WHERE id = %s AND is_active = TRUE",
            (article_id,),
        )
        if cur.fetchone() is None:
            conn.close()
            return jsonify({"error": "Article not found"}), 404

        cur.execute(
            """
            SELECT id FROM article_bookmarks
            WHERE user_id = %s AND article_id = %s
            """,
            (user_id, article_id),
        )
        existing = cur.fetchone()

        if existing:
            cur.execute(
                """
                DELETE FROM article_bookmarks
                WHERE user_id = %s AND article_id = %s
                """,
                (user_id, article_id),
            )
            bookmarked = False
        else:
            cur.execute(
                """
                INSERT INTO article_bookmarks (user_id, article_id)
                VALUES (%s, %s)
                """,
                (user_id, article_id),
            )
            bookmarked = True

        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to toggle bookmark for user %s article %s", user_id, article_id)
        return jsonify({"error": "Failed to update bookmark"}), 500
    finally:
        conn.close()

    return jsonify({"bookmarked": bookmarked})
