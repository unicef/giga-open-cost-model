from giga.schemas.output import OutputSpace
from giga.schemas.conf.models import CostMinimizerConf
from giga.data.space.connected_cost_graph import ConnectedCostGraph
from giga.schemas.geo import PairwiseDistanceTable
from giga.utils.logging import LOGGER


class EconomiesOfScaleMinimizer:
    """
    Minimize the cost of a connected cost graph by using a heuristic
    that removes the largest cost leaf node until the cost of the graph
    is less than the baseline cost of the graph OR
    the graph has only one node left.
    """

    def __init__(self, config: CostMinimizerConf):
        self.config = config

    def get_optimization_callbacks(self, output, root_nodes, baseline_cost_lookup):
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
            nodes = [n for n in list(x.graph.nodes()) if n not in root_nodes]
            return output.project_lifetime_cost(nodes, "fiber", self.config.years_opex)

        def terminal(x):
            # accepts a connected cost graph and returns True if the graph is in a terminal state
            if len(x.graph.nodes()) <= 1:
                return True
            else:
                return False

        def constraint(x):
            # accepts a connected cost graph and returns the baseline cost (e.g. constraint) of the graph
            node_ids = [n for n in list(x.graph.nodes()) if n not in root_nodes]
            return sum(
                [
                    baseline_cost_lookup[sid].technology_connectivity_cost(
                        self.config.years_opex
                    )
                    for sid in node_ids
                ]
            )

        return step, evaluate, constraint, terminal

    def minimize(self, output, cost_graph, root_nodes, baseline_cost_lookup):
        # minimizes the cost of a connected cost graph by iteratively removing the largest cost leaf nodes
        step, evaluate, constraint, terminal = self.get_search_callbacks(
            output, root_nodes, baseline_cost_lookup
        )
        while (evaluate(cost_graph) > constraint(cost_graph)) and (
            not terminal(cost_graph)
        ):
            cost_graph = step(cost_graph)
        return cost_graph

    def run(self, output: OutputSpace):
        """
        This method runs the economies of scale minimizer on a connected cost graph
        that represents interdependencies between schools.
            Input: OutputSpace, that contains a distance collection that can be turned into a connected cost graph
                   AND a set of baseline costs estimated for any other technologies
            Output: A collection of school costs that includes any schools that are cheaper to connect with economies of scale

        The algorithm works as follows:
            1. Group the schools into clusters based on their root node (e.g. fiber nodes)
            2. For each cluster, minimize the cost of the connected cost graph
                a. Remove the largest cost leaf node until the cost of the graph is less than the baseline cost of the graph OR
                      the graph has only one node left.
                b. Assign the costs of the minimized connected cost graph to the fiber technology
            3. Assign the costs of the baseline costs to any schools that are not in the minimized connected cost graph
            4. Assign the costs of the infeasible connections to any schools that are not in the minimized connected cost graph

        """
        LOGGER.info("Starting economies of scale minimizer")
        # generate lookups and graph object needed for minimization
        baseline_cost_lookup = output_space.minimum_cost_lookup(
            self.config.years_opex, ignore_tech=set("fiber")
        )
        distances = PairwiseDistanceTable(
            distances=output.fiber_costs.technology_results.distances
        )
        # group schools into clusters based on their root node (e.g. fiber nodes)
        clusters, root_nodes = list(distances.group_by_source().values()), set(
            distances.group_by_source().keys()
        )
        economies_of_scale_ids = []
        new_connections = []
        for c in clusters:
            # for each cluster of schools, find the minimum cost graph
            initial_cost_graph = ConnectedCostGraph.from_pairwise_distances(c)
            minimized_cost_graph = self.minimize(
                output, initial_cost_graph, root_nodes, baseline_cost_lookup
            )
            # track schools that are cost optimal with economies of scale
            economies_of_scale_ids += [
                n
                for n in list(minimized_cost_graph.graph.nodes())
                if n not in root_nodes
            ]
            new_connections += minimized_cost_graph.to_pairwise_distances()
        # generate a cost collection for the schools that are cost optimal with economies of scale
        minimums = output.get_technology_cost_collection(
            economies_of_scale_ids, "fiber"
        )
        # generate a cost collection for the schools that are not cost optimal with economies of scale, these have costs of NaN
        infeasible = output.infeasible_connections()
        infeasible_ids = [c.school_id for c in infeasible]
        # generate a cost collection for the schools that are not cost optimal with economies of scale, these have baseline costs
        baseline_cost_ids = (
            set(output.aggregated_costs.keys())
            .difference(economies_of_scale_ids)
            .difference(infeasible_ids)
        )
        baseline_costs = [baseline_cost_lookup[sid] for sid in baseline_cost_ids]
        LOGGER.info(
            f"Completed economies of scale minimization: total schools: {len(output.aggregated_costs.keys())}, schools optimal using economies of scale: {len(economies_of_scale_ids)}, schools optimal not using economies of scale: {len(baseline_cost_ids)}, connection not feasible: {len(infeasible_ids)}"
        )
        # update the output space with the new set of economies of scale connections for fiber and track the old fiber network
        output.fiber_costs.technology_results.complete_network_distances = (
            output.fiber_costs.technology_results.distances
        )
        output.fiber_costs.technology_results.distances = new_connections
        return minimums + baseline_costs + infeasible
