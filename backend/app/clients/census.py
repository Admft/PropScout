"""US Census ACS 5-year: median household income and population for the
property's census tract (via FCC block lookup from lat/lon).
"""
from __future__ import annotations

from typing import Optional

from app.clients.http import cached_get_json
from app.config import get_settings

ACS_YEAR = 2023
ACS_VARS = "B19013_001E,B01003_001E"  # median household income, total population


def _tract_from_latlon(lat: float, lon: float) -> Optional[dict]:
    data = cached_get_json(
        "https://geo.fcc.gov/api/census/block/find",
        params={"latitude": lat, "longitude": lon, "format": "json"},
        cache_prefix="fcc:block",
    )
    fips = (data or {}).get("Block", {}).get("FIPS")
    if not fips or len(fips) < 11:
        return None
    return {"state": fips[:2], "county": fips[2:5], "tract": fips[5:11]}


def get_tract_profile(lat: float, lon: float) -> Optional[dict]:
    tract = _tract_from_latlon(lat, lon)
    if not tract:
        return None
    params = {
        "get": ACS_VARS,
        "for": f"tract:{tract['tract']}",
        "in": f"state:{tract['state']} county:{tract['county']}",
    }
    key = get_settings().census_api_key
    if key:
        params["key"] = key
    data = cached_get_json(
        f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5",
        params=params,
        cache_prefix="census:acs5",
    )
    if not data or len(data) < 2:
        return None
    row = dict(zip(data[0], data[1]))
    income = row.get("B19013_001E")
    population = row.get("B01003_001E")
    return {
        "median_household_income": float(income) if income and float(income) > 0 else None,
        "population": int(population) if population else None,
        "acs_year": ACS_YEAR,
        **tract,
    }
