import numpy as np
import math
from typing import List, Dict
import networkx as nx

from giga.schemas.conf.models import SATSolverConf
from giga.schemas.conf.models import TechnologyConfiguration
from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.output import SchoolConnectionCosts
from giga.data.sat.sat_cost_graph import SATCostGraph, SATCostGraphConf
from giga.models.nodes.sat.sat_solver_constrained import SATSolverConstrained
from giga.models.nodes.sat.sat_solver_unconstrained import SATSolverUnconstrained
from giga.schemas.school import GigaSchool
from giga.models.components.electricity_cost_model import ElectricityCostModel
from giga.models.nodes.sat.commons import SATSolution
from giga.schemas.output import SchoolConnectionCosts, PowerConnectionCosts


METERS_IN_KM = 1000.0


class SATOptimizer:
    """
    Estimates the cost of connecting a collection of schools to the internet
    using a SAT solver
    """

    def __init__(
        self,
        config: SATSolverConf,
        technologies: List[TechnologyConfiguration],
        budget_constraint: float,
        years_opex: int,
    ):
        assert len(technologies) > 0, "At least one technology must be provided"
        assert any(
            [t.technology == "Fiber" for t in technologies]
        ), "Fiber technology must be provided"
        self.config = config
        self.technologies = technologies
        self.budget_constraint = budget_constraint
        self.years_opex = years_opex

    def _get_fiber_tech_conf(self):
        for tech in self.technologies:
            if tech.technology == "Fiber":
                return tech
        raise Exception("Fiber technology must be provided")

    def _edge_data_to_cost_fiber(
        self, school: GigaSchool, data: Dict
    ) -> SchoolConnectionCosts:
        # only fiber connections currently supported
        fiber_conf = self._get_fiber_tech_conf()
        cost_per_kms = fiber_conf.capex.cost_per_km * (
            data["weight"] / METERS_IN_KM
        )  # Fiber is always the first technology
        opex_consumer = (
            school.bandwidth_demand * fiber_conf.opex.annual_bandwidth_cost_per_mbps
        )
        opex_provider = fiber_conf.opex.cost_per_km * (data["weight"] / METERS_IN_KM)
        electricity_model = ElectricityCostModel(fiber_conf)
        return SchoolConnectionCosts(
            school_id=school.giga_id,
            capex=cost_per_kms + fiber_conf.capex.fixed_costs,
            capex_provider=cost_per_kms,
            capex_consumer=fiber_conf.capex.fixed_costs,
            opex=opex_provider + opex_consumer,
            opex_provider=opex_provider,
            opex_consumer=opex_consumer,
            technology="Fiber",
            electricity=electricity_model.compute_cost(school),
        )

    def _solution_to_costs_fiber(
        self,
        data_space: ModelDataSpace,
        solution: SATSolution,
        not_in_graph_ids: List[str],
    ) -> List[SchoolConnectionCosts]:
        """
        Converts a SAT solution to a list of school connection costs
        :param solution: the SAT solution to convert
        :return: a list of school connection costs
        """
        costs = []
        unable_costs = []
        cost_data_attribution = solution.cost_data_attribution
        for s in data_space.school_entities:
            school_id = s.giga_id
            if school_id not in cost_data_attribution:
                if s.connected == False and school_id not in not_in_graph_ids:
                    # unable to connect
                    unable_costs.append(
                        SchoolConnectionCosts.budget_exceeded_cost(
                            school_id,
                            "Fiber",  # only fiber connections currently supported
                        )
                    )
            else:
                costs.append(
                    self._edge_data_to_cost_fiber(s, cost_data_attribution[school_id])
                )
        return costs + unable_costs

    def _get_school_costs_not_in_graph(
        self, data_space: ModelDataSpace, graph: SATCostGraph, bw_excluded: List[str]
    ):
        costs = []
        ids = []
        electricity_model = None  # ElectricityCostModel(self.technologies[0])
        for school in data_space.school_entities:
            sid = school.giga_id
            if sid not in graph.graph.nodes():
                if sid in bw_excluded:
                    reason = "FIBER_BW_THRESHOLD"
                else:
                    reason = "FIBER_DISTANCE_THRESHOLD"
                c = SchoolConnectionCosts.infeasible_cost(sid, "Fiber", reason)
                costs.append(c)
                ids.append(sid)
        return costs, ids

    def _unable_to_connect_costs(
        self, connected: List, data_space: ModelDataSpace
    ) -> List[SchoolConnectionCosts]:
        connected_set = set(connected)
        costs = []
        for s in data_space.school_entities:
            if s.giga_id not in connected_set:
                # unable to connect
                costs.append(
                    SchoolConnectionCosts.budget_exceeded_cost(
                        s.giga_id, "Fiber"  # only fiber connections currently supported
                    )
                )
        return costs

    def run(
        self, data_space: ModelDataSpace, progress_bar: bool = False
    ) -> List[SchoolConnectionCosts]:
        """
        Runs the SAT optimizer on the given data space
        :param data_space: the data space containing school and infrastructure information
        :return: a list of minimum costs for each school
        """
        # use the SATCostGraphConf defaults
        graph, bw_excluded = SATCostGraph.compute_from_data_space(
            data_space,
            SATCostGraphConf(),
            self.technologies,
            self.years_opex,
            progress_bar=progress_bar,
        )
        if self.budget_constraint == math.inf or self.budget_constraint == 0:
            solver = SATSolverUnconstrained(self.config, self.technologies)
        else:
            solver = SATSolverConstrained(
                self.config, self.technologies, int(self.budget_constraint)
            )

        solution = solver.run(graph)
        if solution.feasible or solution.optimal:
            if len(self.technologies) == 1:  # only fiber
                (
                    not_in_graph_costs,
                    not_in_graph_ids,
                ) = self._get_school_costs_not_in_graph(
                    data_space, graph, bw_excluded[0]
                )
                costs = self._solution_to_costs_fiber(
                    data_space, solution, not_in_graph_ids
                )

                return costs + not_in_graph_costs, solution
        # TODO: THIS NEEDS TO BE DEALT WITH DOWNSTREAM
        # Add a loggin message here to deal with no solution found
        return [], None
