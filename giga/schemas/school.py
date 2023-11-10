from enum import Enum
from typing import List
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import math

from giga.schemas.geo import UniqueCoordinate
from giga.data.store.stores import COUNTRY_DATA_STORE

DEFAULT_POWER_REQUIRED_PER_SCHOOL = 11_000  # Watts
KM_TO_METERS = 1000

class ConnectivityType(Enum):
    Unknown = "Unknown"
    Fiber = "Fiber"
    Cellular = "Cellular"
    Satellite = "Satellite"
    P2P = "P2P"
    Other = "Other"

CONNECTIVITY_KEYWORDS = {
    ConnectivityType.Unknown: ['unknown'],
    ConnectivityType.Fiber: ['fiber', 'fibre', 'fibra', 'ftt', 'fttx'],
    ConnectivityType.Cellular: ['cell', 'cellular', 'celular', '2g', '3g', '4g', '5g', 'lte', 'gsm', 'umts', 'cdma', 'mobile', 'nr'],
    ConnectivityType.Satellite: ['satellite', 'satelite'],
    ConnectivityType.P2P: ['p2p', 'radio', 'microwave'],
}

class CoverageType(Enum):
    Unknown = "Unknown"
    _None = "None"
    _2G = "2G"
    _3G = "3G"
    _4G = "4G"
    _5G = "5G"

COVERAGE_KEYWORDS = {
    CoverageType.Unknown: ['unknown'],
    CoverageType._None: ['no coverage', 'none'],
    CoverageType._2G: ['2g', 'gsm'],
    CoverageType._3G: ['3g', 'cdma', 'umts'],
    CoverageType._4G: ['4g', 'lte'],
    CoverageType._5G: ['5g', 'nr']
}

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
    connectivity_status: str = Field( "Unknown")  # 'Good', 'Moderate', 'No connection', 'Unknown'
    has_electricity: bool = False
    bandwidth_demand: float = 20.0  # Mbps
    has_fiber: bool = False  # True if the school is connected to a fiber network
    num_students: int = None
    cell_coverage_type: str = Field(..., alias="coverage_type")
    fiber_node_distance: float = math.inf
    power_required_watts: float = DEFAULT_POWER_REQUIRED_PER_SCHOOL
    nearest_LTE_distance: float = math.inf

    class Config:
        use_enum_values = True

    def to_coordinates(self):
        """Transforms the school into a simplified coordinate"""
        return UniqueCoordinate(
            coordinate_id=self.giga_id,
            coordinate=[self.lat, self.lon],
            properties={"has_electricity": self.has_electricity},
        )

# New Class for School Connectivity
class SchoolConnectivity:
    @staticmethod
    def parse(s: str) -> str:
        if pd.isnull(s) or s=='':
            return ConnectivityType.Unknown.value

        s_lower = s.lower()

        for conn_type, keywords in CONNECTIVITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in s_lower:
                    return conn_type.value

        return ConnectivityType.Other.value

class SchoolCoverage:
    @staticmethod
    def parse(s: str) -> str:
        if pd.isnull(s) or s=='':
            return CoverageType.Unknown.value
        
        s_lower = s.lower()

        for cov_type, keywords in COVERAGE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in s_lower:
                    return cov_type.value
        
        return CoverageType.Unknown.value


# New Class for Data Processing
class SchoolDataProcessor:
    @staticmethod
    def process_fields(school_info: GigaSchool):
        # Process 'connected' and 'connectivity_status'
        if school_info.connectivity.lower() == 'yes':
            school_info.connected = True
            school_info.connectivity_status = "Good"
        else:
            school_info.connected = False
            if school_info.connectivity.lower() == "no":
                school_info.connectivity_status = "No connection"
            else:
                school_info.connectivity_status = "Unknown"

        # Process 'electricity'
        if school_info.electricity.lower() == "yes":
            school_info.has_electricity = True
        else:
            school_info.has_electricity = False
            if school_info.electricity.lower() != "no":
                school_info.electricity = "Unknown"

        # Process 'type_connectivity' for 'has_fiber'
        school_info.type_connectivity = SchoolConnectivity.parse(school_info.type_connectivity)
        if school_info.type_connectivity == ConnectivityType.Fiber.value:
            school_info.has_fiber = True
        else:
            school_info.has_fiber = False
        
        # Process distance fields
        for dist_field in ['fiber_node_distance', 'nearest_LTE_distance']:
            school_info = SchoolDataProcessor.process_distance_field(school_info, dist_field)
        
        # Process coverage type field
        school_info = SchoolDataProcessor.process_coverage_type(school_info)
        
        # Process 'admins'
        for admin in ['admin1', 'admin2', 'admin3', 'admin4']:
            if pd.isnull(getattr(school_info, admin)):
                setattr(school_info, admin, '') 

        # Return the updated GigaSchool
        return school_info

    @staticmethod
    def process_distance_field(school_info, field_name):
        dist_value = getattr(school_info, field_name)
        if pd.isnull(dist_value) or dist_value == '':
            setattr(school_info, field_name, math.inf)
        else:
            setattr(school_info, field_name, float(dist_value) * KM_TO_METERS)
        return school_info
    
    @staticmethod
    def process_coverage_type(school_info: GigaSchool):
        # Process 'cell_coverage_type'
        school_info.cell_coverage_type = SchoolCoverage.parse(school_info.cell_coverage_type)
        return school_info
        
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
        for school in self.schools:
            SchoolDataProcessor.process_fields(school)

    def to_coordinate_vector(self):
        """Transforms the school table into a numpy vector of coordinates"""
        return np.array([[s.lat, s.lon] for s in self.schools])

    def to_data_frame(self):
        return pd.DataFrame([e.dict() for e in self.schools])
