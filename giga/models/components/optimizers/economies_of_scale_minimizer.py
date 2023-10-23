from typing import List

from giga.schemas.output import OutputSpace
from giga.schemas.conf.models import CostMinimizerConf
from giga.data.space.connected_cost_graph import ConnectedCostGraph
from giga.schemas.geo import PairwiseDistanceTable, PairwiseDistance
from giga.models.nodes.graph.cost_tree_pruner import CostTreePruner
from giga.models.nodes.graph.cost_tree_pruner import CostTreePrunerV2
from giga.utils.logging import LOGGER


#ECONOMIES_OF_SCALE_TECHNOLOGIES = set(["fiber","p2p"])


class EconomiesOfScaleMinimizer:
    """
    Minimize the cost of a connected cost graph by using a heuristic
    that removes the largest cost leaf node until the cost of the graph
    is less than the baseline cost of the graph OR
    the graph has only one node left.
    """

    def __init__(self, config: CostMinimizerConf, economies_of_scale):
        self.config = config
        self.economies_of_scale = set(economies_of_scale)

    def compute_economies_of_scale_minimums(
        self,
        output: OutputSpace,
        clusters: List[List[PairwiseDistance]],
        pruner: CostTreePrunerV2,
        tech_name: str,
    ):
        """
        This method computes the minimum cost of a connected cost graph
        for each cluster of schools.
        :param output: OutputSpace, that contains cost results for individual technologies
        :param clusters: List[List[PairwiseDistance]], a list of clusters of schools
        :param pruner: CostTreePruner, a pruner that can be used to remove the largest cost leaf nodes iteratively
        :return: tuple of minimums, economies_of_scale_ids, new_connections which represent
                 the minimum costs for each school in all the clusters that are cost optimal with economies of scale,
                 the school IDs for economies of scale schools,
                 the new connections (e.g. pariwise distances) that are cost optimal with economies of scale

        """
        economies_of_scale_ids = []
        new_connections = []
        for c in clusters:
            # for each cluster of schools, find the minimum cost graph
            initial_cost_graph = ConnectedCostGraph.from_pairwise_distances(c)
            minimized_cost_graph = pruner.run(initial_cost_graph)
            # track schools that are cost optimal with economies of scale
            economies_of_scale_ids += [
                n
                for n in list(minimized_cost_graph.graph.nodes())
                if n not in pruner.root_nodes
            ]
            new_connections += minimized_cost_graph.to_pairwise_distances()
        # generate a cost collection for the schools that are cost optimal with economies of scale
        minimums = output.get_technology_cost_collection(
            economies_of_scale_ids, tech_name
        )
        return minimums, economies_of_scale_ids, new_connections
    

    def run(self, output: OutputSpace, scenario_id: str):
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

        :param output: OutputSpace, that contains a distance collection that can be turned into a connected cost graph
        :return a list of minimum costs for each school that are economies of scale optimal
        """
        LOGGER.info("Starting economies of scale minimizer")
        # generate lookups and graph object needed for minimization
        baseline_cost_lookup = output.minimum_cost_lookup(
            self.config.years_opex, ignore_tech=self.economies_of_scale
        )

        # For now, only p2p and fiber are school to school, we might want to do a for loop at some point
        if "fiber" in self.economies_of_scale:
            distances_fiber = PairwiseDistanceTable(distances=output.fiber_distances)
            # group schools into clusters based on their root node (e.g. fiber nodes)
            clusters = list(distances_fiber.group_by_source().values())
            root_nodes = list(distances_fiber.group_by_source().keys())
            tech_name = "fiber"

            # create a pruner to remove schools that exceed baseline costs or budget constraints
            if scenario_id=="minimum_cost_giga":
                pruner = CostTreePrunerV2(
                    self.config.years_opex, baseline_cost_lookup, output, root_nodes, tech_name
                )
            else:
                pruner = CostTreePruner(
                    self.config.years_opex, baseline_cost_lookup, output, root_nodes, tech_name
                )
            # compute the minimum cost of a connected cost graph for each cluster of schools
            (
            minimums,
            economies_of_scale_ids,
            new_connections,
            ) = self.compute_economies_of_scale_minimums(output, clusters, pruner,tech_name)
            if len(output.fiber_distances) > 0:
                # update the output space with the new set of economies of scale connections for fiber and track the old fiber network
                output.fiber_costs.technology_results.complete_network_distances = (
                    output.fiber_costs.technology_results.distances
                )
                output.fiber_costs.technology_results.distances = new_connections

            if "p2p" in self.economies_of_scale:
                distances_p2p = PairwiseDistanceTable(distances=output.p2p_distances)
                # group schools into clusters based on their root node (e.g. fiber nodes)
                clusters = list(distances_p2p.group_by_source().values())
                root_nodes = list(distances_p2p.group_by_source().keys())
                tech_name = "p2p"

                # create a pruner to remove schools that exceed baseline costs or budget constraints
                if scenario_id=="minimum_cost_giga":
                    pruner = CostTreePrunerV2(
                        self.config.years_opex, baseline_cost_lookup, output, root_nodes, tech_name
                    )
                else:
                    pruner = CostTreePruner(
                        self.config.years_opex, baseline_cost_lookup, output, root_nodes, tech_name
                    )
                # compute the minimum cost of a connected cost graph for each cluster of schools
                (
                minimums_p2p,
                economies_of_scale_ids_p2p,
                new_connections_p2p,
                ) = self.compute_economies_of_scale_minimums(output, clusters, pruner,tech_name)

                minimums += minimums_p2p
                economies_of_scale_ids += economies_of_scale_ids_p2p

                if len(output.p2p_distances) > 0:
                # update the output space with the new set of economies of scale connections for fiber and track the old fiber network
                    output.p2p_costs.technology_results.complete_network_distances = (
                        output.p2p_costs.technology_results.distances
                    )
                    output.p2p_costs.technology_results.distances = new_connections_p2p


        else:#only p2p or nothing
            tech_name = "p2p"
            distances_p2p = PairwiseDistanceTable(distances=output.p2p_distances)
            # group schools into clusters based on their root node (e.g. fiber nodes)
            clusters = list(distances_p2p.group_by_source().values())
            root_nodes = list(distances_p2p.group_by_source().keys())
            tech_name = "p2p"

            # create a pruner to remove schools that exceed baseline costs or budget constraints
            if scenario_id=="minimum_cost_giga":
                pruner = CostTreePrunerV2(
                    self.config.years_opex, baseline_cost_lookup, output, root_nodes, tech_name
                )
            else:
                pruner = CostTreePruner(
                    self.config.years_opex, baseline_cost_lookup, output, root_nodes, tech_name
                )
            # compute the minimum cost of a connected cost graph for each cluster of schools
            (
                minimums,
                economies_of_scale_ids,
                new_connections,
            ) = self.compute_economies_of_scale_minimums(output, clusters, pruner,tech_name)

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
            f"Economies of scale minimization: total schools: {len(output.aggregated_costs.keys())}, schools using economies of scale: {len(economies_of_scale_ids)}, schools not using economies of scale: {len(baseline_cost_ids)}, connection not feasible: {len(infeasible_ids)}"
        )
        

        return minimums + baseline_costs + infeasible


    def run_stable(self, output: OutputSpace, scenario_id: str):
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

        :param output: OutputSpace, that contains a distance collection that can be turned into a connected cost graph
        :return a list of minimum costs for each school that are economies of scale optimal
        """
        LOGGER.info("Starting economies of scale minimizer")
        # generate lookups and graph object needed for minimization
        baseline_cost_lookup = output.minimum_cost_lookup(
            self.config.years_opex, ignore_tech=self.economies_of_scale
        )

        # For now, only p2p and fiber are school to school, we might want to do a for loop at some point
        if "fiber" in self.economies_of_scale:
            distances_fiber = PairwiseDistanceTable(distances=output.fiber_distances)
            # group schools into clusters based on their root node (e.g. fiber nodes)
            clusters = list(distances_fiber.group_by_source().values())
            root_nodes = list(distances_fiber.group_by_source().keys())
            tech_name = "fiber"
        else:
            distances_p2p = PairwiseDistanceTable(distances=output.p2p_distances)
            # group schools into clusters based on their root node (e.g. fiber nodes)
            clusters = list(distances_p2p.group_by_source().values())
            root_nodes = list(distances_p2p.group_by_source().keys())
            tech_name = "p2p"

        # create a pruner to remove schools that exceed baseline costs or budget constraints
        if scenario_id=="minimum_cost_giga":
            pruner = CostTreePrunerV2(
                self.config.years_opex, baseline_cost_lookup, output, root_nodes, tech_name
            )
        else:
            pruner = CostTreePruner(
                self.config.years_opex, baseline_cost_lookup, output, root_nodes, tech_name
            )
        # compute the minimum cost of a connected cost graph for each cluster of schools
        (
            minimums,
            economies_of_scale_ids,
            new_connections,
        ) = self.compute_economies_of_scale_minimums(output, clusters, pruner,tech_name)
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
            f"Economies of scale minimization: total schools: {len(output.aggregated_costs.keys())}, schools using economies of scale: {len(economies_of_scale_ids)}, schools not using economies of scale: {len(baseline_cost_ids)}, connection not feasible: {len(infeasible_ids)}"
        )
        if len(output.fiber_distances) > 0:
            # update the output space with the new set of economies of scale connections for fiber and track the old fiber network
            output.fiber_costs.technology_results.complete_network_distances = (
                output.fiber_costs.technology_results.distances
            )
            output.fiber_costs.technology_results.distances = new_connections
            
        return minimums + baseline_costs + infeasible