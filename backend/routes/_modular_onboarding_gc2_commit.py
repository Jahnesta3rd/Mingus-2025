"""
GC2 commit helpers — imported by modular_onboarding.py (keeps GC1 routes readable).

This module is not a blueprint; it exposes callables bound at import time.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from uuid import UUID

from loguru import logger as loguru_logger
from sqlalchemy import asc

from backend.api.profile_endpoints import get_db_connection
from backend.constants.onboarding import CATEGORY_KEY_IDS, MODULE_ORDER
from backend.models.career_profile import CareerProfile
from backend.models.daily_outlook import RelationshipStatus, UserRelationshipStatus
from backend.models.database import db
from backend.models.financial_setup import RecurringExpense, UserIncome
from backend.models.housing_profile import HousingProfile
from backend.models.onboarding_progress import OnboardingProgress
from backend.models.user_models import User
from backend.models.vehicle_models import Vehicle
from backend.models.vibe_tracker import VibeTrackedPerson

def _to_decimal_amount(v: Any) -> Decimal | None:
    """Same semantics as backend.api.financial_setup_api._to_decimal_amount (local copy to avoid heavy imports)."""
    try:
        if isinstance(v, bool):
            return None
        return Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError):
        return None


_MODULAR_EXPENSE_SOURCE = "modular_onboarding"
_PRIMARY_INCOME_SOURCE = "Primary take-home"
_SECONDARY_INCOME_SOURCE = "Secondary income"
_SESSION_HAS_SECONDARY = "modular_gc2_has_secondary_committed"
_PENDING_VEH_PK = "_gc2_pending_vehicle_pk"
_PENDING_PERSON_UUID = "_gc2_pending_person_uuid"
_PENDING_EVT_IDX = "_gc2_pending_custom_event_idx"

# Guided Canvas roster: allowed RelationshipStatus member NAMES (DB / enum keys).
# GC1 emits lowercase values; validation uppercases then checks this set.
_GC_REL_ALLOWED_STATUS_NAMES: frozenset[str] = frozenset(
    {"SINGLE", "DATING", "PARTNERED", "MARRIED", "OTHER"}
)

_RE_VEH = re.compile(r"^vehicles\[(?P<idx>\d+|new)\]\.(?P<fld>[a-z_]+)$")
_RE_PPL = re.compile(r"^people\[(?P<idx>\d+|new)\]\.(?P<fld>[a-z_]+)$")
_RE_CAT = re.compile(r"^categories\[(?P<cat>[a-z_]+)\]\.amount$")
_RE_EVT = re.compile(r"^events\[(?P<idx>\d+|new)\]\.(?P<fld>name|date|cost)$")


def _utcnow() -> datetime:
    return datetime.utcnow()


def _iso(ts: datetime | None) -> str:
    if ts is None:
        return _utcnow().replace(tzinfo=timezone.utc).isoformat()
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc).isoformat()
    return ts.isoformat()


def _coerce_bool(val: Any) -> bool | None:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)) and val in (0, 1):
        return bool(val)
    if isinstance(val, str):
        s = val.strip().lower()
        if s in ("true", "1", "yes"):
            return True
        if s in ("false", "0", "no"):
            return False
    return None


def _validation_failed(
    field_path: str, reason: str, expected: str, got: Any
) -> tuple[dict, int]:
    return (
        {
            "error": "validation_failed",
            "field_path": field_path,
            "reason": reason,
            "expected": expected,
            "got": got,
        },
        400,
    )


def _unknown_field(field_path: str) -> tuple[dict, int]:
    return ({"error": "unknown_field", "field_path": field_path}, 400)


def _merge_important_dates_custom_events_modular(email: str, new_events: list[dict]) -> None:
    """Duplicate of conversation_onboarding._merge_important_dates_custom_events (see that file)."""
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
                date_iso = datetime.now(timezone.utc).date().isoformat()
            try:
                cval = float(cost) if cost is not None else 0.0
            except (TypeError, ValueError):
                cval = 0.0
            customs.append({"name": name, "date": date_iso, "cost": cval})
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


def _load_important_dates(email: str) -> dict:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT important_dates FROM user_profiles WHERE email = %s",
            (email,),
        )
        row = cursor.fetchone()
        if not row or not row.get("important_dates"):
            return {}
        raw = row["important_dates"]
        prev = json.loads(raw) if isinstance(raw, str) else raw
        return prev if isinstance(prev, dict) else {}
    finally:
        conn.close()


def _save_important_dates(email: str, prev: dict) -> None:
    imp_json = json.dumps(prev)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
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


def _custom_events_list(email: str) -> list:
    prev = _load_important_dates(email)
    customs = prev.get("customEvents") or prev.get("custom_events") or []
    return customs if isinstance(customs, list) else []


def _float_eq(a: Any, b: Any) -> bool:
    try:
        return abs(float(a) - float(b)) < 1e-6
    except (TypeError, ValueError):
        return False


def _decimal_eq(a: Any, b: Any) -> bool:
    try:
        return abs(Decimal(str(a)) - Decimal(str(b))) < Decimal("0.01")
    except Exception:
        return False


def _validate_and_cast(field_path: str, value: Any) -> tuple[Any | None, tuple[dict, int] | None]:
    cy = datetime.utcnow().year
    if field_path in ("monthly_takehome",):
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "number", value)
        if v < 0 or v > 500000:
            return None, _validation_failed(field_path, "out_of_range", "[0, 500000]", value)
        return v, None
    if field_path.endswith("monthly_cost") and "people[" in field_path:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "number", value)
        if v < 0 or v > 10000:
            return None, _validation_failed(field_path, "out_of_range", "[0, 10000]", value)
        return v, None
    if field_path in ("housing_type",):
        if not isinstance(value, str) or value.strip().lower() not in ("rent", "own"):
            return None, _validation_failed(
                field_path, "type_mismatch", "{'rent','own'}", value
            )
        return value.strip().lower(), None
    if field_path in ("monthly_cost",) and not field_path.startswith("people"):
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "number", value)
        if v < 0 or v > 50000:
            return None, _validation_failed(field_path, "out_of_range", "[0, 50000]", value)
        return v, None
    if field_path == "split_share_pct":
        if value is None or value == "":
            return None, None  # nullable
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "number or null", value)
        if v < 0 or v > 100:
            return None, _validation_failed(field_path, "out_of_range", "[0, 100]", value)
        return v, None
    if field_path in ("has_buy_goal", "has_secondary", "open_to_move"):
        b = _coerce_bool(value)
        if b is None:
            return None, _validation_failed(field_path, "type_mismatch", "boolean", value)
        return b, None
    if field_path == "target_price":
        if value is None or value == "":
            return None, None
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "number or null", value)
        if v < 0 or v > 10_000_000:
            return None, _validation_failed(field_path, "out_of_range", "[0, 10000000]", value)
        return v, None
    if field_path == "target_timeline_months":
        if value is None or value == "":
            return None, None
        try:
            v = int(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "int or null", value)
        if v < 0 or v > 60:
            return None, _validation_failed(field_path, "out_of_range", "[0, 60]", value)
        return v, None
    if field_path == "vehicle_count":
        if value is None or value == "":
            return None, _validation_failed(field_path, "type_mismatch", "int", value)
        if isinstance(value, bool):
            return None, _validation_failed(field_path, "type_mismatch", "int", value)
        if isinstance(value, float):
            if not value.is_integer():
                return None, _validation_failed(field_path, "type_mismatch", "int", value)
            v = int(value)
        elif isinstance(value, int):
            v = value
        elif isinstance(value, str):
            s = value.strip()
            if not s:
                return None, _validation_failed(field_path, "type_mismatch", "int", value)
            try:
                v = int(s)
            except ValueError:
                return None, _validation_failed(field_path, "type_mismatch", "int", value)
        else:
            try:
                v = int(value)
            except (TypeError, ValueError):
                return None, _validation_failed(field_path, "type_mismatch", "int", value)
        if v < 0 or v > 5:
            return None, _validation_failed(field_path, "out_of_range", "[0, 5]", value)
        return v, None
    if field_path == "zip_or_city":
        if not isinstance(value, str):
            return None, _validation_failed(field_path, "type_mismatch", "non-empty string max 100", value)
        s = value.strip()
        if not s:
            return None, _validation_failed(field_path, "empty_string", "non-empty string", value)
        if len(s) > 100:
            return None, _validation_failed(field_path, "string_too_long", "max 100", value)
        return s, None
    if field_path == "pay_frequency":
        if not isinstance(value, str):
            return None, _validation_failed(field_path, "type_mismatch", "enum string", value)
        v = value.strip().lower()
        if v not in ("weekly", "biweekly", "semimonthly", "monthly"):
            return None, _validation_failed(
                field_path, "type_mismatch", "weekly|biweekly|semimonthly|monthly", value
            )
        return v, None
    if field_path == "secondary_amount":
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "number", value)
        if v < 0 or v > 500000:
            return None, _validation_failed(field_path, "out_of_range", "[0, 500000]", value)
        return v, None
    if field_path == "bonus_cadence":
        return value, None
    if field_path.startswith("categories[") and field_path.endswith("].amount"):
        m = _RE_CAT.match(field_path)
        if not m:
            return None, _unknown_field(field_path)
        cat = m.group("cat")
        if cat not in CATEGORY_KEY_IDS:
            return None, ({"error": "invalid_category", "category": cat}, 400)
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "number", value)
        if v < 0 or v > 100000:
            return None, _validation_failed(field_path, "out_of_range", "[0, 100000]", value)
        return v, None
    if field_path == "relationship_status":
        if not isinstance(value, str):
            return None, _validation_failed(field_path, "type_mismatch", "string enum", value)
        status_name = value.strip().upper()
        if not status_name:
            return None, _validation_failed(
                field_path, "empty_string", "non-empty relationship_status", value
            )
        expected = ",".join(sorted(_GC_REL_ALLOWED_STATUS_NAMES))
        if status_name not in RelationshipStatus.__members__:
            return None, _validation_failed(
                field_path, "invalid_enum", expected, value
            )
        if status_name not in _GC_REL_ALLOWED_STATUS_NAMES:
            return None, _validation_failed(
                field_path, "invalid_enum", expected, value
            )
        return RelationshipStatus[status_name], None
    if field_path == "monthly_social_spend":
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "number", value)
        if v < 0 or v > 10000:
            return None, _validation_failed(field_path, "out_of_range", "[0, 10000]", value)
        return v, None
    if field_path in ("current_role", "industry"):
        if not isinstance(value, str):
            return None, _validation_failed(field_path, "type_mismatch", "string max 100", value)
        s = value.strip()
        if not s:
            return None, _validation_failed(field_path, "empty_string", "non-empty", value)
        if len(s) > 100:
            return None, _validation_failed(field_path, "string_too_long", "max 100", value)
        return s, None
    if field_path == "years_experience":
        if value is None or value == "":
            return None, None
        try:
            v = int(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "int", value)
        if v < 0 or v > 60:
            return None, _validation_failed(field_path, "out_of_range", "[0, 60]", value)
        return v, None
    if field_path == "satisfaction":
        if value is None or value == "":
            return None, None
        try:
            v = int(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "int", value)
        if v < 1 or v > 5:
            return None, _validation_failed(field_path, "out_of_range", "[1, 5]", value)
        return v, None
    if field_path == "target_comp":
        if value is None or value == "":
            return None, None
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None, _validation_failed(field_path, "type_mismatch", "number", value)
        if v < 0 or v > 5_000_000:
            return None, _validation_failed(field_path, "out_of_range", "[0, 5000000]", value)
        return v, None
    m = _RE_VEH.match(field_path)
    if m:
        fld = m.group("fld")
        if fld == "year":
            try:
                v = int(value)
            except (TypeError, ValueError):
                return None, _validation_failed(field_path, "type_mismatch", "int", value)
            if v < 1950 or v > cy + 1:
                return None, _validation_failed(
                    field_path, "out_of_range", f"[1950, {cy + 1}]", value
                )
            return v, None
        if fld in ("make", "model"):
            if not isinstance(value, str) or not value.strip():
                return None, _validation_failed(field_path, "empty_string", "non-empty", value)
            if len(value.strip()) > 100:
                return None, _validation_failed(field_path, "string_too_long", "max 100", value)
            return value.strip(), None
        if fld == "monthly_fuel":
            try:
                v = float(value)
            except (TypeError, ValueError):
                return None, _validation_failed(field_path, "type_mismatch", "number", value)
            if v < 0 or v > 5000:
                return None, _validation_failed(field_path, "out_of_range", "[0, 5000]", value)
            return v, None
        if fld == "monthly_payment":
            if value is None or value == "":
                return None, None
            try:
                v = float(value)
            except (TypeError, ValueError):
                return None, _validation_failed(field_path, "type_mismatch", "number", value)
            if v < 0 or v > 10000:
                return None, _validation_failed(field_path, "out_of_range", "[0, 10000]", value)
            return v, None
        if fld == "recent_maintenance":
            b = _coerce_bool(value)
            if b is None:
                return None, _validation_failed(field_path, "type_mismatch", "boolean", value)
            return b, None
        return None, _unknown_field(field_path)
    m = _RE_PPL.match(field_path)
    if m:
        fld = m.group("fld")
        if fld == "nickname":
            if not isinstance(value, str):
                return None, _validation_failed(field_path, "type_mismatch", "string", value)
            s = value.strip()
            if not s:
                return None, _validation_failed(field_path, "empty_string", "non-empty", value)
            if len(s) > 30:
                return None, _validation_failed(field_path, "string_too_long", "max 30", value)
            return s, None
        if fld == "relationship_type":
            if not isinstance(value, str):
                return None, _validation_failed(field_path, "type_mismatch", "string", value)
            s = value.strip()
            if not s:
                return None, _validation_failed(field_path, "empty_string", "non-empty", value)
            if len(s) > 50:
                return None, _validation_failed(field_path, "string_too_long", "max 50", value)
            return s, None
        if fld == "monthly_cost":
            try:
                v = float(value)
            except (TypeError, ValueError):
                return None, _validation_failed(field_path, "type_mismatch", "number", value)
            if v < 0 or v > 10000:
                return None, _validation_failed(field_path, "out_of_range", "[0, 10000]", value)
            return v, None
        return None, _unknown_field(field_path)
    m = _RE_EVT.match(field_path)
    if m:
        fld = m.group("fld")
        if fld == "name":
            if not isinstance(value, str):
                return None, _validation_failed(field_path, "type_mismatch", "string", value)
            s = value.strip()
            if not s:
                return None, _validation_failed(field_path, "empty_string", "non-empty", value)
            if len(s) > 100:
                return None, _validation_failed(field_path, "string_too_long", "max 100", value)
            return s, None
        if fld == "date":
            if not isinstance(value, str):
                return None, _validation_failed(field_path, "type_mismatch", "YYYY-MM-DD string", value)
            s = value.strip()
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", s):
                return None, _validation_failed(field_path, "bad_date_format", "YYYY-MM-DD", value)
            try:
                d = date.fromisoformat(s)
            except ValueError:
                return None, _validation_failed(field_path, "bad_date_format", "YYYY-MM-DD", value)
            if d < date.today():
                return None, _validation_failed(field_path, "date_in_past", "today or future", value)
            return s, None
        if fld == "cost":
            try:
                v = float(value)
            except (TypeError, ValueError):
                return None, _validation_failed(field_path, "type_mismatch", "number", value)
            if v < 0 or v > 1_000_000:
                return None, _validation_failed(field_path, "out_of_range", "[0, 1000000]", value)
            return v, None
        return None, _unknown_field(field_path)
    return None, _unknown_field(field_path)


def _ordered_vehicles_query(user_id: int):
    return (
        Vehicle.query.filter_by(user_id=user_id)
        .order_by(asc(Vehicle.created_date))
        .all()
    )


def _ordered_people_query(user_id: int):
    return (
        VibeTrackedPerson.query.filter_by(user_id=user_id, is_archived=False)
        .order_by(asc(VibeTrackedPerson.created_at))
        .all()
    )


def _ensure_vehicle_stub(user: User, session: dict, save_session: Callable[[str, dict], None], uid: str) -> Vehicle:
    pk = session.get(_PENDING_VEH_PK)
    if pk:
        v = db.session.get(Vehicle, pk)
        if v and v.user_id == user.id:
            return v
    stub = Vehicle(
        user_id=user.id,
        vin=None,
        year=datetime.utcnow().year,
        make="unknown",
        model="unknown",
        trim=None,
        current_mileage=0,
        monthly_miles=0,
        user_zipcode=None,
        assigned_msa=None,
        notes=None,
        estimated_annual_cost=None,
    )
    db.session.add(stub)
    db.session.flush()
    session[_PENDING_VEH_PK] = stub.id
    try:
        save_session(uid, session)
    except Exception as e:
        loguru_logger.warning("GC2 save_session after vehicle stub: {}", e)
    return stub


def _resolve_vehicle(
    user: User, session: dict, idx_token: str, save_session: Callable[[str, dict], None], uid: str
) -> tuple[Vehicle | None, str | None]:
    rows = _ordered_vehicles_query(user.id)
    if idx_token == "new":
        return _ensure_vehicle_stub(user, session, save_session, uid), None
    try:
        i = int(idx_token)
    except ValueError:
        return None, "bad_index"
    if i < 0 or i >= len(rows):
        return None, "index_out_of_range"
    session.pop(_PENDING_VEH_PK, None)
    try:
        save_session(uid, session)
    except Exception as e:
        loguru_logger.warning("GC2 save_session clear vehicle pending: {}", e)
    return rows[i], None


def _resolve_person(
    user: User, session: dict, idx_token: str, save_session: Callable[[str, dict], None], uid: str
) -> tuple[VibeTrackedPerson | None, str | None]:
    if idx_token == "new":
        pid = session.get(_PENDING_PERSON_UUID)
        if pid:
            try:
                u = UUID(str(pid))
            except ValueError:
                u = None
            if u:
                p = db.session.get(VibeTrackedPerson, u)
                if p and p.user_id == user.id:
                    return p, None
        return None, "precondition_failed"
    try:
        i = int(idx_token)
    except ValueError:
        return None, "bad_index"
    rows = _ordered_people_query(user.id)
    if i < 0 or i >= len(rows):
        return None, "index_out_of_range"
    session.pop(_PENDING_PERSON_UUID, None)
    try:
        save_session(uid, session)
    except Exception as e:
        loguru_logger.warning("GC2 save_session clear person pending: {}", e)
    return rows[i], None


def _touch_progress_row(user: User, load_row: Callable[[User], OnboardingProgress | None]) -> None:
    row = load_row(user)
    now = _utcnow()
    if not row:
        row = OnboardingProgress(
            user_id=user.id,
            completed_modules=[],
            skipped_modules=[],
            current_module=MODULE_ORDER[0],
            started_at=now,
            last_activity_at=now,
        )
        db.session.add(row)
    else:
        row.last_activity_at = now


def _apply_commit_field(
    *,
    user: User,
    uid: str,
    session: dict,
    field_path: str,
    cast_value: Any,
    save_session: Callable[[str, dict], None],
    load_row: Callable[[User], OnboardingProgress | None],
) -> tuple[dict, int]:
    email = (user.email or "").strip().lower()
    committed_at_existing: datetime | None = None
    changed = True
    assigned_index: int | None = None

    if field_path == "bonus_cadence":
        _touch_progress_row(user, load_row)
        db.session.commit()
        return (
            {
                    "ok": True,
                    "changed": False,
                    "note": "not persisted",
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": cast_value,
                },
            200,
        )

    if field_path == "has_secondary":
        assert isinstance(cast_value, bool)
        session[_SESSION_HAS_SECONDARY] = cast_value
        try:
            save_session(uid, session)
        except Exception as e:
            loguru_logger.warning("GC2 redis has_secondary: {}", e)
        if not cast_value:
            for row in UserIncome.query.filter_by(user_id=user.id).all():
                if row.source_name == _SECONDARY_INCOME_SOURCE and row.is_active:
                    row.is_active = False
        _touch_progress_row(user, load_row)
        db.session.commit()
        return (
            {
                    "ok": True,
                    "changed": True,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": cast_value,
                },
            200,
        )

    if field_path == "monthly_takehome":
        dec = _to_decimal_amount(cast_value)
        if dec is None:
            return (
                {
                    "error": "validation_failed",
                    "field_path": field_path,
                    "reason": "type_mismatch",
                    "expected": "number",
                    "got": cast_value,
                },
                400,
            )
        row = None
        for r in UserIncome.query.filter_by(user_id=user.id, is_active=True).all():
            if r.source_name == _PRIMARY_INCOME_SOURCE:
                row = r
                break
        if row is None:
            row = UserIncome(
                user_id=user.id,
                source_name=_PRIMARY_INCOME_SOURCE,
                amount=dec,
                frequency="monthly",
                pay_day=None,
                is_active=True,
            )
            db.session.add(row)
            changed = True
        else:
            changed = not _decimal_eq(row.amount, dec)
            row.amount = dec
        committed_at_existing = row.created_at if row else None
        _touch_progress_row(user, load_row)
        db.session.commit()
        return (
            {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow() if changed else (committed_at_existing or _utcnow())),
                    "field_path": field_path,
                    "value_stored": float(dec),
                },
            200,
        )

    if field_path == "pay_frequency":
        freq = str(cast_value)
        row = None
        for r in UserIncome.query.filter_by(user_id=user.id, is_active=True).all():
            if r.source_name == _PRIMARY_INCOME_SOURCE:
                row = r
                break
        if row is None:
            return (
                {
                    "error": "precondition_failed",
                    "reason": "primary income row missing",
                },
                400,
            )
        changed = (row.frequency or "").lower() != freq.lower()
        row.frequency = freq
        _touch_progress_row(user, load_row)
        db.session.commit()
        return (
            {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": freq,
                },
            200,
        )

    if field_path == "secondary_amount":
        dec = _to_decimal_amount(cast_value)
        declared = session.get(_SESSION_HAS_SECONDARY) is True
        if not declared:
            has_row = any(
                r.source_name == _SECONDARY_INCOME_SOURCE and r.is_active
                for r in UserIncome.query.filter_by(user_id=user.id).all()
            )
            if not has_row:
                return (
                    {
                        "error": "precondition_failed",
                        "reason": "secondary income not declared",
                    },
                    400,
                )
        row = None
        for r in UserIncome.query.filter_by(user_id=user.id, is_active=True).all():
            if r.source_name == _SECONDARY_INCOME_SOURCE:
                row = r
                break
        if row is None:
            row = UserIncome(
                user_id=user.id,
                source_name=_SECONDARY_INCOME_SOURCE,
                amount=dec or Decimal(0),
                frequency="monthly",
                pay_day=None,
                is_active=True,
            )
            db.session.add(row)
            changed = True
        else:
            changed = not _decimal_eq(row.amount, dec)
            row.amount = dec or Decimal(0)
        _touch_progress_row(user, load_row)
        db.session.commit()
        return (
            {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": float(dec or 0),
                },
            200,
        )

    if field_path in (
        "housing_type",
        "monthly_cost",
        "zip_or_city",
        "split_share_pct",
        "has_buy_goal",
        "target_price",
        "target_timeline_months",
    ):
        hp = HousingProfile.query.filter_by(user_id=user.id).first()
        if not hp:
            hp = HousingProfile(user_id=user.id, housing_type="rent", monthly_cost=0.0, zip_or_city="")
            db.session.add(hp)
            db.session.flush()
        attr = field_path
        cur = getattr(hp, attr)
        if attr == "monthly_cost":
            newv = float(cast_value)
            changed = not _float_eq(cur, newv)
            hp.monthly_cost = newv
        elif attr == "housing_type":
            changed = (cur or "").lower() != cast_value
            hp.housing_type = cast_value
        elif attr == "zip_or_city":
            changed = (cur or "") != cast_value
            hp.zip_or_city = cast_value
        elif attr == "split_share_pct":
            changed = cur != cast_value
            hp.split_share_pct = cast_value
        elif attr == "has_buy_goal":
            changed = bool(cur) != bool(cast_value)
            hp.has_buy_goal = bool(cast_value)
        elif attr == "target_price":
            newv = float(cast_value) if cast_value is not None else None
            changed = not _float_eq(cur, newv) if newv is not None else cur is not None
            hp.target_price = newv
        elif attr == "target_timeline_months":
            newv = cast_value if cast_value is not None else None
            changed = cur != newv
            hp.target_timeline_months = newv
        else:
            changed = False
        _touch_progress_row(user, load_row)
        db.session.commit()
        return (
            {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": cast_value,
                },
            200,
        )

    m = _RE_CAT.match(field_path)
    if m:
        cat = m.group("cat")
        amt = _to_decimal_amount(cast_value)
        if amt is None:
            amt = Decimal(0)
        name = cat.replace("_", " ").title()
        row = RecurringExpense.query.filter_by(
            user_id=user.id, category=cat, source=_MODULAR_EXPENSE_SOURCE
        ).first()
        if row is None:
            row = RecurringExpense(
                user_id=user.id,
                name=name,
                amount=amt,
                category=cat,
                due_day=None,
                frequency="monthly",
                is_active=True,
                source=_MODULAR_EXPENSE_SOURCE,
            )
            db.session.add(row)
            changed = True
        else:
            changed = not _decimal_eq(row.amount, amt)
            row.amount = amt
            row.name = name
            row.is_active = True
        _touch_progress_row(user, load_row)
        db.session.commit()
        return (
            {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": float(amt),
                },
            200,
        )

    if field_path == "relationship_status":
        assert isinstance(cast_value, RelationshipStatus)
        enum_v = cast_value
        row = UserRelationshipStatus.query.filter_by(user_id=user.id).first()
        if row is None:
            row = UserRelationshipStatus(
                user_id=user.id,
                status=enum_v,
                satisfaction_score=5,
                financial_impact_score=5,
            )
            db.session.add(row)
            changed = True
        else:
            changed = row.status != enum_v
            row.status = enum_v
        _touch_progress_row(user, load_row)
        db.session.commit()
        return (
            {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": enum_v.value,
                },
            200,
        )

    if field_path == "monthly_social_spend":
        newv = float(cast_value)
        cur = user.social_spend_monthly
        changed = not _float_eq(cur, newv) if cur is not None else True
        user.social_spend_monthly = newv
        _touch_progress_row(user, load_row)
        db.session.commit()
        return (
            {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": newv,
                },
            200,
        )

    if field_path in (
        "current_role",
        "industry",
        "years_experience",
        "satisfaction",
        "open_to_move",
        "target_comp",
    ):
        cp = CareerProfile.query.filter_by(user_id=user.id).first()
        if not cp:
            cp = CareerProfile(user_id=user.id)
            db.session.add(cp)
            db.session.flush()
        cur = getattr(cp, field_path)
        if field_path in ("current_role", "industry"):
            newv = cast_value
            changed = (cur or "") != (newv or "")
            setattr(cp, field_path, newv)
        elif field_path == "open_to_move":
            newv = bool(cast_value)
            changed = bool(cur) != newv
            setattr(cp, field_path, newv)
        elif field_path in ("years_experience", "satisfaction"):
            newv = cast_value
            changed = cur != newv
            setattr(cp, field_path, newv)
        elif field_path == "target_comp":
            newv = float(cast_value) if cast_value is not None else None
            changed = not _float_eq(cur, newv) if newv is not None else cur is not None
            setattr(cp, field_path, newv)
        else:
            newv = cast_value
            changed = cur != newv
            setattr(cp, field_path, newv)
        _touch_progress_row(user, load_row)
        db.session.commit()
        return (
            {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": cast_value,
                },
            200,
        )

    m = _RE_VEH.match(field_path)
    if m:
        idx_tok = m.group("idx")
        fld = m.group("fld")
        veh, err = _resolve_vehicle(user, session, idx_tok, save_session, uid)
        if err:
            return ({"error": "index_out_of_range", "field_path": field_path}, 400)
        assert veh is not None
        if fld in ("make", "model"):
            newv = cast_value
            cur = getattr(veh, fld)
            changed = (cur or "") != (newv or "")
            setattr(veh, fld, newv)
        elif fld == "year":
            changed = int(veh.year) != int(cast_value)
            veh.year = int(cast_value)
        elif fld == "monthly_fuel":
            new_dec = _to_decimal_amount(cast_value) or Decimal(0)
            cur_dec = veh.monthly_fuel_cost
            cur_f = float(cur_dec) if cur_dec is not None else 0.0
            changed = not _float_eq(cur_f, float(new_dec))
            veh.monthly_fuel_cost = new_dec
        elif fld == "monthly_payment":
            new_dec = _to_decimal_amount(cast_value) if cast_value is not None else None
            cur_dec = veh.monthly_payment
            if cur_dec is not None and new_dec is not None:
                changed = not _decimal_eq(cur_dec, new_dec)
            else:
                changed = cur_dec != new_dec
            veh.monthly_payment = new_dec
        elif fld == "recent_maintenance":
            newv = bool(cast_value)
            cur = veh.recent_maintenance
            cur_norm = False if cur is None else bool(cur)
            changed = cur_norm != newv
            veh.recent_maintenance = newv
        else:
            return ({"error": "unknown_field", "field_path": field_path}, 400)
        _touch_progress_row(user, load_row)
        db.session.commit()
        rows = _ordered_vehicles_query(user.id)
        assigned_index = next((i for i, r in enumerate(rows) if r.id == veh.id), None)
        return (
            {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": cast_value,
                    **({"assigned_index": assigned_index} if idx_tok == "new" else {}),
                },
            200,
        )

    m = _RE_PPL.match(field_path)
    if m:
        idx_tok = m.group("idx")
        fld = m.group("fld")
        if idx_tok == "new" and fld == "nickname":
            p = VibeTrackedPerson(
                user_id=user.id,
                nickname=str(cast_value),
                relationship_type=None,
                estimated_monthly_cost=None,
                assessment_count=0,
                is_archived=False,
            )
            db.session.add(p)
            db.session.flush()
            session[_PENDING_PERSON_UUID] = str(p.id)
            try:
                save_session(uid, session)
            except Exception as e:
                loguru_logger.warning("GC2 pending person save: {}", e)
            _touch_progress_row(user, load_row)
            db.session.commit()
            rows = _ordered_people_query(user.id)
            assigned_index = len(rows) - 1
            return (
                {
                    "ok": True,
                    "changed": True,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": cast_value,
                    "assigned_index": assigned_index,
                },
                200,
            )
        pers, err = _resolve_person(user, session, idx_tok, save_session, uid)
        if err == "precondition_failed":
            return (
                {
                    "error": "precondition_failed",
                    "reason": "people[new] requires nickname committed first",
                },
                400,
            )
        if err or pers is None:
            return ({"error": "index_out_of_range", "field_path": field_path}, 400)
        if fld == "nickname":
            newv = str(cast_value)
            changed = pers.nickname != newv
            pers.nickname = newv
        elif fld == "relationship_type":
            newv = str(cast_value)
            changed = (pers.relationship_type or "") != newv
            pers.relationship_type = newv
        elif fld == "monthly_cost":
            newv = float(cast_value)
            changed = not _float_eq(pers.estimated_monthly_cost, newv)
            pers.estimated_monthly_cost = newv
        else:
            return ({"error": "unknown_field", "field_path": field_path}, 400)
        _touch_progress_row(user, load_row)
        db.session.commit()
        rows = _ordered_people_query(user.id)
        assigned_index = next((i for i, r in enumerate(rows) if r.id == pers.id), None)
        return (
            {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": cast_value,
                    **({"assigned_index": assigned_index} if idx_tok == "new" else {}),
                },
            200,
        )

    m = _RE_EVT.match(field_path)
    if m:
        if not email:
            return ({"error": "validation_failed", "reason": "user email missing"}, 400)
        idx_tok = m.group("idx")
        fld = m.group("fld")
        if idx_tok == "new":
            pi = session.get(_PENDING_EVT_IDX)
            customs_l = _custom_events_list(email)
            if pi is None or not isinstance(pi, int) or pi >= len(customs_l):
                stub = {"name": "Event", "date": date.today().isoformat(), "cost": 0.0}
                if fld == "name":
                    stub["name"] = cast_value
                elif fld == "date":
                    stub["date"] = cast_value
                elif fld == "cost":
                    stub["cost"] = float(cast_value)
                _merge_important_dates_custom_events_modular(email, [stub])
                customs2 = _custom_events_list(email)
                session[_PENDING_EVT_IDX] = len(customs2) - 1
                try:
                    save_session(uid, session)
                except Exception as e:
                    loguru_logger.warning("GC2 pending event save: {}", e)
                _touch_progress_row(user, load_row)
                db.session.commit()
                return (
                    {
                        "ok": True,
                        "changed": True,
                        "committed_at": _iso(_utcnow()),
                        "field_path": field_path,
                        "value_stored": cast_value,
                        "assigned_index": len(customs2) - 1,
                    },
                    200,
                )
            prev = _load_important_dates(email)
            customs_mut = list(
                prev.get("customEvents") or prev.get("custom_events") or []
            )
            if pi < 0 or pi >= len(customs_mut):
                return ({"error": "index_out_of_range", "field_path": field_path}, 400)
            ev = dict(customs_mut[pi]) if isinstance(customs_mut[pi], dict) else {}
            old = ev.get(fld)
            ev[fld] = float(cast_value) if fld == "cost" else cast_value
            ev.pop("recurring", None)
            customs_mut[pi] = {
                "name": ev.get("name") or "Event",
                "date": ev.get("date") or date.today().isoformat(),
                "cost": float(ev.get("cost") or 0),
            }
            changed = old != customs_mut[pi].get(fld)
            prev["customEvents"] = customs_mut
            _save_important_dates(email, prev)
            _touch_progress_row(user, load_row)
            db.session.commit()
            return (
                {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": cast_value,
                    "assigned_index": pi,
                },
                200,
            )
        try:
            i = int(idx_tok)
        except ValueError:
            return ({"error": "unknown_field", "field_path": field_path}, 400)
        session.pop(_PENDING_EVT_IDX, None)
        try:
            save_session(uid, session)
        except Exception as e:
            loguru_logger.warning("GC2 clear pending event: {}", e)
        prev = _load_important_dates(email)
        customs_num = list(
            prev.get("customEvents") or prev.get("custom_events") or []
        )
        if i < 0 or i >= len(customs_num):
            return ({"error": "index_out_of_range", "field_path": field_path}, 400)
        ev = dict(customs_num[i]) if isinstance(customs_num[i], dict) else {}
        old = ev.get(fld)
        ev[fld] = float(cast_value) if fld == "cost" else cast_value
        ev.pop("recurring", None)
        customs_num[i] = {
            "name": ev.get("name") or "Event",
            "date": ev.get("date") or date.today().isoformat(),
            "cost": float(ev.get("cost") or 0),
        }
        changed = old != customs_num[i].get(fld)
        prev["customEvents"] = customs_num
        _save_important_dates(email, prev)
        _touch_progress_row(user, load_row)
        db.session.commit()
        return (
            {
                    "ok": True,
                    "changed": changed,
                    "committed_at": _iso(_utcnow()),
                    "field_path": field_path,
                    "value_stored": cast_value,
                },
            200,
        )

    return ({"error": "unknown_field", "field_path": field_path}, 400)


def flatten_module_data(module_id: str, data: dict) -> list[tuple[str, Any]]:
    pairs: list[tuple[str, Any]] = []
    if not isinstance(data, dict):
        return pairs
    if module_id == "income":
        for k in (
            "monthly_takehome",
            "pay_frequency",
            "has_secondary",
            "secondary_amount",
            "bonus_cadence",
        ):
            if k in data:
                pairs.append((k, data[k]))
    elif module_id == "housing":
        for k in (
            "housing_type",
            "monthly_cost",
            "zip_or_city",
            "split_share_pct",
            "has_buy_goal",
            "target_price",
            "target_timeline_months",
        ):
            if k in data:
                pairs.append((k, data[k]))
    elif module_id == "vehicle":
        for i, v in enumerate(data.get("vehicles") or []):
            if isinstance(v, dict):
                for sk, sv in v.items():
                    pairs.append((f"vehicles[{i}].{sk}", sv))
    elif module_id == "recurring_expenses":
        for item in data.get("categories") or []:
            if isinstance(item, dict) and item.get("category_id"):
                pairs.append(
                    (f"categories[{item['category_id']}].amount", item.get("amount"))
                )
    elif module_id == "roster":
        if "relationship_status" in data:
            pairs.append(("relationship_status", data["relationship_status"]))
        if "monthly_social_spend" in data:
            pairs.append(("monthly_social_spend", data["monthly_social_spend"]))
        for i, p in enumerate(data.get("people") or []):
            if isinstance(p, dict):
                for sk, sv in p.items():
                    pairs.append((f"people[{i}].{sk}", sv))
    elif module_id == "career":
        for k in (
            "current_role",
            "industry",
            "years_experience",
            "satisfaction",
            "open_to_move",
            "target_comp",
        ):
            if k in data:
                pairs.append((k, data[k]))
    elif module_id == "milestones":
        for i, ev in enumerate(data.get("events") or []):
            if isinstance(ev, dict):
                for k in ("name", "date", "cost"):
                    if k in ev:
                        pairs.append((f"events[{i}].{k}", ev[k]))
    return pairs


def run_commit_field(
    *,
    user: User,
    uid: str,
    session: dict,
    module_id: str,
    field_path: str,
    value: Any,
    save_session: Callable[[str, dict], None],
    load_row: Callable[[User], OnboardingProgress | None],
) -> tuple[Any, int]:
    if module_id not in MODULE_ORDER:
        return ({"error": "unknown_module", "module_id": module_id}, 400)
    cast_v, err = _validate_and_cast(field_path, value)
    if err:
        return (err[0], err[1])
    return _apply_commit_field(
        user=user,
        uid=uid,
        session=session,
        field_path=field_path,
        cast_value=cast_v,
        save_session=save_session,
        load_row=load_row,
    )


def run_commit_module(
    *,
    user: User,
    uid: str,
    module_id: str,
    data: dict,
    session: dict,
    save_session: Callable[[str, dict], None],
    load_row: Callable[[User], OnboardingProgress | None],
    upsert_db_progress: Callable[[User, dict], None],
) -> tuple[dict, int]:
    if module_id not in MODULE_ORDER:
        return ({"error": "unknown_module", "module_id": module_id}, 400)
    pairs = flatten_module_data(module_id, data)
    committed_fields: list[str] = []
    failed_fields: list[dict] = []
    for fp, val in pairs:
        body, code = run_commit_field(
            user=user,
            uid=uid,
            session=session,
            module_id=module_id,
            field_path=fp,
            value=val,
            save_session=save_session,
            load_row=load_row,
        )
        if code != 200 or not isinstance(body, dict) or not body.get("ok"):
            failed_fields.append(
                {
                    "field_path": fp,
                    "error": (body or {}).get("error", "error"),
                    "reason": (body or {}).get("reason")
                    or (body or {}).get("note")
                    or str(body),
                }
            )
        else:
            committed_fields.append(fp)

    completed = list(session.get("completed_modules") or [])
    skipped = list(session.get("skipped_modules") or [])
    was_completed = module_id in completed
    was_skipped = module_id in skipped
    is_revisit = was_completed
    next_module: str | None = None
    all_done = False

    if not is_revisit:
        if was_skipped:
            skipped = [x for x in skipped if x != module_id]
            session["skipped_modules"] = skipped
        if module_id not in completed:
            completed.append(module_id)
        session["completed_modules"] = completed
        done_set = set(session["completed_modules"] or [])
        skip_set = set(session.get("skipped_modules") or [])
        next_module = None
        all_done = True
        for mid in MODULE_ORDER:
            if mid in done_set or mid in skip_set:
                continue
            all_done = False
            next_module = mid
            break
        if not all_done and next_module is not None:
            session["current_module"] = next_module
        upsert_db_progress(user, session)
    else:
        row = load_row(user)
        now = _utcnow()
        if row:
            row.last_activity_at = now
            db.session.commit()
        next_module = session.get("current_module")
        done_s = set(session.get("completed_modules") or [])
        skip_s = set(session.get("skipped_modules") or [])
        all_done = set(MODULE_ORDER).issubset(done_s | skip_s)

    try:
        save_session(uid, session)
    except Exception as e:
        loguru_logger.warning("GC2 run_commit_module redis save: {}", e)

    return (
        {
            "ok": True,
            "module_id": module_id,
            "next_module": next_module,
            "all_done": all_done,
            "committed_fields": committed_fields,
            "failed_fields": failed_fields,
            "is_revisit": is_revisit,
        },
        200,
    )
