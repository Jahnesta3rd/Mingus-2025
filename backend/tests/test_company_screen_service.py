"""Unit tests for CompanyScreenService — mocked layers and DB."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from backend.services.company_screen_service import CompanyScreenService


@pytest.fixture
def service() -> CompanyScreenService:
    return CompanyScreenService()


def test_compute_composite_all_layers(service: CompanyScreenService):
    result = service._compute_composite(
        layer1_score=80,
        layer1_status="complete",
        layer2_score=60,
        layer2_status="complete",
        layer3_band="positive",
        layer3_status="complete",
    )

    expected = round((80 * 40 + 60 * 35 + 80 * 25) / 100)
    assert result["composite_score"] == expected
    assert result["composite_score"] == 73
    assert result["composite_band"] == "mixed"


def test_compute_composite_layer1_unavailable(service: CompanyScreenService):
    result = service._compute_composite(
        layer1_score=None,
        layer1_status="unavailable",
        layer2_score=80,
        layer2_status="complete",
        layer3_band="positive",
        layer3_status="complete",
    )

    expected = round((80 * 35 + 80 * 25) / 60)
    assert result["composite_score"] == expected
    assert result["composite_score"] == 80
    assert result["composite_band"] == "strong"


def test_compute_composite_all_unavailable(service: CompanyScreenService):
    result = service._compute_composite(
        layer1_score=None,
        layer1_status="unavailable",
        layer2_score=None,
        layer2_status="unavailable",
        layer3_band="insufficient_data",
        layer3_status="insufficient_data",
    )

    assert result["composite_score"] is None
    assert result["composite_band"] is None


def test_compute_composite_layoff_cap_effect(service: CompanyScreenService):
    result = service._compute_composite(
        layer1_score=25,
        layer1_status="complete",
        layer2_score=70,
        layer2_status="complete",
        layer3_band="mixed",
        layer3_status="complete",
    )

    expected = round((25 * 40 + 70 * 35 + 50 * 25) / 100)
    assert result["composite_score"] == expected
    assert result["composite_band"] == "caution"


def test_run_screen_cache_hit(service: CompanyScreenService):
    cached_screen = MagicMock()
    db_session = MagicMock()

    with patch.object(
        service,
        "get_cached_screen",
        return_value=cached_screen,
    ), patch.object(
        service,
        "_serialize_screen",
        return_value={"id": "cached-id", "from_cache": True},
    ) as mock_serialize, patch.object(
        service,
        "_run_layer1",
    ) as mock_layer1:
        result = service.run_screen(1, "Acme Corp", None, db_session)

    assert result["id"] == "cached-id"
    mock_serialize.assert_called_once_with(cached_screen, from_cache=True)
    mock_layer1.assert_not_called()


def test_get_screens_used_this_cycle(service: CompanyScreenService):
    db_session = MagicMock()
    db_session.query.return_value.filter.return_value.count.return_value = 7

    assert service.get_screens_used_this_cycle(42, db_session) == 7


def test_generate_questions_fallback_without_api_key(service: CompanyScreenService):
    screen_data = {
        "composite_band": "mixed",
        "composite_score": 55,
        "layer1_score": 60,
        "layer2_score": 55,
        "layer3_band": "mixed",
        "layoff_event_detected": False,
    }

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        with patch(
            "backend.services.company_screen_service.requests.post",
        ) as mock_post:
            result = service._generate_questions(screen_data, "Acme Corp")

    assert len(result) == 5
    assert all(item["flag_source"] == "fallback" for item in result)
    mock_post.assert_not_called()


def test_serialize_screen_without_layer_details(service: CompanyScreenService):
    from types import SimpleNamespace

    questions_query = MagicMock()
    questions_query.order_by.return_value.all.return_value = []

    screen = SimpleNamespace(
        id="screen-uuid",
        employer_name_text="Acme Corp",
        employer_cik=None,
        composite_score=70,
        composite_band="mixed",
        layer1_score=70,
        layer1_status="complete",
        layoff_event_detected=False,
        layoff_event_date=None,
        layer2_score=65,
        layer2_status="complete",
        layer3_band="mixed",
        layer3_status="complete",
        created_at=SimpleNamespace(isoformat=lambda: "2026-06-22T00:00:00"),
        expires_at=SimpleNamespace(isoformat=lambda: "2026-06-29T00:00:00"),
        questions=questions_query,
    )

    result = service._serialize_screen(screen, from_cache=True)

    assert result["from_cache"] is True
    assert result["layer2_detail"]["jargon_density_score"] is None
    assert result["layer3_detail"]["post_count"] == 0
