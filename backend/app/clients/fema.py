"""FEMA National Flood Hazard Layer: flood zone at a point (no key required).
Zones starting with A or V are Special Flood Hazard Areas (insurance typically
required for federally backed mortgages); X is minimal/moderate risk.
"""
from __future__ import annotations

from typing import Optional

from app.clients.http import cached_get_json

NFHL_QUERY = (
    "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
)

HIGH_RISK_PREFIXES = ("A", "V")


def get_flood_zone(lat: float, lon: float) -> Optional[dict]:
    data = cached_get_json(
        NFHL_QUERY,
        params={
            "geometry": f"{lon},{lat}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY",
            "returnGeometry": "false",
            "f": "json",
        },
        cache_prefix="fema:nfhl",
    )
    features = (data or {}).get("features") or []
    if not features:
        return {"zone": None, "high_risk": None, "note": "No NFHL data at this point"}
    zone = features[0].get("attributes", {}).get("FLD_ZONE")
    return {
        "zone": zone,
        "subtype": features[0].get("attributes", {}).get("ZONE_SUBTY"),
        "high_risk": bool(zone) and zone.upper().startswith(HIGH_RISK_PREFIXES),
    }
