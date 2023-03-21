import numpy as np

from giga.schemas.output import OutputSpace
from giga.schemas.conf.models import CostMinimizerConf
from giga.data.space.connected_cost_graph import ConnectedCostGraph
from giga.schemas.geo import PairwiseDistanceTable
from giga.schemas.output import SchoolConnectionCosts
from giga.models.nodes.graph.cost_tree_pruner import CostTreePruner
from giga.utils.logging import LOGGER


ECONOMIES_OF_SCALE_TECHNOLOGIES = set(["fiber"])


class ConstrainedEconomiesOfScaleMinimizer:
    """
    Minimize the cost of connecting schools under a budget constraint
    by connecting the schools with lowest cost per school first under economies of scale.
    """

    def __init__(self, config: CostMinimizerConf):
        self.config = config

    def _compute_cluster_costs(self, clusters, pruner, root_nodes, output):
        """
        This method computes the minimum cost baseline of a connected cost graph
        for each cluster of schools.
        """
        costs = []
        for c in clusters:
            initial_cost_graph = ConnectedCostGraph.from_pairwise_distances(c)
            minimized_cost_graph = pruner.run(initial_cost_graph)
            cluster_schools = [
                n
                for n in list(minimized_cost_graph.graph.nodes())
                if n not in root_nodes
            ]
            cluster_costs = output.project_lifetime_cost(
                cluster_schools, "fiber", self.config.years_opex
            )
            costs.append((cluster_costs, cluster_schools, minimized_cost_graph))
        return costs

    def _order_schools_by_cost_per_school(self, costs):
        """
        This method orders schools by cost per school.
        """
        # select cluster with schools in them
        costs = [c for c in costs if len(c[1]) > 0]
        # sort based on cost per school
        cost_per_school = [c[0] / len(c[1]) for c in costs]
        ordered_costs = [x for _, x in sorted(zip(cost_per_school, costs))]
        return ordered_costs

    def _process_cost_graph_under_budget(
        self, budget_remaining, cost_graph, root_nodes
    ):
        """
        This method processes a cost graph that fully falls below the budget constraint.
        """
        # update budget
        budget_remaining -= cost_graph.total_cost
        # get the schools that are connected
        schools = [n for n in list(cost_graph.graph.nodes()) if n not in root_nodes]
        # get the connections between the schools
        connections = cost_graph.to_pairwise_distances()
        return budget_remaining, schools, connections

    def _process_cost_graph_over_budget(
        self, budget_remaining, cost_graph, root_nodes, output, pruner
    ):
        """
        This method processes a cost graph that falls over the budget constraint.
        """
        constrained_graph = pruner.run(cost_graph)
        constrained_schools = [
            n for n in list(constrained_graph.graph.nodes()) if n not in root_nodes
        ]
        constrained_costs = output.project_lifetime_cost(
            constrained_schools, "fiber", self.config.years_opex
        )
        budget_remaining -= constrained_costs
        connections = cost_graph.to_pairwise_distances()
        return budget_remaining, constrained_schools, connections

    def minimize_economies_of_scale(
        self, output, clusters, root_nodes, baseline_cost_lookup
    ):
        """
        This method computes the minimum cost of a connected cost graph
        for each cluster of schools, while respecting a budget constraint.
        """
        pruner = CostTreePruner(
            self.config.years_opex,
            baseline_cost_lookup,
            output,
            root_nodes,
            static_upper_bound=self.config.budget_constraint,
        )
        # find the economies of scale costs of all the clusters
        costs = self._compute_cluster_costs(clusters, pruner, root_nodes, output)
        # order the schools by cost per school
        ordered_costs = self._order_schools_by_cost_per_school(costs)
        # while there is budget add cluster and reduce budget
        budget_remaining = self.config.budget_constraint
        connections = []
        school_ids = []
        for c in ordered_costs:
            cluster_cost, cluster, cost_graph = c
            if cluster_cost < budget_remaining:
                # if the whole cluster falls under the budget, this is the optimal solution
                (
                    budget_remaining,
                    cluster_schools,
                    cluster_connections,
                ) = self._process_cost_graph_under_budget(
                    budget_remaining, cost_graph, root_nodes
                )
                school_ids += cluster_schools
                connections += cluster_connections
            else:
                # if the cluster cost is above budget, drop leaf nodes until the budget constraint is satisfied
                pruner = CostTreePruner(
                    self.config.years_opex,
                    baseline_cost_lookup,
                    output,
                    root_nodes,
                    static_upper_bound=budget_remaining,
                )
                (
                    budget_remaining,
                    cluster_schools,
                    cluster_connections,
                ) = self._process_cost_graph_over_budget(
                    budget_remaining, cost_graph, root_nodes, output, pruner
                )
                school_ids += cluster_schools
                connections += cost_graph.to_pairwise_distances()
                break
        # generate a cost collection for the schools that are cost optimal with economies of scale
        minimums = output.get_technology_cost_collection(school_ids, "fiber")
        return minimums, connections, school_ids, budget_remaining

    def minimize_baseline_costs(
        self, budget_remaining, output, baseline_cost_lookup, baseline_cost_ids
    ):
        baseline_costs = [baseline_cost_lookup[sid] for sid in baseline_cost_ids]
        sorted_baseline_costs = sorted(
            baseline_costs,
            key=lambda x: x.technology_connectivity_cost(self.config.years_opex),
        )
        budget_constrained_baseline_costs = []
        budget_constrained_baseline_ids = []
        for c in sorted_baseline_costs:
            # add schools unitl budget exceeded
            conn_cost = c.technology_connectivity_cost(self.config.years_opex)
            delta = budget_remaining - conn_cost
            if delta >= 0.0:
                budget_constrained_baseline_costs += [c]
                budget_constrained_baseline_ids += [c.school_id]
                budget_remaining -= conn_cost
            else:
                break
        return (
            budget_constrained_baseline_costs,
            budget_constrained_baseline_ids,
            budget_remaining,
        )

    def run(self, output: OutputSpace):
        """
        The constrained minimization follows the approach below:
            1. Because all economies of scale costs are optimal with respect to the baseline costs, they are considered first
            3. Each school cluster that has been selected under economies of scale is added to the connected schools collection until the budget runs out
            3. If there is remaining budget, it will be used to connect the cheapest schools using baseline technologies until the budget runs out.
            4. All other schools are considered not possible to connect and have no cost attribution assigned to them.
        """
        LOGGER.info("Starting budget constrained minimizer")
        # generate lookups and graph object needed for minimization
        baseline_cost_lookup = output.minimum_cost_lookup(
            self.config.years_opex, ignore_tech=ECONOMIES_OF_SCALE_TECHNOLOGIES
        )
        distances = PairwiseDistanceTable(
            distances=output.fiber_costs.technology_results.distances
        )
        # group schools into clusters based on their root node (e.g. fiber nodes)
        clusters = list(distances.group_by_source().values())
        root_nodes = set(distances.group_by_source().keys())
        # minimize the economies of scale costs under the budget constraint
        (
            economies_of_scale_costs,
            connections,
            economies_of_scale_ids,
            budget_remaining,
        ) = self.minimize_economies_of_scale(
            output, clusters, root_nodes, baseline_cost_lookup
        )
        # get connections that are infeasible due constraints not related to budget
        infeasible = output.infeasible_connections()
        infeasible_ids = [c.school_id for c in infeasible]
        # minimize the baseline costs under the budget constraint
        baseline_cost_ids = (
            set(output.aggregated_costs.keys())
            .difference(economies_of_scale_ids)
            .difference(infeasible_ids)
        )
        (
            budget_constrained_baseline_costs,
            budget_constrained_baseline_ids,
            budget_remaining,
        ) = self.minimize_baseline_costs(
            budget_remaining, output, baseline_cost_lookup, baseline_cost_ids
        )
        # generate a cost collection for the schools that are not cost optimal with economies of scale, these have costs of NaN
        unable_to_connect_baseline_ids = (
            set(output.aggregated_costs.keys())
            .difference(economies_of_scale_ids)
            .difference(infeasible_ids)
            .difference(budget_constrained_baseline_ids)
        )
        unable_to_connect_baselines = [
            SchoolConnectionCosts.budget_exceeded_cost(
                sid, baseline_cost_lookup[sid].technology
            )
            for sid in unable_to_connect_baseline_ids
        ]
        LOGGER.info(
            f"Budget minimization: budget remaining: {np.round(budget_remaining, decimals=2)} USD, total schools: {len(output.aggregated_costs.keys())}"
        )
        LOGGER.info(
            f"Budget minimization: schools using economies of scale: {len(economies_of_scale_ids)},"
            f"schools not using economies of scale: {len(budget_constrained_baseline_ids)},"
        )
        LOGGER.info(
            f"Budget minimization: schools exceeding budget: {len(unable_to_connect_baseline_ids)}, connection not feasible: {len(infeasible_ids)}"
        )
        # update the output space with the new set of economies of scale connections for fiber and track the old fiber network
        output.fiber_costs.technology_results.complete_network_distances = (
            output.fiber_costs.technology_results.distances
        )
        output.fiber_costs.technology_results.distances = connections
        return (
            economies_of_scale_costs
            + budget_constrained_baseline_costs
            + unable_to_connect_baselines
            + infeasible
        )
