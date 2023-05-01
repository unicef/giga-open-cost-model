from pydantic import BaseModel
import pandas as pd
import networkx as nx

from giga.data.space.model_data_space import ModelDataSpace
from giga.data.sat.cost_minimum_spanning_tree import CostMinimumSpanningTree
from giga.data.sat.cost_relational_graph import CostRelationalGraph
from giga.models.nodes.graph.vectorized_distance_model import VectorizedDistanceModel
from giga.schemas.geo import PairwiseDistanceTable
from giga.utils.logging import LOGGER
from giga.schemas.geo import PairwiseDistance, PairwiseDistanceTable, UniqueCoordinate


LABEL_LOOKUP = {
    "school": "uschool",
    "uschool": "uschool",
    "cschool": "cschool",
    "fiber": "cfnode",
    "cfnode": "cfnode",
    "ufnode": "ufnode",
    "splitter": "splitter",
}

PINDEX_LOOKUP = {
    "school": 1,
    "uschool": 1,
    "cschool": 0,
    "fiber": 0,
    "cfnode": 0,
    "ufnode": 0,
    "splitter": 0,
}

CONNECTED_NODE_LABELS = set(["cfnode", "ufnode", "cschool"])

CONNECTED_META_NODE_LABEL = "metanode"


class SATCostGraphConf(BaseModel):
    """Configuration for SAT cost graph"""

    base_node_cost: int = 0
    base_n_cost: int = 0
    base_per_km_cost: int = 0
    relational_graph_edge_threshold: int = (
        800  # determines at what point to create a simplified graph
    )
    n_nearest_neighbors: int = (
        500  # max number of nearest neighbors to consider when creating the cost graph
    )
    maximum_distance_meters: float = 20_000  # furthest distance between nodes to consider when creating the cost graph
    include_connected: bool = (
        False  # whether to include already connected schools in the cost graph
    )
    n_chunks: int = 500  # number of chunks to split the distance matrix into when creating the cost graph


def add_meta_node(graph, meta_node_name, node_labels, edge_weight=0):
    # adds a meta node to the graph that connects all nodes with the given labels
    # NOTE: this will update the graph in place
    graph.add_node(meta_node_name)
    for n, attributes in graph.nodes(data=True):
        if n == meta_node_name:
            continue
        if attributes["label"] in node_labels:
            graph.add_edge(meta_node_name, n, weight=edge_weight)
    return graph


class SATCostGraph(BaseModel):

    """
    A connected cost graph is a directed graph where each node
    represents a school and each edge represents the cost of
    connecting the school to connectivity infrastructure.
    """

    graph: nx.Graph  # TODO: this may need to be a DiGraph
    config: SATCostGraphConf

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    def from_existing_edges(
        data_space: ModelDataSpace,
        edges: PairwiseDistanceTable,
        config: SATCostGraphConf,
    ):
        g = nx.Graph()
        # Add fiber nodes
        for c in data_space.fiber_coordinates:
            g.add_node(
                c.coordinate_id,
                label=LABEL_LOOKUP["fiber"],
                pindex=PINDEX_LOOKUP["fiber"],
                cost=config.base_node_cost,
                ncost=config.base_n_cost,
                pkmcost=config.base_per_km_cost,
                coordinate=c.coordinate,
            )
        # Add school nodes
        schools = (
            data_space.all_schools if config.include_connected else data_space.schools
        )
        for s in schools.to_coordinates():
            g.add_node(
                s.coordinate_id,
                label=LABEL_LOOKUP["school"],
                pindex=PINDEX_LOOKUP["school"],
                cost=config.base_node_cost,
                ncost=config.base_n_cost,
                pkmcost=config.base_per_km_cost,
                coordinate=s.coordinate,
            )
        # Add edges - school to fiber and school to school
        for e in edges.distances:
            target, source = e.pair_ids
            if source not in g.nodes() or target not in g.nodes():
                LOGGER.warning(f"Error adding edge {source} to {target}")
            else:
                g.add_edge(
                    source,
                    target,
                    weight=int(e.distance),
                    source_coord=e.coordinate2.coordinate,
                    target_coord=e.coordinate1.coordinate,
                )
        return SATCostGraph(graph=g, config=config)

    @staticmethod
    def compute_from_data_space(
        data_space: ModelDataSpace, config: SATCostGraphConf, progress_bar=True
    ):
        fiber_coordinates = (
            data_space.fiber_coordinates + data_space.schools_with_fiber_coordinates
        )
        schools = (
            data_space.all_schools if config.include_connected else data_space.schools
        )
        school_coords = schools.to_coordinates()
        model = VectorizedDistanceModel(
            progress_bar=progress_bar,
            n_nearest_neighbors=config.n_nearest_neighbors,
            maximum_distance=config.maximum_distance_meters,
        )
        LOGGER.info(f"Creating fiber graph from data space")
        LOGGER.info(f"Creating fiber to school edges")
        dists_fiber = model.run((school_coords, fiber_coordinates))
        LOGGER.info(f"Creating school to school edges")
        dists_schools = model.run_chunks(
            (school_coords, school_coords),
            n_chunks=config.n_chunks,
        )
        edges = PairwiseDistanceTable(distances=dists_fiber + dists_schools)
        return SATCostGraph.from_existing_edges(data_space, edges, config)

    def to_pairwise_distance_table(self):
        dists = []
        for source, target, data in self.edges(data=True):
            dists.append(
                PairwiseDistance(
                    pair_ids=(target, source),
                    distance=data["weight"],
                    coordinate1=UniqueCoordinate(
                        coordinate_id=target, coordinate=data["target_coord"]
                    ),
                    coordinate2=UniqueCoordinate(
                        coordinate_id=source, coordinate=data["source_coord"]
                    ),
                )
            )
        return PairwiseDistanceTable(distances=dists)

    def nodes_to_csv(self, filename):
        table = []
        for nid, data in self.graph.nodes(data=True):
            table.append({"vertice": nid, "tags": data["label"]})
        pd.DataFrame(table).to_csv(filename, index=False)

    def edges_to_csv(self, filename):
        table = []
        for source, target, data in self.graph.edges(data=True):
            table.append(
                {"source": source, "target": target, "length": int(data["weight"])}
            )
        pd.DataFrame(table).to_csv(filename, index=False)

    def nodes(self, **kwargs):
        return self.graph.nodes(**kwargs)

    def edges(self, **kwargs):
        return self.graph.edges(**kwargs)

    def get_node(self, node_id):
        return self.graph.nodes[node_id]

    def compute_relational_graph(self):
        rel = CostRelationalGraph(self.graph)
        rel = rel.compute_relational_graph(
            relational_graph_edge_threshold=self.config.relational_graph_edge_threshold
        )
        return rel

    def compute_mst(self, algorithm: str = "boruvka"):
        """
        Compute the minimum spanning tree of the graph
        Adds a meta node to the graph that connects all nodes that are already connected
        """
        mst = self.graph.copy()
        mst = add_meta_node(
            mst, CONNECTED_META_NODE_LABEL, CONNECTED_NODE_LABELS, edge_weight=0
        )
        mst.add_node(CONNECTED_META_NODE_LABEL)
        mst = nx.minimum_spanning_tree(mst, weight="weight", algorithm=algorithm)
        return CostMinimumSpanningTree(mst)
