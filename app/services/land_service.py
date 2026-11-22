
"""
Land Record Service for Bhumi-Setu.
Coordinates exact land-record matching, validation,
area comparison computations, and cadastral limitation labeling.
"""

from typing import Optional, Dict, Any, Tuple

from app.db.models import LandRecord
from app.db.database import (
    search_land_record,
    get_all_records_for_village
)
from app.gis.hierarchy import (
    resolve_district_dataset_name,
    resolve_village_dataset_name
)


class LandRecordService:
    """Business logic for land record lookups and verification summaries."""

    @staticmethod
    def search_record(
        district: str,
        circle: str,
        village: str,
        dag_number: str,
        patta_number: str,
        state: str = "Assam"
    ) -> Tuple[Optional[LandRecord], Optional[str]]:
        """
        Searches using all six administrative and land-record fields.
        Returns (record, error_message).
        """

        if not state or not district or not circle or not village:
            return None, (
                "Please complete all administrative selections: "
                "State, District, Revenue Circle and Village."
            )

        dag_clean = str(dag_number).strip() if dag_number else ""
        patta_clean = str(patta_number).strip() if patta_number else ""

        if not dag_clean or not patta_clean:
            return None, (
                "Both Dag Number and Patta Number are required."
            )

        # Resolve user-friendly names to dataset/database names.
        db_district = resolve_district_dataset_name(district)
        db_village = resolve_village_dataset_name(village)

        # Search using the normalized administrative hierarchy.
        record = search_land_record(
            state=state.strip(),
            district=db_district.strip(),
            circle=circle.strip(),
            village=db_village.strip(),
            dag_number=dag_clean,
            patta_number=patta_clean
        )

        # Also try the display names where database records
        # may have been stored using those names.
        if not record:
            record = search_land_record(
                state=state.strip(),
                district=district.strip(),
                circle=circle.strip(),
                village=village.strip(),
                dag_number=dag_clean,
                patta_number=patta_clean
            )

        if not record:
            available = get_all_records_for_village(
                village=db_village,
                district=db_district,
                circle=circle,
                state=state
            )

            hint_str = ""

            if available:
                examples = [
                    f"Dag {r.dag_number} / Patta {r.patta_number}"
                    for r in available
                ]
                hint_str = (
                    " Available records in this location: "
                    + ", ".join(examples)
                )

            return None, (
                f"No exact land record found for Dag '{dag_clean}' "
                f"and Patta '{patta_clean}' in {village}, "
                f"{circle}, {district}, {state}."
                f"{hint_str}"
            )

        return record, None

    @staticmethod
    def get_area_comparison_metrics(
        record: LandRecord
    ) -> Dict[str, Any]:
        """Extracts technical area comparison metrics."""

        recorded = record.recorded_area_sqm
        manual = record.manual_measurement_sqm
        diff = record.area_difference_sqm
        pct = record.area_difference_pct

        status_text = "Match Within Tolerance (Preliminary)"
        status_color = "normal"

        if diff is not None:
            if abs(diff) > 5.0:
                status_text = "Significant Discrepancy"
                status_color = "inverse"
            elif abs(diff) > 0.0:
                status_text = f"Minor Variance ({diff:+.2f} m²)"

        return {
            "recorded_area_sqm": recorded,
            "manual_measurement_sqm": manual,
            "diff_sqm": diff,
            "diff_pct": pct,
            "recorded_assam_units": record.recorded_area_assam_units,
            "status_text": status_text,
            "status_color": status_color,
            "source": record.source,
            "classification": record.land_classification,
            "disclaimer": (
                "Notice: Manual map measurement is an approximate "
                "spatial estimate for prototype demonstration. "
                "It does not constitute an official cadastral "
                "re-survey or legal verification."
            )
        }
