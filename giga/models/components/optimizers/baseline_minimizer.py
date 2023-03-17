import numpy as np
import math

from giga.schemas.conf.models import CostMinimizerConf
from giga.schemas.output import OutputSpace


class BaselineMinimizer:
    """
    Implements the baseline minimizer which selects the cheapest feasible technology
    """

    def __init__(self, config: CostMinimizerConf):
        self.config = config

    def single_school_minimum_cost(self, school_id, costs):
        # Finds the minimum cost for a single school
        feasible = any(list(map(lambda x: x.feasible, costs)))
        if not feasible:
            reasons = ",".join(
                list(map(lambda x: "" if x.reason is None else x.reason, costs))
            ).strip(",")
            return SchoolConnectionCosts(
                school_id=school_id,
                capex=math.nan,
                opex=math.nan,
                opex_provider=math.nan,
                opex_consumer=math.nan,
                technology="None",
                feasible=False,
                reason=reasons,
            )
        else:
            totals = [
                c.technology_connectivity_cost(self.config.years_opex) for c in costs
            ]
            idx = np.nanargmin(totals)
            return costs[idx]

    def run(self, output: OutputSpace):
        """
        Runs the baseline minimizer
            Input: OutputSpace, that contains costs for all the technologies of interest
            Output: List of minimum costs for each school
        """
        minimum_costs = [
            self.single_school_minimum_cost(school_id, list(technology_costs.values()))
            for school_id, technology_costs in output.aggregated_costs.items()
        ]
        return minimum_costs
