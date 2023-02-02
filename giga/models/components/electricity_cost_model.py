import math
from pydantic import validate_arguments

from giga.schemas.conf.models import ElectricityCostConf, TechnologyConfiguration
from giga.schemas.output import (
    CostResultSpace,
    SchoolConnectionCosts,
    PowerConnectionCosts,
)
from giga.schemas.school import GigaSchool
from giga.data.space.model_data_space import ModelDataSpace


class ElectricityCostModel:
    """
    Computes the electricity costs associated with connecting
    schools to the internet.
    Exposes a non-batch interface (e.g. to compute one school cost at a time)
    """

    def __init__(self, config: TechnologyConfiguration = None):
        self.config = config

    def _cost_of_setup(self):
        return self.config.capex.fixed_costs

    def _cost_of_maintenance(self):
        return self.config.opex.fixed_costs

    def _cost_of_operation(self, school):
        return school.bandwidth_demand * self.config.opex.annual_bandwidth_cost_per_mbps

    def compute_solar_cost(self, school: GigaSchool):
        capex = (
            self.config.electricity_config.capex.solar_panel_costs
            + self.config.electricity_config.capex.battery_costs
        )
        return PowerConnectionCosts(electricity_capex=capex, cost_type="Solar")

    def compute_grid_cost(self, school: GigaSchool):
        opex = (
            self.config.electricity_config.opex.cost_per_kwh
            * self.config.constraints.required_power
        )
        return PowerConnectionCosts(electricity_opex=opex, cost_type="Grid")

    def compute_cost(self, school: GigaSchool):
        if self.config is None and self.config.electricity_config is None:
            return PowerConnectionCosts()
        if school.has_electricity:
            return self.compute_grid_cost(school)
        else:
            return self.compute_solar_cost(school)
