"""Axiom logging handler for the Mingus admin dashboard backend."""

import logging
import os
import traceback
from datetime import datetime, timezone

import requests

try:
    from flask import has_request_context, request
except ImportError:
    def has_request_context():
        return False

    request = None


class AxiomHandler(logging.Handler):
    """Send log records to an Axiom dataset via the ingest API."""

    def __init__(self, api_token: str, dataset: str, timeout: float = 3.0):
        super().__init__()
        self.dataset = dataset
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        })
        self._url = f"https://api.axiom.co/v1/datasets/{dataset}/ingest"

    def emit(self, record: logging.LogRecord) -> None:
        try:
            event = {
                "timestamp": datetime.fromtimestamp(
                    record.created, tz=timezone.utc,
                ).isoformat(),
                "level": record.levelname,
                "message": self.format(record),
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            if has_request_context() and request is not None:
                event["request"] = {
                    "method": request.method,
                    "path": request.path,
                    "ip": request.remote_addr,
                    "user_agent": request.headers.get("User-Agent", ""),
                }

            if record.exc_info:
                event["exception"] = "".join(
                    traceback.format_exception(*record.exc_info),
                )

            self._session.post(
                self._url,
                json=[event],
                timeout=self.timeout,
            )
        except Exception:
            pass


def setup_axiom_logging(app) -> None:
    """Attach Axiom handler to the Flask app logger."""
    api_token = os.getenv("AXIOM_API_TOKEN", "")
    dataset = os.getenv("AXIOM_DATASET_BACKEND", "")

    if not api_token or not dataset:
        print(
            "Warning: AXIOM_API_TOKEN or AXIOM_DATASET_BACKEND not set "
            "— Axiom logging disabled",
        )
        return

    handler = AxiomHandler(api_token, dataset)
    handler.setLevel(logging.INFO)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    print("✓ Axiom logging initialized for backend")
