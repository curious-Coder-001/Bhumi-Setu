"""
Data models for Bhumi-Setu land records.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class LandRecord:
    """Represents a cadastral land record with verification & area comparison metadata."""
    id: Optional[int]
    state: str
    district: str
    circle: str
    village: str
    vlcode: str
    dag_number: str
    patta_number: str
    patta_type: str
    recorded_area_sqm: float
    manual_measurement_sqm: Optional[float]
    land_classification: str
    source: str
    cadastral_geometry_status: str
    has_parcel_polygon: bool
    is_demo_data: bool
    verification_status: str
    notes: Optional[str] = ""

    @property
    def area_difference_sqm(self) -> Optional[float]:
        """Calculates difference: manual measurement - recorded area in sq. m."""
        if self.manual_measurement_sqm is not None:
            return round(self.manual_measurement_sqm - self.recorded_area_sqm, 2)
        return None

    @property
    def area_difference_pct(self) -> Optional[float]:
        """Calculates percentage difference relative to official recorded area."""
        if self.manual_measurement_sqm is not None and self.recorded_area_sqm > 0:
            diff = self.manual_measurement_sqm - self.recorded_area_sqm
            return round((diff / self.recorded_area_sqm) * 100, 3)
        return None

    @property
    def recorded_area_assam_units(self) -> str:
        """
        Converts sq. meters to Assam traditional land units:
        1 Bigha = 5 Katha = 100 Lecha = 1337.80 sq. m.
        1 Katha = 20 Lecha = 267.56 sq. m.
        1 Lecha = 13.378 sq. m.
        """
        sqm = self.recorded_area_sqm
        bigha = int(sqm // 1337.80)
        rem = sqm % 1337.80
        katha = int(rem // 267.56)
        rem = rem % 267.56
        lecha = round(rem / 13.378, 2)
        return f"{bigha} Bigha, {katha} Katha, {lecha} Lecha"
