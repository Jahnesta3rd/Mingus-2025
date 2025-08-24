"""
Minimal Plaid integration shim for tests.
Provides the interfaces used by test_plaid_compliance.py without
requiring real Plaid dependencies or network access.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PlaidConfig:
    client_id: str = "test_client_id"
    secret: str = "test_secret"
    environment: str = "sandbox"


class PlaidIntegration:
    def __init__(self, config: Optional[PlaidConfig] = None):
        self.config = config or PlaidConfig()

    def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        return {
            "access_token": f"access_{public_token}",
            "item_id": "test_item_123",
            "request_id": "req_abc123",
        }

    def get_accounts(self, access_token: str) -> Dict[str, Any]:
        return {
            "accounts": [
                {
                    "account_id": "acc_1",
                    "name": "Checking",
                    "mask": "1234",
                    "official_name": "Checking Account",
                    "type": "depository",
                    "subtype": "checking",
                    "balances": {"available": 1200.0, "current": 1250.0, "iso_currency_code": "USD"},
                }
            ],
            "item": {"item_id": "test_item_123"},
            "request_id": "req_accounts_123",
        }

    def get_transactions(self, access_token: str, start_date: str, end_date: str) -> Dict[str, Any]:
        return {
            "transactions": [
                {
                    "transaction_id": "txn_1",
                    "account_id": "acc_1",
                    "amount": 25.5,
                    "date": start_date,
                    "name": "Coffee Shop",
                    "category": ["Food and Drink", "Coffee Shop"],
                }
            ],
            "total_transactions": 1,
            "request_id": "req_txn_123",
        }

    def remove_item(self, access_token: str) -> Dict[str, Any]:
        return {"removed": True, "request_id": "req_remove_123"}


