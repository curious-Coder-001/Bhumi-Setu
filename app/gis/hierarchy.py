"""
Administrative Hierarchy Service for Bhumi-Setu.
Provides structured cascading navigation:
State (Assam) -> District (Kamrup Metropolitan) -> Circle (Azara) -> Village (Dharapur).
"""
from typing import List, Dict, Optional
from app.gis.loader import (
    get_assam_districts,
    get_kamrup_metro_villages,
    get_azara_villages
)

# Standard administrative aliases for clean UI presentation
DISTRICT_DISPLAY_MAP = {
    "Kamrup Metro": "Kamrup Metropolitan",
    "Kamrup": "Kamrup Rural"
}
DISTRICT_REVERSE_MAP = {v: k for k, v in DISTRICT_DISPLAY_MAP.items()}

VILLAGE_DISPLAY_MAP = {
    "Dharapur CT": "Dharapur",
    "Azara CT": "Azara",
    "Garal CT": "Garal",
    "Majir Gaon CT": "Majir Gaon",
    "Kahi Kuchi CT": "Kahikuchi"
}
VILLAGE_REVERSE_MAP = {v: k for k, v in VILLAGE_DISPLAY_MAP.items()}


def get_states() -> List[str]:
    """Returns available states (currently Assam for prototype)."""
    return ["Assam"]


def get_districts(state: str = "Assam") -> List[str]:
    """Returns sorted list of districts for the selected state."""
    if state != "Assam":
        return []
    gdf = get_assam_districts()
    raw_districts = sorted(gdf["district"].dropna().unique().tolist())
    # Format with clean display names
    display_districts = [DISTRICT_DISPLAY_MAP.get(d, d) for d in raw_districts]
    return sorted(display_districts)


def get_circles(district: str) -> List[str]:
    """Returns revenue circles / subdistricts for a selected district."""
    # Resolve display name back to dataset name
    db_district = DISTRICT_REVERSE_MAP.get(district, district)
    
    if db_district == "Kamrup Metro":
        # Circles confirmed from Kamrup Metro village boundary data
        return ["Azara", "Chandrapur", "Dispur", "Guwahati", "Sonapur"]
    return []


def get_villages(district: str, circle: str) -> List[str]:
    """Returns villages belonging to a specific circle."""
    db_district = DISTRICT_REVERSE_MAP.get(district, district)

    if db_district == "Kamrup Metro" and circle == "Azara":
        gdf = get_azara_villages()
        raw_villages = sorted(gdf["village"].dropna().unique().tolist())
        return [VILLAGE_DISPLAY_MAP.get(v, v) for v in raw_villages]
    
    return []


def resolve_village_dataset_name(display_name: str) -> str:
    """Resolves a user-friendly display name (e.g. 'Dharapur') to dataset name (e.g. 'Dharapur CT')."""
    return VILLAGE_REVERSE_MAP.get(display_name, display_name)


def resolve_district_dataset_name(display_name: str) -> str:
    """Resolves a user-friendly display name (e.g. 'Kamrup Metropolitan') to dataset name (e.g. 'Kamrup Metro')."""
    return DISTRICT_REVERSE_MAP.get(display_name, display_name)
