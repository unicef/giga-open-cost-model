import os
import pytest
from pathlib import Path

from giga.app.config_client import ConfigClient
from giga.models.components.fiber_cost_model import FiberCostModel
from giga.schemas.conf.models import FiberTechnologyCostConf
from giga.models.components.satellite_cost_model import SatelliteCostModel
from giga.schemas.conf.models import SatelliteTechnologyCostConf
from giga.models.components.cellular_cost_model import CellularCostModel
from giga.schemas.conf.models import CellularTechnologyCostConf
from giga.models.components.p2p_cost_model import P2PCostModel
from giga.schemas.conf.models import P2PTechnologyCostConf
from giga.data.space.model_data_space import ModelDataSpace


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
def p2p_config():
    return P2PTechnologyCostConf(
        capex={"tower_fixed_costs":100.0},
        opex={
            "fixed_costs": 0.0,
            "annual_bandwidth_cost_per_mbps": 10.0
        },
        constraints={
            "maximum_bandwithd": 300.0,
            "required_power": 10.0,
            "maximum_range": 800_000,
        },
        electricity_config={
            "capex": {"solar_panel_costs": 500.0, "battery_costs": 0.0},
            "opex": {"cost_per_kwh": 0.1},
        },
    )


@pytest.fixture()
def data_space(global_config):
    return ModelDataSpace(global_config.local_workspace_data_space_config)


def test_fiber_component(fiber_config, data_space):
    # create and run the model
    model = FiberCostModel(fiber_config)
    outputs = model.run(data_space)  # pass in the model at runtime
    # test for regression
    assert all([r.technology == "Fiber" for r in outputs.cost_results])
    assert len(outputs.cost_results) == 50  # 50 schools checked
    assert (
        outputs.cost_results[0].feasible is False
    )  # first school is too far away from a fiber node
    assert outputs.cost_results[1].feasible is True


def test_satellite_component(satellite_config, data_space):
    # create and run the mode
    model = SatelliteCostModel(satellite_config)
    outputs = model.run(data_space)  # pass in the model at runtime
    # test for regression
    assert all([r.technology == "Satellite" for r in outputs.cost_results])
    assert len(outputs.cost_results) == 50  # 50 schools checked
    assert outputs.cost_results[0].capex == 500.0  # Fixed install cost
    assert outputs.cost_results[0].opex == 300.0  # Operating cost


def test_cellular_component(cellular_config, data_space):
    # create and run the mode
    model = CellularCostModel(cellular_config)
    outputs = model.run(data_space)  # pass in the model at runtime
    # test for regression
    assert all([r.technology == "Cellular" for r in outputs.cost_results])
    assert len(outputs.cost_results) == 50  # 50 schools checked
    assert outputs.cost_results[0].capex == 500.0  # Fixed install cost
    assert outputs.cost_results[0].opex == 200.0  # Operating cost

def test_p2p_component(p2p_config, data_space):
    # create and run the mode
    model = P2PCostModel(p2p_config)
    outputs = model.run(data_space)
    assert all([r.technology == "P2P" for r in outputs.cost_results])
    assert len(outputs.cost_results) == 50  # 50 schools checked
    assert outputs.cost_results[0].capex == 100.0  # Fixed install cost
    assert outputs.cost_results[0].opex == 200.0  # Operating cost