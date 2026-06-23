"""Unit tests for commitment_type routing on job recommendations."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.services.job_recommendation_routing import (
    apply_commitment_routing,
    filter_type_1_recommendations,
    get_commitment_type,
)


def _sample_recommendations() -> dict:
    return {
        'same_level': [
            {'title': 'Analyst', 'career_field': 'Finance & Accounting', 'category': 'current_field'},
        ],
        'reach': [
            {'title': 'Senior Analyst', 'career_field': 'Finance & Accounting', 'category': 'current_field'},
        ],
        'conservative': [
            {
                'title': 'Product Manager',
                'career_field': 'Technology',
                'category': 'career_change',
            },
            {
                'title': 'Ops Lead',
                'career_field': 'Finance & Accounting',
                'category': 'passion_field',
            },
        ],
    }


@pytest.mark.parametrize(
    'commitment_type',
    ['type_1', 'type_2', 'type_3', 'unclassified', None],
)
def test_get_commitment_type_reads_profile(commitment_type):
    profile = MagicMock()
    profile.commitment_type = commitment_type
    with patch(
        'backend.services.job_recommendation_routing.CareerCommitmentProfile'
    ) as model:
        model.query.filter_by.return_value.first.return_value = profile
        assert get_commitment_type(42) == (commitment_type or 'unclassified')


def test_get_commitment_type_defaults_unclassified():
    with patch(
        'backend.services.job_recommendation_routing.CareerCommitmentProfile'
    ) as model:
        model.query.filter_by.return_value.first.return_value = None
        assert get_commitment_type(7) == 'unclassified'


def test_type_1_user_gets_commitment_context_and_filters_categories():
    recommendations = _sample_recommendations()
    routed, context = apply_commitment_routing(
        'type_1',
        recommendations,
        user_field='Finance & Accounting',
    )

    assert context is not None
    assert context['type'] == 'type_1'
    assert context['cta_label'] == 'See salary benchmarks for your role'
    assert all(
        job.get('category') not in {'career_change', 'passion_field'}
        for jobs in routed.values()
        if isinstance(jobs, list)
        for job in jobs
    )
    assert len(routed['conservative']) == 0


def test_type_3_user_keeps_category_filter_unapplied():
    recommendations = _sample_recommendations()
    routed, context = apply_commitment_routing(
        'type_3',
        recommendations,
        user_field='Finance & Accounting',
    )

    assert context is not None
    assert context['type'] == 'type_3'
    assert routed == recommendations
    categories = [
        job.get('category')
        for jobs in routed.values()
        if isinstance(jobs, list)
        for job in jobs
    ]
    assert 'career_change' in categories
    assert 'passion_field' in categories


def test_unclassified_user_has_null_commitment_context():
    recommendations = _sample_recommendations()
    routed, context = apply_commitment_routing(
        'unclassified',
        recommendations,
        user_field='Finance & Accounting',
    )

    assert context is None
    assert routed == recommendations


def test_type_2_prepends_second_job_without_changing_engine_order():
    recommendations = {
        'same_level': [{'title': 'Engineer', 'career_field': 'Technology'}],
        'reach': [],
        'conservative': [],
    }
    cp = MagicMock(current_role='Engineer', user_id=99)
    second_job = {
        'title': 'Weekend Tutor',
        'type': 'gig',
        'monthly_est': 800,
        'schedule_fit': 'flexible',
        'why_it_fits': 'Uses teaching skills',
        'first_step': 'Sign up on a tutoring platform',
    }

    routed, context = apply_commitment_routing(
        'type_2',
        recommendations,
        user_field='Technology',
        career_profile=cp,
        second_job_fetcher=lambda _cp: second_job,
    )

    assert context is not None
    assert context['type'] == 'type_2'
    assert routed['same_level'][0]['title'] == 'Weekend Tutor'
    assert routed['same_level'][0]['source'] == 'second_job_advisor'
    assert routed['same_level'][1]['title'] == 'Engineer'


def test_type_1_filters_cross_field_conservative_when_category_missing():
    recommendations = {
        'conservative': [
            {'title': 'Pivot Role', 'career_field': 'Technology'},
            {'title': 'Same Field Role', 'career_field': 'Finance & Accounting'},
        ]
    }
    filtered = filter_type_1_recommendations(
        recommendations,
        user_field='Finance & Accounting',
    )
    assert len(filtered['conservative']) == 1
    assert filtered['conservative'][0]['title'] == 'Same Field Role'
