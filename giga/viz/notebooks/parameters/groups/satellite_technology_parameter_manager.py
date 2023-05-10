from copy import deepcopy

from giga.schemas.conf.models import SatelliteTechnologyCostConf
from giga.viz.notebooks.parameters.parameter_sheet import ParameterSheet


SATELLITE_MODEL_PARAMETERS = [
    {
        "parameter_name": "install_costs",
        "parameter_input_name": "Installation Cost (USD)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 600,
            "min": 0,
            "max": 2_000,
            "step": 1,
            "show_default": True,
        },
    },
    {
        "parameter_name": "annual_bandwidth_cost_per_mbps",
        "parameter_input_name": "Annual cost per Mbps (USD)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 15,
            "min": 0,
            "max": 100,
            "step": 1,
            "show_default": True,
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
            "show_default": True,
        },
    },
    {
        "parameter_name": "required_power",
        "parameter_input_name": "Annual Power Required (kWh)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 200,
            "min": 0,
            "max": 1_000,
            "step": 10,
            "show_default": True,
        },
    },
]


class SatelliteTechnologyParameterManager:
    def __init__(self, sheet_name="satellite", parameters=SATELLITE_MODEL_PARAMETERS):
        self.sheet_name = sheet_name
        self.parameters = {p["parameter_name"]: p for p in parameters}
        self.sheet = ParameterSheet(sheet_name, parameters)

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
            "required_power", config["constraints"]["required_power"]
        )

    def input_parameters(self):
        return self.sheet.input_parameters()

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
        maintenance_cost = float(self.get_parameter_from_sheet("fixed_costs"))
        required_power = float(self.get_parameter_from_sheet("required_power"))
        return SatelliteTechnologyCostConf(
            capex={"fixed_costs": install_cost},
            opex={
                "fixed_costs": maintenance_cost,
                "annual_bandwidth_cost_per_mbps": annual_cost_per_mbps,
            },
            constraints={
                "maximum_bandwithd": 150.0,  # should be pulled from defaults
                "required_power": required_power,
            },
        )
