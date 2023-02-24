from copy import deepcopy
from ipywidgets import VBox
from pydantic import parse_obj_as

from giga.app.config import ConfigClient, get_config
from giga.viz.notebooks.parameters.input_parameter import InputParameter

BASELINE_DATA_SPACE_PARAMETERS = [
    {
        "parameter_name": "country_name",
        "parameter_input_name": "Country",
        "parameter_interactive": {
            "parameter_type": "categorical_dropdown",
            "value": "Sample",
            "options": ["Sample", "Rwanda", "Brazil"],
            "description": "Country:",
        },
    }
]


class DataParameterManager:
    def __init__(
        self, parameters=BASELINE_DATA_SPACE_PARAMETERS, workspace="workspace"
    ):
        self.parameters = {p["parameter_name"]: p for p in parameters}
        self.workspace = workspace
        self._hash = {
            p["parameter_name"]: parse_obj_as(
                InputParameter, p["parameter_interactive"]
            ).parameter
            for p in parameters
        }

    @staticmethod
    def from_config(
        config, default_parameters=BASELINE_DATA_SPACE_PARAMETERS, workspace="workspace"
    ):
        input_parameters = deepcopy(default_parameters)
        input_parameters = {p["parameter_name"]: p for p in input_parameters}  # squish
        input_parameters["country_name"]["parameter_interactive"]["value"] = config[
            "school_data_conf"
        ]["country_id"].capitalize()
        input_parameters = list(input_parameters.values())  # unpack
        return DataParameterManager(input_parameters, workspace=workspace)

    def update_parameters(self, config):
        self._hash["country_name"].value = config["school_data_conf"][
            "country_id"
        ].capitalize()

    def input_parameters(self):
        # specaial handling for scenario type in base parameters
        return VBox(list(self._hash.values()))

    def get_model_parameters(self, workspace="workspace"):
        country_id = self._hash["country_name"].value
        config_request = [
            f"data={country_id.lower()}",
            f"data.workspace={self.workspace}",
        ]
        config = ConfigClient(get_config(config_request))
        return config.local_workspace_data_space_config
