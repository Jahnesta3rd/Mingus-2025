#!/usr/bin/env python3
"""Company screen orchestration — layers 1–3, composite score, interview questions (CS4)."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
LLM_MODEL = "claude-sonnet-4-6"
QUESTION_JSON_RETRY_APPEND = (
    "\n\nIMPORTANT: Return only raw JSON array. No backticks, no markdown, no prose."
)

QUESTION_SYSTEM_PROMPT = """
You are a career coach helping a professional prepare for a job interview.
Generate specific, professional questions the candidate should ask the interviewer.
Questions must be grounded in the specific flags provided — never generic.
Return ONLY valid JSON. No preamble. No markdown fences. No explanation.
"""

BAND_TO_SCORE = {
    "positive": 80,
    "mixed": 50,
    "negative": 20,
    "insufficient_data": None,
}

LAYER_WEIGHTS = {"l1": 40, "l2": 35, "l3": 25}


def _fallback_questions() -> list[dict]:
    """Hardcoded fallback questions when LLM generation fails."""
    return [
        {
            "question_text": (
                "How does the team define success for this role in the first 90 days, "
                "and how is that measured?"
            ),
            "flag_source": "fallback",
        },
        {
            "question_text": (
                "Can you walk me through what a typical week looks like for someone "
                "in this position?"
            ),
            "flag_source": "fallback",
        },
        {
            "question_text": (
                "How does leadership communicate major decisions to individual "
                "contributors on this team?"
            ),
            "flag_source": "fallback",
        },
        {
            "question_text": (
                "What does career growth look like for someone who performs well "
                "in this role?"
            ),
            "flag_source": "fallback",
        },
        {
            "question_text": (
                "What is the team most proud of shipping or accomplishing in the "
                "last 12 months?"
            ),
            "flag_source": "fallback",
        },
    ]


class CompanyScreenService:
    """Orchestrates multi-layer company screening for interview prep."""

    def get_cached_screen(
        self,
        user_id: int,
        employer_name: str,
        db_session,
    ):
        """Return a non-expired CompanyScreen for this user and employer, or None."""
        from backend.models.company_screen import CompanyScreen

        safe_name = employer_name.replace("%", r"\%").replace("_", r"\_")
        return (
            db_session.query(CompanyScreen)
            .filter(
                CompanyScreen.user_id == user_id,
                CompanyScreen.employer_name_text.ilike(safe_name, escape="\\"),
                CompanyScreen.expires_at > datetime.utcnow(),
            )
            .order_by(CompanyScreen.created_at.desc())
            .first()
        )

    def _run_layer1(self, employer_cik: str | None, db_session) -> dict[str, Any]:
        """
        Fetch SEC EDGAR health score and layoff event flag.
        Never raises.
        """
        if not employer_cik:
            return {
                "layer1_score": None,
                "layer1_status": "unavailable",
                "layoff_event_detected": False,
                "layoff_event_date": None,
            }

        try:
            from backend.models.employer import Employer, LayoffEvent
            from backend.services.employer_health_scoring import (
                get_latest_snapshot,
                refresh_employer_health,
            )

            cik_padded = str(employer_cik).strip().zfill(10)
            employer = (
                db_session.query(Employer).filter_by(cik=cik_padded).first()
            )
            if employer is None:
                refresh_employer_health(cik_padded, db_session=db_session)
                employer = (
                    db_session.query(Employer).filter_by(cik=cik_padded).first()
                )

            layer1_score = None
            if employer is not None:
                snapshot = get_latest_snapshot(employer.id, db_session=db_session)
                if snapshot is not None and snapshot.score is not None:
                    layer1_score = int(round(float(snapshot.score)))

            cutoff = datetime.utcnow().date() - timedelta(days=90)
            layoff_event = None
            if employer is not None:
                layoff_event = (
                    db_session.query(LayoffEvent)
                    .filter(
                        LayoffEvent.employer_id == employer.id,
                        LayoffEvent.filing_date >= cutoff,
                    )
                    .order_by(LayoffEvent.filing_date.desc())
                    .first()
                )

            layoff_detected = layoff_event is not None
            layoff_date = (
                layoff_event.filing_date.strftime("%Y-%m-%d")
                if layoff_event
                else None
            )

            if layoff_detected and layer1_score is not None:
                layer1_score = min(layer1_score, 25)

            return {
                "layer1_score": layer1_score,
                "layer1_status": (
                    "complete" if layer1_score is not None else "unavailable"
                ),
                "layoff_event_detected": layoff_detected,
                "layoff_event_date": layoff_date,
            }
        except Exception as exc:
            logger.warning("Layer 1 failed for CIK %s: %s", employer_cik, exc)
            return {
                "layer1_score": None,
                "layer1_status": "unavailable",
                "layoff_event_detected": False,
                "layoff_event_date": None,
            }

    def _compute_composite(
        self,
        layer1_score: int | None,
        layer1_status: str,
        layer2_score: int | None,
        layer2_status: str,
        layer3_band: str | None,
        layer3_status: str,
    ) -> dict[str, Any]:
        """Weighted composite of available layers with renormalized weights."""
        contributions: dict[str, tuple[int, int]] = {}

        if layer1_status == "complete" and layer1_score is not None:
            contributions["l1"] = (layer1_score, LAYER_WEIGHTS["l1"])
        if layer2_status == "complete" and layer2_score is not None:
            contributions["l2"] = (layer2_score, LAYER_WEIGHTS["l2"])

        l3_numeric = BAND_TO_SCORE.get(layer3_band or "", None)
        if layer3_status == "complete" and l3_numeric is not None:
            contributions["l3"] = (l3_numeric, LAYER_WEIGHTS["l3"])

        if not contributions:
            return {"composite_score": None, "composite_band": None}

        total_weight = sum(weight for _, weight in contributions.values())
        weighted_sum = sum(score * weight for score, weight in contributions.values())
        composite = round(weighted_sum / total_weight)

        if composite >= 75:
            band = "strong"
        elif composite >= 50:
            band = "mixed"
        elif composite >= 25:
            band = "caution"
        else:
            band = "high_risk"

        return {"composite_score": composite, "composite_band": band}

    def _generate_questions(
        self,
        screen_data: dict[str, Any],
        employer_name: str,
    ) -> list[dict]:
        """Generate 5 tailored interview questions via Anthropic; never raises."""
        flags: list[str] = []
        if screen_data.get("layoff_event_detected"):
            flags.append(
                "layoff_event: active 8-K workforce reduction filing detected"
            )
        if (screen_data.get("layer2_score") or 100) < 50:
            flags.append(
                "jargon_high: company communications scored below 50/100 for clarity"
            )
        if (screen_data.get("layer1_score") or 100) < 50:
            flags.append(
                "revenue_contraction: employer financial health score below 50/100"
            )
        if screen_data.get("layer3_band") == "negative":
            flags.append(
                "negative_sentiment: Reddit community discussions skew negative"
            )
        if screen_data.get("layer3_band") == "mixed":
            flags.append(
                "mixed_sentiment: Reddit community discussions show mixed signals"
            )

        composite_band = screen_data.get("composite_band", "mixed")
        composite_score = screen_data.get("composite_score", 50)

        user_content = f"""
Company: {employer_name}
Company Screen composite score: {composite_score}/100 ({composite_band})
Flags raised: {json.dumps(flags) if flags else '[] — no risk flags detected'}

Rules:
- Generate exactly 5 questions.
- Each question must be directly traceable to one of the flags above.
- If no flags (clean screen): generate 5 positive-framing questions about
  growth, team culture, learning, and what the interviewer is proud of.
- Tone: curious and professional. Never accusatory. Frame as genuine interest.
- Never generate questions so generic they could apply to any company
  (e.g. "What do you like about working here?" is not acceptable).

Return a JSON array of exactly 5 objects:
[
  {{"question_text": "<full question text>", "flag_source": "<flag name or 'clean_screen'>"}},
  ...
]
"""

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return _fallback_questions()

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body = {
            "model": LLM_MODEL,
            "max_tokens": 1000,
            "system": QUESTION_SYSTEM_PROMPT.strip(),
            "messages": [{"role": "user", "content": user_content}],
        }

        def _attempt(content: str) -> list | None:
            body["messages"] = [{"role": "user", "content": content}]
            try:
                resp = requests.post(
                    ANTHROPIC_MESSAGES_URL,
                    headers=headers,
                    json=body,
                    timeout=30,
                )
                resp.raise_for_status()
                raw = resp.json()["content"][0]["text"]
                raw = (
                    raw.strip()
                    .removeprefix("```json")
                    .removeprefix("```")
                    .removesuffix("```")
                    .strip()
                )
                parsed = json.loads(raw)
                if isinstance(parsed, list) and len(parsed) == 5:
                    return parsed
                return None
            except json.JSONDecodeError:
                return None
            except Exception:
                raise

        try:
            result = _attempt(user_content)
            if result is None:
                result = _attempt(user_content + QUESTION_JSON_RETRY_APPEND)
            if result is None:
                logger.warning(
                    "Question generation returned unparseable JSON for %s",
                    employer_name,
                )
                return _fallback_questions()
            return result
        except Exception as exc:
            logger.warning(
                "Question generation failed for %s: %s",
                employer_name,
                exc,
            )
            return _fallback_questions()

    def get_screens_used_this_cycle(self, user_id: int, db_session) -> int:
        """Count screens created since the first of the current UTC month."""
        from backend.models.company_screen import CompanyScreen

        cycle_start = datetime.utcnow().replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return (
            db_session.query(CompanyScreen)
            .filter(
                CompanyScreen.user_id == user_id,
                CompanyScreen.created_at >= cycle_start,
            )
            .count()
        )

    def run_screen(
        self,
        user_id: int,
        employer_name: str,
        employer_cik: str | None,
        db_session,
    ) -> dict[str, Any]:
        """Orchestrate all layers, persist results, and return serializable dict."""
        from backend.models.company_screen import CompanyScreen, CompanyScreenQuestion
        from backend.services.jargon_scorer import JargonScorer
        from backend.services.reddit_employer_query import EmployerQueryRunner

        cached = self.get_cached_screen(user_id, employer_name, db_session)
        if cached:
            return self._serialize_screen(cached, from_cache=True)

        screen = CompanyScreen(
            user_id=user_id,
            employer_cik=employer_cik,
            employer_name_text=employer_name,
            layer1_status="pending",
            layer2_status="pending",
            layer3_status="pending",
        )
        db_session.add(screen)
        db_session.flush()

        l1 = self._run_layer1(employer_cik, db_session)
        l2 = JargonScorer().score_employer(employer_name, employer_cik, db_session)
        l3 = EmployerQueryRunner().run_employer_query(employer_name)

        screen.layer1_score = l1["layer1_score"]
        screen.layer1_status = l1["layer1_status"]
        screen.layoff_event_detected = l1["layoff_event_detected"]
        screen.layoff_event_date = l1["layoff_event_date"]

        screen.layer2_score = l2.get("layer2_score")
        screen.layer2_status = l2.get("layer2_status", "unavailable")

        screen.layer3_band = l3.get("layer3_band")
        screen.layer3_status = l3.get("layer3_status", "unavailable")

        composite = self._compute_composite(
            screen.layer1_score,
            screen.layer1_status,
            screen.layer2_score,
            screen.layer2_status,
            screen.layer3_band,
            screen.layer3_status,
        )
        screen.composite_score = composite["composite_score"]
        screen.composite_band = composite["composite_band"]

        screen_data = {
            "layoff_event_detected": screen.layoff_event_detected,
            "layer1_score": screen.layer1_score,
            "layer2_score": screen.layer2_score,
            "layer3_band": screen.layer3_band,
            "composite_score": screen.composite_score,
            "composite_band": screen.composite_band,
        }
        questions_raw = self._generate_questions(screen_data, employer_name)

        for index, question_data in enumerate(questions_raw):
            db_session.add(
                CompanyScreenQuestion(
                    screen_id=screen.id,
                    question_text=question_data.get("question_text", ""),
                    flag_source=question_data.get("flag_source"),
                    display_order=index,
                )
            )

        db_session.commit()

        screen._l2_detail = l2
        screen._l3_detail = l3

        return self._serialize_screen(screen, from_cache=False)

    def _serialize_screen(
        self,
        screen,
        from_cache: bool = False,
    ) -> dict[str, Any]:
        """Convert a CompanyScreen ORM object to a JSON-serializable dict."""
        from backend.models.company_screen import CompanyScreenQuestion

        question_rows = screen.questions.order_by(
            CompanyScreenQuestion.display_order
        ).all()
        questions = [
            {
                "id": str(question.id),
                "question_text": question.question_text,
                "flag_source": question.flag_source,
                "display_order": question.display_order,
                "dismissed_at": (
                    question.dismissed_at.isoformat()
                    if question.dismissed_at
                    else None
                ),
                "copied_at": (
                    question.copied_at.isoformat() if question.copied_at else None
                ),
            }
            for question in question_rows
        ]

        l2 = getattr(screen, "_l2_detail", None) or {}
        l3 = getattr(screen, "_l3_detail", None) or {}

        return {
            "id": str(screen.id),
            "employer_name": screen.employer_name_text,
            "employer_cik": screen.employer_cik,
            "composite_score": screen.composite_score,
            "composite_band": screen.composite_band,
            "layer1_score": screen.layer1_score,
            "layer1_status": screen.layer1_status,
            "layoff_event_detected": screen.layoff_event_detected,
            "layoff_event_date": screen.layoff_event_date,
            "layer2_score": screen.layer2_score,
            "layer2_status": screen.layer2_status,
            "layer2_detail": {
                "jargon_density_score": l2.get("jargon_density_score"),
                "role_clarity_score": l2.get("role_clarity_score"),
                "values_authenticity_score": l2.get("values_authenticity_score"),
                "leadership_transparency_score": l2.get(
                    "leadership_transparency_score"
                ),
                "top_jargon_phrases": l2.get("top_jargon_phrases", []),
                "scoring_notes": l2.get("scoring_notes"),
                "from_cache": l2.get("from_cache", False),
            },
            "layer3_band": screen.layer3_band,
            "layer3_status": screen.layer3_status,
            "layer3_detail": {
                "confidence": l3.get("confidence"),
                "red_flags": l3.get("red_flags", []),
                "positive_signals": l3.get("positive_signals", []),
                "sentiment_summary": l3.get("sentiment_summary"),
                "sample_threads": l3.get("sample_threads", []),
                "post_count": l3.get("post_count", 0),
            },
            "questions": questions,
            "created_at": screen.created_at.isoformat(),
            "expires_at": screen.expires_at.isoformat(),
            "from_cache": from_cache,
        }
