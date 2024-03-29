import math
import numpy as np

from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.output import OutputSpace, SchoolConnectionCosts
from giga.schemas.conf.models import MinimumCostScenarioConf
from giga.models.components.fiber_cost_model import FiberCostModel
from giga.models.components.satellite_cost_model import SatelliteCostModel
from giga.models.components.cellular_cost_model import CellularCostModel
from giga.models.components.p2p_cost_model import P2PCostModel
from giga.models.components.fiber_and_p2p_cost_model import FiberP2PCostModel
from giga.models.components.optimizers.economies_of_scale_minimizer import (
    EconomiesOfScaleMinimizer,
)
from giga.models.components.optimizers.constrained_economies_of_scale_minimizer import (
    ConstrainedEconomiesOfScaleMinimizer,
)
from giga.models.components.optimizers.baseline_minimizer import BaselineMinimizer
from giga.utils.logging import LOGGER


class MinimumCostScenario:
    """
    Estimates the cost of connecting a collection of schools to the internet
    using the technologies specified in the configuration
    computes the minimum cost of connectivity by optimizing over the
    net project value of the technology over the configured time horizon.
    """

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
        self.data_space.schools.update_required_power_all(self.config.required_power_per_school)

    def _create_minimizer(self,economies_of_scale):
        if self.config.cost_minimizer_config.economies_of_scale:
            if self.config.cost_minimizer_config.budget_constraint == math.inf:
                return EconomiesOfScaleMinimizer(self.config.cost_minimizer_config,economies_of_scale)
            else:
                return ConstrainedEconomiesOfScaleMinimizer(
                    self.config.cost_minimizer_config,economies_of_scale
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

    def run_stable(self, progress_bar: bool = False):
        """
        Runs the minimum cost scenario by computing the cost of each technology
        and then applying a minimizer to find the minimum cost solution.

        :param progress_bar, wether or not to show the progress bar when running the scenario
        :return output space that contains costs of each technology considered as well as the minimum costs for each school
        """
        LOGGER.info(f"Starting Minimum Cost Scenario")
        self._prep()

        techs = [c.technology for c in self.config.technologies]
        
        #We deal with this now, optimize in the future
        if "Fiber" in techs and "P2P" in techs:
            economies_of_scale = ["fiber","p2p"]
            # compute baseline costs for all the technologies
            for c in self.config.technologies:
                if c.technology!="P2P":
                    cost_model = self._make_model(c)
                    output = cost_model.run(self.data_space, progress_bar=progress_bar)
                    self._to_output_space(output, c)
            #here we should do P2P for everything not feasible before

            #aggregate
            aggregated = self._aggregate_outputs_by_school()
            self.output_space.aggregated_costs = self._aggregate_outputs_by_technology(
                aggregated
            )
        else:
            if "P2P" in techs:
                economies_of_scale = ["p2p"] 
            elif "Fiber" in techs:
                economies_of_scale = ["fiber"]
            # compute baseline costs for all the technologies
            for c in self.config.technologies:
                cost_model = self._make_model(c)
                output = cost_model.run(self.data_space, progress_bar=progress_bar)
                self._to_output_space(output, c)
            aggregated = self._aggregate_outputs_by_school()
            self.output_space.aggregated_costs = self._aggregate_outputs_by_technology(
                aggregated
            )

        # find the minimum cost for each school using the minimizer
        minimizer = self._create_minimizer(economies_of_scale)
        self.output_space.minimum_cost_result = minimizer.run(self.output_space,self.config.scenario_id)
        return self.output_space
    
    def run(self, progress_bar: bool = False):
        """
        Runs the minimum cost scenario by computing the cost of each technology
        and then applying a minimizer to find the minimum cost solution.

        :param progress_bar, wether or not to show the progress bar when running the scenario
        :return output space that contains costs of each technology considered as well as the minimum costs for each school
        """
        LOGGER.info(f"Starting Minimum Cost Scenario")
        self._prep()

        self.output_space.years_opex = self.config.years_opex

        techs = [c.technology for c in self.config.technologies]
        
        #We deal with this now, optimize in the future
        if "Fiber" in techs and "P2P" in techs:
            economies_of_scale = ["fiber","p2p"]
            fiber_conf = self.config.technologies[techs.index("Fiber")]
            p2p_conf = self.config.technologies[techs.index("P2P")]
            #Compute EoS of both fiber and p2p together
            cost_model = FiberP2PCostModel(fiber_conf,p2p_conf)
            outputs = cost_model.run(self.data_space, progress_bar=progress_bar)
            self._to_output_space(outputs[0], fiber_conf)
            self._to_output_space(outputs[1], p2p_conf)
            # compute baseline costs for all the technologies
            for c in self.config.technologies:
                if c.technology!="P2P" and c.technology!="Fiber":
                    cost_model = self._make_model(c)
                    output = cost_model.run(self.data_space, progress_bar=progress_bar)
                    self._to_output_space(output, c)
            #here we should do P2P for everything not feasible before

            #aggregate
            aggregated = self._aggregate_outputs_by_school()
            self.output_space.aggregated_costs = self._aggregate_outputs_by_technology(
                aggregated
            )
        else:
            if "P2P" in techs:
                economies_of_scale = ["p2p"] 
            elif "Fiber" in techs:
                economies_of_scale = ["fiber"]
            else:
                economies_of_scale = []
            # compute baseline costs for all the technologies
            for c in self.config.technologies:
                cost_model = self._make_model(c)
                output = cost_model.run(self.data_space, progress_bar=progress_bar)
                self._to_output_space(output, c)
            aggregated = self._aggregate_outputs_by_school()
            self.output_space.aggregated_costs = self._aggregate_outputs_by_technology(
                aggregated
            )

        # find the minimum cost for each school using the minimizer
        minimizer = self._create_minimizer(economies_of_scale)
        self.output_space.minimum_cost_result = minimizer.run(self.output_space,self.config.scenario_id)
        return self.output_space
