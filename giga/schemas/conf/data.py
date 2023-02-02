from pydantic import BaseModel, validator
from typing import List, Literal, Union

from giga.schemas.tech import ConnectivityTechnology


from giga.data.pipes.data_tables import (
    LocalTablePipeline,
    UploadedTablePipeline,
    LocalJSONPipeline,
    LocalConnectCachePipeline,
)


class CoordinateMapConf(BaseModel):
    """Configuration for loading a local coordinate data map"""

    map_type: Literal["fiber-nodes", "cell-towers"]
    data: Union[UploadedTablePipeline, LocalTablePipeline]

    def load(self):
        return self.data.load()  # loads data from the configured pipeline


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

    country_id: Literal["brazil", "rwanda", "sample"]
    data: Union[UploadedTablePipeline, LocalTablePipeline]
    manual_entries: List[ManualSchoolDataEntry] = []

    # allow any capitalization on country IDs
    @validator("country_id", pre=True)
    def to_lowercase(cls, value):
        return value.lower()

    def load(self):
        return self.data.load()  # loads data from the configured pipeline


class FiberDistanceCacheConf(BaseModel):
    """
    Distance cache for fiber cost models
    """

    cache_type: Literal["fiber-distance"]
    data: LocalConnectCachePipeline

    def load(self):
        return self.data.load()  # loads data from the configured pipeline


class CellularDistanceCacheConf(BaseModel):
    """
    Distance cache for cellular cost models
    """

    cache_type: Literal["cellular-distance"]
    cell_cache_file: str
    data: LocalConnectCachePipeline

    def load(self):
        return self.data.load(
            connected_file=self.cell_cache_file, unconnected_file=None
        )  # loads data from the configured pipeline


class DataSpaceConf(BaseModel):

    school_data_conf: SchoolCountryConf
    fiber_map_conf: CoordinateMapConf = None
    cell_tower_map_conf: CoordinateMapConf = None
    fiber_distance_cache_conf: FiberDistanceCacheConf = None
    cellular_distance_cache_conf: CellularDistanceCacheConf = None
