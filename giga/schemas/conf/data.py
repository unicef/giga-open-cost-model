from pydantic import BaseModel
from typing import List, Literal, TypeVar
from typing import TypeVar

from giga.schemas.tech import ConnectivityTechnology
from giga.schemas.geo import UniqueCoordinateTable


class UploadedCoordinateMapConf(BaseModel):
    """Configuration for loading a local coordinate data map"""
    map_type: Literal['fiber-nodes', 'cell-towers']
    coordinate_map: UniqueCoordinateTable # uploaded coordinate table


class LocalWorkspaceTransportConf(BaseModel):

    workspace: str = '.'
    file_name: str = 'schools.csv'


class ManualSchoolDataEntry(BaseModel):

    school_id: str
    capex_cost: float
    opex_cost: float
    technology: ConnectivityTechnology


class SchoolCountryConf(BaseModel):
    """
        School data configuration when
        cost estimates need to be performed for a country
    """

    country_id: Literal['Brazil', 'Rwanda', 'Sample']
    transport: LocalWorkspaceTransportConf
    manual_entries: List[ManualSchoolDataEntry] = []


class DataSpaceConf(BaseModel):

    school_data_conf: SchoolCountryConf
    fiber_map_conf: UploadedCoordinateMapConf = None
    celltower_map_conf: UploadedCoordinateMapConf = None
