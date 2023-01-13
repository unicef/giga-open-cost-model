from giga.models.scenarios.single_technology_scenario import SingleTechnologyScenario
from giga.models.scenarios.minimum_cost_scenario import MinimumCostScenario

from giga.schemas.conf.models import (
    SingleTechnologyScenarioConf,
    MinimumCostScenarioConf,
)


def create_scenario(scenario_config, data_space, output_space):
    if type(scenario_config) is SingleTechnologyScenarioConf:
        return SingleTechnologyScenario(scenario_config, data_space, output_space)
    elif type(scenario_config) is MinimumCostScenarioConf:
        return MinimumCostScenario(scenario_config, data_space, output_space)
    else:
        raise ValueError(f"Invalid scenario config {type(scenario_config)}")