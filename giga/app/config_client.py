import os
import fnmatch
import json
from typing import List

from giga.utils.globals import COUNTRY_DEFAULT_WORKSPACE
from giga.schemas.conf.data import DataSpaceConf
from giga.schemas.conf.country import CountryDefaults
from giga.app.config import get_registered_countries, get_country_defaults

from giga.utils.logging import LOGGER

class ConfigClient:
    """
    This class is used to access the application configuration. It is a wrapper around the

    """

    def __init__(self, defaults: CountryDefaults):
        self.defaults = defaults

    @staticmethod
    def from_registered_country(country_name: str, workspace: str):
        assert country_name in get_registered_countries(
            COUNTRY_DEFAULT_WORKSPACE
        ), f"Country {country_name} not registered"
        all_defaults = get_country_defaults(workspace=workspace)
        defaults = CountryDefaults.from_defaults(all_defaults[country_name])
        return ConfigClient(defaults)

    @property
    def school_file(self):
        return self.defaults.data.school_file

    @property
    def fiber_file(self):
        return self.defaults.data.fiber_file

    @property
    def cellular_file(self):
        return self.defaults.data.cellular_file

    @property
    def distance_cache_workspace(self):
        return os.path.join(self.defaults.data.workspace, self.defaults.data.country)

    @property
    def local_workspace_data_space_config(self):
        return DataSpaceConf(
            school_data_conf={
                "country_id": self.defaults.data.country,
                "data": {"file_path": self.school_file, "table_type": "school"},
            },
            fiber_map_conf={
                "map_type": "fiber-nodes",
                "data": {
                    "file_path": self.fiber_file,
                    "table_type": "coordinate-map",
                },
            },
            cell_tower_map_conf={
                "map_type": "cell-towers",
                "data": {
                    "file_path": self.cellular_file,
                    "table_type": "cell-towers",
                },
            },
            fiber_distance_cache_conf={
                "cache_type": "fiber-distance",
                "data": {"workspace": self.distance_cache_workspace},
            },
            cellular_distance_cache_conf={
                "cache_type": "cellular-distance",
                "cell_cache_file": self.defaults.data.cellular_distance_cache_file,
                "data": {"workspace": self.distance_cache_workspace},
            },
            p2p_distance_cache_conf={
                "cache_type": "p2p-distance",
                "p2p_cache_file": self.defaults.data.p2p_distance_cache_file,
                "data": {"workspace": self.distance_cache_workspace},
            },
        )
