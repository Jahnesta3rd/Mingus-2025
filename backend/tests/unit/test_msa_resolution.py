"""Unit tests for job recommendation MSA resolution (#165)."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.api.recommendation_engine_endpoints import (  # noqa: E402
    DEFAULT_MSA,
    _match_msa_from_city_text,
    _resolve_msa_for_user_by_zip,
)


class TestResolveMsaForUserByZip:
    def test_houston_zip_resolves_to_26420(self):
        assert _resolve_msa_for_user_by_zip('77001') == '26420'

    def test_atlanta_zip_resolves_to_12060(self):
        assert _resolve_msa_for_user_by_zip('30301') == '12060'

    def test_unknown_zip_falls_back_to_default(self):
        assert _resolve_msa_for_user_by_zip('99999') == DEFAULT_MSA

    def test_city_name_match_when_zip_unknown(self):
        assert _resolve_msa_for_user_by_zip('99999', city_text='Atlanta, GA') == '12060'

    def test_no_zip_no_city_falls_back_to_default(self):
        assert _resolve_msa_for_user_by_zip(None) == DEFAULT_MSA


class TestMatchMsaFromCityText:
    def test_matches_houston(self):
        assert _match_msa_from_city_text('Houston, TX 77002') == '26420'

    def test_no_match_returns_none(self):
        assert _match_msa_from_city_text('Springfield, IL') is None
