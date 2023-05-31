import os
import fnmatch
import json
from typing import List

from giga.utils.globals import COUNTRY_DEFAULT_WORKSPACE
from giga.data.store.stores import COUNTRY_DATA_STORE as data_store

# Get the countries to skip from an variable
skip_in_deployment_str = os.getenv("SKIP_COUNTRIES_IN_DEPLOYMENT", "sample")
# Parse the string into a list
SKIP_IN_DEPLOYMENT = skip_in_deployment_str.split(",") if skip_in_deployment_str else []


def get_registered_countries(directory=COUNTRY_DEFAULT_WORKSPACE) -> None:
    countries = []
    for root, _, filenames in data_store.walk(directory):
        for filename in fnmatch.filter(filenames, "*.json"):
            countries.append(filename.split(".")[0])
    return countries


def get_registered_country_names(
    default_parameter_dir=COUNTRY_DEFAULT_WORKSPACE, skip=SKIP_IN_DEPLOYMENT
):
    countries = get_registered_countries(default_parameter_dir)
    return [c.replace("_", " ").title() for c in countries if c not in skip]


def get_country_defaults(
    workspace="workspace", default_parameter_dir=COUNTRY_DEFAULT_WORKSPACE
):
    countries = get_registered_countries(default_parameter_dir)
    defaults = {}
    for country in countries:
        with data_store.open(os.path.join(default_parameter_dir, f"{country}.json")) as f:
            default = json.load(f)
        default["data"]["workspace"] = workspace
        defaults[country] = default
    return defaults


def get_country_code_lookup(default_parameter_dir=COUNTRY_DEFAULT_WORKSPACE):
    defaults = get_country_defaults(default_parameter_dir=default_parameter_dir)
    return {
        c: default["data"]["country_code"]
        for c, default in defaults.items()
        if default["data"]["country_code"]
    }
