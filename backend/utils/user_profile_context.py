"""Shared user profile resolution helpers (salary, zip)."""

from __future__ import annotations

import json
import re
from decimal import Decimal

from backend.api.profile_endpoints import get_db_connection
from backend.models.career_profile import CareerProfile
from backend.models.database import db
from backend.models.financial_setup import UserIncome
from backend.models.housing_profile import HousingProfile
from backend.models.transaction_schedule import IncomeStream
from backend.models.user_models import User
from backend.models.user_profile import UserProfile

_ZIP_RE = re.compile(r"\b(\d{5})\b")

_INCOME_ANNUAL_MULTIPLIERS = {
    "weekly": 52,
    "biweekly": 26,
    "semimonthly": 24,
    "monthly": 12,
    "annual": 1,
}


def extract_zip_from_text(text: str | None) -> str | None:
    if not text:
        return None
    match = _ZIP_RE.search(str(text).strip())
    return match.group(1) if match else None


def _parse_json_object(raw) -> dict:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    return {}


def resolve_user_zip_code(user: User) -> str | None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s
                """,
                ("user_profiles",),
            )
            profiles_columns = {row["column_name"] for row in cursor.fetchall()}
            cursor.execute(
                "SELECT * FROM user_profiles WHERE email = %s LIMIT 1",
                (user.email,),
            )
            profile_row = cursor.fetchone()
    finally:
        conn.close()

    personal_info = _parse_json_object(
        profile_row.get("personal_info") if profile_row else None
    )
    zip_code = None
    if profile_row and "zip_code" in profiles_columns and profile_row.get("zip_code"):
        zip_code = extract_zip_from_text(str(profile_row["zip_code"]))
    if not zip_code:
        zip_code = extract_zip_from_text(personal_info.get("zip_code"))
    if not zip_code:
        zip_code = extract_zip_from_text(personal_info.get("zipCode"))

    if not zip_code:
        hp = HousingProfile.query.filter_by(user_id=user.id).first()
        zip_code = extract_zip_from_text(hp.zip_or_city if hp else None)

    return zip_code


def sync_user_profile_zip(user: User, zip_or_city_value: str) -> None:
    """Mirror housing zip_or_city into user_profiles.zip_code (upsert by email)."""
    if not user.email:
        return
    value = (zip_or_city_value or "").strip()
    profile = UserProfile.query.filter_by(email=user.email).first()
    if profile is None:
        profile = UserProfile(email=user.email)
        db.session.add(profile)
    profile.zip_code = value or None


def _annualize_income_amount(amount: Decimal | float, frequency: str) -> float:
    multiplier = _INCOME_ANNUAL_MULTIPLIERS.get((frequency or "").lower(), 12)
    return float(amount) * multiplier


def resolve_current_salary(user: User, cp: CareerProfile | None) -> int | None:
    annual_total = 0.0
    has_income = False
    for row in UserIncome.query.filter_by(user_id=user.id, is_active=True).all():
        annual_total += _annualize_income_amount(row.amount, row.frequency)
        has_income = True

    if has_income and annual_total > 0:
        return int(round(annual_total))

    stream_total = 0.0
    has_stream = False
    for row in IncomeStream.query.filter_by(user_id=user.id, is_active=True).all():
        stream_total += _annualize_income_amount(row.amount, row.frequency)
        has_stream = True

    if has_stream and stream_total > 0:
        return int(round(stream_total))

    if cp and cp.target_comp is not None and cp.target_comp > 0:
        return int(round(float(cp.target_comp)))

    return None
