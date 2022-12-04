from typing import List
import math

from giga.models.nodes.graph.greedy_distance_connector import GreedyDistanceConnector
from giga.schemas.conf.models import FiberTechnologyCostConf
from giga.schemas.results import CostResultSpace, SchoolConnectionCosts
from giga.schemas.geo import PairwiseDistance
from giga.data.space.model_data_space import ModelDataSpace


METERS_IN_KM = 1000.0


class FiberCostModel:
    def __init__(self, config: FiberTechnologyCostConf):
        self.config = config

    def _cost_of_connection(self, distance_km):
        return (
            distance_km * self.config.capex.cost_per_km + self.config.capex.fixed_costs
        )

    def _distance_to_costs(self, distances: List[PairwiseDistance]):
        by_school = {
            x.coordinate1.coordinate_id: {
                "school_id": x.coordinate1.coordinate_id,
                "capex": self._cost_of_connection(x.distance / METERS_IN_KM),
            }
            for x in distances
        }
        return by_school

    def _cost_of_operation(self, _schoold):
        return self.config.opex.fixed_costs

    def compute_costs(
        self, distances: List[PairwiseDistance], data_space: ModelDataSpace
    ):
        capex_costs = self._distance_to_costs(distances)
        costs = []
        for school in data_space.school_coordinates:
            sid = school.coordinate_id
            if sid in capex_costs:
                capex = capex_costs[sid]["capex"]
                opex = self._cost_of_operation(school)
                costs.append(
                    SchoolConnectionCosts(
                        school_id=sid, capex=capex, opex=opex, technology="Fiber"
                    )
                )
            else:
                costs.append(
                    SchoolConnectionCosts(
                        school_id=sid,
                        capex=math.nan,
                        opex=math.nan,
                        technology="Fiber",
                        feasible=False,
                        reason="FIBER_DISTANCE_THRESHOLD",
                    )
                )
        return costs

    def run(self, data_space: ModelDataSpace, progress_bar=False) -> CostResultSpace:
        """
        Computes a cost table for schools present in the data_space input
        """
        conection_model = GreedyDistanceConnector(
            data_space.fiber_coordinates,
            dynamic_connect=self.config.capex.economies_of_scale,
            progress_bar=progress_bar,
            maximum_connection_length_m=self.config.constraints.maximum_connection_length,
        )
        # determine which schools can be connected and their distances
        distances = conection_model.run(data_space.school_coordinates)
        costs = self.compute_costs(distances, data_space)
        return CostResultSpace(
            technology_results={"distances": distances}, cost_results=costs
        )
