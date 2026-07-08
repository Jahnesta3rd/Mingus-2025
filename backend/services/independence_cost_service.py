#!/usr/bin/env python3
"""Independence cost calculator — monthly solo living costs and startup estimates."""

from __future__ import annotations

import logging
import statistics
from typing import Any
from uuid import UUID

from sqlalchemy import text

from backend.models.database import db
from backend.models.housing_profile import HousingProfile
from backend.models.user_models import User
from backend.models.user_profile import UserProfile
from backend.models.vehicle_models import Vehicle
from backend.models.vibe_tracker import VibePersonAssessment, VibeTrackedPerson
from backend.services.external_api_service import ExternalAPIService
from backend.services.hprs_input_service import get_hprs_inputs
from backend.services.insurance_plan_scorer import ZIP_TO_STATE
from backend.utils.location_utils import LocationValidator
from backend.utils.user_profile_context import extract_zip_from_text

logger = logging.getLogger(__name__)

_MOCK_MARKET_RENT = 1850.0
_RURAL_POPULATION_THRESHOLD = 100_000
_POOR_TRANSIT_ZIP_PREFIXES = frozenset({"59", "82", "83", "59"})

_MONTHLY_BASELINE = {
    "utilities": 150.0,
    "food": 450.0,
    "transportation": 120.0,
    "phone_internet": 90.0,
    "other": 175.0,
}

_STARTUP_BASELINE = {
    "moving": 800.0,
    "utilities_deposits": 200.0,
    "phone_internet": 150.0,
    "furniture_basics": 1500.0,
    "kitchen_appliances": 600.0,
    "household_items": 400.0,
    "car_purchase": 8000.0,
    "car_insurance_deposit": 300.0,
    "registration": 150.0,
    "maintenance_fund": 1000.0,
}


def _round_money(value: float) -> float:
    return round(float(value), 2)


def _is_monotonically_declining(scores: list[int]) -> bool:
    if len(scores) < 2:
        return False
    return all(scores[i] <= scores[i - 1] for i in range(1, len(scores)))


def _median_1br_from_listings(listings: list[dict[str, Any]]) -> float | None:
    prices: list[float] = []
    for listing in listings:
        bedrooms = listing.get("bedrooms")
        if bedrooms is not None and int(bedrooms) != 1:
            continue
        price = listing.get("price") or listing.get("rent") or listing.get("monthlyRent")
        if price is None:
            continue
        try:
            prices.append(float(price))
        except (TypeError, ValueError):
            continue
    if not prices:
        for listing in listings:
            price = listing.get("price") or listing.get("rent") or listing.get("monthlyRent")
            if price is None:
                continue
            try:
                prices.append(float(price))
            except (TypeError, ValueError):
                continue
    if not prices:
        return None
    return statistics.median(prices)


def _infer_market_trend(listings: list[dict[str, Any]]) -> str:
    days_on_market: list[float] = []
    for listing in listings:
        dom = listing.get("daysOnMarket") or listing.get("days_on_market")
        if dom is None:
            continue
        try:
            days_on_market.append(float(dom))
        except (TypeError, ValueError):
            continue
    if not days_on_market:
        return "stable"
    avg_dom = statistics.mean(days_on_market)
    if avg_dom <= 21:
        return "tight"
    if avg_dom >= 45:
        return "soft"
    return "stable"


class IndependenceCostCalculator:
    """Estimate monthly and startup costs for living independently."""

    def __init__(
        self,
        external_api_service: ExternalAPIService | None = None,
        location_validator: LocationValidator | None = None,
    ) -> None:
        self.external_api_service = external_api_service or ExternalAPIService()
        self.location_validator = location_validator or LocationValidator()

    def get_user_location(self, user_id: int) -> tuple[str | None, str | None]:
        """Return (zip_code, city_name) from housing profile or user profile fallbacks."""
        housing = HousingProfile.query.filter_by(user_id=user_id).first()
        if housing and housing.zip_or_city and housing.zip_or_city.strip():
            zip_code = extract_zip_from_text(housing.zip_or_city)
            city_name = housing.zip_or_city.strip()
            if zip_code:
                location = self.location_validator.geocode_zipcode(zip_code)
                if location and location.city:
                    city_name = location.city
            return zip_code, city_name

        users_zip = self._get_users_zip_code(user_id)
        if users_zip:
            location = self.location_validator.geocode_zipcode(users_zip)
            city_name = location.city if location else None
            return users_zip, city_name

        return None, None

    def _get_users_zip_code(self, user_id: int) -> str | None:
        try:
            row = db.session.execute(
                text("SELECT zip_code FROM users WHERE id = :user_id LIMIT 1"),
                {"user_id": user_id},
            ).fetchone()
            if row and row[0]:
                zip_code = extract_zip_from_text(str(row[0]))
                if zip_code:
                    return zip_code
        except Exception:
            logger.debug("users.zip_code unavailable for user_id=%s", user_id, exc_info=True)

        user = User.query.filter_by(id=user_id).first()
        if user and user.email:
            profile = UserProfile.query.filter_by(email=user.email).first()
            if profile and profile.zip_code:
                return extract_zip_from_text(str(profile.zip_code))
        return None

    def get_market_rent(self, zip_code: str) -> dict[str, Any]:
        """Fetch local 1BR rent intelligence; fall back to mock data when unavailable."""
        clean_zip = extract_zip_from_text(zip_code) or (zip_code or "").strip()[:5]
        if not clean_zip:
            return {"median_1br_rent": _MOCK_MARKET_RENT, "market_trend": "stable"}

        try:
            response = self.external_api_service.get_rental_listings(
                clean_zip,
                {"bedrooms": 1, "limit": 25},
            )
            if response.get("success"):
                listings = response.get("data") or []
                median_rent = _median_1br_from_listings(listings)
                if median_rent is not None:
                    return {
                        "median_1br_rent": _round_money(median_rent),
                        "market_trend": _infer_market_trend(listings),
                    }
        except Exception:
            logger.warning("Rent market lookup failed for zip=%s", clean_zip, exc_info=True)

        return {"median_1br_rent": _MOCK_MARKET_RENT, "market_trend": "stable"}

    def get_cost_of_living_index(self, zip_code: str | None) -> float:
        clean_zip = extract_zip_from_text(zip_code or "") or (zip_code or "").strip()[:5]
        if not clean_zip:
            return 1.0
        location = self.location_validator.geocode_zipcode(clean_zip)
        if location:
            return float(location.cost_of_living_index)
        state = ZIP_TO_STATE.get(clean_zip)
        if state:
            return float(self.location_validator._get_cost_of_living_index(state))
        return 1.0

    def estimate_solo_monthly_expenses(
        self,
        zip_code: str,
        market_rent: float,
    ) -> dict[str, float]:
        """Estimate recurring solo monthly costs with cost-of-living adjustments."""
        col_index = self.get_cost_of_living_index(zip_code)
        housing = _round_money(market_rent)
        utilities = _round_money(_MONTHLY_BASELINE["utilities"] * col_index)
        food = _round_money(_MONTHLY_BASELINE["food"] * col_index)
        transportation = _round_money(_MONTHLY_BASELINE["transportation"] * col_index)
        phone_internet = _round_money(_MONTHLY_BASELINE["phone_internet"])
        other = _round_money(_MONTHLY_BASELINE["other"] * col_index)
        total_monthly = _round_money(
            housing + utilities + food + transportation + phone_internet + other
        )
        return {
            "housing": housing,
            "utilities": utilities,
            "food": food,
            "transportation": transportation,
            "phone_internet": phone_internet,
            "other": other,
            "total_monthly": total_monthly,
            "cost_of_living_index": col_index,
        }

    def estimate_startup_costs(
        self,
        zip_code: str,
        has_car: bool,
        col_index: float,
    ) -> dict[str, Any]:
        """Estimate one-time costs to establish an independent household."""
        market = self.get_market_rent(zip_code)
        market_rent = float(market["median_1br_rent"])
        monthly = self.estimate_solo_monthly_expenses(zip_code, market_rent)
        total_monthly = monthly["total_monthly"]

        moving = _round_money(_STARTUP_BASELINE["moving"] * col_index)
        utilities_deposits = _round_money(_STARTUP_BASELINE["utilities_deposits"])
        rental_deposits = _round_money(market_rent * 2)
        phone_internet = _round_money(_STARTUP_BASELINE["phone_internet"])
        furniture_basics = _round_money(_STARTUP_BASELINE["furniture_basics"] * col_index)
        kitchen_appliances = _round_money(_STARTUP_BASELINE["kitchen_appliances"] * col_index)
        household_items = _round_money(_STARTUP_BASELINE["household_items"] * col_index)
        emergency_fund = _round_money(total_monthly * 3)

        base_total = (
            moving
            + utilities_deposits
            + rental_deposits
            + phone_internet
            + furniture_basics
            + kitchen_appliances
            + household_items
            + emergency_fund
        )

        transportation = {
            "car_purchase": _round_money(_STARTUP_BASELINE["car_purchase"] * col_index),
            "car_insurance_deposit": _round_money(_STARTUP_BASELINE["car_insurance_deposit"]),
            "registration": _round_money(_STARTUP_BASELINE["registration"]),
            "maintenance_fund": _round_money(_STARTUP_BASELINE["maintenance_fund"]),
        }
        car_total = sum(transportation.values())

        return {
            "moving": moving,
            "utilities_deposits": utilities_deposits,
            "rental_deposits": rental_deposits,
            "phone_internet": phone_internet,
            "furniture_basics": furniture_basics,
            "kitchen_appliances": kitchen_appliances,
            "household_items": household_items,
            "emergency_fund": emergency_fund,
            "transportation": transportation,
            "total_without_car": _round_money(base_total),
            "total_with_car": _round_money(base_total + car_total),
        }

    def get_current_housing_cost(self, user_id: int, partner_id: UUID) -> float:
        """Estimate what the user currently pays toward shared housing."""
        partner = (
            VibeTrackedPerson.query.filter_by(id=partner_id, user_id=user_id).first()
        )
        if partner and partner.estimated_monthly_cost is not None:
            partner_cost = float(partner.estimated_monthly_cost)
            if partner_cost >= 800:
                return _round_money(partner_cost)

        hprs = get_hprs_inputs(user_id)
        gross_monthly = hprs.get("gross_monthly_income")
        if gross_monthly and gross_monthly > 0:
            return _round_money(float(gross_monthly) * 0.30)

        return 1000.0

    def get_vibe_trend_12_weeks(
        self,
        user_id: int,
        partner_id: UUID,
    ) -> tuple[bool, list[int]]:
        """Return whether the partner vibe trend is steadily declining over 12 weeks."""
        partner = (
            VibeTrackedPerson.query.filter_by(id=partner_id, user_id=user_id).first()
        )
        if partner is None:
            return False, []

        assessments = (
            VibePersonAssessment.query.filter_by(tracked_person_id=partner_id)
            .order_by(VibePersonAssessment.completed_at.desc())
            .limit(12)
            .all()
        )
        scores = [int(row.emotional_score) for row in reversed(assessments)]
        if len(scores) < 10:
            return False, scores

        is_declining = (
            _is_monotonically_declining(scores)
            and scores[-1] <= 2
            and scores[0] != scores[-1]
        )
        return is_declining, scores

    def _is_poor_transit_area(self, zip_code: str | None) -> bool:
        clean_zip = extract_zip_from_text(zip_code or "") or (zip_code or "").strip()[:5]
        if not clean_zip:
            return False
        if clean_zip[:2] in _POOR_TRANSIT_ZIP_PREFIXES:
            return True
        location = self.location_validator.geocode_zipcode(clean_zip)
        if location is None:
            return False
        if location.msa == "Unknown MSA":
            return True
        return location.population < _RURAL_POPULATION_THRESHOLD

    def determine_car_requirement(self, user_id: int, zip_code: str) -> bool:
        """Return True when independent living likely requires a car."""
        owns_car = (
            Vehicle.query.filter_by(user_id=user_id).count() > 0
        )
        if owns_car:
            return True

        col_index = self.get_cost_of_living_index(zip_code)
        transportation = _round_money(_MONTHLY_BASELINE["transportation"] * col_index)
        if transportation >= 150:
            return True

        return self._is_poor_transit_area(zip_code)

    def calculate_full_assessment(self, user_id: int, partner_id: UUID) -> dict[str, Any]:
        """Combine location, costs, gap analysis, and vibe trend into one payload."""
        zip_code, city_name = self.get_user_location(user_id)
        zip_code = zip_code or "10001"
        market = self.get_market_rent(zip_code)
        market_rent = float(market["median_1br_rent"])
        col_index = self.get_cost_of_living_index(zip_code)

        monthly_costs = self.estimate_solo_monthly_expenses(zip_code, market_rent)
        has_car = self.determine_car_requirement(user_id, zip_code)
        startup_costs = self.estimate_startup_costs(zip_code, has_car, col_index)
        current_housing = self.get_current_housing_cost(user_id, partner_id)
        is_declining, vibe_scores = self.get_vibe_trend_12_weeks(user_id, partner_id)

        monthly_gap = _round_money(monthly_costs["total_monthly"] - current_housing)
        startup_total = (
            startup_costs["total_with_car"]
            if has_car
            else startup_costs["total_without_car"]
        )
        months_to_save = (
            _round_money(startup_total / monthly_gap)
            if monthly_gap > 0
            else None
        )

        return {
            "location": {
                "zip_code": zip_code,
                "city_name": city_name,
                "cost_of_living_index": col_index,
            },
            "market_rent": market,
            "monthly_costs": monthly_costs,
            "startup_costs": startup_costs,
            "current_situation": {
                "current_housing_contribution": current_housing,
                "requires_car": has_car,
            },
            "gap": {
                "monthly_independence_gap": monthly_gap,
                "startup_cost": startup_total,
            },
            "timeline": {
                "months_to_save_startup": months_to_save,
            },
            "vibe_data": {
                "is_declining_12_weeks": is_declining,
                "emotional_scores": vibe_scores,
            },
        }
