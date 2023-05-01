import numpy as np
import math
from typing import List, Dict
import networkx as nx

from giga.schemas.conf.models import SATSolverConf
from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.output import SchoolConnectionCosts
from giga.data.sat.sat_cost_graph import SATCostGraph, SATCostGraphConf
from giga.models.nodes.sat.sat_solver_constrained import SATSolverConstrained
from giga.models.nodes.sat.commons import SATSolution
from giga.schemas.output import SchoolConnectionCosts, PowerConnectionCosts


METERS_IN_KM = 1000.0


class SATOptimizer:
    """
    Estimates the cost of connecting a collection of schools to the internet
    using a SAT solver
    """

    def __init__(self, config: SATSolverConf):
        self.config = config

    def _edge_data_to_cost(self, school_id: str, data: Dict) -> SchoolConnectionCosts:
        # only fiber connections currently supported
        return SchoolConnectionCosts(
            school_id=school_id,
            capex=data["weight"] * self.config.cost_per_km / METERS_IN_KM,
            opex=0.0,  # no attribution of opex in SAT model, need to identify how to treat this
            opex_provider=0.0,
            opex_consumer=0.0,
            technology="Fiber",
            electricity=PowerConnectionCosts(),
        )

    def _solution_to_costs(self, solution: SATSolution) -> List[SchoolConnectionCosts]:
        """
        Converts a SAT solution to a list of school connection costs
        :param solution: the SAT solution to convert
        :return: a list of school connection costs
        """
        costs = []
        for school_id, data in solution.cost_data_attribution.items():
            costs.append(self._edge_data_to_cost(school_id, data))
        return costs

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

    def run(self, data_space: ModelDataSpace) -> List[SchoolConnectionCosts]:
        """
        Runs the SAT optimizer on the given data space
        :param data_space: the data space containing school and infrastructure information
        :return: a list of minimum costs for each school
        """
        # use the SATCostGraphConf defaults
        graph = SATCostGraph.compute_from_data_space(data_space, SATCostGraphConf())
        solver = SATSolverConstrained(self.config)
        solution = solver.run(graph)
        minimum_costs = self._solution_to_costs(solution)
        connected = [cost.school_id for cost in minimum_costs]
        unable_to_connect = self._unable_to_connect_costs(connected, data_space)
        return minimum_costs + unable_to_connect, solution
