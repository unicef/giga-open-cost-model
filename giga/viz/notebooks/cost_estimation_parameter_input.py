import math
import io
import os
from ipywidgets import (
    FloatSlider,
    IntSlider,
    Checkbox,
    Dropdown,
    FileUpload,
    VBox,
    Layout,
)
from ipysheet import sheet, column, row, cell, to_dataframe
from omegaconf import DictConfig

import pandas as pd

from giga.schemas.conf.models import FiberTechnologyCostConf
from giga.schemas.conf.data import DataSpaceConf
from giga.schemas.geo import UniqueCoordinateTable
from giga.app.config import ConfigClient, get_config


FIBER_MODEL_PARAMETERS = [
    {
        "parameter_name": "cost_per_km",
        "parameter_input_name": "Cost Per km (USD)",
        "parameter_interactive": IntSlider(7_500, min=0, max=50_000, step=100),
    },
    {
        "parameter_name": "fixed_costs",
        "parameter_input_name": "Maintenance Cost (USD)",
        "parameter_interactive": IntSlider(0, min=0, max=5_000, step=10),
    },
    {
        "parameter_name": "maximum_connection_length",
        "parameter_input_name": "Maximum Connection Length (km)",
        "parameter_interactive": IntSlider(50, min=0, max=100),
    },
    {
        "parameter_name": "economies_of_scale",
        "parameter_input_name": "Economies of Scale",
        "parameter_interactive": Checkbox(value=True, description="ON"),
    },
]

BASELINE_DATA_SPACE_PARAMETERS = [
    {
        "parameter_name": "country_name",
        "parameter_input_name": "Country",
        "parameter_interactive": Dropdown(
            options=["Sample", "Brazil", "Rwanda"],
            value="Brazil",
            description="Country:",
            layout=Layout(width="400px"),
        ),
    }
]

UPLOADED_DATA_SPACE_PARAMETERS = BASELINE_DATA_SPACE_PARAMETERS + [
    {
        "parameter_name": "fiber_map_upload",
        "parameter_input_name": "Fiber Map",
        "parameter_interactive": FileUpload(
            accept=".csv",
            multiple=False,
            description="Upload Fiber Map",
            layout=Layout(width="400px"),
        ),
    },
    {
        "parameter_name": "cell_tower_map_upload",
        "parameter_input_name": "Cell Tower Map",
        "parameter_interactive": FileUpload(
            accept=".csv",
            multiple=False,
            description="Upload Cell Tower Map",
            layout=Layout(width="400px"),
        ),
    },
]

UPLOAD_SUFFIX = "_upload"


class CostEstimationParameterInput:
    """
    Creates an interactive dashboard in jupyter notebooks that allows users
    to configure data, model, and scenario parameters for connectivity cost estimation
    """

    def __init__(self, local_data_workspace="workspace"):
        self._hashed_sheets = {}
        self.workspace = local_data_workspace

    def fiber_parameters_input(self, sheet_name="fiber"):
        s = sheet(
            sheet_name,
            columns=2,
            rows=len(FIBER_MODEL_PARAMETERS),
            column_headers=False,
            row_headers=False,
            column_width=2,
        )
        name_column = column(
            0, list(map(lambda x: x["parameter_input_name"], FIBER_MODEL_PARAMETERS))
        )
        input_column = column(
            1, list(map(lambda x: x["parameter_interactive"], FIBER_MODEL_PARAMETERS))
        )
        return s

    def fiber_parameters(self, sheet_name="fiber"):
        s = sheet(sheet_name)
        df = to_dataframe(s)
        cost_per_km = float(df[df["A"] == "Cost Per km (USD)"]["B"])
        economies_of_scale = bool(float(df[df["A"] == "Economies of Scale"]["B"]))
        fixed_costs = float(df[df["A"] == "Maintenance Cost (USD)"]["B"])
        maximum_connection_length = (
            float(df[df["A"] == "Maximum Connection Length (km)"]["B"]) * 1000.0
        )  # meters
        return FiberTechnologyCostConf(
            capex={
                "cost_per_km": cost_per_km,
                "economies_of_scale": economies_of_scale,
            },
            opex={"fixed_costs": fixed_costs},
            constraints={"maximum_connection_length": maximum_connection_length},
        )

    def data_parameters_upload_input(self, sheet_name="data"):
        self._hashed_sheets[sheet_name + UPLOAD_SUFFIX] = {
            p["parameter_name"]: p["parameter_interactive"]
            for p in UPLOADED_DATA_SPACE_PARAMETERS
        }
        return VBox(
            list(
                map(
                    lambda x: x["parameter_interactive"], UPLOADED_DATA_SPACE_PARAMETERS
                )
            )
        )

    def data_parameters_input(self, sheet_name="data"):
        self._hashed_sheets[sheet_name] = {
            p["parameter_name"]: p["parameter_interactive"]
            for p in BASELINE_DATA_SPACE_PARAMETERS
        }
        return VBox(
            list(
                map(
                    lambda x: x["parameter_interactive"], BASELINE_DATA_SPACE_PARAMETERS
                )
            )
        )

    def _updated_param_request(self, country):
        return [f"data={country.lower()}", f"data.workspace={self.workspace}"]

    def _process_uploaded_data_parameters(self, s):
        country_id = s["country_name"].value
        config_request = self._updated_param_request(country_id)
        config = ConfigClient(get_config(config_request))
        school_dataset = config.school_file
        content = s["fiber_map_upload"].value[0].content
        return DataSpaceConf(
            school_data_conf={
                "country_id": country_id,
                "data": {"file_path": school_dataset, "table_type": "school"},
            },
            fiber_map_conf={
                "map_type": "fiber-nodes",
                "data": {"uploaded_content": content, "table_type": "coordinate-map"},
            },
        )

    def _process_baseline_data_parameters(self, s):
        country_id = s["country_name"].value
        config_request = self._updated_param_request(country_id)
        config = ConfigClient(get_config(config_request))
        school_dataset = config.school_file
        fiber_dataset = config.fiber_file
        return DataSpaceConf(
            school_data_conf={
                "country_id": country_id,
                "data": {"file_path": school_dataset, "table_type": "school"},
            },
            fiber_map_conf={
                "map_type": "fiber-nodes",
                "data": {"file_path": fiber_dataset, "table_type": "coordinate-map"},
            },
        )

    def data_parameters(self, sheet_name="data"):
        if sheet_name + UPLOAD_SUFFIX in self._hashed_sheets:
            s = self._hashed_sheets[sheet_name + UPLOAD_SUFFIX]
            return self._process_uploaded_data_parameters(s)
        else:
            s = self._hashed_sheets[sheet_name]
            return self._process_baseline_data_parameters(s)

    def parameter_input(self):
        d = self.data_parameters_input()
        f = self.fiber_parameters_input()
        return VBox([f, d])
