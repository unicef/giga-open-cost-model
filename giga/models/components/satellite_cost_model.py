import math
from pydantic import validate_arguments
from typing import List

from giga.schemas.conf.models import SatelliteTechnologyCostConf
from giga.schemas.output import CostResultSpace, SchoolConnectionCosts
from giga.data.space.model_data_space import ModelDataSpace
from giga.models.components.electricity_cost_model import ElectricityCostModel
from giga.utils.logging import LOGGER


class SatelliteCostModel:
    """
    Estimates the cost of connectivity using LEO satellite.
    CapEx considers terminal installation at school and solar installation if needed.
    OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.
    """

    def __init__(self, config: SatelliteTechnologyCostConf):
        self.config = config

    def _cost_of_setup(self):
        return self.config.capex.fixed_costs

    def _cost_of_operation(self, school):
        return (
            school.bandwidth_demand * self.config.opex.annual_bandwidth_cost_per_mbps
            + self.config.opex.fixed_costs
        )

    def compute_costs(self, data_space: ModelDataSpace,used_ids) -> List[SchoolConnectionCosts]:
        """
        Computes the cost of connecting a school to the internet using satellite technology.
        :param data_space: a data space containing school entities
        :return: a list of school connection costs for satellite technology
        """
        new_electricity = self.config.electricity_config.constraints.allow_new_electricity
        electricity_model = ElectricityCostModel(self.config)
        capex_consumer = self._cost_of_setup()
        costs = []
        for school in data_space.school_entities:
            sid = school.giga_id
            if sid in used_ids:#change reason
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "Satellite", "SATELLITE_BW_THRESHOLD"
                )
            elif school.bandwidth_demand > self.config.constraints.maximum_bandwithd:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "Satellite", "SATELLITE_BW_THRESHOLD"
                )
                """
                c = SchoolConnectionCosts(
                    school_id=sid,
                    capex=math.nan,
                    capex_provider=math.nan,
                    capex_consumer=math.nan,
                    opex=math.nan,
                    opex_provider=math.nan,
                    opex_consumer=math.nan,
                    technology="Satellite",
                    feasible=False,
                    reason="SATELLITE_BW_THRESHOLD",
                )
                """
            elif not school.has_electricity and not new_electricity:
                c = SchoolConnectionCosts.infeasible_cost(
                    sid, "Satellite", "NO_ELECTRICITY"
                )
            else:
                opex_consumer = self._cost_of_operation(school)
                c = SchoolConnectionCosts(
                    school_id=sid,
                    capex=capex_consumer,
                    capex_provider=0.0,
                    capex_consumer=capex_consumer,
                    opex=opex_consumer,
                    opex_provider=0.0,
                    opex_consumer=opex_consumer,
                    technology="Satellite",
                )
                c.electricity = electricity_model.compute_cost(school)
            costs.append(c)
        return costs

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def run(self, data_space: ModelDataSpace, used_ids: List = [], **kwargs) -> CostResultSpace:
        """
        Computes a cost table for schools present in the data_space input
        :param data_space: a data space containing school entities
        :return CostResultSpace, that contains the cost of satellite connectivity for all schools in the data space
        """
        LOGGER.info(f"Starting Satellite Cost Model")
        costs = self.compute_costs(data_space,used_ids)
        return CostResultSpace(
            technology_results={"model_type": "Satellite"}, cost_results=costs, tech_name="satellite"
        )
