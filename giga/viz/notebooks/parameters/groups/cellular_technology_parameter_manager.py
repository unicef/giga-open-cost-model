from copy import deepcopy
import ipysheet

from giga.schemas.conf.models import CellularTechnologyCostConf
from giga.viz.notebooks.parameters.parameter_sheet import ParameterSheet


CELLULAR_MODEL_PARAMETERS = [
    {
        "parameter_name": "install_costs",
        "parameter_input_name": "Installation Cost (USD)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 500,
            "min": 0,
            "max": 2_500,
            "step": 10,
        },
    },
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
        "parameter_name": "fixed_costs",
        "parameter_input_name": "Annual Maintenance Cost (USD)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 0,
            "min": 0,
            "max": 1_000,
            "step": 10,
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
            "step": 10,
        },
    },
    {
        "parameter_name": "maximum_range",
        "parameter_input_name": "Maximum Cell Tower Range (km)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 8,
            "min": 0,
            "max": 25,
            "step": 1,
        },
    },
]

METERS_PER_KM = 1000.0


class CellularTechnologyParameterManager:
    def __init__(self, sheet_name="cellular", parameters=CELLULAR_MODEL_PARAMETERS):
        self.sheet_name = sheet_name
        self.parameters = {p["parameter_name"]: p for p in parameters}
        self.sheet = ParameterSheet(sheet_name, parameters)

    @staticmethod
    def from_config(
        config, sheet_name="cellular", default_parameters=CELLULAR_MODEL_PARAMETERS
    ):
        if len(config) == 0:
            return CellularTechnologyParameterManager(
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
        input_parameters["install_costs"]["parameter_interactive"]["value"] = capex[
            "fixed_costs"
        ]
        # get opex
        input_parameters["fixed_costs"]["parameter_interactive"]["value"] = opex[
            "fixed_costs"
        ]
        input_parameters["annual_bandwidth_cost_per_mbps"]["parameter_interactive"][
            "value"
        ] = opex["annual_bandwidth_cost_per_mbps"]
        # get constraints
        input_parameters["required_power"]["parameter_interactive"][
            "value"
        ] = constraints["required_power"]
        input_parameters["maximum_range"]["parameter_interactive"][
            "value"
        ] = constraints["maximum_range"] / METERS_PER_KM
        input_parameters = list(input_parameters.values())  # unpack
        return CellularTechnologyParameterManager(
            sheet_name=sheet_name, parameters=input_parameters
        )

    def update_parameters(self, config):
        if len(config) == 0:
            return
        self.sheet.update_parameter("install_costs", config["capex"]["fixed_costs"])
        self.sheet.update_parameter("fixed_costs", config["opex"]["fixed_costs"])
        self.sheet.update_parameter(
            "annual_bandwidth_cost_per_mbps",
            config["opex"]["annual_bandwidth_cost_per_mbps"],
        )
        self.sheet.update_parameter(
            "rßequired_power", config["constraints"]["required_power"]
        )
        self.sheet.update_parameter(
            "maximum_range", config["constraints"]["maximum_range"] / METERS_PER_KM
        )

    def input_parameters(self):
        return self.sheet.input_parameters()

    def get_parameter_from_sheet(self, parameter_name):
        s = ipysheet.sheet(self.sheet_name)
        df = ipysheet.to_dataframe(s)
        input_name = self.parameters[parameter_name]["parameter_input_name"]
        return df[df["A"] == input_name]["B"]

    def get_model_parameters(self):
        annual_cost_per_mbps = float(
            self.get_parameter_from_sheet("annual_bandwidth_cost_per_mbps")
        )
        install_cost = float(self.get_parameter_from_sheet("install_costs"))
        maintenance_cost = float(self.get_parameter_from_sheet("fixed_costs"))
        required_power = float(self.get_parameter_from_sheet("required_power"))
        maximum_range = (
            float(self.get_parameter_from_sheet("maximum_range")) * METERS_PER_KM
        )
        return CellularTechnologyCostConf(
            capex={"fixed_costs": install_cost},
            opex={
                "fixed_costs": maintenance_cost,
                "annual_bandwidth_cost_per_mbps": annual_cost_per_mbps,
            },
            constraints={
                "maximum_bandwithd": 100.0,  # should be pulled from defaults
                "required_power": required_power,
                "maximum_range": maximum_range,
            },
        )
