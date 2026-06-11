#!/usr/bin/env python3
"""Centralized environment-backed configuration for API keys and external services."""

import os

from dotenv import load_dotenv

load_dotenv()

# API keys
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
BLS_API_KEY = os.environ.get("BLS_API_KEY", "")
SEC_USER_AGENT = os.environ.get("SEC_USER_AGENT", "")

# SEC EDGAR
EDGAR_COMPANY_FACTS_URL = (
    "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
)
EDGAR_SUBMISSIONS_URL = "https://api.sec.gov/submissions/CIK{cik}.json"
EDGAR_FULL_TEXT_URL = (
    "https://efts.sec.gov/LATEST/search-index"
    "?q=%22Item+2.05%22&dateRange=custom&startdt={start}&enddt={end}&forms=8-K"
)
EDGAR_COMPANY_SEARCH_URL = (
    "https://efts.sec.gov/LATEST/search-index"
    "?q=\"{company_name}\"&forms=10-K"
)
RATE_LIMIT_RPS = int(os.environ.get("EDGAR_RATE_LIMIT_RPS", "8"))
