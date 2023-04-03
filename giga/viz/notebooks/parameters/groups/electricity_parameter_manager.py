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
            "step": 0.1,
        },
    },
    {
        "parameter_name": "solar_panel_costs",
        "parameter_input_name": "Solar Panel Install Cost (USD)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 10_000,
            "min": 0,
            "max": 30_000,
            "step": 100,
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

    @staticmethod
    def from_config(
        config,
        sheet_name="electricity",
        default_parameters=ELECTRICITY_MODEL_PARAMETERS,
    ):
        if len(config) == 0:
            return ElectricityParameterManager(
                sheet_name=sheet_name, parameters=default_parameters
            )
        input_parameters = deepcopy(default_parameters)
        input_parameters = {p["parameter_name"]: p for p in input_parameters}  # squish
        capex, opex = config.get("capex", {}), config.get("opex", {})
        # get capex
        input_parameters["solar_panel_costs"]["parameter_interactive"]["value"] = capex[
            "solar_panel_costs"
        ]
        # get opex
        input_parameters["per_kwh_cost"]["parameter_interactive"]["value"] = opex[
            "cost_per_kwh"
        ]
        input_parameters = list(input_parameters.values())  # unpack
        return ElectricityParameterManager(
            sheet_name=sheet_name, parameters=input_parameters
        )

    def update_parameters(self, config):
        if len(config) == 0:
            return
        self.sheet.update_parameter("per_kwh_cost", config["opex"]["cost_per_kwh"])
        self.sheet.update_parameter(
            "solar_panel_costs", config["capex"]["solar_panel_costs"]
        )

    def input_parameters(self):
        return self.sheet.input_parameters()

    def get_parameter_from_sheet(self, parameter_name):
        return self.sheet.get_parameter_value(parameter_name)

    def get_model_parameters(self):
        cost_per_kwh = float(self.get_parameter_from_sheet("per_kwh_cost"))
        install_solar_panels = float(self.get_parameter_from_sheet("solar_panel_costs"))
        return ElectricityCostConf(
            capex={
                "solar_panel_costs": install_solar_panels,
                "battery_costs": 0.0,
            },  # TODO: ignore for now
            opex={"cost_per_kwh": cost_per_kwh},
        )
