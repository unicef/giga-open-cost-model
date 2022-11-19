from pydantic import BaseModel
from typing import List
import math


class BandwidthCost(BaseModel):

    bandwidth_threshold: float # Mbps
    annual_cost: float # USD


class GeneralizedInternetOpex(BaseModel):

    fixed_costs: float = 0.0 # USD
    bandwidth_costs: List[BandwidthCost] = []


class FiberCapex(BaseModel):

    cost_per_km: float # USD
    fixed_costs: float = 0.0 # USD
    economies_of_scale: bool = True

class FiberCosntraints(BaseModel):

    maximum_connection_length: float = math.inf # meters


class FiberTechnologyCostConf(BaseModel):
    capex: FiberCapex
    opex: GeneralizedInternetOpex
    constraints: FiberCosntraints
