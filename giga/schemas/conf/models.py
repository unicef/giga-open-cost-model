from pydantic import BaseModel
from typing import List
import math

from giga.schemas.tech import ConnectivityTechnology


class BandwidthCost(BaseModel):

    bandwidth_threshold: float  # Mbps
    annual_cost: float  # USD


class GeneralizedInternetOpex(BaseModel):

    fixed_costs: float = 0.0  # USD
    bandwidth_costs: List[BandwidthCost] = []


class FiberCapex(BaseModel):

    cost_per_km: float  # USD
    fixed_costs: float = 0.0  # USD
    economies_of_scale: bool = True


class FiberCosntraints(BaseModel):

    maximum_connection_length: float = math.inf  # meters


class FiberTechnologyCostConf(BaseModel):
    capex: FiberCapex
    opex: GeneralizedInternetOpex
    constraints: FiberCosntraints


class TotalCostScenarioConf(BaseModel):

    scenario_id: str
    technologies: List[ConnectivityTechnology]
    years_opex: int = 5  # the number of opex years to consider in the estimate
