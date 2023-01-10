from typing import List
import math
from pydantic import validate_arguments

from giga.models.nodes.graph.greedy_distance_connector import GreedyDistanceConnector
from giga.models.nodes.graph.pairwise_distance_model import PairwiseDistanceModel
from giga.schemas.conf.models import FiberTechnologyCostConf
from giga.schemas.output import CostResultSpace, SchoolConnectionCosts
from giga.schemas.geo import PairwiseDistance
from giga.data.space.model_data_space import ModelDataSpace
from giga.models.components.electricity_cost_model import ElectricityCostModel


METERS_IN_KM = 1000.0


class FiberCostModel:
    """ Estimates the cost of connecting a collection of schools to the internet
        using fiber technology
    """
    def __init__(self, config: FiberTechnologyCostConf):
        self.config = config

    def _cost_of_connection(self, distance_km):
        return (
            distance_km * self.config.capex.cost_per_km + self.config.capex.fixed_costs
        )

    def _cost_of_maintenance(self, distance_km):
        return distance_km * self.config.opex.cost_per_km

    def _distance_to_capex(self, distances: List[PairwiseDistance]):
        by_school = {
            x.coordinate1.coordinate_id: {
                "school_id": x.coordinate1.coordinate_id,
                "capex": self._cost_of_connection(x.distance / METERS_IN_KM),
            }
            for x in distances
        }
        return by_school

    def _distance_to_opex(self, distances: List[PairwiseDistance]):
        by_school = {
            x.coordinate1.coordinate_id: {
                "school_id": x.coordinate1.coordinate_id,
                "opex": self._cost_of_maintenance(x.distance / METERS_IN_KM),
            }
            for x in distances
        }
        return by_school

    def _cost_of_operation(self, school):
        return school.bandwidth_demand * self.config.opex.annual_bandwidth_cost_per_mbps

    def compute_costs(
        self, distances: List[PairwiseDistance], data_space: ModelDataSpace
    ):
        electricity_model = ElectricityCostModel(self.config)
        capex_costs = self._distance_to_capex(distances)
        opex_costs_provider = self._distance_to_opex(distances)
        costs = []
        for school in data_space.school_entities:
            sid = school.giga_id
            if school.bandwidth_demand > self.config.constraints.maximum_bandwithd:
                c = SchoolConnectionCosts(
                        school_id=sid,
                        capex=math.nan,
                        opex=math.nan,
                        opex_provider=math.nan,
                        opex_consumer=math.nan,
                        technology="Fiber",
                        feasible=False,
                        reason="FIBER_BW_THRESHOLD",
                    )
            elif sid in capex_costs:
                capex = capex_costs[sid]["capex"]
                opex_consumer = self._cost_of_operation(school)
                opex_provider = opex_costs_provider[sid]["opex"]
                c = SchoolConnectionCosts(
                        school_id=sid,
                        capex=capex,
                        opex=opex_consumer + opex_provider,
                        opex_provider=opex_provider,
                        opex_consumer=opex_consumer,
                        technology="Fiber",
                    )
            else:
                c = SchoolConnectionCosts(
                        school_id=sid,
                        capex=math.nan,
                        opex=math.nan,
                        opex_provider=math.nan,
                        opex_consumer=math.nan,
                        technology="Fiber",
                        feasible=False,
                        reason="FIBER_DISTANCE_THRESHOLD",
                    )
            c.electricity = electricity_model.compute_cost(school)
            costs.append(c)
        return costs

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def run(
        self, data_space: ModelDataSpace, progress_bar: bool = False, distance_model = PairwiseDistanceModel()
    ) -> CostResultSpace:
        """
        Computes a cost table for schools present in the data_space input
        """
        conection_model = GreedyDistanceConnector(
            data_space.fiber_coordinates,
            dynamic_connect=self.config.capex.economies_of_scale,
            progress_bar=progress_bar,
            maximum_connection_length_m=self.config.constraints.maximum_connection_length,
            distance_model=distance_model
        )
        # determine which schools can be connected and their distances
        distances = conection_model.run(data_space.school_coordinates)
        costs = self.compute_costs(distances, data_space)
        return CostResultSpace(
            technology_results={"distances": distances}, cost_results=costs
        )
