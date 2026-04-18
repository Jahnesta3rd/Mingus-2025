#!/usr/bin/env python3
"""Module-based conversational onboarding (Claude + Redis + optional DB progress)."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone

import anthropic
import redis
from flask import Blueprint, g, jsonify, request

from backend.auth.decorators import require_auth, require_csrf
from backend.constants.onboarding import CATEGORY_KEYS, CATEGORY_KEY_IDS, MODULE_ORDER
from backend.middleware.limiter_ext import limiter
from backend.models.database import db
from backend.models.onboarding_progress import OnboardingProgress
from backend.models.user_models import User
from backend.routes._modular_onboarding_gc2_commit import run_commit_field, run_commit_module

try:
    from dateutil import parser as date_parser
except ImportError:  # pragma: no cover
    date_parser = None

logger = logging.getLogger(__name__)

modular_onboarding_bp = Blueprint(
    "modular_onboarding",
    __name__,
    url_prefix="/api/modular-onboarding",
)

_redis = redis.Redis.from_url(
    os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
    socket_timeout=3,
)

_REDIS_TTL_SEC = 604800  # 7 days
_REDIS_KEY = "onb_session:{uid}"
_TOTAL_TURN_CAP = 35

BASE_SYSTEM = """You are Mingus, a warm and efficient financial onboarding
assistant. Ask one question at a time. Keep responses to 1-2 sentences. Never
lecture. When the user gives an approximate number, accept it and move on.
Do not repeat back what the user just said unless confirming a specific detail
that will be stored. The Onboarding Canvas shows the user what you have captured
so far, so you do not need to recite it back."""

_DOLLAR_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d{1,2})?)|([\d,]+(?:\.\d{1,2})?)\s*(?:usd|dollars?)\b",
    re.IGNORECASE,
)
_READY_STRIP_RE = re.compile(r"\[MODULE_COMPLETE:[^\]]+\]")
_ZIP_RE = re.compile(r"\b(\d{5})\b")
_ISO_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")


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
        raw = (m.group(1) or m.group(2) or "").replace(",", "")
        v = _parse_money_token(raw)
        if v is not None:
            out.append(v)
    return out


def _ext_user_id() -> str:
    ext = getattr(g, "current_user_id", None)
    return str(ext) if ext is not None else ""


def _session_key(uid: str) -> str:
    return _REDIS_KEY.format(uid=uid)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_session() -> dict:
    return {
        "current_module": MODULE_ORDER[0],
        "turn_count": 0,
        "module_turns": {},
        "messages": [],
        "completed_modules": [],
        "skipped_modules": [],
        "started_at": _now_iso(),
    }


def _load_row(user: User) -> OnboardingProgress | None:
    return OnboardingProgress.query.filter_by(user_id=user.id).first()


def _merge_db_into_session(user: User, session: dict) -> None:
    row = _load_row(user)
    if not row:
        return
    if row.completed_modules:
        session["completed_modules"] = list(row.completed_modules)
    if row.skipped_modules:
        session["skipped_modules"] = list(row.skipped_modules)
    if row.current_module and row.current_module in MODULES:
        session["current_module"] = row.current_module
    if row.started_at:
        session["started_at"] = row.started_at.replace(tzinfo=timezone.utc).isoformat()


def _get_session(uid: str, user: User | None) -> dict:
    raw = _redis.get(_session_key(uid))
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    session = _default_session()
    if user is not None:
        _merge_db_into_session(user, session)
    return session


def _save_session(uid: str, session: dict) -> None:
    _redis.setex(_session_key(uid), _REDIS_TTL_SEC, json.dumps(session))


def _upsert_db_progress(user: User, session: dict) -> None:
    row = _load_row(user)
    now = datetime.utcnow()
    if not row:
        row = OnboardingProgress(
            user_id=user.id,
            completed_modules=list(session.get("completed_modules") or []),
            skipped_modules=list(session.get("skipped_modules") or []),
            current_module=session.get("current_module") or MODULE_ORDER[0],
            started_at=now,
            last_activity_at=now,
        )
        db.session.add(row)
    else:
        row.completed_modules = list(session.get("completed_modules") or [])
        row.skipped_modules = list(session.get("skipped_modules") or [])
        row.current_module = session.get("current_module") or MODULE_ORDER[0]
        row.last_activity_at = now
    covered = set(row.completed_modules or []) | set(row.skipped_modules or [])
    all_accounted = all(mid in covered for mid in MODULE_ORDER)
    row.completed_at = now if all_accounted else None
    db.session.commit()


def _delete_db_progress(user: User) -> None:
    row = _load_row(user)
    if row:
        db.session.delete(row)
        db.session.commit()


def _next_open_module(session: dict) -> str | None:
    done = set(session.get("completed_modules") or [])
    skip = set(session.get("skipped_modules") or [])
    for mid in MODULE_ORDER:
        if mid in done or mid in skip:
            continue
        return mid
    return None


def _strip_ready_tokens(text: str) -> str:
    return _READY_STRIP_RE.sub("", text or "").strip()


def _parse_milestone_date(fragment: str) -> str | None:
    s = (fragment or "").strip()
    if not s:
        return None
    iso_m = _ISO_DATE_RE.search(s)
    if iso_m:
        return iso_m.group(1)
    if date_parser is None:
        return None
    has_year = bool(re.search(r"\b20\d{2}\b", s))
    has_month = bool(
        re.search(
            r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\b",
            s,
            re.I,
        )
    )
    if not has_year and not has_month and not re.search(r"\b\d{1,2}[/-]\d{1,2}\b", s):
        return None
    try:
        default = datetime(2026, 1, 1)
        dt = date_parser.parse(s, default=default, fuzzy=False)
        if not has_year and dt.year == default.year and has_month:
            return dt.date().isoformat()
        if has_year or re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", s):
            return dt.date().isoformat()
        if has_month and has_year:
            return dt.date().isoformat()
        return None
    except (ValueError, TypeError, OverflowError):
        return None


def _extract_income(text: str) -> dict:
    low = text.lower()
    out: dict = {}
    amounts = _all_dollar_amounts(text)
    if amounts:
        out["monthly_takehome"] = float(amounts[0])
    freq = None
    compact = low.replace("-", "").replace(" ", "")
    if "biweekly" in compact or "everytwoweeks" in compact or "every2weeks" in compact:
        freq = "biweekly"
    elif "semimonthly" in compact or "twiceamonth" in compact or "twicemonthly" in compact:
        freq = "semimonthly"
    elif "weekly" in low and "biweekly" not in compact:
        freq = "weekly"
    elif "monthly" in low or "permonth" in compact:
        freq = "monthly"
    if freq:
        out["pay_frequency"] = freq
    has_secondary: bool | None = None
    if any(
        x in low
        for x in (
            "no secondary",
            "no side",
            "no freelance",
            "no gig",
            "don't have",
            "dont have",
            "no second",
            "no other income",
        )
    ):
        has_secondary = False
    elif any(
        x in low
        for x in (
            "side",
            "freelance",
            "gig",
            "second job",
            "secondary",
            "part-time",
            "part time",
        )
    ):
        has_secondary = True
    if has_secondary is not None:
        out["has_secondary"] = has_secondary
    if has_secondary and len(amounts) >= 2:
        out["secondary_amount"] = float(amounts[1])
    else:
        out.setdefault("secondary_amount", None)
    bonus = None
    if "no bonus" in low or ("not really" in low and "bonus" in low):
        bonus = "none"
    elif "quarter" in low and "bonus" in low:
        bonus = "quarterly"
    elif ("annual" in low and "bonus" in low) or "year-end" in low:
        bonus = "annual"
    elif "bonus" in low:
        bonus = "unspecified"
    if bonus:
        out["bonus_cadence"] = bonus
    else:
        out.setdefault("bonus_cadence", None)
    return out


def _extract_housing(text: str) -> dict:
    low = text.lower()
    out: dict = {}
    if "mortgage" in low or re.search(r"\bown\b", low) or "homeowner" in low:
        out["housing_type"] = "own"
    elif "rent" in low or "renting" in low or "landlord" in low:
        out["housing_type"] = "rent"
    amts = _all_dollar_amounts(text)
    if amts:
        out["monthly_cost"] = float(amts[0])
    zm = _ZIP_RE.search(text)
    if zm:
        out["zip_or_city"] = zm.group(1)
    else:
        m = re.search(
            r"\b(in|at|near)\s+([A-Za-z][A-Za-z\s]{2,40}?)(?:,|\s+\d{5}|\s*$|\.)",
            text,
            re.I,
        )
        if m:
            out["zip_or_city"] = m.group(2).strip()
    if "split" in low or "roommate" in low or ("partner" in low and "pay" in low):
        pm = re.search(
            r"(\d{1,3})\s*%|(\d{1,3})\s*percent", low
        )
        if pm:
            out["split_share_pct"] = float(pm.group(1) or pm.group(2))
    else:
        out.setdefault("split_share_pct", None)
    out["has_buy_goal"] = any(
        x in low for x in ("buy a home", "buying", "purchase", "down payment", "house hunt")
    )
    if out.get("has_buy_goal") and len(amts) >= 2:
        out["target_price"] = float(amts[1])
    else:
        out.setdefault("target_price", None)
    tm = re.search(r"(\d{1,2})\s*(?:month|mo\b)", low)
    if not tm:
        tm = re.search(r"within\s*(\d{1,2})", low)
    if tm:
        out["target_timeline_months"] = int(tm.group(1))
    else:
        out.setdefault("target_timeline_months", None)
    return out


def _extract_vehicle(text: str) -> dict:
    low = text.lower()
    out: dict = {"vehicles": []}
    if "no vehicle" in low or "don't have a car" in low or "no car" in low:
        out["vehicle_count"] = 0
        return out
    if re.search(r"\b(2\+|two or more|multiple vehicle|more than one)", low):
        out["vehicle_count"] = 2
    elif re.search(r"\b1\b\s+vehicle|\bone\b vehicle|one car|single vehicle", low):
        out["vehicle_count"] = 1
    elif "two" in low and "vehicle" in low:
        out["vehicle_count"] = 2
    else:
        nm = re.search(r"(\d+)\s+vehicle", low)
        if nm:
            n = int(nm.group(1))
            out["vehicle_count"] = min(2, n) if n <= 2 else 2
        else:
            out["vehicle_count"] = 1
    vehicles: list[dict] = []
    year_iter = list(re.finditer(r"\b(19|20)\d{2}\b", text))
    for ym in year_iter:
        year = int(ym.group(0))
        window = text[max(0, ym.start() - 80) : ym.end() + 80]
        make_m = re.search(
            r"\b(Toyota|Honda|Ford|Chevy|Chevrolet|BMW|Tesla|Subaru|Nissan|Hyundai|Kia|Mazda|Jeep|Ram|GMC|Audi|Mercedes|Lexus|Volkswagen|VW)\b",
            window,
            re.I,
        )
        make = make_m.group(1) if make_m else "unknown"
        model_m = re.search(
            r"(?:Toyota|Honda|Ford|Chevy|Chevrolet|BMW|Tesla|Subaru|Nissan|Hyundai|Kia|Mazda|Jeep|Ram|GMC|Audi|Mercedes|Lexus|Volkswagen|VW)\s+([A-Za-z0-9\-]{2,20})",
            window,
            re.I,
        )
        model = model_m.group(1) if model_m else "unknown"
        sub_amts = _all_dollar_amounts(window)
        fuel = float(sub_amts[0]) if sub_amts else 0.0
        pay = float(sub_amts[1]) if len(sub_amts) > 1 else None
        maint = any(
            x in window.lower()
            for x in ("maintenance", "repair", "service", "oil change", "fixed")
        )
        vehicles.append(
            {
                "make": make,
                "model": model,
                "year": year,
                "monthly_fuel": fuel,
                "monthly_payment": pay,
                "recent_maintenance": maint,
            }
        )
    if not vehicles and out.get("vehicle_count", 0) > 0:
        sub_amts = _all_dollar_amounts(text)
        vehicles.append(
            {
                "make": "unknown",
                "model": "unknown",
                "year": datetime.now().year,
                "monthly_fuel": float(sub_amts[0]) if sub_amts else 0.0,
                "monthly_payment": float(sub_amts[1]) if len(sub_amts) > 1 else None,
                "recent_maintenance": "maintenance" in low,
            }
        )
    out["vehicles"] = vehicles[:5]
    return out


def _extract_recurring_expenses(text: str) -> dict:
    low = text.lower()
    categories: list[dict] = []
    found: dict[str, float] = {}
    for cat_id, keys in CATEGORY_KEYS:
        for line in text.splitlines():
            l = line.lower()
            if any(k in l for k in keys):
                amts = _all_dollar_amounts(line)
                if amts:
                    found[cat_id] = float(amts[-1])
    for cat_id, _keys in CATEGORY_KEYS:
        categories.append(
            {"category_id": cat_id, "amount": float(found.get(cat_id, 0.0))}
        )
    if not any(v > 0 for v in found.values()):
        for cat_id, keys in CATEGORY_KEYS:
            for m in _DOLLAR_RE.finditer(text):
                ctx = text[max(0, m.start() - 50) : m.start() + 50].lower()
                if any(k in ctx for k in keys):
                    raw = (m.group(1) or m.group(2) or "").replace(",", "")
                    val = _parse_money_token(raw)
                    if val is not None:
                        found[cat_id] = float(val)
        categories = [
            {"category_id": cid, "amount": float(found.get(cid, 0.0))}
            for cid, _ in CATEGORY_KEYS
        ]
    return {"categories": categories}


def _extract_roster(text: str) -> dict:
    low = text.lower()
    out: dict = {"people": []}
    for label in (
        "single",
        "dating",
        "partnered",
        "married",
        "divorced",
        "other",
    ):
        if re.search(rf"\b{label}\b", low):
            out["relationship_status"] = label
            break
    if "relationship_status" not in out:
        out["relationship_status"] = "unknown"
    nick_m = re.findall(
        r"(?:nickname|call(?:ed)?|goes by)\s+['\"]?([A-Za-z][A-Za-z0-9\-]{1,24})['\"]?",
        text,
        re.I,
    )
    cost_amts = _all_dollar_amounts(text)
    for i, nick in enumerate(nick_m[:8]):
        rel = "other"
        if i < len(cost_amts):
            cost = float(cost_amts[min(i + 1, len(cost_amts) - 1)])
        else:
            cost = 0.0
        out["people"].append(
            {
                "nickname": nick,
                "relationship_type": rel,
                "monthly_cost": cost,
            }
        )
    if "social" in low or "dating spend" in low:
        if cost_amts:
            out["monthly_social_spend"] = float(cost_amts[-1])
    if "monthly_social_spend" not in out:
        if cost_amts:
            out["monthly_social_spend"] = float(cost_amts[-1])
        else:
            out["monthly_social_spend"] = 0.0
    return out


def _extract_career(text: str) -> dict:
    low = text.lower()
    out: dict = {}
    title_m = re.search(
        r"(?:role|title|position|i am a|i'm a|work as)\s*[:\-]?\s*([A-Za-z][A-Za-z\s\-]{3,60}?)(?:\.|,|\n)",
        text,
        re.I,
    )
    if title_m:
        out["current_role"] = title_m.group(1).strip()
    ind_m = re.search(
        r"(?:industry|sector)\s*[:\-]?\s*([A-Za-z][A-Za-z\s\-]{2,40}?)(?:\.|,|\n)",
        text,
        re.I,
    )
    if ind_m:
        out["industry"] = ind_m.group(1).strip()
    ym = re.search(
        r"(?:years of experience|(\d{1,2})\s*(?:\+)?\s*years)", low, re.I
    )
    if ym:
        g = ym.group(1)
        if g:
            out["years_experience"] = int(g)
    sm = re.search(r"(?:satisfaction|rating)\s*(?:of|:)?\s*(\d)\b", low)
    if not sm:
        sm = re.search(r"\b([1-5])\s*/\s*5\b", low)
    if sm:
        out["satisfaction"] = int(sm.group(1))
    out["open_to_move"] = any(
        x in low for x in ("open to move", "would relocate", "new job", "yes, open")
    ) and not ("not open" in low or "no move" in low)
    amts = _all_dollar_amounts(text)
    if out.get("open_to_move") and amts:
        out["target_comp"] = float(amts[-1])
    else:
        out.setdefault("target_comp", None)
    return out


def _extract_milestones(text: str) -> dict:
    low = text.lower()
    events: list[dict] = []
    if any(
        x in low
        for x in (
            "nothing upcoming",
            "nothing coming",
            "no milestone",
            "no upcoming",
            "nothing planned",
        )
    ):
        return {"events": []}
    for block in re.split(r"[\n;]", text):
        if "$" not in block and not re.search(r"\bcost\b", block.lower()):
            continue
        amts = _all_dollar_amounts(block)
        if not amts:
            continue
        cost = float(amts[-1])
        name = re.sub(r"\[MODULE_COMPLETE:\w+\]", "", block).split("$")[0].strip(" :-—\t")
        name = re.sub(r"^\W+", "", name).strip() or "Event"
        date_iso = None
        iso_m = _ISO_DATE_RE.search(block)
        if iso_m:
            date_iso = iso_m.group(1)
        else:
            dm = re.search(
                r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*20\d{2})?\b",
                block,
                re.I,
            )
            if dm:
                date_iso = _parse_milestone_date(dm.group(0))
        recurring = any(x in block.lower() for x in ("annual", "every year", "recur"))
        events.append(
            {
                "name": name[:160],
                "date": date_iso,
                "cost": cost,
                "recurring": recurring,
            }
        )
    if not events and _all_dollar_amounts(text):
        events.append(
            {
                "name": "Milestone",
                "date": None,
                "cost": float(_all_dollar_amounts(text)[0]),
                "recurring": False,
            }
        )
    return {"events": events[:24]}


def extract_module_data(response_text: str, module_id: str) -> dict:
    """Regex / keyword extraction only; never raises."""
    try:
        if module_id not in MODULES:
            return {"_parse_failed": True, "raw": response_text or ""}
        tok = MODULES[module_id]["ready_token"]
        if tok not in (response_text or ""):
            return {}
        fn = MODULES[module_id].get("extraction_fn")
        if not callable(fn):
            return {"_parse_failed": True, "raw": response_text or ""}
        return fn(response_text)
    except Exception:
        logger.exception("extract_module_data failed for %s", module_id)
        return {"_parse_failed": True, "raw": response_text or ""}


def _build_modules() -> dict:
    return {
        "income": {
            "id": "income",
            "display_name": "Income",
            "ready_token": "[MODULE_COMPLETE:income]",
            "per_module_turn_cap": 6,
            "system_prompt_append": (
                "Collect the user monthly take-home pay after taxes, their pay frequency "
                "(weekly, biweekly, semimonthly, monthly), whether they have secondary income "
                "(freelance, side work, gig), and approximate bonus cadence if any. Ask one "
                "thing at a time. Accept approximate numbers. When you have monthly take-home, "
                "pay frequency, and know whether secondary income exists, end your message with "
                "exactly: [MODULE_COMPLETE:income]"
            ),
            "extraction_fn": _extract_income,
        },
        "housing": {
            "id": "housing",
            "display_name": "Housing",
            "ready_token": "[MODULE_COMPLETE:housing]",
            "per_module_turn_cap": 6,
            "system_prompt_append": (
                "Collect: rent or own, monthly housing cost (rent or mortgage plus escrow), "
                "ZIP or city, whether they split cost with a partner or roommate and their "
                "share, and whether they have a buy or move goal in the next 24 months. If "
                "a buy goal, ask the target price range. When you have housing_type, monthly "
                "cost, and location, end with: [MODULE_COMPLETE:housing]"
            ),
            "extraction_fn": _extract_housing,
        },
        "vehicle": {
            "id": "vehicle",
            "display_name": "Vehicle",
            "ready_token": "[MODULE_COMPLETE:vehicle]",
            "per_module_turn_cap": 7,
            "system_prompt_append": (
                "Collect vehicle information. First ask how many vehicles they have "
                "(0, 1, or 2+). For each vehicle collect: make, model, year (precise year), "
                "approximate monthly fuel spend, monthly loan or lease payment if any, and "
                "whether they spent on maintenance in the last 6 months. For budget tier, "
                "lump all vehicles into one summary. For mid-tier and professional, collect "
                "per-vehicle detail. End with: [MODULE_COMPLETE:vehicle]"
            ),
            "extraction_fn": _extract_vehicle,
        },
        "recurring_expenses": {
            "id": "recurring_expenses",
            "display_name": "Recurring Expenses",
            "ready_token": "[MODULE_COMPLETE:expenses]",
            "per_module_turn_cap": 8,
            "system_prompt_append": (
                "Collect monthly recurring expenses across these eight categories: "
                "insurance, debt, subscription, utilities, other, groceries, healthcare, "
                "childcare. Ask about each in turn. Accept approximate "
                "numbers. If the user says a category does not apply, record zero. When you "
                "have amounts for all eight categories (including zeros), end with: "
                "[MODULE_COMPLETE:expenses]"
            ),
            "extraction_fn": _extract_recurring_expenses,
        },
        "roster": {
            "id": "roster",
            "display_name": "Vibe Check",
            "ready_token": "[MODULE_COMPLETE:roster]",
            "per_module_turn_cap": 6,
            "system_prompt_append": (
                "Collect the people who have financial weight in the user life. First ask "
                "their relationship status (single, dating, partnered, married, other). Then "
                "ask who else costs them money regularly (partner, children, parents they "
                "support, dating, close friends). For each person ask a nickname, relationship "
                "type, and approximate monthly cost. Also ask monthly social and dating spend. "
                "When you have relationship status and at least one roster entry or user says "
                "no one, end with: [MODULE_COMPLETE:roster]"
            ),
            "extraction_fn": _extract_roster,
        },
        "career": {
            "id": "career",
            "display_name": "Career",
            "ready_token": "[MODULE_COMPLETE:career]",
            "per_module_turn_cap": 6,
            "system_prompt_append": (
                "Collect current role title, industry, years of experience, satisfaction on "
                "a 1-5 scale, whether open to a move in the next 12 months, and target "
                "compensation if open to a move. For budget tier, skip target compensation. "
                "End with: [MODULE_COMPLETE:career]"
            ),
            "extraction_fn": _extract_career,
        },
        "milestones": {
            "id": "milestones",
            "display_name": "Milestones",
            "ready_token": "[MODULE_COMPLETE:milestones]",
            "per_module_turn_cap": 7,
            "system_prompt_append": (
                "Collect upcoming financial events in the next 12 months. For each event: "
                "the event name, the precise date in YYYY-MM-DD format (ask the user to "
                "confirm the exact date, not a month or season), estimated cost, and whether "
                "it recurs annually. If the user gives an approximate date, ask a follow-up "
                "to pin it down. When you have at least one milestone or the user says "
                "nothing upcoming, end with: [MODULE_COMPLETE:milestones]"
            ),
            "extraction_fn": _extract_milestones,
        },
    }


MODULES = _build_modules()


def _module_completion_flags(session: dict) -> dict[str, dict[str, bool]]:
    done = set(session.get("completed_modules") or [])
    skip = set(session.get("skipped_modules") or [])
    return {
        mid: {"completed": mid in done, "skipped": mid in skip} for mid in MODULE_ORDER
    }


@modular_onboarding_bp.route("/message", methods=["POST"])
@require_auth
@require_csrf
def post_message():
    uid = _ext_user_id()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    user = User.query.filter_by(user_id=uid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    user_message = data.get("user_message")
    current_module_id = data.get("current_module_id")
    if not isinstance(user_message, str) or not user_message.strip():
        return jsonify({"error": "user_message is required"}), 400
    if current_module_id not in MODULES:
        return jsonify({"error": "invalid current_module_id"}), 400

    session = _get_session(uid, user)
    session["current_module"] = current_module_id
    mod = MODULES[current_module_id]
    cap = mod["per_module_turn_cap"]
    mt = session.setdefault("module_turns", {})
    mod_turns = int(mt.get(current_module_id, 0))

    if int(session.get("turn_count", 0)) >= _TOTAL_TURN_CAP:
        _save_session(uid, session)
        _upsert_db_progress(user, session)
        return (
            jsonify(
                {
                    "phase": "hard_cap",
                    "assistant_message": (
                        "We have covered a lot. Let me save what we have so you can "
                        "finish on the dashboard."
                    ),
                    "extracted": None,
                }
            ),
            200,
        )

    if mod_turns >= cap:
        _save_session(uid, session)
        _upsert_db_progress(user, session)
        return (
            jsonify({"phase": "module_cap", "prompt_user_to_confirm": True}),
            200,
        )

    session.setdefault("messages", []).append(
        {
            "role": "user",
            "content": user_message.strip(),
            "module": current_module_id,
        }
    )

    system = (
        BASE_SYSTEM.strip()
        + "\n\n"
        + mod["system_prompt_append"].strip()
    )
    mod_msgs = [
        m
        for m in session["messages"]
        if m.get("module") == current_module_id
        and m.get("role") in ("user", "assistant")
        and m.get("content")
    ]
    api_messages = [
        {"role": m["role"], "content": m["content"]} for m in mod_msgs
    ]

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        system=system,
        messages=api_messages,
    )
    response_text = (message.content[0].text or "").strip()
    ready_tok = mod["ready_token"]

    if ready_tok in response_text:
        extracted = extract_module_data(response_text, current_module_id)
        stripped = _strip_ready_tokens(response_text)
        _save_session(uid, session)
        _upsert_db_progress(user, session)
        return (
            jsonify(
                {
                    "phase": "ready_to_commit",
                    "assistant_message": stripped,
                    "extracted": extracted,
                    "module": current_module_id,
                }
            ),
            200,
        )

    session["messages"].append(
        {
            "role": "assistant",
            "content": response_text,
            "module": current_module_id,
        }
    )
    session["turn_count"] = int(session.get("turn_count", 0)) + 1
    mt[current_module_id] = mod_turns + 1
    _save_session(uid, session)
    _upsert_db_progress(user, session)
    return (
        jsonify(
            {
                "phase": "chatting",
                "assistant_message": response_text,
            }
        ),
        200,
    )


@modular_onboarding_bp.route("/skip-module", methods=["POST"])
@require_auth
@require_csrf
def post_skip_module():
    uid = _ext_user_id()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    user = User.query.filter_by(user_id=uid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json(silent=True) or {}
    module_id = data.get("module_id")
    if module_id not in MODULES:
        return jsonify({"error": "invalid module_id"}), 400

    session = _get_session(uid, user)
    skipped = set(session.get("skipped_modules") or [])
    skipped.add(module_id)
    session["skipped_modules"] = list(skipped)
    _save_session(uid, session)
    _upsert_db_progress(user, session)

    nxt = _next_open_module(session)
    all_done = all(
        mid in (session.get("completed_modules") or [])
        or mid in (session.get("skipped_modules") or [])
        for mid in MODULE_ORDER
    )
    return jsonify({"next_module": nxt, "all_done": all_done}), 200


@modular_onboarding_bp.route("/revisit-module", methods=["POST"])
@require_auth
@require_csrf
def post_revisit_module():
    uid = _ext_user_id()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    user = User.query.filter_by(user_id=uid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json(silent=True) or {}
    module_id = data.get("module_id")
    if module_id not in MODULES:
        return jsonify({"error": "invalid module_id"}), 400

    session = _get_session(uid, user)
    session["current_module"] = module_id
    session.setdefault("module_turns", {})
    session["module_turns"][module_id] = 0
    cm = list(session.get("completed_modules") or [])
    sk = list(session.get("skipped_modules") or [])
    session["completed_modules"] = [x for x in cm if x != module_id]
    session["skipped_modules"] = [x for x in sk if x != module_id]
    _save_session(uid, session)
    _upsert_db_progress(user, session)
    return jsonify({"current_module": module_id}), 200


@modular_onboarding_bp.route("/status", methods=["GET"])
@require_auth
def get_status():
    uid = _ext_user_id()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    user = User.query.filter_by(user_id=uid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    session = _get_session(uid, user)
    row = _load_row(user)
    payload = {
        "session": session,
        "modules": _module_completion_flags(session),
        "db": row.to_dict() if row else None,
    }
    return jsonify(payload), 200


@modular_onboarding_bp.route("/reset", methods=["DELETE"])
@require_auth
@require_csrf
def delete_reset():
    uid = _ext_user_id()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    user = User.query.filter_by(user_id=uid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    _redis.delete(_session_key(uid))
    _delete_db_progress(user)
    return jsonify({"reset": True}), 200


@modular_onboarding_bp.route("/commit-field", methods=["POST"])
@require_auth
@require_csrf
@limiter.limit("120 per minute")
def post_commit_field():
    uid = _ext_user_id()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    user = User.query.filter_by(user_id=uid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    payload = request.get_json(silent=True) or {}
    module_id = payload.get("module_id")
    field_path = payload.get("field_path")
    value = payload.get("value")
    if not isinstance(module_id, str) or module_id not in MODULE_ORDER:
        return jsonify({"error": "unknown_module", "module_id": module_id}), 400
    if not isinstance(field_path, str) or not field_path.strip():
        return jsonify({"error": "malformed_body", "reason": "field_path required"}), 400
    session = _get_session(uid, user)
    body, code = run_commit_field(
        user=user,
        uid=uid,
        session=session,
        module_id=module_id,
        field_path=field_path.strip(),
        value=value,
        save_session=_save_session,
        load_row=_load_row,
    )
    return jsonify(body), code


@modular_onboarding_bp.route("/commit-module", methods=["POST"])
@require_auth
@require_csrf
@limiter.limit("20 per minute")
def post_commit_module():
    uid = _ext_user_id()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    user = User.query.filter_by(user_id=uid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    payload = request.get_json(silent=True) or {}
    module_id = payload.get("module_id")
    data = payload.get("data")
    if not isinstance(module_id, str) or module_id not in MODULE_ORDER:
        return jsonify({"error": "unknown_module", "module_id": module_id}), 400
    if not isinstance(data, dict):
        return jsonify({"error": "malformed_body", "reason": "data must be an object"}), 400
    session = _get_session(uid, user)
    body, code = run_commit_module(
        user=user,
        uid=uid,
        module_id=module_id,
        data=data,
        session=session,
        save_session=_save_session,
        load_row=_load_row,
        upsert_db_progress=_upsert_db_progress,
    )
    return jsonify(body), code
