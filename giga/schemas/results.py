from typing import List, Union
from enum import Enum
from pydantic import BaseModel

from giga.schemas.geo import PairwiseDistance
from giga.schemas.tech import ConnectivityTechnology


class NonConnectionReason(str, Enum):
    """Reasons for why a connection is not feasible"""
    fiber_distance_threshold_exceeded = 'FIBER_DISTANCE_THRESHOLD'


class SchoolConnectionCosts(BaseModel):

    school_id: str
    capex: float # USD
    opex: float # Annual USD
    technology: ConnectivityTechnology
    feasible: bool = True
    reason: NonConnectionReason = None

    class Config:  
        use_enum_values = True


class FiberModelResults(BaseModel):

    distances: List[PairwiseDistance]


class CostResultSpace(BaseModel):
    technology_results: Union[FiberModelResults]
    cost_results: List[SchoolConnectionCosts]