#!/usr/bin/env python3
"""SEC EDGAR API configuration (CR9b)."""

import os

from dotenv import load_dotenv

load_dotenv()

SEC_USER_AGENT = os.environ.get("SEC_USER_AGENT", "")

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
