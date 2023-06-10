from enum import Enum
from typing import List
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

from giga.schemas.geo import UniqueCoordinate
from giga.data.store.stores import COUNTRY_DATA_STORE

DEFAULT_POWER_REQUIRED_PER_SCHOOL = 11_000  # Watts


class SchoolZone(str, Enum):
    """Valid school zone environment"""

    rural = "rural"
    urban = "urban"
    none = ""


class GigaSchool(BaseModel):
    """Definition of a single school"""

    school_id: str
    name: str
    country: str
    country_id: int
    lat: float
    lon: float
    admin_1_name: str
    admin_2_name: str
    admin_3_name: str
    admin_4_name: str
    education_level: str
    giga_id: str = Field(..., alias="giga_id_school")
    school_zone: SchoolZone = Field(..., alias="environment")
    connected: bool = False
    connectivity_status: str = Field(
        "Unknown", alias="connectivity_speed_status"
    )  # 'Good', 'Moderate', 'No connection', 'Unknown'
    has_electricity: bool = False
    bandwidth_demand: float = 20.0  # Mbps
    has_fiber: bool = False  # True if the school is connected to a fiber network
    num_students: int = None
    cell_coverage_type: str = None
    power_required_watts: float = DEFAULT_POWER_REQUIRED_PER_SCHOOL

    class Config:
        use_enum_values = True

    def to_coordinates(self):
        """Transforms the school into a simplified coordinate"""
        return UniqueCoordinate(
            coordinate_id=self.giga_id,
            coordinate=[self.lat, self.lon],
            properties={"has_electricity": self.has_electricity},
        )


class GigaSchoolTable(BaseModel):
    """A table or collection of schools"""

    schools: List[GigaSchool] = Field(..., min_items=1)

    @staticmethod
    def from_csv(file_name: str):
        with COUNTRY_DATA_STORE.open(file_name, 'r') as file:
            frame = pd.read_csv(file, keep_default_na=False)
        return GigaSchoolTable(schools=frame.to_dict("records"))

    @property
    def school_ids(self):
        return [s.giga_id for s in self.schools]

    def to_csv(self, file_name: str):
        frame = self.to_data_frame()
        frame = frame.rename(
            columns={
                "giga_id": "giga_id_school",
                "school_zone": "environment",
                "connectivity_status": "connectivity_speed_status",
            }
        )
        with COUNTRY_DATA_STORE.open(file_name, 'r') as file:
            frame.to_csv(file)

    def filter_schools_by_id(self, school_ids):
        # Filter schools by school_id - uses giga_id as the school_id
        schools = [s for s in self.schools if s.giga_id in school_ids]
        return GigaSchoolTable(schools=schools)

    def to_coordinates(self):
        """Transforms the school table into a table of simplified coordinate"""
        return [s.to_coordinates() for s in self.schools]

    def update_bw_demand_all(self, demand):
        for s in self.schools:
            s.bandwidth_demand = demand

    def to_coordinate_vector(self):
        """Transforms the school table into a numpy vector of coordinates"""
        return np.array([[s.lat, s.lon] for s in self.schools])

    def to_data_frame(self):
        return pd.DataFrame([e.dict() for e in self.schools])
