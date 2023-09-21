from typing import List
import math
from pydantic import validate_arguments

from giga.models.nodes.graph.greedy_distance_connector import GreedyDistanceConnector
from giga.schemas.conf.models import P2PTechnologyCostConf
from giga.schemas.output import CostResultSpace, SchoolConnectionCosts
from giga.schemas.geo import PairwiseDistance
from giga.data.space.model_data_space import ModelDataSpace
from giga.models.components.electricity_cost_model import ElectricityCostModel
from giga.utils.logging import LOGGER


METERS_IN_KM = 1000.0


class P2PCostModel:
    """
    Estimates the cost of connectivity using point to point wireless technology.
    CapEx considers infrastructure costs of installing a transmitted at a cell tower,
    modem/terminal installation costs at school and solar installation if needed.
    OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.
    """

    def __init__(self, config: P2PTechnologyCostConf):
        self.config = config

    def _cost_of_setup_provider(self):
        return self.config.capex.tower_fixed_costs

    def _cost_of_setup_consumer(self):
        return self.config.capex.fixed_costs

    def _cost_of_operation(self, school):
        return (
            school.bandwidth_demand * self.config.opex.annual_bandwidth_cost_per_mbps
            + self.config.opex.fixed_costs
        )

    def compute_costs(
        self, distances: List[PairwiseDistance], data_space: ModelDataSpace
    ) -> List[SchoolConnectionCosts]:
        """
        Computes the cost of connecting a school to the internet using P2P technology.
        :param distances: a list of distances between schools and locations where p2p transmitters can be installed (e.g. cell towers)
        :param data_space: a data space containing school entities and tower infrastructure
        :return: a list of school connection costs for p2p technology
        """
        new_electricity = self.config.electricity_config.constraints.allow_new_electricity
        electricity_model = ElectricityCostModel(self.config)
        connected_set = set([x.coordinate1.coordinate_id for x in distances])
        capex_provider = self._cost_of_setup_provider()
        capex_consumer = self._cost_of_setup_consumer()
        costs = []
        for school in data_space.school_entities:
            sid = school.giga_id
            if school.bandwidth_demand > self.config.constraints.maximum_bandwithd:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "P2P", "P2P_BW_THRESHOLD"
                )
            elif not school.has_electricity and not new_electricity:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "P2P", "NO_ELECTRICITY"
                )
            elif sid in connected_set:
                opex_consumer = self._cost_of_operation(school)
                c = SchoolConnectionCosts(
                    school_id=sid,
                    capex=capex_provider + capex_consumer,
                    capex_provider=capex_provider,
                    capex_consumer=capex_consumer,
                    opex=opex_consumer,
                    opex_provider=0.0,
                    opex_consumer=opex_consumer,
                    technology="P2P",
                )
                c.electricity = electricity_model.compute_cost(school)
            else:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "P2P", "P2P_RANGE_THRESHOLD"
                )
            costs.append(c)
        return costs

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def run(
        self, data_space: ModelDataSpace, progress_bar: bool = False
    ) -> CostResultSpace:
        """
        Computes a cost table for schools present in the data_space input
        :param data_space: a data space containing school entities and tower infrastructure
        :param progress_bar: whether to show a progress bar
        :return CostResultSpace, that contains the cost of p2p connectivity for all schools in the data space
        """
        LOGGER.info(f"Starting P2P Cost Model")
        connection_model = GreedyDistanceConnector(
            data_space.cell_tower_coordinates,
            dynamic_connect=False,  # this will create closest distance pairs
            progress_bar=progress_bar,
            maximum_connection_length_m=self.config.constraints.maximum_range,
            distance_cache=data_space.p2p_cache,
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
