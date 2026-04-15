#!/usr/bin/env python3
"""Faith Card API: daily verse generation, favorites, Redis cache, Anthropic."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from urllib.parse import unquote

import anthropic
import redis
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.auth.decorators import require_auth
from backend.models.database import db
from backend.models.favorite_verse import FavoriteVerse
from backend.models.user_models import User

logger = logging.getLogger(__name__)

faith_card_bp = Blueprint("faith_card", __name__, url_prefix="/api/faith-card")

_redis = redis.Redis.from_url(
    os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
    socket_timeout=3,
)


def get_latest_balance_status(user_pk: int) -> str | None:
    """Most recent balance_status from daily_cashflow for this user, or None."""
    user = db.session.get(User, user_pk)
    if not user or not user.user_id:
        return None
    try:
        row = db.session.execute(
            text(
                "SELECT balance_status FROM daily_cashflow "
                "WHERE user_id = :uid "
                "ORDER BY forecast_date DESC NULLS LAST LIMIT 1"
            ),
            {"uid": user.user_id},
        ).fetchone()
        if not row or row[0] is None:
            return None
        return str(row[0])
    except Exception as e:
        logger.debug("daily_cashflow lookup failed for user %s: %s", user_pk, e)
        return None


def generate_verse(user_id: int) -> dict:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cache_key = f"faith_card:{user_id}:{today}"
    cached = _redis.get(cache_key)
    if cached:
        return json.loads(cached)

    user = db.session.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    first_name = user.first_name or "Friend"
    goal = user.primary_financial_goal or "build financial stability"
    balance_status = get_latest_balance_status(user_id) or "unknown"

    system_prompt = """You are a biblical verse selector for a personal
finance app used by Black Christian professionals. Select a single
NIV verse that speaks directly to the user's current financial
situation and stated goal. Write one bridge sentence connecting
the verse to their situation. Warm and personal. Never preachy.

Respond ONLY with a valid JSON object. No preamble. No backticks.
No markdown. Just the raw JSON.

{
  "verse_text": "Full verse text in NIV translation",
  "verse_reference": "Book Chapter:Verse",
  "bridge_sentence": "One sentence connecting verse to situation"
}

SELECTION GUIDELINES:
balance_status danger: provision in scarcity — Phil 4:19, Matt 6:26,
  Ps 23:1, Isa 41:10, Jer 29:11, 2 Cor 9:8
balance_status warning: wisdom/stewardship — Prov 21:5, Prov 13:11,
  Luke 14:28, Prov 27:12, James 1:5, Prov 3:5-6
balance_status healthy/unknown: gratitude/diligence — Deut 8:18,
  Prov 3:9-10, Luke 6:38, Prov 11:24-25, 2 Cor 9:6, Ecc 11:6

GOAL MODIFIERS (combine with balance_status signal):
paying off debt: Rom 13:8, Prov 22:7, Luke 16:10
saving for home: Prov 24:3-4, Ps 37:3
emergency fund: Prov 6:6-8, Prov 21:20, Gen 41:35-36
family/children: Ps 127:3, Prov 13:22, 1 Tim 5:8
career/income: Prov 22:29, Col 3:23, Ecc 9:10
general stability: Ps 112:5, Matt 6:33

BRIDGE SENTENCE RULES:
- Address user by first name once, naturally
- Reference their specific goal or balance situation
- Under 25 words
- Never start with "This verse..." or "Remember that..."
"""

    user_message = f"""
User: {first_name}
Balance status: {balance_status}
Financial goal: {goal}
Select the most fitting NIV verse and write the bridge sentence.
"""

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(raw)
        assert "verse_text" in result
        assert "verse_reference" in result
        assert "bridge_sentence" in result
    except Exception as e:
        logger.warning("Faith card parse failed for user %s: %s", user_id, e)
        result = {
            "verse_text": "I can do all this through him who gives me strength.",
            "verse_reference": "Philippians 4:13",
            "bridge_sentence": f"{first_name}, whatever today holds, you are not facing it alone.",
        }

    result["balance_status"] = balance_status
    result["goal"] = goal
    result["generated_at"] = datetime.utcnow().isoformat()
    result["is_favorited"] = False

    _redis.setex(cache_key, 86400, json.dumps(result))
    return result


def _current_db_user():
    from flask import g

    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


@faith_card_bp.route("/today", methods=["GET"])
@require_auth
def get_today():
    user = _current_db_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    try:
        payload = generate_verse(user.id)
    except ValueError:
        return jsonify({"error": "User not found"}), 404
    ref = payload.get("verse_reference")
    if ref:
        fav = FavoriteVerse.query.filter_by(
            user_id=user.id, verse_reference=ref
        ).first()
        payload["is_favorited"] = bool(fav)
    return jsonify(payload), 200


@faith_card_bp.route("/favorite", methods=["POST"])
@require_auth
def post_favorite():
    user = _current_db_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json(silent=True) or {}
    verse_reference = data.get("verse_reference")
    verse_text = data.get("verse_text")
    bridge_sentence = data.get("bridge_sentence")
    if not verse_reference or not verse_text or not bridge_sentence:
        return jsonify({"error": "verse_reference, verse_text, bridge_sentence required"}), 400

    today = datetime.utcnow().strftime("%Y-%m-%d")
    cache_key = f"faith_card:{user.id}:{today}"
    cached = _redis.get(cache_key)
    balance_status = None
    goal = None
    if cached:
        try:
            c = json.loads(cached)
            balance_status = c.get("balance_status")
            goal = c.get("goal")
        except json.JSONDecodeError:
            pass

    stmt = pg_insert(FavoriteVerse).values(
        user_id=user.id,
        verse_reference=verse_reference,
        verse_text=verse_text,
        bridge_sentence=bridge_sentence,
        balance_status_at_save=balance_status,
        goal_at_save=goal,
        saved_at=datetime.utcnow(),
    )
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["user_id", "verse_reference"],
    )
    db.session.execute(stmt)
    db.session.commit()
    return jsonify({"favorited": True, "verse_reference": verse_reference}), 200


@faith_card_bp.route("/favorite/<path:verse_reference>", methods=["DELETE"])
@require_auth
def delete_favorite(verse_reference: str):
    user = _current_db_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    ref = unquote(verse_reference)
    FavoriteVerse.query.filter_by(user_id=user.id, verse_reference=ref).delete()
    db.session.commit()
    return jsonify({"unfavorited": True}), 200


@faith_card_bp.route("/favorites", methods=["GET"])
@require_auth
def list_favorites():
    user = _current_db_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    rows = (
        FavoriteVerse.query.filter_by(user_id=user.id)
        .order_by(FavoriteVerse.saved_at.desc())
        .all()
    )
    return (
        jsonify(
            [
                {
                    "verse_reference": r.verse_reference,
                    "verse_text": r.verse_text,
                    "bridge_sentence": r.bridge_sentence,
                    "saved_at": r.saved_at.isoformat() if r.saved_at else None,
                }
                for r in rows
            ]
        ),
        200,
    )
