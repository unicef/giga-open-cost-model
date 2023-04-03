from copy import deepcopy

from giga.schemas.conf.models import FiberTechnologyCostConf
from giga.viz.notebooks.parameters.parameter_sheet import ParameterSheet


METERS_IN_KM = 1_000.0

FIBER_MODEL_PARAMETERS = [
    {
        "parameter_name": "annual_bandwidth_cost_per_mbps",
        "parameter_input_name": "Annual cost per Mbps (USD)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 10,
            "min": 0,
            "max": 100,
            "step": 1,
        },
    },
    {
        "parameter_name": "cost_per_km",
        "parameter_input_name": "Cost Per km (USD)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 8_900,
            "min": 0,
            "max": 50_000,
            "step": 100,
        },
    },
    {
        "parameter_name": "opex_cost_per_km",
        "parameter_input_name": "Maintenance Cost per km (USD)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 100,
            "min": 0,
            "max": 1_000,
            "step": 10,
        },
    },
    {
        "parameter_name": "maximum_connection_length",
        "parameter_input_name": "Maximum Connection Length (km)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 20,
            "min": 0,
            "max": 100,
            "step": 1,
        },
    },
    {
        "parameter_name": "required_power",
        "parameter_input_name": "Annual Power Required (kWh)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 500,
            "min": 0,
            "max": 1_000,
            "step": 10,
        },
    },
    {
        "parameter_name": "economies_of_scale",
        "parameter_input_name": "Economies of Scale",
        "parameter_interactive": {
            "parameter_type": "bool_checkbox",
            "value": True,
            "description": "ON",
        },
    },
]


class FiberTechnologyParameterManager:
    def __init__(self, sheet_name="fiber", parameters=FIBER_MODEL_PARAMETERS):
        self.sheet_name = sheet_name
        self.parameters = {p["parameter_name"]: p for p in parameters}
        self.sheet = ParameterSheet(sheet_name, parameters)

    @staticmethod
    def from_config(
        config, sheet_name="fiber", default_parameters=FIBER_MODEL_PARAMETERS
    ):
        if len(config) == 0:
            return FiberTechnologyParameterManager(
                sheet_name=sheet_name, parameters=default_parameters
            )
        input_parameters = deepcopy(default_parameters)
        input_parameters = {p["parameter_name"]: p for p in input_parameters}  # squish
        capex, opex, constraints = (
            config.get("capex", {}),
            config.get("opex", {}),
            config.get("constraints", {}),
        )
        # get capex
        input_parameters["cost_per_km"]["parameter_interactive"]["value"] = capex[
            "cost_per_km"
        ]
        input_parameters["economies_of_scale"]["parameter_interactive"][
            "value"
        ] = capex["economies_of_scale"]
        # get opex
        input_parameters["opex_cost_per_km"]["parameter_interactive"]["value"] = opex[
            "cost_per_km"
        ]
        input_parameters["annual_bandwidth_cost_per_mbps"]["parameter_interactive"][
            "value"
        ] = opex["annual_bandwidth_cost_per_mbps"]
        # get constraints
        input_parameters["maximum_connection_length"]["parameter_interactive"][
            "value"
        ] = (constraints["maximum_connection_length"] / METERS_IN_KM)
        input_parameters["required_power"]["parameter_interactive"][
            "value"
        ] = constraints["required_power"]
        input_parameters = list(input_parameters.values())  # unpack
        return FiberTechnologyParameterManager(
            sheet_name=sheet_name, parameters=input_parameters
        )

    def update_parameters(self, config):
        if len(config) == 0:
            return
        self.sheet.update_parameter("cost_per_km", config["capex"]["cost_per_km"])
        self.sheet.update_parameter(
            "economies_of_scale", config["capex"]["economies_of_scale"]
        )
        self.sheet.update_parameter("opex_cost_per_km", config["opex"]["cost_per_km"])
        self.sheet.update_parameter(
            "annual_bandwidth_cost_per_mbps",
            config["opex"]["annual_bandwidth_cost_per_mbps"],
        )
        self.sheet.update_parameter(
            "maximum_connection_length",
            config["constraints"]["maximum_connection_length"] / METERS_IN_KM,
        )
        self.sheet.update_parameter(
            "required_power", config["constraints"]["required_power"]
        )

    def input_parameters(self):
        return self.sheet.input_parameters()

    def get_parameter_from_sheet(self, parameter_name):
        return self.sheet.get_parameter_value(parameter_name)

    def get_model_parameters(self):
        cost_per_km = float(self.get_parameter_from_sheet("cost_per_km"))
        annual_cost_per_mbps = float(
            self.get_parameter_from_sheet("annual_bandwidth_cost_per_mbps")
        )
        economies_of_scale = bool(
            float(self.get_parameter_from_sheet("economies_of_scale"))
        )
        opex_per_km = float(self.get_parameter_from_sheet("opex_cost_per_km"))
        required_power = float(self.get_parameter_from_sheet("required_power"))
        maximum_connection_length = (
            float(self.get_parameter_from_sheet("maximum_connection_length")) * 1_000.0
        )  # meters
        return FiberTechnologyCostConf(
            capex={
                "cost_per_km": cost_per_km,
                "economies_of_scale": economies_of_scale,
            },
            opex={
                "cost_per_km": opex_per_km,
                "annual_bandwidth_cost_per_mbps": annual_cost_per_mbps,
            },
            constraints={
                "maximum_connection_length": maximum_connection_length,
                "required_power": required_power,
                "maximum_bandwithd": 2_000.0,
            },
        )
