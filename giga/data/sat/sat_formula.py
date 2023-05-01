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

    def build(self):
        # start with the graphs - the MST is used as an upper bound
        mst = self.graph.compute_mst()
        upper_bound = round(mst.compute_cost())
        # create the relational graph
        if self.relational_graph is None:
            self.relational_graph = self.graph.compute_relational_graph()

        (
            X,
            P,
            A,
            model,
            fixed_costs,
            remaining_budget,
            budget_upper_bound,
            school_objective,
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
        self.fixed_costs = fixed_costs
        self.remaining_budget = remaining_budget
        self.budget_variable = budget_upper_bound
        self.school_objective = school_objective
        return model
