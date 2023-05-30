from copy import deepcopy

from giga.schemas.conf.models import ElectricityCostConf
from giga.viz.notebooks.parameters.parameter_sheet import ParameterSheet

ELECTRICITY_MODEL_PARAMETERS = [
    {
        "parameter_name": "per_kwh_cost",
        "parameter_input_name": "Cost per kWh (USD)",
        "parameter_interactive": {
            "parameter_type": "float_slider",
            "value": 0.10,
            "min": 0,
            "max": 1,
            "step": 0.001,
            "show_default": True,
        },
    },
    {
        "parameter_name": "solar_cost_per_watt",
        "parameter_input_name": "Solar Total Cost (USD/Watt)",
        "parameter_interactive": {
            "parameter_type": "float_slider",
            "value": 1.0,
            "min": 0,
            "max": 10,
            "step": 0.01,
            "show_default": True,
        },
    },
]


class ElectricityParameterManager:
    """
    ElectricityParameterManager manages the interfaces and parameters for the electricity model.
    """

    def __init__(
        self, sheet_name="electricity", parameters=ELECTRICITY_MODEL_PARAMETERS
    ):
        self.sheet_name = sheet_name
        self.parameters = {p["parameter_name"]: p for p in parameters}
        self.sheet = ParameterSheet(sheet_name, parameters)

    def update_parameters(self, config):
        if len(config) == 0:
            return
        self.sheet.update_parameter("per_kwh_cost", config["opex"]["cost_per_kwh"])
        self.sheet.update_parameter(
            "solar_cost_per_watt", config["capex"]["solar_cost_per_watt"]
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
        cost_per_kwh = float(self.get_parameter_from_sheet("per_kwh_cost"))
        solar_cost_per_watt = float(self.get_parameter_from_sheet("solar_cost_per_watt"))
        return ElectricityCostConf(
            capex={
                "solar_cost_per_watt": solar_cost_per_watt
            },
            opex={"cost_per_kwh": cost_per_kwh},
        )
