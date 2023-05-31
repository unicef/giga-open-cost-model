from copy import deepcopy
import math
from ipywidgets import VBox
from pydantic import parse_obj_as
from traitlets import directional_link

from giga.viz.notebooks.parameters.parameter_sheet import ParameterSheet
from giga.viz.notebooks.parameters.input_parameter import InputParameter
from giga.viz.notebooks.parameters.groups.scenario_parameter_manager import (
    ScenarioParameterManager,
    SCENARIO_BASE_PARAMETERS,
    SCENARIO_SHEET_PARAMETERS,
)

SAT_SCENARIO_SHEET_PARAMETERS = [
    {
        "parameter_name": "sat_engine",
        "parameter_input_name": "SAT",
        "parameter_interactive": {
            "parameter_type": "bool_checkbox",
            "value": False,
            "description": "",
        },
    },
    {
        "parameter_name": "road_data",
        "parameter_input_name": "Road Data",
        "parameter_interactive": {
            "parameter_type": "bool_checkbox",
            "value": False,
            "description": "",
        },
    },
]


def not_fiber_scenario(scenario_type):
    if scenario_type == "Fiber Only":
        return False
    else:
        return True


class SATScenarioParameterManager(ScenarioParameterManager):
    def __init__(
        self,
        sheet_name="scenario-sat",
        base_parameters=SCENARIO_BASE_PARAMETERS,
        sheet_parameters=SCENARIO_SHEET_PARAMETERS + SAT_SCENARIO_SHEET_PARAMETERS,
    ):
        super().__init__(sheet_name, base_parameters, sheet_parameters)
        scenario_type = self._hash["scenario_type"]
        sat_flag = self.sheet.get_interactive_parameter("sat_engine")
        road_flag = self.sheet.get_interactive_parameter("road_data")
        directional_link(
            (scenario_type, "value"),
            (sat_flag, "disabled"),
            not_fiber_scenario,
        )
        directional_link(
            (scenario_type, "value"),
            (road_flag, "disabled"),
            not_fiber_scenario,
        )

    def update_parameters(self, config):
        super().update_parameters(config)
        if "sat" in config:
            self.sheet.update_parameter("sat_engine", config["sat"]["sat_engine"])
            self.sheet.update_parameter("road_data", config["sat"]["road_data"])

    def get_model_parameters(self):
        model_parameters = super().get_model_parameters()
        model_parameters["sat"] = {
            "sat_engine": bool(float(self.get_parameter_from_sheet("sat_engine"))),
            "road_data": bool(float(self.get_parameter_from_sheet("road_data"))),
        }
        return model_parameters
