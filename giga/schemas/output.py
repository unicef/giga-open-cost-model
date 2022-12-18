from typing import List, Union
from enum import Enum
from pydantic import BaseModel

from giga.schemas.geo import PairwiseDistance
from giga.schemas.tech import ConnectivityTechnology


class NonConnectionReason(str, Enum):
    """Reasons for why a connection is not feasible"""

    fiber_distance_threshold_exceeded = "FIBER_DISTANCE_THRESHOLD"
    fiber_bw_threshold_exceeded = "FIBER_BW_THRESHOLD"
    satellite_bw_threshold_exceeded = "SATELLITE_BW_THRESHOLD"


class SchoolConnectionCosts(BaseModel):

    school_id: str
    capex: float  # USD
    opex: float  # Total annual USD
    opex_provider: float  # Provider operating costs
    opex_consumer: float  # Consumer operating costs
    technology: ConnectivityTechnology
    feasible: bool = True
    reason: str = None

    class Config:
        use_enum_values = True


class FiberModelResults(BaseModel):

    distances: List[PairwiseDistance]


class GenericModelResults(BaseModel):

    model_type: str = "Generic"


class CostResultSpace(BaseModel):

    technology_results: Union[FiberModelResults, GenericModelResults]
    cost_results: List[SchoolConnectionCosts]


class OutputSpace(BaseModel):

    fiber_costs: CostResultSpace = None
    satellite_costs: CostResultSpace = None
    minimum_cost_result: List[SchoolConnectionCosts] = []

    @property
    def technology_outputs(self):
        techs = [self.fiber_costs, self.satellite_costs]
        return list(filter(lambda x: x is not None, techs))
