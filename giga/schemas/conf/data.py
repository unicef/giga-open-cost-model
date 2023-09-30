from pydantic import BaseModel, validator
from typing import List, Literal, Union

from giga.schemas.tech import ConnectivityTechnology
from giga.app.config import get_registered_countries
from giga.app.create_p2p_distance_cache import P2PCacheCreator, P2PCacheCreatorArgs
from giga.utils.globals import COUNTRY_DEFAULT_WORKSPACE
from giga.data.pipes.data_tables import (
    LocalTablePipeline,
    UploadedTablePipeline,
    LocalJSONPipeline,
    LocalConnectCachePipeline,
)
from giga.schemas.distance_cache import (
    GreedyConnectCache,
)
from giga.utils.logging import LOGGER

#REGISTERED_COUNTRIES = tuple(get_registered_countries(COUNTRY_DEFAULT_WORKSPACE))
REGISTERED_COUNTRIES = tuple(get_registered_countries())

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

    country_id: Literal[REGISTERED_COUNTRIES]
    data: Union[UploadedTablePipeline, LocalTablePipeline]
    manual_entries: List[ManualSchoolDataEntry] = []

    # allow any capitalization on country IDs
    #@validator("country_id", pre=True)
    #def to_lowercase(cls, value):
    #    return value.lower()

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
    
    def redo_meta(connected,schools):
        return None
    
    def redo_schools(connected,k):
        return None


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


class P2PDistanceCacheConf(BaseModel):
    """
    Distance cache for p2p cost models
    """

    cache_type: Literal["p2p-distance"]
    p2p_cache_file: str
    data: LocalConnectCachePipeline

    def load(self, hot_load: bool = False):
        cache: GreedyConnectCache = self.data.load(
            connected_file=self.p2p_cache_file, unconnected_file=None
        )  # loads data from the configured pipeline
        if len(cache) != 0 or not hot_load:
            return cache
        self.hot_load()
        return self.load(False)

    def hot_load(self):
        """
        Fully recompute the P2P cache and replace the existing
        JSON output file.
        """
        LOGGER.info("> Computing initial P2P cache, as it does not exist locally.")
        LOGGER.info(
            "> This may take a while depending on the number of schools included."
        )
        LOGGER.info("> Future runs will be faster once this has completed.")
        args = P2PCacheCreatorArgs()
        args.workspace_directory = self.data.workspace
        P2PCacheCreator(args).run()
        LOGGER.info(f"> P2P cache saved locally. Future runs will now be faster.")




class DataSpaceConf(BaseModel):

    school_data_conf: SchoolCountryConf
    fiber_map_conf: CoordinateMapConf = None
    cell_tower_map_conf: CoordinateMapConf = None
    fiber_distance_cache_conf: FiberDistanceCacheConf = None
    cellular_distance_cache_conf: CellularDistanceCacheConf = None
    p2p_distance_cache_conf: P2PDistanceCacheConf = None
