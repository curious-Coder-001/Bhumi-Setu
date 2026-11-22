"""
Configuration settings for Bhumi-Setu prototype.
Manages file paths, CRS definitions, and application-level constants.
"""
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"
QGIS_DIR = BASE_DIR / "qgis"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DOCUMENTS_DIR = DATA_DIR / "documents"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
# Primary Geospatial Layer Files (using verified qgis/ exports)
DISTRICTS_GEOJSON = QGIS_DIR / "assam_districts.geojson"
KAMRUP_METRO_GEOJSON = QGIS_DIR / "kamrup_metro.geojson"
AZARA_CIRCLE_GEOJSON = QGIS_DIR / "azara.geojson"
AZARA_VILLAGES_GEOJSON = QGIS_DIR / "azara_village.geojson"
DHARAPUR_VILLAGE_GEOJSON = QGIS_DIR / "dharapur_village.geojson"
KAMRUP_METRO_VILLAGES_GEOJSON = QGIS_DIR / "kamrup_metro_village.geojson"

# SQLite Database Path
DATABASE_PATH = PROCESSED_DATA_DIR / "bhumi_setu.db"

# Coordinate Reference Systems
SOURCE_CRS = "EPSG:7755"   # India National Coordinate System (Lambert Conformal Conic)
TARGET_CRS = "EPSG:4326"   # WGS84 Geographic Lat/Lon for Leaflet / Folium web maps

# Application Metadata
APP_TITLE = "Bhumi-Setu"
APP_SUBTITLE = "GIS-Integrated, Government-Verified Digital Land Marketplace for Assam"
APP_VERSION = "0.1.0-prototype"

# Assam Default Map Center
ASSAM_CENTER_LAT = 26.2006
ASSAM_CENTER_LON = 92.9376
DEFAULT_ZOOM_STATE = 7
DEFAULT_ZOOM_DISTRICT = 10
DEFAULT_ZOOM_CIRCLE = 12
DEFAULT_ZOOM_VILLAGE = 14
