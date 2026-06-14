#!/usr/bin/env python3
"""LLM-based extraction of health insurance plan fields from SBC documents."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic

from backend.models.database import db
from backend.models.health_insurance_plan import HealthInsurancePlan

logger = logging.getLogger(__name__)

_LLM_MODEL = "claude-sonnet-4-6"
_MAX_TEXT_CHARS = 12_000
_MIN_TEXT_CHARS = 100
_RETRY_APPEND = (
    "\n\nIMPORTANT: Return only raw JSON. No backticks, no prose."
)

_SYSTEM_PROMPT = (
    "You are a health insurance benefits analyst. Extract "
    "structured data from the insurance SBC document text provided. "
    "Return ONLY valid JSON — no preamble, no markdown, no explanation. "
    "If a field is not explicitly stated, return null. "
    "Do not infer or estimate values."
)

_USER_PROMPT_TEMPLATE = """Extract these fields and return as JSON:
{{
  "plan_name": null,
  "plan_type": null,
  "insurer_name": null,
  "plan_year": null,
  "monthly_premium_employee": null,
  "monthly_premium_employee_spouse": null,
  "monthly_premium_family": null,
  "annual_deductible_individual": null,
  "annual_deductible_family": null,
  "out_of_pocket_max_individual": null,
  "out_of_pocket_max_family": null,
  "coinsurance_pct": null,
  "copay_primary_care": null,
  "copay_specialist": null,
  "copay_er": null,
  "rx_tier1": null,
  "rx_tier2": null,
  "rx_tier3": null,
  "rx_tier4": null,
  "has_hsa_eligible": null,
  "employer_hsa_contribution": null,
  "in_network_only": null
}}

plan_type must be one of HMO, PPO, HDHP, EPO, POS, or null.

Document text:
{document_text}"""

_EXTRACTED_FIELDS = (
    "plan_name",
    "plan_type",
    "insurer_name",
    "plan_year",
    "monthly_premium_employee",
    "monthly_premium_employee_spouse",
    "monthly_premium_family",
    "annual_deductible_individual",
    "annual_deductible_family",
    "out_of_pocket_max_individual",
    "out_of_pocket_max_family",
    "coinsurance_pct",
    "copay_primary_care",
    "copay_specialist",
    "copay_er",
    "rx_tier1",
    "rx_tier2",
    "rx_tier3",
    "rx_tier4",
    "has_hsa_eligible",
    "employer_hsa_contribution",
    "in_network_only",
)


def _strip_json_fences(raw: str) -> str:
    return re.sub(
        r"^```json\s*|^```\s*|```$",
        "",
        raw.strip(),
        flags=re.MULTILINE,
    ).strip()


def _parse_json_response(raw: str) -> dict:
    clean = _strip_json_fences(raw)
    return json.loads(clean)


def _extract_document_text(file_path: str) -> str | None:
    path = Path(file_path)
    if not path.is_file():
        return None

    extension = path.suffix.lower()
    try:
        if extension == ".pdf":
            from pdfminer.high_level import extract_text

            text = extract_text(str(path)) or ""
        elif extension == ".docx":
            from docx import Document

            document = Document(str(path))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        else:
            return None
    except Exception:
        logger.exception("Failed to extract text from %s", file_path)
        return None

    text = (text or "").strip()
    return text if len(text) >= _MIN_TEXT_CHARS else None


def _mark_failed(plan: HealthInsurancePlan) -> None:
    plan.parse_status = "failed"
    plan.updated_at = datetime.utcnow()
    db.session.commit()


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


def _apply_parsed_fields(plan: HealthInsurancePlan, parsed: dict[str, Any]) -> None:
    plan_name = parsed.get("plan_name")
    if plan_name:
        plan.plan_name = str(plan_name)[:200]

    plan_type = parsed.get("plan_type")
    plan.plan_type = str(plan_type)[:20] if plan_type else None

    insurer_name = parsed.get("insurer_name")
    plan.insurer_name = str(insurer_name)[:200] if insurer_name else None

    plan_year = parsed.get("plan_year")
    plan.plan_year = int(plan_year) if plan_year is not None else None

    for field in (
        "monthly_premium_employee",
        "monthly_premium_employee_spouse",
        "monthly_premium_family",
        "annual_deductible_individual",
        "annual_deductible_family",
        "out_of_pocket_max_individual",
        "out_of_pocket_max_family",
        "copay_primary_care",
        "copay_specialist",
        "copay_er",
        "rx_tier1",
        "rx_tier2",
        "rx_tier3",
        "rx_tier4",
        "employer_hsa_contribution",
    ):
        value = parsed.get(field)
        plan.__setattr__(field, None if value is None else value)

    coinsurance_pct = parsed.get("coinsurance_pct")
    plan.coinsurance_pct = int(coinsurance_pct) if coinsurance_pct is not None else None

    hsa_eligible = _coerce_bool(parsed.get("has_hsa_eligible"))
    if hsa_eligible is not None:
        plan.has_hsa_eligible = hsa_eligible

    in_network_only = _coerce_bool(parsed.get("in_network_only"))
    plan.in_network_only = in_network_only


def _call_anthropic(user_message: str, retry_append: str | None = None) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.Anthropic(api_key=api_key)
    content = user_message
    if retry_append:
        content += retry_append

    response = client.messages.create(
        model=_LLM_MODEL,
        max_tokens=1000,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text


def parse_insurance_document_with_llm(plan_id: int) -> dict | None:
    """Extract plan fields from an uploaded SBC document via Claude."""
    try:
        plan = HealthInsurancePlan.query.get(plan_id)
        if plan is None:
            logger.warning(
                "parse_insurance_document_with_llm: plan_id=%s not found",
                plan_id,
            )
            return None

        if plan.parse_status not in ("pending", "failed"):
            logger.warning(
                "parse_insurance_document_with_llm: plan_id=%s has "
                "parse_status=%s, skipping",
                plan_id,
                plan.parse_status,
            )
            return None

        if not plan.raw_document_path:
            logger.warning(
                "parse_insurance_document_with_llm: plan_id=%s has no document",
                plan_id,
            )
            _mark_failed(plan)
            return None

        extracted_text = _extract_document_text(plan.raw_document_path)
        if not extracted_text:
            logger.warning(
                "parse_insurance_document_with_llm: plan_id=%s text extraction failed",
                plan_id,
            )
            _mark_failed(plan)
            return None

        truncated_text = extracted_text[:_MAX_TEXT_CHARS]
        user_message = _USER_PROMPT_TEMPLATE.format(document_text=truncated_text)

        raw_response = _call_anthropic(user_message)
        try:
            parsed = _parse_json_response(raw_response)
        except json.JSONDecodeError:
            raw_response = _call_anthropic(user_message, retry_append=_RETRY_APPEND)
            try:
                parsed = _parse_json_response(raw_response)
            except json.JSONDecodeError:
                logger.error(
                    "parse_insurance_document_with_llm: JSON parse failed "
                    "plan_id=%s raw=%s",
                    plan_id,
                    raw_response[:500],
                )
                _mark_failed(plan)
                return None

        if not isinstance(parsed, dict):
            logger.error(
                "parse_insurance_document_with_llm: expected object plan_id=%s",
                plan_id,
            )
            _mark_failed(plan)
            return None

        _apply_parsed_fields(plan, parsed)
        plan.parsed_json = parsed
        plan.parse_status = "completed"
        plan.parsed_at = datetime.utcnow()
        plan.updated_at = datetime.utcnow()
        db.session.commit()
        return parsed

    except Exception:
        logger.exception(
            "parse_insurance_document_with_llm failed for plan_id=%s",
            plan_id,
        )
        try:
            plan = HealthInsurancePlan.query.get(plan_id)
            if plan is not None:
                _mark_failed(plan)
        except Exception:
            logger.exception(
                "Failed to mark plan_id=%s as failed after parse error",
                plan_id,
            )
        return None
