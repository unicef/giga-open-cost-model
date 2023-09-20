import math
from shapely.geometry import Point
import pandas as pd
from typing import List

from giga.schemas.conf.data import DataSpaceConf
from giga.schemas.school import GigaSchoolTable


class ModelDataSpace:

    """
    Client for providing the necessary external data needed to drive the cost models
    Includes:
        - Schools
        - Fiber Nodes
        - Cell Towers
    """

    def __init__(self, config: DataSpaceConf):
        self.config = config
        self._schools = None
        self._all_schools = None
        self._fiber_map = None
        self._cell_tower_map = None
        self._cell_tower_coordinates = None
        self._fiber_cache = None
        self._cellular_cache = None
        self._p2p_cache = None
        self._for_infra_fiber_cache = None
        self._for_infra_unconnected_schools = None
        self._for_infra_connected_schools = None

    @property
    def schools(self):
        """
        Accessor for school entities - includes coordinates, school ids, and other metadata such as
        electricity availability, connectivity quality, etc.
        """
        if self._schools is None:
            # make schools
            self._all_schools = self.config.school_data_conf.load()
            unconnected = [s for s in self._all_schools.schools if not s.connected]
            if len(unconnected)==0:
                self._schools = self._all_schools
            else:
                self._schools = GigaSchoolTable(schools=unconnected)
        return self._schools

    @property
    def all_schools(self):
        """
        Accessor for unconnected schools - a subset of the schools that are not connected to
        any internet infrastructure
        """
        if self._all_schools is None:
            _ = self.schools
        return self._all_schools

    @property
    def schools_with_fiber_coordinates(self):
        """
        Accessor to fiber school coordinates - a subset of the schools that are connected to fiber infrastrucutre
        """
        fiber_schools = [s for s in self.all_schools.schools if s.has_fiber]
        if len(fiber_schools) > 0:
            return GigaSchoolTable(schools=fiber_schools).to_coordinates()
        else:
            return []

    @property
    def school_coordinates(self):
        """
        Accessor for school coordinates - id, lat, lot information
        """
        return self.schools.to_coordinates()

    @property
    def school_entities(self):
        """
        Accessor for school entities - includes coordinates, school ids, and other metadata such as
        electricity availability, connectivity quality, etc.
        """
        return self.schools.schools
    
    @property
    def all_school_entities(self):
        """
        Accessor for school entities - includes coordinates, school ids, and other metadata such as
        electricity availability, connectivity quality, etc.
        """
        if self._all_schools is None:
            self._all_schools = self.config.school_data_conf.load()
        return self.all_schools.schools

    @property
    def fiber_map(self):
        """
        Accessor for the fiber map, which is a coordinate table containing the coordinates of all
        fiber nodes in the region of interest
        """
        if self._fiber_map is None:
            # make map
            self._fiber_map = self.config.fiber_map_conf.load()
        return self._fiber_map

    @property
    def fiber_coordinates(self):
        """
        Accessor to fiber coordinates - a list of id, lat, lon
        """
        return self.fiber_map.coordinates

    @property
    def cell_tower_map(self):
        """
        Accessor for the cell tower map - a coordinate table containing the coordinates and
        metadata of all cell towers in the region of interest
        """
        if self._cell_tower_map is None:
            # make map
            self._cell_tower_map = self.config.cell_tower_map_conf.load()
        return self._cell_tower_map

    @property
    def cell_tower_coordinates(self):
        """
        Accessor to cell tower coordinates - a list of id, lat, lon
        """
        if self._cell_tower_coordinates is None:
            # make coordinates
            self._cell_tower_coordinates = self.cell_tower_map.to_coordinates()
        return self._cell_tower_coordinates

    @property
    def fiber_cache(self):
        """
        Accessor for the fiber distance cache - a table of distances between all schools and fiber nodes
        This includes pairwise nearest distances between school/shool pairs as well
        """
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
        """
        Accessor for the cellular distance cache - a table of distances between all schools and cell towers
        """
        if self._cellular_cache is None:
            # make cache
            if self.config.cellular_distance_cache_conf is None:
                # skip and return None if no configuration
                return self._cellular_cache
            else:
                self._cellular_cache = self.config.cellular_distance_cache_conf.load()
        return self._cellular_cache

    @property
    def p2p_cache(self):
        """
        Accessor for the p2p distance cache - a table of distances between all schools and cell towers
        Includes line of sight information
        """
        if self._p2p_cache is None:
            # make cache
            if self.config.p2p_distance_cache_conf is None:
                # skip and return None if no configuration
                return self._p2p_cache
            else:
                self._p2p_cache = self.config.p2p_distance_cache_conf.load()
        return self._p2p_cache

    def filter_schools(self, school_ids: List[str]):
        """
        Filters and returns the school entities with the specified ids
        This will return a new data space that includes any downstream dependencies on school entities
        Such as caches and coordinates

        :param school_ids: The school ids to keep in the data space, all others will be removed
        :return: The updated ModelDataSpace with the filtered schools
        """
        _ = self.schools
        new_space = ModelDataSpace(self.config)
        ####
        if len(school_ids)==len(self._all_schools.school_ids):
            new_space._schools = self._schools
            filtered_schools = self.all_schools
        else:
            new_space._schools = self._schools.filter_schools_by_id(school_ids)
            filtered_schools = self._all_schools.filter_schools_by_id(school_ids)
            
        fiber_schools = [s for s in filtered_schools.schools if s.has_fiber]
        if len(fiber_schools) > 0:
            new_space._fiber_schools = GigaSchoolTable(schools=fiber_schools).to_coordinates()
        else:
             new_space._fiber_schools = []
        ####
        new_space._all_schools = self._schools
        new_space._fiber_map = self._fiber_map
        new_space._cell_tower_map = self._cell_tower_map
        new_space._cell_tower_coordinates = self._cell_tower_coordinates
        new_space._fiber_cache = self._fiber_cache
        new_space._cellular_cache = self._cellular_cache
        new_space._p2p_cache = self._p2p_cache
        return new_space

    def get_cell_tower_coordinates_with_technologies(self, technologies: List[str]):
        """
        Filter and return cell tower coordinates with the specified technologies.

        :param technologies: The technology types to filter cell towers by (e.g., '4G', 'LTE').
        :return a list of cell tower coordinates with the specified technology.
        """
        techs = set(technologies)
        filtered = [
            t.to_coordinates()
            for t in self.cell_tower_map.towers
            if t.technologies.intersection(techs)
        ]
        return filtered

    def school_outputs_to_frame(self, outputs):
        lookup = {
            c.giga_id: {
                "lat": c.lat,
                "lon": c.lon,
                "num_students": c.num_students,
                "has_electricity": c.has_electricity,
                "has_fiber": c.has_fiber,
                "cell_coverage_type": c.cell_coverage_type,
                "bandwidth_demand": c.bandwidth_demand,
                "nearest_fiber": self.fiber_cache.connected_cache.get_distance(
                    c.giga_id
                )
                if self.fiber_cache.connected_cache is not None
                else math.inf,
                "nearest_cell_tower": self.cellular_cache.connected_cache.get_distance(
                    c.giga_id
                )
                if self.cellular_cache.connected_cache is not None
                else math.inf,
                "nearest_visible_cell_tower": self.p2p_cache.connected_cache.get_distance(
                    c.giga_id
                )
                if self.p2p_cache.connected_cache is not None
                else math.inf,
            }
            for c in self.school_entities
        }
        df = pd.DataFrame(outputs)
        schools_ids = list(df["school_id"])
        for k in [
            "lat",
            "lon",
            "num_students",
            "has_electricity",
            "has_fiber",
            "cell_coverage_type",
            "bandwidth_demand",
            "nearest_fiber",
            "nearest_cell_tower",
            "nearest_visible_cell_tower",
        ]:
            sids = filter(lambda sid: sid in lookup, schools_ids)
            df[k] = [lookup[sid][k] for sid in sids]
        return df

    def schools_to_frame(self):
        lookup = [
                {"school_id" : c.giga_id,
                "lat": c.lat,
                "lon": c.lon,
                "num_students": c.num_students,
                "has_electricity": c.has_electricity,
                "has_fiber": c.has_fiber,
                "connected": c.connected,
                "type_connectivity": c.type_connectivity,
                "cell_coverage_type": c.cell_coverage_type,
                "electricity": c.electricity,
                "connectivity_status": c.connectivity_status,
                "bandwidth_demand": c.bandwidth_demand,
                "nearest_fiber": self.fiber_cache.connected_cache.get_distance(
                    c.giga_id
                )
                if self.fiber_cache.connected_cache is not None
                else math.inf,
                "nearest_cell_tower": self.cellular_cache.connected_cache.get_distance(
                    c.giga_id
                )
                if self.cellular_cache.connected_cache is not None
                else math.inf,
                "nearest_visible_cell_tower": self.p2p_cache.connected_cache.get_distance(
                    c.giga_id
                )
                if self.p2p_cache.connected_cache is not None
                else math.inf,
            }
            for c in self.all_school_entities
        ]
        df = pd.DataFrame(lookup)
        return df