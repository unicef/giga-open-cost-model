from copy import deepcopy
from ipywidgets import VBox
from pydantic import parse_obj_as
from traitlets import directional_link

from giga.viz.notebooks.parameters.parameter_sheet import ParameterSheet
from giga.viz.notebooks.parameters.input_parameter import InputParameter


SCENARIO_BASE_PARAMETERS = [
    {
        "parameter_name": "scenario_tpye",
        "parameter_input_name": "Cost Scenario",
        "parameter_interactive": {
            "parameter_type": "categorical_dropdown",
            "value": "Lowest Cost",
            "options": [
                "Lowest Cost",
                "Budget Constrained",
                "Fiber Only",
                "Satellite LEO Only",
                "Cellular Only",
                "P2P Only",
            ],
            "description": "Cost Scenario:",
        },
    },
]

SCENARIO_SHEET_PARAMETERS = [
    {
        "parameter_name": "years_opex",
        "parameter_input_name": "OpEx Years",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 5,
            "min": 0,
            "max": 10,
            "step": 1,
        },
    },
    {
        "parameter_name": "bandwidth_demand",
        "parameter_input_name": "Bandwidth Demand (Mbps)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 20,
            "min": 1,
            "max": 500,
            "step": 1,
        },
    },
    {
        "parameter_name": "budget_constraint",
        "parameter_input_name": "Project Budget (Millions USD)",
        "parameter_interactive": {
            "parameter_type": "float_slider",
            "value": 1,
            "min": 0,
            "max": 500,
            "step": 0.1,
        },
    },
]

MILLION_DOLLARS = 1_000_000


def get_scenario_type(config):
    if config["scenario_id"] == "minimum_cost":
        return "Lowest Cost"
    elif config["scenario_id"] == "budget_constrained":
        return "Budget Constrained"
    elif (
        config["scenario_id"] == "single_tech_cost" and config["technology"] == "Fiber"
    ):
        return "Fiber Only"
    elif (
        config["scenario_id"] == "single_tech_cost"
        and config["technology"] == "Satellite"
    ):
        return "Satellite LEO Only"
    elif (
        config["scenario_id"] == "single_tech_cost"
        and config["technology"] == "Cellular"
    ):
        return "Cellular Only"
    elif (
        config["scenario_id"] == "single_tech_cost"
        and config["technology"] == "P2P"
    ):
        return "P2P Only"
    else:
        raise ValueError(f"Unknown scenario_id: {config['scenario_id']}")


def constraint_disabled_transform(scenario_type):
    if scenario_type == "Budget Constrained":
        return False
    else:
        return True


class ScenarioParameterManager:
    def __init__(
        self,
        sheet_name="scenario",
        base_parameters=SCENARIO_BASE_PARAMETERS,
        sheet_parameters=SCENARIO_SHEET_PARAMETERS,
    ):
        self.sheet_name = sheet_name
        # these contain the parameter values and configs
        self.base_parameters = {p["parameter_name"]: p for p in base_parameters}
        self.sheet_parameters = {p["parameter_name"]: p for p in sheet_parameters}
        # these contain the interactive UI components
        self.sheet = ParameterSheet(sheet_name, sheet_parameters)
        self._hash = {
            p["parameter_name"]: parse_obj_as(
                InputParameter, p["parameter_interactive"]
            ).parameter
            for p in base_parameters
        }
        # link the scenario to the budget
        scenario_type = self._hash["scenario_tpye"]
        budget_constraint = self.sheet.get_interactive_parameter("budget_constraint")
        directional_link(
            (scenario_type, "value"),
            (budget_constraint, "disabled"),
            constraint_disabled_transform,
        )

    @staticmethod
    def from_config(
        config,
        sheet_name="scenario",
        default_base_parameters=SCENARIO_BASE_PARAMETERS,
        default_sheet_parameters=SCENARIO_SHEET_PARAMETERS,
    ):
        if len(config) == 0:
            return ScenarioParameterManager(
                sheet_name=sheet_name,
                base_parameters=default_base_parameters,
                sheet_parameters=default_sheet_parameters,
            )
        input_base_parameters = deepcopy(default_base_parameters)
        input_sheet_parameters = deepcopy(default_sheet_parameters)
        input_base_parameters = {
            p["parameter_name"]: p for p in input_base_parameters
        }  # squish
        input_sheet_parameters = {
            p["parameter_name"]: p for p in input_sheet_parameters
        }  # squish
        input_sheet_parameters["years_opex"]["parameter_interactive"]["value"] = config[
            "years_opex"
        ]
        input_sheet_parameters["bandwidth_demand"]["parameter_interactive"][
            "value"
        ] = config["bandwidth_demand"]
        if config["scenario_id"] == "minimum_cost":
            input_base_parameters["scenario_tpye"]["parameter_interactive"][
                "value"
            ] = "Lowest Cost"
        elif config["scenario_id"] == "budget_constrained":
            input_base_parameters["scenario_tpye"]["parameter_interactive"][
                "value"
            ] = "Budget Constrained"
            input_sheet_parameters["budget_constraint"]["parameter_interactive"][
                "value"
            ] = (config["cost_minimizer_config"]["budget_constraint"] / MILLION_DOLLARS)
        elif (
            config["scenario_id"] == "single_tech_cost"
            and config["technology"] == "Fiber"
        ):
            input_base_parameters["scenario_tpye"]["parameter_interactive"][
                "value"
            ] = "Fiber Only"
        elif (
            config["scenario_id"] == "single_tech_cost"
            and config["technology"] == "Satellite"
        ):
            input_base_parameters["scenario_tpye"]["parameter_interactive"][
                "value"
            ] = "Satellite LEO Only"
        elif (
            config["scenario_id"] == "single_tech_cost"
            and config["technology"] == "Cellular"
        ):
            input_base_parameters["scenario_tpye"]["parameter_interactive"][
                "value"
            ] = "Cellular Only"
        elif (
            config["scenario_id"] == "single_tech_cost"
            and config["technology"] == "P2P"
        ):
            input_base_parameters["scenario_tpye"]["parameter_interactive"][
				"value"
			] = "P2P Only"
        else:
            raise ValueError(
                f'Unknown scenario type {config["scenario_parameters"]["scenario_id"]}'
            )
        input_base_parameters = list(input_base_parameters.values())  # unpack
        input_sheet_parameters = list(input_sheet_parameters.values())  # unpack
        return ScenarioParameterManager(
            sheet_name=sheet_name,
            base_parameters=input_base_parameters,
            sheet_parameters=input_sheet_parameters,
        )

    def update_parameters(self, config):
        self._hash["scenario_tpye"].value = get_scenario_type(config)
        self.sheet.update_parameter("years_opex", config["years_opex"])
        self.sheet.update_parameter("bandwidth_demand", config["bandwidth_demand"])
        self.sheet.update_parameter(
            "budget_constraint",
            config["cost_minimizer_config"]["budget_constraint"] / MILLION_DOLLARS,
        )

    def input_parameters(self):
        # specaial handling for scenario type in base parameters
        base = VBox(list(self._hash.values()))
        sheet = self.sheet.input_parameters()
        return VBox([base, sheet])

    def get_parameter_from_sheet(self, parameter_name):
        return self.sheet.get_parameter_value(parameter_name)

    def get_model_parameters(self):
        base_parameters = {
            "scenario_type": self._hash["scenario_tpye"].value,
            "opex_responsible": "Consumer",  # s["opex_responsible"].value,
        }
        years_opex = float(self.get_parameter_from_sheet("years_opex"))
        bandwidth_demand = float(self.get_parameter_from_sheet("bandwidth_demand"))
        budget_constraint = float(self.get_parameter_from_sheet("budget_constraint"))
        sheet_parameters = {
            "years_opex": years_opex,
            "bandwidth_demand": bandwidth_demand,
            "cost_minimizer_config": {
                "budget_constraint": budget_constraint * MILLION_DOLLARS
            },
        }
        return {**base_parameters, **sheet_parameters}
