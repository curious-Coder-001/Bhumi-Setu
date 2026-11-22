"""
Database seeding module for Bhumi-Setu.
Inserts the competition demonstration land record (Dharapur Dag 1 / Patta 1)
with strict adherence to demonstration labels and verification disclaimers.
"""
from typing import Optional
from pathlib import Path
from app.db.database import get_db_connection, init_db


def seed_demo_records(db_path: Optional[Path] = None) -> None:
    """Seeds the demonstration land records into SQLite."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    demo_records = [
        {
            "state": "Assam",
            "district": "Kamrup Metropolitan",
            "circle": "Azara",
            "village": "Dharapur",
            "vlcode": "303423",
            "dag_number": "1",
            "patta_number": "1",
            "patta_type": "Periodic Patta (Myadi)",
            "recorded_area_sqm": 448.37,
            "manual_measurement_sqm": 448.15,
            "land_classification": "Bakhasthan-3",
            "source": "BhuNaksha Assam",
            "cadastral_geometry_status": "Cadastral parcel vector pending field survey / digitization. Village boundary confirmed.",
            "has_parcel_polygon": 0,
            "is_demo_data": 1,
            "verification_status": "Demonstration Data - Preliminary Comparison Only (Not Legal Title Verification)",
            "notes": (
                "Competition demonstration record. Manual map measurement was ~448.15 sq. m. "
                "The observed variance of -0.22 sq. m. (-0.05%) represents a preliminary area comparison "
                "for technical demonstration purposes, not a legal title verification or official survey result."
            )
        }
    ]

    for rec in demo_records:
        cursor.execute("""
        INSERT INTO land_records (
            state, district, circle, village, vlcode, dag_number, patta_number,
            patta_type, recorded_area_sqm, manual_measurement_sqm, land_classification,
            source, cadastral_geometry_status, has_parcel_polygon, is_demo_data,
            verification_status, notes
        ) VALUES (
            :state, :district, :circle, :village, :vlcode, :dag_number, :patta_number,
            :patta_type, :recorded_area_sqm, :manual_measurement_sqm, :land_classification,
            :source, :cadastral_geometry_status, :has_parcel_polygon, :is_demo_data,
            :verification_status, :notes
        )
        ON CONFLICT(village, dag_number, patta_number) DO UPDATE SET
            state = excluded.state,
            district = excluded.district,
            circle = excluded.circle,
            vlcode = excluded.vlcode,
            patta_type = excluded.patta_type,
            recorded_area_sqm = excluded.recorded_area_sqm,
            manual_measurement_sqm = excluded.manual_measurement_sqm,
            land_classification = excluded.land_classification,
            source = excluded.source,
            cadastral_geometry_status = excluded.cadastral_geometry_status,
            has_parcel_polygon = excluded.has_parcel_polygon,
            is_demo_data = excluded.is_demo_data,
            verification_status = excluded.verification_status,
            notes = excluded.notes;
        """, rec)

    conn.commit()
    conn.close()
    print("Demo land record seeded successfully.")


if __name__ == "__main__":
    seed_demo_records()
