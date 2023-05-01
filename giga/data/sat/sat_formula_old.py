import itertools
from pydantic import BaseModel
from typing import Dict, List
import networkx as nx
from ortools.sat.python import cp_model

from giga.data.sat.sat_cost_graph import SATCostGraph
from giga.utils.logging import LOGGER
from giga.data.sat.sat_utils import build_sat_problem


class SATFormula:

    """
    Manages the formula or set of variables and constraints to be passed to the solver.
    The formula is a set of variables and constraints that are passed to the solver.
    The variables are the decision variables that are used to determine the optimal
    solution. The constraints are the conditions that must be met by the solution.
    """

    def __init__(
        self,
        budget: int,
        cost_per_m: int,
        graph: SATCostGraph,
        relational_graph=None,
        do_hints=True,
    ):
        self.budget = budget
        self.remaining_budget = budget
        self.cost_per_m = cost_per_m
        self.graph = graph
        self.relational_graph = relational_graph
        self.do_hints = do_hints
        self.model = cp_model.CpModel()
        # problem variables
        self.X = {}
        self.P = {}
        self.A = {}
        # cost values
        self.fixed_costs = 0
        self.budget_variable = None
        self.school_objective = None

    def _make_metanode(self):
        self.X["metanode"] = self.model.NewBoolVar("x_metanode")
        self.model.Add(self.X["metanode"] == True)  # is this necessary?

    def _process_vertex(
        self,
        id,
        attributes,
        vertices,
        for_cost_vars,
        for_cost_weights,
        for_obj_vars,
        for_obj_weights,
    ):
        label = attributes["label"]
        cost, ncost = attributes["cost"], attributes["ncost"]
        pkmcost, pindex = attributes["pkmcost"], attributes["pindex"]

        self.X[id] = self.model.NewBoolVar("x_{0}".format(id))
        if label not in vertices:
            vertices[label] = []
        vertices[label].append(id)

        if label in ["cfnode", "cschool"]:
            if self.budget == 0:
                self.fixed_costs += cost + ncost
                self.model.Add(self.X[id] == True)
            else:
                self.remaining_budget -= cost + ncost
                self.model.Add(self.X[id] == True)
        elif label == "uschool":
            if self.budget == 0:
                self.fixed_costs += cost + ncost
                self.model.Add(self.X[id] == True)
            else:
                if cost + ncost > 0:
                    for_cost_vars.append(self.X[id])
                    for_cost_weights.append(cost + ncost)
                for_obj_vars.append(self.X[id])
                for_obj_weights.append(pindex)
        else:
            if self.budget == 0:
                if cost + ncost > 0:
                    for_obj_vars.append(self.X[id])
                    for_obj_weights.append(cost + ncost)
            else:
                if cost + ncost > 0:
                    for_cost_vars.append(self.X[id])
                    for_cost_weights.append(cost + ncost)
        return vertices, for_cost_vars, for_cost_weights, for_obj_vars, for_obj_weights

    def _make_node_vars(
        self,
        vertices: Dict,
        for_cost_vars: List,
        for_cost_weights: List,
        for_obj_vars: List,
        for_obj_weights: List,
    ):
        for id, attributes in self.graph.nodes(data=True):
            (
                vertices,
                for_cost_vars,
                for_cost_weights,
                for_obj_vars,
                for_obj_weights,
            ) = self._process_vertex(
                id,
                attributes,
                vertices,
                for_cost_vars,
                for_cost_weights,
                for_obj_vars,
                for_obj_weights,
            )
        return vertices, for_cost_vars, for_cost_weights, for_obj_vars, for_obj_weights

    def _process_edge_parenthood(
        self,
        n1,
        n2,
        w,
        pkm1,
        pkm2,
        for_cost_vars,
        for_cost_weights,
        for_obj_vars,
        for_obj_weights,
    ):
        self.P[(n1, n2)] = self.model.NewBoolVar("p_{0}@{1}".format(n1, n2))

        if w > 0:
            if self.budget == 0:
                for_obj_vars.append(self.P[(n1, n2)])
                for_obj_weights.append(w * (pkm1 + self.cost_per_m))
            else:
                for_cost_vars.append(self.P[(n1, n2)])
                for_cost_weights.append(w * (pkm1 + self.cost_per_m))

        return for_cost_vars, for_cost_weights, for_obj_vars, for_obj_weights

    def _make_edge_vars(
        self,
        vertices: Dict,
        for_cost_vars: List,
        for_cost_weights: List,
        for_obj_vars: List,
        for_obj_weights: List,
    ):
        for n1, n2, attributes in self.graph.edges(data=True):
            w = attributes["weight"]
            pkm1, pkm2 = (
                self.graph.get_node(n1)["pkmcost"],
                self.graph.get_node(n2)["pkmcost"],
            )

            if n1 in vertices["cfnode"] + vertices["ufnode"] + vertices["cschool"]:
                if n2 in vertices["uschool"] + vertices["splitter"]:
                    (
                        for_cost_vars,
                        for_cost_weights,
                        for_obj_vars,
                        for_obj_weights,
                    ) = self._process_edge_parenthood(
                        n2,
                        n1,
                        w,
                        pkm2,
                        pkm1,
                        for_cost_vars,
                        for_cost_weights,
                        for_obj_vars,
                        for_obj_weights,
                    )
            elif n1 in vertices["uschool"] + vertices["splitter"]:
                if n2 in vertices["cfnode"] + vertices["ufnode"] + vertices["cschool"]:
                    (
                        for_cost_vars,
                        for_cost_weights,
                        for_obj_vars,
                        for_obj_weights,
                    ) = self._process_edge_parenthood(
                        n1,
                        n2,
                        w,
                        pkm1,
                        pkm2,
                        for_cost_vars,
                        for_cost_weights,
                        for_obj_vars,
                        for_obj_weights,
                    )
                elif n2 in vertices["uschool"] + vertices["splitter"]:
                    (
                        for_cost_vars,
                        for_cost_weights,
                        for_obj_vars,
                        for_obj_weights,
                    ) = self._process_edge_parenthood(
                        n1,
                        n2,
                        w,
                        pkm1,
                        pkm2,
                        for_cost_vars,
                        for_cost_weights,
                        for_obj_vars,
                        for_obj_weights,
                    )
                    (
                        for_cost_vars,
                        for_cost_weights,
                        for_obj_vars,
                        for_obj_weights,
                    ) = self._process_edge_parenthood(
                        n2,
                        n1,
                        w,
                        pkm2,
                        pkm1,
                        for_cost_vars,
                        for_cost_weights,
                        for_obj_vars,
                        for_obj_weights,
                    )

                    self.model.AddBoolOr(
                        [self.P[(n1, n2)].Not(), self.P[(n2, n1)].Not()]
                    )

        for fn in vertices["cfnode"] + vertices["cschool"] + vertices["ufnode"]:
            self.P[(fn, "metanode")] = self.model.NewBoolVar(
                "p_{0}@metanode".format(fn)
            )
            if fn in vertices["cfnode"] or fn in vertices["cschool"]:
                self.model.Add(self.P[(fn, "metanode")] == True)

        return vertices, for_cost_vars, for_cost_weights, for_obj_vars, for_obj_weights

    def _make_ancestors(self, vertices: Dict):
        for n1, n2 in self.relational_graph.edges():
            if n1 == "metanode":
                self.A[(n2, "metanode")] = self.model.NewBoolVar(
                    "a_{0}@metanode".format(n2)
                )
            elif n2 == "metanode":
                self.A[(n1, "metanode")] = self.model.NewBoolVar(
                    "a_{0}@metanode".format(n1)
                )
            elif (
                n1 in vertices["cfnode"]
                or n1 in vertices["ufnode"]
                or n1 in vertices["cschool"]
            ):
                if n2 in vertices["splitter"] or n2 in vertices["uschool"]:
                    self.A[(n2, n1)] = self.model.NewBoolVar("a_{0}@{1}".format(n2, n1))
            elif (
                n2 in vertices["cfnode"]
                or n2 in vertices["ufnode"]
                or n2 in vertices["cschool"]
            ):
                if n1 in vertices["splitter"] or n1 in vertices["uschool"]:
                    self.A[(n1, n2)] = self.model.NewBoolVar("a_{0}@{1}".format(n1, n2))
            elif (n1 in vertices["splitter"] or n1 in vertices["uschool"]) and (
                n2 in vertices["splitter"] or n2 in vertices["uschool"]
            ):
                self.A[(n1, n2)] = self.model.NewBoolVar("a_{0}@{1}".format(n1, n2))
                self.A[(n2, n1)] = self.model.NewBoolVar("a_{0}@{1}".format(n2, n1))
        return vertices

    def _make_constraints(self, vertices: Dict):
        def process_node(node, target_list):
            clause = []
            for target in target_list:
                if (node, target) in self.P:
                    clause.append(self.P[(node, target)])
            return clause

        def process_pair(node1, node2):
            if (node1, node2) in self.P:
                pji = self.P[(node1, node2)]
                clause = process_node(
                    node2,
                    vertices["uschool"]
                    + vertices["splitter"]
                    + vertices["cfnode"]
                    + vertices["ufnode"]
                    + vertices["cschool"],
                )
                self.model.AddBoolOr([pji.Not()] + clause)

        def process_us_sp_pair(us, sp):
            if (us, sp) in self.P:
                pji = self.P[(us, sp)]
                self.model.AddImplication(pji, self.A[(us, sp)])

        uschool_sp_combinations = [
            (us, sp) for us in vertices["uschool"] for sp in vertices["splitter"]
        ]

        for us in vertices["uschool"] + vertices["splitter"]:
            clause = process_node(
                us,
                vertices["uschool"]
                + vertices["splitter"]
                + vertices["cfnode"]
                + vertices["ufnode"]
                + vertices["cschool"],
            )

            self.model.Add(sum(c for c in clause) <= 1)
            self.model.Add(sum(c for c in clause) == 1).OnlyEnforceIf(self.X[us])
            self.model.Add(sum(c for c in clause) == 0).OnlyEnforceIf(self.X[us].Not())

        for fn in vertices["ufnode"]:
            self.model.Add(self.X[fn] == self.P[fn, "metanode"])

        for us1, us2 in itertools.product(vertices["uschool"], repeat=2):
            process_pair(us1, us2)

        for us, sp in uschool_sp_combinations:
            process_pair(us, sp)

        for sp1, sp2 in itertools.product(vertices["splitter"], repeat=2):
            process_pair(sp1, sp2)

        for fn in vertices["ufnode"]:
            for us, sp in uschool_sp_combinations:
                if (us, fn) in self.P:
                    pji = self.P[(us, fn)]
                    self.model.AddImplication(pji, self.P[(fn, "metanode")])
                if (sp, fn) in self.P:
                    pji = self.P[(sp, fn)]
                    self.model.AddImplication(pji, self.P[(fn, "metanode")])

        for us, sp in uschool_sp_combinations:
            process_us_sp_pair(us, sp)

        for sp1, sp2 in itertools.product(vertices["splitter"], repeat=2):
            process_us_sp_pair(sp1, sp2)

        for fn in vertices["ufnode"]:
            self.model.AddImplication(
                self.P[(fn, "metanode")], self.A[(fn, "metanode")]
            )

        for fn in vertices["cfnode"]:
            self.model.Add(self.A[(fn, "metanode")] == True)

        for cs in vertices["cschool"]:
            self.model.Add(self.A[(cs, "metanode")] == True)

        return vertices

    def _make_asymmetry(self, vertices: Dict):
        for us in vertices["uschool"]:
            for us2 in vertices["uschool"]:
                if (us, us2) in self.A:
                    self.model.AddImplication(
                        self.A[(us, us2)], self.A[(us2, us)].Not()
                    )
            for sp in vertices["splitter"]:
                if (us, sp) in self.A:
                    self.model.AddImplication(self.A[(us, sp)], self.A[(sp, us)].Not())

        for sp in vertices["splitter"]:
            for us in vertices["uschool"]:
                if (sp, us) in self.A:
                    self.model.AddImplication(self.A[(sp, us)], self.A[(us, sp)].Not())
            for sp2 in vertices["splitter"]:
                if (sp, sp2) in self.A:
                    model.AddImplication(self.A[(sp, sp2)], self.A[(sp2, sp)].Not())
        return vertices

    def _make_root_path(self, vertices: Dict):
        def add_transitivity_constraint(vi, vj, vk):
            if (vi, vj) in self.A and (vj, vk) in self.A and (vi, vk) in self.A:
                self.model.AddBoolOr(
                    [self.A[(vi, vj)].Not(), self.A[(vj, vk)].Not(), self.A[(vi, vk)]]
                )

        all_vertices = (
            ["metanode"]
            + vertices["cfnode"]
            + vertices["ufnode"]
            + vertices["cschool"]
            + vertices["uschool"]
            + vertices["splitter"]
        )
        for vi, vj, vk in itertools.product(all_vertices, repeat=3):
            add_transitivity_constraint(vi, vj, vk)
        if self.budget == 0:
            self._connect_all_unconnected_schools(vertices)
        self._enforce_edge_and_node_balance(vertices, all_vertices)
        return vertices

    def _connect_all_unconnected_schools(self, vertices: Dict):
        for us in vertices["uschool"]:
            self.model.Add(self.A[(us, "metanode")] == True)

    def _enforce_edge_and_node_balance(self, vertices: Dict, all_vertices: List[str]):
        clause1 = [self.X[v] for v in all_vertices if v != "metanode"]
        clause2 = [
            self.P[(v1, v2)]
            for v1, v2 in itertools.product(all_vertices, repeat=2)
            if (v1, v2) in self.P
        ]
        self.model.Add(sum(clause1) == sum(clause2))

    def _make_leq_constraints(
        self,
        upper_bound: int,
        for_cost_vars: List,
        for_cost_weights: List,
        for_obj_vars: List,
        for_obj_weights: List,
    ):
        if self.budget > 0:
            leq = []
            for i in range(len(for_cost_vars)):
                aux = self.model.NewIntVar(0, 10000000, "aux")
                self.model.Add(aux == for_cost_weights[i]).OnlyEnforceIf(
                    for_cost_vars[i]
                )
                self.model.Add(aux == 0).OnlyEnforceIf(for_cost_vars[i].Not())
                leq.append(aux)
            self.budget_variable = self.model.NewIntVar(0, 10000000, "Budget_cost")
            self.model.Add(self.budget_variable == sum(v for v in leq))
            self.model.Add(self.budget_variable <= self.remaining_budget)

            self.school_objective = self.model.NewIntVar(0, 100000000, "obj_schools")
            obj_aux = []
            for i in range(len(for_obj_vars)):
                aux = self.model.NewIntVar(0, 10000000, "aux")
                self.model.Add(aux == for_obj_weights[i]).OnlyEnforceIf(for_obj_vars[i])
                self.model.Add(aux == 0).OnlyEnforceIf(for_obj_vars[i].Not())
                obj_aux.append(aux)
            self.model.Add(self.school_objective == sum(v for v in obj_aux))
            self.model.Maximize(self.school_objective)
        else:
            # No budget cost variable or school obective
            if upper_bound > 0:
                obj_cost = self.model.NewIntVar(
                    0, upper_bound - self.fixed_costs, "obj_cost"
                )
            else:
                obj_cost = self.model.NewIntVar(0, 1000000000, "obj_cost")
            obj_aux = []
            for i in range(len(for_obj_vars)):
                aux = self.model.NewIntVar(0, 10000000, "aux")
                self.model.Add(aux == for_obj_weights[i]).OnlyEnforceIf(for_obj_vars[i])
                self.model.Add(aux == 0).OnlyEnforceIf(for_obj_vars[i].Not())
                obj_aux.append(aux)
            self.model.Add(obj_cost == sum(v for v in obj_aux))
            self.model.Minimize(obj_cost)
        return for_cost_vars, for_cost_weights, for_obj_vars, for_obj_weights

    def _make_hints(self, vertices: Dict, mst: nx.Graph):
        if self.budget == 0:
            used_hints = []
            for sc in vertices["uschool"]:
                path = list(nx.shortest_path(mst, "metanode", sc))
                for i in range(2, len(path)):
                    if (path[i], path[i - 1]) not in used_hints:
                        self.model.AddHint(self.P[(path[i], path[i - 1])], True)
                        used_hints.append((path[i], path[i - 1]))
        return vertices

    def build_old(self):
        # for managing the less than or equal to constraint
        constraint_vars, constraint_weights = [], []
        # for managing the objective
        obj_vars, obj_weight = [], []
        # variable managers
        vertices = {}
        vertices["ufnode"], vertices["cschool"], vertices["splitter"] = [], [], []
        # start with the graphs - the MST is used as an upper bound
        mst = self.graph.compute_mst()
        upper_bound = round(mst.compute_cost())
        LOGGER.info(f"MST Cost: {upper_bound}")
        # create the relational graph
        if self.relational_graph is None:
            self.relational_graph = self.graph.compute_relational_graph()
        # add metanode
        self._make_metanode()
        # set vars from nodes
        (
            vertices,
            constraint_vars,
            constraint_weights,
            obj_vars,
            obj_weight,
        ) = self._make_node_vars(
            vertices, constraint_vars, constraint_weights, obj_vars, obj_weight
        )
        # set vars from edges
        (
            vertices,
            constraint_vars,
            constraint_weights,
            obj_vars,
            obj_weight,
        ) = self._make_edge_vars(
            vertices, constraint_vars, constraint_weights, obj_vars, obj_weight
        )
        # set ancestor vars
        vertices = self._make_ancestors(vertices)
        # make constriants
        vertices = self._make_constraints(vertices)
        # make asymmetry
        vertices = self._make_asymmetry(vertices)
        # make transitivity + root path
        vertices = self._make_root_path(vertices)
        # set leq constraints
        (
            constraint_vars,
            constraint_weights,
            obj_vars,
            obj_weight,
        ) = self._make_leq_constraints(
            upper_bound, constraint_vars, constraint_weights, obj_vars, obj_weight
        )
        # add hints
        if self.do_hints:
            LOGGER.info("Adding hints")
            vertices = self._make_hints(vertices, mst)
        LOGGER.info("SAT Formula Built")
        return self.model

    def build(self):
        # start with the graphs - the MST is used as an upper bound
        mst = self.graph.compute_mst()
        upper_bound = round(mst.compute_cost())
        LOGGER.info(f"MST Cost: {upper_bound}")
        # create the relational graph
        if self.relational_graph is None:
            self.relational_graph = self.graph.compute_relational_graph()

        (
            X,
            P,
            A,
            model,
            fixed_costs,
            new_max_cost,
            budget_cost,
            obj_schools,
        ) = build_sat_problem(
            self.graph.graph,
            self.relational_graph,
            None,  # dt
            self.cost_per_m,
            self.budget,
            upper_bound,
            self.do_hints,
            mst,
        )
        self.X = X
        self.P = P
        self.A = A
        self.model = model
        return model
