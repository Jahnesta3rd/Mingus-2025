"""Unit tests for housing search listing normalization (HRA-03)."""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.api.housing_endpoints import (  # noqa: E402
    _extract_listings_from_api_payload,
    _normalize_rental_listing,
    resolve_msa_code_for_zip,
)


class TestHousingSearchZipVariance:
    def test_different_zips_normalize_to_different_cities(self):
        msa_nyc = resolve_msa_code_for_zip('10001')
        msa_phx = resolve_msa_code_for_zip('85001')
        nyc = _normalize_rental_listing(
            {'city': 'New York', 'state': 'NY', 'rent': 2400, 'bedrooms': 2},
            '10001',
            msa_nyc,
            0,
        )
        phx = _normalize_rental_listing(
            {'city': 'Phoenix', 'state': 'AZ', 'rent': 1600, 'bedrooms': 2},
            '85001',
            msa_phx,
            0,
        )

        assert nyc['city'] != phx['city']
        assert nyc['zip_code'] == '10001'
        assert phx['zip_code'] == '85001'
        assert nyc['title'].startswith('New York')
        assert phx['title'].startswith('Phoenix')
        assert 'listing_url' in nyc

    def test_msa_codes_differ_by_zip(self):
        assert resolve_msa_code_for_zip('10001') == '35620'
        assert resolve_msa_code_for_zip('85001') == '38060'
        assert resolve_msa_code_for_zip('10001') != resolve_msa_code_for_zip('85001')

    def test_msa_logged(self, caplog):
        caplog.set_level(logging.INFO, logger='backend.api.housing_endpoints')
        zip_code = '10001'
        msa_code = resolve_msa_code_for_zip(zip_code)
        logging.getLogger('backend.api.housing_endpoints').info(
            'housing_search zip=%s msa=%s source=%s',
            zip_code,
            msa_code,
            'request',
        )
        assert 'housing_search zip=10001' in caplog.text
        assert 'msa=35620' in caplog.text

    def test_extract_listings_from_nested_payload(self):
        payload = {'listings': [{'id': '1', 'city': 'Chicago', 'state': 'IL'}]}
        assert len(_extract_listings_from_api_payload(payload)) == 1

    def test_extract_listings_from_list_payload(self):
        payload = [{'id': '1', 'city': 'Chicago', 'state': 'IL'}]
        assert len(_extract_listings_from_api_payload(payload)) == 1
