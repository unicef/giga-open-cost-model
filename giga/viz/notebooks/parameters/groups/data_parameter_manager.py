from copy import deepcopy
from ipywidgets import VBox
from pydantic import parse_obj_as

from giga.app.config_client import ConfigClient
from giga.viz.notebooks.parameters.input_parameter import InputParameter
from giga.app.config import get_registered_country_names


BASELINE_DATA_SPACE_PARAMETERS = [
    {
        "parameter_name": "country_name",
        "parameter_input_name": "Country",
        "parameter_interactive": {
            "parameter_type": "categorical_dropdown",
            "value": "Rwanda",
            "options": get_registered_country_names(),  # load in the available countries dynamically
            "description": "Country:",
        },
    }
]


def country_name_to_key(country_name):
    return country_name.lower().replace(" ", "_")


def country_key_to_name(country_key):
    return country_key.replace("_", " ").title()


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

    @property
    def interactive_country_parameter(self):
        return self._hash["country_name"]

    def update_parameters(self, config):
        self._hash["country_name"].value = country_key_to_name(
            config["school_data_conf"]["country_id"]
        )

    def input_parameters(self):
        # specaial handling for scenario type in base parameters
        return VBox(list(self._hash.values()))

    def freeze(self):
        self.interactive_country_parameter.disabled = True

    def unfreeze(self):
        self.interactive_country_parameter.disabled = False

    def get_model_parameters(self):
        country_id = country_name_to_key(self._hash["country_name"].value)
        config = ConfigClient.from_registered_country(country_id, self.workspace)
        return config.local_workspace_data_space_config
    
    def get_country_id(self):
        return country_name_to_key(self._hash["country_name"].value)
