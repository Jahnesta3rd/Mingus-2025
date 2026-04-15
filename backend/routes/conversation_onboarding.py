#!/usr/bin/env python3
"""Conversational onboarding: income, expenses, milestones via Claude + Redis."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone

import anthropic
import redis
from flask import Blueprint, g, jsonify, request

from backend.api.financial_setup_api import _normalize_expense_category, _to_decimal_amount
from backend.api.profile_endpoints import get_db_connection
from backend.auth.decorators import require_auth, require_csrf
from backend.models.database import db
from backend.models.financial_setup import RecurringExpense, UserIncome
from backend.models.user_models import User

logger = logging.getLogger(__name__)

conversation_onboarding_bp = Blueprint(
    "conversation_onboarding",
    __name__,
    url_prefix="/api/conversation-onboarding",
)

_redis = redis.Redis.from_url(
    os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
    socket_timeout=3,
)

_REDIS_TTL_SEC = 7200  # 2 hours

_BASE_SYSTEM = (
    "You are a friendly, direct financial assistant for Mingus, "
    "a personal finance app used by Black professionals aged 25-40. "
    "Keep responses under 60 words. Be conversational, not clinical. "
    "Never use bullet points. Ask one question at a time."
)

_CLUSTER_PROMPTS = {
    "income": (
        _BASE_SYSTEM
        + " You are collecting the user's income information. "
        "Ask for their monthly take-home pay after taxes. "
        "Then ask if they have any secondary income. "
        "Keep it to 2-3 exchanges total. "
        "When you have monthly take-home and know about secondary income, "
        "end your message with the exact token: [INCOME_READY]"
    ),
    "expenses": (
        _BASE_SYSTEM
        + " You are collecting the user's monthly expenses. "
        "Start by asking about their two biggest recurring expenses. "
        "Then ask about food, transportation, subscriptions. "
        "Accept approximate numbers. Keep it to 4-5 exchanges. "
        "When you have at least 3 expense categories, "
        "end your message with: [EXPENSES_READY]"
    ),
    "milestones": (
        _BASE_SYSTEM
        + " You are collecting upcoming financial events. "
        "Ask if there is anything coming up in the next 6 months "
        "that costs money — a trip, a car repair, a registration. "
        "Capture: event name, approximate date, approximate cost. "
        "Keep it to 3-4 exchanges. "
        "When you have at least one milestone or the user says nothing "
        "is coming up, end your message with: [MILESTONES_READY]"
    ),
}

_READY_TOKENS = {
    "income": "[INCOME_READY]",
    "expenses": "[EXPENSES_READY]",
    "milestones": "[MILESTONES_READY]",
}

_DOLLAR_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d{1,2})?)|([\d,]+(?:\.\d{1,2})?)\s*(?:usd|dollars?)\b",
    re.IGNORECASE,
)


def _redis_uid() -> str:
    ext = getattr(g, "current_user_id", None)
    return str(ext) if ext is not None else ""


def _k_history(uid: str) -> str:
    return f"conv_onboarding:history:{uid}"


def _k_cluster(uid: str) -> str:
    return f"conv_onboarding:cluster:{uid}"


def _k_turns(uid: str) -> str:
    return f"conv_onboarding:turns:{uid}"


def _k_extracted(uid: str) -> str:
    return f"conv_onboarding:extracted:{uid}"


def _touch(uid: str, *keys: str) -> None:
    for k in keys:
        if _redis.exists(k):
            _redis.expire(k, _REDIS_TTL_SEC)


def _save_json(uid: str, key: str, value) -> None:
    _redis.setex(key, _REDIS_TTL_SEC, json.dumps(value))


def _load_json_list(uid: str, key: str) -> list:
    raw = _redis.get(key)
    if not raw:
        return []
    try:
        v = json.loads(raw)
        return v if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []


def _load_json_dict(uid: str, key: str) -> dict:
    raw = _redis.get(key)
    if not raw:
        return {}
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else {}
    except json.JSONDecodeError:
        return {}


def _current_cluster(uid: str) -> str:
    c = _redis.get(_k_cluster(uid))
    if c in ("income", "expenses", "milestones", "done"):
        return c
    return "income"


def _clear_user_keys(uid: str) -> None:
    for k in (
        _k_history(uid),
        _k_cluster(uid),
        _k_turns(uid),
        _k_extracted(uid),
    ):
        _redis.delete(k)


def _parse_money_token(s: str) -> float | None:
    s = (s or "").replace(",", "").strip()
    if not s:
        return None
    try:
        v = float(s)
        return v if v >= 0 else None
    except ValueError:
        return None


def _all_dollar_amounts(text: str) -> list[float]:
    out: list[float] = []
    for m in _DOLLAR_RE.finditer(text or ""):
        g1, g2 = m.group(1), m.group(2)
        raw = g1 or g2
        v = _parse_money_token(raw or "")
        if v is not None:
            out.append(v)
    return out


def extract_cluster_data(response_text: str, cluster: str) -> dict:
    ready_token = _READY_TOKENS.get(cluster)
    if not ready_token or ready_token not in (response_text or ""):
        return {}

    text = response_text or ""
    low = text.lower()

    if cluster == "income":
        amounts = _all_dollar_amounts(text)
        if not amounts:
            return {}
        primary = None
        for m in _DOLLAR_RE.finditer(text):
            g1, g2 = m.group(1), m.group(2)
            raw = g1 or g2
            start = m.start()
            ctx = text[max(0, start - 70) : start + 70].lower()
            if any(
                k in ctx
                for k in (
                    "take-home",
                    "take home",
                    "takehome",
                    "monthly",
                    "paycheck",
                    "after tax",
                    "home pay",
                )
            ):
                v = _parse_money_token(raw or "")
                if v is not None:
                    primary = v
                    break
        if primary is None:
            primary = amounts[0]
        has_secondary: bool | None = None
        secondary_amount: float | None = None
        if any(
            x in low
            for x in (
                "no secondary",
                "no side",
                "don't have secondary",
                "dont have secondary",
                "no freelance",
                "not anymore",
                "no second",
                "only my main",
                "just the one",
                "no other income",
            )
        ):
            has_secondary = False
        elif re.search(r"\b(yes|yeah|yep)\b", low) or any(
            x in low
            for x in (
                "side income",
                "freelance",
                "second job",
                "part-time",
                "part time",
                "also make",
                "another",
            )
        ):
            has_secondary = True
        if has_secondary is True and len(amounts) >= 2:
            secondary_amount = amounts[1]
        elif has_secondary is True and len(amounts) == 1:
            has_secondary = None
        if has_secondary is None:
            return {}
        return {
            "monthly_takehome": float(primary),
            "has_secondary": bool(has_secondary),
            "secondary_amount": float(secondary_amount)
            if secondary_amount is not None
            else None,
        }

    if cluster == "expenses":
        categories: list[dict] = []
        # "Rent: $1500" / "$800 on food" / "subscriptions about $50"
        line_pat = re.compile(
            r"(?P<label>[A-Za-z][A-Za-z\s\-]{1,40}?)\s*[:\-]?\s*\$(?P<amt>[\d,]+(?:\.\d{1,2})?)",
            re.IGNORECASE,
        )
        for m in line_pat.finditer(text):
            name = (m.group("label") or "").strip()
            amt = _parse_money_token(m.group("amt") or "")
            if name and amt is not None and amt > 0:
                categories.append({"name": name, "amount": float(amt)})
        if len(categories) < 3:
            # fallback: pair amounts with nearby words (limited)
            amounts = _all_dollar_amounts(text)
            if len(amounts) >= 3:
                categories = [
                    {"name": "expense_1", "amount": float(amounts[0])},
                    {"name": "expense_2", "amount": float(amounts[1])},
                    {"name": "expense_3", "amount": float(amounts[2])},
                ]
            else:
                return {}
        return {"categories": categories[:12]}

    if cluster == "milestones":
        if any(
            x in low
            for x in (
                "nothing coming",
                "nothing is coming",
                "not that i know",
                "no upcoming",
                "no plans",
                "nothing planned",
                "nothing major",
                "can't think",
                "cant think",
                "nothing on the horizon",
                "all quiet",
            )
        ):
            return {"events": []}
        events: list[dict] = []
        chunk = re.split(r"[.\n]", text)
        for part in chunk:
            if "$" not in part:
                continue
            amts = _all_dollar_amounts(part)
            if not amts:
                continue
            cost = float(amts[-1])
            date_hint = ""
            dm = re.search(
                r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}\b",
                part,
                re.I,
            )
            iso = re.search(r"\b20\d{2}-\d{2}-\d{2}\b", part)
            if iso:
                date_hint = iso.group(0)
            elif dm:
                date_hint = dm.group(0).strip()
            name = part.split("$")[0].strip(" :-—\t")
            name = re.sub(r"^\W+", "", name).strip()
            if len(name) < 2:
                name = "Upcoming expense"
            events.append(
                {"name": name[:120], "date_hint": date_hint or "", "cost": cost}
            )
        if not events and (amounts := _all_dollar_amounts(text)):
            events.append(
                {
                    "name": "Planned expense",
                    "date_hint": "",
                    "cost": float(amounts[0]),
                }
            )
        if not events:
            return {}
        return {"events": events[:20]}

    return {}


def _strip_ready_token(response_text: str, cluster: str) -> str:
    tok = _READY_TOKENS.get(cluster)
    if not tok:
        return response_text
    return (response_text or "").replace(tok, "").strip()


def _guess_expense_category(name: str) -> str:
    n = (name or "").lower()
    if any(x in n for x in ("rent", "mortgage", "housing", "landlord")):
        return "housing"
    if any(x in n for x in ("uber", "lyft", "gas", "car", "auto", "transit", "metro")):
        return "transportation"
    if any(x in n for x in ("netflix", "spotify", "subscription", "gym", "software")):
        return "subscription"
    if any(x in n for x in ("insurance", "health", "medical")):
        return "insurance"
    if any(x in n for x in ("util", "electric", "water", "internet", "phone")):
        return "utilities"
    if any(x in n for x in ("debt", "loan", "credit card", "student")):
        return "debt"
    norm = _normalize_expense_category(n)
    return norm if norm else "other"


def _next_cluster(current: str) -> str:
    return {"income": "expenses", "expenses": "milestones", "milestones": "done"}.get(
        current, "done"
    )


def _merge_important_dates_custom_events(
    email: str, new_events: list[dict]
) -> None:
    if not new_events:
        return
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT important_dates FROM user_profiles WHERE email = %s",
            (email,),
        )
        row = cursor.fetchone()
        prev: dict = {}
        if row and row.get("important_dates"):
            try:
                raw = row["important_dates"]
                prev = json.loads(raw) if isinstance(raw, str) else raw
                if not isinstance(prev, dict):
                    prev = {}
            except (TypeError, ValueError):
                prev = {}
        customs = prev.get("customEvents") or prev.get("custom_events") or []
        if not isinstance(customs, list):
            customs = []
        for ev in new_events:
            if not isinstance(ev, dict):
                continue
            name = str(ev.get("name") or "Event").strip()
            cost = ev.get("cost")
            dh = str(ev.get("date_hint") or ev.get("date") or "").strip()
            date_iso = dh[:10] if len(dh) >= 10 and re.match(r"\d{4}-\d{2}-\d{2}", dh) else ""
            if not date_iso:
                # keep hint in name if not ISO-parseable
                date_iso = datetime.now(timezone.utc).date().isoformat()
            try:
                cval = float(cost) if cost is not None else 0.0
            except (TypeError, ValueError):
                cval = 0.0
            customs.append(
                {
                    "name": name,
                    "date": date_iso,
                    "cost": cval,
                }
            )
        prev["customEvents"] = customs
        imp_json = json.dumps(prev)
        cursor.execute(
            "UPDATE user_profiles SET important_dates = %s, "
            "updated_at = CURRENT_TIMESTAMP WHERE email = %s",
            (imp_json, email),
        )
        if cursor.rowcount == 0:
            cursor.execute(
                "INSERT INTO user_profiles (email, first_name, personal_info, "
                "financial_info, monthly_expenses, important_dates, health_wellness, "
                "goals, created_at, updated_at) "
                "VALUES (%s, NULL, '{}', '{}', '{}', %s, '{}', '{}', "
                "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (email, imp_json),
            )
        conn.commit()
    finally:
        conn.close()


def commit_to_database(user_id: str, extracted: dict | None = None) -> dict:
    """Persist onboarding extraction using the same persistence layer as financial setup."""
    ts = datetime.now(timezone.utc).isoformat()
    uid = str(user_id)
    if extracted is None:
        raw = _redis.get(_k_extracted(uid))
        extracted = json.loads(raw) if raw else {}
    if not isinstance(extracted, dict):
        extracted = {}

    if not any(
        bool(extracted.get(k))
        for k in ("income", "expenses", "milestones")
    ):
        return {"success": False, "committed_at": ts, "error": "Nothing to commit"}

    user = User.query.filter_by(user_id=uid).first()
    if not user:
        return {"success": False, "committed_at": ts, "error": "User not found"}

    email = (user.email or "").strip().lower()
    if not email:
        return {"success": False, "committed_at": ts, "error": "User email missing"}

    try:
        inc = extracted.get("income")
        if isinstance(inc, dict) and inc.get("monthly_takehome") is not None:
            monthly = _to_decimal_amount(inc.get("monthly_takehome"))
            if monthly is None or monthly <= 0:
                raise ValueError("invalid monthly_takehome")
            sources = [
                {
                    "source_name": "Primary take-home",
                    "amount": float(monthly),
                    "frequency": "monthly",
                    "pay_day": None,
                }
            ]
            if inc.get("has_secondary") and inc.get("secondary_amount"):
                sec = _to_decimal_amount(inc.get("secondary_amount"))
                if sec is not None and sec > 0:
                    sources.append(
                        {
                            "source_name": "Secondary income",
                            "amount": float(sec),
                            "frequency": "monthly",
                            "pay_day": None,
                        }
                    )
            for row in UserIncome.query.filter_by(user_id=user.id).all():
                row.is_active = False
            for item in sources:
                db.session.add(
                    UserIncome(
                        user_id=user.id,
                        source_name=item["source_name"],
                        amount=_to_decimal_amount(item["amount"]),
                        frequency="monthly",
                        pay_day=None,
                        is_active=True,
                    )
                )

        exp = extracted.get("expenses")
        if isinstance(exp, dict) and exp.get("categories"):
            cats = exp["categories"]
            if not isinstance(cats, list) or not cats:
                raise ValueError("invalid expenses.categories")
            for row in RecurringExpense.query.filter_by(user_id=user.id).all():
                row.is_active = False
            for item in cats:
                if not isinstance(item, dict):
                    continue
                name = (item.get("name") or "").strip()
                amt = _to_decimal_amount(item.get("amount"))
                if not name or amt is None or amt <= 0:
                    continue
                cat = _guess_expense_category(name)
                db.session.add(
                    RecurringExpense(
                        user_id=user.id,
                        name=name,
                        amount=amt,
                        category=cat,
                        frequency=str(item.get("frequency") or "monthly").lower(),
                        due_day=None,
                        is_active=True,
                        source=None,
                    )
                )

        mil = extracted.get("milestones")
        if isinstance(mil, dict) and "events" in mil:
            evs = mil.get("events") or []
            if isinstance(evs, list) and evs:
                _merge_important_dates_custom_events(email, evs)

        db.session.commit()
        _clear_user_keys(uid)
        return {"success": True, "committed_at": ts}
    except Exception as e:
        db.session.rollback()
        logger.error("commit_to_database failed for %s: %s", uid, e)
        return {"success": False, "committed_at": ts, "error": str(e)}


@conversation_onboarding_bp.route("/message", methods=["POST"])
@require_auth
@require_csrf
def post_message():
    uid = _redis_uid()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    msg = data.get("message")
    if not isinstance(msg, str) or not msg.strip():
        return jsonify({"error": "message is required"}), 400

    history = _load_json_list(uid, _k_history(uid))
    cluster = _current_cluster(uid)
    if cluster == "done":
        return jsonify({"error": "Onboarding already complete; reset to continue."}), 400

    try:
        turn_count = int(_redis.get(_k_turns(uid)) or "0")
    except ValueError:
        turn_count = 0

    if turn_count >= 25:
        return (
            jsonify(
                {
                    "type": "hard_cap",
                    "message": "You have reached the conversation limit for this session. "
                    "Confirm what you have so far or reset to start over.",
                }
            ),
            200,
        )

    history.append({"role": "user", "content": msg.strip()})
    system = _CLUSTER_PROMPTS.get(cluster) or _CLUSTER_PROMPTS["income"]

    client = anthropic.Anthropic()
    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=system,
        messages=api_messages,
    )
    raw_assistant = (message.content[0].text or "").strip()
    history.append({"role": "assistant", "content": raw_assistant})
    turn_count += 1

    _save_json(uid, _k_history(uid), history)
    _redis.setex(_k_turns(uid), _REDIS_TTL_SEC, str(turn_count))
    _redis.setex(_k_cluster(uid), _REDIS_TTL_SEC, cluster)
    _touch(uid, _k_extracted(uid))

    extracted = extract_cluster_data(raw_assistant, cluster)
    content = _strip_ready_token(raw_assistant, cluster)
    ready_to_confirm = bool(extracted)

    return (
        jsonify(
            {
                "type": "message",
                "content": content,
                "cluster": cluster,
                "turn": turn_count,
                "ready_to_confirm": ready_to_confirm,
                "extracted": extracted if extracted else None,
            }
        ),
        200,
    )


@conversation_onboarding_bp.route("/confirm", methods=["POST"])
@require_auth
@require_csrf
def post_confirm():
    uid = _redis_uid()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    cluster = data.get("cluster")
    payload = data.get("data")
    if cluster not in ("income", "expenses", "milestones"):
        return jsonify({"error": "cluster must be income, expenses, or milestones"}), 400
    if not isinstance(payload, dict):
        return jsonify({"error": "data must be an object"}), 400

    current = _current_cluster(uid)
    if current != cluster:
        return (
            jsonify(
                {
                    "error": f"Cluster mismatch: expected {current!r}, got {cluster!r}",
                }
            ),
            400,
        )

    extracted = _load_json_dict(uid, _k_extracted(uid))
    extracted[cluster] = payload
    next_cluster = _next_cluster(cluster)

    if next_cluster == "done":
        result = commit_to_database(uid, extracted)
        if not result.get("success"):
            return (
                jsonify({"error": result.get("error", "commit failed")}),
                500,
            )
        return jsonify({"next_cluster": "done", "done": True}), 200

    _save_json(uid, _k_extracted(uid), extracted)
    _redis.setex(_k_cluster(uid), _REDIS_TTL_SEC, next_cluster)
    _redis.delete(_k_history(uid))
    _redis.setex(_k_turns(uid), _REDIS_TTL_SEC, "0")
    _touch(uid, _k_extracted(uid))

    return jsonify({"next_cluster": next_cluster, "done": False}), 200


@conversation_onboarding_bp.route("/commit", methods=["POST"])
@require_auth
@require_csrf
def post_commit():
    uid = _redis_uid()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    out = commit_to_database(uid, None)
    code = 200 if out.get("success") else 500
    return jsonify(out), code


@conversation_onboarding_bp.route("/reset", methods=["DELETE"])
@require_auth
@require_csrf
def delete_reset():
    uid = _redis_uid()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    _clear_user_keys(uid)
    return jsonify({"reset": True}), 200
