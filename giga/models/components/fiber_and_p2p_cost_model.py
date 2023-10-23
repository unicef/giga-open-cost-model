from typing import List
import math
from pydantic import validate_arguments

from giga.models.nodes.graph.greedy_distance_connector import DoubleGreedyDistanceConnector
from giga.models.nodes.graph.pairwise_distance_model import PairwiseDistanceModel
from giga.models.nodes.graph.vectorized_distance_model import VectorizedDistanceModel
from giga.schemas.conf.models import FiberTechnologyCostConf, P2PTechnologyCostConf
from giga.schemas.output import CostResultSpace, SchoolConnectionCosts
from giga.schemas.geo import PairwiseDistance, UniqueCoordinate
from giga.data.space.model_data_space import ModelDataSpace
from giga.models.components.electricity_cost_model import ElectricityCostModel
from giga.utils.logging import LOGGER



METERS_IN_KM = 1000.0


class FiberP2PCostModel:
    """
    Estimates the cost of connecting a collection of schools to the internet using fiber technology.
    Can optionally consider economies of scale,
    which allows schools that already connected with fiber during modeling to be used as fiber nodes.
    CapEx considers infrastructure costs of laying fiber,
    modem/terminal installation costs at school and solar installation if needed.
    OpEx considers maintenance of fiber infrastructure, maintenance of equipment at school,
    costs of internet at the school, and electricity costs.
    """

    def __init__(self, fiber_config: FiberTechnologyCostConf, p2p_config: P2PTechnologyCostConf):
        self.fiber_config = fiber_config
        self.p2p_config = p2p_config

    def p2p_cost_of_setup_provider(self):
        return self.p2p_config.capex.tower_fixed_costs

    def p2p_cost_of_setup_consumer(self):
        return self.p2p_config.capex.fixed_costs

    def p2p_cost_of_operation(self, school):
        return (
            school.bandwidth_demand * self.p2p_config.opex.annual_bandwidth_cost_per_mbps
            + self.p2p_config.opex.fixed_costs
        )

    def fiber_cost_of_connection(self, distance_km):
        return (
            distance_km * self.fiber_config.capex.cost_per_km * self.fiber_config.constraints.correction_coeficient
        )

    def fiber_cost_of_maintenance(self, distance_km):
        return distance_km * self.fiber_config.constraints.correction_coeficient * self.fiber_config.opex.cost_per_km

    def fiber_distance_to_capex(self, distances: List[PairwiseDistance]):
        by_school = {
            x.coordinate1.coordinate_id: {
                "school_id": x.coordinate1.coordinate_id,
                "capex": self.fiber_cost_of_connection(x.distance / METERS_IN_KM),
            }
            for x in distances
        }
        return by_school

    def fiber_distance_to_opex(self, distances: List[PairwiseDistance]):
        by_school = {
            x.coordinate1.coordinate_id: {
                "school_id": x.coordinate1.coordinate_id,
                "opex": self.fiber_cost_of_maintenance(x.distance / METERS_IN_KM),
            }
            for x in distances
        }
        return by_school

    def fiber_cost_of_operation(self, school):
        return (
            school.bandwidth_demand * self.fiber_config.opex.annual_bandwidth_cost_per_mbps
            + self.fiber_config.opex.fixed_costs
        )

    def fiber_cost_of_setup(self, school):
        return self.fiber_config.capex.fixed_costs

    def compute_fiber_costs(
        self, distances: List[PairwiseDistance], data_space: ModelDataSpace
    ) -> List[SchoolConnectionCosts]:
        """
        Computes the cost of connecting a school to the internet using fiber technology.
        :param distances: a list of distances between schools and fiber nodes OR other fiber connected schools
        :param data_space: a data space containing school entities and fiber infrastructure
        :return: a list of school connection costs for fiber technology
        """
        new_electricity = self.fiber_config.electricity_config.constraints.allow_new_electricity
        electricity_model = ElectricityCostModel(self.fiber_config)
        capex_costs_provider = self.fiber_distance_to_capex(distances)
        opex_costs_provider = self.fiber_distance_to_opex(distances)
        costs = []
        for school in data_space.school_entities:
            sid = school.giga_id
            if school.bandwidth_demand > self.fiber_config.constraints.maximum_bandwithd:
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
                capex_consumer = self.fiber_cost_of_setup(school)
                opex_consumer = self.fiber_cost_of_operation(school)
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
    
    def compute_p2p_costs(
        self, distances: List[PairwiseDistance], data_space: ModelDataSpace
    ) -> List[SchoolConnectionCosts]:
        """
        Computes the cost of connecting a school to the internet using P2P technology.
        :param distances: a list of distances between schools and locations where p2p transmitters can be installed (e.g. cell towers)
        :param data_space: a data space containing school entities and tower infrastructure
        :return: a list of school connection costs for p2p technology
        """
        new_electricity = self.p2p_config.electricity_config.constraints.allow_new_electricity
        electricity_model = ElectricityCostModel(self.p2p_config)
        connected_set = set([x.coordinate1.coordinate_id for x in distances])
        capex_provider = self.p2p_cost_of_setup_provider()
        capex_consumer = self.p2p_cost_of_setup_consumer()
        costs = []
        for school in data_space.school_entities:
            sid = school.giga_id
            if school.bandwidth_demand > self.p2p_config.constraints.maximum_bandwithd:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "P2P", "P2P_BW_THRESHOLD"
                )
            elif not school.has_electricity and not new_electricity:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "P2P", "NO_ELECTRICITY"
                )
            elif sid in connected_set:
                opex_consumer = self.p2p_cost_of_operation(school)
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
    
    def compute_costs(
        self, fiber_distances: List[PairwiseDistance], p2p_distances: List[PairwiseDistance], data_space: ModelDataSpace
    ) -> (List[SchoolConnectionCosts],List[SchoolConnectionCosts]):
        return self.compute_fiber_costs(fiber_distances, data_space), self.compute_p2p_costs(p2p_distances, data_space)
    
    def get_distance_threshold(self):
        bd = 20
        years = 5
        d = (self.p2p_config.capex.tower_fixed_costs+self.p2p_config.capex.fixed_costs+years*(bd*self.p2p_config.opex.annual_bandwidth_cost_per_mbps
            + self.p2p_config.opex.fixed_costs) - self.fiber_config.capex.fixed_costs - years*(bd*self.fiber_config.opex.annual_bandwidth_cost_per_mbps
            + self.fiber_config.opex.fixed_costs))/(self.fiber_config.capex.cost_per_km * self.fiber_config.constraints.correction_coeficient)
    
        return d

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def run(
        self,
        data_space: ModelDataSpace,
        used_ids: List = [],
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
        LOGGER.info(f"Starting Fiber and P2P Cost Model")

        ### Fiber
        #fiber_cache = data_space.fiber_cache
        if len(data_space.fiber_coordinates)==0:
            #use distance to fiber in master
            connected = [UniqueCoordinate(coordinate_id="metanode")]
            if self.fiber_config.capex.schools_as_fiber_nodes:
                connected += data_space._fiber_schools

            data_space.fiber_cache.redo_meta(connected,data_space.school_entities)
        else:
            connected = data_space.fiber_coordinates
            k = len(connected)
            if self.fiber_config.capex.schools_as_fiber_nodes:
                connected += data_space._fiber_schools
                if len(connected)>k:
                    data_space.fiber_cache.redo_schools(connected,k,data_space.school_entities)

        #####

        ### P2P

        #####

        distance_threshold = self.get_distance_threshold()* METERS_IN_KM

        connection_model = DoubleGreedyDistanceConnector(
            [connected,data_space.cell_tower_coordinates],
            dynamic_connect=self.fiber_config.capex.economies_of_scale,
            maximum_connection_length_m=[self.fiber_config.constraints.maximum_connection_length * METERS_IN_KM,self.p2p_config.constraints.maximum_range * METERS_IN_KM],
            distance_model=distance_model,
            progress_bar=progress_bar,
            distance_cache=[data_space.fiber_cache,data_space.p2p_cache],
            distance_threshold=distance_threshold
        )
        new_electricity = self.fiber_config.electricity_config.constraints.allow_new_electricity
        # determine which schools can be connected and their distances
        if new_electricity:
            school_coords = [coord for coord in data_space.school_coordinates if coord.coordinate_id not in used_ids]
            fiber_distances,p2p_distances = connection_model.run(school_coords)
        else:
            school_coords = [coord for coord in data_space.school_with_electricity_coordinates if coord.coordinate_id not in used_ids]
            fiber_distances,p2p_distances = connection_model.run(school_coords)
        fiber_costs, p2p_costs = self.compute_costs(fiber_distances,p2p_distances,data_space)
        return CostResultSpace(
            technology_results={"distances": fiber_distances}, cost_results=fiber_costs, tech_name="fiber"
        ), CostResultSpace(
            technology_results={"distances": p2p_distances}, cost_results=p2p_costs, tech_name="p2p"
        )
