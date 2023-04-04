from giga.schemas.conf.models import SingleTechnologyScenarioConf
from giga.models.components.fiber_cost_model import FiberCostModel
from giga.models.components.satellite_cost_model import SatelliteCostModel
from giga.models.components.cellular_cost_model import CellularCostModel
from giga.models.components.p2p_cost_model import P2PCostModel
from giga.schemas.output import CostResultSpace
from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.output import OutputSpace
from giga.utils.logging import LOGGER


class SingleTechnologyScenario:
    def __init__(
        self,
        config: SingleTechnologyScenarioConf,
        data_space: ModelDataSpace,
        output_space: OutputSpace,
    ):
        self.config = config
        self.data_space = data_space
        self.output_space = output_space

    def _make_model(self):
        if self.config.technology == "Fiber":
            return FiberCostModel(self.config.tech_config)
        elif self.config.technology == "Satellite":
            return SatelliteCostModel(self.config.tech_config)
        elif self.config.technology == "Cellular":
            return CellularCostModel(self.config.tech_config)
        elif self.config.technology == "P2P":
            return P2PCostModel(self.config.tech_config)
        else:
            raise ValueError("No Supported Technology")

    def _to_output_space(self, output: CostResultSpace):
        if self.config.technology == "Fiber":
            self.output_space.fiber_costs = output
        elif self.config.technology == "Satellite":
            self.output_space.satellite_costs = output
        elif self.config.technology == "Cellular":
            self.output_space.cellular_costs = output
        elif self.config.technology == "P2P":
            self.output_space.p2p_costs = output
        else:
            return self.output_space
        return self.output_space

    def _prep(self):
        # update bw demand
        self.data_space.schools.update_bw_demand_all(self.config.bandwidth_demand)

    def run(self, progress_bar: bool = False):
        LOGGER.info(f"Starting Single Technology Scenario {self.config.technology}")
        self._prep()
        cost_model = self._make_model()
        output = cost_model.run(self.data_space, progress_bar=progress_bar)
        return self._to_output_space(output)
