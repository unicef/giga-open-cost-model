from copy import deepcopy

from giga.schemas.conf.models import SATSolverConf
from giga.viz.notebooks.parameters.parameter_sheet import ParameterSheet


METERS_IN_KM = 1_000.0

SAT_SOLVER_PARAMS = [
    {
        "parameter_name": "time_limit",
        "parameter_input_name": "SAT Time Limit (seconds)",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 600,
            "min": 1,
            "max": 3_600,
            "step": 1,
        },
    },
    {
        "parameter_name": "num_workers",
        "parameter_input_name": "Number of Workers",
        "parameter_interactive": {
            "parameter_type": "int_slider",
            "value": 16,
            "min": 1,
            "max": 16,
            "step": 1,
        },
    },
    {
        "parameter_name": "do_hints",
        "parameter_input_name": "Use Hints",
        "parameter_interactive": {
            "parameter_type": "bool_checkbox",
            "value": False,
            "description": "ON",
        },
    },
    {
        "parameter_name": "search_log",
        "parameter_input_name": "Show SAT Search Logs",
        "parameter_interactive": {
            "parameter_type": "bool_checkbox",
            "value": False,
            "description": "ON",
        },
    },
]


class SATSolverParameterManager:
    def __init__(self, sheet_name="sat_solver", parameters=SAT_SOLVER_PARAMS):
        self.sheet_name = sheet_name
        self.parameters = {p["parameter_name"]: p for p in parameters}
        self.sheet = ParameterSheet(sheet_name, parameters)

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

    def freeze(self):
        self.sheet.freeze()

    def unfreeze(self):
        self.sheet.unfreeze()

    def get_model_parameters(self, budget: float = 0.0, cost_per_km: float = 0.0):
        time_limit = int(self.get_parameter_from_sheet("time_limit"))
        num_workers = int(self.get_parameter_from_sheet("num_workers"))
        do_hints = bool(float(self.get_parameter_from_sheet("do_hints")))
        search_log = bool(float(self.get_parameter_from_sheet("search_log")))
        return SATSolverConf(
            budget=budget,
            cost_per_km=cost_per_km,
            time_limit=time_limit,
            do_hints=do_hints,
            num_workers=num_workers,
            search_log=search_log,
        )
