from typing import List
import math
from pydantic import validate_arguments

from giga.models.nodes.graph.greedy_distance_connector import GreedyDistanceConnector
from giga.schemas.conf.models import CellularTechnologyCostConf
from giga.schemas.output import CostResultSpace, SchoolConnectionCosts
from giga.schemas.geo import PairwiseDistance
from giga.data.space.model_data_space import ModelDataSpace
from giga.models.components.electricity_cost_model import ElectricityCostModel
from giga.utils.logging import LOGGER


METERS_IN_KM = 1000.0


class CellularCostModel:
    """
    Cost model for estimating the cost of cellular connectivity.
    CapEx considers modem installation at school and solar installation if needed.
    No other infrastructure costs are considered.
    OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.
    """

    def __init__(self, config: CellularTechnologyCostConf):
        self.config = config

    def _cost_of_setup(self):
        return self.config.capex.fixed_costs

    def _cost_of_operation(self, school):
        return (
            school.bandwidth_demand * self.config.opex.annual_bandwidth_cost_per_mbps
            + self.config.opex.fixed_costs
        )

    def _existing_cell_coverage(self, school):
        return (
            school.cell_coverage_type
            in self.config.constraints.valid_cellular_technologies
        )

    def compute_costs(
        self, distances: List[PairwiseDistance], data_space: ModelDataSpace
    ) -> List[SchoolConnectionCosts]:
        """
        Compute the cost of cellular connectivity for each school in the data space.
        :param distances: List of distances between schools and cell towers
        :param data_space: ModelDataSpace, that contains school entities
        :return: List of SchoolConnectionCosts, that contains the cost of cellular connectivity for each school
        """
        new_electricity = self.config.electricity_config.constraints.allow_new_electricity
        electricity_model = ElectricityCostModel(self.config)
        connected_set = set([x.coordinate1.coordinate_id for x in distances])
        capex_consumer = self._cost_of_setup()
        costs = []
        for school in data_space.school_entities:
            sid = school.giga_id
            if school.bandwidth_demand > self.config.constraints.maximum_bandwithd:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "Cellular", "CELLULAR_BW_THRESHOLD"
                )
            elif not school.has_electricity and not new_electricity:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "Cellular", "NO_ELECTRICITY"
                )
            elif sid in connected_set or self._existing_cell_coverage(school):
                # either school is in range of a cell tower or school has coverage information from supplemental data
                opex_consumer = self._cost_of_operation(school)
                c = SchoolConnectionCosts(
                    school_id=sid,
                    capex=capex_consumer,
                    capex_provider=0.0,
                    capex_consumer=capex_consumer,
                    opex=opex_consumer,
                    opex_provider=0.0,
                    opex_consumer=opex_consumer,
                    technology="Cellular",
                )
                c.electricity = electricity_model.compute_cost(school)
            else:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "Cellular", "CELLULAR_RANGE_THRESHOLD"
                )
            costs.append(c)
        return costs

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def run(
        self, data_space: ModelDataSpace, progress_bar: bool = False
    ) -> CostResultSpace:
        """
        Computes a cost table for schools present in the data_space input
        :param data_space: ModelDataSpace, that contains school entities, and cell tower coordinates
        :param progress_bar: bool, whether to show a progress bar
        :return: CostResultSpace, that contains the cost of cellular connectivity for all schools in the data space
        """
        tower_coordinates = data_space.get_cell_tower_coordinates_with_technologies(
            self.config.constraints.valid_cellular_technologies
        )
        LOGGER.info(f"Starting Cellular Cost Model")
        connection_model = GreedyDistanceConnector(
            tower_coordinates,
            dynamic_connect=False,  # this will create closest distance pairs
            progress_bar=progress_bar,
            maximum_connection_length_m=self.config.constraints.maximum_range * METERS_IN_KM,
            distance_cache=data_space.cellular_cache,
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
