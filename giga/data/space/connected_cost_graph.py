import pandas as pd
import numpy as np
import networkx as nx

from giga.schemas.geo import PairwiseDistance


class ConnectedCostGraph:
    """
    A connected cost graph is a directed graph where each node
    represents a school and each edge represents the cost of
    connecting the school to connectivity infrastructure.
    """

    def __init__(self, graph, coordinates=None):
        self.graph = graph
        self.coordinates = coordinates

    @staticmethod
    def from_pairwise_distances(distances):
        # Create a directed graph from a list of pairwise distances
        edges = []
        coords = {}
        for e in distances:
            edges.append(
                {
                    "source": e.pair_ids[1],
                    "target": e.pair_ids[0],
                    "weight": int(np.round(e.distance)),
                }
            )
            coords[e.coordinate1.coordinate_id] = e.coordinate1
            coords[e.coordinate2.coordinate_id] = e.coordinate2
        frame = pd.DataFrame(edges)
        G = nx.from_pandas_edgelist(
            frame, edge_attr="weight", create_using=nx.DiGraph()
        )
        return ConnectedCostGraph(G, coords)

    @property
    def total_cost(self):
        # The total cost of the graph is the sum of the weights of all edges
        return self.graph.size(weight="weight")

    @property
    def leaf_nodes(self):
        # A leaf node is a node with no outgoing edges and exactly one incoming edge
        return [
            node
            for node in self.graph
            if self.graph.out_degree(node) == 0 and self.graph.in_degree(node) == 1
        ]

    @property
    def largest_leaf_edge(self):
        # The largest leaf edge is the edge with the largest weight that connects a leaf node to the graph
        leaf_edges = self.graph.in_edges(self.leaf_nodes, data=True)
        return sorted(leaf_edges, key=lambda x: x[2]["weight"])[-1]

    @property
    def largest_cost_leaf_node(self):
        # The largest cost leaf node is the leaf node with the largest weight edge
        return self.largest_leaf_edge[1]

    def remove_node(self, node):
        # Remove a node from the graph
        self.graph.remove_node(node)

    def to_pairwise_distances(self):
        # Convert the graph back to a list of pairwise distances
        edges = self.graph.edges(data=True)
        return [
            PairwiseDistance(
                pair_ids=(e[0], e[1]),
                coordinate1=self.coordinates[e[0]],
                coordinate2=self.coordinates[e[1]],
                distance=e[2]["weight"],
            )
            for e in edges
        ]
