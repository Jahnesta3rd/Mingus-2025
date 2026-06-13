#!/usr/bin/env python3
"""VIN Advisor — book value, repair exposure, keep/monitor/replace verdict, and salary-matched suggestions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from loguru import logger

from backend.models.transaction_schedule import IncomeStream
from backend.models.vehicle_models import Vehicle

# WMI model-year character map (position 10); values cycle every 30 years.
_VIN_YEAR_BASE: dict[str, int] = {
    "A": 1980,
    "B": 1981,
    "C": 1982,
    "D": 1983,
    "E": 1984,
    "F": 1985,
    "G": 1986,
    "H": 1987,
    "J": 1988,
    "K": 1989,
    "L": 1990,
    "M": 1991,
    "N": 1992,
    "P": 1993,
    "R": 1994,
    "S": 1995,
    "T": 1996,
    "V": 1997,
    "W": 1998,
    "X": 1999,
    "Y": 2000,
    "1": 2001,
    "2": 2002,
    "3": 2003,
    "4": 2004,
    "5": 2005,
    "6": 2006,
    "7": 2007,
    "8": 2008,
    "9": 2009,
}

_MAKE_BUCKETS: dict[str, tuple[str, int, float]] = {
    "bmw": ("luxury", 38000, 1.5),
    "mercedes-benz": ("luxury", 38000, 1.5),
    "mercedes": ("luxury", 38000, 1.5),
    "lexus": ("luxury", 38000, 1.5),
    "volvo": ("luxury", 38000, 1.5),
    "acura": ("near-luxury", 32000, 1.3),
    "infiniti": ("near-luxury", 32000, 1.3),
    "cadillac": ("near-luxury", 32000, 1.3),
    "toyota": ("mainstream", 25000, 0.87),
    "honda": ("mainstream", 25000, 0.87),
    "subaru": ("mainstream", 25000, 0.87),
    "mazda": ("mainstream", 25000, 0.87),
    "kia": ("value", 20000, 0.9),
    "hyundai": ("value", 20000, 0.9),
    "nissan": ("value", 20000, 0.9),
    "mitsubishi": ("value", 20000, 0.9),
    "ford": ("domestic", 26000, 1.0),
    "chevrolet": ("domestic", 26000, 1.0),
    "dodge": ("domestic", 26000, 1.0),
    "gmc": ("domestic", 26000, 1.0),
}

_DEFAULT_BUCKET = ("default", 24000, 1.0)

_REPAIRS: list[dict[str, Any]] = [
    {
        "key": "transmission_service",
        "name": "Transmission Service",
        "base_cost": 2200,
        "high_age": True,
        "likelihood": 0.70,
        "frequency_note": "Typical every 60k–100k miles or 8–10 years",
    },
    {
        "key": "brake_system",
        "name": "Brake System",
        "base_cost": 850,
        "high_age": False,
        "likelihood": 0.80,
        "frequency_note": "Pads/rotors every 30k–50k miles",
    },
    {
        "key": "catalytic_converter",
        "name": "Catalytic Converter",
        "base_cost": 1400,
        "high_age": True,
        "likelihood": 0.50,
        "frequency_note": "Often fails after 100k miles or 10+ years",
    },
    {
        "key": "timing_belt_chain",
        "name": "Timing Belt / Chain",
        "base_cost": 900,
        "high_age": False,
        "likelihood": 0.60,
        "frequency_note": "Belt ~60k–100k miles; chain inspected at 100k+",
    },
    {
        "key": "ac_compressor",
        "name": "A/C Compressor",
        "base_cost": 1100,
        "high_age": False,
        "likelihood": 0.45,
        "frequency_note": "Common after 7–10 years of use",
    },
    {
        "key": "water_pump",
        "name": "Water Pump",
        "base_cost": 600,
        "high_age": False,
        "likelihood": 0.55,
        "frequency_note": "Often replaced with timing service",
    },
    {
        "key": "suspension_struts",
        "name": "Suspension / Struts",
        "base_cost": 1200,
        "high_age": False,
        "likelihood": 0.65,
        "frequency_note": "Typical every 50k–80k miles",
    },
]

_CAR_SUGGESTIONS: list[tuple[float, float, list[dict[str, str]]]] = [
    (
        0,
        22000,
        [
            {
                "name": "Honda Civic",
                "price_range": "$21k-$27k",
                "reason": "Lowest TCO, exceptional reliability",
            },
            {
                "name": "Toyota Corolla",
                "price_range": "$21k-$28k",
                "reason": "Best resale in class",
            },
            {
                "name": "Hyundai Elantra",
                "price_range": "$20k-$25k",
                "reason": "10yr/100k warranty",
            },
        ],
    ),
    (
        22000,
        35000,
        [
            {
                "name": "Toyota Camry",
                "price_range": "$27k-$34k",
                "reason": "Best mid-size reliability",
            },
            {
                "name": "Honda Accord",
                "price_range": "$28k-$37k",
                "reason": "Top safety, spacious",
            },
            {
                "name": "Mazda CX-5",
                "price_range": "$29k-$38k",
                "reason": "Premium feel, lower repair costs",
            },
        ],
    ),
    (
        35000,
        float("inf"),
        [
            {
                "name": "Toyota RAV4 Hybrid",
                "price_range": "$33k-$42k",
                "reason": "Best 5-yr TCO with fuel savings",
            },
            {
                "name": "BMW 3 Series CPO",
                "price_range": "$35k-$50k",
                "reason": "Certified pre-owned reduces risk",
            },
            {
                "name": "Lexus ES350",
                "price_range": "$42k-$52k",
                "reason": "Toyota reliability, luxury experience",
            },
        ],
    ),
]


@dataclass(frozen=True)
class RepairItem:
    name: str
    cost: int
    frequency_note: str
    likelihood_pct: float


@dataclass(frozen=True)
class CarSuggestion:
    name: str
    price_range: str
    reason: str


@dataclass(frozen=True)
class VinAdvisorResult:
    vin: str
    year: int
    make: str
    model: str
    book_value: int
    vehicle_age: int
    top_repairs: list[RepairItem]
    annual_repair_exposure: int
    repair_to_value_ratio: float
    verdict: str
    replacement_year_range: dict[str, int]
    car_suggestions: list[CarSuggestion]
    annual_salary: int


def _resolve_make_bucket(make: str) -> tuple[str, int, float]:
    key = (make or "").strip().lower()
    return _MAKE_BUCKETS.get(key, _DEFAULT_BUCKET)


def decode_vin_model_year(vin: str, reference_year: int | None = None) -> int | None:
    """Decode model year from VIN position 10 using the WMI year-char cycle."""
    if not vin or len(vin) < 10:
        return None
    code = vin[9].upper()
    base = _VIN_YEAR_BASE.get(code)
    if base is None:
        return None

    ref = reference_year or date.today().year
    candidates = [base + 30 * offset for offset in range(0, 4) if base + 30 * offset <= ref + 1]
    if not candidates:
        return base
    return max(candidates)


def estimate_book_value(make: str, vehicle_year: int, reference_year: int | None = None) -> int:
    """Depreciate bucket MSRP by 0.82^age; floor $1,500; round to nearest $100."""
    ref = reference_year or date.today().year
    age = max(0, ref - vehicle_year)
    _, base_msrp, _ = _resolve_make_bucket(make)
    raw = base_msrp * (0.82**age)
    value = max(1500, round(raw / 100) * 100)
    return int(value)


def compute_top_repairs(make: str, vehicle_age: int) -> list[RepairItem]:
    """Return top 3 repairs ranked by likelihood × make-adjusted cost."""
    _, _, cost_multiplier = _resolve_make_bucket(make)
    scored: list[tuple[float, RepairItem]] = []

    for repair in _REPAIRS:
        likelihood = repair["likelihood"]
        if repair["high_age"] and vehicle_age > 8:
            likelihood *= 2.0

        adjusted_cost = int(round(repair["base_cost"] * cost_multiplier))
        score = likelihood * adjusted_cost
        item = RepairItem(
            name=repair["name"],
            cost=adjusted_cost,
            frequency_note=repair["frequency_note"],
            likelihood_pct=round(likelihood * 100, 1),
        )
        scored.append((score, item))

    scored.sort(key=lambda row: row[0], reverse=True)
    return [item for _, item in scored[:3]]


def compute_verdict(
    book_value: int,
    vehicle_age: int,
    top_repairs: list[RepairItem],
    reference_year: int | None = None,
) -> tuple[str, float, int, dict[str, int]]:
    """Return verdict, repair-to-value ratio, annual exposure, and replacement window."""
    ref = reference_year or date.today().year
    top3_costs = sum(item.cost for item in top_repairs)
    annual_repair_exposure = int(round(top3_costs * 0.4))
    ratio = annual_repair_exposure / book_value if book_value > 0 else 1.0
    ratio = round(ratio, 2)

    if ratio >= 0.50 or vehicle_age > 12:
        verdict = "replace"
        replacement_year_range = {"from": ref, "to": ref + 2}
    elif ratio < 0.25 and vehicle_age <= 8:
        verdict = "keep"
        replacement_year_range = {
            "from": ref + max(1, 12 - vehicle_age),
            "to": ref + max(3, 15 - vehicle_age),
        }
    else:
        verdict = "monitor"
        replacement_year_range = {
            "from": ref + 1,
            "to": ref + max(2, 12 - vehicle_age),
        }

    return verdict, ratio, annual_repair_exposure, replacement_year_range


def compute_car_suggestions(annual_salary: int, book_value: int) -> list[CarSuggestion]:
    """Return three salary- and value-matched replacement suggestions."""
    salary_budget = annual_salary * 0.25 if annual_salary > 0 else 0
    value_budget = book_value * 2.5
    budget = min(salary_budget, value_budget) if annual_salary > 0 else value_budget

    tier = _CAR_SUGGESTIONS[-1][2]
    for low, high, suggestions in _CAR_SUGGESTIONS:
        if budget < high:
            tier = suggestions
            break

    return [
        CarSuggestion(
            name=row["name"],
            price_range=row["price_range"],
            reason=row["reason"],
        )
        for row in tier
    ]


def compute_annual_salary(income_streams: list[IncomeStream]) -> int:
    """Sum all income streams normalized to an annual figure."""
    total = 0.0
    for stream in income_streams:
        amount = float(stream.amount or 0)
        freq = (stream.frequency or "").strip().lower()
        if freq == "monthly":
            total += amount * 12
        elif freq == "biweekly":
            total += amount * 26
        elif freq == "weekly":
            total += amount * 52
        elif freq == "annual":
            total += amount
    return int(round(total))


def analyze_vehicle(user_id: int, db_session) -> VinAdvisorResult | None:
    """Load the user's primary vehicle and income, then run the VIN Advisor pipeline."""
    logger.info("VIN Advisor analyze_vehicle user_id={}", user_id)

    vehicle = (
        db_session.query(Vehicle)
        .filter(Vehicle.user_id == user_id)
        .order_by(Vehicle.id.asc())
        .first()
    )
    if vehicle is None:
        logger.info("VIN Advisor: no vehicle for user_id={}, returning None", user_id)
        return None

    income_streams = (
        db_session.query(IncomeStream).filter(IncomeStream.user_id == user_id).all()
    )
    annual_salary = compute_annual_salary(income_streams)

    ref_year = date.today().year
    year = vehicle.year or decode_vin_model_year(vehicle.vin or "", ref_year)
    if year is None:
        year = ref_year

    vehicle_age = max(0, ref_year - year)
    make = vehicle.make or ""
    model = vehicle.model or ""
    vin = vehicle.vin or ""

    book_value = estimate_book_value(make, year, ref_year)
    top_repairs = compute_top_repairs(make, vehicle_age)
    verdict, ratio, annual_repair_exposure, replacement_year_range = compute_verdict(
        book_value, vehicle_age, top_repairs, ref_year
    )
    car_suggestions = compute_car_suggestions(annual_salary, book_value)

    return VinAdvisorResult(
        vin=vin,
        year=year,
        make=make,
        model=model,
        book_value=book_value,
        vehicle_age=vehicle_age,
        top_repairs=top_repairs,
        annual_repair_exposure=annual_repair_exposure,
        repair_to_value_ratio=ratio,
        verdict=verdict,
        replacement_year_range=replacement_year_range,
        car_suggestions=car_suggestions,
        annual_salary=annual_salary,
    )


def _smoke_test() -> None:
    """Standalone smoke test with hardcoded inputs (no database)."""
    make = "Toyota"
    year = 2016
    vin = "4T1BF1FK5GU123456"
    ref_year = 2026
    annual_salary = 72000

    vehicle_age = ref_year - year
    book_value = estimate_book_value(make, year, ref_year)
    top_repairs = compute_top_repairs(make, vehicle_age)
    verdict, ratio, exposure, replacement_range = compute_verdict(
        book_value, vehicle_age, top_repairs, ref_year
    )
    suggestions = compute_car_suggestions(annual_salary, book_value)

    result = VinAdvisorResult(
        vin=vin,
        year=year,
        make=make,
        model="Camry",
        book_value=book_value,
        vehicle_age=vehicle_age,
        top_repairs=top_repairs,
        annual_repair_exposure=exposure,
        repair_to_value_ratio=ratio,
        verdict=verdict,
        replacement_year_range=replacement_range,
        car_suggestions=suggestions,
        annual_salary=annual_salary,
    )

    logger.info("VIN Advisor smoke test result: {}", result)
    print("VIN Advisor smoke test OK")
    print(f"  {result.year} {result.make} {result.model} (age {result.vehicle_age})")
    print(f"  book_value=${result.book_value:,}")
    print(f"  verdict={result.verdict} ratio={result.repair_to_value_ratio}")
    print(f"  annual_repair_exposure=${result.annual_repair_exposure:,}")
    print("  top_repairs:")
    for repair in result.top_repairs:
        print(
            f"    - {repair.name}: ${repair.cost:,} "
            f"({repair.likelihood_pct}% likely) — {repair.frequency_note}"
        )
    print(f"  replacement_year_range={result.replacement_year_range}")
    print("  car_suggestions:")
    for car in result.car_suggestions:
        print(f"    - {car.name} {car.price_range}: {car.reason}")


if __name__ == "__main__":
    _smoke_test()
