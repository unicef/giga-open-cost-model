from copy import deepcopy
import math
from ipywidgets import VBox
from pydantic import parse_obj_as
from traitlets import directional_link

from giga.viz.notebooks.parameters.parameter_sheet import ParameterSheet
from giga.viz.notebooks.parameters.input_parameter import InputParameter


DEFAULT_BUDGET_MILLIONS = 1

SCENARIO_BASE_PARAMETERS = [
    {
        "parameter_name": "scenario_type",
        "parameter_input_name": "Cost Scenario",
        "parameter_interactive": {
            "parameter_type": "categorical_dropdown",
            "value": "Lowest Cost",
            "options": [
                "Lowest Cost",
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
            "show_default": True,
        },
    },
    {
        "parameter_name": "bandwidth_demand",
        "parameter_input_name": "Bandwidth Demand (Mbps)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 20,
            "min": 0,
            "max": 500,
            "step": 5,
            "show_default": True,
        },
    },
    {
        "parameter_name": "use_budget_constraint",
        "parameter_input_name": "Use Budget Constraint",
        "parameter_interactive": {
            "parameter_type": "bool_checkbox",
            "value": False,
            "description": "",
        },
    },
    {
        "parameter_name": "budget_constraint",
        "parameter_input_name": "Project Budget (Millions USD)",
        "parameter_interactive": {
            "parameter_type": "float_slider",
            "value": DEFAULT_BUDGET_MILLIONS,
            "min": 0,
            "max": 500,
            "step": 0.01,
        },
    },
]

MILLION_DOLLARS = 1_000_000


def get_scenario_type(config):
    if config["scenario_id"] == "minimum_cost":
        return "Lowest Cost"
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
    elif config["scenario_id"] == "single_tech_cost" and config["technology"] == "P2P":
        return "P2P Only"
    else:
        raise ValueError(f"Unknown scenario_id: {config['scenario_id']}")


def constraint_disabled_transform(budget_cosntraint_on):
    return not budget_cosntraint_on


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
        scenario_type = self._hash["scenario_type"]
        budget_flag = self.sheet.get_interactive_parameter("use_budget_constraint")
        budget_constraint = self.sheet.get_interactive_parameter("budget_constraint")
        directional_link(
            (budget_flag, "value"),
            (budget_constraint, "disabled"),
            constraint_disabled_transform,
        )

    def update_parameters(self, config):
        self._hash["scenario_type"].value = get_scenario_type(config)
        self.sheet.update_parameter("years_opex", config["years_opex"])
        self.sheet.update_parameter("bandwidth_demand", config["bandwidth_demand"])
        try:
            self.sheet.update_parameter(
                "budget_constraint",
                config["cost_minimizer_config"]["budget_constraint"] / MILLION_DOLLARS,
            )
            self.sheet.update_parameter("use_budget_constraint", True)
        except KeyError:
            self.sheet.update_parameter(
                "budget_constraint",
                DEFAULT_BUDGET_MILLIONS,
            )
            self.sheet.update_parameter("use_budget_constraint", False)

    def update_country_parameters(self, config):
        self.sheet.update_parameter("years_opex", config["years_opex"])
        self.sheet.update_parameter("bandwidth_demand", config["bandwidth_demand"])

    def input_parameters(self):
        # specaial handling for scenario type in base parameters
        base = VBox(list(self._hash.values()))
        sheet = self.sheet.input_parameters()
        return VBox([base, sheet])

    def get_parameter_from_sheet(self, parameter_name):
        return self.sheet.get_parameter_value(parameter_name)

    def freeze(self):
        # do not update budget constraint with this interface
        budget_state = self.sheet.get_interactive_parameter(
            "budget_constraint"
        ).disabled
        self.sheet.freeze()
        self.sheet.get_interactive_parameter(
            "budget_constraint"
        ).disabled = budget_state
        self._hash["scenario_type"].disabled = True

    def unfreeze(self):
        budget_state = self.sheet.get_interactive_parameter(
            "budget_constraint"
        ).disabled
        self.sheet.unfreeze()
        self.sheet.get_interactive_parameter(
            "budget_constraint"
        ).disabled = budget_state
        self._hash["scenario_type"].disabled = False

    def get_model_parameters(self):
        base_parameters = {
            "scenario_type": self._hash["scenario_type"].value,
            "opex_responsible": "Consumer",  # s["opex_responsible"].value,
        }
        years_opex = float(self.get_parameter_from_sheet("years_opex"))
        bandwidth_demand = float(self.get_parameter_from_sheet("bandwidth_demand"))
        use_budget_constraint = self.get_parameter_from_sheet("use_budget_constraint")
        budget_constraint = float(self.get_parameter_from_sheet("budget_constraint"))
        sheet_parameters = {
            "years_opex": years_opex,
            "bandwidth_demand": bandwidth_demand,
            "use_budget_constraint": use_budget_constraint,
            "cost_minimizer_config": {
                "budget_constraint": budget_constraint * MILLION_DOLLARS
            },
        }
        return {**base_parameters, **sheet_parameters}
