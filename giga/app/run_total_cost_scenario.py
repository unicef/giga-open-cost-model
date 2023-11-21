#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()
import os
import argparse

from giga.utils.logging import LOGGER
from giga.app.config_client import ConfigClient
from giga.schemas.output import OutputSpace
from giga.models.scenarios.scenario_dispatcher import create_scenario

from giga.schemas.conf.models import (
    FiberTechnologyCostConf,
    SatelliteTechnologyCostConf,
    CellularTechnologyCostConf,
    P2PTechnologyCostConf,
    MinimumCostScenarioConf,
    ElectricityCostConf,
    PriorityScenarioConf,
)

from giga.data.space.model_data_space import ModelDataSpace
from giga.app.config import get_country_default

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Required data is loaded from here
DEFAULT_WORKPACE = os.path.join(ROOT_DIR, "../../notebooks/sample_workspace")
DEFAULT_WORKPACE = "workspace"

DEFAULT_SCENARIO_PARAMS = {
    "opex_responsible": "Consumer",
    "years_opex": 5.0,
    "bandwidth_demand": 40.0,
}  # in mbs

DEFAULT_ELECTRICITY_CONF = ElectricityCostConf(
    capex={"solar_cost_per_watt": 3.0},  # USD
    opex={"cost_per_kwh": 0.09},  # USD
    constraints={"required_power_per_school": 11000,
    "allow_new_electricity": True}
)

DEFAULT_FIBER_CONF = FiberTechnologyCostConf(
    capex={
        "fixed_costs": 0.0,
        "cost_per_km": 10_000,  # USD
        "economies_of_scale": True,
        "schools_as_fiber_nodes": True
    },
    opex={
        "fixed_costs": 0,
        "cost_per_km": 0,  # USD
        "annual_bandwidth_cost_per_mbps": 6.09,  # in USD
    },
    constraints={
        "maximum_connection_length": 20,  # in kmeters
        "required_power": 500,  # in kWh
        "maximum_bandwithd": 2_000.0,  # mbps
        "correction_coeficient": True
    },
    electricity_config=DEFAULT_ELECTRICITY_CONF,
)

DEFAULT_SATELLITE_CONF = SatelliteTechnologyCostConf(
    capex={"fixed_costs": 534},  # USD hardware installation
    opex={
        "fixed_costs": 0.0,  # USD hardware maintance
        "annual_bandwidth_cost_per_mbps": 34.0,
    },
    constraints={
        "maximum_bandwithd": 150.0,  # should be pulled from defaults
        "required_power": 10.0,
    },
    electricity_config=DEFAULT_ELECTRICITY_CONF,
)

DEFAULT_CELLULAR_CONF = CellularTechnologyCostConf(
    capex={"fixed_costs": 534.0},
    opex={
        "fixed_costs": 0.0,
        "annual_bandwidth_cost_per_mbps": 34.0,
    },
    constraints={
        "maximum_bandwithd": 100.0,
        "required_power": 10.0,
        "maximum_range": 6,  # in km
    },
    electricity_config=DEFAULT_ELECTRICITY_CONF,
)

DEFAULT_P2P_CONF = P2PTechnologyCostConf(
    capex={
        "fixed_costs": 4272.0,
        "tower_fixed_costs": 0.0,
    },
    opex={
        "fixed_costs": 0.0,
        "annual_bandwidth_cost_per_mbps": 68.0,
    },
    constraints={
        "maximum_bandwithd": 100.0,
        "required_power": 10.0,
        "maximum_range": 35,  # in km
    },
    electricity_config=DEFAULT_ELECTRICITY_CONF,
)

"""
This script will run a total cost scenario using for a "Sample" country
using the input workspace defined above (or specified as an argument).
It will write an output table containing the costs for each school that was part of
the input data.
"""


def main():
    parser = argparse.ArgumentParser()
    # No required arguments for now
    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    optional.add_argument(
        "--workspace",
        "-w",
        default=DEFAULT_WORKPACE,
        help="Local workspace where required input data is stored",
    )
    optional.add_argument(
        "--country",
        "-c",
        #choices=["RWA", "BRA"],
        default="RWA",
        help="Specifies the country of interest, your workspace will need to contain the data for that country",
    )
    optional.add_argument("--output-file", "-o", default="costs.csv")
    optional.add_argument(
        "--scenario-type",
        "-s",
        choices=["minimum-cost-giga", "priority-cost","fiber", "cellular", "p2p", "satellite"],
        default="minimum-cost-giga",
        help="Defines the type of scenario to run",
    )
    optional.add_argument(
        "--no-fiber",
        "-nf",
        action="store_false",
        dest="try_fiber",
        help="Disallows the use of fiber",
    )
    optional.add_argument(
        "--no-cellular",
        "-nc",
        action="store_false",
        dest="try_cellular",
        help="Disallows the use of cellular",
    )
    optional.add_argument(
        "--no-p2p",
        "-np",
        action="store_false",
        dest="try_p2p",
        help="Disallows the use of p2p",
    )
    optional.add_argument(
        "--no-satellite",
        "-ns",
        action="store_false",
        dest="try_satellite",
        help="Disallows the use of satellite",
    )
    args = parser.parse_args()

    # Configure data space client - we'll use a helper here that will point to the local workspace
    global_config = ConfigClient.from_country_defaults(get_country_default(args.country, workspace= args.workspace))
    available_tech = global_config.defaults.model_defaults.available_tech
    data_space_config = global_config.local_workspace_data_space_config
    data_space = ModelDataSpace(data_space_config)

    # Configure scenario
    techs = []
    if args.try_fiber and available_tech.fiber:
        fiber_config = DEFAULT_FIBER_CONF
        #fiber_config.electricity_config = DEFAULT_ELECTRICITY_CONF
        techs.append(fiber_config)
    if args.try_cellular and available_tech.cellular:
        cell_config = DEFAULT_CELLULAR_CONF
        #cell_config.electricity_config = DEFAULT_ELECTRICITY_CONF
        techs.append(cell_config)
    if args.try_p2p and available_tech.p2p:
        p2p_config = DEFAULT_P2P_CONF
        #p2p_config.electricity_config = DEFAULT_ELECTRICITY_CONF
        techs.append(p2p_config)
    if args.try_satellite and available_tech.satellite:
        satellite_config = DEFAULT_SATELLITE_CONF
        #satellite_config.electricity_config = DEFAULT_ELECTRICITY_CONF
        techs.append(satellite_config)

    if args.scenario_type == "minimum-cost-giga":
        # minimum cost
        scenario_config = MinimumCostScenarioConf(
            scenario_id = "minimum_cost_giga",
            years_opex = 5,  # the number of opex years to consider in the estimate
            opex_responsible = "Consumer",
            bandwidth_demand =  20,  # Mbps
            required_power_per_school = 11000, #Watts
            technologies=[],
        )
        
    else:
        scenario_config = PriorityScenarioConf(
            scenario_id = "priority_cost",
            years_opex = 5,  # the number of opex years to consider in the estimate
            opex_responsible = "Consumer",
            bandwidth_demand = 20,  # Mbps
            required_power_per_school = 11000, #Watts
            technologies=[],
        )

    scenario_config.technologies = techs
    # create scenario
    scenario = create_scenario(scenario_config, data_space)
    # run the scenario
    output_space = scenario.run()
    # write results
    output_space.table.to_csv(args.output_file)


if __name__ == "__main__":
    main()
