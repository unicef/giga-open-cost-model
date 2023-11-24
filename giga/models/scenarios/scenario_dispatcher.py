from giga.schemas.output import OutputSpace
from giga.models.scenarios.single_technology_scenario import SingleTechnologyScenario
from giga.models.scenarios.minimum_cost_scenario import MinimumCostScenario
from giga.models.scenarios.priority_scenario import PriorityScenario

from giga.schemas.conf.models import (
    SingleTechnologyScenarioConf,
    MinimumCostScenarioConf,
    PriorityScenarioConf,
)


def create_scenario(scenario_config, data_space):

    output_space = OutputSpace(years_opex = scenario_config.years_opex)

    if type(scenario_config) is SingleTechnologyScenarioConf:
        return SingleTechnologyScenario(scenario_config, data_space, output_space)
    elif type(scenario_config) is MinimumCostScenarioConf:
            return MinimumCostScenario(scenario_config, data_space, output_space)
    elif type(scenario_config) is PriorityScenarioConf:
        return PriorityScenario(scenario_config, data_space, output_space)
    else:
        raise ValueError(f"Invalid scenario config {type(scenario_config)}")
