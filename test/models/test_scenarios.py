import os
import pytest
from pathlib import Path

from giga.app.config_client import ConfigClient
from giga.models.components.fiber_cost_model import FiberCostModel
from giga.schemas.conf.models import FiberTechnologyCostConf, SatelliteTechnologyCostConf, CellularTechnologyCostConf, SingleTechnologyScenarioConf, MinimumCostScenarioConf
from giga.models.components.satellite_cost_model import SatelliteCostModel
from giga.models.components.cellular_cost_model import CellularCostModel
from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.output import OutputSpace
from giga.models.scenarios.single_technology_scenario import SingleTechnologyScenario
from giga.models.scenarios.minimum_cost_scenario import MinimumCostScenario


FIXTURE_DIRECTORY = Path(__file__).resolve().parent / "fixtures"
SAMPLE_WORKSPACE = os.path.join(FIXTURE_DIRECTORY, "sample_workspace")


@pytest.fixture()
def global_config():
    return ConfigClient.from_registered_country("sample", SAMPLE_WORKSPACE)


@pytest.fixture()
def fiber_config():
    return FiberTechnologyCostConf(
        capex={
            "cost_per_km": 7_500,  # USD
            "economies_of_scale": True,
        },
        opex={
            "cost_per_km": 100,  # USD
            "annual_bandwidth_cost_per_mbps": 10,  # in USD
        },
        constraints={
            "maximum_connection_length": 20_000,  # in meters
            "required_power": 500,  # in kWh
            "maximum_bandwithd": 2_000.0,  # mbps
        },
        electricity_config={
            "capex": {"solar_panel_costs": 500.0, "battery_costs": 0.0},
            "opex": {"cost_per_kwh": 0.1},
        },
    )


@pytest.fixture()
def satellite_config():
    return SatelliteTechnologyCostConf(
        capex={"fixed_costs": 500},  # USD hardware installation
        opex={
            "fixed_costs": 0.0,  # USD hardware maintance
            "annual_bandwidth_cost_per_mbps": 15.0,
        },
        constraints={
            "maximum_bandwithd": 150.0,  # should be pulled from defaults
            "required_power": 200.0,
        },
        electricity_config={
            "capex": {"solar_panel_costs": 500.0, "battery_costs": 0.0},
            "opex": {"cost_per_kwh": 0.1},
        },
    )


@pytest.fixture()
def cellular_config():
    return CellularTechnologyCostConf(
        capex={"fixed_costs": 500.0},
        opex={
            "fixed_costs": 0.0,
            "annual_bandwidth_cost_per_mbps": 10.0,
        },
        constraints={
            "maximum_bandwithd": 100.0,
            "required_power": 10.0,
            "maximum_range": 8_000,
        },  # in m
        electricity_config={
            "capex": {"solar_panel_costs": 500.0, "battery_costs": 0.0},
            "opex": {"cost_per_kwh": 0.1},
        },
    )

@pytest.fixture()
def single_tech_scenario_config_fiber(fiber_config):
    return SingleTechnologyScenarioConf(
        scenario_id="single_tech_test_scenario",
        technology="Fiber",
        years_opex=5,
        opex_responsible="Consumer",
        bandwidth_demand=40,
        tech_config=fiber_config
    )

@pytest.fixture()
def minimum_cost_scenario_config(fiber_config, satellite_config, cellular_config):
    # TODO (Nathan Eliason): Add p2p config to this test
    c = MinimumCostScenarioConf(
        scenario_id="minimum_cost",
        years_opex=5,
        opex_responsible="Consumer",
        bandwidth_demand=40,
        technologies=[fiber_config, satellite_config, cellular_config]
    )
    c.technologies[2] = cellular_config
    return c

@pytest.fixture()
def data_space(global_config):
    return ModelDataSpace(global_config.local_workspace_data_space_config)

@pytest.fixture()
def output_space():
    return OutputSpace()

def test_single_tech_scenario(single_tech_scenario_config_fiber, data_space, output_space):
    scenario = SingleTechnologyScenario(single_tech_scenario_config_fiber, data_space, output_space)
    output_space = scenario.run()
    cost_table = output_space.table
    cost_table['total_cost'] = cost_table['total_cost'].fillna(0)
    assert cost_table is not None
    assert len(cost_table[cost_table["technology"] == "Fiber"]) == 50
    assert len(cost_table[cost_table["technology"] == "Satellite"]) == 0
    assert len(cost_table[cost_table["technology"] == "Cellular"]) == 0
    assert sum(cost_table['total_cost']) == pytest.approx(2_753_199, 0.1)


def test_minimum_cost_scenario(minimum_cost_scenario_config, data_space, output_space):
    # TODO (Nathan Eliason): cost results may be different after p2p models are included
    scenario = MinimumCostScenario(minimum_cost_scenario_config, data_space, output_space)
    output_space = scenario.run()
    cost_table = output_space.table
    cost_table['total_cost'] = cost_table['total_cost'].fillna(0)
    assert cost_table is not None
    assert len(cost_table[cost_table["technology"] == "Fiber"]) == 0
    assert len(cost_table[cost_table["technology"] == "Satellite"]) == 27
    assert len(cost_table[cost_table["technology"] == "Cellular"]) == 23
    assert sum(cost_table['total_cost']) == pytest.approx(169_745, 0.1)
