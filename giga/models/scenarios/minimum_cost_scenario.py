import math
import numpy as np

from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.output import OutputSpace, SchoolConnectionCosts
from giga.schemas.conf.models import MinimumCostScenarioConf
from giga.models.components.fiber_cost_model import FiberCostModel
from giga.models.components.satellite_cost_model import SatelliteCostModel
from giga.models.components.cellular_cost_model import CellularCostModel


class MinimumCostScenario:
    def __init__(
        self,
        config: MinimumCostScenarioConf,
        data_space: ModelDataSpace,
        output_space: OutputSpace,
    ):
        self.config = config
        self.data_space = data_space
        self.output_space = output_space

    def _prep(self):
        # update bw demand
        self.data_space.schools.update_bw_demand_all(self.config.bandwidth_demand)

    def _make_model(self, model_config):
        if model_config.technology == "Fiber":
            return FiberCostModel(model_config)
        elif model_config.technology == "Satellite":
            return SatelliteCostModel(model_config)
        elif model_config.technology == "Cellular":
            return CellularCostModel(model_config)
        else:
            raise ValueError("No Supported Technology")

    def _to_output_space(self, output, config):
        if config.technology == "Fiber":
            self.output_space.fiber_costs = output
        elif config.technology == "Satellite":
            self.output_space.satellite_costs = output
        elif config.technology == "Cellular":
            self.output_space.cellular_costs = output
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

    def _compute_total_cost(self, cost):
        if self.config.opex_responsible == "Consumer":
            opex = cost.opex_consumer
        elif self.config.opex_responsible == "Provider":
            opex = cost.opex_provider
        else:
            opex = cost.opex
        return cost.capex + self.config.years_opex * opex

    def _find_minmum_cost(self, costs, school_id):
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
            totals = list(map(lambda x: self._compute_total_cost(x), costs))
            idx = np.nanargmin(totals)
            return costs[idx]

    def run(self):
        self._prep()
        for c in self.config.technologies:
            cost_model = self._make_model(c)
            output = cost_model.run(self.data_space)
            self._to_output_space(output, c)
        aggregated = self._aggregate_outputs_by_school()
        minimum_costs = [
            self._find_minmum_cost(costs, school_id)
            for school_id, costs in aggregated.items()
        ]
        self.output_space.minimum_cost_result = minimum_costs
        return self.output_space
