
"""
SQLite database management for Bhumi-Setu land records.
Provides schema creation, CRUD operations, and exact land-record search.
"""

import sqlite3
from typing import List, Optional
from pathlib import Path

from app.config import DATABASE_PATH
from app.db.models import LandRecord


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Creates a SQLite connection with Row factory enabled."""
    path = db_path or DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """Initializes the database without deleting existing records."""
    conn = get_db_connection(db_path)

    try:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS land_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state TEXT NOT NULL,
            district TEXT NOT NULL,
            circle TEXT NOT NULL,
            village TEXT NOT NULL,
            vlcode TEXT,
            dag_number TEXT NOT NULL,
            patta_number TEXT NOT NULL,
            patta_type TEXT DEFAULT 'Periodic Patta',
            recorded_area_sqm REAL NOT NULL,
            manual_measurement_sqm REAL,
            land_classification TEXT NOT NULL,
            source TEXT NOT NULL,
            cadastral_geometry_status TEXT NOT NULL,
            has_parcel_polygon INTEGER DEFAULT 0,
            is_demo_data INTEGER DEFAULT 1,
            verification_status TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(village, dag_number, patta_number)
        );
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_land_search
        ON land_records(
            state, district, circle, village,
            dag_number, patta_number
        );
        """)

        conn.commit()

    finally:
        conn.close()


def row_to_land_record(row: sqlite3.Row) -> LandRecord:
    """Converts an SQLite row into a LandRecord object."""

    return LandRecord(
        id=row["id"],
        state=row["state"],
        district=row["district"],
        circle=row["circle"],
        village=row["village"],
        vlcode=row["vlcode"] or "",
        dag_number=row["dag_number"],
        patta_number=row["patta_number"],
        patta_type=row["patta_type"] or "Periodic Patta",
        recorded_area_sqm=float(row["recorded_area_sqm"]),
        manual_measurement_sqm=(
            float(row["manual_measurement_sqm"])
            if row["manual_measurement_sqm"] is not None
            else None
        ),
        land_classification=row["land_classification"],
        source=row["source"],
        cadastral_geometry_status=row["cadastral_geometry_status"],
        has_parcel_polygon=bool(row["has_parcel_polygon"]),
        is_demo_data=bool(row["is_demo_data"]),
        verification_status=row["verification_status"],
        notes=row["notes"] or ""
    )


def search_land_record(
    district: str,
    circle: str,
    village: str,
    dag_number: str,
    patta_number: str,
    db_path: Optional[Path] = None,
    state: Optional[str] = None
) -> Optional[LandRecord]:
    """
    Searches using exact administrative and land-record fields.

    State is optional temporarily for backward compatibility.
    The updated LandRecordService will pass it explicitly.
    """

    conn = get_db_connection(db_path)

    try:
        cursor = conn.cursor()

        query = """
        SELECT *
        FROM land_records
        WHERE LOWER(TRIM(district)) = LOWER(TRIM(?))
          AND LOWER(TRIM(circle)) = LOWER(TRIM(?))
          AND LOWER(TRIM(village)) = LOWER(TRIM(?))
          AND TRIM(dag_number) = TRIM(?)
          AND TRIM(patta_number) = TRIM(?)
        """

        params = [
            district,
            circle,
            village,
            str(dag_number),
            str(patta_number)
        ]

        if state:
            query += """
              AND LOWER(TRIM(state)) = LOWER(TRIM(?))
            """
            params.append(state)

        query += " ORDER BY id ASC LIMIT 1;"

        cursor.execute(query, params)
        row = cursor.fetchone()

        return row_to_land_record(row) if row else None

    finally:
        conn.close()


def get_all_records_for_village(
    village: str,
    db_path: Optional[Path] = None,
    district: Optional[str] = None,
    circle: Optional[str] = None,
    state: Optional[str] = None
) -> List[LandRecord]:
    """
    Retrieves records for an exact village.
    Optional administrative filters restrict suggestions
    to the correct location.
    """

    conn = get_db_connection(db_path)

    try:
        cursor = conn.cursor()

        query = """
        SELECT *
        FROM land_records
        WHERE LOWER(TRIM(village)) = LOWER(TRIM(?))
        """

        params = [village]

        if district:
            query += """
              AND LOWER(TRIM(district)) = LOWER(TRIM(?))
            """
            params.append(district)

        if circle:
            query += """
              AND LOWER(TRIM(circle)) = LOWER(TRIM(?))
            """
            params.append(circle)

        if state:
            query += """
              AND LOWER(TRIM(state)) = LOWER(TRIM(?))
            """
            params.append(state)

        query += " ORDER BY dag_number ASC;"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [row_to_land_record(row) for row in rows]

    finally:
        conn.close()
