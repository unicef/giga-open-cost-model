import math
from typing import List, Dict

from giga.schemas.output import SchoolConnectionCosts, OutputSpace
from giga.data.space.connected_cost_graph import ConnectedCostGraph


class CostTreePruner:
    def __init__(
        self,
        project_years: int,
        dynamic_upper_bound_lookup: Dict[str, SchoolConnectionCosts],
        output: OutputSpace,
        root_nodes: List[str],
        static_upper_bound: float = math.inf,
    ):
        self.project_years = project_years
        self.dynamic_upper_bound_lookup = dynamic_upper_bound_lookup
        self.output = output
        self.root_nodes = root_nodes
        self.static_upper_bound = static_upper_bound

    def get_optimization_callbacks(self):
        """
        Generates a set of callbacks that are used by the minimizer:
        step: used to search the space of possible graphs by (can have any implementation including ones based on gradient descent)
        evaluate: used to evaluate the cost of a graph
        terminal: used to determine if a graph is in a terminal state
        constraint: used to evaluate the baseline cost of a graph or the constraint value that a minimum cost graph must be below
        """

        def step(x):
            # accepts a connected cost graph and returns a modified connected cost graph
            x.remove_node(x.largest_cost_leaf_node)
            return x

        def evaluate(x):
            # accepts a connected cost graph and returns the cost of the graph
            nodes = [n for n in list(x.graph.nodes()) if n not in self.root_nodes]
            return self.output.project_lifetime_cost(nodes, "fiber", self.project_years)

        def terminal(x):
            # accepts a connected cost graph and returns True if the graph is in a terminal state
            if len(x.graph.nodes()) <= 1:
                return True
            else:
                return False

        def constraint(x):
            # accepts a connected cost graph and returns the baseline cost (e.g. constraint) of the graph
            # minimum bounds constraint is the smallest of the baseline upper bound or the static upper bound
            node_ids = [n for n in list(x.graph.nodes()) if n not in self.root_nodes]
            baseline_cost = sum(
                [
                    self.dynamic_upper_bound_lookup[sid].technology_connectivity_cost(
                        self.project_years
                    )
                    for sid in node_ids
                ]
            )
            return min(baseline_cost, self.static_upper_bound)

        return step, evaluate, constraint, terminal

    def run(self, cost_graph: ConnectedCostGraph):
        """
        This method runs the minimizer on a connected cost graph, it follows the following steps:
            For a cluster, minimize the cost of the connected cost graph
                a. Remove the largest cost leaf node until the cost of the graph is less than the baseline cost of the graph OR
                        the graph has only one node left.
                b. Assign the costs of the minimized connected cost graph to the fiber technology
        """
        step, evaluate, constraint, terminal = self.get_optimization_callbacks()
        while (evaluate(cost_graph) > constraint(cost_graph)) and (
            not terminal(cost_graph)
        ):
            cost_graph = step(cost_graph)
        return cost_graph
