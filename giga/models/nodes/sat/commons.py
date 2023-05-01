from pydantic import BaseModel, FilePath
from ortools.sat.python import cp_model
import networkx as nx

from giga.data.sat.sat_formula import SATFormula
from giga.schemas.geo import PairwiseDistance, PairwiseDistanceTable, UniqueCoordinate


class SATSolution(BaseModel):
    solution_tree: nx.Graph = None
    initial_cost_graph: nx.Graph = None
    relational_graph: nx.Graph = None
    problem: SATFormula = None
    n_schools: int = None
    total_cost: int = None
    feasible: bool = False
    optimal: bool = False
    optimal_cost: bool = False

    class Config:
        arbitrary_types_allowed = True

    @property
    def solution_edge_distances(self):
        assert (
            self.solution_tree is not None and self.initial_cost_graph is not None
        ), "Need a solution tree and initial cost graph to get edge coordinates"
        edges = []
        for source, target, data in self.solution_tree.edges(data=True):
            edges.append(
                PairwiseDistance(
                    pair_ids=(target, source),
                    distance=data["weight"],
                    coordinate1=UniqueCoordinate(
                        coordinate_id=target,
                        coordinate=self.initial_cost_graph.graph.nodes[target][
                            "coordinate"
                        ],
                    ),
                    coordinate2=UniqueCoordinate(
                        coordinate_id=source,
                        coordinate=self.initial_cost_graph.graph.nodes[source][
                            "coordinate"
                        ],
                    ),
                )
            )
        return PairwiseDistanceTable(distances=edges)

    @property
    def cost_data_attribution(self):
        # TODO: This is a hacky way to get the cost attribution. We should be able to get this from the solver.
        costs = {}
        directed = self.solution_tree.to_directed()
        fnodes = [
            n
            for n, data in self.solution_tree.nodes(data=True)
            if data["label"] == "cfnode"
        ]
        for f in fnodes:
            for source, target in nx.bfs_edges(directed, f):
                data = directed.edges[source, target]
                costs[target] = data
        return costs
