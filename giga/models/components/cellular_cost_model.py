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
    def __init__(self, config: CellularTechnologyCostConf):
        self.config = config

    def _cost_of_setup(self):
        return self.config.capex.fixed_costs

    def _cost_of_maintenance(self):
        return self.config.opex.fixed_costs

    def _cost_of_operation(self, school):
        return school.bandwidth_demand * self.config.opex.annual_bandwidth_cost_per_mbps

    def compute_costs(
        self, distances: List[PairwiseDistance], data_space: ModelDataSpace
    ):
        electricity_model = ElectricityCostModel(self.config)
        connected_set = set([x.coordinate1.coordinate_id for x in distances])
        capex_costs = self._cost_of_setup()
        opex_provider = self._cost_of_maintenance()
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
                        technology="Cellular",
                        feasible=False,
                        reason="CELLULAR_BW_THRESHOLD",
                    )
            elif sid in connected_set:
                opex_consumer = self._cost_of_operation(school)
                c = SchoolConnectionCosts(
                        school_id=sid,
                        capex=capex_costs,
                        opex=opex_consumer + opex_provider,
                        opex_provider=opex_provider,
                        opex_consumer=opex_consumer,
                        technology="Cellular",
                    )
            else:
                c = SchoolConnectionCosts(
                        school_id=sid,
                        capex=math.nan,
                        opex=math.nan,
                        opex_provider=math.nan,
                        opex_consumer=math.nan,
                        technology="Cellular",
                        feasible=False,
                        reason="CELLULAR_RANGE_THRESHOLD",
                    )
            c.electricity = electricity_model.compute_cost(school)
            costs.append(c)
        return costs

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def run(
        self, data_space: ModelDataSpace, progress_bar: bool = False
    ) -> CostResultSpace:
        """
        Computes a cost table for schools present in the data_space input
        """
        LOGGER.info(f"Starting Cellular Cost Model")
        conection_model = GreedyDistanceConnector(
            data_space.cell_tower_coordinates,
            dynamic_connect=False, # this will create closest distance pairs
            progress_bar=progress_bar,
            maximum_connection_length_m=self.config.constraints.maximum_range,
            distance_cache=data_space.cellular_cache
        )
        # determine which schools are in range of cell towers
        distances = conection_model.run(data_space.school_coordinates)
        costs = self.compute_costs(distances, data_space)
        return CostResultSpace(
            technology_results={"distances": distances}, cost_results=costs
        )
