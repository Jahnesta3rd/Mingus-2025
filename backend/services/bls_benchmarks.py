"""
BLS Consumer Expenditure Survey–derived benchmarks for wellness spending.

Source: U.S. Bureau of Labor Statistics, Consumer Expenditure Survey (CEX),
2023 tables on expenditures by income group.
See: https://www.bls.gov/cex/

These constants are approximate aggregates intended to anchor Mingus wellness
recommendations to external, public data. Update when new CEX data is released.
"""

# Healthcare as % of gross income by income tercile
HEALTHCARE_PCT_INCOME = {
    "low": 0.07,
    "mid": 0.05,
    "high": 0.04,
}

# Average monthly childcare cost by income tercile (2023 BLS/CPI-derived)
CHILDCARE_MONTHLY_AVG = {
    "low": 400,
    "mid": 850,
    "high": 1800,
}

# Entertainment/recreation as % of gross income
ENTERTAINMENT_PCT_INCOME = {
    "low": 0.04,
    "mid": 0.05,
    "high": 0.06,
}

# Food away from home (proxy for relationship/dining spend) as % of income
FOOD_AWAY_PCT_INCOME = {
    "low": 0.04,
    "mid": 0.055,
    "high": 0.07,
}

