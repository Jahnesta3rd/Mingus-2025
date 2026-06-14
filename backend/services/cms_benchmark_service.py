#!/usr/bin/env python3
"""CMS plan benchmark service for Health Insurance Advisor."""

from __future__ import annotations

import logging
from decimal import Decimal

from backend.api.profile_endpoints import get_db_connection

logger = logging.getLogger(__name__)

DATA_SOURCE = "cms_puf_2026"


def _to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def get_plan_benchmark(
    state_code: str,
    metal_level: str,
    plan_type: str | None = None,
) -> dict | None:
    state_code = state_code.upper().strip()
    metal_level = metal_level.strip()

    conditions = [
        "state_code = %s",
        "metal_level = %s",
        "oop_max_individual IS NOT NULL",
    ]
    params: list = [state_code, metal_level]

    if plan_type:
        conditions.append("plan_type = %s")
        params.append(plan_type)

    where_clause = " AND ".join(conditions)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                  COUNT(*) AS plan_count,
                  ROUND(AVG(oop_max_individual)) AS avg_oop_max,
                  ROUND(AVG(deductible_individual)) AS avg_deductible,
                  ROUND(MIN(oop_max_individual)) AS min_oop,
                  ROUND(MAX(oop_max_individual)) AS max_oop,
                  ROUND(AVG(sbc_baby_total)) AS avg_baby_cost,
                  ROUND(AVG(sbc_diabetes_total)) AS avg_diabetes_cost,
                  ROUND(AVG(sbc_fracture_total)) AS avg_fracture_cost,
                  SUM(CASE WHEN is_hsa_eligible THEN 1 ELSE 0 END) AS hsa_eligible_count
                FROM cms_benchmark_plans
                WHERE {where_clause}
                """,
                params,
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row or int(row["plan_count"]) == 0:
        return None

    plan_count = int(row["plan_count"])
    hsa_eligible_count = int(row["hsa_eligible_count"] or 0)

    return {
        "state_code": state_code,
        "metal_level": metal_level,
        "plan_type": plan_type,
        "plan_count": plan_count,
        "avg_oop_max": _to_float(row["avg_oop_max"]),
        "avg_deductible": _to_float(row["avg_deductible"]),
        "min_oop": _to_float(row["min_oop"]),
        "max_oop": _to_float(row["max_oop"]),
        "avg_baby_cost": _to_float(row["avg_baby_cost"]),
        "avg_diabetes_cost": _to_float(row["avg_diabetes_cost"]),
        "avg_fracture_cost": _to_float(row["avg_fracture_cost"]),
        "hsa_eligible_pct": hsa_eligible_count / plan_count,
        "data_source": DATA_SOURCE,
        "coverage_note": None,
    }


def _oop_percentile(user_oop: float | None, avg_oop: float | None) -> str | None:
    if user_oop is None or avg_oop is None:
        return None
    if user_oop < avg_oop:
        return "better"
    if user_oop > avg_oop:
        return "worse"
    return "similar"


def _build_summary_line(
    state_code: str,
    metal_level: str,
    user_plan_oop: float | None,
    avg_oop_max: float | None,
) -> str:
    if user_plan_oop is None or avg_oop_max is None:
        return f"Benchmark data for {metal_level} plans in {state_code}."

    oop_vs_avg = user_plan_oop - avg_oop_max
    if oop_vs_avg < 0:
        return (
            f"Your plan's OOP max is ${abs(oop_vs_avg):,.0f} lower than the "
            f"average {metal_level} plan in {state_code}."
        )
    if oop_vs_avg > 0:
        return (
            f"Your plan's OOP max is ${oop_vs_avg:,.0f} higher than the "
            f"average {metal_level} plan in {state_code}."
        )
    return f"Your plan's OOP max matches the {state_code} {metal_level} average."


def get_benchmark_context(
    state_code: str,
    user_plan_oop: float | None,
    user_plan_deductible: float | None,
    metal_level: str = "Silver",
) -> dict:
    try:
        benchmark = get_plan_benchmark(state_code, metal_level)
        if benchmark is None:
            return {
                "available": False,
                "reason": "Regional benchmark data not available for this state.",
            }

        avg_oop_max = benchmark["avg_oop_max"]
        avg_deductible = benchmark["avg_deductible"]

        oop_vs_avg = (
            user_plan_oop - avg_oop_max
            if user_plan_oop is not None and avg_oop_max is not None
            else None
        )
        ded_vs_avg = (
            user_plan_deductible - avg_deductible
            if user_plan_deductible is not None and avg_deductible is not None
            else None
        )

        return {
            "available": True,
            "state_code": benchmark["state_code"],
            "metal_level": benchmark["metal_level"],
            "benchmark": benchmark,
            "user_plan": {
                "oop_max": user_plan_oop,
                "deductible": user_plan_deductible,
            },
            "comparison": {
                "oop_vs_avg": oop_vs_avg,
                "ded_vs_avg": ded_vs_avg,
                "oop_percentile": _oop_percentile(user_plan_oop, avg_oop_max),
                "ded_percentile": _oop_percentile(user_plan_deductible, avg_deductible),
                "summary_line": _build_summary_line(
                    benchmark["state_code"],
                    benchmark["metal_level"],
                    user_plan_oop,
                    avg_oop_max,
                ),
            },
            "scenario_costs": {
                "avg_baby_cost": benchmark["avg_baby_cost"],
                "avg_diabetes_cost": benchmark["avg_diabetes_cost"],
                "avg_fracture_cost": benchmark["avg_fracture_cost"],
            },
        }
    except Exception:
        logger.exception("Failed to load CMS benchmark context for %s", state_code)
        return {"available": False, "reason": "error"}
