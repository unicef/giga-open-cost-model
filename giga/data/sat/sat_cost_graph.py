from pydantic import BaseModel
import pandas as pd
import networkx as nx

from giga.data.space.model_data_space import ModelDataSpace
from giga.data.sat.cost_minimum_spanning_tree import CostMinimumSpanningTree
from giga.data.sat.cost_relational_graph import CostRelationalGraph
from giga.models.nodes.graph.vectorized_distance_model import VectorizedDistanceModel
from giga.models.nodes.graph.greedy_distance_connector import GreedyDistanceConnector
from giga.schemas.geo import PairwiseDistanceTable
from giga.utils.logging import LOGGER
from giga.schemas.geo import PairwiseDistance, PairwiseDistanceTable, UniqueCoordinate
import math
from typing import List
from giga.schemas.conf.models import TechnologyConfiguration
from giga.schemas.conf.models import FiberTechnologyCostConf
from giga.models.components.electricity_cost_model import ElectricityCostModel
from giga.data.sat.cost_minimum_spanning_tree import CostMinimumSpanningDirectedTree

import string
from dataclasses import dataclass, field
from enum import Enum
from operator import itemgetter
from queue import PriorityQueue

from networkx.utils import py_random_state

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

METERS_IN_KM = 1_000.0
IMPOSSIBLE_EDGES = [
    ("cfnode", "cfnode"),
    ("cfnode", "ufnode"),
    ("ufonde", "ufnode"),
    ("cfonde", "cschool"),
    ("cschool", "cfnode"),
    ("ufnode", "cschool"),
    ("cschool", "ufnode"),
    ("cschool", "cschool"),
]

KINDS = {"max", "min"}

STYLES = {
    "branching": "branching",
    "arborescence": "arborescence",
    "spanning arborescence": "arborescence",
}

INF = float("inf")


@py_random_state(1)
def random_string(L=15, seed=None):
    return "".join([seed.choice(string.ascii_letters) for n in range(L)])


def _min_weight(weight):
    return -weight


def _max_weight(weight):
    return weight


def branching_weight(G, attr="weight", default=1):
    """
    Returns the total weight of a branching.

    You must access this function through the networkx.algorithms.tree module.

    Parameters
    ----------
    G : DiGraph
        The directed graph.
    attr : str
        The attribute to use as weights. If None, then each edge will be
        treated equally with a weight of 1.
    default : float
        When `attr` is not None, then if an edge does not have that attribute,
        `default` specifies what value it should take.

    Returns
    -------
    weight: int or float
        The total weight of the branching.

    Examples
    --------
    >>> G = nx.DiGraph()
    >>> G.add_weighted_edges_from([(0, 1, 2), (1, 2, 4), (2, 3, 3), (3, 4, 2)])
    >>> nx.tree.branching_weight(G)
    11

    """
    return sum(edge[2].get(attr, default) for edge in G.edges(data=True))


def greedy_branching(G, attr="weight", default=1, kind="max", seed=None):
    """
    Returns a branching obtained through a greedy algorithm.

    This algorithm is wrong, and cannot give a proper optimal branching.
    However, we include it for pedagogical reasons, as it can be helpful to
    see what its outputs are.

    The output is a branching, and possibly, a spanning arborescence. However,
    it is not guaranteed to be optimal in either case.

    Parameters
    ----------
    G : DiGraph
        The directed graph to scan.
    attr : str
        The attribute to use as weights. If None, then each edge will be
        treated equally with a weight of 1.
    default : float
        When `attr` is not None, then if an edge does not have that attribute,
        `default` specifies what value it should take.
    kind : str
        The type of optimum to search for: 'min' or 'max' greedy branching.
    seed : integer, random_state, or None (default)
        Indicator of random number generation state.
        See :ref:`Randomness<randomness>`.

    Returns
    -------
    B : directed graph
        The greedily obtained branching.

    """
    if kind not in KINDS:
        raise nx.NetworkXException("Unknown value for `kind`.")

    if kind == "min":
        reverse = False
    else:
        reverse = True

    if attr is None:
        # Generate a random string the graph probably won't have.
        attr = random_string(seed=seed)

    edges = [(u, v, data.get(attr, default)) for (u, v, data) in G.edges(data=True)]

    # We sort by weight, but also by nodes to normalize behavior across runs.
    try:
        edges.sort(key=itemgetter(2, 0, 1), reverse=reverse)
    except TypeError:
        # This will fail in Python 3.x if the nodes are of varying types.
        # In that case, we use the arbitrary order.
        edges.sort(key=itemgetter(2), reverse=reverse)

    # The branching begins with a forest of no edges.
    B = nx.DiGraph()
    B.add_nodes_from(G)

    # Now we add edges greedily so long we maintain the branching.
    uf = nx.utils.UnionFind()
    for i, (u, v, w) in enumerate(edges):
        if uf[u] == uf[v]:
            # Adding this edge would form a directed cycle.
            continue
        elif B.in_degree(v) == 1:
            # The edge would increase the degree to be greater than one.
            continue
        else:
            # If attr was None, then don't insert weights...
            data = {}
            if attr is not None:
                data[attr] = w
            B.add_edge(u, v, **data)
            uf.union(u, v)

    return B


class MultiDiGraph_EdgeKey(nx.MultiDiGraph):
    """
    MultiDiGraph which assigns unique keys to every edge.

    Adds a dictionary edge_index which maps edge keys to (u, v, data) tuples.

    This is not a complete implementation. For Edmonds algorithm, we only use
    add_node and add_edge, so that is all that is implemented here. During
    additions, any specified keys are ignored---this means that you also
    cannot update edge attributes through add_node and add_edge.

    Why do we need this? Edmonds algorithm requires that we track edges, even
    as we change the head and tail of an edge, and even changing the weight
    of edges. We must reliably track edges across graph mutations.

    """

    def __init__(self, incoming_graph_data=None, **attr):
        cls = super()
        cls.__init__(incoming_graph_data=incoming_graph_data, **attr)

        self._cls = cls
        self.edge_index = {}

    def remove_node(self, n):
        keys = set()
        for keydict in self.pred[n].values():
            keys.update(keydict)
        for keydict in self.succ[n].values():
            keys.update(keydict)

        for key in keys:
            del self.edge_index[key]

        self._cls.remove_node(n)

    def remove_nodes_from(self, nbunch):
        for n in nbunch:
            self.remove_node(n)

    def add_edge(self, u_for_edge, v_for_edge, key_for_edge, **attr):
        """
        Key is now required.

        """
        u, v, key = u_for_edge, v_for_edge, key_for_edge
        if key in self.edge_index:
            uu, vv, _ = self.edge_index[key]
            if (u != uu) or (v != vv):
                raise Exception(f"Key {key!r} is already in use.")

        self._cls.add_edge(u, v, key, **attr)
        self.edge_index[key] = (u, v, self.succ[u][v][key])

    def add_edges_from(self, ebunch_to_add, **attr):
        for u, v, k, d in ebunch_to_add:
            self.add_edge(u, v, k, **d)

    def remove_edge_with_key(self, key):
        try:
            u, v, _ = self.edge_index[key]
        except KeyError as err:
            raise KeyError(f"Invalid edge key {key!r}") from err
        else:
            del self.edge_index[key]
            self._cls.remove_edge(u, v, key)

    def remove_edges_from(self, ebunch):
        raise NotImplementedError


def get_path(G, u, v):
    """
    Returns the edge keys of the unique path between u and v.

    This is not a generic function. G must be a branching and an instance of
    MultiDiGraph_EdgeKey.

    """
    nodes = nx.shortest_path(G, u, v)

    # We are guaranteed that there is only one edge connected every node
    # in the shortest path.

    def first_key(i, vv):
        # Needed for 2.x/3.x compatibilitity
        keys = G[nodes[i]][vv].keys()
        # Normalize behavior
        keys = list(keys)
        return keys[0]

    edges = [first_key(i, vv) for i, vv in enumerate(nodes[1:])]
    return nodes, edges


def is_forest(G):
    """
    Returns True if `G` is a forest.

    A forest is a graph with no undirected cycles.

    For directed graphs, `G` is a forest if the underlying graph is a forest.
    The underlying graph is obtained by treating each directed edge as a single
    undirected edge in a multigraph.

    Parameters
    ----------
    G : graph
        The graph to test.

    Returns
    -------
    b : bool
        A boolean that is True if `G` is a forest.

    Raises
    ------
    NetworkXPointlessConcept
        If `G` is empty.

    Examples
    --------
    >>> G = nx.Graph()
    >>> G.add_edges_from([(1, 2), (1, 3), (2, 4), (2, 5)])
    >>> nx.is_forest(G)
    True
    >>> G.add_edge(4, 1)
    >>> nx.is_forest(G)
    False

    Notes
    -----
    In another convention, a directed forest is known as a *polyforest* and
    then *forest* corresponds to a *branching*.

    See Also
    --------
    is_branching

    """
    if len(G) == 0:
        raise nx.exception.NetworkXPointlessConcept("G has no nodes.")

    if G.is_directed():
        components = (G.subgraph(c) for c in nx.weakly_connected_components(G))
    else:
        components = (G.subgraph(c) for c in nx.connected_components(G))

    return all(len(c) - 1 == c.number_of_edges() for c in components)


def is_branching(G):
    """
    Returns True if `G` is a branching.

    A branching is a directed forest with maximum in-degree equal to 1.

    Parameters
    ----------
    G : directed graph
        The directed graph to test.

    Returns
    -------
    b : bool
        A boolean that is True if `G` is a branching.

    Examples
    --------
    >>> G = nx.DiGraph([(0, 1), (1, 2), (2, 3), (3, 4)])
    >>> nx.is_branching(G)
    True
    >>> G.remove_edge(2, 3)
    >>> G.add_edge(3, 1)  # maximum in-degree is 2
    >>> nx.is_branching(G)
    False

    Notes
    -----
    In another convention, a branching is also known as a *forest*.

    See Also
    --------
    is_forest

    """
    return is_forest(G) and max(d for n, d in G.in_degree()) <= 1


class Edmonds:
    """
    Edmonds algorithm [1]_ for finding optimal branchings and spanning
    arborescences.

    This algorithm can find both minimum and maximum spanning arborescences and
    branchings.

    Notes
    -----
    While this algorithm can find a minimum branching, since it isn't required
    to be spanning, the minimum branching is always from the set of negative
    weight edges which is most likely the empty set for most graphs.

    References
    ----------
    .. [1] J. Edmonds, Optimum Branchings, Journal of Research of the National
           Bureau of Standards, 1967, Vol. 71B, p.233-240,
           https://archive.org/details/jresv71Bn4p233

    """

    def __init__(self, G, seed=None):
        self.G_original = G

        # Need to fix this. We need the whole tree.
        self.store = True

        # The final answer.
        self.edges = []

        # Since we will be creating graphs with new nodes, we need to make
        # sure that our node names do not conflict with the real node names.
        self.template = random_string(seed=seed) + "_{0}"

    def _init(self, attr, default, kind, style, preserve_attrs, seed, partition):
        if kind not in KINDS:
            raise nx.NetworkXException("Unknown value for `kind`.")

        # Store inputs.
        self.attr = attr
        self.default = default
        self.kind = kind
        self.style = style

        # Determine how we are going to transform the weights.
        if kind == "min":
            self.trans = trans = _min_weight
        else:
            self.trans = trans = _max_weight

        if attr is None:
            # Generate a random attr the graph probably won't have.
            attr = random_string(seed=seed)

        # This is the actual attribute used by the algorithm.
        self._attr = attr

        # This attribute is used to store whether a particular edge is still
        # a candidate. We generate a random attr to remove clashes with
        # preserved edges
        self.candidate_attr = "candidate_" + random_string(seed=seed)

        # The object we manipulate at each step is a multidigraph.
        self.G = G = MultiDiGraph_EdgeKey()
        for key, (u, v, data) in enumerate(self.G_original.edges(data=True)):
            d = {attr: trans(data.get(attr, default))}

            if data.get(partition) is not None:
                d[partition] = data.get(partition)

            if preserve_attrs:
                for d_k, d_v in data.items():
                    if d_k != attr:
                        d[d_k] = d_v

            G.add_edge(u, v, key, **d)

        self.level = 0

        # These are the "buckets" from the paper.
        #
        # As in the paper, G^i are modified versions of the original graph.
        # D^i and E^i are nodes and edges of the maximal edges that are
        # consistent with G^i. These are dashed edges in figures A-F of the
        # paper. In this implementation, we store D^i and E^i together as a
        # graph B^i. So we will have strictly more B^i than the paper does.
        self.B = MultiDiGraph_EdgeKey()
        self.B.edge_index = {}
        self.graphs = []  # G^i
        self.branchings = []  # B^i
        self.uf = nx.utils.UnionFind()

        # A list of lists of edge indexes. Each list is a circuit for graph G^i.
        # Note the edge list will not, in general, be a circuit in graph G^0.
        self.circuits = []
        # Stores the index of the minimum edge in the circuit found in G^i
        # and B^i. The ordering of the edges seems to preserve the weight
        # ordering from G^0. So even if the circuit does not form a circuit
        # in G^0, it is still true that the minimum edge of the circuit in
        # G^i is still the minimum edge in circuit G^0 (despite their weights
        # being different).
        self.minedge_circuit = []

    def find_optimum(
        self,
        attr="weight",
        default=1,
        kind="max",
        style="branching",
        preserve_attrs=False,
        partition=None,
        seed=None,
    ):
        """
        Returns a branching from G.

        Parameters
        ----------
        attr : str
            The edge attribute used to in determining optimality.
        default : float
            The value of the edge attribute used if an edge does not have
            the attribute `attr`.
        kind : {'min', 'max'}
            The type of optimum to search for, either 'min' or 'max'.
        style : {'branching', 'arborescence'}
            If 'branching', then an optimal branching is found. If `style` is
            'arborescence', then a branching is found, such that if the
            branching is also an arborescence, then the branching is an
            optimal spanning arborescences. A given graph G need not have
            an optimal spanning arborescence.
        preserve_attrs : bool
            If True, preserve the other edge attributes of the original
            graph (that are not the one passed to `attr`)
        partition : str
            The edge attribute holding edge partition data. Used in the
            spanning arborescence iterator.
        seed : integer, random_state, or None (default)
            Indicator of random number generation state.
            See :ref:`Randomness<randomness>`.

        Returns
        -------
        H : (multi)digraph
            The branching.

        """
        self._init(attr, default, kind, style, preserve_attrs, seed, partition)
        uf = self.uf

        # This enormous while loop could use some refactoring...

        G, B = self.G, self.B
        D = set()
        nodes = iter(list(G.nodes()))
        attr = self._attr
        G_pred = G.pred

        def desired_edge(v):
            """
            Find the edge directed toward v with maximal weight.

            If an edge partition exists in this graph, return the included edge
            if it exists and no not return any excluded edges. There can only
            be one included edge for each vertex otherwise the edge partition is
            empty.
            """
            edge = None
            weight = -INF
            for u, _, key, data in G.in_edges(v, data=True, keys=True):
                # Skip excluded edges
                if data.get(partition) == nx.EdgePartition.EXCLUDED:
                    continue
                new_weight = data[attr]
                # Return the included edge
                if data.get(partition) == nx.EdgePartition.INCLUDED:
                    weight = new_weight
                    edge = (u, v, key, new_weight, data)
                    return edge, weight
                # Find the best open edge
                if new_weight > weight:
                    weight = new_weight
                    edge = (u, v, key, new_weight, data)

            return edge, weight

        while True:
            # (I1): Choose a node v in G^i not in D^i.
            try:
                v = next(nodes)
            except StopIteration:
                # If there are no more new nodes to consider, then we *should*
                # meet the break condition (b) from the paper:
                #   (b) every node of G^i is in D^i and E^i is a branching
                # Construction guarantees that it's a branching.
                assert len(G) == len(B)
                if len(B):
                    assert is_branching(B)

                if self.store:
                    self.graphs.append(G.copy())
                    self.branchings.append(B.copy())

                    # Add these to keep the lengths equal. Element i is the
                    # circuit at level i that was merged to form branching i+1.
                    # There is no circuit for the last level.
                    self.circuits.append([])
                    self.minedge_circuit.append(None)
                break
            else:
                if v in D:
                    # print("v in D", v)
                    continue

            # Put v into bucket D^i.
            # print(f"Adding node {v}")
            D.add(v)
            B.add_node(v)

            edge, weight = desired_edge(v)
            # print(f"Max edge is {edge!r}")
            if edge is None:
                # If there is no edge, continue with a new node at (I1).
                continue
            else:
                # Determine if adding the edge to E^i would mean its no longer
                # a branching. Presently, v has indegree 0 in B---it is a root.
                u = edge[0]

                if uf[u] == uf[v]:
                    # Then adding the edge will create a circuit. Then B
                    # contains a unique path P from v to u. So condition (a)
                    # from the paper does hold. We need to store the circuit
                    # for future reference.
                    Q_nodes, Q_edges = get_path(B, v, u)
                    Q_edges.append(edge[2])  # Edge key
                else:
                    # Then B with the edge is still a branching and condition
                    # (a) from the paper does not hold.
                    Q_nodes, Q_edges = None, None

                # Conditions for adding the edge.
                # If weight < 0, then it cannot help in finding a maximum branching.
                if self.style == "branching" and weight <= 0:
                    acceptable = False
                else:
                    acceptable = True

                # print(f"Edge is acceptable: {acceptable}")
                if acceptable:
                    dd = {attr: weight}
                    if edge[4].get(partition) is not None:
                        dd[partition] = edge[4].get(partition)
                    B.add_edge(u, v, edge[2], **dd)
                    G[u][v][edge[2]][self.candidate_attr] = True
                    uf.union(u, v)
                    if Q_edges is not None:
                        # print("Edge introduced a simple cycle:")
                        # print(Q_nodes, Q_edges)

                        # Move to method
                        # Previous meaning of u and v is no longer important.

                        # Apply (I2).
                        # Get the edge in the cycle with the minimum weight.
                        # Also, save the incoming weights for each node.
                        minweight = INF
                        minedge = None
                        Q_incoming_weight = {}
                        for edge_key in Q_edges:
                            u, v, data = B.edge_index[edge_key]
                            # We cannot remove an included edges, even if it is
                            # the minimum edge in the circuit
                            w = data[attr]
                            Q_incoming_weight[v] = w
                            if data.get(partition) == nx.EdgePartition.INCLUDED:
                                continue
                            if w < minweight:
                                minweight = w
                                minedge = edge_key

                        self.circuits.append(Q_edges)
                        self.minedge_circuit.append(minedge)

                        if self.store:
                            self.graphs.append(G.copy())
                        # Always need the branching with circuits.
                        self.branchings.append(B.copy())

                        # Now we mutate it.
                        new_node = self.template.format(self.level)

                        # print(minweight, minedge, Q_incoming_weight)

                        G.add_node(new_node)
                        new_edges = []
                        for u, v, key, data in G.edges(data=True, keys=True):
                            if u in Q_incoming_weight:
                                if v in Q_incoming_weight:
                                    # Circuit edge, do nothing for now.
                                    # Eventually delete it.
                                    continue
                                else:
                                    # Outgoing edge. Make it from new node
                                    dd = data.copy()
                                    new_edges.append((new_node, v, key, dd))
                            else:
                                if v in Q_incoming_weight:
                                    # Incoming edge. Change its weight
                                    w = data[attr]
                                    w += minweight - Q_incoming_weight[v]
                                    dd = data.copy()
                                    dd[attr] = w
                                    new_edges.append((u, new_node, key, dd))
                                else:
                                    # Outside edge. No modification necessary.
                                    continue

                        G.remove_nodes_from(Q_nodes)
                        B.remove_nodes_from(Q_nodes)
                        D.difference_update(set(Q_nodes))

                        for u, v, key, data in new_edges:
                            G.add_edge(u, v, key, **data)
                            if self.candidate_attr in data:
                                del data[self.candidate_attr]
                                B.add_edge(u, v, key, **data)
                                uf.union(u, v)

                        nodes = iter(list(G.nodes()))
                        self.level += 1

        # (I3) Branch construction.
        # print(self.level)
        H = self.G_original.__class__()

        def is_root(G, u, edgekeys):
            """
            Returns True if `u` is a root node in G.

            Node `u` will be a root node if its in-degree, restricted to the
            specified edges, is equal to 0.

            """
            if u not in G:
                # print(G.nodes(), u)
                raise Exception(f"{u!r} not in G")
            for v in G.pred[u]:
                for edgekey in G.pred[u][v]:
                    if edgekey in edgekeys:
                        return False, edgekey
            else:
                return True, None

        # Start with the branching edges in the last level.
        edges = set(self.branchings[self.level].edge_index)
        while self.level > 0:
            self.level -= 1

            # The current level is i, and we start counting from 0.

            # We need the node at level i+1 that results from merging a circuit
            # at level i. randomname_0 is the first merged node and this
            # happens at level 1. That is, randomname_0 is a node at level 1
            # that results from merging a circuit at level 0.
            merged_node = self.template.format(self.level)

            # The circuit at level i that was merged as a node the graph
            # at level i+1.
            circuit = self.circuits[self.level]
            # print
            # print(merged_node, self.level, circuit)
            # print("before", edges)
            # Note, we ask if it is a root in the full graph, not the branching.
            # The branching alone doesn't have all the edges.

            isroot, edgekey = is_root(self.graphs[self.level + 1], merged_node, edges)
            edges.update(circuit)
            if isroot:
                minedge = self.minedge_circuit[self.level]
                if minedge is None:
                    raise Exception

                # Remove the edge in the cycle with minimum weight.
                edges.remove(minedge)
            else:
                # We have identified an edge at next higher level that
                # transitions into the merged node at the level. That edge
                # transitions to some corresponding node at the current level.
                # We want to remove an edge from the cycle that transitions
                # into the corresponding node.
                # print("edgekey is: ", edgekey)
                # print("circuit is: ", circuit)
                # The branching at level i
                G = self.graphs[self.level]
                # print(G.edge_index)
                target = G.edge_index[edgekey][1]
                for edgekey in circuit:
                    u, v, data = G.edge_index[edgekey]
                    if v == target:
                        break
                else:
                    raise Exception("Couldn't find edge incoming to merged node.")
                # print(f"not a root. removing {edgekey}")

                edges.remove(edgekey)

        self.edges = edges

        H.add_nodes_from(self.G_original.nodes(data=True))
        for edgekey in edges:
            u, v, d = self.graphs[0].edge_index[edgekey]
            dd = {self.attr: self.trans(d[self.attr])}

            # Optionally, preserve the other edge attributes of the original
            # graph
            if preserve_attrs:
                for key, value in d.items():
                    if key not in [self.attr, self.candidate_attr]:
                        dd[key] = value

            # TODO: make this preserve the key.
            H.add_edge(u, v, **dd)

        return H


class SATCostGraphConf(BaseModel):
    """Configuration for SAT cost graph"""

    relational_graph_edge_threshold: int = (
        800  # determines at what point to create a simplified graph
    )
    n_nearest_neighbors: int = (
        500  # max number of nearest neighbors to consider when creating the cost graph
    )
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
    digraph: nx.DiGraph = None

    class Config:
        arbitrary_types_allowed = True

    def extend_for_all_old(
        self,
        data_space: ModelDataSpace,
        edges: PairwiseDistanceTable,
        config: SATCostGraphConf,
        technologies: List[TechnologyConfiguration],
        years_opex: int,
        distances_cell: List[PairwiseDistance],
        distances_p2p: List[PairwiseDistance],
    ):
        # First LEO
        leo_excluded = []
        self.graph.add_node("metaLEO", label="metaTech")
        self.graph.add_edge("metanode", "metaLEO", weight=0)
        electricity_model = ElectricityCostModel(technologies[1])
        for s in data_space.school_entities:
            sid = s.giga_id
            sc = s.to_coordinates()
            if s.bandwidth_demand > technologies[1].constraints.maximum_bandwithd:
                leo_excluded.append(sid)
            else:
                if sid not in self.graph.nodes():
                    electricity = electricity_model.compute_cost(s)
                    self.graph.add_node(
                        sc.coordinate_id,
                        label=LABEL_LOOKUP["uschool"],
                        pindex=PINDEX_LOOKUP["uschool"],
                        cost=0,
                        ncost=0,
                        pkmcost=0,
                        coordinate=sc.coordinate,
                    )
                weight = (
                    electricity.electricity_opex * years_opex
                    + electricity.electricity_capex
                    + s.bandwidth_demand
                    * technologies[1].opex.annual_bandwidth_cost_per_mbps
                    * years_opex
                    + technologies[1].capex.fixed_costs
                    + technologies[1].opex.fixed_costs
                )
                self.graph.add_edge(
                    "metaLEO",
                    sid,
                    weight=int(weight),
                    weight_float=weight,
                    source_coord=None,  # We might need to add something...
                    target_coord=s.to_coordinates().coordinate,
                )

        # Second cell
        cell_excluded_bw = []
        cell_excluded_range = []
        self.graph.add_node("metaCELL", label="metaTech")
        self.graph.add_edge("metanode", "metaCELL", weight=0)
        electricity_model = ElectricityCostModel(technologies[2])
        # We will need to change the connected_set if we have cell tower capacities or individual opex at some point
        connected_set = set([x.coordinate1.coordinate_id for x in distances_cell])
        #####

        for s in data_space.school_entities:
            sid = s.giga_id
            sc = s.to_coordinates()
            if s.bandwidth_demand > technologies[2].constraints.maximum_bandwithd:
                cell_excluded_bw.append(sid)
            elif (
                sid in connected_set
                or s.cell_coverage_type
                in technologies[2].constraints.valid_cellular_technologies
            ):
                if sid not in self.graph.nodes():
                    electricity = electricity_model.compute_cost(s)
                    self.graph.add_node(
                        sc.coordinate_id,
                        label=LABEL_LOOKUP["uschool"],
                        pindex=PINDEX_LOOKUP["uschool"],
                        cost=0,
                        ncost=0,
                        pkmcost=0,
                        coordinate=sc.coordinate,
                    )
                weight = (
                    electricity.electricity_opex * years_opex
                    + electricity.electricity_capex
                    + s.bandwidth_demand
                    * technologies[2].opex.annual_bandwidth_cost_per_mbps
                    * years_opex
                    + technologies[2].capex.fixed_costs
                    + technologies[2].opex.fixed_costs
                )
                self.graph.add_edge(
                    "metaCELL",
                    sid,
                    weight=int(weight),
                    weight_float=weight,
                    source_coord=None,  # We might need to add something...
                    target_coord=s.to_coordinates().coordinate,
                )
            else:
                cell_excluded_range.append(sid)

        # Third P2P
        p2p_excluded_bw = []
        p2p_excluded_range = []
        self.graph.add_node("metaP2P", label="metaTech")
        self.graph.add_edge("metanode", "metaP2P", weight=0)
        electricity_model = ElectricityCostModel(technologies[3])
        # We will need to change the connected_set if we have cell tower capacities or individual opex at some point
        connected_set = set([x.coordinate1.coordinate_id for x in distances_p2p])
        #####

        for s in data_space.school_entities:
            sid = s.giga_id
            sc = s.to_coordinates()
            if s.bandwidth_demand > technologies[3].constraints.maximum_bandwithd:
                p2p_excluded_bw.append(sid)
            elif (
                sid in connected_set
                or s.cell_coverage_type
                in technologies[2].constraints.valid_cellular_technologies
            ):  # Adding this here but will need to change to p2p_coverage or similar
                if sid not in self.graph.nodes():
                    electricity = electricity_model.compute_cost(s)
                    self.graph.add_node(
                        sc.coordinate_id,
                        label=LABEL_LOOKUP["uschool"],
                        pindex=PINDEX_LOOKUP["uschool"],
                        cost=0,
                        ncost=0,
                        pkmcost=0,
                        coordinate=sc.coordinate,
                    )
                weight = (
                    electricity.electricity_opex * years_opex
                    + electricity.electricity_capex
                    + s.bandwidth_demand
                    * technologies[3].opex.annual_bandwidth_cost_per_mbps
                    * years_opex
                    + technologies[3].capex.fixed_costs
                    + technologies[3].opex.fixed_costs
                    + technologies[3].capex.tower_fixed_costs
                )
                self.graph.add_edge(
                    "metaCELL",
                    sid,
                    weight=int(weight),
                    weight_float=weight,
                    source_coord=None,  # We might need to add something...
                    target_coord=s.to_coordinates().coordinate,
                )
            else:
                p2p_excluded_range.append(sid)

        # I should push the cost to the edges in the fiber case as well so MST works well

        return [
            leo_excluded,
            cell_excluded_range,
            cell_excluded_bw,
            p2p_excluded_range,
            p2p_excluded_bw,
        ]

    def extend_for_all(
        self,
        data_space: ModelDataSpace,
        edges: PairwiseDistanceTable,
        config: SATCostGraphConf,
        technologies: List[TechnologyConfiguration],
        years_opex: int,
        distances_cell: List[PairwiseDistance],
        distances_p2p: List[PairwiseDistance],
    ):
        # Create digraph
        digraph = nx.DiGraph()

        # Prepare graph pushing fiber
        aux_dict = {}
        for n, attributes in self.graph.nodes(data=True):
            if n != "metanode" and attributes["label"] == "uschool":
                aux_dict[n] = attributes

        for n in aux_dict:
            attributes = aux_dict[n]
            new_id = n + "_uschool"
            digraph.add_node(
                new_id,
                label=LABEL_LOOKUP["uschool"],
                pindex=attributes["pindex"],
                cost=0,
                ncost=0,
                pkmcost=0,
                coordinate=attributes["coordinate"],
            )
            digraph.add_node(
                n,
                label="uschool_fiber",
                pindex=0,
                cost=0,
                ncost=0,
                pkmcost=attributes["pkmcost"],
                coordinate=attributes["coordinate"],
            )
            self.graph.nodes[n]["label"] == "uschool_fiber"

            digraph.add_edge(
                n,
                new_id,
                weight=attributes["cost"] + attributes["ncost"],
                weight_float=attributes["cost"] + attributes["ncost"],
                source_coord=attributes["coordinate"],
                target_coord=attributes["coordinate"],
            )

            new_id2 = n + "_nofiber"
            digraph.add_node(
                new_id2,
                label="uschool_nofiber",
                pindex=0,
                cost=0,
                ncost=0,
                pkmcost=0,
                coordinate=attributes["coordinate"],
            )

            digraph.add_edge(
                new_id2,
                new_id,
                weight=0,
                weight_float=0,
                source_coord=attributes["coordinate"],
                target_coord=attributes["coordinate"],
            )

        for n1, n2, attributes in self.graph.edges(data=True):
            if n1 == "metanode":
                digraph.add_edge(n1, n2, **attributes)
            elif n1 == "cfnode" or n1 == "ufnode" or n1 == "cschool":
                if n2 == "metanode":
                    digraph.add_edge(n2, n1, **attributes)
                else:
                    digraph.add_edge(n1, n2, **attributes)
            elif n1 == "uschool_fiber" or n1 == "splitter":
                if (
                    n2 == "metanode"
                    or n2 == "cfnode"
                    or n2 == "ufnode"
                    or n2 == "cschool"
                ):
                    digraph.add_edge(n2, n1, **attributes)
                elif n2 == "uschool_fiber" or n2 == "splitter":
                    digraph.add_edge(n1, n2, **attributes)
                    digraph.add_edge(n2, n1, **attributes)

        # First LEO
        leo_excluded = []
        digraph.add_node("metaLEO", label="metaTech")
        digraph.add_edge("metanode", "metaLEO", weight=0)
        electricity_model = ElectricityCostModel(technologies[1])
        for s in data_space.school_entities:
            sid = s.giga_id + "_uschool"
            sc = s.to_coordinates()
            if s.bandwidth_demand > technologies[1].constraints.maximum_bandwithd:
                leo_excluded.append(s.giga_id)
            else:
                electricity = electricity_model.compute_cost(s)
                if sid not in digraph.nodes():
                    digraph.add_node(
                        sc.coordinate_id + "_uschool",
                        label=LABEL_LOOKUP["uschool"],
                        pindex=PINDEX_LOOKUP["uschool"],
                        cost=0,
                        ncost=0,
                        pkmcost=0,
                        coordinate=sc.coordinate,
                    )

                digraph.add_node(
                    sc.coordinate_id + "_nofiber",
                    label="uschool_nofiber",
                    pindex=0,
                    cost=0,
                    ncost=0,
                    pkmcost=0,
                    coordinate=sc.coordinate,
                )
                digraph.add_edge(
                    sc.coordinate_id + "_nofiber",
                    sc.coordinate_id + "_uschool",
                    weight=0,
                    weight_float=0,
                    source_coord=sc.coordinate,
                    target_coord=sc.coordinate,
                )
                weight = (
                    electricity.electricity_opex * years_opex
                    + electricity.electricity_capex
                    + s.bandwidth_demand
                    * technologies[1].opex.annual_bandwidth_cost_per_mbps
                    * years_opex
                    + technologies[1].capex.fixed_costs
                    + technologies[1].opex.fixed_costs
                )
                digraph.add_edge(
                    "metaLEO",
                    sc.coordinate_id + "_nofiber",
                    weight=int(weight),
                    weight_float=weight,
                    source_coord=None,  # We might need to add something...
                    target_coord=s.to_coordinates().coordinate,
                )

        # Second cell
        cell_excluded_bw = []
        cell_excluded_range = []
        digraph.add_node("metaCELL", label="metaTech")
        digraph.add_edge("metanode", "metaCELL", weight=0)
        electricity_model = ElectricityCostModel(technologies[2])
        # We will need to change the connected_set if we have cell tower capacities or individual opex at some point
        connected_set = set([x.coordinate1.coordinate_id for x in distances_cell])
        #####

        for s in data_space.school_entities:
            sid = s.giga_id + "_uschool"
            sc = s.to_coordinates()
            if s.bandwidth_demand > technologies[2].constraints.maximum_bandwithd:
                cell_excluded_bw.append(s.giga_id)
            elif (
                sid in connected_set
                or s.cell_coverage_type
                in technologies[2].constraints.valid_cellular_technologies
            ):
                electricity = electricity_model.compute_cost(s)
                if sid not in digraph.nodes():

                    digraph.add_node(
                        sc.coordinate_id + "_uschool",
                        label=LABEL_LOOKUP["uschool"],
                        pindex=PINDEX_LOOKUP["uschool"],
                        cost=0,
                        ncost=0,
                        pkmcost=0,
                        coordinate=sc.coordinate,
                    )

                digraph.add_node(
                    sc.coordinate_id + "_nofiber",
                    label="uschool_nofiber",
                    pindex=0,
                    cost=0,
                    ncost=0,
                    pkmcost=0,
                    coordinate=sc.coordinate,
                )
                digraph.add_edge(
                    sc.coordinate_id + "_nofiber",
                    sc.coordinate_id + "_uschool",
                    weight=0,
                    weight_float=0,
                    source_coord=sc.coordinate,
                    target_coord=sc.coordinate,
                )
                weight = (
                    electricity.electricity_opex * years_opex
                    + electricity.electricity_capex
                    + s.bandwidth_demand
                    * technologies[2].opex.annual_bandwidth_cost_per_mbps
                    * years_opex
                    + technologies[2].capex.fixed_costs
                    + technologies[2].opex.fixed_costs
                )
                digraph.add_edge(
                    "metaCELL",
                    sc.coordinate_id + "_nofiber",
                    weight=int(weight),
                    weight_float=weight,
                    source_coord=None,  # We might need to add something...
                    target_coord=s.to_coordinates().coordinate,
                )
            else:
                cell_excluded_range.append(s.giga_id)

        # Third P2P
        p2p_excluded_bw = []
        p2p_excluded_range = []
        digraph.add_node("metaP2P", label="metaTech")
        digraph.add_edge("metanode", "metaP2P", weight=0)
        electricity_model = ElectricityCostModel(technologies[3])
        # We will need to change the connected_set if we have cell tower capacities or individual opex at some point
        connected_set = set([x.coordinate1.coordinate_id for x in distances_p2p])
        #####

        for s in data_space.school_entities:
            sid = s.giga_id + "_uschool"
            sc = s.to_coordinates()
            if s.bandwidth_demand > technologies[3].constraints.maximum_bandwithd:
                p2p_excluded_bw.append(s.giga_id)
            elif (
                sid in connected_set
                or s.cell_coverage_type
                in technologies[2].constraints.valid_cellular_technologies
            ):  # Adding this here but will need to change to p2p_coverage or similar
                electricity = electricity_model.compute_cost(s)
                if sid not in digraph.nodes():

                    digraph.add_node(
                        sid,
                        label=LABEL_LOOKUP["uschool"],
                        pindex=PINDEX_LOOKUP["uschool"],
                        cost=0,
                        ncost=0,
                        pkmcost=0,
                        coordinate=sc.coordinate,
                    )

                digraph.add_node(
                    sc.coordinate_id + "_nofiber",
                    label="uschool_nofiber",
                    pindex=0,
                    cost=0,
                    ncost=0,
                    pkmcost=0,
                    coordinate=sc.coordinate,
                )
                digraph.add_edge(
                    sc.coordinate_id + "_nofiber",
                    sc.coordinate_id + "_uschool",
                    weight=0,
                    weight_float=0,
                    source_coord=sc.coordinate,
                    target_coord=sc.coordinate,
                )

                weight = (
                    electricity.electricity_opex * years_opex
                    + electricity.electricity_capex
                    + s.bandwidth_demand
                    * technologies[3].opex.annual_bandwidth_cost_per_mbps
                    * years_opex
                    + technologies[3].capex.fixed_costs
                    + technologies[3].opex.fixed_costs
                    + technologies[3].capex.tower_fixed_costs
                )
                digraph.add_edge(
                    "metaCELL",
                    sc.coordinate_id + "_nofiber",
                    weight=int(weight),
                    weight_float=weight,
                    source_coord=None,  # We might need to add something...
                    target_coord=s.to_coordinates().coordinate,
                )
            else:
                p2p_excluded_range.append(s.giga_id)

        self.digraph = digraph

        return [
            leo_excluded,
            cell_excluded_range,
            cell_excluded_bw,
            p2p_excluded_range,
            p2p_excluded_bw,
        ]

    ###################

    @staticmethod
    def from_existing_edges_fiber(
        data_space: ModelDataSpace,
        edges: PairwiseDistanceTable,
        config: SATCostGraphConf,
        technology: FiberTechnologyCostConf,
        years_opex: int,
    ):
        g = nx.Graph()

        connected_ids = set()

        # Add fiber nodes
        for c in data_space.fiber_coordinates:
            g.add_node(
                c.coordinate_id,
                label=LABEL_LOOKUP["fiber"],
                pindex=PINDEX_LOOKUP["fiber"],
                cost=0,  # config.base_node_cost,
                ncost=0,  # config.base_n_cost,
                pkmcost=0,  # config.base_per_km_cost,
                coordinate=c.coordinate,
            )
            connected_ids.add(c.coordinate_id)
        # Add school nodes
        schools = (
            data_space.all_schools if config.include_connected else data_space.schools
        )
        bw_excluded = []
        electricity_model = ElectricityCostModel(technology)
        for s in schools.schools:  # .to_coordinates():
            sc = s.to_coordinates()
            if s.connected == False:
                if s.bandwidth_demand <= technology.constraints.maximum_bandwithd:
                    electricity = electricity_model.compute_cost(s)
                    g.add_node(
                        sc.coordinate_id,
                        label=LABEL_LOOKUP["uschool"],
                        pindex=PINDEX_LOOKUP["uschool"],
                        cost=int(
                            s.bandwidth_demand
                            * technology.opex.annual_bandwidth_cost_per_mbps
                        )
                        * years_opex
                        + int(technology.capex.fixed_costs),  # config.base_node_cost,
                        ncost=int(electricity.electricity_opex) * years_opex
                        + int(electricity.electricity_capex),  # config.base_n_cost,
                        pkmcost=math.ceil(
                            (technology.opex.cost_per_km / METERS_IN_KM) * years_opex
                        ),  # config.base_per_km_cost,
                        coordinate=sc.coordinate,
                    )
                else:
                    bw_excluded.append(sc.coordinate_id)
            elif s.has_fiber:
                g.add_node(
                    sc.coordinate_id,
                    label=LABEL_LOOKUP["cschool"],
                    pindex=PINDEX_LOOKUP["cschool"],
                    cost=0,  # s.bandwidth_demand * technology.opex.annual_bandwidth_cost_per_mbps + technology.capex.fixed_costs,#config.base_node_cost,
                    ncost=0,  # config.base_n_cost,
                    pkmcost=0,  # technology.opex.cost_per_km,#config.base_per_km_cost,
                    coordinate=sc.coordinate,
                )
                connected_ids.add(sc.coordinate_id)
        ###################
        # Add edges - school to fiber and school to school
        for e in edges.distances:
            target, source = e.pair_ids
            if source not in g.nodes() or target not in g.nodes():
                LOGGER.warning(f"Error adding edge {source} to {target}")
            elif target != source:
                source_label = g.nodes[source]["label"]
                target_label = g.nodes[target]["label"]
                if (source_label, target_label) not in IMPOSSIBLE_EDGES:
                    g.add_edge(
                        source,
                        target,
                        weight=int(e.distance),
                        weight_float=e.distance,
                        source_coord=e.coordinate2.coordinate,
                        target_coord=e.coordinate1.coordinate,
                    )

        # We need a connected graph - remove unconnected
        # Find all connected components
        components = list(nx.connected_components(g))

        # Identify the components that don't contain any node from the list of IDs
        unrelated_components = [
            component
            for component in components
            if not any(node in connected_ids for node in component)
        ]

        # Remove the unrelated components from the graph
        for component in unrelated_components:
            for node in component:
                g.remove_node(node)

        # ADD METANODE
        g = add_meta_node(
            g, CONNECTED_META_NODE_LABEL, CONNECTED_NODE_LABELS, edge_weight=0
        )
        ###################

        return SATCostGraph(graph=g, config=config), bw_excluded

    ###################

    @staticmethod
    def compute_from_data_space(
        data_space: ModelDataSpace,
        config: SATCostGraphConf,
        technologies: List[TechnologyConfiguration],
        years_opex: int,
        progress_bar: bool = False,
    ):

        technology = technologies[0]  # Fiber is the first always

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
            maximum_distance=technology.constraints.maximum_connection_length,
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
        cost_graph, fiber_bw_excluded = SATCostGraph.from_existing_edges_fiber(
            data_space, edges, config, technology, years_opex
        )
        if len(technologies) == 1:  # Fiber only
            return cost_graph, [fiber_bw_excluded]
        else:
            # Tech order: Fiber LEO Cell P2P
            # 1 LEO
            # doesn't need anything

            # 2 Cell
            tower_coordinates = data_space.get_cell_tower_coordinates_with_technologies(
                technologies[2].constraints.valid_cellular_technologies
            )
            LOGGER.info(f"Starting Cellular Cost Model")
            connection_model = GreedyDistanceConnector(
                tower_coordinates,
                dynamic_connect=False,  # this will create closest distance pairs
                progress_bar=progress_bar,
                maximum_connection_length_m=technologies[2].constraints.maximum_range,
                distance_cache=data_space.cellular_cache,
            )
            # determine which schools are in range of cell towers
            distances_cell = connection_model.run(data_space.school_coordinates)

            # 3 P2P
            connect_model = GreedyDistanceConnector(
                data_space.cell_tower_coordinates,
                dynamic_connect=False,  # this will create closest distance pairs
                progress_bar=progress_bar,
                maximum_connection_length_m=technologies[3].constraints.maximum_range,
                distance_cache=data_space.p2p_cache,
            )
            # determine which schools are in range of cell towers
            distances_p2p = connect_model.run(data_space.school_coordinates)

            other_excluded = cost_graph.extend_for_all(
                data_space,
                edges,
                config,
                technologies,
                years_opex,
                distances_cell,
                distances_p2p,
            )
            return cost_graph, fiber_bw_excluded + other_excluded

    ###################

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
        mst = nx.minimum_spanning_tree(mst, weight="weight", algorithm=algorithm)
        return CostMinimumSpanningTree(mst)

    def compute_mst_directed(self):
        mst = self.digraph.copy()

        edmonds = Edmonds(mst)
        mst = edmonds.find_optimum(
            attr="weight", kind="min", style="arborescence", preserve_attrs=True
        )
        return CostMinimumSpanningDirectedTree(mst)
