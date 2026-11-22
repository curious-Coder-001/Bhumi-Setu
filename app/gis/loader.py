"""
Geospatial Data Loader for Bhumi-Setu.
Loads prepared GeoJSON layers from the qgis/ directory, validates geometries,
and transforms CRS from EPSG:7755 to EPSG:4326 for interactive web map rendering.
"""
from pathlib import Path
from typing import Dict, Optional
import geopandas as gpd

from app.config import (
    DISTRICTS_GEOJSON,
    KAMRUP_METRO_GEOJSON,
    AZARA_CIRCLE_GEOJSON,
    AZARA_VILLAGES_GEOJSON,
    DHARAPUR_VILLAGE_GEOJSON,
    KAMRUP_METRO_VILLAGES_GEOJSON,
    TARGET_CRS,
)

# Global in-memory cache to avoid disk re-reads and redundant reprojections
_GEO_CACHE: Dict[str, gpd.GeoDataFrame] = {}


def load_geojson_layer(file_path: Path, cache_key: Optional[str] = None) -> gpd.GeoDataFrame:
    """
    Reads a GeoJSON file, verifies CRS, reprojects to EPSG:4326 if necessary,
    and returns a clean GeoDataFrame.
    """
    key = cache_key or str(file_path)
    if key in _GEO_CACHE:
        return _GEO_CACHE[key].copy()

    if not file_path.exists():
        raise FileNotFoundError(f"Geospatial dataset not found at expected path: {file_path}")

    # Read dataset
    gdf = gpd.read_file(file_path)

    # Clean string column names (strip trailing newlines or spaces from QGIS exports)
    gdf.columns = [c.strip() for c in gdf.columns]

    # Validate and reproject to EPSG:4326 (WGS84 Lat/Lon for web map display)
    if gdf.crs is None:
        # Source data from QGIS project is known EPSG:7755
        gdf = gdf.set_crs(epsg=7755)

    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(TARGET_CRS)

    # Cache the reprojected result
    _GEO_CACHE[key] = gdf
    return gdf.copy()


def get_assam_districts() -> gpd.GeoDataFrame:
    """Returns all 33 Assam districts in EPSG:4326."""
    return load_geojson_layer(DISTRICTS_GEOJSON, cache_key="assam_districts")


def get_kamrup_metro_boundary() -> gpd.GeoDataFrame:
    """Returns Kamrup Metropolitan district boundary in EPSG:4326."""
    return load_geojson_layer(KAMRUP_METRO_GEOJSON, cache_key="kamrup_metro")


def get_azara_circle_boundary() -> gpd.GeoDataFrame:
    """Returns Azara revenue circle boundary in EPSG:4326."""
    return load_geojson_layer(AZARA_CIRCLE_GEOJSON, cache_key="azara_circle")


def get_azara_villages() -> gpd.GeoDataFrame:
    """Returns all 28 villages in Azara circle in EPSG:4326."""
    return load_geojson_layer(AZARA_VILLAGES_GEOJSON, cache_key="azara_villages")


def get_dharapur_village() -> gpd.GeoDataFrame:
    """Returns the verified Dharapur village boundary in EPSG:4326."""
    return load_geojson_layer(DHARAPUR_VILLAGE_GEOJSON, cache_key="dharapur_village")


def get_kamrup_metro_villages() -> gpd.GeoDataFrame:
    """Returns all villages in Kamrup Metro district in EPSG:4326."""
    return load_geojson_layer(KAMRUP_METRO_VILLAGES_GEOJSON, cache_key="kamrup_metro_villages")
