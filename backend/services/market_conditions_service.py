#!/usr/bin/env python3
"""
Market conditions service (#165) — national, regional, and personal layers.

National/regional indicators are cached in market_data_cache with TTL.
Personal income percentile uses seeded oes_wage_data (no live BLS OES API).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from backend.utils.user_profile_context import (
    extract_zip_from_text,
    resolve_current_salary,
    resolve_user_zip_code,
)
from backend.data.oes_wage_data_2024 import MSA_META
from backend.models.career_profile import CareerProfile
from backend.models.database import db
from backend.models.housing_profile import HousingProfile
from backend.models.market_conditions_models import MarketDataCache, OesWageData
from backend.models.user_models import User
from backend.services.mci_service import (
    BLS_LAYOFF_RATE_FALLBACK,
    FRED_MORTGAGE_SERIES,
    PMMS_FALLBACK_RATE,
    _fetch_bls_timeseries_points,
    _fetch_fred_series_latest,
    _today_iso,
)

logger = logging.getLogger(__name__)

BLS_LAYOFF_SERIES = "JTS000000000000000LDR"
BLS_CPI_SERIES = "CUSR0000SA0"

NATIONAL_TTL = timedelta(hours=24)
REGIONAL_TTL = timedelta(hours=24)
PERSONAL_TTL = timedelta(days=7)

# Top-50-metro ZIP → CBSA (covers six seed MSAs + major metros).
ZIP_TO_MSA: dict[str, str] = {
    # Atlanta (12060)
    "30301": "12060", "30302": "12060", "30303": "12060", "30304": "12060",
    "30305": "12060", "30306": "12060", "30307": "12060", "30308": "12060",
    "30309": "12060", "30310": "12060", "30311": "12060", "30312": "12060",
    "30313": "12060", "30314": "12060", "30315": "12060", "30316": "12060",
    "30317": "12060", "30318": "12060", "30319": "12060", "30324": "12060",
    "30326": "12060", "30327": "12060", "30328": "12060", "30329": "12060",
    "30331": "12060", "30332": "12060", "30334": "12060", "30336": "12060",
    "30337": "12060", "30338": "12060", "30339": "12060", "30340": "12060",
    "30341": "12060", "30342": "12060", "30344": "12060", "30345": "12060",
    "30346": "12060", "30349": "12060", "30350": "12060", "30354": "12060",
    # DC Metro (47900)
    "20001": "47900", "20002": "47900", "20003": "47900", "20004": "47900",
    "20005": "47900", "20006": "47900", "20007": "47900", "20008": "47900",
    "20009": "47900", "20010": "47900", "20011": "47900", "20012": "47900",
    "20015": "47900", "20016": "47900", "20017": "47900", "20018": "47900",
    "20019": "47900", "20020": "47900", "20024": "47900", "20036": "47900",
    "20037": "47900", "22201": "47900", "22202": "47900", "22203": "47900",
    "22204": "47900", "22205": "47900", "22206": "47900", "22207": "47900",
    "22301": "47900", "22302": "47900", "22304": "47900", "22314": "47900",
    "20814": "47900", "20815": "47900", "20816": "47900", "20817": "47900",
    # Houston (26420)
    "77001": "26420", "77002": "26420", "77003": "26420", "77004": "26420",
    "77005": "26420", "77006": "26420", "77007": "26420", "77008": "26420",
    "77009": "26420", "77010": "26420", "77011": "26420", "77012": "26420",
    "77013": "26420", "77014": "26420", "77015": "26420", "77016": "26420",
    "77017": "26420", "77018": "26420", "77019": "26420", "77020": "26420",
    "77021": "26420", "77022": "26420", "77023": "26420", "77024": "26420",
    "77025": "26420", "77026": "26420", "77027": "26420", "77028": "26420",
    "77029": "26420", "77030": "26420", "77031": "26420", "77036": "26420",
    "77056": "26420", "77057": "26420", "77063": "26420", "77077": "26420",
    "77079": "26420", "77080": "26420", "77098": "26420",
    # Dallas (19100)
    "75201": "19100", "75202": "19100", "75203": "19100", "75204": "19100",
    "75205": "19100", "75206": "19100", "75207": "19100", "75208": "19100",
    "75209": "19100", "75210": "19100", "75211": "19100", "75212": "19100",
    "75214": "19100", "75215": "19100", "75216": "19100", "75217": "19100",
    "75218": "19100", "75219": "19100", "75220": "19100", "75223": "19100",
    "75224": "19100", "75225": "19100", "75226": "19100", "75227": "19100",
    "75228": "19100", "75229": "19100", "75230": "19100", "75231": "19100",
    "75232": "19100", "75233": "19100", "75234": "19100", "75235": "19100",
    "75236": "19100", "75237": "19100", "75238": "19100", "75240": "19100",
    "75243": "19100", "75244": "19100", "75246": "19100", "75247": "19100",
    "75248": "19100", "75249": "19100", "75251": "19100", "75252": "19100",
    "75254": "19100", "76001": "19100", "76002": "19100", "76006": "19100",
    "76010": "19100", "76011": "19100", "76012": "19100", "76013": "19100",
    # NYC (35620)
    "10001": "35620", "10002": "35620", "10003": "35620", "10004": "35620",
    "10005": "35620", "10006": "35620", "10007": "35620", "10009": "35620",
    "10010": "35620", "10011": "35620", "10012": "35620", "10013": "35620",
    "10014": "35620", "10016": "35620", "10017": "35620", "10018": "35620",
    "10019": "35620", "10020": "35620", "10021": "35620", "10022": "35620",
    "10023": "35620", "10024": "35620", "10025": "35620", "10026": "35620",
    "10027": "35620", "10028": "35620", "10029": "35620", "10030": "35620",
    "10031": "35620", "10032": "35620", "10033": "35620", "10034": "35620",
    "10035": "35620", "10036": "35620", "10037": "35620", "10038": "35620",
    "10039": "35620", "10040": "35620", "11201": "35620", "11205": "35620",
    "11211": "35620", "11215": "35620", "11217": "35620", "11222": "35620",
    "11231": "35620", "11238": "35620", "07030": "35620", "07302": "35620",
    # Chicago (16980)
    "60601": "16980", "60602": "16980", "60603": "16980", "60604": "16980",
    "60605": "16980", "60606": "16980", "60607": "16980", "60608": "16980",
    "60609": "16980", "60610": "16980", "60611": "16980", "60612": "16980",
    "60613": "16980", "60614": "16980", "60615": "16980", "60616": "16980",
    "60617": "16980", "60618": "16980", "60619": "16980", "60620": "16980",
    "60621": "16980", "60622": "16980", "60623": "16980", "60624": "16980",
    "60625": "16980", "60626": "16980", "60628": "16980", "60629": "16980",
    "60630": "16980", "60631": "16980", "60632": "16980", "60634": "16980",
    "60636": "16980", "60637": "16980", "60638": "16980", "60639": "16980",
    "60640": "16980", "60641": "16980", "60642": "16980", "60643": "16980",
    "60644": "16980", "60645": "16980", "60646": "16980", "60647": "16980",
    "60649": "16980", "60651": "16980", "60652": "16980", "60653": "16980",
    "60654": "16980", "60655": "16980", "60656": "16980", "60657": "16980",
    "60659": "16980", "60660": "16980", "60661": "16980",
    # Los Angeles (31080)
    "90001": "31080", "90002": "31080", "90003": "31080", "90004": "31080",
    "90005": "31080", "90006": "31080", "90007": "31080", "90008": "31080",
    "90010": "31080", "90011": "31080", "90012": "31080", "90013": "31080",
    "90014": "31080", "90015": "31080", "90016": "31080", "90017": "31080",
    "90018": "31080", "90019": "31080", "90020": "31080", "90024": "31080",
    "90025": "31080", "90026": "31080", "90027": "31080", "90028": "31080",
    "90029": "31080", "90034": "31080", "90035": "31080", "90036": "31080",
    "90038": "31080", "90039": "31080", "90046": "31080", "90048": "31080",
    "90049": "31080", "90064": "31080", "90066": "31080", "90067": "31080",
    "90068": "31080", "90069": "31080", "90210": "31080", "90212": "31080",
    # San Francisco (41860)
    "94102": "41860", "94103": "41860", "94104": "41860", "94105": "41860",
    "94107": "41860", "94108": "41860", "94109": "41860", "94110": "41860",
    "94111": "41860", "94112": "41860", "94114": "41860", "94115": "41860",
    "94116": "41860", "94117": "41860", "94118": "41860", "94121": "41860",
    "94122": "41860", "94123": "41860", "94124": "41860", "94127": "41860",
    "94131": "41860", "94132": "41860", "94133": "41860", "94134": "41860",
    "94158": "41860", "94601": "41860", "94602": "41860", "94606": "41860",
    # Phoenix (38060)
    "85001": "38060", "85003": "38060", "85004": "38060", "85006": "38060",
    "85007": "38060", "85008": "38060", "85009": "38060", "85012": "38060",
    "85013": "38060", "85014": "38060", "85015": "38060", "85016": "38060",
    "85017": "38060", "85018": "38060", "85019": "38060", "85020": "38060",
    "85021": "38060", "85022": "38060", "85023": "38060", "85024": "38060",
    # Boston (14460)
    "02108": "14460", "02109": "14460", "02110": "14460", "02111": "14460",
    "02113": "14460", "02114": "14460", "02115": "14460", "02116": "14460",
    "02118": "14460", "02119": "14460", "02120": "14460", "02121": "14460",
    "02122": "14460", "02124": "14460", "02125": "14460", "02126": "14460",
    "02127": "14460", "02128": "14460", "02129": "14460", "02130": "14460",
    "02131": "14460", "02132": "14460", "02134": "14460", "02135": "14460",
    # Miami (33100)
    "33101": "33100", "33109": "33100", "33125": "33100", "33126": "33100",
    "33127": "33100", "33128": "33100", "33129": "33100", "33130": "33100",
    "33131": "33100", "33132": "33100", "33133": "33100", "33134": "33100",
    "33135": "33100", "33136": "33100", "33137": "33100", "33138": "33100",
    "33139": "33100", "33140": "33100", "33141": "33100", "33142": "33100",
    # Seattle (42660)
    "98101": "42660", "98102": "42660", "98103": "42660", "98104": "42660",
    "98105": "42660", "98106": "42660", "98107": "42660", "98108": "42660",
    "98109": "42660", "98112": "42660", "98115": "42660", "98116": "42660",
    "98117": "42660", "98118": "42660", "98119": "42660", "98121": "42660",
    "98122": "42660", "98125": "42660", "98126": "42660", "98133": "42660",
    # Denver (19740)
    "80202": "19740", "80203": "19740", "80204": "19740", "80205": "19740",
    "80206": "19740", "80207": "19740", "80209": "19740", "80210": "19740",
    "80211": "19740", "80212": "19740", "80214": "19740", "80218": "19740",
    "80219": "19740", "80220": "19740", "80222": "19740", "80223": "19740",
    # Philadelphia (37980)
    "19102": "37980", "19103": "37980", "19104": "37980", "19106": "37980",
    "19107": "37980", "19118": "37980", "19119": "37980", "19121": "37980",
    "19122": "37980", "19123": "37980", "19125": "37980", "19130": "37980",
    # San Diego (41740)
    "92101": "41740", "92102": "41740", "92103": "41740", "92104": "41740",
    "92105": "41740", "92106": "41740", "92107": "41740", "92108": "41740",
    "92109": "41740", "92110": "41740", "92111": "41740", "92113": "41740",
}

MSA_FRED_UNEMPLOYMENT: dict[str, str] = {
    "12060": "ATLA013URN",
    "47900": "WASH911URN",
    "26420": "HOUS448URN",
    "19100": "DALL148URN",
    "35620": "NEWY636URN",
    "16980": "CHIC917URN",
    "31080": "LOSA706URN",
    "41860": "SANF806URN",
    "38060": "PHOE004URN",
    "14460": "BOST115URN",
    "33100": "MIAM112URN",
    "42660": "SEAT653URN",
    "19740": "DENV708URN",
    "37980": "PHIL148URN",
    "41740": "SAND706URN",
}

MSA_STATE_FALLBACK: dict[str, str] = {
    "12060": "GAURN",
    "47900": "DCURN",
    "26420": "TXURN",
    "19100": "TXURN",
    "35620": "NYURN",
    "16980": "ILURN",
    "31080": "CAURN",
    "41860": "CAURN",
    "38060": "AZURN",
    "14460": "MAURN",
    "33100": "FLURN",
    "42660": "WAURN",
    "19740": "COURN",
    "37980": "PAURN",
    "41740": "CAURN",
}

# Field-level wage growth YoY fallback when Atlanta Fed series unavailable.
FIELD_WAGE_GROWTH_YOY: dict[str, float] = {
    "Technology": 4.2,
    "Healthcare (Clinical)": 3.8,
    "Healthcare (Admin/Ops)": 3.5,
    "Finance & Accounting": 3.6,
    "Legal": 3.2,
    "Marketing & Communications": 3.4,
    "Sales": 3.0,
    "Education & Training": 2.8,
    "Engineering (Civil/Mech/Ind)": 3.9,
    "Creative & Design": 3.1,
    "Operations & Supply Chain": 3.5,
    "Human Resources": 3.3,
    "Real Estate": 3.0,
    "Government & Public Policy": 2.9,
    "Hospitality & Food Service": 4.5,
    "Retail & Consumer": 3.2,
    "Construction & Trades": 4.0,
    "Media & Journalism": 2.7,
    "Science & Research": 3.6,
    "Military / Veterans": 3.0,
}
DEFAULT_WAGE_GROWTH_YOY = 3.5


def resolve_user_msa(user: User) -> tuple[str | None, str | None]:
    """
    Resolve CBSA code and display name from profile zip sources.

    Order: housing_profile.zip_or_city → user_profiles.zip_code (via helper).
    """
    hp = HousingProfile.query.filter_by(user_id=user.id).first()
    zip_code = extract_zip_from_text(hp.zip_or_city if hp else None)
    if not zip_code:
        zip_code = resolve_user_zip_code(user)

    if not zip_code:
        return None, None

    msa_code = ZIP_TO_MSA.get(zip_code)
    if not msa_code:
        return None, None

    msa_name = MSA_META.get(msa_code)
    if not msa_name:
        from backend.scripts.job_postings_seed_data import MSA_CONFIG

        meta = MSA_CONFIG.get(msa_code, {})
        city = meta.get("city", "")
        state = meta.get("state", "")
        msa_name = f"{city}, {state}" if city else msa_code

    return msa_code, msa_name


def _read_cache(key: str) -> tuple[dict | None, datetime | None]:
    try:
        row = MarketDataCache.query.filter_by(key=key).first()
        if row:
            return dict(row.value), row.fetched_at
    except Exception as exc:
        logger.warning("market_data_cache read failed for %s: %s", key, exc)
    return None, None


def _write_cache(key: str, value: dict) -> None:
    try:
        row = MarketDataCache.query.filter_by(key=key).first()
        now = datetime.utcnow()
        if row:
            row.value = value
            row.fetched_at = now
        else:
            db.session.add(MarketDataCache(key=key, value=value, fetched_at=now))
        db.session.commit()
    except Exception as exc:
        logger.warning("market_data_cache write failed for %s: %s", key, exc)
        db.session.rollback()


def _cached_fetch(
    key: str,
    ttl: timedelta,
    fetch_fn,
) -> tuple[dict, bool]:
    """
    Return (payload, stale_flag).
    On fetch failure returns last cached value with stale=True.
    """
    cached, fetched_at = _read_cache(key)
    fresh = (
        cached is not None
        and fetched_at is not None
        and datetime.utcnow() - fetched_at < ttl
    )
    if fresh:
        return cached, False

    try:
        payload = fetch_fn()
        if payload:
            _write_cache(key, payload)
            return payload, False
    except Exception as exc:
        logger.warning("Live fetch failed for %s: %s", key, exc)

    if cached:
        return cached, True

    try:
        payload = fetch_fn(fallback_only=True)
    except TypeError:
        payload = fetch_fn()
    return payload or {}, True


def _fetch_layoff_rate(*, fallback_only: bool = False) -> dict:
    if fallback_only:
        rate = float(BLS_LAYOFF_RATE_FALLBACK)
        return {
            "layoff_rate": rate,
            "layoff_rate_label": f"{rate:.1f}% monthly layoff rate",
            "data_date": _today_iso(),
        }

    points = _fetch_bls_timeseries_points(BLS_LAYOFF_SERIES, lookback_months=6)
    if points:
        rate = float(points[-1][1])
        as_of = points[-1][0]
    else:
        rate = float(BLS_LAYOFF_RATE_FALLBACK)
        as_of = _today_iso()

    return {
        "layoff_rate": round(rate, 2),
        "layoff_rate_label": f"{rate:.1f}% monthly layoff rate",
        "data_date": as_of,
    }


def _fetch_mortgage_rate(*, fallback_only: bool = False) -> dict:
    if fallback_only:
        rate = float(PMMS_FALLBACK_RATE)
        return {
            "mortgage_rate": rate,
            "mortgage_rate_label": f"{rate:.2f}% 30-year fixed",
            "data_date": _today_iso(),
        }

    points = _fetch_fred_series_latest(FRED_MORTGAGE_SERIES, limit=1)
    if points:
        rate = float(points[-1][1])
        as_of = points[-1][0]
    else:
        rate = float(PMMS_FALLBACK_RATE)
        as_of = _today_iso()

    return {
        "mortgage_rate": round(rate, 2),
        "mortgage_rate_label": f"{rate:.2f}% 30-year fixed",
        "data_date": as_of,
    }


def _fetch_cpi_yoy(*, fallback_only: bool = False) -> dict:
    fallback_yoy = 3.1
    if fallback_only:
        return {
            "cpi_yoy": fallback_yoy,
            "cpi_label": f"{fallback_yoy:.1f}% year-over-year",
            "data_date": _today_iso(),
        }

    points = _fetch_bls_timeseries_points(BLS_CPI_SERIES, lookback_months=14)
    if len(points) >= 13:
        latest_val = points[-1][1]
        year_ago_val = points[-13][1]
        if year_ago_val:
            yoy = ((latest_val - year_ago_val) / year_ago_val) * 100.0
            as_of = points[-1][0]
            return {
                "cpi_yoy": round(yoy, 1),
                "cpi_label": f"{yoy:.1f}% year-over-year",
                "data_date": as_of,
            }

    return {
        "cpi_yoy": fallback_yoy,
        "cpi_label": f"{fallback_yoy:.1f}% year-over-year",
        "data_date": _today_iso(),
    }


def _fetch_national_layer() -> tuple[dict, bool]:
    stale_flags: list[bool] = []

    layoff, s1 = _cached_fetch("national:jolts", NATIONAL_TTL, _fetch_layoff_rate)
    stale_flags.append(s1)
    mortgage, s2 = _cached_fetch("national:mortgage", NATIONAL_TTL, _fetch_mortgage_rate)
    stale_flags.append(s2)
    cpi, s3 = _cached_fetch("national:cpi", NATIONAL_TTL, _fetch_cpi_yoy)
    stale_flags.append(s3)

    dates = [layoff.get("data_date"), mortgage.get("data_date"), cpi.get("data_date")]
    data_date = max(d for d in dates if d) if any(dates) else _today_iso()

    national = {
        "layoff_rate": layoff.get("layoff_rate", BLS_LAYOFF_RATE_FALLBACK),
        "layoff_rate_label": layoff.get("layoff_rate_label", ""),
        "mortgage_rate": mortgage.get("mortgage_rate", PMMS_FALLBACK_RATE),
        "mortgage_rate_label": mortgage.get("mortgage_rate_label", ""),
        "cpi_yoy": cpi.get("cpi_yoy", 3.1),
        "cpi_label": cpi.get("cpi_label", ""),
        "data_date": data_date,
    }
    return national, any(stale_flags)


def _fetch_regional_unemployment(msa_code: str, *, fallback_only: bool = False) -> dict:
    series_id = MSA_FRED_UNEMPLOYMENT.get(msa_code)
    state_series = MSA_STATE_FALLBACK.get(msa_code)

    if fallback_only or not series_id:
        return {"unemployment_rate": None, "data_date": _today_iso()}

    points = _fetch_fred_series_latest(series_id, limit=1)
    if not points and state_series:
        points = _fetch_fred_series_latest(state_series, limit=1)

    if points:
        return {
            "unemployment_rate": round(float(points[-1][1]), 1),
            "data_date": points[-1][0],
        }
    return {"unemployment_rate": None, "data_date": _today_iso()}


def _fetch_regional_hpi(msa_code: str, *, fallback_only: bool = False) -> dict:
    if fallback_only:
        return {"housing_price_index": None, "data_date": _today_iso()}

    series_id = f"ATNHPIUS{msa_code}A"
    points = _fetch_fred_series_latest(series_id, limit=1)
    if points:
        return {
            "housing_price_index": round(float(points[-1][1]), 1),
            "data_date": points[-1][0],
        }
    return {"housing_price_index": None, "data_date": _today_iso()}


def _fetch_regional_layer(msa_code: str, msa_name: str) -> tuple[dict | None, bool]:
    unemp_key = f"regional:{msa_code}:unemployment"
    hpi_key = f"regional:{msa_code}:hpi"

    unemp, s1 = _cached_fetch(
        unemp_key,
        REGIONAL_TTL,
        lambda fallback_only=False: _fetch_regional_unemployment(msa_code, fallback_only=fallback_only),
    )
    hpi, s2 = _cached_fetch(
        hpi_key,
        REGIONAL_TTL,
        lambda fallback_only=False: _fetch_regional_hpi(msa_code, fallback_only=fallback_only),
    )

    dates = [unemp.get("data_date"), hpi.get("data_date")]
    data_date = max(d for d in dates if d) if any(dates) else _today_iso()

    regional = {
        "msa_name": msa_name,
        "unemployment_rate": unemp.get("unemployment_rate"),
        "housing_price_index": hpi.get("housing_price_index"),
        "data_date": data_date,
    }
    return regional, any([s1, s2])


def compute_percentile(
    salary: int,
    pct_10: int,
    pct_25: int,
    pct_50: int,
    pct_75: int,
    pct_90: int,
) -> int:
    """Interpolate an integer percentile (1–99) from OES wage bands."""
    bands = [(10, pct_10), (25, pct_25), (50, pct_50), (75, pct_75), (90, pct_90)]
    salary_f = float(salary)

    if salary_f <= pct_10:
        if pct_10 <= 0:
            return 1
        return max(1, min(10, int(round((salary_f / pct_10) * 10))))

    if salary_f >= pct_90:
        if pct_90 <= 0:
            return 99
        excess = salary_f - pct_90
        span = max(pct_90 * 0.25, 1.0)
        return min(99, 90 + int(round((excess / span) * 9)))

    prev_pct, prev_wage = 10, float(pct_10)
    for pct, wage in bands[1:]:
        if salary_f <= wage:
            if wage <= prev_wage:
                return pct
            frac = (salary_f - prev_wage) / (wage - prev_wage)
            return max(prev_pct, min(pct, int(round(prev_pct + frac * (pct - prev_pct)))))
        prev_pct, prev_wage = pct, float(wage)

    return 90


def _lookup_oes_row(bls_career_field: str, msa_code: str) -> OesWageData | None:
    cache_key = f"personal:oes:{bls_career_field}:{msa_code}"
    cached, fetched_at = _read_cache(cache_key)
    if cached and fetched_at and datetime.utcnow() - fetched_at < PERSONAL_TTL:
        return _oes_from_cache_dict(cached)

    row = (
        OesWageData.query.filter_by(
            bls_career_field=bls_career_field,
            msa_code=msa_code,
        ).first()
    )
    if row:
        _write_cache(
            cache_key,
            {
                "bls_career_field": row.bls_career_field,
                "msa_code": row.msa_code,
                "msa_name": row.msa_name,
                "pct_10": row.pct_10,
                "pct_25": row.pct_25,
                "pct_50": row.pct_50,
                "pct_75": row.pct_75,
                "pct_90": row.pct_90,
                "source_year": row.source_year,
            },
        )
    return row


def _oes_from_cache_dict(data: dict) -> OesWageData:
    row = OesWageData()
    row.bls_career_field = data["bls_career_field"]
    row.msa_code = data["msa_code"]
    row.msa_name = data["msa_name"]
    row.pct_10 = data["pct_10"]
    row.pct_25 = data["pct_25"]
    row.pct_50 = data["pct_50"]
    row.pct_75 = data["pct_75"]
    row.pct_90 = data["pct_90"]
    row.source_year = data["source_year"]
    return row


def _wage_growth_yoy(bls_career_field: str) -> float:
    return FIELD_WAGE_GROWTH_YOY.get(bls_career_field, DEFAULT_WAGE_GROWTH_YOY)


def _build_personal_layer(
    user: User,
    cp: CareerProfile | None,
    msa_code: str | None,
    msa_name: str | None,
) -> tuple[dict | None, str | None]:
    if not cp or not cp.bls_career_field:
        return None, None

    current_salary = resolve_current_salary(user, cp)
    if current_salary is None or current_salary <= 0:
        return None, None

    lookup_msa = msa_code if msa_code else "00000"
    oes = _lookup_oes_row(cp.bls_career_field, lookup_msa)
    if not oes and lookup_msa != "00000":
        oes = _lookup_oes_row(cp.bls_career_field, "00000")

    if not oes:
        return None, None

    display_msa = msa_name if msa_code else "National"
    percentile = compute_percentile(
        current_salary,
        oes.pct_10,
        oes.pct_25,
        oes.pct_50,
        oes.pct_75,
        oes.pct_90,
    )

    personal = {
        "percentile": percentile,
        "current_salary": current_salary,
        "pct_10": oes.pct_10,
        "pct_25": oes.pct_25,
        "pct_50": oes.pct_50,
        "pct_75": oes.pct_75,
        "pct_90": oes.pct_90,
        "field_label": cp.bls_career_field,
        "msa_name": display_msa,
        "wage_growth_yoy": _wage_growth_yoy(cp.bls_career_field),
        "source_year": oes.source_year,
        "above_median": current_salary >= oes.pct_50,
    }
    note = f"Based on {oes.source_year} BLS data"
    return personal, note


def get_market_conditions(user: User) -> dict:
    """Build full market conditions payload for an authenticated user."""
    national, national_stale = _fetch_national_layer()

    msa_code, msa_name = resolve_user_msa(user)
    regional = None
    regional_stale = False
    if msa_code and msa_name:
        regional, regional_stale = _fetch_regional_layer(msa_code, msa_name)

    cp = CareerProfile.query.filter_by(user_id=user.id).first()
    personal, personal_note = _build_personal_layer(user, cp, msa_code, msa_name)

    return {
        "national": national,
        "regional": regional,
        "personal": personal,
        "meta": {
            "national_stale": national_stale,
            "regional_stale": regional_stale,
            "personal_note": personal_note,
        },
    }
