#!/usr/bin/env python3
"""
Weekly check-in question bank and rotation logic (#176).
"""

from __future__ import annotations

import random
from typing import Any

from sqlalchemy import func

from backend.models.database import db
from backend.models.wellness import CheckinQuestionLog

CHECKIN_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "self_state",
        "label": "Self-State (body/energy)",
        "questions": [
            {
                "id": "self_q1",
                "text": "How good did you feel physically and mentally this week, overall?",
                "anchor": True,
                "scale_labels": {"1": "Very rough", "5": "Great"},
            },
            {
                "id": "self_q2",
                "text": "How many times did you move intentionally this week?",
                "anchor": False,
                "scale_labels": {"1": "Not at all", "5": "Every day"},
            },
            {
                "id": "self_q3",
                "text": "How would you rate your energy level throughout the week?",
                "anchor": False,
                "scale_labels": {"1": "Depleted", "5": "Energized"},
            },
            {
                "id": "self_q4",
                "text": "How many hours of sleep did you average per night?",
                "anchor": False,
                "scale_labels": {"1": "Under 5 hrs", "5": "8+ hrs"},
            },
            {
                "id": "self_q5",
                "text": "How present and focused were you at work this week?",
                "anchor": False,
                "scale_labels": {"1": "Very distracted", "5": "Fully focused"},
            },
            {
                "id": "self_q6",
                "text": "How would you rate your stress level this week?",
                "anchor": False,
                "scale_labels": {"1": "Overwhelmed", "5": "Calm"},
            },
        ],
    },
    {
        "id": "career_purpose",
        "label": "Career / Purpose",
        "questions": [
            {
                "id": "career_q1",
                "text": "How secure do you feel in your career or primary income source right now?",
                "anchor": True,
                "scale_labels": {"1": "Very insecure", "5": "Very secure"},
            },
            {
                "id": "career_q2",
                "text": "How motivated were you at work this week?",
                "anchor": False,
                "scale_labels": {"1": "No motivation", "5": "Highly motivated"},
            },
            {
                "id": "career_q3",
                "text": "How aligned does your work feel with what you actually want to be doing?",
                "anchor": False,
                "scale_labels": {"1": "Completely misaligned", "5": "Perfectly aligned"},
            },
            {
                "id": "career_q4",
                "text": "How clear are you on your next career move or financial goal?",
                "anchor": False,
                "scale_labels": {"1": "No clarity", "5": "Very clear"},
            },
            {
                "id": "career_q5",
                "text": "How would you rate your progress toward your income or career goals this week?",
                "anchor": False,
                "scale_labels": {"1": "Falling behind", "5": "Ahead of target"},
            },
        ],
    },
    {
        "id": "relationships",
        "label": "Relationships / Vibe",
        "questions": [
            {
                "id": "rel_q1",
                "text": "How would you rate the quality of your most important relationships this week?",
                "anchor": True,
                "scale_labels": {"1": "Very strained", "5": "Thriving"},
            },
            {
                "id": "rel_q2",
                "text": "Did you feel emotionally supported by the people around you this week?",
                "anchor": False,
                "scale_labels": {"1": "Not at all", "5": "Very much"},
            },
            {
                "id": "rel_q3",
                "text": "How aligned are you with your partner on financial goals?",
                "anchor": False,
                "scale_labels": {"1": "Not aligned", "5": "Fully aligned"},
            },
            {
                "id": "rel_q4",
                "text": "Did any relationship this week cost you money you hadn't planned?",
                "anchor": False,
                "scale_labels": {"1": "Significantly", "5": "Not at all"},
            },
            {
                "id": "rel_q5",
                "text": "How present and engaged were you in your relationships this week?",
                "anchor": False,
                "scale_labels": {"1": "Distracted/absent", "5": "Fully present"},
            },
            {
                "id": "rel_q6",
                "text": "How clear are you on what you want in your relationships right now?",
                "anchor": False,
                "scale_labels": {"1": "Very unclear", "5": "Very clear"},
            },
        ],
    },
    {
        "id": "emotional_financial",
        "label": "Emotional-Financial Readiness",
        "questions": [
            {
                "id": "ef_q1",
                "text": "How intentional were your financial decisions this week?",
                "anchor": True,
                "scale_labels": {"1": "Very reactive", "5": "Very intentional"},
            },
            {
                "id": "ef_q2",
                "text": "How much did stress drive your spending decisions this week?",
                "anchor": False,
                "scale_labels": {"1": "A lot", "5": "Not at all"},
            },
            {
                "id": "ef_q3",
                "text": "Did you reward yourself with a purchase this week?",
                "anchor": False,
                "scale_labels": {"1": "Significantly", "5": "Not at all"},
            },
            {
                "id": "ef_q4",
                "text": "How would you rate your money mindset this week?",
                "anchor": False,
                "scale_labels": {"1": "Scarcity/fear", "5": "Abundance/confidence"},
            },
            {
                "id": "ef_q5",
                "text": "How well did your spending reflect your actual priorities this week?",
                "anchor": False,
                "scale_labels": {"1": "Very misaligned", "5": "Fully aligned"},
            },
        ],
    },
]

_DOMAIN_BY_ID = {d["id"]: d for d in CHECKIN_QUESTIONS}
_QUESTION_BY_ID: dict[str, dict[str, Any]] = {}
for _domain in CHECKIN_QUESTIONS:
    for _q in _domain["questions"]:
        _QUESTION_BY_ID[_q["id"]] = {**_q, "domain": _domain["id"]}


def _last_shown_week(user_id: int, question_id: str) -> int:
    """Return the most recent week_number this question was logged; 0 if never shown."""
    row = (
        CheckinQuestionLog.query.filter_by(user_id=user_id, question_id=question_id)
        .order_by(CheckinQuestionLog.year.desc(), CheckinQuestionLog.week_number.desc())
        .first()
    )
    if row is None:
        return 0
    return int(row.week_number or 0)


def _pick_rotating_question(user_id: int, domain: dict[str, Any]) -> dict[str, Any]:
    """Pick one non-anchor question (least recently shown; random tie-break)."""
    pool = [q for q in domain["questions"] if not q.get("anchor")]
    if not pool:
        pool = domain["questions"]

    scored: list[tuple[int, dict[str, Any]]] = []
    for q in pool:
        scored.append((_last_shown_week(user_id, q["id"]), q))

    min_week = min(s for s, _ in scored)
    candidates = [q for s, q in scored if s == min_week]
    return random.choice(candidates)


def get_this_weeks_questions(user_id: int, week_number: int, year: int) -> list[dict[str, Any]]:
    """
    Return 8 questions (2 per domain): anchor + least-recently-shown rotating question.
    """
    del week_number, year  # reserved for future week-specific overrides
    result: list[dict[str, Any]] = []
    for domain in CHECKIN_QUESTIONS:
        anchor = next(q for q in domain["questions"] if q.get("anchor"))
        rotating = _pick_rotating_question(user_id, domain)
        for q in (anchor, rotating):
            result.append(
                {
                    "id": q["id"],
                    "domain": domain["id"],
                    "text": q["text"],
                    "anchor": bool(q.get("anchor")),
                    "scale_labels": q["scale_labels"],
                }
            )
    return result


def log_rotating_question_answers(
    user_id: int,
    week_number: int,
    year: int,
    answers: list[dict[str, Any]],
) -> None:
    """Upsert CheckinQuestionLog rows for each rotating question answer."""
    for item in answers:
        qid = item.get("question_id")
        if not qid:
            continue
        answer = item.get("answer")
        existing = CheckinQuestionLog.query.filter_by(
            user_id=user_id,
            question_id=qid,
            week_number=week_number,
            year=year,
        ).first()
        if existing:
            existing.answer = answer
        else:
            db.session.add(
                CheckinQuestionLog(
                    user_id=user_id,
                    question_id=qid,
                    week_number=week_number,
                    year=year,
                    answer=answer,
                )
            )
    db.session.flush()


def normalize_spending_discipline(value: int | float | None) -> float | None:
    """Normalize spending_discipline_rating to 0–10 scale."""
    if value is None:
        return None
    v = float(value)
    if v > 10:
        return v / 10.0
    return v


def compute_stress_spend_signal(stress_level: int | None, spending_discipline_rating: int | None) -> bool:
    """True when stress is high and spending discipline is low (0–10 normalized)."""
    if stress_level is None or spending_discipline_rating is None:
        return False
    discipline = normalize_spending_discipline(spending_discipline_rating)
    if discipline is None:
        return False
    return stress_level >= 7 and discipline <= 4
