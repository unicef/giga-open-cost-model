from typing import List, Union, Literal, Dict
from enum import Enum
from pydantic import BaseModel
import math
import numpy as np

from giga.schemas.geo import PairwiseDistance
from giga.schemas.tech import ConnectivityTechnology
from giga.viz.notebooks.helpers import output_to_table


class PowerConnectionCosts(BaseModel):

    electricity_opex: float = 0.0  # USD
    electricity_capex: float = 0.0  # USD
    cost_type: Literal["Grid", "Solar"] = "Grid"

    class Config:
        case_sensitive = False


class NonConnectionReason(str, Enum):
    """Reasons for why a connection is not feasible"""

    fiber_distance_threshold_exceeded = "FIBER_DISTANCE_THRESHOLD"
    fiber_bw_threshold_exceeded = "FIBER_BW_THRESHOLD"
    satellite_bw_threshold_exceeded = "SATELLITE_BW_THRESHOLD"
    cellular_bw_threshold_exceeded = "CELLULAR_BW_THRESHOLD"
    cellular_range_threshold_exceeded = "CELLULAR_RANGE_THRESHOLD"


class SchoolConnectionCosts(BaseModel):

    school_id: str
    capex: float  # USD
    opex: float  # Total annual USD
    opex_provider: float  # Provider operating costs
    opex_consumer: float  # Consumer operating costs
    technology: ConnectivityTechnology
    feasible: bool = True
    reason: str = "Included"
    electricity: PowerConnectionCosts = None

    class Config:
        use_enum_values = True

    @staticmethod
    def infinite_cost(school_id, tech="None"):
        return SchoolConnectionCosts(
            school_id=school_id,
            capex=math.inf,
            opex=math.inf,
            opex_provider=math.inf,
            opex_consumer=math.inf,
            technology=tech,
        )

    def technology_connectivity_cost(self, num_years: int):
        # estimate of total cost of connectivity over the length of the project
        return self.capex + self.opex * num_years


class FiberModelResults(BaseModel):

    distances: List[PairwiseDistance]
    complete_network_distances: List[PairwiseDistance] = []


class CellularModelResults(BaseModel):

    distances: List[PairwiseDistance]


class GenericModelResults(BaseModel):

    model_type: str = "Generic"


class CostResultSpace(BaseModel):

    technology_results: Union[
        FiberModelResults, CellularModelResults, GenericModelResults
    ]
    cost_results: List[SchoolConnectionCosts]


class OutputSpace(BaseModel):

    fiber_costs: CostResultSpace = None
    satellite_costs: CostResultSpace = None
    cellular_costs: CostResultSpace = None
    aggregated_costs: Dict[str, Dict[str, SchoolConnectionCosts]] = {}
    minimum_cost_result: List[SchoolConnectionCosts] = []

    @property
    def technology_outputs(self):
        techs = [self.fiber_costs, self.satellite_costs, self.cellular_costs]
        return list(filter(lambda x: x is not None, techs))

    @property
    def table(self):
        return output_to_table(self)

    def get_technology_cost_by_school(self, school_id: str, technology: str):
        assert (
            school_id in self.aggregated_costs
        ), f"{school_id} not in aggregated costs"
        assert (
            technology.lower() in self.aggregated_costs[school_id]
        ), f"{technology} not in aggregated costs for {school_id}"
        return self.aggregated_costs[school_id][technology]

    def get_technology_cost_collection(self, schools: List[str], technology: str):
        return [self.get_technology_cost_by_school(s, technology) for s in schools]

    def project_lifetime_cost(self, schools: List[str], technology: str, n_years: int):
        costs = self.get_technology_cost_collection(schools, technology)
        return sum([c.technology_connectivity_cost(n_years) for c in costs])

    def minimum_cost_lookup(self, num_years: int, ignore_tech=set()):
        """
        Returns a dictionary of school_id: minimum cost for connectivity
        for schools that have at least one feasible connection
        """
        min_costs = {}
        for school_id, costs in self.aggregated_costs.items():
            valid_costs = [
                v
                for k, v in costs.items()
                if v.technology.lower() not in ignore_tech and v.feasible
            ]
            if len(valid_costs) == 0:
                # if ignored technology is the only feasible technology, school has infinite cost
                min_costs[school_id] = SchoolConnectionCosts.infinite_cost(school_id)
            else:
                min_idx = np.argmin(
                    [c.technology_connectivity_cost(num_years) for c in valid_costs]
                )
                min_costs[school_id] = valid_costs[min_idx]
        return min_costs

    def infeasible_connections(self):
        connections = []
        for school_id, technologies in self.aggregated_costs.items():
            feasible = any(list(map(lambda x: x.feasible, technologies.values())))
            if not feasible:
                reasons = ",".join(
                    list(
                        map(
                            lambda x: "" if x.reason is None else x.reason,
                            technologies.values(),
                        )
                    )
                ).strip(",")
                connections.append(
                    SchoolConnectionCosts(
                        school_id=school_id,
                        capex=math.nan,
                        opex=math.nan,
                        opex_provider=math.nan,
                        opex_consumer=math.nan,
                        technology="None",
                        feasible=False,
                        reason=reasons,
                    )
                )
        return connections
