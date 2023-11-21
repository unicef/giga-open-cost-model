from copy import deepcopy
import math
from ipywidgets import VBox, Textarea, Layout, HBox, Label
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
            "value": "Lowest Cost - Actual",
            "options": [
                "Lowest Cost - Actual",
                "Lowest Cost - Giga",
                "Priorities",
            ],
            "description": "Cost Scenario:",
        },
    },
]

SCENARIO_SHEET_PARAMETERS_OLD = [
    {
        "parameter_name": "fiber",
        "parameter_input_name": "Allow fiber",
        "parameter_interactive": {
            "parameter_type": "bool_checkbox",
            "value": True,
            "description": "",
        },
    },
    {
        "parameter_name": "cell",
        "parameter_input_name": "Allow cellular",
        "parameter_interactive": {
            "parameter_type": "bool_checkbox",
            "value": True,
            "description": "",
        },
    },{
        "parameter_name": "p2p",
        "parameter_input_name": "Allow P2P",
        "parameter_interactive": {
            "parameter_type": "bool_checkbox",
            "value": True,
            "description": "",
        },
    },
    {
        "parameter_name": "sat",
        "parameter_input_name": "Allow satellite",
        "parameter_interactive": {
            "parameter_type": "bool_checkbox",
            "value": True,
            "description": "",
        },
    },
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

SCENARIO_SHEET_PARAMETERS = [
    {
        "parameter_name": "technologies",
        "parameter_input_name": "Select the allowed technologies (the order will be taken into account for priority scenario)",
        "parameter_interactive":{
            "parameter_type":"select_multiple",
            "options": ["Fiber","Cellular","P2P","Satellite"],
            "value": [],
            "description": "",
        },
    },
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


def get_scenario_type_old(config):
    if config["scenario_id"] == "minimum_cost":
        return "Lowest Cost"
    elif (
        config["scenario_id"] == "single_tech_cost" and config["single_tech"] == "Fiber"
    ):
        return "Fiber Only"
    elif (
        config["scenario_id"] == "single_tech_cost"
        and config["single_tech"] == "Satellite"
    ):
        return "Satellite LEO Only"
    elif (
        config["scenario_id"] == "single_tech_cost"
        and config["single_tech"] == "Cellular"
    ):
        return "Cellular Only"
    elif config["scenario_id"] == "single_tech_cost" and config["single_tech"] == "P2P":
        return "P2P Only"
    else:
        raise ValueError(f"Unknown scenario_id: {config['scenario_id']}")

def get_scenario_type(config):
    if config["scenario_id"] == "minimum_cost_actual":
        return "Lowest Cost - Actual"
    elif config["scenario_id"] == "minimum_cost_giga":
        return "Lowest Cost - Giga"
    elif config["scenario_id"] == "priority_cost":
        return "Priorities"
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
        budget_flag = self.sheet.get_interactive_parameter("use_budget_constraint")
        budget_constraint = self.sheet.get_interactive_parameter("budget_constraint")
        directional_link(
            (budget_flag, "value"),
            (budget_constraint, "disabled"),
            constraint_disabled_transform,
        )
        #ordered techs
        self.techs_ordered = []
        self.chosen_techs_label = Label("Chosen Technologies (ordered):")
        self.chosen_techs = Textarea(
            description='',
            disabled=True,
            layout=Layout(height='80px')  # Adjust the height as needed
        )
        self.sheet.get_interactive_parameter("technologies").observe(self.on_change_techs)


    def on_change_techs(self,change):
        if change['type'] == 'change' and change['name'] == 'value':
            for elem in change['new']:
                if elem not in self.techs_ordered:
                    self.techs_ordered.append(elem)
            for elem in self.techs_ordered:
                if elem not in change['new']:
                    self.techs_ordered.remove(elem)
            selected_techs = '\n'.join(self.techs_ordered)
            self.chosen_techs.value = selected_techs

    def get_ordered_techs(self):
        return self.techs_ordered
    
    def set_ordered_techs(self,values):
        self.techs_ordered = values

    def update_parameters_old(self, config):
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

    def update_parameters(self, config):
        self._hash["scenario_type"].value = get_scenario_type(config)
        self.sheet.update_parameter("years_opex", config["years_opex"])
        self.sheet.update_parameter("bandwidth_demand", config["bandwidth_demand"])
        if config["cost_minimizer_config"]["budget_constraint"]==math.inf:
            self.sheet.update_parameter(
                "budget_constraint",
                DEFAULT_BUDGET_MILLIONS,
            )
            self.sheet.update_parameter("use_budget_constraint", False)
        else:
            self.sheet.update_parameter(
                "budget_constraint",
                config["cost_minimizer_config"]["budget_constraint"] / MILLION_DOLLARS,
            )
            self.sheet.update_parameter("use_budget_constraint", True)

    def update_country_parameters(self, config):
        self.sheet.update_parameter("years_opex", config["years_opex"])
        self.sheet.update_parameter("bandwidth_demand", config["bandwidth_demand"])

    def update_techs_parameters(self, config):
        select_multiple = self.sheet.get_interactive_parameter("technologies")
        options = []
        if config['fiber']:
            options.append("Fiber")
        if config['cellular']:
            options.append("Cellular")
        if config['p2p']:
            options.append("P2P")
        if config['satellite']:
            options.append("Satellite")

        select_multiple.options = options
        select_multiple.value = []#options
        self.techs_ordered = []#options

        self.chosen_techs.value = ""
        

    def input_parameters(self, show_defaults = True):
        # specaial handling for scenario type in base parameters
        base = VBox(list(self._hash.values()))
        sheet = self.sheet.input_parameters(show_defaults)
        return HBox([VBox([base, sheet]),VBox([self.chosen_techs_label,self.chosen_techs])])

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
            "scenario_type": self._hash["scenario_type"].value if "scenario_type" in self._hash else None,
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
