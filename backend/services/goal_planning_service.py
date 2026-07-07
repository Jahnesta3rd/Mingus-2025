#!/usr/bin/env python3
"""Goal planning analysis service — runs Node pipeline with server-side Claude access."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_NODE_SCRIPT = _REPO_ROOT / "frontend" / "scripts" / "goalPlanningAnalyze.mjs"
_DEFAULT_TIMEOUT_SECONDS = 60


class GoalPlanningServiceError(Exception):
    """Raised when goal planning analysis fails."""


def _validate_payload(goal: dict[str, Any] | None, user_profile: dict[str, Any] | None) -> None:
    if not goal or not isinstance(goal, dict):
        raise GoalPlanningServiceError("goal is required")
    if not goal.get("type"):
        raise GoalPlanningServiceError("goal.type is required")
    if not user_profile or not isinstance(user_profile, dict):
        raise GoalPlanningServiceError("userProfile is required")


def run_goal_planning_analyze(
    goal: dict[str, Any],
    user_profile: dict[str, Any],
    *,
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run the shared Node goal-planning pipeline with server-side Anthropic credentials."""

    _validate_payload(goal, user_profile)

    if not _NODE_SCRIPT.is_file():
        raise GoalPlanningServiceError("Goal planning runner script is missing")

    env = os.environ.copy()
    payload = json.dumps({"goal": goal, "userProfile": user_profile})

    try:
        completed = subprocess.run(
            ["node", str(_NODE_SCRIPT)],
            input=payload,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout_seconds,
            cwd=str(_REPO_ROOT / "frontend"),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GoalPlanningServiceError("Goal planning analysis timed out") from exc
    except OSError as exc:
        logger.exception("Failed to start goal planning Node runner")
        raise GoalPlanningServiceError("Goal planning runner unavailable") from exc

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        logger.error(
            "Goal planning runner failed (code=%s): %s",
            completed.returncode,
            stderr or completed.stdout,
        )
        raise GoalPlanningServiceError(stderr or "Goal planning analysis failed")

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON from goal planning runner: %s", completed.stdout[:500])
        raise GoalPlanningServiceError("Invalid analysis response") from exc

    required_keys = (
        "goalAnalysis",
        "recommendations",
        "jobSuggestions",
        "gigSuggestions",
        "expenseSuggestions",
    )
    for key in required_keys:
        if key not in result:
            raise GoalPlanningServiceError(f"Missing {key} in analysis response")

    return result
