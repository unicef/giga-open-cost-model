import os
import json
from pydantic import BaseModel, FilePath, DirectoryPath, validator
from typing import List, Dict, Union
from giga.schemas.conf.models import (
    ElectricityCostConf,
    FiberTechnologyCostConf,
    SatelliteTechnologyCostConf,
    CellularTechnologyCostConf,
    P2PTechnologyCostConf,
    SingleTechnologyScenarioConf,
    MinimumCostScenarioConf,
)


class ScenarioDefaults(BaseModel):
    years_opex: int
    bandwidth_demand: float


class GigaDefaults(BaseModel):
    scenario: ScenarioDefaults
    fiber: FiberTechnologyCostConf
    satellite: SatelliteTechnologyCostConf
    cellular: CellularTechnologyCostConf
    electricity: ElectricityCostConf
    p2p: P2PTechnologyCostConf


class DataDefaults(BaseModel):
    country: str
    country_code: int = None
    workspace: str
    school_file: str
    fiber_file: str
    cellular_file: str
    cellular_distance_cache_file: str  # name of file for the cache, not direct path
    p2p_distance_cache_file: str
    country_center: Dict[str, float] = {"lat": 0.0, "lon": 0.0}

    @property
    def country_center_tuple(self):
        # return a lat, lon tuple of the center
        return (self.country_center["lat"], self.country_center["lon"])


class DataDefaultsRegistration(BaseModel):
    country: str
    country_code: int = None
    workspace: str
    school_file: str
    fiber_file: str
    cellular_file: str
    cellular_distance_cache_file: str


class CountryDefaultsRegistration(BaseModel):
    """
    Used to register a new country with the system
    """

    data: DataDefaultsRegistration
    model_defaults: GigaDefaults

    @staticmethod
    def as_validator(defaults: Dict):
        defaults = defaults.copy()
        assert (
            "data" in defaults
        ), "Default configuration must have a top level 'data' section"
        data_lookup_required = set(
            [
                "country",
                "country_code",
                "workspace",
                "school_file",
                "fiber_file",
                "cellular_file",
            ]
        )
        for key in data_lookup_required:
            assert (
                key in defaults["data"]
            ), f"Default configuration must have a 'data.{key}' section"
        defaults["data"]["skip_validation"] = True
        return CountryDefaultsRegistration(**defaults)


class CountryDefaults(BaseModel):
    data: DataDefaults
    model_defaults: GigaDefaults

    def to_json(self) -> str:
        return json.dumps({
            "data": self.data.dict(),
            "model_defaults": self.model_defaults.dict()
        })

    @staticmethod
    def from_defaults(defaults: Dict, **kwargs):
        data_defaults = defaults["data"]
        data = DataDefaults(
            country=data_defaults["country"],
            country_code=data_defaults["country_code"],
            workspace=data_defaults["workspace"],
            school_file=os.path.join(
                data_defaults["workspace"],
                data_defaults["country"],
                data_defaults["school_file"],
            ),
            fiber_file=os.path.join(
                data_defaults["workspace"],
                data_defaults["country"],
                data_defaults["fiber_file"],
            ),
            cellular_file=os.path.join(
                data_defaults["workspace"],
                data_defaults["country"],
                data_defaults["cellular_file"],
            ),
            cellular_distance_cache_file=data_defaults["cellular_distance_cache_file"],
            p2p_distance_cache_file=data_defaults["p2p_distance_cache_file"],
            country_center=data_defaults["country_center"],
        )
        return CountryDefaults(
            data=data, model_defaults=defaults["model_defaults"], **kwargs
        )
