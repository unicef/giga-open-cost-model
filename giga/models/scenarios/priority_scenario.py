import math
import numpy as np

from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.output import OutputSpace, SchoolConnectionCosts
from giga.schemas.conf.models import PriorityScenarioConf
from giga.models.components.fiber_cost_model import FiberCostModel
from giga.models.components.satellite_cost_model import SatelliteCostModel
from giga.models.components.cellular_cost_model import CellularCostModel
from giga.models.components.p2p_cost_model import P2PCostModel

from giga.models.components.optimizers.priority_minimizer import (
    PriorityMinimizer,
)
from giga.models.components.optimizers.constrained_priority_minimizer import (
    ConstrainedPriorityMinimizer,
)
from giga.models.components.optimizers.baseline_minimizer import BaselineMinimizer
from giga.utils.logging import LOGGER


class PriorityScenario:
    """
    Estimates the cost of connecting a collection of schools to the internet
    using the technologies specified in the configuration
    computes the minimum cost of connectivity by optimizing over the
    net project value of the technology over the configured time horizon.
    """

    def __init__(
        self,
        config: PriorityScenarioConf,
        data_space: ModelDataSpace,
        output_space: OutputSpace,
    ):
        self.config = config
        self.data_space = data_space
        self.output_space = output_space

    def _prep(self):
        # update bw demand
        self.data_space.schools.update_bw_demand_all(self.config.bandwidth_demand)
        self.data_space.schools.update_required_power_all(self.config.required_power_per_school)

    def _create_minimizer(self, tech_name, current_cost):
        if self.config.cost_minimizer_config.economies_of_scale:
            if self.config.cost_minimizer_config.budget_constraint == math.inf:
                return PriorityMinimizer(self.config.cost_minimizer_config)
            else:
                return ConstrainedPriorityMinimizer(
                    self.config.cost_minimizer_config,tech_name,current_cost
                )
        else:
            return BaselineMinimizer(self.config.cost_minimizer_config)

    def _make_model(self, model_config):
        if model_config.technology == "Fiber":
            return FiberCostModel(model_config)
        elif model_config.technology == "Satellite":
            return SatelliteCostModel(model_config)
        elif model_config.technology == "Cellular":
            return CellularCostModel(model_config)
        elif model_config.technology == "P2P":
            return P2PCostModel(model_config)
        else:
            raise ValueError("No Supported Technology")

    def _to_output_space(self, output, config):
        if config.technology == "Fiber":
            self.output_space.fiber_costs = output
        elif config.technology == "Satellite":
            self.output_space.satellite_costs = output
        elif config.technology == "Cellular":
            self.output_space.cellular_costs = output
        elif config.technology == "P2P":
            self.output_space.p2p_costs = output
        else:
            return self.output_space
        return self.output_space

    def _aggregate_outputs_by_school(self):
        agg = {}
        for outputs in self.output_space.technology_outputs:
            for cost_result in outputs.cost_results:
                sid = cost_result.school_id
                if sid not in agg:
                    agg[sid] = [cost_result]
                else:
                    agg[sid].append(cost_result)
        return agg

    def _aggregate_outputs_by_technology(self, by_school):
        by_tech = {}
        for sid, costs in by_school.items():
            by_tech[sid] = {c.technology.lower(): c for c in costs}
        return by_tech
    
    def trim_results(self,tech_name,current_cost,new_schools):
        minimizer = ConstrainedPriorityMinimizer(
                    self.config.cost_minimizer_config,tech_name,current_cost
                )
        current_cost,removed_ids = minimizer.run(self.output_space, new_schools)
        for sid in removed_ids:
            self.output_space.aggregated_costs[sid] = {}

        for outputs in self.output_space.technology_outputs:
            if outputs.tech_name==tech_name:
                outputs.cost_results = [x for x in outputs.cost_results if x.school_id not in removed_ids]

        return current_cost,removed_ids

    def run(self, progress_bar: bool = False):
        """
        Runs the priority scenario by computing the cost of each technology
        and then following a priority of fiber-4G-P2P-Satellite independent of cost

        :param progress_bar, wether or not to show the progress bar when running the scenario
        :return output space that contains costs of each technology considered as well as the minimum costs for each school
        """
        LOGGER.info(f"Starting Priority Cost Scenario")
        self._prep()

        self.output_space.years_opex = self.config.years_opex
        
        used_ids = []
        removed_ids = []
        current_cost = 0.0
        tech_name = "fiber"
        # compute baseline costs for all the technologies
        for c in self.config.technologies:
            tech_name = c.technology.lower()
            cost_model = self._make_model(c)
            output = cost_model.run(self.data_space, used_ids, progress_bar=progress_bar)
            self._to_output_space(output, c)
            aggregated = self._aggregate_outputs_by_school()
            self.output_space.aggregated_costs = self._aggregate_outputs_by_technology(
                aggregated
            )
            new_schools = []
            for cost_result in output.cost_results:
                if cost_result.feasible:
                    used_ids.append(cost_result.school_id)
                    new_schools.append(cost_result.school_id)
            new_cost = self.output_space.project_lifetime_cost(
                new_schools, tech_name, self.config.years_opex
            )
            if (current_cost+new_cost>=self.config.cost_minimizer_config.budget_constraint):
                current_cost,removed_ids = self.trim_results(tech_name,current_cost,new_schools)
                used_ids = [x for x in used_ids if x not in removed_ids]
            else:
                current_cost += new_cost

        # find the priorities cost for each school using the minimizer
        minimizer = PriorityMinimizer(self.config.cost_minimizer_config)
        self.output_space.minimum_cost_result = minimizer.run(self.output_space, removed_ids)
        return self.output_space
