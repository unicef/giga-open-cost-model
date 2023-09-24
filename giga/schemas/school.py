from enum import Enum
from typing import List
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

from giga.schemas.geo import UniqueCoordinate
from giga.data.store.stores import COUNTRY_DATA_STORE

DEFAULT_POWER_REQUIRED_PER_SCHOOL = 11_000  # Watts

def parse_connectivity(s):
    if pd.isnull(s) or s=='':
        return "Unknown"
    if "fiber" in s or "Fiber" in s or "FIBER" in s or "Fibre" in s or "fibre" in s or "FIBRE" in s or "Fibra" in s:
        return "Fiber"
    if "cell" in s or "Cell" in s or "Cellular" in s or "cellular" in s or "Celular" in s or "G" in s:
        return "Cellular"
    if "Satellite" in s or "satellite" in s or "SATELLITE" in s or "SATELITE" in s:
        return "Satellite"
    if "unknow" in s or "Unknown" in s:
        return "Unknown"
    if "P2P" in s or "radio" in s or "Radio" in s or "Microwave" in s or "microwave" in s:
        return "Microwave"
    
    return "Other"

class SchoolZone(str, Enum):
    """Valid school zone environment"""

    rural = "rural"
    urban = "urban"
    none = ""


class GigaSchool(BaseModel):
    """Definition of a single school"""

    school_id: str
    name: str
    #country: str
    #country_id: int
    lat: float
    lon: float
    admin1: str
    admin2: str
    admin3: str
    admin4: str
    education_level: str
    giga_id: str = Field(..., alias="giga_id_school")
    school_zone: str =  Field(..., alias="school_region") #SchoolZone = Field(..., alias="school_region")
    connected: bool = False
    connectivity: str
    type_connectivity: str
    electricity: str
    connectivity_status: str = Field(
        "Unknown"
    )  # 'Good', 'Moderate', 'No connection', 'Unknown'
    has_electricity: bool = False
    bandwidth_demand: float = 20.0  # Mbps
    has_fiber: bool = False  # True if the school is connected to a fiber network
    num_students: int = None
    cell_coverage_type: str = Field(..., alias="coverage_type")
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
    
    def process_fields(self):
        # connected and connectivity_status
        if self.connectivity=="Yes" or self.connectivity=="yes" or self.connectivity=="YES":
            self.connected = True
            self.connectivity_status = "Good" #we do not care about good or moderate for now - would need sql query for that
        else:
            self.connected = False
            if self.connectivity=="No" or self.connectivity=="no" or self.connectivity=="NO":
                self.connectivity_status = "No connection"
            else:
                self.connectivity_status = "Unknown"

        #electricity
        if self.electricity=="Yes" or self.electricity=="yes" or self.electricity=="YES":
            self.has_electricity = True
        else:
            self.has_electricity = False
            if self.electricity!="No" and self.electricity!="no" and self.electricity!="NO":
                self.electricity = "Unknown"

        #fiber
        self.type_connectivity = parse_connectivity(self.type_connectivity)
        if self.type_connectivity=="Fiber":
            self.has_fiber = True
        else:
            self.has_fiber = False

        #admins
        if pd.isnull(self.admin1):
            self.admin1 = ''
        if pd.isnull(self.admin2):
            self.admin2 = ''
        if pd.isnull(self.admin3):
            self.admin3 = ''
        if pd.isnull(self.admin4):
            self.admin4 = ''
        


class GigaSchoolTable(BaseModel):
    """A table or collection of schools"""

    schools: List[GigaSchool] = Field(..., min_items=1)

    @staticmethod
    def from_csv_old(file_name: str):
        with COUNTRY_DATA_STORE.open(file_name, 'r') as file:
            frame = pd.read_csv(file, keep_default_na=False)
        return GigaSchoolTable(schools=frame.to_dict("records"))
    
    @staticmethod
    def from_csv(file_name: str):
        with COUNTRY_DATA_STORE.open(file_name, 'r') as file:
            frame = pd.read_csv(file, keep_default_na=False)
        gst = GigaSchoolTable(schools=frame.to_dict("records"))
        gst.process_fields_all()
        return gst

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

    def update_required_power_all(self, power):
        for s in self.schools:
            s.power_required_watts = power

    def process_fields_all(self):
        for s in self.schools:
            s.process_fields()

    def to_coordinate_vector(self):
        """Transforms the school table into a numpy vector of coordinates"""
        return np.array([[s.lat, s.lon] for s in self.schools])

    def to_data_frame(self):
        return pd.DataFrame([e.dict() for e in self.schools])
