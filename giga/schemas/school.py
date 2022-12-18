from enum import Enum
from typing import List
from pydantic import BaseModel, Field
import pandas as pd

from giga.schemas.geo import UniqueCoordinate


class EducationLevel(str, Enum):
    """Valid level of education"""

    primary = "Primary"
    secondary = "Secondary"
    other = "Other"
    none = ""


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
    education_level: EducationLevel
    giga_id: str = Field(..., alias="giga_id_school")
    school_zone: SchoolZone = Field(..., alias="environment")
    connected: bool = False
    bandwidth_demand = 20.0  # Mbps

    class Config:
        use_enum_values = True

    def to_coordinates(self):
        """Transforms the school into a simplified coordinate"""
        return UniqueCoordinate(
            coordinate_id=self.giga_id, coordinate=[self.lat, self.lon]
        )


class GigaSchoolTable(BaseModel):
    """A table or collection of schools"""

    schools: List[GigaSchool] = Field(..., min_items=1)

    @staticmethod
    def from_csv(file_name: str):
        frame = pd.read_csv(file_name, keep_default_na=False)
        return GigaSchoolTable(schools=frame.to_dict("records"))

    def to_coordinates(self):
        """Transforms the school table into a table of simplified coordinate"""
        return [s.to_coordinates() for s in self.schools]

    def update_bw_demand_all(self, demand):
        for s in self.schools:
            s.bandwidth_demand = demand
