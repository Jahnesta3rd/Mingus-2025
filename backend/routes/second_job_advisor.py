#!/usr/bin/env python3
"""Second income advisor API — Claude-powered job suggestions."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic
from flask import Blueprint, jsonify, request

from backend.auth.decorators import require_auth
from backend.constants.anthropic_models import CLAUDE_SONNET_MODEL

logger = logging.getLogger(__name__)

second_job_advisor_bp = Blueprint(
    "second_job_advisor", __name__, url_prefix="/api/second-job"
)

_SYSTEM_PROMPT = (
    "You are a second income advisor for Black professionals "
    "in the United States. Return ONLY a valid JSON object — "
    "no preamble, no markdown fences. The JSON must contain "
    "exactly one key: 'jobs', an array of exactly 3 objects."
)

_RETRY_APPEND = (
    "\n\nIMPORTANT: Return ONLY raw JSON with no markdown fences. "
    "The top-level object must have exactly one key 'jobs' containing "
    "exactly 3 job objects. Each job must include title, type, "
    "hourly_range, hours_per_week, monthly_est, schedule_fit, "
    "why_it_fits, debt_impact, first_step, and startup_cost."
)

_VALID_SCHEDULES = frozenset(
    {"flexible", "evenings_weekends", "weekends", "mornings", "remote"}
)

_DISCLAIMER = (
    "Job suggestions are AI-generated estimates. "
    "Verify pay rates and opportunities in your local market."
)


def _build_user_prompt(
    *,
    current_job: str,
    city: str | None,
    free_hours_per_week: int,
    schedule_preference: str,
    skills: str | None,
    total_debt: float | None,
) -> str:
    debt_label = f"${total_debt:,.0f}" if total_debt is not None else "Unknown"
    return f"""Current job: {current_job}
Location: {city or 'Not specified'}
Free hours per week: {free_hours_per_week}
Schedule: {schedule_preference}
Skills/interests: {skills or 'Not specified'}
Total debt to pay down: {debt_label}

Suggest 3 realistic second income opportunities.
Each must match the schedule and hours available.
Prioritize options with low startup cost and fast first payment.

Return this exact JSON structure:
{{
  'jobs': [
    {{
      'title': str,
      'type': 'gig'|'part_time'|'freelance'|'contract',
      'hourly_range': str,
      'hours_per_week': int,
      'monthly_est': float,
      'schedule_fit': str,
      'why_it_fits': str,
      'debt_impact': str,
      'first_step': str,
      'startup_cost': str
    }}
  ]
}}"""


def _parse_jobs_json(raw: str) -> list[dict[str, Any]] | None:
    cleaned = re.sub(
        r"^```json\s*|^```\s*|```$",
        "",
        raw.strip(),
        flags=re.MULTILINE,
    ).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    jobs = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(jobs, list) or len(jobs) != 3:
        return None
    return jobs


def _call_claude(user_prompt: str, *, retry: bool = False) -> str | None:
    try:
        client = anthropic.Anthropic()
        content = user_prompt + (_RETRY_APPEND if retry else "")
        response = client.messages.create(
            model=CLAUDE_SONNET_MODEL,
            max_tokens=1000,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
        block = response.content[0] if response.content else None
        text = (getattr(block, "text", None) or "").strip()
        return text or None
    except Exception as exc:
        logger.warning("second_job_advisor anthropic call failed: %s", exc)
        return None


def _generate_jobs(user_prompt: str) -> list[dict[str, Any]] | None:
    raw = _call_claude(user_prompt)
    if raw:
        jobs = _parse_jobs_json(raw)
        if jobs is not None:
            return jobs

    raw = _call_claude(user_prompt, retry=True)
    if not raw:
        return None
    return _parse_jobs_json(raw)


@second_job_advisor_bp.route("/suggest", methods=["POST"])
@require_auth
def suggest():
    body = request.get_json(silent=True) or {}

    current_job = (body.get("current_job") or "").strip()
    if not current_job:
        return jsonify({"error": "current_job is required"}), 400

    free_hours = body.get("free_hours_per_week")
    if free_hours is None:
        return jsonify({"error": "free_hours_per_week is required"}), 400
    try:
        free_hours_per_week = int(free_hours)
    except (TypeError, ValueError):
        return jsonify({"error": "free_hours_per_week must be an integer"}), 400
    if free_hours_per_week <= 0:
        return jsonify({"error": "free_hours_per_week must be positive"}), 400

    schedule_preference = (body.get("schedule_preference") or "flexible").strip()
    if schedule_preference not in _VALID_SCHEDULES:
        return jsonify({"error": "invalid schedule_preference"}), 400

    city = (body.get("city") or "").strip() or None
    skills = (body.get("skills") or "").strip() or None

    total_debt: float | None = None
    if body.get("total_debt") is not None:
        try:
            total_debt = float(body["total_debt"])
        except (TypeError, ValueError):
            return jsonify({"error": "total_debt must be a number"}), 400

    user_prompt = _build_user_prompt(
        current_job=current_job,
        city=city,
        free_hours_per_week=free_hours_per_week,
        schedule_preference=schedule_preference,
        skills=skills,
        total_debt=total_debt,
    )

    jobs = _generate_jobs(user_prompt)
    if jobs is None:
        return (
            jsonify(
                {
                    "error": "suggestion_failed",
                    "message": "Could not generate suggestions. Try again.",
                }
            ),
            500,
        )

    monthly_potential = round(
        sum(float(job.get("monthly_est") or 0) for job in jobs),
        2,
    )

    return jsonify(
        {
            "jobs": jobs,
            "monthly_potential": monthly_potential,
            "disclaimer": _DISCLAIMER,
        }
    ), 200
