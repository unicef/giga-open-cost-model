from typing import List, Union, Literal, Dict
from enum import Enum
from pydantic import BaseModel
import math
import numpy as np
import pandas as pd

from giga.schemas.geo import PairwiseDistance
from giga.schemas.tech import ConnectivityTechnology
from giga.viz.notebooks.helpers import output_to_table


def results_to_complete_table(results: List, n_years: int, attribution, school_ids):
    if school_ids==None:
        df = pd.DataFrame([dict(x) for x in results])
    
        electricity_capex = list(
            map(
            lambda x: x.electricity.electricity_capex if x.feasible else math.nan,
            results,
            )
        )
        electricity_opex = list(
            map(
            lambda x: x.electricity.electricity_opex if x.feasible else math.nan,
            results,
            )
        )
        electricity_type = list(
            map(lambda x: x.electricity.cost_type if x.feasible else math.nan, results)
        )
        total_cost = [
            r.technology_connectivity_cost(n_years, attribution=attribution)
            for r in results
        ]
    else:
        df = pd.DataFrame([dict(x) for x in results if x.school_id in school_ids])
        electricity_capex = []
        for r in results:
            if r.school_id in school_ids:
                if r.feasible:
                    electricity_capex.append(r.electricity.electricity_capex)
                else:
                    electricity_capex.append(math.nan)
        
        electricity_opex = []
        for r in results:
            if r.school_id in school_ids:
                if r.feasible:
                    electricity_opex.append(r.electricity.electricity_opex)
                else:
                    electricity_opex.append(math.nan)

        electricity_type = []
        for r in results:
            if r.school_id in school_ids:
                if r.feasible:
                    electricity_type.append(r.electricity.cost_type)
                else:
                    electricity_type.append(math.nan)

        total_cost = [
            r.technology_connectivity_cost(n_years, attribution=attribution)
            for r in results if r.school_id in school_ids
        ]

    df["electricity_capex"] = electricity_capex
    df["electricity_opex"] = electricity_opex
    df["electricity_type"] = electricity_type
    df["recurring_costs"] = df["opex_consumer"] + df["electricity_opex"]
    df["total_cost"] = total_cost
    df = df.drop(columns=["electricity"])
    return df


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
    p2p_bw_threshold_exceeded = "P2P_BW_THRESHOLD"
    p2p_range_threshold_exceeded = "P2P_RANGE_THRESHOLD"
    budget_exceeded = "BUDGET_EXCEEDED"
    no_electricity = "NO_ELECTRICITY"


class SchoolConnectionCosts(BaseModel):

    school_id: str
    capex: float  # USD
    capex_provider: float  # Provider capital costs
    capex_consumer: float  # Consumer capital costs
    opex: float  # Total annual USD
    opex_provider: float  # Provider operating costs
    opex_consumer: float  # Consumer operating costs
    technology: ConnectivityTechnology
    feasible: bool = True
    reason: str = "Included"
    electricity: PowerConnectionCosts = PowerConnectionCosts()

    class Config:
        use_enum_values = True

    @staticmethod
    def infinite_cost(school_id, tech="None"):
        return SchoolConnectionCosts(
            school_id=school_id,
            capex=math.inf,
            capex_provider=math.inf,
            capex_consumer=math.inf,
            opex=math.inf,
            opex_provider=math.inf,
            opex_consumer=math.inf,
            technology=tech,
        )

    @staticmethod
    def infeasible_cost(school_id: str, tech: str, reason: NonConnectionReason):
        return SchoolConnectionCosts(
            school_id=school_id,
            capex=math.nan,
            capex_provider=math.nan,
            capex_consumer=math.nan,
            opex=math.nan,
            opex_provider=math.nan,
            opex_consumer=math.nan,
            technology=tech,
            feasible=False,
            reason=reason,
            electricity=PowerConnectionCosts(
                electricity_opex=math.nan, electricity_capex=math.nan
            ),
        )

    @staticmethod
    def budget_exceeded_cost(school_id, tech):
        return SchoolConnectionCosts(
            school_id=school_id,
            capex=math.inf,
            capex_provider=math.inf,
            capex_consumer=math.inf,
            opex=math.inf,
            opex_provider=math.inf,
            opex_consumer=math.inf,
            technology=tech,
            feasible=False,
            reason=NonConnectionReason.budget_exceeded,
        )

    def technology_connectivity_cost(self, num_years: int, attribution="both"):
        # estimate of total cost of connectivity over the length of the project
        if attribution == "provider":
            total_capex = self.capex_provider
            total_opex = self.opex_provider
        elif attribution == "consumer":
            total_capex = self.capex_consumer + self.electricity.electricity_capex
            total_opex = self.opex_consumer + self.electricity.electricity_opex
        else:
            total_capex = self.capex + self.electricity.electricity_capex
            total_opex = self.opex + self.electricity.electricity_opex
        return total_capex + total_opex * num_years


class FiberModelResults(BaseModel):

    distances: List[PairwiseDistance]
    complete_network_distances: List[PairwiseDistance] = []


class CellularModelResults(BaseModel):

    distances: List[PairwiseDistance]


class P2PModelResults(BaseModel):

    distances: List[PairwiseDistance]


class GenericModelResults(BaseModel):

    model_type: str = "Generic"


class CostResultSpace(BaseModel):

    technology_results: Union[
        FiberModelResults, CellularModelResults, P2PModelResults, GenericModelResults
    ]
    cost_results: List[SchoolConnectionCosts]


class OutputSpace(BaseModel):

    fiber_costs: CostResultSpace = None
    satellite_costs: CostResultSpace = None
    cellular_costs: CostResultSpace = None
    p2p_costs: CostResultSpace = None
    aggregated_costs: Dict[str, Dict[str, SchoolConnectionCosts]] = {}
    minimum_cost_result: List[SchoolConnectionCosts] = []
    years_opex: int = 5

    @property
    def technology_outputs(self):
        techs = [
            self.fiber_costs,
            self.satellite_costs,
            self.cellular_costs,
            self.p2p_costs,
        ]
        return list(filter(lambda x: x is not None, techs))

    @property
    def table(self):
        return output_to_table(self)

    @property
    def fiber_distances(self):
        if self.fiber_costs is not None:
            return self.fiber_costs.technology_results.distances
        else:
            return []

    def filter_schools(self, school_ids: List[str]):
        """
        Filters and returns the school entities with the specified ids
        This will return a new data space that includes any downstream dependencies on school entities
        Such as caches and coordinates

        :param school_ids: The school ids to keep in the data space, all others will be removed
        :return: The updated OutputSpace with the filtered schools
        """
        if self.fiber_costs != None:
            fiber_costs = CostResultSpace(technology_results=self.fiber_costs.technology_results,cost_results=[])
        
            for sc in self.fiber_costs.cost_results:
                if sc.school_id in school_ids:
                    fiber_costs.cost_results.append(sc)
        else:
            fiber_costs = None

        if self.satellite_costs != None:
            satellite_costs = CostResultSpace(technology_results=self.satellite_costs.technology_results,cost_results=[])
        
            for sc in self.satellite_costs.cost_results:
                if sc.school_id in school_ids:
                    satellite_costs.cost_results.append(sc)
        else:
            satellite_costs = None

        if self.cellular_costs != None:
            cellular_costs = CostResultSpace(technology_results=self.cellular_costs.technology_results,cost_results=[])
        
            for sc in self.cellular_costs.cost_results:
                if sc.school_id in school_ids:
                    cellular_costs.cost_results.append(sc)
        else:
            cellular_costs = None

        if self.p2p_costs != None:
            p2p_costs = CostResultSpace(technology_results=self.p2p_costs.technology_results,cost_results=[])
        
            for sc in self.p2p_costs.cost_results:
                if sc.school_id in school_ids:
                    p2p_costs.cost_results.append(sc)
        else:
            p2p_costs = None
        
        aggregated_costs = {}
        for sid in school_ids:
            if sid in self.aggregated_costs:
                aggregated_costs[sid] = self.aggregated_costs[sid]

        minimum_cost_result = []
        for sc in self.minimum_cost_result:
            if sc.school_id in school_ids:
                minimum_cost_result.append(sc)

        new_space = OutputSpace(fiber_costs = fiber_costs, satellite_costs = satellite_costs, cellular_costs = cellular_costs, p2p_costs = p2p_costs, aggregated_costs = aggregated_costs, minimum_cost_result = minimum_cost_result)

        return new_space

    def full_results_table(self, n_years: int, attribution="both", school_ids = None):
        if self.minimum_cost_result:
            results = self.minimum_cost_result
        else:
            results = self.technology_outputs[0].cost_results
        return results_to_complete_table(results, n_years, attribution, school_ids)

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
    
    def priority_cost_lookup(self):
        """
        Returns a dictionary of school_id: priority cost for connectivity
        for schools that have at least one feasible connection
        """
        min_costs = {}
        for school_id in self.aggregated_costs:
            costs = self.aggregated_costs[school_id]
            if 'cellular' in costs:
                if costs['cellular'].feasible:
                    min_costs[school_id] = costs['cellular']
                    continue
            if 'p2p' in costs:
                if costs['p2p'].feasible:
                    min_costs[school_id] = costs['p2p']
                    continue
            if 'satellite' in costs:
                if costs['satellite'].feasible:
                    min_costs[school_id] = costs['satellite']
                    continue
            
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
                        capex_provider=math.nan,
                        capex_consumer=math.nan,
                        opex=math.nan,
                        opex_provider=math.nan,
                        opex_consumer=math.nan,
                        technology="None",
                        feasible=False,
                        reason=reasons,
                        electricity=PowerConnectionCosts(
                            electricity_opex=math.nan, electricity_capex=math.nan
                        ),
                    )
                )
        return connections
