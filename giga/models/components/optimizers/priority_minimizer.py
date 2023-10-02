from typing import List

from giga.schemas.output import OutputSpace, SchoolConnectionCosts
from giga.schemas.conf.models import CostMinimizerConf
from giga.utils.logging import LOGGER


class PriorityMinimizer:
    """
    Minimize the cost of a connected cost graph by using a heuristic
    that removes the largest cost leaf node until the cost of the graph
    is less than the baseline cost of the graph OR
    the graph has only one node left.
    """

    def __init__(self, config: CostMinimizerConf):
        self.config = config


    def run(self, output: OutputSpace, scenario_id: str):
        """
       
        """
        LOGGER.info("Starting priorities scenario")
        connections = []
        for sid in output.aggregated_costs:
            if 'fiber' in output.aggregated_costs[sid]:
                if output.aggregated_costs[sid]['fiber'].feasible:
                    connections.append(output.aggregated_costs[sid]['fiber'])
                    continue
            if 'cellular' in output.aggregated_costs[sid]:
                if output.aggregated_costs[sid]['cellular'].feasible:
                    connections.append(output.aggregated_costs[sid]['cellular'])
                    continue
            if 'p2p' in output.aggregated_costs[sid]:
                if output.aggregated_costs[sid]['p2p'].feasible:
                    connections.append(output.aggregated_costs[sid]['p2p'])
                    continue
            if 'satellite' in output.aggregated_costs[sid]:
                if output.aggregated_costs[sid]['satellite'].feasible:
                    connections.append(output.aggregated_costs[sid]['satellite'])
                    continue
            
            connections.append(SchoolConnectionCosts.infeasible_cost(sid, "None", "OUT OF RANGE"))

        return connections
