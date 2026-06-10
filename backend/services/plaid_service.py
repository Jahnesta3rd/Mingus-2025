#!/usr/bin/env python3
"""Plaid Link + transaction sync for optional bank connection."""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Any

from dotenv import load_dotenv
from plaid import Configuration, Environment
from plaid.api import plaid_api
from plaid.api_client import ApiClient
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions

load_dotenv()

logger = logging.getLogger(__name__)


def _resolve_plaid_environment() -> str:
    raw = (os.environ.get("PLAID_ENV") or "").strip().lower()
    mapping = {
        "sandbox": Environment.Sandbox,
        "development": Environment.Sandbox,
        "production": Environment.Production,
    }
    host = mapping.get(raw)
    if host is None:
        raise ValueError(f"Invalid or missing PLAID_ENV: {raw!r}")
    return host


class PlaidService:
    def __init__(self) -> None:
        client_id = os.environ.get("PLAID_CLIENT_ID", "")
        secret = os.environ.get("PLAID_SECRET", "")
        if not client_id or not secret:
            raise ValueError("PLAID_CLIENT_ID and PLAID_SECRET are required")

        configuration = Configuration(
            host=_resolve_plaid_environment(),
            api_key={"clientId": client_id, "secret": secret},
        )
        api_client = ApiClient(configuration)
        self._client = plaid_api.PlaidApi(api_client)
        self._client_id = client_id
        self._secret = secret

    def create_link_token(self, user_id: int) -> str:
        try:
            request = LinkTokenCreateRequest(
                products=[Products("transactions")],
                client_name="Mingus",
                country_codes=[CountryCode("US")],
                language="en",
                user=LinkTokenCreateRequestUser(client_user_id=str(user_id)),
            )
            response = self._client.link_token_create(request)
            return response.link_token
        except Exception:
            logger.exception("Plaid create_link_token failed for user_id=%s", user_id)
            raise

    def exchange_public_token(self, public_token: str) -> dict[str, str]:
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self._client.item_public_token_exchange(request)
            return {
                "access_token": response.access_token,
                "item_id": response.item_id,
            }
        except Exception:
            logger.exception("Plaid exchange_public_token failed")
            raise

    def get_transactions(self, access_token: str, days_back: int = 30) -> list[dict[str, Any]]:
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            options = TransactionsGetRequestOptions(
                include_personal_finance_category=True,
                count=500,
            )
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options=options,
            )
            response = self._client.transactions_get(request)
            return [self._map_transaction(txn) for txn in response.transactions]
        except Exception:
            logger.exception("Plaid get_transactions failed")
            raise

    @staticmethod
    def _map_transaction(txn: Any) -> dict[str, Any]:
        amount = float(txn.amount)
        category = None
        subcategory = None
        pfc = getattr(txn, "personal_finance_category", None)
        if pfc is not None:
            category = getattr(pfc, "primary", None)
            subcategory = getattr(pfc, "detailed", None)
        if category is None and getattr(txn, "category", None):
            cats = txn.category
            if isinstance(cats, list) and cats:
                category = cats[0]
                if len(cats) > 1:
                    subcategory = cats[1]

        merchant = getattr(txn, "merchant_name", None) or getattr(txn, "name", None)
        return {
            "plaid_transaction_id": txn.transaction_id,
            "amount": abs(amount),
            "merchant": merchant,
            "category": category,
            "subcategory": subcategory,
            "date": txn.date,
            "is_debit": amount > 0,
            "account_id": txn.account_id,
            "pending": bool(getattr(txn, "pending", False)),
        }


try:
    plaid_service = PlaidService()
except Exception:
    logger.warning("PlaidService unavailable — bank connection endpoints will return 503")
    plaid_service = None  # type: ignore[assignment]
