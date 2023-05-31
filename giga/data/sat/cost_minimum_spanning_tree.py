import networkx as nx


IGNORE_COST_NODES = set(["metanode"])

UNCONNECTED_NODE_LABELS = set(["uschool"])


class CostMinimumSpanningTree:
    def __init__(self, tree: nx.Graph):
        self.tree = tree

    def compute_cost_fiber(self, cost_per_meter: float = 1.0):
        # TODO: We don't need both of the per km or per m costs
        c = 0
        per_km_cost_lookup = {}
        # node costs
        for n, attributes in self.tree.nodes(data=True):
            if n not in IGNORE_COST_NODES:
                c += attributes["cost"] + attributes["ncost"]
                if attributes["label"] in UNCONNECTED_NODE_LABELS:
                    per_km_cost_lookup[n] = attributes["pkmcost"]
        # edge costs
        for n1, n2, attributes in self.tree.edges(data=True):
            if n1 in per_km_cost_lookup:
                c += attributes["weight"] * (cost_per_meter + per_km_cost_lookup[n1])
            elif n2 in per_km_cost_lookup:
                c += attributes["weight"] * (cost_per_meter + per_km_cost_lookup[n2])
            else:
                c += attributes["weight"] * cost_per_meter
        return c


class CostMinimumSpanningDirectedTree:
    def __init__(self, tree: nx.DiGraph):
        self.tree = tree

    def compute_cost_all(self, cost_per_meter: float = 1.0):
        # TODO: We don't need both of the per km or per m costs
        c = 0
        used_links = []
        for n, attributes in self.tree.nodes(data=True):
            if n != "metanode" and attributes["label"] == "uschool":
                path = list(nx.shortest_path(self.tree, "metanode", n))
                if (
                    self.tree.nodes[path[len(path) - 3]]["label"] == "metaTech"
                ):  # metaTech
                    c += self.tree.edges[path[1], path[2]]["weight"]
                else:  # fiber
                    for i in range(2, len(path)):
                        if (path[i], path[i - 1]) not in used_links:
                            pkmcost = self.tree.nodes[path[i - 1]]["pkmcost"]
                            cost = (
                                self.tree.nodes[path[i - 1]]["cost"]
                                + self.tree.nodes[path[i - 1]]["ncost"]
                            )
                            c += (
                                self.tree.edges[path[i - 1], path[i]]["weight"]
                                * (cost_per_meter + pkm)
                                + cost
                            )
                            used_links.append((path[i], path[i - 1]))
        return c
