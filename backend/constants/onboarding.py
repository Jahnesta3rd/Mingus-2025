"""Shared onboarding module identifiers (order preserved)."""

from __future__ import annotations

MODULE_ORDER = (
    "income",
    "housing",
    "vehicle",
    "recurring_expenses",
    "roster",
    "career",
    "milestones",
)

# Option C category keys + keyword hints for recurring expense extraction (GC1).
# Tuple format: (category_key, (hint_substrings, ...)).
CATEGORY_KEYS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "insurance",
        (
            "insurance",
            "health insurance",
            "renter",
            "renters",
            "homeowner",
            "homeowners",
        ),
    ),
    (
        "debt",
        (
            "debt",
            "loan",
            "loans",
            "credit card",
            "student loan",
            "minimum payment",
            "car payment",
            "auto loan",
            "vehicle loan",
        ),
    ),
    (
        "subscription",
        (
            "subscription",
            "subscriptions",
            "netflix",
            "spotify",
            "streaming",
            "gym",
            "software",
        ),
    ),
    (
        "utilities",
        ("utilit", "electric", "water", "gas bill", "internet", "phone"),
    ),
    ("other", ("other", "misc", "rent", "rental")),
    ("groceries", ("food", "grocery", "groceries")),
    (
        "healthcare",
        ("healthcare", "medical", "doctor", "pharmacy", "copay"),
    ),
    ("childcare", ("childcare", "daycare", "babysit")),
)

# Keys only (commit-field / DB validation).
CATEGORY_KEY_IDS: tuple[str, ...] = tuple(k for k, _ in CATEGORY_KEYS)
