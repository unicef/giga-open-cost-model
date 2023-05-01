import networkx as nx


DEFAULT_MAX_NUMBER_EDGES_THRESHOLD = 1_000

RELATIONAL_NODE_LABELS = set(["cfnode", "ufnode", "cschool", "uschool"])

CONNECTED_META_NODE_LABEL = "metanode"


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


def find_minimum_degree_node(G: nx.Graph):
    mins = sorted(G.degree, key=lambda x: x[1], reverse=False)
    minVal = mins[0][1]
    minsTied = []
    i = 0
    while mins[i][1] == minVal:
        minsTied.append(mins[i])
        i += 1
        if i == len(mins):
            break
    if i == 1:
        return minsTied[0][0]
    minsTied2 = []
    for t in minsTied:
        neis = list(G.neighbors(t[0]))
        sumd = 0
        for n in neis:
            sumd += G.degree(n)
        minsTied2.append((t[0], sumd))
    minsTiedSorted = sorted(minsTied2, key=lambda x: x[1], reverse=True)
    return minsTiedSorted[0][0]


class CostRelationalGraph:
    def __init__(self, base_graph: nx.Graph):
        self.base_graph = base_graph
        self.relational_graph = None

    @staticmethod
    def read_gml(filename: str):
        graph = nx.read_gml(filename)
        g = CostRelationalGraph(graph)
        g.relational_graph = graph
        return g

    def nodes(self, **kwargs):
        return self.relational_graph.nodes(**kwargs)

    def edges(self, **kwargs):
        return self.relational_graph.edges(**kwargs)

    def write_gml(self, filename: str):
        assert self.relational_graph is not None, "No relational graph to write"
        nx.write_gml(self.relational_graph, filename)

    def _simple_relational_graph(self):
        relational_graph = self.base_graph.copy()
        relational_graph = add_meta_node(
            relational_graph,
            CONNECTED_META_NODE_LABEL,
            RELATIONAL_NODE_LABELS,
            edge_weight=0,
        )
        relational_graph, _ = nx.algorithms.chordal.complete_to_chordal_graph(
            relational_graph
        )
        return relational_graph

    def _adhoc_relational_graph(self):
        relational_graph = self.base_graph.copy()
        relational_graph = add_meta_node(
            relational_graph,
            CONNECTED_META_NODE_LABEL,
            RELATIONAL_NODE_LABELS,
            edge_weight=0,
        )
        nodes = list(self.base_graph.nodes)
        tmp = relational_graph.copy()
        edges = []
        while len(tmp.nodes()) > 0:
            i = find_minimum_degree_node(tmp)
            for j in nodes:
                if i != j:
                    for k in nodes:
                        if (
                            j != k
                            and i != k
                            and (tmp.has_edge(i, j) or tmp.has_edge(j, i))
                            and (tmp.has_edge(i, k) or tmp.has_edge(k, i))
                        ):
                            tmp.add_edge(j, k, weight=0)
                            edges.append((j, k))
            tmp.remove_node(i)
        for a, b in edges:
            if not relational_graph.has_edge(a, b):
                relational_graph.add_edge(a, b, weight=0)
        return relational_graph

    def compute_relational_graph(
        self, relational_graph_edge_threshold: int = DEFAULT_MAX_NUMBER_EDGES_THRESHOLD
    ):
        if self.base_graph.number_of_edges() > relational_graph_edge_threshold:
            self.relational_graph = self._simple_relational_graph()
            return self
        else:
            self.relational_graph = self._adhoc_relational_graph()
            return self
