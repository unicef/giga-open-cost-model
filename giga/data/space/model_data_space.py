from shapely.geometry import Point
import geopandas as gpd

from giga.schemas.conf.data import DataSpaceConf


class ModelDataSpace:

    """
    Client for providing the necessary external data needed to drive the cost models
    """

    def __init__(self, config: DataSpaceConf):
        self.config = config
        self._schools = None
        self._fiber_map = None
        self._cell_tower_map = None
        self._fiber_cache = None
        self._cellular_cache = None

    @property
    def schools(self):
        if self._schools is None:
            # make schools
            self._schools = self.config.school_data_conf.load()
        return self._schools

    @property
    def school_coordinates(self):
        return self.schools.to_coordinates()

    @property
    def school_entities(self):
        return self.schools.schools

    @property
    def fiber_map(self):
        if self._fiber_map is None:
            # make map
            self._fiber_map = self.config.fiber_map_conf.load()
        return self._fiber_map

    @property
    def fiber_coordinates(self):
        return self.fiber_map.coordinates

    @property
    def cell_tower_map(self):
        if self._cell_tower_map is None:
            # make map
            self._cell_tower_map = self.config.cell_tower_map_conf.load()
        return self._cell_tower_map

    @property
    def cell_tower_coordinates(self):
        return self.cell_tower_map.to_coordinates()

    @property
    def fiber_cache(self):
        if self._fiber_cache is None:
            # make cache
            if self.config.fiber_distance_cache_conf is None:
                # skip and return None if no configuration
                return self._fiber_cache
            else:
                self._fiber_cache = self.config.fiber_distance_cache_conf.load()
        return self._fiber_cache

    @property
    def cellular_cache(self):
        if self._cellular_cache is None:
            # make cache
            if self.config.cellular_distance_cache_conf is None:
                # skip and return None if no configuration
                return self._cellular_cache
            else:
                self._cellular_cache = self.config.cellular_distance_cache_conf.load()
        return self._cellular_cache

    def filter_schools(self, school_ids):
        # load schools if not already loaded
        _ = self.schools
        self._schools = self._schools.filter_schools_by_id(school_ids)
        return self

    def school_outputs_to_frame(self, outputs):
        lookup = {
            c.coordinate_id: tuple(reversed(c.coordinate))
            for c in self.school_coordinates
        }
        geometry = [Point(lookup[sid]) for sid in outputs["school_id"]]
        return gpd.GeoDataFrame(outputs, crs="4326", geometry=geometry)
