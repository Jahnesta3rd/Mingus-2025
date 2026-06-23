#!/usr/bin/env python3
"""Commitment-type routing layer for job recommendations."""

from __future__ import annotations

import copy
import logging
from typing import Callable

from backend.models.career_commitment_profile import CareerCommitmentProfile
from backend.models.career_profile import CareerProfile

logger = logging.getLogger(__name__)

_TYPE1_EXCLUDED_CATEGORIES = frozenset({'career_change', 'passion_field'})

_COMMITMENT_CONTEXT_BY_TYPE = {
    'type_1': {
        'type': 'type_1',
        'framing': (
            'Your strongest financial move right now is optimizing your current income.'
        ),
        'cta_label': 'See salary benchmarks for your role',
    },
    'type_2': {
        'type': 'type_2',
        'framing': (
            'Here are income paths that keep your options open while you build your '
            'parallel path.'
        ),
        'cta_label': 'Find a second income stream',
    },
    'type_3': {
        'type': 'type_3',
        'framing': (
            'Based on your track record, here are roles that fit where your skills '
            'are headed.'
        ),
        'cta_label': 'Explore roles in your field',
    },
}


def get_commitment_type(user_id: int) -> str:
    """Load commitment classification for routing; defaults to unclassified."""
    profile = CareerCommitmentProfile.query.filter_by(user_id=user_id).first()
    if profile and profile.commitment_type:
        return profile.commitment_type
    return 'unclassified'


def _recommendations_use_category(recommendations: dict) -> bool:
    for jobs in recommendations.values():
        if not isinstance(jobs, list):
            continue
        for job in jobs:
            if isinstance(job, dict) and 'category' in job:
                return True
    return False


def filter_type_1_recommendations(
    recommendations: dict,
    user_field: str | None,
) -> dict:
    """Exclude passion-field and career-pivot jobs for type_1 users."""
    filtered = copy.deepcopy(recommendations)
    use_category = _recommendations_use_category(filtered)
    for tier, jobs in filtered.items():
        if not isinstance(jobs, list):
            continue
        kept = []
        for job in jobs:
            if not isinstance(job, dict):
                kept.append(job)
                continue
            category = job.get('category')
            if use_category and category in _TYPE1_EXCLUDED_CATEGORIES:
                continue
            if (
                not use_category
                and tier == 'conservative'
                and user_field
                and job.get('career_field')
                and job.get('career_field') != user_field
            ):
                continue
            kept.append(job)
        filtered[tier] = kept
    return filtered


def _second_job_to_recommendation(job: dict) -> dict:
    """Map a second-job advisor payload into the recommendations job shape."""
    return {
        'job_id': None,
        'title': job.get('title'),
        'company': job.get('type'),
        'location': None,
        'msa': None,
        'career_field': None,
        'seniority_level': None,
        'salary_min': None,
        'salary_max': None,
        'salary_median': job.get('monthly_est'),
        'advancement_trajectory': job.get('why_it_fits'),
        'overall_score': None,
        'salary_increase_potential': None,
        'success_probability': None,
        'url': None,
        'remote_friendly': None,
        'category': 'second_income',
        'source': 'second_job_advisor',
        'schedule_fit': job.get('schedule_fit'),
        'first_step': job.get('first_step'),
    }


def prepend_second_job_recommendation(
    recommendations: dict,
    second_job: dict,
) -> dict:
    """Insert the top second-job suggestion as the first recommendation item."""
    merged = copy.deepcopy(recommendations)
    item = _second_job_to_recommendation(second_job)
    tier = 'same_level'
    merged.setdefault(tier, [])
    if not isinstance(merged[tier], list):
        merged[tier] = [merged[tier]]
    merged[tier] = [item, *merged[tier]]
    return merged


def fetch_second_job_top_recommendation(cp: CareerProfile) -> dict | None:
    """Call the second-job advisor helpers and return the top suggestion."""
    from backend.routes.second_job_advisor import _build_user_prompt, _generate_jobs

    user_prompt = _build_user_prompt(
        current_job=(cp.current_role or 'Professional').strip(),
        city=None,
        free_hours_per_week=10,
        schedule_preference='flexible',
        skills=None,
        total_debt=None,
    )
    jobs = _generate_jobs(user_prompt)
    if not jobs:
        return None
    return jobs[0]


def apply_commitment_routing(
    commitment_type: str,
    recommendations: dict,
    *,
    user_field: str | None = None,
    career_profile: CareerProfile | None = None,
    second_job_fetcher: Callable[[CareerProfile], dict | None] = fetch_second_job_top_recommendation,
) -> tuple[dict, dict | None]:
    """Apply commitment-type framing and filters without altering engine scoring."""
    if commitment_type == 'type_1':
        return (
            filter_type_1_recommendations(recommendations, user_field),
            _COMMITMENT_CONTEXT_BY_TYPE['type_1'],
        )

    if commitment_type == 'type_2':
        routed = copy.deepcopy(recommendations)
        if career_profile is not None:
            try:
                top_second_job = second_job_fetcher(career_profile)
            except Exception as exc:
                logger.warning(
                    "second_job_advisor merge skipped for user_id=%s: %s",
                    career_profile.user_id,
                    exc,
                )
                top_second_job = None
            if top_second_job:
                routed = prepend_second_job_recommendation(routed, top_second_job)
        return routed, _COMMITMENT_CONTEXT_BY_TYPE['type_2']

    if commitment_type == 'type_3':
        return recommendations, _COMMITMENT_CONTEXT_BY_TYPE['type_3']

    return recommendations, None
