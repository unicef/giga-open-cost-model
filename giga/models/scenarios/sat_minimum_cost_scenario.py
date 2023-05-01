import math
import numpy as np

from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.output import OutputSpace, SchoolConnectionCosts, CostResultSpace
from giga.schemas.conf.models import SATMinimumCostScenarioConf
from giga.models.nodes.sat.sat_solver_constrained import SATSolverConstrained
from giga.models.components.optimizers.sat_optimizer import SATOptimizer
from giga.utils.logging import LOGGER


class SATMinimumCostScenario:
    """
    Estimates the cost of connecting a collection of schools to the internet
    using a SAT solver to minimize the cost of connecting schools to the internet
    """

    def __init__(
        self,
        config: SATMinimumCostScenarioConf,
        data_space: ModelDataSpace,
        output_space: OutputSpace,
    ):
        self.config = config
        self.data_space = data_space
        self.output_space = output_space

    def _prep(self):
        # update bw demand
        self.data_space.schools.update_bw_demand_all(self.config.bandwidth_demand)

    def _create_minimizer(self):
        return SATOptimizer(self.config.sat_solver_config)

    def run(self, progress_bar: bool = False):
        """
        Runs the minimum cost scenario using a SAT solver

        :param progress_bar, wether or not to show the progress bar when running the scenario
        :return output space that contains costs of each technology considered as well as the minimum costs for each school
        """
        LOGGER.info(f"Starting SAT Minimum Cost Scenario")
        self._prep()
        minimizer = self._create_minimizer()
        costs, solution = minimizer.run(self.data_space)
        self.output_space.fiber_costs = CostResultSpace(
            technology_results={
                "distances": solution.solution_edge_distances.distances
            },
            cost_results=costs,
        )
        return self.output_space
