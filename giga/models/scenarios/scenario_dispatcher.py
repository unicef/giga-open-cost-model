from giga.models.scenarios.single_technology_scenario import SingleTechnologyScenario
from giga.models.scenarios.minimum_cost_scenario import MinimumCostScenario
from giga.models.scenarios.priority_scenario import PriorityScenario
from giga.models.scenarios.sat_minimum_cost_scenario import SATMinimumCostScenario

from giga.schemas.conf.models import (
    SingleTechnologyScenarioConf,
    MinimumCostScenarioConf,
    PriorityScenarioConf,
)


def create_scenario(scenario_config, data_space, output_space):
    if type(scenario_config) is SingleTechnologyScenarioConf:
        return SingleTechnologyScenario(scenario_config, data_space, output_space)
    elif type(scenario_config) is MinimumCostScenarioConf:
        if (
            scenario_config.sat_solver_config is not None
            and scenario_config.sat_solver_config.sat_engine
        ):
            return SATMinimumCostScenario(scenario_config, data_space, output_space)
        else:
            return MinimumCostScenario(scenario_config, data_space, output_space)
    elif type(scenario_config) is PriorityScenarioConf:
        return PriorityScenario(scenario_config, data_space, output_space)
    else:
        raise ValueError(f"Invalid scenario config {type(scenario_config)}")
