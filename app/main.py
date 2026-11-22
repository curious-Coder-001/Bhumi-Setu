"""
Bhumi-Setu — Streamlit Frontend
GIS-Integrated, Government-Verified Digital Land Marketplace for Assam

Entry point:
F:\\Bhumi-Setu\\.venv\\Scripts\\streamlit.exe run app/main.py
"""

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so app.* imports work from anywhere.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st
from streamlit_folium import st_folium

from app.ui.due_diligence import render_due_diligence_dashboard
from app.config import APP_TITLE, APP_SUBTITLE, APP_VERSION
from app.db.seed_data import seed_demo_records
from app.gis.hierarchy import (
    get_states,
    get_districts,
    get_circles,
    get_villages,
)
from app.gis.map_service import create_village_map
from app.services.land_service import LandRecordService


# ===========================================================================
# PAGE CONFIGURATION
# ===========================================================================
st.set_page_config(
    page_title="Bhumi-Setu | Assam Land Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            f"**Bhumi-Setu** v0.1.0-prototype\n\n"
            "GIS-Integrated Digital Land Marketplace for Assam. "
            "Prototype demonstration only. Not legal land title verification."
        )
    },
)


# ===========================================================================
# CUSTOM CSS — Government-facing professional palette
# ===========================================================================
st.markdown(
    """
<style>
html, body, [class*="css"] {
    font-family: 'Segoe UI', Arial, sans-serif;
}
.bs-header {
    background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 60%, #2563EB 100%);
    padding: 1.4rem 2rem 1.2rem 2rem;
    border-radius: 10px;
    margin-bottom: 1.2rem;
    color: white;
}
.bs-header h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: white;
}
.bs-header p {
    margin: 0.3rem 0 0 0;
    font-size: 0.95rem;
    color: #BFDBFE;
}
.bs-badge {
    display: inline-block;
    background: #FEF3C7;
    color: #92400E;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
    margin-top: 0.5rem;
    letter-spacing: 0.03em;
}
.bs-section-title {
    font-size: 1.0rem;
    font-weight: 700;
    color: #1E3A8A;
    border-left: 4px solid #2563EB;
    padding-left: 0.6rem;
    margin: 1.0rem 0 0.6rem 0;
}
.bs-record-card {
    background: #F0F7FF;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
}
.bs-record-label {
    font-size: 0.75rem;
    color: #64748B;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.bs-record-value {
    font-size: 1.0rem;
    color: #1E293B;
    font-weight: 600;
    margin-top: 2px;
}
.bs-passport {
    background: white;
    border: 2px solid #1D4ED8;
    border-radius: 12px;
    padding: 1.4rem;
    margin-top: 0.6rem;
    box-shadow: 0 2px 10px rgba(29,78,216,0.08);
}
.bs-passport-title {
    font-size: 1.0rem;
    font-weight: 700;
    color: #1E3A8A;
    margin: 0 0 0.2rem 0;
}
.bs-passport-subtitle {
    font-size: 0.75rem;
    color: #64748B;
    margin: 0;
}
.bs-tag-gov {
    display: inline-block;
    background: #DBEAFE;
    color: #1E40AF;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    margin-right: 4px;
}
.bs-tag-demo {
    display: inline-block;
    background: #FEF3C7;
    color: #92400E;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    margin-right: 4px;
}
.bs-metric-box {
    background: #EFF6FF;
    border: 1px solid #93C5FD;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    text-align: center;
}
.bs-metric-num {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1D4ED8;
    line-height: 1.1;
}
.bs-metric-label {
    font-size: 0.72rem;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-top: 2px;
}
.bs-gis-note {
    background: #FFF7ED;
    border-left: 4px solid #F59E0B;
    border-radius: 4px;
    padding: 0.6rem 0.8rem;
    font-size: 0.8rem;
    color: #78350F;
    margin-top: 0.5rem;
}
.bs-demo-banner {
    background: #FEF3C7;
    border: 1px solid #FCD34D;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.82rem;
    color: #78350F;
    margin-bottom: 0.6rem;
}
.bs-nav-label {
    font-size: 0.72rem;
    color: #94A3B8;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0.5rem 0 0.3rem 0;
}
.stDeployButton { display: none !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ===========================================================================
# STARTUP: Ensure DB is seeded (idempotent upsert — safe on every run)
# ===========================================================================
@st.cache_resource(show_spinner=False)
def _bootstrap_db() -> str:
    """Ensure the demo record is present in the database."""
    try:
        seed_demo_records()
        return "ok"
    except Exception as exc:
        return f"error: {exc}"


_db_status = _bootstrap_db()


# ===========================================================================
# CACHED DATA LOADERS
# ===========================================================================
@st.cache_data(show_spinner=False)
def _get_states():
    return get_states()


@st.cache_data(show_spinner=False)
def _get_districts(state: str):
    return get_districts(state)


@st.cache_data(show_spinner=False)
def _get_circles(district: str):
    return get_circles(district)


@st.cache_data(show_spinner=False)
def _get_villages(district: str, circle: str):
    return get_villages(district, circle)


def _build_map():
    """Build the Folium map once and cache it."""
    return create_village_map(village_gdf=None, show_circle_context=True)


# ===========================================================================
# SEARCH-FIELD PERSISTENCE
# ===========================================================================
SEARCH_STATE_FILE = _PROJECT_ROOT / "search_state.json"

SEARCH_FIELD_KEYS = (
    "sel_state",
    "sel_district",
    "sel_circle",
    "sel_village",
    "dag_input",
    "patta_input",
)


def _load_saved_search_state() -> dict:
    """Load the six saved search fields. Invalid/missing files are ignored."""
    if not SEARCH_STATE_FILE.exists():
        return {}

    try:
        data = json.loads(SEARCH_STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {
                key: data[key]
                for key in SEARCH_FIELD_KEYS
                if key in data
            }
    except (OSError, json.JSONDecodeError):
        pass

    return {}


def _init_state():

    """Initialize Streamlit state without overwriting existing widget values."""
    defaults = {
        "search_triggered": False,
        "search_result": None,
        "search_error": None,
        "sel_state": None,
        "sel_district": "— Select District —",
        "sel_circle": "— Select Circle —",
        "sel_village": "— Select Village —",
        "dag_input": "",
        "patta_input": "",
    }

    saved_values = _load_saved_search_state()
    defaults.update(saved_values)

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _save_search_state():
    """Save only the six search fields to the local JSON file."""
    saved_data = {
        key: st.session_state.get(key)
        for key in SEARCH_FIELD_KEYS
    }

    try:
        SEARCH_STATE_FILE.write_text(
            json.dumps(saved_data, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        # Keep the app usable even if the local file cannot be written.
        st.session_state["search_state_save_error"] = str(exc)


def _on_search_field_change():
    """Streamlit callback: persist values after a widget changes."""
    _save_search_state()


_init_state()
# Load a land record selected from the marketplace
passport_request = st.session_state.pop(
    "passport_request",
    None
)

if passport_request:
    st.session_state["sel_state"] = passport_request["state"]
    st.session_state["passport_review_status"] = passport_request.get(
        "review_status",
        "Not Submitted"
    )
    st.session_state["sel_district"] = passport_request["district"]
    st.session_state["sel_circle"] = passport_request["circle"]
    st.session_state["sel_village"] = passport_request["village"]
    st.session_state["dag_input"] = str(passport_request["dag_number"])
    st.session_state["patta_input"] = str(passport_request["patta_number"])
    st.session_state["passport_search_pending"] = True

# ===========================================================================
# HEADER BANNER
# ===========================================================================
st.html(
    f"""
<div class="bs-header">
    <h1>&#127963; {APP_TITLE}</h1>
    <p>{APP_SUBTITLE}</p>
    <span class="bs-badge">&#9888;&#65039; PROTOTYPE DEMONSTRATION &mdash; NOT A LEGAL LAND REGISTRY SERVICE</span>
</div>
"""
)


# ===========================================================================
# SIDEBAR — SEARCH PANEL
# ===========================================================================
with st.sidebar:
    st.markdown(
        '<p class="bs-nav-label">Land Record Search</p>',
        unsafe_allow_html=True,
    )

    if _db_status != "ok":
        st.error(f"Database initialisation issue: {_db_status}")

    # -----------------------------------------------------------------------
    # Administrative hierarchy — cascading selectors
    # -----------------------------------------------------------------------
    states = list(_get_states() or [])

    # Validate restored State against the currently available options.
    if states:
        if st.session_state.sel_state not in states:
            st.session_state.sel_state = states[0]
    else:
        st.session_state.sel_state = None

    if states:
        sel_state = st.selectbox(
            "State",
            options=states,
            key="sel_state",
            help="Currently Assam is supported in this prototype.",
            on_change=_on_search_field_change,
        )
    else:
        st.warning("No State data is currently available.")
        sel_state = None

    districts = list(_get_districts(sel_state) or []) if sel_state else []
    district_options = ["— Select District —"] + districts

    if st.session_state.sel_district not in district_options:
        st.session_state.sel_district = "— Select District —"

    sel_district_raw = st.selectbox(
        "District",
        options=district_options,
        key="sel_district",
        help="Select a district within the chosen state.",
        on_change=_on_search_field_change,
    )
    sel_district = (
        sel_district_raw
        if sel_district_raw != "— Select District —"
        else None
    )

    circles = list(_get_circles(sel_district) or []) if sel_district else []
    circle_options = ["— Select Circle —"] + circles

    if st.session_state.sel_circle not in circle_options:
        st.session_state.sel_circle = "— Select Circle —"

    sel_circle_raw = st.selectbox(
        "Revenue Circle",
        options=circle_options,
        key="sel_circle",
        help="Revenue circles vary by district. Only Azara circle has demo data.",
        on_change=_on_search_field_change,
    )
    sel_circle = (
        sel_circle_raw
        if sel_circle_raw != "— Select Circle —"
        else None
    )

    villages = (
        list(_get_villages(sel_district, sel_circle) or [])
        if sel_district and sel_circle
        else []
    )
    village_options = ["— Select Village —"] + villages

    if st.session_state.sel_village not in village_options:
        st.session_state.sel_village = "— Select Village —"

    sel_village_raw = st.selectbox(
        "Village",
        options=village_options,
        key="sel_village",
        help="Villages are populated from the GIS boundary dataset.",
        on_change=_on_search_field_change,
    )
    sel_village = (
        sel_village_raw
        if sel_village_raw != "— Select Village —"
        else None
    )

    st.divider()

    st.markdown(
        '<p class="bs-nav-label">Parcel Identifiers</p>',
        unsafe_allow_html=True,
    )

    dag_input = st.text_input(
        "Dag Number",
        placeholder="e.g. 1",
        key="dag_input",
        help="Enter the cadastral Dag number.",
        on_change=_on_search_field_change,
    )

    patta_input = st.text_input(
        "Patta Number",
        placeholder="e.g. 1",
        key="patta_input",
        help="Enter the Patta number associated with the Dag.",
        on_change=_on_search_field_change,
    )

    st.divider()

    # -----------------------------------------------------------------------
    # Search button
    # -----------------------------------------------------------------------
    search_clicked = st.button(
        "Search Land Record",
        use_container_width=True,
        type="primary",
        disabled=(
            not sel_village
            or not dag_input.strip()
            or not patta_input.strip()
        ),
    )

    if search_clicked or st.session_state.pop("passport_search_pending", False):
        with st.spinner("Querying land registry database..."):
            record, error = LandRecordService.search_record(
   			 state=sel_state or "",
   			 district=sel_district or "",
  		         circle=sel_circle or "",
    			 village=sel_village or "",
    			 dag_number=dag_input.strip(),
    			 patta_number=patta_input.strip(),
)

        st.session_state.search_triggered = True
        st.session_state.search_result = record
        st.session_state.search_error = error

    # -----------------------------------------------------------------------
    # Clear results
    # -----------------------------------------------------------------------
    if st.session_state.search_triggered:
        if st.button("Clear Results", use_container_width=True):
            st.session_state.search_triggered = False
            st.session_state.search_result = None
            st.session_state.search_error = None
            st.rerun()

    st.divider()

    with st.expander("Demo Data Hint", expanded=False):
        st.markdown(
            """
**Available demo record:**

| Field | Value |
|---|---|
| District | Kamrup Metropolitan |
| Circle | Azara |
| Village | Dharapur |
| Dag | **1** |
| Patta | **1** |

This is the only record in the prototype database.
"""
        )

    st.markdown(
        f"<br><small style='color:#94A3B8'>{APP_VERSION}</small>",
        unsafe_allow_html=True,
    )


# ===========================================================================
# MAIN CONTENT AREA — Two-column layout
# ===========================================================================
left_col, right_col = st.columns([1.05, 1.0], gap="large")


# ===========================================================================
# LEFT COLUMN: Search results + Digital Land Passport
# ===========================================================================
with left_col:
    if not st.session_state.search_triggered:
        st.markdown(
            '<div class="bs-section-title">Land Parcel Information</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
<div class="bs-record-card" style="text-align:center; padding: 2.5rem 1.5rem; color: #94A3B8;">
    <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">&#128203;</div>
    <div style="font-weight: 600; font-size: 1rem; color: #64748B;">No parcel selected</div>
    <div style="font-size: 0.85rem; margin-top: 0.4rem;">
        Use the search panel on the left to look up a land record by<br>
        administrative hierarchy, Dag Number, and Patta Number.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    elif st.session_state.search_error:
        st.markdown(
            '<div class="bs-section-title">Search Result</div>',
            unsafe_allow_html=True,
        )
        st.error(f"{st.session_state.search_error}")
        st.info(
            "Only the Azara circle -> Dharapur village -> Dag 1 / Patta 1 "
            "record is available in this prototype database."
        )

    elif st.session_state.search_result is not None:
        record = st.session_state.search_result
        metrics = LandRecordService.get_area_comparison_metrics(record)

        if record.is_demo_data:
            st.markdown(
                """
<div class="bs-demo-banner">
    <strong>DEMONSTRATION DATA</strong> &mdash; This record is sourced from BhuNaksha Assam for prototype
    demonstration only. It does not constitute legal title verification or an official cadastral survey.
</div>
""",
                unsafe_allow_html=True,
            )

        # Government Land Record
        st.markdown(
            '<div class="bs-section-title">Government Land Record</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.html(
                f"""
<div class="bs-record-card">
    <div class="bs-record-label">State</div>
    <div class="bs-record-value">{record.state}</div>
    <div class="bs-record-label" style="margin-top:0.7rem">District</div>
    <div class="bs-record-value">{record.district}</div>
</div>
"""
            )

        with c2:
            st.html(
                f"""
<div class="bs-record-card">
    <div class="bs-record-label">Revenue Circle</div>
    <div class="bs-record-value">{record.circle}</div>
    <div class="bs-record-label" style="margin-top:0.7rem">Village</div>
    <div class="bs-record-value">{record.village}</div>
</div>
"""
            )

        with c3:
            st.html(
                f"""
<div class="bs-record-card">
    <div class="bs-record-label">Census Village Code</div>
    <div class="bs-record-value">{record.vlcode or "&mdash;"}</div>
    <div class="bs-record-label" style="margin-top:0.7rem">Patta Type</div>
    <div class="bs-record-value" style="font-size:0.88rem">{record.patta_type}</div>
</div>
"""
            )

        c4, c5, c6 = st.columns(3)

        with c4:
            st.html(
                f"""
<div class="bs-record-card">
    <div class="bs-record-label">Dag Number</div>
    <div class="bs-record-value" style="font-size:1.6rem">{record.dag_number}</div>
</div>
"""
            )

        with c5:
            st.html(
                f"""
<div class="bs-record-card">
    <div class="bs-record-label">Patta Number</div>
    <div class="bs-record-value" style="font-size:1.6rem">{record.patta_number}</div>
</div>
"""
            )

        with c6:
            st.html(
                f"""
<div class="bs-record-card">
    <div class="bs-record-label">Land Classification</div>
    <div class="bs-record-value">{record.land_classification}</div>
    <div class="bs-record-label" style="margin-top:0.7rem">Data Source</div>
    <div class="bs-record-value" style="font-size:0.85rem">{record.source}</div>
</div>
"""
            )

        # Area Comparison Metrics
        st.markdown(
            '<div class="bs-section-title">Area Comparison Metrics</div>',
            unsafe_allow_html=True,
        )

        cm1, cm2, cm3, cm4 = st.columns(4)

        with cm1:
            st.markdown(
                f"""
<div class="bs-metric-box">
    <div class="bs-metric-num">{metrics['recorded_area_sqm']:.2f}</div>
    <div class="bs-metric-label">Recorded (m&sup2;)</div>
</div>
""",
                unsafe_allow_html=True,
            )

        with cm2:
            manual_display = (
                f"{metrics['manual_measurement_sqm']:.2f}"
                if metrics["manual_measurement_sqm"] is not None
                else "&mdash;"
            )
            st.markdown(
                f"""
<div class="bs-metric-box">
    <div class="bs-metric-num">{manual_display}</div>
    <div class="bs-metric-label">Map Measure (m&sup2;)</div>
</div>
""",
                unsafe_allow_html=True,
            )

        with cm3:
            diff_display = (
                f"{metrics['diff_sqm']:+.2f}"
                if metrics["diff_sqm"] is not None
                else "&mdash;"
            )
            pct_display = (
                f"({metrics['diff_pct']:+.3f}%)"
                if metrics["diff_pct"] is not None
                else ""
            )
            st.markdown(
                f"""
<div class="bs-metric-box">
    <div class="bs-metric-num" style="font-size:1.2rem">{diff_display}</div>
    <div class="bs-metric-label">Variance (m&sup2;) {pct_display}</div>
</div>
""",
                unsafe_allow_html=True,
            )

        with cm4:
            st.markdown(
                f"""
<div class="bs-metric-box">
    <div class="bs-metric-num" style="font-size:0.95rem; line-height:1.3">{metrics['recorded_assam_units']}</div>
    <div class="bs-metric-label">Traditional Units</div>
</div>
""",
                unsafe_allow_html=True,
            )

        status_color_map = {
            "normal": "#16A34A",
            "inverse": "#DC2626",
        }
        status_color = status_color_map.get(
            metrics["status_color"],
            "#64748B",
        )

        st.markdown(
            f"""
<div style="margin:0.5rem 0 0.3rem 0; padding:0.4rem 0.9rem; background:#F8FAFC;
     border:1px solid #E2E8F0; border-radius:6px; display:inline-block;
     color:{status_color}; font-weight:700; font-size:0.85rem;">
    Status: {metrics['status_text']}
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div class="bs-gis-note">
    {metrics['disclaimer']}
</div>
""",
            unsafe_allow_html=True,
        )

        # Cadastral Geometry Status
        st.markdown(
            '<div class="bs-section-title">Cadastral Geometry Status</div>',
            unsafe_allow_html=True,
        )

        parcel_status_label = (
            "No cadastral parcel polygon available"
            if not record.has_parcel_polygon
            else "Parcel polygon available"
        )

        st.markdown(
            f"""
<div class="bs-record-card" style="padding: 0.9rem 1.1rem;">
    <div style="font-size:0.85rem; color:#1E293B; margin-bottom:0.4rem;">
        <strong>{parcel_status_label}</strong>
    </div>
    <div style="font-size:0.82rem; color:#64748B;">{record.cadastral_geometry_status}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        # Digital Land Passport
        st.markdown(
            '<div class="bs-section-title">Digital Land Passport</div>',
            unsafe_allow_html=True,
        )

        area_diff_display = (
            f"{record.area_difference_sqm:+.2f} m&sup2; "
            f"({record.area_difference_pct:+.3f}%)"
            if record.area_difference_sqm is not None
            else "&mdash;"
        )

        manual_area_display = (
            f"{record.manual_measurement_sqm:.2f} m&sup2;"
            if record.manual_measurement_sqm is not None
            else "Not available"
        )

        cadaster_display = (
            "Parcel polygon available"
            if record.has_parcel_polygon
            else "Pending digitisation"
        )

        st.html(
            f"""
<div class="bs-passport">
    <div style="border-bottom: 2px solid #DBEAFE; padding-bottom: 0.7rem; margin-bottom: 0.9rem;">
        <p class="bs-passport-title">Digital Land Passport &mdash; {record.village}, {record.district}</p>
        <p class="bs-passport-subtitle">Bhumi-Setu Prototype &middot; For demonstration purposes only</p>
    </div>

    <div style="margin-bottom:0.8rem;">
        <span class="bs-tag-gov">GOV RECORD</span>
        <span style="font-size:0.75rem; color:#1E40AF; font-weight:600;">
            Fields sourced from BhuNaksha Assam government database
        </span>
    </div>
    <table style="width:100%; border-collapse:collapse; font-size:0.88rem; margin-bottom:1rem;">
        <tr style="background:#EFF6FF;">
            <td style="padding:5px 8px; color:#64748B; width:42%;">State</td>
            <td style="padding:5px 8px; font-weight:600; color:#1E293B;">{record.state}</td>
        </tr>
        <tr>
            <td style="padding:5px 8px; color:#64748B;">District</td>
            <td style="padding:5px 8px; font-weight:600; color:#1E293B;">{record.district}</td>
        </tr>
        <tr style="background:#EFF6FF;">
            <td style="padding:5px 8px; color:#64748B;">Revenue Circle</td>
            <td style="padding:5px 8px; font-weight:600; color:#1E293B;">{record.circle}</td>
        </tr>
        <tr>
            <td style="padding:5px 8px; color:#64748B;">Village / Census Code</td>
            <td style="padding:5px 8px; font-weight:600; color:#1E293B;">{record.village} / {record.vlcode or "&mdash;"}</td>
        </tr>
        <tr style="background:#EFF6FF;">
            <td style="padding:5px 8px; color:#64748B;">Dag Number</td>
            <td style="padding:5px 8px; font-weight:600; color:#1E293B;">{record.dag_number}</td>
        </tr>
        <tr>
            <td style="padding:5px 8px; color:#64748B;">Patta Number</td>
            <td style="padding:5px 8px; font-weight:600; color:#1E293B;">{record.patta_number}</td>
        </tr>
        <tr style="background:#EFF6FF;">
            <td style="padding:5px 8px; color:#64748B;">Patta Type</td>
            <td style="padding:5px 8px; font-weight:600; color:#1E293B;">{record.patta_type}</td>
        </tr>
        <tr>
            <td style="padding:5px 8px; color:#64748B;">Land Classification</td>
            <td style="padding:5px 8px; font-weight:600; color:#1E293B;">{record.land_classification}</td>
        </tr>
        <tr style="background:#EFF6FF;">
            <td style="padding:5px 8px; color:#64748B;">Recorded Area</td>
            <td style="padding:5px 8px; font-weight:600; color:#1E293B;">
                {record.recorded_area_sqm:.2f} m&sup2;
                <span style="font-weight:400; color:#64748B; margin-left:6px;">
                    ({record.recorded_area_assam_units})
                </span>
            </td>
        </tr>
        <tr>
            <td style="padding:5px 8px; color:#64748B;">Data Source</td>
            <td style="padding:5px 8px; font-weight:600; color:#1E293B;">{record.source}</td>
        </tr>
    </table>

    <div style="margin-bottom:0.5rem;">
        <span class="bs-tag-demo">PROTOTYPE ESTIMATE</span>
        <span style="font-size:0.75rem; color:#92400E; font-weight:600;">
            Fields derived from manual GIS map measurement &mdash; NOT an official survey
        </span>
    </div>
    <table style="width:100%; border-collapse:collapse; font-size:0.88rem; margin-bottom:0.9rem;">
        <tr style="background:#FFFBEB;">
            <td style="padding:5px 8px; color:#64748B; width:42%;">Map-Measured Area</td>
            <td style="padding:5px 8px; font-weight:600; color:#92400E;">{manual_area_display}</td>
        </tr>
        <tr>
            <td style="padding:5px 8px; color:#64748B;">Area Variance</td>
            <td style="padding:5px 8px; font-weight:600; color:#92400E;">{area_diff_display}</td>
        </tr>
        <tr style="background:#FFFBEB;">
            <td style="padding:5px 8px; color:#64748B;">Cadastral Geometry</td>
            <td style="padding:5px 8px; font-weight:600; color:#92400E;">{cadaster_display}</td>
        </tr>
        <tr>
            <td style="padding:5px 8px; color:#64748B;">Verification Status</td>
            <td style="padding:5px 8px; font-size:0.82rem; color:#92400E;">{record.verification_status}</td>
        </tr>
    </table>

    <div class="bs-gis-note" style="margin-top:0.3rem;">
        {record.notes}
    </div>

    <div style="margin-top:1rem; padding-top:0.7rem; border-top:1px solid #E2E8F0;
                font-size:0.72rem; color:#94A3B8; text-align:center;">
        This Digital Land Passport is a <strong>prototype demonstration artefact</strong>.
        It does not constitute legal ownership proof, official title certification,
        or a government-issued document. Official land records must be verified
        through the Government of Assam Revenue &amp; Disaster Management Department.
    </div>
</div>
"""
        )
        st.write(
            "**Marketplace Review Status:**",
            st.session_state.get("passport_review_status", "Not Submitted")
        )
        render_due_diligence_dashboard(record)

    else:
        st.warning(
            "The search was submitted, but no record object was returned. "
            "Please try the search again."
        )


# ===========================================================================
# RIGHT COLUMN: GIS MAP
# ===========================================================================
with right_col:
    st.markdown(
        '<div class="bs-section-title">GIS Boundary Map</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.search_result:
        r = st.session_state.search_result
        st.markdown(
            f"""
<div style="font-size:0.82rem; color:#475569; margin-bottom:0.5rem; padding: 0.4rem 0.7rem;
     background:#F1F5F9; border-radius:6px; border-left: 3px solid #2563EB;">
    Displaying SOI-verified village boundary for <strong>{r.village}</strong>,
    {r.circle} Circle, {r.district}.
    Use the layer control (top-right of map) to switch between Street Map and Satellite Imagery.
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
<div style="font-size:0.82rem; color:#475569; margin-bottom:0.5rem; padding: 0.4rem 0.7rem;
     background:#F1F5F9; border-radius:6px; border-left: 3px solid #2563EB;">
    Displaying Dharapur village boundary &mdash; the demo parcel is located within this area.
    Use the layer control (top-right of map) to switch between Street Map and Satellite Imagery.
</div>
""",
            unsafe_allow_html=True,
        )

    with st.spinner("Loading GIS boundary layers..."):
        folium_map = _build_map()

    st_folium(
        folium_map,
        width="100%",
        height=540,
        returned_objects=[],
        key="main_folium_map",
    )

    st.markdown(
        """
<div class="bs-gis-note">
    <strong>GIS Disclaimer:</strong> This map displays only the Survey of India (SOI) verified
    <em>village boundary</em> for Dharapur. Individual cadastral Dag parcel polygons are
    <strong>not available</strong> in this prototype &mdash; they are pending field survey and vector digitisation.
    No parcel boundaries or ownership markers are generated or implied by this map.
    Boundary data: EPSG:7755 (India National Grid) &rarr; reprojected to EPSG:4326 (WGS84).
</div>
""",
        unsafe_allow_html=True,
    )

    with st.expander("Map Layer Legend", expanded=False):
        st.markdown(
            """
| Layer | Description | Source |
|---|---|---|
| Village Boundary (blue fill) | Dharapur CT village polygon | Survey of India (SOI) |
| Dashed outline | Azara Revenue Circle boundary | QGIS export |
| Street Map | OpenStreetMap base tiles | OSM Contributors |
| Satellite | Esri World Imagery | Esri, Maxar |
"""
        )


# ===========================================================================
# FOOTER
# ===========================================================================
st.divider()

footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 1])

with footer_col1:
    st.markdown(
        f"""
<div style="font-size:0.78rem; color:#94A3B8;">
    <strong style="color:#64748B;">Bhumi-Setu</strong> {APP_VERSION} &middot;
    GIS data: Survey of India (SOI) &amp; NWIC &middot;
    Land records: BhuNaksha Assam
</div>
""",
        unsafe_allow_html=True,
    )

with footer_col2:
    st.markdown(
        """
<div style="font-size:0.78rem; color:#94A3B8; text-align:center;">
    CRS: EPSG:7755 &rarr; EPSG:4326
</div>
""",
        unsafe_allow_html=True,
    )

with footer_col3:
    st.markdown(
        """
<div style="font-size:0.78rem; color:#EF4444; text-align:right; font-weight:600;">
    PROTOTYPE ONLY
</div>
""",
        unsafe_allow_html=True,
    )
