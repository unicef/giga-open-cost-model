from copy import deepcopy

from giga.schemas.conf.models import CellularTechnologyCostConf
from giga.viz.notebooks.parameters.parameter_sheet import ParameterSheet


CELLULAR_MODEL_PARAMETERS = [
    {
        "parameter_name": "install_costs",
        "parameter_input_name": "Setup Costs (USD)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 50,
            "min": 0,
            "max": 1_000,
            "step": 1,
            "show_default": True,
        },
    },
    {
        "parameter_name": "annual_bandwidth_cost_per_mbps",
        "parameter_input_name": "Annual cost per Mbps (USD)",
        "parameter_interactive": {
            "parameter_type": "float_slider",
            "value": 10,
            "min": 0,
            "max": 1800,
            "step": 0.01,
            "show_default": True,
        },
    },
    {
        "parameter_name": "required_power",
        "parameter_input_name": "Annual Power Required (kWh)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 10,
            "min": 0,
            "max": 100,
            "step": 1,
            "show_default": True,
        },
    },
    {
        "parameter_name": "maximum_range",
        "parameter_input_name": "Maximum Cell Tower Range (km)",
        "parameter_interactive": {
            "parameter_type": "float_slider",
            "value": 8,
            "min": 0,
            "max": 25,
            "step": 0.1,
            "show_default": True,
        },
    },
]

METERS_PER_KM = 1000.0


class CellularTechnologyParameterManager:
    def __init__(self, sheet_name="cellular", parameters=CELLULAR_MODEL_PARAMETERS):
        self.sheet_name = sheet_name
        self.parameters = {p["parameter_name"]: p for p in parameters}
        self.sheet = ParameterSheet(sheet_name, parameters)

    def update_parameters(self, config):
        if len(config) == 0:
            return
        self.sheet.update_parameter("install_costs", config["capex"]["fixed_costs"])
        self.sheet.update_parameter(
            "annual_bandwidth_cost_per_mbps",
            config["opex"]["annual_bandwidth_cost_per_mbps"],
        )
        self.sheet.update_parameter(
            "required_power", config["constraints"]["required_power"]
        )
        self.sheet.update_parameter(
            "maximum_range", config["constraints"]["maximum_range"] #/ METERS_PER_KM
        )

    def input_parameters(self, show_defaults = True):
        return self.sheet.input_parameters(show_defaults)

    def get_parameter_from_sheet(self, parameter_name):
        return self.sheet.get_parameter_value(parameter_name)

    def freeze(self):
        self.sheet.freeze()

    def unfreeze(self):
        self.sheet.unfreeze()

    def get_model_parameters(self):
        annual_cost_per_mbps = float(
            self.get_parameter_from_sheet("annual_bandwidth_cost_per_mbps")
        )
        install_cost = float(self.get_parameter_from_sheet("install_costs"))
        required_power = float(self.get_parameter_from_sheet("required_power"))
        maximum_range = (
            float(self.get_parameter_from_sheet("maximum_range")) * METERS_PER_KM
        )
        return CellularTechnologyCostConf(
            capex={"fixed_costs": install_cost},
            opex={
                "fixed_costs": 0.0,
                "annual_bandwidth_cost_per_mbps": annual_cost_per_mbps,
            },
            constraints={
                "maximum_bandwithd": 100.0,  # should be pulled from defaults
                "required_power": required_power,
                "maximum_range": maximum_range,
            },
        )
