from typing import List
import math
from pydantic import validate_arguments

from giga.models.nodes.graph.greedy_distance_connector import GreedyDistanceConnector
from giga.models.nodes.graph.pairwise_distance_model import PairwiseDistanceModel
from giga.models.nodes.graph.vectorized_distance_model import VectorizedDistanceModel
from giga.schemas.conf.models import FiberTechnologyCostConf
from giga.schemas.output import CostResultSpace, SchoolConnectionCosts
from giga.schemas.geo import PairwiseDistance
from giga.data.space.model_data_space import ModelDataSpace
from giga.models.components.electricity_cost_model import ElectricityCostModel
from giga.utils.logging import LOGGER


METERS_IN_KM = 1000.0


class FiberCostModel:
    """
    Estimates the cost of connecting a collection of schools to the internet using fiber technology.
    Can optionally consider economies of scale,
    which allows schools that already connected with fiber during modeling to be used as fiber nodes.
    CapEx considers infrastructure costs of laying fiber,
    modem/terminal installation costs at school and solar installation if needed.
    OpEx considers maintenance of fiber infrastructure, maintenance of equipment at school,
    costs of internet at the school, and electricity costs.
    """

    def __init__(self, config: FiberTechnologyCostConf):
        self.config = config

    def _cost_of_connection(self, distance_km):
        return (
            distance_km * self.config.capex.cost_per_km
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
        return (
            school.bandwidth_demand * self.config.opex.annual_bandwidth_cost_per_mbps
            + self.config.opex.fixed_costs
        )

    def _cost_of_setup(self, school):
        return self.config.capex.fixed_costs

    def compute_costs(
        self, distances: List[PairwiseDistance], data_space: ModelDataSpace
    ) -> List[SchoolConnectionCosts]:
        """
        Computes the cost of connecting a school to the internet using fiber technology.
        :param distances: a list of distances between schools and fiber nodes OR other fiber connected schools
        :param data_space: a data space containing school entities and fiber infrastructure
        :return: a list of school connection costs for fiber technology
        """
        new_electricity = self.config.electricity_config.constraints.allow_new_electricity
        electricity_model = ElectricityCostModel(self.config)
        capex_costs_provider = self._distance_to_capex(distances)
        opex_costs_provider = self._distance_to_opex(distances)
        costs = []
        for school in data_space.school_entities:
            sid = school.giga_id
            if school.bandwidth_demand > self.config.constraints.maximum_bandwithd:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "Fiber", "FIBER_BW_THRESHOLD"
                )
            elif not school.has_electricity and not new_electricity:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "Fiber", "NO_ELECTRICITY"
                )
            elif sid in capex_costs_provider:
                capex_provider = capex_costs_provider[sid]["capex"]
                opex_provider = opex_costs_provider[sid]["opex"]
                capex_consumer = self._cost_of_setup(school)
                opex_consumer = self._cost_of_operation(school)
                c = SchoolConnectionCosts(
                    school_id=sid,
                    capex=capex_provider + capex_consumer,
                    capex_provider=capex_provider,
                    capex_consumer=capex_consumer,
                    opex=opex_consumer + opex_provider,
                    opex_provider=opex_provider,
                    opex_consumer=opex_consumer,
                    technology="Fiber",
                )
                c.electricity = electricity_model.compute_cost(school)
            else:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "Fiber", "FIBER_DISTANCE_THRESHOLD"
                )
            costs.append(c)
        return costs

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def run(
        self,
        data_space: ModelDataSpace,
        progress_bar: bool = False,
        distance_model=VectorizedDistanceModel(),
    ) -> CostResultSpace:
        """
        Computes a cost table for schools present in the data_space input
        :param data_space: a data space containing school entities and fiber infrastructure
        :param progress_bar: whether to show a progress bar
        :param distance_model: a customizable distance model to use for computing pairwise distances
        :return CostResultSpace, that contains the cost of fiber connectivity for all schools in the data space
        """
        LOGGER.info(f"Starting Fiber Cost Model")
        if self.config.capex.schools_as_fiber_nodes:
            connection_model = GreedyDistanceConnector(
                data_space.fiber_coordinates + data_space._fiber_schools,
                dynamic_connect=self.config.capex.economies_of_scale,
                progress_bar=progress_bar,
                maximum_connection_length_m=self.config.constraints.maximum_connection_length,
                distance_model=distance_model,
                distance_cache=data_space.fiber_cache,
            )
        else:
            connection_model = GreedyDistanceConnector(
                data_space.fiber_coordinates,
                dynamic_connect=self.config.capex.economies_of_scale,
                progress_bar=progress_bar,
                maximum_connection_length_m=self.config.constraints.maximum_connection_length,
                distance_model=distance_model,
                distance_cache=data_space.fiber_cache,
            )
        new_electricity = self.config.electricity_config.constraints.allow_new_electricity
        # determine which schools can be connected and their distances
        if new_electricity:
            distances = connection_model.run(data_space.school_coordinates)
        else:
            distances = connection_model.run(data_space.school_with_electricity_coordinates)
        costs = self.compute_costs(distances, data_space)
        return CostResultSpace(
            technology_results={"distances": distances}, cost_results=costs
        )
