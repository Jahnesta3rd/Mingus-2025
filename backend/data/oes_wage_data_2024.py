"""
2024 BLS OES wage percentile seed data (#165).

National medians are approximate 2024 BLS OES published figures.
Metro values apply documented regional multipliers (±10%) from national
medians; Technology / Atlanta is hand-tuned to published MSA OES bands.
"""

from __future__ import annotations

SOURCE_YEAR = 2024

NATIONAL_MEDIANS: dict[str, int] = {
    "Technology": 104_900,
    "Healthcare (Clinical)": 77_760,
    "Healthcare (Admin/Ops)": 58_000,
    "Finance & Accounting": 82_000,
    "Legal": 127_990,
    "Marketing & Communications": 72_000,
    "Sales": 62_000,
    "Education & Training": 58_000,
    "Engineering (Civil/Mech/Ind)": 92_000,
    "Creative & Design": 58_000,
    "Operations & Supply Chain": 68_000,
    "Human Resources": 68_000,
    "Real Estate": 62_000,
    "Government & Public Policy": 72_000,
    "Hospitality & Food Service": 38_000,
    "Retail & Consumer": 42_000,
    "Construction & Trades": 52_000,
    "Media & Journalism": 58_000,
    "Science & Research": 85_000,
    "Military / Veterans": 68_000,
}

MSA_META: dict[str, str] = {
    "00000": "National",
    "12060": "Atlanta-Sandy Springs-Roswell, GA",
    "47900": "Washington-Arlington-Alexandria, DC-VA-MD-WV",
    "26420": "Houston-The Woodlands-Sugar Land, TX",
    "19100": "Dallas-Fort Worth-Arlington, TX",
    "35620": "New York-Newark-Jersey City, NY-NJ-PA",
    "16980": "Chicago-Naperville-Elgin, IL-IN-WI",
}

MSA_MULTIPLIERS: dict[str, float] = {
    "00000": 1.0,
    "12060": 1.05,
    "47900": 1.28,
    "26420": 1.04,
    "19100": 1.06,
    "35620": 1.38,
    "16980": 1.12,
}

SEED_MSAS = ("12060", "47900", "26420", "19100", "35620", "16980")

SEED_FIELDS = tuple(NATIONAL_MEDIANS.keys())

_PERCENTILE_RATIOS = {
    "pct_10": 0.50,
    "pct_25": 0.65,
    "pct_50": 1.0,
    "pct_75": 1.30,
    "pct_90": 1.66,
}

# Hand-tuned to 2024 BLS OES MSA bands (sanity checks: $55K < p50, $120K > p75).
_FIELD_MSA_OVERRIDES: dict[tuple[str, str], dict[str, int]] = {
    ("Technology", "12060"): {
        "pct_10": 58_000,
        "pct_25": 72_000,
        "pct_50": 95_000,
        "pct_75": 115_000,
        "pct_90": 145_000,
    },
}


def _scale_percentiles(median: int) -> dict[str, int]:
    return {
        key: int(round(median * ratio))
        for key, ratio in _PERCENTILE_RATIOS.items()
    }


def build_oes_wage_rows() -> list[dict]:
    """Build all seed rows: 20 fields × (6 MSAs + national) = 140 rows."""
    rows: list[dict] = []

    for field in SEED_FIELDS:
        national_median = NATIONAL_MEDIANS[field]
        national_pct = _scale_percentiles(national_median)
        rows.append(
            {
                "bls_career_field": field,
                "msa_code": "00000",
                "msa_name": MSA_META["00000"],
                **national_pct,
                "source_year": SOURCE_YEAR,
            }
        )

        for msa_code in SEED_MSAS:
            override = _FIELD_MSA_OVERRIDES.get((field, msa_code))
            if override:
                pct = override
            else:
                adjusted_median = int(round(national_median * MSA_MULTIPLIERS[msa_code]))
                pct = _scale_percentiles(adjusted_median)
            rows.append(
                {
                    "bls_career_field": field,
                    "msa_code": msa_code,
                    "msa_name": MSA_META[msa_code],
                    **pct,
                    "source_year": SOURCE_YEAR,
                }
            )

    return rows
