from pydantic import BaseModel, FilePath
from ortools.sat.python import cp_model
import networkx as nx

from giga.data.sat.sat_formula import SATFormula
from giga.data.sat.sat_cost_graph import SATCostGraph
from giga.data.sat.cost_relational_graph import CostRelationalGraph
from giga.models.nodes.sat.commons import SATSolution
from giga.schemas.conf.models import SATSolverConf
from giga.utils.logging import LOGGER


class SATSolverUnconstrained:
    def __init__(self, config: SATSolverConf):
        self.config = config

    def _get_solution(self, solver, problem):
        T = nx.Graph()
        d = {}
        num_schools = 0
        for n, attributes in problem.graph.nodes(data=True):
            if solver.Value(problem.X[n]):
                T.add_node(n)
                d[n] = attributes
                if attributes["label"] == "uschool":
                    num_schools += 1
        nx.set_node_attributes(T, d)

        for n1, n2, attributes in problem.graph.edges(data=True):
            add_edge = False
            if (n1, n2) in problem.P and n1 != "metanode" and n2 != "metanode":
                if solver.Value(problem.P[(n1, n2)]):
                    add_edge = True
            if (n2, n1) in problem.P and n1 != "metanode" and n2 != "metanode":
                if solver.Value(problem.P[(n2, n1)]):
                    add_edge = True
            if add_edge:
                T.add_edge(n1, n2, weight=attributes["weight"])
        return T, num_schools, solver.ObjectiveValue()

    def _set_solver_params(self, solver):
        solver.parameters.max_time_in_seconds = self.config.time_limit
        solver.parameters.num_search_workers = self.config.num_workers
        solver.parameters.log_search_progress = self.config.search_log
        return solver

    def _parse_solution(self, status, solver, problem):
        if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
            tree, n_schools, cost = self._get_solution(solver, problem)
            return SATSolution(
                solution_tree=tree,
                n_schools=n_schools,
                total_cost=cost + problem.fixed_costs,
                feasible=True,
                optimal=status == cp_model.OPTIMAL,
                optimal_cost=True,
            )
        else:
            return SATSolution()

    def _solve(self, problem: SATFormula):
        solver = cp_model.CpSolver()
        solver = self._set_solver_params(solver)
        # run solver
        status = solver.Solve(problem.model)
        return self._parse_solution(status, solver, problem)

    def run(self, graph: SATCostGraph):
        """
        Runs the unconstrained (scenario 1) SAT solver on a SATCostGraph
        :param graph: SATCostGraph representing the fiber and school geometries
        :return: SATSolution object containing the cost and tree of the solution
        """
        if self.config.load_relational_graph_path is not None:
            LOGGER.info(
                f"Loading relational graph from {self.config.load_relational_graph_path}"
            )
            relational_graph = CostRelationalGraph.read_gml(
                self.config.load_relational_graph_path
            )
        else:
            relational_graph = None
        problem = SATFormula(
            self.config.budget,
            self.config.cost_per_m,
            graph,
            relational_graph=relational_graph,
            do_hints=self.config.do_hints,
        )
        LOGGER.info("Building SAT problem")
        problem.build()
        solution = self._solve(problem)
        solution.initial_cost_graph = graph
        solution.problem = problem
        solution.relational_graph = problem.relational_graph
        if self.config.write_relational_graph_path is not None:
            problem.relational_graph.write_gml(self.config.write_relational_graph_path)
        return solution
