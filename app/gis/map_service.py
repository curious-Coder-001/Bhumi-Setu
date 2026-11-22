"""
Interactive Map Builder for Bhumi-Setu using Folium.
Renders official administrative and village boundaries in EPSG:4326.
Strictly adheres to GIS constraints:
- Displays ONLY verified village boundaries.
- DOES NOT generate fake parcel geometries, coordinates, or parcel centroid markers.
"""
from typing import Optional, Tuple
import folium
from folium import plugins
import geopandas as gpd

from app.gis.loader import get_dharapur_village, get_azara_circle_boundary


def create_village_map(
    village_gdf: Optional[gpd.GeoDataFrame] = None,
    show_circle_context: bool = True
) -> folium.Map:
    """
    Constructs an interactive Folium map centered on Dharapur village.
    
    Layers included:
    1. Base Layers: OpenStreetMap and Esri World Imagery (Satellite).
    2. Circle Boundary (Azara) for geographic context (optional subtle outline).
    3. Dharapur Village Boundary (verified Survey of India polygon).
    
    NO fake Dag 1 parcel polygons or parcel centroid markers are generated.
    """
    gdf = village_gdf if village_gdf is not None else get_dharapur_village()

    # Calculate bounding box for auto-zoom
    minx, miny, maxx, maxy = gdf.total_bounds
    center_lat = (miny + maxy) / 2.0
    center_lon = (minx + maxx) / 2.0

    # Initialize Folium Map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles=None,
        control_scale=True
    )

    # Base Tile 1: OpenStreetMap
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Street Map (OSM)",
        control=True
    ).add_to(m)

    # Base Tile 2: Esri Satellite Imagery
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, Maxar, Earthstar Geographics, and the GIS User Community",
        name="Satellite Imagery (Esri)",
        control=True
    ).add_to(m)

    # Optional Circle Context (Azara boundary outline)
    if show_circle_context:
        try:
            circle_gdf = get_azara_circle_boundary()
            folium.GeoJson(
                circle_gdf,
                name="Azara Circle Boundary",
                style_function=lambda x: {
                    "fillColor": "transparent",
                    "color": "#64748B",  # Slate gray
                    "weight": 1.5,
                    "dashArray": "4, 4",
                    "fillOpacity": 0.0
                },
                tooltip=folium.Tooltip("Azara Revenue Circle Boundary")
            ).add_to(m)
        except Exception:
            pass  # Non-fatal if circle boundary is unavailable

    # Verified Village Boundary (Dharapur CT)
    row = gdf.iloc[0]
    village_name = row.get("village", "Dharapur")
    vlcode = row.get("vlcode", "303423")
    subdistrict = row.get("subdistric", "Azara")
    district = row.get("district", "Kamrup Metro")
    src_agency = row.get("src_agency", "Survey of India (SOI)")

    popup_html = f"""
    <div style="font-family: Arial, sans-serif; min-width: 200px; font-size: 13px;">
        <h4 style="margin: 0 0 8px 0; color: #1E3A8A; border-bottom: 2px solid #3B82F6; padding-bottom: 4px;">
            {village_name}
        </h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="color: #64748B;">Census Code:</td><td><b>{vlcode}</b></td></tr>
            <tr><td style="color: #64748B;">Circle:</td><td><b>{subdistrict}</b></td></tr>
            <tr><td style="color: #64748B;">District:</td><td><b>{district}</b></td></tr>
            <tr><td style="color: #64748B;">Boundary Source:</td><td><b>{src_agency}</b></td></tr>
            <tr><td style="color: #64748B;">CRS:</td><td>EPSG:7755 &rarr; EPSG:4326</td></tr>
        </table>
        <div style="margin-top: 8px; padding: 4px 6px; background-color: #FEF3C7; border-left: 3px solid #D97706; font-size: 11px; color: #92400E;">
            Cadastral Dag parcels pending vector integration.
        </div>
    </div>
    """

    folium.GeoJson(
        gdf,
        name=f"Village Boundary: {village_name}",
        style_function=lambda x: {
            "fillColor": "#3B82F6",    # Blue fill
            "color": "#1D4ED8",        # Deep blue border
            "weight": 2.5,
            "fillOpacity": 0.20
        },
        highlight_function=lambda x: {
            "fillColor": "#60A5FA",
            "color": "#1E40AF",
            "weight": 3.5,
            "fillOpacity": 0.35
        },
        tooltip=folium.Tooltip(
            f"<b>{village_name}</b> (Click for SOI administrative metadata)",
            sticky=True
        ),
        popup=folium.Popup(popup_html, max_width=320)
    ).add_to(m)

    # Fit bounds directly to the village perimeter with padding
    m.fit_bounds([[miny, minx], [maxy, maxx]], padding=[20, 20])

    # Add Layer Control and Fullscreen toggle
    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    plugins.Fullscreen(position="topleft").add_to(m)

    return m
