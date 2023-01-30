#!/usr/bin/env python3

import os
import argparse
import logging

from giga.utils.logging import LOGGER
from giga.app.config import ConfigClient, get_config
from giga.models.components.fiber_cost_model import FiberCostModel
from giga.schemas.output import OutputSpace
from giga.models.scenarios.scenario_dispatcher import create_scenario

from giga.schemas.conf.models import (
    FiberTechnologyCostConf,
    SatelliteTechnologyCostConf,
    CellularTechnologyCostConf,
    MinimumCostScenarioConf,
    SingleTechnologyScenarioConf,
    ElectricityCostConf,
)

from giga.data.space.model_data_space import ModelDataSpace


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Required data is loaded from here
DEFAULT_WORKPACE = os.path.join(ROOT_DIR, '../../notebooks/sample_workspace')


DEFAULT_SCENARIO_PARAMS = {'opex_responsible': 'Consumer',
                           'years_opex': 5.0,
                           'bandwidth_demand': 40.0} # in mbs

DEFAULT_ELECTRICITY_CONF = ElectricityCostConf(
                                capex={"solar_panel_costs": 10_000, # USD
                                       "battery_costs": 0.0},
                                opex={"cost_per_kwh": 0.10} # USD
                            )

DEFAULT_FIBER_CONF = FiberTechnologyCostConf(
                        capex={
                            "cost_per_km": 7_500, # USD
                            "economies_of_scale": True,
                        },
                        opex={
                            "cost_per_km": 100, # USD
                            "annual_bandwidth_cost_per_mbps": 10, # in USD
                        },
                        constraints={
                            "maximum_connection_length": 20_000, # in meters
                            "required_power": 500, # in kWh
                            "maximum_bandwithd": 2_000.0, # mbps
                        },
                        electricity_config=DEFAULT_ELECTRICITY_CONF
                    )

DEFAULT_SATELLITE_CONF = SatelliteTechnologyCostConf(
            capex={
                "fixed_costs": 500 # USD hardware installation
            },
            opex={
                "fixed_costs": 0.0, # USD hardware maintance
                "annual_bandwidth_cost_per_mbps": 15.0,
            },
            constraints={
                "maximum_bandwithd": 150.0,  # should be pulled from defaults
                "required_power": 200.0,
            },
            electricity_config=DEFAULT_ELECTRICITY_CONF
        )

DEFAULT_CELLULAR_CONF = CellularTechnologyCostConf(
            capex={"fixed_costs": 500.0},
            opex={
                "fixed_costs": 0.0,
                "annual_bandwidth_cost_per_mbps": 10.0,
            },
            constraints={"maximum_bandwithd": 100.0,
                         "required_power": 10.0,
                         "maximum_range": 8_000  # in m
            },
            electricity_config=DEFAULT_ELECTRICITY_CONF
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
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('--workspace', '-w', default=DEFAULT_WORKPACE, help='Local workspace where required input data is stored')
    optional.add_argument('--country', '-c', 
                          choices=['sample', 'rwanda', 'brazil'], default='sample',
                          help='Specifies the country of interest, your workspace will need to contain the data for that country')
    optional.add_argument('--output-file', '-o', default='costs.csv')
    optional.add_argument('--scenario-type', '-s', 
                          choices=['minimum-cost', 'fiber', 'cellular', 'satellite'], default='minimum-cost',
                          help='Defines the type of scenario to run')
    args = parser.parse_args()

    # Configure data space client - we'll use a helper here that will point to the local workspace
    global_config = ConfigClient(get_config(["data={args.country}", f"data.workspace={args.workspace}"]))
    data_space_config = global_config.local_workspace_data_space_config
    data_space = ModelDataSpace(data_space_config)

    # Configure scenario
    if args.scenario_type == 'fiber':
        scenario_config = SingleTechnologyScenarioConf(
                technology="Fiber",
                tech_config=DEFAULT_FIBER_CONF,
                **DEFAULT_SCENARIO_PARAMS
            )
    elif args.scenario_type == 'cellular':
        scenario_config = SingleTechnologyScenarioConf(
                technology="Cellular",
                tech_config=DEFAULT_CELLULAR_CONF,
                **DEFAULT_SCENARIO_PARAMS
            )
        scenario_config.tech_config = DEFAULT_CELLULAR_CONF
    elif args.scenario_type == 'satellite':
        scenario_config = SingleTechnologyScenarioConf(
                technology="Satellite",
                tech_config=DEFAULT_SATELLITE_CONF,
                **DEFAULT_SCENARIO_PARAMS
            )
    else:
        # minimum cost
        scenario_config = MinimumCostScenarioConf(
                            **DEFAULT_SCENARIO_PARAMS, 
                            technologies=[DEFAULT_FIBER_CONF,
                                          DEFAULT_SATELLITE_CONF,
                                          DEFAULT_CELLULAR_CONF]
        )
        scenario_config.technologies[2] = DEFAULT_CELLULAR_CONF
    # Initialize the output space (client for managing model results)
    output_space = OutputSpace()
    # create scenario
    scenario = create_scenario(scenario_config, data_space, output_space)
    # run the scenario
    output_space = scenario.run()
    # write results
    output_space.table.to_csv(args.output_file)


if __name__=='__main__':
    main()
