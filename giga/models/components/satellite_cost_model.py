import math
from pydantic import validate_arguments

from giga.schemas.conf.models import SatelliteTechnologyCostConf
from giga.schemas.output import CostResultSpace, SchoolConnectionCosts
from giga.data.space.model_data_space import ModelDataSpace


class SatelliteCostModel:
    def __init__(self, config: SatelliteTechnologyCostConf):
        self.config = config

    def _cost_of_setup(self):
        return self.config.capex.fixed_costs

    def _cost_of_maintenance(self):
        return self.config.opex.fixed_costs

    def _cost_of_operation(self, school):
        return school.bandwidth_demand * self.config.opex.annual_bandwidth_cost_per_mbps

    def compute_costs(self, data_space: ModelDataSpace):
        capex_costs = self._cost_of_setup()
        opex_provider = self._cost_of_maintenance()
        costs = []
        for school in data_space.school_entities:
            sid = school.giga_id
            if school.bandwidth_demand > self.config.constraints.maximum_bandwithd:
                costs.append(
                    SchoolConnectionCosts(
                        school_id=sid,
                        capex=math.nan,
                        opex=math.nan,
                        opex_provider=math.nan,
                        opex_consumer=math.nan,
                        technology="Satellite",
                        feasible=False,
                        reason="SATELLITE_BW_THRESHOLD",
                    )
                )
            else:
                opex_consumer = self._cost_of_operation(school)
                costs.append(
                    SchoolConnectionCosts(
                        school_id=sid,
                        capex=capex_costs,
                        opex=opex_consumer + opex_provider,
                        opex_provider=opex_provider,
                        opex_consumer=opex_consumer,
                        technology="Satellite",
                    )
                )

        return costs

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def run(
        self, data_space: ModelDataSpace, progress_bar: bool = False
    ) -> CostResultSpace:
        """
        Computes a cost table for schools present in the data_space input
        """
        costs = self.compute_costs(data_space)
        return CostResultSpace(
            technology_results={"model_type": "Satellite"}, cost_results=costs
        )
